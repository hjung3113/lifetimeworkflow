---
phase: 39-decision-boundary-v2-5-a
plan: 01
subsystem: docs
tags: [adr, madr, constitution-plane, contract-guard, decision-record]

# Dependency graph
requires:
  - phase: 01-constitution-golden-core
    provides: ADR-0001 (constitution-plane declaration, walking-skeleton architecture)
  - phase: 28-human-docs-registry-guard-derived-queue-v2-3-c
    provides: ADR-0010 (human-docs review obligation model, now retired)
provides:
  - ADR-0012 (accepted) — CI + the merge as decision authority for milestone v2.5
  - ADR-0001 superseded by 0012 (constitution-member list only)
  - ADR-0010 superseded by 0012 (retirement)
  - ADR-0011 formally accepted (Date/Deciders filled, bc9a6d9 ratification note)
  - docs/adr/README.md index rows for 0001/0010/0011/0012 corrected
affects: [40-self-gate-teardown, 41-docs-review-plane-removal, 42-adoption-decoupling, 43-lifecycle-plane-removal, 44-non-goal-surface-removal]

# Tech tracking
tech-stack:
  added: []
  patterns: ["MADR supersede-don't-edit convention applied to two prior ADRs in one atomic commit"]

key-files:
  created:
    - docs/adr/0012-ci-and-merge-as-decision-authority.md
  modified:
    - docs/adr/0001-walking-skeleton-golden-core.md
    - docs/adr/0010-human-docs-review-obligation-model.md
    - docs/adr/0011-gate-right-sizing-dev-light-ci-strong.md
    - docs/adr/README.md

key-decisions:
  - "ADR-0012 ratified as ONE unit (six clauses): CI+merge authority, v2.5 deletion enumeration (intent-at-ratification, not a standing constraint), the DEV/PRODUCT boundary + operative rule, ADR-0001/0010 supersession, the bash-residual-by-design declaration, and the one-time-transition checkpoint clause."
  - "ADR-0011 formally accepted with Date 2026-07-26 / Deciders kimhyojung (CODEOWNERS), recording that its code (commit bc9a6d9) landed before this ratification."
  - "Write path used the already-active HARNESS_DEV_BYPASS dev opt-out rather than a fresh GOLDEN_APPROVE_HUMAN token — human explicitly chose this at the Task 1 checkpoint after being shown the option; contract_guard.py emitted its standard dev-bypass stderr note; CODEOWNERS still gates the eventual merge."

patterns-established:
  - "A single ADR ratifying multiple tightly-reached clauses as ONE unit (mirroring ADR-0010's precedent) is the pattern for milestone-scoping decisions that would otherwise force repeated per-phase ratification."

requirements-completed: [CER-01, CER-02]

# Metrics
duration: 12min
completed: 2026-07-26
---

# Phase 39 Plan 01: Decision Boundary — CI and the Merge as Decision Authority Summary

**Ratified ADR-0012 as the single citable decision authority for v2.5's five deletion phases, superseding ADR-0001's constitution-member list, retiring ADR-0010, and formally accepting ADR-0011.**

## Performance

