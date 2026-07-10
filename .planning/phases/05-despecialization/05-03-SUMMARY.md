---
phase: 05-despecialization
plan: 03
subsystem: infra
tags: [git-mv, contracts, contract-drift, golden, snapshot, syrupy, despecialization, monorepo]

# Dependency graph
requires:
  - phase: 05-01
    provides: drift component ratifiable via GOLDEN_APPROVE_HUMAN (live commit-gate approval path)
  - phase: 05-02
    provides: golden_runner golden_dir/converter/project parametrization + generic sample instance (greeting)
provides:
  - "Semiconductor domain seed relocated under examples/log-parser/ via history-preserving git mv (renames, R)"
  - "Root contract-hash manifest rebaselined to the generic instance only (format-conventions + sample/greeting); live drift reads clean"
  - "examples/log-parser/contracts/.hashes/manifest.json — the example's own drift baseline over the 4 moved domain schemas"
  - "Core golden_runner de-pinned: no TOY_CONVERTER_PROJECT domain default, no dead toy_converter_project fixture"
  - "Domain golden_runner tests moved with their cases + a minimal example conftest so .NET-gated cases SKIP cleanly"
  - "Regenerated docs-sync + contracts-index snapshots + repointed core tests (EXPECTED_PAGES, rows() target, test_agents_md planes)"
