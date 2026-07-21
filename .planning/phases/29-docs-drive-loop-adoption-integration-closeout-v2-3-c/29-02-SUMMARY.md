---
phase: 29-docs-drive-loop-adoption-integration-closeout-v2-3-c
plan: 02
subsystem: docs-review-obligation gate + adoption write path
tags: [DOCSUP-07, ADR-0010, self-green, integration-test]
requires:
  - tools/adoption_apply/apply.py (ReviewLedgerRefusal, REVIEW_LEDGER_GLOBS — 28-09)
  - tools/hooks/ledger_guard.py (layer 1 — 28-REVIEW CR-02)
  - tools/docs_guard/{guard,ledger,registry,digest}.py (28-04/05, CR-01/CR-03)
provides:
  - end-to-end evidence that /adopt can PROPOSE a registry row and cannot make a binding green
affects: []
tech-stack:
  added: []
  patterns: [zero-write spy, mutation proof, real-git docs_repo fixture]
key-files:
  created:
    - tools/adoption_apply/tests/test_docs_binding_proposal.py
    - tools/docs_guard/tests/test_selfgreen_end_to_end.py
  modified: []
decisions:
  - "The repoint case (ADR-0010 clause 4 as corrected by CR-03) was added to the plan's four task-2 tests, plus a second-cycle green non-degradation control."
  - "Layer 1 (ledger_guard.decide) was exercised alongside layer 2 in the same test, so the DOCSUP-07 proof covers all three ADR-0010 clause 3b layers across the two files."
  - "No production code changed. Zero fixtures were written into the real repo tree; docs/.docs-review-ledger.toml still does not exist."
metrics:
  tasks: 2
  commits: 2
  tests_added: 14
---

# Phase 29 Plan 02: Self-Green End-to-End Proof Summary

`/adopt` can propose a `docs/doc-dependencies.toml` row in the same apply cycle in which its
`docs/.docs-review-ledger.toml` record is refused before any byte is written, and a binding an
agent could legally reach on its own — fresh id or repointed already-ratified id — cannot classify
`FRESH`; every claim is backed by a mutation that flips it.

## What was built

Two integration test files, 14 tests, no production change.

| File | Layer of ADR-0010 clause 3b | Tests |
|------|-----------------------------|-------|
| `tools/adoption_apply/tests/test_docs_binding_proposal.py` | 1 (`ledger_guard.decide`, the Write/Edit tool path) + 2 (`refuse_unsafe_destination` → `ReviewLedgerRefusal`) | 7 |
| `tools/docs_guard/tests/test_selfgreen_end_to_end.py` | 3 (`first_seen-unratified` → greenness) | 7 |

Task 1 (`56cbac7`) — one manifest carrying BOTH destinations: the registry lands with its proposed
bytes, the ledger destination is bucketed `refused`, and the ledger file does not exist afterwards.
The zero-write spy is the 27.1 SC-2 idiom widened to `builtins.open` + `tempfile.mkstemp` (the
publish path is `mkstemp → os.fdopen → os.link`, so `os.open` alone would not see a future plain
`open(..., "wb")`). The raised type is asserted to be `ReviewLedgerRefusal` and NOT a
`ConstitutionRefusal`. The registry payload is validated against
`contracts/harness/docs/doc-dependencies.schema.json` rather than eyeballed, so the cycle proposes a
real binding. Unknown ownership is asserted to become a `questionRecord` carrying no `owner`,
`sources`, `severity`, `dispositions` or `binding` key (the `OWNER_TBD` never-fabricate rule).

Task 2 (`6fa6e91`) — against the hermetic real-`git init` `docs_repo` fixture: a `required`
proposed binding with no `[[reviewed]]` row is `BROKEN` with a `broken-binding` finding and
`ok=False`; its advisory twin is `STALE_ADVISORY`, never `FRESH`; a binding plus a matching
`reviewed-no-change` row carrying its exact live digests, introduced in one change, reports
`first_seen-unratified`; and a genuinely ratified binding repointed at a different
`(sources, target)` pair does the same. Every digest is produced by calling
`digest.compute`/`digest.resolve`; every ledger row is built through a helper that asserts its field
set equals the shipped `ledger._ROW_KEYS`, so no fixture pins a row shape.

## Deviations from Plan

### [Rule 2 — missing critical coverage] The repoint case was added

