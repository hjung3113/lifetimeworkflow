---
phase: 41-docs-review-plane-removal
plan: 02
subsystem: infra
tags: [docs-review-plane, deletion, ADR-0010, CER-05, ledger_guard, adoption_apply]

# Dependency graph
requires:
  - phase: 41-docs-review-plane-removal
    plan: "41-01"
    provides: docs/.docs-review-ledger.toml deleted, tools/docs_guard/ deleted, two
      expected-red memory_regen collection errors (tools.docs_guard) left for Plan 03
provides:
  - tools/hooks/ledger_guard.py deleted (the ADR-0010 clause 3b layer-1 PreToolUse hook)
  - harness/plugins/ledger-guard.ts deleted (its unexecuted opencode twin)
  - harness/permission-matrix.json's docs/.docs-review-ledger.toml deny glob + "THIRD
    path-deny domain" _note prose removed
  - tools/harness_emit/merge.py's HARNESS_SIGNATURES + ledger_guard hook-group dict removed
  - tools/adoption_apply/apply.py's ReviewLedgerRefusal class, ledger_guard import, and
    ledger-glob check removed; refuse_unsafe_destination and apply_manifest still work
  - tools/adoption_apply/cli.py's apply_module.ReviewLedgerRefusal catch clause removed
    (Rule 1 fix, undocumented consumer found this session)
  - tools/adoption_apply/tests/test_constitution_refusal.py's ledger-specific trailing
    section (11 tests + REVIEW_LEDGER_DESTINATIONS) removed; ConstitutionRefusal-only
    tests intact
  - tools/adoption_apply/tests/test_docs_binding_proposal.py deleted outright (D-04)
