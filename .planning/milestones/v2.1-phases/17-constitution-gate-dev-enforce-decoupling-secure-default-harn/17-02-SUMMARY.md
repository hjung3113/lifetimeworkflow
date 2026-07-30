---
phase: 17-constitution-gate-dev-enforce-decoupling-secure-default-harn
plan: 02
status: complete
---

# Plan 17-02 Summary

## Completed

- **Task 1 (agent-side):** Drafted ADR-0007 (Block A body + Block B README row) into the durable
  scratch `17-02-ADR-0007.draft.md` in the ADR-0006 MADR shape, recording all LOCKED decisions
  (secure default, distinct-from-token, byte-hygiene-never-waived, shared `dev_bypassed()`, flag in
  gitignored settings.local only, CODEOWNERS-is-the-real-gate) and the accepted agent-self-enabling
  risk, LINK-not-restate Links.
- **Task 2 (human-gated):** ADR-0007 landed into
  `docs/adr/0007-constitution-gate-dev-enforce-decoupling.md` + the index row into
  `docs/adr/README.md`, via the human-ratified path (repo owner directed the landing; CODEOWNERS
  ratifies at PR merge). Committed `ad6f644`.

## Verification

- 17-02 must_haves green: Status accepted, Context and Problem Statement, Decision Outcome, `## Links`;
  records HARNESS_DEV_BYPASS + GOLDEN_APPROVE_HUMAN (distinct) + byte-hygiene + CODEOWNERS; next number
  0007 correct; no marker leak; no fabricated token.
- T-17-04 respected: ADR-0007 was NOT self-landed via the new `HARNESS_DEV_BYPASS` flag — the raw-shell
  landing does not go through the agent Write/Edit tool the contract-guard hook matches.

## Notes

- With Phase 17 shipped, enabling `HARNESS_DEV_BYPASS` in gitignored `.claude/settings.local.json`
  lets the dev agent land future constitution writes in-session (CODEOWNERS still gates merge) —
  ending the manual raw-shell handoff used for ADR-0006 / ADR-0007.
