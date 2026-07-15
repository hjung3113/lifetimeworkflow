# Design — `HARNESS_DEV_BYPASS`: secure-default dev opt-out for the constitution gates

*Date: 2026-07-14 · Status: approved (brainstorm) · Scope: harness core (`tools/hooks/`)*

## Problem

The harness's **product** guard `contract-guard` (`tools/hooks/contract_guard.py`, HOOK-04) is wired
as a live `PreToolUse(Write|Edit)` hook in the very Claude Code session used to **develop** the
harness (`.claude/settings.json:125` → `uv run python -m tools.hooks.contract_guard`). So the
artifact-under-construction governs its own workshop: an agent doing legitimate GSD work on the
harness's own `docs/adr/` / `contracts/` / `golden/` is denied, and a bug in the WIP guard could
brick all dev writes. The same entanglement applies to `commit_gate` (`PreToolUse(Bash)` on `git
commit`).

This is deliberate dogfooding (SC4 = "an agent Write to `docs/adr/` is DENIED without the token" is a
verified behavior), but there is no way for the dev human to opt the **local dev session** out
without disabling the dogfood entirely or fabricating the `GOLDEN_APPROVE_HUMAN` audit token.

## Non-goals

- Not weakening the true gate. **CODEOWNERS review at PR merge remains the non-bypassable
  ratification** for the constitution plane. The runtime hooks are an accident-prevention guardrail,
  never a sandbox against a determined agent (an agent that can edit `.claude/settings.local.json`
  could already remove the hook — the defense against that is the PR diff + CODEOWNERS, unchanged).
- Not touching byte-hygiene. BOM/CRLF §4.3-4.6 enforcement is mechanical correctness, never a
  human-ratification concern, and stays enforced even under the dev bypass.
- Not diverging the two emitted runtimes. The flag is read from env at runtime; no committed config
  in either runtime changes.

## Decision

Add a **dedicated, secure-default dev opt-out env flag `HARNESS_DEV_BYPASS`**, distinct from the
`GOLDEN_APPROVE_HUMAN` ratification token, honored by both constitution gates.

### Semantics (mirrors the existing token rule)

- `HARNESS_DEV_BYPASS` unset **or** empty/whitespace-only ⇒ **no bypass** (default = enforce). This
  preserves SC4 by default.
- `HARNESS_DEV_BYPASS` set to any non-blank value ⇒ the **access-control** deny (the "human token
  required" branch) is waived for that process.
- It is **separate** from `GOLDEN_APPROVE_HUMAN` so a dev-bypassed write is never mislabeled "human
  ratified" — the audit meaning of the token is preserved. A write allowed via the dev flag emits a
  non-blocking stderr note: `constitution write allowed via HARNESS_DEV_BYPASS (dev-only) —
  CODEOWNERS still gates merge`.
- **Byte-hygiene is NOT waived**: even a dev-bypassed constitution write still fails if its payload
  bytes violate §4.3-4.6 (BOM/CRLF). In `contract_guard.decide()` this is automatic — feeding
  `approved=True` skips only the access-control deny; the `lint_bytes` branch still runs.

### Where the flag lives

- Set only in **`.claude/settings.local.json`** `env` block — already **gitignored**
  (`.gitignore:27`), so it is local to one dev machine's Claude session.
- **Never** in committed `.claude/settings.json`, CI workflow env, or opencode config. Everywhere
  except the explicit local dev session, the flag is unset ⇒ gates enforce.

## Components & changes

1. **Shared helper** — add `DEV_BYPASS_ENV = "HARNESS_DEV_BYPASS"` and a single
   `dev_bypassed() -> bool` (non-blank check) in the module both gates already import
   (`tools/hooks/_stdin.py`). One definition, no drift between the two gates.

2. **`tools/hooks/contract_guard.py`** — in `main()`, change
   `approved = bool((os.environ.get(APPROVAL_ENV) or "").strip())`
   to `approved = token_present or dev_bypassed()`. Thread a flag into `decide()` (or compute the
   stderr note at the `main()` seam) so a dev-bypass allow prints the dev-only note. `decide()`'s
   byte-hygiene branch is unchanged.

3. **`tools/hooks/commit_gate.py`** — extend `_human_approved()` (or its call sites) so the
   DRIFT-ONLY bypass also honors `dev_bypassed()`, with the same dev-only stderr note. Scope stays
   DRIFT-ONLY (polyglot/other gates unaffected), matching today's token bypass.

4. **`docs/adr/0007-*.md`** — append-only ADR recording: the dev opt-out, its secure default
   (enforce-unless-explicitly-bypassed), the token-vs-dev-flag separation, and the explicit statement
   that CODEOWNERS at merge remains the real gate. (Landing 0007 itself uses the new flag or a manual
   human write — the same human-gated path as any ADR.)

## Tests (`tools/hooks/tests/`)

- `HARNESS_DEV_BYPASS=1` + constitution path ⇒ **allowed** (no access deny).
- `HARNESS_DEV_BYPASS=1` + constitution path + BOM/CRLF payload ⇒ **still denied** (byte-hygiene not
  waived).
- `HARNESS_DEV_BYPASS` unset ⇒ **still denied** without a token (SC4 regression guard).
- `HARNESS_DEV_BYPASS=""` / whitespace ⇒ **does NOT bypass** (mirrors the token blank-rule).
- `commit_gate`: `HARNESS_DEV_BYPASS=1` downgrades a drift FAIL to WARN(dev) exactly like the token,
  and unset keeps the FAIL.

## Verification

- Existing SC4 assertions stay green with the flag unset.
- With the flag set in a local `.claude/settings.local.json`, the dev agent can Write to `docs/adr/`
  in-session; the stderr dev-note appears; the PR diff still routes through CODEOWNERS.

## Rollout / phase placement

New GSD phase (harness-core change with its own ADR + tests). Does **not** belong to Phase 12
(memory-model reframe); Phase 12 stays as-is and its 12-03 ADR-0006 lands via the human path. This
design is the input to that new phase's plan.
