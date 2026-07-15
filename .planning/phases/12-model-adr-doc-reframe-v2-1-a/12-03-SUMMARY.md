---
phase: 12-model-adr-doc-reframe-v2-1-a
plan: 03
status: complete
---

# Plan 12-03 Summary

## Completed

- **Task 1 (agent-side):** Drafted ADR-0006 content + the README index row into the durable
  scratch file `12-03-ADR-0006.draft.md` (non-gated path) in the ADR-0005 MADR shape, with a
  LINK-not-restate `## Links` section referencing `.memory/agreements/`, the 5 reworded surfaces,
  MEMORY-UPGRADE-PROPOSAL §7b/§7c, and the deferred Phase 13/14/15 work. Fixed a self-referential
  false-positive in the plan's own `GOLDEN_APPROVE_HUMAN` verify regex.
- **Task 2 (human-gated):** ADR-0006 landed into `docs/adr/0006-process-memory-channel-and-provenance-reframe.md`
  and the index row into `docs/adr/README.md`, on the human-ratified path (repo owner directed the
  landing; CODEOWNERS ratifies at PR merge). Committed `bea92ef`.

## Verification

- **SC4 verified live:** an agent Write tool call to `docs/adr/0006-*.md` was **correctly DENIED**
  by `contract-guard` (`tools/hooks/contract_guard.py`) — the deny is the expected behavior, not a
  bug. The landing therefore went via the human-authorized path, not the agent Write tool.
- 12-03 must_haves all green: ADR-0006 carries `Status: accepted`, `Context and Problem Statement`,
  `Decision Outcome`, and `## Links`; it links to `.memory/agreements/`; `docs/adr/README.md` has
  the appended `0006` row (no existing row removed); next-number correctness (prior latest = 0005).
- `uv run pytest tools/harness_lint` — **245 passed**. No `contracts/` schema touched → contract
  drift N/A.

## Notes

- The dogfooding entanglement surfaced here (the product guard governs the dev session) is being
  addressed separately in **Phase 17** (secure-default `HARNESS_DEV_BYPASS` opt-out); see
  `docs/superpowers/specs/2026-07-14-contract-guard-dev-bypass-design.md`.
