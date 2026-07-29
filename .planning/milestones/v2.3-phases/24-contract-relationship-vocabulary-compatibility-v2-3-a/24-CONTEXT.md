# Phase 24: Contract-Relationship Vocabulary + Compatibility - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Ship the ratified **contract-relationship record vocabulary** and its **additive, backward-compatible configuration seam** — nothing more. This phase delivers three things and stops:

1. **TOPO-01** — A human-ratified Draft 2020-12 schema under `contracts/harness/topology/` defining a single relationship: stable id + tracked contract reference + exactly one authority endpoint + one-or-more dependent endpoints + optional explanatory `kind`/`labels`. Positive/negative fixtures pass the existing contract-hash/drift ratification path.
2. **TOPO-02** — An additive `[[contract_graph.relationships]]` TOML slot accepted by both `harness/project.toml` and `workspace.toml`, plus a thin raw-data accessor. Existing loader APIs and legacy config stay byte-unchanged.
3. **TOPO-03** — One deterministic `effective_relationships()` path that lowers every legacy `[pipeline].edges` entry to an authority/dependent relationship and unions it with explicit records, failing on duplicate ids / duplicate semantic edges / contradictions, while leaving current linear fixtures byte-unchanged.

**NOT this phase (Phase 25 owns):** the domain-neutral compiler, the `harness_lint` consistency gate, endpoint/authority-resolution validation, affected-set queries, `/pipeline`·`pipeline-map`·orchestrator generalization, non-linear proof fixtures, and the topology ADR ratification. This phase fixes the *wire shape* and *coexistence semantics* only — the schema validates structure/cardinality, not graph resolution.

</domain>

<decisions>
## Implementation Decisions

These are the HOW choices locked during discussion (auto-mode, recommended defaults). All stay inside the TOPO-01/02/03 boundary above.

### Schema granularity & file layout
- **D-01:** One **record-level** schema `contracts/harness/topology/relationship.schema.json` validating a *single* relationship object — NOT a graph-document schema wrapping the whole array. Rationale: mirrors the existing `contracts/harness/task-control/*.schema.json` per-record pattern; array-level consistency (unique ids, resolution) is Phase 25's compiler job, not the schema's. Positive/negative fixtures are instance files validated against this schema through the existing hash/drift path.

### Endpoint reference shape
- **D-02:** Endpoints are **bare stable-id strings**. `authority` = a single string; `dependents` = a non-empty array of strings. The schema enforces *shape and cardinality only* (exactly-one authority, ≥1 dependent). Existence/resolution of an endpoint against declared components/members is deliberately **deferred to the Phase 25 compiler** — keeping Phase 24 pure vocabulary.

### Additive TOML slot + accessor
- **D-03:** The `[[contract_graph.relationships]]` TOML record mirrors the schema fields **1:1** (`id`, `contract`, `authority`, `dependents`, optional `kind`/`labels`). New accessor `contract_graph_relationships(cfg)` in `tools/harness_config/loader.py` returns **raw `list[dict]` passthrough** — zero validation, traversal, discovery, or domain policy — exactly mirroring the data-only posture of the existing `pipeline()` / `components()` helpers (TOPO-02 pure-DATA). Existing loader signatures untouched.

### Legacy `[pipeline].edges` lowering
- **D-04:** Each legacy edge `{ from, to, contract }` lowers deterministically to: `authority = from` (the producer owns the contract), `dependents = [to]`. The synthesized id is **namespaced** (e.g. `pipeline/<contract>/<from>-><to>`) so lowered ids can never collide with human-authored explicit-record ids. `effective_relationships()` unions lowered edges with explicit `[[contract_graph.relationships]]` records in one path.

### Failure taxonomy for `effective_relationships()`
- **D-05:** The union fails (deterministically, stable diagnostic) on: (a) **duplicate id** — same `id` appears twice; (b) **duplicate semantic edge** — same `(authority, contract, dependent)` triple; (c) **contradiction** — the same `contract` claimed by two *different* authorities. Current linear fixtures have no explicit records, so they exercise lowering-only and stay **byte-unchanged**.

### Claude's Discretion
- Exact synthesized-id delimiter/format (D-04) and diagnostic message wording (D-05) are left to the planner/executor, provided they are deterministic and stable-sortable.
- Whether the schema lives as a single `relationship.schema.json` or gains a sibling `topology/` README is executor discretion — the record schema itself is fixed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Ratified design (authoritative — read first)
- `.planning/research/v2.3-scoping-FINAL.md` — §"Theme A" (TOPO-01..07) + §"Phase 24 — Contract-Relationship Vocabulary and Compatibility" (Goal, Owns 1:1, Exit). The human-approved sol-vs-fable merged FINAL; the source of every decision above.
- `.planning/REQUIREMENTS.md` — TOPO-01, TOPO-02, TOPO-03 (this phase owns these 1:1).
- `.planning/ROADMAP.md` — Phase 24 line + DAG (`24→25`, `24→26`).

