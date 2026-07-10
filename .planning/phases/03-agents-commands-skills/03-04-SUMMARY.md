---
phase: 03-agents-commands-skills
plan: 04
subsystem: harness
tags: [opencode, claude-code, slash-commands, golden-runner, pytest, frontmatter, harness-lint]

# Dependency graph
requires:
  - phase: 03-02
    provides: tools/harness_lint/frontmatter.py (shared parse_frontmatter)
  - phase: 03-03
    provides: harness/agents/*.md (five personas the commands' agent: fields resolve to)
  - phase: 01
    provides: tools/golden_runner (runner + approve human-gate), uv/pytest/ruff toolchain, docs/adr MADR convention, .memory/state plane
provides:
  - 8 golden-adjacent slash-command macros (harness/commands/{build,test,lint,golden,golden-approve,adr,checkpoint,component}.md)
  - test_commands.py — glob-based STRUCTURAL command frontmatter gate (per-plan wave-2 gate)
  - test_agent_referential_integrity.py — phase-level full-suite integration test (agent: → real persona file)
affects: [03-05, 03-06, 03-07, phase-06-emitter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Thin command macro: markdown frontmatter (agent/description/subtask) + body that wraps an EXISTING tools/* CLI — no re-implemented logic"
    - "dotnet path presence-gated on $HOME/.dotnet, announce+skip (non-fatal) when absent (D-05)"
    - "Glob-driven structural lint auto-covers later-wave commands with no edits"
    - "Cross-file (agent-file) resolution split OUT of the per-plan structural gate into a phase-level full-suite integration test to avoid a false cross-wave gate"

key-files:
  created:
    - harness/commands/build.md
    - harness/commands/test.md
    - harness/commands/lint.md
    - harness/commands/golden.md
    - harness/commands/golden-approve.md
    - harness/commands/adr.md
    - harness/commands/checkpoint.md
    - harness/commands/component.md
    - tools/harness_lint/tests/test_commands.py
    - tools/harness_lint/tests/test_agent_referential_integrity.py
  modified: []

key-decisions:
  - "Command agent: fields kept to the five Plan-03 persona slugs (orchestrator, python-engineer); golden/lint → python-engineer, the rest → orchestrator so every reference resolves"
  - "Structural gate asserts a well-formed agent SLUG (lowercase alnum + hyphens) but NOT file existence; existence is the phase-level integration test"
  - "dotnet gate resolves via explicit $HOME/.dotnet/dotnet (not PATH), announces a non-fatal SKIP when absent"

patterns-established:
  - "Thin-macro-over-tested-CLI: commands add zero new logic; golden/golden-approve reuse tools.golden_runner verbatim (Don't-Hand-Roll)"
  - "Two-tier command validation: per-plan STRUCTURAL glob gate (test_commands.py) + phase-level referential-integrity integration test (test_agent_referential_integrity.py)"

requirements-completed: [CMD-01, CMD-02, CMD-03, CMD-04, CMD-07, CMD-09]

# Metrics
duration: 11min
completed: 2026-07-08
---

# Phase 3 Plan 04: Golden-Adjacent Command Macros + Structural Command Gate Summary

**Eight thin `harness/commands/*.md` macros wrapping the tested Phase-1 CLIs (golden_runner, uv/pytest, ruff, memory state, MADR), a glob-based STRUCTURAL frontmatter validator, and a phase-level agent-referential-integrity integration test — with the dotnet path presence-gated and /golden-approve's human-only refusal preserved.**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-07-08
- **Completed:** 2026-07-08
- **Tasks:** 3
- **Files created:** 10

## Accomplishments
- Authored the 8 golden-adjacent commands (`/build /test /lint /golden /golden-approve /adr /checkpoint /component`) as neutral markdown macros over existing `tools/*` CLIs — no re-implemented golden/normalize/approval logic.
- `/build` and `/test` gate the .NET path on the explicit `$HOME/.dotnet/dotnet` bootstrap path and **announce + skip (non-fatal)** when the SDK is absent (BOOT-01 egress deferral, D-05).
- `/golden-approve` documents the already-coded human-only refusal (exit 3 without `--approve` + `--adr` + `$GOLDEN_APPROVE_HUMAN` token) — no agent self-bless (CMD-03).
- `test_commands.py` glob-validates all command frontmatter STRUCTURALLY (valid frontmatter, routing-trigger description P7, well-formed non-empty agent slug, boolean subtask) — auto-covers Wave-3 migration commands with no edits.
- `test_agent_referential_integrity.py` proves every command `agent:` resolves to a real `harness/agents/<agent>.md` under the full suite (green after wave 2).

## Task Commits

1. **Task 1: Author the 8 golden-adjacent command macros** - `792e37b` (feat)
2. **Task 2: Glob-based STRUCTURAL command frontmatter validator** - `381fb08` (test)
3. **Task 3: Phase-level agent-referential-integrity integration test** - `e22d3ef` (test)

_Task 2 is a validator against subjects (the commands) authored in Task 1, so it went green immediately; the invariant was proven real by a transient bad-command check (noun-phrase description, missing agent, non-boolean subtask each fail) before committing._

## Files Created/Modified
- `harness/commands/build.md` - polyglot build; dotnet-gated + `uv sync --all-packages`
- `harness/commands/test.md` - `uv run pytest` + dotnet-gated `dotnet test`
- `harness/commands/lint.md` - `ruff check` + `ruff format --check` + dotnet-gated `dotnet format`
- `harness/commands/golden.md` - wraps `python -m tools.golden_runner.runner $ARGUMENTS` (exit 0 PASS / 1 FAIL)
- `harness/commands/golden-approve.md` - wraps `python -m tools.golden_runner.approve`; documents the exit-3 human gate
- `harness/commands/adr.md` - next-numbered append-only MADR scaffold; never edits an existing ADR
- `harness/commands/checkpoint.md` - writes `.memory/state/{activeContext,progress}.md` + individual-file git commit
- `harness/commands/component.md` - scaffolds a member in mandated order (structure → self-sufficient AGENTS.md → tests, P11)
- `tools/harness_lint/tests/test_commands.py` - STRUCTURAL glob gate (33 cases green)
- `tools/harness_lint/tests/test_agent_referential_integrity.py` - phase-level referential-integrity integration test (8 cases green)

## Decisions Made
- Command `agent:` fields restricted to the five Plan-03 persona slugs so the phase-level integration test resolves every reference (`golden`/`lint` → `python-engineer`; `build`/`test`/`golden-approve`/`adr`/`checkpoint`/`component` → `orchestrator`).
- Structural gate asserts agent well-formedness (slug regex) but deliberately NOT file existence — existence is the decoupled Task-3 integration test (avoids a false cross-wave gate, per plan).
- dotnet gate uses the explicit absolute `$HOME/.dotnet/dotnet` path (mirrors golden_runner P5), not a bare PATH lookup.

## Deviations from Plan

None - plan executed exactly as written. (The cosmetic duplicate `</output>` tag in the plan file was ignored per instructions.)

## Issues Encountered
None. Full suite: `168 passed, 2 skipped` (the 2 skips are the .NET end-to-end golden spawns, deferred by BOOT-01 egress — expected/unchanged).

## Threat Coverage
- **T-03-13 (command injection via $ARGUMENTS):** commands pass `$ARGUMENTS` positionally to list-form CLIs (golden_runner is `shell=False`); no shell strings built from args — documented in `/golden` and `/golden-approve`.
- **T-03-14 (agent self-bless):** `/golden-approve` reuses `tools.golden_runner.approve` refusal (exit 3); not re-implemented.
- **T-03-15 (description-as-label):** `test_commands.py` asserts a routing trigger token per command (P7).
- **T-03-16 (dangling agent reference):** structural gate asserts well-formed agent field; `test_agent_referential_integrity.py` asserts resolution to a real persona file under the full suite.

## Next Phase Readiness
- Golden-adjacent half of success criterion 3 satisfied. Wave-3 migration commands (`/new-normalization-rule`, `/strangler-step`, `/docs-sync`) will be auto-covered by the glob-driven `test_commands.py` and `test_agent_referential_integrity.py` with no edits to those tests.
- No new blockers. .NET dotnet-path execution remains deferred (BOOT-01 egress) — commands skip gracefully.

## Self-Check: PASSED

All 10 created files present; all 3 task commits (`792e37b`, `381fb08`, `e22d3ef`) exist in history. Full suite: 168 passed, 2 skipped (dotnet deferred).

---
*Phase: 03-agents-commands-skills*
*Completed: 2026-07-08*
