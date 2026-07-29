---
phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
plan: 02
subsystem: infra
tags: [contract-graph, topology, queries, affected-set, cycle-safe, determinism, TOPO-05]

# Dependency graph
requires:
  - phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
    plan: 01
    provides: "compile_graph(cfg) -> {relationships, adjacency, diagnostics}; the adjacency map this plan queries"
provides:
  - "tools/contract_graph/query.py: direct/reverse/transitive over the compiled adjacency -> {ids: sorted, paths: [...]}"
  - "Cycle-safe transitive() via the iterative visited-set worklist (Pattern 2) — O(nodes+edges), deterministic"
  - "D-03 return contract: sorted ids AND connecting paths (never ids alone), 1-hop paths for direct/reverse"
  - "Structural D-03 invariant proof: query.py imports no task-evidence plane + performs no file I/O"
affects: [plan-25-03-conductor, plan-25-04-proof, TOPO-06, TOPO-07, DOCSUP]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Consume-the-compiled-graph: queries read graph['adjacency'] only, never re-resolve endpoints or re-walk config"
    - "Cycle-safe iterative worklist: visited-check BEFORE enqueue is the sole termination guarantee (no recursion)"
    - "Deterministic traversal: neighbours visited in sorted order so first-found paths are byte-identical across runs"
    - "Structural invariant as an automatable test: assert forbidden import/IO substrings absent from the module source"

key-files:
  created:
    - tools/contract_graph/query.py
    - tools/contract_graph/tests/test_query.py
  modified:
    - tools/contract_graph/__init__.py

key-decisions:
  - "reverse() builds a transposed adjacency (dependent -> [authorities]) once per call, then returns sorted predecessors — no per-call O(n^2) rescan of edges"
  - "transitive() returns the reachable set EXCLUDING the start node; each id carries its first-found (BFS) path from the start"
  - "__init__ PEP-562 __getattr__ now routes each re-exported name to its owning submodule (compile_graph->compile, direct/reverse/transitive->query) via a name->module map — the Plan-01 delegate-only-to-compile shape could not serve query names"

patterns-established:
  - "The D-03 no-task-evidence/no-contract-preload invariant is proven STRUCTURALLY (source-text assertion), not by subjective review"

requirements-completed: [TOPO-05]

# Metrics
duration: ~20min
completed: 2026-07-19
---

# Phase 25 Plan 02: Cycle-Safe Affected-Set Query Layer Summary

**`direct`/`reverse`/`transitive` over the compiled contract-graph adjacency — each returning sorted ids AND the connecting path(s) (D-03), with cycle-safe iterative traversal, byte-identical determinism, and a structural proof that the query layer touches neither the task-evidence plane nor the filesystem.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-19
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `tools/contract_graph/query.py` implements the three TOPO-05 affected-set shapes purely over `compile_graph()`'s `adjacency` dict — no re-resolution of endpoints, no re-walking of raw config.
- `direct(graph, node)` returns sorted one-hop dependents with `[node, dep]` paths; `reverse(graph, node)` transposes the adjacency once (`dependent -> [authorities]`) and returns sorted predecessors with `[node, pred]` paths.
- `transitive(graph, node)` uses the research Pattern-2 iterative visited-set worklist (visited-check BEFORE enqueue) — a legal cycle terminates in O(nodes+edges) with no recursion, no stack-overflow, no double-counting. Neighbours are visited in sorted order, so the first-found path recorded for each reached node is byte-identical across runs.
- All three return the D-03 shape `{"ids": [...sorted...], "paths": [[...]]}` where `paths[i]` corresponds to `ids[i]` and starts at the query node — ids AND connecting paths, never ids alone. An isolated/disconnected node yields `{"ids": [], "paths": []}` (never `KeyError`).
- The D-03 no-task-evidence/no-contract-preload invariant is proven by two STRUCTURAL tests that read `query.py`'s source text and assert the forbidden import substrings (`tools.task_packet`/`tools.evidence`/`tools.task_control`/`tools.handoff`) and the file-I/O substrings (`open(`, `.read_text(`) are absent — the query layer's blast radius is bounded to pure in-memory traversal (mitigates T-25-03 DoS and T-25-04 scope-creep from the threat register).
- 9 query tests green; full `tools/contract_graph` package (compile + query) 18 green; full suite 947 passed; contract-drift OK; new files ruff-clean.

