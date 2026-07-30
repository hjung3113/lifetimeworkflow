---
phase: 17-constitution-gate-dev-enforce-decoupling-secure-default-harn
plan: 01
status: complete
---

# Plan 17-01 Summary

## Completed

- **Task 1 — shared helper.** Added `DEV_BYPASS_ENV = "HARNESS_DEV_BYPASS"` + `dev_bypassed() -> bool`
  (non-blank check mirroring the token blank-rule) and `import os` to `tools/hooks/_stdin.py`; unit
  test for blank/whitespace ⇒ False. (commit `a6ab9f5`)
- **Task 2 — contract_guard.** Threaded `dev_bypassed()` into `main()` (`approved = token OR
  dev_bypassed()`); extracted `_on_constitution_plane()` (reused by `decide()`); emit a distinct
  on-plane dev-only stderr note naming `HARNESS_DEV_BYPASS` + CODEOWNERS (never "ratified"). `decide()`
  byte-hygiene branch unchanged. Tests SC1–SC4 + source-path-no-note. (commit `911e8d8`)
- **Task 3 — commit_gate.** Threaded `dev_bypassed()` into `check_drift()` as a DRIFT-ONLY
  `WARN (dev)` PASS, distinct from the token's `WARN (ratified)`; token check stays first;
  polyglot/golden untouched. Tests SC5 + no-polyglot-weakening. (commit `b1ddee9`)

## Verification

- `uv run pytest tools/hooks tools/harness_lint` — **348 passed**.
- SC6: `grep -rn HARNESS_DEV_BYPASS .claude/settings.json .github/ opencode.json` — **empty** (the flag
  lives only in gitignored `.claude/settings.local.json`; no committed config carries it).
- Secure default preserved: flag unset ⇒ constitution write still denied / drift still FAIL (regression tests green).
- No model identifier in any commit.

## Notes

- Task 1 was implemented by a delegated Codex worktree (`gpt-5.6-terra`), FF-merged; Tasks 2–3 were
  implemented directly after the Codex terminal stalled on MCP-server startup. Result is identical to
  the plan.
- Wave 2 (plan 17-02 / ADR-0007) is human-gated — draft staged in `17-02-ADR-0007.draft.md`; the agent
  must NOT self-land it via the new `HARNESS_DEV_BYPASS` flag (T-17-04).
