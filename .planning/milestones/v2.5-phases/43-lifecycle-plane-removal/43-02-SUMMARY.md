---
phase: 43-lifecycle-plane-removal
plan: 02
subsystem: memory-injection + structural-fixtures
tags: [lifecycle-plane-removal, injector, wave-1, CER-07]
requires: []
provides:
  - "inject.py emits only the activeContext pointer; no active-task block"
  - "no module in the repo imports TASK_HEADER"
  - "_NEW_GATES reflects the post-drop steady state"
affects:
  - "43-03 (emitter run; owns test_expected_slot_counts, merge.py, harness/opencode.json)"
  - "43-04 (deletes tools/handoff, tools/evidence)"
tech-stack:
  added: []
  patterns: ["same-commit cross-package consumer repair (W-6)"]
key-files:
  created: []
  modified:
    - tools/memory_regen/inject.py
    - tools/memory_regen/tests/test_inject_assembler.py
    - tools/handoff/tests/test_handoff.py
    - tools/hooks/tests/test_settings_coexist.py
    - tools/adoption_scan/scan.py
decisions:
  - "Removed the orphaned D-05/TCP-15 'reserved slot' comment together with the ('task', task) tuple it annotated, rather than leaving it stranded above the contracts slot where it would assert something false"
metrics:
  duration: ~12 min
  completed: 2026-07-28
  commits: 2
  tasks: 2
---

# Phase 43 Plan 02: Wave-1 injector + structural-fixture repair Summary

Stripped `inject.py`'s active-task block while proving the activeContext pointer survives, repaired
the cross-package `TASK_HEADER` consumer in the same commit (W-6), and swept the two structural
sites that hardcoded state this phase invalidates — all with the B-1/B-6 scope boundaries held
intact for Plan 43-03.

## Commits

| Hash | Description |
|------|-------------|
| `a88ae70` | `refactor(43-02)`: strip inject.py's active-task block, keep the activeContext pointer, repair the W-6 cross-package consumer |
| `8912c35` | `chore(43-02)`: drop the resume_gate tuple from `_NEW_GATES`; stop citing `tools/evidence/capture.py` in `scan.py`'s docstring |

Both commits used `git commit -m ... -- <explicit pathspec>` with `git diff --cached --name-only`
inspected first. No `git add -A`, no `git add .`, no `git commit -a`, no `git checkout <ref> -- .`.

## Task 1 (`a88ae70`)

Deleted from `tools/memory_regen/inject.py`: `_active_task_pointer` (whole function), `TASK_HEADER`,
the `tools.handoff` import block, the now-unused `import json`, the `task = _active_task_pointer(...)`
call, the `("task", task)` section tuple, and `"task"` from the never-drop exemption tuple (now
`("agreements", "banner", "drift")`). `_active_context_pointer` was left byte-for-byte untouched.

Deleted `test_malformed_active_task_is_fail_closed_and_capped` and
`test_absent_active_task_is_normal_no_task_session` from the assembler tests. The four
pointer-survival tests were left untouched.

**W-6, same commit:** removed `from tools.memory_regen.inject import TASK_HEADER, assemble` and
`test_real_generate_activate_assemble_injects_reserved_task_pointer` from
`tools/handoff/tests/test_handoff.py`. Confirmed by grep before editing that these were the only two
sites outside `inject.py` referencing the deleted symbols, exactly as the plan stated. Nothing else
in that file changed; `activate`, `generate`, `subprocess` and `pytest` all remain in use, and ruff
is clean.

### Acceptance criteria — all held

| Criterion | Result |
|---|---|
| `pytest tools/memory_regen/tests/test_inject_assembler.py -q` | 20 passed |
| `test_active_context_is_pointer_not_body` present and green | 1 passed (run in isolation) |
| `pytest tools/handoff/tests/test_handoff.py -q` collects and exits 0 | 16 passed |
| `grep -rn "TASK_HEADER" tools/` | no output (exit 1) |
| `grep -n "tools.handoff\|_active_task_pointer\|^import json" tools/memory_regen/inject.py` | no output |
| `grep -c "def _active_context_pointer" tools/memory_regen/inject.py` | `1` |
| `pytest --collect-only -q` | 1313 collected, 0 errors |
| `pytest -q` | 1313 passed |

