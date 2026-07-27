---
phase: 42-adoption-decoupling-install-set-repair
plan: 05
subsystem: adoption-lifecycle
tags: [harness-emit, docs, adopt, brownfield-adoption, cer-06, prod-01, phase-close]

# Dependency graph
requires:
  - "42-02 (approval-gate contract deleted, apply.py/cli.py prose finished)"
  - "42-03 (scan.py secret-pattern inline complete, no task-control read)"
  - "42-04 (install-set repaired, fixture-install test green)"
provides:
  - "harness/commands/adopt.md and harness/skills/brownfield-adoption/SKILL.md rewritten at
    source to describe the actual discover/draft/review/apply lifecycle, with no promote
    sub-verb and no human-gate section — re-emitted byte-identical into .claude/ and .opencode/"
  - "The full D-15 done-condition bundle run and recorded: all 9 checks green"
  - "REQUIREMENTS.md CER-06/PROD-01 self-consistent across the checkbox list and the
    traceability table"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Source-first, then emit: harness/** prose edited at source, python -m tools.harness_emit
      projects it into both runtime trees in the SAME commit (ordering rule 6) — never hand-edit
      .claude/** or .opencode/**"
    - "A prose edit to an emitted harness/** file also invalidates the committed
      test_emit_determinism.ambr snapshot; regenerate it with --snapshot-update in the same
      commit as the source edit (amend-if-red, D-12), not a follow-up commit"

key-files:
  created: []
  modified:
    - harness/commands/adopt.md
    - harness/skills/brownfield-adoption/SKILL.md
    - .claude/commands/adopt.md
    - .opencode/command/adopt.md
    - .claude/skills/brownfield-adoption/SKILL.md
    - .opencode/skill/brownfield-adoption/SKILL.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - .planning/REQUIREMENTS.md

key-decisions:
  - "The /adopt command's frontmatter description, title, and ## Notes closing sentence all
    dropped promote/human-gate language; the ### promote sub-verb section and the entire
    ## The human gate (refusal is the default) section (including its human-run example
    invocation) were deleted whole."
  - "brownfield-adoption/SKILL.md's five-stage runbook became four-stage
    (discover/draft/human-review/apply); ## Stage 4: promote was deleted whole and the old
    ## Stage 5: apply was renumbered to ## Stage 4: apply with no other prose change (its body
    already described apply_manifest correctly)."
  - "The ## Related bullet pointing at gate-model/SKILL.md was softened to describe the
    constitution-plane refusal apply performs, rather than naming a 'promotion stage' that no
    longer exists — the rest of the bullet's substance (gate-model as the general
    refuse-by-default pattern) remained accurate and was kept, per the interfaces block's
    instruction not to delete the whole ## Related section."
  - "REQUIREMENTS.md's traceability table rows for CER-06 and PROD-01 were changed from 'Not
    started' to 'Complete', matching the checkbox list (both already [x] from 42-03/42-04) —
    the premature-checkbox-vs-table mismatch the plan flagged is now resolved in the direction
    the evidence supports: both requirements are genuinely done as of this plan."

requirements-completed: [CER-06, PROD-01]

# Metrics
duration: ~50min
completed: 2026-07-28
---

# Phase 42 Plan 05: Harness Prose Rewrite + Full Done-Condition Bundle Summary

**Rewrote `/adopt` and `brownfield-adoption` at `harness/` source to drop the deleted promotion
lifecycle, re-emitted both runtime trees, then ran and recorded the phase's complete D-15
done-condition — all 9 checks green, closing CER-06 and PROD-01.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-07-28
- **Tasks:** 2/2
- **Files modified:** 8 (2 harness sources, 4 emitted projections, 1 test snapshot, 1
  requirements doc)

## Accomplishments

- Rewrote `harness/commands/adopt.md`: frontmatter `description:` and the title line dropped
  "promotion"/"promote"/"human-gated" language; deleted the `### promote` sub-verb section and
  the whole `## The human gate (refusal is the default)` section (including its human-run
  example); `## Notes` now points at the surviving discover/draft/apply flow and states review
  happens at the PR.
- Rewrote `harness/skills/brownfield-adoption/SKILL.md`: frontmatter `description:` and the body
  "five-stage" sentence became "four-stage"; deleted `## Stage 4: promote` whole; renumbered the
  old `## Stage 5: apply` to `## Stage 4: apply` unchanged otherwise; softened the `## Related`
  bullet referencing gate-model to not name a "promotion stage".
- Ran `python -m tools.harness_emit`, confirming exactly the 4 expected emitted files changed
  (`.claude/commands/adopt.md`, `.opencode/command/adopt.md`,
  `.claude/skills/brownfield-adoption/SKILL.md`, `.opencode/skill/brownfield-adoption/SKILL.md`)
  — byte-identical projection, no unexpected drift elsewhere in the 109-artifact emit.
  `EXPECTED_SKILLS`/`EXPECTED_COMMANDS` counts in `tools/harness_lint/caps.py` did not need to
  change (prose-only rewrite, no command/skill added or removed).
  Committed source + all 4 emitted files in one commit (`4f5510b`, ordering rule 6).
- Discovered the committed `test_emit_determinism.ambr` snapshot (syrupy) went RED after the
  prose edit (expected — it pins the exact rendered byte content of every emitted artifact).
  Regenerated it with `--snapshot-update` and amended it into the SAME commit rather than a
  follow-up commit, per D-12's amend-if-red discipline. Confirmed green afterward.
- Ran and recorded the full D-15 done-condition bundle (Task 2) — see "Done-Condition Evidence"
  below.
- Ran the full v2.5 REQUIREMENTS.md reconciliation directed by phase_critical_rules item 6: both
  CER-06 and PROD-01 were already checked `[x]` (from 42-03/42-04); the traceability table's
  "Not started" rows for both were the stale half — updated both to "Complete".
- Reported whole-phase LOC from `git diff --stat` across all five plans (D-17).

## Done-Condition Evidence (D-15, all 9 checks)

1. `uv run pytest -q` → **1315 passed**, exit 0.
2. `grep -rn "task_control" tools/adoption_apply/ tools/adoption_scan/` → no output, grep exit 1
   (nothing found). Note: `scan.py` retains two hyphenated `task-control` *comments* documenting
   provenance of the byte-identical-copied secret patterns (`contracts/harness/task-control/
   gate-registry.json`) — these do not match the underscored module-name grep and correctly
   describe a historical copy source, not a live read.
3. `grep -rn "GOLDEN_APPROVE_HUMAN" tools/adoption_apply/ tools/adoption_scan/` → no output, grep
   exit 1 (nothing found).
4. Scratch `draft → apply` cycle, `env -u GOLDEN_APPROVE_HUMAN` in front of both invocations,
   against a throwaway `git init` repo + a fresh synthetic target tree (mirroring
   `test_cli.py`'s `git_repo`/`synthetic_target`/`_write_state` fixtures, run via direct CLI
   `uv run python -m tools.adoption_apply draft|apply`, not the pytest harness): `draft` exit 0
   (wrote `inventory.json`/`plan.json`/`manifest.json`), `apply` exit 0
   (`applied=407 skipped=126 refused=35`), no promotion step in between. Separately confirmed
   `python -m tools.adoption_apply promote --help` now fails argparse (`invalid choice: 'promote'
   (choose from 'draft', 'apply')`) — the sub-verb no longer exists.
5. `uv run pytest tools/adoption_scan/tests/test_install_completeness.py -x -q` → **2 passed**.
6. `python -m tools.harness_emit && git status --porcelain` → empty (after the Task 1 commit).
7. Stale-derived check: `uv run python -m tools.docs_sync.generate` (12 reference pages
   regenerated) and `uv run python -m tools.memory_regen.contracts_index` (15 contracts indexed)
   both followed by `git status --porcelain` → empty both times — derived plane already current.
8. `uv run python -m tools.contract_drift.drift` → `contract-drift: OK — live manifest matches
   the committed baseline.`, exit 0.
9. Ruff ratchet (`.github/workflows/ci.yml`'s lint job invocation):
   `uv run python -m tools.ruff_baseline` → `ruff ratchet: 245 findings (baseline 245) — PASS:
   every rule class is at its baseline.`, exit 0.

No gate-fix amendment was needed beyond the snapshot regeneration folded into Task 1's commit —
every check in this list passed on first run.

## ROADMAP Phase-42 Success Criteria (all 6, with evidence)

1. `grep -rn "task_control" tools/adoption_apply/ tools/adoption_scan/` returns nothing — verified
   above (D-15 check 2).
2. `grep -rn "GOLDEN_APPROVE_HUMAN" tools/adoption_apply/ tools/adoption_scan/` returns nothing;
   full `draft → apply` completes with the variable unset — verified above (D-15 checks 3-4).
3. `scan.py` reads no file under `contracts/harness/task-control/`; its 8 secret patterns are
   owned locally alongside `SECRET_PATH_GLOBS` (landed in 42-03); secret-redaction tests pass
   unchanged — confirmed as part of the full-suite green in check 1 above (no test file for
   secret redaction was touched this plan).
4. `_CATEGORY_GLOBS` contains a `tools/**/*` entry (landed in 42-04) and the fixture-install test
   passes — verified above (D-15 check 5).
5. `uv run pytest -q` is green; `emit-drift`, `stale-derived`, `contract-drift`, ruff ratchet all
   clean — verified above (D-15 checks 1, 6, 7, 8, 9).
6. Net surface change adds no command, agent, skill, contract, hook, or dependency — this plan
   added zero new files (only edited 2 harness sources + their 4 emitted projections + 1 test
   snapshot); the phase's only new file across all 5 plans is
   `tools/adoption_scan/tests/test_install_completeness.py` (42-04), a test, not a
   command/agent/skill/contract/hook. `EXPECTED_SKILLS`/`EXPECTED_COMMANDS` counts in
   `tools/harness_lint/caps.py` are unchanged (confirmed by the emitter running clean with no
   count-guard failure).

## Task Commits

1. **Task 1: Rewrite adopt.md + brownfield-adoption SKILL.md at source, then re-emit** -
   `4f5510b` (docs) — source rewrite + 4 emitted-tree projections + the
   `test_emit_determinism.ambr` snapshot update, folded into one commit per D-12's
   amend-if-red discipline (the snapshot regeneration was discovered and amended in before the
   commit's final state, not left as a separate follow-up).
2. **Task 2: Full phase-gate verification** - no new commit (verification-only task; every check
   passed on first run, no gate-fix amendment needed).

**Plan metadata:** (this commit, immediately following, includes the REQUIREMENTS.md
reconciliation)

## Files Created/Modified

- `harness/commands/adopt.md` — promote sub-verb + human-gate section deleted; description/title/
  Notes updated to describe discover/draft/apply
- `harness/skills/brownfield-adoption/SKILL.md` — five-stage → four-stage; Stage 4: promote
  deleted; old Stage 5: apply renumbered to Stage 4; Related bullet softened
- `.claude/commands/adopt.md`, `.opencode/command/adopt.md`,
  `.claude/skills/brownfield-adoption/SKILL.md`, `.opencode/skill/brownfield-adoption/SKILL.md` —
  re-emitted, byte-identical projections of the two source edits
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — regenerated to match the
  new rendered content (syrupy snapshot, not a behavior change)
- `.planning/REQUIREMENTS.md` — CER-06/PROD-01 traceability table rows: "Not started" →
  "Complete"

## Decisions Made

- See frontmatter `key-decisions` for the four decisions made this plan (prose scope, Related
  bullet softening, REQUIREMENTS.md reconciliation direction).
- No Rule 4 (architectural) deviations encountered — this plan was a pure prose rewrite +
  verification sweep, exactly as scoped.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking issue] `test_emit_determinism.ambr` snapshot went RED after the prose
edit, blocking Task 1's own acceptance criterion (`uv run pytest tools/harness_emit
tools/harness_lint -q` green)**
- **Found during:** Task 1, running the acceptance-criteria pytest invocation immediately after
  the emit + first commit attempt
- **Issue:** The committed syrupy snapshot pins the exact rendered content of all 109 emitted
  artifacts; a legitimate content change to `adopt.md`/`brownfield-adoption/SKILL.md` is by
  construction also a change to that pinned content, so the snapshot test failed with the old
  frontmatter description still embedded in the expected value.
- **Fix:** Ran `uv run pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update
  -q`, reviewed the diff (confirmed it was exactly the two files' intended prose changes and
  nothing else), staged the updated `.ambr` file, and amended it into the same Task 1 commit
  (`git commit --amend --no-edit -- <full pathspec including the snapshot>`) rather than filing a
  separate commit — per D-12's amend-if-red ordering rule.
- **Files modified:** `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
- **Commit:** `4f5510b` (folded into Task 1's amended commit, not a separate hash)

No other deviations. No Rule 4 (architectural) issues; no auth gates; no checkpoints hit
(`autonomous: true`, no `type="checkpoint:*"` tasks in this plan).

## Issues Encountered

None beyond the snapshot-regeneration deviation above, which is the expected shape of a
harness-source prose edit (every prior phase's `harness/**` rewrite in this repo has needed the
same regeneration step).

## User Setup Required

None — no external service configuration required.

## Verification

- `grep -c "promote\|human gate\|five-stage" harness/commands/adopt.md
  harness/skills/brownfield-adoption/SKILL.md` → `0` for both files.
- `python -m tools.harness_emit && git status --porcelain` → empty (emit-drift clean).
- `uv run pytest tools/harness_emit tools/harness_lint -q` → 412 passed.
- Full D-15 done-condition bundle (9 checks) — see "Done-Condition Evidence" above, all green.
- All 6 ROADMAP Phase-42 success criteria — see section above, all satisfied with evidence.
- `test -f .claude/skills/adopt/SKILL.md` → confirmed absent, as the plan's read_first note
  anticipated (no such file exists to touch).

**Changed LOC, whole phase (D-17, from `git diff --stat 733db6f^..4f5510b`, i.e. the commit
immediately preceding Phase 42's first content commit through this plan's final commit):**
33 files changed, 907 insertions(+), 1383 deletions(-)

## Next Phase Readiness

- CER-06 and PROD-01 are both closed: adoption runs `draft → apply → PR review` with no
  `task_control` import, no `GOLDEN_APPROVE_HUMAN`, and the installed product ships the Python its
  own emitted commands/CI invoke, proven by a regression-guarding fixture-install test rather than
  a one-time manual check.
- `harness/commands/adopt.md` and `harness/skills/brownfield-adoption/SKILL.md` now describe
  exactly what the code does — no divergence between the harness's own documentation and its
  runtime behavior for either the `/adopt` command or the `brownfield-adoption` skill.
- Out of scope and left untouched per the plan's explicit boundary: `tools/task_control`,
  `gate-registry.json`, `secret_scan`, `deny-domains.*` all survive for Phases 43/44.
- No blockers for Phase 43 (Lifecycle Plane Removal) — this phase's work is fully independent of
  and does not pre-empt that deletion.

## Self-Check: PASSED

All claimed files and commit hashes verified present in the working tree and git history:
- `test -f harness/commands/adopt.md` → found
- `test -f harness/skills/brownfield-adoption/SKILL.md` → found
- `test -f .claude/commands/adopt.md` → found
- `test -f .opencode/command/adopt.md` → found
- `test -f .claude/skills/brownfield-adoption/SKILL.md` → found
- `test -f .opencode/skill/brownfield-adoption/SKILL.md` → found
- `test -f tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` → found
- `git log --oneline --all | grep -q 4f5510b` → found

---
*Phase: 42-adoption-decoupling-install-set-repair*
*Completed: 2026-07-28*
