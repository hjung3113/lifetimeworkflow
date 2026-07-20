---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
plan: 01
subsystem: infra
tags: [uv-workspace, task-control, cas, atomic-write, python-stdlib]

# Dependency graph
requires:
  - phase: 20 (task-control)
    provides: "tools/task_control/manager.py's _atomic_create/_cas_write/missing_artifacts idiom, reused (copied, not imported) by batch.py"
  - phase: 26 (adoption_scan)
    provides: "tools/adoption_scan/pyproject.toml + tests/conftest.py sys.path wiring shape, cloned verbatim for the new sibling member"
provides:
  - "tools/adoption_apply — new zero-dependency uv workspace member, auto-discovered by root tools/* wildcard"
  - "batch_id_for()/create_or_resume_batch()/read_status()/update_status() — the .workflow/tasks/<id>/artifacts/adoption/<batch-id>/ layout, content-derived batch id (D-02), CAS-guarded status mutation"
affects: [27-02, 27-03, 27-04, 27-05, 27-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Adoption batch = new artifact kind under manager.py::missing_artifacts()'s existing artifacts/<kind>/<run-id>/ convention — zero manager.py change"
    - "batch.py carries its own copy of the tempfile.mkstemp+os.link/os.replace+fcntl.flock idiom rather than importing manager.py's private underscore functions across the package boundary"

key-files:
  created:
    - tools/adoption_apply/pyproject.toml
    - tools/adoption_apply/__init__.py
    - tools/adoption_apply/__main__.py
    - tools/adoption_apply/batch.py
    - tools/adoption_apply/tests/__init__.py
    - tools/adoption_apply/tests/conftest.py
    - tools/adoption_apply/tests/test_batch_layout.py
  modified:
    - uv.lock

key-decisions:
  - "D-01 upheld: zero edit to contracts/harness/task-control/transitions.json — a batch is purely additive evidence, never a phase-transition gate"
  - "D-02 implemented: <batch-id> = sha256(target_ref|UTC-date)[:16], deterministic per (target_ref, discover-day)"
  - "batch.py does not import manager.py's private _atomic_create/_cas_write — it copies the exact sequence to avoid a private cross-package import, per 27-RESEARCH's Don't Hand-Roll guidance"

patterns-established:
  - "Task-local batch layout: artifacts/adoption/<batch-id>/status.json satisfies missing_artifacts()'s artifact-kind convention automatically"

requirements-completed: [ADOPT-04]

# Metrics
duration: 3min
completed: 2026-07-20
---

# Phase 27 Plan 01: Task-local adoption batch scaffold + CAS-guarded status Summary

Stood up `tools/adoption_apply` as a new zero-dependency uv workspace member and implemented
`batch.py`'s content-derived, resume-safe, CAS-guarded `artifacts/adoption/<batch-id>/status.json`
layout — the ADOPT-04 batch-layout half, with zero edits to `tools/task_control/manager.py` or
`contracts/harness/task-control/transitions.json`.

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-20T15:51:59Z
- **Completed:** 2026-07-20T15:54:37Z
- **Tasks:** 2 completed
- **Files modified:** 7 created, 1 modified (uv.lock)

## Accomplishments
- `tools/adoption_apply` is a real, importable, zero-dependency uv workspace member; `uv sync --all-packages` is clean and `uv.lock` gains only the new member's own registration entry (same precedent as Phase 26's `adoption_scan` — commit `8e42966`)
- `batch.py` implements `batch_id_for`/`create_or_resume_batch`/`read_status`/`update_status` per the plan's `<behavior>` block; all 4 tests in `test_batch_layout.py` green, including the two named Nyquist rows (`test_resume_safely`, `test_batch_uses_existing_cas`)
- Zero `contracts/` touched (D-01 verified via `git diff --stat -- contracts/`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Workspace member scaffold** - `159388f` (feat)
2. **Task 2: batch.py — content-derived batch id, CAS-guarded status**
   - RED: `3e6db96` (test) — failing tests, collection error confirms `tools.adoption_apply.batch` did not exist
   - GREEN: `9f00fc8` (feat) — implementation, all 4 tests pass

_TDD task 2 followed RED → GREEN; no REFACTOR commit was needed (implementation was already lint-clean after one line-length fix folded into the GREEN commit)._

## Files Created/Modified
- `tools/adoption_apply/pyproject.toml` - new virtual uv workspace member, cloned from `tools/adoption_scan/pyproject.toml` shape (`package = false`, `dependencies = []`)
- `tools/adoption_apply/__init__.py` - empty, marks the package
- `tools/adoption_apply/__main__.py` - entrypoint importing `tools.adoption_apply.cli:main` (module does not yet exist — authored in a later plan of this phase; this file only needs to be import-syntactically valid, and package-level `import tools.adoption_apply` never executes `__main__.py`)
- `tools/adoption_apply/batch.py` - `BatchError`, `batch_id_for`, `create_or_resume_batch`, `read_status`, `update_status`, `_batch_dir`, plus private `_atomic_create_status`/`_atomic_replace_status` helpers mirroring `manager.py`'s idiom
- `tools/adoption_apply/tests/__init__.py` - empty
- `tools/adoption_apply/tests/conftest.py` - sys.path wiring only (no `tmp_minirepo`-style fixture)
- `tools/adoption_apply/tests/test_batch_layout.py` - 4 tests: resume-safety, different-ref/date mints new batch, CAS stale-writer rejection, exact-increment requirement
- `uv.lock` - gains the new `logparser-adoption-apply` member entry only; no third-party package version changed

## Deviations from Plan

None - plan executed exactly as written. One incidental fix folded into the GREEN commit: `ruff check` flagged an over-100-char docstring line in `read_status`, reformatted to a multi-line docstring before committing (not a deviation from behavior, purely a lint-cleanliness fix applied before the GREEN commit landed).

## Verification

- `uv sync --all-packages` — clean, exits 0
- `git diff --exit-code uv.lock` — clean (member registration was already committed in Task 1; no further drift)
- `uv run pytest tools/adoption_apply -q` — 4 passed
- `git diff --stat -- contracts/ .github/` — empty
- `uv run ruff check tools/adoption_apply/` — all checks passed

## Self-Check: PASSED

- FOUND: tools/adoption_apply/pyproject.toml
- FOUND: tools/adoption_apply/__init__.py
- FOUND: tools/adoption_apply/__main__.py
- FOUND: tools/adoption_apply/batch.py
- FOUND: tools/adoption_apply/tests/__init__.py
- FOUND: tools/adoption_apply/tests/conftest.py
- FOUND: tools/adoption_apply/tests/test_batch_layout.py
- FOUND commit 159388f
- FOUND commit 3e6db96
- FOUND commit 9f00fc8

## Next Steps
- 27-02: `contracts/harness/adoption/approval.schema.json` (constitution-plane, human-ratified) + hash-manifest rebaseline
- 27-03: `apply.py` — structural constitution refusal + atomic/collision-safe/idempotent create + marker-merge (builds directly on this plan's `batch.py`)