affects: [05-04, 05-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "History-preserving relocation via verbatim git mv (renames stay R → excluded from commit_gate --diff-filter=ACM → dirty BOM/CRLF golden seeds not re-linted)"
    - "Per-instance drift baseline: path-keyed manifest built by pointing build_manifest() at an alternate contracts root"
    - "Core template names no domain artifact: converter project supplied via run_golden_case(project=..., golden_dir=...)"

key-files:
  created:
    - examples/log-parser/contracts/.hashes/manifest.json
    - examples/log-parser/tests/conftest.py
  modified:
    - contracts/.hashes/manifest.json
    - tools/golden_runner/runner.py
    - tools/golden_runner/tests/conftest.py
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
    - tools/memory_regen/tests/test_agents_md.py
    - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr

key-decisions:
  - "libs/dotnet/ moved WHOLESALE with the example (not a uv member, no core Python importer; ADR-0002 core-is-language-neutral); libs/python/normalize + libs/normalize-fixtures STAY (uv members / core-imported)"
  - "KIND map left with 'other' fallback for the generic sample rather than adding a 'sample' kind, to keep test_rows_have_kind_owner_hash_and_status green without widening its allowed-kind set"
  - "test_rows_are_sorted_and_typed repointed off the moved standard-log to format-conventions (a surviving schema with top-level const props) — coverage preserved, not deleted"

patterns-established:
  - "Relocation invariant: verbatim git mv only (P2) — a content edit reclassifies the rename A/M and trips the polyglot re-lint on the intentionally-dirty seeds"
  - "Two-baseline drift: root manifest for the generic core, an example-local manifest for the relocated instance"

requirements-completed: [GEN-01]

# Metrics
duration: ~20min
completed: 2026-07-09
---

# Phase 5 Plan 03: GEN-01 Domain MOVE Summary

**Relocated the semiconductor log-parser domain seed + its .NET language-side impl under `examples/log-parser/` via history-preserving `git mv`, rebaselined the root manifest to the generic instance only (drift clean), built the example's own manifest, de-pinned the core golden_runner, and regenerated the two stale snapshots — the non-example suite stays green (361 passed).**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-09
- **Tasks:** 2
- **Files modified:** 36 files changed (137 insertions, 119 deletions), 27 renames + 9 ACM

## Accomplishments
- Domain seed relocated as history-preserving renames: `contracts/{log-specs,reference-data,state}` + `contracts/normalization/correction-rules.{catalog.yaml,schema.json}`, `components/toy-converter`, `libs/dotnet` (wholesale: Normalize/ + Normalize.Tests/ + AGENTS.md), `golden/{repr-only,value-regression}`, and the three domain golden_runner tests + `tests/recorded/*` → `examples/log-parser/`.
- Core stayed language-neutral: `libs/python/normalize`, `libs/normalize-fixtures`, `contracts/normalization/format-conventions.schema.json`, and the generic golden_runner tests (`test_sample_loop`/`test_identity_converter`/`test_approve_gate` + conftest) are UNMOVED.
- Root manifest rebaselined to `{format-conventions, sample/greeting}` (2 schemas); `contract-drift` reads clean. Example manifest built over the example contracts root (4 domain schemas).
- Core golden_runner de-pinned: dropped the `TOY_CONVERTER_PROJECT` default (project now required via `run_golden_case(project=...)`) and deleted the dead `toy_converter_project` conftest fixture — no dangling `components/toy-converter` reference.
- Regenerated the docs-sync `.ambr` and contracts-index `.ambr` snapshots (repo-map `.ambr` unchanged — it is fixture-based); proved determinism by re-running without `--snapshot-update`.
- Repointed core tests to surviving material: docs-sync `EXPECTED_PAGES` → `{format-conventions, greeting}`, `rows()` target → format-conventions, `test_agents_md` drops `libs/dotnet/AGENTS.md` from `PER_PACKAGE_AGENTS` and the `libs/dotnet` literal from the root-map assertion.

## Task Commits

The whole move landed as ONE commit through the LIVE pre-commit gate (token active, NO `--no-verify`):

1. **Task 1 + Task 2 (single move commit)** — `ebe4276` (feat)

_Per the plan: Task 1 performs the moves + rebaseline (no commit yet), Task 2 regenerates snapshots + lands the single commit._

## Files Created/Modified
- `examples/log-parser/**` — relocated domain seed + .NET impl (renames, history preserved)
- `examples/log-parser/contracts/.hashes/manifest.json` — the example's own drift baseline (created)
- `examples/log-parser/tests/conftest.py` — mirrors the generic require_dotnet/golden_out/dotnet_exe fixtures + example golden_dir/converter project (created)
- `contracts/.hashes/manifest.json` — rebaselined to generic only
- `tools/golden_runner/runner.py` — removed the domain converter default; `run_converter` now requires an explicit project
- `tools/golden_runner/tests/conftest.py` — removed the dead `toy_converter_project` fixture
- `tools/docs_sync/tests/test_docs_sync_determinism.py` + `.ambr` — EXPECTED_PAGES + rows() target repointed, snapshot regenerated
- `tools/memory_regen/tests/test_agents_md.py` — dropped libs/dotnet as a core plane
- `tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr` — regenerated over the post-move root tree

## Decisions Made
- **libs/dotnet moved wholesale** with the example (not a uv member, no core Python importer; ADR-0002 core-is-language-neutral). Python normalize core stays (uv members / core-imported).
- **KIND left with 'other' fallback** for the generic sample rather than adding a `"sample"` kind, to avoid widening `test_rows_have_kind_owner_hash_and_status`'s allowed-kind set.
- **test_rows_are_sorted_and_typed repointed** to format-conventions (surviving, has top-level const props) — coverage preserved, not deleted.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing golden_dir on one verified_path call in the moved test_compare_recorded**
- **Found during:** Task 2 (validating the relocated example tests run correctly)
- **Issue:** After repointing `test_compare_recorded.py` to the example golden tree, the final P9 assertion (`verified_path(case)`) still used the default core golden dir, raising `FileNotFoundError` against the (now non-existent) root `golden/value-regression/...`.
- **Fix:** Passed `_GOLDEN_DIR` (examples/log-parser/golden) into that remaining `verified_path(case, _GOLDEN_DIR)` call, matching the other overridden calls in the test.
- **Files modified:** examples/log-parser/tests/test_compare_recorded.py
- **Verification:** `uv run pytest examples/log-parser/tests/` → 2 passed, 2 skipped (.NET-gated); import-parse check clean.
- **Committed in:** ebe4276 (the move commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug was in a relocated (out-of-testpaths) example test; fix restores the intended §4-5 P9 assertion against the example's own baseline. No scope creep.

## Issues Encountered
- The full-suite count is 361 passed / 0 skipped after the move (the 2 previously-skipped .NET-gated domain tests + the 2 passing recorded-comparison tests moved to `examples/`, which is outside `testpaths=[libs/python, tools]` so they are no longer collected by the core run). Verified the moved tests still behave correctly when invoked directly (2 passed, 2 skipped).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 05-04 / 05-05 can proceed: the domain seed is cleanly separated under `examples/log-parser/` behind a rebaselined manifest; the live drift gate is clean.
- 05-05 owns the final root `AGENTS.md` recast to the template shape; this plan set `test_agents_md` to stop asserting `libs/dotnet/AGENTS.md` at root and dropped `libs/dotnet` from the required root-map members so 05-05's recast reconciles cleanly.
- .NET csproj relative-reference fixups for the moved `libs/dotnet` / toy-converter are egress-deferred (out of this env's scope) and do not affect the pytest suite.

## Self-Check: PASSED
- `examples/log-parser/contracts/log-specs/standard-log.schema.json` — FOUND
- `examples/log-parser/contracts/.hashes/manifest.json` — FOUND
- `contracts/.hashes/manifest.json` (rebaselined) — FOUND
- Commit `ebe4276` — FOUND in git log; landed through the live gate (no --no-verify)
- `git log --follow` on the moved standard-log schema shows pre-move history (ec3915a feat(01-02))
- Retained core paths (libs/python/normalize, libs/normalize-fixtures, format-conventions.schema.json, generic golden_runner tests) — all present
- Moved paths (contracts/log-specs, components/toy-converter, libs/dotnet, golden/repr-only) — all gone from core
- `uv run python -m tools.contract_drift.drift` — clean
- `uv run pytest` — 361 passed

---
*Phase: 05-despecialization*
*Completed: 2026-07-09*
