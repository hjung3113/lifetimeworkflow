---
phase: 47-package-facts
plan: 03
subsystem: infra
tags: [config-loader, override-layer, monorepo, package-facts, gen-04]

# Dependency graph
requires:
  - phase: 47-02
    provides: "tools/memory_regen/package_facts.py::build_facts() -> {\"packages\": [...], \"edges\": [...]}"
provides:
  - "effective_packages(cfg=None, facts=None) in tools/harness_config/loader.py — the MONO-03 layering function, re-exported from tools/harness_config"
  - "The MONO-03 zero-edits consistency proof for both live configs: core (harness/project.toml) and the example instance's overlay"
affects: [47-04, 47-05, 48, 49]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Field-level override layering (derived-is-base, declared-fields-win, no-match-stays-declared-only-never-raises) as a sibling function in loader.py, mirroring effective_relationships()'s shape with one deliberate divergence"
    - "Lazy in-function import of a heavier tools.memory_regen submodule (mirrors compile_graph's deferred load_project import) to keep loader.py's module-load footprint light"

key-files:
  created:
    - tools/harness_config/tests/test_effective_packages.py
    - tools/harness_lint/tests/test_package_facts_override.py
    - examples/log-parser/tests/test_package_facts_override_instance.py
    - .planning/phases/47-package-facts/deferred-items.md
  modified:
    - tools/harness_config/loader.py
    - tools/harness_config/__init__.py

key-decisions:
  - "GEN-04 self-check on the new core-plane test file's own docstring: an early wording ('...lives under examples/log-parser/tests/...') tripped the literal examples/ scanner. Reworded to 'the example instance's own test tree' before committing — zero examples/ literals remain under tools/."
  - "A pre-existing (Plan 47-02) GEN-04 failure in test_core_no_example_dep.py (the committed package-facts.ambr snapshot names real examples/log-parser/* manifest paths) was verified out-of-scope for this plan (isolated by moving this plan's 3 new files aside — the same single failure reproduces on the unmodified baseline) and logged to deferred-items.md rather than fixed, per the executor's scope-boundary rule."

requirements-completed: [MONO-03]

# Metrics
duration: 35min
completed: 2026-07-30
---

# Phase 47 Plan 03: Package Facts Override Layer Summary

**Added `effective_packages(cfg=None, facts=None)` to `tools/harness_config/loader.py`, demoting `[[components]]` from source-of-truth to an override slot layered field-by-field over Plan 47-02's derived package facts — proven for both the core config and the example instance's overlay with zero edits to either.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-07-30 (session start)
- **Completed:** 2026-07-30T03:11:14Z
- **Tasks:** 2 completed
- **Files modified:** 6 (2 modified, 4 new)

## Accomplishments
- `effective_packages()` in `loader.py`: builds `by_id` from `build_facts()["packages"]` (never mutated in place), merges each declared `[[components]]` entry over its matching derived record (declared fields win, unshared fields on either side survive), keeps a no-match component as-is (declared-only, no fabricated `manifest`/`dir`/`language`), passes through any derived package with no override, and returns the union stable-sorted by `id`.
- Re-exported via the existing single-module PEP 562 dispatch in `tools/harness_config/__init__.py` (`__all__` + generic `getattr(loader, name)` — no per-name dict needed, unlike `contract_graph`'s dispatch).
- 4 hermetic unit tests (`test_effective_packages.py`) over synthetic `facts`/`cfg` dicts: override-wins, no-match-stays-declared-only-no-raise, unmatched-derived-passes-through, output-sorted-by-id.
- Core-config consistency gate (`test_package_facts_override.py`): `harness/project.toml` loads through `effective_packages()` with zero edits, and every declared component id survives (override or declared-only) — fail-loud naming any offender.
- Instance-config consistency gate (`examples/log-parser/tests/test_package_facts_override_instance.py`), placed outside root `testpaths` per GEN-04, mirroring `test_pipeline_topology.py`'s exact placement: proves the same two properties for the example instance's `project.toml` overlay (`parser`/`converter`/`scheduler`/`collector` components — none of which match a real derived package id today, exercising the "no match, no raise" divergence for real).
- Mutation check (plan-required acceptance criterion): temporarily changed the no-raise assertion in `test_component_with_no_matching_package_stays_declared_only_no_raise` to `pytest.raises(KeyError)` — FAILED with `DID NOT RAISE`, proving the assertion is falsifiable; reverted.
- `uv run pytest tools/harness_config -q tools/harness_lint/tests/test_package_facts_override.py -q` → 39 passed. `uv run pytest examples/log-parser/tests/test_package_facts_override_instance.py -q` → 2 passed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement effective_packages() in loader.py + export it** - `fb224d3` (feat)
2. **Task 2: Unit tests + the MONO-03 core-config and instance-config consistency gates** - `adc4eac` (test)

**Plan metadata:** (pending — this SUMMARY commit)

## Files Created/Modified
- `tools/harness_config/loader.py` - added `effective_packages(cfg=None, facts=None)`, appended after `effective_relationships` (before `language_bash_scopes`).
- `tools/harness_config/__init__.py` - added `"effective_packages"` to `__all__` (dispatch is already generic single-module lookup, needs no per-name wiring).
- `tools/harness_config/tests/test_effective_packages.py` - 4 hermetic unit tests, domain-neutral `"a"`/`"b"` ids.
- `tools/harness_lint/tests/test_package_facts_override.py` - CORE-config-only consistency gate.
- `examples/log-parser/tests/test_package_facts_override_instance.py` - INSTANCE-overlay-only consistency gate (example leg, outside root `testpaths`).
- `.planning/phases/47-package-facts/deferred-items.md` - new file, logs the pre-existing Plan-47-02 GEN-04 failure found (not caused) during this plan's verification.

## Decisions Made
- Followed the plan's `<behavior>` spec exactly for the merge semantics: `{**by_id[comp_id], **comp}` gives declared-fields-win, base-only-fields-survive in one dict-spread expression, matching the docstring's stated principle verbatim.
- Kept the docstring's divergence callout generic ("the example instance's overlay") per GEN-04, per the plan's explicit instruction not to name the instance path literally in `loader.py`.
- The plan's Task 1 acceptance criterion expected `grep -c "effective_packages" tools/harness_config/__init__.py` to return at least 2 (assuming a per-name dispatch dict like `contract_graph`'s). This module already uses a simpler generic single-module `__getattr__` dispatch (`if name in __all__: from tools.harness_config import loader; return getattr(loader, name)`), so only 1 literal occurrence (in `__all__`) is possible or needed — the functional proof (`uv run python -c "from tools.harness_config import effective_packages"` succeeds) is what actually matters, and it passes. Documented here rather than fabricating a second literal occurrence just to satisfy the grep count.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed a GEN-04 self-inflicted leak in this plan's own new test docstring**
- **Found during:** Task 2, post-write verification (`grep -rn "examples/" tools/harness_config tools/harness_lint/tests/test_package_facts_override.py`)
- **Issue:** `tools/harness_lint/tests/test_package_facts_override.py`'s module docstring originally read "...own leg-appropriate gate lives under examples/log-parser/tests/..." — a literal `examples/` path token under `tools/`, violating this plan's own hard constraint (GEN-04: no literal `examples/` path string in anything written under `tools/`, `harness/`, `libs/`).
- **Fix:** Reworded to "the example instance's own test tree" — same meaning, zero literal `examples/` substring.
- **Files modified:** `tools/harness_lint/tests/test_package_facts_override.py`
- **Verification:** `grep -rn "examples/" tools/harness_config tools/harness_lint/tests/test_package_facts_override.py` returns zero hits; `test_core_no_example_dep.py`'s own scan of this file's line no longer flags it.
- **Committed in:** `adc4eac` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug, self-inflicted GEN-04 leak caught and fixed before commit)
**Impact on plan:** Necessary correctness fix for this plan's own hard constraint. No scope creep.