### Existing patterns to mirror / extend (reuse, do not reinvent)
- `harness/project.toml` — the `[[languages]]` + `[[components]]`/`[pipeline]` **data-only, no-enforcement** slot pattern the new `[[contract_graph.relationships]]` slot must match (see the `BEGIN PIPE-01 topology` block).
- `workspace.toml` — the additive slot must also be accepted here (TOPO-02 = project **and** workspace TOML).
- `tools/harness_config/loader.py` — stdlib-`tomllib` thin loader; extend with the passthrough accessor + `effective_relationships()`; existing `components()` / `pipeline()` / `languages()` are the shape-and-signature template. Do NOT change their signatures.
- `contracts/harness/task-control/*.schema.json` — the per-record Draft 2020-12 schema exemplar (e.g. `task.schema.json`, `state.schema.json`) the topology record schema should follow.

### Ratification / gate path (must pass unchanged)
- `tools/contract_hash/` + `tools/contract_drift/` — the RFC-8785 schema-hash + drift ratification path the new schema + fixtures must pass (positive/negative). Reuse; do not fork.
- `tools/harness_lint/tests/test_pipeline_config.py` — existing topology consistency gate; the **Phase 25** compiler gate will extend this posture, but reference it now to keep the new data shape gate-compatible.
- `docs/adr/` — **ADR-0009 is reserved** for the topology model. The ADR is authored/ratified in **Phase 25**, not here — Phase 24 leaves the reservation intact.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/harness_config/loader.py`: `pipeline(cfg)` and `components(cfg)` are pure `tomllib` passthroughs — the new `contract_graph_relationships(cfg)` accessor is a near-copy (raw dict list, no logic). `effective_relationships()` is the one new function carrying lowering + union + fail logic.
- `contracts/harness/task-control/` schemas: proven Draft 2020-12 per-record shape + the contract-hash/drift ratification wiring the new `contracts/harness/topology/relationship.schema.json` plugs into with no new machinery.
- `harness/project.toml` `BEGIN/END PIPE-01 topology` markers + consumer-comment convention: the new slot should carry the same "Pure DATA, no enforcement / Consumers:" documentation posture.

### Established Patterns
- **Data-only config slots** — enforcement never lives in `project.toml`/`workspace.toml`; it lives in `harness_lint` gates. Phase 24 adds DATA + a thin accessor; validation logic stays out (compiler is Phase 25).
- **Contract-first ratification** — a new schema is a constitution-plane change: it lands with positive/negative fixtures through the hash/drift gate (machines gate, humans ratify).
- **Additive union, not migration** — `effective_relationships()` *lowers* legacy `[pipeline]` and *unions*; it never rewrites or requires editing existing linear configs (byte-unchanged invariant).

### Integration Points
- `[[contract_graph.relationships]]` reads flow into: Phase 25 compiler/queries, Phase 26 brownfield mapper vocabulary, and (via lowering) the existing `/pipeline` trace. Keep the accessor return shape stable — three downstream consumers bind to it.

</code_context>

<specifics>
## Specific Ideas

- Namespaced lowered ids (`pipeline/<contract>/<from>-><to>`) are the recommended collision-avoidance scheme so lowered vs explicit records never clash in the union — see D-04.
- The generic-default topology (two-stage `source`→`sink` carrying `greeting`) is the byte-unchanged regression fixture for TOPO-03: after lowering, its effective relationships must be derivable with zero config edits.

</specifics>

<deferred>
## Deferred Ideas

- **Compiler, `harness_lint` consistency gate, endpoint/authority resolution validation** — Phase 25 (TOPO-04).
- **Affected-set queries (direct/reverse/transitive, cycle-safe)** — Phase 25 (TOPO-05).
- **`/pipeline`·`pipeline-map`·orchestrator generalization + byte-identical re-emit** — Phase 25 (TOPO-06).
- **Non-linear generic + cross-repo proof fixtures + topology ADR-0009 ratification** — Phase 25 (TOPO-07).
- **version/semver compatibility engine, topology runtime/broker, second orchestrator** — OUT of scope for milestone v2.3 (PROJECT.md).

None of the above is dropped — each is already owned by a later phase or explicitly out-of-scope.

</deferred>

---

*Phase: 24-Contract-Relationship Vocabulary + Compatibility*
*Context gathered: 2026-07-19*
