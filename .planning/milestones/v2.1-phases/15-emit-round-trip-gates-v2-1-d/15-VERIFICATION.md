---
phase: 15-emit-round-trip-gates-v2-1-d
verified: 2026-07-15T18:39:30Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
---

# Phase 15: Emit Round-Trip + Gates Verification Report

**Phase Goal:** Every new/changed surface from this milestone (`/agree`, updated skills, the
updated `AGENTS.md` managed block) round-trips the Phase-7 emitter to both runtimes with no model
id — proving emit-drift clean, GEN-04 green, and counts/fixtures updated. This is the emit portion
of MEM2-06 (its ADR portion landed in Phase 12).

**Verified:** 2026-07-15T18:39:30Z
**Status:** passed
**Re-verification:** No — initial verification

All commands below were re-executed independently in this session against the live working tree
(not copy-pasted from SUMMARY.md). Every claim in 15-01-SUMMARY.md and 15-02-SUMMARY.md that could
be mechanically reproduced was reproduced and matched.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Both `.opencode/command/agree.md` and `.claude/commands/agree.md` exist and are tracked | ✓ VERIFIED | `git ls-files --error-unmatch` on both paths exits 0 (reproduced independently) |
| 2 | AGENTS.md HARNESS-MANAGED Commands index lists `agree` | ✓ VERIFIED | `grep -n "agree" AGENTS.md` line 104: `... add-language, adr, agree, build, checkpoint ...` |
| 3 | A fresh re-emit produces zero diff over the documented emit-drift path set | ✓ VERIFIED | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` → exit 0, reproduced independently |
| 4 | The projected-tree `.ambr` snapshot matches `harness/` source | ✓ VERIFIED | `uv run pytest tools/harness_emit/tests/test_emit_determinism.py::test_projected_tree_matches_committed_snapshot` → 1 passed |
| 5 | No model identifier appears anywhere in the emitted trees, bodies included | ✓ VERIFIED | Grepped all 84 `emit-manifest.json`-owned paths (not just the plan's narrower 4-path set) for `claude-*(opus\|sonnet\|haiku)`, `gpt-[0-9]`, `gemini-[0-9]`, `o1-`/`o3-mini` → 0 hits. Also confirmed every `provider/` value in scanned paths matches `provider/[a-z0-9-]*-tier` (only `explorer-tier` and `implementer-tier` present) |
| 6 | GEN-04 core→example independence stays green | ✓ VERIFIED | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` → 18 passed, run AFTER the `.ambr` regen (the hazard window) |
| 7 | Full non-example suite passes | ✓ VERIFIED | `uv run pytest -q` → 659 passed, 0 failed (reproduced independently, matches SUMMARY claim) |
| 8 | `test_coexist.py` module docstring states the correct count (20), matching its own assertion | ✓ VERIFIED | Line 3: "The emitter writes its 20 harness commands..."; `ls harness/commands/*.md \| wc -l` = 20; `test_all_20_commands_emit_to_both_trees` passes |

**Score:** 8/8 truths verified

### SC1 Wording Note (not a gap)

