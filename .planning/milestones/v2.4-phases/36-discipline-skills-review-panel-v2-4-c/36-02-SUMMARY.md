---
phase: 36-discipline-skills-review-panel-v2-4-c
plan: 02
subsystem: task-control lifecycle enforcement
tags: [LANE-01, LANE-02, task-control, phase-gate, mutation-proof]
requires:
  - tools/discipline/check.py (36-01)
  - harness/risk-policy.toml required_disciplines (36-01)
provides:
  - a refusal at both lifecycle choke points when a lane's declared discipline is unsatisfied
  - python -m tools.discipline with the 0/1/3 exit mapping
affects: [36-03, 36-04]
tech-stack:
  added: []
  patterns: [fail-before-CAS, mutation proof, reused exit-code convention]
key-files:
  created:
    - tools/discipline/__main__.py
  modified:
    - tools/task_control/manager.py
    - tools/task_control/phase_gate.py
    - tools/task_control/tests/test_task_control.py
    - tools/handoff/tests/test_handoff.py
    - tools/lifecycle_eval/runner.py
decisions:
  - "The enforcement tests live in the existing test_task_control.py rather than a new file, so they reuse make_task/satisfy_target instead of standing up a second task-packet factory. satisfy_target was split into satisfy_artifacts + satisfy_disciplines so the refusal tests can satisfy one without the other."
  - "tools/lifecycle_eval/runner.py gained _assert_missing_disciplines_reject: the end-to-end evaluator now proves the refusal fires BEFORE it records anything, mirroring the artifact assertion it already made."
  - "No new subcommand on the task-control CLI; the discipline surface is its own module, so the task-control argument surface is unchanged."
metrics:
  tasks: 3
  commits: 1
  tests_added: 7
---

# Phase 36 Plan 02: Lifecycle Enforcement Summary

A lane's declared discipline is now something the lifecycle machinery **refuses on**. This is the
property LANE-01 says was missing and LANE-02 asks for on the panel specifically.

## Demonstration (verbatim)

A real STRICT packet, all four required artifacts present, at PLAN:

```
$ uv run python -m tools.discipline $TASK --phase EXECUTE
lane STRICT at EXECUTE: 1 discipline(s) owed
  MISSING  clarify (skill clarify, record clarify.json) — clarify
discipline: run the declared skill and record it before the next transition
exit=1

$ uv run python -m tools.task_control transition $TASK EXECUTE --expected-revision 3
FAIL: missing required disciplines: clarify
exit=1
```

After writing `$TASK/discipline/clarify.json`:

```
$ uv run python -m tools.discipline $TASK --phase EXECUTE
lane STRICT at EXECUTE: 1 discipline(s) owed
  OK       clarify (skill clarify, record clarify.json)
exit=0

$ uv run python -m tools.task_control transition $TASK EXECUTE --expected-revision 3
{ … "phase": "EXECUTE" … }
```

The packet was created with `tools.risk_router.intake.create_packet` at scores of 2 across all seven
axes (total 14 → STRICT). Nothing about the demonstration is a fixture: it is the shipped CLI.

## RED run recorded

Against unmodified `manager.py` / `phase_gate.py`: **5 failed, 20 passed** —
`test_strict_execute_is_refused_without_the_clarify_record`,
`test_strict_verify_is_refused_without_the_review_panel`,
`test_three_identical_seats_do_not_satisfy_the_panel`,
`test_phase_gate_refuses_a_resumed_task_missing_its_discipline`,
`test_the_refusal_is_load_bearing`, each with `DID NOT RAISE TaskControlError`.

## What enforces what

| Site | Behaviour |
|------|-----------|
| `manager.transition()` | raises `TaskControlError("missing required disciplines: …")` after the artifact check and **before** `_cas_write` — asserted by a test that a refused transition leaves phase and revision unchanged |
| `phase_gate.phase_gate()` | adds `discipline: <id>` to the refresh list for the phase being resumed |
| `python -m tools.discipline` | 0 clean / 1 outstanding / 3 invalid declaration-or-packet — the `tools.docs_guard` convention, reused |

Every refusal has a positive control that succeeds once the record exists, plus
`test_fast_owes_no_discipline_and_is_unaffected` as the no-op control, so the gate cannot degrade
into always-red.

**Mutation proof** (`test_the_refusal_is_load_bearing`): with `STRICT`'s `required_disciplines`
emptied in the loaded policy, the identical transition succeeds. The control is load-bearing.

## Deviations from Plan

### [Rule 1 — reuse beats a second factory] Tests landed in the existing file

**Plan said:** a new `tools/task_control/tests/test_discipline_enforcement.py`.
**Issue:** `tools/task_control/tests/` has no `__init__.py`, so a sibling test module cannot import
`make_task` / `satisfy_target` from `test_task_control.py`. A new file would have had to duplicate
the ~70-line packet factory, which is exactly what the standing reuse rule forbids.
**Fix:** the enforcement tests are a clearly headed section of `test_task_control.py`
(`# ── LANE-01 / LANE-02 …`), and `satisfy_target` was split into `satisfy_artifacts` +
`satisfy_disciplines` so refusal tests can satisfy artifacts without satisfying disciplines.

### [Rule 2 — the change reaches further than planned] Three fixture surfaces, not one

**Found during:** the full-suite run.
**Issue:** `tools/handoff/tests/test_handoff.py` and `tools/lifecycle_eval/runner.py` also drive real
transitions, and both stopped at the first discipline refusal.
**Fix:** both now discharge the lane's method obligations the same way they already discharged its
artifact obligations. `lifecycle_eval` additionally gained `_assert_missing_disciplines_reject`, so
the evaluator asserts the refusal *fires* before recording — a fixture cannot pass because the gate
silently does not exist. **`tools/lifecycle_eval/runner.py` is a source of the advisory
`lifecycle-eval-shadow-metrics` docs binding; plan 04 owns the target review.**

### [Rule 3 — tooling reality] Whole-file reformat of `test_task_control.py`

The repo's format-on-write hook reformatted `tools/task_control/tests/test_task_control.py` in full
on first edit (it was previously long-line/semicolon-dense). The diff is therefore much larger than
the added tests. It is deterministic formatter output and it *reduced* ruff findings
(E501 267→177, E702 102→67); it was not hand-authored and no assertion changed.

## Verification

| Gate | Result |
|------|--------|
| `uv run pytest -q` | **1586 passed, 8 snapshots** (baseline 1543) |
| `uv run python -m tools.ruff_baseline` | exit 0 — 266 findings vs baseline 393 |
| `uv run python -m tools.contract_drift.drift` | OK |
| demonstration | reproduced above, verbatim |

**Observed flake, not a regression:** `tools/memory_ui/tests/test_server.py::
test_post_missing_content_length_is_refused` failed once in a full run and passed on re-run and in
isolation, both with and without this change. It binds a local socket; recorded, not chased.

## Human-gated / carried

- None from this plan. Ledger untouched, no bypass token set.
