# 9. Contract-Relationship Graph Model: Compiler, Affected-Set Queries, and Conductor Rendering Contract

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-19
- **Deciders:** kimhyojung (CODEOWNERS)
- **Supersedes:** —
- **Superseded by:** —
- **Complements:** [ADR-0002](0002-general-template-de-specialization.md), [ADR-0003](0003-pipeline-topology-slot-and-instance-overlay.md)

## Context and Problem Statement

Phase 24 shipped the *vocabulary* for a general contract-relationship graph — the ratified
`relationship.schema.json` per-record shape, the additive `[contract_graph]` TOML slot, and
`effective_relationships()`, which lowers legacy `[pipeline].edges` and unions explicit
`[[contract_graph.relationships]]` rows into one stable-sorted, deduped record list (raising
`ValueError` on the three failure modes). But that vocabulary was not yet *usable*: nothing
resolved endpoints against declared components/members, nothing validated authority-owned-contract
existence, nothing traversed the graph for affected-set routing, and the conductor surfaces
(`/pipeline`, `pipeline-map`, `orchestrator`) still read the raw linear passthrough.

The harness needed **one general, deterministic way** to validate and query
contract-relationships beyond the linear pipeline model — consumed by the **existing** conductor
surface, with **no second interpreter, no new command, and no new persona**. Because Phases 26–29
(brownfield adoption, Living Docs graph-impact reports) all depend on this whole surface as a unit,
the model must be fixed as **one ratified decision**, not a partial or single-topic record (D-04).

## Decision Drivers

- Keep contracts and ADRs authoritative and human-ratified; the graph model consumes them, it does
  not become a competing authority.
- Preserve a domain-neutral core and the one-way instance dependency (ADR-0002).
- One deterministic implementation the conductor CONSUMES — never a second interpretation of the
  graph (TOPO-06).
- Legal non-linear shapes (fan-in, fan-out, disconnected components, canonical cycles) must be
  first-class, not errors.
- The existing linear topology render must stay **byte-identical** (TOPO-06 hard requirement).
- The query layer must not leak into the task-control evidence plane or preload contract bodies.

## Considered Options

1. **Re-derive authority/dependents inline** from `[pipeline].edges` +
   `[[contract_graph.relationships]]` inside the compiler. *Rejected:* forks the lowering/union
   logic away from `effective_relationships()`, the single Phase-24 path, and re-introduces the
   dedup/sort/failure-mode handling that function already owns.
2. **Numbered diagnostic codes** (`TOPO-C001`-style) for the consistency gate. *Rejected:* the
   repo's established gate convention (GEN-04, POLY-01, GEN-03) is descriptive grep-able slugs;
   numbered codes are opaque in CI output (D-02).
3. **Edge-list or adjacency-map human-facing render**, and/or a **new graph command/persona**.
   *Rejected:* an edge-list breaks linear byte-identity and reads worse; a new command/persona
   violates TOPO-06's "usable through the EXISTING surface" intent.
4. **Compiler + query layer on top of `effective_relationships()`, indented-tree render on the
   existing surfaces, descriptive slugs.** *Proposed.*

## Decision Outcome

**Ratified by human/CODEOWNERS on 2026-07-19.**

Adopted as ONE ratified unit per D-04 — the record/graph model, the affected-set query semantics,
and the conductor rendering contract ship together and are fixed together:

### 1. The record/graph model (compiler resolution + diagnostic slugs)

- The per-record shape is Phase 24's `relationship.schema.json`
  (`{id, contract, authority, dependents}`); the additive `[contract_graph]` TOML slot and
  `effective_relationships()`'s lowering + additive union + stable sort-by-id remain the **single**
  record source. The compiler does **not** re-lower or re-union — it is a resolution/validation
  layer ON TOP (`tools/contract_graph/compile.py::compile_graph(cfg) -> {relationships, adjacency,
  diagnostics}`).
- `compile_graph` resolves every authority/dependent endpoint via `split_endpoint` against declared
  `[[components]]` (project) and `[[members]]` (workspace), and builds a sorted, repo-confined
  adjacency map (`authority -> [sorted dependents]`).
- **Authority-owned-contract resolution** uses a **produces-check with an existence-only
  fallback**: when the authority endpoint resolves to a declared component/member carrying a
  `produces` list, ownership means the contract is in that `produces` list (same rule as legacy
  edges); when the authority is an opaque logical id with no `produces`-bearing declaration, it
  falls back to schema-glob **existence** under `contracts/` (project) or `<member>/contracts/`
  (cross-repo) — reusing the repo's established schema-glob existence idiom rather than a fourth
  bespoke checker. This fallback is a genuine design decision and is recorded here per D-04.
- Three **descriptive, stable, grep-able diagnostic slugs** (D-02) are returned as sorted data
  (never raised): `unresolved-authority`, `dangling-endpoint`, `unknown-contract`. The three
  `effective_relationships()` `ValueError` modes stay hard crashes — the two layers are not
  conflated.
