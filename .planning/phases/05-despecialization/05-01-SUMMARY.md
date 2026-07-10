---
phase: 05-despecialization
plan: 01
subsystem: infra
tags: [commit-gate, contract-drift, golden-approve, hooks, python, tdd]

# Dependency graph
requires:
  - phase: 04-guardrails
    provides: "commit_gate composition (drift/polyglot/golden) + 04-05 test suite; contract_guard GOLDEN_APPROVE_HUMAN precedent"
provides:
  - "D-05 commit-gate approval path: contract-drift honors GOLDEN_APPROVE_HUMAN (warn+pass) while polyglot/golden stay hard"
  - "Sanctioned landing path for the intended Phase 5 domain-move commits (05-02/03/05)"
affects: [05-02, 05-03, 05-05, despecialization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Human-ratification token mirror: reuse contract_guard's bool((os.environ.get(APPROVAL_ENV) or '').strip()) verbatim"
    - "Scoped bypass: approval confined to a single component; sibling gates provably untouched"

key-files:
  created: []
  modified:
    - tools/hooks/commit_gate.py
    - tools/hooks/tests/test_commit_gate.py

key-decisions:
  - "Bypass is DRIFT-ONLY: _human_approved() is called only inside check_drift; check_polyglot/check_golden untouched (T-05-01)"
  - "Empty/blank token does NOT authorize — mirrors contract_guard Q1 (T-05-02)"
  - "Approved drift returns PASS with a WARN(ratified) detail line so the bypass is still logged (T-05-03)"

patterns-established:
  - "Pattern 1: verbatim token-check mirror across gates keeps 'machines gate, humans ratify' semantics identical"
  - "Pattern 2: a component-scoped approval must be proven non-weakening by a dedicated cross-component test"

requirements-completed: [GEN-01]

# Metrics
duration: 2min
completed: 2026-07-09
---

# Phase 5 Plan 01: Commit-Gate Drift Approval Path Summary

**The commit-gate contract-drift component now honors a human-set GOLDEN_APPROVE_HUMAN token (drift FAIL → logged WARN+PASS) while polyglot §4.3-4.6 and golden equivalence stay hard.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-07-09T03:45:21Z
- **Completed:** 2026-07-09T03:47:25Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments
- Added `APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"` + `_human_approved()` to `commit_gate.py` as a verbatim mirror of the `contract_guard.py:91` precedent (no new flag, no new package).
- `check_drift` turns a drift FAIL into a `PASS` with a `WARN (ratified)` detail line when the token is set; still FAILs when absent/empty/blank.
- Extended the 04-05 suite with four D-05 cases: token→warn/pass, absent→block, empty/blank→block, and token≠weaken-polyglot (proving drift-only scope).
- Full suite stays green: 354 passed, 2 pre-existing dotnet-absent skips.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1: Extend 04-05 suite with four D-05 approval cases (RED)** - `a6f9c6f` (test)
2. **Task 2: Add drift-only approval bypass to check_drift (GREEN)** - `34ed4ec` (feat)

_No REFACTOR commit needed — implementation was minimal and clean at GREEN._

## Files Created/Modified
- `tools/hooks/commit_gate.py` - Added `APPROVAL_ENV`/`_human_approved()`; `check_drift` warn+passes approved drift; module docstring drift bullet updated to note the DRIFT-ONLY bypass.
- `tools/hooks/tests/test_commit_gate.py` - Appended the four D-05 approval cases under a new section; existing tests untouched.

## Decisions Made
- Kept the bypass strictly inside `check_drift`; grep confirms `GOLDEN_APPROVE_HUMAN`/`_human_approved` never appear in `check_polyglot`/`check_golden`.
- WARN message embeds both `GOLDEN_APPROVE_HUMAN` and `ratified` so the audit line is greppable and the drift FAIL string is provably absent from the log on the approved path.

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results
- `uv run pytest tools/hooks/tests/test_commit_gate.py -x -q` → 20 passed (16 pre-existing + 4 new).
- `uv run pytest tools/hooks/tests/test_commit_gate.py tools/hooks/tests/test_contract_guard.py -q` → 34 passed.
- `uv run pytest` (full suite) → **354 passed, 2 skipped** (both skips are the pre-existing dotnet-absent golden end-to-end cases).
- `uv run python -m tools.hooks.commit_gate` on a clean tree → exit 0, golden-parity SKIP logged.
- Grep: `GOLDEN_APPROVE_HUMAN` appears in `commit_gate.py` only within the docstring, `APPROVAL_ENV`, `_human_approved`, and `check_drift`.

## TDD Gate Compliance
RED (`test(05-01)` @ `a6f9c6f`) precedes GREEN (`feat(05-01)` @ `34ed4ec`). Gate sequence satisfied.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The sanctioned D-05 landing path is live: the intended Phase 5 domain-move commits (05-02/03/05) can now be committed through the gate with a human GOLDEN_APPROVE_HUMAN token rather than by bash-bypassing it.
- This commit itself was core-only (`tools/hooks/` only, no contract change) and landed clean with NO token.

## Self-Check: PASSED
- FOUND commit a6f9c6f
- FOUND commit 34ed4ec
- FOUND tools/hooks/commit_gate.py
- FOUND tools/hooks/tests/test_commit_gate.py

---
*Phase: 05-despecialization*
*Completed: 2026-07-09*
