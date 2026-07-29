---
phase: 41-docs-review-plane-removal
plan: 04
subsystem: infra
tags: [docs-review-plane, deletion, ADR-0012, CER-05, contract-drift, ci-fan-in, ruamel-yaml]

# Dependency graph
requires:
  - phase: 41-docs-review-plane-removal
    plan: "41-03"
    provides: harness/commands/docs-update.md + harness/skills/docs-upkeep/ deleted at source
      and re-emitted, tools/memory_regen/docs_staleness.py + its inject.py pointer row deleted —
      the last local consumers of the docs-review plane before this plan's constitution-plane
      and CI-plane cleanup
provides:
  - contracts/harness/docs/doc-dependencies.schema.json (and its now-empty parent directory)
    deleted; contract-drift green against a rebaselined contracts/.hashes/manifest.json in the
    same commit
  - The CI docs-guard job (ci.yml:317-351) and its comment block deleted; gate.needs reduced from
    12 to 11 entries with only the docs-guard token removed, verified by a ruamel.yaml-resolved
    parse (D-14), never grep
  - The committed-derived contracts-index plane (.memory/derived/contracts-index.md +
    tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr) regenerated to reflect
    16 contracts (was 17) — an in-scope consequence of this plan's own schema deletion, not part
    of the Plan-05 prose/test sweep
