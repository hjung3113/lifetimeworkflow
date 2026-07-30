---
phase: 49-contract-impact
plan: 01
subsystem: infra
tags: [contract-graph, impact-analysis, traversal-composition, pytest]

# Dependency graph
requires:
  - phase: 25-declared-contract-relationship-graph-v2-3-c
    provides: "tools/contract_graph/query.py (direct/reverse/transitive), compile.py (compile_graph)"
  - phase: 47-package-facts
    provides: "tools/memory_regen/package_facts.build_facts(), tools/contract_graph/ownership.py (owning_package)"
  - phase: 48-convention-profiles
    provides: "effective_packages()'s dir-key adapter filter idiom (loader.py:330-338)"
provides:
  - "tools/contract_graph/impact.py — report(contract_path, cfg=None, graph=None, facts=None) composing direct/reverse/transitive + package/owner attribution"
  - "main() CLI entry point (python -m tools.contract_graph.impact <contract-path-or-node-id>)"
affects: [49-02-contract-impact-command-wiring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "impact.py follows the repo's injectable cfg=None/graph=None/facts=None pure-function convention (mirrors owning_package/conventions_for)"
    - "refusal report has a structurally different key set than resolved reports (never a shape-identical 'empty success')"

key-files:
  created:
    - tools/contract_graph/impact.py
    - tools/contract_graph/tests/test_impact.py
  modified: []

key-decisions:
  - "contract_owner is None both when resolution matched via bare node id (no contract file path to attribute) AND when owning_package() raises ValueError (no enclosing package in facts) — both paths never fabricate an owner."
  - "owners dict is keyed by every id in sorted(node_set) (start node + direct/reverse/transitive union), not just the traversal result ids, so the query node's own owner is always present."

patterns-established:
  - "Extended no-second-traversal-engine structural check: catches while-loops, for-loops iterating adjacency directly, AND locally-defined recursive functions — not just the while-shaped re-implementation a naive check would miss."

requirements-completed: [MONO-08]

# Metrics
duration: 25min
completed: 2026-07-30
---

# Phase 49 Plan 01: Contract Impact Reporter Summary

**`tools/contract_graph/impact.py::report()` composes direct/reverse/transitive + effective_packages()/owning_package() into one deterministic, clean-refusing impact report — zero new traversal logic.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 completed
- **Files modified:** 2 (both new)

## Accomplishments

- `tools/contract_graph/impact.py` — `report(contract_path, cfg=None, graph=None, facts=None)` resolves a
  contract path (or bare node id) to a graph node via `effective_relationships()`, calls
  `direct`/`reverse`/`transitive` unmodified, and attributes affected packages/per-node owners via
  `effective_packages()` (reusing the exact Phase-48 `"dir"`-key adapter filter) and `owning_package()`.
  `main()` CLI entry point mirrors `package_facts.main()`'s shape.
- `tools/contract_graph/tests/test_impact.py` — 10 tests on synthetic domain-neutral (`a`/`b`/`c`/`d`,
  contract `widget`) fixtures, covering all five MONO-08 behaviors: traversal reuse, package
  attribution, the (strengthened) no-second-traversal-engine structural check, the three-way
  refused/isolated/affected key-set distinction, and determinism.
- Extended the plan's structural check per the plan-checker's warning: the AST scan now fails on a
  `while`-shaped re-implementation, a `for`-loop iterating `graph["adjacency"]` directly, AND any
  locally-defined recursive function in `impact.py` — not just the `while`-only shape a naive check
  would catch. Both violation shapes were mutation-tested against synthetic stubs (see below).

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement impact.py's report() + main()** - `4199110` (feat)
2. **Task 2: test_impact.py — the five MONO-08 behaviors** - `7d12815` (test)

**Plan metadata:** (this commit)

## Files Created/Modified

- `tools/contract_graph/impact.py` — new module: `_resolve_node`, `report`, `main`
- `tools/contract_graph/tests/test_impact.py` — new test file: 10 tests

## Decisions Made

- `contract_owner` is `None` on both "resolved via bare node id" (no contract file path exists to
  attribute) and "resolution matched a contract id but `owning_package()` raised `ValueError`"
  (facts had no enclosing package) — the field never fabricates a value in either case, consistent
  with `ownership.py`'s "never fabricates" posture.
- `owners` is keyed by every id in the FULL `node_set` (start node ∪ direct ∪ reverse ∪ transitive
  ids), not only the traversal result ids, so the query node's own declared owner is always present
  in the report even when it has zero neighbours (the isolated case).

## Deviations from Plan

**1. [Rule 1 - Bug] GEN-04 grep-count violation in the new test file's own module docstring**
- **Found during:** Task 2, running the plan's `grep -c "examples/" tools/contract_graph/tests/test_impact.py` acceptance check.
- **Issue:** The docstring's own prose used the literal string `` `` `examples/` `` `` path`` while
  explaining the GEN-04 rule it was following — tripping the exact grep the plan specifies must
  return `0`.
- **Fix:** Reworded to "instance-directory path" (no literal `examples/` substring); re-ran the
  grep, confirmed `0` on both `impact.py` and `test_impact.py`.
- **Files modified:** `tools/contract_graph/tests/test_impact.py`
- **Verification:** `grep -c "examples/" tools/contract_graph/impact.py tools/contract_graph/tests/test_impact.py` → `0` / `0`.
- **Committed in:** `7d12815` (Task 2 commit — caught before commit, not a follow-up fix)

---

**Total deviations:** 1 auto-fixed (1 bug — GEN-04 self-leak in docstring prose, same class as `10-01`'s
own documented `test_pipeline_config.py` self-leak).
**Impact on plan:** Trivial wording fix; no scope creep, no behavior change.

## Mutation-Check Proof (hard-constraint requirement)

### 1. The extended structural check itself, against two synthetic violation stubs

Both shapes trip `_traversal_violations()` (the extended AST check in `test_impact.py`), proving the
check is not a "check that cannot fail":

- `test_check_traps_a_while_frontier_stub` — a synthetic `while frontier:` stub → violation
  `"while-loop"` detected. PASSED.
- `test_check_traps_a_for_over_adjacency_stub` — a synthetic `for node in graph['adjacency']:` stub
  → violation `"for-over-adjacency: graph['adjacency']"` detected. PASSED. (This is the exact shape
  the plan-checker warned a `while`-only check would silently miss.)

Both are real, permanently-committed pytest tests (not one-off manual runs) — see
`tools/contract_graph/tests/test_impact.py::test_check_traps_a_while_frontier_stub` and
`::test_check_traps_a_for_over_adjacency_stub`.

### 2. The required "checks that cannot fail" mutation drill on a real test

Command run (mutating `test_report_composes_direct_reverse_transitive_not_rederived` to compare
against `direct(graph, "b")` instead of `direct(graph, "a")`):

```
uv run pytest tools/contract_graph/tests/test_impact.py -k test_report_composes_direct_reverse_transitive_not_rederived -v
```

Output (excerpt, before revert):

```
tools/contract_graph/tests/test_impact.py::test_report_composes_direct_reverse_transitive_not_rederived FAILED [100%]
...
>       assert result["direct"] == direct(graph, "b")  # MUTATION: intentionally wrong
E       AssertionError: assert {'ids': ['b',..., ['a', 'd']]} == {'ids': [], 'paths': []}
...
FAILED tools/contract_graph/tests/test_impact.py::test_report_composes_direct_reverse_transitive_not_rederived
1 failed, 9 deselected in 0.03s
```

Reverted immediately after capturing the `FAILED` line; re-ran the full file — `10 passed`.

## Issues Encountered

None beyond the GEN-04 wording deviation documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `tools/contract_graph/impact.py::report`/`main` are ready for Plan 02's `/impact` command wiring
  and the `contract-change` route's *Repository evidence* block replacement.
- Full suite (`uv run pytest -q`) is green: 945 passed (baseline 935 + this plan's 10 new tests).
- `tools/contract_graph`/`tools/harness_config` scoped suite: 94 passed.
- `query.py`, `compile.py`, `ownership.py`, `loader.py` are byte-unchanged — `git diff --stat`
  confirms exactly the two new files this plan claims (plus the pre-existing, unrelated
  `.planning/STATE.md` orchestrator-position edit from before this plan started).

---
*Phase: 49-contract-impact*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: tools/contract_graph/impact.py
- FOUND: tools/contract_graph/tests/test_impact.py
- FOUND: .planning/phases/49-contract-impact/49-01-SUMMARY.md
- FOUND commit: 4199110 (Task 1)
- FOUND commit: 7d12815 (Task 2)
- FOUND commit: de8fd55 (this docs commit)
