---
phase: 29-docs-drive-loop-adoption-integration-closeout-v2-3-c
plan: 03
subsystem: harness-surface
tags: [DOCSUP-06, docs-update, docs-upkeep, emit-round-trip, wiring-lint]
requires:
  - tools/docs_guard/cli.py::main (the 0/1/3 exit mapping and the fixed argv)
  - tools/docs_guard/exclusions.py::exclusion_reason (29-01 — the enforcing control)
  - tools/harness_lint/caps.py::EXPECTED_SKILLS
  - tools/harness_emit/generate.py::emit (both-tree projection + the HARNESS-MANAGED merge)
provides:
  - "harness/commands/docs-update.md — the thin fixed-argv macro over tools.docs_guard"
  - "harness/skills/docs-upkeep/SKILL.md — the read-guard / edit-or-disposition / human-ratifies runbook"
  - "tools/harness_lint/tests/test_docs_update_wiring.py — the presence-AND-absence wiring lint"
  - "the four emitted twins under .opencode/ and .claude/"
affects:
  - 29-04 (seeds bindings against harness/skills/**; docs-upkeep is now part of that surface)
  - 29-05 (milestone closeout counts 25 commands / 13 skills)
tech-stack:
  added: []
  patterns:
    - "thin-command-over-coded-tool: the command re-runs the gate, never re-derives its findings"
    - "assert-the-absence: the wiring lint pins what the command must NOT contain (no glob literal, no derived-queue path)"
    - "counters move together: EXPECTED_SKILLS and the command count in one change"
key-files:
  created:
    - harness/commands/docs-update.md
    - harness/skills/docs-upkeep/SKILL.md
    - tools/harness_lint/tests/test_docs_update_wiring.py
    - .opencode/command/docs-update.md
    - .opencode/skill/docs-upkeep/SKILL.md
    - .claude/commands/docs-update.md
    - .claude/skills/docs-upkeep/SKILL.md
  modified:
    - tools/harness_lint/caps.py
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/emit-manifest.json
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - AGENTS.md
decisions:
  - "D-04 satisfied structurally: the wiring lint asserts the command body contains no `.memory/` path at all, so the fresh-clone false green cannot be reintroduced by a later edit"
  - "D-06 satisfied by pointing, not restating: the command carries zero glob literals and the skill names exclusion_reason and its three reason strings as the control"
  - "CLAUDE.md was NOT modified — its HARNESS-MANAGED fence carries prose only, no command/skill list; only AGENTS.md holds the spliced lists"
  - "The round-trip was verified with `git status --porcelain`, which sees untracked files; a bare `git diff` reported clean while four emitted files were untracked"
metrics:
  tasks: 3
  commits: 3
  tests_added: 7
---

# Phase 29 Plan 03: The `/docs-update` + `docs-upkeep` Surface Summary

One thin command and one runbook skill, authored runtime-neutrally and emitted to both runtimes —
whose correctness is mostly negative space: the command re-runs `tools.docs_guard` rather than
reading a gitignored queue, carries no second copy of the exclusion globs, and never restates
contract drift.

## What was built

| Task | Deliverable | Commit |
|------|-------------|--------|
| 1 | `tools/harness_lint/tests/test_docs_update_wiring.py` — 7 tests, RED-confirmed | `2aa3882` |
| 2 | The command, the skill, and all three counters in one change | `a3230da` |
| 3 | Both emitted trees + manifest + snapshot + the `AGENTS.md` fence | `1b0ede3` |

### The wiring lint (task 1)

Seven tests, four of which assert an **absence** — that is where the plan's risk actually lives:

| Test | Pins |
|---|---|
| `test_command_exists_and_is_routed_to_python_engineer` | D-01 — `agent: python-engineer`, `subtask: true`, routing-trigger description |
| `test_command_names_the_guard_module` | D-04 — the data source is `tools.docs_guard` |
| `test_command_names_no_memory_path` | D-04 — no `.memory/` path anywhere in the body |
| `test_command_carries_no_exclusion_glob_literal` | D-06 — none of five glob literals appears |
| `test_command_routes_all_three_exit_codes` | D-05 — `exit 0`, `exit 1`, `exit 3` all spelled |
| `test_skill_exists_and_names_the_enforcing_control` | D-06 — the body names `exclusion_reason` |
| `test_docs_upkeep_is_an_expected_skill` | D-02 — a half-widening fails here, legibly |

Frontmatter is read through the shared `parse_frontmatter`; no hand-sliced `---` fence.

### RED evidence (verbatim, run plain — never `! uv run pytest`)

```
FileNotFoundError: [Errno 2] No such file or directory:
  '/Users/hyojung/orca/lifetimeworkflow/harness/commands/docs-update.md'

AssertionError: harness/skills/docs-upkeep/SKILL.md is missing

AssertionError: docs-upkeep is not in caps.EXPECTED_SKILLS — the skill and the cap must move together
assert 'docs-upkeep' in frozenset({'brownfield-adoption', 'context-budget', 'data-contracts',
  'fan-out-synthesize', 'gate-model', 'golden-debug', ...})

7 failed in 0.07s
```

All seven failed for the intended reason (the two source files absent, the cap not yet widened) —
no collection or import error masquerading as RED.

### The three counters (task 2, one commit)

- `tools/harness_lint/caps.py` — `EXPECTED_SKILLS` 12 → **13** (`docs-upkeep`), with a Phase-29
  sentence added to the enumeration comment in the Phase-8/10 style.
- `tools/harness_emit/tests/test_coexist.py` — all **three** literals: the `def` name
  (`test_all_24_…` → `test_all_25_…`) and both `assert len(...) == 24` → `== 25`, plus the
  Phase-29 docstring line.

After task 2 the narrow selection had exactly **one** failure —
`test_projected_tree_matches_committed_snapshot` — the expected pre-emit one that task 3 closes.

### Emit round-trip (task 3, D-03)

`git status --porcelain` immediately after the first emit, i.e. the check that sees `??`:

```
 M AGENTS.md
 M tools/harness_emit/emit-manifest.json
?? .claude/commands/docs-update.md
?? .claude/skills/docs-upkeep/
?? .opencode/command/docs-update.md
?? .opencode/skill/docs-upkeep/
```

Four untracked files that a bare `git diff` would have reported as clean — the 15-REVIEW CR-01
blind spot, observed live and not re-inherited. Every `??` was `git add`ed explicitly.

`CLAUDE.md` is correctly **unmodified**: its HARNESS-MANAGED fence carries prose only, while the
spliced command/skill lists live in `AGENTS.md:104-105`, which moved (`docs-update` into the
commands list, `docs-upkeep` into the skills list).

**Second-emit proof, run after the commit:**

```
$ uv run python -m tools.harness_emit && \
  git status --porcelain -- .opencode .claude opencode.json AGENTS.md CLAUDE.md \
    tools/harness_emit/emit-manifest.json
(empty)
```

Byte no-op. `git diff --exit-code -- .opencode .claude opencode.json AGENTS.md CLAUDE.md` also
exits 0.

## Gate results

| Gate | Result |
|---|---|
| `uv run pytest tools/harness_lint tools/harness_emit -q` | **363 passed**, 1 snapshot passed |
| `uv run pytest tools/harness_lint/tests/test_agents.py tools/harness_emit/tests/test_opencode_config.py -q` (model identifier) | **38 passed** |
| `uv run ruff check` / `format --check` on every file this plan authored | clean |
| `git diff --cached --check` (excluding the machine-generated `.ambr`) | clean |
| Second emit `git status --porcelain -- .opencode .claude` | empty |
| `harness/skills/gate-model/SKILL.md`, `harness/skills/brownfield-adoption/SKILL.md` | unmodified (`git status` empty for both) |
| `contracts/`, `docs/adr/`, `golden/`, `docs/.docs-review-ledger.toml` | unmodified |

## Deviations from Plan

**None affecting behavior.** Two notes:

1. **`CLAUDE.md` is in the plan's `files_modified` but was not modified.** Its fence carries no
   command/skill list, so the emitter had nothing to splice. This is the emitter's correct output,
   not a missed step — verified by re-running the emitter twice and getting no `CLAUDE.md` delta.

2. **Pre-existing `E501` in `tools/harness_emit/tests/test_coexist.py`** (the
   `test_gsd_owned_claude_files_untouched_and_unlisted` docstring, 101 chars) surfaced when linting
   a file this plan edits. Verified pre-existing by running ruff against the committed `HEAD`
   revision of that file. Out of scope per the scope boundary — logged to
   `deferred-items.md` in this phase directory, not fixed.

Separately, `git diff --cached --check` reports trailing whitespace inside the regenerated
`test_emit_determinism.ambr`. That is syrupy's own indentation of blank lines within a snapshot
block and is pre-existing in kind (931 such lines at `HEAD`, 980 after this plan's four new
artifacts). It is machine-generated content required for the snapshot to match; it is not
hand-authored byte hygiene.

## Known Stubs

None. Both authored files are complete surfaces, and both are wired to already-shipped code
(`tools.docs_guard.cli`, `tools.docs_guard.exclusions`).

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file-access pattern and no schema
change; `T-29-SC` holds (zero new dependencies).

## Self-Check: PASSED

All seven created files exist on disk; all three commits (`2aa3882`, `a3230da`, `1b0ede3`) are
present in `git log --oneline --all`.
