---
phase: 41-docs-review-plane-removal
plan: 01
subsystem: infra
tags: [docs-review-plane, deletion, ADR-0012, CER-05, tools.docs_guard]

# Dependency graph
requires:
  - phase: 40-self-gate-teardown
    provides: the delete->stage->commit->verify->amend-if-red discipline (D-10) and the
      YAML-resolved gate.needs check method, both reused verbatim here
provides:
  - docs/doc-dependencies.toml unbound (0 [[binding]] rows) then deleted outright
  - docs/.docs-review-ledger.toml deleted (not authored/edited — D-08)
  - tools/docs_guard/ (6110 LOC guard package + its 8-file test suite) deleted entirely
  - docs/reference/doc-dependencies.md (derived page) deleted
affects: [41-02, 41-03, 41-04, 41-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [unbind-before-delete (D-09), pathspec-scoped commits (D-11), deletion-only phase with no replacement (D-06)]

key-files:
  created: []
  modified:
    - docs/doc-dependencies.toml (emptied of bindings, then deleted)
    - docs/.docs-review-ledger.toml (deleted)
    - tools/docs_guard/ (deleted, 19 files)
    - docs/reference/doc-dependencies.md (deleted)

key-decisions:
  - "Followed D-09 unbind-first: Task 1 landed the 8-binding removal + ledger deletion as its own commit before any tool/package deletion in Task 2."
  - "Did not touch contracts/harness/docs/doc-dependencies.schema.json — reserved for Plan 04's rebaseline-paired deletion, per D-02 and the plan's explicit scope boundary."
  - "Left the two now-expected-red memory_regen collection errors unfixed — Plan 02/03's job per D-03 and this plan's own out-of-scope list."

patterns-established:
  - "Pattern: unbind-then-delete ordering for any future registry+ledger+guard-package removal — empty the binding/registry surface in a standalone commit before deleting the tool that reads it, so no dangling binding ever references a since-removed contract."

requirements-completed: [CER-05]

# Metrics
duration: 12min
completed: 2026-07-27
---

# Phase 41 Plan 01: Docs-Review Plane Unbind + Guard Package Deletion Summary

**Deleted the 6110-LOC `tools/docs_guard` package plus its bindingless registry and derived reference page, after first emptying all 8 `[[binding]]` rows and removing the human-authored ledger in a dedicated unbind commit — 6,335 total lines removed across two pathspec-scoped commits, zero replacement of any kind.**

## Performance

- **Duration:** ~12 min
- **Tasks:** 2 completed
- **Files modified:** 22 (1 edited-then-deleted, 21 deleted outright)

## Accomplishments
- Emptied `docs/doc-dependencies.toml` of all 8 `[[binding]]` rows and deleted `docs/.docs-review-ledger.toml` (90 lines) in one commit, satisfying D-09's unbind-first ordering and D-08's "deletion is not authoring" rule.
- Deleted the entire `tools/docs_guard/` package (10 non-test files + 9 test files, 6110 LOC) plus the now-consumerless `docs/doc-dependencies.toml` and its derived `docs/reference/doc-dependencies.md` page in a second, independently pathspec-scoped commit.
- Confirmed `contracts/harness/docs/doc-dependencies.schema.json` remains untouched, correctly deferred to Plan 04's rebaseline-paired deletion.

## Task Commits

Each task was committed atomically:

1. **Task 1: Unbind — empty the registry and delete the ledger (D-09)** - `711030e` (feat)
2. **Task 2: Delete the guard package, the emptied registry, and its derived page** - `d2ca9da` (feat)

_No plan-metadata commit separate from these two — this summary/STATE/ROADMAP update is the final commit for this plan._

## Files Created/Modified
- `docs/doc-dependencies.toml` - emptied of all 8 `[[binding]]` rows in commit 1 (header comment block preserved), then deleted outright in commit 2
- `docs/.docs-review-ledger.toml` - deleted (90 lines; not an edit to a `[[reviewed]]` row)
- `tools/docs_guard/{guard,cli,ledger,registry,impact,digest,exclusions,__main__,__init__}.py`, `pyproject.toml`, `tests/*` (9 files) - deleted (6110 LOC)
- `docs/reference/doc-dependencies.md` - deleted (11-line derived page)

## Decisions Made
- Confirmed the mechanical binding count (`grep -c '^\[\[binding\]\]'`) was exactly 8 before editing, matching D-09/CONTEXT.md.
- Kept `docs/doc-dependencies.toml`'s header comment block intact through Task 1 (only bindings removed), then deleted the whole file in Task 2 — matches the plan's explicit two-step instruction.
- Left `contracts/harness/docs/doc-dependencies.schema.json`, `tools/hooks/ledger_guard.py`, `.github/workflows/ci.yml`, and every other out-of-scope surface named in the plan's rule 6 untouched.

## Deviations from Plan

None — plan executed exactly as written. No Rule 1/2/3/4 auto-fixes were needed; this is a pure, mechanical two-commit deletion matching the plan's tasks verbatim.

## Issues Encountered

**Minor divergence from CONTEXT.md's predicted red-test set (not a defect):** CONTEXT.md's `<interfaces>` section named `tools/adoption_apply/tests/test_docs_binding_proposal.py` as a test expected to go red immediately after Task 2's commit (it reads `docs/doc-dependencies.toml`'s path constant and imports the schema). On actual re-run (`uv run pytest tools/adoption_apply/tests/test_docs_binding_proposal.py -q`), **all 7 tests in that file still pass** — it references the schema file (still present, Plan 04's target) and the registry path as a string constant, but does not `open()`/read the deleted `docs/doc-dependencies.toml` at collection or test time in a way that fails yet. The plan's own frontmatter/verification section correctly anticipated a *different*, actually-observed pair instead:
- `tools/memory_regen/tests/test_docs_staleness.py` — `ModuleNotFoundError: No module named 'tools.docs_guard'` (imports `tools.docs_guard.guard` at `docs_staleness.py:42`)
- `tools/memory_regen/tests/test_inject_docs_pointer.py` — same `ModuleNotFoundError` (imports `tools.docs_guard.guard` directly)

Both are exactly the two collection failures the plan's `<verification>` block predicted (`uv run pytest --collect-only -q` — "exactly two collection failures... both importing the now-deleted `tools.docs_guard`"). This is the expected intermediate state, not a regression — Plan 02/03's job per D-03. `test_docs_binding_proposal.py` will separately go red once Plan 04 deletes the schema it reads; that is out of this plan's scope.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02/03 can now proceed: `tools/memory_regen/docs_staleness.py` and its two test files are confirmed red (`ModuleNotFoundError: tools.docs_guard`) and ready for Plan 02/03's deletion per D-03. `tools/adoption_apply/tests/test_docs_binding_proposal.py` is unexpectedly still green — Plan 04 (or whichever plan owns D-04's adoption-consumer edit) should re-verify it goes red once the schema file is deleted, rather than assuming it is already red now.

No blockers. `contracts/harness/docs/doc-dependencies.schema.json` is confirmed present and untouched for Plan 04.

## Self-Check: PASSED

- `test ! -e tools/docs_guard` — FOUND: gone (confirmed via `test` exit 0)
- `test ! -f docs/doc-dependencies.toml` — FOUND: gone (confirmed via `test` exit 0)
- `test ! -f docs/reference/doc-dependencies.md` — FOUND: gone (confirmed via `test` exit 0)
- `test ! -f docs/.docs-review-ledger.toml` — FOUND: gone (confirmed via `test` exit 0)
- `test -f contracts/harness/docs/doc-dependencies.schema.json` — FOUND: present (confirmed via `test` exit 0)
- Commit `711030e` — FOUND in `git log --oneline`
- Commit `d2ca9da` — FOUND in `git log --oneline`
- `git diff --stat 711030e~1..d2ca9da` reports **6,335 total deletions** across both commits (D-17 measured, not estimated)

---
*Phase: 41-docs-review-plane-removal*
*Completed: 2026-07-27*
