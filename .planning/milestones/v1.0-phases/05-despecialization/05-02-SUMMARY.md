---
phase: 05-despecialization
plan: 02
subsystem: testing
tags: [golden-runner, identity-converter, json-schema, contract-hash, drift, docs-sync, syrupy]

# Dependency graph
requires:
  - phase: 05-01
    provides: commit-gate drift approval path (GOLDEN_APPROVE_HUMAN warn+pass) so residual drift is ratifiable
  - phase: 01-golden
    provides: golden_runner compare loop + §4.3-4.6 normalize_tsv core
provides:
  - Language-agnostic built-in identity converter (verbatim stdlib byte-copy, no .NET) in the golden runner
  - golden_dir override threaded through case_dir/seed/verified/received/compare/run_golden_case
  - Domain-neutral sample contract (contracts/sample/greeting.schema.json) with zero semiconductor vocabulary
  - Generic golden case (golden/sample/*) running the full contract->hash->drift->golden loop without .NET
  - Rebaselined 6-schema root contract-hash manifest, drift-clean
affects: [05-03, despecialization, template-clone]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Converter selector on run_golden_case (identity vs dotnet) — core no longer hardcodes the domain converter"
    - "golden_dir override — core no longer pins REPO_ROOT/golden; same §4.3-4.6 loop serves generic + domain trees"
    - "Row-order-only representation diff as the identity-converter PASS proof (normalize_tsv R8)"

key-files:
  created:
    - contracts/sample/greeting.schema.json
    - golden/sample/meta.yaml
    - golden/sample/input/seed.tsv
    - golden/sample/expected/baseline.verified.tsv
    - tools/golden_runner/tests/test_identity_converter.py
    - tools/golden_runner/tests/test_sample_loop.py
  modified:
    - tools/golden_runner/runner.py
    - contracts/.hashes/manifest.json
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr

key-decisions:
  - "Identity converter routes past resolve_dotnet entirely; converter default stays 'dotnet' for backward compatibility"
  - "Representation diff limited to ROW-ORDER (R8) because an identity converter cannot canonicalize decimals/timezones"
  - "seed.tsv authored byte-clean (LF, no BOM) since it is an ADDED file linted by the polyglot commit-gate (R1/R2)"

patterns-established:
  - "Parametrized golden engine: per-case converter + golden_dir override make the core example-independent"
  - "A generic default instance proves the machinery runs on a blank domain (clone-and-go template state)"

requirements-completed: [GEN-02]

# Metrics
duration: ~18min
completed: 2026-07-09
---

# Phase 5 Plan 02: GEN-02 Generic Default Instance Summary

**A domain-neutral greeting sample contract + a .NET-free identity-converter golden case exercise the full contract→hash→drift→golden loop on a blank domain, with the golden runner parametrized by converter and golden_dir.**

## Performance

- **Duration:** ~18 min
- **Tasks:** 2
- **Files created:** 6
- **Files modified:** 5

## Accomplishments
- Added a built-in **language-agnostic identity converter** (`run_identity_converter`) — verbatim stdlib byte-copy, no `dotnet`, no subprocess, zero domain vocabulary.
- Threaded a `golden_dir` override through `case_dir`/`seed_path`/`verified_path`/`received_path`/`compare`/`run_golden_case`, and added a `converter` selector (default `"dotnet"`, backward-compatible) — the core no longer pins the domain converter or golden root. The §4.3-4.6 `normalize_tsv` compare path is untouched.
- Shipped `contracts/sample/greeting.schema.json`: a trivial Draft 2020-12 schema (`name`/`greeting`, `required:[name]`) with **zero semiconductor vocabulary**.
- Shipped `golden/sample/*`: a byte-clean (LF, no BOM) 2-column seed in **unsorted** row order + a baseline that is the same lines ordinal-sorted, so `normalize_tsv` (R8) makes identity-output == baseline → **PASS** with no `.received`.
- Rebaselined the root manifest to 6 schemas; `tools.contract_drift.drift` reads **clean**.
- Extended docs-sync `EXPECTED_PAGES` with `greeting` and regenerated its determinism snapshot (proven deterministic on re-run without `--snapshot-update`).

## Task Commits

Each task was committed atomically:

1. **Task 1: Parametrize golden_runner — identity converter + golden_dir override** — `c5597a5` (feat)
2. **Task 2: Generic default instance — sample contract + golden case + rebaseline + docs-sync page** — `84dd0eb` (feat)

_TDD (Task 1): test authored first, confirmed RED (ImportError on `run_identity_converter`), then GREEN; committed as a single atomic task commit per the orchestrator's "commit atomically per task" directive._

## Files Created/Modified
- `tools/golden_runner/runner.py` — `run_identity_converter` + `converter`/`golden_dir` params; normalize path unchanged
- `tools/golden_runner/tests/test_identity_converter.py` — row-order PASS, value-diff FAIL+`.received`, byte-copy, golden_dir reroot (tmp case, order-independent)
- `contracts/sample/greeting.schema.json` — GEN-02 domain-neutral sample contract
- `golden/sample/{meta.yaml,input/seed.tsv,expected/baseline.verified.tsv}` — identity golden case (row-order-only diff)
- `contracts/.hashes/manifest.json` — rebaselined (6 schemas, incl. `contracts/sample/greeting.schema.json`)
- `tools/docs_sync/tests/test_docs_sync_determinism.py` — `greeting` added to EXPECTED_PAGES; five-page test renamed/reworded
- `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` — regenerated (render now covers greeting)
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` — regenerated (index render now covers greeting)
- `tools/golden_runner/tests/test_sample_loop.py` — sample PASSES via identity (no .NET), in manifest, drift clean

## Decisions Made
- Identity converter is selected by `converter="identity"` and skips `resolve_dotnet`/`run_converter` entirely; any other value keeps the .NET spawn so `test_repr_only`/`test_value_regression` remain unchanged (they SKIP cleanly when dotnet is absent).
- The sample's representation diff is deliberately **row-order only** — an identity converter performs no decimal/timezone canonicalization, so any other diff class would (correctly) FAIL.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Regenerated the memory_regen contracts-index determinism snapshot**
- **Found during:** Task 2 (full-suite run)
- **Issue:** `tools/memory_regen/tests/test_contracts_index.py::test_render_matches_committed_snapshot` renders `index_rows()` over the real `contracts/` tree, which now yields the greeting schema — the committed `.ambr` no longer matched. The plan called out only the analogous docs-sync snapshot (Blocker-1) but the same regeneration is required for the contracts-index snapshot, which is directly caused by adding the schema.
- **Fix:** `uv run pytest tools/memory_regen/tests/test_contracts_index.py --snapshot-update`, then re-ran without `--snapshot-update` to prove determinism (7 passed, 1 snapshot passed).
- **Files modified:** `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr`
- **Verification:** Deterministic on re-run; committed in Task 2.
- **Committed in:** `84dd0eb`

---

**Total deviations:** 1 auto-fixed (1 blocking snapshot regeneration).
**Impact on plan:** Necessary consequence of the new schema on a derived-plane snapshot; no scope creep. The §4.3-4.6 normalize path and all contracts remained untouched.

## Issues Encountered

**commit_gate drift-block tests fail only when the ratification token is live in the shell (out of scope, deferred).**
Three tests in `tools/hooks/tests/test_commit_gate.py` (`test_drift_present_blocks`, `test_golden_skip_does_not_suppress_drift`, `test_from_hook_blocks_commit_on_drift`) assert a drift BLOCK but do not `delenv("GOLDEN_APPROVE_HUMAN")`. Because this session must keep `GOLDEN_APPROVE_HUMAN` exported (the precondition to author constitution-plane `contracts/sample/**` + `golden/sample/**`), the 05-01 drift-approval path turns the expected block into warn+pass and they fail. This is a pre-existing test-isolation gap in a prior-plan file, NOT a 05-02 regression:

- With the token unset (CI-equivalent): `env -u GOLDEN_APPROVE_HUMAN uv run pytest` → **364 passed, 2 skipped** (green).
- With the token live (this session): the same run reports those **3 failures** plus 360 passed.

Logged to `.planning/phases/05-despecialization/deferred-items.md` (DEF-05-02-1) with a suggested hermetic fix. Left the concurrent/prior-plan test file untouched per the orchestrator directive.

## Test Results
- `uv run pytest tools/golden_runner/tests/test_identity_converter.py tools/golden_runner/tests/test_compare_recorded.py` → 6 passed.
- `uv run pytest tools/golden_runner/` → 12 passed, 2 skipped (dotnet-gated e2e skip cleanly).
- `uv run pytest tools/golden_runner/tests/test_sample_loop.py tools/docs_sync/tests/test_docs_sync_determinism.py` → 12 passed (snapshot deterministic).
- `uv run python -m tools.contract_drift.drift` → `contract-drift: OK — live manifest matches the committed baseline.`
- Byte-clean proof (`od -c`): `golden/sample/input/seed.tsv` and `expected/baseline.verified.tsv` show no `357 273 277` (BOM) and no `\r`.
- Full suite (CI-equivalent, token unset): **364 passed, 2 skipped**.

## Next Phase Readiness
- The core now points at a generic instance, not a void — 05-03 (domain move to `examples/log-parser/`) can rely on the parametrized converter + golden_dir and the drift-clean rebaselined manifest.
- Recommended before/independently: apply the DEF-05-02-1 hermetic fix so the commit-gate suite is token-agnostic.

## Self-Check: PASSED

All 6 created artifacts + the SUMMARY exist on disk; both task commits (`c5597a5`, `84dd0eb`) are present in git history.

---
*Phase: 05-despecialization*
*Completed: 2026-07-09*