1316 → 1313 is exactly the three deleted tests.

## Task 2 (`8912c35`)

Removed only the `("PreToolUse", "tools.hooks.resume_gate", "Write|Edit|Bash")` tuple from
`_NEW_GATES`. Rewrote `scan.py`'s docstring sentence to state the same no-subprocess /
no-task-state-mutation constraint without naming `tools/evidence/capture.py`; the
`gate-registry.json` citation lower in the same docstring was left alone.

### Acceptance criteria — all held

| Criterion | Result |
|---|---|
| `grep -n "resume_gate" tools/hooks/tests/test_settings_coexist.py` | no output |
| `grep -c 'PreToolUse"\]) == 8' ...` | `1` (deliberately unchanged) |
| `grep -c "4 GSD + 4 harness" ...` | `2` (deliberately unchanged) |
| `grep -n "tools/evidence/capture" tools/adoption_scan/scan.py` | no output |
| B-6: `git log -1 --name-only` | only the two declared files; `merge.py`, `test_coexist.py`, `harness/opencode.json` absent |
| `pytest test_settings_coexist.py test_settings_merge.py test_coexist.py -q` | 15 passed |
| `pytest tools/hooks/tests/test_settings_coexist.py -q` | `4 passed` — matches the plan's live-measured prediction exactly |
| `pytest -q` | 1313 passed |

## Deviations from Plan

**One, cosmetic and adjacent to a sanctioned deletion.** The plan's `<interfaces>` named line 186
(`("task", task),`) for deletion but did not mention the comment on line 185:

```python
# D-05/TCP-15: this reserved slot is deliberately before all droppable summaries.
```

That comment exists solely to annotate the tuple being deleted. Left in place it would have sat
directly above `("contracts", ...)` and asserted, falsely, that the contracts slot is a reserved
non-droppable one. I removed it with the tuple it describes. This changes no behavior and no test
reads it. Everything else in the plan was followed literally.

## Acceptance criteria that did not hold

None. Every criterion in both tasks passed as written, including the two deliberate
"still-present" boundary assertions reserved for Plan 43-03.

## Things the plan did not anticipate

1. **A transient full-suite red caused by concurrent Wave-1 plan 43-01, not by this plan.**
   Immediately after `a88ae70`, `pytest -q` reported
   `tools/harness_emit/tests/test_emit_determinism.py::test_projected_tree_matches_committed_snapshot`
   failing. This was a race, not a defect: 43-01 had `harness/agents/orchestrator.md` edited in the
   working tree with its snapshot update not yet committed. Once 43-01 committed `9056d22` the tree
   went clean and the test passed. Attribution is unambiguous — the failing test reads `harness/`
   and the emit snapshot, and `a88ae70` touched only `tools/`; the pre-commit full-suite run of this
   plan's exact content, on an otherwise-clean tree, was `1313 passed`. **Implication for future
   concurrent waves:** a full-suite run is not a sound per-plan gate while a sibling plan holds
   uncommitted edits. Per-plan greenness should be judged pre-commit on a clean tree, or the plans
   should be serialized at the point of the shared emit-snapshot test.

2. **A `git commit` argument-order trap.** The plan's action text spells the command as
   `git commit -- <paths>` and my first attempt appended `-m` after the `--`, where git treats the
   message and the flag as pathspecs and aborts. Harmless (nothing was committed) but worth writing
   down for later plans in this phase, which all carry the same `git commit -- <pathspec>` wording:
   the message must precede the `--`.

3. `contracts/harness/task-control/gate-registry.json` is cited **twice** in `scan.py`'s docstring,
   not once. The plan said to leave that citation alone, which I did — noting the count only so a
   later plan touching that file is not surprised.

## Self-Check: PASSED

- `tools/memory_regen/inject.py` — FOUND, modified
- `tools/memory_regen/tests/test_inject_assembler.py` — FOUND, modified
- `tools/handoff/tests/test_handoff.py` — FOUND, modified
- `tools/hooks/tests/test_settings_coexist.py` — FOUND, modified
- `tools/adoption_scan/scan.py` — FOUND, modified
- commit `a88ae70` — FOUND in `git log`
- commit `8912c35` — FOUND in `git log`
- working tree clean; full suite `1313 passed` at HEAD
