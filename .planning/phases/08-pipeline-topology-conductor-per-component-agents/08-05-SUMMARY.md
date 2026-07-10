---
phase: 08-pipeline-topology-conductor-per-component-agents
plan: 05
subsystem: harness-core-routing-surface
tags: [pipeline-topology, skill, command, PIPE-05, GEN-04, anti-sprawl]
requires:
  - tools/harness_config components()/pipeline()/load_project() (08-01)
  - harness/agents/templates/component-engineer.md + /component derivation (08-03)
  - harness/skills/gate-model/SKILL.md + harness/commands/component.md (idiom clones)
provides:
  - "pipeline-map core skill: trace a request across the declared topology, resolve a stage to its owning component agent"
  - "/pipeline command: deterministic render of the [[components]]/[pipeline] slot (stage list + edge chain + stage->agent resolution), no live runtime"
  - "EXPECTED_SKILLS bumped 8->9 (anti-sprawl gate green at 9)"
affects:
  - Plan 08-04 instance overlay (its concrete topology is what /pipeline renders in an instance)
  - agent routing surface (new skill/command other agents dispatch on)
tech-stack:
  added: []
  patterns:
    - "Clone gate-model SKILL.md frontmatter idiom (name / description >- routing trigger / progressive-disclosure body)"
    - "Clone component.md/orient.md command idiom (description routing signal / agent: orchestrator / subtask boolean / numbered render steps)"
    - "Deterministic render of loader passthrough output — no live runtime (RESEARCH Open Q#4)"
key-files:
  created:
    - harness/skills/pipeline-map/SKILL.md
    - harness/commands/pipeline.md
  modified:
    - tools/harness_lint/tests/test_skills.py
decisions:
  - "The trace is a deterministic RENDER of declared config (loader output), not a live pipeline execution (RESEARCH Open Q#4)"
  - "Core artifacts stay domain-neutral (source/sink generic ids only) so GEN-04 stays green; concrete owners come from the instance overlay"
  - "Reworded 'converter' -> 'stage implementation' in command prose to trip zero domain tokens in a core file (project caution)"
metrics:
  duration: 10min
  tasks: 2
  files: 3
  completed: 2026-07-10
---

# Phase 08 Plan 05: Pipeline-Map Skill + /pipeline Command Summary

Made the pipeline model executable at the agent-facing surface: a domain-neutral `pipeline-map` core
skill that teaches how to trace a request across the declared `[[components]]`/`[pipeline]` topology
and find the owning component agent, plus a `/pipeline` command that deterministically renders the
dataflow (stage list + edge chain) from `tools.harness_config` and resolves each stage to its
`<id>-engineer` agent file. No live runtime — the trace is a render of loader output. Anti-sprawl
skill-set gate raised 8→9, all core-plane and GEN-04 green.

## What Was Built

**Task 1 — pipeline-map skill + EXPECTED_SKILLS bump (`6d9fc10`)**
- `harness/skills/pipeline-map/SKILL.md` (new): cloned the gate-model frontmatter idiom
  (`name: pipeline-map`, a UNIQUE `description: >-` routing trigger keyed on "trace a request across
  the pipeline dataflow / find the component agent that owns a stage"). Body (98 lines, well under
  the ~500 cap): the topology slot fields (id/stage/language/consumes/produces), how edges chain
  stages, how to read them via `components()`/`pipeline()`/`load_project()`, and how each stage
  resolves to `<id>-engineer.md` in the instance's `agents/`. Strictly domain-neutral (source/sink
  generic vocabulary — zero parser/converter/standard-log/equipment tokens).
- `tools/harness_lint/tests/test_skills.py`: added `"pipeline-map"` to the `EXPECTED_SKILLS`
  frozenset (8 → 9) with a Phase-8 comment line.

**Task 2 — /pipeline command (`5c3bfc4`)**
- `harness/commands/pipeline.md` (new): cloned the component.md/orient.md command idiom —
  `description: >-` routing signal ("trace/visualize the pipeline dataflow and find the owning
  component agent"), `agent: orchestrator` (resolves to the real primary persona), `subtask: true`
  (boolean). Body is a numbered deterministic render procedure: (1) load the active topology via
  `from tools.harness_config import components, pipeline, load_project` (core default vs instance
  overlay path); (2) print each component as `stage N: <id> (<language>) consumes=[...]
  produces=[...]`; (3) print the edge chain `from -> to (contract)`; (4) resolve each stage to
  `<id>-engineer.md` and flag any missing owner. States explicitly there is NO live runtime.
  Domain-neutral (source/sink example ids only).

## Verification

- `uv run pytest tools/harness_lint/tests/test_skills.py tools/harness_lint/tests/test_core_no_example_dep.py` → 56 passed (skill-set-no-sprawl + caps + unique-description + GEN-04 green).
- `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_agent_referential_integrity.py` → 86 passed (frontmatter parses, subtask boolean, `agent: orchestrator` resolves to a real persona).
- `grep -iE 'parser|converter|standard-log|equipment|examples/|libs/dotnet'` on BOTH new core files → no match (domain-neutral core).
- Render data readable: `python -c "from tools.harness_config import components, pipeline; ..."` → `['source', 'sink']` / `[{'from': 'source', 'to': 'sink', 'contract': 'sample-record'}]`.
- Full non-example suite: `uv run pytest` → **439 passed, 3 snapshots passed** (was 430 at 08-03; +9 from the skill parametrized gates over the new skill).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - GEN-04 compliance] Removed a domain token from command prose**
- **Found during:** Task 2 verification
- **Issue:** The command's Notes line read "it never spawns a stage or runs a converter" — the word
  "converter" is a domain token the project cautions forbid in ANY core file (belt-and-suspenders
  beyond the GEN-04 guard, which stayed green regardless).
- **Fix:** Reworded to "runs any stage implementation".
- **Files modified:** harness/commands/pipeline.md
- **Commit:** 5c3bfc4 (folded into the Task 2 commit before landing)

## must_haves Truth Check

- A pipeline-map skill exists under harness/skills/pipeline-map/ within Claude caps with a unique routing-trigger description — YES (98-line body, unique description, gates green).
- EXPECTED_SKILLS is exactly 9 (adds pipeline-map) and the skill-set gate stays green — YES.
- A /pipeline command renders the declared topology dataflow (stage->stage edges) and resolves each stage to its component agent by reading tools.harness_config — a deterministic render, no live runtime — YES.
- The /pipeline command passes every command gate (frontmatter parses, agent resolves to a real persona, description is a routing signal, subtask is boolean) — YES (86 passed).

## Anti-Sprawl

Adding `pipeline-map` REQUIRED bumping the pinned `EXPECTED_SKILLS` frozenset 8→9 (Phase 5.7 raised
it 4→8); the skill-set-no-sprawl gate now asserts exactly the 9 enumerated core skills. The
`/pipeline` command trips no expected-set (commands are not enumerated in a frozenset — they are
gated by shape, not membership).

## Self-Check: PASSED

- FOUND: harness/skills/pipeline-map/SKILL.md
- FOUND: harness/commands/pipeline.md
- FOUND commit 6d9fc10 (Task 1)
- FOUND commit 5c3bfc4 (Task 2)
