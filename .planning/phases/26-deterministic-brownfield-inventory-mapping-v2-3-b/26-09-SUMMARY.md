---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
plan: 09
subsystem: adoption-scan
tags: [contract-candidate, codeowners, plan-classification, detect, jsonschema]

requires:
  - phase: 26-08
    provides: inventory.schema.json surfaceRecord.evidence minItems:1 (evidence pointers always non-empty)
provides:
  - plan.py::classify() now walks inventory["schema_surfaces"] per evidence pointer, emitting one contract-candidate proposal per schema file
  - detect.py::detect_codeowners_surfaces() recognizes all three GitHub-honored CODEOWNERS locations (CODEOWNERS, .github/CODEOWNERS, docs/CODEOWNERS)
  - five new tests proving both fixes, including a live-repo-scan assertion against this checkout's own contracts/ tree
affects: [27-brownfield-adoption-application]

tech-stack:
  added: []
  patterns:
    - "live-count-matched test assertion: never hardcode a real-repo file count in a test; derive it via rglob at test time (test_dispositions.py's existing pattern, now reused here)"

key-files:
  created: []
  modified:
    - tools/adoption_scan/plan.py
    - tools/adoption_scan/detect.py
    - tools/adoption_scan/tests/test_plan_classification.py
    - tools/adoption_scan/tests/test_detect.py
    - tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr

key-decisions:
  - "classify()'s new schema_surfaces walk loop is placed immediately after the existing codeowners_surfaces loop, mirroring its exact shape, per the plan's <interfaces> precedent."
  - "detect_codeowners_surfaces() rewritten to a frozenset membership check + per-path surfaceRecord (never one lumped record), mirroring detect_documentation_surfaces()'s per-nested-AGENTS.md precedent."

patterns-established:
  - "contract-candidate proposals always hardcode classification:'unknown' — whether a schema is a tracked, ratified contract is a human/CODEOWNERS-gated decision, never inferred from file existence."

requirements-completed: [ADOPT-01, ADOPT-02]

duration: 15min
completed: 2026-07-20
---

# Phase 26 Plan 09: schema_surfaces Wiring (WR-05) + Multi-Location CODEOWNERS Detection (WR-06) Summary

**`plan.py::classify()` now emits a `contract-candidate` proposal per schema-file evidence pointer (closing the last permanently-dead-code question kind in this phase's gap-closure round), and `detect_codeowners_surfaces()` now recognizes all three GitHub-honored CODEOWNERS locations instead of only `.github/CODEOWNERS`.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 1 completed (auto, tdd)
- **Files modified:** 5

## Accomplishments
- `plan.py::classify()` gained a `schema_surfaces` walk loop placed after the existing `codeowners_surfaces` loop: for each `entry` in `inventory.get("schema_surfaces", [])`, for each `ref` in `entry["evidence"]`, emits one `contract-candidate` proposal (`classification` always `"unknown"`) — closing WR-05, the identical defect class Plan 26-05 already fixed for `codeowners_surfaces`. No changes needed to `_QUESTION_KIND_BY_PROPOSAL_KIND`, `_GROUP_BY_QUESTION_KIND`, `_BLOCKING_KINDS`, or `_question_text()` — all already carried the `"contract-candidate"` wiring from a prior plan.
- `detect.py::detect_codeowners_surfaces()` widened from a single `.github/CODEOWNERS` equality check to a `_CODEOWNERS_PATHS` frozenset membership check (`CODEOWNERS`, `.github/CODEOWNERS`, `docs/CODEOWNERS`), emitting one `surfaceRecord` per distinct matching path found (sorted by `target`) — closing WR-06.
- Five new tests added:
  - `test_contract_candidate_question_fires` — a `schema_surfaces` entry produces exactly one `contract-candidate` proposal + one non-blocking `contract-candidate` question.
  - `test_contract_candidate_proposal_per_schema_file` — two evidence pointers in one `schema_surfaces` entry produce two separate proposals, not one lumped proposal.
  - `test_contract_candidate_matches_real_repo_schema_count` — a real scan of this harness's own `contracts/` tree produces exactly one `contract-candidate` proposal per live `*.schema.json` file (derived via `rglob` at test time, never hardcoded, mirroring `test_dispositions.py`'s `test_catalog_covers_real_contract_schemas` pattern).
  - `test_codeowners_surface_root_location` and `test_codeowners_surface_docs_location` — each of the two previously-unrecognized CODEOWNERS locations independently produces its own `surfaceRecord`.
- Refreshed `test_snapshots.ambr`: diff inspected and confirmed to touch only the `===== plan =====` section (one new `contract-candidate` proposal + question for `tmp_minirepo`'s existing `contracts/widget.schema.json` fixture case), with `===== inventory =====` and `===== manifest =====` untouched.

## Task Commits

1. **Task 1: plan.py schema_surfaces wiring (WR-05) + detect.py multi-path CODEOWNERS (WR-06)** - `b240832` (fix)

**Plan metadata:** (this summary's commit)

## Files Created/Modified
- `tools/adoption_scan/plan.py` - `classify()` gains the `schema_surfaces` walk loop emitting per-evidence-pointer `contract-candidate` proposals
- `tools/adoption_scan/detect.py` - `detect_codeowners_surfaces()` widened to the three-location `_CODEOWNERS_PATHS` frozenset, one surfaceRecord per matching path
- `tools/adoption_scan/tests/test_plan_classification.py` - three new tests (question-fires, per-schema-file granularity, live-repo-count match)
- `tools/adoption_scan/tests/test_detect.py` - two new tests (root and docs/ CODEOWNERS locations)
- `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr` - refreshed, plan section only

## Decisions Made
- Mirrored the plan's `<interfaces>` precedent exactly for the `schema_surfaces` walk shape (walking `entry["evidence"]`, not the outer list, since `detect_schema_surfaces()` returns at most one per-repo record whose evidence list has one entry per matching schema file).
- Widened `detect_codeowners_surfaces()` via a frozenset + dict-of-matches rather than three separate equality checks, keeping the function's shape close to `detect_documentation_surfaces()`'s existing per-path pattern.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- `schema_surfaces` reaches a classified `contract-candidate` proposal/question on a real scan — the last permanently-dead-code defect class from this phase's gap-closure round is closed.
- `detect_codeowners_surfaces()` recognizes all three GitHub-honored CODEOWNERS locations.
- Full suite (1031 passed), `contract-drift` (OK), GEN-04 guard (18 passed), and `uv.lock` (unchanged) all green.
- This was the final plan (09 of 9) of Phase 26 — deterministic-brownfield-inventory-mapping-v2-3-b. No blockers for Phase 27 (ADOPT-04..07, brownfield-adoption application).

---
*Phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b*
*Completed: 2026-07-20*
