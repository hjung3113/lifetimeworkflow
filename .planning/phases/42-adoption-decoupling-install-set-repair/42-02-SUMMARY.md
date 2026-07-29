---
phase: 42-adoption-decoupling-install-set-repair
plan: 02
subsystem: adoption-lifecycle
tags: [contracts, docs-sync, memory-regen, adoption, cer-06]

# Dependency graph
requires:
  - phase: 42-adoption-decoupling-install-set-repair
    plan: "42-01"
    provides: approval.py + its cli.py wiring deleted, severing the one live
      tools.task_control import; the orphaned contract and the prose-only
      task_control mentions (apply.py:16/207/241, batch.py x5) deferred here
  - phase: 41-docs-review-plane-removal
    plan: "41-04"
    provides: the git-rm + same-commit manifest-rebaseline procedure and the
      in-scope derived-plane-regen-as-direct-consequence precedent, both reused
      verbatim
provides:
  - "contracts/harness/adoption/approval.schema.json deleted; contracts/.hashes/manifest.json
    rebaselined in the same commit (16 -> 15 contracts); contract-drift green"
  - "docs/reference/approval.md pruned by docs_sync's regen; EXPECTED_PAGES (13 -> 12) and its
    committed syrupy snapshot updated; .memory/derived/contracts-index.md + its snapshot
    regenerated to the post-deletion count"
  - "tools/adoption_apply/{apply.py,batch.py,pyproject.toml} no longer name
    tools.task_control.manager anywhere; grep -rn task_control tools/adoption_apply/ returns
    nothing"
affects: [42-03, 42-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "git rm (Bash, not Write/Edit) -> same-commit manifest rebaseline -> contract-drift
      verify -> commit, reused verbatim from Phase 41's 41-04 procedure"
    - "in-scope derived-plane snapshot regen (contracts-index + docs_sync determinism) as a
      direct, same-task consequence of the schema deletion, not a separate prose-sweep task"

key-files:
  created: []
  modified:
    - contracts/harness/adoption/approval.schema.json (deleted)
    - contracts/.hashes/manifest.json
    - docs/reference/approval.md (deleted)
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
    - .memory/derived/contracts-index.md
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr
    - tools/adoption_apply/apply.py
    - tools/adoption_apply/batch.py
    - tools/adoption_apply/pyproject.toml

key-decisions:
  - "Regenerated tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr (the
    module's own committed render() snapshot, distinct from the EXPECTED_PAGES frozenset the
    plan named explicitly) as an in-scope Rule-1 consequence of Task 1's own schema deletion --
    it broke immediately after the EXPECTED_PAGES edit and prune-regen, mirroring the
    contracts-index precedent from 41-04. Not a separate scope addition: the plan's own
    acceptance criteria required `uv run pytest tools/docs_sync tools/memory_regen -q` green,
    and this snapshot is inside tools/docs_sync."
  - "cli.py required no edit -- re-read in full per the plan's own acceptance check and
    confirmed clean; Plan 01 had already removed every task_control/approval/promotion
    string from it."

requirements-completed: [CER-06]

# Metrics
duration: ~25min
completed: 2026-07-28
---

# Phase 42 Plan 02: Contract Deletion, Manifest Rebaseline, Derived-Plane Prune, D-10/D-11 Prose Sweep Summary

**Deleted the orphaned `approval.schema.json` contract with a same-commit manifest rebaseline (D-02), pruned its derived-plane page/index row/snapshots, and finished the D-10/D-11 prose sweep closing every remaining `tools.task_control.manager` reference in `tools/adoption_apply/`.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-07-28
- **Tasks:** 2/2
- **Files modified:** 10 across 2 commits (2 deleted, 8 edited)

## Accomplishments

- `contracts/harness/adoption/approval.schema.json` deleted via `git rm` (no `HARNESS_DEV_BYPASS` needed — `contract_guard`'s `PreToolUse` hook matches only `Write|Edit`, never `Bash`); `contracts/.hashes/manifest.json` rebaselined in the same commit via `uv run python -m tools.contract_hash.hash --write`, dropping exactly the `approval` key (16 -> 15 contracts); `uv run python -m tools.contract_drift.drift` confirmed green before commit.
- `EXPECTED_PAGES` in `tools/docs_sync/tests/test_docs_sync_determinism.py` dropped `"approval"` (13 -> 12 pages) and its provenance-narrating docstring comment updated; `python -m tools.docs_sync` regenerated `docs/reference/**`, whose prune-then-write semantics deleted `docs/reference/approval.md` automatically.
- Discovered and fixed an in-scope consequence of the deletion, mirroring 41-04's precedent: `test_docs_sync_determinism.py`'s own committed `render()` syrupy snapshot (`tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr`) still contained the `approval` page and went red immediately after the `EXPECTED_PAGES` edit — regenerated via `pytest --snapshot-update`.
- `.memory/derived/contracts-index.md` and its syrupy snapshot regenerated to the post-deletion 15-contract count via `python -m tools.memory_regen.contracts_index` + `pytest tools/memory_regen/tests/test_contracts_index.py --snapshot-update`.
- Finished the D-10/D-11 prose sweep: `apply.py:16`'s module docstring, `apply.py:207`'s `atomic_create` docstring, and `apply.py:241`'s `_atomic_replace` docstring reworded to describe each already-inlined sequence on its own terms, dropping every `tools.task_control.manager` reference. `batch.py`'s five docstring/comment mentions (lines 4, 6, 14, 59, 92) reworded the same way. `pyproject.toml`'s `description` field updated to drop "human-ratification promotion" language and reflect the surviving `draft`/`apply`-only lifecycle. `cli.py` re-read in full and confirmed already clean (Plan 01's edit).

