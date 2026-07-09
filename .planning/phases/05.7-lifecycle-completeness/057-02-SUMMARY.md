---
phase: 5.7
plan: "02"
slug: should-have-lifecycle
wave: 2
status: complete
created: 2026-07-09
---

# Phase 5.7 · Plan 02 — SUMMARY (SHOULD-HAVE, LIFE-06..11)

Completed the onboard→plan→review→integrate lifecycle stages. Domain-neutral; guard sets updated
in-wave; non-example suite green.

## Delivered
- **LIFE-06** `harness/commands/orient.md` — regenerates the derived plane
  (`tools.memory_regen.repo_map`/`contracts_index`) + prints the `inject.assemble()` pointer payload
  + the read-order golden path. Runtime-independent replacement for the deferred opencode injector.
- **LIFE-07** `harness/commands/review.md` — `git diff` → read-only `code-reviewer` →
  severity-classified findings → back to the scoped engineer; secret-scan posture noted (enforcement
  stays in the on-write hook — no invented CLI).
- **LIFE-08** `harness/skills/gate-model/SKILL.md` — the gate map: constitution `path_deny_globs`,
  machines-gate/humans-ratify, exit-3 refusals (`golden_runner.approve`, `strangler_guard`), hook
  surface, `GOLDEN_APPROVE_HUMAN` token.
- **LIFE-09** `harness/skills/two-plane-memory/SKILL.md` — constitution vs derived; committed
  `.memory/state/` vs gitignored `.memory/derived/`; derived-never-hand-edited; lazy-load.
- **LIFE-10** `harness/commands/verify-work.md` — in-session composite gate (`/lint` + `/test` +
  `/contract-check` + `/golden`); golden step is .NET-presence-gated + presence-safe (announced skip
  in the bare template, which ships no converter); distinct from Phase-6 CI + `/checkpoint`.
- **LIFE-11** `harness/agents/orchestrator.md` augmented with an intake→decompose procedure + a
  work-shape → persona/command routing decision table. No new persona.

## Guards
- `EXPECTED_SKILLS` += `gate-model`, `two-plane-memory` (now 8). `test_agents` still exactly 4
  personas + `code-reviewer` read-only invariant intact. Referential integrity green. Prose guard
  clean.

## Verification
- Full non-example `uv run pytest` green (402 passed, +41 vs the 361 baseline).
- `/orient` + `/verify-work` macros exercised in-container: memory regen OK; verify-work golden step
  announces a non-fatal .NET skip (exit 0). Net-new ruff errors: 0.
