---
phase: 08-pipeline-topology-conductor-per-component-agents
plan: 04
subsystem: instance-pipeline-topology
tags: [pipeline-topology, instance-overlay, component-agents, PIPE-04, example-leg, GEN-04]
requires:
  - harness/project.toml [[components]]/[pipeline] generic slot + [[languages]] (PIPE-01, GEN-03)
  - tools/harness_config loader load_project(path=) / components() / pipeline() / languages()
  - harness/agents/templates/component-engineer.md (PIPE-03 fill-in-the-blanks persona)
  - examples/log-parser/agents/dotnet-engineer.md (per-instance persona idiom)
  - examples/log-parser/tests/conftest.py (example-leg sys.path wiring)
provides:
  - "examples/log-parser/project.toml — concrete 4-component instance topology overlay (parser→converter→scheduler→collector)"
  - "4 per-stage instance component agents (parser/converter/scheduler/collector), subagent-mode least-privilege"
  - "examples/log-parser/tests/test_pipeline_topology.py — instance topology gate (example leg only)"
affects:
  - "Demonstrates the neutral-core mechanism (08-01/02/03/05) end-to-end on a real 4-component pipeline"
  - "conductor /pipeline trace can resolve the full 4-stage instance flow to real agent files"
tech-stack:
  added: []
  patterns:
    - "Instance overlay = [[components]]+[pipeline] under examples/, loaded path-locally via load_project(path=); core [instance] root stays generic"
    - "Instantiate component-engineer template into per-stage instance personas; name==component.id, bash allow == its language toolchain only"
    - "Instance-plane gate lives under examples/tests (off root testpaths) → runs in example leg only, invisible to core suite (no GEN-04 trip)"
key-files:
  created:
    - examples/log-parser/project.toml
    - examples/log-parser/agents/parser.md
    - examples/log-parser/agents/converter.md
    - examples/log-parser/agents/scheduler.md
    - examples/log-parser/agents/collector.md
    - examples/log-parser/tests/test_pipeline_topology.py
  modified: []
decisions:
  - "Overlay reuses real domain contract names (standard-log, equipment-progress) — legal because GEN-04 never scans examples/; the scheduler→collector edge reuses equipment-progress (scheduler batches it through)"
  - "Agent name == topology component.id (parser/converter/scheduler/collector), NOT <id>-engineer — per plan Task 2; keeps stage→agent resolution a plain id lookup"
  - "Instance topology gate reads instance languages from the CORE harness/project.toml [[languages]] via default load_project(), while loading the topology from the example overlay path-locally"
metrics:
  duration: 10min
  tasks: 3
  files: 6
  completed: 2026-07-10
---

# Phase 08 Plan 04: Instance Pipeline-Topology Overlay + 4 Component Agents + Instance Gate Summary

PIPE-04 — the concrete demonstration that the neutral-core pipeline mechanism (PIPE-01 topology slot,
PIPE-02 conductor, PIPE-03 component-engineer template) works on a real 4-component pipeline: an
`examples/log-parser/project.toml` overlay declaring the linear
`parser(1,.NET)→converter(2,.NET)→scheduler(3,py)→collector(4,py)` topology with real domain-contract
edges, four per-stage least-privilege component agents instantiated from the template, and an
instance topology gate that runs only in the example leg.

## What Was Built

**Task 1 — instance topology overlay (`1228d95`)**
- New `examples/log-parser/project.toml`: four `[[components]]` (`parser` stage 1 / `converter`
  stage 2, both `language="dotnet"`; `scheduler` stage 3 / `collector` stage 4, both
  `language="python"`) with real edge-contract labels, plus a `[pipeline]` table with the 3 linear
  edges (`parser→converter` `standard-log`; `converter→scheduler` `equipment-progress`;
  `scheduler→collector` `equipment-progress`). Each edge `contract` is in the upstream `produces` AND
  the downstream `consumes`. Names its own `[instance] root = "examples/log-parser"`; the core
  `harness/project.toml` `[instance] root` stays `""` (unchanged). Real domain names are legal here —
  GEN-04 never scans `examples/`.

