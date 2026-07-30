---
phase: 03-agents-commands-skills
plan: 03
subsystem: agents
tags: [opencode, claude-code, agent-personas, frontmatter, permission, dual-representation, read-only-reviewer, harness-lint]

# Dependency graph
requires:
  - phase: 03-agents-commands-skills (03-02)
    provides: tools/harness_lint/frontmatter.py (shared parse_frontmatter reused by test_agents.py)
  - phase: 03-agents-commands-skills (03-01)
    provides: harness/permission-matrix.json (15-key set + dotnet/uv/pytest bash scope mirrored into persona permission blocks)
provides:
  - "harness/agents/orchestrator.md — AGENT-01 primary orchestrator (task/todowrite delegation, no heavy edits)"
  - "harness/agents/dotnet-engineer.md — AGENT-02 (permission.bash {dotnet *: allow} + Claude Read,Edit,Bash,Grep,Glob)"
  - "harness/agents/python-engineer.md — AGENT-03 (permission.bash {uv *, pytest *: allow} + same Claude tools)"
  - "harness/agents/code-reviewer.md — AGENT-04 read-only reviewer in BOTH representations (edit/bash/write deny; tools Read,Grep,Glob)"
  - "harness/agents/explorer.md — AGENT-05 cheap-tier (provider/explorer-tier) read-only explorer returning file paths"
  - "tools/harness_lint/tests/test_agents.py — structural validation of all 5 personas + read-only invariant in both reps"
  - "tools/harness_lint/tests/conftest.py — repo-root sys.path wiring for harness_lint tests"
affects: [03-04, 03-05, phase-6-emitter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-representation agent frontmatter: one neutral file carries opencode `permission:` AND Claude `tools:` (Phase-6 emitter splits)"
    - "Read-only invariant asserted in BOTH representations via is_read_only() (permission edit/bash/write not allow AND tools has no Write/Bash/Edit)"
    - "Routing-signal descriptions (verb-first 'Use when…') gated by a trigger-token assertion (P7)"
    - "Placeholder model tier tokens only (provider/explorer-tier) — no real model IDs"

key-files:
  created:
    - harness/agents/orchestrator.md
    - harness/agents/dotnet-engineer.md
    - harness/agents/python-engineer.md
    - harness/agents/code-reviewer.md
    - harness/agents/explorer.md
    - tools/harness_lint/tests/test_agents.py
    - tools/harness_lint/tests/conftest.py
  modified: []

key-decisions:
  - "Reviewer authored with an explicit permission.write:deny (defensive) even though opencode folds writes into edit; test tolerates 'write' as a deny-only alias so the 15-key subset check stays honest"
  - "explorer is the ONLY persona with a `model` field (provider/explorer-tier placeholder); all others omit model to inherit (primary uses global, subagents inherit caller)"
  - "orchestrator gets task/todowrite allow + edit/bash ask (delegates, no heavy edits); engineers get scoped bash last-wins mirroring permission-matrix.json"
  - "is_read_only() enforces the invariant for BOTH code-reviewer AND explorer in both runtime representations (T-03-09 / P-perm)"

requirements-completed: [AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05]

# Metrics
duration: 10min
completed: 2026-07-08
---

# Phase 3 Plan 03: Five dual-representation agent personas + read-only-reviewer structural validator Summary

**Authored the five scoped personas (orchestrator/dotnet-engineer/python-engineer/code-reviewer/explorer) as neutral `harness/agents/*.md` carrying BOTH the opencode `permission:` intent and the Claude `tools:` allowlist, and added `test_agents.py` proving each frontmatter is valid and the read-only invariant holds for reviewer AND explorer in both runtime representations.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-08
- **Tasks:** 2
- **Files created:** 7

## Accomplishments
- AGENT-01..05 satisfied: five least-privilege personas exist in neutral single source with verb-first routing-signal descriptions, correct model tiering, and dual-representation permission/tools scoping.
- Read-only-reviewer invariant (T-03-09, P-perm) proven structurally in BOTH representations: code-reviewer and explorer deny edit/bash/write in the opencode `permission` block and expose exactly `Read, Grep, Glob` in the Claude `tools` allowlist.
- Engineer bash scope mirrors `permission-matrix.json`: dotnet-engineer allows `dotnet *`, python-engineer allows `uv *` and `pytest *`, everything else gated to `ask`.
- No real model identifiers: explorer carries the placeholder `provider/explorer-tier`; all other personas omit `model` to inherit.
- `test_agents.py` (7 test functions, 23 parametrized cases) reuses the shared `parse_frontmatter` and pins exactly the five personas (no sprawl, P1/P8).

## Task Commits

1. **Task 1: Author the 5 agent personas (dual-representation)** - `e8e394c` (feat)
2. **Task 2: Structural validator for agent frontmatter (test_agents.py)** - `67ba0f4` (test)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added tools/harness_lint/tests/conftest.py**
- **Found during:** Task 2 (first pytest run of test_agents.py)
- **Issue:** `test_agents.py` imports `from tools.harness_lint import parse_frontmatter`, but the harness_lint tests dir had no conftest to put the repo root on `sys.path` (the pre-existing `test_opencode_json.py` uses path-only access and never imports `tools`). Collection failed with `ModuleNotFoundError: No module named 'tools'`.
- **Fix:** Added `tools/harness_lint/tests/conftest.py` mirroring `tools/harness_perms/tests/conftest.py` (insert `parents[3]` repo root into `sys.path`).
- **Files modified:** tools/harness_lint/tests/conftest.py
- **Commit:** `67ba0f4`

### Reconciliation note (write-key vs 15-key subset)
The plan's Task 1 action lists `write:"deny"` for code-reviewer, while Task 2 behavior requires permission keys ⊆ the 15 valid opencode keys ("write" is not among them — opencode folds writes into `edit`). Reconciled by authoring `write:deny` defensively (maximizes the read-only signal, matches the RESEARCH persona table) and defining the subset check as `keys ⊆ (15 valid ∪ {"write"} deny-only alias)`, documented in the test. The invariant remains non-vacuous.

## Verification
- `uv run pytest tools/harness_lint/tests/test_agents.py -x -q` → 23 passed.
- Non-vacuity proven: temporarily flipping code-reviewer to `edit: allow` FAILED `test_read_only_personas_have_no_write_affordance[code-reviewer]`; reverted → 23 passed (file restored byte-identical, `git diff` clean).
- `uv run pytest tools/harness_lint -q` → 27 passed.
- Full suite `uv run pytest -q` → 127 passed, 2 skipped (expected .NET egress-blocked golden-spawn skips).

## Known Stubs
None — all five personas are fully authored with concrete frontmatter and system-prompt bodies. (The `.opencode/` + `.claude/` emit from these neutral sources is Phase-6 by design, D-01.)

## Self-Check: PASSED
