---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
plan: 04
subsystem: infra
tags: [refuse-by-default, human-ratification, cas, jsonschema, adoption-workflow]

# Dependency graph
requires:
  - phase: 27-01
    provides: "batch.py — create_or_resume_batch/read_status/update_status, _batch_dir layout, CAS-guarded status.json"
  - phase: 27-02
    provides: "contracts/harness/adoption/approval.schema.json — the ratified (batch_id, draft_hash, task_revision, git_ref, decisions, approved_at) shape, closed decisionKindEnum/disposition"
provides:
  - "tools/adoption_apply/approval.py — AdoptionApprovalRefused, promote(), check_valid(): the ADOPT-06 refuse-by-default human-ratification gate bound to (draft_hash, task_revision, git_ref)"
  - "SC-1 full resume + invalidation cycle proven end-to-end, composing 27-01's batch.py with this plan's approval.py"
affects: [27-05, 27-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Refuse-by-default promotion mirrors tools/golden_runner/approve.py's three-signal order (flag, decision-reference/decisions, human-confirmation env var) — same GOLDEN_APPROVE_HUMAN env var reused, not a second adoption-specific variable"
    - "check_valid() recomputes every element of the (draft_hash, task_revision, git_ref) binding fresh at call time — never cached, never a prefix/descendant fuzzy match (mirrors handoff.py::validate's strict exact-membership ref check)"
    - "approval.json uses os.replace-based atomic replace (not create-once) — an approval may be legitimately re-issued after invalidation"

key-files:
  created:
    - tools/adoption_apply/approval.py
    - tools/adoption_apply/tests/test_approval_invalidation.py
  modified: []

key-decisions:
  - "Reused the exact GOLDEN_APPROVE_HUMAN env var name/precedent from golden_runner/approve.py rather than inventing an adoption-specific variable, per 27-RESEARCH Code Examples guidance"
  - "promote()'s three refusal checks (approve flag, non-empty decisions, human confirmation) run in that fixed order, mirroring golden_runner/approve.py's shape exactly, without importing its private names — a peer module with a different binding tuple"
  - "_recompute_draft_hash reads the batch's inventory.json/plan.json/manifest.json raw bytes directly (already deterministic JSON as written by adoption_scan.cli), concatenated in a fixed order — no re-canonicalization needed on read"

patterns-established:
  - "Fresh-recompute invalidation: any single-axis change (draft/revision/ref) independently invalidates a prior approval, proven by three separate tests holding the other two axes constant"

requirements-completed: [ADOPT-04, ADOPT-06]

# Metrics
duration: 12min
completed: 2026-07-21
---

# Phase 27 Plan 04: Approval Refuse-by-Default Gate + SC-1 Resume Cycle Summary

**`approval.py`'s refuse-by-default `promote()`/`check_valid()` gate, bound to a fresh-recomputed `(draft_hash, task_revision, git_ref)` exact-equality triple, mirroring `golden_runner/approve.py`'s proven human-ratification pattern — with the full SC-1 resume+invalidation cycle proven end to end against `batch.py`.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-21T00:00:00Z
- **Completed:** 2026-07-21T00:12:00Z
- **Tasks:** 2 completed (Task 2's `test_sc1_full_resume_cycle` landed in the same TDD GREEN commit as Task 1, since it composes the same fixtures/helpers as the invalidation tests)
- **Files modified:** 2 created

## Accomplishments
- `AdoptionApprovalRefused`, `promote()`, and `check_valid()` implemented per the plan's `<behavior>` block, refusing promotion unless an explicit `approve` flag, at least one decision, and a `GOLDEN_APPROVE_HUMAN`-matched confirmation are all present — in that fixed order, mirroring `tools/golden_runner/approve.py`
- Approval binding is `(draft_hash, task_revision, git_ref)`, each recomputed FRESH at every `check_valid` call — `_recompute_draft_hash` hashes the batch's 3 draft files, `_current_task_revision` delegates to `tools.task_control.manager.show`, `_current_git_ref` is an own-copy fixed-argv `git rev-parse HEAD` helper
- 7 tests all green and independently passing (verified via `-k <name>` isolation runs): 2 refusal tests, 3 INDEPENDENT single-axis invalidation tests (draft-only, revision-only, ref-only — each holding the other two axes constant), 1 positive control, and `test_sc1_full_resume_cycle` proving SC-1's full sentence end to end
- Every `approval.json` write is validated against `contracts/harness/adoption/approval.schema.json` via `Draft202012Validator` before being durably written (`os.replace`-based, since an approval may be legitimately re-issued after invalidation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Refuse-by-default promote() + fresh-recomputed exact-equality invalidation**
   - RED: `e48d45a` (test) — collection fails: `tools.adoption_apply.approval` does not exist yet (verified via a temporary file move + failing pytest run before committing)
   - GREEN: `ee8702f` (feat) — implementation lands, all 7 tests pass (Task 2's `test_sc1_full_resume_cycle` is included in this same test file/commit, since it reuses Task 1's fixtures)
2. **Task 2: SC-1 full resume + invalidation cycle** — folded into the Task 1 RED/GREEN pair above; `test_sc1_full_resume_cycle` is present in the same `test_approval_invalidation.py` file committed in `e48d45a`/`ee8702f`

_No REFACTOR commit was needed — `ruff check` found one fixable style nit (unnecessary `encoding="utf-8"` argument) which was corrected before the GREEN commit landed, not after._

## Files Created/Modified
- `tools/adoption_apply/approval.py` - `AdoptionApprovalRefused`, `promote()`, `check_valid()`, plus private `_recompute_draft_hash`/`_current_task_revision`/`_current_git_ref`/`_validate_against_schema`/`_atomic_replace` helpers
- `tools/adoption_apply/tests/test_approval_invalidation.py` - 7 tests: 2 refusal, 3 independent single-axis invalidation, 1 positive control, 1 SC-1 composed integration test

## Decisions Made
- Reused `GOLDEN_APPROVE_HUMAN` verbatim rather than a new adoption-specific env var (RESEARCH-mandated precedent, also shared with `tools/hooks/contract_guard.py`)
- Test fixtures write `state.json` directly (bypassing `manager.create`/`transition`) to keep the fixture focused purely on schema-valid revision bumps, not task-control lifecycle policy — `show()` (the only manager.py entry point `approval.py` calls) only reads and schema-validates, so this is a legitimate test shortcut, not a deviation in the shipped module
- Draft-hash recomputation reads the 3 batch files' raw bytes directly rather than re-parsing/re-canonicalizing JSON on read, since `adoption_scan.cli`'s `scan._dump` already writes deterministic bytes

## Deviations from Plan

None - plan executed exactly as written. Task 2 was folded into Task 1's commit pair rather than getting its own separate commit, since `test_sc1_full_resume_cycle` reuses the exact fixtures/helpers (`git_repo`, `task_dir`, `_seed_batch`, `_write_draft`) authored for Task 1's invalidation tests, and splitting them across two commits would have required either duplicating fixtures or an artificial partial-file commit. This is a mechanical commit-grouping choice, not a scope or behavior deviation — both tasks' acceptance criteria are fully met and independently verified (`test_sc1_full_resume_cycle -x` passes standalone).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. `GOLDEN_APPROVE_HUMAN` is a human-provided environment variable at promotion time, already an established precedent from `tools/golden_runner/approve.py` (no new setup surface introduced).

## Next Phase Readiness
- `tools/adoption_apply` now ships `batch.py` (27-01), `apply.py` (27-03), and `approval.py` (27-04) — the full ADOPT-04/05/06 machinery
- 27-05 (SC-3 fixtures) and 27-06 (CLI + `/adopt` command + skill) can compose `promote()`/`check_valid()` directly; no further approval-layer work outstanding
- Full suite green at 1079 passed (was 1072 before this plan; +7 new tests, 0 regressions); `uv.lock` and `contracts/` untouched (D-01 upheld)

---
*Phase: 27-task-local-adoption-workflow-safe-application-v2-3-b*
*Completed: 2026-07-21*
