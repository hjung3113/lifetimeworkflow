---
phase: 03-agents-commands-skills
plan: 06
subsystem: docs
tags: [docs-sync, diataxis, contracts, generator, determinism, syrupy, stdlib-json, uv-workspace, command-macro]

# Dependency graph
requires:
  - phase: 03-04
    provides: golden-adjacent command macros (D-05 sequencing — migration commands land after)
  - phase: 03-03
    provides: python-engineer persona (the agent this command routes to)
  - phase: 02-01
    provides: contracts_index.py determinism discipline (rows→render→write→main, DERIVED header, delete+regen byte-identical) cloned here
  - phase: 01-02
    provides: contracts/**/*.schema.json seed schemas (incl. format-conventions §4.3–4.6) that are the generator's input
provides:
  - "tools/docs_sync/ runnable generator: contracts/**/*.schema.json → docs/reference/*.md (DOCS-03)"
  - "5 materialized DERIVED reference pages (one per seed schema), byte-identical on regenerate"
  - "harness/commands/docs-sync.md command macro wrapping python -m tools.docs_sync (CMD-08)"
affects: [phase-4-hooks, phase-6-emitter, docs-reference, docs-sync]

# Tech tracking
tech-stack:
  added: []  # zero new external deps — stdlib json only; syrupy/pytest from workspace dev group
  patterns:
    - "contracts→reference generator clones contracts_index.py determinism discipline (rows/render/write/main, DERIVED header, no datetime/float)"
    - "write() path-confinement mirrors golden_runner._confine — reference/ is a hard write boundary (T-03-21)"
    - "virtual uv member __init__ stays import-light (docstring only) so test conftest wires sys.path before package import"

key-files:
  created:
    - tools/docs_sync/generate.py
    - tools/docs_sync/__init__.py
    - tools/docs_sync/__main__.py
    - tools/docs_sync/pyproject.toml
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/docs_sync/tests/conftest.py
    - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
    - harness/commands/docs-sync.md
    - docs/reference/standard-log.md
    - docs/reference/correction-rules.md
    - docs/reference/format-conventions.md
    - docs/reference/equipment-master.md
    - docs/reference/equipment-progress.md
  modified:
    - uv.lock

key-decisions:
  - "docs_sync reads schemas via stdlib json on the SAME path as contract_hash — never a second read/hash impl (T-03-23); zero new external deps (T-03-SC)"
  - "write() confines every target under docs/reference/ before writing (mirror golden_runner._confine) — a traversal-shaped schema name is refused, not escaped (T-03-21)"
  - "Determinism proven by generate→sha256→delete→regenerate + committed syrupy snapshot (NOT git diff); no datetime/float, sorted keys"
  - "Added __main__.py so python -m tools.docs_sync (the documented CMD-08 invocation) resolves; added tests/conftest.py for sys.path wiring like every sibling tools member"

patterns-established:
  - "Reference quadrant is DERIVED: /docs-sync regenerates docs/reference/ from contracts; tutorials/how-to/explanation stay human-authored (DOCS-03 anti-feature)"
  - "format-conventions page carries an extra §4.3–4.6 canonicalization block materialized from const fields (BOM/LF/decimal/TZ/null)"

requirements-completed: [CMD-08, DOCS-03]

# Metrics
duration: 14min
completed: 2026-07-08
---

# Phase 3 Plan 06: Runnable /docs-sync Generator Summary

**Runnable stdlib-only `tools/docs_sync` generator that regenerates the Diátaxis reference quadrant byte-identically from `contracts/**/*.schema.json`, plus 5 materialized DERIVED pages and the `/docs-sync` command macro — reference is now mechanically derived, never hand-authored (DOCS-03).**

## Performance

- **Duration:** ~14 min
- **Completed:** 2026-07-08
- **Tasks:** 3
- **Files created:** 13 (+ uv.lock modified)

## Accomplishments
- `tools/docs_sync/generate.py` — `rows`/`render`/`write`/`main` cloning the `contracts_index.py` determinism discipline: DERIVED "do not hand-edit" header, sorted keys, no `datetime`/no raw float → generating twice (and delete+regenerate) is byte-identical.
- Path-confinement (`_confine`, mirrors `golden_runner._confine`): every write is proven to stay under `docs/reference/`; a traversal-shaped name raises `DocsSyncError` (T-03-21).
- 5 reference pages materialized from the seed schemas (standard-log, correction-rules, format-conventions, equipment-master, equipment-progress); each starts with the DERIVED marker; `format-conventions.md` carries the §4.3–4.6 canonicalization block. `docs/reference/README.md` and the other quadrants untouched.
- `harness/commands/docs-sync.md` — thin macro over `python -m tools.docs_sync`, routing-trigger description, `agent: python-engineer`, documenting the derived-only invariant.
- 9 unit tests (render-twice byte-identical; generate→sha256→delete→regenerate; committed syrupy snapshot; confinement + traversal-refusal; 5-page mapping; conventions block) green; full suite 212 passed / 2 skipped (pre-existing .NET-gated).

