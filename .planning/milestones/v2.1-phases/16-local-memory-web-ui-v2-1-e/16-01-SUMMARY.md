---
phase: 16-local-memory-web-ui-v2-1-e
plan: 01
subsystem: testing
tags: [pytest, syrupy, uv-workspace, pointer-index, memory-ui, red-tests, dependency-injection]

# Dependency graph
requires:
  - phase: 14-write-path-anti-churn
    provides: tools.agree.write (add/retire, AgreementRefused) — the sanctioned agreement writer the routes delegate to
  - phase: 02-memory-planes
    provides: tools/memory_regen DERIVED-generator template (repo_map.py) + tmp_agreements_tree corpus
provides:
  - New tools/memory_ui uv workspace member (zero-dep, package=false) enrolled in uv.lock
  - Shared Wave-0 test conftest re-exporting the synthetic tmp_agreements_tree corpus
  - tmp_pointer_scan_tree fixture (state + active/retired agreements + docs + AGENTS.md, planner decoy)
  - RED tests pinning the pointer-index generator API (build_index/render_md/write/DERIVED_HEADER)
  - RED tests pinning the pure route-function API (list/view/add/retire/save_progress) + orphan flow
affects: [16-02-pointer-index, 16-03-routes, 16-04-wiring, 16-05-referential-integrity]

# Tech tracking
tech-stack:
  added: []  # zero external packages (D-16-01, stdlib only); only the zero-resolution member entry hits uv.lock
  patterns:
    - "Interface-first RED: tests import the target module deferred (inside each test body) so an unimplemented module still COLLECTS all named tests"
    - "Injected-dir DI in tests: every route/generator call threads tmp state_dir/agreements_dir/derived_dir/base_dir — no real plane, no socket"
    - "Seeded derived/pointer-index.json injects the orphan surface so referential-integrity tests read a synthetic index"

key-files:
  created:
    - tools/memory_ui/pyproject.toml
    - tools/memory_ui/__init__.py
    - tools/memory_ui/tests/__init__.py
    - tools/memory_ui/tests/conftest.py
    - tools/memory_ui/tests/test_routes.py
    - tools/memory_ui/tests/test_referential_integrity.py
    - tools/memory_regen/tests/test_pointer_index.py
  modified:
    - tools/memory_regen/tests/conftest.py
    - uv.lock

key-decisions:
  - "Deferred the target-module import into each test body so the RED files COLLECT all named tests despite the unimplemented module (the interface-first contract Wave-1/2 build against)"
  - "Referential-integrity tests inject a seeded derived/pointer-index.json (matches the architecture diagram 'UI reads the JSON') rather than hardcoding a scan-root path the retire signature does not expose"
  - "Named the pointer-index test file test_pointer_index.py per the PLAN frontmatter (RESEARCH/PATTERNS called it test_pointer_index_determinism.py — followed the plan)"

patterns-established:
  - "RED-collect discipline: unimplemented modules are imported inside test functions, not at module top, so pytest --collect-only lists every test and the interface stays visible"
  - "Word-boundary slug fixture: docs/guide.md carries both a real 'plan' reference (line 3) and a 'planner' decoy (line 4) so the false-positive guard is falsifiable"

requirements-completed: [MEM2-07]

# Metrics
duration: 14min
completed: 2026-07-18
---

# Phase 16 Plan 01: Wave-0 Test Infrastructure Summary

**Enrolled the zero-dep `tools/memory_ui` workspace member and authored 15 RED tests that pin the pointer-index generator API and the pure route-function API (list/view/add/retire/save-progress + orphan surface-and-confirm) entirely against injected tmp dirs — no real `.memory/` plane touched, no socket opened.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-07-18T01:33Z
- **Completed:** 2026-07-18
- **Tasks:** 3
- **Files modified:** 9 (7 created, 2 modified)

## Accomplishments
- New `tools/memory_ui/` uv workspace member enrolled (auto-picked by the `tools/*` glob); `uv.lock` gained ONLY the zero-resolution member entry (6 lines), no unrelated resolution churn.
- Shared test conftest re-exports the synthetic `tmp_agreements_tree` corpus and a new `tmp_pointer_scan_tree` fixture (state files + one active + one retired agreement + a `docs/` tree + a single-file `AGENTS.md`, with a `planner` decoy line).
- 6 RED tests pin the pointer-index generator API (determinism via write→hash→delete→regenerate, DERIVED header + no timestamp/float, no `.memory/derived/` self-reference, word-boundary slug, referrer shape `{file,line,kind}` sorted, committed-snapshot reference).
- 9 RED tests pin the route API (SC1: list/view/add/retire/progress-save; SC3: orphan 409 + confirm-to-proceed with referrer docs left byte-unchanged) — all threading injected tmp dirs, delegating agreement writes to `tools.agree.write` via a spy.

