---
phase: 43-lifecycle-plane-removal
plan: 04
wave: 3
subsystem: lifecycle-plane
tags: [deletion, lifecycle-plane, CER-07, harness-emit, ci]
requires: ["43-03"]
provides:
  - "The 8 mutually-referential lifecycle tools/ packages (7021 LOC) deleted as one unit (D-04)"
  - "resume_gate hook source + resume-gate plugin source deleted; emitted plugin and manifest row pruned"
  - "4 task-control commands, 5 discipline skills, 3 harness/*.toml declarations, .workflow/tasks/ gone"
  - "CI lifecycle-eval job and its jobs.gate.needs entry removed together (SIM-1/SIM-2)"
  - "Both runtime trees re-emitted; full suite green at 982 passed"
affects:
  - "tools/harness_lint/caps.py"
  - "tools/adoption_scan/destinations.py"
  - ".github/workflows/ci.yml"
tech-stack:
  added: []
  patterns:
    - "repair-the-invalidated-test-in-the-same-commit-as-the-deletion (Phases 41/42 precedent)"
    - "emit-snapshot rule (W-4): harness/commands|skills edit regenerates the .ambr in-commit"
    - "pathspec-scoped cleanliness checks under expected uv.lock dirt (W-9)"
key-files:
  created:
    - .planning/phases/43-lifecycle-plane-removal/43-04-SUMMARY.md
  modified:
    - tools/harness_lint/caps.py
    - tools/harness_lint/tests/test_tests_are_isolatable.py
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - tools/adoption_scan/tests/test_install_completeness.py
    - tools/adoption_scan/destinations.py
    - .github/workflows/ci.yml
    - AGENTS.md
    - tools/harness_emit/emit-manifest.json
decisions: []
metrics:
  duration: "~12 min"
  completed: 2026-07-28
  tests: "982 passed, 7 snapshots"
  commits: 2
---

# Phase 43 Plan 04: Lifecycle Plane Runtime-Surface Deletion Summary

Deleted the lifecycle plane's entire runtime surface as one unit — 8 mutually-referential `tools/`
packages plus the hook, plugin, 4 commands, 5 skills, 3 `harness/*.toml` declarations,
`.workflow/tasks/` and the CI `lifecycle-eval` job — refreshing every live-tree artifact the
deletion invalidated inside the same commit, then re-emitting both runtime trees.

## Commits

| Hash | Message |
|---|---|
| `dff6675` | `feat(43-04): delete the lifecycle plane's runtime surface (CER-07)` |
| `1fee674` | `chore(43-04): re-emit both runtime trees after the lifecycle-plane removal` |

### Measured `git diff --stat` totals for the deletion commit (`dff6675`)

```
86 files changed, 20 insertions(+), 9438 deletions(-)
```

By status: **79 `D`, 7 `M`** — the 7 modified being `.github/workflows/ci.yml`,
`tools/harness_lint/caps.py`, `tools/harness_lint/tests/test_tests_are_isolatable.py`,
`tools/harness_emit/tests/test_coexist.py`,
`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`,
`tools/adoption_scan/tests/test_install_completeness.py` and
`tools/adoption_scan/destinations.py`.

## What Was Done

### Task 1 — `dff6675`, executed in the plan's mandated order

**Step 0 (SIM-1/SIM-2), before the module-count pre-check.** Deleted the `ci.yml` `lifecycle-eval`
job block (`:221-235` plus its 4 banner lines and the separating blank line) **and** its
`jobs.gate.needs` entry (`:345`) together. YAML-resolved verification exited 0 with `needs` at
exactly 10 entries and no `lifecycle-eval` job. Doing this first is what kept
`tools.lifecycle_eval.runner` from becoming an unresolvable module ref.

**Deletions.** `git rm -r` over the 8 packages, `tools/hooks/resume_gate.py`,
`harness/plugins/resume-gate.ts`, the 4 commands, the 5 skill directories, the 3 `.toml`
declarations, `.workflow/tasks`, and the two wiring tests (`test_capability_wiring.py`,
`test_discipline_wiring.py`) — ordering rule 8.

**Steps 1-5, the invalidated-artifact repairs, all in-commit:**

1. `caps.py` — dropped the 5 discipline-skill entries from `EXPECTED_SKILLS` (12 remain) and
   rewrote the comment block above it that named the three now-deleted `.toml` files and
   `test_discipline_wiring.py`.
