---
phase: 06-ci-gates
plan: 01
subsystem: infra
tags: [ci, config-ssot, tomllib, gen-03, gen-04, test-matrix]

# Dependency graph
requires:
  - phase: 05 (GEN-03/GEN-04 harness config + guards)
    provides: harness/project.toml SSOT slot, languages() passthrough loader, core-no-example-dep guard
provides:
  - per-language test_paths data slot in harness/project.toml (dotnet .csproj + python example tests dir)
  - languages() surfaces test_paths unchanged (raw passthrough, no signature change)
  - Wave-0 matrix-shape test asserting the CI include-list built from languages()
  - SSOT consistency gate extended to verify test_paths presence + on-disk existence
  - widened GEN-04 instance-pointer exemption (root|persona|test_paths) with a live negative control
affects: [06-02, 06-03, ci.yml matrix emitter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive config data-slot consumed via raw passthrough (l.get('test_paths', []))"
    - "Key-scoped + file-scoped guard exemption paired with a tamper-evidence negative control"

key-files:
  created:
    - tools/harness_config/tests/test_matrix_emit.py
  modified:
    - harness/project.toml
    - tools/harness_config/loader.py
    - tools/harness_lint/tests/test_language_config.py
    - tools/harness_lint/tests/test_core_no_example_dep.py

key-decisions:
  - "dotnet test_paths names Normalize.Tests.csproj explicitly (3 .csproj + no .sln → bare `dotnet test` fails)"
  - "python test_paths = examples/log-parser/tests (example pytest lives off root testpaths)"
  - "Guard exemption widened to (root|persona|test_paths) — same precedent as the persona pointer; kept key+file scoped so genuine leaks still trip"

patterns-established:
  - "test_paths is additive and inert to language_bash_scopes() — SSOT scope equality gate unchanged"
  - "Every widened exemption ships with a negative control proving the scan stays live"

requirements-completed: [CI-01]

# Metrics
duration: 6min
completed: 2026-07-09
---

# Phase 6 Plan 01: test_paths CI-matrix data slot Summary

**Per-language `test_paths` data slot added to `harness/project.toml` (explicit dotnet test .csproj + python example tests dir), surfaced through the `languages()` passthrough, gated by a Wave-0 matrix-shape test and an on-disk-existence consistency check, with the GEN-04 core-no-example-dep guard widened by construction to sanction the new instance-pointer line.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-07-09T13:11:30Z
- **Completed:** 2026-07-09T13:16:46Z
- **Tasks:** 3 (Task 1 + Task 2 TDD)
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments
- Landed the config-declared `test_paths` SSOT slot the Wave-2 CI matrix consumes (D-01 config-derived, not hardcoded) for both the dotnet and python legs.
- `languages()` surfaces `test_paths` with zero signature change (raw passthrough; docstring note only).
- Widened the GEN-04 `_INSTANCE_POINTER_LINE` exemption to `(root|persona|test_paths)` BY CONSTRUCTION so the guard stays green, and added a live negative control proving the scan still flags a genuine `examples/` leak on any non-pointer key.
- Confirmed every declared `test_paths` entry exists on disk (`.csproj` file + tests directory).

## Task Commits

1. **Task 1 (RED): matrix-shape test** — `92d649d` (test)
2. **Task 2 (GREEN): test_paths data slot + loader note** — `3aecd44` (feat)
3. **Task 3: SSOT gate + widened GEN-04 exemption + negative control** — `8acc240` (test)

_Task 1/2 form the TDD RED→GREEN pair for the `test_paths` field._

## Files Created/Modified
- `tools/harness_config/tests/test_matrix_emit.py` — Wave-0 test building the CI matrix include-list from `languages()` (id + test + list[str] test_paths, one leg per language).
- `harness/project.toml` — additive `test_paths` array on both `[[languages]]` tables (data-only).
- `tools/harness_config/loader.py` — docstring note that legs may carry an optional `test_paths` (no signature change).
- `tools/harness_lint/tests/test_language_config.py` — `test_each_configured_language_has_test_paths` (list[str], non-empty, `.exists()` on disk).
- `tools/harness_lint/tests/test_core_no_example_dep.py` — widened `_INSTANCE_POINTER_LINE` + comment/docstring; two new tests (`test_instance_pointer_test_paths_is_exempt`, `test_negative_control_flags_nonexempt_project_toml_leak`).

## Decisions Made
- Named the dotnet test project explicitly (`Normalize.Tests/Normalize.Tests.csproj`) because the example has 3 `.csproj` and no `.sln`, so a bare `dotnet test` cannot resolve a project.
- Used `.exists()` (not `.is_file()`) for the on-disk check since the dotnet target is a file but the python target is a directory.
- Kept the guard exemption key-scoped (`root|persona|test_paths`) and file-scoped (`harness/project.toml`) rather than a blanket pass, preserving GEN-04 tamper-evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reworded my own docstring to avoid a self-inflicted GEN-04 leak**
- **Found during:** Task 3 (verify)
- **Issue:** The `test_each_configured_language_has_test_paths` docstring I added literally contained the string `examples/log-parser/tests`, which the GEN-04 `_PATH_TOKENS` scan (`examples/`) correctly flagged as a core-plane example reference — a leak introduced by my own edit.
- **Fix:** Reworded the docstring to say "a tests directory" without the raw `examples/` path token. The behavioral `.exists()` assertion is unchanged (the path still comes from config data, which is exempt).
- **Files modified:** `tools/harness_lint/tests/test_language_config.py`
- **Verification:** `test_core_has_no_example_dependency` no longer reports my file; my 4 key tests pass.
- **Committed in:** `8acc240` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — self-inflicted, fixed inline).
**Impact on plan:** No scope creep. The `test_paths` values, loader passthrough, SSOT gate, and guard widening all landed exactly as planned.

