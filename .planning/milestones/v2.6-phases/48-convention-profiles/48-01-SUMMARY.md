---
phase: 48-convention-profiles
plan: 01
subsystem: infra
tags: [config, python, harness-config, contract-graph, monorepo]

# Dependency graph
requires:
  - phase: 47
    provides: package-facts / effective_packages() layering ([[components]] over derived package graph)
provides:
  - "conventions_for(path, cfg=None, facts=None) — pure nearest-wins join of package facts + [[languages]] config"
  - "_nearest_agents_md(dir_) — bounded filesystem walk for the nearest enclosing AGENTS.md"
affects: [48-02, 48-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Injectable-pure-function convention (cfg=None/facts=None) applied to a new join function for hermetic testing without monkeypatch"
    - "Adapter filter (dir-key presence) kept local to the caller, never pushed into the reused pure utility (ownership.py stays untouched)"

key-files:
  created:
    - tools/harness_config/tests/test_conventions_for.py
  modified:
    - tools/harness_config/loader.py
    - tools/harness_config/__init__.py

key-decisions:
  - "owning_package() reused unmodified from tools.contract_graph — no second path-matcher, no second command table"
  - "Missing-language-row case degrades to None commands (never raises), mirroring effective_packages's declared-only-no-raise posture"
  - "The dir-key adapter filter lives inside conventions_for(), not inside ownership.py, to keep that module pure/dependency-free per its own docstring contract"

patterns-established:
  - "Nearest-wins convention resolution: any future consumer of language/AGENTS.md/command info should call conventions_for(), not re-derive the join"

requirements-completed: [MONO-05, MONO-06]

# Metrics
duration: 25min
completed: 2026-07-30
---

# Phase 48 Plan 01: conventions_for() Nearest-Wins Convention-Profile Lookup Summary

**Added `conventions_for(path)` — a pure join over Phase-47 package facts and the `[[languages]]` config that resolves nearest-enclosing package, commands, and nearest `AGENTS.md`, reusing `owning_package()` unmodified.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-07-30T00:10:00Z
- **Completed:** 2026-07-30T00:36:31Z
- **Tasks:** 2 completed
- **Files modified:** 2 (loader.py, __init__.py), 1 created (test_conventions_for.py)

## Accomplishments
- `conventions_for(path, cfg=None, facts=None)` resolves package/dir/language/test/format/bash_scope/agents_md/is_default via a pure join, with zero new dependency or reimplemented command table.
- `_nearest_agents_md()` performs a bounded (never-escapes-`_REPO_ROOT`) filesystem walk for the nearest enclosing `AGENTS.md`.
- 5 new tests prove MONO-05 (nearest-wins + explicit default) and MONO-06's strong falsifiable command-inheritance form; the falsifiable test was mutation-verified to actually fail.
- `tools/contract_graph/ownership.py` remains byte-unchanged (`git diff --stat` empty).

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement conventions_for() + _nearest_agents_md() and export it** - `d0cad03` (feat)
2. **Task 2: Tests proving MONO-05 nearest-wins/default and MONO-06's falsifiable form** - `8df233d` (test)

**Plan metadata:** (this commit)

## Files Created/Modified
- `tools/harness_config/loader.py` - Added `conventions_for()` + `_nearest_agents_md()`, module-level import of `owning_package`
- `tools/harness_config/__init__.py` - Added `"conventions_for"` to `__all__` (alphabetical; PEP 562 `__getattr__` needed no edit)
- `tools/harness_config/tests/test_conventions_for.py` - 5 new tests (created)

## Decisions Made
- Reused `owning_package()` unmodified; the `"dir"`-key adapter filter (for declared-only components missing a `"dir"` key) lives in `conventions_for()`, never in `ownership.py` — matches the plan's hard constraint and `ownership.py`'s own "touched by nothing" docstring mandate.
- A package whose `language` has no matching `[[languages]]` row returns `test`/`format`/`bash_scope` all `None` rather than raising, mirroring `effective_packages`'s existing "degrade, never raise" posture.
- `_nearest_agents_md` stops its walk once `_REPO_ROOT` itself has been checked — the T-48-01 bounded-walk mitigation from the plan's threat model, implemented as written (no crafted `dir_` can escape the repo tree).

## Deviations from Plan

None - plan executed exactly as written. One micro-adjustment during Task 2 (not a deviation from behavior, purely test-source wording): the test module docstring's use of the literal substrings `"examples/"` and `"monkeypatch"` inside prose (describing what the tests do *not* do) tripped the plan's own `grep -c` acceptance checks for those substrings; reworded to "instance-directory literals" / "monkey-patching" with no change to test logic. Re-verified both `grep -c` checks return `0` after the wording fix.

## Mutation Check (per plan's explicit requirement)

Ran for real, as instructed:
1. Edited `test_editing_language_command_changes_every_affected_profile_with_no_profile_edit`'s final assertion from `after_root["test"] == "NEW"` to `after_root["test"] == "OLD"`.
2. `uv run pytest tools/harness_config/tests/test_conventions_for.py -k test_editing_language_command -x` **FAILED** with `AssertionError: assert ('NEW' == 'OLD' ...)` — confirming the test is genuinely falsifiable, not a "check that cannot fail."
3. Reverted the mutation; re-ran `uv run pytest tools/harness_config/tests/test_conventions_for.py -x -q` → 5 passed.

## Issues Encountered
None.

## Verification Evidence

- `uv run pytest tools/harness_config tools/contract_graph -q` → 76 passed (71 pre-existing + 5 new; zero regressions).
- `git diff --stat -- tools/contract_graph/ownership.py` → empty (module untouched).
- `git diff --stat -- .github/workflows/ci.yml` → empty (zero CI diff, per plan's no-growth constraint).
- `grep -n "examples/" $(git diff HEAD~2 --name-only -- tools/ harness/ libs/)` → no hits (GEN-04 clean).
- All 8 Task-1 acceptance-criteria commands and both Task-2 pytest/grep acceptance criteria re-verified green after the wording fix.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `conventions_for()` is importable, tested, and ready for Plan 02 (derived-artifact rendering into `.memory/derived/package-facts.md`) and Plan 03 (`/component` command step 2 integration) to build on directly.
- No blockers identified.

---
*Phase: 48-convention-profiles*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: tools/harness_config/tests/test_conventions_for.py
- FOUND: .planning/phases/48-convention-profiles/48-01-SUMMARY.md
- FOUND commit: d0cad03
- FOUND commit: 8df233d