affects: [41-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [YAML-resolved gate.needs verification via ruamel.yaml (D-14, reused from Phase 40),
    pathspec-scoped commits (D-11), delete -> stage -> commit -> verify -> amend-if-red (D-10),
    in-scope derived-plane snapshot regen as a direct consequence of a deletion task (reused from
    Plan 03's emit-determinism precedent)]

key-files:
  created: []
  modified:
    - contracts/harness/docs/doc-dependencies.schema.json (deleted)
    - contracts/.hashes/manifest.json (rebaselined, doc-dependencies key removed, 1 line)
    - .github/workflows/ci.yml (docs-guard job + comment block deleted, 37 lines;
      gate.needs docs-guard token removed, 11 entries remain)
    - .memory/derived/contracts-index.md (regenerated, 17 -> 16 contracts)
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr (regenerated to match)

key-decisions:
  - "Regenerated .memory/derived/contracts-index.md and its syrupy snapshot as an IN-SCOPE
    consequence of Task 1's schema deletion (Rule 1 — direct bug caused by this plan's own
    change), not as part of the D-13/rule-7 prose/test sweep explicitly deferred to Plan 05.
    The deferral list names test_docs_sync_determinism.py specifically; it does not name
    test_contracts_index.py, and the latter was GREEN immediately before this plan's Task 1
    (confirmed via a disposable clone checked out at the prior commit, never via any in-place
    git checkout of the working tree) — the count-mismatch break was caused here, so it is fixed
    here, mirroring Plan 03's own emit-determinism.ambr regen precedent."
  - "Left test_docs_sync_determinism.py's 3 newly-surfaced failures untouched — that file (plus
    its snapshot) is explicitly named in phase-critical-rule-7 and CONTEXT.md D-13 as Plan 05's
    job, regardless of whether it was already red or is newly red as a consequence of this plan's
    deletion. The plan's own scope boundary is a direct instruction and takes precedence over the
    generic deviation-rule 'fix what your task broke' default for this one named file."
  - "No HARNESS_DEV_BYPASS was needed for the contract deletion: git rm (Bash) does not trigger
    contract_guard's Write|Edit matcher, confirmed by a clean commit with no PreToolUse denial."

requirements-completed: [CER-05]

# Metrics
duration: ~20min
completed: 2026-07-26
---

# Phase 41 Plan 04: Contract + CI Fan-In Job Deletion Summary

**Deleted `contracts/harness/docs/doc-dependencies.schema.json` with a same-commit manifest rebaseline, then deleted the CI `docs-guard` job and its `gate.needs` fan-in entry (verified by a mechanically-run `ruamel.yaml` parse, never grep), and regenerated the contracts-index derived plane that the schema deletion made stale — the last constitution-plane and CI-plane surface of the docs-review plane is now gone.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-07-26T18:59:37Z (per STATE.md `last_updated`; this session's wall-clock start)
- **Completed:** 2026-07-26T19:06:15Z
- **Tasks:** 2 completed (plus one in-scope discovered-consequence commit)
- **Files modified:** 5 across 3 commits

## Accomplishments

- Deleted `contracts/harness/docs/doc-dependencies.schema.json` and its now-empty parent directory via `git rm -r` (Bash, not Write/Edit — confirmed `contract_guard`'s `Write|Edit` matcher never fired, so no `HARNESS_DEV_BYPASS` was needed).
- Rebaselined `contracts/.hashes/manifest.json` via `uv run python -m tools.contract_hash.hash --write` in the **same commit** as the schema deletion (D-02): exactly the one `doc-dependencies` key removed, no other entry touched. `uv run python -m tools.contract_drift.drift` confirmed green before commit.
- Deleted the CI `docs-guard` job and its full comment block (`ci.yml:317-351`, 37 lines) and removed only the `docs-guard` token from `gate.needs` (`:381`, was 12 entries → 11), leaving every other token's order, spacing, and commas untouched.
- Verified D-14 mechanically — the plan's exact `ruamel.yaml` assertion, run as the task's own acceptance check, not eyeballed:
  ```
  ['setup', 'lang-tests', 'contract-check', 'drift', 'golden', 'core-suite', 'lint', 'lifecycle-eval', 'emit-drift', 'stale-derived', 'workspace']
  ```
  — 11 entries, `docs-guard` absent, as observed evidence.
- Discovered and fixed an in-scope consequence of Task 1's own deletion: `test_contracts_index.py::test_render_matches_committed_snapshot` went from green (confirmed via a disposable clone checked out at the pre-Plan-04 commit `6e55481`) to red because the contract count dropped 17→16. Regenerated `.memory/derived/contracts-index.md` (the MAINT-02 committed-derived tier) via `python -m tools.memory_regen.contracts_index` and the syrupy snapshot via `pytest --snapshot-update`.
- Full suite after all three commits: **14 failed, 1333 passed** — one fewer failure than the 15 observed right after Task 2, and matching exactly "11 pre-existing D-13-deferred (`test_coexist.py` ×2, `test_docs_update_wiring.py` ×7, `test_settings_coexist.py` ×2) + 3 in `test_docs_sync_determinism.py`" — both groups explicitly named in CONTEXT.md D-13 and this plan's phase-critical-rule 7 as Plan 05's job.

## Task Commits

Each task was committed atomically, plus one in-scope discovered-consequence commit:

1. **Task 1: Delete the contract and rebaseline the manifest** - `1d33141` (feat)
2. **Task 2: Delete the CI docs-guard job and its fan-in needs entry** - `1ee94a2` (feat)
3. **In-scope: regenerate contracts-index derived plane** - `d83faef` (test)

_No separate plan-metadata commit distinct from these three — this summary/STATE/ROADMAP update is the final commit for this plan._

## Files Created/Modified

- `contracts/harness/docs/doc-dependencies.schema.json` - deleted (69 lines)
- `contracts/.hashes/manifest.json` - rebaselined, `doc-dependencies` key removed (1 line)
- `.github/workflows/ci.yml` - `docs-guard` job + comment block deleted (37 lines); `gate.needs` `docs-guard` token removed
- `.memory/derived/contracts-index.md` - regenerated (17 → 16 contracts)
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` - regenerated to match

## Decisions Made

See `key-decisions` in frontmatter — three decisions, all documented there with rationale.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `test_contracts_index.py`'s committed snapshot went stale from this plan's own schema deletion**
- **Found during:** post-Task-2 full-suite run, comparing failure count against the 41-03 baseline (11 expected-red)
- **Issue:** Deleting `contracts/harness/docs/doc-dependencies.schema.json` in Task 1 correctly dropped the live contract count from 17 to 16, but the committed-derived `.memory/derived/contracts-index.md` and its syrupy snapshot still asserted 17 — a direct, mechanical consequence of the deletion, not a pre-existing failure. Confirmed the pre-plan state was green by cloning the repo into a disposable scratch directory and checking out the pre-Task-1 commit there (never by mutating the working repo's tracked files in place).
- **Fix:** Regenerated `.memory/derived/contracts-index.md` via `python -m tools.memory_regen.contracts_index` and the snapshot via `pytest tools/memory_regen/tests/test_contracts_index.py --snapshot-update`
- **Files modified:** `.memory/derived/contracts-index.md`, `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`
- **Verification:** full suite failure count dropped from 15 to 14, matching the expected 11 (Plan 05's) + 3 (`test_docs_sync_determinism.py`, also explicitly Plan 05's per D-13/rule-7)
- **Committed in:** `d83faef`

---

**Total deviations:** 1 auto-fixed (1 Rule-1 bug, a direct consequence of this plan's own deletion)
**Impact on plan:** Necessary to keep the committed-derived plane (MAINT-02) accurate; no scope creep — `test_docs_sync_determinism.py`, also newly red from the same deletion, was deliberately left untouched because it is explicitly named in the plan's own out-of-scope list (rule 7) as Plan 05's job.

## Issues Encountered

**Tooling incident (self-corrected, no lasting effect):** while investigating whether `test_docs_sync_determinism.py` and `test_contracts_index.py` were pre-existing failures, an in-place `git checkout <old-commit> -- .` was run against the working repo instead of against a disposable clone, temporarily reverting the working tree's `ci.yml`, `contracts/.hashes/manifest.json`, and re-adding the deleted schema file to the index (staged, not committed). Caught immediately via `git status --short`; restored with `git checkout HEAD -- .github/workflows/ci.yml contracts/.hashes/manifest.json` plus an explicit `git rm --cached` + `rm -f` + `rmdir` of the re-added schema file. Verified recovery via `git diff HEAD --stat` (empty) before proceeding — both prior commits (`1d33141`, `1ee94a2`) were never touched, HEAD never moved, and nothing was force-reset. All subsequent investigation used a genuinely disposable `git clone` under the scratchpad directory instead.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 05 can proceed with the prose/test sweep: `AGENTS.md`, `tools/harness_lint/caps.py`, `tools/harness_lint/workspace_check.py`, `harness/skills/gate-model/SKILL.md`'s docs-plane claims, `tools/harness_emit/tests/test_coexist.py`, `tools/hooks/tests/test_settings_coexist.py`, `tools/harness_lint/tests/test_docs_update_wiring.py`, `tools/docs_sync/tests/test_docs_sync_determinism.py` + its snapshot (`EXPECTED_PAGES` still lists `doc-dependencies` and the render/prune tests reflect it), `uv.lock`, and the final residue sweep for `docs_guard|docs-guard|docs-review-ledger|ledger_guard|docs-upkeep|docs-update|doc-dependencies` outside `.planning/`. Full suite currently 14 failed / 1333 passed, all 14 failures in files Plan 05 explicitly owns. No blockers.

## Self-Check: PASSED

- `test ! -f contracts/harness/docs/doc-dependencies.schema.json` — exit 0 (confirmed)
- `test ! -d contracts/harness/docs` — exit 0 (confirmed)
- `grep -c doc-dependencies contracts/.hashes/manifest.json` — 0 (confirmed)
- `uv run python -m tools.contract_drift.drift` — exits 0, "OK — live manifest matches the committed baseline." (confirmed)
- `grep -c docs-guard .github/workflows/ci.yml` — 0 (confirmed)
- `grep -n needs: .github/workflows/ci.yml` — exactly 2 lines (`:80` `lang-tests: needs: setup`, `:345` `gate: needs: [...]`) (confirmed)
- `uv run python -c "from ruamel.yaml import YAML; ...; assert 'docs-guard' not in n and len(n)==11"` — exits 0, prints the exact 11-entry list quoted above (confirmed)
- Commit `1d33141` — FOUND in `git log --oneline`
- Commit `1ee94a2` — FOUND in `git log --oneline`
- Commit `d83faef` — FOUND in `git log --oneline`
- `git diff --stat 6e55481..d83faef` reports **5 files changed, 3 insertions(+), 111 deletions(-)** (D-17 measured, not estimated)
- `uv run pytest -q` — 1333 passed, 14 failed, all 14 in files explicitly named as Plan 05's job (confirmed)

---
*Phase: 41-docs-review-plane-removal*
*Completed: 2026-07-26*
