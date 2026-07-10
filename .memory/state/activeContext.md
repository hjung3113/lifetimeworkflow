# activeContext — volatile session hint (COMMITTED, PROVISIONAL)

> PROVISIONAL — this file is a hint, not truth. `contracts/` and `docs/adr/` always
> override `.memory/state/` on conflict. No secrets, tokens, credentials, or PII here.
> The SessionStart injector injects only a *pointer* to this file, never its body.

## In flight

- Phase 2 — Two-Plane Memory + Rules. 02-01 laid the `.memory/` two-plane skeleton +
  `tools/memory_regen` member. 02-02 fixed the single injection contract
  (`inject.assemble`) and wired the Claude SessionStart injector as the 4th slot
  (coexists) + authored-deferred opencode adapter.

## Next

- 02-03 contracts-index and 02-04 repo-map produce `.memory/derived/*.md` — `assemble()`
  already reads their heads and degrades gracefully until they exist. 02-05 AGENTS.md rules.
