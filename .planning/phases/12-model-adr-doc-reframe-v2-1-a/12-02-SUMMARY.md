---
phase: 12-model-adr-doc-reframe-v2-1-a
plan: 02
status: complete
---

# Plan 12-02 Summary

## Completed

- Reworded the state banners in `activeContext.md` and `progress.md` to establish
  data authority: `contracts/` and `docs/adr/` win data conflicts over `.memory/state/`.
- Retained the active-context secrets and pointer clauses, and the progress durable-decision
  ADR clause.
- Reworded the root `AGENTS.md` lazy-load rule above the HARNESS-MANAGED block; the managed
  region was not changed.

## Verification

- The Plan 12-02 structural assertions pass: no `provisional`, `hint, not truth`, or
  `confirm before trusting` phrasing remains in the three edited surfaces; each preserves
  the `docs/adr/` data-authority reference.
- `tools/memory_regen/inject.py` remains unchanged.
