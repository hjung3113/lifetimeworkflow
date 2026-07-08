---
phase: 04-plugins-hooks
plan: 02
subsystem: infra
tags: [hooks, pretooluse, secret-scan, stdin-adapter, permission-resolver, uv-workspace, tdd]

# Dependency graph
requires:
  - phase: 03-permissions (CONFIG-02)
    provides: tools.harness_perms.resolve_path / load_matrix — reused verbatim (D-02) for *.env path-deny
provides:
  - Shared tools/hooks stdin adapter (_stdin.parse_event / emit_deny / emit_block / read_stdin) — the seam every Phase-4 gate imports
  - tools/hooks uv workspace member skeleton (package=false, zero deps) that plans 03/04/05 drop gate modules into without file collisions
  - HOOK-02 secret_scan PreToolUse gate (AWS key / PEM header / assignment-shape content + *.env path deny, fixture allow-list)
affects: [04-03 contract-guard, 04-04 polyglot-boundary, 04-05 stop-gate, 04-06 composition]

# Tech tracking
tech-stack:
  added: []  # stdlib-only (json/re/sys/dataclasses) + reused resolver; dependencies=[]; no new packages (T-04-SC)
  patterns:
    - "Thin hook-stdin adapter (_stdin) as the single JSON<->decision seam for all Phase-4 gates"
    - "PEP 562 lazy package re-export (mirrors tools.harness_perms) to survive pytest conftest bootstrap"
    - "Composition-safe path deny: gate feeds resolver a SECRET-specific glob subset, never the full matrix deny key"
    - "Shape-anchored secret regex + fixture allow-list (not generic entropy) to kill false positives"

key-files:
  created:
    - tools/hooks/pyproject.toml
    - tools/hooks/__init__.py
    - tools/hooks/_stdin.py
    - tools/hooks/secret_scan.py
    - tools/hooks/tests/__init__.py
    - tools/hooks/tests/conftest.py
    - tools/hooks/tests/test_stdin.py
    - tools/hooks/tests/test_secret_scan.py
  modified:
    - uv.lock

key-decisions:
  - "secret_scan feeds resolve_path only SECRET_PATH_GLOBS = ['*.env','**/*.env'] — NOT the full matrix constitution deny key — so it does not shadow contract-guard's GOLDEN_APPROVE_HUMAN bypass (Blocker-1 / 04-06 composition invariant)"
  - "parse_event is fail-safe: malformed/empty/non-object stdin yields a sentinel Event() (all fields '') that maps to 'no decision' — a broken payload never crashes the gate (T-04-05)"
  - "Secret detection is shape-anchored (AWS AKIA, PEM header, secret|token|api_key = 16+ chars) plus a tests/golden/normalize-fixtures allow-list rather than Shannon entropy, to avoid tripping the repo's own high-entropy fixtures (Pitfall 5 / T-04-04)"

patterns-established:
  - "Phase-4 gate module shape: import _stdin (parse_event/emit_deny) + reused resolver; pure decide(); main() prints deny JSON on hit / silent exit 0 otherwise; guard raise SystemExit(main())"
  - "Virtual uv member per gate package (package=false, dependencies=[]) with tests/conftest.py inserting repo root on sys.path (parents[3])"

requirements-completed: [HOOK-02]

# Metrics
duration: 7min
completed: 2026-07-08
---

# Phase 4 Plan 02: Shared hook stdin adapter + HOOK-02 secret_scan Summary

**Stdlib-only tools/hooks uv member: a fail-safe Claude PreToolUse stdin adapter (parse_event/emit_deny/emit_block) shared by all Phase-4 gates, plus the HOOK-02 secret_scan gate that denies AWS-key/PEM/assignment-shape content and *.env paths (via the reused CONFIG-02 resolver over a SECRET-specific glob subset) while explicitly NOT shadowing the constitution-plane bypass.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-07-08T12:34:27Z
- **Completed:** 2026-07-08T12:41:24Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 9 (8 created, uv.lock updated)

