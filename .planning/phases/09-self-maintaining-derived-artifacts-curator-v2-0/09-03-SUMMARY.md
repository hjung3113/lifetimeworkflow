---
phase: 09-self-maintaining-derived-artifacts-curator-v2-0
plan: 03
subsystem: infra
tags: [curator, agent-persona, emitter, opencode, claude, derived-plane, two-plane-memory, refresh-memory]

# Dependency graph
requires:
  - phase: 09-01
    provides: docs_sync prune-then-write + reconciled docs/reference (clean committed-derived baseline)
  - phase: 09-02
    provides: contracts-index flipped gitignored→committed-derived (the guarded artifact)
  - phase: 07
    provides: tools.harness_emit single-source→dual-runtime emitter + emit-manifest ownership
provides:
  - "curator persona (harness/agents/curator.md) — read-mostly owner of derived freshness (edit+bash allow, write deny, no model id, domain-neutral)"
  - "/refresh-memory command — macro over tools.memory_regen.* + tools.docs_sync (agent: curator)"
  - "/verify-work step 5 — in-session derived-freshness gate (mirror of CI stale-derived)"
  - "committed-derived (machine-write + CI-verify) sub-tier documented in two-plane-memory skill"
  - "EXPECTED_PERSONAS 5-member SSOT (curator admitted) + persona-boundary and hook-posture tests"
  - "curator + refresh-memory round-tripped to .opencode/ + .claude/ + emit-manifest.json"
affects: [09-04, phase-10-econ, phase-11-mrepo]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Read-mostly persona with a narrow write affordance (edit+bash allow, write deny) — hybrid of python-engineer + code-reviewer shapes"
    - "Macro-over-generators command (invocation-only, no inline derivation, D-06)"
    - "Body-scan + hook-posture structural tests (regex over authored markdown + settings.json/plugins)"

key-files:
  created:
    - harness/agents/curator.md
    - harness/commands/refresh-memory.md
    - tools/harness_lint/tests/test_derived_freshness.py
  modified:
    - tools/harness_lint/caps.py
    - tools/harness_lint/tests/test_agents.py
    - harness/commands/verify-work.md
    - harness/skills/two-plane-memory/SKILL.md
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - .opencode/agent/curator.md (emitted)
    - .claude/agents/curator.md (emitted)
    - .opencode/command/refresh-memory.md (emitted)
    - .claude/commands/refresh-memory.md (emitted)
    - .opencode/command/verify-work.md (emitted)
    - .claude/commands/verify-work.md (emitted)
    - .opencode/skill/two-plane-memory/SKILL.md (emitted)
    - .claude/skills/two-plane-memory/SKILL.md (emitted)
    - AGENTS.md (emitted index)
    - tools/harness_emit/emit-manifest.json (regenerated)

key-decisions:
  - "curator is a concrete emitted persona in harness/agents/ (bumps EXPECTED_PERSONAS 4→5), NOT a templates/ scaffold; stays OUT of READ_ONLY_PERSONAS since it writes derived"
  - "curator's constitution write-deny is the GLOBAL path_deny_globs + contract-guard hook (opencode edit key is not path-globbable); frontmatter write:deny is a defensive floor, prose is advisory"
  - "/refresh-memory runs repo-map (session-only, D-02) AND the committed-derived set; the /verify-work step + CI gate guard ONLY the committed-derived set"
  - "two-plane-memory now names three derived sub-tiers: committed-state, committed-derived (machine-write+CI-verify), gitignored-derived — correcting the prior prose that implied docs/reference/ was gitignored"

patterns-established:
  - "Read-mostly-with-narrow-write persona: edit+bash allow + write:deny, excluded from READ_ONLY_PERSONAS"
  - "Invokes-only-tools body-scan test enforcing D-06 (no inline derivation logic in curator/command)"
  - "Hook-posture test: no memory_regen/docs_sync on any Pre/PostToolUse (settings.json) or tool.execute.* (plugin) write path"

requirements-completed: [MAINT-01, MAINT-03, MAINT-04]

# Metrics
duration: 9min
completed: 2026-07-13
---

# Phase 9 Plan 03: Curator persona + /refresh-memory + emitter round-trip Summary

**Read-mostly `curator` persona (edit+bash allow, write deny, no model id) plus `/refresh-memory` and a `/verify-work` freshness step, all round-tripped once through the Phase-7 emitter to both runtimes with GEN-04 green.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-13T15:44:25Z
- **Completed:** 2026-07-13T15:53:00Z
- **Tasks:** 3
- **Files modified:** 18 (7 hand-authored, 11 emitter-produced/regenerated)

## Accomplishments
- Authored `curator` — the delegatable read-mostly owner of derived freshness: writes derived paths only, regenerates ONLY by invoking `tools.memory_regen.*` + `tools.docs_sync` (D-06), carries no model identifier, stays domain-neutral (GEN-04).
- Bumped `EXPECTED_PERSONAS` 4→5 as a single SSOT edit (lands in both the structural lints and the emit-time validators); left `READ_ONLY_PERSONAS` unchanged.
- Authored `/refresh-memory` (macro over the full regen set, `agent: curator`) and spliced a presence-safe derived-freshness step 5 into `/verify-work` (four→five gates).
- Corrected + extended the two-plane-memory skill: three derived sub-tiers, with the committed-derived (machine-write + CI-verify) tier documenting the Plan-02 contracts-index flip and clarifying `docs/reference/**` was always committed-derived.
- Added `test_derived_freshness.py` (invokes-only-tools body-scan D-06 + no-on-write-regen hook posture MAINT-03/D-09) and curator boundary assertions in `test_agents.py`.
- Ran the emitter exactly once: curator + refresh-memory projected to `.opencode/` + `.claude/`, manifest regenerated listing all four new paths; re-emit is byte-identical (idempotent).

