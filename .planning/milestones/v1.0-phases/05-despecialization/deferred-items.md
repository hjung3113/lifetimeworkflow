# Phase 5 — Deferred Items (out-of-scope discoveries)

## From 05-02 (GEN-02 generic default instance)

### DEF-05-02-1 — commit_gate drift-block tests leak the active ratification token

**STATUS: RESOLVED** — repaired 2026-07-09 by `ccef8b4`; re-verified 2026-07-22 (Phase 35 / DEBT-04). See the closure below.

- **Discovered during:** 05-02 Task 2 full-suite run.
- **Symptom:** With `GOLDEN_APPROVE_HUMAN` set in the process env (the session precondition
  required to author constitution-plane `contracts/sample/**` + `golden/sample/**`), three
  tests in `tools/hooks/tests/test_commit_gate.py` fail:
  `test_drift_present_blocks`, `test_golden_skip_does_not_suppress_drift`,
  `test_from_hook_blocks_commit_on_drift`. They monkeypatch `run_gate` to report drift and
  assert a BLOCK, but do NOT `delenv("GOLDEN_APPROVE_HUMAN")`, so the 05-01 drift-approval
  path (token → warn+pass) turns the expected block into a pass.
- **Proof it is environmental, not a regression from 05-02:**
  `env -u GOLDEN_APPROVE_HUMAN uv run pytest` → full suite **364 passed, 2 skipped** (green).
  The failures appear ONLY when the human token is live in the executing shell; they do not
  occur in CI (which does not export the token).
- **Root cause:** test-isolation gap in a prior-plan (05-01) test file, exposed by the token
  precondition. NOT caused by any 05-02 change.
- **Why deferred:** out of scope per the executor SCOPE BOUNDARY (only auto-fix issues
  DIRECTLY caused by the current task); the file belongs to a concurrent/prior plan
  (orchestrator directive: leave concurrent-phase files untouched).
- **Suggested fix (future):** add `monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)`
  to the three drift-block tests (mirroring `test_drift_present_without_approval_still_blocks`)
  so they are hermetic regardless of the ambient token.

#### Closure — verified 2026-07-22 (Phase 35, DEBT-04)

Re-tested before being trusted. The defect **does not reproduce**, and this record is closed as
already-resolved rather than fixed again.

- **Repaired by:** `ccef8b4` *test(commit-gate): make drift-block tests hermetic to ambient
  GOLDEN_APPROVE_HUMAN* (2026-07-09). Its message names DEF-05-02-1 by id and states it resolves it.
  The fix is not the per-test `delenv` this record suggested but a strictly broader one: an
  **autouse fixture** (`_no_ambient_approval`, `tools/hooks/tests/test_commit_gate.py:28-38`)
  that strips the token for **every** test in the module, and strips `HARNESS_DEV_BYPASS` for the
  same reason. The approval-path tests set their token in-body, which runs after the autouse
  fixture, so they were unaffected.

- **Reproduction attempt, both ways** — the three tests this record names, run explicitly:

  | Run | Result |
  |---|---|
  | `env -u GOLDEN_APPROVE_HUMAN uv run pytest <the 3 tests> -q` | **3 passed** |
  | `GOLDEN_APPROVE_HUMAN=phase-35-probe uv run pytest <the 3 tests> -q` | **3 passed** |
  | `GOLDEN_APPROVE_HUMAN=phase-35-probe uv run pytest tools/hooks -q` | **112 passed** |

- **Causal proof, not just a green run.** A green suite alone cannot distinguish "repaired" from
  "the symptom moved". The autouse fixture body was neutered (both `delenv` calls replaced with
  `pass`) and the module re-run with the token exported: **exactly the three named tests failed** —
  `test_drift_present_blocks`, `test_golden_skip_does_not_suppress_drift`,
  `test_from_hook_blocks_commit_on_drift` — reproducing this record's symptom precisely. The
  mutation was reverted and the tree confirmed clean. That fixture is therefore the load-bearing
  repair, and the record's diagnosis of the root cause was correct.

- **No new fix was invented.** The defect was already closed; inventing a second fix would have
  manufactured work and obscured who actually repaired it.

## DEF-05-SESSION-TOKEN — GOLDEN_APPROVE_HUMAN persists in THIS session's process env
- **What:** Phase 5's constitution-plane writes (05-02/03/05) were landed via the sanctioned
  approval path — `GOLDEN_APPROVE_HUMAN` set in a gitignored `.claude/settings.local.json` `env`
  block, verified injected into the Write-tool/commit-gate hooks.
- **Caveat:** Claude Code injects `env` on ADD but does NOT unset it on file removal within a
  running session, and an empty-value override does not propagate either. So the token remains in
  THIS session's process env — contract_guard is effectively bypassed for the remainder of the
  session. This could not be re-armed without a session restart.
- **Resolution:** `.claude/settings.local.json` was DELETED (never committed — gitignored), so a
  FRESH session starts with no token and contract_guard is fully re-armed. No residual risk beyond
  the authoring session, in which the sole actor made only the ADR-0002-ratified changes.
- **Status:** resolved for future sessions; no action needed.
