---
phase: 42-adoption-decoupling-install-set-repair
plan: 03
subsystem: adoption-lifecycle
tags: [python, regex, secrets, pytest, adoption, cer-06]

# Dependency graph
requires:
  - phase: 42-adoption-decoupling-install-set-repair
    provides: "Plan 01's delete/git-add/commit/verify ordering discipline (D-12/D-13/D-14), reused
      unchanged for this file-independent plan"
provides:
  - "tools/adoption_scan/scan.py owning SECRET_CONTENT_PATTERNS (8 byte-identical secret regexes)
    locally, no filesystem read of contracts/harness/task-control/gate-registry.json"
  - "test_scan_exclusions.py repointed at scan.SECRET_CONTENT_PATTERNS, dropping its last direct
    read of the old _GATE_REGISTRY_PATH constant"
affects: [44-task-control-plane-removal]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Own the constant locally rather than reading it as DATA from a contract file at import/call
      time, when the contract is scheduled for deletion — same idiom SECRET_PATH_GLOBS already
      used in this module, now extended to SECRET_CONTENT_PATTERNS"

key-files:
  created: []
  modified:
    - tools/adoption_scan/scan.py
    - tools/adoption_scan/__init__.py
    - tools/adoption_scan/tests/test_scan_exclusions.py

key-decisions:
  - "D-04/D-05 as specified in CONTEXT.md: the 8 secret_patterns entries were transcribed fresh
    from the live gate-registry.json (not from this plan's or the prior research's copy) and
    proven byte-identical via a direct tuple-equality assertion, not by visual inspection."
  - "gate-registry.json itself was left untouched (D-06) — only scan.py's read of it was removed;
    Phase 44 (CER-08) owns deleting the contract file."

requirements-completed: [CER-06]

# Metrics
duration: ~15min
completed: 2026-07-28
---

# Phase 42 Plan 03: Inline adoption_scan's Secret Patterns Summary

**Moved the 8 `secret_patterns` regexes `tools/adoption_scan/scan.py` used to read at call-time from `contracts/harness/task-control/gate-registry.json` into a local, byte-identical `SECRET_CONTENT_PATTERNS` tuple, severing the module's last dependency on the task-control contract Phase 44 deletes.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-07-28
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments
- `scan.py` now owns `SECRET_CONTENT_PATTERNS: tuple[str, ...]` (8 entries), placed adjacent to the existing `SECRET_PATH_GLOBS` constant, following that precedent exactly.
- `_secret_pattern()` compiles directly from the local tuple (`"(?:" + "|".join(SECRET_CONTENT_PATTERNS) + ")"`, unchanged `re.IGNORECASE` flag, unchanged `@functools.lru_cache(maxsize=1)` decorator) instead of doing `json.loads()` on the contract file.
- The now-unused `_GATE_REGISTRY_PATH` module constant was deleted; `import json` was kept since `_dump()` still uses `json.dumps` elsewhere in the file.
- `scan.py`'s module docstring (item 2) and `tools/adoption_scan/__init__.py`'s matching paragraph were both updated to describe the new local-tuple sourcing instead of the old "read as DATA from gate-registry.json" phrasing.
- `test_scan_exclusions.py:211` (`test_secret_patterns_1_branch_attribution`), the one test that read `scan._GATE_REGISTRY_PATH` directly, was repointed at `scan.SECRET_CONTENT_PATTERNS[1]`, dropping the `json.loads`/file-read entirely. `json` stayed imported in the test file (still used by `test_readonly`/inventory serialization elsewhere).

## Task Commits

Each task was committed atomically:

1. **Task 1: Inline the 8 secret patterns into scan.py, drop the gate-registry.json read** - `2f8978c` (refactor)
2. **Task 2: Repoint test_scan_exclusions.py:211 at the new local tuple** - `d9c81df` (test)

**Plan metadata:** (this commit, immediately following)

## Files Created/Modified
- `tools/adoption_scan/scan.py` - `SECRET_CONTENT_PATTERNS` tuple added; `_GATE_REGISTRY_PATH` and the `json.loads` registry read removed; docstring item 2 updated
- `tools/adoption_scan/__init__.py` - module docstring's secret-pattern-sourcing paragraph updated to match
- `tools/adoption_scan/tests/test_scan_exclusions.py` - `test_secret_patterns_1_branch_attribution` repointed at `scan.SECRET_CONTENT_PATTERNS[1]`

## Decisions Made
- D-04/D-05 as specified in CONTEXT.md — see frontmatter `key-decisions`.
- No new helper module or dependency was added, per the plan's constraint (rule 6).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Verification

- `uv run pytest tools/adoption_scan -q` -> 85 passed
- `uv run pytest --collect-only -q` (whole repo) -> 1313 tests collected, exit 0
- `grep -c "_GATE_REGISTRY_PATH" tools/adoption_scan/scan.py` -> 0
- `grep -c "SECRET_CONTENT_PATTERNS" tools/adoption_scan/scan.py` -> 3 (definition + docstring reference + use inside `_secret_pattern`)
- Byte-identity proof: `uv run python -c "..."` comparing `tuple(json.load(open('contracts/harness/task-control/gate-registry.json'))['secret_patterns'])` against `scan.SECRET_CONTENT_PATTERNS` -> assertion passed, printed `OK byte-identical`
- `uv run pytest tools/adoption_scan/tests/test_scan_exclusions.py -x` -> all `test_secret_patterns_1_*` tests pass unchanged (proving the copy is faithful, per D-05)
- `grep -rn "task_control" tools/adoption_scan/` -> no matches
- `uv run ruff check tools/adoption_scan/` -> All checks passed
- `git log --oneline -5` shows exactly 2 new commits for this plan's 2 tasks (`2f8978c`, `d9c81df`)

**Changed LOC (D-17, from `git diff --stat`):** 3 files changed, 27 insertions(+), 13 deletions(-)
(`scan.py` +18 net [30 lines touched], `__init__.py` net +2 [7 lines touched], `test_scan_exclusions.py` net -1 [3 lines touched])

## Next Phase Readiness
- `tools/adoption_scan/` no longer reads any file under `contracts/harness/task-control/` — CER-06's remaining live coupling in this package is fully severed.
- `contracts/harness/task-control/gate-registry.json` itself is untouched (D-06); Phase 44 (CER-08) still owns deleting it and rebaselining the manifest.
- No blockers for Plans 02/04/05 or Phase 44.

## Self-Check: PASSED

All claimed modified files and both task commit hashes verified present in the working tree and git history.

---
*Phase: 42-adoption-decoupling-install-set-repair*
*Completed: 2026-07-28*