## Issues Encountered

**Pre-existing GEN-04 failure discovered, not fixed (out of scope):** `uv run pytest tools/harness_lint -q` surfaces one failure — `test_core_no_example_dep.py::test_core_has_no_example_dependency` — caused by `tools/memory_regen/tests/__snapshots__/test_package_facts.ambr` (committed in Plan 47-02) containing literal `examples/log-parser/...` manifest paths for the 4 real example packages the derived generator discovers over the real tree. Verified pre-existing (not introduced by this plan) by temporarily moving all three of this plan's new test files aside and re-running the full `tools/harness_lint` suite: the identical single failure and offender set reproduces on the unmodified baseline (266 passed / 1 failed, vs. 305 passed / 1 failed with this plan's tests present — same one failure either way). Logged to `.planning/phases/47-package-facts/deferred-items.md` per the executor's scope-boundary rule (only auto-fix issues directly caused by the current task's own changes) rather than fixed here, since fixing it would mean editing Plan 47-02's generator/snapshot or the GEN-04 scanner itself — outside this report-only phase's `+0 gates/CI/commands` boundary and outside Task 1/2's stated file list.

## Mutation Verification (acceptance criterion)

Per Task 2's acceptance criteria: temporarily replaced `test_component_with_no_matching_package_stays_declared_only_no_raise`'s body with `with pytest.raises(KeyError): effective_packages(cfg, facts)`.
- Result: `Failed: DID NOT RAISE <class 'KeyError'>` — the test FAILED as expected (proving the original "no raise" assertion is falsifiable, not vacuous).
- Reverted immediately; full targeted suite re-confirmed green (`uv run pytest tools/harness_config/tests/test_effective_packages.py tools/harness_lint/tests/test_package_facts_override.py -x -q` → 6 passed; `uv run pytest examples/log-parser/tests/test_package_facts_override_instance.py -x -q` → 2 passed).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `effective_packages()` is the single public MONO-03 entry point; Phase 48/49 can import it in-process for per-package convention profiles and `/impact` without re-deriving the override layer.
- The pre-existing `test_core_no_example_dep.py` failure (see Issues Encountered) remains open — a future plan (or Plan 47-05, which already touches the derived-artifact/CI wiring) should decide whether to exempt committed `.ambr` snapshots from the GEN-04 scanner or scrub example rows from the snapshot fixture.
- No architectural changes; `components()`, `load_project()`, `build_facts()` signatures from prior plans are unchanged and reused verbatim.

---
*Phase: 47-package-facts*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: tools/harness_config/loader.py
- FOUND: tools/harness_config/__init__.py
- FOUND: tools/harness_config/tests/test_effective_packages.py
- FOUND: tools/harness_lint/tests/test_package_facts_override.py
- FOUND: examples/log-parser/tests/test_package_facts_override_instance.py
- FOUND: .planning/phases/47-package-facts/deferred-items.md
- FOUND: .planning/phases/47-package-facts/47-03-SUMMARY.md
- FOUND commit: fb224d3 (feat)
- FOUND commit: adc4eac (test)
- FOUND commit: 0ac082b (docs: plan summary)
