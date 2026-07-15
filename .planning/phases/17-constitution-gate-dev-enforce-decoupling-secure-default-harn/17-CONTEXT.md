# Phase 17 — CONTEXT

**Source:** Approved brainstorm design `docs/superpowers/specs/2026-07-14-contract-guard-dev-bypass-design.md` (this phase implements it).

## Domain

Harness-core runtime hooks (`tools/hooks/`). Decouple the product's constitution gates from the
Claude **dev** session without weakening enforcement anywhere else. Independent of the v2.1 MEM2
chain (phases 12–16).

## Phase Boundary

**In scope:**
- `tools/hooks/_stdin.py` — add `DEV_BYPASS_ENV = "HARNESS_DEV_BYPASS"` + one shared `dev_bypassed() -> bool` (non-blank check, mirrors the token blank-rule).
- `tools/hooks/contract_guard.py` — `main()` (line ~94): `approved = token_present or dev_bypassed()`; emit a non-blocking stderr dev-note when the allow came via the dev flag (not the token). `decide()` byte-hygiene branch unchanged.
- `tools/hooks/commit_gate.py` — extend `_human_approved()` (lines ~56-58) / its DRIFT-ONLY bypass to also honor `dev_bypassed()`, same dev-note. Scope stays DRIFT-ONLY.
- Tests under `tools/hooks/tests/` for both gates (see Success Criteria).
- `docs/adr/0007-*.md` — append-only ADR recording the posture change (human-gated landing, like ADR-0006).

**Out of scope:**
- Any change to CODEOWNERS / PR-merge ratification (stays the real gate, untouched).
- Emitting the flag into any committed runtime config. The flag is read from env only; it lives solely in gitignored `.claude/settings.local.json`. Both runtimes keep identical guard code.
- The v2.1 MEM2 surfaces.

## Implementation Decisions (LOCKED by the approved spec)

1. **Secure default:** `HARNESS_DEV_BYPASS` unset/blank/whitespace ⇒ NO bypass (enforce). Preserves SC4.
2. **Distinct from the token:** separate env var from `GOLDEN_APPROVE_HUMAN`; a dev-bypassed write is never labeled "human ratified" (audit meaning preserved). Distinct dev-only stderr note.
3. **Byte-hygiene never waived:** even a dev-bypassed constitution write still fails on BOM/CRLF (§4.3-4.6). In `contract_guard.decide()` this is automatic (feeding `approved=True` skips only the access-control deny).
4. **Shared helper, no drift:** one `dev_bypassed()` in `_stdin.py` used by both gates.
5. **Flag location:** gitignored `.claude/settings.local.json` `env` block only (`.gitignore:27` confirms ignored). Never in committed settings.json / CI / opencode.

## Success Criteria

- `HARNESS_DEV_BYPASS=1` + constitution-plane Write ⇒ allowed (access-deny waived); dev-note on stderr.
- `HARNESS_DEV_BYPASS=1` + constitution path + BOM/CRLF payload ⇒ still DENIED (byte-hygiene).
- `HARNESS_DEV_BYPASS` unset ⇒ still DENIED without a token (SC4 regression guard).
- `HARNESS_DEV_BYPASS=""` / whitespace ⇒ does NOT bypass (mirrors token blank-rule).
- `commit_gate`: `HARNESS_DEV_BYPASS=1` downgrades a drift FAIL → WARN(dev) exactly like the token; unset keeps FAIL.
- Existing hook suites stay green; no committed config carries the flag.

## Canonical References

- Design spec: `docs/superpowers/specs/2026-07-14-contract-guard-dev-bypass-design.md`
- Current gates: `tools/hooks/contract_guard.py` (HOOK-04), `tools/hooks/commit_gate.py`, shared `tools/hooks/_stdin.py`.
- Precedent ADR: `docs/adr/0004-constitution-hook-fail-open-posture.md`; token precedent `tools/golden_runner/approve.py`.
- Wiring: `.claude/settings.json:125` (contract_guard PreToolUse), commit_gate Bash matcher.

## Risk Summary

- **Fail-open regression:** the default MUST stay enforce. Mitigated by SC4 regression test (unset ⇒ deny).
- **Agent self-enabling:** an agent could write the flag into `.claude/settings.local.json`. Accepted — same trust model as an agent editing settings to drop the hook; the real defense is the PR diff + CODEOWNERS, unchanged. Record explicitly in ADR-0007.
