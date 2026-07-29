---
phase: 45-projection-repair
plan: 02
subsystem: harness-guardrails
tags: [glob-liveness, sc-1, drained-assertion, skip-vocabulary, codeowners-declined]
requires:
  - "45-01 having collapsed the constitution plane to three members and removed the zero-match routes/globs"
provides:
  - "a mechanical, git-index-grounded liveness assertion over harness/permission-matrix.json path_deny_globs"
  - "the same assertion over tools/hooks/contract_guard.CONSTITUTION_GLOBS"
  - "a re-subjected determinism test that cannot silently drain to [] == [] again"
  - "commit_gate + pre-commit prose that names only the two components that run"
affects:
  - "tools/harness_lint/tests/test_agents.py (matrix-side coverage)"
  - "tools/hooks/tests/test_contract_guard.py (guard-side coverage)"
  - "tools/harness_config/tests/test_topology_relationships.py"
  - "tools/adoption_scan/tests/test_install_completeness.py"
  - "tools/hooks/commit_gate.py, harness/git-hooks/pre-commit (docstrings/prose only)"
tech-stack:
  added: []
  patterns: ["git ls-files-grounded assertion", "probe re-subjection over test deletion", "declared-scope comment against future widening"]
key-files:
  created:
    - .planning/phases/45-projection-repair/45-02-SUMMARY.md
  modified:
    - tools/harness_lint/tests/test_agents.py
    - tools/hooks/tests/test_contract_guard.py
    - tools/harness_config/tests/test_topology_relationships.py
    - tools/adoption_scan/tests/test_install_completeness.py
    - tools/hooks/commit_gate.py
    - harness/git-hooks/pre-commit
decisions:
  - "SC-1's glob clause is asserted with fnmatch.fnmatchcase — the resolver's own matcher — not pathlib glob (D-06)"
  - "SC-1's CODEOWNERS clause is DECLINED on the record under SC-8; no CODEOWNERS parser is added"
  - "the assertion is NOT widened to SECRET_PATH_GLOBS / _CATEGORY_GLOBS, whose subject is a scanned target repo"
  - "the drained determinism test is RE-SUBJECTED, not deleted (D-16)"
  - "the module-count floor stays >= 11; only the name moves (vacuity guard, not a census)"
metrics:
  commits: 2
  tests_before: 874
  tests_after: 876
  completed: 2026-07-29
---

# Phase 45 Plan 02: SC-1 Glob Liveness + Drained-Assertion Repair Summary

Made ROADMAP SC-1's glob clause mechanical with two `git ls-files`-grounded assertions inside the two
modules that already load the declarations, and repaired the three assertions four deletion phases had
drained — two commits, 874 → 876, and 876 held at every checkpoint.

## What Changed

### Commit 1 — `b70c0ee` (two paths, +94/−0)

`test(45-02): assert mechanically that no declared path glob matches zero tracked files`

```
 tools/harness_lint/tests/test_agents.py  | 48 ++++++++++++++++++++++++++++++++
 tools/hooks/tests/test_contract_guard.py | 46 ++++++++++++++++++++++++++++++
 2 files changed, 94 insertions(+)
```

Two test functions, plus a `_tracked_paths()` helper local to each module (the `git ls-files`
subprocess idiom of `test_core_no_example_dep.py` / `test_core_no_workspace_member_dep.py`) and two
stdlib imports (`subprocess`, `fnmatch.fnmatchcase`) per module:

- `tools/harness_lint/tests/test_agents.py::test_every_path_deny_glob_matches_a_tracked_file`, sited
  immediately after `test_constitution_paths_denied_globally`, which already loads
  `harness/permission-matrix.json`.
- `tools/hooks/tests/test_contract_guard.py::test_every_constitution_glob_matches_a_tracked_file`,
  sited immediately after `test_every_declared_plane_member_is_independently_enforced`, which already
  mutation-proves `CONSTITUTION_GLOBS`.

