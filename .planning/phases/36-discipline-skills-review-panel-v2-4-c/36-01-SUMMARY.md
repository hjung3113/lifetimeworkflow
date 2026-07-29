---
phase: 36-discipline-skills-review-panel-v2-4-c
plan: 01
subsystem: risk policy + lane discipline declaration
tags: [LANE-01, LANE-02, risk-router, discipline, contract-avoidance]
requires:
  - tools/risk_router/router.py (lane requirement matrix, effective-policy hash)
  - tools/task_packet/transitions.py (TRANSITIONS_PATH — the ordered phase array)
provides:
  - a per-lane required_disciplines slot with monotone-superset validation
  - harness/disciplines.toml + tools/discipline (the pure satisfied-vs-missing decision function)
affects: [36-02, 36-03]
tech-stack:
  added: []
  patterns: [live-policy read, tool-local JSON Schema, defect-list validation, mutation proof]
key-files:
  created:
    - harness/disciplines.toml
    - tools/discipline/{__init__,check}.py
    - tools/discipline/record.schema.json
    - tools/discipline/pyproject.toml
    - tools/discipline/tests/test_discipline.py
  modified:
    - harness/risk-policy.toml
    - tools/risk_router/router.py
    - tools/risk_router/overlay.schema.json
    - tools/risk_router/tests/test_router.py
    - uv.lock
decisions:
  - "The three per-lane requirement keys are now one tuple, LANE_REQUIREMENT_KEYS, so validation, the overlay merge and the lower-lane sweep cannot diverge for the new key."
  - "decide()'s return is asserted key-for-key by a test that names the contract wall, so a future addition trips here instead of at intake."
  - "The ruff baseline was NOT lowered despite the ratchet reporting a shrink (393 -> 383): the lead's brief forbade --update. Recorded as an available free ratchet for a later phase."
metrics:
  tasks: 3
  commits: 2
  tests_added: 36
---

# Phase 36 Plan 01: Lane Discipline Declaration Summary

A lane's required discipline is now declared policy data with the same monotone validation the
artifact and gate matrices already get, and a pure checker decides whether a task packet discharged
it. Zero contract bytes moved.

## What was built

**`c651040` — the policy slot.** `harness/risk-policy.toml` gains `required_disciplines` per lane
(FAST `[]`, STANDARD `clarify`, STRICT `+ test-driven-change, adversarial-review-panel`, CONTROLLED
`+ diagnose, domain-modeling`). `_validate_core_policy`, `_effective_policy`'s overlay merge and the
lower-lane obligation sweep all iterate the new `LANE_REQUIREMENT_KEYS` tuple rather than a hardcoded
pair, so the new key inherits every existing rule instead of getting a parallel implementation.
`overlay.schema.json` accepts `required_disciplines_add`.

**`91f873a` — the declaration and the checker.** `harness/disciplines.toml` declares five
disciplines; `tools/discipline/check.py` exposes `PHASE_ORDER`, `load_declarations`,
`lane_disciplines`, `required_disciplines`, `validate_record` and `missing_disciplines`.

## The contract wall, and how it was avoided

`contracts/harness/task-control/task.schema.json` pins `risk_decision` with
`"additionalProperties": false`, and `tools/risk_router/intake.py` writes `decide()`'s return there
verbatim. **One extra key in `decide()` would make every new `task.json` schema-invalid** and would
have forced a constitution-plane edit this phase may not make.

So `decide()` is unchanged — asserted by `test_decision_record_keys_are_unchanged`, which spells out
the reason in its docstring. The requirement is read from **live policy** at check time, exactly as
`manager._required_artifacts` already does. `required_disciplines` still enters `_effective_policy`,
so `policy_hashes.effective` moves when disciplines change and an overlay can raise them.

`uv run python -m tools.contract_drift.drift` → `OK — live manifest matches the committed baseline`.

## RED runs recorded

Task 1, against unmodified `router.py`: **6 failed, 44 passed**, failing
`test_shipped_policy_declares_a_discipline_matrix`,
`test_higher_lane_may_not_drop_a_lower_lane_discipline`, `test_duplicate_discipline_is_rejected`,
`test_missing_discipline_slot_is_rejected`, `test_effective_hash_moves_with_a_discipline_change`,
`test_overlay_may_add_disciplines_but_never_remove_them` — the last with
`RiskRouterError: invalid overlay schema at lanes.FAST: Additional properties are not allowed
('required_disciplines_add' was unexpected)`. `test_decision_record_keys_are_unchanged` passed
against unmodified code, which is the point: it is the wall guard, not a new feature.

## Defect classes, each with its own asserted message

| Case | Asserted defect |
|------|-----------------|
| wrong skill | `record names skill diagnose, declaration names clarify` |
| satisfied too late | `record was satisfied at VERIFY, after the owed phase EXECUTE` |
| non-existent output | `record cites an output that does not exist: not-written.md` |
| no output | `record cites 0 output(s), declaration requires 1` |
| duplicate panel seats | `panel carries 2 distinct expert seat(s), declaration requires 3` |
| unknown finding cited | `panel seat security cites a finding absent from evidence.json: F-99` |
| undeclared verdict | `panel seat … reports an undeclared verdict: looks-fine` |
| no panel at all | `record declares no panel, but the discipline requires one` |
| schema violation | short-circuits to exactly one `schema …` message |
| record from another task | `clarify (record belongs to task task-9999)` |

Plus five positive controls — one well-formed record per declared discipline — and a FAST/BLOCKED
owes-nothing pair, so the rule cannot degrade into "nothing is ever satisfied".

## Deviations from Plan

### [Rule 3 — environment reality] `uv run pytest tools/<pkg>` cannot be used for narrow selections

**Found during:** task 2 verification.
**Issue:** `uv run pytest tools/discipline -q` fails with `ModuleNotFoundError: No module named
'tools'`. This is **pre-existing and not caused by this change** — verified by moving
`tools/discipline/` out of the tree entirely and running `uv run pytest tools/task_control -q`, which
fails identically. The repo has no root `conftest.py` and `tools/` is a namespace package; the repo
root only reaches `sys.path` when a collected test package's `__init__.py` chain walks up to it, or
when pytest is invoked as a module.
**Fix:** narrow selections use `uv run python -m pytest <path>`. Full-suite runs (`uv run pytest -q`)
are unaffected. No `__init__.py` was added under `tools/discipline/tests/`, matching the convention
in `tools/task_control/tests/` and `tools/risk_router/tests/`.
**Not fixed here:** adding a root `conftest.py` would be a repo-wide change well outside this phase.

### [Rule 1 — a smaller, better shape] `LANE_REQUIREMENT_KEYS` instead of a third branch

The plan said "extend the existing `for key in (...)` tuple rather than writing a parallel loop".
Three separate sites carried that literal pair (validation, overlay merge, lower-lane sweep). All
three now read one module constant, so the next requirement key is a one-line change and cannot be
half-wired.

## Verification

| Gate | Result |
|------|--------|
| `uv run pytest -q` | **1579 passed, 8 snapshots** (baseline 1543 → +36) |
| `uv run python -m tools.ruff_baseline` | exit 0 — 383 findings vs baseline 393 |
| `uv run python -m tools.contract_drift.drift` | OK — no contract moved |
| `uv run ruff check tools/discipline harness` | All checks passed |
| `python3 tools/harness_lint/workspace_check.py` | OK — every globbed member has a pyproject |

## Human-gated / carried

- None from this plan. `docs/.docs-review-ledger.toml` untouched; no bypass token set.
- The free ruff ratchet (393 → 383) is left unclaimed per the brief's explicit `--update` prohibition.
