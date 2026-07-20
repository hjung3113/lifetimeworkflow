"""approval.py — the ADOPT-06 human-ratification gate (refuse-by-default promotion).

Modeled 1:1 on ``tools/golden_runner/approve.py``'s "machines gate, humans ratify" pattern
(CONTRACT-03, Pitfall P9): promotion is REFUSED unless ALL of an explicit human ``approve`` flag,
at least one reviewed decision, and a human confirmation value matching the
``GOLDEN_APPROVE_HUMAN`` environment variable are present — the SAME env var name/precedent
``tools/golden_runner/approve.py`` and ``tools/hooks/contract_guard.py`` already use, reused
deliberately rather than inventing a second adoption-specific variable.

Where ``/golden-approve`` binds a promotion to ``(case, adr_id)``, this gate binds to
``(draft_hash, task_revision, git_ref)`` — an exact-equality triple, each element RECOMPUTED FRESH
at every :func:`check_valid` call, never cached or trusted from an earlier call in the same
process (27-RESEARCH Pitfall 2: a "compatible"/"descendant" fuzzy ref match is not the correctness
bar; ``tools/handoff/handoff.py::validate``'s strict exact-membership ref check is). Changing ANY
ONE of the three — the draft content, the task's CAS revision, or the git ref — independently
invalidates a prior approval; no partial credit.

This module does not import ``tools.golden_runner.approve``'s private names: it is a peer module
with a different binding tuple, mirroring the SHAPE only (27-RESEARCH Alternatives Considered).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.adoption_apply.batch import _batch_dir
from tools.task_control.manager import show

REPO_ROOT = Path(__file__).resolve().parents[2]
APPROVAL_SCHEMA = REPO_ROOT / "contracts/harness/adoption/approval.schema.json"
APPROVAL_FILENAME = "approval.json"

# Reused verbatim from tools/golden_runner/approve.py — the same human-confirmation env var,
# not a second adoption-specific variable (27-RESEARCH Code Examples).
HUMAN_TOKEN_ENV = "GOLDEN_APPROVE_HUMAN"

_DRAFT_FILES: tuple[str, ...] = ("inventory.json", "plan.json", "manifest.json")


class AdoptionApprovalRefused(Exception):
    """Promotion refused: missing human approve flag, empty decisions, or bad confirmation."""


def _canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def _recompute_draft_hash(batch_dir: Path) -> str:
    """Deterministic sha256 over the batch's 3 draft artifacts, fixed order, recomputed fresh."""
    digest = hashlib.sha256()
    for name in _DRAFT_FILES:
        path = batch_dir / name
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _current_task_revision(task_dir: Path) -> int:
    """Delegate to tools.task_control.manager.show — never a hand-rolled state.json read."""
    return show(task_dir)["revision"]


