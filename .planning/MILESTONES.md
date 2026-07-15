# Milestones

## v2.0 Long-Horizon (Shipped: 2026-07-14)

**Phases completed:** 3 phases, 11 plans, 16 tasks

**Key accomplishments:**

- 1. [TDD sequencing] Prune test authored in Task 1 RED, not Task 2
- Read-mostly `curator` persona (edit+bash allow, write deny, no model id) plus `/refresh-memory` and a `/verify-work` freshness step, all round-tripped once through the Phase-7 emitter to both runtimes with GEN-04 green.
- Non-bypassable `stale-derived` CI job that regenerates docs/reference + .memory/derived/contracts-index.md and fails on any diff via the untracked-safe `git add -A` + `git diff --cached --exit-code` primitive, proven by a structural + negative-control test — completing MAINT-02.
- Authored the ECON-01/ECON-02 substrate — a fan-out-synthesize skill (decompose → dispatch N read-only explorer subtasks → recover schema-bounded citation-bearing summaries → orchestrator synthesizes), its co-located domain-neutral Draft 2020-12 return-contract JSON Schema, a thin /fan-out-synthesize command routing to the orchestrator, the anti-sprawl enumeration entry, and the Wave-0 structural gate.
- A dedicated `context-budget` skill (fan out vs work inline) wired at both named integration points — the orchestrator routing table/intake and `/orient` read-order — alongside the `fan-out-synthesize` substrate, so the delegate-vs-inline routing decision is a first-class, observable step (ECON-03).
- Round-tripped the fan-out-synthesize + context-budget surface through the Phase-7 emitter to both runtimes byte-identically, regenerated opencode.json/emit-manifest/AGENTS.md, and closed Phase 10 with a green gate (537 passed, GEN-04 green, emit-drift clean, 11 skills / 5 personas).
- 1. [Rule 3 - Blocking] Added tests/conftest.py + tests/__init__.py to the new uv member
- A repo:stage edge is proven to cross a repo boundary in the workspace layer, and a generalized GEN-04 guard proves the core references no workspace member with a key-scoped pointer exemption and live negative controls.
- The contract-first safety net now spans repo boundaries: cross-repo drift iterates each member's own baseline (no merge) and resolves every edge's contract in its producer, the golden runner resolves an edge-spanning case under a member root with a widened-not-removed `_confine` allowlist, and a separate `workspace` CI job in `gate.needs` enforces both (MREPO-03).
- Workspace-wide analysis is prose-wired to fan out one read-only worker per member repo with

workspace-level synthesis (no single context holds every repo), reusing the Phase-10 fan-out
substrate with NO new surface, and round-tripped byte-identical to both runtimes — closing out
Phase 11.

---
