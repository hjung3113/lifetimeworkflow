---
phase: 46-product-flow
plan: 02
subsystem: harness
tags: [flow, command, harness-emit, emit-manifest, coexist, syrupy, activeContext, PROD-04]

# Dependency graph
requires:
  - phase: 46-product-flow
    plan: 01
    provides: the four `## Route:` sections in `harness/agents/orchestrator.md` that `/flow` points at as the authority for the steps
  - phase: 44-command-consolidation
    provides: the 17-command live surface this plan takes to 18
provides:
  - "`harness/commands/flow.md` — the deployed product's named entry point, the one command PROD-04 authorises"
  - Both runtime projections (`.opencode/command/flow.md`, `.claude/commands/flow.md`) and the +2 ownership-manifest rows
  - A command-count coexistence gate that reads 18 at all four sites including the function NAME
affects: [46-03 phase verification, v2.6 /impact]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A new command file requires an explicit targeted `git add` before `git commit -- <pathspec>`: the pathspec form only accepts paths already known to git and aborts the entire commit on an untracked one"
    - "The renderer enumeration for a command ADDITION is identical to a DELETION's (D-16 class), and includes two artifacts D-14 does not name: `AGENTS.md`'s emitter-spliced block and `README.md`'s hand-maintained list"

key-files:
  created:
    - harness/commands/flow.md
    - .opencode/command/flow.md
    - .claude/commands/flow.md
  modified:
    - tools/harness_emit/emit-manifest.json
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - AGENTS.md
    - README.md

key-decisions:
  - "`/flow` is a pure router: no `!`-prefixed shell block, so `/checkpoint` and `/orient` keep sole ownership of execution and `test_install_completeness.py`'s `python -m tools.X` regex-walk is trivially satisfied"
  - "The route table names the four routes and their owners but does NOT restate the steps — `harness/agents/orchestrator.md`'s `## Route:` sections are cited as the single authority, so the two files cannot drift"
  - "Step 3 words the resume as pointer-then-read: `/orient`'s injector payload names `activeContext.md`, it never inlines the body"
  - "Fixed `test_coexist.py:3`'s stale \"20 harness commands\" — a sixth instance of the D-16 class, false since Phase 41, asserted by nothing"

metrics:
  duration: ~25 min
  completed: 2026-07-29
  commits: 1
  tasks: 2
---

# Phase 46 Plan 02: /flow — the product's named entry point Summary

Added `harness/commands/flow.md` (17 → 18 commands) — a shell-free router that names the four
routes, points at the orchestrator's `## Route:` sections as the authority, and round-trips
route/step/next-command through `.memory/state/activeContext.md` via the existing `/checkpoint`
writer and `/orient` reader — and repaired, in the same commit, all six committed artifacts that
render the live command set.

## What was built

**Task 1 — `harness/commands/flow.md` (66 lines, source only).** Frontmatter `agent: orchestrator`,
`subtask: false`, description carrying both routing trigger tokens. Body: (1) a four-row route table
— route / trigger / owner — with an explicit "stop and ask, there is no fifth route" and the
`research`-is-not-a-route note (D-06); (2) the literal three lines to record
(`- Route:` / `- Step:` / `- Next command:`) under `## In flight` / `## Next`, with **no new state
file, writer, or reader** stated plainly (D-10); (3) resume via `/orient`'s pointer payload, worded
as pointer-then-read; (4) the six-field completion contract referenced, not re-copied. Auto-covered
by the glob-driven command lint with **zero edits** to `test_commands.py`; `flow` was not added to
`EXPECTED_GOLDEN_ADJACENT`, and no `EXPECTED_COMMANDS` was created (D-15).

**Task 2 — the renderer enumeration, all in commit `4df76db`.**

| # | Renderer | Named by D-14? | Change |
|---|----------|----------------|--------|
| 1 | `tools/harness_emit/tests/test_coexist.py:40` — function **NAME** | yes | `test_all_17_…` → `test_all_18_commands_emit_to_both_trees` |
| 2 | `test_coexist.py:41` docstring + phase-history paragraph | yes | 17 → 18, plus the Phase-46 history sentence |
| 3 | `test_coexist.py:73,74` assertions + f-strings | yes | `== 17` → `== 18` (both trees) |
| 4 | `tools/harness_emit/emit-manifest.json` | yes | **+2 rows**, self-generated, in the commit pathspec |
| 5 | `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` | yes | `--snapshot-update` in-commit, +130 lines (≈2× the 66-line source, one projection per runtime) |
| 6 | `AGENTS.md` HARNESS-MANAGED `**Commands**` line | **NO** | emitter-spliced; gains `flow` after `fan-out-synthesize` |
| 7 | `README.md:119-122` hand-maintained 17-name list | **NO** | `/flow` inserted in sorted position between `/fan-out-synthesize` and `/lint`; asserted by nothing |
| 8 | `test_coexist.py:3` module docstring "20 harness commands" | **NO — found in-file** | stale since Phase 41 (live was 17); corrected to 18 |

