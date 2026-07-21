"""DOCSUP-05 — the stable grouped report and the pinned 0/1/3 exit mapping.

``python -m tools.docs_guard`` runs this. Phase 29's ``/docs-update`` binds to BOTH the exit codes
and the disposition vocabulary spelled below, so both are pinned here rather than discovered later:

===== ==================================================================================
 0     clean — no BROKEN, no STALE_REQUIRED, no failing coherence finding, uncovered
       within the ratchet. ``STALE_ADVISORY`` may be present, goes to STDERR, and does
       NOT change the code.
 1     BROKEN / STALE_REQUIRED / a failing coherence finding / an uncovered regression.
 3     the registry or ledger is INVALID. Distinct from 1 because the operator action is
       different: fix the registry, not the docs. A MISSING registry is 0 with zero
       bindings, never 3.
 2     argparse's stdlib usage error. NEVER produced deliberately.
===== ==================================================================================

Nothing else may escape that table. In particular the graph-impact computation — which reads the
live ``harness/project.toml`` and raises on a malformed or self-contradictory config — is run
inside :func:`main` behind a containment that degrades to an EMPTY impact map and says so on
stderr, rather than letting a config error out as a traceback and an undocumented code (WR-03).

Two things this report deliberately does NOT do:

**It never restates contract-drift or golden.** Those gates are LEADING and authoritative (D-13),
which the first line says out loud; a binding whose source is mid-drift renders as
``SUPPRESSED (contract-drift leading)`` and stops there. Restating their findings would give one
change two failures with two different remedies.

**It never suggests an in-place edit of an accepted ADR.** :data:`ADR_REMEDIATION` is the single
home for that rule, and it points at the ``/adr`` supersede path. ``contract_guard`` would deny the
write anyway, but a report that teaches the wrong action is itself the defect (D-09) —
``test_report_never_suggests_adr_edit`` asserts it across every reachable ADR state, not one sample.

Determinism: fixed column order, bindings sorted by id, findings sorted, impact ids sorted. No
wall-clock, no floating-point, no ``set`` iteration in output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.docs_guard.guard import DEFAULT_LEDGER_PATH, REPO_ROOT, classify
from tools.docs_guard.impact import impact_map
from tools.docs_guard.ledger import LedgerError
from tools.docs_guard.registry import DEFAULT_REGISTRY_PATH, RegistryError

__all__ = ["ADR_REMEDIATION", "DIFF_LABEL", "REMEDIATION", "main", "render"]

HEADER = (
    "docs-guard: contract-drift and golden are leading and authoritative — this gate reports "
    "human-doc review obligations only and never restates their findings."
)

# Rendered only when the reviewed digests can be compared against the working tree. DOCSUP-05's
# "diff only when retrievable from git": with no readable history the delta would be a guess, so
# the distinct `unverified-disposition` reason is shown in its place (D-08).
DIFF_LABEL = "digest delta"

_NO_IMPACT = "(none)"
_NO_ROW = "(no reviewed row)"
_PREFIX_LEN = 12

# THE single home for the append-only / supersede-don't-edit rule. One constant, so the rule cannot
# be spelled two ways in two branches and drift apart.
ADR_REMEDIATION = (
    "open obligation: author a NEW superseding ADR through the /adr command and the human "
    "constitution path, then re-disposition this binding. An accepted ADR is append-only — it is "
    "superseded, never revised."
)

# Three of these describe symptoms an operator could confuse ("the digests disagree") and carry
# three DIFFERENT fixes, so they are three DISTINCT lines and must stay that way. Collapsing them
# teaches the wrong fix, which for `first_seen-unratified` means re-recording a digest that is
# already correct instead of getting the row ratified.
REMEDIATION: dict[str, str] = {
    "stale-digest": (
        "review the target document against the changed sources, then re-record both digests in "
        "the ledger"
    ),
    "disposition-incoherent": (
        "the row claims 'updated' but the target document has not moved since the previous "
        "committed ledger — make the documentation change first, then re-record both digests"
    ),
    "first_seen-unratified": (
        "this binding has never been ratified: the human review commit that LANDS its [[reviewed]] "
        "row is the ratification. The digests are already correct — a binding cannot be blessed in "
        "the same change that introduces it"
    ),
    "unverified-disposition": (
        "the previous committed ledger could not be read, so the claim cannot be verified — this "
        "is a git history/checkout-depth problem, not a documentation problem"
    ),
    "superseding-adr-required": ADR_REMEDIATION,
    "unknown-binding": (
        "the ledger blesses a binding the registry does not declare — remove the row, or restore "
        "the binding it refers to"
    ),
    "broken-binding": (
        "the binding does not describe a reviewable pair: restore the missing file, fix the "
        "selector, or record the first [[reviewed]] row"
    ),
    "uncovered-regression": (
        "a human-authored document lost its coverage — add a binding for it, or have a human "
        "raise [coverage] uncovered_max deliberately. This gate never raises it"
    ),
    "binding-count-regression": (
        "a binding was removed below the committed floor — restore it, or have a human lower "
        "[coverage] binding_min deliberately. This gate never lowers it"
    ),
}

_STDERR_STATES = frozenset({"STALE_ADVISORY"})
_STDERR_LEVELS = frozenset({"warn", "note"})


def _prefix(digest: str | None) -> str:
    return digest[:_PREFIX_LEN] if digest else "-"


def _binding_block(entry: dict, impact: list[str]) -> list[str]:
    """One stable block per binding, columns in the FIXED DOCSUP-05 order.

    changed source path + hash prefix -> graph impact ids -> target doc -> severity -> required
    disposition. The order is part of the contract: Phase 29's ``/docs-update`` reads these blocks,
    and a reordering would be a silent format break.
    """
    state = entry["state"]
    if state == "SUPPRESSED":
        state = "SUPPRESSED (contract-drift leading)"

    sources = ", ".join(entry["sources"]) or "(no sources)"
    lines = [
        f"  [{state}] {entry['id']}",
        f"    sources      : {sources}@{_prefix(entry['live_source_digest'])}",
        f"    impact       : {', '.join(impact) if impact else _NO_IMPACT}",
        f"    target       : {entry['target']}@{_prefix(entry['live_target_digest'])}",
        f"    severity     : {entry['severity']}",
        f"    dispositions : {', '.join(entry['dispositions'])}",
        f"    reviewed     : {entry['disposition'] or _NO_ROW}",
    ]

    reasons = list(entry["reasons"])
    if entry["disposition"] and "unverified-disposition" not in reasons:
        lines.append(
            f"    {DIFF_LABEL}: source {_prefix(entry['source_digest'])} -> "
            f"{_prefix(entry['live_source_digest'])}; target "
            f"{_prefix(entry['target_digest'])} -> {_prefix(entry['live_target_digest'])}"
        )
    for reason in reasons:
        lines.append(f"    reason       : {reason}")
        remediation = REMEDIATION.get(reason)
        if remediation:
            lines.append(f"    remediation  : {remediation}")
    if entry["disposition"] == "SUPERSEDING_ADR_REQUIRED":
        lines.append(f"    remediation  : {ADR_REMEDIATION}")
    return lines


def render(result: dict, impact: dict[str, list[str]] | None = None) -> tuple[list[str], list[str]]:
    """Render ``result`` into ``(stdout_lines, stderr_lines)``.

    ``impact`` maps a binding id to its graph impact ids; when omitted it is computed from the
    bindings in ONE ``impact_map`` call. Passing it explicitly is the hermetic seam the report tests
    use. A binding absent from the map reports no impact ids — the same NEVER-FABRICATE answer
    ``impact_map`` gives for a binding whose sources resolve to nothing.

    Advisory blocks and warn/note findings go to STDERR so they are visible without changing what a
    CI step's stdout diff shows; failures and the summary go to STDOUT.
    """
    out: list[str] = [HEADER, ""]
    err: list[str] = []

    if impact is None:
        impact = impact_map(result["bindings"])

    for entry in result["bindings"]:
        ids = impact.get(entry["id"], [])
        block = _binding_block(entry, ids)
        (err if entry["state"] in _STDERR_STATES else out).extend([*block, ""])

    for finding in result["findings"]:
        line = f"  {finding['level']}: {finding['message']}"
        remediation = REMEDIATION.get(finding["reason"])
        block = [line] + ([f"    remediation  : {remediation}"] if remediation else [])
        (err if finding["level"] in _STDERR_LEVELS else out).extend(block)

    uncovered = result["uncovered"]
    limit = "no ratchet" if uncovered["max"] is None else f"uncovered_max = {uncovered['max']}"
    out.append("")
    out.append(
        f"docs-guard: {len(result['bindings'])} binding(s); "
        f"{uncovered['live']} uncovered human-authored document(s) ({limit})."
    )
    out.append(f"docs-guard: {'OK' if result['ok'] else 'FAILED'}")
    return out, err


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.docs_guard",
        description=(
            "DOCSUP-03/05 human-doc review obligation gate. Exit 0 clean, 1 broken/stale-required/"
            "uncovered-regression, 3 registry-or-ledger invalid."
        ),
    )
    # Explicit paths (D-14, the load_project(path=...) seam) so an instance-local overlay is
    # possible later; only the core registry ships in Phase 28.
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)

    try:
        result = classify(
            registry_path=Path(args.registry),
            ledger_path=Path(args.ledger),
            root=Path(args.root),
        )
    except (RegistryError, LedgerError) as error:
        # A clean one-line diagnostic, never a traceback: exit 3 is a DOCUMENTED failure mode, and
        # a traceback here would be an undocumented one. The message names the offending id or key
        # only — registry.py/ledger.py already guarantee they never echo file CONTENT, since a
        # hostile registry may carry arbitrary bytes (T-28-30).
        print(f"docs-guard: registry/ledger invalid — {error}", file=sys.stderr)
        return 3

    # The graph impact is computed HERE, not inside `render`, and its failure is contained: both
    # `effective_relationships(None)` and `compile_graph(None)` read the live `harness/project.toml`
    # and raise on a malformed or self-contradictory config (one contract claimed by two
    # authorities). Left inside `render` that raise escaped `main` as a traceback and an
    # UNDOCUMENTED exit code — the exact failure mode the exit table above forbids. Degrading to an
    # EMPTY impact map is the already-established correct answer (`impact.py`'s NEVER FABRICATE
    # posture): an unmappable impact set is empty, never invented. The degradation is STATED on
    # stderr, never silent — a report that quietly drops a column teaches the wrong confidence.
    try:
        impact = impact_map(result["bindings"])
    except Exception as error:  # noqa: BLE001 — same posture as guard.py's drift-gate degradation
        impact = {entry["id"]: [] for entry in result["bindings"]}
        print(
            f"docs-guard: graph impact unavailable, reporting no impact ids — {error}",
            file=sys.stderr,
        )

    out, err = render(result, impact)
    for line in out:
        print(line)
    for line in err:
        print(line, file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
