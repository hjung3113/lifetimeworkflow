---
phase: 02-two-plane-memory-rules
plan: 02
subsystem: infra
tags: [session-start-injection, claude-hooks, opencode-plugin, memory, contract-drift, python]

# Dependency graph
requires:
  - phase: 02-01
    provides: ".memory/ two-plane skeleton + tools/memory_regen uv-workspace member (pinned tree-sitter + networkx)"
  - phase: 01-05
    provides: "tools.contract_drift.run_gate — live drift status reused in the injected payload"
provides:
  - "inject.assemble() — the single injection contract (capped, banner-first, priority-truncated, pointer-only payload) shared by both runtimes"
  - "Claude SessionStart injector wired as the 4th slot in .claude/settings.json (3 existing hooks preserved)"
  - ".claude/hooks/memory-inject.sh — regen + assemble + node-encoded {hookSpecificOutput:{additionalContext}} envelope"
  - "harness/plugins/session-inject.ts — authored-deferred opencode adapter consuming the SAME assembler"
affects: [02-03-contracts-index, 02-04-repo-map, phase-3-config-opencode]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single injection contract, two thin runtime adapters (Claude now, opencode deferred)"
    - "Priority-truncate whole sections (never mid-line) under a char budget"
    - "Node-encode the SessionStart envelope, payload via argv (command-injection defense)"

key-files:
  created:
    - tools/memory_regen/inject.py
    - tools/memory_regen/tests/test_inject_assembler.py
    - tools/memory_regen/tests/test_hook_wiring.py
    - .claude/hooks/memory-inject.sh
    - harness/plugins/session-inject.ts
  modified:
    - .claude/settings.json

key-decisions:
  - "assemble(budget_chars=4000, derived_dir, state_dir) — optional path kwargs added after the documented budget arg so tests inject temp derived trees without touching real .memory/"
  - "Banner (0) + drift (1) are never dropped even below their combined size; only priority>=2 sections are budget-gated"
  - "opencode adapter authored-only, execution deferred (no opencode runtime in container) — RESUME note mirrors the .NET deferral pattern"

patterns-established:
  - "Single injection contract: python -m tools.memory_regen.inject is the ONE payload source; each runtime is a thin envelope wrapper (D-01)"
  - "Graceful degradation: missing Wave-2 generators (repo_map/contracts_index) never break the hook (|| true) — assembler emits a 'pending' pointer"

requirements-completed: [HOOK-05]

# Metrics
duration: 5min
completed: 2026-07-08
---

# Phase 2 Plan 02: Claude SessionStart Injector Summary

**A single `inject.assemble()` injection contract — capped (~1k-token), banner-first, drift-aware, pointer-only payload — wired as the coexisting 4th Claude SessionStart hook, with an authored-deferred opencode adapter consuming the identical assembler.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-07-08T07:01:39Z
- **Completed:** 2026-07-08T07:06:22Z
- **Tasks:** 2
- **Files created/modified:** 6

## Accomplishments
- `inject.assemble()` — the shared injection contract: provisional banner (never dropped) + live drift via `run_gate` (never dropped) + contracts-index summary + repo-map top-N + activeContext pointer, all under a soft ~4000-char cap with whole-section priority-truncation.
- Claude SessionStart injector added as the **4th** `.claude/settings.json` slot; the 3 existing hooks (gsd-check-update.js, gsd-session-state.sh, tools/bootstrap/install.sh) survive byte-for-byte (coexist, not overwrite).
- `.claude/hooks/memory-inject.sh` emits a valid `{hookSpecificOutput:{additionalContext}}` envelope whose first line is the provisional banner; payload passed via node argv (command-injection defense T-02-04).
- Authored-deferred opencode adapter `harness/plugins/session-inject.ts` documents the same contract via `event`=session.created + `chat.system.transform`, with a RESUME note (execution deferred, no opencode runtime here).
- 16 new unit/structural tests green; full workspace suite 60 passed / 2 pre-existing .NET skips.

## Task Commits

1. **Task 1 (RED): failing inject.assemble tests** - `56caa89` (test)
2. **Task 1 (GREEN): implement inject.assemble** - `3b38b3f` (feat)
3. **Task 2: 4th SessionStart slot + hook + opencode stub + wiring test** - `7b0e26f` (feat)

_Task 1 was TDD (test → feat). Task 2 is config+adapter wiring._

## Files Created/Modified
- `tools/memory_regen/inject.py` - The shared assembler: `assemble()`, `BANNER`, section builders (`_drift_summary`, `_contracts_summary`, `_repo_map_topN`, `_active_context_pointer`), `main()` CLI.
- `tools/memory_regen/tests/test_inject_assembler.py` - cap/banner/priority-truncate/pointer-not-body/no-$schema/CLI assertions (11 tests).
- `tools/memory_regen/tests/test_hook_wiring.py` - structural: 4 SessionStart groups, 3 existing survive, injector references memory-inject.sh, opencode stub deferred (5 tests).
- `.claude/hooks/memory-inject.sh` - SessionStart wrapper: best-effort regen + assemble + node-encode envelope.
- `.claude/settings.json` - appended the 4th SessionStart slot.
- `harness/plugins/session-inject.ts` - authored-deferred opencode adapter stub (same contract).

## Decisions Made
- **Optional path kwargs on `assemble()`** (`derived_dir`, `state_dir`) after the documented `budget_chars` arg — preserves the D-01 contract signature while letting tests inject temp derived trees (repo-map present/absent) without mutating the real `.memory/`.
- **Banner + drift never budget-gated** — even at `budget_chars=1` both are emitted, because they carry the non-ignorable provisional invariant (D-02) and the live safety signal; only priority≥2 sections are dropped.
- **Standalone-runnable hook** — `memory-inject.sh` derives the project dir from `${BASH_SOURCE}` when `CLAUDE_PROJECT_DIR` is unset, so `bash .claude/hooks/memory-inject.sh` works in tests and manual runs.

## Deviations from Plan

None - plan executed exactly as written. The only additions beyond the literal `assemble(budget_chars=4000)` signature were the optional `derived_dir`/`state_dir` keyword arguments (defaulted to the real paths), which keep the documented contract intact while enabling isolated tests — a testability affordance, not a scope change.

## Issues Encountered
None.

## opencode Injection — DEFERRED (RESUME note)

`harness/plugins/session-inject.ts` is **authored only; execution validation is deferred** (D-01) — there is no opencode runtime in this container (same pattern as the .NET egress deferral). It consumes the SAME `python -m tools.memory_regen.inject` contract. **RESUME at Phase 3 (CONFIG / opencode install):** re-verify the opencode hook names (`event` session.created + `chat.system.transform` vs `experimental.chat.system.transform` — MEDIUM confidence per 02-RESEARCH A2) before wiring into `opencode.json`. Do NOT attempt to run/test the plugin until then.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The single injection contract is fixed and unit-tested — 02-03 (contracts-index) and 02-04 (repo-map) only need to produce `.memory/derived/contracts-index.md` and `.memory/derived/repo-map.md`; `assemble()` already reads their heads and degrades gracefully until they exist.
- opencode adapter is ready for Phase-3 execution validation once the opencode surface lands.

## Self-Check: PASSED

All 6 created/modified files present; `.claude/settings.json` SessionStart has 4 groups; task commits `56caa89`, `3b38b3f`, `7b0e26f` all verified in git history.

---
*Phase: 02-two-plane-memory-rules*
*Completed: 2026-07-08*
