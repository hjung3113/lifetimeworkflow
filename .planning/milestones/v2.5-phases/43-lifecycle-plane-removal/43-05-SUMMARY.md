---
phase: 43-lifecycle-plane-removal
plan: 05
subsystem: infra
tags: [lifecycle-plane, deletion, CER-07, contract-drift, syrupy-snapshot, ruamel-yaml, readme-sweep, uv-lock]

# Dependency graph
requires:
  - phase: 43-lifecycle-plane-removal
    plan: "43-04"
    provides: tools/lifecycle_eval + the 8 workspace members deleted, the CI lifecycle-eval job
      and its jobs.gate.needs entry removed in that same commit (SIM-1), and the
      test_tests_are_isolatable.py / test_install_completeness.py literals already repaired —
      leaving only the constitution-plane contracts, the derived plane, the two READMEs and
      uv.lock for this wave
provides:
  - contracts/harness/task-control/ reduced to gate-registry.json alone (6 of 7 deleted), with
    contracts/.hashes/manifest.json rebaselined 15 -> 9 documents in the SAME commit and
    contract-drift green
  - DATA_CONTRACT_PATHS narrowed to gate-registry.json + deny-domains.json, with
    test_hash.py's expected set narrowed in the same commit and a negative control over the
    retained transitions fixture (B-3)
  - docs_sync EXPECTED_PAGES shrunk 12 -> 7, the 5 orphaned docs/reference pages pruned by the
    generator, and both live-tree syrupy snapshots (docs_sync determinism, contracts_index)
    regenerated in that same commit (BLOCKER-1 close-out)
  - README.md + README.ko.md swept of every deleted module/command/package reference, with the
    CI fan-in line REGENERATED from the ruamel-resolved jobs.gate.needs (W-8) and all three
    hardcoded test counts set to the measured 982
  - uv.lock refreshed — no reference to any of the 8 removed workspace members
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [in-commit manifest rebaseline alongside contract deletion (Phase 41 precedent),
    in-commit regeneration of live-tree syrupy snapshots invalidated by the same commit's
    deletion, prose mirrors of resolved config REGENERATED from the resolver rather than
    token-edited (W-8), pathspec-scoped commits with message-first / `--` last]

key-files:
  created: []
  modified:
    - contracts/harness/task-control/{attestation,evidence,handoff,state,task}.schema.json (deleted)
    - contracts/harness/task-control/transitions.json (deleted)
    - contracts/.hashes/manifest.json (rebaselined, 15 -> 9 documents)
    - tools/contract_hash/hash.py (DATA_CONTRACT_PATHS: transitions.json entry removed)
    - tools/contract_hash/tests/test_hash.py (expected set narrowed + negative control)
    - tools/docs_sync/tests/test_docs_sync_determinism.py (EXPECTED_PAGES 12 -> 7)
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr (regenerated)
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr (regenerated, 9 contracts)
    - docs/reference/{attestation,evidence,handoff,state,task}.md (pruned by the generator)
    - .memory/derived/contracts-index.md (regenerated, 15 -> 9 contracts)
    - README.md (fan-in line regenerated; v2.2 row, command-tour entries, quickstart block and
      milestone bullets removed; test count 904 -> 982)
    - README.ko.md (v2.2 section, quickstart block and layout lines removed; roadmap bullet
      rewritten; test count 904 -> 982)
    - uv.lock (8 removed workspace members dropped, 66 lines)

key-decisions:
  - "Reworded the B-3 negative-control comment so it does not contain the literal token
    `transitions.json`. The repo's format-on-write hook had already reflowed the test function,
    and my first comment wording pushed `grep -c \"transitions.json\" test_hash.py` to 3 — the
    plan's acceptance criterion measures exactly 2 (the retained fixture write + the assertion).
    The criterion was treated as load-bearing and the comment was changed to match it, not the
    other way round."
  - "Staged Task 1's deletions with `git rm` (for the 5 generator-pruned docs/reference pages)
    plus a path-scoped `git add` for the modified files, because `git add -- <path>` refuses a
    pathspec whose file no longer exists on disk. `git add -A` was never used, in any form."
  - "Left README.md's `milestones-v1.0–v2.2 shipped` badge (:16) untouched — it is milestone
    history, names no deleted path, and is outside the plan's enumerated site list."

requirements-completed: [CER-07]

# Metrics
duration: ~30min
completed: 2026-07-28
---

# Phase 43 Plan 05: Contract Deletion, Derived-Plane Rebaseline and README Sweep Summary

**Deleted the last 6 task-control contracts with a same-commit manifest rebaseline, narrowed the
`DATA_CONTRACT_PATHS` tuple and the test that reads it, pruned the 5 orphaned reference pages and
regenerated both live-tree syrupy snapshots in that same commit, then swept both READMEs — including
regenerating the CI fan-in line from the YAML-resolved `gate.needs`, which repaired a pre-existing
missing-`lint` drift — and refreshed `uv.lock`.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-07-28
- **Tasks:** 2 completed, 2 commits
- **Files modified:** 21 across 2 commits

