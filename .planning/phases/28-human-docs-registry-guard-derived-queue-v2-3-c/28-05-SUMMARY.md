---
phase: 28-human-docs-registry-guard-derived-queue-v2-3-c
plan: 05
subsystem: docs-guard
tags: [DOCSUP-03, DOCSUP-05, gate, classifier, ratchet, contract-graph]
requires:
  - tools/docs_guard/digest.py (28-02)
  - tools/docs_guard/registry.py (28-03)
  - tools/docs_guard/ledger.py (28-04)
  - tools/contract_drift/drift.py::run_gate
  - tools/contract_graph/{compile,query}.py (Phase 25)
provides:
  - tools/docs_guard/guard.py::classify — the five-state, first-match-wins classifier
  - tools/docs_guard/guard.py::HUMAN_CORPUS — the D-07 corpus constant that sets the ratchet's meaning
  - tools/docs_guard/impact.py::impact_ids — graph impact ids, empty when unmapped
  - tools/docs_guard/cli.py::{main,render,REMEDIATION,ADR_REMEDIATION,DIFF_LABEL}
  - "`python -m tools.docs_guard` end to end, exit 0/1/3"
affects:
  - Phase 29 /docs-update (binds to the state vocabulary AND the exit codes)
  - plan 28-07 (seeds [coverage] uncovered_max from the live count recorded below)
  - plan 28-08 (fan-in: full suite / drift / emit / GEN-04)
tech-stack:
  added: []
  patterns:
    - "run_gate-shaped result dict (drift.py:177-216) mirrored, exit-code decision left to the CLI"
    - "git-tracked-only enumeration with failure-tolerant degradation (destinations.py:205-225)"
    - "injectable gate seam (drift_gate=) so suppression tests are hermetic"
key-files:
  created:
    - tools/docs_guard/guard.py
    - tools/docs_guard/impact.py
    - tools/docs_guard/cli.py
    - tools/docs_guard/tests/test_guard.py
    - tools/docs_guard/tests/test_impact.py
    - tools/docs_guard/tests/test_report.py
  modified:
    - tools/docs_guard/__main__.py (docstring only — the lazy main() wiring was already correct)
decisions:
  - "FRESH requires digest equality AND an empty blocking-finding set — the classifier-level half of the self-green closure"
  - "binding_min is consumed from ledger.check_coherence (committed-history authority) rather than re-derived in guard.py, to avoid double-reporting"
  - "impact.py does not consult _tracked_schemas — the relationship-record test is strictly stronger and keeps the helper pure"
  - "a SUPPRESSED binding's coherence findings are demoted to note level so exactly one gate reports a contract change"
metrics:
  tasks: 3
  commits: 3
  tests_added: 179 total in tools/docs_guard (57 new across the three new test modules)
---

# Phase 28 Plan 05: Docs-Guard Classifier, Impact Ids, and Report Summary

Five-state first-match-wins classifier in which digest equality is necessary but **not** sufficient
for `FRESH`, over a git-tracked human corpus with two read-only ratchets, plus contract-graph impact
ids and a stable grouped report behind the pinned 0/1/3 exit mapping.

## What Landed

| Task | Deliverable | Commit |
|------|-------------|--------|
| 1 | `guard.py` + `test_guard.py` — five states, both ratchets, drift suppression | `6db057c` |
| 2 | `impact.py` + `test_impact.py` — graph impact ids, empty when unmapped | `3264b86` |
| 3 | `cli.py` + `test_report.py` + `__main__.py` docstring — report and exits | `f52dc32` |

### The classification order (numbered in the source so it cannot be reordered by accident)

1. `BROKEN` — missing target, zero-expansion selector, missing source, or a `required` binding with
   no `[[reviewed]]` row. Ordered **before every staleness check** (D-05).
2. `SUPPRESSED` — a source is a contract in `run_gate()["drifted"]`. `run_gate` is called **once**
   per classify and only its **path** half crosses the boundary.
3. `FRESH` — digests equal **AND** disposition is not `SUPERSEDING_ADR_REQUIRED` **AND**
   `BLOCKING_REASONS ∩ findings(id) == ∅`.