2. `test_tests_are_isolatable.py` — narrowed the code tuple at `:125` to
   `("tools/harness_lint/tests",)`. Module docstring and the `:108` hint string left alone per
   `<surviving_residue>`.
3. `test_coexist.py` — renamed to `test_all_21_commands_emit_to_both_trees`, both `25` literals and
   both f-strings to `21`, Phase-43 line appended to the docstring history. `_SEED_SETTINGS` and the
   structural tests untouched.
4. `test_install_completeness.py` — floor `>= 20` → `>= 12`, function renamed to
   `test_discovers_at_least_twelve_modules`, f-string and docstring rationale updated.
5. `destinations.py` — removed the single `"harness/risk-policy.toml"` glob (W-3).

**Step 6 (W-4).** Regenerated `test_emit_determinism.ambr` via `--snapshot-update`, then re-ran
without the flag: 4 passed, 1 snapshot passed.

### The B-2 pre-check landed on **13**, exactly as the plan predicted

The mandated pre-check was red with a "found 13" message, and the surviving package list matched the
plan's `<interfaces>` table verbatim:

```
AssertionError: expected at least 20 distinct top-level tools packages, found 13:
['adoption_apply', 'adoption_scan', 'agree', 'contract_drift', 'contract_hash', 'docs_sync',
 'golden_runner', 'harness_emit', 'harness_lint', 'memory_regen', 'polyglot_lint',
 'ruff_baseline', 'strangler_guard']
```

The sibling `test_every_referenced_tools_module_lands_in_applied_target` was green at that same
point — confirming step 0 had done its job. This is the SIM-1 failure class the CI-job move exists
to prevent, and it did not occur.

### Task 2 — `1fee674`

Emitter run (`88 artifacts`) propagated the deletions into both trees, pruned
`.opencode/plugin/resume-gate.ts` and its manifest row, and refreshed `AGENTS.md`'s managed index.
No emitted path or manifest row was hand-edited. A second emitter run produced an empty
`git diff --stat` — idempotent.

## Deviations from Plan

**1. [Rule 3 — Blocking] Removed leftover `__pycache__` bytecode directories under the 8 deleted packages.**

- **Found during:** Task 1, immediately after `git rm -r`.
- **Issue:** `git rm -r` removes tracked files only. Each of the 8 package directories survived on
  disk holding nothing but untracked, gitignored `.pyc` files, so the plan's own acceptance
  criterion `test ! -d tools/<name>` would have failed for all 8.
- **Verification before acting:** measured `0` non-`.pyc` files and `0` git-tracked paths beneath
  the 8 directories, then removed exactly those 8 paths with a targeted `rm -rf`. No `git clean`,
  no blanket reset.
- **Fix:** `rm -rf` scoped to the 8 named directories. All 8 then satisfied `test ! -d`.

**2. [Rule 3 — Blocking] Removed 10 empty emitted skill directories after the re-emit.**

- **Found during:** Task 2, after `tools.harness_emit`.
- **Issue:** the emitter deleted the tracked `SKILL.md`/`references/*` files but git does not track
  directories, leaving `.opencode/skill/<name>/` and `.claude/skills/<name>/` as empty shells for
  all 5 deleted skills.
- **Verification before acting:** confirmed `files=0` under each of the 10 paths.
- **Fix:** `rmdir` on the 10 empty paths. Both trees then read exactly 12 skills, matching
  `EXPECTED_SKILLS`.

**3. [Rule 1 — Bug] One extra `twenty` cross-reference in `test_install_completeness.py`.**

- **Found during:** Task 1 step 4, verifying the B-2 criterion.
- **Issue:** `:117` carried a comment reading
  `# non-vacuous, backstopped by test_discovers_at_least_twenty_modules above` — a stale reference to
  the function I had just renamed. The plan's acceptance criterion
  `grep -n ">= 20\|at least 20\|twenty"` requires **no output**, so this single line would have
  failed the criterion.
- **Fix:** updated the comment to name `test_discovers_at_least_twelve_modules`. This is within the
  plan's stated artifact intent ("its name/message no longer claiming 'twenty'") — the plan simply
  did not enumerate this third site.

## Expected Reds That Occurred, As Documented