Both match with `fnmatch.fnmatchcase` — the matcher `tools/harness_perms/resolver.py:47`
(`resolve_path`) uses at runtime, so a row that passes here is a row the resolver could actually act
on. Both fail with the offending glob named in the message.

Measured after this commit: **876 passed, 7 snapshots**. Working tree clean; **no new file anywhere in
the tree** — `git status --porcelain | wc -l` = 0.

Net surface change: **+0 gates, +0 tools, +0 modules, +0 contracts, +0 dependencies, +0 fixtures, +0
conftest entries, +0 CI jobs.** Two functions inside two existing modules that already load the two
declarations — coverage of an existing declaration, not new surface (SC-8).

### Commit 2 — `db1d7a0` (four paths, +42/−13)

`fix(45-02): re-subject the drained assertions and narrow the SKIP vocabulary`

```
 harness/git-hooks/pre-commit                          |  8 ++---
 tools/adoption_scan/tests/test_install_completeness.py |  4 +--
 tools/harness_config/tests/test_topology_relationships.py | 34 ++++++++++++++++++++--
 tools/hooks/commit_gate.py                            |  9 +++---
 4 files changed, 42 insertions(+), 13 deletions(-)
```

1. **`test_output_is_deterministic`** — confirmed live before touching it:
   `effective_relationships(load_project())` returns `[]`, so the test asserted `[] == []`. Re-subjected
   to a synthetic cfg carrying two explicit relationship records (distinct ids, distinct contracts, so
   neither the duplicate-id, duplicate-semantic-edge nor contradiction guard fires), copying the shape
   `test_accessor_is_raw_passthrough` builds. It now asserts non-emptiness AND `len == 2` AND equality
   across two calls. `test_accessor_returns_empty_on_linear_default` left untouched per instruction —
   its name is still literally true of the generic default config.
2. **`test_discovers_at_least_twelve_modules` → `test_discovers_at_least_eleven_modules`** — rename
   only, at both sites (the `def` at `:196` and the comment reference at `:222`). Floor untouched at
   `>= 11`; the docstring's 20 → 12 → 11 history and its "do not raise it back toward the live value"
   instruction are preserved verbatim. Re-verified: no other code callers (the remaining hits are all
   under `.planning/`, which this plan does not touch).
3. **`tools/hooks/commit_gate.py`** — three docstring sites narrowed to `PASS | FAIL`: the module
   header (`exits 0 iff every non-skipped component passes` → `every component passes`), the
   `GateResult` docstring, and `run_composition`'s docstring (the `A SKIP never blocks…` sentence
   became `A FAIL never suppresses a sibling component: both always run and both are always reported
   (T-04-13)`, preserving the T-04-13 reference). No field, no control flow, no behaviour changed.
4. **`harness/git-hooks/pre-commit`** — the `golden-parity` component and the
   "SKIPped-with-a-log when .NET is absent" claim removed; narrowed to the two live components.

Measured after this commit: **876 passed, 7 snapshots**. `grep -c 'SKIP'` = **0** in both files.

## Negative Controls (verbatim results)

### Task 1 — the mutation the new assertions exist to catch

Re-added `"golden/**"` to BOTH declarations (`harness/permission-matrix.json` `path_deny_globs` and
`tools/hooks/contract_guard.CONSTITUTION_GLOBS`, keeping them in sync) and ran ONLY the two new node
ids:

```
FAILED tools/harness_lint/tests/test_agents.py::test_every_path_deny_glob_matches_a_tracked_file
FAILED tools/hooks/tests/test_contract_guard.py::test_every_constitution_glob_matches_a_tracked_file
2 failed in 0.04s
```

```
E  AssertionError: CONSTITUTION_GLOBS members matching ZERO git-tracked files: ['golden/**'] — a
   plane member with no subject is a dead control; remove it (with a superseding ADR) or repoint it
E  assert not ['golden/**']
```