## Accomplishments
- Created the `tools/hooks` uv workspace member skeleton (`pyproject.toml` package=false / zero deps, PEP 562 lazy-re-export `__init__.py`) that plans 03/04/05 add sibling gate modules into without touching each other's files.
- Implemented the shared `_stdin` adapter: `parse_event(text)->Event` (frozen dataclass; missing keys default to `""`; malformed/empty/non-object stdin -> safe sentinel), `read_stdin()` (try/except-wrapped), `emit_deny` (PreToolUse `permissionDecision:"deny"` shape), `emit_block` (top-level `{"decision":"block"}` shape for later Post/Stop gates).
- Delivered HOOK-02 `secret_scan`: `decide(file_path, content)` denies on a `*.env` path (reused `resolve_path` over `SECRET_PATH_GLOBS`) OR a shape-anchored content match not under the `tests/`/`golden/`/`libs/normalize-fixtures/` allow-list; `main()` wires `_stdin` -> `decide` -> `emit_deny` JSON on hit.
- Proved the composition invariant with a test: a constitution-plane path (`contracts/x.schema.json`) with no secret content is NOT denied — secret_scan does not shadow contract-guard's approval bypass.

## Task Commits

Each TDD gate was committed atomically (test -> impl):

1. **Task 1 RED: shared stdin adapter tests** - `b7e35d6` (test)
2. **Task 1 GREEN: shared stdin adapter impl** - `7b4462f` (feat)
3. **Task 2 RED: HOOK-02 secret_scan tests** - `4bac8df` (test)
4. **Task 2 GREEN: HOOK-02 secret_scan impl** - `8495793` (feat)
5. **Style: ruff format + import-sort hooks tests** - `4b2c202` (style)

_Note: commit `fb71bf6 test(04-01)` interleaves here — it belongs to a concurrent 04-01 executor, not this plan._

## Files Created/Modified
- `tools/hooks/pyproject.toml` - Virtual uv member (package=false, dependencies=[]) registering the gate package.
- `tools/hooks/__init__.py` - PEP 562 lazy re-export of `parse_event`/`emit_deny`/`emit_block`/`read_stdin`/`Event`.
- `tools/hooks/_stdin.py` - Fail-safe Claude hook-stdin adapter: `Event` frozen dataclass, `parse_event`, `read_stdin`, `emit_deny`, `emit_block`.
- `tools/hooks/secret_scan.py` - HOOK-02 PreToolUse gate: `SECRET_PATH_GLOBS`, shape-anchored `PATTERNS`, `ALLOWLIST_PREFIXES`, `decide()`, `main()`.
- `tools/hooks/tests/{__init__.py,conftest.py}` - Test package + repo-root sys.path wiring (parents[3], mirrors harness_perms).
- `tools/hooks/tests/test_stdin.py` - 9 tests: field extraction, defaults, frozen-ness, malformed/empty/non-object sentinel, both decision shapes.
- `tools/hooks/tests/test_secret_scan.py` - 16 tests: content denies, *.env path deny, allow-list passes, constitution-plane non-shadow, main() stdin round-trips.
- `uv.lock` - New virtual member `logparser-hooks` registered (no new packages).

## Decisions Made
- **SECRET-specific glob subset, not the full deny key** — `secret_scan` calls `resolve_path(SECRET_PATH_GLOBS, path)` where `SECRET_PATH_GLOBS = ["*.env","**/*.env"]`. It deliberately never reads the full matrix constitution deny key; feeding the resolver the constitution globs would make any-deny-wins aggregation block a constitution write even with `GOLDEN_APPROVE_HUMAN`, killing contract-guard's bypass (Blocker-1 fix, 04-06). Verified by both a `decide()` unit test and a `grep -q "path_deny_globs"` negative check on the source.
- **Fail-safe adapter, gate-chosen posture** — `_stdin` maps malformed input to a sentinel (`Event()`); `secret_scan` treats that as no-hit (fail-open for an advisory gate that has no file to guard). Individual future gates can layer fail-closed on top.
- **Shape-anchored + allow-list over entropy** — avoids flagging the repo's own high-entropy fixtures; the `GOLDEN_APPROVE_HUMAN` token in a test file is explicitly asserted un-flagged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff lint/format on the new test files**
- **Found during:** Post-Task-2 verification
- **Issue:** `test_secret_scan.py` had E501 long-line violations and `test_stdin.py` had an I001 import-order nit — the repo wires ruff into pre-commit/CI, so unformatted files would fail the gate.
- **Fix:** `ruff check --fix` + `ruff format` on `tools/hooks/`; re-ran the 25 hook tests (still green).
- **Files modified:** tools/hooks/tests/test_stdin.py, tools/hooks/tests/test_secret_scan.py
- **Verification:** `ruff check tools/hooks/` -> All checks passed; `ruff format --check` -> clean.
- **Committed in:** `4b2c202` (style)