## Task Commits

1. **Task 1: Delete the 6 task-control contracts, rebaseline, narrow the expected set, regenerate the derived plane and both snapshots** — `9105f0b` (feat) — 18 files, 17 insertions / 978 deletions
2. **Task 2: Regenerate the fan-in line, sweep both READMEs, refresh uv.lock** — `c92c869` (docs) — 3 files, 16 insertions / 152 deletions

## Accomplishments

- `git rm`'d `attestation`, `evidence`, `handoff`, `state`, `task` schemas and `transitions.json`;
  **`gate-registry.json` survives untouched** for Phase 44 (CER-08), as does its `DATA_CONTRACT_PATHS`
  entry and `deny-domains.json`'s. `ls contracts/harness/task-control/` shows exactly one file.
- Rebaselined `contracts/.hashes/manifest.json` in the same commit: `wrote contracts/.hashes/manifest.json
  (9 contract JSON documents hashed)`; `tools.contract_drift.drift` exit 0.
- B-3 repaired in that same commit: `test_hash.py`'s expected set is now
  `{"contracts/harness/task-control/gate-registry.json"}`, the `transitions.json` fixture write is
  **retained**, and an explicit `assert "contracts/harness/task-control/transitions.json" not in before`
  proves the tuple entry was dropped rather than the fixture. The registry-mutation half is untouched.
- `EXPECTED_PAGES` shrunk 12 → 7 (`attestation`, `evidence`, `handoff`, `state`, `task` removed;
  `deny-domains`, `format-conventions`, `greeting`, `inventory`, `manifest`, `plan`, `relationship`
  retained). `python -m tools.docs_sync` **pruned** the 5 orphaned pages itself — none was hand-deleted.
- Both live-tree syrupy snapshots regenerated with `--snapshot-update` and re-verified non-updating
  **before** the commit, and both landed **inside** it (BLOCKER-1 closed).
- W-5 held exactly as documented: `git ls-files .memory/derived/` lists only `contracts-index.md`;
  `repo_map` was run and staged nothing.
- SIM-1 confirmed read-only before any Task 2 edit: `jobs.gate.needs` resolves to **10** entries with
  `lifecycle-eval` absent from both `needs` and `jobs`. `.github/workflows/ci.yml` was never opened
  for writing and does not appear in either commit.
- W-8 satisfied by regeneration, not token-editing: the resolver printed
  `setup, lang-tests, contract-check, drift, golden, core-suite, lint, emit-drift, stale-derived, workspace, gate`
  and that exact string was pasted into `README.md`. The byte-equality criterion passes, which also
  means the **pre-existing missing-`lint` error is now repaired**. `README.ko.md` gained no fan-in line
  (`grep -c "core-suite" README.ko.md` → 0).
