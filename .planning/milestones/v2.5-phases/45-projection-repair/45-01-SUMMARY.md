---
phase: 45-projection-repair
plan: 01
subsystem: harness-guardrails
tags: [constitution-plane, contract-guard, codeowners, adr-0012, dead-control-removal]
requires:
  - "docs/adr/0012-ci-and-merge-as-decision-authority.md clause (d) (ratified supersession)"
  - "Phase 44's code move of golden/** into the instance overlay"
provides:
  - "a three-member constitution plane (contracts/**, docs/adr/**, docs/glossary.md) in every copy this plan owns"
  - "a permission matrix with no deny row lacking a live enforcer"
  - "a CODEOWNERS constitution block whose every route matches real paths"
affects:
  - "tools/hooks/contract_guard.py (the only ENFORCED declaration)"
  - "harness/permission-matrix.json (inert data mirror)"
  - ".github/CODEOWNERS (merge-time ratification)"
  - "tools/adoption_scan/destinations.py (adoption catalog)"
tech-stack:
  added: []
  patterns: ["dead-control removal", "probe re-subjection over test deletion"]
key-files:
  created:
    - .planning/phases/45-projection-repair/45-01-SUMMARY.md
  modified:
    - harness/permission-matrix.json
    - tools/hooks/contract_guard.py
    - tools/hooks/tests/test_contract_guard.py
    - tools/harness_perms/resolver.py
    - tools/harness_perms/tests/test_resolver.py
    - tools/harness_perms/tests/test_order_resolution.py
    - tools/hooks/_stdin.py
    - tools/harness_lint/tests/test_agents.py
    - tools/adoption_apply/tests/test_constitution_refusal.py
    - .github/CODEOWNERS
    - tools/adoption_scan/destinations.py
decisions:
  - "golden/** is REMOVED from the constitution plane per ADR-0012 clause (d), not repointed (D-01)"
  - "all copies of the declaration moved in ONE commit so no dead control stays green (D-02)"
  - "the *.env deny rows and their asserting tests die together (D-04)"
  - "the byte-hygiene CRLF control and the adoption refusal probe are RE-SUBJECTED, not deleted (D-16)"
  - "the GEN-04 phrasing rule was honoured: no core-plane file gained an `examples/` token"
metrics:
  commits: 2
  tests_before: 880
  tests_after: 874
  completed: 2026-07-29
---

# Phase 45 Plan 01: Constitution-Plane Collapse Summary

Collapsed the constitution plane from four members to three across all eleven files that declare or
assert it, deleted the two enforcer-less `*.env` deny rows with their tests, and removed the three
zero-match routes/globs — two commits, both ending at 874 passed / 7 snapshots.

## What Changed

### Commit 1 — `016d4c1` (nine paths)
`fix(45-01): collapse the constitution plane to three members and drop the enforcer-less *.env deny rows`

```
 harness/permission-matrix.json                     |  7 ++---
 .../tests/test_constitution_refusal.py             |  2 +-
 tools/harness_lint/tests/test_agents.py            |  2 +-
 tools/harness_perms/resolver.py                    |  4 +--
 tools/harness_perms/tests/test_order_resolution.py |  8 ++---
 tools/harness_perms/tests/test_resolver.py         |  8 -----
 tools/hooks/_stdin.py                              |  9 +++---
 tools/hooks/contract_guard.py                      | 32 +++++++++++---------
 tools/hooks/tests/test_contract_guard.py           | 35 ++++++++++------------
 9 files changed, 47 insertions(+), 60 deletions(-)
```

Measured after this commit: **874 passed, 7 snapshots**.

Arithmetic held exactly as the plan predicted: 880 − 3 whole tests deleted
(`test_golden_write_denied`, `test_dotenv_denied`, `test_unapproved_golden_write_denied`)
− 3 parametrize cases removed from `test_constitution_and_secret_paths_denied` = **874**.
The two probe swaps did not move the count.

