# Phase 25: Graph Compiler, Queries, Conductor, Proof - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-19
**Phase:** 25-Graph Compiler, Queries, Conductor, Proof
**Mode:** `--chain` (interactive discuss, then auto-advance to plan+execute)
**Areas discussed:** Conductor rendering, Diagnostic code format, Query output shape, ADR-0009 scope

---

## Conductor rendering of non-linear graphs

| Option | Description | Selected |
|--------|-------------|----------|
| Indented tree | authority→dependents indented tree; cycle marker `(cycle → node)`; closest to current linear render → byte-identical preserved | ✓ |
| Edge-list | one `authority → dependent (contract)` line each; flat, no hierarchy | |
| Adjacency map | per-node neighbor list; good for machine queries, poor human flow | |

**Selected:** Indented tree (recommended).
**Notes:** TOPO-06 requires existing linear output byte-identical; the tree degrades to the current line for linear topologies. An adjacency structure may still exist internally for queries (D-03).

---

## Consistency-gate diagnostic code format

| Option | Description | Selected |
|--------|-------------|----------|
| Descriptive slug | `unresolved-authority`, `dangling-endpoint`, `unknown-contract`; matches GEN-04/POLY-01/GEN-03 | ✓ |
| Numbered code | `TOPO-C001` style; stable but needs a lookup table | |

**Selected:** Descriptive slug (recommended).
**Notes:** Self-documenting in CI output; consistent with the repo's existing harness_lint diagnostic style.

---

## Affected-set query output shape

| Option | Description | Selected |
|--------|-------------|----------|
| ids + path | sorted related ids AND connecting path(s); cycle-safe via visited-set | ✓ |
| ids only | sorted id set only; no "why impacted" path | |

**Selected:** ids + path (recommended).
**Notes:** Both conductor routing and doc reports need the path. Invariant (TOPO-05): queries create no new task-evidence requirement and do not preload contract bodies.

---

## ADR-0009 scope

| Option | Description | Selected |
|--------|-------------|----------|
| model + queries + conductor | record/graph model + affected-set query semantics + conductor rendering contract | ✓ |
| model only | record/graph model only; queries/conductor left as impl detail | |

**Selected:** model + queries + conductor (recommended).
**Notes:** All three land together this phase and Phases 26–29 depend on the whole surface; fix as one ratified unit. ADR-0009 reserved in Phase 24, authored + human-ratified here.

---

## Claude's Discretion

- Compiler module location, internal graph data structure, exact slug spellings, query function signatures.
- Indented-tree glyphs + cycle-marker wording (provided linear output stays byte-identical).

## Deferred Ideas

- Brownfield adoption (ADOPT-*) → Phases 26–27.
- Living Docs (DOCSUP-*) → Phases 28–29 (consume this phase's affected-set queries).
- version/semver engine, topology runtime/broker, second orchestrator, impact-driven task-evidence policy → out of scope (v2.3).
