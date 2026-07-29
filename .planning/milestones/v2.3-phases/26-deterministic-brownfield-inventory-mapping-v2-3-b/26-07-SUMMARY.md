---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
plan: 07
subsystem: infra
tags: [adoption-scan, git-ls-files, syrupy, snapshot-testing, reproducibility]

requires:
  - phase: 26-06
    provides: destination_catalog() rule-derived enumeration over the live repo file tree
provides:
  - destination_catalog() filtered to git-tracked files only, with a failure-tolerant fallback
  - destination identity derived from the enumerated path, not the resolved symlink target
  - vendor/generated segment denylist reuse (scan.py) as a belt-and-suspenders skip
  - a real git-worktree clean-checkout reproduction test proving catalog invariance
  - build_manifest(catalog=...) injectable-catalog parameter
  - a fixed, small committed manifest snapshot decoupled from the live repo's file count
affects: [27-brownfield-adoption-application]

tech-stack:
  added: []
  patterns:
    - "git ls-files subprocess filter, failure-tolerant (mirrors test_core_no_example_dep.py's idiom but with check=False)"
    - "injectable catalog= keyword parameter to decouple a committed snapshot from live repo state"

key-files:
  created: []
  modified:
    - tools/adoption_scan/destinations.py
    - tools/adoption_scan/tests/test_dispositions.py
    - tools/adoption_scan/tests/test_snapshots.py
    - tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr

key-decisions:
  - "destination_catalog() calls _tracked_repo_files() once per call and reuses the result across the whole enumeration loop, rather than per-candidate, for both determinism and performance."
  - "The fixed manifest-snapshot catalog omits a preserve-reachable row — constructing a hash-equal pair against this harness's own real file content inside a synthetic fixture would defeat the point of decoupling the snapshot from live repo content; preserve stays proven by test_dispositions.py's existing collision-rule tests."

patterns-established:
  - "A committed byte-snapshot test that must stay stable across unrelated repo growth should render over an explicit fixed input list, not a live enumeration — pass the live enumeration as the function's default, and thread an injectable override for the snapshot test."

requirements-completed: [ADOPT-03]

duration: 25min
completed: 2026-07-20
---

# Phase 26 Plan 07: Deterministic Catalog + Snapshot-Decoupling Gap Closure Summary

