---
phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
reviewed: 2026-07-19T07:03:48Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - tools/contract_graph/compile.py
  - tools/contract_graph/query.py
  - tools/contract_graph/__init__.py
  - tools/harness_config/loader.py
  - tools/harness_lint/tests/test_contract_graph_config.py
  - harness/commands/pipeline.md
  - harness/skills/pipeline-map/SKILL.md
  - harness/agents/orchestrator.md
  - docs/adr/0009-contract-relationship-graph-model.md
findings:
  critical: 1
  warning: 1
  info: 2
  total: 4
status: issues_found
---

# Phase 25: Code Review Report

**Reviewed:** 2026-07-19T07:03:48Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed the TOPO-04/05/06 graph compiler, query layer, lazy re-export shim, the extended
`effective_relationships()` loader guard, the consistency gate, and the three conductor prose
surfaces against ADR-0009. The intentional scope decisions ratified in ADR-0009 (compiler-on-top of
`effective_relationships()`, returned-not-raised diagnostics, `{ids, paths}` cycle-safe queries with
no file I/O, legal non-linear shapes, deferred WR-01, closed WR-02) were verified and are NOT
flagged.

One real correctness defect was found: the adjacency builder in `compile_graph` does not
de-duplicate dependents, so a **legal** topology — the same authority pointing at the same dependent
via two *distinct* contracts — produces a duplicated adjacency entry, which then makes `direct()` and
`reverse()` return duplicate `ids` and duplicate `paths`. This is provably wrong output for valid
input and is not exercised by any current fixture (core/workspace defaults stay green), so the gate
does not catch it. Remaining findings are a robustness gap inconsistent with the ratified WR-02
principle and two prose-accuracy nits.

## Critical Issues

### CR-01: `compile_graph` adjacency is not de-duplicated — duplicate dependents corrupt `direct()`/`reverse()`

**File:** `tools/contract_graph/compile.py:115-121` (build), consumed at `tools/contract_graph/query.py:35-36` and `46-52`
**Issue:**
The adjacency row is built by unconditional `list.extend` and only *sorted* on return — never
de-duplicated:

```python
if resolved_dependents:
    adjacency.setdefault(authority, [])
    adjacency[authority].extend(resolved_dependents)
...
"adjacency": {k: sorted(adjacency[k]) for k in sorted(adjacency)},
```

`effective_relationships()` only rejects a *duplicate `(authority, contract, dependent)` triple* and
a *contract claimed by two authorities*. It does NOT reject two records that share an
`(authority, dependent)` pair but carry **different contracts** — that is a legal shape (one producer
emitting two distinct contracts, both consumed by the same downstream). Both records resolve, and
`extend` appends the same dependent twice.

Concrete reproduction (all constraints satisfied, zero `ValueError`):

```python
cfg = {
    "components": [
        {"id": "a", "produces": ["c1", "c2"], "consumes": []},
        {"id": "b", "produces": [], "consumes": ["c1", "c2"]},
    ],
    "contract_graph": {"relationships": [
        {"id": "r1", "contract": "c1", "authority": "a", "dependents": ["b"]},
        {"id": "r2", "contract": "c2", "authority": "a", "dependents": ["b"]},
    ]},
}
g = compile_graph(cfg)
# g["adjacency"] == {"a": ["b", "b"]}          <-- duplicate dependent
direct(g, "a")   # {"ids": ["b", "b"], "paths": [["a", "b"], ["a", "b"]]}  <-- duplicated
reverse(g, "b")  # {"ids": ["a", "a"], "paths": [["b", "a"], ["b", "a"]]}  <-- duplicated
```

This violates the documented adjacency contract ("authority -> sorted[dependents]", set-semantics
implied) and the D-03 query contract (sorted `ids`). Downstream conductor routing consuming these
`ids`/`paths` would double-count an affected component. (`transitive()` is unaffected — its
visited-set skips the second occurrence — which further hides the defect from the existing tests.)

**Fix:** De-duplicate at the single source (the adjacency build) so all three query consumers are
correct:

```python
if resolved_dependents:
    adjacency.setdefault(authority, set()).update(resolved_dependents)
...
"adjacency": {k: sorted(adjacency[k]) for k in sorted(adjacency)},
```

(Use a `set` accumulator, or `sorted(set(adjacency[k]))` on return.) Add a regression test for the
two-distinct-contracts-same-edge shape, which no current fixture covers.

## Warnings

### WR-01: New unguarded `member["root"]` index reintroduces the bare-`KeyError` failure mode WR-02 closed

**File:** `tools/contract_graph/compile.py:156`
**Issue:**
`_contract_ownership_diagnostic` indexes `member_by_id[resolved_id]["root"]` with no guard. ADR-0009
records **WR-02 (closed)** as a ratified principle: a malformed record must surface an *actionable
`ValueError` naming the offending record*, "replacing the previous bare `KeyError`." The loader was
hardened accordingly (`loader.py:117-136`), but the new compiler code — sitting in the same topology
subsystem and operating on the same raw-passthrough config (`members()` is explicitly "NO enforcement
here") — introduces a fresh bare-`KeyError` path: a member declaration missing `root` crashes with an
opaque `KeyError: 'root'` instead of a descriptive diagnostic or a named `ValueError`. Relationship
keys (`id`/`contract`/`authority`/`dependents`) are protected because `effective_relationships()`
guards them upstream, but `member["root"]` is not.

**Fix:** Guard the lookup consistently with the WR-02 pattern, e.g.:

```python
member = member_by_id[resolved_id]
if "root" not in member:
    raise ValueError(
        f"compile_graph: member {resolved_id!r} missing 'root' (relationship {rel['id']})"
    )
member_root = _REPO_ROOT / member["root"]
```

## Info

### IN-01: ADR-0009 "component/member carrying a `produces` list" over-states the implementation

**File:** `docs/adr/0009-contract-relationship-graph-model.md:74-80` vs `tools/contract_graph/compile.py:144-158`
**Issue:**
The ADR states ownership uses a produces-check "when the authority endpoint resolves to a declared
**component/member** carrying a `produces` list." The implementation applies the produces-check only
for `kind == "component"`; a `member` authority *always* takes the existence-only path, ignoring any
`produces` field it might carry. Today this has no functional impact — the `[[members]]` shape
(`workspace_config.members`) carries only `id` + `root`, never `produces` — so the code is correct
for every reachable config. But the ADR wording implies members participate in the produces-check,
which they do not.
**Fix:** Tighten the ADR sentence to "a declared **component** carrying a `produces` list" (members
are opaque cross-repo roots resolved existence-only), or add a code comment noting members are
existence-only by definition.

### IN-02: Tree-render prose over-claims parity with `transitive`'s visited discipline

**File:** `harness/commands/pipeline.md:110-113` and `harness/skills/pipeline-map/SKILL.md:87-90`
**Issue:**
Both surfaces describe the indented-tree cycle guard as "the exact visited-set-before-recurse
discipline `tools.contract_graph.query.transitive` uses." The concrete instruction is correct — track
the visited set **on the current root-to-node path** (path-local). But `transitive` uses a single
**global** visited set (a node reached once is never revisited on any path). The two disciplines
differ: an implementer who literally reuses `transitive`'s global-visited approach for the tree would
wrongly collapse a legal diamond (a→b, a→c, b→d, c→d), printing `d` under only one parent and losing
the other branch. The termination property is shared; the visited *scope* is not.
**Fix:** Drop the "exact same discipline" analogy or qualify it: "the same visited-before-recurse
*termination* guarantee, but scoped to the current path (not the global visited set `transitive`
uses)."

---

_Reviewed: 2026-07-19T07:03:48Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
