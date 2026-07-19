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

key-decisions:
  - "Rebaselined via tools.contract_hash.hash --write only (never hand-edited); the diff added exactly 3 keys, no other manifest entry's hash changed"
  - "Paused at the plan's blocking checkpoint (Task 3) before running the derived-plane regen, per the plan's own gate and this session's authorization boundary — did NOT self-ratify the constitution-plane diff; a human independently re-verified the diff and responded \"approved\" (the plan's <resume-signal>) before Task 4 ran"
  - "HARNESS_DEV_BYPASS dev-session opt-out (ADR-0007) was used to author/rebaseline the schemas — never conflated with, or substituted for, the human ratification that resumed the plan"

patterns-established:
  - "Adoption schema style template: $schema/$id/title/description, additionalProperties:false at every object level, explicit required arrays, $defs duplicated per schema (not $ref'd across files) — Plan 02/03 must follow this same template if any further contract work is needed"

requirements-completed: [ADOPT-01, ADOPT-02, ADOPT-03]

# Metrics
duration: ~50min (paused for human checkpoint review between Task 2 and Task 3's follow-on)
completed: 2026-07-19
---

# Phase 26 Plan 01: Adoption Constitution Schemas Summary

**Three self-contained Draft 2020-12 schemas (inventory/plan/manifest) authored under `contracts/harness/adoption/`, human-ratified at the mandatory blocking checkpoint, contract-hash manifest rebaselined, and the committed-derived plane (docs/reference + contracts-index) regenerated — plan complete.**

## Performance

- **Duration:** ~50 min total (Tasks 1-2 landed, then a blocking human-verify checkpoint pause for external review, then Task 3's follow-on derived-plane regen)
- **Tasks completed:** 4 of 4 (Task 1 + Task 2 auto tasks, the blocking checkpoint ratified "approved", Task 3's follow-on derived-plane regen)
- **Files modified:** 6 (5 created, 3 modified across the constitution + derived planes — see key-files)

## Accomplishments

- Authored `contracts/harness/adoption/inventory.schema.json` — ADOPT-01 bounded deterministic inventory contract encoding D-01/D-02/D-08/D-09/D-10 structurally.
- Authored `contracts/harness/adoption/plan.schema.json` — ADOPT-02 evidence-separated mapping plan contract, whose `relationshipCandidate` $def duplicates (not `$ref`s) the Phase-24 `relationship.schema.json` shape, and whose `questionRecord`/`candidateRecord` implement the D-05 schema-incomplete-candidate guarantee.
- Authored `contracts/harness/adoption/manifest.schema.json` — ADOPT-03 total disposition manifest contract with the exact 6-value `dispositionEnum` plus a separate `excluded[]` array for GSD-owned lanes.
- Rebaselined `contracts/.hashes/manifest.json` via `tools.contract_hash.hash --write` (never hand-edited); `tools.contract_drift.drift` reports OK.
- Reached the plan's `type="checkpoint:human-verify" gate="blocking"` task and PAUSED — did not self-ratify. The repo owner independently re-verified the diff (drift OK, diffstat exactly the 3 schemas + manifest, zero cross-file `$ref`, `excludedEntry` props exactly `[excluded, path, size]`, dispositionEnum exact 6 values, `questionRecord.id` pattern, `candidateRecord` has no `authority` property, no token string under `contracts/`) and responded "approved" — the plan's `<resume-signal>`.
- Ran the derived-plane regeneration (`tools.docs_sync` + `tools.memory_regen.contracts_index`) and confirmed the exact `stale-derived` CI mirror command sequence exits 0 with no diff.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author the three ratified adoption schemas** - `245a101` (feat)
2. **Task 2: Ratify — rebaseline contract-hash manifest, verify drift green** - `3f84070` (chore)
3. **[checkpoint] Human ratification of the constitution-plane schema landing** - no code commit (human review + "approved" resume-signal, external to this repo's commit history)
4. **Task 3 follow-on: Regenerate the committed-derived plane** - `97bebfc` (docs)

Supporting commits: `22b543a` (initial paused-state SUMMARY), `57526af` (self-check appended), `f7fb4a8` (STATE.md paused-position update) — superseded by this completed SUMMARY and the plan-completion STATE/ROADMAP update below.

## Files Created/Modified

- `contracts/harness/adoption/inventory.schema.json` - ADOPT-01 inventory artifact contract (included/excluded files, language/manifest/surface detection, enumeration_mode, max_file_bytes)
- `contracts/harness/adoption/plan.schema.json` - ADOPT-02 mapping-plan artifact contract (proposals, relationship candidates, question records)
- `contracts/harness/adoption/manifest.schema.json` - ADOPT-03 disposition manifest artifact contract (total 6-value disposition enum + excluded lanes)
- `contracts/.hashes/manifest.json` - rebaselined JCS SHA-256 manifest including the 3 new schemas; `git diff --stat` showed exactly 3 lines added, no other entry touched
- `docs/reference/inventory.md`, `docs/reference/plan.md`, `docs/reference/manifest.md` - new DERIVED Diátaxis reference pages generated from the 3 adoption schemas
- `.memory/derived/contracts-index.md` - regenerated (10 → 13 contracts indexed; the 3 new rows report `clean` drift)

## Decisions Made

- Followed the plan's schema spec literally (Task 1's `<action>` block is an exhaustive field-by-field spec); no schema-shape deviations.
- Wrote all three schemas via the repo's `HARNESS_DEV_BYPASS=1` dev-session opt-out (ADR-0007), never fabricating or setting `GOLDEN_APPROVE_HUMAN`.
- Confirmed `git diff --stat contracts/.hashes/manifest.json` touches ONLY the 3 new adoption-schema keys before committing Task 2, satisfying its acceptance criteria exactly.
- Correctly PAUSED at the blocking checkpoint rather than self-ratifying or running the derived-plane regen ahead of human confirmation — resumed only after the repo owner's independent re-verification and explicit "approved" response.

## Deviations from Plan

None — plan executed exactly as written. One clarification, not a deviation: the plan's own Task 1 `<verify><automated>` grep pattern (`grep -q '"draft/2020-12/schema"'`) does not match ANY schema in this repo — including the pre-existing precedent `contracts/harness/task-control/evidence.schema.json` — because every `$schema` value is the full URL `"https://json-schema.org/draft/2020-12/schema"` and the literal substring `'"draft/2020-12/schema"'` therefore never appears (the character before `draft` is `/`, not `"`). Verified this is a pre-existing plan/verify-script quirk, not specific to this plan's schemas, by testing the identical grep against the precedent file (also fails). The prose acceptance criteria — "contain the exact `\"$schema\": \"https://json-schema.org/draft/2020-12/schema\"` string" — IS satisfied by all three new schemas (verified directly). No fix applied; documenting for the record since it could otherwise look like a missed acceptance criterion.

## Issues Encountered

None — all tasks passed on the first attempt; determinism was proven directly (the 8 pre-existing reference pages regenerated byte-identical, only the 3 new adoption pages + contracts-index changed).

## Checkpoint Ratification

The plan's `type="checkpoint:human-verify" gate="blocking"` task was correctly NOT self-ratified by the executor. The repo owner independently re-verified the constitution-plane diff (commits `245a101`, `3f84070`) — drift OK, diffstat exactly the 3 schemas + manifest (+458 lines / 4 files, nothing else), zero cross-file `$ref`, `excludedEntry` properties exactly `[excluded, path, size]` with `additionalProperties:false`, `dispositionEnum` exactly the 6 required values, `questionRecord` required fields + id pattern correct, `candidateRecord` carries no `authority` property, and no `GOLDEN_APPROVE_HUMAN` (or any other) token anywhere under `contracts/` — then responded "approved", satisfying the plan's `<resume-signal>`. The `HARNESS_DEV_BYPASS` dev-session opt-out used to author/rebaseline the schemas was never conflated with this human ratification.

## Next Phase Readiness

- Plan 26-01 is complete: all three ADOPT-01/02/03 constitution contracts are ratified and drift-clean, the committed-derived plane is fresh, and `uv run python -m tools.contract_drift.drift` is green.
- Ready to proceed to Plan 02 (`tools/adoption_scan` scan.py + detect.py — confined read-only enumeration, exclusion classification, language/manifest/surface detection, the one synthetic mini-repo fixture) and Plan 03 (plan.py + destinations.py + cli.py), both of which now validate against these fixed, ratified shapes.
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
- FOUND: commit 245a101 (Task 1)
- FOUND: commit 3f84070 (Task 2)
- FOUND: commit 97bebfc (Task 3 follow-on: derived-plane regen)
