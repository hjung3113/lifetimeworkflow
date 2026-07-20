---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
plan: 02
subsystem: contracts
tags: [json-schema, contract-hash, contract-drift, docs-sync, memory-regen, adoption, approval]

# Dependency graph
requires:
  - phase: 26-task-local-adoption-workflow-safe-application-v2-3-b
    provides: "The three ratified brownfield-adoption contracts (inventory/manifest/plan.schema.json, ADOPT-01/02/03) and the contract-hash/drift/docs-sync/contracts-index tooling this plan reuses unmodified"
provides:
  - "contracts/harness/adoption/approval.schema.json: a NEW, self-contained (D-11, no cross-file $ref) Draft 2020-12 approval-record contract binding a promotion decision list to the exact tuple (draft_hash, task_revision, git_ref) — any change to draft content, task CAS revision, or git ref invalidates the approval"
  - "A closed 6-value decisionKindEnum (contract, golden, adr, relationship-authority, conflict, unknown) matching ADOPT-06's item kinds exactly, and a decisionRecord shape (item_id, kind, disposition in {approve,reject,defer}, optional note) — this is the exact shape Plans 27-04 and 27-06 depend on"
  - "Rebaselined contracts/.hashes/manifest.json (one new entry) with tools.contract_drift.drift clean"
  - "Regenerated committed-derived plane: docs/reference/approval.md (new page) and .memory/derived/contracts-index.md (one new row, 13→14 contracts)"
  - "Widened docs_sync EXPECTED_PAGES + an additive-only syrupy snapshot update for the new approval page"
affects: [27-04-adoption-apply-approval-py, 27-06]

# Tech tracking
tech-stack:
  added: []
  patterns: ["New self-contained sibling schema over $ref-extending an existing schema when the two binding vocabularies are structurally different (D-11)"]

key-files:
  created:
    - contracts/harness/adoption/approval.schema.json
    - docs/reference/approval.md
    - .planning/phases/27-task-local-adoption-workflow-safe-application-v2-3-b/27-02-SUMMARY.md
  modified:
    - contracts/.hashes/manifest.json
    - .memory/derived/contracts-index.md
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr

key-decisions:
  - "A1: followed — new self-contained approval.schema.json, no attestation.schema.json extension. attestation.schema.json's constraints[] array binds a task's declared constraint-source files (constraint_id, source_path, source_sha256, phase/action mappings) — a CLARIFY/SPEC-time constraint-tracking vocabulary. approval.schema.json binds a human promotion decision to (draft_hash, task_revision, git_ref) over a fixed 6-kind decision list — a structurally different EXECUTE/REVIEW-time ratification vocabulary. Reusing attestation's shape would have forced an unrelated field set (prohibited_action_ids, required_evidence_ids, applies_to_phases) onto a schema that has no use for them. The new-schema call trades a small amount of vocabulary duplication (the record-with-kind-enum pattern, also seen in manifest.schema.json's dispositionRecord) for D-11 self-containment and semantic precision — no cross-file $ref (D-11), no forced coupling between two independently-evolving binding shapes."
  - "The binding tuple is exactly (draft_hash, task_revision, git_ref) with a closed 6-value decisionKindEnum (contract, golden, adr, relationship-authority, conflict, unknown) and a disposition enum of {approve, reject, defer} — this exact shape is the ratified target Plans 27-04 (approval.py validation) and 27-06 depend on."
  - "Ratified via a blocking checkpoint:human-verify gate — the human operator reviewed the full schema text, the single-entry manifest diff, the derived-plane regeneration diff, and explicitly ratified the A1 design call (not just the bytes) on 2026-07-21 during /gsd:execute-phase 27, in-session. The mechanical write itself was permitted by the ambient HARNESS_DEV_BYPASS=1 dev-session setting — this is explicitly the mechanical-write permission only, NOT a substitute for or conflated with the human ratification recorded here."

requirements-completed: [ADOPT-06]

# Metrics
duration: 32min
completed: 2026-07-21
---

# Phase 27 Plan 02: ADOPT-06 Approval Record Contract Summary

**New self-contained `approval.schema.json` binding a promotion decision list to `(draft_hash, task_revision, git_ref)` over a closed 6-kind vocabulary, human-ratified as a deliberate non-extension of `attestation.schema.json`.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-07-20T16:29:00Z
- **Completed:** 2026-07-20T16:59:25Z (checkpoint ratified 2026-07-21 in-session)
- **Tasks:** 2 (1 auto + 1 blocking checkpoint)
- **Files modified:** 6

## Accomplishments
- Authored `contracts/harness/adoption/approval.schema.json` — a new, self-contained (D-11) Draft 2020-12 contract for the ADOPT-06 promotion-approval record
- Rebaselined `contracts/.hashes/manifest.json` via `tools.contract_hash.hash --write` only (one new entry), confirmed `tools.contract_drift.drift` clean
- Regenerated the committed-derived plane (`docs/reference/approval.md`, `.memory/derived/contracts-index.md`) with no other page/row disturbed
- Reached and closed a blocking `checkpoint:human-verify` gate — the constitution-plane write and the A1 design tradeoff were explicitly human-ratified, not agent self-approved

