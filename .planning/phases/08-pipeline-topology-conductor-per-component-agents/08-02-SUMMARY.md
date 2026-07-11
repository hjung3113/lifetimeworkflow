---
phase: 08-pipeline-topology-conductor-per-component-agents
plan: 02
subsystem: harness-agents
tags: [conductor, topology-routing, orchestrator, anti-sprawl, PIPE-02, GEN-04]
requires:
  - "08-01 topology slot: tools.harness_config components()/pipeline() + [[components]]/[pipeline]"
  - "harness/agents/orchestrator.md existing mode:primary persona"
provides:
  - "Topology-aware conductor: orchestrator routes by pipeline stage/component (not only language)"
  - "'Trace the topology' intake step referencing tools.harness_config"
  - "Stage/component routing rows + /pipeline entry in the decision table"
  - "test_orchestrator_topology.py structural gate pinning the routing signal"
affects:
  - "Plan 08-04 (instance overlay declares concrete component engineers the conductor routes to)"
tech-stack:
  added: []
  patterns:
    - "Evolve-in-place: the conductor IS the existing primary orchestrator, no second primary"
    - "Structural gate reads agent frontmatter via shared parse_frontmatter (no fence slicing)"
key-files:
  created:
    - tools/harness_lint/tests/test_orchestrator_topology.py
  modified:
    - harness/agents/orchestrator.md
    - tools/harness_lint/tests/test_pipeline_config.py
decisions:
  - "Conductor evolved in place — EXPECTED_PERSONAS stays exactly 4 (no conductor.md, no second primary)"
  - "Routing keys on both dimensions: language boundary AND pipeline stage/component, resolving owner from topology first then falling back to the language engineer"
metrics:
  duration: 9min
  tasks: 2
  files: 3
  completed: 2026-07-10
---

# Phase 08 Plan 02: Topology-Aware Conductor Summary

Evolved the existing primary `orchestrator` persona IN PLACE into a topology-aware conductor: it
now reads the declared `[[components]]`/`[pipeline]` slot (Plan 01) and routes by pipeline
stage/component, not only by language — with a new "Trace the topology" intake step, stage/component
routing rows, a `/pipeline` entry, and a structural gate that pins the signal. It stays the SINGLE
`mode: primary` persona; EXPECTED_PERSONAS is unchanged at 4.

## What Was Built

**Task 1 — evolve orchestrator into the conductor (`9f88082`)**
- `harness/agents/orchestrator.md` `description`: added that it "reads the declared topology and
  routes by stage/component (not only by language)" alongside the existing language-boundary
  language; the `use`/`when` routing-trigger tokens are preserved (test_description_is_routing_signal).
- Body: reframed the job/specialist prose to route by stage/component and resolve the owning
  component engineer from the topology, falling back to the language engineer when a component
  declares none.
- "## Intake → decompose": inserted step 3 **Trace the topology** — read `[[components]]`/`[pipeline]`
  via `tools.harness_config` (`components()`/`pipeline()`), identify the touched stage/component and
  its upstream/downstream edge contracts — before Decompose/Delegate (steps renumbered 1..6).
- "## Routing decision table": added a two-dimension preamble and rows keyed on stage/component
  (declared component engineer, no-engineer language fallback, edge-contract change) plus a
  `/pipeline` "Which component owns this stage?" entry. `name`/`mode: primary` unchanged.

**Task 2 — structural gate pinning the routing signal (`d7f1d00`)**
- `tools/harness_lint/tests/test_orchestrator_topology.py` (new): `_REPO_ROOT = parents[3]`, reads
  `harness/agents/orchestrator.md` via shared `parse_frontmatter`. Three tests:
  `test_orchestrator_stays_single_primary` (name==orchestrator, mode==primary),
  `test_conductor_has_topology_intake` (case-insensitive "trace the topology" + `topology` token),
  `test_conductor_routes_by_stage_component` (`stage` + a component role word AND `/pipeline`).

## Verification

- `uv run pytest tools/harness_lint/tests/test_agents.py` → 19 passed (EXPECTED_PERSONAS stays 4,
  orchestrator single primary, no real model identifier).
- `uv run pytest tools/harness_lint/tests/test_orchestrator_topology.py` → 3 passed.
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` → GEN-04 green.
- `grep -v '^#' harness/agents/orchestrator.md | grep -Ei 'standard-log|equipment|libs/dotnet|examples/'` → no match.
- Full non-example suite: `uv run pytest` → **421 passed, 3 snapshots passed**.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pre-existing GEN-04 prose leak in `test_pipeline_config.py`**
- **Found during:** Task 2 verification (running `test_core_no_example_dep.py`).
- **Issue:** `tools/harness_lint/tests/test_pipeline_config.py` (authored in Plan 08-01) carried the
  literal ``examples/`` token in its docstring ("they must NOT reference any `examples/` instance").
  The GEN-04 guard scans `git ls-files` (tracked files only); 08-01 ran the guard while the file was
  still untracked, so the leak slipped the gate and the file was committed. Once tracked, the guard
  flags it — a genuine core-plane prose leak, exactly what this phase exists to prevent.
- **Fix:** Reworded the docstring to "must NOT reference any instance overlay (an instance's own
  topology lives under its own tree, never the core default)" — meaning unchanged, literal token gone.
- **Files modified:** `tools/harness_lint/tests/test_pipeline_config.py`
- **Commit:** `d7f1d00`

**2. [Rule 1 - Bug] Same leak in the newly-authored topology gate docstring**
- **Found during:** Full-suite run after the Task 2 commit.
- **Issue:** `test_orchestrator_topology.py`'s own docstring described its neutrality using the
  literal ``examples/`` token, which the GEN-04 guard flagged once the file became tracked.
- **Fix:** Reworded to "no instance-overlay path or domain-contract tokens ... GEN-04 core-plane guard".
- **Files modified:** `tools/harness_lint/tests/test_orchestrator_topology.py`
- **Commit:** `34b1163`

## must_haves Truth Check

- The primary orchestrator reads the declared topology and routes by stage/component, not only by
  language — YES (description + Trace-the-topology intake + routing rows).
- The orchestrator stays the single mode:primary persona; EXPECTED_PERSONAS stays exactly 4 — YES
  (test_expected_personas_present_no_sprawl + test_orchestrator_stays_single_primary green).
- The intake procedure includes a "Trace the topology" step referencing tools.harness_config — YES.

## Anti-Sprawl

Evolved the existing persona in place — no new agent file, no second primary. The pinned
EXPECTED_PERSONAS frozenset is unchanged (4). Adding `test_orchestrator_topology.py` trips no
EXPECTED_* set (those enumerate personas/skills/golden-adjacent artifacts, not test modules).

## Self-Check: PASSED

- FOUND: harness/agents/orchestrator.md
- FOUND: tools/harness_lint/tests/test_orchestrator_topology.py
- FOUND commit 9f88082 (Task 1)
- FOUND commit d7f1d00 (Task 2)
- FOUND commit 34b1163 (deviation fix)