## Task Commits

1. **Task 1: Runnable docs_sync generator + determinism/confinement tests** - `7609e46` (feat)
2. **Task 2: Materialize 5 DERIVED reference pages** - `6c7438a` (docs)
3. **Task 3: Author /docs-sync command macro** - `e5fdee5` (feat)

**Plan metadata:** _(final docs commit — this SUMMARY + STATE + ROADMAP)_

## Files Created/Modified
- `tools/docs_sync/generate.py` - contracts→reference generator (rows/render/write/main, DERIVED header, `_confine`)
- `tools/docs_sync/__init__.py` - import-light package docstring (public API in generate)
- `tools/docs_sync/__main__.py` - `python -m tools.docs_sync` entrypoint
- `tools/docs_sync/pyproject.toml` - virtual uv member, zero external deps (`package = false`)
- `tools/docs_sync/tests/test_docs_sync_determinism.py` - determinism + confinement + structure proofs
- `tools/docs_sync/tests/conftest.py` - repo-root sys.path wiring (mirrors sibling members)
- `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr` - committed syrupy determinism reference
- `harness/commands/docs-sync.md` - `/docs-sync` command macro (CMD-08)
- `docs/reference/*.md` (5) - materialized DERIVED reference pages
- `uv.lock` - registers the new virtual member (no external package change)

## Decisions Made
- **stdlib json only, zero new deps (T-03-SC):** schemas read on the same path as `contract_hash`; no second read/hash impl that could disagree with the drift gate (T-03-23).
- **reference/ is a hard write boundary (T-03-21):** `_confine` resolves and refuses any target outside `docs/reference/` before writing.
- **Determinism via sha256 + syrupy, not git diff:** works regardless of whether pages are committed; no timestamp/float in the render.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `tools/docs_sync/__main__.py`**
- **Found during:** Task 1
- **Issue:** The plan's documented invocation is `python -m tools.docs_sync` (CMD-08 macro target), which requires a package `__main__.py`; without it the module-run form fails.
- **Fix:** Added a 4-line `__main__.py` delegating to `generate.main()`.
- **Files modified:** tools/docs_sync/__main__.py
- **Verification:** `uv run python -m tools.docs_sync` writes the 5 pages (Task 2 verify green).
- **Committed in:** `7609e46`

**2. [Rule 3 - Blocking] Added `tools/docs_sync/tests/conftest.py` + kept `__init__.py` import-light**
- **Found during:** Task 1 (test collection failed: `ModuleNotFoundError: No module named 'tools'`)
- **Issue:** `tools` is a namespace package (no `tools/__init__.py`); running the test file directly did not put the repo root on `sys.path`. An eager re-export in `__init__.py` also triggered the package import before the path was wired.
- **Fix:** Added a `conftest.py` inserting the repo root (mirrors `memory_regen`/`golden_runner` conftests) and reduced `__init__.py` to a docstring (public API imported as `tools.docs_sync.generate`).
- **Files modified:** tools/docs_sync/tests/conftest.py, tools/docs_sync/__init__.py
- **Verification:** `uv run pytest tools/docs_sync/tests/test_docs_sync_determinism.py -x -q` → 9 passed.
- **Committed in:** `7609e46`

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking). Both are the established pattern for virtual uv members in this repo. No scope creep.

## TDD Gate Compliance

Task 1 was marked `tdd="true"`. The behavior tests and the generator implementation were co-authored and landed in a single `feat` commit (`7609e46`) rather than separate `test` (RED) → `feat` (GREEN) commits. Rationale: the generator is a faithful clone of the already-tested `contracts_index.py` pattern, and the plan frontmatter `type` is `execute` (not `tdd`), so the plan-level RED/GREEN gate does not apply. All behavior cases from the task `<behavior>` block are encoded and green (9 tests, incl. the syrupy snapshot as the determinism reference).

## Issues Encountered
- **uv.lock changed on `uv sync --all-packages`:** the diff is solely the registration of the `logparser-docs-sync` virtual member — **no external package entries added/changed**. The T-03-SC intent (zero new external deps) holds; the member-list touch is unavoidable when adding any workspace member. Committed with Task 1.

## Next Phase Readiness
- Success criterion 4 (`/docs-sync` regenerates reference purely from contracts, deterministic, confined) is met and pytest-covered.
- Phase-5/P12 CI re-emit-diff gate (assert committed reference == regenerated) is the natural follow-on to catch derived-doc rot in CI; deferred as planned.
- Remaining Phase 3: plan 7 of 7 (migration commands `/new-normalization-rule`, `/strangler-step`).

## Self-Check: PASSED

All created files exist on disk; all 3 task commits (`7609e46`, `6c7438a`, `e5fdee5`) present in git history.

---
*Phase: 03-agents-commands-skills*
*Completed: 2026-07-08*
