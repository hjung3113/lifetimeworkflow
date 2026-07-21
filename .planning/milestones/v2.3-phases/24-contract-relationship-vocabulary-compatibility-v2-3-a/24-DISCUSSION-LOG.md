# Phase 24: Contract-Relationship Vocabulary + Compatibility - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-19
**Phase:** 24-Contract-Relationship Vocabulary + Compatibility
**Mode:** `--auto --chain` (autonomous discuss, recommended defaults selected; auto-advance to plan)
**Areas discussed:** Schema granularity, Endpoint reference shape, Additive TOML slot + accessor, Legacy pipeline lowering, Failure taxonomy

---

## Schema granularity & file layout

| Option | Description | Selected |
|--------|-------------|----------|
| Record-level schema | One `relationship.schema.json` validating a single relationship object; array consistency deferred to Phase 25 compiler | ✓ |
| Graph-document schema | One schema wrapping the whole relationships array with uniqueness/resolution constraints | |

**Selected:** Record-level schema (recommended default).
**Notes:** Mirrors existing `contracts/harness/task-control/*.schema.json` per-record pattern; keeps Phase 24 to vocabulary only. Positive/negative fixtures are instance files through the existing hash/drift path.

---

## Endpoint reference shape

| Option | Description | Selected |
|--------|-------------|----------|
| Bare stable-id strings | `authority` = single string, `dependents` = non-empty string array; schema enforces shape/cardinality only | ✓ |
| Structured endpoint objects | Endpoints as `{component, role, ...}` objects with richer metadata in the schema | |

**Selected:** Bare stable-id strings (recommended default).
**Notes:** Existence/resolution validation deferred to the Phase 25 compiler — Phase 24 stays pure vocabulary. Schema enforces exactly-one authority + ≥1 dependent.

---

## Additive TOML slot + accessor

| Option | Description | Selected |
|--------|-------------|----------|
| 1:1 mirror + raw passthrough | `[[contract_graph.relationships]]` mirrors schema fields; `contract_graph_relationships()` returns raw `list[dict]`, zero logic | ✓ |
| Accessor with light validation | Accessor validates/normalizes records on read | |

**Selected:** 1:1 mirror + raw passthrough (recommended default).
**Notes:** TOPO-02 mandates pure-DATA posture with no validation/traversal/discovery — mirrors existing `pipeline()`/`components()`. Existing loader signatures stay untouched; project AND workspace TOML accept the slot.

---

## Legacy `[pipeline].edges` lowering

| Option | Description | Selected |
|--------|-------------|----------|
| authority=from, dependents=[to], namespaced id | Producer owns contract; synth id namespaced (`pipeline/<contract>/<from>-><to>`) to avoid collision with explicit ids | ✓ |
| authority=to (consumer-owned) | Invert ownership so the consuming side is authority | |

**Selected:** authority=from + namespaced synthesized id (recommended default).
**Notes:** Producer-owns-contract matches the existing produces/consumes semantics. Namespacing prevents lowered/explicit id collision in the `effective_relationships()` union.

---

## Failure taxonomy for `effective_relationships()`

| Option | Description | Selected |
|--------|-------------|----------|
| dup-id + dup-semantic + contradiction | Fail on duplicate id, duplicate `(authority,contract,dependent)` triple, or one contract with two authorities | ✓ |
| dup-id only | Fail only on duplicate id; allow semantic overlaps | |

**Selected:** Three-way taxonomy (recommended default).
**Notes:** Deterministic stable diagnostic. Linear fixtures carry no explicit records → lowering-only → byte-unchanged invariant preserved (TOPO-03 exit criterion).

---

## Claude's Discretion

- Exact synthesized-id delimiter/format and diagnostic message wording (must stay deterministic and stable-sortable).
- Whether `contracts/harness/topology/` gains a sibling README alongside the record schema.

## Deferred Ideas

- Compiler + `harness_lint` consistency gate + endpoint/authority resolution → Phase 25 (TOPO-04).
- Cycle-safe affected-set queries → Phase 25 (TOPO-05).
- `/pipeline`·`pipeline-map`·orchestrator generalization + byte-identical re-emit → Phase 25 (TOPO-06).
- Non-linear + cross-repo proof fixtures + topology ADR-0009 ratification → Phase 25 (TOPO-07).
- version/semver engine, topology runtime/broker, second orchestrator → out of scope (v2.3 PROJECT.md).