## Task Commits

Each task was committed atomically:

1. **Task 1: Delete approval.schema.json, rebaseline the hash manifest, prune the derived plane** - `d4c8328` (feat)
2. **Task 2: Finish the D-10/D-11 prose sweep — apply.py, cli.py, batch.py, pyproject.toml** - `3e5c3ff` (docs)

**Plan metadata:** (this commit, immediately following)

## Files Created/Modified

- `contracts/harness/adoption/approval.schema.json` - deleted (77 lines, the orphaned ADOPT-06 contract)
- `contracts/.hashes/manifest.json` - rebaselined, `approval` key removed
- `docs/reference/approval.md` - deleted (pruned by docs_sync regen)
- `tools/docs_sync/tests/test_docs_sync_determinism.py` - `EXPECTED_PAGES` drops `"approval"`, provenance comment updated
- `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` - regenerated (in-scope consequence)
- `.memory/derived/contracts-index.md` - regenerated (16 -> 15 contracts)
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` - regenerated to match
- `tools/adoption_apply/apply.py` - three docstrings reworded to drop `tools.task_control.manager`
- `tools/adoption_apply/batch.py` - five docstring/comment mentions reworded
- `tools/adoption_apply/pyproject.toml` - `description` field updated

## Decisions Made

See `key-decisions` in frontmatter. In short: the `docs_sync` module's own committed render() snapshot needed regeneration as a direct Rule-1 consequence of Task 1's own deletion (not a scope addition — required for the plan's own `tools/docs_sync -q` green acceptance criterion); `cli.py` needed no edit, confirmed by re-reading it in full.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `test_docs_sync_determinism.py`'s own committed render() snapshot went stale from this plan's own deletion**
- **Found during:** Task 1, running `uv run pytest tools/docs_sync tools/memory_regen -q` after the `EXPECTED_PAGES` edit and docs regen
- **Issue:** The plan named `EXPECTED_PAGES` explicitly but not the module's separate `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` (a full committed render() snapshot over all schemas, including `approval`'s rendered markdown) — a direct, mechanical consequence of the deletion, not a pre-existing failure.
- **Fix:** Regenerated via `uv run pytest tools/docs_sync/tests/test_docs_sync_determinism.py --snapshot-update`.
- **Files modified:** `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr`
- **Verification:** `uv run pytest tools/docs_sync tools/memory_regen -q` → 94 passed
- **Committed in:** `d4c8328` (same commit as Task 1, matching the plan's own bundled staging instruction)

---

**Total deviations:** 1 auto-fixed (1 Rule-1 bug, a direct consequence of this plan's own deletion, following the exact 41-04 precedent named in the plan's own context block).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `test ! -f contracts/harness/adoption/approval.schema.json` → exit 0
- `grep -c approval contracts/.hashes/manifest.json` → 0
- `uv run python -m tools.contract_drift.drift` → exits 0, "OK — live manifest matches the committed baseline."
- `test ! -f docs/reference/approval.md` → exit 0
- `uv run pytest tools/docs_sync tools/memory_regen -q` → 94 passed
- `grep -rn "task_control" tools/adoption_apply/` → no matches
- `grep -rn "GOLDEN_APPROVE_HUMAN" tools/adoption_apply/` → no matches
- `uv run pytest tools/adoption_apply -q` → 73 passed
- `uv run pytest -q` (whole repo) → 1315 passed, 0 failed
- `git log --oneline -5` shows exactly 2 new commits for this plan's 2 tasks (`d4c8328`, `3e5c3ff`)

**Changed LOC (D-17, from `git diff --stat aef2c14..HEAD`):** 10 files changed, 29 insertions(+), 149 deletions(-)

## Next Phase Readiness

- `tools/adoption_apply/` no longer names `tools.task_control` anywhere — grep-clean, satisfying this plan's half of the phase-level SC-1 gate. `tools/adoption_scan/`'s `_GATE_REGISTRY_PATH` reference is Plan 03's job (already landed per `42-03-SUMMARY.md`); re-running the phase-level combined grep is Plan 05's/verification's job.
- `contracts/harness/adoption/approval.schema.json` no longer exists; the three surviving adoption contracts (`inventory`, `plan`, `manifest`) are untouched.
- `harness/commands/adopt.md` and `harness/skills/brownfield-adoption/SKILL.md` still describe the deleted promotion gate — out of scope here, explicitly Plan 05's job per this plan's own rule 7.
- No blockers for Plan 05.

## Self-Check: PASSED

- `test ! -f contracts/harness/adoption/approval.schema.json` — exit 0 (confirmed)
- `test ! -f docs/reference/approval.md` — exit 0 (confirmed)
- Commit `d4c8328` — FOUND in `git log --oneline`
- Commit `3e5c3ff` — FOUND in `git log --oneline`
- `grep -rn "task_control" tools/adoption_apply/` — no matches (confirmed)
- `uv run pytest -q` — 1315 passed, 0 failed (confirmed)

---
*Phase: 42-adoption-decoupling-install-set-repair*
*Completed: 2026-07-28*
