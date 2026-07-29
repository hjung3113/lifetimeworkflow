---
phase: 45-projection-repair
plan: 03
subsystem: harness-emitted-surface
tags: [constitution-plane, harness-emit, projection, codeowners, gen-04, syrupy]
requires:
  - "45-01's three-member CONSTITUTION_GLOBS (contracts/**, docs/adr/**, docs/glossary.md)"
  - "45-01's GEN-04-constrained wording: 'the instance-scoped golden CODEOWNERS route'"
provides:
  - "nine harness/ sources whose plane-membership and route claims match the enforced guard"
  - "both runtime trees byte-consistent with harness/ after the correction"
  - "a regenerated projection snapshot pinning the corrected trees"
affects:
  - ".claude/{agents,commands,skills}/** (emitted)"
  - ".opencode/{agent,command,skill}/** (emitted)"
  - "tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr"
tech-stack:
  added: []
  patterns: ["source-first emit (D-18)", "mechanical token grep over eye-graded review"]
key-files:
  created:
    - .planning/phases/45-projection-repair/45-03-SUMMARY.md
  modified:
    - harness/agents/code-reviewer.md
    - harness/agents/curator.md
    - harness/agents/python-engineer.md
    - harness/commands/adopt.md
    - harness/commands/refresh-memory.md
    - harness/skills/brownfield-adoption/SKILL.md
    - harness/skills/data-contracts/SKILL.md
    - harness/skills/python-conventions/SKILL.md
    - harness/skills/two-plane-memory/SKILL.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
decisions:
  - "membership lists were SUBSTITUTED not truncated: `golden/` -> `docs/glossary.md`, keeping every list at three members (D-02)"
  - "the two GEN-04-constrained sites were phrased in words with no `examples/` token (D-06, T-45-11)"
  - "source + 18 emitted twins + .ambr committed as ONE commit so no window ends red (D-18/D-19)"
metrics:
  commits: 1
  tests_before: 876
  tests_after: 876
  completed: 2026-07-29
---

# Phase 45 Plan 03: Emitted-Surface Projection Repair Summary

Corrected all nine `harness/` artifacts that declared a four-member constitution plane or pointed at
the deleted `/golden/` CODEOWNERS route, re-projected both runtime trees and regenerated the syrupy
projection snapshot — one commit of 28 paths, ending at 876 passed / 7 snapshots.

## What Changed

### Commit `258148e` (28 paths)
`fix(45-03): state the three-member constitution plane in every emitted artifact`

```
 .claude/**   (9 files)
 .opencode/** (9 files)
 harness/**   (9 files)
 tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr | 31 ++++++-----------
 28 files changed, 49 insertions(+), 45 deletions(-)
```

### The seven membership claims (substitution, not truncation)

Every list is still three members: `golden/` was **replaced by** `docs/glossary.md`, matching
`contract_guard.CONSTITUTION_GLOBS == ["contracts/**", "docs/adr/**", "docs/glossary.md"]`. Dropping
the member outright would have left two-member lists and failed the plan's own must-have ("states
three members").

| Source | Line | New text |
|--------|------|----------|
| `harness/agents/code-reviewer.md` | 33 | ``(`contracts/`, `docs/adr/`, `docs/glossary.md`).`` |
| `harness/agents/curator.md` | 39-40 | same list inside the out-of-bounds bullet |
| `harness/commands/adopt.md` | 40 | ``(`contracts/` · `docs/adr/` · `docs/glossary.md`)`` — behavioral claim, now true of `adoption_apply` |
| `harness/commands/refresh-memory.md` | 41 | ``(`contracts/`, `docs/adr/`, `docs/glossary.md`) or `.memory/state/`.`` |
| `harness/skills/brownfield-adoption/SKILL.md` | 52 | same behavioral claim as adopt.md |
| `harness/skills/python-conventions/SKILL.md` | 44 | the **ninth source** — Non-negotiables block, reflowed to keep the line width |
| `harness/skills/two-plane-memory/SKILL.md` | 17 | ``**What:** `contracts/**`, `docs/adr/**`, `docs/glossary.md`, plus the language-neutral spec …`` |

### The two GEN-04-constrained rewrites

`harness/agents/python-engineer.md:29` — reuses plan 01's recorded wording verbatim:

> …never self-bless a golden; promotion is human review at the PR (**the instance-scoped golden
> CODEOWNERS route**).

`harness/skills/data-contracts/SKILL.md:34` — rewritten so the sibling relationship is
instance-scoped, carrying neither an `examples/` token nor the backticked `` `golden/` `` signature,
while keeping the point it was making:

> - The golden baseline directory is a **separate top-level sibling** within the instance overlay that
>   owns it — never nested under a `contracts/` tree.

## Surviving-by-design `golden` mentions (deliberately NOT touched)

These name the golden **concept** or the still-live **instance gate**, both of which exist, so by D-06
they are not stale. None carries the backticked `` `golden/` `` / `` `golden/**` `` token, which is why
the mechanical verify can be exact:

`harness/agents/code-reviewer.md:32`, `harness/agents/curator.md:6,39`,
`harness/agents/orchestrator.md:69`, `harness/agents/python-engineer.md:6,29`,
`harness/commands/build.md:3`, `harness/commands/contract-check.md:18,33,42`,
`harness/commands/orient.md:32,36`, `harness/commands/review.md:32`, `harness/commands/test.md:5`,
`harness/skills/data-contracts/SKILL.md:7,34,48`, `harness/skills/two-plane-memory/SKILL.md:22,59`,
`harness/skills/polyglot-boundary/SKILL.md` + its `references/canonicalization-table.md`.

