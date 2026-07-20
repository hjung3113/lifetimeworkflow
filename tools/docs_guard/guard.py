"""DOCSUP-03 five-state classifier — the plan that turns three read-only modules into a GATE.

``classify()`` returns a ``run_gate``-shaped result dict (mirroring
``tools/contract_drift/drift.py:177-216``) and decides nothing about process exit; ``cli.py`` owns
the 0/1/3 mapping. Phase 29's ``/docs-update`` binds to BOTH this state vocabulary and those exit
codes, so both are pinned here rather than discovered later.

Three properties are load-bearing and each has its own adversarial row in ``tests/test_guard.py``,
shown RED against a deliberately-wrong classifier before this module landed:

**1. FIRST-MATCH-WINS with ``BROKEN`` ordered before every staleness check (D-05).** A missing
target or a selector expanding to zero paths must never be reported as merely stale — the operator
would go re-record a digest for a document that does not exist. The order below is NUMBERED in
comments precisely so a future editor cannot reorder it by accident.

**2. Digest equality is NECESSARY but NOT SUFFICIENT for ``FRESH``.** ``FRESH`` additionally
requires an EMPTY blocking-finding set for that binding id. Without the second half this module
would re-open the self-blessing hole ``ledger.py`` just closed: an agent-authored brand-new binding
plus a ``reviewed-no-change`` row carrying that binding's exact live digests is consistent by
construction, and a digest-equality-only rule reports it green. ``first_seen-unratified`` is
therefore consumed here, not merely emitted upstream.

**3. Both ratchets are READ-ONLY (D-06).** This module contains no filesystem write of any kind.
Raising ``uncovered_max`` or ``binding_min`` is a HUMAN edit — a gate that can lower its own
threshold is self-blessing, which is the "machines gate, humans ratify" non-negotiable. The guard
PRINTS ``ratchet can tighten: ...`` and never applies it.

Contract-drift and golden stay LEADING and authoritative (D-13). ``run_gate()`` is read ONCE per
classify for the SUPPRESSION decision only, and its findings are never carried into this result —
otherwise every contract change would fail twice with two different remedies.

Determinism: no wall-clock, no calendar, no floating-point, and no ``set`` iteration reaching
output — every returned sequence is explicitly sorted.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from tools.adoption_scan.destinations import DERIVED_GLOBS
from tools.docs_guard.digest import MissingSourceError, compute, resolve
from tools.docs_guard.ledger import (
    LEDGER_PATH,
    LEVEL_FAIL,
    REASON_FIRST_SEEN,
    REASON_INCOHERENT,
    REASON_OPEN_OBLIGATION,
    REASON_STALE,
    REASON_UNKNOWN_BINDING,
    REASON_UNVERIFIED,
    Finding,
    ReviewedRow,
    check_coherence,
    load_ledger,
    previous_document,
    previous_ledger,
)
from tools.docs_guard.registry import (
    DEFAULT_REGISTRY_PATH,
    Binding,
    identity_digest,
    identity_digests,
    load_registry,
)
from tools.harness_emit.manifest import is_gsd_owned
from tools.harness_perms import resolve_path

# guard.py -> docs_guard -> tools -> repo root (parents[2]). Resolved from ``__file__``, never the
# CWD — same posture as registry.py.
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER_PATH = REPO_ROOT / LEDGER_PATH

# The registry's repo-relative spelling, the ``LEDGER_PATH`` twin. Used ONLY as the fallback when an
# explicit ``--registry`` resolves outside the root, so nothing caller-influenced reaches the git
# argv (T-28-20). Derived from the module constant rather than retyped.
REGISTRY_PATH = DEFAULT_REGISTRY_PATH.relative_to(REPO_ROOT).as_posix()

# The five DOCSUP-03 states plus ``SUPPRESSED`` (D-13). ``UNCOVERED`` is a per-DOCUMENT state, not
# a binding state — it lives in ``result["uncovered"]``, never in a binding entry.
STATES: tuple[str, ...] = (
    "BROKEN",
    "SUPPRESSED",
    "FRESH",
    "STALE_REQUIRED",
    "STALE_ADVISORY",
    "UNCOVERED",
)

# ── D-07: the human-authored corpus. THIS CONSTANT SETS THE RATCHET'S MEANING. ─────────────────
# Do not edit it without deliberately moving `uncovered_max` in the same change: widening it
# silently reds the gate, narrowing it silently blesses whatever was removed. It is stated here as
# a module constant, not inferred inside a loop, so the ratchet's denominator is reviewable.
#
# MINUS `DERIVED_GLOBS` (imported, never retyped — destinations.py is its single authoritative
# home), minus the GSD-owned lane, minus the instance tree (GEN-04). Derived and GSD-owned trees
# have their own generators and owners; counting them would either double-report or make the
# ratchet meaningless.
HUMAN_CORPUS: tuple[str, ...] = (
    "docs/tutorials/**/*",
    "docs/how-to/**/*",
    "docs/explanation/**/*",
    "docs/glossary.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".memory/README.md",
)

# `.planning` is the GSD-owned lane and the second entry is the instance tree (GEN-04). Neither is
# reachable through HUMAN_CORPUS's patterns today; the structural skip is belt-and-suspenders so a
# future pattern addition can never silently pull one in. Both are named as bare top-level segments
# rather than as globs, because a core-plane file may not carry an instance path token.
_EXCLUDED_TOP_LEVEL: frozenset[str] = frozenset({".planning", "examples"})

# Guard-level reason constants. Kept greppable and distinct from ledger.py's, because they carry a
# different remedy: a ratchet finding is fixed in the ledger, a staleness finding in the docs.
REASON_UNCOVERED_REGRESSION = "uncovered-regression"
REASON_UNCOVERED_TIGHTEN = "uncovered-can-tighten"
REASON_BROKEN = "broken-binding"

# A binding carrying ANY of these may not be FRESH, no matter how well its digests agree. This set
# IS the self-green closure — see property 2 in the module docstring. `first_seen-unratified` is
# the row that closes plan 28-04's hole; `unverified-disposition` and `disposition-incoherent` are
# the other two reasons `check_coherence` can emit that mean "this claim has not been established".
BLOCKING_REASONS: frozenset[str] = frozenset(
    {
        REASON_INCOHERENT,
        REASON_FIRST_SEEN,
        REASON_UNVERIFIED,
        REASON_OPEN_OBLIGATION,
        REASON_UNKNOWN_BINDING,
    }
)

# The ONLY reasons drift suppression may demote. `stale-digest` is the one finding that is
# genuinely DOWNSTREAM of contract drift — the source moved, so of course the reviewed digest no
# longer matches, and reporting that here would give one change two remedies (D-13).
#
# Everything in BLOCKING_REASONS is deliberately ABSENT. Those findings are about WHO RATIFIED
# WHAT, not about whether a source moved: `first_seen-unratified` says nobody has ever ratified
# this binding, `disposition-incoherent` says the claim contradicts history,
# `unverified-disposition` says the claim cannot be checked at all, `unknown-binding` says the row
# blesses something that does not exist, and `superseding-adr-required` is an open obligation. A
# drifted source has no bearing on any of them, and demoting them let a brand-new self-blessed
# binding report ok=True merely because one of its sources happened to be mid-drift — a PERMANENT
# escape, because the commit that would have failed is the commit that lands the row into history.
SUPPRESSIBLE_REASONS: frozenset[str] = frozenset({REASON_STALE})

__all__ = ["BLOCKING_REASONS", "HUMAN_CORPUS", "STATES", "SUPPRESSIBLE_REASONS", "classify"]


# ── corpus enumeration (P6 / Phase 26 CR-01) ──────────────────────────────────────────────────


def _tracked_files(root: Path) -> frozenset[str] | None:
    """Repo-relative POSIX paths ``git`` considers tracked at ``root``, or ``None`` when unknown.

    GIT-TRACKED-ONLY is the rule: an untracked working-tree file must not move the uncovered count,
    or CI's clean checkout disagrees with a developer's tree — the exact reproducibility defect
    Phase 26's CR-01 fixed. The failure-tolerant degradation (git binary missing, or the invocation
    failing, both yield ``None`` -> unfiltered enumeration rather than an exception) is copied from
    ``tools/adoption_scan/destinations.py:205-225``; a gate must not become unrunnable because git
    is absent.
    """
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True,
            check=False,
            shell=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return frozenset(completed.stdout.decode("utf-8", "surrogateescape").splitlines())


def human_corpus(root: Path) -> list[str]:
    """The sorted, git-tracked, repo-relative human-authored corpus at ``root`` (D-07)."""
    tracked = _tracked_files(root)
    found: set[str] = set()
    for pattern in HUMAN_CORPUS:
        for candidate in root.glob(pattern):
            if not candidate.is_file():
                continue
            rel = candidate.relative_to(root).as_posix()
            if rel.split("/", 1)[0] in _EXCLUDED_TOP_LEVEL:
                continue
            if is_gsd_owned(rel):
                continue
            if resolve_path(DERIVED_GLOBS, rel) == "deny":
                continue
            if tracked is not None and rel not in tracked:
                continue
            found.add(rel)
    return sorted(found)


# ── per-binding digests ───────────────────────────────────────────────────────────────────────


def _binding_digests(binding: Binding, root: Path) -> tuple[str, str, list[str]]:
    """Return ``(source_digest, target_digest, broken_reasons)`` for one binding.

    A selector expanding to ZERO paths is recorded as a broken reason even though ``compute([])``
    yields a perfectly well-formed digest — consistency is not coverage, and that digest would
    otherwise match a ledger row forever (``broken_zero_expansion``). ``MissingSourceError`` maps to
    a broken reason too: an absent file is never hashed as empty, or a BROKEN binding would be
    indistinguishable from a FRESH one.
    """
    reasons: list[str] = []

    try:
        source_paths = resolve(binding.sources, root)
    except ValueError as error:
        return "", "", [f"source selector could not be resolved: {error}"]
    if binding.sources and not source_paths:
        reasons.append(
            f"source selector(s) {list(binding.sources)} expand to zero paths — "
            f"the binding watches nothing"
        )

    try:
        source_digest = compute(source_paths, root)
    except MissingSourceError as error:
        source_digest = ""
        reasons.append(f"source is missing: {error}")

    try:
        target_digest = compute(resolve([binding.target], root), root)
    except MissingSourceError:
        target_digest = ""
        reasons.append(f"target document is missing: {binding.target}")
    except ValueError as error:
        target_digest = ""
        reasons.append(f"target could not be resolved: {error}")

    return source_digest, target_digest, reasons


# ── suppression (D-13) ────────────────────────────────────────────────────────────────────────


def _default_drift_gate() -> dict:
    """The real ``contract_drift.run_gate``, degrading to "nothing drifted" if it cannot run.

    Imported lazily: ``run_gate`` rebuilds the whole contract manifest, and importing it at module
    scope would make every consumer of this package pay for it.
    """
    try:
        from tools.contract_drift.drift import run_gate

        return run_gate()
    except Exception:  # noqa: BLE001 — drift is the LEADING gate; its failure is reported there
        return {"ok": True, "drifted": []}


def _drifted_paths(gate_result: dict) -> frozenset[str]:
    """The repo-relative paths ``run_gate`` reports as drifted — and NOTHING else from its result.

    Only the path half of each ``(rel, kind, classification)`` tuple crosses this boundary. The
    kind and the breaking/non-breaking classification stay behind on purpose: contract-drift is the
    LEADING, authoritative gate for them, and restating its findings here is the double-report
    DOCSUP-05 forbids (``drift_findings_not_restated``).
    """
    return frozenset(str(entry[0]) for entry in gate_result.get("drifted", ()) if entry)


# ── the classifier ────────────────────────────────────────────────────────────────────────────


def _finding_dict(finding: Finding) -> dict:
    return {
        "binding_id": finding.binding_id,
        "reason": finding.reason,
        "level": finding.level,
        "message": finding.message,
    }


def _sorted_findings(findings: Iterable[dict]) -> list[dict]:
    return sorted(findings, key=lambda f: (f["binding_id"], f["reason"], f["message"]))


def _previous_rel(path: Path, root: Path, fallback: str) -> str:
    """``path``'s repo-relative spelling, for ``git show HEAD:./<rel>``.

    Derived by ``relative_to(root)``, which by construction can only produce a path INSIDE the
    root — an explicit ``--ledger`` / ``--registry`` outside the tree falls back to the module
    constant rather than reaching the git argv (T-28-20's posture: nothing attacker-influenced in
    the command line).
    """
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return fallback


def classify(
    *,
    registry_path: str | Path,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    root: str | Path = REPO_ROOT,
    drift_gate: Callable[[], dict] | None = None,
) -> dict:
    """Classify every registry binding and enforce both read-only ratchets.

    Returns ``{"ok", "bindings", "uncovered", "coverage", "findings"}``. ``ok`` is False iff any
    ``BROKEN``, any ``STALE_REQUIRED``, any fail-level coherence finding, an uncovered regression,
    or a binding-count regression exists. ``STALE_ADVISORY`` and warn/note-level findings NEVER
    flip it.

    Every path argument is EXPLICIT (D-14, the ``load_project(path=...)`` seam) so an instance-local
    overlay is possible later. ``drift_gate`` is the D-13 suppression input, injectable so tests
    are hermetic; it is called EXACTLY ONCE per classify, never once per binding.

    Writes nothing. See property 3 in the module docstring.
    """
    root_path = Path(root).resolve()
    ledger = Path(ledger_path)

    bindings: Sequence[Binding] = load_registry(registry_path, root_path)
    coverage, rows = load_ledger(ledger)
    rows_by_id: dict[str, ReviewedRow] = {row.id: row for row in rows}
    previous = previous_ledger(_previous_rel(ledger, root_path, LEDGER_PATH), root_path)

    # A ratification is a statement about a binding's MEANING, so establishing it needs the
    # previous committed REGISTRY as well as the previous committed ledger. Without this the
    # history test keyed on the binding NAME alone, and repointing an already-ratified id at a
    # different source/target pair inherited its ratification silently (CR-03). `previous is None`
    # (history unreadable) yields an EMPTY repointed set — the same degrade-to-no-check posture
    # every other history-dependent rule in this package takes.
    previous_registry = previous_document(
        _previous_rel(Path(registry_path), root_path, REGISTRY_PATH), root_path
    )
    committed_identity = identity_digests(previous_registry)
    repointed_ids = (
        frozenset()
        if previous_registry is None
        else frozenset(
            binding.id
            for binding in bindings
            if committed_identity.get(binding.id)
            != identity_digest(binding.sources, binding.target)
        )
    )

    live_digests: dict[str, tuple[str, str]] = {}
    broken_reasons: dict[str, list[str]] = {}
    for binding in bindings:
        source_digest, target_digest, reasons = _binding_digests(binding, root_path)
        live_digests[binding.id] = (source_digest, target_digest)
        broken_reasons[binding.id] = reasons

    coherence = check_coherence(
        rows,
        previous,
        live_digests,
        {binding.id: binding.severity for binding in bindings},
        repointed_ids,
    )
    blocking_by_id: dict[str, list[str]] = {}
    for finding in coherence:
        if finding.reason in BLOCKING_REASONS:
            blocking_by_id.setdefault(finding.binding_id, []).append(finding.reason)

    # ONE call per classify (D-13). `run_gate` is a full manifest rebuild; per-binding invocation
    # would make this gate's cost scale with the registry.
    drifted = _drifted_paths((drift_gate or _default_drift_gate)())

    entries: list[dict] = []
    findings: list[dict] = [_finding_dict(finding) for finding in coherence]
    ok = True

    for binding in bindings:
        row = rows_by_id.get(binding.id)
        source_digest, target_digest = live_digests[binding.id]
        reasons = list(broken_reasons[binding.id])
        stale_state = "STALE_REQUIRED" if binding.severity == "required" else "STALE_ADVISORY"

        # ── FIRST-MATCH-WINS. The numbers are the ORDER. Do not reorder them. ──────────────────
        # 1. BROKEN — a missing target, a zero-expansion selector, or a `required` binding with no
        #    [[reviewed]] row at all. Ordered FIRST so a broken binding is never reported as merely
        #    stale (`broken_beats_stale`, `broken_zero_expansion`).
        if binding.severity == "required" and row is None:
            reasons.append(
                f"binding {binding.id} is required but has no [[reviewed]] row in the ledger"
            )
        if reasons:
            state = "BROKEN"
            findings.append(
                {
                    "binding_id": binding.id,
                    "reason": REASON_BROKEN,
                    "level": LEVEL_FAIL,
                    "message": f"{REASON_BROKEN}: binding {binding.id}: " + "; ".join(reasons),
                }
            )
        # 2. SUPPRESSED — a source is a contract currently reported drifted. Contract-drift is the
        #    LEADING gate; this binding's staleness is its downstream consequence, not a second
        #    independent defect with a second remedy (D-13). The second half of the condition is
        #    load-bearing and must not be simplified away: a binding carrying a blocking coherence
        #    finding has an UNESTABLISHED ratification claim, which drift neither causes nor
        #    excuses. Without it, evaluating drift before the FRESH guard means a self-blessed
        #    binding never reaches the self-green closure at step 3 at all.
        elif _sources_drifted(binding, root_path, drifted) and not blocking_by_id.get(binding.id):
            state = "SUPPRESSED"
            reasons.append("contract-drift leading")
        # 3. FRESH — digest equality is NECESSARY but NOT SUFFICIENT. An open ADR obligation and
        #    any blocking coherence finding (notably `first_seen-unratified`) both deny green even
        #    when the digests agree exactly. This is the whole content of the self-green closure;
        #    it is written as an explicit guard, never as an afterthought.
        elif (
            row is not None
            and (row.source_digest, row.target_digest) == (source_digest, target_digest)
            and row.disposition != "SUPERSEDING_ADR_REQUIRED"
            and not blocking_by_id.get(binding.id)
        ):
            state = "FRESH"
        # 4. STALE_REQUIRED / STALE_ADVISORY, by severity. The terminal branch: a binding that
        #    reached here either has a digest that moved, or has matching digests and an
        #    unsatisfied precondition from step 3 (the reasons list says which).
        else:
            state = stale_state
            reasons.extend(sorted(blocking_by_id.get(binding.id, [])))
            if row is None:
                reasons.append("no [[reviewed]] row in the ledger")
            elif (row.source_digest, row.target_digest) != (source_digest, target_digest):
                reasons.append("reviewed digests no longer match the working tree")

        if state == "BROKEN" or state == "STALE_REQUIRED":
            ok = False

        entries.append(
            {
                "id": binding.id,
                "state": state,
                "severity": binding.severity,
                "target": binding.target,
                "sources": list(binding.sources),
                "dispositions": list(binding.dispositions),
                "disposition": row.disposition if row is not None else None,
                "source_digest": row.source_digest if row is not None else None,
                "target_digest": row.target_digest if row is not None else None,
                "live_source_digest": source_digest,
                "live_target_digest": target_digest,
                "reasons": reasons,
            }
        )

    # D-13, second half: a suppressed binding must not contribute to exit 1, and that has to hold
    # for its STALENESS findings too — `stale-digest` for a binding whose contract is mid-drift is
    # the downstream consequence of the leading gate's failure, not a second independent defect.
    # The finding is kept (the operator still sees why the binding is suppressed) but demoted to a
    # note, so exactly one gate reports the change: contract-drift.
    #
    # The demotion is RESTRICTED to `SUPPRESSIBLE_REASONS`. Demoting every fail-level finding for a
    # suppressed binding also demoted the ratification-authority reasons, which turned drift into a
    # laundering channel for a self-blessed row (see SUPPRESSIBLE_REASONS above). Together with the
    # `not blocking_by_id` half of the SUPPRESSED branch this is belt-and-braces: neither the state
    # nor the level can be reached by a binding whose ratification has never been established.
    suppressed_ids = {entry["id"] for entry in entries if entry["state"] == "SUPPRESSED"}
    for finding in findings:
        if (
            finding["binding_id"] in suppressed_ids
            and finding["level"] == LEVEL_FAIL
            and finding["reason"] in SUPPRESSIBLE_REASONS
        ):
            finding["level"] = "note"
            finding["message"] += " (suppressed — contract-drift leading)"

    # ── the uncovered ratchet (read-only) ──────────────────────────────────────────────────────
    covered = {binding.target for binding in bindings}
    uncovered = [path for path in human_corpus(root_path) if path not in covered]
    # The ENFORCED ceiling is the PREVIOUS COMMITTED one, symmetric with `binding_min`
    # (`ledger.py:435-439`): reading it from the working tree would let the same uncommitted edit
    # that drops a document out of coverage also raise the bar it is about to breach. The
    # working-tree value is used ONLY when there is no committed ledger to read — with no history
    # there is no committed ceiling at all, so honouring the working-tree one can only ADD a
    # constraint, never relax one (WR-01).
    previous_coverage = (previous or {}).get("coverage")
    committed_max = (
        previous_coverage.get("uncovered_max") if isinstance(previous_coverage, dict) else None
    )
    uncovered_max = (
        committed_max
        if isinstance(committed_max, int) and not isinstance(committed_max, bool)
        else coverage.get("uncovered_max")
    )
    if uncovered_max is not None:
        if len(uncovered) > uncovered_max:
            ok = False
            findings.append(
                {
                    "binding_id": "",
                    "reason": REASON_UNCOVERED_REGRESSION,
                    "level": LEVEL_FAIL,
                    "message": (
                        f"{REASON_UNCOVERED_REGRESSION}: {len(uncovered)} uncovered "
                        f"human-authored document(s) but the committed ratchet allows at most "
                        f"uncovered_max = {uncovered_max}"
                    ),
                }
            )
        elif len(uncovered) < uncovered_max:
            # SUGGESTED, never applied — the guard prints the tightening and a human lands it.
            findings.append(
                {
                    "binding_id": "",
                    "reason": REASON_UNCOVERED_TIGHTEN,
                    "level": "note",
                    "message": f"ratchet can tighten: set uncovered_max = {len(uncovered)}",
                }
            )

    # The `binding_min` count ratchet is NOT evaluated here: `ledger.check_coherence` already
    # evaluates it against the PREVIOUS COMMITTED ledger, which is the authoritative threshold
    # (28-04) — reading it from the working tree would let the same edit that deletes a binding
    # also lower the bar. `uncovered_max` above is read the SAME way for the same reason; the two
    # ratchets are symmetric. Its findings are folded above; re-deriving it here would double-
    # report.
    # It is NOT redundant with the uncovered ratchet: a binding whose target lies outside
    # HUMAN_CORPUS can be deleted without moving the uncovered count by a single unit, so that
    # deletion would otherwise be entirely unguarded (`binding_deleted_outside_corpus`).
    if any(finding["level"] == LEVEL_FAIL for finding in findings):
        ok = False

    return {
        "ok": ok,
        "bindings": sorted(entries, key=lambda entry: entry["id"]),
        "uncovered": {"live": len(uncovered), "max": uncovered_max, "paths": uncovered},
        "coverage": {
            "uncovered_max": coverage.get("uncovered_max"),
            "binding_min": coverage.get("binding_min"),
        },
        "findings": _sorted_findings(findings),
    }


def _sources_drifted(binding: Binding, root: Path, drifted: frozenset[str]) -> bool:
    """True iff any of ``binding``'s sources is a currently-drifted contract path.

    Both the raw selector and each resolved path are checked: a binding may name the schema
    literally (the common case) or reach it through a glob.
    """
    if not drifted:
        return False
    if any(selector in drifted for selector in binding.sources):
        return True
    try:
        resolved = resolve(binding.sources, root)
    except ValueError:
        return False
    return any(path.relative_to(root).as_posix() in drifted for path in resolved)
