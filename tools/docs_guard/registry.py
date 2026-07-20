"""DOCSUP-01 loader + validator for ``docs/doc-dependencies.toml`` — the review-obligation registry.

**This module is the registry's ONLY validator (D-16 / A7).** ``/contract-check`` step 1 pairs each
``<name>.schema.json`` with a sibling ``.yaml``/``.yml``/``.json`` instance (``ci.yml:108-127``);
the registry instance is ``.toml`` and lives under ``docs/``, so CI silently SKIPS it. Nobody may
assume double validation — if a rejection is not implemented here, it is not implemented anywhere.
That is why every rule below has an adversarial row in ``tests/test_registry.py`` that was shown
RED against a shape-only validator before it landed.

Two halves, in a load-bearing ORDER:

1. SHAPE — ``contracts/harness/docs/doc-dependencies.schema.json`` (constitution plane, hash-gated).
   All ``iter_errors()`` are emitted at once, sorted by ``json_path``.
2. SEMANTICS — the five DOCSUP-01 rejections the schema provably cannot express (they need
   cross-row uniqueness, a live filesystem, and glob-set membership): path escape, duplicate id,
   empty selector on a ``required`` row, a derived/generated ``target``, and the accepted-ADR edit
   policy (D-09).

A sixth rejection — control characters and the markdown table separator in a selector — IS
expressible in the schema and is stated there as a ``pattern``. It is restated here, and ordered
BEFORE the shape pass, only so the operator sees a named-character message instead of a printed
regex: the reason a path may not contain a newline (a forged row in the derived queue, and an
inflated SessionStart count) is not recoverable from the regex.

Determinism: every diagnostic list is ``sorted()`` before it reaches a message — a gate whose
message ordering varies across runs is not reviewable (``tools/harness_config/loader.py:149-160``).

Purity: ``load_registry`` performs read-only filesystem access and writes nothing. No CLI here —
plan 28-05 owns ``cli.py``.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from jsonschema import Draft202012Validator

from tools.adoption_apply.apply import PathEscapeError, refuse_if_outside_root
from tools.adoption_scan.destinations import DERIVED_GLOBS
from tools.harness_perms import resolve_path
from tools.hooks.contract_guard import CONSTITUTION_GLOBS

# registry.py -> docs_guard -> tools -> repo root (parents[2]). Resolved from ``__file__``, never
# from the CWD: locating the constitution-plane schema by CWD would let an invocation from an
# arbitrary directory silently pick up a different (or no) schema — T-28-15's bypass.
REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "contracts" / "harness" / "docs" / "doc-dependencies.schema.json"
DEFAULT_REGISTRY_PATH = REPO_ROOT / "docs" / "doc-dependencies.toml"

# The two upper-case dispositions are ADR-track ONLY, and a docs/adr/** target is FORCED to exactly
# this pair (D-09): SUPERSEDING_ADR_REQUIRED is an open obligation that can never make a binding
# green, and `updated` would have the report teach an in-place edit of an append-only document.
# A subset, a superset, and `updated` in any position all reject.
ADR_DISPOSITIONS: frozenset[str] = frozenset({"REVIEWED_STILL_CURRENT", "SUPERSEDING_ADR_REQUIRED"})

# Sliced out of the IMPORTED constitution globs rather than retyped, so the ADR test cannot drift
# from tools/hooks/contract_guard.py's plane definition.
ADR_GLOBS: list[str] = [glob for glob in CONSTITUTION_GLOBS if glob.startswith("docs/adr/")]

__all__ = [
    "ADR_DISPOSITIONS",
    "ADR_GLOBS",
    "DEFAULT_REGISTRY_PATH",
    "DERIVED_GLOBS",
    "Binding",
    "RegistryError",
    "identity_digest",
    "identity_digests",
    "load_registry",
]


def identity_digest(sources: Iterable[str], target: str) -> str:
    """A digest over a binding's MEANING — its sorted source selectors and its target.

    This hashes SELECTORS, never file content: it answers "what is this binding ABOUT", the
    question a ledger row's ratification is actually a statement about. Content lives in the
    ``source_digest`` / ``target_digest`` pair and moves on every ordinary edit; the identity moves
    only when someone repoints the binding.

    Each field is prefixed with its own label and ``\\n``-terminated, so ``sources=["a"],
    target="b"`` and ``sources=["b"], target="a"`` cannot collide. Sources are sorted, so a pure
    reordering of the selector list is correctly NOT a repoint.
    """
    hasher = hashlib.sha256()
    for selector in sorted(sources):
        hasher.update(b"source\n")
        hasher.update(selector.encode("utf-8"))
        hasher.update(b"\n")
    hasher.update(b"target\n")
    hasher.update(target.encode("utf-8"))
    hasher.update(b"\n")
    return hasher.hexdigest()


def identity_digests(document: dict | None) -> dict[str, str]:
    """Index a PARSED registry document by binding id -> :func:`identity_digest`.

    Deliberately LENIENT, mirroring ``ledger._previous_rows``: the caller feeds this the PREVIOUS
    COMMITTED registry, which is history that already passed the gate once. Re-validating it here
    would let a historical shape change fail a present-day review, so a malformed row is simply not
    indexed rather than raising.
    """
    if document is None:
        return {}
    block = document.get("binding", [])
    if not isinstance(block, list):
        return {}
    indexed: dict[str, str] = {}
    for entry in block:
        if not isinstance(entry, dict):
            continue
        rid, sources, target = entry.get("id"), entry.get("sources"), entry.get("target")
        if not isinstance(rid, str) or not isinstance(target, str) or not isinstance(sources, list):
            continue
        if not all(isinstance(selector, str) for selector in sources):
            continue
        indexed[rid] = identity_digest(sources, target)
    return indexed


class Binding(NamedTuple):
    """One validated ``[[binding]]`` row.

    A NamedTuple rather than the raw dict so downstream plans (28-05's CLI, 28-06's classifier) get
    attribute access and a field set that cannot silently grow a key.
    """

    id: str
    sources: tuple[str, ...]
    target: str
    severity: str
    dispositions: tuple[str, ...]


class RegistryError(ValueError):
    """The registry is INVALID (plan 28-05 maps this to exit 3 — distinct from a stale binding).

    Carries the full sorted diagnostic list, joined into one message: a gate that reports only the
    first of five problems costs the operator five round trips. Names the offending id/path ONLY,
    never file content — a hostile registry may carry arbitrary bytes (T-28-14).
    """


def _fail(reason: str, diagnostics: list[str]) -> None:
    """Raise with a deterministically sorted diagnostic list (see the module docstring)."""
    raise RegistryError(f"{reason}: " + "; ".join(sorted(diagnostics)))


def _reject_structural_escape(selector: str, label: str) -> str | None:
    """Return a diagnostic iff ``selector`` is an absolute spelling or has a literal ``..`` SEGMENT.

    The PRIMARY control, and it runs BEFORE any ``Path.resolve()`` or filesystem call — the shape
    copied from ``tools/adoption_apply/apply.py:109-125``. Segment-wise, never substring: a file
    legitimately named ``a..b.py`` must stay valid, and a ``".." in selector`` test would
    over-refuse it (that row is in ``VALID_CASES``).
    """
    normalized = selector.replace("\\", "/")
    segments = normalized.split("/")
    if normalized.startswith("/") or (len(selector) > 1 and selector[1] == ":"):
        return f"{label} is an absolute path: {selector!r}"
    if ".." in segments:
        return f"{label} contains a '..' path segment: {selector!r}"
    return None


def _reject_forbidden_characters(selector: str, label: str) -> str | None:
    """Return a diagnostic iff ``selector`` carries a control character or the table separator.

    The schema expresses the same rule as a ``pattern``, and that is the primary control. This is
    restated here for the operator-facing MESSAGE: a raw jsonschema ``pattern`` failure prints the
    regex, which teaches nothing about why a path may not contain a newline. The reason is
    concrete — the registry is agent-writable by design (DOCSUP-07), and these values are
    interpolated into the derived staleness queue's markdown table, whose row count the SessionStart
    pointer reports, so a TOML multi-line basic string could forge queue rows and inflate that
    count.

    The offending character is reported by NAME, never echoed: a hostile registry may carry
    arbitrary bytes and this diagnostic reaches the gate's output (T-28-14).
    """
    for char in selector:
        if char == "|":
            return f"{label} contains a forbidden character: '|' (markdown table separator)"
        if ord(char) < 0x20 or ord(char) == 0x7F:
            return f"{label} contains a forbidden control character: U+{ord(char):04X}"
    return None


def _adr_status(target_path: Path) -> str | None:
    """Return the ADR's ``- **Status:**`` value, or ``None`` when absent/unreadable.

    Tolerates a missing file: an unreadable status is treated as not-accepted by the caller, which
    is the fail-closed direction.
    """
    try:
        text = target_path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- **Status:**"):
            return stripped.removeprefix("- **Status:**").strip().lower()
    return None


def load_registry(
    path: str | Path = DEFAULT_REGISTRY_PATH, root: str | Path = REPO_ROOT
) -> list[Binding]:
    """Load, validate, and return the registry's bindings sorted by ``id``.

    ``path`` is EXPLICIT (D-14, the ``load_project(path=...)`` seam) so an instance-local overlay is
    possible later; only the core registry ships in Phase 28.

    A MISSING registry file is NOT an error — it yields zero bindings, so plans 28-05/28-06 can land
    before plan 28-07's seed data. Missing != invalid; only invalid maps to exit 3.
    """
    path = Path(path)
    root_path = Path(root).resolve()

    # ── 1. Parse ────────────────────────────────────────────────────────────────────────────────
    if not path.exists():
        return []
    try:
        with path.open("rb") as handle:
            document = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        # Never a raw traceback out of a gate (T-28-14). The decoder's message carries a line/column
        # and the offending token only, not the file body.
        raise RegistryError(f"registry is not valid TOML: {path.name}: {error}") from error

    # ── 2. FORBIDDEN CHARACTERS — ordered BEFORE the schema on purpose ─────────────────────────
    # The schema carries the same rule as a ``pattern``, but a raw jsonschema pattern failure prints
    # the REGEX, which teaches nothing about why a path may not contain a newline. Running the
    # named-character scan first means the operator sees the actionable message; the schema remains
    # the primary, machine-checkable statement of the constraint (WR-02). Access is defensive
    # because shape has not been validated yet — a malformed row is left for step 3 to report.
    forbidden: list[str] = []
    for row in document.get("binding", []) if isinstance(document.get("binding"), list) else []:
        if not isinstance(row, dict):
            continue
        rid = row.get("id")
        label_id = rid if isinstance(rid, str) else "<unnamed>"
        selectors = row.get("sources")
        if isinstance(selectors, list):
            for index, selector in enumerate(selectors):
                if not isinstance(selector, str):
                    continue
                found = _reject_forbidden_characters(
                    selector, f"binding {label_id!r} sources[{index}]"
                )
                if found:
                    forbidden.append(found)
        target = row.get("target")
        if isinstance(target, str):
            found = _reject_forbidden_characters(target, f"binding {label_id!r} target")
            if found:
                forbidden.append(found)
    if forbidden:
        _fail("registry forbidden character", forbidden)

    # ── 3. SHAPE — the constitution-plane schema, ALL errors at once ────────────────────────────
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    shape_errors = Draft202012Validator(schema).iter_errors(document)
    diagnostics = sorted(f"{error.json_path}: {error.message}" for error in shape_errors)
    if diagnostics:
        raise RegistryError("registry shape is invalid: " + "; ".join(diagnostics))

    rows: list[dict] = list(document.get("binding", []))

    # ── 3. STRUCTURAL path escape — BEFORE any filesystem call ─────────────────────────────────
    escapes: list[str] = []
    for row in rows:
        for index, selector in enumerate(row["sources"]):
            found = _reject_structural_escape(selector, f"binding {row['id']!r} sources[{index}]")
            if found:
                escapes.append(found)
        found = _reject_structural_escape(row["target"], f"binding {row['id']!r} target")
        if found:
            escapes.append(found)
    if escapes:
        _fail("registry path escape", escapes)

    # ── 4. RESOLVE-THEN-CONFINE backstop (catches the symlink escape) ───────────────────────────
    # ``refuse_unsafe_destination`` is deliberately NOT reused here: it ALSO refuses
    # ``contracts/**`` as a constitution-plane write, but a contract schema is a legitimate registry
    # SOURCE (that row is in ``VALID_CASES``). The narrow ``refuse_if_outside_root`` is the right
    # control — confinement only, no plane classification. Do not "unify" these two call sites.
    for row in rows:
        for index, selector in enumerate(row["sources"]):
            try:
                refuse_if_outside_root(root_path / selector, root_path)
            except PathEscapeError:
                escapes.append(
                    f"binding {row['id']!r} sources[{index}] resolves outside the repo root: "
                    f"{selector!r}"
                )
        try:
            refuse_if_outside_root(root_path / row["target"], root_path)
        except PathEscapeError:
            escapes.append(
                f"binding {row['id']!r} target resolves outside the repo root: {row['target']!r}"
            )
    if escapes:
        _fail("registry path escape", escapes)

    # ── 5. DUPLICATE ID — the deterministic sorted diagnostic (loader.py:149-160) ───────────────
    id_seen: set[str] = set()
    dup_ids: set[str] = set()
    for row in rows:
        rid = row["id"]
        if rid in id_seen:
            dup_ids.add(rid)
        id_seen.add(rid)
    if dup_ids:
        raise RegistryError("registry duplicate binding id(s): " + ", ".join(sorted(dup_ids)))

    # ── 6/7/8. Per-row semantics ───────────────────────────────────────────────────────────────
    empty_required: list[str] = []
    derived_targets: list[str] = []
    adr_pair: list[str] = []
    adr_proposed: list[str] = []
    adr_vocabulary: list[str] = []

    for row in rows:
        rid = row["id"]
        target = row["target"]
        dispositions = set(row["dispositions"])

        # 6 — empty selector, CONDITIONAL on severity. An `advisory` row with no sources stays
        # valid, which is exactly why the schema omits `minItems` (plan 28-01).
        if row["severity"] == "required" and not row["sources"]:
            empty_required.append(f"binding {rid!r} is required but selects no sources")

        # 7 — a derived/generated target would make a machine-regenerated artifact look
        # human-reviewed (T-28-12). Matched against the IMPORTED catalog with the repo's existing
        # glob resolver (the one `contract_guard._on_constitution_plane` uses) — no new matcher, and
        # DERIVED_GLOBS is never retyped: destinations.py is its single authoritative home.
        if resolve_path(DERIVED_GLOBS, target) == "deny":
            derived_targets.append(f"binding {rid!r} names the derived target {target!r}")

        # 8 — the accepted-ADR edit policy (D-09).
        if resolve_path(ADR_GLOBS, target) == "deny":
            if dispositions != set(ADR_DISPOSITIONS):
                adr_pair.append(
                    f"binding {rid!r} targets an ADR and must declare exactly "
                    f"{sorted(ADR_DISPOSITIONS)}, not {sorted(dispositions)}"
                )
            if _adr_status(root_path / target) != "accepted":
                adr_proposed.append(
                    f"binding {rid!r} targets {target!r}, which is not an accepted ADR "
                    "(a mid-ratification document's content is expected to change)"
                )
        elif dispositions & ADR_DISPOSITIONS:
            # Keep the vocabulary structurally partitioned, so Phase 29's /docs-update filter can
            # split ADR-track from ordinary rows on the disposition alone.
            adr_vocabulary.append(
                f"binding {rid!r} targets {target!r} and may not declare the ADR-only "
                f"disposition(s) {sorted(dispositions & ADR_DISPOSITIONS)}"
            )

    if empty_required:
        _fail("registry empty sources on a required binding", empty_required)
    if derived_targets:
        _fail("registry derived target", derived_targets)
    if adr_pair:
        _fail("registry accepted-ADR disposition pair", adr_pair)
    if adr_proposed:
        _fail("registry target is not an accepted ADR", adr_proposed)
    if adr_vocabulary:
        _fail("registry ADR-only disposition on a non-ADR target", adr_vocabulary)

    return sorted(
        (
            Binding(
                id=row["id"],
                sources=tuple(row["sources"]),
                target=row["target"],
                severity=row["severity"],
                dispositions=tuple(row["dispositions"]),
            )
            for row in rows
        ),
        key=lambda binding: binding.id,
    )
