---
phase: 42-adoption-decoupling-install-set-repair
plan: 01
subsystem: adoption-lifecycle
tags: [python, cli, argparse, pytest, adoption, cer-06]

# Dependency graph
requires:
  - phase: 41-docs-review-plane-removal
    provides: the delete/git-add/commit/verify ordering discipline (D-12/D-13) and the
      contract-deletion + manifest-rebaseline procedure this milestone reuses
provides:
  - "tools/adoption_apply/ with the whole ADOPT-06 human-ratification gate deleted"
  - "cli.py draft -> apply with no promote subcommand, no check_valid refusal, no approval import"
  - "test_cli.py rewritten: 5 tests deleted, 4 edited, dead helper/fixture/constants removed"
affects: [42-02-contract-and-docstring-cleanup, 43-lifecycle-plane-teardown]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "delete -> git add -> git commit -- <pathspec> -> verify -> amend-if-red ordering (carried
      from Phase 41, reused here for a tracked-file deletion under git-ls-files-reading code)"

key-files:
  created: []
  modified:
    - tools/adoption_apply/cli.py
    - tools/adoption_apply/tests/test_cli.py

key-decisions:
  - "D-01: deleted approval.py whole (promote, check_valid, HUMAN_TOKEN_ENV, the
    tools.task_control import) rather than partially trimming it — nothing meaningful would
    remain to gate once the task-revision element and env token are both removed."
  - "D-03: apply no longer refuses on a missing promotion; draft -> apply is now a two-step
    sequence with the PR as the review boundary (ADR-0012), not a local gate."

requirements-completed: [CER-06]

# Metrics
duration: ~20min
completed: 2026-07-28
---

# Phase 42 Plan 01: Delete the ADOPT-06 Approval Gate Summary

**Deleted `tools/adoption_apply/approval.py` and its `promote`/`check_valid` CLI wiring whole, leaving `draft -> apply` as the only adoption lifecycle path and severing the module's one live `tools.task_control` import.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-28
- **Tasks:** 2/2
- **Files modified:** 4 (2 deleted, 2 edited)

## Accomplishments
- `approval.py` (234 lines) and `test_approval_invalidation.py` (435 lines) deleted whole via `git rm`.
- `cli.py`'s `promote` subcommand, `_cmd_promote`, the `check_valid` apply-refusal block, the two `approval` imports, and the stale docstring paragraph naming `promote`/`golden_runner.approve.py` removed; the now-unused `typing.Any` import and a stale `--repo-root` comment referencing `check_valid`/`promote_parser` were also cleaned up as part of the same edit.
- `test_cli.py` rewritten: 5 promote/refusal-specific test functions deleted outright, 4 apply-path tests edited to drop their `_promote()` precondition (and the now-unused `decisions_path`/`monkeypatch` parameters where `monkeypatch` served no other purpose), and the dead `_promote()` helper, `decisions_path` fixture, and `HUMAN_TOKEN_ENV`/`_HUMAN_VALUE`/`_DECISIONS` module constants removed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Delete approval.py + cli.py's promote/check_valid wiring + test_approval_invalidation.py** - `733db6f` (refactor)
2. **Task 2: Rewrite test_cli.py — delete 5 tests, edit 4, remove dead helper/fixture/constants** - `9025a05` (test)

**Plan metadata:** (this commit, immediately following)

## Files Created/Modified
- `tools/adoption_apply/approval.py` - deleted (the whole ADOPT-06 gate)
- `tools/adoption_apply/tests/test_approval_invalidation.py` - deleted (exercised only the deleted module)
- `tools/adoption_apply/cli.py` - `promote` subcommand, `check_valid` refusal, approval imports removed; `draft`/`apply` are the only subcommands
- `tools/adoption_apply/tests/test_cli.py` - 5 tests deleted, 4 tests edited to drop the promote precondition, dead helper/fixture/constants removed

## Decisions Made
- D-01/D-03 as specified in CONTEXT.md — no replacement gate was invented; the review moves to the PR per ADR-0012's DEV/PRODUCT boundary.
- Removed the now-orphaned `typing.Any` import in `cli.py` (it was imported solely for `_cmd_promote`'s `decisions` parameter typing) — a direct, in-scope consequence of the deletion, not a separate decision requiring its own commit.

## Deviations from Plan

None - plan executed exactly as written. The two additional cleanups noted above (unused `Any` import, one stale inline comment) were direct fallout of the exact deletions the plan specified, verified via `ruff check tools/adoption_apply/` returning clean, not independent scope additions.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Verification

- `uv run pytest tools/adoption_apply -q` → 73 passed
- `uv run pytest --collect-only -q` (whole repo) → 1313 tests collected, exit 0
- `test ! -f tools/adoption_apply/approval.py` → exit 0
- `test ! -f tools/adoption_apply/tests/test_approval_invalidation.py` → exit 0
- `grep -n "check_valid\|approval_promote\|_cmd_promote\|promote_parser" tools/adoption_apply/cli.py` → no matches
- `grep -rn "GOLDEN_APPROVE_HUMAN" tools/adoption_apply/` → no matches
- `grep -rn "from tools.adoption_apply.approval\|import approval" tools/adoption_apply/` → no matches
- `grep -c "^def test_" tools/adoption_apply/tests/test_cli.py` → 5
- `grep -rn "task_control" tools/adoption_apply/` → only the prose hits enumerated in RESEARCH.md's Coupling Map (`apply.py:16/:207/:241`, `batch.py` x5) — Plan 02's job, untouched here, matching the plan's own out-of-scope note
- `uv run ruff check tools/adoption_apply/` → All checks passed
- `git log --oneline -5` shows exactly 2 new commits for this plan's 2 tasks (`733db6f`, `9025a05`)

**Changed LOC (D-17, from `git diff --stat`):** 4 files changed, 13 insertions(+), 956 deletions(-)
(`approval.py` -233, `cli.py` net -47 [66 lines touched], `test_approval_invalidation.py` -435, `test_cli.py` net -226 [235 lines touched])

## Next Phase Readiness
- `tools/adoption_apply/` no longer imports `tools.task_control` or reads `GOLDEN_APPROVE_HUMAN`; the one live coupling this plan targeted (CER-06's `approval.py:37` import) is severed.
- Prose-only `task_control` references remain in `apply.py` (`:16`, `:207`, `:241`) and `batch.py` (x5) — explicitly deferred to Plan 02 per this plan's scope boundary (rule 6).
- `contracts/harness/adoption/approval.schema.json` and its `contracts/.hashes/manifest.json` entry are now orphaned (D-02) and remain for Plan 02 to delete + rebaseline.
- No blockers for Plan 02.

## Self-Check: PASSED

All claimed created/deleted files and both task commit hashes verified present in the working tree and git history.

---
*Phase: 42-adoption-decoupling-install-set-repair*
*Completed: 2026-07-28*
