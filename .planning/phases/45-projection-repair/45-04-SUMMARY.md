---
phase: 45-projection-repair
plan: 04
subsystem: root-documentation
tags: [cer-11, projection-repair, agents-md, readme, hand-owned-prose]
requires: ["45-02"]
provides:
  - "root AGENTS.md free of deleted modules, commands and directories"
  - "README.md + README.ko.md free of retired commands and deleted surface"
  - "README.ko.md unlinked from docs/how-to/task-lifecycle.md (unblocks plan 05)"
affects:
  - AGENTS.md
  - README.md
  - README.ko.md
tech-stack:
  added: []
  patterns: ["hand-edit outside the HARNESS-MANAGED block; verified re-emit-stable"]
key-files:
  created:
    - .planning/phases/45-projection-repair/45-04-SUMMARY.md
  modified:
    - AGENTS.md
    - README.md
    - README.ko.md
decisions:
  - "AGENTS.md:7-8 deliberately left unchanged — all three artifacts it names are live and the phrase CER-11/ROADMAP quote is not in the file"
  - "REQUIREMENTS.md:105 / ROADMAP.md:245 miscite the golden-path table as AGENTS.md:52-62; the live table was :62-71"
  - "README.md mermaid golden-runner node relabelled rather than deleted, to satisfy the plan's no-golden_runner grep while keeping the diagram honest"
metrics:
  duration: ~15 min
  completed: 2026-07-29
---

# Phase 45 Plan 04: Root Document Projection Repair Summary

Repaired the three hand-owned root documents (`AGENTS.md`, `README.md`, `README.ko.md`) so they
stop naming the golden-runner package, the root `golden/` directory, `harness/task-control/`, and
the retired `/golden`, `/golden-approve` and `/pipeline` commands — all outside the emitter's
managed block, so no re-emit would ever have fixed them.

## What Shipped

**Commit `3094ec5` — `AGENTS.md` (1 file, +8/-7)**

- `:26-33` constitution-plane sentence: four members → **three** (`contracts/`, `docs/adr/`,
  `docs/glossary.md`), citing ADR-0012 clause (d) as superseding ADR-0001 §Decision to the extent
  that `golden/**` leaves the constitution-plane core. The "no agent self-blesses a golden
  baseline" rule is kept and now names the CODEOWNERS `/examples/*/golden/` ratification route.
- Golden-path command table: both `tools.golden_runner` rows deleted (runner + approve).
- CORE monorepo map: the root `golden/` line deleted.
- `tools/` engine list: `golden_runner` removed.
- `:100-109` HARNESS-MANAGED block: untouched.

**Commit `3ac6cf0` — `README.md` + `README.ko.md` (2 files, +15/-19)**

`README.md`
- two-plane feature row: constitution → three members.
- mermaid `CONST` subgraph: `G["golden/"]` replaced by `GL["docs/glossary.md"]`; the
  normalized-compare edge now points at `golden runner (instance overlay)`.
- quickstart: the `uv run python -m tools.golden_runner.runner` step deleted (this block is the
  CORE quick start).
- command list: `/golden`, `/golden-approve`, `/pipeline` replaced by the live 17-command set.
- layout tree: root `golden/` line deleted; `golden_runner` removed from the `tools/` list.
- "Machines gate, humans ratify" bullet restated as the `GOLDEN_APPROVE_HUMAN` token +
  CODEOWNERS `/examples/*/golden/` route.
- `:46`, `:53`, `:59`, `:60`, `:153`, `:186`, `:216` untouched — they name gates/CI jobs that
  still exist (`.github/workflows/ci.yml` still has the `golden` job).

`README.ko.md`
- two-plane row: three members.
- `/golden-approve` row restated as the human token + CODEOWNERS ratification.
- `harness/task-control/  # gate-registry` line deleted (dir died Phase 43, registry Phase 44).
- `golden/` tree line deleted.
- docs line: ADR range `0001–0008` → `0001–0012`, and the `how-to/task-lifecycle.md` link
  **removed** — this is what clears plan 05's deletion of that file.
- `golden_runner` removed from the tools list.
- `:107` ("contract-drift/golden 게이트 green 유지") left alone — those gates are live.

## Verification