## Issues Encountered

**Concurrent 06-02 introduced a GEN-04 failure in the shared branch (OUT OF SCOPE — not fixed).**

The full non-example suite reports `412 passed, 1 failed`. The single failure is
`test_core_has_no_example_dependency`, tripped by a **06-02-owned** file:
`tools/contract_drift/tests/test_cli_flags.py:49` —
`schema = contracts / "state" / "equipment-progress.schema.json"` carries the GEN-05 prose token
`equipment`. This was committed by 06-02 (`39f57d0`), interleaved on the shared branch AFTER
06-01's Task-1 commit — it is not caused by any 06-01 change.

- Per the scope boundary (only fix issues directly caused by this task) and the explicit instruction
  to leave concurrent 06-02 files untouched, this was NOT fixed here.
- The offending line is a `schema =` assignment, NOT a `harness/project.toml` instance-pointer, so it
  is correctly OUTSIDE 06-01's key-scoped exemption; widening the guard to cover it would over-broaden
  GEN-04 and defeat the negative control. Resolution belongs to 06-02.
- Logged to `.planning/phases/06-ci-gates/deferred-items.md`.
- **Proof 06-01 is green in isolation:** deselecting only that one 06-02 test →
  `uv run pytest` = **412 passed**; `uv run pytest tools/harness_config tools/harness_lint` = **168 passed**.

## Verification Results

- `uv run pytest tools/harness_config tools/harness_lint -q` → **168 passed, 1 failed** (the sole failure is the 06-02 `equipment` leak; 168 passed with it deselected).
- `uv run pytest` (full non-example suite) → **412 passed, 1 failed** (same single 06-02-owned failure; 412 passed with it deselected).
- Declared `test_paths` on-disk: both `EXISTS` (`Normalize.Tests.csproj` + `examples/log-parser/tests`).
- SSOT gate `test_matrix_language_scopes_equal_config` still passes (additive field inert to `language_bash_scopes()`).

## User Setup Required
None.

## Next Phase Readiness
- The `test_paths` SSOT slot is ready for the Wave-2 `ci.yml` matrix emitter to fan out over.
- **Blocker for the phase (not for this plan):** 06-02 must resolve its `equipment`-token GEN-04 leak in `test_cli_flags.py` before the full-suite gate goes green.

## Self-Check: PASSED

- Created files present: `test_matrix_emit.py`, `06-01-SUMMARY.md`, `deferred-items.md`.
- Task commits present: `92d649d`, `3aecd44`, `8acc240`.

---
*Phase: 06-ci-gates*
*Completed: 2026-07-09*