4. `STALE_REQUIRED` / `STALE_ADVISORY` by severity — the terminal branch, carrying the reason that
   denied step 3.

## RED evidence (DOCSUP-03 classification)

All three tables were authored first and run against a throwaway classifier that (a) evaluated
staleness before brokenness, (b) counted the corpus by filesystem walk, and (c) ignored `run_gate`.
The run collected 29 tests: **10 failed, 19 passed** — every negative control green, confirming the
failures are the intended assertions and not a collection, import, or fixture error.

```
FAILED tools/docs_guard/tests/test_guard.py::test_state_order[broken_beats_stale]
FAILED tools/docs_guard/tests/test_guard.py::test_state_order[broken_zero_expansion]
FAILED tools/docs_guard/tests/test_guard.py::test_state_order[broken_no_ledger_row_required]
FAILED tools/docs_guard/tests/test_guard.py::test_state_order[superseding_adr_never_fresh]
FAILED tools/docs_guard/tests/test_guard.py::test_state_order[first_seen_never_fresh]
FAILED tools/docs_guard/tests/test_guard.py::test_digest_equality_is_not_sufficient_for_fresh[superseding_adr_never_fresh]
FAILED tools/docs_guard/tests/test_guard.py::test_digest_equality_is_not_sufficient_for_fresh[first_seen_never_fresh]
FAILED tools/docs_guard/tests/test_guard.py::test_uncovered_untracked_file
FAILED tools/docs_guard/tests/test_guard.py::test_drifted_source_suppressed
FAILED tools/docs_guard/tests/test_guard.py::test_drift_gate_called_once_per_classify
10 failed, 19 passed in 2.57s
```

Verbatim per mandated row — each is the intended assertion failing for its stated reason:

**`broken_beats_stale`** — a staleness-first order reports the deleted target as merely stale:
```
E       AssertionError: broken_beats_stale: expected BROKEN
E       assert 'STALE_REQUIRED' == 'BROKEN'
```

**`broken_zero_expansion`** — `compute([])` is a well-formed digest, so a digest-equality-first
classifier calls a binding that watches nothing green:
```
E       AssertionError: broken_zero_expansion: expected BROKEN
E       assert 'FRESH' == 'BROKEN'
```

**`uncovered_untracked_file`** — a filesystem walk counts a file CI's clean checkout does not have:
```
E       AssertionError: an untracked file moved the uncovered count
E       assert 8 == 7
```

**`drifted_source_suppressed`** — ignoring `run_gate` double-reports the contract change:
```
E       AssertionError: assert 'STALE_REQUIRED' == 'SUPPRESSED'
E         - SUPPRESSED
E         + STALE_REQUIRED
```

**`first_seen_never_fresh`** (the self-green closure at the classifier level) — matching digests
alone re-open the hole `ledger.py` closed:
```
E       AssertionError: first_seen_never_fresh: expected STALE_REQUIRED
E       assert 'FRESH' == 'STALE_REQUIRED'
```
and its direct form:
```
    assert entry["source_digest"] == entry["live_source_digest"]
    assert entry["target_digest"] == entry["live_target_digest"]
>   assert entry["state"] != "FRESH"
E   AssertionError: assert 'FRESH' != 'FRESH'
```

Negative controls GREEN against the throwaway, as required: `advisory_no_ledger_row`, `fresh`,
`stale_required`, `stale_advisory`, `second_commit_is_fresh`, `uncovered_regression`,
`uncovered_equal`/`uncovered_tightened` (after the fixture correction below),
`undrifted_source_not_suppressed`, `drift_findings_not_restated`, `ratchet_not_written`, and the
three binding-count rows.

### RED evidence (DOCSUP-05 impact ids)

`impact.py`'s throwaway fabricated an id from the schema stem whenever the chain did not resolve.
**5 failed, 9 passed** — every unmapped row red, every mapped/structural row green:

