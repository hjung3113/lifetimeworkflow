---
phase: 44-non-goal-surface-removal
plan: 04
wave: 4
subsystem: harness-surface
tags: [CER-09, surface-removal, ci-path-resolution, golden]
requires: ["44-03"]
provides:
  - "A CI bare-path resolution assertion covering every pytest path argument in .github/workflows/*.yml"
  - "The golden command/skill surface retired from both planes and both runtime trees"
affects:
  - "tools/adoption_scan/tests/test_install_completeness.py"
  - "harness/** (2 commands + 2 skills deleted, 9 files swept)"
  - "examples/log-parser/** (9 files swept)"
  - "tools/harness_lint/caps.py, tools/harness_lint/tests/test_commands.py, tools/harness_emit/tests/test_coexist.py"
  - ".opencode/, .claude/, opencode.json, AGENTS.md, tools/harness_emit/emit-manifest.json"
tech-stack:
  added: []
  patterns: ["ruamel.yaml workflow walk (already-resolved transitive dep; PyYAML not added)"]
key-files:
  created: []
  modified:
    - tools/adoption_scan/tests/test_install_completeness.py
    - tools/harness_lint/caps.py
    - tools/harness_lint/tests/test_commands.py
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/project_skill.py
    - tools/harness_emit/emit-manifest.json
  deleted:
    - harness/commands/golden.md
    - harness/commands/golden-approve.md
    - harness/skills/golden-testing/SKILL.md
    - harness/skills/golden-debug/SKILL.md
    - harness/skills/golden-debug/references/canonicalization-axes.md
decisions:
  - "Golden-promotion prose in both planes now names human review at the PR (the golden/ and /examples/*/golden/ CODEOWNERS entries) instead of the retired /golden-approve command; the never-self-bless invariant is preserved verbatim."
  - "No replacement instance skill authored for golden guidance — that would be surface growth against SC-8."
metrics:
  commits: 2
  duration: ~35m
  completed: 2026-07-29
---

# Phase 44 Plan 04: CI-path resolution + golden command/skill retirement Summary

Landed the CI bare-path resolution assertion that protects plan 05's relocation, then retired the
`/golden` + `/golden-approve` commands and the `golden-testing` + `golden-debug` skills from both
planes and both runtime trees — leaving `tools/golden_runner` and the module-discovery floor of 12
untouched.

## Commits

| Hash | Message | Diffstat |
|---|---|---|
| `8b5bc41` | `test(44-04): assert every CI pytest path argument resolves to a real path` | 1 file changed, 103 insertions(+) |
| `8678b45` | `chore(44-04): retire the /golden + /golden-approve commands and the golden-testing + golden-debug skills` | 57 files changed, 87 insertions(+), 1044 deletions(-) |

## Task 1 — CI pytest path resolution

Three additions to `tools/adoption_scan/tests/test_install_completeness.py`:

- `_discover_ci_pytest_path_args` — resolves each `.github/workflows/*.yml` with `ruamel.yaml`
  (already-resolved transitive dep at 0.19.1; **PyYAML not added**), walks `jobs.*.steps[*].run`, and
  extracts the bare filesystem path arguments following a `pytest` token. Conservative: flags,
  value-taking-flag values, shell-metacharacter tokens and post-separator tokens are skipped; a token
  qualifies only when it contains `/` or names an existing top-level entry.
- `test_ci_pytest_path_arguments_are_discovered_non_vacuously` — vacuity backstop.
- `test_every_ci_pytest_path_argument_resolves` — the assertion.

**Discovered set, 8 path arguments (non-vacuous, both target paths present):**

```
('ci.yml', 'golden',    'tools/golden_runner')
('ci.yml', 'golden',    'examples/log-parser/tests')
('ci.yml', 'lint',      'tools/ruff_baseline')
('ci.yml', 'workspace', 'tools/workspace_config')
('ci.yml', 'workspace', 'tools/harness_lint/tests/test_workspace_config.py')
('ci.yml', 'workspace', 'tools/harness_lint/tests/test_core_no_workspace_member_dep.py')
('ci.yml', 'workspace', 'tools/golden_runner/tests/test_workspace_golden.py')
('ci.yml', 'workspace', 'tools/contract_drift/tests/test_workspace_drift.py')
```

