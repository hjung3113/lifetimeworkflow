---
status: complete
phase: 40-self-gate-teardown
source: [40-01-SUMMARY.md]
started: 2026-07-27
updated: 2026-07-27
---

## Current Test

[testing complete]

## Tests

### 1. The self-gate is actually gone
expected: `uv run python -m tools.skill_registry --check` fails with "No module named tools.skill_registry" (previously exited 0). `test -d tools/skill_registry` and `test -e harness/skills/registry.lock` both fail. A repo-wide grep for skill_registry/registry-lock/registry.lock over tools/ harness/ .github/ pyproject.toml uv.lock returns nothing.
result: pass
evidence: |
  Run in the live tree /Users/hyojung/orca/lifetimeworkflow (branch
  claude/data-pipeline-harness-8aypct, HEAD after 45364d7):
    $ uv run python -m tools.skill_registry --check
    /Users/hyojung/orca/lifetimeworkflow/.venv/bin/python3: No module named tools.skill_registry
  V-1 grep over tools/ harness/ .github/ pyproject.toml uv.lock -> no output (exit 1).
  V-2 grep over docs/ -> only docs/adr/0012-*.md and
  docs/explanation/agent-workflow-skillset-design-guide.md, both documented survivors.
note: |
  The user first ran this command from the STALE worktree
  /Users/hyojung/orca/workspaces/lifetimeworkflow/lifetimeworkflow (branch
  hjung3113/lifetimeworkflow, at the v2.3 merge 36fb372), which never contained
  tools/skill_registry at all — so that run produced the same message regardless of
  this phase and was NOT valid evidence. Flagged at the time; the pass is recorded
  against the live-tree run above, distinguishable by its .venv path.

### 2. Deleting a skill is no longer blocked by the lock
expected: This is the phase's whole purpose. Deleting any skill directory under harness/skills/ and running the suite produces failures from the *intended* remaining gates (caps.py EXPECTED_SKILLS, emit-manifest, emitted-tree shape) and ZERO registry-lock failures. Before this phase, the same deletion also required `uv run python -m tools.skill_registry --write` to rewrite the lock; that step no longer exists.
result: pass
evidence: |
  Dry-run in the live tree: `rm -rf harness/skills/two-plane-memory` then
  `uv run pytest -q` -> 18 failed, 1642 passed. ZERO registry-lock failures
  (that gate no longer exists). The 18 are the intended remaining gates:
  tools/harness_lint/tests/test_skills.py::test_expected_skills_present_no_sprawl
  (caps.py EXPECTED_SKILLS, kept deliberately per D-03), plus
  tools/harness_emit/tests/test_manifest.py and test_opencode_config.py
  (emit-manifest + emitted-tree shape, already covered by ordering rule 6:
  every skill add-or-delete edits caps.py and re-emits in the same commit).
  Tree restored via `git checkout -- harness/skills/two-plane-memory`;
  `git status --porcelain` empty afterwards.
conclusion: |
  CER-04's scope is exactly met: the only step removed is the lock rewrite
  (`uv run python -m tools.skill_registry --write`). Phases 41/43/44 still owe
  the caps.py edit and the re-emit — that was never in this phase's scope.

### 3. CI job graph still resolves
expected: `.github/workflows/ci.yml` parses as valid YAML; the `gate` fan-in job lists exactly 12 entries; `registry-lock` is absent from that list; and every remaining entry names a job that actually exists (no dangling `needs`).
result: pass
evidence: |
  yaml.safe_load('.github/workflows/ci.yml') parses clean. Programmatic check:
    gate.needs count: 12        (was 13)
    registry-lock present: False
    dangling entries: []        (every remaining entry names a real job)
  V-3 grep: `needs:` appears on exactly 2 lines — :80 (`needs: setup`) and :381
  (the fan-in). gate.needs moved 410 -> 381 as a consequence of deleting the
  29-line job block; the only token changed on that line is the removed
  `registry-lock` (Success Criterion 2 — no other entry added, removed or
  reordered).
note: |
  VALIDATION.md originally listed this as manual-only ("GitHub validates the job
  graph at dispatch; no local command reproduces it"). Closed locally instead by
  parsing the YAML and resolving every `needs` entry against the jobs map — a
  dangling entry is a workflow-load failure that pytest can never surface, so it
  warranted its own check rather than waiting on a push.

### 4. Nothing else moved
expected: Full suite green (1664 passed, 0 failed). uv sync resolves. emit-drift, stale-derived, contract-drift and ruff-ratchet all clean. The teardown commit contains exactly 10 paths and no planning or unrelated files.
result: pass
evidence: |
  V-4 `uv run pytest`            -> 1664 passed, 0 failed (8 snapshots passed)
  V-5 `uv sync --all-packages`   -> Resolved 61 packages / Checked 30 packages, exit 0
  V-6 emit-drift (3-step)        -> exit 0, empty diff
  V-7 stale-derived (3-step)     -> exit 0, empty diff
  V-8 tools.contract_drift.drift -> "OK — live manifest matches the committed baseline."
  V-9 tools.ruff_baseline        -> "245 findings (baseline 245) / PASS: every rule class is at its baseline."
  `git show --stat --name-only 45364d7` -> exactly the 10 teardown paths, no superset.
note: |
  The empty emit-drift diff is the meaningful one: registry.lock was a declaration
  ABOUT harness/skills/, not an emitted artifact, so deleting it must leave
  .opencode/ and .claude/ untouched. It did.
  Suite progression across the phase matches the discovered ordering constraint
  exactly: 3 failed with deletions unstaged -> 1 failed staged -> 0 failed committed.

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]

## Notes

This phase has **no user-facing surface** — it deletes a CI job, a tool package, a lock file and two
gate tests. Every test above is therefore a developer/CI-observable check rather than a UI or
workflow walk-through. All four were run by the assistant before being presented; the observed
results are recorded in `40-01-SUMMARY.md`. The user's role here is to confirm the *claims* are the
right ones, not to re-run the commands.
