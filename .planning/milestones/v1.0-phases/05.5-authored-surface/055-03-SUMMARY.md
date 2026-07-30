---
phase: 05.5-authored-surface
plan: 03
subsystem: testing
tags: [harness-lint, guard, gen-04, gen-05, prose-purity, tamper-evidence, pytest]

# Dependency graph
requires:
  - phase: 05.5-authored-surface (055-01)
    provides: git mv of moved assets (dotnet-engineer persona, dotnet-conventions/normalization-catalog/pipeline-patterns skills, libs/dotnet) into examples/log-parser/ — so the moved-asset tokens vanish from core
  - phase: 05.5-authored-surface (055-02)
    provides: bounded prose sweep of surviving core refs — so every remaining flagged token except the sanctioned project.toml persona= pointer is reworded
provides:
  - GEN-05 prose tier on the GEN-04 core→example guard (_PROSE_TOKENS scan)
  - generalized instance-pointer exemption (root= AND persona=) for harness/project.toml
  - per-token negative controls proving the prose scan is live (wafer/설비 as 0-occurrence anchors)
  - positive exemption test for the dotnet.persona instance pointer
  - closure of the transient RED (test_core_has_no_example_dependency now passes on the real tree)
affects: [phase-6-ci, phase-7-emitter, harness-lint, template-instance-split]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-tier core→instance guard: SCOPE-A code-dependency tokens + GEN-05 narrow prose tokens in one _scan_lines pass"
    - "Per-token parametrized negative controls with 0-occurrence anchors (wafer/설비) to guarantee the scan cannot silently no-op"
    - "Single sanctioned pointer-line exemption generalized via a shared regex (root|persona) for the one instance-data file (ADR-0002 (c))"

key-files:
  created: []
  modified:
    - tools/harness_lint/tests/test_core_no_example_dep.py

key-decisions:
  - "Prose token set kept NARROW — excludes bare dotnet/.NET/parser/converter/normalize/log-parser to avoid over-flagging legitimately-general core text (argparse, golden_runner prose, package names)"
  - "Generalized _is_instance_root_line → _is_instance_pointer_line (shared regex ^\\s*(root|persona)\\s*=) so the one dotnet.persona line carrying both examples/ and dotnet-engineer is exempted whole"
  - "wafer/설비 chosen as 0-real-occurrence live-scan anchors for the negative controls"

patterns-established:
  - "Prose-purity tamper-evidence: any core file regrowing a moved-asset/domain token RED-flags the full suite"
  - "Additive guard extension — SCOPE-A behavior and all existing tests preserved intact"

requirements-completed: [GEN-05]

# Metrics
duration: 6min
completed: 2026-07-09
---

# Phase 5.5 Plan 03: GEN-04 Guard Prose Extension Summary

**Extended the GEN-04 core→example guard from SCOPE-A code-dependency tokens to a narrow GEN-05 prose tier (moved-asset proper nouns + libs/dotnet + rare semiconductor vocab), generalized the instance-pointer exemption to cover the dotnet.persona line, and closed the phase's one transient RED — the full non-example suite is now fully green (361 passed, 0 failed).**

## Performance

- **Duration:** ~6 min
- **Completed:** 2026-07-09
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `_PROSE_TOKENS` (10 tokens: `dotnet-engineer`, `dotnet-conventions`, `normalization-catalog`, `pipeline-patterns`, `libs/dotnet`, `equipment`, `standard-log`, `correction-rules`, `wafer`, `설비`) and wired them into `_scan_lines` alongside the existing SCOPE-A path/import tokens.
- Generalized `_is_instance_root_line` → `_is_instance_pointer_line` with a shared regex `\s*(root|persona)\s*=`, exempting the sanctioned `harness/project.toml` `dotnet.persona = "examples/log-parser/agents/dotnet-engineer.md"` line (which legitimately carries both an `examples/` and a `dotnet-engineer` token).
- Added a parametrized per-token negative control (`test_negative_control_flags_each_prose_token`) proving each prose token is live — `wafer`/`설비` are 0-occurrence guaranteed-live anchors.
- Added `test_instance_pointer_persona_is_exempt` — positive proof the persona pointer is NOT flagged.
- Updated the module docstring: guard now enforces the GEN-05 prose tier; removed the "deferred to GEN-05" caveat; documented the deliberately-excluded general terms.
- Closed the transient RED: `test_core_has_no_example_dependency` now passes on the real post-move + post-sweep tree (0 hits; the only remaining core token — the `project.toml:27` persona pointer — is exempted).

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend the GEN-04 guard to prose tokens + generalize the instance-pointer exemption** - `8c56605` (test)

## Files Created/Modified
- `tools/harness_lint/tests/test_core_no_example_dep.py` - Added `_PROSE_TOKENS` + `_INSTANCE_POINTER_LINE` regex; extended `_scan_lines`; renamed/generalized the exemption helper to `_is_instance_pointer_line`; added the parametrized per-token negative control and the persona-pointer positive exemption test; updated the module docstring to the two-tier (SCOPE-A + GEN-05) framing.

## Decisions Made
- Kept the prose token set narrow (proper nouns + rare vocab), explicitly excluding `dotnet`/`.NET`/`parser`/`converter`/`normalize`/`log-parser` to prevent over-reach RED-flags on legitimately-general core text (RESEARCH Pitfall 2).
- Renamed the exemption helper to `_is_instance_pointer_line` (plan-sanctioned optional rename) and drove both `root =` and `persona =` off one shared `_INSTANCE_POINTER_LINE` regex, so the single sanctioned instance-data file exemption is expressed once.
- Kept `test_instance_root_pointer_is_exempt` intact and added `test_instance_pointer_persona_is_exempt` beside it rather than merging, preserving the SCOPE-A regression coverage.

## Deviations from Plan

None - plan executed exactly as written. (A repo formatter reflowed the written file after the Write; the reflow was cosmetic and all 16 guard tests plus the full suite passed.)

## Issues Encountered
None. The pre-execution git-grep confirmed the real tree carried exactly one flagged token in core (`harness/project.toml:27` persona pointer), which the generalized exemption covers — the guard read 0 offenders on first run.

## Verification Results
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x -q` → **16 passed** (guard passes on the real tree, all SCOPE-A + per-token prose negative controls flag, both instance-pointer exemptions pass positively).
- `uv run pytest` (full non-example suite) → **361 passed, 0 failed** (3 snapshots passed). The transient RED is closed.
- `test_core_has_no_example_dependency` → confirmed passing individually (1 passed).

## Next Phase Readiness
- Phase 5.5 authored-surface work is complete: the core planes carry 0 domain/moved-asset prose tokens, provably enforced with per-token tamper-evidence and the sole sanctioned `project.toml` instance-pointer exemption.
- The two-tier guard is ready to catch any future core regrowth of instance/domain vocabulary in CI (Phase 6) and remains stable across the per-language emit work (Phase 7).

## Self-Check: PASSED
- `tools/harness_lint/tests/test_core_no_example_dep.py` — FOUND, defines `_PROSE_TOKENS`, `_is_instance_pointer_line`, `test_instance_pointer_persona_is_exempt`.
- Commit `8c56605` — FOUND in git log.

---
*Phase: 05.5-authored-surface*
*Completed: 2026-07-09*