**`destination_catalog()` is now filtered to git-tracked files only (closing CR-01's clean-checkout non-reproducibility), and the committed manifest snapshot renders over a small fixed catalog instead of the live ~340-row repo file count (closing CR-02) — both proven by an actual `git worktree` clean-checkout reproduction test, not just a green local run.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 completed
- **Files modified:** 4

## Accomplishments
- `destination_catalog()` now excludes any candidate that `git ls-files` does not report as tracked, computed once per call via a new failure-tolerant `_tracked_repo_files()` helper (degrades to unfiltered enumeration when git is unavailable, per D-09).
- Destination identity is now derived from the enumerated `candidate` path (`candidate.relative_to(_REPO_ROOT)`) rather than the resolved symlink target (WR-04) — two distinct symlinks to the same file now produce two distinct catalog rows.
- Added `_SKIP_SEGMENTS` (`scan._VENDOR_SEGMENTS | scan._GENERATED_SEGMENTS`, imported not redefined) as a belt-and-suspenders skip for the git-unavailable fallback path (WR-02).
- `test_total` rewritten as an explicit dispositioned/excluded partition proof with a named `_MIN_CATALOG_ROWS = 300` sanity floor, replacing the vacuously-passable `len(catalog) > 100` check (WR-11).
- Added `test_catalog_invariant_to_untracked_local_state`: spins up a real `git worktree add --detach` at HEAD, runs the catalog inside it via a subprocess, and asserts it equals the current tree's catalog — an actual clean-checkout reproduction, executed and passing (not skipped) in this environment.
- Added `test_catalog_excludes_untracked_file_in_matched_category`: a live-created untracked `.memory/derived/*` file is proven excluded from the catalog while it exists.
- `build_manifest()` gained a keyword-only `catalog: list[dict] | None = None` parameter; every existing caller (`cli.py`, live-catalog structural tests) is unaffected (default `None` preserves the live `destination_catalog()` call).
- `test_snapshots.py` now passes a small, hand-listed `_FIXED_CATALOG` (6 rows spanning 5 of the 6 `DISPOSITION_ENUM` values — `human-ratification-required`, `derived-regenerate`, `marker-merge`, `create`, `conflict` twice) to `build_manifest(..., catalog=...)`, and the committed snapshot's manifest section shrank from ~1360 lines / ~340 rows to 6 rows.

## Task Commits

1. **Task 1: Git-tracked filter (CR-01) + vendor/generated denylist (WR-02) + symlink identity (WR-04) + totality rigor (WR-11)** - `696e2af` (fix)
2. **Task 2: Injectable catalog for build_manifest (CR-02) + fixed-catalog snapshot test + full verify** - `fa52f88` (fix)

## Files Created/Modified
- `tools/adoption_scan/destinations.py` - `_tracked_repo_files()`, `_SKIP_SEGMENTS`, rewritten `destination_catalog()` loop (git-tracked filter + symlink-identity fix + vendor/generated skip), `build_manifest(..., catalog=None)`, updated module/function docstrings
- `tools/adoption_scan/tests/test_dispositions.py` - WR-11 `test_total` rewrite, `_MIN_CATALOG_ROWS` constant, `test_catalog_invariant_to_untracked_local_state`, `test_catalog_excludes_untracked_file_in_matched_category`, `test_catalog_excludes_vendor_and_generated_segments`, `test_symlink_identity_uses_enumerated_path_not_resolved_target`
- `tools/adoption_scan/tests/test_snapshots.py` - `_FIXED_CATALOG` module-level tuple, `build_manifest(..., catalog=list(_FIXED_CATALOG))`
- `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr` - regenerated via `--snapshot-update`; manifest section now 6 rows instead of ~340

## Decisions Made
- `_tracked_repo_files()` is called once at the top of `destination_catalog()`, not per glob candidate, for both determinism (a single consistent snapshot of tracked state per call) and performance (one subprocess spawn instead of hundreds).
- The fixed snapshot catalog deliberately omits a `preserve`-reachable row — constructing a hash-equal fixture pair against this harness's own real file content would couple the "decoupled" snapshot back to live repo content, defeating the purpose of CR-02's fix. `preserve` stays fully proven by `test_dispositions.py::test_each_disposition_reachable` and `test_collision_rule`, which are unchanged.

## Deviations from Plan

None - plan executed exactly as written, including both mandatory line-length fixes required to keep `ruff check`/`ruff format` clean (wrapping two over-100-char lines introduced by new docstring/test prose — mechanical formatting only, no behavior change).

## Issues Encountered

None.

## Clean-Checkout Reproduction Evidence (mandatory acceptance criterion)

Ran the full suite including the real `git worktree` reproduction test (not skipped):

```
$ uv run pytest tools/adoption_scan/tests/test_dispositions.py -q
....................                                                     [100%]
20 passed in 2.01s
```

Catalog row count in the current working tree (which may carry local untracked state):

```
$ uv run python -c "from tools.adoption_scan import destinations; print(len(destinations.destination_catalog()))"
341
```

`test_catalog_invariant_to_untracked_local_state` independently re-derives the SAME catalog inside a fresh `git worktree add --detach <tmp>/clean-worktree HEAD` (no `.memory/derived/*` regen step, no local untracked files) and asserts it equals this 341-row catalog byte-for-byte (as a sorted destination list) — the test passed (not skipped), meaning the git-tracked filter makes the two catalogs identical regardless of local working-tree state. This is the CI-shape reproduction (`actions/checkout` has no untracked derived artifacts), not merely a green run on this working tree.

## Full Verification (Task 2 acceptance criteria)

```
$ uv run pytest tools/adoption_scan -q
..............................................................           [100%]
--------------------------- snapshot report summary ----------------------------
1 snapshot passed.
62 passed in 3.92s

$ uv run python -m tools.contract_drift.drift
contract-drift: OK — live manifest matches the committed baseline.

$ uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q
..................                                                       [100%]
18 passed in 0.08s

$ uv sync --all-packages && git diff --exit-code uv.lock
Resolved 56 packages in 3ms
Checked 30 packages in 1ms
(uv.lock unchanged)
```

`ruff check`/`ruff format --check`/`pyright` all clean on every touched file.

## Next Phase Readiness
- CR-01 and CR-02 from 26-VERIFICATION.md gap 1 are closed; the phase goal's "agent-free, fully CI-testable" property now holds unconditionally — `destination_catalog()` is provably invariant to local untracked state, and the committed snapshot no longer couples to the live repo's growing file count.
- No blockers for Phase 27 (ADOPT-04..07, brownfield-adoption application): this plan touched only `tools/adoption_scan/destinations.py` and its tests, and the manifest shape (`{destination, disposition}` rows + `excluded`) is unchanged.

---
*Phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b*
*Completed: 2026-07-20*
