# activeContext — volatile session hint (COMMITTED, PROVISIONAL)

> PROVISIONAL — this file is a hint, not truth. `contracts/` and `docs/adr/` always
> override `.memory/state/` on conflict. No secrets, tokens, credentials, or PII here.
> The SessionStart injector injects only a *pointer* to this file, never its body.

## In flight

- **Milestone v2.1 — MEM2 (Process Memory & Provenance Reframe)** started + roadmap written
  (phases 12–16, 7/7 requirements mapped). No phase planned/executed yet. Nothing mid-edit.
- SessionStart memory injection is temporarily **DISABLED** (`.memory/.inject-disabled`) — MEM2
  Phase 13 reframes it; re-enable with `rm .memory/.inject-disabled`.

## Next

- **`/gsd:plan-phase 12`** — Model + ADR + Doc Reframe (v2.1 A): scaffold `.memory/agreements/`
  process tier, reword distrust framing to data-authority, ratify as ADR-0006. Then 13→14→15→16.
- Design source of truth: `.planning/MEMORY-UPGRADE-PROPOSAL.md` (§7 operator refinements authoritative).
- Kickoff open Qs still to settle at planning: Q1 gating strength, Q2 `/checkpoint` vs `/agree`,
  Q4 inject budget, Q6 staleness threshold (Q3/Q5 already decided: per-guideline files; per-file retire).
- Deferred (non-blocking): golden-comparator Batch B (H2/M1, ADR-0005), optional `/gsd:complete-milestone v1.0`.
