"""PIPE-02 structural gate — pins the conductor's topology-routing signal.

The primary ``orchestrator`` was evolved (Plan 08-02) into a topology-aware conductor: it reads
the declared ``[[components]]`` / ``[pipeline]`` slot and routes by pipeline stage/component, not
only by language. This gate keeps that evolution from silently regressing:

- it stays the ONE ``mode: primary`` persona named ``orchestrator`` (no second primary);
- its intake carries a "Trace the topology" step and the ``topology`` token;
- its routing section keys on stage/component (or the component role words) and references ``/pipeline``.

Parsing is delegated to the shared ``parse_frontmatter`` — no hand-sliced ``---`` fences. Kept
domain-neutral (no ``examples/`` / domain-contract tokens) so the GEN-04 core→example guard stays green.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint import parse_frontmatter

# test_orchestrator_topology.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ORCHESTRATOR = _REPO_ROOT / "harness" / "agents" / "orchestrator.md"


def _read() -> tuple[dict, str]:
    fm, body = parse_frontmatter(_ORCHESTRATOR.read_text(encoding="utf-8"))
    return fm, body


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
    assert "/pipeline" in lowered, "routing does not reference the /pipeline entry command"
