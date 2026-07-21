# Phase 25: Graph Compiler, Queries, Conductor, Proof - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the general contract-relationship graph **usable** through ONE deterministic implementation and the EXISTING user-facing topology surface — no new command, no new persona, no second interpreter. Owns TOPO-04, TOPO-05, TOPO-06, TOPO-07. Delivers exactly:

1. **TOPO-04** — A domain-neutral **compiler** + a `harness_lint` **consistency gate**. Emits stably-ordered, repo-confined graph data + stable diagnostic codes; validates endpoints and authority-owned-contract resolution; accepts fan-in, fan-out, disconnected components, and canonical cycles.
2. **TOPO-05** — **Affected-set queries** (direct / reverse / transitive) that terminate on cycles and return deterministically ordered ids + paths, for conductor routing and documentation reports — without selecting new task-evidence requirements or preloading contract bodies.
3. **TOPO-06** — Generalize the EXISTING `orchestrator`, `/pipeline`, and `pipeline-map` skill to consume the canonical graph: preserve the locked linear rendering byte-identical, render branches/cycles safely, round-trip `harness/` → both runtimes byte-identical, no new graph command or persona.
4. **TOPO-07** — Domain-neutral proof: generic project/workspace fixtures proving shared-contract fan-out, request/response as separate records, event fan-out, a legal cycle, and cross-repo authority resolution; log-parser instance unchanged; GEN-04 twins green; a human-ratified topology **ADR-0009** records the model.

**Builds directly on Phase 24 (shipped):** the ratified `relationship.schema.json`, the additive `[contract_graph]` slot, and `tools/harness_config/loader.py::effective_relationships()` (lowering + additive union, already sorted-by-id, already raising on the 3 failure modes). Phase 25 consumes that single path — it does NOT re-implement lowering/union.

</domain>

<decisions>
## Implementation Decisions

Interactive discussion (--chain). Four user-facing gray areas locked; the rest (compiler module location, gate internals, fixture file layout, code structure) is researcher/planner territory.

### Conductor rendering of non-linear graphs
- **D-01:** `/pipeline` and `pipeline-map` render the graph as an **indented tree** rooted at authority endpoints descending to dependents. A cycle is rendered with an explicit terminal marker (e.g. `(cycle → <node>)`) rather than recursing. Rationale: closest structural match to the current linear render, so the **existing linear topology output stays byte-identical** (TOPO-06 hard requirement); best human readability for following data flow. NOT edge-list, NOT adjacency-map for the human-facing surface (an adjacency structure may still exist internally for queries — see D-03).

### Consistency-gate diagnostic codes
- **D-02:** Diagnostics are **descriptive, grep-able slugs** (e.g. `unresolved-authority`, `dangling-endpoint`, `unknown-contract`), matching the existing `harness_lint` gate convention (GEN-04, POLY-01, GEN-03). Stable across runs. NOT numbered `TOPO-C001`-style codes — the descriptive form is self-documenting in CI output and consistent with the repo's established diagnostic style.

### Affected-set query output shape
- **D-03:** Queries return **sorted ids AND the connecting path(s)** — not ids alone. Both consumers need paths: conductor routing and documentation reports explain *why* a node is impacted. Cycle-safe via a visited-set so traversal terminates on legal cycles. Deterministic ordering. Queries return ids/paths ONLY — they create **no new task-evidence requirement** and **do not preload contract bodies** (TOPO-05 invariant; keeps this independent of the task-control evidence plane).

### ADR-0009 scope
- **D-04:** ADR-0009 records the **full model landed this phase**: the record/graph model + the affected-set query semantics + the conductor rendering contract. Rationale: all three ship together in Phase 25 and Phases 26–29 depend on the whole surface, so the decision record fixes them as one ratified unit. (ADR-0009 was reserved but NOT created in Phase 24 — it is authored and human-ratified HERE.)