## Task Commits

1. **Task 1 (feat): cycle-safe direct/reverse/transitive query layer** — `c5e9d74`
2. **Task 2 (test): determinism, cycle-safety, D-03 no-evidence structural invariant** — `fb7b945`

## Files Created/Modified

- `tools/contract_graph/query.py` - The query layer: `direct`/`reverse`/`transitive` over the compiled adjacency, cycle-safe worklist, `{ids, paths}` D-03 shape.
- `tools/contract_graph/tests/test_query.py` - 9 tests: 5 behavior (direct/reverse, 2-node cycle, diamond, determinism) + 4 structural/robustness (no task-evidence import, no file I/O, twin cycles terminate, isolated-node empty result).
- `tools/contract_graph/__init__.py` - PEP-562 `__getattr__` extended to route `direct`/`reverse`/`transitive` to the `query` submodule (kept `compile_graph` -> `compile`).

## Decisions Made

- `reverse()` transposes the adjacency once per call rather than rescanning edges per predecessor, keeping it linear in edge count.
- `transitive()` excludes the start node from `ids` and records the first-found (BFS) path per reached node.
- The `__init__` re-export map was widened to key each name to its owning submodule; the Plan-01 shape delegated every name to `compile` and would have raised `AttributeError` for the query names.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `__init__.py` PEP-562 delegate had to be widened to route query names**
- **Found during:** Task 1
- **Issue:** The plan's `<action>` asserted "PEP-562 `__getattr__` needs no change since it already delegates by name lookup against `__all__`." In fact the Plan-01 `__getattr__` imported the `compile` submodule specifically and returned `getattr(compile, name)`; the new `direct`/`reverse`/`transitive` live in `query.py`, so an unchanged delegate would have raised `AttributeError` for every query name.
- **Fix:** Replaced the compile-only delegate with a `name -> owning-submodule` map (`compile_graph`->`compile`, query names -> `query`) using `importlib.import_module`. `compile_graph` re-export behaviour is unchanged.
- **Files modified:** `tools/contract_graph/__init__.py`
- **Commit:** `c5e9d74`

**2. [Rule 3 - Blocking] Lint (E501/B905) on newly-authored files**
- **Found during:** Task 2
- **Issue:** New docstrings exceeded the repo's 100-char line cap (E501) and a `zip()` lacked `strict=` (B905).
- **Fix:** Reflowed the overlong docstring lines and added `strict=True` to the `zip()` in the diamond-path test. All newly-authored files are ruff-clean.
- **Files modified:** `tools/contract_graph/query.py`, `tools/contract_graph/tests/test_query.py`
- **Commit:** `fb7b945`

## Issues Encountered

None blocking. (`requirements mark-complete TOPO-05` reported it was already marked complete; no action needed. The `state.record-metric` SDK verb rejected the positional-arg form, so the Performance Metrics row and the decision entry were appended to STATE.md directly.)

## Deferred Issues

- The four pre-existing `E501` violations in `tools/harness_config/loader.py` (carried from Plan 01) remain out of scope and untouched.

## User Setup Required

None.

## Next Phase Readiness

- `direct`/`reverse`/`transitive` are ready for Plan 03's conductor: the `transitive()` visited-set shape is the exact traversal Plan 03's indented-tree renderer reuses for its `(cycle -> <node>)` marker.
- Full suite green (947 passed), contract-drift OK, GEN-04 guard green.

---
*Phase: 25-graph-compiler-queries-conductor-proof-v2-3-a*
*Completed: 2026-07-19*

## Self-Check: PASSED

All created/modified files exist on disk (`query.py`, `test_query.py`, `__init__.py`); both task commits (`c5e9d74`, `fb7b945`) present in git history.
