---
phase: 47-package-facts
plan: 01
subsystem: infra
tags: [adoption-scan, dependency-parsing, tomllib, stdlib-only, monorepo]

# Dependency graph
requires: []
provides:
  - "detect_dependencies(path, kind, text) in tools/adoption_scan/detect.py — pure content-in/edges-out dependency-edge parser for pyproject.toml, package.json, *.csproj, go.mod, Cargo.toml"
  - "5 private kind-specific parser helpers, each unit-tested including the Cargo.toml path-vs-registry drop distinction"
affects: [47-02, 47-03, 47-04, 47-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Content-parsing sibling function (not a signature widen): new pure detect_dependencies() beside detect_manifests(), preserving detect.py's no-filesystem-access invariant for every other function in the ladder."

key-files:
  created: []
  modified:
    - tools/adoption_scan/detect.py
    - tools/adoption_scan/tests/test_detect.py

key-decisions:
  - "Helper functions take only (text) — path is accepted by detect_dependencies for signature symmetry with detect_manifests but is otherwise unused, since every parser is content-only."
  - "Unresolvable/unrecognized kind returns [] rather than raising, matching detect.py's other detectors' fail-open register."

patterns-established:
  - "Cargo.toml parser is deliberately scoped to path dependencies only — a plain string/registry spec is silently dropped, never fabricated as an edge."

requirements-completed: [MONO-02]

# Metrics
duration: 12min
completed: 2026-07-29
---

# Phase 47 Plan 01: Package Facts — Dependency Parsing Summary

**Added `detect_dependencies(path, kind, text)` plus 5 kind-specific parsers (pyproject.toml, package.json, .csproj, go.mod, Cargo.toml) to `tools/adoption_scan/detect.py`, proven by 6 new unit tests including a mutation-verified drop-vs-keep distinction for Cargo.toml.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-29T17:47:00Z
- **Completed:** 2026-07-29T17:59:51Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments
- `detect_dependencies(path, kind, text)` dispatches to 5 private helpers on `kind`, returns `[]` for an unrecognized kind, never touches the filesystem.
- Each of the 5 manifest kinds parses declared runtime/dev dependency edges exactly per the CONTEXT.md-locked semantics: pyproject.toml (`[project].dependencies` + PEP 735 `[dependency-groups].dev`, version specifier stripped), package.json (`dependencies`/`devDependencies`), `.csproj` (`<ProjectReference Include>`, path-based), go.mod (both `require (...)` block and single-line `require`), Cargo.toml (path dependencies only — registry/version-string deps dropped).
- `detect_manifests` and every other pre-existing function in `detect.py` are byte-unchanged (verified via `git diff` hunk inspection — only the import block and an append after the last function were touched).
- 6 new unit tests added covering all 5 kinds plus the unrecognized-kind fail-open case; full `tools/adoption_scan` suite (96 tests) green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement detect_dependencies + 5 kind-specific parser helpers** - `83ad913` (feat)
2. **Task 2: Unit-test detect_dependencies for all 5 manifest kinds** - `2c55f07` (test)

**Plan metadata:** (pending — this SUMMARY commit)

## Files Created/Modified
- `tools/adoption_scan/detect.py` - added `detect_dependencies` + `_dependencies_from_{pyproject,package_json,csproj,go_mod,cargo_toml}` + `_DEPENDENCY_PARSER_BY_KIND` dispatch table + `_dependency_bare_name` helper; new stdlib imports (`json`, `re`, `tomllib`, `xml.etree.ElementTree`).
- `tools/adoption_scan/tests/test_detect.py` - 6 new test functions covering all 5 manifest kinds' dependency parsing plus the unrecognized-kind case.

## Decisions Made
- Kept `detect_dependencies`'s `path` parameter unused inside the function body (explicit `del path` with a comment) rather than dropping it from the signature, per the plan's required interface (`detect_dependencies(path, kind, text)`).
- Private helpers take only `text: str` (not `path`) since none of the 5 parsers need the manifest's own path to extract dependency names/paths — keeps each helper minimal and matches the "content-in, edges-out" framing from RESEARCH Pattern 1.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Mutation Verification (acceptance criterion)

Per the plan's Task 2 acceptance criteria, ran mutation checks on the pyproject and Cargo.toml tests before finalizing:
- `test_pyproject_runtime_and_dev_dependencies_parsed`: inverted the expected `kind` for `widget-test-tools` from `"dev"` to `"runtime"` → test FAILED (`AssertionError: assert 'dev' == 'runtime'`) → reverted.
- `test_cargo_toml_path_dependency_kept_registry_dependency_dropped`: inverted the expected entry count/name-set to include the dropped registry dependency (`widget-registry`) → test FAILED (`AssertionError: assert 2 == 3`) → reverted.

Both mutations confirmed the assertions can fail — satisfying this repo's "checks that cannot fail" defect-avoidance requirement.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `detect_dependencies` is ready for Plan 47-02's generator (`tools/memory_regen/package_facts.py`) to call with manifest text it reads off disk, per the plan's `key_links` interface (`detect_dependencies\\(` pattern match).
- No architectural changes; `detect_manifests`'s existing signature/behavior is fully preserved.

---
*Phase: 47-package-facts*
*Completed: 2026-07-29*