affects: [41-03, 41-04, 41-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [pathspec-scoped commits (D-11), source-first emitter edits (D-12),
    deletion-only phase with no replacement (D-06)]

key-files:
  created: []
  modified:
    - tools/hooks/ledger_guard.py (deleted, 90 lines)
    - harness/plugins/ledger-guard.ts (deleted, 77 lines)
    - harness/permission-matrix.json (glob entry + note prose trimmed)
    - tools/harness_emit/merge.py (HARNESS_SIGNATURES entry + hook-group dict removed)
    - tools/adoption_apply/apply.py (39 lines removed)
    - tools/adoption_apply/cli.py (1 line removed — Rule 1 fix)
    - tools/adoption_apply/tests/test_constitution_refusal.py (247 lines removed)
    - tools/adoption_apply/tests/test_docs_binding_proposal.py (deleted, 244 lines)

key-decisions:
  - "Fixed tools/adoption_apply/cli.py's apply_module.ReviewLedgerRefusal catch clause as a Rule 1 auto-fix — not in the plan's files_modified list, but uv run pytest tools/adoption_apply -q surfaced an AttributeError the moment ReviewLedgerRefusal was deleted from apply.py, the exact same undocumented-consumer failure mode RESEARCH.md's Pitfall 2 predicted for apply.py itself."
  - "Also removed now-unused imports (merge_module, merge_settings, load_matrix, resolve_path, REPO_ROOT, CONSTITUTION_GLOBS) from test_constitution_refusal.py beyond the plan's explicit `from tools.hooks import ledger_guard` instruction — they were only referenced by the deleted ledger-specific test section, and ruff check confirms the file is now clean."
  - "Left tools/harness_emit/tests/test_coexist.py and tools/hooks/tests/test_settings_coexist.py untouched — both reference the string literal \"tools.hooks.ledger_guard\" in fixture data simulating the still-live .claude/settings.json (which Plan 03's re-emit has not yet regenerated), not a Python import; both pass unchanged."
  - "Confirmed the two tools/memory_regen collection errors (ModuleNotFoundError: tools.docs_guard) are the same pre-existing Plan 01 deviation, unrelated to this plan's edits — deferred to Plan 02/03's memory_regen job per D-03 and this plan's own out-of-scope rule 6."

requirements-completed: [CER-05]

# Metrics
duration: ~25min
completed: 2026-07-27
---

# Phase 41 Plan 02: Ledger-Guard Hook + Adoption-Apply Consumer Removal Summary

**Deleted the `ledger_guard` PreToolUse hook (90 lines) and its opencode twin (77 lines), trimmed the two files that reference it as data, and repaired the two Python-level consumers RESEARCH.md and a live test run found (`tools/adoption_apply/apply.py`'s module-level import plus its undocumented sibling `cli.py`), removing 717 total lines across two pathspec-scoped commits.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 completed
- **Files modified:** 8 (2 deleted outright as the hook pair, 4 edited, 1 test file deleted outright, 1 undocumented-consumer fix)

## Accomplishments
- Deleted `tools/hooks/ledger_guard.py` and `harness/plugins/ledger-guard.ts`; trimmed `harness/permission-matrix.json`'s `path_deny_globs` array and `_note` prose; removed `tools.hooks.ledger_guard` from `tools/harness_emit/merge.py`'s `HARNESS_SIGNATURES` and deleted its hook-group dict + preceding ADR-0010 comment — one pathspec-scoped commit (`04c411d`, 186 deletions / 2 insertions).
- Removed `ReviewLedgerRefusal`, the `tools.hooks.ledger_guard` import, and the ledger-glob check from `tools/adoption_apply/apply.py`'s `refuse_unsafe_destination`; narrowed `apply_manifest`'s except clause to `ConstitutionRefusal` only; removed the ledger-specific trailing test section (11 tests) from `test_constitution_refusal.py`; deleted `test_docs_binding_proposal.py` outright (D-04) — a second pathspec-scoped commit (`2cc5ef1`, 531 deletions / 4 insertions).
- Found and fixed an undocumented third consumer: `tools/adoption_apply/cli.py`'s `except (... apply_module.ReviewLedgerRefusal ...)` clause, which raised `AttributeError` the moment `apply.py`'s class was deleted — caught by running `uv run pytest tools/adoption_apply -q` before committing, exactly the discipline RESEARCH.md's Pitfall 2 prescribed.
- Confirmed `tools.adoption_apply.apply` imports cleanly (`uv run python -c "import tools.adoption_apply.apply"` exits 0) and `uv run pytest tools/adoption_apply -q` is 100/100 green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Delete the hook + its emitter wiring, edit permission-matrix.json** - `04c411d` (feat)
2. **Task 2: Fix the undocumented adoption_apply consumers and delete the docs-binding proposal test** - `2cc5ef1` (feat)

_No plan-metadata commit separate from these two — this summary/STATE/ROADMAP update is the final commit for this plan._

## Files Created/Modified
- `tools/hooks/ledger_guard.py` - deleted (90 lines)
- `harness/plugins/ledger-guard.ts` - deleted (77 lines)
- `harness/permission-matrix.json` - removed `"docs/.docs-review-ledger.toml"` from `path_deny_globs`; trimmed the "THIRD path-deny domain" sentence span from `_note`, leaving every other clause verbatim
- `tools/harness_emit/merge.py` - removed `"tools.hooks.ledger_guard"` from `HARNESS_SIGNATURES` (6→5 entries); deleted the `ledger_guard` `PreToolUse` hook-group dict and its ADR-0010 clause 3b comment
- `tools/adoption_apply/apply.py` - 39 lines removed: the `ReviewLedgerRefusal` class + docstring, its justification comment, the `from tools.hooks.ledger_guard import REVIEW_LEDGER_GLOBS` import, the ledger-glob check block in `refuse_unsafe_destination`, and one line of now-stale docstring prose in `apply_manifest`
- `tools/adoption_apply/cli.py` - 1 line removed: `apply_module.ReviewLedgerRefusal` from the CLI's exception tuple (Rule 1 fix)
- `tools/adoption_apply/tests/test_constitution_refusal.py` - 247 lines removed: `from tools.hooks import ledger_guard`, the now-unused `LEDGER_REL` constant and 5 other now-dead imports (`merge_module`, `merge_settings`, `load_matrix`, `resolve_path`, `REPO_ROOT`, `CONSTITUTION_GLOBS`), and the entire `REVIEW_LEDGER_DESTINATIONS`-through-EOF trailing section (11 ledger-specific test functions)
- `tools/adoption_apply/tests/test_docs_binding_proposal.py` - deleted outright (244 lines, D-04)

## Decisions Made
- Rule 1 auto-fix applied to `cli.py` (not in the plan's `files_modified` list): `uv run pytest tools/adoption_apply -q` surfaced `AttributeError: module 'tools.adoption_apply.apply' has no attribute 'ReviewLedgerRefusal'` in 3 CLI subprocess tests immediately after Task 2's `apply.py` edit, before that edit was committed. Fixed inline in the same commit per the shared Rule 1-3 process (fix → verify → continue → track as deviation).
- Removed the now-dead imports in `test_constitution_refusal.py` beyond the plan's literal instruction (`from tools.hooks import ledger_guard` only) because they were exclusively used by the deleted ledger-specific section; `uv run ruff check` on the file confirms zero unused-import warnings.
- Left `tools/harness_emit/tests/test_coexist.py` and `tools/hooks/tests/test_settings_coexist.py` untouched: both carry the string `"tools.hooks.ledger_guard"` as fixture DATA (simulating the still-live, not-yet-re-emitted `.claude/settings.json`), not a Python `import` statement — both pass unmodified and are explicitly out of scope until Plan 03's re-emit.
- Left `.opencode/plugin/ledger-guard.ts`, `.claude/settings.json`, and `contracts/harness/security/deny-domains.json` untouched per phase-critical rule 4/6 — Plan 03's re-emit job.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `tools/adoption_apply/cli.py`'s dangling `ReviewLedgerRefusal` reference**
- **Found during:** Task 2, running `uv run pytest tools/adoption_apply -q` before committing
- **Issue:** `cli.py`'s `_cmd_apply` exception tuple referenced `apply_module.ReviewLedgerRefusal`, which no longer exists once `apply.py`'s class was removed — `AttributeError` at call time, failing 3 CLI subprocess tests (`test_cli_apply_refuses_hostile_destination_cleanly` and both `test_cli_apply_refuses_directory_shaped_destination` parametrizations)
- **Fix:** Removed the `apply_module.ReviewLedgerRefusal,` line from the `except (...)` tuple in `cli.py`
- **Files modified:** `tools/adoption_apply/cli.py`
- **Commit:** `2cc5ef1` (same commit as the rest of Task 2, since the fix was applied before the commit)

## Issues Encountered

None beyond the Rule 1 fix above. `uv run pytest --collect-only -q` shows the same 2 pre-existing collection errors documented in Plan 01's SUMMARY (`tools/memory_regen/tests/test_docs_staleness.py` and `test_inject_docs_pointer.py`, both `ModuleNotFoundError: tools.docs_guard`) — unchanged by this plan, deferred to Plan 03.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 03 can now proceed with `tools/memory_regen/**` and `harness/commands/docs-update.md` + `harness/skills/docs-upkeep/**` deletion, and the emitter re-run that will regenerate `.claude/settings.json`/`.opencode/**` without the `ledger_guard` hook group. No blockers.

## Self-Check: PASSED

- `test ! -f tools/hooks/ledger_guard.py` — FOUND: gone (confirmed via `test` exit 0)
- `test ! -f harness/plugins/ledger-guard.ts` — FOUND: gone (confirmed via `test` exit 0)
- `grep -c 'docs/.docs-review-ledger.toml' harness/permission-matrix.json` — 0 (confirmed)
- `grep -ci 'third path-deny domain' harness/permission-matrix.json` — 0 (confirmed)
- `grep -c 'tools.hooks.ledger_guard' tools/harness_emit/merge.py` — 0 (confirmed)
- `grep -c 'ledger_guard\|ReviewLedgerRefusal\|REVIEW_LEDGER_GLOBS' tools/adoption_apply/apply.py` — 0 (confirmed)
- `test ! -f tools/adoption_apply/tests/test_docs_binding_proposal.py` — FOUND: gone (confirmed via `test` exit 0)
- `uv run python -c "import tools.adoption_apply.apply"` — exits 0 (confirmed)
- `uv run pytest tools/adoption_apply -q` — 100 passed (confirmed)
- `uv run pytest --collect-only -q` — 1356 tests collected, 2 pre-existing errors (unrelated to this plan, per Plan 01's documented deviation)
- Commit `04c411d` — FOUND in `git log --oneline`
- Commit `2cc5ef1` — FOUND in `git log --oneline`
- `git diff --stat 04c411d~1..2cc5ef1` reports **717 total deletions / 6 insertions** across both commits (D-17 measured, not estimated)

---
*Phase: 41-docs-review-plane-removal*
*Completed: 2026-07-27*