```
FAILED tools/docs_guard/tests/test_impact.py::test_unmapped_paths_are_empty_never_fabricated[human_doc]
FAILED tools/docs_guard/tests/test_impact.py::test_unmapped_paths_are_empty_never_fabricated[untracked_stem]
FAILED tools/docs_guard/tests/test_impact.py::test_unmapped_paths_are_empty_never_fabricated[not_a_schema]
FAILED tools/docs_guard/tests/test_impact.py::test_unmapped_paths_are_empty_never_fabricated[source_file]
FAILED tools/docs_guard/tests/test_impact.py::test_results_are_sorted_and_deduplicated_across_inputs
5 failed, 9 passed in 0.03s
```
```
E       AssertionError: source_file: expected an empty impact list
E       assert ['one.py'] == []
```

## Live uncovered count

`uv run python -m tools.docs_guard` against the live tree, verbatim:

```
docs-guard: contract-drift and golden are leading and authoritative — this gate reports human-doc review obligations only and never restates their findings.


docs-guard: 0 binding(s); 12 uncovered human-authored document(s) (no ratchet).
docs-guard: OK
```

**`live_uncovered = 12`** (exit 0, zero bindings — no registry committed yet). Plan 28-07 sets the
initial `[coverage] uncovered_max` from this number. The twelve paths, for that plan's convenience:

```
.memory/README.md
AGENTS.md
CLAUDE.md
docs/explanation/README.md
docs/explanation/agent-workflow-skillset-design-guide.md
docs/explanation/next-milestone-task-control-plane.md
docs/explanation/task-lifecycle-shadow-metrics.md
docs/explanation/template-and-instances.md
docs/glossary.md
docs/how-to/README.md
docs/how-to/task-lifecycle.md
docs/tutorials/README.md
```

Note for 28-07: seeding a binding whose `target` is one of these lowers the count by one, so
`uncovered_max` must be set from the count observed **after** the registry is seeded, not from 12.

## Verification

| Check | Result |
|-------|--------|
| `uv run pytest tools/docs_guard -q` | **179 passed** |
| `uv run python -m tools.docs_guard` | exit 0, prints the uncovered count |
| `uv run python -m tools.docs_guard --help` | works |
| `grep -nE 'write_text\|write_bytes\|open\(.*["'"'"']w' tools/docs_guard/guard.py` | no output |
| `grep -n 'paths' tools/docs_guard/impact.py` | `paths` never returned to the caller |
| `git status --porcelain contracts docs .github` | empty |
| `uv run ruff check tools/docs_guard` / `ruff format --check` | clean, 16 files formatted |

Success criteria: SC-3 met (`BROKEN` proven to win over staleness by construction; both ratchets
enforced read-only); digest equality proven necessary-but-not-sufficient with a non-degradation
control; exit codes 0/1/3 exercised including the registry-invalid channel; impact ids real where
the mapping resolves and empty everywhere else; the report is byte-identical across renders, never
restates drift, and never suggests editing an accepted ADR in any state.

## Deviations from Plan

**1. [Rule 3 — anti-duplication] `binding_min` is consumed, not re-derived**
- **Found during:** Task 1.
- **Issue:** the plan's Task 1 action asks `guard.classify` to evaluate the `binding_min` ratchet
  against `coverage["binding_min"]` from `load_ledger`, but `ledger.check_coherence` already
  evaluates it — against the **previous committed** ledger, which 28-04 established as the
  authoritative threshold (reading it from the working tree lets the same edit that deletes a
  binding also lower the bar). Implementing both would double-report every regression.
- **Fix:** `guard.py` folds `check_coherence`'s `binding-count-regression` /
  `binding-count-can-tighten` findings and does not re-derive them; the choice and its reasoning are
  a comment at the point where the second ratchet would otherwise have gone. The plan's required
  behaviour is unchanged and fully asserted: regression fails naming both numbers, equal passes
  silently, growth emits `ratchet can tighten: set binding_min = <live>`, and
  `binding_deleted_outside_corpus` proves the two ratchets are not interchangeable.
- **Files:** `tools/docs_guard/guard.py`, `tools/docs_guard/tests/test_guard.py`.
- **Commit:** `6db057c`.

**2. [Rule 2 — correctness] a `SUPPRESSED` binding's coherence findings are demoted**
- **Found during:** Task 1, caught by `test_drifted_source_suppressed`'s `ok is True` assertion.
- **Issue:** suppressing the binding STATE was not enough — its fail-level `stale-digest` finding
  still flipped `ok`, so a drifted contract produced exit 1 from this gate as well as from
  contract-drift. That is exactly the double-report D-13 exists to prevent (T-28-28).