**Mutation control, verbatim.** `ci.yml:168` repointed `tools/golden_runner` → `tools/golden_runner_moved`:

```
E       AssertionError: CI hands pytest a path argument that does not exist in this checkout: ci.yml job 'golden' -> 'tools/golden_runner_moved' (checked 8 path argument(s))
FAILED tools/adoption_scan/tests/test_install_completeness.py::test_every_ci_pytest_path_argument_resolves
1 failed, 4 passed in 0.39s
```

Restored with `git checkout -- .github/workflows/ci.yml` (explicit single path, never `-- .`):
`5 passed in 0.38s`.

Post-commit: full suite `917 passed`, ruff ratchet `73 findings (baseline 84)` PASS,
GEN-04 `18 passed`. Commit contains exactly one file.

## Task 2 — golden command/skill retirement

**Deleted (4 source artifacts, 5 files):** `harness/commands/golden.md`,
`harness/commands/golden-approve.md`, `harness/skills/golden-testing/SKILL.md`,
`harness/skills/golden-debug/SKILL.md`, `harness/skills/golden-debug/references/canonicalization-axes.md`.
`git ls-files` for all four paths was confirmed empty after `git rm`, then the two skill directories
were `rm -rf`'d (no `__pycache__`/untracked residue was present, but the confirm-then-rm order from
Phase 43 was followed).

**Harness-plane sweep — 9 files**, from a fresh `git grep`, not the plan's HEAD-time enumeration:
`agents/orchestrator.md` (two routing rows lost `/golden`; the "Golden went red" row excised
entirely — both its targets were deleted), `agents/python-engineer.md`,
`agents/templates/engineer.md`, `agents/templates/component-engineer.md`, `commands/orient.md`,
`commands/verify-work.md`, `commands/new-contract-rule.md`, `skills/brownfield-adoption/SKILL.md`,
`skills/polyglot-boundary/SKILL.md`, `skills/python-conventions/SKILL.md`.

**Instance-plane sweep — the 9 files named in the plan**, all rewritten (not repointed) to say golden
promotion is human review at the PR via the `/examples/*/golden/` CODEOWNERS entry; the
"use the `golden-debug` skill" sentences dropped outright; the "never an agent self-bless"
invariant kept in every one. Only body prose touched — the four component agents' frontmatter is
untouched, and `examples/log-parser/tests` stayed green at 14 passed.

**Preserved deliberately:** `harness/commands/verify-work.md`'s
`uv run python -m tools.golden_runner.runner` loop and
`harness/skills/python-conventions/SKILL.md`'s `python -m tools.golden_runner.runner` idiom (the
only two surviving module references, and the whole slack of the floor);
`harness/agents/templates/component-engineer.md:9`'s `<id>.md` resolution token.
Only the *skill/command name* pointers were swept out of `verify-work.md` — including the
`use golden-debug` string inside the preserved shell loop's FAIL echo, which the gate's
`git grep` would otherwise have caught.

**Declaration repairs, same commit:** `caps.py` `EXPECTED_SKILLS` 10 → 8 (before the emitter ran);
`test_commands.py` `EXPECTED_GOLDEN_ADJACENT` 8 → 6 plus its comment and docstring;
`test_coexist.py` 19 → 17 at all four sites including the function name
(`test_all_19_commands_emit_to_both_trees` → `test_all_17_…`).
`tools/harness_emit/project_skill.py`'s `iter_reference_files` docstring now names
`polyglot-boundary` alone.

**`emit-manifest.json` row-delta: 10 rows removed, 0 added** (`0 10` numstat) — the five
`.claude/` rows and the five `.opencode/` rows for the four retired artifacts. Not hand-edited;
in the commit pathspec.

## Post-commit verification (all green, working tree clean)

