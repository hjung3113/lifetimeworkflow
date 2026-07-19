---
phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
plan: 01
subsystem: infra
tags: [contract-graph, topology, compiler, harness-lint, effective-relationships, diagnostics]

# Dependency graph
requires:
  - phase: 24-contract-relationship-vocabulary-compatibility-v2-3-a
    provides: "effective_relationships() lowering+union+sort-by-id+3 failure modes; relationship.schema.json; [contract_graph] slot"
provides:
  - "tools/contract_graph/ uv workspace member exposing compile_graph(cfg=None) -> {relationships, adjacency, diagnostics}"
  - "Endpoint resolution (authority/dependents) via split_endpoint against declared components/members"
  - "Authority-owned-contract resolution: produces-membership + schema-glob existence fallback (project + cross-repo)"
  - "Three stable D-02 diagnostic slugs: unresolved-authority / dangling-endpoint / unknown-contract"
  - "TOPO-04 harness_lint consistency gate (test_contract_graph_config.py) — zero-diagnostics anchors on core + workspace defaults"
  - "WR-02 closed: effective_relationships() raises actionable ValueError (not bare KeyError) on malformed edge/record"
affects: [plan-25-02-queries, plan-25-03-conductor, plan-25-04-proof, TOPO-05, TOPO-06, TOPO-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Compiler-on-top-of-loader: compile_graph consumes effective_relationships() verbatim, never re-lowers/re-unions"
    - "Descriptive grep-able diagnostic slugs returned as sorted list[str] (never raised), mirroring contract_drift.run_gate result-dict"
    - "Schema-glob existence idiom reused for authority-owned-contract resolution (project contracts/ + cross-repo member contracts/)"

key-files:
  created:
    - tools/contract_graph/pyproject.toml
    - tools/contract_graph/__init__.py
    - tools/contract_graph/compile.py
    - tools/contract_graph/tests/__init__.py
    - tools/contract_graph/tests/conftest.py
    - tools/contract_graph/tests/test_compile.py
    - tools/harness_lint/tests/test_contract_graph_config.py
  modified:
    - tools/harness_config/loader.py
    - tools/harness_config/tests/test_topology_relationships.py

key-decisions:
  - "New sibling package tools/contract_graph/ (not an extension of harness_config) — clean separation of the resolution layer from the lowering/union loader"
  - "compile_graph never raises for graph shape; only effective_relationships()'s own ValueError propagates"
  - "unknown-contract uses produces-membership when the authority is a component with a produces list, else existence-only schema glob"

patterns-established:
  - "Consume-don't-reimplement: the compiler is a thin validation/resolution layer over the single effective_relationships() path"
  - "Legal shapes (fan-in/fan-out/disconnected/cycle) are never flagged — a cycle is just two adjacency entries with no special casing"

requirements-completed: [TOPO-04]

# Metrics
duration: ~35min
completed: 2026-07-19
---

# Phase 25 Plan 01: Graph Compiler + Consistency Gate Summary

**Domain-neutral `compile_graph()` resolution layer over `effective_relationships()` — endpoint + authority-owned-contract resolution, three stable diagnostic slugs, a green harness_lint gate on core/workspace defaults, and WR-02 (bare KeyError) closed.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-07-19
- **Tasks:** 3 (all TDD: RED → GREEN per task)
- **Files modified:** 9 (7 created, 2 modified)

## Accomplishments
- New `tools/contract_graph/` uv workspace member (package=false, zero deps) auto-discovered by the root `tools/*` glob, with PEP 562 lazy re-export mirroring `harness_config`.
- `compile_graph(cfg=None)` sits ON TOP of `effective_relationships()` — never re-lowers/re-unions — resolving every authority/dependent endpoint via `split_endpoint` against declared components (project) and members (workspace), and building a sorted, repo-confined adjacency map.
- Fan-in, fan-out, disconnected components, and canonical cycles all compile with EMPTY diagnostics (structurally legal, never flagged).
- Three D-02 descriptive slugs (`unresolved-authority` / `dangling-endpoint` / `unknown-contract`) fire exactly once per violated constraint, are stable-sorted, and never raise.
- Authority-owned-contract resolution reuses the repo's schema-glob existence idiom — `produces`-membership for component-backed authorities, existence-only fallback against `contracts/` (project) or `<member>/contracts/` (cross-repo).
- TOPO-04 `harness_lint` gate wired: core-default project and default workspace both stay green (`diagnostics == []`).
- WR-02 closed: `effective_relationships()` now guards missing edge/record keys and raises an actionable `ValueError` naming the offending record (signature/return shape unchanged) — no more opaque bare `KeyError`.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 (RED): scaffold member + failing legal-shape tests** — `004143e` (test)
2. **Task 1 (GREEN): compile_graph endpoint resolution + adjacency** — `a92e8d1` (feat)
3. **Task 2 (RED): failing D-02 diagnostic-slug tests** — `9762c7a` (test)
4. **Task 2 (GREEN): emit diagnostic slugs during resolution** — `874abd8` (feat)
5. **Task 3: harness_lint gate + WR-02 closure (KeyError → ValueError)** — `1abee47` (feat)

## Files Created/Modified
- `tools/contract_graph/pyproject.toml` - New uv workspace member (package=false, zero deps).
- `tools/contract_graph/__init__.py` - PEP 562 lazy re-export of `compile_graph`.
- `tools/contract_graph/compile.py` - The compiler: endpoint resolution, adjacency, D-02 diagnostics.
- `tools/contract_graph/tests/{__init__.py,conftest.py}` - Test-package wiring (repo root onto sys.path).
- `tools/contract_graph/tests/test_compile.py` - 9 tests: 5 legal-shape + 4 diagnostic-slug.
- `tools/harness_lint/tests/test_contract_graph_config.py` - TOPO-04 gate: zero-diagnostics anchors.
- `tools/harness_config/loader.py` - WR-02 guard (additive; missing-key → ValueError).
- `tools/harness_config/tests/test_topology_relationships.py` - 2 WR-02 regression tests.

## Decisions Made
- New sibling package rather than extending `harness_config`, keeping the resolution/validation layer distinct from the lowering/union loader.
- `compile_graph` returns diagnostics as data (never raises for graph shape); only `effective_relationships()`'s own `ValueError` propagates.
- `unknown-contract` prefers `produces`-membership when the authority is a component carrying a `produces` list, else falls back to schema-glob existence (project root or cross-repo member root).

## Deviations from Plan

None - plan executed exactly as written. (The plan's TDD structure was honored: Task 1 `compile_graph` returned empty diagnostics first, then Task 2 layered emission — RED-before-GREEN preserved for the Task 2 diagnostic tests.)

## Issues Encountered
- Initial test collection failed with `ModuleNotFoundError: No module named 'tools'` because the new test package had no `conftest.py`/`__init__.py` to place the repo root on `sys.path`. Resolved by adding both, mirroring `tools/harness_config/tests/conftest.py` (the established virtual-member import-wiring pattern).

## Deferred Issues
- Four pre-existing `E501` (line > 100) lint violations in `tools/harness_config/loader.py` docstrings (lines 83/91/98/99, present in HEAD before this plan) are out of scope per the scope boundary and were left untouched. All newly-authored files are lint-clean.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `compile_graph()` + `adjacency` are the foundation for Plan 02 (affected-set queries), Plan 03 (conductor rendering), and Plan 04 (proof fixtures).
- Full suite green (938 passed), contract-drift OK, GEN-04 guard green.

---
*Phase: 25-graph-compiler-queries-conductor-proof-v2-3-a*
*Completed: 2026-07-19*