Roadmap/plan Success Criterion 1 names `EXPECTED_COMMANDS`. Confirmed independently:
`grep -rn "EXPECTED_COMMANDS" tools/ harness/ libs/` → 0 hits, exit 1. The symbol has never existed
anywhere in source. `test_commands.py`/`test_coexist.py` are glob-driven by design (no
commands-equivalent of `EXPECTED_PERSONAS`/`EXPECTED_SKILLS`/`EXPECTED_TEMPLATES` in `caps.py`, and
none should be added — that would add drift surface the glob design avoids). Per the phase's own
prior-milestone precedent (D-11), and consistent with instructions given for this verification, SC1
is treated as mis-worded prose, not an unmet criterion — its substance (fixtures/counts updated to
match the new source) is independently verified via truths 4 and 8 above.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.opencode/command/agree.md` | opencode projection of /agree | ✓ VERIFIED | exists, tracked, byte-matches a fresh emit |
| `.claude/commands/agree.md` | Claude projection of /agree | ✓ VERIFIED | exists, tracked, byte-matches a fresh emit |
| `tools/harness_emit/emit-manifest.json` | ownership manifest incl. both `agree.md` paths | ✓ VERIFIED | 84 paths total; both agree.md entries present |
| `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` | regenerated snapshot matching current source | ✓ VERIFIED | test passes independently |
| `tools/harness_emit/tests/test_coexist.py` | docstring corrected 19→20 | ✓ VERIFIED | line 3 confirmed |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `harness/commands/agree.md` | `.opencode/command/agree.md` + `.claude/commands/agree.md` | glob discovery (`iter_commands`) + `project_command` | ✓ WIRED | fresh re-emit reproduces byte-identical output, confirmed by clean diff |
| `harness/commands/agree.md` | `AGENTS.md` HARNESS-MANAGED block | `merge.splice_managed_block` | ✓ WIRED | `agree` present in sorted position in the Commands index line |
| `.ambr` snapshot | `test_core_no_example_dep.py` (_CORE_ROOTS scan) | git ls-files over tools/harness/libs | ✓ WIRED | GEN-04 passes post-regen; no domain-token leak |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|--------------|----------------|--------------|--------|----------|
| MEM2-06 | 15-01-PLAN.md, 15-02-PLAN.md | Emit round-trip portion: `/agree` + updated skills + `AGENTS.md` managed block projected to both runtimes, no model id, emit-drift clean, GEN-04 green | ✓ SATISFIED | REQUIREMENTS.md marks MEM2-06 → Phase 15 → "Complete"; all supporting truths above verified independently. No orphaned requirements — MEM2-06 is the only ID mapped to Phase 15 and both plans declare it. |

### Anti-Patterns Found

No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers found in the files modified by this phase
(emitted files are machine-generated derivatives; the one hand-edit, `test_coexist.py`, is a
single corrected docstring line with no debt markers).

### Code Review Findings (carried forward, judged against this phase's goal)

An independent code review (`15-REVIEW.md`, standard depth, 15 files) ran after execution and found:

- **CR-01 (Critical, review-rated):** The CI `emit-drift` job (`.github/workflows/ci.yml:197`)
  uses a bare `git diff --exit-code` over the documented path set, which is structurally blind to
  **new untracked files**. The reviewer proved by injection (adding then removing a probe file)
  that a newly-emitted, non-name-enumerated artifact (e.g. a skill reference file) can ship stale
  and the gate still passes. This is the same class of defect that let Phase 14's re-emit debt
  through undetected in the first place — it is not something Phase 15 introduced, and Phase 15
  correctly worked around it via ordering discipline (emit-then-commit before snapshot-regen,
  verified with `git status` non-empty checks) rather than by fixing the CI job itself, which is
  outside this phase's "change no code" scope and outside `tools/harness_emit/**.py`.
  **Independently confirmed:** reading `.github/workflows/ci.yml:180-197` shows the bare `git diff`
  and confirms `tools/harness_emit/emit-manifest.json` is not in the diffed path set even though it
  changed in this phase's own emit.
  **Judgment:** does not block Phase 15's stated goal — the roadmap SC ("the emit-drift gate is
  clean") is a point-in-time check on the *current* re-emit, which is genuinely clean, reproduced
  independently in this verification. It is a real, still-open **structural weakness of the gate
  itself**, not a defect in this phase's deliverable. **WARNING, not BLOCKER** — recommend a human
  decide whether to open a follow-up phase/ticket to apply the `stale-derived` job's `git add -A` +
  `git diff --cached` idiom to `emit-drift` (the reviewer's suggested fix is concrete and in the
  review report).
- **WR-01 (Warning):** `test_projected_tree_matches_committed_snapshot`'s name implies it detects
  stale committed trees; it only ever compares two source-derived renderings and never opens
  `.opencode/`/`.claude/`. Non-blocking naming/documentation issue; recommend a rename+docstring fix
  as follow-up.
- **WR-02 (Warning):** `/agree`'s body instructs "do not build shell strings from feedback" while
  interpolating `$ARGUMENTS` directly into a shell command — a pre-existing Phase-14 source
  decision, out of Phase 15's scope (no code/source changes permitted in this phase), but flagged by
  the reviewer per the plan's own contingency ("flag only if a reviewer raises it"). Recommend
  follow-up against `harness/commands/agree.md`.
- **IN-01, IN-02 (Info):** minor `/checkpoint` git-add redundancy and `session-inject.ts` silent
  error swallowing — both pre-existing, non-blocking, informational only.

None of these findings contradict or invalidate any of the 8 verified truths above; all describe
either pre-existing conditions this phase correctly did not touch, or forward-looking robustness
gaps in gates whose current-state cleanliness was independently re-verified in this report.

### Human Verification Required

None. All roadmap success criteria and plan must-haves are independently verifiable via
tests/greps/diffs, and were reproduced in this session rather than taken from SUMMARY.md. The
CR-01/WR-01/WR-02 findings above are code-review judgment calls, not runtime/visual/UX behaviors —
they are recorded as non-blocking WARNINGS for the developer to triage as a follow-up, not gates on
this phase's completion.

### Gaps Summary

No gaps. All 8 derived truths for MEM2-06's emit portion were independently verified against the
live repository state in this session:

- Both `agree.md` projections exist, are tracked, and are byte-identical to a fresh isolated emit.
- The `AGENTS.md` managed Commands index includes `agree`.
- The emit-drift replica (the exact CI command) exits 0 right now.
- The `.ambr` snapshot test passes.
- Zero model identifiers exist across all 84 manifest-owned emitted artifacts (a strictly wider
  scan than the plan's own 4-path grep, which — as 15-02-SUMMARY.md itself flagged — omitted
  `.claude/agents/`).
- GEN-04 passes after the regen (the highest-risk window for a domain-token leak).
- The full suite is 659 passed / 0 failed, up from the sanctioned baseline of 1 failed / 658 passed.
- `test_coexist.py`'s docstring and assertion agree at 20.

SC1's literal reference to a non-existent `EXPECTED_COMMANDS` symbol is recorded as mis-worded
prose rather than an unmet criterion, consistent with the milestone's established D-11 precedent
and this verification's own independent confirmation of zero hits for that symbol anywhere in
source.

The one Critical-rated code review finding (CR-01, emit-drift gate's blindness to untracked files)
is a genuine, still-open structural gap — but it predates this phase, was correctly navigated
(not silently ignored) via commit-ordering discipline, and does not falsify any of the 8 truths
that define this phase's goal. It is carried forward as a recommended follow-up, not a phase-15
gap.

---

_Verified: 2026-07-15T18:39:30Z_
_Verifier: Claude (gsd-verifier)_
