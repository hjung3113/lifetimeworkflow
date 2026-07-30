# Phase 17 — RESEARCH

> Grounded from direct code inspection during the brainstorm. The design is settled
> (`docs/superpowers/specs/2026-07-14-contract-guard-dev-bypass-design.md`); this captures the exact
> seams the planner should target.

## Current code (verified)

### `tools/hooks/contract_guard.py`
- `APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"` (line ~46).
- `decide(file_path, content, approved) -> dict | None` (line ~49): off-plane ⇒ `None`; on-plane AND
  not `approved` ⇒ access-control `emit_deny`; on-plane AND approved BUT `lint_bytes` fails ⇒
  byte-hygiene `emit_deny`; on-plane, approved, byte-pristine ⇒ `None`.
- `main()` (line ~86-98): `approved = bool((os.environ.get(APPROVAL_ENV) or "").strip())` (line ~94).
  **This is the single line to change** to `approved = <token> or dev_bypassed()`.
- Imports from `tools.hooks._stdin`: `emit_deny, parse_event, read_stdin, repo_relative`.

### `tools/hooks/commit_gate.py`
- `APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"` (line ~53).
- `_human_approved() -> bool` (line ~56-58): `return bool((os.environ.get(APPROVAL_ENV) or "").strip())`.
- Drift path (line ~155-169): when `_human_approved()` ⇒ FAIL becomes `WARN (ratified)`; else
  `FAIL unapproved schema change(s)`. Bypass is DRIFT-ONLY (polyglot/other gates unaffected).
- **Extension point:** `_human_approved()` OR its call site should also honor `dev_bypassed()`.

### `tools/hooks/_stdin.py`
- Shared module imported by BOTH gates ⇒ correct home for `DEV_BYPASS_ENV` + `dev_bypassed()`.

### Wiring / config
- `.claude/settings.json:125` → `uv run python -m tools.hooks.contract_guard` (PreToolUse Write|Edit).
- `.claude/settings.local.json` is **gitignored** (`.gitignore:27`) ⇒ safe home for the dev flag.

## Key findings

1. `contract_guard.decide()` already keeps byte-hygiene independent of `approved` — so feeding
   `approved=True` via the dev flag automatically preserves byte-hygiene. No change to `decide()`
   logic needed beyond threading a note-reason for the dev-allow.
2. The token blank-rule (`(... or "").strip()`) must be mirrored exactly for the dev flag: empty/
   whitespace ⇒ no bypass.
3. Distinct env var is essential: reusing `GOLDEN_APPROVE_HUMAN` would forge the audit token's
   meaning. Use `HARNESS_DEV_BYPASS`.
4. SC4 is a live, already-verified behavior (an agent Write to `docs/adr/` was denied during Phase
   12). The regression test must assert: flag unset ⇒ still denied.
5. commit_gate's existing token bypass emits `WARN (ratified)`; the dev bypass should emit a
   distinct dev-scoped note so logs distinguish "human ratified" from "dev bypass".

## Test surface

- `tools/hooks/tests/` — existing gate tests (e.g. `test_commit_gate.py`) show the fixture pattern
  (monkeypatch env + call `decide`/`main`/gate fn). Add cases per the CONTEXT Success Criteria for
  both `contract_guard` and `commit_gate`, plus a `dev_bypassed()` unit test for the blank-rule.

## Validation Architecture

- Framework: pytest (uv workspace). Fast unit tests, no compile.
- Per-task asserts: `uv run pytest tools/hooks/tests -q` after each task; full `uv run pytest
  tools/hooks tools/harness_lint` before verify.
- ADR-0007 landing is a manual/human-gated verification (same as ADR-0006).
