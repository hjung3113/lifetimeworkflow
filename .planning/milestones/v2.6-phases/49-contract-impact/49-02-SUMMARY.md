---
phase: 49-contract-impact
plan: 02
subsystem: infra
tags: [harness-emit, orchestrator-route, contract-graph, command-surface]

# Dependency graph
requires:
  - phase: 49-contract-impact
    plan: 01
    provides: "tools/contract_graph/impact.py::report()/main() — the reporter this plan wires"
provides:
  - "harness/commands/impact.md — thin /impact command (composes tools.contract_graph.impact, no logic in markdown)"
  - "contract-change route's Repository evidence block naming /impact instead of the inline uv run python -c one-liner"
  - "command-surface guards (test_commands.py, test_coexist.py) pinned at 19, EXPECTED_COMMAND_NAMES includes impact"
  - "structural five-subsection-order test for all four orchestrator routes"
  - "both runtime trees (.opencode/, .claude/) re-emitted byte-clean and idempotently"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structural route-shape check (subsection header positions, not prose fidelity) added to test_orchestrator_topology.py — mirrors the plan-checker's warning that prose claims alone are checks-that-cannot-fail"

key-files:
  created:
    - harness/commands/impact.md
  modified:
    - harness/agents/orchestrator.md
    - tools/harness_lint/tests/test_commands.py
    - tools/harness_lint/tests/test_orchestrator_topology.py
    - tools/harness_emit/tests/test_coexist.py
    - .opencode/command/impact.md
    - .opencode/agent/orchestrator.md
    - .claude/commands/impact.md
    - .claude/agents/orchestrator.md
    - tools/harness_emit/emit-manifest.json
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - AGENTS.md

key-decisions:
  - "Added a fifth structural test (test_every_route_carries_all_five_subsections_in_order) beyond the plan's stated scope, per the plan's own hard-constraint strengthening the plan-checker flagged — mutation-proved against an out-of-order injection before commit"
  - "tools/harness_emit/tests/test_coexist.py's hardcoded '18' (test_all_18_commands_emit_to_both_trees) was a Rule-1 auto-fix: this file was not in the plan's files_modified list but was broken directly by the plan's own 18->19 change, same class as the test_commands.py guard it mirrors"

requirements-completed: [MONO-08, MONO-09]

# Metrics
duration: 35min
completed: 2026-07-30
---

# Phase 49 Plan 02: Contract Impact Command Wiring Summary

**`/impact <contract>` is now command 19 of 19: a thin macro invoking Plan 01's reporter, replacing the contract-change route's inline `uv run python -c` one-liner, with both runtime trees re-emitted byte-clean and idempotent, and the SessionStart injector + CI proven structurally untouched.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-07-30T03:05:00Z (approx)
- **Completed:** 2026-07-30T03:42:38Z
- **Tasks:** 3 completed
- **Files modified:** 11 (1 created, 10 modified)

## Accomplishments

- `harness/commands/impact.md` — thin command (`description`/`agent: orchestrator`/`subtask: true`
  frontmatter, one `!`uv run python -m tools.contract_graph.impact "$ARGUMENTS"`` shell line), no
  `python -c` inline logic (`grep -c "python -c" harness/commands/impact.md` → `0`).
- `tools/harness_lint/tests/test_commands.py` — `test_command_count_is_stable` bumped to 19,
  `EXPECTED_COMMAND_NAMES` gains `"impact"` (alphabetical, between `flow` and `lint`). Mutation-proved:
  reverting to `== 18` fails with `assert 19 == 18` (captured, then restored).
- `harness/agents/orchestrator.md` — the `contract-change` route's *Repository evidence* block now
  names `/impact <path/to/contract.schema.json>` instead of the inline
  `uv run python -c "from tools.harness_config import ...; from tools.contract_graph import ..."`
  one-liner; the block's own "A single-command form of this block is planned" forward-reference is
  discharged for this route only. The other three routes (`small-change`, `bugfix`, `feature`) are
  byte-unchanged — confirmed by `git diff` showing exactly the 20-line block replacement.
