---
phase: 15-emit-round-trip-gates-v2-1-d
plan: 01
subsystem: harness-emit
tags: [emit, derived-plane, gates, mem2-06]
requires:
  - harness/commands/agree.md (Phase 14, 104cecd)
  - Phase-13 body edits to orient/checkpoint/lint/two-plane-memory/session-inject
provides:
  - Committed .opencode/ + .claude/ trees carrying /agree and every Phase-13/14 body edit
  - AGENTS.md HARNESS-MANAGED command index listing agree
  - emit-manifest.json owning both agree.md paths
  - Projected-tree .ambr matching current harness/ source
affects:
  - CI core-suite (was RED -> green)
  - CI emit-drift (was RED -> green)
  - PR #3 ratification of ADR-0004/0005/0006/0007 (unblocked)
tech-stack:
  added: []
  patterns:
    - "Generator-owned derived plane: invoke the emitter, commit its output, hand-write nothing"
    - "Gate ordering as process control where no automated control exists"
key-files:
  created:
    - .opencode/command/agree.md
    - .claude/commands/agree.md
  modified:
    - .opencode/command/orient.md
    - .claude/commands/orient.md
    - .opencode/command/checkpoint.md
    - .claude/commands/checkpoint.md
    - .opencode/command/lint.md
    - .claude/commands/lint.md
    - .opencode/skill/two-plane-memory/SKILL.md
    - .claude/skills/two-plane-memory/SKILL.md
    - .opencode/plugin/session-inject.ts
    - AGENTS.md
    - tools/harness_emit/emit-manifest.json
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
decisions:
  - "Emitted and committed the trees BEFORE regenerating the .ambr — the ordering is the only control against gate theft (T-15-01)"
  - "Did NOT create EXPECTED_COMMANDS (0 source hits; D-11 precedent held for the third time)"
  - "Did NOT touch emitter code — glob discovery already covered /agree, proven by execution"
metrics:
  duration: 9min
  tasks: 2
  files: 14
  completed: 2026-07-16
---

# Phase 15 Plan 01: Emit Round-Trip Summary

Ran the Phase-7 emitter and committed exactly what it wrote, settling the accumulated
Phase-13/14 re-emit debt that redded both failing CI jobs on PR #3 — zero code changed.

## What Happened

Two commits, in mandatory order:

| # | SHA | What |
|---|-----|------|
| 1 | `0f39e6d` | `feat(15-01)` — the emit: 2 new files, 11 modified (13 paths staged) |
| 2 | `2da29e9` | `test(15-01)` — the `.ambr` regen (156 insertions / 17 deletions) |

`git log --oneline -2` confirms the emit precedes the regen. This ordering is the phase's
central control, not a stylistic preference — see Gate-Theft below.

## Measured Delta vs. Research Prediction

The research delta was a snapshot of the researcher's working tree (Assumption A2), so I
re-measured with `git status` after emitting rather than trusting the counts.

**The prediction was exact — zero divergence:**

| Predicted | Measured | Match |
|-----------|----------|-------|
| 2 new files | `.opencode/command/agree.md`, `.claude/commands/agree.md` | ✅ |
| 8 changed files | orient ×2, checkpoint ×2, lint ×2, two-plane-memory SKILL ×2, session-inject.ts = 9 | ✅ (see note) |
| 1 AGENTS.md line | `--numstat` = `1 1`, single hunk at line 104, inside the fence | ✅ |
| +2 manifest entries | both `agree.md` paths, nothing pruned (`grep -c agree` = 2) | ✅ |
| 1 `.ambr` | only `harness_emit`'s; other four untouched | ✅ |

*Note on "8 changed":* the research table lists 8 rows but its last row bundles
`session-inject.ts` alongside the skill pair, totalling **9** modified emitted files
(+ AGENTS.md + manifest = 11 modified, 13 staged). A presentation artifact of the table,
not a substantive divergence — every named file matched exactly. Emitter reported
**84 artifacts**, matching the researcher's isolated run.

### Explicitly-unchanged set — confirmed no-op

