"""PIPE-02 structural gate — pins the conductor's topology-routing signal.

The primary ``orchestrator`` was evolved (Plan 08-02) into a topology-aware conductor: it reads
the declared ``[[components]]`` / ``[pipeline]`` slot and routes by pipeline stage/component, not
only by language. This gate keeps that evolution from silently regressing:

- it stays the ONE ``mode: primary`` persona named ``orchestrator`` (no second primary);
- its intake carries a "Trace the topology" step and the ``topology`` token;
- its routing section keys on stage/component (or the component role words).

Parsing is delegated to the shared ``parse_frontmatter`` — no hand-sliced ``---`` fences. Kept
domain-neutral (no instance-overlay path or domain-contract tokens) so the GEN-04 core-plane guard stays green.
"""

from __future__ import annotations

import re

from pathlib import Path

from tools.harness_lint import parse_frontmatter

# test_orchestrator_topology.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ORCHESTRATOR = _REPO_ROOT / "harness" / "agents" / "orchestrator.md"

# The five subsection headers every route carries, in this fixed order (Phase 49 plan-checker
# warning 2 — a prose-fidelity claim alone is not a check; this asserts the STRUCTURE).
_ROUTE_SUBSECTIONS = (
    "When to use",
    "Steps",
    "Repository evidence",
    "Stop condition",
    "Next command",
)

_ROUTE_HEADER_RE = re.compile(r"^## Route: (?P<name>\S+)", re.MULTILINE)


def _read() -> tuple[dict, str]:
    fm, body = parse_frontmatter(_ORCHESTRATOR.read_text(encoding="utf-8"))
    return fm, body


def _route_bodies(body: str) -> dict[str, str]:
    """Split ``body`` into ``{route_name: route_section_text}`` at each ``## Route: <name>`` header."""
    matches = list(_ROUTE_HEADER_RE.finditer(body))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[m.group("name")] = body[start:end]
    return sections


def test_orchestrator_stays_single_primary() -> None:
    """The conductor IS the evolved orchestrator — one primary named ``orchestrator``."""
    fm, _ = _read()
    assert fm.get("name") == "orchestrator", (
        f"conductor must stay named 'orchestrator', got {fm.get('name')!r}"
    )
    assert fm.get("mode") == "primary", (
        f"conductor must stay mode:primary (no second primary), got {fm.get('mode')!r}"
    )


def test_conductor_has_topology_intake() -> None:
    """Intake carries a 'Trace the topology' step and the ``topology`` routing token."""
    _, body = _read()
    lowered = body.lower()
    assert "trace the topology" in lowered, (
        "orchestrator.md intake is missing the 'Trace the topology' step"
    )
    assert "topology" in lowered, "orchestrator.md body does not mention 'topology'"


def test_conductor_routes_by_stage_component() -> None:
    """Routing mentions both stage and component (or role words) AND references ``/pipeline``."""
    _, body = _read()
    lowered = body.lower()
    assert "stage" in lowered, "routing does not mention pipeline 'stage'"
    _COMPONENT_TOKENS = ("component", "parser", "converter", "scheduler", "collector")
    assert any(tok in lowered for tok in _COMPONENT_TOKENS), (
        f"routing does not mention a component dimension ({_COMPONENT_TOKENS})"
    )


def test_every_route_carries_all_five_subsections_in_order() -> None:
    """Every ``## Route:`` section carries all five subsection headers, in the fixed order.

    Phase 49 plan-checker warning 2: prose fidelity alone ("the route still talks about the same
    things") is not a check — this asserts the actual header sequence per route, so a future edit
    that drops or reorders a subsection (e.g. the contract-change route's Repository evidence
    rewrite) fails loudly instead of silently.
    """
    _, body = _read()
    sections = _route_bodies(body)
    assert sections, "no '## Route: <name>' sections found in orchestrator.md"

    for name, text in sections.items():
        positions = [text.find(f"**{h}**") for h in _ROUTE_SUBSECTIONS]
        missing = [h for h, pos in zip(_ROUTE_SUBSECTIONS, positions) if pos == -1]
        assert not missing, f"route {name!r} is missing subsection(s): {missing}"
        assert positions == sorted(positions), (
            f"route {name!r} has its five subsections out of order: "
            f"{list(zip(_ROUTE_SUBSECTIONS, positions))}"
        )
