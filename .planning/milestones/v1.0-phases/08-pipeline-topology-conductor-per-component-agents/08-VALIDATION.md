---
phase: 8
slug: pipeline-topology-conductor-per-component-agents
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-10
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `08-RESEARCH.md` § Validation Architecture. Every mechanism is a structural/unit
> pytest gate over authored files (TOML data slot + persona/skill/command markdown + Python guards) —
> no external runtime.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (`minversion = "8.4"`) via `uv run pytest` |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`, `testpaths = ["libs/python", "tools"]` |
| **Quick run command** | `uv run pytest tools/harness_lint tools/harness_config -x` |
| **Full suite command** | `uv run pytest` (core; ~413 passing baseline) **AND** `uv run pytest examples/log-parser/tests` (instance leg — NOT in root `testpaths`) |
| **Estimated runtime** | ~30–60 seconds (structural gates are file reads, no I/O-bound tests) |

---

## Sampling Rate

- **After every task commit:** Run the specific new/edited gate the task touches, e.g. `uv run pytest tools/harness_lint/tests/test_pipeline_config.py -x` (Nyquist: sample the exact invariant the task changes).
- **After every plan wave:** Run `uv run pytest tools/harness_lint tools/harness_config` — all structural gates + loader units; catches cross-artifact drift (a component naming an undeclared language, a command with a dangling agent).
- **Before `/gsd:verify-work`:** Full core suite (`uv run pytest`) green **AND** instance leg (`uv run pytest examples/log-parser/tests`) green. Re-run `tools/memory_regen` if any schema/contract file was added.
- **Max feedback latency:** < 60 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 8-01-xx | 01 | 1 | PIPE-01 | T-8-01 (V5 input-validation) | Malformed topology slot fails loud (component.language ∈ languages; edges well-formed), never silent | structural gate | `uv run pytest tools/harness_lint/tests/test_pipeline_config.py -x` | ❌ W0 | ⬜ pending |
| 8-01-xx | 01 | 1 | PIPE-01 | — | Loader passthrough returns declared components/pipeline unchanged | unit | `uv run pytest tools/harness_config/tests/test_loader.py -x` | ❌ W0 (extend) | ⬜ pending |
| 8-01-xx | 01 | 1 | PIPE-01/06 | T-8-02 (boundary erosion) | Core carries zero example dependency after edits | guard | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ✅ (stay green) | ⬜ pending |
| 8-02-xx | 02 | 2 | PIPE-02 | T-8-04 (model-id leak) | Orchestrator stays the single primary; `EXPECTED_PERSONAS` unchanged (4); no sprawl | structural gate | `uv run pytest tools/harness_lint/tests/test_agents.py::test_expected_personas_present_no_sprawl -x` | ✅ (assert unchanged) | ⬜ pending |
| 8-02-xx | 02 | 2 | PIPE-02 | — | Conductor routing table carries topology/stage/component signal | structural | new assertion in `test_agents.py` / `test_pipeline_config.py` (grep routing for stage/component) | ❌ W0 (optional) | ⬜ pending |
| 8-03-xx | 03 | 2 | PIPE-03 | T-8-01 (V4 least-priv) | `component-engineer` template exists, subagent-mode, least-privilege perms, NOT counted as a persona | structural gate | `uv run pytest tools/harness_lint/tests/test_agent_templates.py -x` | ❌ W0 | ⬜ pending |
| 8-03-xx | 03 | 2 | PIPE-03 | — | Scaffold/`/component` command resolves to a real persona | integration | `uv run pytest tools/harness_lint/tests/test_agent_referential_integrity.py -x` | ✅ (auto-covers) | ⬜ pending |
| 8-04-xx | 04 | 3 | PIPE-04 | — | Instance declares 4 components; each binds a real agent file + real contract; edges well-formed | instance structural | `uv run pytest examples/log-parser/tests/test_pipeline_topology.py -x` | ❌ W0 (example leg) | ⬜ pending |
| 8-04-xx | 04 | 3 | PIPE-04 | T-8-01 (EoP) | 4 component agents parse, subagent-mode, least-privilege | instance structural | same file (glob `examples/log-parser/agents/*.md`) | ❌ W0 | ⬜ pending |
| 8-05-xx | 05 | 3 | PIPE-05 | — | `pipeline-map` skill within caps, unique routing desc; skill set is exactly 9 | structural gate | `uv run pytest tools/harness_lint/tests/test_skills.py -x` | ✅ (bump `EXPECTED_SKILLS` 8→9) | ⬜ pending |
| 8-05-xx | 05 | 3 | PIPE-05 | — | `/pipeline` command frontmatter + routing + agent resolves | structural + integration | `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_agent_referential_integrity.py -x` | ✅ (glob auto-covers) | ⬜ pending |
| 8-06-xx | 06 | 4 | PIPE-06 | T-8-02/03/04 | Full core suite green; GEN-04/05 + persona + template gates green | full suite | `uv run pytest` **AND** `uv run pytest examples/log-parser/tests` | ✅ + W0 additions | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs are placeholders (`8-PP-xx`) — the planner assigns concrete task numbers.*

---

## Wave 0 Requirements

- [ ] `tools/harness_lint/tests/test_pipeline_config.py` — generic topology consistency gate: component.language ∈ declared languages, edge contracts (consumes/produces) well-formed, ids unique (PIPE-01/06)
- [ ] `tools/harness_config/tests/test_loader.py` — extend with `components()` / `pipeline()` passthrough asserts (PIPE-01)
- [ ] `tools/harness_lint/tests/test_agent_templates.py` — template anti-sprawl + shape gate; closes the current gap where `harness/agents/templates/*.md` is validated by nothing (non-recursive `agents/*.md` glob) (PIPE-03/06)
- [ ] `examples/log-parser/tests/test_pipeline_topology.py` — instance topology + 4-agent structural gate; runs in the example leg (PIPE-04)
- [ ] Edit `tools/harness_lint/tests/test_skills.py` — bump `EXPECTED_SKILLS` 8→9 (add `pipeline-map`) (PIPE-05)
- [ ] Confirm `tools/harness_lint/tests/test_agents.py` — `EXPECTED_PERSONAS` stays 4 (conductor = evolved orchestrator, no new primary) (PIPE-02)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Conductor can trace a request across the full parser→converter→scheduler→collector flow | PIPE-04 | Narrative/agent-behavior demonstration; the deterministic slice is the topology structural gate, but the end-to-end "trace" reads as reasoning over loader output | Run `/pipeline` (or the `pipeline-map` skill) against the log-parser instance overlay; confirm it renders all 4 stages, both edges, and resolves each stage to its component agent file |

*The `/pipeline` "trace" is a deterministic render of loader output (Open Question #4 recommendation) — its structural correctness IS automated by `test_pipeline_topology.py`; only the human-facing readability of the trace is manual.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (6 items above)
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