- `tools/harness_lint/tests/test_orchestrator_topology.py` — added
  `test_every_route_carries_all_five_subsections_in_order`, an automated structural check (per the
  plan's strengthened hard constraint) that every `## Route:` section carries *When to use*, *Steps*,
  *Repository evidence*, *Stop condition*, *Next command* in that exact order — not merely that the
  prose still mentions each. Mutation-proved: injecting an out-of-order `**Next command**` header into
  the `feature` route fails with an explicit position mismatch; reverted and re-confirmed green.
- Both runtime trees re-emitted via `uv run python -m tools.harness_emit`: `impact.md` projected to
  `.opencode/command/` and `.claude/commands/`, `orchestrator.md` re-projected to both agent trees,
  `AGENTS.md`'s HARNESS-MANAGED command list regenerated to include `impact`. A second immediate
  re-emit produced zero further diff (idempotent).
- `tools/harness_emit/tests/test_coexist.py`'s `test_all_18_commands_emit_to_both_trees` (a real,
  previously-passing test that broke the moment the 19th command existed) was renamed to
  `test_all_19_commands_emit_to_both_trees`, its count assertions bumped to 19, and its docstring's
  count-history extended with the Phase 49 line — a Rule 1 auto-fix, not a plan scope change.
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` regenerated via
  `--snapshot-update` (the projected command/route text changed shape, exactly as the plan
  anticipated).
- MONO-09 no-growth proofs, all recorded directly (not merely asserted):
  - `git diff --stat -- tools/memory_regen/inject.py` → empty
  - `git diff --stat -- .github/workflows/ci.yml` → empty
  - `grep -rn "impact" .github/workflows/ci.yml` → zero hits
  - `uv run pytest tools/memory_regen/tests/test_inject_determinism.py -q` → 7 passed, file unmodified
  - `uv run pytest -q` (full suite) → **951 passed**

## Task Commits

Each task was committed atomically:

1. **Task 1: Create harness/commands/impact.md and bump the command-surface guards** - `4fa4ef1` (feat)
2. **Task 2: Rewrite the contract-change route's Repository evidence block** - `0b8c1f9` (feat)
3. **Task 3: Emit round-trip + no-growth proofs (injector, CI)** - `0aedf82` (feat)

**Plan metadata:** (this commit, following)

## Files Created/Modified

- `harness/commands/impact.md` - new thin `/impact` command
- `harness/agents/orchestrator.md` - contract-change route's Repository evidence block rewritten
- `tools/harness_lint/tests/test_commands.py` - count guard 18→19, `EXPECTED_COMMAND_NAMES` +impact
- `tools/harness_lint/tests/test_orchestrator_topology.py` - new structural five-subsection-order test
- `tools/harness_emit/tests/test_coexist.py` - count guard 18→19 (Rule 1 fix)
- `.opencode/command/impact.md`, `.claude/commands/impact.md` - re-emitted projections
- `.opencode/agent/orchestrator.md`, `.claude/agents/orchestrator.md` - re-emitted projections
- `tools/harness_emit/emit-manifest.json` - updated ownership manifest
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` - regenerated snapshot
- `AGENTS.md` - HARNESS-MANAGED command list regenerated (via emitter, not hand-edited)

## Decisions Made

- Implemented the plan-checker's strengthened hard constraint (structural five-subsection-order
  assertion) as a new test rather than extending an existing one, since no prior test parsed route
  sections by name — keeping the new check isolated and independently mutation-provable.
- Treated `test_coexist.py`'s stale `18` as a Rule 1 bug fix (a real test this plan's own change
  broke), not a deviation requiring a checkpoint — it mirrors the exact guard class
  (`test_commands.py`) the plan already named for bumping, just in a sibling file the plan's
  `files_modified` list omitted.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `tools/harness_emit/tests/test_coexist.py`'s hardcoded command count broke**
