---
phase: 05.5-authored-surface
plan: 01
subsystem: harness
tags: [template-despecialization, harness_lint, anti-sprawl, git-mv, adr-0002, examples]

# Dependency graph
requires:
  - phase: 05-despecialization
    provides: the git-mv history-preserving move precedent (05-05-PLAN) and the GEN-04 core→example dependency guard base
provides:
  - "domain skills (normalization-catalog, pipeline-patterns) and instance-language skill (dotnet-conventions) relocated to examples/log-parser/skills/"
  - "instance-language persona dotnet-engineer relocated to examples/log-parser/agents/"
  - "harness_lint anti-sprawl pins reduced to the exact 4 core skills + 4 core personas"
  - "strangler-step command agent repointed to core orchestrator; prose genericized"
  - "project.toml dotnet.persona repointed to the moved examples/ persona path (ADR-0002 (c) sanctioned instance pointer)"
affects: [055-02 prose sweep, 055-03 guard extension]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Anti-sprawl frozensets pin the exact core authored set; a moved/glob-vanished asset requires only the frozenset edit"
    - "Instance-language authored surface lives under examples/log-parser/; core harness/ stays language-neutral (ADR-0002 (b))"

key-files:
  created:
    - examples/log-parser/skills/normalization-catalog/SKILL.md
    - examples/log-parser/skills/pipeline-patterns/SKILL.md
    - examples/log-parser/skills/dotnet-conventions/SKILL.md
    - examples/log-parser/agents/dotnet-engineer.md
  modified:
    - tools/harness_lint/tests/test_skills.py
    - tools/harness_lint/tests/test_agents.py
    - harness/commands/strangler-step.md
    - harness/project.toml

key-decisions:
  - "Honored the explicit 'Do NOT touch the guard (055-03)' instruction: the project.toml persona pointer trips test_core_no_example_dep, whose exemption RESEARCH line 230 assigns to 055-03 — left that single guard test RED as a transient, phase-owned consequence rather than editing the guard."
  - "strangler-step repointed to agent: orchestrator (core delegating persona, RESEARCH A1) rather than python-engineer."

patterns-established:
  - "Glob-based harness_lint discovery: relocating an authored asset makes it vanish from the scanned set; only the anti-sprawl frozenset needs editing."

requirements-completed: [GEN-05]

# Metrics
duration: 6min
completed: 2026-07-09
---

# Phase 5.5 Plan 01: Authored-Surface Move Summary

**Relocated the domain/instance-language authored surface (3 skills + dotnet-engineer persona) to examples/log-parser/ via history-preserving git mv, reduced the two harness_lint anti-sprawl pins to the exact 4 core skills + 4 core personas, and repointed the two references (strangler-step agent, project.toml persona) that the move invalidated.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-09T05:16:16Z
- **Completed:** 2026-07-09T05:22:26Z
- **Tasks:** 2
- **Files modified:** 8 (4 moved, 4 edited)

## Accomplishments
- History-preserving `git mv` of `normalization-catalog`, `pipeline-patterns`, `dotnet-conventions` skills and the `dotnet-engineer` persona into `examples/log-parser/{skills,agents}/` — all recorded as `R100` (100%-similarity renames).
- `EXPECTED_SKILLS` 7→4 (`python-conventions`, `golden-testing`, `data-contracts`, `skill-creator`); `EXPECTED_PERSONAS` 5→4 (`orchestrator`, `python-engineer`, `code-reviewer`, `explorer`). Both anti-sprawl tests green.
- `strangler-step.md` `agent: dotnet-engineer` → `agent: orchestrator`; line-5 `.NET parser/converter` prose genericized to "the instance's language side". Referential-integrity test green.
- `project.toml` `dotnet.persona` → `examples/log-parser/agents/dotnet-engineer.md`. Persona-existence test green.

## Task Commits

1. **Task 1: Move 4 authored assets + reduce the two anti-sprawl pins** — `9e97fa3` (refactor)
2. **Task 2: Repoint strangler-step agent + project.toml persona** — `9563a3c` (fix)
3. **Anti-sprawl comment rewording (in-scope cleanup)** — `5e31f8d` (style)

