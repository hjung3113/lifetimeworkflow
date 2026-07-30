---
phase: 47-package-facts
plan: 02
subsystem: infra
tags: [derived-artifact, memory-regen, adoption-scan, dependency-graph, monorepo, stdlib-only]

# Dependency graph
requires:
  - phase: 47-01
    provides: "detect_dependencies(path, kind, text) in tools/adoption_scan/detect.py"
provides:
  - "tools/memory_regen/package_facts.py — build_facts()/render()/write()/main(), the derived-plane generator MONO-01/MONO-02 require"
  - ".memory/derived/package-facts.md — the first committed package + dependency graph artifact (23 packages, 2 edges over the real tree)"
affects: [47-03, 47-04, 47-05, 48, 49]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cloned contracts_index.py's rows->render->write->main generator idiom verbatim for a second committed-derived artifact"
    - "Light git ls-files enumeration (not scan.build_inventory) feeding detect.detect_manifests, per CONTEXT.md's resolved Open Question 2"

key-files:
  created:
    - tools/memory_regen/package_facts.py
    - tools/memory_regen/tests/test_package_facts.py
    - tools/memory_regen/tests/__snapshots__/test_package_facts.ambr
  modified: []

key-decisions:
  - "package.json's language column defaults to javascript (no language signal in .claude/package.json), per CONTEXT.md A3"
  - "Dependency edges are resolved and deduplicated in build_facts() (the generator), not in detect_dependencies() (which stays a pure name/kind parser per Plan 47-01)"
  - "Cargo.toml path-dependency resolution normalizes the referenced directory then appends /Cargo.toml before matching a known package's manifest path"

patterns-established:
  - "A second generator (package_facts.py) now shares contracts_index.py's exact rows/render/write/main + DERIVED-header + no-timestamp-no-float determinism contract"

requirements-completed: [MONO-01, MONO-02]

# Metrics
duration: 25min
completed: 2026-07-30
---

# Phase 47 Plan 02: Package Facts — Derived Generator Summary

**Built `tools/memory_regen/package_facts.py`, the first committed `.memory/derived/package-facts.md` (23 packages, 2 dependency edges), and a 12-test suite proving byte-identical determinism plus per-manifest-kind add/remove-a-dependency correctness on synthetic fixtures.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-07-30 (session start)
- **Completed:** 2026-07-30T03:05:10+09:00
- **Tasks:** 2 completed
- **Files modified:** 3 (all new)

## Accomplishments
- `tools/memory_regen/package_facts.py` clones `contracts_index.py`'s rows→render→write→main idiom: `discover_manifests()` (light `git ls-files` walk, not `scan.build_inventory()`) → `detect.detect_manifests` → `tests/fixtures/**` exclusion → `build_facts()` (reads each manifest's text, resolves `_package_id`, calls `detect.detect_dependencies`, resolves declared deps to known package ids/manifest paths, drops the unresolved and the self-referencing) → `render()` (two markdown tables: Packages, Dependency Edges) → `write()`/`main()`.
- `uv run python -m tools.memory_regen.package_facts` produces `.memory/derived/package-facts.md`: 23 packages (24 tracked manifests minus the 1 excluded `tools/adoption_apply/tests/fixtures/polyglot-single/pyproject.toml`), 2 edges (both `.csproj` `ProjectReference`: `Normalize.Tests` → `Normalize`, `ToyConverter` → `Normalize`) — matching RESEARCH's measured real-tree baseline exactly.
- 12 new tests in `tools/memory_regen/tests/test_package_facts.py`: 2 determinism (render-twice, generate/delete/regenerate byte-identical via sha256), 2 structure (DERIVED marker, real-tree package shape), 1 discovery/exclusion (tmp_path `git init` repo proving a `tests/fixtures/**` manifest is dropped), 5 per-manifest-kind add/remove-a-dependency round trips (pyproject.toml, package.json, `.csproj`, go.mod, Cargo.toml — all on synthetic `widget-*` fixtures, since the live tree only exercises 2 of 5 kinds), 1 unresolvable-dependency-is-dropped, and 1 committed syrupy snapshot of `render(build_facts())` over the real tree.
- Mutation check (plan-required acceptance criterion): temporarily made the pyproject.toml round-trip test's "after" rewrite a no-op (still declaring the dependency) — the trailing `assert facts_after["edges"] == []` FAILED with `AssertionError: assert [{'from': 'widget-app', ...}] == []`, proving the assertion is falsifiable; reverted.
- `uv run pytest tools/memory_regen tools/adoption_scan -q` — 190 passed, 6 snapshots passed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement the package_facts.py generator** - `b9252ea` (feat)
2. **Task 2: Test determinism, per-kind add/remove-a-dependency correctness, and snapshot** - `2fb246f` (test)

