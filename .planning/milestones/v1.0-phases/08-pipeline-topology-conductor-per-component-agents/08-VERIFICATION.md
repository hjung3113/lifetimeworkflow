---
phase: 08-pipeline-topology-conductor-per-component-agents
verified: 2026-07-11T13:05:17Z
status: passed
score: 6/6 must-haves verified (gap closed post-verification)
overrides_applied: 0
gaps:
  - truth: "The conductor (/pipeline command + pipeline-map skill) can resolve each of the 4 declared log-parser stages to a real, existing component-agent file when followed as documented — ROADMAP Success Criterion 3 ('the conductor can trace the full parser→converter→scheduler→collector flow') and PIPE-04's must-have truth ('the conductor can trace the full parser→converter→scheduler→collector flow from the instance overlay')"
    status: resolved
    reason: >-
      harness/commands/pipeline.md and harness/skills/pipeline-map/SKILL.md (both PIPE-05, Plan
      08-05) document the stage→agent resolution algorithm as
      "<instance-root>/agents/<id>-engineer.md" (e.g. examples/log-parser/agents/parser-engineer.md).
      Plan 08-04, however, deliberately named the 4 real instance component agents "<id>.md" (no
      "-engineer" suffix) — its own SUMMARY records the decision explicitly: "Agent name ==
      topology component.id (parser/converter/scheduler/collector), NOT <id>-engineer". No
      automated test exercises the /pipeline command's or pipeline-map skill's documented
      resolution algorithm against the real examples/log-parser/agents/*.md files, so this
      cross-plan naming mismatch (Plan 08-04 vs Plan 08-05, developed in parallel, both wave 2/3
      but Plan 08-05 only depends_on 08-01) was never caught by the guard suite or by Plan 08-06's
      closeout. Reproduced directly: computing "<instance-root>/agents/<id>-engineer.md" for all 4
      declared components (parser/converter/scheduler/collector) resolves to 4 non-existent paths
      — following the documented procedure literally on the log-parser instance reports "NO OWNING
      AGENT" for every stage, the opposite of the demonstrated capability.
    artifacts:
      - path: "harness/commands/pipeline.md"
        issue: "Step 4 computes the expected agent path as '<instance-root>/agents/<id>-engineer.md' — does not exist for any of the 4 log-parser stages"
      - path: "harness/skills/pipeline-map/SKILL.md"
        issue: "Documents resolving a stage to '<id>-engineer.md' in the instance's agents/ dir — contradicts the actual instance agent filenames"
      - path: "examples/log-parser/agents/parser.md, converter.md, scheduler.md, collector.md"
        issue: "Named '<id>.md' (matches the instance topology gate's own expectation in test_pipeline_topology.py), NOT '<id>-engineer.md' as /pipeline and pipeline-map assume"
    missing:
      - "Pick one naming convention and make all four artifacts agree: either update pipeline.md's and pipeline-map/SKILL.md's documented resolution pattern from '<id>-engineer.md' to '<id>.md' (matching the actual PIPE-04 convention and test_pipeline_topology.py), OR rename the 4 instance agent files (+ update test_pipeline_topology.py assertions and any project.toml references) to the '<id>-engineer.md' convention the template/command/skill currently document"
      - "Add a regression check that actually exercises the /pipeline resolution algorithm against the real examples/log-parser/agents/*.md files (e.g. extend examples/log-parser/tests/test_pipeline_topology.py or add a harness_lint cross-check), so future naming drift between the command/skill docs and instance agents fails loud instead of silently"
---

# Phase 8: Pipeline-Topology Conductor + Per-Component Agents Verification Report

**Phase Goal:** Evolve the harness agent model from per-language to pipeline-aware: a generic pipeline-topology slot in the neutral core, an `orchestrator` upgraded into a dataflow-aware conductor that routes by pipeline stage/component, a neutral `component-engineer` template, and a concrete 4-component demonstration in `examples/log-parser/` (parser→converter→scheduler→collector).
**Verified:** 2026-07-11T13:05:17Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Core declares a generic `[[components]]`+`[pipeline]` topology DATA slot (zero example dependency); loader exposes `components()`/`pipeline()`; consistency gate fails loud on divergence | ✓ VERIFIED | `harness/project.toml` lines 57-79 declare a generic `source`→`sink` topology; `tools/harness_config/loader.py` has `def components()`/`def pipeline()`; `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` → 18 passed; `uv run pytest tools/harness_lint/tests/test_pipeline_config.py tools/harness_config/tests/test_loader.py -q` → 10 passed |
| 2 | The primary `orchestrator` is topology-aware: it reads the declared topology and routes by pipeline stage/component (not only language); stays the ONE `mode: primary` persona (EXPECTED_PERSONAS stays 4); neutral `component-engineer` template exists, anti-sprawl-exempt | ✓ VERIFIED | `harness/agents/orchestrator.md` carries a "Trace the topology" intake step and a routing table keyed on stage/component + `/pipeline`; `EXPECTED_PERSONAS = frozenset({"orchestrator","python-engineer","code-reviewer","explorer"})` (unchanged, 4 members); `uv run pytest tools/harness_lint/tests/test_agents.py tools/harness_lint/tests/test_orchestrator_topology.py -q` → 23 passed |
| 3 | `examples/log-parser/` demonstrates the mechanism end-to-end — 4 component agents + the log-parser topology declared in the instance's `project.toml` slot; the conductor can trace the full parser→converter→scheduler→collector flow | ✗ FAILED | `examples/log-parser/project.toml` declares the 4-stage topology and 4 agent files exist (`parser.md`, `converter.md`, `scheduler.md`, `collector.md`); `uv run pytest examples/log-parser/tests -q` → 9 passed, 2 skipped (expected .NET-egress skips). BUT the documented "trace the flow" mechanism (`/pipeline` + `pipeline-map` skill) resolves stage owners via a path pattern (`<id>-engineer.md`) that does not match the actual agent filenames (`<id>.md`) — reproduced directly, all 4 stage resolutions compute a non-existent path. See Gaps. |
| 4 | New skill(s)/command(s) make the pipeline model executable (topology-trace / `/pipeline`); full non-example `uv run pytest` green; GEN-04/05 + persona guards clean; Phase 7 emit surface unaffected | ⚠ PARTIAL | `harness/skills/pipeline-map/SKILL.md` + `harness/commands/pipeline.md` exist and pass all structural/shape/anti-sprawl gates (`EXPECTED_SKILLS` bumped to 9, `test_skills.py` → 38 passed); `uv run pytest` (core) → 440 passed, 3 snapshots passed; `uv run pytest examples/log-parser/tests` → 9 passed, 2 skipped. The command/skill exist and are wired at the frontmatter/gate level, but the documented rendering algorithm they both specify is functionally broken against the one real instance that demonstrates it (same root cause as Truth 3). |
| 5 | Guards/tests: GEN-04 core→example no-dependency + persona anti-sprawl extended to conductor + `component-engineer` template; topology-slot consistency gate | ✓ VERIFIED | `test_single_primary_carries_conductor_signal` in `tools/harness_lint/tests/test_agents.py` asserts exactly one `mode: primary` persona carrying a conductor signal; `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py tools/harness_lint/tests/test_pipeline_config.py tools/harness_lint/tests/test_agent_templates.py tools/harness_lint/tests/test_skills.py -q` → 68 passed |
| 6 | ADR-0003 records the pipeline-topology-slot + instance-overlay decision on the constitution plane, mirrors ADR-0002's MADR structure, cites GEN-04 as primary driver, indexed in `docs/adr/README.md` | ✓ VERIFIED | `docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md` exists with `plane: constitution`, MADR 4.x structure, "GEN-04 must stay green — the primary driver" decision driver; `docs/adr/README.md` line 32 lists the ADR-0003 row; landed via commit `ec5a01f` |

**Score:** 5/6 truths verified (Truth 3 failed; Truth 4 partial and rolled into the same gap)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `harness/project.toml` | Generic `[[components]]`+`[pipeline]` slot, zero domain tokens | ✓ VERIFIED | `source`/`sink`/`sample-record` generic default present, GEN-04 green |
| `tools/harness_config/loader.py` | `components()`/`pipeline()` passthrough | ✓ VERIFIED | Both functions present, tested |
| `tools/harness_config/__init__.py` | Lazy re-export | ✓ VERIFIED | `components`, `pipeline` in `__all__` |
| `tools/harness_lint/tests/test_pipeline_config.py` | Topology consistency gate | ✓ VERIFIED | Present, green |
| `harness/agents/orchestrator.md` | Topology-aware conductor (evolved in place) | ✓ VERIFIED | Substantive routing table + intake, not a stub |
| `tools/harness_lint/tests/test_orchestrator_topology.py` | Structural gate pinning the routing signal | ✓ VERIFIED | 4 real assertions, all pass |
| `harness/agents/templates/component-engineer.md` | Neutral fill-in-the-blanks template | ✓ VERIFIED | `mode: subagent`, placeholders, not counted as a persona |
| `harness/commands/component.md` | Scaffold binding per-component agents | ✓ VERIFIED | Mandated-order scaffold + component-binding guard |
| `tools/harness_lint/tests/test_agent_templates.py` | Template anti-sprawl + shape gate | ✓ VERIFIED | `EXPECTED_TEMPLATES = {"engineer", "component-engineer"}`, 9 passed |
| `examples/log-parser/project.toml` | Concrete 4-component instance topology | ✓ VERIFIED | 4 components, 3 well-formed edges |
| `examples/log-parser/agents/{parser,converter,scheduler,collector}.md` | 4 subagent, least-privilege component agents | ✓ VERIFIED | All exist, `mode: subagent`, scoped bash allow |
| `examples/log-parser/tests/test_pipeline_topology.py` | Instance topology gate | ✓ VERIFIED | 4 assertions, all pass |
| `harness/skills/pipeline-map/SKILL.md` | Topology-trace skill within Claude caps | ⚠ ORPHANED (functionally) | Exists, passes shape/caps gates, but its documented resolution algorithm (`<id>-engineer.md`) does not match the real instance agent files it is meant to trace |
| `harness/commands/pipeline.md` | `/pipeline` renders dataflow + resolves stage owners | ⚠ ORPHANED (functionally) | Exists, passes command gates, but Step 4's resolution algorithm does not match the real instance agent files — see gap |
| `docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md` | Constitution-plane ADR | ✓ VERIFIED | `plane: constitution`, MADR structure, indexed |
| `tools/harness_lint/tests/test_agents.py` | Conductor-signal + persona-count assertion | ✓ VERIFIED | `test_single_primary_carries_conductor_signal` present and passing |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `tools/harness_lint/tests/test_pipeline_config.py` | `tools.harness_config.components`/`pipeline` | import + consistency assertions | ✓ WIRED | Passes |
| `tools/harness_config/loader.py` | `harness/project.toml [[components]]` | `tomllib` read | ✓ WIRED | Passes |
| `harness/agents/orchestrator.md` | `tools.harness_config` components/pipeline | intake "Trace the topology" step | ✓ WIRED | Textual reference present, gate pins it |
| `harness/commands/component.md` | `harness/agents/templates/component-engineer.md` | copy + fill placeholders | ✓ WIRED | Scaffold documented and consistent with the template's own placeholder set |
| `examples/log-parser/tests/test_pipeline_topology.py` | `examples/log-parser/project.toml` + `agents/*.md` | `load_project(path=...)` + existence asserts | ✓ WIRED | Passes; asserts `agents/<id>.md` (matches actual files) |
| `harness/commands/pipeline.md` | `tools.harness_config` components/pipeline | render step reads declared topology | ✓ WIRED (render step) | The load-topology half works |
| `harness/commands/pipeline.md` Step 4 | `examples/log-parser/agents/*.md` | stage→agent path resolution | ✗ NOT_WIRED | Computes `<id>-engineer.md`; real files are `<id>.md` — resolution fails for all 4 stages |
| `harness/skills/pipeline-map/SKILL.md` | `examples/log-parser/agents/*.md` | documented stage→agent lookup | ✗ NOT_WIRED | Same mismatch as above |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Core topology loader returns generic default | `python -c "from tools.harness_config import components,pipeline; ..."` | `['source','sink']` / `[{'from':'source','to':'sink','contract':'sample-record'}]` | ✓ PASS |
| `/pipeline` Step-4 stage→agent resolution against the real log-parser instance | Reproduced the documented `<instance-root>/agents/<id>-engineer.md` computation for all 4 declared components | All 4 paths (`parser-engineer.md`, `converter-engineer.md`, `scheduler-engineer.md`, `collector-engineer.md`) resolve to non-existent files; real files are `parser.md`/`converter.md`/`scheduler.md`/`collector.md` | ✗ FAIL |
| Instance topology gate (real convention) | `uv run pytest examples/log-parser/tests -q` | 9 passed, 2 skipped (expected .NET-egress skips) | ✓ PASS |
| Core suite full run | `uv run pytest -q` | 440 passed, 3 snapshots passed | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PIPE-01 | 08-01 | Generic pipeline-topology DATA slot + loader + consistency gate, zero example dependency | ✓ SATISFIED | `harness/project.toml`, `loader.py`, `test_pipeline_config.py`, GEN-04 green |
| PIPE-02 | 08-02 | Orchestrator evolved in place into topology-aware conductor, single primary | ✓ SATISFIED | `orchestrator.md`, `test_orchestrator_topology.py`, `EXPECTED_PERSONAS` unchanged |
| PIPE-03 | 08-03 | Neutral `component-engineer` template + `/component` binding | ✓ SATISFIED | `templates/component-engineer.md`, `commands/component.md`, `test_agent_templates.py` |
| PIPE-04 | 08-04 | `examples/log-parser/` 4-component end-to-end demonstration; conductor traces the full flow | ⚠ BLOCKED (partial) | Topology + agents + instance gate all exist and pass, but the "conductor can trace the full flow" claim fails when exercised via the documented `/pipeline` mechanism — see gap |
| PIPE-05 | 08-05 | `pipeline-map` skill + `/pipeline` command make the model executable | ⚠ BLOCKED (partial) | Artifacts exist and pass structural gates, but the core "resolve each stage to its component agent" behavior is broken for the one real instance — see gap |
| PIPE-06 | 08-06 | Guards extended (GEN-04, anti-sprawl, template gate, topology gate, skills(9)); full suite green both legs; ADR-0003 | ✓ SATISFIED | All listed gates green; `uv run pytest` and `uv run pytest examples/log-parser/tests` both green; ADR-0003 present and indexed |

### Anti-Patterns Found

None. Scanned all phase-modified files (`harness/project.toml`, `tools/harness_config/*`, `tools/harness_lint/tests/test_pipeline_config.py`, `harness/agents/orchestrator.md`, `tools/harness_lint/tests/test_orchestrator_topology.py`, `harness/agents/templates/component-engineer.md`, `harness/commands/component.md`, `tools/harness_lint/tests/test_agent_templates.py`, `examples/log-parser/project.toml`, `examples/log-parser/agents/*.md`, `examples/log-parser/tests/test_pipeline_topology.py`, `harness/skills/pipeline-map/SKILL.md`, `harness/commands/pipeline.md`, `tools/harness_lint/tests/test_skills.py`, `docs/adr/0003-*.md`, `tools/harness_lint/tests/test_agents.py`) for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` — the only hits are the intentional, documented `<PLACEHOLDER>` token convention in `component-engineer.md`/`component.md` (the template's fill-in-the-blanks mechanism, not debt). No model identifiers found in any agent/ADR file.

### Human Verification Required

None. The gap identified (stage→agent naming mismatch) is deterministically reproducible via file-existence checks, not a judgment call requiring human testing.

### Gaps Summary

Five of six roadmap success criteria are cleanly achieved with strong evidence: the generic core topology slot (PIPE-01), the evolved topology-aware conductor (PIPE-02), the neutral component-engineer template (PIPE-03), and the closeout guard/ADR work (PIPE-06) are all substantive, wired, and gate-verified. The concrete 4-component instance demonstration (PIPE-04) and the pipeline-map skill/`/pipeline` command (PIPE-05) both exist and pass every automated structural gate — but they were built as two independent, wave-parallel plans (08-04 depends only on 08-01/08-03; 08-05 depends only on 08-01) that never cross-validated each other, and they disagree on the instance component-agent filename convention: Plan 08-04 explicitly chose `<id>.md` (documented in its own SUMMARY as a deliberate decision — "NOT `<id>-engineer`"), while Plan 08-05's `/pipeline` command and `pipeline-map` skill both document and implement resolution via `<id>-engineer.md`. No test in the guard suite exercises the `/pipeline`/`pipeline-map` resolution algorithm against the real `examples/log-parser/agents/*.md` files, so this was never caught. The practical effect: the phase's headline claim — "the conductor can trace the full parser→converter→scheduler→collector flow" — is false when the actually-built tracing mechanism is followed as documented; it reports every one of the 4 stages as having no owning agent. This is a small, mechanical fix (align the naming convention across `pipeline.md`, `pipeline-map/SKILL.md`, and either the instance agents or the template), but it is a real functional gap in the demonstrated deliverable, not a documentation nit — the phase should not be marked complete until it's closed.

---

_Verified: 2026-07-11T13:05:17Z_
_Verifier: Claude (gsd-verifier)_


---

## Gap Resolution (post-verification, 2026-07-11)

The single gap — conductor stage→agent resolution documenting `<id>-engineer.md` while the instance
ships `<id>.md` — was fixed in commit `17c1792`:

- `harness/commands/pipeline.md` and `harness/skills/pipeline-map/SKILL.md` now document the
  resolution convention as `<id>.md` (the `-engineer` suffix names the *template*
  `component-engineer.md`, not the derived per-component agents). `name == component id`.
- Added an example-leg drift-guard `test_core_resolution_convention_matches_instance_agents`
  (example→core read — GEN-04-safe) that computes the documented owner path for every stage,
  asserts it resolves to a real instance agent, and asserts the stale `<id>-engineer.md` token is
  gone from the core docs — so future core↔instance naming drift fails loud.

**Re-verified green:** `uv run pytest` → 440 passed; `uv run pytest examples/log-parser/tests` →
10 passed, 2 skipped (the 2 skips are the expected .NET egress-blocked golden-spawn cases). Following
`/pipeline` as documented now resolves all 4 log-parser stages to their real agents. **Status: passed.**
