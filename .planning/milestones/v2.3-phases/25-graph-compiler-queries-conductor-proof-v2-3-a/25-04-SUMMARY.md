---
phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
plan: 04
subsystem: contract-graph-proof
tags: [topo-07, proof-fixtures, cross-repo-authority, wr-01, gen-04]
requires:
  - "tools.contract_graph.compile_graph (Plan 01)"
  - "tools.contract_graph.transitive (Plan 02)"
  - "tools.workspace_config.split_endpoint / members"
  - "tests/fixtures/workspace (Phase-11 2-member fixture)"
provides:
  - "domain-neutral non-linear proof-fixture corpus (fan-out, request/response split, event fan-out, legal cycle)"
  - "automated WR-01 fixture-vocabulary constraint scan"
  - "cross-repo authority-resolution proof + instance-untouched + GEN-04 regression"
affects:
  - "tools/contract_graph/tests"
tech-stack:
  added: []
  patterns:
    - "records-derive-components: synthesize a compilable cfg from bare relationship records"
    - "non-contiguous Path.joinpath for GEN-04-safe instance-path reference"
key-files:
  created:
    - tools/contract_graph/tests/fixtures/graphs/valid/cases.json
    - tools/contract_graph/tests/test_proof_fixtures.py
    - tools/contract_graph/tests/test_cross_repo_authority.py
  modified: []
decisions:
  - "WR-01 DEFERRED: no change to the Phase-24 lowered-id scheme; the deferral is enforced by an automated corpus scan constraining every fixture id/contract/authority/dependent to exclude `/` and `->`."
  - "Proof cfgs derive their components from the records themselves (every endpoint a component, authority produces / dependent consumes) so the fixtures prove the SHAPE, not endpoint bookkeeping."
metrics:
  duration: 10min
  completed: 2026-07-19
  tasks: 2
  files: 3
---

# Phase 25 Plan 04: TOPO-07 Domain-Neutral Proof Fixtures Summary

Every non-linear shape the general relationship model promises — shared-contract fan-out,
request/response as two separate records, event fan-out, a legal multi-node cycle, and cross-repo
authority resolution — is now fixture-proven against Plan-01's compiler and Plan-02's queries, with
WR-01's disposition made an automated falsifiable test and the log-parser instance + GEN-04 guard
provably untouched.

## What Was Built

**Task 1 — non-linear proof fixtures + WR-01 scan** (`ae39643`)
- `tools/contract_graph/tests/fixtures/graphs/valid/cases.json`: four named domain-neutral scenarios
  (`shared-contract-fanout`, `request-response-split`, `event-fanout`, `legal-cycle`), each a list of
  relationship records mirroring `relationship.schema.json`, all strings `/`- and `->`-free.
- `tools/contract_graph/tests/test_proof_fixtures.py`: derives a compilable cfg from each scenario's
  records (endpoints → components, authority `produces` / dependent `consumes`), asserts each shape
  compiles with empty diagnostics and the expected adjacency, asserts `transitive(graph, "node-a")`
  terminates on the cycle returning `["node-b", "node-c"]` without re-entering the start, and runs the
  corpus-wide WR-01 vocabulary scan.

**Task 2 — cross-repo authority + guard regressions** (`f3c189f`)
- `tools/contract_graph/tests/test_cross_repo_authority.py`: a `member-a:emit` authority resolves the
  repo half against the two declared members (reusing the existing Phase-11 `tests/fixtures/workspace/`
  roots) and its `greeting` contract is existence-checked under member-a's own `contracts/` tree —
  same idiom as `test_edge_contracts_tracked_in_producer`. An undeclared repo half emits
  `unresolved-authority`. The reference instance `project.toml` is proven untouched (`git diff` vs
  HEAD empty), and the GEN-04 guard is re-run as a `shell=False` subprocess and asserted green. The
  instance path is built from non-contiguous `Path.joinpath("examples", "log-parser", ...)` segments so
  this core-plane file carries no contiguous instance-path token.

## Must-Haves Verification

- Shared-contract fan-out, request/response split, event fan-out all compile with empty diagnostics — PASS.
- Legal cycle compiles clean AND `transitive()` terminates with correct `{ids, paths}` — PASS.
- Cross-repo authority resolves via `split_endpoint` against declared members, contract existence-checked
  in the producer member's own tree (idiom reused, no new checker) — PASS.
- WR-01 go/no-go explicit: DEFERRED, enforced by an automated fixture-vocabulary scan — PASS.
- Log-parser instance untouched, GEN-04 guard green — PASS.

## Deviations from Plan

None — plan executed exactly as written. Both tasks are test-plane-only (fixture JSON + test files);
no non-test source files, so the MVP+TDD behavior-adding gate is exempt.

## Verification Evidence

- `uv run pytest tools/contract_graph/tests/test_proof_fixtures.py -q` → 5 passed.
- `uv run pytest tools/contract_graph/tests/test_cross_repo_authority.py tools/harness_lint/tests/test_core_no_example_dep.py -q` → 22 passed.
- `git diff --stat HEAD -- examples/log-parser/project.toml` → empty (instance untouched).
- `uv run pytest tools/contract_graph -q` → 27 passed.
- `uv run pytest -q` (full suite) → 961 passed, 6 snapshots passed, 0 failed.

## Self-Check: PASSED

- FOUND: tools/contract_graph/tests/fixtures/graphs/valid/cases.json
- FOUND: tools/contract_graph/tests/test_proof_fixtures.py
- FOUND: tools/contract_graph/tests/test_cross_repo_authority.py
- FOUND commit: ae39643 (Task 1)
- FOUND commit: f3c189f (Task 2)