| Check | Expected | Observed |
|---|---|---|
| `uv run pytest -q` after commit 1 | 876 passed, 7 snapshots | **876 passed, 7 snapshots** |
| `uv run pytest tools/memory_regen -q` after commit 1 | 82 passed | **82 passed, 4 snapshots** |
| `grep -n 'golden_runner\|^golden/' AGENTS.md` | no output | **no output** |
| `grep -c 'golden/' AGENTS.md` | ≥1 | **3** (`:30`, `:32`, and the instance map line `:92`) |
| `uv run python -m tools.harness_emit` + `git status --porcelain` | edits survive re-emit | **clean — byte-identical** |
| `uv run pytest -q` after commit 2 | 876 passed, 7 snapshots | **876 passed, 7 snapshots** |
| `grep -n 'golden_runner\|golden-approve\|/pipeline\|task-control\|task-lifecycle' README.md README.ko.md` | no output | **no output** |
| every `` `/cmd` `` in README resolves under `harness/commands/` | no DANGLING | **17 found, 0 dangling** |
| final `git status --porcelain` | empty | **empty** |

The instance map line at `AGENTS.md:92` (`examples/<instance>/   Own contracts/, golden/, ...`) is
what keeps `test_agents_md.py:44`'s literal `golden/` requirement satisfied, and `uv run pytest`
survives in the command table for `:48-50`. The gate was not weakened.

## Recorded Decisions (for the milestone-close PR)

**1. `AGENTS.md:7-8` is deliberately unchanged.** It reads *"Prose is advisory — the backstop is
the SessionStart injector plus the hooks (contract-guard, polyglot-boundary linter)."* All three
named artifacts are live (`harness/plugins/session-inject.ts`, `harness/plugins/contract-guard.ts`,
`harness/plugins/polyglot-lint.ts`), and the phrase **"the true backstop"** that CER-11's CONTEXT
D-07 and ROADMAP SC-4 both quote **does not appear anywhere in the file**. This is a citation defect
in the requirement, not a defect in `AGENTS.md`. Correcting a line that is already true would be
scope invention, so the line was left alone and the defect is recorded here.

**2. Corrected line citation.** `REQUIREMENTS.md:105` and `ROADMAP.md:245` both cite
`AGENTS.md:52-62` as the stale golden-path table. Measured on the pre-edit file, `:52-62` is
§B *Working agreements* and is not stale; the golden-path table was at **`:62-71`**. The
miscitation has been copied forward through the requirements themselves — future readers should
work from live line numbers, not from the requirement's.

## Deviations from Plan

**1. `README.md` mermaid golden-runner node: relabelled, not path-scoped.**
The Task 2 action text offers "re-scope the node to the instance overlay (or drop it and leave the
edge pointing at the instance-side runner)". Scoping it literally as
`examples/<instance>/golden_runner` (the real directory name) reintroduced the token
`golden_runner`, which the task's own verify grep asserts must produce **no output**. The two
instructions are mutually exclusive as written. Resolved in favour of the verify criterion: the
edge label is `golden runner (instance overlay)` — honest about the runner still existing and no
longer being core, and grep-clean. Recorded rather than silently chosen.

**2. No other deviations.** No Rule 1/2/3 auto-fixes were needed; no architectural (Rule 4)
questions arose; no package-manager installs; `uv.lock` untouched.

## Observations the Plan Did Not Anticipate

- **The HARNESS-MANAGED block moved to `:101-110`.** The plan measured it at `:100-109`. The
  constitution-plane paragraph grew by one net line, shifting the block down by one. This does not
  violate any criterion — the criterion was that every *edit* sits outside the block, which holds
  (all edits are `:26-86`), and the re-emit check confirmed byte-identical survival. But a future
  plan quoting `:100-109` will be one line off.
- **Both READMEs still advertise `tests-982 passing` / `982 통과`** (`README.md:12`, `:107`;
  `README.ko.md:60`) against an actual core suite of 876. This is stale surface of exactly the kind
  CER-11 targets, but it is a *count*, not a "deleted module, command, path or directory", so D-06
  does not authorize touching it and this plan's task list does not name it. **Left unchanged;
  flagged for a follow-up.**
- **`README.md:128`** claims `harness/agents/` holds "5 personas" — verified accurate
  (`ls harness/agents/*.md` = 5). No action.
- The `README.md` core quickstart is now four steps rather than five; the numbering is contiguous
  because the deleted golden step was last.

## Known Stubs

None.

## Threat Flags

None — no new network, auth, file-access or schema surface. All three files are prose; no test
reads either README (`git grep 'README'` over the test tree returns no file reads).

## Self-Check: PASSED

- `AGENTS.md` — FOUND, modified, committed in `3094ec5`
- `README.md` — FOUND, modified, committed in `3ac6cf0`
- `README.ko.md` — FOUND, modified, committed in `3ac6cf0`
- commit `3094ec5` — FOUND in `git log`
- commit `3ac6cf0` — FOUND in `git log`
- working tree clean; suite 876 passed / 7 snapshots; `tools/memory_regen` 82 passed
