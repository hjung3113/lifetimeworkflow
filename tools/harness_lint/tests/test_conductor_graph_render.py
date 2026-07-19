"""TOPO-06 conductor-render gate — the CONCRETE proof artifact for two claims.

1. **Linear-render byte-identity (research Pitfall 1 / Assumption A2).** The existing linear
   render text in ``harness/commands/pipeline.md`` — the two-stage ``stage N: ... consumes=...
   produces=...`` block and the ``from -> to (contract)`` edge line — MUST stay byte-identical
   after Plan 03 generalizes the conductor. These prose command files carry no runnable render
   function today, so the falsifiable proof is a hardcoded literal-string assertion against the
   exact shipped example lines: any future edit that rewrites them fails this test loudly.
2. **The D-01 non-linear addition is actually present** — both ``pipeline.md`` and
   ``pipeline-map/SKILL.md`` gained a graph/indented-tree/cycle-marker render section.

Plus the anti-sprawl invariants: ``orchestrator.md`` stays the ONE ``mode: primary`` persona named
``orchestrator`` (no second primary), and the persona set is UNCHANGED — ``EXPECTED_PERSONAS`` is
imported (never re-hardcoded) so this gate tracks the single source.

Parsing is delegated to the shared ``parse_frontmatter`` (no hand-sliced ``---`` fences). Kept
domain-neutral (generic ``source``/``sink`` ids only) so the GEN-04 core-plane guard stays green.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint import parse_frontmatter
from tools.harness_lint.caps import EXPECTED_PERSONAS

# test_conductor_graph_render.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PIPELINE_CMD = _REPO_ROOT / "harness" / "commands" / "pipeline.md"
_PIPELINE_MAP = _REPO_ROOT / "harness" / "skills" / "pipeline-map" / "SKILL.md"
_ORCHESTRATOR = _REPO_ROOT / "harness" / "agents" / "orchestrator.md"

# The exact linear-case example lines that shipped before Plan 03 — the byte-identity anchors.
_LINEAR_STAGE_LINES = (
    "stage 1: source (python) consumes=[] produces=[greeting]",
    "stage 2: sink (python) consumes=[greeting] produces=[]",
)
_LINEAR_EDGE_LINE = "source -> sink (greeting)"


def test_linear_stage_block_is_byte_identical() -> None:
    """The two-stage linear render lines are present verbatim (TOPO-06 byte-identity anchor)."""
    text = _PIPELINE_CMD.read_text(encoding="utf-8")
    for line in _LINEAR_STAGE_LINES:
        assert line in text, (
            f"linear stage-render line drifted — expected exact text {line!r} in pipeline.md"
        )


def test_linear_edge_line_is_byte_identical() -> None:
    """The linear edge-chain render line is present verbatim (second byte-identity anchor)."""
    text = _PIPELINE_CMD.read_text(encoding="utf-8")
    assert _LINEAR_EDGE_LINE in text, (
        f"linear edge-render line drifted — expected exact text {_LINEAR_EDGE_LINE!r} in pipeline.md"
    )


def test_both_surfaces_carry_the_d01_nonlinear_render() -> None:
    """pipeline.md AND pipeline-map/SKILL.md gained the cycle + indent/tree render addition."""
    for path in (_PIPELINE_CMD, _PIPELINE_MAP):
        lowered = path.read_text(encoding="utf-8").lower()
        assert "cycle" in lowered, f"{path.name} is missing the D-01 cycle-marker mention"
        assert ("indent" in lowered) or ("tree" in lowered), (
            f"{path.name} is missing the D-01 indented-tree render mention"
        )


def test_orchestrator_stays_single_primary_named_orchestrator() -> None:
    """No second primary introduced — orchestrator stays name=='orchestrator', mode=='primary'."""
    fm, _ = parse_frontmatter(_ORCHESTRATOR.read_text(encoding="utf-8"))
    assert fm.get("name") == "orchestrator", (
        f"conductor must stay named 'orchestrator', got {fm.get('name')!r}"
    )
    assert fm.get("mode") == "primary", (
        f"conductor must stay mode:primary (no second primary), got {fm.get('mode')!r}"
    )


def test_persona_set_unchanged() -> None:
    """The persona set is UNCHANGED — every EXPECTED_PERSONA file exists, no new one added."""
    agents_dir = _REPO_ROOT / "harness" / "agents"
    on_disk = {p.stem for p in agents_dir.glob("*.md")}
    assert on_disk == set(EXPECTED_PERSONAS), (
        f"persona set drifted — on disk {sorted(on_disk)} vs expected {sorted(EXPECTED_PERSONAS)}"
    )
