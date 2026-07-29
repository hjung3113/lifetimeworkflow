"""PIPE-04 INSTANCE topology gate (example leg) — proves the concrete 4-component overlay resolves.

This is the instance-plane twin of the core `test_pipeline_config.py` (PIPE-01), but it runs ONLY in
the example leg: the root pytest `testpaths` excludes `examples/`, so this file is invisible to the
core suite (`uv run pytest`) and runs only under `uv run pytest examples/log-parser/tests`. A
core-plane copy would name domain contracts and trip `test_core_no_example_dep.py` (GEN-04) — this
placement keeps the demonstration where domain vocabulary is allowed.

It loads the overlay `examples/log-parser/project.toml` path-locally (reusing the existing
`load_project(path=...)` signature — no new loader) and asserts the conductor-traceable flow:
every stage 1..4 binds a REAL component agent file + a declared instance language, and the 3 edges
are well-formed. The instance languages are read from the core `harness/project.toml` [[languages]]
slot (the active-instance slot) via the default `load_project()`.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import components, languages, load_project, pipeline
from tools.harness_lint import parse_frontmatter

# test_pipeline_topology.py -> tests -> log-parser (the instance root).
_EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
_OVERLAY = _EXAMPLE_ROOT / "project.toml"
_AGENTS_DIR = _EXAMPLE_ROOT / "agents"

_EXPECTED_IDS = ["parser", "converter", "scheduler", "collector"]


def _overlay() -> dict:
    """The instance topology overlay, loaded path-locally (reuse the load_project(path=) signature)."""
    return load_project(_OVERLAY)


def test_four_components_declared() -> None:
    """The overlay declares exactly the 4 pipeline components in linear stage order 1..4.

    ids == [parser, converter, scheduler, collector] and the stages are contiguous 1..4 — the
    concrete topology the conductor traces for this instance (PIPE-04).
    """
    comps = components(_overlay())
    assert [c["id"] for c in comps] == _EXPECTED_IDS, [c["id"] for c in comps]
    assert sorted(c["stage"] for c in comps) == [1, 2, 3, 4]


def test_each_component_binds_a_real_agent() -> None:
    """Every declared component binds a REAL instance agent file that parses to `mode: subagent`.

    This is the conductor-traceability proof: each stage resolves to a concrete component agent
    (`examples/log-parser/agents/<id>.md`), not a dangling reference (T-8-01 / T-8-06).
    """
    for comp in components(_overlay()):
        agent = _AGENTS_DIR / f"{comp['id']}.md"
        assert agent.is_file(), f"component {comp['id']!r}: no agent file at {agent}"
        fm, _ = parse_frontmatter(agent.read_text())
        assert fm.get("mode") == "subagent", (
            f"{agent}: mode is {fm.get('mode')!r}, expected subagent"
        )
        assert fm.get("name") == comp["id"], (
            f"{agent}: name {fm.get('name')!r} != component id {comp['id']!r}"
        )


def test_component_languages_declared() -> None:
    """Every component's `language` is one the instance declares in harness/project.toml [[languages]].

    The active-instance language slot (dotnet + python) lives in the core config; a component naming
    an undeclared toolchain is a topology the conductor cannot route — fail loud.
    """
    declared = {lang["id"] for lang in languages(load_project())}
    for comp in components(_overlay()):
        assert comp["language"] in declared, (
            f"component {comp['id']!r}: language {comp['language']!r} not in declared "
            f"instance languages {sorted(declared)}"
        )


def test_pipeline_edges_well_formed() -> None:
    """The 3 edges form the linear chain and each `contract` is exchanged by its endpoints.

    Mirrors the core `test_pipeline_edges_are_well_formed`: `from`/`to` name declared components and
    `contract` is BOTH in the from-component's `produces` AND the to-component's `consumes`.
    """
    cfg = _overlay()
    edges = pipeline(cfg).get("edges", [])
    assert len(edges) == 3, f"expected 3 edges, got {len(edges)}"
    by_id = {c["id"]: c for c in components(cfg)}
    for edge in edges:
        src, dst, contract = edge["from"], edge["to"], edge["contract"]
        assert src in by_id, f"edge {edge!r}: `from` {src!r} is not a declared component"
        assert dst in by_id, f"edge {edge!r}: `to` {dst!r} is not a declared component"
        assert contract in by_id[src].get("produces", []), (
            f"edge {edge!r}: contract {contract!r} not in {src!r}.produces "
            f"({by_id[src].get('produces', [])})"
        )
        assert contract in by_id[dst].get("consumes", []), (
            f"edge {edge!r}: contract {contract!r} not in {dst!r}.consumes "
            f"({by_id[dst].get('consumes', [])})"
        )


# The stage->agent resolution CONVENTION lives in the core (domain-neutral) docs; the concrete agents
# live in THIS instance. A drift between the two (core documents one filename pattern, the instance
# ships another) silently breaks stage->owner resolution — every stage reports "NO OWNING AGENT"
# while all gates stay green. This example-leg guard reads the core doc (example->core is the ALLOWED
# direction; GEN-04 only forbids core->example) and pins both sides to the `<id>.md` convention so
# future drift fails loud. Regression: gap surfaced by Phase-8 verification (08-05 documented
# `<id>-engineer.md` while 08-04 shipped `<id>.md`).
#
# Phase 44 (CER-08) deleted the `/pipeline` command and the `pipeline-map` skill this tuple used to
# name. The surviving core carrier of the convention is the neutral component-agent template, which
# each per-component agent in this instance is derived from — so it is the right doc to pin.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CORE_RESOLUTION_DOCS = (_REPO_ROOT / "harness" / "agents" / "templates" / "component-engineer.md",)


def test_core_resolution_convention_matches_instance_agents() -> None:
    """The core-documented stage->agent path convention resolves to this instance's real agents.

    Computes, per the `<id>.md` convention the core docs declare, the owning-agent path for every
    stage and asserts the file exists — the exact resolution a topology trace performs. Also asserts
    that the core doc no longer carries the stale `<id>-engineer.md` stage-resolution token, so
    reintroducing the mismatch fails here instead of silently producing an all-gaps trace.
    """
    for comp in components(_overlay()):
        owner = _AGENTS_DIR / f"{comp['id']}.md"  # the documented `<id>.md` convention
        assert owner.is_file(), (
            f"stage {comp['id']!r}: core `<id>.md` convention resolves to {owner}, which does not "
            f"exist — a topology trace would report NO OWNING AGENT (core-vs-instance naming drift)"
        )
    for doc in _CORE_RESOLUTION_DOCS:
        text = doc.read_text()
        assert "<id>.md" in text, (
            f"{doc}: core docs must document the `<id>.md` resolution convention"
        )
        assert "<id>-engineer.md" not in text, (
            f"{doc}: stale `<id>-engineer.md` stage-resolution token — the derived per-component "
            f"agent is `<id>.md` (the `-engineer` suffix names the template, not the agents)"
        )
