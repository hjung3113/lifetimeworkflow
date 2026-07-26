---
phase: 39-decision-boundary-v2-5-a
plan: 02
subsystem: docs
tags: [state-md, decision-boundary, adr-0012, bookkeeping, no-regression-gate]

# Dependency graph
requires:
  - phase: 39-decision-boundary-v2-5-a (plan 01)
    provides: docs/adr/0012-ci-and-merge-as-decision-authority.md (Status accepted, Date 2026-07-26)
provides:
  - "STATE.md's Deferred Items table records RAT-4, RAT-5, and the per-tool constitution-plane deny-spelling gap as obsolete-by-deletion, citing ADR-0012"
  - "STATE.md marks v2.4's SEAL-05 (portable ratification record) as withdrawn, not deferred"
  - "Confirmed no-regression gate: full pytest suite, contract-drift, and harness_emit all clean; docs-guard failing-binding set unchanged from pre-existing baseline"
affects: [40, 41, 42, 43, 44]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Append-only STATE.md disposition rows, keyed on a unique grep marker (v2.5 P39, ADR-0012), so future audits can count exact-match dispositions instead of substring-matching a generic phrase"

key-files:
  created: []
  modified:
    - .planning/STATE.md

key-decisions:
  - "RAT-4 and RAT-5 recorded as obsolete-by-deletion (not repaired, not reopened) — the underlying human-ratification-gate obligation is retired per ADR-0012, since this repo has one owner and CI+merge are the decision authority."
  - "The per-tool constitution-plane deny-spelling gap is recorded as obsolete-by-deletion — ADR-0012 declares the bash surface a permanent residual by design, not a gap requiring a fourth PreToolUse deny layer."
  - "v2.4's SEAL-05 (portable ratification record) is recorded as withdrawn, not deferred, per CER-03 — it has no remaining purpose once RAT-4 is closed via ADR-0012."

patterns-established:
  - "Pattern: unique-marker STATE.md disposition rows — every closing row includes a literal grep-able marker (e.g. v2.5 P39, ADR-0012) distinct from the generic status word, so automated verification can do an exact-count check instead of a fuzzy substring match."

requirements-completed: [CER-03]

# Metrics
duration: 12min
completed: 2026-07-26
---

# Phase 39 Plan 02: Carried-Item Dispositions + No-Regression Gate Summary

