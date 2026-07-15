"""ECON-03 structural gate — pins the delegate-vs-inline heuristic at BOTH integration points.

Plan 10-02 authored the ``context-budget`` skill (the delegate-vs-inline heuristic) and surfaced it,
alongside the ``fan-out-synthesize`` substrate, at the two named seams where the routing decision
becomes observable and repeatable:

- the primary ``orchestrator`` — routing table + a named delegate-vs-inline intake step;
- the ``/orient`` onboarding command — read-order step 4.

This gate keeps that wiring from silently regressing: both the ``context-budget`` token and a
fan-out token must appear in each seam's body. Parsing is delegated to the shared
``parse_frontmatter`` — no hand-sliced ``---`` fences. Kept domain-neutral (no instance-overlay path
or domain-contract tokens) so the GEN-04 core-plane guard stays green.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint import parse_frontmatter

# test_context_budget_wiring.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ORCHESTRATOR = _REPO_ROOT / "harness" / "agents" / "orchestrator.md"
_ORIENT = _REPO_ROOT / "harness" / "commands" / "orient.md"
_SKILL = _REPO_ROOT / "harness" / "skills" / "context-budget" / "SKILL.md"


def _body(path: Path) -> str:
    _, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return body.lower()


def test_context_budget_skill_exists() -> None:
    """The heuristic lives in its own skill (D-10 — not buried in orchestrator prose)."""
    assert _SKILL.is_file(), "harness/skills/context-budget/SKILL.md is missing"
    fm, _ = parse_frontmatter(_SKILL.read_text(encoding="utf-8"))
    assert fm.get("name") == "context-budget", (
        f"context-budget skill must be named 'context-budget', got {fm.get('name')!r}"
    )


def test_orchestrator_wires_the_heuristic() -> None:
    """Orchestrator body references context-budget AND a fan-out token (routing + intake)."""
    body = _body(_ORCHESTRATOR)
    assert "context-budget" in body, "orchestrator.md does not reference the context-budget skill"
    assert "fan-out" in body, "orchestrator.md does not surface the fan-out-synthesize skill"


def test_orient_wires_the_heuristic() -> None:
    """/orient read-order surfaces context-budget AND a fan-out token."""
    body = _body(_ORIENT)
    assert "context-budget" in body, "orient.md read-order does not list the context-budget skill"
    assert "fan-out" in body, "orient.md read-order does not list the fan-out-synthesize skill"