**Both RED.** The mutation was then reverted (`git checkout -- harness/permission-matrix.json
tools/hooks/contract_guard.py`, explicit paths only) and the full suite re-confirmed at 876 before
committing. This is the Phase-44 defect (CR-01) that was previously caught by reading, now caught at
the assertion.

### Task 2 — the drain the re-subjected test exists to catch

Loading the test module and replacing its bound `effective_relationships` with `lambda cfg: []`
(simulating a future deletion that drains the subject):

```
unmutated: PASS
mutant killed (drain -> []): subject drained to [] — re-subject this test, do not let it assert [] == []
```

## The DECLINED CODEOWNERS Clause (verbatim, on the record)

SC-1's CODEOWNERS half ("no CODEOWNERS route matches zero paths") is **NOT built**, deliberately.

Measured: **no module in this repo parses `.github/CODEOWNERS` routes.** `test_contract_guard.py`,
`test_commands.py` and `test_detect.py` only match the literal string `"CODEOWNERS"`, and
`destination_catalog()` reads the file as a path, never its routes. Covering the clause therefore
requires a **new CODEOWNERS parser with no existing home**, which SC-8 forbids. The clause is
satisfied instead by plan 01 having deleted the two dead routes (`/golden/`, `/approvals/`).

**Honest residual, recorded rather than papered over:** nothing mechanically prevents a FUTURE dead
CODEOWNERS route. T-45-06 is `accept`, not `mitigate`.

This reasoning is also in commit `b70c0ee`'s message, so a reviewer meets it at the commit.

## Scope Deliberately Not Widened

Both new tests carry a `SCOPE` paragraph in their docstring stating that they are **not** extended to
`tools/adoption_scan/scan.py`'s `SECRET_PATH_GLOBS` or `tools/adoption_scan/destinations.py`'s
`_CATEGORY_GLOBS`: their subject is a **scanned brownfield TARGET repository**, not this checkout, so
a zero match there is correct behaviour and asserting otherwise would be a false failure. The comment
exists so a later reader does not "helpfully" widen it.

The matcher choice is likewise pinned in the docstring: `fnmatchcase` (`*` crosses `/`, `**` degrades
to a plain `*`), NOT `pathlib.Path.glob`'s recursive `**` — probing one declaration with the other's
matcher produced 13 false DEAD verdicts during research.

## Verification Results

| Check | Expected | Observed |
|-------|----------|----------|
| `uv run pytest -q` baseline (pre-plan) | 874 passed, 7 snapshots | 874 passed, 7 snapshots |
| `uv run pytest -q` after commit 1 | 876 passed, 7 snapshots | **876 passed, 7 snapshots** |
| `uv run pytest -q` after commit 2 | 876 passed, 7 snapshots | **876 passed, 7 snapshots** |
| targeted `test_agents.py` + `test_contract_guard.py` | green | 65 passed |
| targeted `tools/harness_config tools/adoption_scan tools/hooks` | green | 215 passed, 1 snapshot |
| `git status --porcelain \| wc -l` after each commit | 0 | 0, 0 |
| negative control: `golden/**` re-added | both new tests FAIL | both FAILED (`test_agents.py:243`, `test_contract_guard.py:419`) |
| negative control: accessor drained to `[]` | `test_output_is_deterministic` FAILS | AssertionError raised |
| `grep -c 'SKIP' tools/hooks/commit_gate.py harness/git-hooks/pre-commit` | 0 in both | 0, 0 |
| `uv run python -m tools.harness_emit` then `git status --porcelain` | empty | empty (exit 0) — `pre-commit` is not an emitted artifact |
| `uv run python -m tools.ruff_baseline` | PASS | PASS (74 findings vs baseline 84, unchanged from plan 01; **not** `--update`ed) |
| `uv run pytest examples/log-parser -q` | 31 passed | 31 passed |

