---
phase: 36-discipline-skills-review-panel-v2-4-c
plan: 03
subsystem: authored harness surface + emit
tags: [LANE-01, LANE-02, skills, fan-out-reuse, emit-round-trip]
requires:
  - harness/disciplines.toml (36-01)
  - tools/discipline (36-01, 36-02)
  - harness/skills/fan-out-synthesize (Phase 10 substrate)
provides:
  - five discipline skills + /discipline, emitted to both runtimes
  - the policy <-> declaration <-> skill drift gate
affects: [36-04]
tech-stack:
  added: []
  patterns: [progressive-disclosure SKILL.md, references/ schema, both-direction drift gate]
key-files:
  created:
    - harness/skills/{clarify,test-driven-change,diagnose,domain-modeling,adversarial-review-panel}/SKILL.md
    - harness/skills/adversarial-review-panel/references/panel-seat.schema.json
    - harness/commands/discipline.md
    - tools/harness_lint/tests/test_discipline_wiring.py
  modified:
    - tools/harness_lint/caps.py
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - tools/harness_emit/emit-manifest.json
    - AGENTS.md (emitter-managed block)
    - .opencode/**, .claude/** (emitted)
decisions:
  - "The panel's min_experts and verdict vocabulary are data in harness/disciplines.toml and the skill points at them; a wiring test asserts the skill does NOT restate the number, so changing the requirement never means editing a skill."
  - "The wiring gate fails in both directions. The reverse direction (a declaration no lane requires) is what stops a dead procedure accumulating — the failure mode a one-way check would miss."
  - "The emit-determinism syrupy snapshot was updated with --snapshot-update. It is an emit-projection snapshot under tools/harness_emit/tests/__snapshots__, not a golden/ baseline, so it carries no human-approval gate."
metrics:
  tasks: 4
  commits: 1
  tests_added: 8
---

# Phase 36 Plan 03: Discipline Skills + Review Panel Summary

The method an agent follows to satisfy a lane's discipline now exists as authored, emitted surface,
and it cannot drift from the policy that requires it.

## What was built

| Skill | Routing trigger (disjoint by construction) |
|-------|--------------------------------------------|
| `clarify` | the requirements are ambiguous and you are about to build anyway |
| `test-driven-change` | you are about to write the code before the failing test |
| `diagnose` | something fails and the cause is not yet known |
| `domain-modeling` | the vocabulary is unsettled and a schema is about to harden |
| `adversarial-review-panel` | one reviewer's angle is not enough for this change |

Plus `harness/commands/discipline.md` — a thin macro over `uv run python -m tools.discipline` with
the 0/1/3 routing, which states explicitly that it never writes a record.

Each skill ends by naming exactly what its discipline record must contain, so the prose and
`tools/discipline/check.py` agree by construction rather than by hope. None restates a rule another
skill owns: `clarify` points at `gate-model` / `pipeline-map` / `context-budget`, `test-driven-change`
at `golden-testing` / `python-conventions`, `diagnose` at `golden-debug` for the seven
canonicalization axes, `domain-modeling` at `polyglot-boundary` / `two-plane-memory` /
`data-contracts`.

## LANE-02: reuse, not a second engine

`adversarial-review-panel` is an **application** of `fan-out-synthesize`:

- seats are dispatched via the runtime's own subtask affordance to the read-only `explorer` persona;
- returns are bounded by `references/panel-seat.schema.json` — `expert`, `frame`, `verdict`,
  citation-bearing `findings`, each with an optional `falsifier`;
- findings land in the packet's `evidence.json`, so an open blocker/major already refuses COMPLETE
  through machinery that shipped in v2.2. The panel grows **no** second enforcement path.

`test_the_panel_skill_reuses_the_fan_out_substrate` asserts the body names both the substrate and
the read-only persona; `test_the_panel_thresholds_are_data_not_prose` asserts `min_experts` lives in
the declaration and the skill points there.

`/review` is explicitly not superseded — it stays the single-seat entry point. The panel is the
thing a lane can *require*.

## The drift gate, both directions, both mutated

| Test | Direction |
|------|-----------|
| `test_every_required_discipline_is_declared` | a lane requiring an id nobody declared |
| `test_every_declaration_is_required_by_some_lane` | a declared procedure no lane owes |
| `test_every_declared_skill_exists_and_is_authored` | a declaration pointing at a missing SKILL.md |
| `test_an_undeclared_requirement_is_caught` | MUTATION on a copy |
| `test_a_declaration_naming_a_missing_skill_is_caught` | MUTATION on a copy |

**RED run recorded:** with `harness/skills/clarify/` moved out of the tree,
`test_every_declared_skill_exists_and_is_authored` fails with
`assert False + where False = PosixPath('…/harness/skills/clarify/SKILL.md').is_file` — 1 failed, 7
passed. The real files are never written by a test; the mutations operate on a `tmp_path` copy.

## Emit round-trip (verified, not assumed)

`uv run python -m tools.harness_emit` → **114 artifacts** to `.opencode/` + `.claude/` +
`opencode.json`. `EXPECTED_SKILLS` 13 → 18 and the command count 25 → 26 landed in the same commit
as the authored files.

Round-trip proof, using `git status --porcelain` (untracked-visible — bare `git diff` is blind to
new files, the 29 D-03 blind spot):

```
$ git commit … && uv run python -m tools.harness_emit >/dev/null && git status --porcelain
(no output)
```

The emitter also rewrote the `AGENTS.md` HARNESS-MANAGED block (both lists now carry the new
entries); committed as produced, not hand-edited.

## Deviations from Plan

### [Rule 2 — an unlisted artifact had to move] The emit-determinism snapshot

**Found during:** `uv run pytest tools/harness_lint tools/harness_emit -q`.
**Issue:** `test_projected_tree_matches_committed_snapshot` compares the whole projected tree against
a syrupy `.ambr`; six new emitted artifacts change it by construction.
**Fix:** `uv run pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update`. This is
an emit-projection snapshot under `tools/harness_emit/tests/__snapshots__/`, **not** a `golden/`
baseline — it carries no human-approval gate, and re-running the emitter reproduces it exactly.

## Verification

| Gate | Result |
|------|--------|
| `uv run pytest -q` | **1619 passed, 8 snapshots** (baseline 1543) |
| `uv run pytest tools/harness_lint -q` | 366 passed |
| `uv run python -m tools.harness_emit` then `git status --porcelain` | **empty** |
| `uv run python -m tools.ruff_baseline` | exit 0 |
| `uv run python -m tools.contract_drift.drift` | OK |

## Human-gated / carried

- None from this plan. No contract, ADR, golden or glossary byte moved; ledger untouched.