**Found during:** pre-execution re-read of the shipped code (the lead's brief).
**Issue:** the plan predates 28-REVIEW CR-03. The history test now keys on
`(id, the binding's committed (sources, target))`, and ADR-0010 clause 4 was corrected in place to
say a repointed binding is a NEW obligation. A DOCSUP-07 end-to-end proof that only covered the
fresh-id case would leave the agent-writable-registry laundering path unasserted at the integration
level.
**Fix:** added `test_repointing_a_ratified_binding_is_a_new_obligation`, its mutation
(`test_repoint_detection_is_load_bearing`), and `test_ratified_binding_is_green_before_the_repoint`
as the non-degradation control that keeps the rule from degrading into "nothing is ever green".
**Commit:** `6fa6e91`

### [Rule 2] Layer 1 was exercised, not just layers 2 and 3

**Issue:** the plan was written when layer 1 was inert data; CR-02 made
`tools/hooks/ledger_guard.py` a real enforcer. A "three layers, no single layer suffices" claim
proven across two layers is a claim about two layers.
**Fix:** `test_both_write_side_layers_refuse_the_ledger_and_keep_the_registry_writable` drives the
hook's own `decide()` with an absolute path AND the apply choke point as a bare call, asserting the
registry stays writable at both. Under mutation it is one of the four failures recorded below.
**Commit:** `56cbac7`

### [plan assumption corrected, no code impact] The ledger row shape did NOT change

The plan's B-4 concern (CR-03 adds `binding_digest`) is moot: `tools/docs_guard/ledger.py:73`
`_ROW_KEYS` is still `{id, source_digest, target_digest, disposition}` — the fixer routed identity
through the previous committed REGISTRY precisely so a human ratifier never hand-writes a third
derived digest. The fixtures read `_ROW_KEYS` anyway, so they follow whichever shape ships.

## RED evidence

Every control here already shipped, so RED was produced by mutating the shipped control and running
the selection PLAIN (never an inverted `! uv run pytest`, which exits 0 on a collection error). In
all three runs passing tests appear alongside the failures, which is the proof collection succeeded.

**Mutation A — `tools/hooks/ledger_guard.py`: `REVIEW_LEDGER_GLOBS = []`** (layers 1 + 2; the
constant is imported by `apply.py`, so one edit neutralizes both):

```
FAILED tools/adoption_apply/tests/test_docs_binding_proposal.py::test_registry_applied_and_ledger_refused_in_one_cycle
FAILED tools/adoption_apply/tests/test_docs_binding_proposal.py::test_ledger_refused_before_any_write[plain]
FAILED tools/adoption_apply/tests/test_docs_binding_proposal.py::test_ledger_refused_before_any_write[case_variant]
FAILED tools/adoption_apply/tests/test_docs_binding_proposal.py::test_both_write_side_layers_refuse_the_ledger_and_keep_the_registry_writable
4 failed, 3 passed in 0.06s
```

with, verbatim:

```
E       Failed: DID NOT RAISE <class 'tools.adoption_apply.apply.ReviewLedgerRefusal'>
E       AssertionError: layer 1 did not deny the ledger
E       assert None is not None
E        +  where None = <function decide ...>('/…/docs/.docs-review-ledger.toml')
```

The in-test mutation `test_refusal_is_load_bearing` (monkeypatching `apply.REVIEW_LEDGER_GLOBS` to
`[]`) records the bucket flip the plan asked for: `refused == []` and
`applied == ["docs/.docs-review-ledger.toml", "docs/doc-dependencies.toml"]`, with the ledger bytes
on disk.

**Mutation B — `tools/docs_guard/ledger.py::_check_content_bound` returns `[]` immediately**
(neutralizes `first_seen-unratified`):

```
E       AssertionError: assert 'FRESH' != 'FRESH'   (test_same_commit_self_blessing_is_caught:227)
E       AssertionError: assert 'FRESH' != 'FRESH'   (test_repointing_a_ratified_binding_is_a_new_obligation:343)
2 failed, 5 passed in 0.83s
```

**Mutation C — `tools/docs_guard/guard.py`: the `required and row is None` BROKEN arm disabled**:

```
E       AssertionError: assert 'STALE_REQUIRED' == 'BROKEN'
1 failed, 6 passed in 0.78s
```

All three mutations were reverted with `git checkout -- <the single mutated file>`; `git status
--porcelain` was clean of production files before each commit.

## Gate results

| Gate | Result |
|------|--------|
| `uv run pytest tools/adoption_apply/tests/test_docs_binding_proposal.py -q` | 7 passed |
| `uv run pytest tools/docs_guard/tests/test_selfgreen_end_to_end.py -q` | 7 passed |
| `uv run pytest tools/adoption_apply tools/docs_guard -q` (plan verification) | 369 passed |
| `uv run ruff check` / `ruff format --check` on both files | clean |
| `git diff --name-only HEAD~2 -- harness/skills \| wc -l` | 0 |
| `git status --porcelain` after both commits | only the two intended files, both committed |

## Observation for the reviewer (not fixed here — out of plan scope)

Layer 3's history test reads the previous committed ledger with `git show HEAD:./<path>`, so its
fulcrum is **HEAD vs. the WORKING TREE**: it distinguishes a self-blessed row from a ratified one
only while the change is uncommitted. The `docs-guard` CI job (`.github/workflows/ci.yml:281-291`)
runs `actions/checkout` and then the guard, so HEAD there already CONTAINS the change under review —
a self-blessed row committed together with its binding appears in `git show HEAD:` and would not
report `first_seen-unratified` in that job. The layer is therefore load-bearing for pre-commit /
local-loop evaluation, and the write-side layers 1 and 2 are what actually stop the row reaching a
commit in the first place. This is Phase 28 design territory (ADR-0010 clause 4 says "previous
COMMITTED ledger" without pinning which ref CI evaluates), it was NOT verified against a live PR
run, and nothing was changed for it here. Flagging it rather than quietly asserting around it.

## Known Stubs

None.

## Threat Flags

None — no new network, auth, file-access or schema surface. Two test files only.

## Self-Check: PASSED

- `tools/adoption_apply/tests/test_docs_binding_proposal.py` — FOUND
- `tools/docs_guard/tests/test_selfgreen_end_to_end.py` — FOUND
- commit `56cbac7` — FOUND
- commit `6fa6e91` — FOUND
- `docs/.docs-review-ledger.toml` — ABSENT, as required