## Task Commits

Each task was committed atomically:

1. **Task 1: Bump EXPECTED_PERSONAS + author curator.md + persona-boundary tests** - `3fbfc57` (feat)
2. **Task 2: /refresh-memory + /verify-work freshness step + two-plane doc + boundary/hook tests** - `bcb3c1a` (feat)
3. **Task 3: Round-trip the emitter to both runtimes + regenerate manifest** - `6615903` (feat)

**Plan metadata:** _(this commit)_ (docs: complete plan)

## Files Created/Modified
- `harness/agents/curator.md` - NEW read-mostly persona (dual-representation frontmatter, D-05/D-06 boundary prose)
- `harness/commands/refresh-memory.md` - NEW macro over the full regen set (agent: curator)
- `tools/harness_lint/tests/test_derived_freshness.py` - NEW body-scan + hook-posture gate
- `tools/harness_lint/caps.py` - EXPECTED_PERSONAS 4→5 (curator admitted)
- `tools/harness_lint/tests/test_agents.py` - curator admitted/not-read-only + constitution-deny assertions
- `harness/commands/verify-work.md` - step 5 derived-freshness (presence-safe); intro four→five
- `harness/skills/two-plane-memory/SKILL.md` - committed-derived sub-tier + docs/reference correction
- `tools/harness_emit/emit-manifest.json` - regenerated (4 new emitted paths)
- `.opencode/**`, `.claude/**`, `AGENTS.md` - emitter output (curator + refresh-memory + edited verify-work/two-plane)

## Decisions Made
- See `key-decisions` frontmatter. Core call: curator's derived-only boundary is enforced by global `path_deny_globs` + the contract-guard hook, not a per-persona glob — the frontmatter `write: deny` is a defensive floor and the body prose is advisory.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated hardcoded command-count test 17→18**
- **Found during:** Task 3 (emitter round-trip)
- **Issue:** `test_coexist.py::test_all_17_commands_emit_to_both_trees` asserts an exact command count of 17; adding `/refresh-memory` makes it 18, so the emit suite red-failed.
- **Fix:** Renamed the test to `test_all_18_commands_emit_to_both_trees`, updated both count assertions to 18 and the module docstring, with a note that Phase 9 adds /refresh-memory.
- **Files modified:** tools/harness_emit/tests/test_coexist.py
- **Verification:** `uv run pytest tools/harness_emit -q` → 250 passed.
- **Committed in:** 6615903 (Task 3 commit)

**2. [Rule 3 - Blocking] Regenerated the projected-tree syrupy snapshot**
- **Found during:** Task 3 (emitter round-trip)
- **Issue:** `test_emit_determinism.py::test_projected_tree_matches_committed_snapshot` pins the projected agent/command/skill tree via a committed `.ambr`; the new curator + refresh-memory + edited verify-work/two-plane content legitimately changed it.
- **Fix:** Ran `pytest ... --snapshot-update` (the sanctioned syrupy update mechanism, analogous to /golden-approve on the derived-snapshot side) — a machine-regenerated derived artifact, not a hand edit.
- **Files modified:** tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
- **Verification:** Snapshot passes on re-run; re-emit byte-identical.
- **Committed in:** 6615903 (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking test updates directly caused by adding the new command)
**Impact on plan:** Both are mechanical consequences of adding one new emitted command; no scope creep. No emitted file was hand-edited — only test expectations/snapshots for the new artifact.

## Issues Encountered
None beyond the two Rule-3 test updates above. The emitter accepted curator + refresh-memory with no model-id / over-cap / GEN-04 failure on the first run.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MAINT-01 (curator), MAINT-03 (no on-write regen hook), MAINT-04 (/refresh-memory + /verify-work freshness) delivered in harness/ source and round-tripped to both runtimes.
- Plan 09-04 can now wire the CI `stale-derived` job knowing the local /refresh-memory + /verify-work freshness surface and the curator owner exist; the committed-derived baseline (docs/reference + contracts-index) is clean.
- Constitution plane untouched; no blockers introduced.

## Self-Check: PASSED

- All hand-authored + emitted files exist (curator.md, refresh-memory.md, test_derived_freshness.py, both-runtime emissions, SUMMARY).
- Task commits verified in git log: 3fbfc57, bcb3c1a, 6615903.
- emit-manifest.json lists all 4 new emitted paths (curator + refresh-memory, both runtimes).
- Re-emit byte-identical (idempotent); `uv run pytest tools/harness_lint tools/harness_emit` → 250 passed; GEN-04 green.

---
*Phase: 09-self-maintaining-derived-artifacts-curator-v2-0*
*Completed: 2026-07-13*