- **Fix:** findings attributable to a suppressed binding are kept (the operator still sees why it is
  suppressed) but demoted to note level with a ` (suppressed — contract-drift leading)` marker, so
  exactly one gate reports the change. No `run_gate` content is added by the marker.
- **Files:** `tools/docs_guard/guard.py`. **Commit:** `6db057c`.

**3. [Rule 3 — hermeticity] `impact.py` does not consult `_tracked_schemas`**
- **Issue:** the plan's chain describes `contracts/<...>/<stem>.schema.json -> <stem>` *(if in
  `_tracked_schemas`)*. `compile._tracked_schemas` globs the **live repo** `contracts/` tree, which
  would make a helper documented as pure depend on the checkout and break the in-memory-`cfg`
  hermeticity the same plan requires.
- **Fix:** the gate is the `effective_relationships` record lookup alone, which is strictly stronger
  — a stem carrying an authority record is a declared contract by construction, and a stem present
  in `_tracked_schemas` but absent from the relationships still yields `[]` (asserted by
  `untracked_stem`, and by `test_declared_contract_with_unresolvable_authority_is_empty`). Both the
  prefix and the `.schema.json` suffix are still required, so `contracts/README.md` is not read as a
  contract named `README`.
- **Files:** `tools/docs_guard/impact.py`, `tools/docs_guard/tests/test_impact.py`.
- **Commit:** `3264b86`.

**4. [test-fixture correction, not a weakening] ratchet fixtures use `advisory` bindings**
- **Found during:** Task 1's RED run. The first draft seeded the ratchet cases with `required`
  bindings that had no `[[reviewed]]` row, which is legitimately `BROKEN` and flipped `ok` in every
  ratchet row, making the ratchet assertions untestable. `_seed_corpus` now seeds `advisory`
  bindings so `ok` is a pure function of the ratchet under test; the "required + no row = BROKEN"
  rule keeps its own row in `STATE_ORDER_CASES`. RED was re-run after the change and the mandated
  rows stayed red for their stated reasons.

**5. [docstring accuracy] `tools/docs_guard/__main__.py`**
- Its docstring said "``cli.py`` lands later in the phase", which stopped being true in this plan.
  The lazy-import wiring itself was already correct and is unchanged; only the rationale text moved
  to the still-valid reason (import cost). No behaviour change.

## Anti-pattern fence compliance

Every mandated adversarial row was RED before the fix, the verbatim failure is recorded above, and
in every case the recorded output is the intended assertion failing — never a `ModuleNotFoundError`,
collection error, or fixture error. The RED runs were plain (non-inverted) `pytest` invocations
whose full output was read, precisely because an inverted `!` gate exits 0 on a collection or import
error and masquerades as RED; the pass/fail split (19 passed / 10 failed, then 9 passed / 5 failed)
is itself the evidence that collection succeeded.

The `ratchet_not_written` static no-write scan carries a live planted-token negative control, so a
typo in its token list cannot make it vacuously green.

## Known Stubs

None. No placeholder values, no `TODO`/`FIXME`, no component left unwired — `impact_ids`' empty
return for an unmapped path is the specified correct answer (D-12), not a stub.

## Threat Flags

None. The three modules add no network endpoint, no auth path, and no schema at a trust boundary.
The one new external-process call (`git ls-files`) uses a fixed argv with `shell=False` and takes no
registry- or ledger-controlled value, matching `destinations.py`'s posture; `_previous_rel` confines
an operator-supplied `--ledger` to a repo-relative path via `relative_to(root)` and otherwise falls
back to the module constant, so nothing caller-influenced reaches the `git show` argv (T-28-20).

## Self-Check: PASSED

```
FOUND: tools/docs_guard/guard.py
FOUND: tools/docs_guard/impact.py
FOUND: tools/docs_guard/cli.py
FOUND: tools/docs_guard/tests/test_guard.py
FOUND: tools/docs_guard/tests/test_impact.py
FOUND: tools/docs_guard/tests/test_report.py
FOUND: 6db057c
FOUND: 3264b86
FOUND: f52dc32
```