**Plan metadata:** (pending — this SUMMARY commit)

## Files Created/Modified
- `tools/memory_regen/package_facts.py` - the generator: `_KIND_LANGUAGE`, `_is_excluded`, `discover_manifests`, `_package_id`, `build_facts`, `render`, `write`, `main`.
- `tools/memory_regen/tests/test_package_facts.py` - 12 tests across the 5 guarantee groups.
- `tools/memory_regen/tests/__snapshots__/test_package_facts.ambr` - committed syrupy snapshot of `render(build_facts())` over the real tree.

## Decisions Made
- Followed the plan's `<behavior>` spec exactly for `_package_id`'s per-kind name resolution (pyproject `[project].name`, package.json `name`, `.csproj` basename stem, go.mod `module` directive, Cargo.toml `[package].name`), falling back to the manifest's parent-directory name (or `"."` at repo root) when no declared name exists.
- Dependency-edge resolution logic (path normalization, self-reference drop, dedup, sort) lives entirely in `build_facts()` — `detect.detect_dependencies()` (Plan 47-01) stays untouched and returns only `{"name"/"path", "kind"}` dicts, preserving the sibling-function-not-signature-change pattern from RESEARCH.
- `import json` promoted to a top-level stdlib import (the initial draft used an inline `__import__("json")` to avoid an early edit conflict with the post-write formatter hook — cleaned up before committing).

## Deviations from Plan

None - plan executed exactly as written. `build_facts()`, `render()`, `write()`, `main()`, `discover_manifests()`, `_package_id()`, and `_is_excluded()` all match the plan's `<behavior>` section's specified names and shapes.

## Issues Encountered

None.

## Mutation Verification (acceptance criterion)

Per Task 2's acceptance criteria: temporarily commented out (made a no-op) the dependency-removal rewrite inside `test_pyproject_dependency_add_remove_round_trip`'s "after" phase, so the manifest still declared `dependencies = ["widget-core"]` when the trailing assertion ran.
- Result: `AssertionError: assert [{'from': 'widget-app', 'kind': 'runtime', 'to': 'widget-core'}] == []` — the test FAILED as expected.
- Reverted immediately; full suite re-confirmed green (`uv run pytest tools/memory_regen/tests/test_package_facts.py -x -q -v` → 12 passed, 1 snapshot passed).

This satisfies the repo's "checks that cannot fail" defect-avoidance requirement for the load-bearing MONO-02 criterion-2 proof.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `build_facts()` is the single public entry point Phase 47-03 (`tools/harness_config/loader.py::effective_packages`) and Phase 48/49 will import in-process — never re-parsing the rendered markdown.
- `.memory/derived/package-facts.md` exists on disk but is currently gitignored by the existing `.memory/derived/*` contents-form glob (no `!.memory/derived/package-facts.md` re-inclusion line yet) — that wiring, plus the `stale-derived` CI job widening and `test_ci_stale_derived.py` updates, is explicitly Plan 47-05's job per the plan's `<interfaces>`/RESEARCH Pattern 3. This plan deliberately did not touch `.gitignore` or `ci.yml`.
- No architectural changes; `detect_manifests`/`detect_dependencies` signatures from Plan 47-01 are unchanged and reused verbatim.

---
*Phase: 47-package-facts*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: tools/memory_regen/package_facts.py
- FOUND: tools/memory_regen/tests/test_package_facts.py
- FOUND: tools/memory_regen/tests/__snapshots__/test_package_facts.ambr
- FOUND: .planning/phases/47-package-facts/47-02-SUMMARY.md
- FOUND commit: b9252ea (feat)
- FOUND commit: 2fb246f (test)
- FOUND commit: 5a1a916 (docs: plan summary)
