---
phase: 52-evidence-bounded-real-target-adoption
plan: 04
subsystem: infra
tags: [python, fcntl, apply, adoption-apply, memory-regen, lock-sidecar]

# Dependency graph
requires:
  - phase: 52-01
    provides: "contracts/harness/adoption/inventory.schema.json non-workspace-member enum (unrelated to this plan's scope; wave-1 dependency only)"
provides:
  - "lock_sidecar_for()/expected_lock_sidecars()/HARNESS_MANAGED_LOCK_SIDECARS declare the 3 marker-merge flock sidecars as known harness-managed artifacts, checked against the real filesystem via rglob rather than a restatement of the naming rule"
  - "_apply_marker_merge reports a prior-run lock sidecar on stderr with honestly-scoped provenance wording (never 'stale'), conditional on a fresh non-blocking acquisition succeeding, with mutual exclusion and merged-content byte-identity provably unchanged"
  - "test_workspace_star_dependency_edges_resolve_by_name locks in the Phase-51 OBS-03 refutation (workspace:*/workspace:^ dependencies resolve to real runtime/dev edges) with zero production change"
affects: [52-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Non-blocking-first flock: try LOCK_EX|LOCK_NB, fall back to the blocking LOCK_EX only on BlockingIOError/OSError — lets the success path distinguish 'sidecar pre-existed and was just acquired' from 'another holder currently has it', without weakening the blocking guarantee for the genuinely-held case."
    - "Mutation-then-revert-in-place verification via a saved backup file, applied directly to the working tree, observed red, then restored byte-for-byte — used three times in this plan (Task 1's dot-drop mutation, Task 2's unconditional-report mutation, Task 3's version-string-skip mutation)."

key-files:
  created: []
  modified:
    - tools/adoption_apply/apply.py
    - tools/adoption_apply/tests/test_atomic_apply.py
    - tools/memory_regen/tests/test_package_facts.py

key-decisions:
  - "The prior-run report fires only when the non-blocking acquisition succeeds AND the sidecar pre-existed — a genuinely held lock takes the blocking fallback path with no report, so T-52-12 (misreading a held lock as a leftover) cannot occur."
  - "The message names only what the predicate proves ('a lock sidecar from a prior run ... acquired, not silently reused') — never 'stale'. Under D-15's no-unlink rule the sidecar exists on every run after the first, so a staleness claim would be false on ~100% of re-runs; this is recorded as a known gap, not a working staleness signal, for Phase 53 to inherit knowingly."
  - "test_marker_merge_acquires_exclusive_flock's assertion was widened from `call.args[1] == fcntl.LOCK_EX` to a bitmask check (`call.args[1] & fcntl.LOCK_EX == fcntl.LOCK_EX`) because Task 2's fast path now calls flock with `LOCK_EX | LOCK_NB` on the first attempt — a legitimate test update for the new correct behavior, not a weakening of the assertion (it still fails if the LOCK_EX bit is ever dropped)."

requirements-completed: [RTA-03, OBS-02]

# Metrics
duration: ~35min active work (single continuous session, no checkpoints)
completed: 2026-08-01
---

# Phase 52 Plan 04: Evidence-Bounded Real-Target Adoption — Lock-Sidecar Declaration + Prior-Run Report + OBS-D-02 Lock-In Summary

**The three marker-merge `.lock` sidecars are declared as known harness-managed artifacts (not unlinked), a sidecar left over from a prior run is announced on stderr with wording that claims only provenance, and the Phase-51 `workspace:*` refutation is locked in by a regression test with zero production change.**

## Performance

- **Tasks:** 3/3 completed
- **Files modified:** 3 (0 created, 3 modified)

## Accomplishments

- `lock_sidecar_for("AGENTS.md") == ".AGENTS.md.lock"` etc. (`tools/adoption_apply/apply.py`), `expected_lock_sidecars(destinations)` filters through the imported `MARKER_CAPABLE` frozenset (never retyped), and `HARNESS_MANAGED_LOCK_SIDECARS` is the frozenset Plan 05's phase-local comparison will import as its allowlist. The filesystem-agreement test drives every `MARKER_CAPABLE` destination through the real `_apply_marker_merge`, then compares an `rglob("*.lock")` scan of the temp target to `expected_lock_sidecars(MARKER_CAPABLE)` — the declaration is checked against reality, never against a copy of its own formula.
- `_apply_marker_merge` now captures `pre_existed = lock_path.exists()` before opening the sidecar, tries a non-blocking `LOCK_EX | LOCK_NB` acquisition first, and — only when that acquisition succeeds AND a sidecar pre-existed — prints one stderr line: `apply: lock sidecar from a prior run at {lock_path} — acquired, not silently reused (sidecars are never unlinked, D-15)`. A genuinely held lock (another holder currently inside the critical section) falls through to the original blocking `flock(LOCK_EX)` with no report. The word "stale" appears nowhere in the new code or message.
- `test_workspace_star_dependency_edges_resolve_by_name` (`tools/memory_regen/tests/test_package_facts.py`) builds a synthetic `packages/widget-shared` + `apps/widget-app` + `apps/widget-service` pnpm-shaped tree and asserts both the `workspace:*` runtime edge and the `workspace:^` dev edge resolve by name, plus that an unresolvable `@widget/ghost` dependency yields no edge. Zero production code changed — `detect.py:273` is confirmed correct, not repaired.
- No sidecar was unlinked anywhere in this plan; `_read_target_no_symlink`, `_atomic_replace`, `atomic_create`, and `refuse_unsafe_destination` are all byte-for-byte unchanged.

## Task Commits

Each task was committed atomically:

1. **Task 1: Declare the marker-merge lock sidecars as known harness-managed artifacts** - `0472ade` (feat)
2. **Task 2: Report a prior-run lock sidecar on stderr instead of silently reusing it** - `9a1432b` (feat)
3. **Task 3: OBS-D-02 lock-in — workspace:* dependencies must keep resolving to real edges** - `1017579` (test)

## Files Created/Modified

- `tools/adoption_apply/apply.py` - `lock_sidecar_for()`, `expected_lock_sidecars()`, `HARNESS_MANAGED_LOCK_SIDECARS` (Task 1); `_apply_marker_merge`'s non-blocking-first flock + conditional stderr report (Task 2)
- `tools/adoption_apply/tests/test_atomic_apply.py` - 4 new Task-1 tests (naming rule, filter, filesystem-agreement, frozenset value), 4 new Task-2 tests (prior-run report, fresh-target negative control, held-lock-still-blocks, byte-identical merged content), and one pre-existing assertion widened to a bitmask check (see Decisions)
- `tools/memory_regen/tests/test_package_facts.py` - 1 new test (`test_workspace_star_dependency_edges_resolve_by_name`), no production file touched

## Decisions Made

See `key-decisions` in frontmatter: the fast-path-with-fallback flock structure (T-52-12 mitigation), the honestly-scoped "provenance not staleness" wording (D-15/D-16 tension), and the widened `test_marker_merge_acquires_exclusive_flock` bitmask assertion.

## Mutation Evidence (checks-that-cannot-fail guard)

All three observed-RED mutations were applied directly to the working tree via a saved backup file, the target test run and observed red, then the file restored byte-for-byte from the backup before the task's commit.

**1. Task 1 — dropping the leading dot from `lock_sidecar_for`'s formula** (`name + ".lock"` instead of `"." + name + ".lock"`), guards `test_expected_lock_sidecars_matches_filesystem_after_every_marker_merge` and `test_lock_sidecar_for_matches_the_three_phase51_paths`:
```
AssertionError: assert {'.AGENTS.md....gs.json.lock'} == {'.claude/set...AUDE.md.lock'}
  Extra items in the left set:
  '.CLAUDE.md.lock'
  '.AGENTS.md.lock'
  '.claude/.settings.json.lock'
  Extra items in the right set:
  '.claude/settings.json.lock'...
```

**2. Task 2 — making the prior-run report unconditional** (dropping the `pre_existed` guard, `if True:` instead of `if pre_existed:`), guards `test_fresh_target_emits_no_prior_run_lock_sidecar_report`:
```
AssertionError: assert 'lock sideca... a prior run' not in 'apply: lock...ked, D-15)\n'
  'lock sidecar from a prior run' is contained here:
  apply: lock sidecar from a prior run at /private/var/.../.AGENTS.md.lock — acquired, not silently reused (sidecars are never unlinked, D-15)
```

**3. Task 3 — making `_dependencies_from_package_json` skip entries whose version starts with `workspace:`** (a version-string-sensitive resolution, the exact regression class OBS-03 refuted), guards `test_workspace_star_dependency_edges_resolve_by_name`:
```
AssertionError: assert {'from': 'widget-app', 'kind': 'runtime', 'to': '@widget/shared'} in []
```

Each mutation was reverted from its saved backup and `git diff --quiet` confirmed the target file returned to exactly the intended committed state before staging.

## Own-authorship fences (reviewer-checked, not automated)

Per this plan's `<parallel_execution_note>` and per-task acceptance criteria, the staged set (`git diff --cached --name-only`) was checked immediately before every commit:

- Task 1 commit staged exactly: `tools/adoption_apply/apply.py`, `tools/adoption_apply/tests/test_atomic_apply.py`
- Task 2 commit staged exactly: `tools/adoption_apply/apply.py`, `tools/adoption_apply/tests/test_atomic_apply.py`
- Task 3 commit staged exactly: `tools/memory_regen/tests/test_package_facts.py` (no production file — `git diff --quiet -- tools/memory_regen/package_facts.py tools/adoption_scan/detect.py` succeeded)

No commit in this plan lists `tools/harness_config/**`, `tools/adoption_apply/cli.py`, `tools/adoption_apply/tests/conftest.py`, or `tools/adoption_apply/tests/test_cli.py` — all 52-03-owned. In this serialized (non-worktree) execution, 52-03 had already fully completed and committed before this plan started, so there was no actual concurrent writer to fence against; the checks above passed trivially as the wave note anticipated, and are recorded for the record rather than because a real race was observed.

## Deviations from Plan

**1. [Rule 1 - Bug-adjacent test fix] Widened `test_marker_merge_acquires_exclusive_flock`'s flag assertion to a bitmask check**
- **Found during:** Task 2
- **Issue:** The pre-existing test asserted `call.args[1] == fcntl.LOCK_EX` (the bare flag value). Task 2's non-blocking-first fast path now calls `flock(fileno, fcntl.LOCK_EX | fcntl.LOCK_NB)` on the first attempt, so the exact-value assertion is never satisfied by that call even though the `LOCK_EX` bit is correctly set.
- **Fix:** Changed the assertion to `call.args[1] & fcntl.LOCK_EX == fcntl.LOCK_EX`, which still fails if the `LOCK_EX` bit is ever dropped from any call (the property the test exists to protect), but tolerates the additional `LOCK_NB` bit.
- **Files modified:** `tools/adoption_apply/tests/test_atomic_apply.py`
- **Verification:** `uv run pytest tools/adoption_apply/tests/test_atomic_apply.py -q` green (21 passed); this is the only deleted line in the diff to that file, and it lies outside `_observe_marker_merge_concurrency`/`_assert_mutual_exclusion`/`test_concurrency_control_removal_is_detected`, so the mutual-exclusion proof and its negative control remain unmodified as the plan requires.
- **Committed in:** `9a1432b` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1, test assertion widened to accommodate a correct behavioral change).
**Impact on plan:** Necessary consequence of Task 2's flock structure change; no scope creep, no weakening of what the test protects against.

## Issues Encountered

None beyond the one deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 52-05 (phase-local apply comparison) can import `tools.adoption_apply.apply.HARNESS_MANAGED_LOCK_SIDECARS` directly as its allowlist for the `matches`/`unexpected_paths` computation (D-21).
- The D-15/D-16 limitation is recorded here for Phase 53: the prior-run report cannot distinguish a normal re-run from a crash-interrupted one, and this is a deliberate scope boundary (NG-01), not an oversight.
- Full suite green: `uv run pytest -q` → 1006 passed, 8 snapshots passed (up from 997 in 52-03; +9 new tests across the three tasks).

---
*Phase: 52-evidence-bounded-real-target-adoption*
*Completed: 2026-08-01*

## Self-Check: PASSED

All claimed files exist (`tools/adoption_apply/apply.py`, `tools/adoption_apply/tests/test_atomic_apply.py`, `tools/memory_regen/tests/test_package_facts.py`) and all three claimed commit hashes (`0472ade`, `9a1432b`, `1017579`) are present in `git log --oneline --all`.
