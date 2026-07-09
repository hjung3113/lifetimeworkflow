# Phase 5 — Deferred Items (out-of-scope discoveries)

## From 05-02 (GEN-02 generic default instance)

### DEF-05-02-1 — commit_gate drift-block tests leak the active ratification token

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
