---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
plan: 08
subsystem: adoption-scan
tags: [contract-drift, inventory-schema, plan-schema, jsonschema, cross-schema-regression]

requires:
  - phase: 26-07
    provides: destination_catalog() git-tracked filter + build_manifest(catalog=) injectable-catalog param
provides:
  - inventory.schema.json's surfaceRecord.evidence tightened to minItems:1, matching plan.schema.json
  - a rebaselined contracts/.hashes/manifest.json (single hash change) + regenerated derived plane
  - a forward-direction cross-schema regression test (every schema-valid inventory produces a schema-valid plan)
  - a negative-control test proving evidence:[] now fails at the inventory-schema gate itself
affects: [27-brownfield-adoption-application]

tech-stack:
  added: []
  patterns:
    - "cross-schema regression test: construct a maximally-populated fixture satisfying schema A, feed it through the producer function, assert the output validates against schema B"

key-files:
  created: []
  modified:
    - contracts/harness/adoption/inventory.schema.json
    - contracts/.hashes/manifest.json
    - .memory/derived/contracts-index.md
    - tools/adoption_scan/tests/test_plan_classification.py
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr

key-decisions:
  - "Rebaselined inventory.schema.json toward plan.schema.json's existing minItems:1 (not the reverse) because no detect.py _surface() call site ever constructs a surfaceRecord with empty evidence — every call site is guarded by a non-empty entries check, so tightening the contract is non-breaking for the actual producer."
  - "docs/reference/inventory.md was regenerated but produced zero diff — the evidence field lives inside a nested $defs.surfaceRecord entry that docs_sync's generator does not render into the top-level properties table, so this is expected, not a missed regen step."

patterns-established:
  - "A cross-schema evidence-cardinality invariant is proven, not just asserted, by a regression test that builds a maximally-populated schema-valid fixture and validates the producer's output against the downstream schema — catches future re-divergence between the two contracts loud and fast."

requirements-completed: [ADOPT-01, ADOPT-02]

duration: 20min
completed: 2026-07-20
---

# Phase 26 Plan 08: Evidence-Cardinality Contract Reconciliation (CR-03) Summary

**`inventory.schema.json`'s `surfaceRecord.evidence` now requires `minItems: 1` (was 0), closing the cross-schema contradiction with `plan.schema.json` that previously let a schema-valid inventory crash `cli.main()` with zero artifacts written — reconciled via a human-ratified constitution-plane rebaseline plus a forward/negative regression-test pair.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2 completed (1 auto + 1 blocking checkpoint, both resolved)
- **Files modified:** 5