**Pitfall 4 / D-12 — `test_catalog_invariant_to_untracked_local_state` red between `git rm` and
`git commit`.** The plan's step-7 pre-staging bundle instructed "confirm all green BEFORE
staging". It came back `1 failed, 39 passed`, the failure being this test, which spawns a
`git worktree ... HEAD` and compares that clean checkout's catalog against the working tree's.
With the deletions staged but HEAD still at `548421d`, the two sets differed by exactly the 49
deleted catalog rows (`Left contains 49 more items, first extra item:
'tools/lifecycle_eval/fixtures/negative-fixtures.json'`).

This is precisely the intra-commit red the plan documents in `<objective>` and the threat model's
first trust boundary — structurally impossible to clear before the commit lands. I did **not**
improvise a repair. After committing, the same bundle ran **34 passed**.

**W-9 — ` M uv.lock`.** Appeared the instant the deletion landed and remains uncommitted, as
designed. It was never staged, never added to either pathspec, and every cleanliness check in this
plan was run pathspec-scoped. It is 43-05 Task 2's to commit.

## Acceptance Criteria

Every criterion in both tasks held. Selected measurements:

| Criterion | Result |
|---|---|
| 8 × `test ! -d tools/<pkg>`, `test ! -e .workflow/tasks` | all pass |
| `caps.py` skill grep / hyphenated-toml grep | both empty |
| `test_coexist.py`: no `== 25`/`test_all_26`; `grep -c "== 21"` | empty; `2` |
| BLOCKER-2 `grep -c '"tools/lifecycle_eval/tests"'` | `0` |
| B-2: no `>= 20`/`twenty`; `grep -c ">= 12"` | empty; `1` |
| SIM-1 YAML resolve: `needs` len 10, no `lifecycle-eval` job | exit 0 |
| SIM-1 `test_install_completeness.py` (both tests) | 3 passed |
| SIM-2 `test_ci_lint_gate.py` | **6 passed** — matches the simulation exactly |
| W-3 `grep -n "risk-policy" destinations.py` | empty |
| W-4 `.ambr` deleted-package grep | `0` |
| W-7 forms 1, 2, 3 + product-surface grep | all exit 1 (empty) |
| Idempotent re-emit diff | empty |
| `.opencode/plugin/resume-gate.ts`; manifest `resume-gate.ts` count | pruned; `0` |
| **`uv run pytest -q`** | **982 passed, 7 snapshots, exit 0** |

Test count moved 1313 → 982; the 331-test delta is the deleted packages' own suites plus the two
wiring tests.

## Things The Plan Did Not Anticipate

1. **`git rm -r` and the emitter both leave directory shells behind.** The plan's directory-absence
   criteria (`test ! -d tools/<name>`, and implicitly the emitted skill dirs) cannot be met by
   `git rm`/emit alone whenever untracked bytecode or empty dirs remain. Both deviations above are
   this same gap. Worth encoding as a standing post-deletion step for future removal phases.

2. **`<interfaces>` parenthetical "19 conftest.py files use the idiom" measures 17.** The
   confirmation aid for BLOCKER-2 says `grep -l sys.path.insert tools/*/tests/conftest.py` yields 19
   post-deletion; the live measurement is **17**. The number conflates two distinct counts: there are
   indeed **19** surviving `tools/*/tests` directories — which is the load-bearing figure, since
   `test_the_scan_finds_the_members_it_claims_to` asserts `len(found) >= 10` against
   `_members_with_tests()` — but only 17 of them carry a `conftest.py`. `tools/contract_drift/tests`
   and `tools/contract_hash/tests` have none, using the alternative idiom the file's own docstring
   at `:33` describes. All 17 that exist do use `sys.path.insert`, and
   `tools/harness_lint/tests/conftest.py` (`:22`) remains a live example of the pattern, so the
   substantive confirmation the plan asked for holds.

   **No criterion was adjusted and no code was changed for this** — it is a prose slip in a
   non-criterion note, and the assertion it backstops was never at risk (19 ≫ 10).

3. **`<success_criteria>` carries a stale "14".** It reads "its pre-check reconciled against the
   measured 14", contradicting the `<interfaces>` table, the `<must_haves>` B-2 entry and the Task 1
   action text, which all say **13** post-SIM-1. The measured value was 13. This is a leftover from
   the pre-SIM-1 revision that the corrected sections fixed but this one sentence did not.

## Self-Check: PASSED

- `.planning/phases/43-lifecycle-plane-removal/43-04-SUMMARY.md` — FOUND
- Commit `dff6675` — FOUND
- Commit `1fee674` — FOUND
- `.planning/STATE.md` / `.planning/ROADMAP.md` — untouched, as instructed