- **Found during:** Task 3, running `uv run pytest tools/harness_emit tools/memory_regen -q`
- **Issue:** `test_all_18_commands_emit_to_both_trees` asserted `len(opencode_cmds) == 18` /
  `len(claude_cmds) == 18` against the real `harness/commands/*.md` source tree — a genuine,
  previously-green test broken the moment `/impact` became the 19th command file, but not listed
  in the plan's `files_modified`.
- **Fix:** Renamed the test to `test_all_19_commands_emit_to_both_trees`, bumped both count
  assertions to 19, extended the docstring's count-history commentary with the Phase 49 line
  (mirroring the existing per-phase history format), and updated the module docstring's "18
  harness commands" to "19".
- **Files modified:** `tools/harness_emit/tests/test_coexist.py`
- **Verification:** `uv run pytest tools/harness_emit tools/memory_regen -q` → 154 passed.
- **Committed in:** `0aedf82` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — a sibling command-count guard, same class as the
plan's own `test_commands.py` guard, broken by the same 18→19 change).
**Impact on plan:** Trivial, same-shape fix as the plan's explicitly-named guard bump. No scope
creep, no behavior change, no new gate.

## Mutation-Check Proofs (hard-constraint requirements)

### 1. `test_command_count_is_stable` (Task 1)

Reverted `== 19` to `== 18`, ran `uv run pytest tools/harness_lint/tests/test_commands.py -k
test_command_count_is_stable -v`:

```
>       assert len(_command_files()) == 18
E       AssertionError: assert 19 == 18
FAILED tools/harness_lint/tests/test_commands.py::test_command_count_is_stable
```

Restored `== 19` immediately after capturing the failure; full file re-ran green (79 passed).

### 2. `test_every_route_carries_all_five_subsections_in_order` (Task 2)

Injected a duplicate out-of-order `**Next command**` header into the `feature` route's body, ran
`uv run pytest tools/harness_lint/tests/test_orchestrator_topology.py::test_every_route_carries_all_five_subsections_in_order
-v`:

```
E       AssertionError: route 'feature' has its five subsections out of order:
E       [('When to use', 2), ('Steps', 179), ('Repository evidence', 1217),
E        ('Stop condition', 2266), ('Next command', 2241)]
FAILED ...::test_every_route_carries_all_five_subsections_in_order
```

Reverted the injection immediately after capturing the failure; full topology file re-ran green
(4 passed).

## Issues Encountered

None beyond the `test_coexist.py` Rule-1 fix documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 49 (Contract Impact) is complete: MONO-08 (Plan 01's reporter) and MONO-09 (this plan's
  on-demand-only wiring, structurally proven) are both closed.
- Command count is durably pinned at 19 across two independent guard files
  (`tools/harness_lint/tests/test_commands.py`, `tools/harness_emit/tests/test_coexist.py`) —
  any future command addition/removal now fails both.
- The contract-change route's evidence step is a single named command; the other three routes'
  "single-command form is planned" forward-references remain open for a future phase to close, out
  of this plan's scope.
- Full suite (`uv run pytest -q`) green: 951 passed. Working tree clean after the final task
  commit.

---
*Phase: 49-contract-impact*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: harness/commands/impact.md
- FOUND: harness/agents/orchestrator.md
- FOUND: tools/harness_lint/tests/test_commands.py
- FOUND: tools/harness_lint/tests/test_orchestrator_topology.py
- FOUND: tools/harness_emit/tests/test_coexist.py
- FOUND: .opencode/command/impact.md
- FOUND: .claude/commands/impact.md
- FOUND commit: 4fa4ef1 (Task 1)
- FOUND commit: 0b8c1f9 (Task 2)
- FOUND commit: 0aedf82 (Task 3)
- FOUND commit: f005614 (this docs commit)