Probe re-subjections (deliberately count-neutral):
- `test_approved_constitution_with_crlf_still_denied` → `contracts/x.schema.json` (T-45-03: this is
  the byte-hygiene path's only test).
- `test_constitution_refusal.py`'s parametrize row → `docs/adr/y/0099-example.md`.

Assertion repointing: the two `assert "golden-approve" in reason` lines became
`assert "GOLDEN_APPROVE_HUMAN" in reason`; the neighbouring `assert "CODEOWNERS" in reason` lines
were left untouched and stayed green.

### Commit 2 — `14659e3` (two paths)
`fix(45-01): remove the CODEOWNERS routes and the adoption-catalog glob that match zero paths`

```
 .github/CODEOWNERS                  | 10 +++++-----
 tools/adoption_scan/destinations.py |  1 -
 2 files changed, 5 insertions(+), 6 deletions(-)
```

Measured after this commit: **874 passed, 7 snapshots** — the catalog glob cost no test, as measured
in the plan's replay.

## GEN-04-Constrained Wording (verbatim, for plans 03 and 06 to reuse)

**`harness/permission-matrix.json` `_note`** — the replacement for the four-member sentence:

> `path_deny_globs` are the constitution path-scoped denies the resolver enforces (opencode's native
> `edit` key is not path-globbable, so path denies live here as data). The constitution subset is
> THREE members — contracts/\*\*, docs/adr/\*\* and the literal file docs/glossary.md.
> docs/adr/0001-walking-skeleton-golden-core.md:48 declared FOUR; that declaration is superseded by
> docs/adr/0012-ci-and-merge-as-decision-authority.md clause (d) to the extent that golden/\*\* leaves
> the constitution-plane core, and the relocated instance baselines are now ratified at the merge by
> **the instance-scoped golden CODEOWNERS route** rather than in-session. This data implements those
> accepted decisions rather than defining them, so a member may not be added or dropped without a
> superseding ADR. path_deny_globs is now an exact duplicate of contract_guard.CONSTITUTION_GLOBS
> with no independent production reader; the two are kept in sync by
> tools/harness_lint/tests/test_agents.py.

**`tools/hooks/contract_guard.py` (the former `:55` `approve.py` path)**:

> `# Human confirmation token; a NON-EMPTY value == human-authorized session. Reuses the existing`
> `# GOLDEN_APPROVE_HUMAN precedent, which now lives in the instance overlay's relocated`
> `# golden_runner approve script — agents must not fabricate it.`

Neither sentence contains the literal token `examples/`.

## New Live Refusal String

```
contract-guard: '<path>' is on the constitution plane (contracts/ · docs/adr/ · docs/glossary.md);
it is CODEOWNERS-gated and may only be changed by a human who sets GOLDEN_APPROVE_HUMAN, ratified
at the PR through CODEOWNERS. Refusing the write.
```

Contains `CODEOWNERS` (twice); contains no `golden-approve`.

## Verification Results

| Check | Expected | Observed |
|-------|----------|----------|
| `uv run pytest -q` after commit 1 | 874 passed, 7 snapshots | 874 passed, 7 snapshots |
| `uv run pytest -q` after commit 2 | 874 passed, 7 snapshots | 874 passed, 7 snapshots |
| GEN-04 guard + cross-repo companion | green | 22 passed |
| `uv run python -m tools.harness_emit` then `git status --porcelain` | no `.opencode/`/`.claude/`/`opencode.json` change | clean — emitted trees byte-identical |
| `git grep -n '"golden/\*\*"' -- tools harness .github` | no output | no output (exit 1) |
| both declarations == `['contracts/**','docs/adr/**','docs/glossary.md']` | equal | `declarations OK` |
| `grep -c 'golden' tools/adoption_scan/destinations.py` | 0 | 0 |
| `uv run pytest examples/log-parser -q` | 31 passed | 31 passed |
| `uv run python -m tools.ruff_baseline` | PASS | PASS (74 findings vs baseline 84; **not** `--update`ed, per plan) |

Preserved-by-instruction fixtures confirmed intact: the `docs/how-to/task-lifecycle.md` allow-probe
in `test_resolver.py::test_neighbouring_docs_allowed` and the negative-control tuple in
`test_contract_guard.py::test_neighbouring_docs_paths_are_not_constitution`.

## Deviations from Plan

**1. [Rule 3 — blocking] Reflowed the `_stdin.py` docstring paragraph to avoid a NEW E501**
- **Found during:** Task 1, step (7).
- **Issue:** the three-member list is longer than the list it replaced; the single-line edit produced
  a 103-char line, a brand-new E501 finding under `ruff check`.
- **Fix:** rewrapped the surrounding four-line paragraph. Wording and meaning unchanged.
- **Why:** the plan's own verification requires `tools.ruff_baseline` to PASS and forbids running
  `--update` here, so introducing a new finding was not acceptable even though the total count still
  ratcheted downward.
- **File:** `tools/hooks/_stdin.py` · **Commit:** `016d4c1`

Nothing else deviated. No architectural (Rule 4) decision arose.

## Criteria That Did Not Hold Literally

**One wording nit, not a behavioural miss.** Task 2's verify says
`grep -n '^/' .github/CODEOWNERS   # expect 4 routes`. The observed output is **5 lines**:

```
/contracts/        @hjung3113
/docs/adr/         @hjung3113
/docs/glossary.md  @hjung3113
/examples/*/contracts/   @hjung3113
/examples/*/golden/      @hjung3113
```

The plan's "4" collapses the two instance routes into one `/examples/*/...` bullet, and its own Task 2
action text mandates that BOTH instance routes at `:34-36` survive untouched. Five is therefore the
intended state; the substantive criterion — no `/golden/`, no `/approvals/`, instance routes intact —
holds exactly. Flagged so plan 06 can correct the expectation text rather than the file.

## Anything the Plan Did Not Anticipate

Only the E501 interaction above. Every other measured number in the plan — the 880 baseline, the 874
target, the three-deletion/three-param arithmetic, the zero-test cost of the catalog glob, and the
emitted trees being unreachable from this tier — reproduced exactly.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or trust-boundary schema was
introduced; this plan is net-removal of dead declarations.

## Self-Check: PASSED

- `.planning/phases/45-projection-repair/45-01-SUMMARY.md` — FOUND
- commit `016d4c1` — FOUND
- commit `14659e3` — FOUND
