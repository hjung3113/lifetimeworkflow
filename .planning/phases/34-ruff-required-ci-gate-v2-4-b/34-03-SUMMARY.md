---
phase: 34-ruff-required-ci-gate-v2-4-b
plan: 03
subsystem: ci
tags: [DEBT-01, ci-gate, fan-in, observed-failure]
requires:
  - tools.ruff_baseline (plan 02)
  - .github/workflows/ci.yml::gate.needs
provides:
  - "the `lint` CI job, gating on `uv run python -m tools.ruff_baseline`"
  - "tools/harness_lint/tests/test_ci_lint_gate.py — 6 structural assertions"
  - "the general invariant: every job except `gate` is a member of gate.needs"
affects:
  - "future CI jobs — the general fan-in invariant fails for the next one that is not wired in"
tech-stack:
  added: []
  patterns:
    - "parse the workflow, never grep it — `lint` occurs in comments and in polyglot_lint"
    - "the gate is observed failing before it is claimed to be a gate"
key-files:
  created:
    - tools/harness_lint/tests/test_ci_lint_gate.py
  modified:
    - .github/workflows/ci.yml
decisions:
  - "D-09/D-10 held: job named `lint`, shaped like docs-guard, and it does NOT run a bare `ruff check .`"
  - "D-12 held: the fail->pass cycle is observed locally against the exact command CI runs"
metrics:
  tasks: 4
  commits: 3
  tests_added: 6
---

# Phase 34 Plan 03: The Blocking Job, and Proof It Blocks Summary

`lint` is job 12 in `ci.yml` and a member of `gate.needs`. It was observed going red on two
different regression shapes and green on their removal.

## What was built

| Task | Deliverable | Commit |
|------|-------------|--------|
| 1 | `test_ci_lint_gate.py` — 6 structural assertions, RED | `7ac2627` |
| 2 | The `lint` job + `gate.needs` membership | `4e907c4` |
| 3 | The RED→GREEN observation (nothing committed) + one self-inflicted E501 fixed | `bf19f13` |
| 4 | Full-gate re-verification | — |

## RED evidence (task 1, run PLAIN)

`uv run pytest tools/harness_lint/tests/test_ci_lint_gate.py -x -q`, verbatim first failure:

```
E       AssertionError: ci.yml must define a `lint` job (DEBT-01)
E       assert 'lint' in {'contract-check': {...}, ...}
```

5 failed, 1 passed. The one that passed is `test_every_job_is_in_the_fan_in` — the general
invariant already held, which is the point: it is not a restatement of this phase's job, it is the
guard for the next one.

## The gate observed failing, then passing

Against **the exact command the CI job runs**, `uv run python -m tools.ruff_baseline`. GitHub
Actions cannot be dispatched for this branch from here, and a green CI run would only ever evidence
the passing half.

**Baseline state**
```
ruff ratchet: 393 findings (baseline 393)
PASS: every rule class is at its baseline.
exit=0
```

**RED 1 — an existing rule class grows.** One over-long comment appended to
`tools/ruff_baseline/ratchet.py`:
```
ruff ratchet: 394 findings (baseline 393)
  REGRESSION  E501: baseline 267 -> found 268

FAIL: a ruff rule class grew. The baseline may only SHRINK.
Fix the new finding(s) above. Do NOT raise the baseline — `--update` refuses to, and hand-raising the committed file is visible in review.
exit=1
```

**RED 1b — `--update` refuses to absorb it.** The same tree, asking the tool to record the new
number:
```
REFUSED: refusing to raise the ruff baseline (E501: 267 -> 268). The baseline may only shrink — fix the new findings instead.
exit=3
```
`git diff -- tools/ruff_baseline/baseline.json` was empty afterwards: the refusal did not partially
write.

**RED 2 — a rule code the baseline has never seen.** A bare `except:` (E722, a class the vendored
exclusion removed from the repo entirely, so its baseline is absent = 0):
```
ruff ratchet: 394 findings (baseline 393)
  REGRESSION  E722: baseline 0 -> found 1

FAIL: a ruff rule class grew. The baseline may only SHRINK.
exit=1
```

**GREEN — both reverted**
```
ruff ratchet: 393 findings (baseline 393)
PASS: every rule class is at its baseline.
exit=0
```
`git status --porcelain` afterwards showed only this phase's uncommitted summary — the observation
left nothing behind.

