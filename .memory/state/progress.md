# progress — terse running log (COMMITTED)

> DATA AUTHORITY — on a data conflict, `contracts/` and `docs/adr/` win over
> `.memory/state/`. This is a session progress log, not a reason to re-verify grounded work.
> No secrets/PII. Durable decisions go in append-only `docs/adr/`, not here.

- v1.0 (phases 1–8) + v2.0 (phases 9–11): complete + archived.
- Full-harness audit: done — Batch A merged; Batch B (H2/M1 golden comparator) deferred (ADR-0005).
- SessionStart injection: temporarily DISABLED (`.memory/.inject-disabled`) until MEM2.
- NEXT: MEM2 memory-model upgrade — see `.planning/MEMORY-UPGRADE-PROPOSAL.md` → `/gsd:new-milestone`.
