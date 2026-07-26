# Phase 40-01 — Self-Gate Teardown — Summary

**Completed:** 2026-07-27
**Requirement:** CER-04
**Teardown commit:** `45364d7` — `feat(40): delete the skill-registry self-gate`
**Result:** all nine V-checks green; suite 1664 passed / 0 failed

---

## What was deleted

One atomic commit (`45364d7`), exactly ten paths, no superset:

| Path | What it was |
|---|---|
| `tools/skill_registry/` (6 files, 611 LOC) | the lock builder + `--check`/`--write` CLI |
| `harness/skills/registry.lock` | the 24-skill declaration (8462 bytes) |
| `tools/harness_lint/tests/test_skill_registry_lock.py` (50 LOC) | the in-suite mirror of the CI job |
| `.github/workflows/ci.yml` | CI job `registry-lock` (comment block + body) and its `gate.needs` entry |
| `uv.lock` | the `harness-skill-registry` virtual workspace member |

`pyproject.toml` was not edited — `members = ["tools/*"]` is a glob, so removing the directory
removed the member (D-04). No `exclude` entry was added.

---

## Verification — observed output, not "passed"

| # | Check | Observed |
|---|---|---|
| V-1 | absence sweep over `tools/ harness/ .github/ pyproject.toml uv.lock` | no output, `exit=1` (no match) |
| V-2 | same sweep over `docs/` | exactly the two documented survivors: `docs/adr/0012-ci-and-merge-as-decision-authority.md` and `docs/explanation/agent-workflow-skillset-design-guide.md` |
| V-3 | `grep -n "needs:" .github/workflows/ci.yml` | 2 lines — `:80` (`needs: setup`) and `:381` (fan-in, **12 entries**, `registry-lock` absent, no other token changed) |
| V-4 | `uv run pytest` | `1664 passed in 76.60s`, 8 snapshots passed, 0 failed |
| V-5 | `uv sync --all-packages` | `Resolved 61 packages / Checked 30 packages`, exit 0 |
| V-6 | emit-drift (3-step, `ci.yml` path set) | `exit=0` — empty diff |
| V-7 | stale-derived (3-step, `docs/reference` + `.memory/derived/contracts-index.md`) | `exit=0` — empty diff |
| V-8 | `tools.contract_drift.drift` | `contract-drift: OK — live manifest matches the committed baseline.` |
| V-9 | `tools.ruff_baseline` | `ruff ratchet: 245 findings (baseline 245) / PASS: every rule class is at its baseline.` |

`gate.needs` moved from line 410 to line 381 as a consequence of deleting the 29-line job block —
expected, and the only change to that line is the removed token.

---

## The guarantee this phase drops — read this before adding a gate back

With `harness/skills/registry.lock` gone, **editing a skill's `description` now silently changes
agent routing with no gate objecting.** Nothing catches it. That is deliberate and ratified in
`docs/adr/0012-ci-and-merge-as-decision-authority.md` — CI and the merge are the authority — and it
is recorded as accepted risk 4 in `.planning/research/v2.5-scoping-FINAL.md:156`.

It is **not** an oversight, and it must not be re-mechanized without a new ADR. The milestone's
binding constraint is explicit: the surface may not grow without retiring at least as much.

What still covers the neighbouring cases, so the loss is not overstated:

- a skill **added or removed by name** → still caught by `tools/harness_lint/caps.py:137`
  `EXPECTED_SKILLS`, asserted by `tools/harness_emit/validate.py:182-183` and
  `tools/harness_emit/tests/test_emit_determinism.py:100-104`. Deliberately kept (D-03) — deleting
  it here would have removed the last name-level guard exactly as phases 41/43/44 begin deleting
  skills.
- a `harness/` edit that was **not re-emitted** → still caught by CI `emit-drift`.

Genuinely uncovered: a description or `references/` change inside an existing skill that *is*
re-emitted in the same commit.

---

## Finding: the deletion-phase ordering constraint (applies to phases 41, 43, 44)

The plan originally required all V-checks green **before** staging or committing. That is
**impossible** in this repo for any phase that deletes a tracked file, and the executor correctly
stopped rather than working around it.

`tools/adoption_scan` derives its file set from git, not the filesystem
(`destinations.py:217` → `git ls-files`). Three tests are red in the window between "file deleted on
disk" and "deletion committed":

| Test | Reads | Cleared by |
|---|---|---|
| `test_plan_classification.py::test_contract_candidate_matches_real_repo_schema_count` | git INDEX, then `stat()`s each path | **staging** |
| `test_scan_exclusions.py::test_ci_yml_false_positive_closed` | same | **staging** |
| `test_dispositions.py::test_catalog_invariant_to_untracked_local_state` | checks out **HEAD** into a temp `git worktree`, diffs its catalog against the current tree | **the commit only** |

The third is red *by construction* for any uncommitted deletion of a tracked file — staging cannot
fix it, because HEAD is unchanged. Measured: with deletions unstaged, 3 failed / 1661 passed; staged,
1 failed / 1663 passed; committed, **0 failed / 1664 passed**.

**Corrected order for every later deletion phase: delete → stage → commit → verify → `--amend` if
red.** This does not weaken the atomic-commit rule (D-01): the guarantee is *one commit in history*,
and `git commit --amend` preserves it while still allowing repair.

Do not "fix" `tools/adoption_scan` to accommodate this — the test is correct; the catalog *should*
be HEAD-derived.

---

## Process note — a mis-shaped commit was corrected

An intermediate commit (`2aa64fb`, since rebuilt) accidentally combined the teardown with a planning
document, because the teardown deletions were already staged when the planning file was committed.
Caught during verification, before any push. The branch was rewound with `git reset --soft` and
rebuilt as the two commits it should have been: `45364d7` (teardown, 10 paths) and `2902752`
(the plan correction). Nothing was pushed at any point; no shared history was rewritten.

Operational lesson worth carrying: in a phase whose whole guarantee is commit shape, run
`git diff --cached --name-only` immediately **before every** `git commit`, not only before the one
commit you think matters.

---

## Net surface change

**−1 CI job, −1 tool package, −1 lock file, −2 gate tests, +0** commands / agents / skills /
contracts / hooks / tools. Deletion-only, as required by Success Criterion 6.

## Known, accepted residue

`.memory/derived/repo-map.md` still names `tools/skill_registry/registry.py` symbols. It is outside
the `stale-derived` gate's tracked path set, regenerates on the next `/orient` or `/refresh-memory`,
and gates nothing. D-06's sweep path list deliberately omits `.memory/`.

## Unblocks

Phase 41 (Docs-Review Plane Removal) and every later skill deletion. The command that no longer has
to be run before deleting a skill: `uv run python -m tools.skill_registry --write`.
