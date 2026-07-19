---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
plan: 01
subsystem: contracts
tags: [json-schema, draft-2020-12, contract-hash, contract-drift, adoption, brownfield]

# Dependency graph
requires:
  - phase: 24-contract-relationship-vocabulary-compatibility-v2-3-a
    provides: "contracts/harness/topology/relationship.schema.json — the ratified relationship record vocabulary this plan's relationshipCandidate $def duplicates (D-11)"
provides:
  - "contracts/harness/adoption/inventory.schema.json — ADOPT-01 inventory artifact contract"
  - "contracts/harness/adoption/plan.schema.json — ADOPT-02 mapping-plan artifact contract"
  - "contracts/harness/adoption/manifest.schema.json — ADOPT-03 disposition manifest artifact contract"
  - "rebaselined contracts/.hashes/manifest.json including the 3 new schemas, contract-drift green"
  - "regenerated committed-derived plane: docs/reference/{inventory,plan,manifest}.md + .memory/derived/contracts-index.md"
affects: [27-brownfield-adoption-apply, "phase-26 plans 02 and 03 (scanner code validates against these fixed shapes)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Self-contained Draft 2020-12 schemas (D-11) — each of the 3 adoption schemas duplicates its own evidenceRef/classification $defs, zero cross-file $ref, mirroring contracts/harness/task-control/*.schema.json"
    - "Structural D-10 guarantee — inventory.schema.json's excludedEntry $def has no sha256 property in its own properties block (additionalProperties:false + required:[path,size,excluded]), so a secret-flagged exclusion cannot structurally carry a content hash"
    - "Schema-incomplete candidate shape (D-05) — plan.schema.json's candidateRecord.record is an open object (no required/additionalProperties), so a partial relationship candidate can never be mistaken for a ratified relationship record"

key-files:
  created:
    - contracts/harness/adoption/inventory.schema.json
    - contracts/harness/adoption/plan.schema.json
    - contracts/harness/adoption/manifest.schema.json
    - docs/reference/inventory.md
    - docs/reference/plan.md
    - docs/reference/manifest.md
  modified:
    - contracts/.hashes/manifest.json
    - .memory/derived/contracts-index.md
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr

key-decisions:
  - "Rebaselined via tools.contract_hash.hash --write only (never hand-edited); the diff added exactly 3 keys, no other manifest entry's hash changed"
  - "Paused at the plan's blocking checkpoint (Task 3) before running the derived-plane regen, per the plan's own gate and this session's authorization boundary — did NOT self-ratify the constitution-plane diff; a human independently re-verified the diff and responded \"approved\" (the plan's <resume-signal>) before Task 4 ran"
  - "HARNESS_DEV_BYPASS dev-session opt-out (ADR-0007) was used to author/rebaseline the schemas — never conflated with, or substituted for, the human ratification that resumed the plan"
  - "Post-wave full-suite test gate caught 4 test failures the plan's own tasks did not surface (the plan's <verify> commands never ran the full pytest suite); fixed by updating the hardcoded EXPECTED_PAGES fixture constant + --snapshot-update on exactly the 2 affected snapshot tests, diff-reviewed to confirm every changed hunk is purely additive and traces to the 3 new adoption schemas before committing"

patterns-established:
  - "Adoption schema style template: $schema/$id/title/description, additionalProperties:false at every object level, explicit required arrays, $defs duplicated per schema (not $ref'd across files) — Plan 02/03 must follow this same template if any further contract work is needed"

requirements-completed: [ADOPT-01, ADOPT-02, ADOPT-03]

# Metrics
duration: ~65min (paused for human checkpoint review between Task 2 and Task 3's follow-on; +15min for a post-wave test-gate fix)
completed: 2026-07-19
---

# Phase 26 Plan 01: Adoption Constitution Schemas Summary

**Three self-contained Draft 2020-12 schemas (inventory/plan/manifest) authored under `contracts/harness/adoption/`, human-ratified at the mandatory blocking checkpoint, contract-hash manifest rebaselined, committed-derived plane regenerated, and a post-wave full-suite test-gate failure (4 stale fixtures) fixed — plan complete.**

## Performance

- **Duration:** ~65 min total (Tasks 1-2 landed, then a blocking human-verify checkpoint pause for external review, then Task 3's follow-on derived-plane regen, then a required post-wave test-gate fix)
- **Tasks completed:** 4 of 4 plan tasks (Task 1 + Task 2 auto tasks, the blocking checkpoint ratified "approved", Task 3's follow-on derived-plane regen) **plus one required follow-up fix** (post-wave `pytest -q` gate — see "Post-Wave Test Gate Fix" below)
- **Files modified:** 9 (5 created, 4 modified across the constitution + derived + test-fixture planes — see key-files)

## Accomplishments

- Authored `contracts/harness/adoption/inventory.schema.json` — ADOPT-01 bounded deterministic inventory contract encoding D-01/D-02/D-08/D-09/D-10 structurally.
- Authored `contracts/harness/adoption/plan.schema.json` — ADOPT-02 evidence-separated mapping plan contract, whose `relationshipCandidate` $def duplicates (not `$ref`s) the Phase-24 `relationship.schema.json` shape, and whose `questionRecord`/`candidateRecord` implement the D-05 schema-incomplete-candidate guarantee.
- Authored `contracts/harness/adoption/manifest.schema.json` — ADOPT-03 total disposition manifest contract with the exact 6-value `dispositionEnum` plus a separate `excluded[]` array for GSD-owned lanes.
- Rebaselined `contracts/.hashes/manifest.json` via `tools.contract_hash.hash --write` (never hand-edited); `tools.contract_drift.drift` reports OK.
- Reached the plan's `type="checkpoint:human-verify" gate="blocking"` task and PAUSED — did not self-ratify. The repo owner independently re-verified the diff (drift OK, diffstat exactly the 3 schemas + manifest, zero cross-file `$ref`, `excludedEntry` props exactly `[excluded, path, size]`, dispositionEnum exact 6 values, `questionRecord.id` pattern, `candidateRecord` has no `authority` property, no token string under `contracts/`) and responded "approved" — the plan's `<resume-signal>`.
- Ran the derived-plane regeneration (`tools.docs_sync` + `tools.memory_regen.contracts_index`) and confirmed the exact `stale-derived` CI mirror command sequence exits 0 with no diff.
- **Post-wave full-suite test gate caught 4 pre-existing-fixture failures** (see "Post-Wave Test Gate Fix" below) that this plan's own per-task `<verify>` commands did not surface (none of them ran the full `pytest -q` suite); fixed them and re-verified the full suite green (962 passed).

## Task Commits

Each task was committed atomically:

1. **Task 1: Author the three ratified adoption schemas** - `245a101` (feat)
2. **Task 2: Ratify — rebaseline contract-hash manifest, verify drift green** - `3f84070` (chore)
3. **[checkpoint] Human ratification of the constitution-plane schema landing** - no code commit (human review + "approved" resume-signal, external to this repo's commit history)
4. **Task 3 follow-on: Regenerate the committed-derived plane** - `97bebfc` (docs)
5. **Post-wave fix: update docs_sync/contracts_index fixtures for the 3 new adoption schemas** - `d9591c4` (fix)

Supporting commits: `22b543a` (initial paused-state SUMMARY), `57526af` (self-check appended), `f7fb4a8` (STATE.md paused-position update) — superseded by this completed SUMMARY and the plan-completion STATE/ROADMAP update below.

## Files Created/Modified

- `contracts/harness/adoption/inventory.schema.json` - ADOPT-01 inventory artifact contract (included/excluded files, language/manifest/surface detection, enumeration_mode, max_file_bytes)
- `contracts/harness/adoption/plan.schema.json` - ADOPT-02 mapping-plan artifact contract (proposals, relationship candidates, question records)
- `contracts/harness/adoption/manifest.schema.json` - ADOPT-03 disposition manifest artifact contract (total 6-value disposition enum + excluded lanes)
- `contracts/.hashes/manifest.json` - rebaselined JCS SHA-256 manifest including the 3 new schemas; `git diff --stat` showed exactly 3 lines added, no other entry touched
- `docs/reference/inventory.md`, `docs/reference/plan.md`, `docs/reference/manifest.md` - new DERIVED Diátaxis reference pages generated from the 3 adoption schemas
- `.memory/derived/contracts-index.md` - regenerated (10 → 13 contracts indexed; the 3 new rows report `clean` drift)
- `tools/docs_sync/tests/test_docs_sync_determinism.py` - `EXPECTED_PAGES` frozenset gained `inventory`/`manifest`/`plan` (post-wave fix)
- `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` - `--snapshot-update`d for the 3 new adoption page sections (post-wave fix, diff-reviewed additive-only)
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` - `--snapshot-update`d for the 10→13 count + 3 new rows (post-wave fix, diff-reviewed additive-only)

## Decisions Made

- Followed the plan's schema spec literally (Task 1's `<action>` block is an exhaustive field-by-field spec); no schema-shape deviations.
- Wrote all three schemas via the repo's `HARNESS_DEV_BYPASS=1` dev-session opt-out (ADR-0007), never fabricating or setting `GOLDEN_APPROVE_HUMAN`.
- Confirmed `git diff --stat contracts/.hashes/manifest.json` touches ONLY the 3 new adoption-schema keys before committing Task 2, satisfying its acceptance criteria exactly.
- Correctly PAUSED at the blocking checkpoint rather than self-ratifying or running the derived-plane regen ahead of human confirmation — resumed only after the repo owner's independent re-verification and explicit "approved" response.

## Deviations from Plan

**The plan's own tasks executed exactly as written** (schema shapes, rebaseline, checkpoint, derived-plane regen all matched the `<action>`/`<acceptance_criteria>` blocks verbatim). However, the plan itself had a scope gap that surfaced only after a post-wave full-suite test run — see "Post-Wave Test Gate Fix" below; this is documented as a Rule 1 auto-fixed bug (broken test behavior caused by the plan's own change), not a plan-instruction deviation.

One clarification, not a deviation: the plan's own Task 1 `<verify><automated>` grep pattern (`grep -q '"draft/2020-12/schema"'`) does not match ANY schema in this repo — including the pre-existing precedent `contracts/harness/task-control/evidence.schema.json` — because every `$schema` value is the full URL `"https://json-schema.org/draft/2020-12/schema"` and the literal substring `'"draft/2020-12/schema"'` therefore never appears (the character before `draft` is `/`, not `"`). Verified this is a pre-existing plan/verify-script quirk, not specific to this plan's schemas, by testing the identical grep against the precedent file (also fails). The prose acceptance criteria — "contain the exact `\"$schema\": \"https://json-schema.org/draft/2020-12/schema\"` string" — IS satisfied by all three new schemas (verified directly). No fix applied; documenting for the record since it could otherwise look like a missed acceptance criterion.

## Post-Wave Test Gate Fix

**[Rule 1 - Bug] docs_sync/contracts_index test fixtures went stale when the 3 adoption schemas landed.**

- **Found during:** A post-wave `uv run pytest -q` run by the coordinator, AFTER this plan's own tasks and their per-task `<verify>` commands had all passed and the plan was reported complete. None of the plan's own `<verify>` blocks ran the full suite — only `contract_drift`, the `stale-derived` mirror, and direct JSON/schema-shape checks — so this gap was invisible to the plan's own gates.
- **Issue:** `tools/docs_sync/tests/test_docs_sync_determinism.py` hardcodes `EXPECTED_PAGES` (a frozenset pinning the exact set of reference pages docs_sync must produce) — it still listed only the pre-26-01 8 pages, not the 3 new ones. This broke `test_seed_schemas_map_one_to_one_to_pages` and `test_prune_removes_orphan_pages_preserves_readme` (both assert against the same constant). Separately, two committed syrupy `.ambr` snapshots (`test_docs_sync_determinism.ambr`, `test_contracts_index.ambr`) pinned `render()` output over the pre-26-01 contracts tree, so `test_render_matches_committed_snapshot` failed in both modules once the 3 new schemas' rendered pages/rows appeared. Net: 4 failed / 958 passed.
- **Fix:**
  1. Added `inventory`, `manifest`, `plan` to `EXPECTED_PAGES` in `tools/docs_sync/tests/test_docs_sync_determinism.py` (fixed 2 of the 4 failures immediately).
  2. Ran `--snapshot-update` scoped to ONLY the two affected tests (`test_render_matches_committed_snapshot` in both `test_docs_sync_determinism.py` and `test_contracts_index.py`) — never a blanket `--snapshot-update` across the suite.
  3. Before committing, `git diff`'d both `.ambr` files and confirmed every changed hunk is purely additive and traces to the 3 adoption schemas: the docs_sync snapshot gained exactly 3 new `===== <name> =====` sections (inventory/manifest/plan) with zero changes to the 8 pre-existing sections; the contracts_index snapshot gained exactly 3 new `clean` rows plus the `10 contract(s)` → `13 contract(s)` count line, with zero changes to any pre-existing row. No unrelated snapshot debt was swept in — confirmed, not assumed.
- **Files modified:** `tools/docs_sync/tests/test_docs_sync_determinism.py`, `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr`, `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`
- **Verification:** `uv run pytest -q` → **962 passed, 0 failed** (full suite, not a subset — actual tail output below). `uv run python -m tools.contract_drift.drift` → OK (re-confirmed after the fix, unaffected by test-only changes). Stale-derived CI mirror → exit 0 (re-confirmed after the fix).
- **Committed in:** `d9591c4`

```
........................................................................ [ 22%]
........................................................................ [ 29%]
........................................................................ [ 37%]
........................................................................ [ 44%]
........................................................................ [ 52%]
........................................................................ [ 59%]
........................................................................ [ 67%]
........................................................................ [ 74%]
........................................................................ [ 82%]
........................................................................ [ 89%]
........................................................................ [ 97%]
..........................                                               [100%]
--------------------------- snapshot report summary ----------------------------
6 snapshots passed.
962 passed in 44.69s
```

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug — stale test fixtures from the plan's own derived-plane change)
**Impact on plan:** Necessary correctness fix; the plan's `must_haves.truths` explicitly requires the derived plane to regenerate "in this SAME wave so the stale-derived CI job does not go red on a later, unrelated commit" — this fix closes the equivalent gap for the full pytest suite (fixtures pinning that same derived output), which the plan's own verify steps did not check. No scope creep — only the 2 fixture files directly broken by this plan's schema additions were touched.

## Issues Encountered

The post-wave full-suite failure above (4 failed / 958 passed) was the only issue encountered; it is fully resolved and documented as a Rule 1 auto-fix in "Post-Wave Test Gate Fix". Aside from that, all plan tasks passed on the first attempt; determinism was proven directly both before and after the fix (all 8 pre-existing reference pages regenerated byte-identical both times; only the 3 new adoption pages + contracts-index legitimately changed).

## Checkpoint Ratification

The plan's `type="checkpoint:human-verify" gate="blocking"` task was correctly NOT self-ratified by the executor. The repo owner independently re-verified the constitution-plane diff (commits `245a101`, `3f84070`) — drift OK, diffstat exactly the 3 schemas + manifest (+458 lines / 4 files, nothing else), zero cross-file `$ref`, `excludedEntry` properties exactly `[excluded, path, size]` with `additionalProperties:false`, `dispositionEnum` exactly the 6 required values, `questionRecord` required fields + id pattern correct, `candidateRecord` carries no `authority` property, and no `GOLDEN_APPROVE_HUMAN` (or any other) token anywhere under `contracts/` — then responded "approved", satisfying the plan's `<resume-signal>`. The `HARNESS_DEV_BYPASS` dev-session opt-out used to author/rebaseline the schemas was never conflated with this human ratification.

## Next Phase Readiness

- Plan 26-01 is complete: all three ADOPT-01/02/03 constitution contracts are ratified and drift-clean, the committed-derived plane is fresh, the FULL test suite is green (962 passed, not a subset), and `uv run python -m tools.contract_drift.drift` is OK.
- Ready to proceed to Plan 02 (`tools/adoption_scan` scan.py + detect.py — confined read-only enumeration, exclusion classification, language/manifest/surface detection, the one synthetic mini-repo fixture) and Plan 03 (plan.py + destinations.py + cli.py), both of which now validate against these fixed, ratified shapes.
- **Lesson for future plans in this repo:** a plan's own `<verify>` steps checking `contract_drift` + the `stale-derived` mirror is NOT equivalent to a green full test suite — any plan that adds a new schema/contract should also run (or have a checkpoint verify) `uv run pytest -q` before being reported complete, since hardcoded `EXPECTED_*` fixture constants and committed snapshots elsewhere in the tree can silently pin the pre-change state.
- No blockers carried forward from this plan.

---
*Phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b*
*Completed: 2026-07-19*

## Self-Check: PASSED

- FOUND: contracts/harness/adoption/inventory.schema.json
- FOUND: contracts/harness/adoption/plan.schema.json
- FOUND: contracts/harness/adoption/manifest.schema.json
- FOUND: docs/reference/inventory.md
- FOUND: docs/reference/plan.md
- FOUND: docs/reference/manifest.md
- FOUND: tools/docs_sync/tests/test_docs_sync_determinism.py (EXPECTED_PAGES updated)
- FOUND: tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr (snapshot-updated)
- FOUND: tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr (snapshot-updated)
- FOUND: commit 245a101 (Task 1)
- FOUND: commit 3f84070 (Task 2)
- FOUND: commit 97bebfc (Task 3 follow-on: derived-plane regen)
- FOUND: commit d9591c4 (post-wave test gate fix)
- CONFIRMED: `uv run pytest -q` → 962 passed, 0 failed (full suite)
