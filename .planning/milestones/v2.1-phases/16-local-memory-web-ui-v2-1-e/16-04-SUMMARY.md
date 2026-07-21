---
phase: 16-local-memory-web-ui-v2-1-e
plan: 04
subsystem: memory-derived-regen-wiring
tags: [pointer-index, session-start, derived-regen, emit-round-trip, SC2, MEM2-07]

# Dependency graph
requires:
  - phase: 16-local-memory-web-ui-v2-1-e
    provides: 16-02 tools/memory_regen/pointer_index.py DERIVED reference-scanner generator
  - phase: 02-memory-planes
    provides: SessionStart derived-regen path (repo_map + contracts_index) in session-inject.ts + memory-inject.sh
  - phase: 07-emitter
    provides: tools.harness_emit runtime-neutral harness/ → .opencode/ + .claude/ projection
provides:
  - pointer-index regenerates alongside repo_map + contracts_index at SessionStart + /orient + /refresh-memory (SC2 structurally true)
  - both runtime trees (.opencode/ + .claude/) carry the pointer_index regen wiring, no model id, emit-drift clean
affects: [16-05-referential-integrity (orphan check consumes the always-fresh pointer-index)]

# Tech tracking
tech-stack:
  added: []  # zero external packages — source edits + emit only (T-16-SC)
  patterns:
    - "pointer-index joins the derived-regen module list next to repo_map/contracts_index — generated, never hand-maintained (curator posture)"
    - "gitignored-derived output stays uncommitted; only the WIRING is committed"
    - "emit round-trip gate-theft avoidance: commit emitted trees BEFORE regenerating the projected-tree .ambr twin (Phase-15 CR-01 ordering)"

key-files:
  created:
    - .planning/phases/16-local-memory-web-ui-v2-1-e/16-04-SUMMARY.md
  modified:
    - harness/plugins/session-inject.ts
    - harness/commands/orient.md
    - harness/commands/refresh-memory.md
    - .opencode/plugin/session-inject.ts
    - .opencode/command/orient.md
    - .opencode/command/refresh-memory.md
    - .claude/commands/orient.md
    - .claude/commands/refresh-memory.md
    - .claude/hooks/memory-inject.sh
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr

key-decisions:
  - "pointer-index placed in the SESSION-derived (gitignored) group of /refresh-memory (step 1, next to repo_map), NOT the committed-derived group — it stays DERIVED/gitignored, never committed, never gated"
  - ".claude/hooks/memory-inject.sh (hand-authored Claude SessionStart hook, NOT emitter-owned) got its regen list edited directly — it is the real dev-runtime regen path and the emitter does not project it"
  - "inject.py left untouched — pointer-index is a separate derived artifact the assembler does not read; byte-identity determinism + no-wall-clock gates stay green"
  - "cleared the deferred Phase-14/15 re-emit debt: harness_emit suite now 47 passed / 0 failed (the sanctioned red test_projected_tree_matches_committed_snapshot is green after a legitimate emit + snapshot regen)"

requirements-completed: [MEM2-07]

metrics:
  duration: 9min
  tasks: 2
  files: 10
  completed: 2026-07-18
---

# Phase 16 Plan 04: Wire Pointer-Index into Derived-Regen Path + Emit Round-Trip Summary

Wired `tools.memory_regen.pointer_index` into the SessionStart derived-regen path (opencode plugin + Claude hook) and both `/orient` and `/refresh-memory`, then round-tripped the harness source through the Phase-7 emitter to both runtime trees with no model id and clean emit-drift — making SC2 ("generated, never hand-maintained") structurally true.

## What Was Built

