---
phase: 09-self-maintaining-derived-artifacts-curator-v2-0
plan: 04
subsystem: infra
tags: [ci, github-actions, derived-plane, drift-gate, ruamel, git-diff, MAINT-02]

requires:
  - phase: 09-01
    provides: docs/reference reconciled + docs_sync prune-then-write (green committed-derived tree)
  - phase: 09-02
    provides: .memory/derived/contracts-index.md flipped gitignored→tracked (committed-derived)
  - phase: 09-03
    provides: /refresh-memory command (the fix message the gate points at) + curator persona
provides:
  - stale-derived CI job — regenerates the committed-derived set and FAILS on any diff (untracked-safe)
  - stale-derived wired into gate.needs (non-bypassable fan-in)
  - structural + negative-control test proving the gate's presence, diff primitive, wiring, and no-event-injection posture
affects: [phase-10-context-economy, phase-11-multi-repo, ci-maintenance]

tech-stack:
  added: []
  patterns:
    - "Regenerate-then-diff CI gate with git add -A + git diff --cached --exit-code (untracked-safe, P1)"
    - "Distinct freshness gate per derived concern (stale-derived separate from emit-drift, D-07)"

key-files:
  created:
    - tools/harness_lint/tests/test_ci_stale_derived.py
  modified:
    - .github/workflows/ci.yml

key-decisions:
  - "stale-derived is a SEPARATE job from emit-drift (D-07) — committed-derived memory (docs/reference + contracts-index) vs runtime surface (.opencode/.claude) are distinct concerns"
  - "git add -A + git diff --cached --exit-code (NOT bare git diff) so a freshly-created untracked reference page cannot slip the gate (Pitfall P1)"
  - "On-failure message points at /refresh-memory (09-03) plus the literal regen commands (D-08 contributor ergonomics, mirrors emit-drift)"

patterns-established:
  - "Untracked-safe drift gate: stage-then-diff-cached is the correct primitive whenever the derived set can gain new files"
  - "Negative-control test co-locates the gate's core assertion (stale-vs-clean discrimination) with real git plumbing, shell=False"

requirements-completed: [MAINT-02]

duration: 12min
completed: 2026-07-13
---

# Phase 09 Plan 04: Stale-Derived CI Gate Summary

**Non-bypassable `stale-derived` CI job that regenerates docs/reference + .memory/derived/contracts-index.md and fails on any diff via the untracked-safe `git add -A` + `git diff --cached --exit-code` primitive, proven by a structural + negative-control test — completing MAINT-02.**

## Performance

- **Duration:** 12 min
- **Completed:** 2026-07-13
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- Added the `stale-derived` job to `.github/workflows/ci.yml` — a clone of `emit-drift` (checkout@v7.0.0 → setup-uv@v8.3.2 → `uv sync --all-packages`) that regenerates the committed-derived set via `tools.docs_sync` + `tools.memory_regen.contracts_index`, then fails on any diff.
- Applied the one deliberate deviation from `emit-drift`: `git add -A` + `git diff --cached --exit-code` (untracked-safe) instead of bare `git diff`, so a newly-created reference page cannot slip through (Pitfall P1).
- Wired `stale-derived` into `gate.needs` (fan-in, non-bypassable) and kept the least-privilege posture (top-level `permissions: { contents: read }`, no `${{ github.event.* }}` interpolation).
- Added an on-failure message echoing a copy-pasteable fix (`/refresh-memory` or the literal regen + commit commands) — mirrors `emit-drift` contributor ergonomics (D-08).
- Added `tools/harness_lint/tests/test_ci_stale_derived.py` with 8 tests: structural assertions (job exists, correct diff primitive, in `gate.needs`, regen modules present, actionable fix, no event interpolation) + two negative-control tests proving the diff primitive discriminates stale-vs-clean and catches a new untracked page bare `git diff` misses.

## Task Commits

1. **Task 1: Add the stale-derived job + wire it into gate.needs** - `c85fd00` (feat)
2. **Task 2: Structural + negative-control test for the gate** - `4f925b3` (test)

## Files Created/Modified

- `.github/workflows/ci.yml` - Added the `stale-derived` job (regen → `git add -A` → `git diff --cached --exit-code` → fail-on-diff with an actionable fix message) and appended `stale-derived` to `gate.needs`.
- `tools/harness_lint/tests/test_ci_stale_derived.py` - Structural test (ruamel `YAML(typ="safe")` over ci.yml) + negative-control test (real git plumbing, `subprocess` `shell=False`).

## Decisions Made

- Kept `stale-derived` as a distinct job rather than folding into `emit-drift` (D-07): the two cover orthogonal derived concerns (committed-derived memory vs the emitted runtime surface); a single job would blur the failure signal.
- The gate diffs exactly the two committed-derived paths (`docs/reference`, `.memory/derived/contracts-index.md`) — the same set flipped tracked in 09-01/09-02. `repo-map.md` stays session-ephemeral and is intentionally NOT gated.

## Deviations from Plan

None - plan executed exactly as written.

The plan itself specified the one intentional divergence from the `emit-drift` analog (`git add -A` + `git diff --cached --exit-code`); that is a plan requirement, not an executor deviation.

## Issues Encountered

- Ruff flagged three over-length comment lines (E501) in the new test after the formatter pass; shortened the comments. No logic change. Final `ruff check` clean, 8 tests pass.

## User Setup Required

None - no external service configuration required.

Note (unchanged from prior CI plans): true non-bypassability requires a human to enable the `gate` job as a REQUIRED status check in branch protection (D-02, out of scope) — the workflow file cannot grant that itself.

## Next Phase Readiness

- MAINT-02 complete: a stale derived plane cannot merge. The committed-derived tree is green on arrival (verified: regen → `git add -A` → `git diff --cached --exit-code` exits 0 on the current clean tree).
- Full `tools/harness_lint` suite green (211 passed) after the change — no regression.
- Manual-only residual (per VALIDATION): a throwaway PR mutating a committed derived page should red the `stale-derived` job with the fix message — verifiable once the workflow runs on GitHub.

---
*Phase: 09-self-maintaining-derived-artifacts-curator-v2-0*
*Completed: 2026-07-13*