**2. [Docstring wording] avoid literal `path_deny_globs` token in secret_scan.py**
- **Found during:** Task 2 acceptance-criteria check
- **Issue:** The plan's acceptance criterion greps the source to prove secret_scan does NOT reference the full `path_deny_globs` key; my initial docstring/comment mentioned the literal token, tripping the negative grep.
- **Fix:** Reworded the docstring and comment to say "the full matrix constitution deny key" instead of the literal identifier — behavior unchanged, `resolve_path` still reused.
- **Files modified:** tools/hooks/secret_scan.py
- **Verification:** `grep -q "path_deny_globs" tools/hooks/secret_scan.py` -> absent; `grep -q "resolve_path"` -> present.
- **Committed in:** `8495793` (folded into the Task 2 GREEN commit)

---

**Total deviations:** 2 (1 blocking Rule-3 lint, 1 acceptance-driven wording). No scope creep — all within HOOK-02.
**Impact on plan:** Both necessary to pass the repo's ruff gate and the plan's own acceptance grep. Behavior identical to the plan spec.

## Issues Encountered
- **Concurrent 04-01 executor broke `uv run` mid-plan.** A parallel agent created `tools/polyglot_lint/` (matching the `tools/*` workspace glob) without a `pyproject.toml` first, so `uv run` failed workspace resolution ("member missing pyproject.toml"). This is external, out-of-scope work — per the scope boundary I did NOT touch it. I verified my gates via the already-synced venv interpreter (`.venv/bin/python -m pytest --ignore=tools/polyglot_lint`, 252 passed) during that window. The parallel agent subsequently added its `pyproject.toml` and its `lint.py`, after which the plan's exact `uv run pytest` full-suite command passed cleanly (270 passed, 2 skipped). No action needed on my side; noted for awareness only.

## Verification Results
- `uv run pytest tools/hooks/tests -x -q` -> **25 passed** (9 stdin + 16 secret_scan).
- `uv run pytest` (full suite) -> **270 passed, 2 skipped** (the 2 skips are the pre-existing dotnet-not-installed golden-runner skips, 01-06). No regression.
- Manual demos (all exit 0): real AWS-key write -> deny JSON; identical string under `tests/` -> silent allow; `contracts/x.schema.json` (no secret) -> silent allow.
- `grep -q "path_deny_globs" secret_scan.py` -> absent (SECRET subset only); `grep -q "resolve_path"` -> present (resolver reused, D-02).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Shared `tools/hooks/_stdin` seam + member skeleton are ready for 04-03 (contract-guard), 04-04 (polyglot-boundary), 04-05 (stop-gate) to add sibling gate modules.
- Composition invariant honored: secret_scan leaves the constitution plane to contract-guard, so 04-06 aggregation can any-deny-wins without the two gates fighting over the `GOLDEN_APPROVE_HUMAN` bypass.
- `emit_block` (top-level `{"decision":"block"}`) is in place but unused until the PostToolUse/Stop gates land in later plans.

## Self-Check: PASSED

All 8 created source/test files + SUMMARY.md exist on disk; all 5 task commits (b7e35d6, 7b4462f, 4bac8df, 8495793, 4b2c202) present in git history.

---
*Phase: 04-plugins-hooks*
*Completed: 2026-07-08*
