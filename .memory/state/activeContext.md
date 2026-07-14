# activeContext — volatile session hint (COMMITTED, PROVISIONAL)

> PROVISIONAL — this file is a hint, not truth. `contracts/` and `docs/adr/` always
> override `.memory/state/` on conflict. No secrets, tokens, credentials, or PII here.
> The SessionStart injector injects only a *pointer* to this file, never its body.

## In flight

- Nothing in flight. Clean milestone boundary — `milestone: v2.0` complete + archived; no open phase.

## Next

- Start the next milestone with `/gsd:new-milestone` when ready.
- Deferred (non-blocking; see `.planning/STATE.md` → Operator Next Steps + `.planning/AUDIT-FINDINGS.md`):
  golden-comparator Batch B (H2/M1), optional `/gsd:complete-milestone v1.0`, `git push origin v2.0`.
