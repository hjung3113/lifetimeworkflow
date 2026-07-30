---
phase: 43-lifecycle-plane-removal
plan: 03
wave: 2
subsystem: harness-emit
tags: [harness-emit, hooks, retirement, phase-gate]
requires: ["43-01", "43-02"]
provides:
  - "resume_gate PreToolUse hook retired from merge.py, both runtime trees re-emitted"
  - "D-02 phase gate green — Wave 3 deletion authorized"
affects:
  - "tools/harness_emit/merge.py"
  - ".claude/settings.json"
  - "harness/opencode.json"
tech-stack:
  added: []
  patterns: ["RETIRED_SIGNATURES transient-drop (D-06)", "emitter-only propagation (D-14)"]
key-files:
  created: []
  modified:
    - tools/harness_emit/merge.py
    - harness/opencode.json
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - tools/hooks/tests/test_settings_coexist.py
    - .claude/settings.json
    - opencode.json
    - "10 emitted D-01 command/agent files (.opencode/ + .claude/)"
decisions: []
metrics:
  duration: "~7 min"
  completed: 2026-07-28
  tests: "1313 passed, 7 snapshots"
  commits: 1
---

# Phase 43 Plan 03: Wave-2 Re-emit and resume_gate Retirement Summary

Retired the `resume_gate` PreToolUse hook with cause and effect in a single commit, propagated
Wave-1's five D-01 repairs into both runtime trees via the emitter, and passed the D-02 phase gate
that authorizes Wave 3 deletion.

## What Was Done

### Task 1 — `ceebc4e` `refactor(43-03): retire resume_gate hook and re-emit both runtime trees`

Executed in the plan's exact six-step order:

1. **Cause (B-6)** — `tools/harness_emit/merge.py`: dropped `"tools.hooks.resume_gate"` from
   `HARNESS_SIGNATURES`, set `RETIRED_SIGNATURES = ("tools.hooks.resume_gate",)`, deleted the
   `Write|Edit|Bash` resume_gate dict from `HARNESS_HOOK_GROUPS["PreToolUse"]`.
   `harness/opencode.json`: `plugin` array reduced to `["harness/plugins/session-inject.ts"]`.
   `tools/harness_emit/tests/test_coexist.py`: matching dict removed from `_SEED_SETTINGS`
   (coupled edit — `test_seeded_settings_json_reproduced_byte_for_byte` runs a full emit over it).
2. **Emit** — `python -m tools.harness_emit`, 109 artifacts. Produced exactly the predicted 12-file
   diff: the 10 emitted D-01 command/agent files, `.claude/settings.json`, and root `opencode.json`.
3. **Effect (B-1)** — `test_expected_slot_counts` corrected: `== 8` → `== 7`, assertion message and
   docstring first clause to `4 GSD + 3 harness` / `7 PreToolUse (4 GSD + 3 harness)`. PostToolUse
   assertion and message left byte-unchanged.
4. **Reset (D-06)** — `RETIRED_SIGNATURES` back to `()`, second emitter run. Before-vs-after diff
   comparison across that run exited 0: the reset did not re-add the dropped group, and
   `.claude/settings.json` stayed at 7.
5. **Snapshot (W-4)** — `test_emit_determinism.ambr` regenerated, then re-run without
   `--snapshot-update`: 4 passed, 1 snapshot passed.
6. **Green before commit** — targeted 4-file set 19 passed; full suite 1313 passed.

`git log -1 --name-status` confirms all six B-6/B-1 files landed in the one commit:
`merge.py`, `harness/opencode.json`, `test_coexist.py`, the `.ambr`, `test_settings_coexist.py`,
and the emitted `.claude/settings.json`.

### Task 2 — D-02 phase gate (no commit; verification only)

| Gate | Result |
|------|--------|
| `uv run pytest -q` | **1313 passed, 7 snapshots** — exit 0 |
| `uv run python -m tools.contract_drift.drift` | exit 0 — live manifest matches committed baseline |
| B-4 name-scoped sweep over the 15 D-01 files (5 source + 10 emitted) | no output, exit 1 |
| Working tree after post-commit re-emit | clean (`emit-drift` CI form exits 0) |

## Pre-Deletion Baseline

**1313 passed, 7 snapshots.** This is the figure Plans 43-04 and 43-05 must not regress below,
minus the counts of tests this phase intentionally deletes alongside their modules. (Wave 1's own
3 removed tests — 2 in `test_inject_assembler.py`, 1 in `test_handoff.py` — are already netted out
of this number.)

## Acceptance Criteria

Every criterion in both tasks held as written. Measured results:

- `grep resume_gate|resume-gate` over `.claude/settings.json opencode.json harness/opencode.json` — exit 1
- `grep resume_gate` over `merge.py test_coexist.py` — exit 1
- `RETIRED_SIGNATURES: tuple[str, ...] = ()` at `merge.py:111`
- Idempotence (before-vs-after the second emitter run) — `diff` exit 0; post-commit
  `git diff --exit-code` form also exit 0
- `.claude/settings.json` hooks: PreToolUse **7**, PostToolUse **4**, SessionStart **4**
- Literal counts: `== 7` → 1, `4 GSD + 3 harness` → 2, `4 GSD + 4 harness` → 0, `PostToolUse == 4` → 1
- B-6 proof (`test_settings_merge.py` + `test_coexist.py` + `test_settings_coexist.py`) — 15 passed
- W-4 — `test_emit_determinism.py` 4 passed without `--snapshot-update`; `resume-gate` in `.ambr` → 0
- W-2 — `.opencode/plugin/resume-gate.ts` present; `emit-manifest.json` retains 1 `resume-gate.ts` row

## Deviations from Plan

None. The plan was followed literally; no criterion was adjusted and no code was changed to make a
criterion fit.

## Observations (nothing the plan failed to anticipate)

- **`AGENTS.md`, `CLAUDE.md` and `emit-manifest.json` produced no diff.** All three are in Task 1's
  pathspec; the emitter left them byte-identical, so they simply did not stage. For the manifest this
  is the outcome W-2 predicts and explicitly labels correct — `harness/plugins/resume-gate.ts` is
  still on disk, so `iter_plugins()` re-emitted `.opencode/plugin/resume-gate.ts` and its row was
  rightly retained. It was **not** hand-edited. 43-04 Task 2's re-emit prunes both.
- **Idempotence framing mattered in practice.** `git diff --stat -- .opencode .claude opencode.json`
  after the second run showed 12 files, exactly as the plan warned. Treating that as a failure and
  "fixing" it would have reverted this commit's entire reason for existing. The before-vs-after
  comparison across the second run is what actually proves idempotence, and it exited 0.
- **Commit argument order.** `git commit -m "<msg>" -- <paths>` used as instructed; message first,
  `--` last. Staged set was inspected with `git diff --cached --name-only` before committing.

## Self-Check: PASSED

- `43-03-SUMMARY.md` written to `.planning/phases/43-lifecycle-plane-removal/`
- Commit `ceebc4e` present on `claude/data-pipeline-harness-8aypct` (verified via `git log`)
- `.planning/STATE.md` and `ROADMAP.md` deliberately untouched, per execution instruction
