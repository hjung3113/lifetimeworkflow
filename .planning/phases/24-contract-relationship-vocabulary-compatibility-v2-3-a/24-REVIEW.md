---
phase: 24-contract-relationship-vocabulary-compatibility-v2-3-a
reviewed: 2026-07-19T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - contracts/harness/topology/relationship.schema.json
  - contracts/.hashes/manifest.json
  - harness/project.toml
  - workspace.toml
  - tools/harness_config/loader.py
  - tools/harness_config/__init__.py
  - tools/harness_config/tests/fixtures/relationships/valid/cases.json
  - tools/harness_config/tests/fixtures/relationships/negative/cases.json
  - tools/harness_config/tests/test_relationship_schema.py
  - tools/harness_config/tests/test_topology_relationships.py
  - tools/workspace_config/loader.py
  - tools/workspace_config/__init__.py
  - tools/docs_sync/tests/test_docs_sync_determinism.py
  - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
  - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 24: Code Review Report

**Reviewed:** 2026-07-19
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

This phase adds the contract-relationship vocabulary: a Draft 2020-12 record schema
(`relationship.schema.json`), two raw-passthrough accessors
(`contract_graph_relationships` on both loaders), and the deterministic lowering/union function
`effective_relationships`. The DATA slots in `harness/project.toml` and `workspace.toml` are empty
by default, and the drift/docs derived artifacts (manifest hash, docs-sync + contracts-index
snapshots) are all in sync — I recomputed the RFC-8785 canonical hash of the new schema and it
matches `contracts/.hashes/manifest.json` (`27377a88…`).

Verified as correct (do not "fix"): the schema shape is well-formed — `additionalProperties:false`,
`required` covers the four mandatory fields, `authority` is a scalar string (not an array),
`dependents` has `minItems:1` + `uniqueItems:true`, and every negative fixture maps 1:1 to exactly
one violated constraint. Endpoints are correctly treated as opaque strings (no `split_endpoint`).
Existing loader signatures are unchanged (TOPO-02 held). The three-mode failure taxonomy
(duplicate id / duplicate semantic triple / contradiction) is logically correct and its diagnostics
are stable-sorted, so output ordering is deterministic. The `sorted(contradictions.items())` call is
safe despite the set values because dict contract keys are unique, so tuple comparison never reaches
the unorderable `set` element.

The two findings below concern the lowered-id construction and the exception type on malformed input.

## Warnings

### WR-01: Lowered relationship `id` is built by non-injective string interpolation — distinct edges can collide, and the "can never collide" guarantee is false

**File:** `tools/harness_config/loader.py:117-125` (also docstring claim at lines 96-98)

**Issue:** The lowered id is `f"pipeline/{edge['contract']}/{edge['from']}->{edge['to']}"`. Because
`contract`, `from`, and `to` are explicitly documented as OPAQUE strings passed through verbatim
(they may contain `/`, `:`, or the literal `->` separator — e.g. workspace endpoints are `repo:stage`),
the mapping from an edge triple to an id string is not injective. Two semantically distinct edges can
produce the same id:

```
{from: "a",    to: "b->c", contract: "x"}  ->  "pipeline/x/a->b->c"
{from: "a->b", to: "c",    contract: "x"}  ->  "pipeline/x/a->b->c"   # collision
```

A `/` inside a contract id causes the same class of collision. When this happens, `effective_relationships`
raises a *false* `duplicate relationship id` `ValueError` for two edges that are not actually duplicates.
Separately, the docstring asserts the `pipeline/…` namespace "can never collide with a human-authored
explicit id" — this is not enforced anywhere; an explicit record whose author writes `id = "pipeline/…"`
collides identically. The guarantee is aspirational, not structural.

Impact is bounded (a spurious error, never silent data loss — the duplicate-id gate always fires), and
today's default endpoints (`source`/`sink`, `member-a:emit`) don't hit it, so this is a WARNING rather
than a BLOCKER. But it is a latent correctness trap the moment an instance uses an endpoint or contract
id containing `/` or `->`.

