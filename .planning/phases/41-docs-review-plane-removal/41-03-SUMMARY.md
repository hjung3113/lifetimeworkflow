---
phase: 41-docs-review-plane-removal
plan: 03
subsystem: infra
tags: [docs-review-plane, deletion, ADR-0012, CER-05, emit-manifest, harness_emit, memory_regen]

# Dependency graph
requires:
  - phase: 41-docs-review-plane-removal
    plan: "41-02"
    provides: tools/hooks/ledger_guard.py + harness/plugins/ledger-guard.ts deleted,
      tools/harness_emit/merge.py's HARNESS_SIGNATURES entry removed (the source-side half of the
      ledger_guard removal this plan's re-emit had to actually propagate)
provides:
  - harness/commands/docs-update.md and harness/skills/docs-upkeep/ deleted at source; re-emit
    propagated the deletion into .opencode/command, .opencode/skill, .opencode/plugin
    (ledger-guard.ts), .claude/commands, .claude/skills, and repaired AGENTS.md's managed index
  - tools/harness_emit/emit-manifest.json auto-pruned of its five now-orphaned rows by the
    emitter itself (never hand-edited)
  - tools/harness_emit/merge.py gained a RETIRED_SIGNATURES mechanism so a formerly harness-owned
    settings.json hook group is actually dropped on re-emit instead of silently kept forever
  - tools/harness_lint/caps.py's EXPECTED_SKILLS no longer lists "docs-upkeep"
  - tools/memory_regen/docs_staleness.py (233 LOC), its two dependent test files, and the orphaned
    test_docs_staleness.ambr snapshot deleted; inject.py's assemble() no longer carries the
    ("docs", ...) row or _docs_staleness_pointer/DOCS_HEADER
  - harness/commands/refresh-memory.md (+ both emitted copies) no longer invokes the deleted
    tools.memory_regen.docs_staleness module
