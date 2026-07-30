---
phase: 35-carried-debt-dispositions-v2-4-b
plan: 01
subsystem: commit-gate / deferred-items bookkeeping
tags: [DEBT-04, DEF-05-02-1, test-isolation, closure]
requires:
  - tools/hooks/tests/test_commit_gate.py
  - .planning/phases/05-despecialization/deferred-items.md
provides:
  - "DEF-05-02-1 closed as ALREADY-RESOLVED with a named repairing commit and mutation-backed causality"
affects:
  - ".planning/STATE.md Deferred Items row (reported, NOT written -- orchestrator owns the file)"
tech-stack:
  added: []
  patterns:
    - "closure-by-mutation: a green run is not accepted as proof of repair until neutering the suspected repair reproduces the recorded symptom exactly"
decisions:
  - "No fix invented. The defect was already closed; a second fix would have manufactured work and obscured who repaired it."
  - "The record's suggested per-test delenv was NOT applied -- the shipped repair (an autouse fixture) is strictly broader and already covers it."
metrics:
  tasks: 3
  commits: 1
  tests_added: 0
---

# Phase 35 Plan 01: DEF-05-02-1 Verified and Closed

**Disposition: ALREADY-RESOLVED.** Repaired 2026-07-09 by `ccef8b4`; the record was never updated.
The debt that survived into v2.4 was bookkeeping, not a test defect.

## What Landed

| Task | Deliverable | Commit |
|------|-------------|--------|
| 1-3 | `DEF-05-02-1` closed in `.planning/phases/05-despecialization/deferred-items.md` with both-ways runs, the repairing commit, and mutation evidence | `b4937b7` |

No code changed. That is the finding, not an omission.

## Evidence

### It does not reproduce

The three tests the record names — `test_drift_present_blocks`,
`test_golden_skip_does_not_suppress_drift`, `test_from_hook_blocks_commit_on_drift` — all exist and
all pass regardless of the ambient token:

| Run | Result |
|---|---|
| `env -u GOLDEN_APPROVE_HUMAN uv run pytest <the 3 tests> -q` | **3 passed** |
| `GOLDEN_APPROVE_HUMAN=phase-35-probe uv run pytest <the 3 tests> -q` | **3 passed** |
| `GOLDEN_APPROVE_HUMAN=phase-35-probe uv run pytest tools/hooks -q` | **112 passed** |

### Why — the repairing commit

`git log -S'_no_ambient_approval' -- tools/hooks/tests/test_commit_gate.py` returns exactly one
commit: **`ccef8b4`** *test(commit-gate): make drift-block tests hermetic to ambient
GOLDEN_APPROVE_HUMAN* (2026-07-09, +14 lines, that file only). Its message ends **"Resolves
DEF-05-02-1"** — the id was closed by name in code seven months before the milestone close that
carried it forward.

The shipped repair is **broader than the record's suggestion**. The record proposed adding
`monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)` to three tests. `ccef8b4` instead added
an autouse fixture (`tools/hooks/tests/test_commit_gate.py:28-38`) that strips the token for
**every** test in the module and strips `HARNESS_DEV_BYPASS` alongside it for the identical reason —
a dev session's opt-out would false-green the same base-block tests. The approval-path tests set
their token in-body, which runs after the autouse fixture, so they are unaffected. That
generalization matters: the narrow fix would have left the same leak open to any test added later.

### Causality proven, not assumed

A green run cannot distinguish "repaired" from "the symptom moved", so the claim was tested. Both
`delenv` calls in the autouse fixture were replaced with `pass` and the module re-run with the token
exported:

```
3 failed
  test_drift_present_blocks
  test_golden_skip_does_not_suppress_drift
  test_from_hook_blocks_commit_on_drift
```

**Exactly the three tests the record names, and no others** — the recorded symptom reproduced
precisely. That is positive evidence the fixture is the load-bearing repair and that the record's
original root-cause diagnosis was correct. The mutation was reverted and `git status --short
tools/hooks/` confirmed empty.

## Deviations

None. Task 2a (apply the fix) was not reached because Task 1 branched to 2b, which is the planned
behaviour, not a deviation.

## What STATE.md Should Say

`.planning/STATE.md` was **not** touched — the orchestrator owns it. The row at line 295 should move
from `open` to `resolved`:

> | testing (isolation) | DEF-05-02-1: 3 commit_gate drift-block tests leak the live
> `GOLDEN_APPROVE_HUMAN` token (missing delenv). **RESOLVED — repaired 2026-07-09 by `ccef8b4`
> (autouse fixture stripping the token, and `HARNESS_DEV_BYPASS`, for the whole module); the record
> was stale, not the code. Re-verified 2026-07-22 both ways (3 passed each) and causally confirmed
> by mutation.** See phases/05-despecialization/deferred-items.md | **resolved** | 05-02 |

## Residuals

None for this item. One observation worth carrying, though it is not a defect: **`DEF-05-02-1` sat
closed-in-code but open-in-record for the whole of v2.3.** Nothing reconciles a deferred-items row
against the commit that resolves it, so a debt can be paid and still be carried. That is a
process gap, not a code gap, and it is recorded here rather than acted on.