The 8 ruff findings reported on the two commit-1 files are all pre-existing E501 lines
(`test_agents.py:6,82,94,178,191`; `test_contract_guard.py:4,41,203`) — none is in an added range, and
the total stayed at 74.

## Deviations from Plan

**1. [Rule 1 — bug] The pre-commit shim's SECOND stale count, at `:22`, was corrected too**

- **Found during:** Task 2, step (4).
- **Issue:** the plan names `harness/git-hooks/pre-commit:4-6`. The same file's closing comment at
  `:22` also read "composes the **three** built-once gates" — the identical false claim, in the
  identical file, about the identical control.
- **Fix:** "three" → "two". No other change.
- **Why:** D-06 is the test applied to every candidate — a live file describing a control that no
  longer exists. Leaving the second sentence would have shipped the exact defect the task removes, in
  the file the task already opens. Bounded strictly to the named file; no new file was touched.
- **File:** `harness/git-hooks/pre-commit` · **Commit:** `db1d7a0`

Nothing else deviated. No Rule 4 (architectural) decision arose. No package-manager install occurred;
`uv.lock` untouched.

## Criteria That Did Not Hold Literally

**One line-number nit, no behavioural miss.** The plan (via the replay) predicts the new assertions at
`test_agents.py:233` and `test_contract_guard.py:412`. Observed: **`test_agents.py:243`** and
**`test_contract_guard.py:419`**. The offset is the length of the scope/matcher docstrings the plan
itself mandates ("Put that reason in a comment above each new test"); prose length is not a criterion.
The substantive claim — **both assertions RED under the `golden/**` mutation** — held exactly, and both
line numbers are recorded above so plan 06 can cite the real ones.

Every other number reproduced exactly: the 874 baseline, the +2 → 876 target, 876 unchanged across
Task 2, zero new files, clean emit, and the `[] == []` drain being live in
`tools/harness_config/tests/` (NOT `tools/harness_lint/tests/` as CONTEXT D-11 and the ROADMAP state —
the plan's corrected path is the right one).

## Anything the Plan Did Not Anticipate

**A self-inflicted process hazard worth recording for later plans: `git checkout -- <file>` used to
revert a temporary mutation will also revert an UNCOMMITTED task edit in that same file.** While
negative-controlling the re-subjected determinism test, an in-place mutation of
`test_topology_relationships.py` was reverted with `git checkout -- <that file>`, which discarded the
Task 2 edit along with the mutation. The edit was re-applied and the negative control was then re-run
by monkeypatching the imported symbol in a throwaway interpreter instead of editing the file — which
is also the stronger control, since it drains the accessor rather than the fixture. Committed state is
correct; recording the trap because the phase's remaining plans do more mutation testing.

(The first mutation attempt, `"relationships": [] or [...]`, was also simply an ineffective mutant —
`[] or [...]` evaluates to the records — so its green result proved nothing. The surviving-mutant
report above uses the accessor-drain mutation, which is the real condition.)

Nothing else surprised. The plan's measured claims — the resolver/`pathlib` matcher split, the live
`[]` from `load_project()`, the live module count of 11, the two rename sites, the absence of
`pre-commit` from `emit-manifest.json`, and no test asserting the SKIP strings — all reproduced.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or trust-boundary schema was introduced.
T-45-05 and T-45-07 are now mitigated by live, mutation-proven assertions; T-45-06 remains `accept`
with the residual stated above.

## Self-Check: PASSED

- `.planning/phases/45-projection-repair/45-02-SUMMARY.md` — FOUND
- commit `b70c0ee` — FOUND
- commit `db1d7a0` — FOUND
- `tools/harness_lint/tests/test_agents.py::test_every_path_deny_glob_matches_a_tracked_file` — FOUND
- `tools/hooks/tests/test_contract_guard.py::test_every_constitution_glob_matches_a_tracked_file` — FOUND