## Files Created/Modified
- `examples/log-parser/skills/{normalization-catalog,pipeline-patterns,dotnet-conventions}/SKILL.md` — moved domain/instance-language skills (bodies unchanged; legitimate under examples/).
- `examples/log-parser/agents/dotnet-engineer.md` — moved instance-language persona.
- `tools/harness_lint/tests/test_skills.py` — `EXPECTED_SKILLS` reduced to 4 core skills.
- `tools/harness_lint/tests/test_agents.py` — `EXPECTED_PERSONAS` reduced to 4 core personas.
- `harness/commands/strangler-step.md` — `agent:` repointed to orchestrator; prose genericized.
- `harness/project.toml` — `dotnet.persona` repointed to the moved examples/ path.

## Decisions Made
- **Left one guard test RED per explicit instruction.** The plan's required Task 2 edit (`project.toml dotnet.persona → examples/…`) introduces an `examples/` token that trips the CURRENT `test_core_no_example_dep` guard. RESEARCH Pitfall 3 (lines 164-166) and the 055-03 checklist (line 230: "generalize `_is_instance_root_line`→pointer-line (root+persona)") assign the required pointer-exemption to **055-03**. The orchestrator explicitly instructed "Do NOT touch the guard (055-03)". The specific prohibition + RESEARCH wave-mapping take precedence over the plan's general "suite green" expectation, so the guard was left untouched and 055-03 will exempt the sanctioned pointer.
- **strangler-step → orchestrator** (RESEARCH A1): any core persona satisfies referential integrity; orchestrator best matches "decompose + delegate to a language engineer".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded my own anti-sprawl comments to avoid a stray `examples/` path token**
- **Found during:** Task 1 / post-verification full-suite run
- **Issue:** The explanatory comments I added above `EXPECTED_SKILLS`/`EXPECTED_PERSONAS` literally contained `examples/log-parser/…`, creating two *non-sanctioned* core→example references that tripped `test_core_no_example_dep` (on top of the plan-intended project.toml pointer).
- **Fix:** Reworded both comments to "moved to the log-parser example instance (Phase 5.5)" — no `examples/` slash token. This reduces the guard's offender list to exactly the single ADR-0002 (c)-sanctioned `project.toml` persona pointer.
- **Files modified:** tools/harness_lint/tests/test_skills.py, tools/harness_lint/tests/test_agents.py
- **Verification:** guard offender list dropped from 3 to 1 (the sanctioned pointer only)
- **Committed in:** `5e31f8d`

---

**Total deviations:** 1 auto-fixed (1 blocking, self-inflicted cleanup).
**Impact on plan:** No scope creep. The guard was NOT edited (055-03 owns that).

## Issues Encountered

**KNOWN TRANSIENT RED — `test_core_no_example_dep::test_core_has_no_example_dependency` (owned by 055-03).**
- The plan's required `project.toml dotnet.persona = "examples/log-parser/agents/dotnet-engineer.md"` edit is a core→instance path reference that the CURRENT GEN-04 guard flags. The guard exempts only the `[instance] root =` line, not `persona =`.
- The fix — generalizing `_is_instance_root_line` to also exempt the `persona =` pointer plus a positive exemption test — is explicitly scoped to **055-03** (RESEARCH line 230; traceability line 150 "+ guard pointer-line exemption, else the extended guard flags this line"; wave-map lines 221-222).
- Per the orchestrator's explicit "Do NOT touch the guard (055-03)" and RESEARCH, this test is left RED intentionally. It resolves when 055-03 runs.
- **Full-suite state after this plan:** 349 passed, 1 failed (only the above). All 4 plan-scoped RED tests (skills anti-sprawl, personas anti-sprawl, referential-integrity, persona-existence) are green.
- No `git commit --no-verify` used; no hook disabled; no GOLDEN_APPROVE_HUMAN token needed (no constitution-plane writes).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The load-bearing move is complete and all 4 authored assets live under `examples/log-parser/` (R100 renames, history preserved).
- 055-02 (prose sweep) can proceed against the moved tree.
- **055-03 must run to close the intentional `test_core_no_example_dep` RED** by adding the `project.toml` `persona =` pointer-exemption (and the wider prose-token guard extension). Until then, `uv run pytest` reports exactly 1 failure on that single guard test.

## Self-Check: PASSED

All 4 relocated files exist under `examples/log-parser/`; all 3 task commits (`9e97fa3`, `9563a3c`, `5e31f8d`) present in git history; SUMMARY.md written.

---
*Phase: 05.5-authored-surface*
*Completed: 2026-07-09*