**Task 2 — 4 component agents (`be58db3`)**
- `examples/log-parser/agents/{parser,converter,scheduler,collector}.md`, each an instantiation of
  `harness/agents/templates/component-engineer.md`: `mode: subagent`, `name` == its `component.id`,
  `tools: Read, Edit, Bash, Grep, Glob`, and least-privilege `permission.bash` — `parser`/`converter`
  allow `"dotnet *"`, `scheduler`/`collector` allow `"uv *"`, everything else `"*": ask`. Each
  `description` carries a stage-keyed `use`/`when` routing trigger naming its `consumes`/`produces`
  edge contracts; bodies close with the per-package `AGENTS.md`-first pointer (T-8-01 mitigation).

**Task 3 — instance topology gate (`18084fd`)**
- New `examples/log-parser/tests/test_pipeline_topology.py`: loads the overlay path-locally via
  `load_project(_EXAMPLE_ROOT / "project.toml")`. Four assertions —
  `test_four_components_declared` (ids == `[parser, converter, scheduler, collector]`, stages 1..4),
  `test_each_component_binds_a_real_agent` (a `agents/<id>.md` exists per component and parses to
  `mode: subagent` with `name == id`), `test_component_languages_declared` (each `component.language`
  ∈ the core `[[languages]]`), `test_pipeline_edges_well_formed` (3 edges, contract ∈ upstream
  produces ∩ downstream consumes). Lives under `examples/tests` (off root `testpaths`), so it runs
  ONLY in the example leg — invisible to the core suite, no GEN-04 trip (T-8-06 mitigation).

## Verification

- `uv run pytest examples/log-parser/tests/test_pipeline_topology.py -q` → **4 passed**.
- `uv run pytest examples/log-parser/tests -q` → **9 passed, 2 skipped** (the 2 skips are the expected
  `.NET` egress-blocked golden-spawn cases — not failures).
- `uv run pytest` (full non-example core suite) → **439 passed, 3 snapshots passed** — this new file
  is NOT collected by the root suite (confirming the off-`testpaths` placement).
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` → **18 passed** (GEN-04
  green — no core file was edited; `harness/project.toml [instance] root` still `""`).

## Deviations from Plan

None - plan executed exactly as written.

## must_haves Truth Check

- `examples/log-parser/project.toml` declares the concrete 4-component topology
  (`parser→converter→scheduler→collector`) with real edge contracts — YES.
- Four instance component agents exist, each subagent-mode least-privilege bound to its stage — YES.
- The instance topology gate (example leg) proves each component binds a real agent file + real
  language and edges are well-formed — YES (`test_pipeline_topology.py`, 4 passed).
- The conductor can trace the full `parser→converter→scheduler→collector` flow from the instance
  overlay — YES (every stage resolves to a real component-agent file via the gate).

## Threat Register Check

- T-8-01 (Elevation of Privilege) — mitigated: each agent's bash allow is exactly its language
  toolchain (`dotnet *` / `uv *`), everything else `ask`; the gate asserts `mode: subagent`.
- T-8-02 (Tampering / boundary erosion) — mitigated: domain names confined to `examples/`; GEN-04
  guard re-run green, core `[instance] root` unchanged.
- T-8-06 (invisible instance breakage) — mitigated: gate placed under `examples/log-parser/tests/`;
  both `uv run pytest` and `uv run pytest examples/log-parser/tests` run and are green.
- T-8-SC (supply chain) — N/A: zero package installs this phase.

## Anti-Sprawl

The 4 new agents are INSTANCE-owned (`examples/log-parser/agents/`) — invisible to the core
`EXPECTED_PERSONAS` set (which globs `harness/agents/*.md` only), so `EXPECTED_PERSONAS` stays 4. The
new test module is not enumerated by any `EXPECTED_*` artifact set. No pinned-set update required.

## Known Stubs

None — the overlay, agents, and gate are concrete and fully wired (the gate proves every stage
resolves to a real agent file + declared language + well-formed edge).

## Self-Check: PASSED

- FOUND: examples/log-parser/project.toml
- FOUND: examples/log-parser/agents/parser.md
- FOUND: examples/log-parser/agents/converter.md
- FOUND: examples/log-parser/agents/scheduler.md
- FOUND: examples/log-parser/agents/collector.md
- FOUND: examples/log-parser/tests/test_pipeline_topology.py
- FOUND commit 1228d95 (Task 1)
- FOUND commit be58db3 (Task 2)
- FOUND commit 18084fd (Task 3)