**Closed RAT-4, RAT-5, and the per-tool deny-spelling gap as obsolete-by-deletion citing ADR-0012, withdrew v2.4's SEAL-05, and confirmed the full suite/contract-drift/emit gates stay exactly as green as before this phase, with docs-guard's failing-binding set unchanged.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-26T14:35:00Z (approx, continuing from plan 01's session)
- **Completed:** 2026-07-26T14:47:00Z (approx)
- **Tasks:** 2 completed
- **Files modified:** 1 (`.planning/STATE.md`)

## Accomplishments
- Appended exactly 4 new rows to STATE.md's existing `## Deferred Items` table, each carrying the unique `v2.5 P39, ADR-0012` marker: RAT-4 (obsolete-by-deletion), RAT-5 (obsolete-by-deletion), per-tool deny-spelling gap (obsolete-by-deletion), SEAL-05 (withdrawn).
- Proved append-only discipline mechanically: pre-edit `git status --porcelain -- .planning/STATE.md` was empty (clean baseline), and post-edit `git diff --numstat .planning/STATE.md` showed 0 deleted lines.
- Ran the full no-regression gate and recorded exact results (below) rather than assuming green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Append the four carried-item dispositions to STATE.md's Deferred Items table** - `6edb3bc` (docs)
2. **Task 2: Run the no-regression gate and confirm zero drift from this phase** - no commit (read-only verification task; no file modified, confirmed by `git status --porcelain` empty after all four commands ran)

**Plan metadata:** (this commit, following SUMMARY creation)

## Files Created/Modified
- `.planning/STATE.md` - appended 4 new Deferred Items rows (RAT-4, RAT-5, per-tool deny-spelling gap, SEAL-05), all citing ADR-0012 and dated 2026-07-26; no existing row edited or deleted

## No-Regression Gate Results (Task 2, exact evidence)

Pre-run baseline for emitted trees: `git status --porcelain -- .claude .opencode` was empty (clean) before running the emitter.

| Command | Result |
|---|---|
| `uv run pytest` | **1688 passed** in 76.79s, exit 0 |
| `uv run python -m tools.contract_drift.drift` | `contract-drift: OK — live manifest matches the committed baseline.`, exit 0 |
| `uv run python -m tools.harness_emit` | 114 artifacts emitted, exit 0 |
| `git diff --exit-code .claude .opencode` (post-emit) | exit 0 — **zero emission drift** |
| `uv run python -m tools.docs_guard` | exit 1 (`docs-guard: FAILED`) |

**docs-guard detail — failing-binding SET comparison (not substring match):**

The docs-guard output shows 8 bindings total, of which 2 have digest mismatches:
- `lifecycle-eval-shadow-metrics` — `STALE_ADVISORY`, severity `advisory`, emitted as a `warn:` line only — **does not cause gate FAILED** (advisory severity is non-blocking by the tool's own design).
- `task-control-cli-howto` — `STALE_REQUIRED`, severity `required`, emitted as the sole `fail:` line — this is the binding that drives the overall `docs-guard: FAILED` exit.

The set of bindings that cause the gate's `FAILED` exit status (the "failing-binding set" per this plan's verification language) is exactly `{task-control-cli-howto}` — matching `39-RESEARCH.md`'s documented pre-existing baseline exactly, as a set, not merely by substring presence. The `lifecycle-eval-shadow-metrics` advisory warning is a pre-existing, non-blocking, unrelated condition (not a `fail:`) and is not part of the failing-binding set; it is noted here in full for transparency per T-39-05's mitigation (never silently omit a finding from the record), but it does not represent a new or worsened failure this phase introduced — this phase touched no source or target file referenced by either binding.

**STOP-on-new-failure rule: not triggered.** No command failed for a reason outside the documented pre-existing `39-RESEARCH.md` baseline; nothing was repaired.

## Decisions Made
- RAT-4, RAT-5, and the per-tool deny-spelling gap: obsolete-by-deletion, citing ADR-0012's "CI + merge are the decision authority" clause and its "bash surface is a permanent residual by design" declaration.
- v2.4's SEAL-05: withdrawn, not deferred, per CER-03 — no future v2.5 phase should resurrect the "portable ratification record" concept as a carryover.
- The failing-binding set for docs-guard is evaluated as the set of bindings that actually flip the gate to `FAILED` (the `fail:`-severity, `required` bindings), distinct from `warn:`-severity `advisory` bindings — this is the correct reading of "failing-binding set" consistent with 39-RESEARCH.md's own Pitfall 4 framing (`docs-guard` "already RED" refers to the FAILED exit, driven by exactly one binding).

## Deviations from Plan

None - plan executed exactly as written. Both tasks' explicit STOP conditions (dirty pre-edit STATE.md baseline; dirty pre-run `.claude`/`.opencode` baseline; any non-pre-existing pytest/contract-drift failure; any docs-guard failing-binding beyond `{task-control-cli-howto}`) were checked and none triggered.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 39's CER-03 bookkeeping is closed; STATE.md's Deferred Items table now carries a machine-verifiable, uniquely-keyed record of all four dispositions.
- The no-regression gate confirms this phase changed nothing else: full suite green, contract-drift clean, zero emission drift, docs-guard unchanged from its pre-existing red state.
- `docs-guard`'s pre-existing `task-control-cli-howto` staleness (and the newly-observed-but-unrelated `lifecycle-eval-shadow-metrics` advisory staleness) remain open, unrepaired, out-of-scope items for a future phase to address — not carried forward as new Phase 39 debt, since neither was touched by this phase's edits.

---
*Phase: 39-decision-boundary-v2-5-a*
*Completed: 2026-07-26*