### Carried forward from Phase 24 (do not re-decide)
- Namespaced lowered ids `pipeline/<contract>/<from>-><to>`; endpoints are **opaque strings** (no `split_endpoint`, no `repo:stage` parsing at the vocabulary layer — but endpoint RESOLUTION against declared components/members is exactly TOPO-04's new job this phase).
- `effective_relationships()` is the single lowering+union path; stable sort-by-id; raises `ValueError` on duplicate id / duplicate semantic edge / contradiction.

### Claude's Discretion
- Compiler module location (extend `tools/harness_config/` vs a new `tools/contract_graph/` module), internal graph data structure (adjacency map is fine internally even though D-01 fixes the human-facing render), exact slug spellings, and query function signatures — planner/researcher decide, provided outputs are deterministic and repo-confined.
- Exact indented-tree glyphs and the cycle-marker wording, provided the existing linear output is byte-identical.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Ratified design + requirements (authoritative)
- `.planning/research/v2.3-scoping-FINAL.md` — §"Theme A" (TOPO-04..07) + §"Phase 25 — Graph Compiler, Queries, Conductor, and Proof" (Goal, Owns, Exit).
- `.planning/REQUIREMENTS.md` — TOPO-04, TOPO-05, TOPO-06, TOPO-07 (owned 1:1 by this phase).
- `.planning/ROADMAP.md` — "### Phase 25" (4 observable success criteria + `Depends on: Phase 24`).

### Phase 24 output this phase consumes (read to avoid re-implementing)
- `.planning/phases/24-contract-relationship-vocabulary-compatibility-v2-3-a/24-CONTEXT.md` — the locked vocabulary decisions D-01..D-05.
- `.planning/phases/24-contract-relationship-vocabulary-compatibility-v2-3-a/24-01-SUMMARY.md` + `24-02-SUMMARY.md` — what shipped (schema, slot, accessors, `effective_relationships()`).
- `contracts/harness/topology/relationship.schema.json` — the ratified record the compiler validates against.
- `tools/harness_config/loader.py` — `effective_relationships()` (lines ~90–176: lowering + union + 3 failure modes, sort-by-id) and `contract_graph_relationships()`; the compiler/queries consume THIS, signatures stay stable.

### Surfaces to generalize (TOPO-06 — must round-trip byte-identical, no model ids)
- `harness/commands/pipeline.md` — the `/pipeline` command source.
- `harness/skills/pipeline-map/SKILL.md` — the pipeline-map skill.
- `harness/agents/orchestrator.md` — the single orchestrator persona (no new persona allowed).

### Gate reuse + GEN-04 (do not fork)
- `tools/harness_lint/tests/test_pipeline_config.py` + `test_orchestrator_topology.py` + `test_workspace_config.py` — existing topology consistency gates the new gate extends.
- `tools/contract_drift/drift.py` — the drift check to REUSE for authority-owned-contract resolution (TOPO-04); do not re-implement contract existence checks.
- `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 guard; any new test referencing the log-parser instance path builds it via non-contiguous `Path` segments (see Phase 24 precedent).

### Decision record to author (TOPO-07)
- `docs/adr/` — **ADR-0009 is authored and human-ratified in THIS phase** (reserved in Phase 24, highest existing is ADR-0008). Scope per D-04.

### Advisory items carried from Phase 24 review (optional to fold in)
- `.planning/phases/24-.../24-REVIEW.md` — WR-01 (lowered-id non-injectivity when endpoint/contract ids contain `/` or `->`) and WR-02 (bare `KeyError` vs `ValueError` on malformed records). Not required here, but the compiler/gate touching this code path is the natural place to close them if the planner chooses.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/harness_config/loader.py::effective_relationships()` — already produces the canonical, deduped, sorted relationship list the compiler compiles from. The compiler = validation/resolution layer ON TOP; do not duplicate lowering/union.
- `tools/contract_drift/drift.py` — RFC-8785 hash/drift machinery; reuse for authority-owned-contract resolution instead of a new contract-existence check.
- `tools/harness_lint/tests/test_*_config.py` + `test_orchestrator_topology.py` — the consistency-gate posture (stable-string diagnostics, repo-confined) the new gate mirrors.
- `harness/commands/pipeline.md`, `harness/skills/pipeline-map/SKILL.md`, `harness/agents/orchestrator.md` — the three surfaces to generalize; they re-emit to `.opencode/` + `.claude/` via the harness-emit round-trip (must stay byte-identical, no model ids).

### Established Patterns
- **Single deterministic implementation** — one compiler + one query module; conductor surfaces CONSUME it, never re-interpret the graph (TOPO-06).
- **Descriptive stable diagnostics** — GEN-04 / POLY-01 / GEN-03 slug style (D-02).
- **Reuse drift, don't fork** — authority→contract resolution rides existing drift checks (TOPO-04).
- **GEN-04 one-way core→example** — new fixtures/tests in the test plane; non-contiguous `Path` segments for instance references.

### Integration Points
- Compiler/query output feeds: conductor routing (orchestrator), `/pipeline`+pipeline-map render (D-01 indented tree), Phase 28–29 Living-Docs graph-impact reports (DOCSUP), and Phase 26 brownfield mapper vocabulary.

</code_context>

<specifics>
## Specific Ideas

- Indented-tree render with `(cycle → <node>)` terminal marker (D-01); existing linear output must diff byte-identical.
- Queries return `{ids: [...sorted], paths: [[...]]}`-shaped results (D-03) — path present for both conductor routing and doc reports.
- Generic non-linear proof fixtures (TOPO-07): shared-contract fan-out, request+response as two separate records, event fan-out, one legal cycle, cross-repo authority resolution — all domain-neutral, log-parser instance untouched.

</specifics>

<deferred>
## Deferred Ideas

- **Brownfield adoption (ADOPT-*)** — Phases 26–27.
- **Living Docs (DOCSUP-*)** — Phases 28–29 (consume this phase's affected-set queries for graph-impact reports).
- **version/semver compatibility engine, topology runtime/broker, second orchestrator, impact-driven task-evidence policy** — OUT of scope for v2.3 (PROJECT.md); D-03 explicitly forbids the query layer from creating task-evidence requirements.

None dropped — each owned by a later phase or explicitly out-of-scope.

</deferred>

---

*Phase: 25-Graph Compiler, Queries, Conductor, Proof*
*Context gathered: 2026-07-19*
