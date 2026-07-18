"""Deterministic lane-specific task phase transition table."""

from __future__ import annotations

PHASES = frozenset(
    {
        "INTAKE",
        "CLARIFY",
        "SPEC",
        "PLAN",
        "EXECUTE",
        "REVIEW",
        "VERIFY",
        "COMPLETE",
        "BLOCKED",
    }
)

_FAST = {
    ("INTAKE", "EXECUTE"),
    ("EXECUTE", "VERIFY"),
    ("VERIFY", "COMPLETE"),
}

# STANDARD may omit CLARIFY, SPEC, PLAN, and REVIEW, but never moves backward.
_STANDARD = {
    (source, target)
    for index, source in enumerate(("INTAKE", "CLARIFY", "SPEC", "PLAN"))
    for target in ("CLARIFY", "SPEC", "PLAN", "EXECUTE")[index:]
    if source != target
} | {
    ("EXECUTE", "REVIEW"),
    ("EXECUTE", "VERIFY"),
    ("REVIEW", "VERIFY"),
    ("VERIFY", "COMPLETE"),
}

_STRICT = {
    ("INTAKE", "CLARIFY"),
    ("CLARIFY", "SPEC"),
    ("SPEC", "PLAN"),
    ("PLAN", "EXECUTE"),
    ("EXECUTE", "REVIEW"),
    ("REVIEW", "VERIFY"),
    ("VERIFY", "COMPLETE"),
}


def _with_blocked(edges: set[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Add explicit blocking and resume edges without allowing COMPLETE to reopen."""
    active = {phase for edge in edges for phase in edge if phase != "COMPLETE"}
    return frozenset(
        edges | {(phase, "BLOCKED") for phase in active} | {("BLOCKED", phase) for phase in active}
    )


ALLOWED_TRANSITIONS = {
    "FAST": _with_blocked(_FAST),
    "STANDARD": _with_blocked(_STANDARD),
    "STRICT": _with_blocked(_STRICT),
    # CONTROLLED uses the STRICT order. Human approvals, dry-runs, and rollback evidence are
    # represented by packet artifacts; enforcement belongs to the Phase 20 transition gate.
    "CONTROLLED": _with_blocked(_STRICT),
}


def is_transition_allowed(lane: str, source: str, target: str) -> bool:
    """Return False for unknown lanes, phases, and non-edges."""
    if source not in PHASES or target not in PHASES:
        return False
    return (source, target) in ALLOWED_TRANSITIONS.get(lane, frozenset())