## Task Commits

Each task committed atomically:

1. **Task 1: Enroll member + shared conftest & fixtures** - `fa3748b` (feat)
2. **Task 2: RED tests for the pointer-index generator** - `c87b9e0` (test)
3. **Task 3: RED tests for routes + referential integrity** - `2b38d25` (test)

_Wave-0 authors RED tests only; the RED state is the intended output — implementation arrives in 16-02/16-03/16-04/16-05._

## Files Created/Modified
- `tools/memory_ui/pyproject.toml` - Zero-dep member (`logparser-memory-ui`, `dependencies = []`, `package = false`)
- `tools/memory_ui/__init__.py`, `tools/memory_ui/tests/__init__.py` - Namespace-member package inits (empty)
- `tools/memory_ui/tests/conftest.py` - `parents[3]` sys.path wiring + re-export of `tmp_agreements_tree`
- `tools/memory_ui/tests/test_routes.py` - RED: list/view/add/retire/save-progress route API (SC1)
- `tools/memory_ui/tests/test_referential_integrity.py` - RED: orphan surface-and-confirm (SC3)
- `tools/memory_regen/tests/test_pointer_index.py` - RED: generator determinism + scan-correctness (SC2)
- `tools/memory_regen/tests/conftest.py` - Added `tmp_pointer_scan_tree` fixture (writes only under `tmp_path`)
- `uv.lock` - Zero-resolution member entry only

## Decisions Made
- **Deferred imports for RED collectibility.** The target modules (`tools.memory_regen.pointer_index`, `tools.memory_ui.routes`) do not exist yet; importing them at module top would turn collection into an error and hide the test names. Importing inside each test body keeps all 15 tests collectible (the interface-first contract) while they fail at call time — the intended RED state.
- **Injected seeded pointer-index for the orphan flow.** `retire_agreement`'s documented signature exposes `derived_dir` (not `base_dir`/`scan_roots`), so the referential-integrity tests seed `derived_dir/pointer-index.json` — consistent with the RESEARCH architecture diagram ("the UI reads `pointer-index.json`") and never touching a real plane.
- **File naming followed the PLAN.** Used `test_pointer_index.py` (PLAN frontmatter + Task 2 `<files>`); RESEARCH/PATTERNS referred to `test_pointer_index_determinism.py`. The plan is authoritative and its verify command greps `test_pointer_index.py`.

## Deviations from Plan

None - plan executed exactly as written. (`uv sync` transiently pruned the memory_regen tree-sitter/networkx toolchain — a documented consequence of a bare `uv sync` on a member whose deps are absent from the virtual root, decision 02-01; restored with `uv sync --all-packages`. No file impact.)

## Issues Encountered
- Bare `uv sync` uninstalled the pinned `tree-sitter`/`networkx` wheels (expected per STATE decision 02-01). Restored the full env with `uv sync --all-packages`; `uv.lock` delta remained exactly the zero-dep member entry.

## Verification
- `uv run pytest tools/memory_ui tools/memory_regen/tests/test_pointer_index.py --collect-only -q` → 15 tests collected (all named tests present).
- Full non-example suite: `15 failed, 659 passed` — the 15 failures are exactly the authored RED tests; the 659 previously-passing tests are unchanged (no regression).
- `git status --short .memory/` clean after every test run (no real agreement or derived file authored).
- `git diff` on `uv.lock` shows only the `logparser-memory-ui` virtual member entry.

## Next Phase Readiness
- 16-02 implements `tools/memory_regen/pointer_index.py` against the 6 pinned generator tests (and generates the `.ambr` snapshot on first green run — intentionally NOT pre-seeded here).
- 16-03 implements `tools/memory_ui/routes.py` (+ `server.py`, `page.py`, `__main__.py`, `_stamp.py`) against the pinned route signatures.
- 16-05 implements the orphan surface-and-confirm reconciliation against the referential-integrity tests.
- No blockers introduced. `.NET` egress blocker (BOOT-01) is unrelated to this Python-only phase.

## Self-Check: PASSED

All created files exist on disk; all three task commits (`fa3748b`, `c87b9e0`, `2b38d25`) are present in git history.

---
*Phase: 16-local-memory-web-ui-v2-1-e*
*Completed: 2026-07-18*