## An unplanned live catch, worth more than the staged ones

Between generating the baseline and wiring the job, plan 03's own new test file introduced **two**
E501 findings. The ratchet caught them unprompted (`E501: baseline 267 -> found 269`) before any
deliberate RED was staged. They were fixed (`bf19f13`), not baselined. This is the gate doing its
job on an unstaged, genuinely accidental regression — including one committed by the agent that
built it.

## Deviations from Plan

**DEV-07 — an extra commit.** The plan budgeted two commits for tasks 1–2 and none for task 3.
`bf19f13` exists because of the live catch above. Fixing the findings rather than the baseline is
the behaviour the gate is supposed to produce, so it is recorded rather than squashed away.

**DEV-08 — the RED-2 rule code changed.** The plan named E722 as "absent from the baseline"; that
held. Worth noting it is only absent *because* plan 01 excluded the vendored tree — before that
exclusion, E722 had a baseline of 2 and this observation would have needed a different rule.

## Gate results (task 4)

| Gate | Result |
|------|--------|
| `uv run pytest -q` | **1539 passed**, 8 snapshots (1506 before this plan; +27 ratchet, +6 CI-structure) |
| `uv run python -m tools.contract_drift.drift` | `OK — live manifest matches the committed baseline` |
| `uv run python -m tools.harness_emit` then `git status --porcelain` | clean (nothing under `harness/` was touched) |
| `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` | `ok -- validation done` |
| `uv run pytest tools/harness_lint -q` | 329 passed |
| `uv run python -m tools.ruff_baseline` | exit 0 |
| `grep 'needs: \[setup' .github/workflows/ci.yml` | `lint` present, between `core-suite` and `lifecycle-eval` |

## Open obligation this phase created (not closable by an agent)

**`3bc21ea` turned the `docs-guard` gate red**, found by the phase-35 agent and reproduced here
(`uv run python -m tools.docs_guard` → exit 1). The autofix touched two source files of the
`task-control-cli-howto` binding, so its combined source digest moved
`54e3b89ec1ed -> 4876a7c947a5` while the target digest stayed put. That is docs-guard working
correctly: a source moved and a human-authored document was left un-re-reviewed.

The review was performed and the answer is `reviewed-no-change` — the entire diff to those files
is import wrapping plus two genuinely unused imports, and `docs/how-to/task-lifecycle.md`
documents CLI invocations whose subcommands, flags and exit codes are untouched. `updated` would
be wrong on the gate's own terms, since it is verified against a *target*-digest delta.

**The ledger is human-authored only** (ADR-0010 §3b; the file's own header states that
`[[reviewed]]` carries no reviewer field precisely because the committing hand *is* the record).
An agent landing its own reviewed row is byte-identical to the self-green attack. So the exact
one-line change, both digests computed live, and the reasoning are drafted at
`.planning/phases/34-ruff-required-ci-gate-v2-4-b/drafts/docs-review-ledger-task-control-cli-howto.md`
for a human to author. **Phase 34 does not close green on `docs-guard` until that lands.**

`[STALE_ADVISORY] lifecycle-eval-shadow-metrics` also moved and is deliberately left alone —
advisory findings do not change the exit code, and the docs-upkeep loop is bounded to the exit-1
set.

## Known Stubs

None.

## Threat Flags

None. No new action, no new permission; the job interpolates nothing from `github.event.*` and the
top-level `permissions: contents: read` is unchanged — all four asserted by
`test_lint_job_keeps_the_repo_security_posture`.

## The one thing this cannot do

`gate` becoming a **required** status check is a repo setting, not something a workflow file can
grant — the same limit `ci.yml:9-13` already records for every other job. Until a human enables it
in branch protection, `lint` blocks the fan-in but the fan-in itself is advisory. That is out of
scope here (D-02, repo-config, human action), and it is the same condition all eleven sibling jobs
are already in.

## Self-Check: PASSED

- `.github/workflows/ci.yml` — `lint` job present, in `gate.needs`
- `tools/harness_lint/tests/test_ci_lint_gate.py` — FOUND
- commit `7ac2627` — FOUND
- commit `4e907c4` — FOUND
- commit `bf19f13` — FOUND