| Check | Result |
|---|---|
| `uv run pytest -q` | 899 passed, 7 snapshots |
| `uv run pytest examples/log-parser/tests -q` | 14 passed |
| re-emit + `git diff --exit-code` | clean |
| `contract_drift.drift` | OK — live manifest matches baseline |
| `tools.ruff_baseline` | PASS, 73 findings (baseline 84), E501 improved |
| `workspace_check.py` | OK |
| `test_install_completeness.py` + `test_commands.py` + `test_skills.py` | 108 passed |
| deletion / grep / count gate | `17 8` → GATE PASS |
| `git status --porcelain` | empty after both commits |
| `git grep -c "tools.golden_runner" -- harness` | `verify-work.md:1`, `python-conventions/SKILL.md:1` |
| module-discovery floor | 12 top-level packages, `golden_runner` among them; floor test passed |
| `import tools.golden_runner.runner` | OK |

Full-suite count moved 917 → 899: the 18-test drop is the parametrized `test_commands.py` /
`test_skills.py` cases for the four deleted artifacts, plus the deleted-skill reference cases.

## Deviations from Plan

**None affecting outcome.** Three observations where the plan's HEAD-time notes and the live repo
differed, all resolved the way the plan instructs (re-grep, don't work from the enumeration):

1. **`<measured_anchors>` listed `harness/skills/data-contracts/SKILL.md` and
   `harness/skills/two-plane-memory/SKILL.md` as `/golden`-or-`/golden-approve` carriers.** A fresh
   `git grep` shows neither carries any of the four tokens — earlier plans already swept them. No
   edit was made to either; they are in the plan's `files_modified` but were correctly left alone.
2. **`harness/commands/verify-work.md:44`'s preserved shell loop contained a `golden-debug` string**
   (`echo 'FAIL: golden red — use golden-debug, do NOT edit .verified.'`). The plan calls out
   preserving the `tools.golden_runner` invocation on that line but does not name the pointer inside
   it; the gate's `git grep` would have red-flagged it. The echo text was narrowed to
   `FAIL: golden red — do NOT edit .verified.`; the module invocation is byte-identical.
3. **Staging mechanics.** `git add -- $(…)` does not word-split under zsh, so the 52 modified/emitted-
   deleted paths were staged with `git add --pathspec-from-file=<file>` and the commit used
   `--pathspec-from-file` over all 57 paths. Still an explicit per-path pathspec — no `git add -A`,
   no `git add .`, no `git commit -a`.

## Criteria that did not hold

None. Every measured number in the plan reproduced exactly: 8 CI path arguments discovered with both
`tools/golden_runner` targets among them; the mutation control red; the three `adoption_scan` tests
(`test_dispositions::test_catalog_invariant_to_untracked_local_state`,
`test_plan_classification::test_contract_candidate_matches_real_repo_schema_count`,
`test_scan_exclusions::test_ci_yml_false_positive_closed`) red between `git rm` and `git commit` and
green after, unrepaired; 10 manifest rows pruned; 17 commands / 8 skills; module floor exactly 12;
ruff `73 (baseline 84)` with no `--update`.

## Not touched (by instruction)

`docs/glossary.md`, `docs/how-to/README.md`, `docs/how-to/approve-a-golden.md` (Phase 45 CER-11);
`docs/adr/**` and `.planning/**` (append-only / historical); `.github/workflows/ci.yml`
(plan 05 repoints it); `tools/golden_runner/**` and `tools/hooks/contract_guard.py` (out of this
plan's scope — the package moves in wave 5); `CLAUDE.md`'s stack-table `/golden-approve` mentions
(outside the HARNESS-MANAGED markers and outside this plan's pathspec);
`.planning/STATE.md` and `ROADMAP.md`.

## Self-Check: PASSED

- `.planning/phases/44-non-goal-surface-removal/44-04-SUMMARY.md` — FOUND
- commit `8b5bc41` — FOUND
- commit `8678b45` — FOUND
- `harness/commands/golden.md`, `harness/commands/golden-approve.md`,
  `harness/skills/golden-testing`, `harness/skills/golden-debug` — absent from disk and from
  `git ls-files`
