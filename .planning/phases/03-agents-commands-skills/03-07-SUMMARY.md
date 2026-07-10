---
phase: 03-agents-commands-skills
plan: 07
subsystem: testing
tags: [strangler-fig, golden-baseline, refusal-gate, command-macro, contract-first, uv-workspace]

# Dependency graph
requires:
  - phase: 03-04
    provides: golden-adjacent command macros + harness_lint glob validator (test_commands.py)
  - phase: 03-03
    provides: dotnet-engineer / python-engineer personas the migration commands route to
  - phase: 01-06
    provides: tools.golden_runner.approve GoldenApprovalRefused exit-3 refusal shape (mirrored)
provides:
  - Runnable /strangler-step baseline-refusal gate (tools/strangler_guard) — refuses (exit 3) without a captured legacy golden .verified baseline
  - /strangler-step command macro (gate-first, single-path, /golden-parity-mandatory)
  - /new-normalization-rule order-enforcing scaffold (contract -> (input,expected) data case -> failing code stub)
affects: [phase-04-hooks, migration, contract-guard]

# Tech tracking
tech-stack:
  added: [logparser-strangler-guard (virtual uv member, stdlib-only)]
  patterns:
    - "Refuse-without-baseline gate (Pattern 5): machine gate mirrors approve.py GoldenApprovalRefused -> exit 3, never fabricates a baseline"
    - "Order-enforcing scaffold (Pattern 4): mandated order + intentional failing stub so the sequence cannot be silently skipped"

key-files:
  created:
    - tools/strangler_guard/guard.py
    - tools/strangler_guard/__main__.py
    - tools/strangler_guard/__init__.py
    - tools/strangler_guard/pyproject.toml
    - tools/strangler_guard/tests/test_refusal.py
    - tools/strangler_guard/tests/conftest.py
    - tools/strangler_guard/tests/__init__.py
    - harness/commands/strangler-step.md
    - harness/commands/new-normalization-rule.md
  modified:
    - uv.lock

key-decisions:
  - "Target path -> golden case slug is deterministic (re.sub non-alnum -> '-'), reproducible by the golden plane and the seeding test; guard reads <golden_dir>/<slug>/expected/baseline.verified.tsv with a tolerant *.verified* fallback"
  - "Guard is stdlib-only (pathlib + re); uv.lock changes only register the virtual member (no external deps) — satisfies the stdlib-only criterion"
  - "Added __main__.py + tests/conftest.py beyond the plan file list (Rule 3): required for `python -m tools.strangler_guard` invocation and namespace-package test import path"

patterns-established:
  - "Pattern 5 refuse-without-baseline: require_baseline raises StranglerRefused; main() maps to exit 3 (mirrors approve.py); never creates a baseline"
  - "Pattern 4 order-enforcing scaffold: /new-normalization-rule forces contract -> data case -> failing code stub (intentional per D-06)"

requirements-completed: [CMD-05, CMD-06]

# Metrics
duration: 9min
completed: 2026-07-08
---

# Phase 3 Plan 07: Migration commands (strangler refusal gate + normalization-rule order scaffold) Summary

**Runnable /strangler-step baseline-refusal gate (tools/strangler_guard, refuses with exit 3 when no captured legacy golden .verified baseline exists, mirroring approve.py) plus two migration command macros — /strangler-step (gate-first, single-path, /golden-parity-mandatory) and /new-normalization-rule (contract -> data-case -> failing-stub order scaffold).**

## Performance

- **Duration:** 9 min
- **Started:** 2026-07-08T09:49:04Z
- **Completed:** 2026-07-08
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Runnable strangler baseline-refusal gate: `require_baseline` returns the captured `.verified` baseline for a target path or raises `StranglerRefused`; `main()` maps refusal to exit 3, never fabricates a baseline (P10 / T-03-24).
- `/strangler-step` macro runs the gate FIRST (`python -m tools.strangler_guard $ARGUMENTS`, list-form subprocess — no shell interpolation, T-03-27), aborts on refusal, extracts one path only, requires `/golden` parity green; big-bang / self-blessing forbidden.
- `/new-normalization-rule` macro enforces the mandated order — contract entry → data-based `(input, expected)` case → **failing** code stub (intentional per D-06, Pattern 4) — so contract-first cannot be silently skipped (T-03-26).
- Both commands carry valid frontmatter with routing-trigger descriptions and real Plan-03 personas (dotnet-engineer / python-engineer), no real model IDs.

## Task Commits

