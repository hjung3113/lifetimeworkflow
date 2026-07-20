"""apply.py — the ADOPT-05 atomic, collision-safe, idempotent manifest-apply writer.

RESEARCH's single highest-risk finding drives this module: ``tools/hooks/contract_guard.py`` is a
Claude Code ``PreToolUse`` hook — it fires ONLY on Claude's own Write/Edit tool calls, never on a
bare Python ``os.replace()``/``os.link()`` invocation. A caller that invokes this module directly
(bare CLI, CI, non-Claude-Code automation) has NO Claude hook anywhere in the loop. ``apply.py``
therefore duplicates the constitution-plane check as an explicit, structural, in-process
precondition — :func:`refuse_if_constitution`, reusing ``tools.hooks.contract_guard.
CONSTITUTION_GLOBS`` as DATA (never re-derived) — called at the START of :func:`apply_disposition`,
before any ``open()``/``os.link()``/``os.replace()`` call, for EVERY disposition branch, not cached
once per batch. A second, independent structural control, :func:`refuse_if_outside_root`, confines
discovery/draft-mode writes (ADOPT-05 clause 1) to a given task artifact root — the peer control
`/adopt draft` (Plan 27-06's ``cli.py``) calls before writing ``inventory.json``/``plan.json``/
``manifest.json``.

Two publish idioms, reused verbatim from ``tools.task_control.manager``'s already-audited sequence
(``tempfile.mkstemp`` in the target's own directory -> write/flush/fsync -> publish -> directory
fsync -> ``finally: os.unlink(tmp)``), each copied (not cross-package-imported) per 27-RESEARCH's
"Don't Hand-Roll" guidance:

* :func:`atomic_create` — ``os.link``-based; raises ``FileExistsError`` -> :class:`CollisionError`
  on an existing target. Never silently overwrites. Used for the ``create`` disposition, where a
  target is NOT expected to exist yet.
* :func:`_atomic_replace` — ``os.replace``-based. Used ONLY by :func:`_apply_marker_merge`, where a
  marker-merge target already exists by definition (``AGENTS.md``/``CLAUDE.md``/
  ``.claude/settings.json`` always pre-exist in a real target tree).

Marker-merge for the 3 ``MARKER_CAPABLE`` destinations reuses ``tools.harness_emit.merge``'s
``splice_managed_block``/``merge_settings`` verbatim — no second fence/marker scheme.

:func:`apply_manifest` iterates ``manifest["dispositions"]`` ONLY (never ``excluded[]``, never a
destination absent from both) and is TOTAL over the 6-value ``DISPOSITION_ENUM`` — any other value
raises :class:`UnknownDispositionError` rather than silently defaulting to ``create``.

No arbitrary command execution: this module never builds a ``subprocess`` argv from manifest/draft
content — in fact it never calls ``subprocess`` at all.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from tools.adoption_scan.destinations import DISPOSITION_ENUM, MARKER_CAPABLE, _existing_hash
from tools.harness_emit.merge import merge_settings, splice_managed_block
from tools.harness_perms import resolve_path
from tools.hooks.contract_guard import CONSTITUTION_GLOBS


class ConstitutionRefusal(ValueError):
    """Raised when a destination resolves onto the CODEOWNERS-gated constitution plane."""


class PathEscapeError(ValueError):
    """Raised when a resolved path is not the given root or a descendant of it."""


class CollisionError(ValueError):
    """Raised when ``atomic_create`` hits an existing target (the ``os.link`` collision check)."""


class UnknownDispositionError(ValueError):
    """Raised when a disposition record's ``disposition`` is outside ``DISPOSITION_ENUM``."""


class ConcurrentDriftError(ValueError):
    """Raised when a ``create`` target now exists though the manifest recorded none at draft
    time."""


def refuse_if_constitution(destination: str) -> None:
    """Raise :class:`ConstitutionRefusal` iff ``destination`` is on the constitution plane.

    Pure, in-process, structural — independent of any Claude ``PreToolUse`` hook. Callable as a
    bare function with no Claude tool-call event object anywhere in the chain.
    """
    if resolve_path(CONSTITUTION_GLOBS, destination) == "deny":
        raise ConstitutionRefusal(
            f"'{destination}' is on the constitution plane (contracts/ · docs/adr/ · golden/); "
            "apply.py refuses this write structurally, independent of any Claude hook."
        )


def refuse_if_outside_root(path: str | Path, root: str | Path) -> None:
    """Raise :class:`PathEscapeError` iff ``path`` does not resolve to ``root`` or a descendant.

    Resolved-path-based (``Path.resolve()``), not a string-prefix check — refuses both a direct
    out-of-root destination and a ``..``-traversal escape attempt. ADOPT-05 clause 1's structural
    control for discovery/draft-mode writes.
    """
    resolved_root = Path(root).resolve()
    resolved_path = Path(path).resolve()
    if resolved_path != resolved_root and resolved_root not in resolved_path.parents:
        raise PathEscapeError(
            f"'{path}' resolves outside the confined root '{root}' — refusing the write."
        )