## Accomplishments
- `inventory.schema.json`'s `$defs.surfaceRecord.properties.evidence.minItems` changed from `0` to `1`, and its description corrected from "May be empty for an unknown/absent surface." to "A surface with no evidence is never emitted by any detector; evidence is always non-empty." — matching actual `detect.py` producer behavior, since every `_surface()` call site (`documentation_surfaces`, `ci_surfaces`, `test_surfaces`, `schema_surfaces`, `codeowners_surfaces`) only fires when its backing `entries` list is non-empty.
- `contracts/.hashes/manifest.json` rebaselined via `tools.contract_hash.hash --write` — exactly one hash changed (`inventory.schema.json`); `tools.contract_drift.drift` confirmed OK.
- Derived plane regenerated: `.memory/derived/contracts-index.md` updated (new hash); `docs/reference/inventory.md` regenerated but produced no diff (the changed field is nested inside `$defs`, which the docs_sync table renderer does not surface — confirmed this is the generator's existing behavior, not a stale-regen bug).
- Added `test_build_plan_validates_for_every_inventory_surface_shape`: constructs one maximally-populated, schema-valid inventory (non-empty `documentation_surfaces`/`ci_surfaces`/`test_surfaces`/`candidate_process_boundaries`/`schema_surfaces`/`codeowners_surfaces`, each with one minimally-shaped non-empty-evidence entry), validates it against `inventory.schema.json` (proving the fixture itself is conformant under the tightened rule), then calls `plan.build_plan()` and asserts zero `Draft202012Validator` errors against `plan.schema.json` — the forward-direction proof 26-REVIEW.md CR-03 asked for.
- Added `test_empty_evidence_surface_record_now_fails_at_inventory_schema_gate`: the exact CR-03 repro shape (`codeowners_surfaces` entry with `evidence: []`) now fails `inventory.schema.json` validation directly — proving the contradiction is caught one gate earlier than the previous `build_plan()`-time failure.
- Updated `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` (12-char hash prefix for `inventory.schema.json` changed) to keep the committed contracts-index snapshot in sync with the rebaseline — this is a Rule 1 auto-fix (the snapshot test would otherwise be the one red test in the suite after a correct rebaseline).

## Task Commits

1. **Task 1: Rebaseline surfaceRecord.evidence to minItems:1 + derived-plane regen + cross-schema regression test** - `6a18c29` (fix)
2. **Task 2: Human ratification of the evidence-cardinality rebaseline** - human-ratified in-session (checkpoint, no separate commit — see below)

**Plan metadata:** (this summary's commit)

## Files Created/Modified
- `contracts/harness/adoption/inventory.schema.json` - `surfaceRecord.evidence` tightened to `minItems: 1`, description corrected
- `contracts/.hashes/manifest.json` - rebaselined (one hash changed)
- `.memory/derived/contracts-index.md` - regenerated
- `tools/adoption_scan/tests/test_plan_classification.py` - added `_minimal_surface_record` helper + the forward-direction and negative-control regression tests
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` - regenerated to match the new hash (Rule 1 auto-fix)

## Decisions Made
- Rebaselined `inventory.schema.json` toward `plan.schema.json`'s existing `minItems: 1` (the non-breaking direction, per `detect.py` producer-behavior evidence), not the reverse.
- The one incidental follow-on file — the `contracts_index` `.ambr` snapshot — was regenerated via `--snapshot-update` under Rule 1 (auto-fix bugs) since it is a direct, mechanical consequence of the hash rebaseline this task already performs, not new scope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Regenerated the stale `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` snapshot**
- **Found during:** Task 1 full-suite verification (`uv run pytest -q`)
- **Issue:** After the hash rebaseline, `test_render_matches_committed_snapshot` failed because the committed `.ambr` still pinned the old `inventory.schema.json` hash prefix (`1fafc89580c9`) against the new live value (`34a31944180f`).
- **Fix:** Ran `uv run pytest tools/memory_regen/tests/test_contracts_index.py -q --snapshot-update` to regenerate the snapshot, then confirmed the diff touched only the one expected hash prefix.
- **Files modified:** `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`
- **Verification:** Full suite re-run green (`1026 passed`); diff inspected and limited to the single hash line.
- **Committed in:** `6a18c29` (part of Task 1's atomic commit, per the plan's WR-10 one-commit requirement)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug/stale-derived fix)
**Impact on plan:** Necessary to keep the full suite green after the contract rebaseline; folded into the same atomic commit per the plan's own atomicity requirement, so no scope creep beyond what the plan already mandated.

## Issues Encountered
None beyond the one auto-fixed stale snapshot above.

## Checkpoint Ratification

Task 2 (`checkpoint:human-verify`, `gate="blocking"`) was NOT self-approved. The agent presented the schema diff (`surfaceRecord.evidence` `minItems` 0→1 + description correction) and the rebaselined `contracts/.hashes/manifest.json` diff, along with `contract-drift.drift` OK and full-suite-green evidence, and paused. The team lead independently re-verified (`contract_drift.drift` OK, `pytest tools/adoption_scan -q` 64 passed, `docs_sync` re-run clean, repo-wide grep confirming no existing producer emits `evidence: []`) before relaying the human's approval. `HARNESS_DEV_BYPASS` (a dev-only write-permission flag, distinct from human ratification) was the mechanism that allowed the agent's constitution-plane write; it was never conflated with, nor substituted for, the human's review-and-approve step. CODEOWNERS review at PR merge to `main` remains the durable, mechanical gate for this repo (see STATE.md's standing note on `main` vs the default working branch).

## Next Phase Readiness
- CR-03 (26-VERIFICATION.md gap 2) is closed: `inventory.schema.json` and `plan.schema.json` now agree on evidence cardinality; no schema-valid inventory can produce a `build_plan()` output that fails `plan.schema.json` validation, proven by an executable regression test rather than by prose.
- No blockers for Phase 27 (ADOPT-04..07, brownfield-adoption application): this plan touched only the `inventory.schema.json` contract, its hash/derived-plane pair, and one test file; the inventory/plan shapes consumed downstream are otherwise unchanged.

---
*Phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b*
*Completed: 2026-07-20*