1. **Task 1 (RED): failing refusal test** - `7b450ad` (test)
2. **Task 1 (GREEN): runnable strangler baseline-refusal gate** - `0f5b555` (feat)
3. **Task 2: /strangler-step + /new-normalization-rule macros** - `ed536f8` (feat)

**Plan metadata:** (final docs commit — this SUMMARY + STATE.md + ROADMAP.md)

## Files Created/Modified
- `tools/strangler_guard/guard.py` - `require_baseline` / `StranglerRefused` / `baseline_path` / `main`; refuses without a captured baseline, exit 3.
- `tools/strangler_guard/__main__.py` - enables `python -m tools.strangler_guard <target-path>`.
- `tools/strangler_guard/pyproject.toml` - virtual uv member (`logparser-strangler-guard`, `package = false`, stdlib-only).
- `tools/strangler_guard/tests/test_refusal.py` - refusal raises + main exit 3 + never-fabricates; affirmative path returns baseline.
- `tools/strangler_guard/tests/conftest.py`, `tests/__init__.py` - namespace-package sys.path wiring.
- `harness/commands/strangler-step.md` - gate-first single-path migration macro (agent: dotnet-engineer).
- `harness/commands/new-normalization-rule.md` - contract→data→failing-stub order scaffold (agent: python-engineer).
- `uv.lock` - registers the `logparser-strangler-guard` virtual member (no external deps).

## Decisions Made
- **Deterministic target→baseline mapping.** `require_baseline` derives a golden case slug from the target path (`re.sub(r"[^a-z0-9]+","-", …)`) and checks `<golden_dir>/<slug>/expected/baseline.verified.tsv`, with a tolerant `*.verified*` glob fallback under the case dir. Reproducible by both the golden plane and the seeding test.
- **Refusal shape mirrors approve.py exactly.** `StranglerRefused` → exit 3, message starts `REFUSED: no captured legacy golden baseline`; the load-bearing assertions are the refusals (approve.py discipline).
- **Stdlib-only.** No external deps added; the only `uv.lock` change is the virtual-member registration.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `__main__.py` and `tests/conftest.py` beyond the plan's file list**
- **Found during:** Task 1
- **Issue:** The plan file list omitted `__main__.py` (required for `python -m tools.strangler_guard` — the exact invocation in acceptance criteria and the command macro) and a test `conftest.py` (required for `import tools.strangler_guard...` to resolve in the namespace-package layout, mirroring docs_sync/memory_regen).
- **Fix:** Added `tools/strangler_guard/__main__.py` and `tools/strangler_guard/tests/conftest.py`.
- **Files modified:** tools/strangler_guard/__main__.py, tools/strangler_guard/tests/conftest.py
- **Verification:** `uv run python -m tools.strangler_guard nonexistent/path` exits 3; test suite imports and passes.
- **Committed in:** `0f5b555` (Task 1 GREEN) / `7b450ad` (conftest with RED test).

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for the specified invocation and test import path. No scope creep.

## Issues Encountered
None. All acceptance criteria and full-suite verification green on first pass.

## Verification

- `uv sync --all-packages` — green; uv.lock change is member registration only (no external deps).
- `uv run pytest tools/strangler_guard/tests/test_refusal.py -x -q` — 5 passed.
- `uv run python -m tools.strangler_guard nonexistent/path` — exit 3, prints REFUSED.
- `uv run pytest tools/harness_lint/tests/test_commands.py -x -q` — 45 passed (both new commands validated by the glob).
- `uv run pytest` (full suite) — 227 passed, 2 skipped (pre-existing .NET egress skips, 01-06).

## Known Stubs
None. The `/new-normalization-rule` macro *documents* an intentional failing code stub as its forcing function (D-06, Pattern 4) — that is command guidance, not a stub in this plan's own deliverables.

## Next Phase Readiness
- **Phase 3 is COMPLETE (7/7 plans).** All 9 command macros authored (8 golden-adjacent + 3 migration; docs-sync counted in golden-adjacent tooling), 5 agents, 7 skills, permission resolver, docs_sync generator, and the strangler refusal gate.
- Runtime enforcement of these gates (contract-guard deny, permission hooks) lands in Phase 4; this plan ships the runnable refusal + structural validation.
- Standing blocker unchanged: .NET 10 SDK egress-blocked (BOOT-01) — golden end-to-end spawn still deferred; the normalize+diff and refusal paths are proven without a live .NET runtime.

## Self-Check: PASSED

All created files present on disk; all task commits (`7b450ad`, `0f5b555`, `ed536f8`) present in git history.

---
*Phase: 03-agents-commands-skills*
*Completed: 2026-07-08*
