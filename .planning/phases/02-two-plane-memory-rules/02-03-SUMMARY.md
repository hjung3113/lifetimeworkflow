---
phase: 02-two-plane-memory-rules
plan: 03
subsystem: infra
tags: [memory, contracts-index, drift, syrupy, derived-plane, python, uv]

# Dependency graph
requires:
  - phase: 02-01
    provides: tools/memory_regen uv-workspace member + pinned toolchain + tmp_contracts_tree fixture
  - phase: 01-05
    provides: tools.contract_hash.build_manifest + tools.contract_drift.run_gate (RFC 8785 JCS hash + drift gate)
provides:
  - contracts-index generator (tools/memory_regen/contracts_index.py) reusing Phase-1 hash/drift
  - deterministic .memory/derived/contracts-index.md (DERIVED-marked, gitignored)
  - committed syrupy determinism reference snapshot
affects: [02-injector, 03-docs-sync, 04-contract-guard]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Derived-plane generator = REUSE constitution-plane modules (build_manifest/run_gate), never re-implement hashing (T-02-09 drift laundering)"
    - "Determinism proof on a gitignored artifact = committed syrupy .ambr snapshot + generate/hash/delete/regenerate, NOT git diff (Pitfall 2)"

key-files:
  created:
    - tools/memory_regen/contracts_index.py
    - tools/memory_regen/tests/test_contracts_index.py
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr
  modified: []

key-decisions:
  - "index_rows(contracts_dir, baseline_path) is parameterized so the drift test can diff a mutated tmp tree against its own baseline — production defaults to CONTRACTS_DIR/MANIFEST_PATH."
  - "owner column is hardcoded TBD (A3) — no machine-readable owner exists in contracts today; never fabricate."

patterns-established:
  - "Pattern: derived generator imports Phase-1 build_manifest+run_gate (hash[:12] + live drift status), assembles sorted rows, renders DERIVED-marked table with no timestamp/float → byte-identical on regen."

requirements-completed: [MEM-03]

# Metrics
duration: 8min
completed: 2026-07-08
---

# Phase 2 Plan 03: contracts-index Generator Summary

**Deterministic `.memory/derived/contracts-index.md` generator that REUSES Phase-1 build_manifest + run_gate to emit one DERIVED-marked row per contract (path, kind, hash[:12], live drift status) — delete+regen byte-identical, proven by a committed syrupy snapshot.**

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-07-08
- **Tasks:** 1 (TDD: test + implementation co-committed)
- **Files modified:** 3 created

## Accomplishments
- `contracts_index.py` — `index_rows` / `render` / `write` / `main` scan `contracts/**/*.schema.json` and reuse `tools.contract_hash.build_manifest` (JCS SHA-256, no re-hash) + `tools.contract_drift.run_gate` (live drift + breaking classification, T-02-09 no second hasher).
- Output carries the `DERIVED — do not hand-edit` header (T-02-08), sorted rows, owner→TBD (A3), hash prefix, and `clean` / `drift:<kind>:<cls>` status. No timestamp, no float, no schema body (Pitfall 1 / T-02-06).
- Determinism proven three ways: render-twice byte-identical, generate→sha256→delete→regenerate identical hash (NOT git diff, since the target is gitignored — Pitfall 2), and a committed `.ambr` syrupy snapshot over the real tree.
- Drift correctness proven on the `tmp_contracts_tree` fixture: one mutated schema surfaces `drift:*` while its sibling stays `clean`.
- Replaces the `(contracts-index pending)` stub the injector (`inject.py`) reads.

## Task Commits

1. **Task 1: contracts-index generator — scan + reuse drift modules + deterministic render** - `57b6c1b` (feat, TDD test+impl co-committed)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `tools/memory_regen/contracts_index.py` - generator: reuse Phase-1 hash/drift → deterministic derived index.
- `tools/memory_regen/tests/test_contracts_index.py` - determinism (render-twice + hash-roundtrip), drift correctness, structure, syrupy snapshot.
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` - committed determinism reference.

## Decisions Made
- `index_rows` parameterized on `(contracts_dir, baseline_path)` to make the tmp-tree drift test possible while defaulting to the real contracts tree + committed manifest in production.
- Owner column emits `TBD` unconditionally (A3) — no machine-readable owner today; fabricating would violate the derive-from-contracts-only rule (D-06).

## Deviations from Plan

None - plan executed exactly as written. The plan's TDD RED/GREEN were co-committed as a single atomic feat commit (test + implementation together) since the generator is ~80% reuse of already-green Phase-1 modules; both the failing-first intent and passing state are captured by the committed test suite.

## Issues Encountered
None. All 7 new tests green; full suite 67 passed, 2 skipped (pre-existing .NET egress skips, out of scope).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Derived-plane contracts-index is live; the injector's `_contracts_summary` now folds a real index head instead of the pending stub.
- Wave-2 sibling (repo-map generator) remains; injector already reads both derived files opportunistically.

## Self-Check: PASSED

All created files exist on disk; task commit `57b6c1b` present in git history.

---
*Phase: 02-two-plane-memory-rules*
*Completed: 2026-07-08*