**Fix:** Either (a) build the id from a delimiter that cannot appear in the components (or percent-/JSON-encode
each component before joining), or (b) if the namespacing claim is meant to hold, soften the docstring and
rely solely on the duplicate-id detection instead of asserting impossibility. Example for (a):

```python
import json
lowered = [
    {
        "id": "pipeline/" + json.dumps(
            [edge["contract"], edge["from"], edge["to"]], separators=(",", ":")
        ),
        "contract": edge["contract"],
        "authority": edge["from"],
        "dependents": [edge["to"]],
    }
    for edge in cfg.get("pipeline", {}).get("edges", [])
]
```

### WR-02: `effective_relationships` raises bare `KeyError` (not a diagnostic `ValueError`) on a malformed edge/record missing a required key

**File:** `tools/harness_config/loader.py:117-152`

**Issue:** The lowering comprehension indexes edges with `edge['contract']`, `edge['from']`, `edge['to']`,
and the dedup loops index records with `rel["id"]`, `rel["authority"]`, `rel["contract"]`, `rel["dependents"]`.
An explicit `[[contract_graph.relationships]]` record (or a `[pipeline].edges` entry) that is missing any of
these keys — a real possibility since `effective_relationships` performs no schema validation and can run on
raw TOML before any Phase-25 resolution — raises an uncaught `KeyError` with an opaque message (e.g. `KeyError: 'authority'`),
crashing instead of surfacing which record was malformed. The docstring documents only three `ValueError`
failure modes; this fourth crash path is undocumented and gives the operator no actionable diagnostic. This is
distinct from the deliberately-deferred endpoint/graph *resolution* — it is the lowering step itself failing
ungracefully on malformed local shape.

**Fix:** Guard the required keys and raise a `ValueError` naming the offending record, e.g.:

```python
for rel in merged:
    missing = {"id", "contract", "authority", "dependents"} - rel.keys()
    if missing:
        raise ValueError(
            f"effective_relationships: relationship record missing key(s) {sorted(missing)}: {rel!r}"
        )
```

(Or apply the equivalent guard to raw edges before lowering.) If malformed-shape handling is genuinely intended
to be out of scope for this phase, document the `KeyError` contract explicitly instead of leaving it implicit.

## Info

### IN-01: `contract_graph_relationships` is duplicated verbatim across both loaders

**File:** `tools/workspace_config/loader.py:67-77` and `tools/harness_config/loader.py:77-87`

**Issue:** The two accessors are byte-for-byte identical logic (`list(cfg.get("contract_graph", {}).get("relationships", []))`).
This mirrors the pre-existing `edges`/`pipeline` duplication between the two loaders, so it is consistent with the
established two-loader pattern rather than a new smell — but it does mean a future change to the accessor shape must
be made in two places.

**Fix:** Acceptable as-is given the existing convention. If consolidation is ever desired, extract a shared
`_two_level_get(cfg, "contract_graph", "relationships")` helper; otherwise leave a note that the two copies must
stay in lockstep.

### IN-02: Negative schema fixtures don't cover wrong-type violations (`authority` as array, non-string dependent)

**File:** `tools/harness_config/tests/fixtures/relationships/negative/cases.json:1-54`

**Issue:** The negative suite covers missing-required, empty/duplicate dependents, and additional-property, but not
type violations — notably `authority` supplied as an array (the exact "exactly ONE authority, not an array" invariant
the schema description calls out) or a non-string dependent item. The schema does enforce these via `type`, so the
constraint is protected; the gap is only in the regression net proving it stays protected.

**Fix:** Add two negative fixtures — `authority` as `["a","b"]` and `dependents` as `[1]` — to lock the cardinality/type
guarantees against future schema edits.

---

_Reviewed: 2026-07-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