- **Fan-in, fan-out, disconnected components, and canonical cycles are explicitly legal** — they
  compile with empty diagnostics and are never flagged. A cycle is simply two adjacency entries with
  no special casing. The TOPO-04 `harness_lint` gate anchors zero diagnostics on core + workspace
  defaults.

### 2. The affected-set query semantics (TOPO-05)

- `tools/contract_graph/query.py` exposes `direct` / `reverse` / `transitive` over the compiled
  `adjacency` — reading the compiled graph only, never re-resolving endpoints or re-walking config.
- Every query returns the D-03 shape **`{ids: [...sorted...], paths: [[...]]}`** — sorted ids AND
  the connecting path(s), never ids alone, where `paths[i]` corresponds to `ids[i]` and starts at
  the query node. Both consumers (conductor routing and documentation reports) need the paths to
  explain *why* a node is impacted.
- `transitive` is **cycle-safe** via an iterative visited-set worklist (visited-check before
  enqueue): a legal cycle terminates in O(nodes+edges) with no recursion and no double-counting;
  neighbours are visited in sorted order so first-found paths are byte-identical across runs.
- The query layer creates **no new task-evidence requirement** and **preloads no contract body**
  (TOPO-05 invariant) — proven structurally (the module imports no task-control/evidence/handoff
  plane and performs no file I/O), keeping it independent of the task-control evidence plane.

### 3. The conductor rendering contract (D-01, TOPO-06)

- `/pipeline` and `pipeline-map` render the general (branching/cyclic) graph as an **indented tree**
  rooted at authority endpoints with no incoming edge (lexicographically-first authority for a fully
  cyclic graph), descending one indent level per hop. An already-visited node is printed as an
  explicit terminal `(cycle -> <node>)` marker rather than recursing, reusing the query layer's
  visited-set discipline.
- The **existing linear topology render stays byte-identical** — the tree render is an ADDITIVE
  section; the linear stage-list/edge-chain output is untouched (proven by a hardcoded literal-text
  regression, zero removed lines).
- **No new graph command and no new persona** (TOPO-06): the single `orchestrator` persona's
  "Trace the topology" step is enriched with one sentence citing `direct`/`reverse`/`transitive` for
  non-linear affected-set routing; the surfaces round-trip byte-identically to both runtimes
  (`.opencode/` + `.claude/`) with no model identifier.

### Deferred / closed dispositions (recorded for a traceable decision trail)

- **WR-01 (deferred, fixture-vocabulary-constrained):** the Phase-24 lowered id
  `pipeline/<contract>/<from>-><to>` is non-injective when component/contract ids contain `/` or
  `->` (24-REVIEW.md). This milestone **defers** the code fix and instead **constrains fixture
  vocabulary** — every proof fixture id/contract/authority/dependent excludes `/` and `->`, enforced
  by Plan 04's automated corpus scan (a falsifiable test, not a manual convention).
- **WR-02 (closed):** `effective_relationships()` now raises an actionable `ValueError` naming the
  offending record on a malformed edge/record, replacing the previous bare `KeyError` (Plan 01
  Task 3); signature and return shape are unchanged.

### Consequences

- **Good:** one deterministic compiler + query implementation; the conductor consumes it and never
  re-interprets the graph; legal non-linear shapes are first-class; the linear render is provably
  byte-identical; the query layer's blast radius is bounded to pure in-memory traversal.
- **Good:** Phases 26–29 build on a single ratified surface rather than a moving target.
- **Bad / accepted:** WR-01 remains a deferred, vocabulary-constrained gap — fixture authors must
  keep endpoint/contract ids free of `/` and `->` until the id scheme is made injective in a later
  milestone; the automated scan is the guard, not a code fix.

## Approval

Ratified by human/CODEOWNERS (kimhyojung) on 2026-07-19. Once ratified this decision is authoritative
and append-only.

## Links

- Record shape: `contracts/harness/topology/relationship.schema.json`.
- Single lowering/union path: `tools/harness_config/loader.py::effective_relationships()`.
- Compiler + queries: `tools/contract_graph/compile.py`, `tools/contract_graph/query.py`, and the
  TOPO-04 gate `tools/harness_lint/tests/test_contract_graph_config.py`.
- Conductor surfaces (byte-identical linear render preserved): `harness/commands/pipeline.md`,
  `harness/skills/pipeline-map/SKILL.md`, `harness/agents/orchestrator.md`.
- Proof fixtures + dispositions: `tools/contract_graph/tests/fixtures/graphs/valid/cases.json`,
  `tools/contract_graph/tests/test_proof_fixtures.py`,
  `tools/contract_graph/tests/test_cross_repo_authority.py`.
- Design authority: `.planning/phases/25-graph-compiler-queries-conductor-proof-v2-3-a/25-CONTEXT.md`
  (D-01..D-04) and `.planning/phases/24-contract-relationship-vocabulary-compatibility-v2-3-a/24-REVIEW.md`
  (WR-01/WR-02).