**Task 1 — source wiring (commit 27343f9):**
- `harness/plugins/session-inject.ts`: appended `"tools.memory_regen.pointer_index"` to the SessionStart regen module loop (line ~36), preserving array order.
- `harness/commands/orient.md`: pointer_index added to the step-1 derived-regen macro alongside repo_map/contracts_index.
- `harness/commands/refresh-memory.md`: pointer_index added to step-1 (session-derived, gitignored) next to repo_map — with a note that it is gitignored-derived, never committed, never gated. The "invokes ONLY `tools.memory_regen.*` + `tools.docs_sync`" note stays true (pointer_index is a `tools.memory_regen.*` module).
- `inject.py` untouched; inject determinism + no-wall-clock tests green (14 passed).

**Task 2 — emit round-trip (commits aefc86e + 6ca5c94):**
- Ran `python -m tools.harness_emit` (zero emitter code change, glob discovery) → projected the Task-1 edits into `.opencode/plugin/session-inject.ts`, `.opencode/command/{orient,refresh-memory}.md`, `.claude/commands/{orient,refresh-memory}.md`.
- Hand-edited `.claude/hooks/memory-inject.sh` regen list (this Claude SessionStart hook is hand-authored, NOT emitter-owned — the emitter's domain is agents/commands/skills/plugins/config only, so the hook is its own source-of-truth).
- Verified emit-drift clean via the CI replica: `git add -A` the trees, re-emit, `git diff --exit-code` = exit 0 (no untracked masquerade — Phase-15 CR-01 lesson honored).
- Verified zero model identifiers in every changed emitted artifact.
- Gate-theft avoidance: committed the emitted trees FIRST (aefc86e), confirmed `test_projected_tree_matches_committed_snapshot` STILL failed (positive proof the `.ambr` was not blessed early), THEN regenerated the snapshot against the committed fresh tree and committed it separately (6ca5c94).

## Deviations from Plan

**1. [Rule 2 — missing critical wiring] `.claude/hooks/memory-inject.sh` regen list edited directly**
- **Found during:** Task 2 emit.
- **Issue:** The plan's `files_modified` lists `.claude/hooks/memory-inject.sh`, but the emitter does not project it (it is a hand-authored Claude SessionStart hook outside the emitter's agents/commands/skills/plugins/config domain). Without editing it, the actual dev-runtime (Claude) SessionStart path would regenerate repo_map + contracts_index but NOT pointer_index — SC2 would be structurally false on the runtime that actually executes here.
- **Fix:** Added `uv run python -m tools.memory_regen.pointer_index ... || true` to the hook's best-effort regen block (lines 25-27), matching the repo_map/contracts_index pattern.
- **Files modified:** `.claude/hooks/memory-inject.sh`
- **Commit:** aefc86e

**2. [expected — deferred-debt resolution] cleared the sanctioned red snapshot test**
- The long-standing `test_projected_tree_matches_committed_snapshot` (baseline "1 failed", carried since Phase 12/13) is now green. It was settled the correct way — a real re-emit + a snapshot regen ordered AFTER the emit commit — not by a force-`--snapshot-update` over a stale tree. `harness_emit` suite is now 47 passed / 0 failed.

## Verification

- grep: `pointer_index` present in all 3 harness sources + all 6 emitted files (both runtimes).
- `uv run pytest tools/memory_regen/tests -k determinism` → 14 passed (inject byte-identity + no-wall-clock green).
- CI replica: re-emit + `git diff --exit-code -- .opencode .claude` = exit 0 (emit-drift clean).
- Model-id scan over changed emitted files: empty (clean).
- GEN-04 core→example independence: 18 passed.
- `tools/harness_emit`: 47 passed / 0 failed.
- Combined `memory_regen + harness_emit + harness_lint` suites: 391 passed.

## Known Stubs

None. The opencode `session-inject.ts` remains authored-execution-deferred (D-01, no opencode runtime in-container) — a pre-existing, documented posture, not a stub introduced here.

## Self-Check: PASSED
- FOUND: harness/plugins/session-inject.ts (pointer_index wired)
- FOUND: .claude/hooks/memory-inject.sh (pointer_index wired)
- FOUND: commits 27343f9, aefc86e, 6ca5c94