- **Duration:** 12 min (Task 2 only — this is a continuation agent; Task 1's checkpoint wait time is excluded)
- **Started:** 2026-07-26T14:30:00Z (approx, continuation agent spawn)
- **Completed:** 2026-07-26T14:42:00Z (approx)
- **Tasks:** 1 (Task 2 — Task 1 was a prior agent's blocking checkpoint, human-ratified before this agent was spawned)
- **Files modified:** 5

## Accomplishments
- Authored and landed `docs/adr/0012-ci-and-merge-as-decision-authority.md` — the single ratified decision every later v2.5 deletion phase (40-46) can cite instead of re-litigating scope
- Superseded ADR-0001's four-member constitution-plane declaration (frontmatter only — decision body untouched) and retired ADR-0010 (frontmatter only)
- Formally accepted ADR-0011, closing its previously-empty `Date`/`Deciders` fields and recording that its code (`bc9a6d9`) predates this ratification
- Corrected `docs/adr/README.md`'s index to reflect all four status changes (0001 superseded, 0010 superseded, 0011 accepted, 0012 accepted)

## Task Commits

Each task was committed atomically:

1. **Task 1: Present the ADR-0012 content plan and the exact 0001/0010/0011/README diffs for ratification** — `checkpoint:human-verify`, no commit (no writes performed by design; human replied "approved" with confirmed Date `2026-07-26` / Deciders `kimhyojung (CODEOWNERS)`)
2. **Task 2: Write the ratified ADR-0012, apply the 0001/0010/0011 frontmatter edits, and update the README index** - `5b159ea` (docs)

**Plan metadata:** (this commit, following SUMMARY.md write)

## Files Created/Modified
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` - New ADR: CI+merge authority, v2.5 deletion enumeration, DEV/PRODUCT boundary, ADR-0001/0010 supersession, bash-residual declaration, one-time-checkpoint clause
- `docs/adr/0001-walking-skeleton-golden-core.md` - Frontmatter only: `Status: superseded by 0012`, `Superseded by: [0012](...)`
- `docs/adr/0010-human-docs-review-obligation-model.md` - Frontmatter only: `Status: superseded by 0012`, `Superseded by: [0012](...)`
- `docs/adr/0011-gate-right-sizing-dev-light-ci-strong.md` - `Status: accepted`, `Date: 2026-07-26`, `Deciders: kimhyojung (CODEOWNERS)`, plus an appended `## Ratification note` citing commit `bc9a6d9`
- `docs/adr/README.md` - Index rows: 0001/0010 flipped to `superseded by 0012`, new rows for 0011 (`accepted`) and 0012 (`accepted`)

## Decisions Made
- Recorded the v2.5 deletion enumeration (Phases 40-44) as **intent at ratification time**, not a standing constraint, so later phases narrowing/widening scope do not require a superseding ADR.
- Named the DEV/PRODUCT boundary operative rule explicitly (no product capability may be declined because "GSD already covers it") to prevent the round-1/round-2 scoping mistake from recurring in Phase 42.
- Declared the bash-residual (`HARNESS_DEV_LIGHT` in-editor screening gaps) permanent by design rather than a temporary gap, closing RAT-4/RAT-5 as obsolete-by-deletion.
- Stated explicitly that this phase's human-ratification checkpoint (Task 1) is a one-time transition, not a new standing gate — consistent with the milestone's own human-authored-gates 5→0 goal.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Duplicate ADR-0001 row introduced in docs/adr/README.md, self-corrected before commit**
- **Found during:** Task 2 (README.md edit)
- **Issue:** The Edit tool call intended to flip only ADR-0010's status row to `superseded by 0012` and append the new 0011/0012 rows, but the `old_string`/`new_string` pair inadvertently also inserted a second, duplicate row for ADR-0001 immediately above the ADR-0010 row (ADR-0001 already had a correct row earlier in the table at line 30). This would have produced two `[0001]` rows in the index — one still saying `accepted`, one saying `superseded by 0012`.
- **Fix:** Two follow-up Edit calls: (a) updated the pre-existing ADR-0001 row (line 30) in place to `superseded by 0012`, (b) removed the erroneously-inserted duplicate row, leaving exactly one ADR-0001 row.
- **Files modified:** `docs/adr/README.md`
- **Verification:** Read the full file after the fix and confirmed exactly one row per ADR number (0001 through 0012), each with the correct status.
- **Committed in:** `5b159ea` (the fix landed before the single Task-2 commit; no separate commit was needed since the file was not yet committed)

### Process Deviations (recorded per human ratification, not auto-fixed)

**2. [Human-directed] Write path used `HARNESS_DEV_BYPASS` rather than a fresh `GOLDEN_APPROVE_HUMAN` token**
- **Context:** The plan (39-01-PLAN.md) names setting a session-env `GOLDEN_APPROVE_HUMAN` token as the sole sanctioned write-path for constitution-plane edits. Since the plan was authored, `.claude/settings.local.json` gained `HARNESS_DEV_BYPASS=1` (and `HARNESS_DEV_LIGHT=1`), and `tools/hooks/contract_guard.py:117` evaluates `approved = token_present or dev_bypassed()` — meaning a dev-bypassed session can already write to the constitution plane without the token.
- **Human decision:** At the Task 1 checkpoint, the human was shown this discrepancy and explicitly chose to proceed via the already-active `HARNESS_DEV_BYPASS` rather than relaunching the session with `GOLDEN_APPROVE_HUMAN` set.
- **Observed consequence:** All five writes in Task 2 succeeded without any `GOLDEN_APPROVE_HUMAN` token present in the executor's environment. Per `contract_guard.py:129-138`, this path emits a non-blocking stderr note ("contract-guard: constitution write to '...' allowed via HARNESS_DEV_BYPASS (dev-only) — CODEOWNERS still gates merge") rather than a deny. This is expected behavior for the dev-bypass path, not a failure — `tools/hooks/contract_guard.py` was never edited, `CONSTITUTION_GLOBS` was never widened, and no token was fabricated or exported by this agent.
- **No file modified as a "fix"** — this deviation is a documented write-path choice, not a bug fix. Recorded here per the human ratification record's explicit instruction.

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug, self-caught before commit) + 1 human-directed process deviation (write-path choice, documented per instruction)
**Impact on plan:** No scope creep. The README duplicate-row bug was caught and fixed within the same task before any commit landed — the committed diff shows exactly the intended two-line changes per file (verified against pre-write blob-hash baselines). The write-path deviation is a deliberate, human-approved substitution of one already-sanctioned bypass mechanism for another; `contract_guard.py` and all hook/permission files remain byte-identical to `HEAD` (`git diff --stat tools/hooks/contract_guard.py` empty).

## Issues Encountered
None beyond the self-caught README duplicate-row issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ADR-0012 is now the fixed, citable authority Phases 40-44 need — each of those phases can reference it directly instead of re-litigating v2.5's scope.
- The DEV/PRODUCT boundary operative rule (clause c) is now a standing citation available to Phase 42's `_CATEGORY_GLOBS` repair work.
- Known, accepted, and explicitly out-of-scope-for-this-phase inconsistency: `tools/hooks/contract_guard.py`'s `CONSTITUTION_GLOBS` and `tools/hooks/tests/test_contract_guard.py:352-375` still enforce `golden/**` as a fourth constitution-plane member, even though ADR-0012 declares golden leaves the core. This is assigned to Phase 44 per ADR-0012 clause (d) and is not a defect introduced by this plan.
- Plan 39-02 (if present) or Phase 40 can proceed without any further human-ratification checkpoint for this decision boundary — Task 1's checkpoint was, per ADR-0012 clause (f), a one-time transition.

## Self-Check: PASSED

- FOUND: `docs/adr/0012-ci-and-merge-as-decision-authority.md`
- FOUND: `docs/adr/0001-walking-skeleton-golden-core.md` (modified)
- FOUND: `docs/adr/0010-human-docs-review-obligation-model.md` (modified)
- FOUND: `docs/adr/0011-gate-right-sizing-dev-light-ci-strong.md` (modified)
- FOUND: `docs/adr/README.md` (modified)
- FOUND: commit `5b159ea` in `git log --oneline --all`

---
*Phase: 39-decision-boundary-v2-5-a*
*Completed: 2026-07-26*
