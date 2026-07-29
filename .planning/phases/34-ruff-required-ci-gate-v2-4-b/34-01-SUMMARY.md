---
phase: 34-ruff-required-ci-gate-v2-4-b
plan: 01
subsystem: ruff-config
tags: [DEBT-01, ruff, vendored-exclusion, autofix]
requires:
  - pyproject.toml::[tool.ruff]
provides:
  - "extend-exclude covering docs/references/opencode-matt-workflows"
  - "a 393-finding tree for plan 02's baseline to hold"
affects:
  - 34-02 (baseline.json records the post-fix counts)
tech-stack:
  added: []
  patterns:
    - "config-level exclusion of vendored third-party sources, never per-rule ignores"
    - "safe autofixes only; --unsafe-fixes never passed"
key-files:
  created: []
  modified:
    - pyproject.toml
    - "16 files under tools/ (mechanical import fixes)"
decisions:
  - "D-07 held: only ruff-classified safe fixes; B904/B905/B007/F841 go to the baseline unfixed"
  - "Every F401 removal was checked for cross-module re-export before commit"
metrics:
  tasks: 2
  commits: 2
  tests_added: 0
---

# Phase 34 Plan 01: Exclusion + Safe Autofixes Summary

The finding set went **617 → 424 → 393**. The vendored tree left the report; the machine-fixable
findings left the tree; everything else is now real debt for plan 02's ratchet to hold.

## What was built

| Task | Deliverable | Commit |
|------|-------------|--------|
| 1 | `extend-exclude` += `docs/references/opencode-matt-workflows`, with the reason in a comment | `0233f51` |
| 2 | `ruff check . --no-cache --fix` across 16 files under `tools/` | `3bc21ea` |

## Measured, at every step

| State | Total | Delta |
|---|---:|---|
| at `8cb8458` | 617 | — |
| after the vendored exclusion | **424** | −193 |
| after the safe autofixes | **393** | −31 |

Vendored tree measured directly (`ruff check docs/references/opencode-matt-workflows --no-cache`):
**193 errors**. The leak check `ruff check . --no-cache --output-format=concise | grep '^docs/'`
is empty — nothing outside the vendored tree was swept up by the pattern. E401 (7) and E722 (2)
vanished entirely, both classes having lived only in vendored code.

Final composition, which plan 02's `baseline.json` must record:

```
267	E501	line-too-long
102	E702	multiple-statements-on-one-line-semicolon
 20	E701	multiple-statements-on-one-line-colon
  1	B007	unused-loop-control-variable
  1	B904	raise-without-from-inside-except
  1	B905	zip-without-explicit-strict
  1	F841	unused-variable
Found 393 errors.
```

## Deviations from Plan

**DEV-01 — the autofix removed 31, not the predicted 24.** The plan predicted 400 remaining; the
real number is 393. Ruff reported `Found 419 errors (26 fixed, 393 remaining)`, and the three
numbers only reconcile once you notice the fix is not count-preserving: splitting an over-long
`from x import a, b, c, …` line into a parenthesised multi-line form **also removes its E501**.
Seven E501 findings went that way, and two extra I001s appeared and were fixed within the same
pass. Predicted E501 274, actual **267**. This is a deviation in the executor's favour and the
numbers were re-derived rather than the target being adjusted to match.

**DEV-02 — the baseline the plan was written against had already moved.** Commit `8cb8458`
(a sibling phase, DEBT-03) landed on this branch during research and removed 3 E501 findings from
`tools/docs_guard/`. The research document carries the retraction (§1.0); the practical
consequence recorded here is that plan 02 must generate `baseline.json` immediately before
committing it.

## Verification of the F401 removals

Ruff's unused-import fix is only safe if the name is not re-exported and imported elsewhere.
Removed: `_json` (from `tools/handoff/handoff.py`'s import of `task_control.manager`), and `json`
+ `Any` from `tools/task_control/phase_gate.py`. Grepped every `from tools.handoff.handoff import`
and `from tools.task_control.phase_gate import` site in `tools/`, `libs/`, `examples/` — 12 hits,
none naming any of the three. The `datetime, timezone` → `UTC, datetime` rewrites (UP017) are
`datetime.now(timezone.utc)` → `datetime.now(UTC)`, semantically identical on py311+.

## Gate results

| Gate | Result |
|------|--------|
| `uv run pytest -q` | **1506 passed**, 8 snapshots (baseline was 1500; a sibling phase added 6) |
| `uv run ruff check . --no-cache --statistics` | 393, composition above |
| `uv run ruff format --check .` | 25 → **17** files would reformat (improved, not worsened) |
| `git diff -- uv.lock` | empty |
| `git status --porcelain` | empty after both commits |

## Known Stubs

None.

## Threat Flags

None. Zero dependency changes; the diff is one config line plus mechanical import reordering.

## Self-Check: PASSED

- `pyproject.toml` — modified, `extend-exclude` contains the vendored path
- commit `0233f51` — FOUND
- commit `3bc21ea` — FOUND