def atomic_create(path: Path, payload: bytes) -> None:
    """Create ``path`` exactly once via durable temp + hard-link publication.

    Mirrors ``tools.task_control.manager._atomic_create``'s exact sequence, operating on raw
    ``bytes`` rather than a JSON-serializable dict. ``os.link`` raises ``FileExistsError`` on an
    existing target -> :class:`CollisionError`; ``os.replace`` (which silently overwrites) is never
    used here.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CollisionError(f"target already exists: {path}") from exc
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


def _atomic_replace(path: Path, payload: bytes) -> None:
    """Durably replace ``path`` with a same-directory temporary file.

    Mirrors ``tools.task_control.manager._atomic_replace``'s exact sequence, bytes-based. Only used
    by :func:`_apply_marker_merge`, where the target already exists by definition.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _apply_marker_merge(destination: str, target_path: Path, block_body: str = "") -> None:
    """Merge the harness-managed content into ``target_path`` and publish it atomically.

    ``.json`` destinations (``.claude/settings.json``) go through ``merge_settings``; every other
    marker-capable destination (``AGENTS.md``/``CLAUDE.md``) goes through ``splice_managed_block``
    with ``block_body`` as the fenced content. Both merge functions are already documented
    idempotent — a second call with the same input reproduces the same output byte-for-byte.
    """
    target_path = Path(target_path)
    if destination.endswith(".json"):
        existing: dict[str, Any] = (
            json.loads(target_path.read_text(encoding="utf-8")) if target_path.is_file() else {}
        )
        merged = merge_settings(existing)
        payload = (json.dumps(merged, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    else:
        existing_text = target_path.read_text(encoding="utf-8") if target_path.is_file() else ""
        merged_text = splice_managed_block(existing_text, block_body)
        payload = merged_text.encode("utf-8")
    _atomic_replace(target_path, payload)


def apply_disposition(
    record: dict[str, Any],
    target_root: str | Path,
    *,
    payload: bytes = b"",
    block_body: str = "",
) -> dict[str, str]:
    """Dispatch a single ``dispositionRecord`` to the correct writer, or refuse the write.

    ``refuse_if_constitution(destination)`` is called FIRST — before any branch, before any
    ``open()``/``os.link()``/``os.replace()`` call — so a constitution-plane destination is refused
    regardless of its disposition value. Returns ``{"destination", "disposition", "status"}`` where
    ``status`` is ``"applied"`` or ``"skipped"``. Raises on any refusal/error rather than returning
    a refused status — the caller (``apply_manifest``) decides which exceptions to bucket vs.
    propagate.
    """
    destination = record["destination"]
    disposition_value = record["disposition"]
    refuse_if_constitution(destination)

    if disposition_value not in DISPOSITION_ENUM:
        raise UnknownDispositionError(
            f"unknown disposition {disposition_value!r} for destination {destination!r}"
        )

    target_path = Path(target_root) / destination

    if disposition_value == "create":
        if target_path.exists():
            current_hash = _existing_hash(target_path)
            raise ConcurrentDriftError(
                f"concurrent target drift: '{destination}' now exists (sha256={current_hash}) but "
                "the manifest recorded no existing target for a 'create' disposition at draft time"
            )
        atomic_create(target_path, payload)
        return {"destination": destination, "disposition": disposition_value, "status": "applied"}

    if disposition_value == "marker-merge":
        if destination not in MARKER_CAPABLE:
            raise ValueError(
                f"'{destination}' is not marker-capable; the disposition manifest is malformed"
            )
        _apply_marker_merge(destination, target_path, block_body)
        return {"destination": destination, "disposition": disposition_value, "status": "applied"}

    # preserve / conflict / derived-regenerate / human-ratification-required: never written by
    # apply.py. human-ratification-required destinations are expected to already be refused above
    # (they live on the constitution plane by construction); this is a belt-and-suspenders no-op
    # for the case where one somehow is not.
    return {"destination": destination, "disposition": disposition_value, "status": "skipped"}


def apply_manifest(
    manifest: dict[str, Any],
    target_root: str | Path,
    *,
    payloads: dict[str, bytes] | None = None,
    block_bodies: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    """Apply every record in ``manifest["dispositions"]`` (never ``excluded[]``) against
    ``target_root``.

    Iterates ``dispositions[]`` ONLY, sorted by destination for deterministic output ordering.
    ``ConstitutionRefusal`` is caught per-record and bucketed into ``"refused"`` — a single refused
    destination does not abort the rest of the apply cycle. Every other exception
    (``ConcurrentDriftError``, ``UnknownDispositionError``, ``CollisionError``, a malformed
    marker-capable destination) propagates immediately — those are integrity faults, not routine
    per-destination outcomes.

    Returns ``{"applied": [...], "skipped": [...], "refused": [...]}`` — destinations only.
    """
    target_root = Path(target_root)
    payloads = payloads or {}
    block_bodies = block_bodies or {}
    summary: dict[str, list[str]] = {"applied": [], "skipped": [], "refused": []}

    for record in sorted(manifest["dispositions"], key=lambda r: r["destination"]):
        destination = record["destination"]
        try:
            result = apply_disposition(
                record,
                target_root,
                payload=payloads.get(destination, b""),
                block_body=block_bodies.get(destination, ""),
            )
        except ConstitutionRefusal:
            summary["refused"].append(destination)
            continue
        summary["applied" if result["status"] == "applied" else "skipped"].append(destination)

    return summary