## Task Commits

Each task was committed atomically:

1. **Task 1: Author approval.schema.json + rebaseline hash + regenerate derived plane** - `c5e91bb` (feat)
2. **Task 2: Checkpoint — Human ratification** - human-ratified in-session 2026-07-21 (no separate code commit; ratification recorded in this SUMMARY per plan's `<output>` instruction)

**Plan metadata:** (this commit) `docs: complete 27-02 plan`

## Files Created/Modified
- `contracts/harness/adoption/approval.schema.json` - New ADOPT-06 approval-record contract
- `contracts/.hashes/manifest.json` - Rebaselined (one new entry)
- `docs/reference/approval.md` - Regenerated reference page (new)
- `.memory/derived/contracts-index.md` - Regenerated (one new row, 13→14)
- `tools/docs_sync/tests/test_docs_sync_determinism.py` - Widened `EXPECTED_PAGES` with `"approval"`
- `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` - Additive-only snapshot update for the new page

## Decisions Made

**A1: followed — new self-contained `approval.schema.json`, no `attestation.schema.json` extension.** `attestation.schema.json`'s `constraints[]` array binds a task's declared constraint-source files (`constraint_id`, `source_path`, `source_sha256`, phase/action mappings) — a CLARIFY/SPEC-time constraint-tracking vocabulary. `approval.schema.json` binds a human promotion decision to `(draft_hash, task_revision, git_ref)` over a fixed 6-kind decision list — a structurally different EXECUTE/REVIEW-time ratification vocabulary. Reusing `attestation`'s shape would have forced an unrelated field set (`prohibited_action_ids`, `required_evidence_ids`, `applies_to_phases`) onto a schema that has no use for them. The new-schema call trades a small amount of vocabulary duplication (the record-with-kind-enum pattern, also seen in `manifest.schema.json`'s `dispositionRecord`) for D-11 self-containment and semantic precision — no cross-file `$ref` (D-11), no forced coupling between two independently-evolving binding shapes.

The binding tuple is exactly `(draft_hash, task_revision, git_ref)` with a closed 6-value `decisionKindEnum` (`contract`, `golden`, `adr`, `relationship-authority`, `conflict`, `unknown`) and a `disposition` enum of `{approve, reject, defer}` — this exact shape is the ratified target Plans 27-04 and 27-06 depend on.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The initial `uv run pytest tools/docs_sync -q` run failed on `test_render_matches_committed_snapshot` because the committed syrupy snapshot did not yet include the new `approval` page. Resolved by running `--snapshot-update`, which produced an additive-only diff to the `.ambr` file (18 insertions, 0 deletions) — no existing page's snapshot text was touched. This was anticipated by the plan's own acceptance criteria ("use `--snapshot-update` ONLY for the new `approval` page's own snapshot entry, never touch an existing page's snapshot") and is not treated as a deviation.

## Human Ratification Record

Ratified via a blocking `checkpoint:human-verify` gate. The human operator reviewed, in-session:
- The full text of `contracts/harness/adoption/approval.schema.json`
- The single-entry `contracts/.hashes/manifest.json` diff
- The derived-plane regeneration diff (`docs/reference/approval.md` new, `.memory/derived/contracts-index.md` +1 row, 13→14)
- The A1 design tradeoff (new self-contained schema vs. extending `attestation.schema.json`) — ratified as a knowing design decision, not merely as bytes

The orchestrator independently verified (not from the executor's self-report): `Draft202012Validator.check_schema` passes; a well-formed approval record validates; `decisions: []` is rejected by `minItems: 1`; a malformed `git_ref` is rejected by the 40-hex pattern; `git show --stat c5e91bb` confirms one atomic commit over exactly the six expected files; `tools.contract_drift.drift` exits 0.

**Ratified:** 2026-07-21, during `/gsd:execute-phase 27`, via explicit in-session confirmation.

The `HARNESS_DEV_BYPASS=1` ambient dev-session setting permitted the Task 1 mechanical write only — it is explicitly recorded here as distinct from, and not a substitute for, this human ratification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `contracts/harness/adoption/approval.schema.json` is ratified and ready for Plan 27-04's `approval.py` to validate every `approval.json` write against before it lands.
- The `(draft_hash, task_revision, git_ref)` binding tuple and the closed 6-value `decisionKindEnum` are now the fixed contract surface Plans 27-04 and 27-06 build against — no further schema changes expected for ADOPT-06.

---
*Phase: 27-task-local-adoption-workflow-safe-application-v2-3-b*
*Completed: 2026-07-21*
