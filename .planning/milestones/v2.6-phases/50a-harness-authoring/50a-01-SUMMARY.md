---
phase: 50a-harness-authoring
plan: 01
subsystem: infra
tags: [harness, skills, emitter, pytest, contract-first]

# Dependency graph
requires:
  - phase: 49-command-integrity
    provides: stable 19-command surface (EXPECTED_COMMAND_NAMES) this plan cites without restating
provides:
  - "harness/skills/harness-author/SKILL.md — the absorbed, widened (skills+commands+agents)
    meta-authoring skill with grounded path:line defaults"
  - "tools/harness_lint/tests/test_harness_author.py — citation-integrity, dangling-reference, and
    reachability structural gates"
  - "tools/harness_lint/caps.py EXPECTED_SKILLS pinned to the new 8-name set (harness-author, not
    skill-creator)"
  - "regenerated tools/harness_emit/emit-manifest.json + both emitted trees + AGENTS.md's
    HARNESS-MANAGED block"
affects: [50b-managed-adopt, any future phase authoring a new skill/command/agent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Citation-integrity testing: a body-embedded backtick-quoted path[:anchor] citation is
      mechanically proven to resolve (numeric line/range or verbatim name-anchor), mirroring
      test_core_no_example_dep.py's git-ls-files-scoped scan + single-assert-joined-offenders idiom"
    - "Self-exempting dangling-reference scan: a guard module that documents the forbidden literal
      (docstrings, negative-control test) excludes its own file from the scan it runs, same as
      test_core_no_example_dep.py's _SELF pattern"

key-files:
  created:
    - tools/harness_lint/tests/test_harness_author.py
    - harness/skills/harness-author/SKILL.md
  modified:
    - tools/harness_lint/caps.py
    - harness/skills/brownfield-adoption/SKILL.md
    - tools/harness_emit/emit-manifest.json
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - .opencode/skill/harness-author/SKILL.md
    - .claude/skills/harness-author/SKILL.md
    - AGENTS.md
  deleted:
    - harness/skills/skill-creator/SKILL.md
    - .opencode/skill/skill-creator/SKILL.md
    - .claude/skills/skill-creator/SKILL.md

key-decisions:
  - "Task 3 (from the original plan) was pre-merged into Task 2's action text by the plan itself
    (plan-checker finding: an intermediate commit between absorption and re-emit is red by
    construction, since generate.py's check_skill_set raises before any write on a mismatched
    set) — executed as ONE task, ONE commit, per the plan's explicit instruction."
  - "caps.py's EXPECTED_SKILLS docstring addendum names the absorption by role ('the prior
    skills-only meta-authoring skill') rather than by the literal string 'skill-creator', because
    that docstring lives inside tools/, a scan root of this plan's own dangling-reference test —
    using the literal would make the gate flag its own fix."
  - "The harness-author SKILL.md frontmatter description also avoids the literal 'skill-creator'
    string for the same self-referential reason (caught during Task 2 verification, then fixed
    before commit)."

patterns-established:
  - "Grounded-default authoring skill: point at a caps/regex source by path:line or path::name
    instead of restating a cap number, so the citation (not a second copy) is what could go
    stale-detectably."

requirements-completed: [MONO-10, MONO-11]

# Metrics
duration: 12min
completed: 2026-07-30
---

# Phase 50a Plan 01: Harness Authoring Summary

**Absorbed `skill-creator` into a wider `harness-author` skill covering skills+commands+agents, with a new citation-integrity test proving every offered `path:line` default actually resolves in this checkout — skill count stays 8, command count stays 19, zero new packages/contracts.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-30T04:36:00Z (approx, first Read)
- **Completed:** 2026-07-30T04:48:59Z
- **Tasks:** 2 executed (Task 3 pre-merged into Task 2 per plan; not executed separately)
- **Files modified:** 14 (see `git show --stat` on the Task 2 commit)

## Accomplishments
- New `harness/skills/harness-author/SKILL.md` — generalizes `skill-creator`'s Step 0 anti-sprawl
  question to all three emitter-projected kinds (skills, commands, agents), with every offered
  default cited as a `path:line`/name anchor into `tools/harness_lint/caps.py`,
  `tools/harness_lint/tests/test_commands.py`, `harness/commands/component.md`,
  `harness/agents/curator.md`, and `harness/skills/context-budget/SKILL.md`.
- New `tools/harness_lint/tests/test_harness_author.py` — four tests: citation-integrity (every
  cited path/anchor resolves), no-dangling-reference (no tracked file outside `.planning/` still
  names `skill-creator`), a negative control proving that scan is live, and a reachability proof
  that everything `skill-creator` did (Step 0 question, name regex, dir-name rule,
  description-cap-by-reference, shared-caps sentence, verify command) survived the absorption.
- `skill-creator` deleted from `harness/skills/`, `caps.py`'s `EXPECTED_SKILLS`,
  `brownfield-adoption/SKILL.md`'s sibling enumeration and closing citation, and both emitted
  trees — in the SAME commit as `harness-author`'s creation, so skill count is never 9.
- Derived plane regenerated: `emit-manifest.json`, the `.opencode`/`.claude` emitted skill copies,
  `AGENTS.md`'s HARNESS-MANAGED skills line, and the `test_emit_determinism.ambr` snapshot.

## Task Commits

1. **Task 1: Write the new structural gate module (RED)** - `2eecaa0` (test)
2. **Task 2: Author harness-author, absorb skill-creator, regenerate the derived plane (ONE atomic
   task, ONE commit — includes the work of the plan's marked-skip Task 3)** - `99c4951` (feat)

Task 3 was marked `skip="merged-into-task-2"` in the plan and was not executed as a separate
task/commit, per the plan's explicit instruction (the plan-checker's finding that an intermediate
commit would be red by construction — `generate.py:361-362`'s `validate.check_skill_set` raises
before any write on a mismatched skill set).

## Files Created/Modified
- `tools/harness_lint/tests/test_harness_author.py` - citation-integrity, dangling-reference, and
  reachability structural gates (4 tests)
- `harness/skills/harness-author/SKILL.md` - the absorbed, widened meta-authoring skill
- `harness/skills/skill-creator/SKILL.md` - deleted
- `tools/harness_lint/caps.py` - `EXPECTED_SKILLS` swapped `skill-creator` → `harness-author`;
  docstring narration appended (phrased by role, not the literal name)
- `harness/skills/brownfield-adoption/SKILL.md` - sibling-skill enumeration and closing citation
  updated to `harness-author`
- `tools/harness_emit/emit-manifest.json` - regenerated (GENERATED file, never hand-edited)
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` - regenerated via
  `--snapshot-update`
- `.opencode/skill/harness-author/SKILL.md`, `.claude/skills/harness-author/SKILL.md` - emitted
  copies created by `python -m tools.harness_emit`
- `.opencode/skill/skill-creator/SKILL.md`, `.claude/skills/skill-creator/SKILL.md` - pruned by
  `manifest.prune_then_write`
- `AGENTS.md` - HARNESS-MANAGED skills line regenerated

## Decisions Made
- Task 3 pre-merged into Task 2 (plan-authored decision, not an executor deviation) — followed as
  written.
- Docstring addendum in `caps.py` and the new skill's own `description` frontmatter both avoid the
  literal substring `skill-creator`, phrasing the absorption by role instead — required because
  `caps.py` and `harness-author/SKILL.md` both live inside this task's own dangling-reference scan
  scope (`tools/`, `harness/`); using the literal name would make the new gate flag the very fix it
  exists to verify.

## Deviations from Plan

None — plan executed exactly as written (Task 3's skip was itself authored into the plan, not an
executor decision).

## Issues Encountered
- After `git rm harness/skills/skill-creator` and the emit-driven prune of the two emitted
  copies, the parent directories (`harness/skills/skill-creator/`, `.opencode/skill/skill-creator/`,
  `.claude/skills/skill-creator/`) were left as empty directories on disk (git does not track empty
  dirs). `tools/adoption_scan`'s real-repo scan tests (`test_scan_exclusions.py`,
  `test_plan_classification.py`, `test_dispositions.py`) walk the filesystem and `stat()` every
  candidate; an empty directory alone did not break them, but the STAGED-yet-uncommitted deletion
  of the emitted `SKILL.md` files (removed on disk, present in `git ls-files` until staged) did —
  `build_inventory` derives its candidate list from tracked paths and failed with
  `FileNotFoundError` until `git add` staged the deletions. Resolved by removing the leftover empty
  directories and staging every changed/deleted/created path before running the full suite; this
  is normal git-staging sequencing, not a code bug, and required no fix beyond staging order.
- `test_dispositions.py::test_catalog_invariant_to_untracked_local_state` compares the catalog from
  a fresh `git worktree` checked out at `HEAD` against the current working tree; it correctly failed
  while Task 2's changes were staged but not yet committed, and passed once the Task 2 commit
  landed. No action needed beyond committing in the plan's prescribed order.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `harness-author` is live, cited by, and citable from future skill/command/agent authoring; the
  citation-integrity gate (`test_harness_author.py`) generalizes as a reusable idiom for any future
  body-embedded-citation skill.
- No blockers for 50b (managed adopt) or subsequent phases; the emitted-tree/manifest/snapshot
  triad stays regenerable and idempotent.

---
*Phase: 50a-harness-authoring*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: tools/harness_lint/tests/test_harness_author.py
- FOUND: harness/skills/harness-author/SKILL.md
- FOUND: .planning/phases/50a-harness-authoring/50a-01-SUMMARY.md
- FOUND commit: 2eecaa0 (Task 1)
- FOUND commit: 99c4951 (Task 2, includes merged Task 3 work)
- CONFIRMED DELETED: harness/skills/skill-creator/SKILL.md
- Full suite: `uv run pytest -q` → 971 passed
- Emit idempotency: two consecutive `python -m tools.harness_emit` runs produced no further
  `git diff` in `.opencode .claude opencode.json AGENTS.md CLAUDE.md tools/harness_emit/emit-manifest.json`
- Structural counts: `git ls-files harness/skills/*/SKILL.md | wc -l` = 8;
  `test_command_count_is_stable` passed (19)
