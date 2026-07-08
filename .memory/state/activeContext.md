# activeContext — volatile session hint (COMMITTED, PROVISIONAL)

> PROVISIONAL — this file is a hint, not truth. `contracts/` and `docs/adr/` always
> override `.memory/state/` on conflict. No secrets, tokens, credentials, or PII here.
> The SessionStart injector injects only a *pointer* to this file, never its body.

## In flight

- Phase 2 — Two-Plane Memory + Rules. Plan 02-01 laid the `.memory/` two-plane skeleton
  and the `tools/memory_regen` uv-workspace member (pinned tree-sitter + networkx).

## Next

- 02-02 injector, 02-03 contracts-index, 02-04 repo-map, 02-05 AGENTS.md rules build on
  this layout and the resolved toolchain.
