---
phase: 05-despecialization
plan: 04
subsystem: infra
tags: [gen-03, project-config, tomllib, uv-workspace, permission-matrix, ssot, consistency-test]

# Dependency graph
requires:
  - phase: 03-harness-core
    provides: harness/permission-matrix.json + tools.harness_perms.load_matrix (language allow-scopes)
  - phase: 03-harness-core
    provides: harness/agents/{dotnet,python}-engineer.md personas + tools.harness_lint structural-test idiom
provides:
  - "harness/project.toml — GEN-03 language/toolchain SSOT slot ([instance] root + [[languages]] dotnet/python)"
  - "tools/harness_config uv member — stdlib tomllib loader (load_project / languages / language_bash_scopes)"
  - "consistency gate proving matrix scopes + personas derive from the config (config = SSOT, no codegen)"
affects: [06-config-derived-ci-matrix, template-clone-non-dotnet-python]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "config-as-data + thin stdlib consumer (mirrors permission-matrix.json + harness_perms)"
    - "derived-not-hardcoded satisfied by a CONSISTENCY TEST, not codegen (D-03)"
    - "new tools/* uv member as virtual package (package=false, PEP 562 lazy re-export, conftest sys.path wiring)"

key-files:
  created:
    - harness/project.toml
    - tools/harness_config/__init__.py
    - tools/harness_config/loader.py
    - tools/harness_config/pyproject.toml
    - tools/harness_config/tests/conftest.py
    - tools/harness_config/tests/test_loader.py
    - tools/harness_lint/tests/test_language_config.py
  modified:
    - uv.lock

key-decisions:
  - "GEN-03 satisfied via a consistency test (assert hardcoded matrix/personas AGREE with config), not full codegen — per D-03 'codegen is overkill'. Existing hardcoded values reinterpreted as the example instance's declared values; nothing ripped out."
  - "Matrix language allow-scopes derived as 'the bash keys whose decision == allow' rather than a hardcoded literal, so the test reads the same data the resolver enforces."
  - "Implicit 'pytest *' scope folded into language_bash_scopes() (Python's test-runner carries its own allow-scope alongside 'uv *') rather than repeated as a per-language config field."

patterns-established:
  - "config-as-data SSOT slot: harness/project.toml is pure data; loader adds no enforcement; the test is the tamper-evidence"
  - "new uv virtual member scaffold: pyproject (package=false) + PEP 562 lazy __init__ + tests/conftest.py sys.path insert"

requirements-completed: [GEN-03]

# Metrics
duration: 12min
completed: 2026-07-09
---

# Phase 5 Plan 04: GEN-03 Language/Toolchain Config Slot Summary

**harness/project.toml as the language/toolchain SSOT (.NET 10 + Python/uv example instance) with a stdlib-tomllib loader and a consistency gate proving the permission-matrix scopes and engineer personas derive from it — no codegen.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-09T03:45:47Z
- **Completed:** 2026-07-09T03:57Z
- **Tasks:** 2
- **Files modified:** 8 (7 created + uv.lock)

## Accomplishments
- `harness/project.toml`: GEN-03 SSOT slot — `[instance] root=""` + two `[[languages]]` tables (dotnet, python) carrying `id`/`bash_scope`/`test`/`format`/`persona` (+ `sdk_bootstrap` for dotnet). Values are the log-parser example instance's declared toolchains, not a core hardcode.
- `tools/harness_config/`: new `tools/*` uv member (package=false) mirroring `harness_perms`; stdlib `tomllib` loader exposing `load_project()`, `languages()`, and `language_bash_scopes()` (union of bash_scopes + implicit `pytest *`). Zero external dependencies.
- `tools/harness_lint/tests/test_language_config.py`: consistency gate asserting the permission-matrix `dotnet */uv */pytest *` allow-scopes EQUAL the config-derived set, each configured persona file exists, and each language declares a test command. Config is now authoritative.

## Task Commits

Each task was committed atomically:

1. **Task 1: harness/project.toml + harness_config loader (uv member)** - `536c305` (feat)
2. **Task 2: consistency test — matrix scopes + personas derive from config** - `b536e94` (test)
3. **Post-task style fix: wrap docstrings/comments to 100-col ruff limit** - `50555f3` (style)

## Files Created/Modified
- `harness/project.toml` - GEN-03 language/toolchain SSOT slot (data-only, no enforcement)
- `tools/harness_config/loader.py` - stdlib tomllib loader + language_bash_scopes helper
- `tools/harness_config/__init__.py` - PEP 562 lazy re-export of the loader API
- `tools/harness_config/pyproject.toml` - virtual uv member (package=false, deps=[])
- `tools/harness_config/tests/conftest.py` - repo-root sys.path wiring for namespace-package import
- `tools/harness_config/tests/test_loader.py` - loader unit tests (5)
- `tools/harness_lint/tests/test_language_config.py` - GEN-03 consistency gate (3)
- `uv.lock` - registers the in-repo virtual member `logparser-harness-config` only (no external adds)

## Decisions Made
See frontmatter `key-decisions`. Core: GEN-03 met by a consistency test rather than codegen (D-03); hardcoded matrix/persona values are kept and proven consistent with the config, not replaced.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Wrapped over-limit docstrings/comments to the 100-col ruff line-length**
- **Found during:** Post-Task-2 verification (ruff check)
- **Issue:** Four comment/docstring lines in `loader.py` and `test_language_config.py` exceeded the repo's `line-length = 100` (E501), which would fail the `ruff` lint gate (pre-commit + CI).
- **Fix:** Re-wrapped the offending lines; no behavior change.
- **Files modified:** tools/harness_config/loader.py, tools/harness_lint/tests/test_language_config.py
- **Verification:** `uv run ruff check` → All checks passed; affected tests still green (8 passed).
- **Committed in:** `50555f3` (style)

---

**Total deviations:** 1 auto-fixed (1 blocking/lint). **Impact:** cosmetic wrapping only; keeps the ruff gate green. No scope creep.

## Issues Encountered
- A concurrent plan (05-01) landed commit `db4a817` interleaved between this plan's commits. Confirmed disjoint: 05-01 touched only STATE.md + its own SUMMARY; this plan's commits (`536c305`, `b536e94`, `50555f3`) touched only the GEN-03 files. No conflict, no shared files.

## Test Results
- `uv run pytest tools/harness_config tools/harness_lint/tests/test_language_config.py -x -q` → **8 passed**
- `uv run pytest` (full suite) → **357 passed, 2 skipped** (the 2 skips are pre-existing .NET-egress-blocked golden spawns, unrelated to this plan)
- SSOT proof (manual): removing the `dotnet` language from `harness/project.toml` makes `test_matrix_language_scopes_equal_config` FAIL (extra `dotnet *` in matrix), then restored → green. Confirms config is authoritative.
- `uv sync --all-packages` resolves cleanly with the new member.

## Known Stubs
None — the config carries real values (the log-parser example instance) and both loader + gate are fully wired to disk.

## Next Phase Readiness
- `language_bash_scopes()` + `harness/project.toml` are the precondition for the Phase 6 config-derived CI matrix.
- Cloning the repo as a domain-neutral template now = swap the `[[languages]]` tables; the consistency gate keeps matrix/personas honest against whatever the slot declares.

## Self-Check: PASSED
- All 7 created files present on disk; uv.lock modified.
- Commits `536c305`, `b536e94`, `50555f3` present in git log.

---
*Phase: 05-despecialization*
*Completed: 2026-07-09*