- Both READMEs swept: the B-5 residue grep over 15 alternatives returns **no output** (exit 1);
  `/pipeline` retained (Phase 44's); `README.ko.md:133`'s `how-to/task-lifecycle.md` reference retained
  (W-2 carry-forward). Milestone history was **rewritten, not deleted** — both files now record the
  plane as shipped in v2.2 and removed in v2.5 under CER-07, naming no deleted path.
- `uv.lock` refreshed via `uv sync --all-packages`; all 8 removed workspace members return `grep -c` 0.
- Test counts written from this plan's own measured run: **982**, into `README.md:12` badge,
  `README.md`'s `# 2. Run the full harness test suite` comment, and `README.ko.md`'s
  `# 2. 전체 하네스 테스트 스위트` comment.

## Verification Results

| Gate | Result |
|------|--------|
| `uv run pytest -q` (after Task 1 commit) | **982 passed, 7 snapshots** |
| `uv run pytest -q` (after Task 2 commit) | **982 passed, 7 snapshots** |
| `uv run pytest --collect-only -q` | 982 tests collected, 0 errors |
| `uv run python -m tools.contract_drift.drift` | exit 0 — live manifest matches baseline |
| `python -m tools.harness_emit && git diff --exit-code` (emit-drift, bare) | exit 0 |
| stale-derived (docs_sync + contracts_index regen, no diff) | exit 0 |
| `uv run python -m tools.ruff_baseline.ratchet` | exit 0 (clean; `--update` not run — nothing to shrink) |
| SIM-1 ruamel confirmation of `jobs.gate.needs` | exit 0 — 10 entries, `lifecycle-eval` absent |
| W-8 README byte-equality vs resolved `gate.needs + gate` | exit 0 |
| B-5 residue grep over both READMEs | no output (exit 1) |
| `tools/adoption_scan/tests/test_install_completeness.py` | 3 passed; live module count **13** |
| `git status --porcelain -- <both .ambr>` | empty |

**Pitfall 4 red window observed and ignored as documented** — the three `adoption_scan` tests were not
polled mid-window; the plan's instruction to run the full suite only *after* the commit was followed
literally, and the post-commit suite was green on the first run, so the window closed exactly as the
simulation predicted.

## D-18 — Whole-phase LOC removed (measured, not estimated)

`git diff --shortstat f589a67..HEAD` (baseline = `f589a67 chore(43): mark phase 43 planned`, the last
commit before 43-01's first code commit):

- **Including `.planning/`:** 157 files changed, 943 insertions(+), **12383 deletions(-)**
- **Excluding `.planning/` (code + docs + config only):** 153 files changed, 199 insertions(+),
  **12383 deletions(-)** — net **−12184** lines

Both figures clear the `>= 7021` expectation by a wide margin.

## Deviations from Plan

**1. [Rule 3 — Blocking] `git add -- <path>` cannot stage an already-deleted file.**
- **Found during:** Task 1, at the staging step.
- **Issue:** `git add -- contracts/harness/task-control/attestation.schema.json` aborted with
  `fatal: pathspec ... did not match any files`, because the file was already gone from the worktree
  (5 of them removed by the `docs_sync` generator's prune, 6 by `git rm`).
- **Fix:** the 6 contracts were already staged by `git rm`; the 5 generator-pruned reference pages were
  staged with an explicitly-enumerated `git rm --quiet -- <5 paths>`; the remaining 7 modified files
  with a path-scoped `git add`. `git add -A` / `git add .` / `git commit -a` were never used.
- **Files modified:** none beyond the plan's list.
- **Commit:** `9105f0b`

**2. [Rule 1 — Criterion preservation] The B-3 negative-control comment was reworded.**
- **Found during:** Task 1, immediately after the `test_hash.py` edit.
- **Issue:** the repo's format-on-write hook reflowed the whole test function (the previously
  semicolon-compressed statements were expanded across lines — cosmetic, no semantic change), and my
  first comment wording contained the literal `transitions.json`, which would have made
  `grep -c "transitions.json" tools/contract_hash/tests/test_hash.py` return **3** against the plan's
  measured criterion of **2**.
- **Fix:** the comment now says "the transitions data contract" instead of the filename. The criterion
  returns 2. The code was changed to satisfy the criterion; the criterion was not adjusted.
- **Commit:** `9105f0b`

## Things the plan did not anticipate

- **`test_install_completeness.py` holds 3 tests, not 2.** The plan's Task-2 criterion says "BOTH tests
  in that module"; the module actually contains `test_catalog_excludes_dev_only_test_assets`,
  `test_discovers_at_least_twelve_modules`, and
  `test_every_referenced_tools_module_lands_in_applied_target`. All 3 pass, exit 0, so the criterion is
  satisfied in substance. Nothing was edited; this is a miscount in the plan's prose, not a defect.
- **The plan's `<execution_context>` @-references point at `/home/user/...`**, which does not exist on
  this machine. No effect on execution.
- **The full-suite count did not move (982 before and after).** Task 1 deleted 6 contracts but added no
  test and removed none — `docs_sync`'s determinism tests iterate the live tree rather than being
  parametrised per page, so the count is invariant to page removal. Worth knowing for anyone auditing
  the README badge against a pre-phase number.

## Acceptance criteria that did not hold

None. Every criterion in both tasks was run and passed as written, with the single prose-level
discrepancy noted above (2 vs 3 tests in `test_install_completeness.py`).

## W-2 carry-forward — Phase 45 scope (restated)

Three human-owned Diátaxis documents survive this phase describing the removed plane in stale prose,
and are **deliberately not repaired here**:

- `docs/how-to/task-lifecycle.md` (106 lines, 11 dying-surface references)
- `docs/explanation/next-milestone-task-control-plane.md` (504 lines, 19 references)
- `docs/explanation/task-lifecycle-shadow-metrics.md` (13 lines, framed on the same plane)

No markdown links run from these into the 5 `docs/reference/` pages this plan pruned, so no broken-link
failure mode exists — the residue is stale prose only, and no link checker or docs-prose gate would
catch it either way. This is **Phase 45 (projection repair)** scope.

## Known Stubs

None.

## Threat Flags

None — this plan removes surface and adds no endpoint, auth path, file-access pattern, or schema.

## Self-Check: PASSED

- `contracts/harness/task-control/gate-registry.json` — FOUND (sole survivor)
- `docs/reference/attestation.md`, `docs/reference/task.md` — confirmed ABSENT (as intended)
- `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` — FOUND, committed, not dirty
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` — FOUND, committed, not dirty
- commit `9105f0b` — FOUND in `git log`
- commit `c92c869` — FOUND in `git log`, `--name-only` lists exactly `README.ko.md`, `README.md`,
  `uv.lock` (no `.github/workflows/ci.yml`)