Also untouched by instruction: `harness/agents/templates/**` (not in `emit-manifest.json`, plan 06
owns it). Its two live `` `golden/` `` CODEOWNERS-entry tokens survive at
`templates/component-engineer.md:46` and `templates/engineer.md:39` — outside this plan's grep scope
and outside its ownership. Also untouched: the `libs/python/AGENTS.md` pointer line in
`python-conventions/SKILL.md`, per the plan's explicit instruction.

## Verification Results

| Check | Expected | Observed |
|-------|----------|----------|
| task 1 · `git status --porcelain \| grep -c '^ M harness/'` | 9 | 9 |
| task 1 · runtime-tree modifications before emit | 0 | 0 |
| task 1 · backticked-token grep over `harness/{agents,commands,skills}` minus templates | no output | no output (exit 1) |
| task 1 · GEN-04 guard + `test_cross_repo_authority.py` | green | **22 passed** |
| task 1 · concept survives (`golden-testing` / `contract-check.md`) | non-empty | non-empty (see finding 1) |
| task 2 · emit → porcelain | exactly 27 (9 src + 18 twins), no collateral | exactly 27, no collateral |
| task 2 · suite before snapshot regen | 1 measured failure | `1 failed, 875 passed` — only `test_projected_tree_matches_committed_snapshot` |
| task 2 · `--snapshot-update` | 1 snapshot updated | 1 snapshot updated, 4 passed |
| **post-commit · `uv run pytest -q`** | **876 passed, 7 snapshots** | **876 passed, 7 snapshots** |
| post-commit · second `harness_emit` → porcelain | empty | empty (idempotence / emit-drift proof, CER-10) |
| post-commit · `contract_hash.hash` + `docs_sync.generate` + `memory_regen.contracts_index` → porcelain | empty | empty |
| post-commit · backticked-token grep over `.claude` + `.opencode` | no output | no output (exit 1) |
| post-commit · commit path count | 28 | 28 |
| post-commit · `uv run pytest examples/log-parser -q` | 31 passed | 31 passed |
| `uv run python -m tools.ruff_baseline` | PASS | PASS (74 vs baseline 84; **not** `--update`ed) |

Emitted twins confirmed carrying the three-member list: 14 `docs/glossary.md` hits across
`.claude` + `.opencode` (7 sources × 2 trees), plus the 2 python-engineer route lines and the 2
data-contracts sibling lines = all 9 sources × 2 trees projected.

## Deviations from Plan

**None.** No Rule 1/2/3 auto-fix was needed; no Rule 4 architectural decision arose. The one
line-reflow (`python-conventions/SKILL.md:44-45`, so the substituted longer member kept the file's
wrap width) is a formatting consequence of the instructed edit, not a deviation — it changes no
wording and no front-matter field.

No front-matter `name` / `description` / `mode` / `tools` field was touched; `caps.py` stayed silent
and the emitter wrote all 69 artifacts with only the 18 expected twins changing.

## Criteria That Did Not Hold Literally

**1. `harness/skills/golden-testing/` and `harness/skills/golden-debug/` do not exist.** The plan's
DO-NOT-TOUCH list names both, and task 1's fifth verify leg passes the first as a pathspec:
`git grep -l 'golden' -- harness/skills/golden-testing harness/commands/contract-check.md`. The
observed `harness/skills/` contents are: `brownfield-adoption`, `context-budget`, `data-contracts`,
`fan-out-synthesize`, `polyglot-boundary`, `python-conventions`, `skill-creator`, `two-plane-memory`.
The verify's stated expectation ("non-empty") **still holds** — `contract-check.md` matches — and
the substantive criterion (golden-as-a-concept survives) holds across the fourteen surviving
mentions listed above. Nothing was adjusted: the two named directories are simply not present to
touch. Flagged so plan 06 can correct the expectation text rather than the tree.

**2. The DO-NOT-TOUCH line reference `data-contracts/SKILL.md:47` is now `:48`**, because the
instructed rewrite of `:34` grew from one line to two. The line's content is untouched.

## Anything the Plan Did Not Anticipate

Nothing material. All five pre-briefed measurements reproduced exactly: the GEN-04 phrasing rule was
required (the guard scans `harness/`, 22 tests green after the word-form repoint); the ninth source
was real and emitted; the two behavioral claims are now true of `adoption_apply`; one
`--snapshot-update` closed the single expected syrupy failure and the second emit was byte-empty;
the count stayed 876 / instance 31.

One nuance worth recording for plan 06: the membership fix is a **substitution**, not a deletion.
The plan's action text reads "drop `golden/` … leaving `contracts/`, `docs/adr/` and
`docs/glossary.md`", but six of the seven lists never contained `docs/glossary.md` — so satisfying
the must-have ("states three members") required writing it in. The resulting lists are now exact
duplicates of `contract_guard.CONSTITUTION_GLOBS`, which is the stronger property.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or trust-boundary schema. T-45-08
through T-45-11 are all discharged: the sweep is verified by mechanical grep, no runtime-tree file
was hand-edited (the emitter wrote all 18), no front-matter field moved, and no `examples/` token
entered `harness/`.

## Self-Check: PASSED

- `.planning/phases/45-projection-repair/45-03-SUMMARY.md` — FOUND
- commit `258148e` — FOUND
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — FOUND (modified in `258148e`)