`opencode.json` and `.claude/settings.json` did **not** appear in `git status` after the
emit, and are absent from `git show --stat HEAD`. The emitter rewrites both to byte-identical
content, exactly as the research measured. No `.claude/agents/` or `.opencode/agent/` path
moved (GSD-owned `gsd-*.md` untouched — T-15-06 control intact). `uv.lock` diff is empty.

## The Gate-Theft Trap — how it was avoided

I read `test_emit_determinism.py:63-79` and confirmed firsthand that it renders from
`_AGENTS_DIR`/`_COMMANDS_DIR`/`_SKILLS_DIR` (`harness/` source) and never opens the committed
trees. So `--snapshot-update` alone would have reported `0 failed / 659 passed` over trees
still missing `/agree` — a fully green suite on a broken repo.

Guarded by evidence, not intent:

- Emitted first; asserted `git status` was non-empty (13 paths).
- After the emit commit, verified `test_projected_tree_matches_committed_snapshot` **still
  FAILED** — positive proof the snapshot had not been touched early.
- Verified via the CI replica (`re-emit && git diff --exit-code`), never via a green pytest.

## Verification

| Check | Result |
|-------|--------|
| Emit-drift replica over the 8-path set | **exit 0 — clean** |
| `git ls-files --error-unmatch` both `agree.md` | tracked |
| Full suite | **0 failed / 659 passed** (from 1 failed / 658) |
| GEN-04 (`test_core_no_example_dep.py`), run *after* regen | 18 passed |
| `test_all_20_commands_emit_to_both_trees` | passed |
| `EXPECTED_COMMANDS` in `tools/`+`harness/`+`libs/` | 0 hits (not invented) |
| Emitter `.py` files changed | 0 |

## Deviations from Plan

### Observations, not fixes — two plan acceptance criteria are mis-specified

Both are flaws in the *criteria*, not the work. No code or emitted byte was changed in response.

**1. The AGENTS.md line-count grep cannot ever return 2.** The criterion specifies
`git diff HEAD~1 HEAD -- AGENTS.md | grep -c '^[+-][^+-]'` equals 2. The changed line is a
**markdown list item**, so it renders as `+- **Commands** ...` — the second character is `-`,
which `[^+-]` excludes. It returns **0** regardless of correctness. Verified the substance
instead via `git diff --numstat` (`1 1`) and `git diff -U0` (single hunk `@@ -104 +104 @@`,
inside the 98–107 fence). The splice is correct: exactly one line, `agree` in sorted position,
nothing outside the fence moved.

**2. The snapshot blast-radius pathspec silently matches nothing.** The criterion uses
`git status --porcelain -- 'tools/**/__snapshots__'`. Git pathspec `*` does not cross `/`, so
this returns empty whether or not a snapshot moved — a check that always "passes". Re-verified
with an explicit `git ls-files '*.ambr'` path list: only `test_emit_determinism.ambr` modified,
the `docs_sync` and three `memory_regen` fixtures untouched. Scope held.

Neither warranted a fix under the zero-code constraint; both are recorded for Plan 02.

### Not done, deliberately

- **`EXPECTED_COMMANDS` not created** — 0 source hits; SC1's wording names a symbol that has
  never existed. D-11 precedent held (third occurrence this milestone).
- **`test_coexist.py:3` module docstring still says "19"** — the research flagged it as a
  cosmetic one-liner (A4). Left alone: it is a source-file edit in a phase whose defining
  constraint is "change no code", and no gate reads it. Deferred to Plan 02.

## Downstream Impact

Both PR #3 red jobs (`core-suite`, `emit-drift`) were this single inherited re-emit debt and
are now settled locally. `gate.needs` lists both, so this unblocks ratification of
**ADR-0004 / 0005 / 0006 / 0007** — the phase's real payoff.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern, or schema change. Every file
touched is machine-generated by the existing emitter; T-15-05 (plugin byte-copy) and T-15-06
(GSD-owned files) controls verified intact.

## Known Stubs

None.

## Self-Check: PASSED

- `.opencode/command/agree.md` — FOUND, tracked
- `.claude/commands/agree.md` — FOUND, tracked
- `tools/harness_emit/emit-manifest.json` — FOUND, contains `.opencode/command/agree.md`
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — FOUND, regenerated
- Commit `0f39e6d` — FOUND
- Commit `2da29e9` — FOUND, strictly later than `0f39e6d`