affects: [41-04, 41-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [pathspec-scoped commits (D-11), source-first emitter edits (D-12),
    deletion-only phase with no replacement (D-06), retired-signature drop in a
    signature-matched settings.json merge (new pattern, this plan)]

key-files:
  created: []
  modified:
    - harness/commands/docs-update.md (deleted)
    - harness/skills/docs-upkeep/SKILL.md (deleted)
    - tools/harness_emit/emit-manifest.json (5 rows auto-pruned by the emitter)
    - .opencode/command/docs-update.md, .opencode/skill/docs-upkeep/SKILL.md,
      .opencode/plugin/ledger-guard.ts (deleted, emitter output)
    - .claude/commands/docs-update.md, .claude/skills/docs-upkeep/SKILL.md (deleted, emitter output)
    - .claude/settings.json (ledger_guard PreToolUse group dropped, emitter output)
    - AGENTS.md (managed command/skill index repaired, emitter output)
    - tools/harness_emit/merge.py (RETIRED_SIGNATURES + drop branch added — Rule 1 fix)
    - tools/harness_lint/caps.py (docs-upkeep removed from EXPECTED_SKILLS — Rule 3 fix)
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr (regenerated)
    - tools/memory_regen/docs_staleness.py (deleted, 233 LOC)
    - tools/memory_regen/tests/test_docs_staleness.py (deleted, 273 lines)
    - tools/memory_regen/tests/test_inject_docs_pointer.py (deleted, 186 lines)
    - tools/memory_regen/tests/__snapshots__/test_docs_staleness.ambr (deleted, orphaned)
    - tools/memory_regen/inject.py (_docs_staleness_pointer, DOCS_HEADER, and the assemble() row removed)
    - harness/commands/refresh-memory.md + .opencode/command/refresh-memory.md +
      .claude/commands/refresh-memory.md (stranded docs_staleness invocation/prose removed — Rule 1 fix)

key-decisions:
  - "Fixed tools/harness_lint/caps.py's EXPECTED_SKILLS frozenset (removed \"docs-upkeep\") as a
    Rule 3 auto-fix: the emitter's check_skill_set anti-drift assertion hard-failed BEFORE any
    file was written, the moment harness/skills/docs-upkeep/ was deleted — the re-emit could not
    even start without this one-line fix. Left the surrounding Phase-history comment block
    untouched (cosmetic prose sweep, Plan 05's job per phase-critical rule 6)."
  - "Added tools/harness_emit/merge.py's RETIRED_SIGNATURES mechanism as a Rule 1 bug fix: Plan
    02 removed \"tools.hooks.ledger_guard\" from HARNESS_SIGNATURES, but merge_settings's existing
    logic classifies a group matching NO current signature as sig=None, the exact same bucket as
    a GSD/human group — so the live ledger_guard PreToolUse group would have been preserved
    verbatim forever instead of removed, contradicting the plan's own must_haves.truths claim that
    re-emit alone removes it. A group whose command matches a RETIRED_SIGNATURES entry is now
    dropped explicitly. Verified: re-running the emitter after the fix produces a
    .claude/settings.json with zero ledger_guard occurrences, and a second re-emit is byte-identical
    (idempotent)."
  - "Fixed harness/commands/refresh-memory.md as a Rule 1 bug fix (found while verifying the
    docs_staleness deletion, not in the plan's files_modified list): its step 1 invoked
    `uv run python -m tools.memory_regen.docs_staleness`, a module Task 2 deletes, and described
    the docs-staleness queue in prose. Removed both; re-emitted so the two projected copies
    (.opencode/command/, .claude/commands/) pick up the fix; updated the emit-determinism snapshot
    to match."
  - "Regenerated tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr via
    `pytest --snapshot-update` as an in-scope consequence of this plan's own source deletion
    (not a deferred prose-sweep item) — the snapshot pins the exact emitted content of every
    command/skill/config and would otherwise assert a stale, pre-deletion tree forever."
  - "Deleted the now-orphaned tools/memory_regen/tests/__snapshots__/test_docs_staleness.ambr
    snapshot file alongside its deleted test — syrupy flagged it as 'unused' after
    test_docs_staleness.py was removed."
  - "Left tools/harness_emit/tests/test_coexist.py, tools/harness_lint/tests/test_docs_update_wiring.py,
    and tools/hooks/tests/test_settings_coexist.py untouched and now expected-red (11 failing tests
    total) — all three are explicitly named in 41-CONTEXT.md's D-13 prose/test sweep and this plan's
    own phase-critical rule 6 as Plan 05's job, not this plan's."
  - "Left the pre-existing unrelated .planning/config.json modification untouched, and the
    REQUIREMENTS.md CER-05 [x]-vs-\"Not started\" drift (line 49 vs line 183) untouched, per
    phase-critical rules 8 and 9."

requirements-completed: [CER-05]

# Metrics
duration: ~40min
completed: 2026-07-27
---

# Phase 41 Plan 03: Docs-Update Command/Skill Deletion + Staleness-Queue Removal Summary

**Deleted `harness/commands/docs-update.md` and `harness/skills/docs-upkeep/` at source and re-emitted both runtime trees, discovering and fixing two blocking emitter-mechanism gaps (`EXPECTED_SKILLS` drift and a settings.json merge that could never actually remove a retired hook group) plus one stranded `refresh-memory.md` invocation along the way, then deleted the derived `docs_staleness` queue and its `inject.py` pointer row — 1,517 total lines removed across three pathspec-scoped commits, with `uv run pytest --collect-only -q` now exiting 0 with zero errors for the first time since Plan 01.**

## Performance

- **Duration:** ~40 min
- **Tasks:** 2 completed (plus in-scope discovered fixes)
- **Files modified:** 21 (10 deleted outright, 11 edited — 4 of them emitter output)

## Accomplishments

- Deleted `harness/commands/docs-update.md` and `harness/skills/docs-upkeep/SKILL.md` at source, then ran `uv run python -m tools.harness_emit` to propagate the deletion into `.opencode/command/`, `.opencode/skill/`, `.opencode/plugin/ledger-guard.ts`, `.claude/commands/`, `.claude/skills/`, `tools/harness_emit/emit-manifest.json` (five rows auto-pruned), and `AGENTS.md`'s managed command/skill index — never a hand-edit of any emitted file.
- Found and fixed two blocking emitter-mechanism gaps that would have silently defeated the deletion:
  1. `tools/harness_lint/caps.py`'s `EXPECTED_SKILLS` anti-drift frozenset still listed `"docs-upkeep"`, hard-failing the emitter's `check_skill_set` check before any file was written — one-line removal.
  2. `tools/harness_emit/merge.py`'s signature-matched settings.json merge had no path to actually **remove** a formerly harness-owned hook group: Plan 02 removed `"tools.hooks.ledger_guard"` from `HARNESS_SIGNATURES`, but the merge then classified the live group as `sig=None` — indistinguishable from a GSD/human group — and would have preserved it verbatim forever. Added a `RETIRED_SIGNATURES` tuple + a drop branch so a retired signature's group is recognized and removed on re-emit.
- Confirmed emit-drift idempotency: re-running `uv run python -m tools.harness_emit` a second time produces an empty diff, and `.claude/settings.json` has zero `ledger_guard` occurrences.
- Deleted `tools/memory_regen/docs_staleness.py` (233 LOC, already import-broken since Plan 01), `test_docs_staleness.py` (273 lines), `test_inject_docs_pointer.py` (186 lines), and the now-orphaned `test_docs_staleness.ambr` snapshot; removed `_docs_staleness_pointer`, `DOCS_HEADER`, and the `("docs", ...)` row from `inject.py`'s `assemble()`, leaving `contracts` directly followed by `repomap`.
- Found and fixed a stranded reference while verifying the staleness-queue deletion: `harness/commands/refresh-memory.md` still invoked `uv run python -m tools.memory_regen.docs_staleness` (now deleted) and described the queue in prose. Fixed at source and re-emitted so both projected copies pick up the repair.
- Regenerated `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` twice (once after Task 1's deletion, once after the `refresh-memory.md` fix) so the committed snapshot matches the emitted tree exactly.
- `uv run pytest --collect-only -q` now exits 0 with **1347 tests collected, zero errors** — the two `ModuleNotFoundError: tools.docs_guard` collection failures carried since Plan 01 are gone.
- `uv run pytest -q`: **1336 passed, 11 expected-red** — all 11 in `tools/harness_emit/tests/test_coexist.py`, `tools/harness_lint/tests/test_docs_update_wiring.py`, and `tools/hooks/tests/test_settings_coexist.py`, every one named in CONTEXT.md's D-13 prose/test sweep and this plan's own phase-critical rule 6 as Plan 05's job.

## Task Commits

Each task was committed atomically (plus one in-scope snapshot-update commit and a discovered-fix commit folded into Task 2's commit):

1. **Task 1: Delete the runtime surface at source and re-emit both trees** - `56d2d4c` (feat)
2. **Snapshot regeneration for Task 1's deletion** - `cf0f80d` (test)
3. **Task 2: Delete the derived staleness queue (+ the stranded refresh-memory.md fix)** - `29616be` (feat)

_No plan-metadata commit separate from these three — this summary/STATE/ROADMAP update is the final commit for this plan._

## Files Created/Modified

- `harness/commands/docs-update.md` - deleted
- `harness/skills/docs-upkeep/SKILL.md` - deleted
- `tools/harness_emit/emit-manifest.json` - 5 rows auto-pruned by the emitter (never hand-edited)
- `.opencode/command/docs-update.md`, `.opencode/skill/docs-upkeep/SKILL.md`, `.opencode/plugin/ledger-guard.ts` - deleted (emitter output)
- `.claude/commands/docs-update.md`, `.claude/skills/docs-upkeep/SKILL.md` - deleted (emitter output)
- `.claude/settings.json` - `ledger_guard` PreToolUse group dropped (emitter output, after the merge.py fix)
- `AGENTS.md` - managed command/skill index repaired (emitter output)
- `tools/harness_emit/merge.py` - added `RETIRED_SIGNATURES` + a drop branch in `merge_settings` (Rule 1 fix)
- `tools/harness_lint/caps.py` - removed `"docs-upkeep"` from `EXPECTED_SKILLS` (Rule 3 fix)
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` - regenerated
- `tools/memory_regen/docs_staleness.py` - deleted (233 LOC)
- `tools/memory_regen/tests/test_docs_staleness.py` - deleted (273 lines)
- `tools/memory_regen/tests/test_inject_docs_pointer.py` - deleted (186 lines)
- `tools/memory_regen/tests/__snapshots__/test_docs_staleness.ambr` - deleted (orphaned)
- `tools/memory_regen/inject.py` - `_docs_staleness_pointer`, `DOCS_HEADER`, and the `("docs", ...)` assemble() row removed
- `harness/commands/refresh-memory.md`, `.opencode/command/refresh-memory.md`, `.claude/commands/refresh-memory.md` - stranded `docs_staleness` invocation + prose removed (Rule 1 fix)

## Decisions Made

See `key-decisions` in frontmatter — six decisions, all documented there with rationale.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `tools/harness_lint/caps.py`'s `EXPECTED_SKILLS` still listed `docs-upkeep`**
- **Found during:** Task 1, first `uv run python -m tools.harness_emit` run after deleting the skill source
- **Issue:** `generate.py`'s `emit()` calls `validate.check_skill_set()` against the hand-maintained `EXPECTED_SKILLS` anti-drift frozenset; with `docs-upkeep`'s source deleted but still listed as expected, the emitter raised `HarnessEmitError: skill set drift — missing ['docs-upkeep'], unexpected []` before writing a single file
- **Fix:** Removed `"docs-upkeep"` from the frozenset (one line); left the surrounding phase-history comment block for Plan 05
- **Files modified:** `tools/harness_lint/caps.py`
- **Commit:** `56d2d4c`

**2. [Rule 1 - Bug] `tools/harness_emit/merge.py` could not actually remove a retired hook group**
- **Found during:** Task 1, verifying the plan's `must_haves.truths` claim that re-emit removes the `ledger_guard` PreToolUse group
- **Issue:** Plan 02 removed `"tools.hooks.ledger_guard"` from `HARNESS_SIGNATURES`; `merge_settings` then classified the live group as `sig=None` (no signature match), the same bucket used for GSD/human groups — so it was preserved verbatim on every re-emit instead of removed. A pure signature-set diff is structurally incapable of expressing "delete this"
- **Fix:** Added `RETIRED_SIGNATURES: tuple[str, ...] = ("tools.hooks.ledger_guard",)` and a drop branch in `merge_settings`'s existing-group loop: a group matching a retired signature is dropped instead of kept
- **Files modified:** `tools/harness_emit/merge.py`
- **Commit:** `56d2d4c`
- **Verification:** re-running the emitter twice confirmed `.claude/settings.json` has zero `ledger_guard` occurrences and the second run is byte-identical (idempotent)

**3. [Rule 1 - Bug] `harness/commands/refresh-memory.md` invoked the module Task 2 deletes**
- **Found during:** Task 2, `grep -rl docs_staleness` sweep before finalizing the deletion
- **Issue:** `refresh-memory.md`'s step 1 shell block ran `uv run python -m tools.memory_regen.repo_map && ... && uv run python -m tools.memory_regen.docs_staleness` and its prose described the queue — both would break `/refresh-memory` the instant `docs_staleness.py` was deleted
- **Fix:** Removed the `docs_staleness` invocation from the shell block and the prose paragraph describing the queue; re-emitted so `.opencode/command/refresh-memory.md` and `.claude/commands/refresh-memory.md` pick up the fix
- **Files modified:** `harness/commands/refresh-memory.md`, `.opencode/command/refresh-memory.md`, `.claude/commands/refresh-memory.md`
- **Commit:** `29616be`

## Issues Encountered

None beyond the three Rule 1/3 fixes above, all resolved inline before their respective task commits. The 11 expected-red tests (`test_coexist.py` ×2, `test_docs_update_wiring.py` ×7, `test_settings_coexist.py` ×2) are the anticipated consequence of this plan's own deletion and are explicitly named in CONTEXT.md's D-13 and this plan's phase-critical rule 6 as out of scope — Plan 05's prose/test sweep.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 04 can proceed with `contracts/**` and `.github/workflows/ci.yml` deletion. Plan 05 owns the prose/test sweep left red here: `AGENTS.md` (already partially repaired by this plan's re-emit — only the harness-managed block, no further edit needed there), `harness/skills/gate-model/SKILL.md`'s docs-plane claims, `.memory/README.md`'s "third path-deny domain" sentence, and the wiring tests (`test_docs_update_wiring.py`, `test_settings_coexist.py`, `test_coexist.py`) plus `uv.lock`. No blockers.

## Self-Check: PASSED

- `test ! -f harness/commands/docs-update.md` — FOUND: gone (confirmed via `test` exit 0)
- `test ! -d harness/skills/docs-upkeep` — FOUND: gone (confirmed via `test` exit 0)
- `grep -c 'docs-update\|docs-upkeep' tools/harness_emit/emit-manifest.json` — 0 (confirmed)
- `find .opencode .claude -iname '*docs-update*' -o -iname '*docs-upkeep*'` — only unrelated GSD-vendored files (`.claude/commands/gsd/docs-update.md`, `.claude/get-shit-done/workflows/docs-update.md`), out of this plan's scope
- `grep -c 'ledger_guard' .claude/settings.json` — 0 (confirmed)
- `test ! -f tools/memory_regen/docs_staleness.py` — FOUND: gone (confirmed via `test` exit 0)
- `grep -c '_docs_staleness_pointer\|docs_staleness' tools/memory_regen/inject.py` — 0 (confirmed)
- `uv run pytest --collect-only -q` — 1347 tests collected, 0 errors (confirmed)
- `uv run pytest -q` — 1336 passed, 11 expected-red (confirmed, all D-13-deferred)
- `uv run python -m tools.harness_emit` re-run twice — idempotent, empty diff (confirmed via `git status --porcelain`)
- Commit `56d2d4c` — FOUND in `git log --oneline`
- Commit `cf0f80d` — FOUND in `git log --oneline`
- Commit `29616be` — FOUND in `git log --oneline`
- `git diff --stat 56d2d4c~1..29616be` reports **21 files changed, 28 insertions(+), 1517 deletions(-)** across all three commits (D-17 measured, not estimated)

---
*Phase: 41-docs-review-plane-removal*
*Completed: 2026-07-27*