Items 6, 7 and 8 are the three the phase context's D-14 enumeration does not name. Item 8 is the
sixth instance of the D-16 class and is the reason the file was read end-to-end rather than
line-patched at the four cited offsets.

**Checked and cleared, as the plan directed — none needed edits:** `caps.py` (no `EXPECTED_COMMANDS`),
`test_commands.py` (glob-driven), `destinations.py` (glob), `adoption_scan`'s
`test_snapshots.ambr` (renders a decoupled `_FIXED_CATALOG`), `docs_sync` / `memory_regen` snapshots.
`CLAUDE.md`'s managed block is pointer-only prose and came back byte-unchanged, so it stayed out of
the pathspec.

## Measurements

| Metric | Value |
|--------|-------|
| `ls harness/commands/*.md \| wc -l` | **18** |
| `uv run pytest -q` | **881 passed**, 7 snapshots passed, 0 failures (876 → 881, **+5**) |
| `grep -c flow tools/harness_emit/emit-manifest.json` | **2** (`.claude/commands/flow.md`, `.opencode/command/flow.md`) |
| `git diff --shortstat HEAD~1 HEAD` (D-24) | **8 files changed, 333 insertions(+), 8 deletions(-)** |
| `uv run python -m tools.ruff_baseline` | exit 0 — 74 findings, baseline 74 |
| `git diff HEAD~1 HEAD -- uv.lock` | empty |
| New files under `contracts/`, `harness/{skills,agents,git-hooks}`, `.github/workflows/` | 0 |
| `git status --porcelain` post-commit | empty |

**The +5, not +4.** Two suites parametrize per command file: four ids from
`tools/harness_lint/tests/test_commands.py` (`test_frontmatter_parses`,
`test_description_is_routing_signal`, `test_agent_field_well_formed`,
`test_subtask_is_boolean_when_present`) plus one from
`test_agent_referential_integrity.py::test_command_agent_resolves_to_real_persona`. The renamed
`test_coexist` function is a rename, not an addition. 881 is the baseline Plan 03 reads.

## Deviations from Plan

None. The plan executed exactly as written, including its two pre-measured corrections:

- **The mandatory `git add`.** `git commit -- <pathspec>` was handed eight paths, three of them
  untracked. The explicit `git add harness/commands/flow.md .opencode/command/flow.md
  .claude/commands/flow.md` ran first, as prescribed; the commit then succeeded and named all eight
  paths. Not a D-18 violation — only `git add -A`, `git add .` and `git commit -a` are forbidden, and
  an explicit targeted add is already the pattern in `harness/commands/checkpoint.md`.
- **The emit-drift replica ran after the commit**, per the plan's step 7, and exited 0. It was not
  run pre-commit, where CI's `git add -A && git diff --cached --exit-code` form exits 1 by
  construction.

Every predicate in both `<verify>` blocks held. Nothing surfaced that the plan did not anticipate.

## Net surface change

**+1 command, +0 everything else** — no gate, tool, contract, skill, agent, hook, CI job, state
file, or dependency. `flow.md` carries no `!` shell block and no new permission; `agent: orchestrator`
inherits the existing `edit: ask` / `bash: ask` matrix (T-46-07). No file from
`docs/references/opencode-matt-workflows/` is imported or depended on (T-46-08). `uv.lock` unchanged
(T-46-SC). The manifest was never hand-edited but was in the pathspec (T-46-05); the coexist function
was renamed, not just its assertions (T-46-06).

## Threat Flags

None. The commit introduces no network endpoint, auth path, file-access pattern, or schema change.

## Known Stubs

None.

## Success criteria

ROADMAP SC5 (the 18-count) and the `+1 command, +0 everything else` half of SC8 are satisfied at
commit `4df76db`. SC6's round-trip and the whole-phase form of SC8 belong to Plan 03.

## Commits

- `4df76db` — `feat(46): /flow — the product's named entry point (PROD-04)` (8 files, +333/−8)

## Self-Check: PASSED

- `harness/commands/flow.md` — FOUND
- `.opencode/command/flow.md` — FOUND
- `.claude/commands/flow.md` — FOUND
- commit `4df76db` — FOUND in `git log`