def _current_git_ref(repo_root: Path) -> str:
    """Own-copy fixed-argv git-plumbing helper (mirrors handoff.py::_git's shape)."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise AdoptionApprovalRefused("cannot resolve repository HEAD for approval binding")
    return result.stdout.strip()


def _approval_path(task_dir: Path, batch_id: str) -> Path:
    return _batch_dir(task_dir, batch_id) / APPROVAL_FILENAME


def _validate_against_schema(document: dict[str, Any]) -> None:
    schema = json.loads(APPROVAL_SCHEMA.read_bytes())
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path)
    )
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.path) or "<root>"
        raise AdoptionApprovalRefused(f"approval.json:{where}: {error.message}")


def _atomic_replace(path: Path, document: dict[str, Any]) -> None:
    """Durably replace *path* — an approval may be legitimately re-issued after invalidation,
    so this is NOT a create-once primitive (unlike batch.py's status.json)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(document))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def promote(
    task_dir: Path,
    batch_id: str,
    repo_root: Path,
    *,
    approve: bool = False,
    decisions: list[dict[str, Any]] | None = None,
    confirmation: str | None = None,
) -> dict[str, Any]:
    """Ratify a batch's decisions into ``approval.json`` — or refuse (ADOPT-06).

    Mirrors ``golden_runner/approve.py::promote``'s exact three-signal refusal order: missing the
    explicit human flag, then an empty decisions list, then a missing/incorrect human confirmation.
    Only once all three pass is the approval document built, EVERY field recomputed fresh (never
    trusted from an earlier call in the same process), schema-validated, and durably written.
    """
    if not approve:
        raise AdoptionApprovalRefused(
            "REFUSED: promotion requires an explicit human --approve flag "
            "(agents must not self-bless an adoption batch, ADOPT-06)."
        )
    if not decisions:
        raise AdoptionApprovalRefused(
            "REFUSED: promotion requires at least one reviewed decision "
            "(a promotion with zero decisions is meaningless, ADOPT-06)."
        )

    reference_value = os.environ.get(HUMAN_TOKEN_ENV)
    if not reference_value or confirmation != reference_value:
        raise AdoptionApprovalRefused(
            f"REFUSED: promotion requires the human confirmation value (${HUMAN_TOKEN_ENV}); "
            "an agent must not fabricate it."
        )

    batch_dir = _batch_dir(task_dir, batch_id)
    document = {
        "batch_id": batch_id,
        "draft_hash": _recompute_draft_hash(batch_dir),
        "task_revision": _current_task_revision(task_dir),
        "git_ref": _current_git_ref(repo_root),
        "decisions": decisions,
        "approved_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    _validate_against_schema(document)
    _atomic_replace(_approval_path(task_dir, batch_id), document)
    return document


def check_valid(task_dir: Path, batch_id: str, repo_root: Path) -> bool:
    """True iff a stored approval's ``(draft_hash, task_revision, git_ref)`` still holds exactly.

    Every element is recomputed fresh at call time (T-27-04-03: no cached/stale validity result).
    No partial credit — any single mismatch returns ``False``.

    Never raises: an unreadable, malformed, or structurally-wrong stored approval is treated as
    invalid, extending WR-02's guarantee from the draft artifacts to the approval document itself
    (WR-06).
    """
    path = _approval_path(task_dir, batch_id)
    if not path.is_file():
        return False
    batch_dir = _batch_dir(task_dir, batch_id)
    try:
        # CR-01: decode EXPLICITLY as UTF-8 rather than handing bytes to `json.loads`, which runs
        # `json.detect_encoding` and silently accepts UTF-16/UTF-32 — an approval document in a
        # non-UTF-8 encoding would then validate as current, which §4.3 byte hygiene does not
        # sanction. The explicit decode also moves the failure of undecodable bytes onto a
        # `UnicodeDecodeError` we name below, instead of one raised implicitly inside `json.loads`.
        stored = json.loads(path.read_bytes().decode("utf-8"))
        draft_hash = _recompute_draft_hash(batch_dir)
        return (
            stored["draft_hash"] == draft_hash
            and stored["task_revision"] == _current_task_revision(task_dir)
            and stored["git_ref"] == _current_git_ref(repo_root)
        )
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as exc:
        # OSError: WR-02's original coverage — an incomplete batch directory (a
        # missing draft artifact) is no partial credit, never an uncaught crash out of a validity
        # check. WR-06 adds: JSONDecodeError for malformed approval bytes (it subclasses
        # ValueError, not OSError, so it was genuinely uncovered), KeyError for a missing required
        # key, and TypeError for valid JSON that is not an object, where ``stored["draft_hash"]``
        # raises rather than returning a mismatch. CR-01 adds UnicodeDecodeError — also a
        # ValueError subclass, named neither by JSONDecodeError nor by OSError — for bytes that
        # are not decodable UTF-8 at all. ``FileNotFoundError`` is not listed: it is an ``OSError``
        # subclass, so naming it was redundant.
        #
        # The diagnostic names the path and the exception class ONLY — never the file's contents or
        # the exception's message body, since a corrupted approval may hold arbitrary bytes (the
        # same no-content-leak rule test_marker_merge_refuses_symlink_read establishes).
        print(
            f"approval.json unusable for batch '{batch_id}' at {path}: {type(exc).__name__}",
            file=sys.stderr,
        )
        return False
