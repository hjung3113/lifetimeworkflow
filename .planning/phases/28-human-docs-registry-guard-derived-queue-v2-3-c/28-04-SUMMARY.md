---
phase: 28-human-docs-registry-guard-derived-queue-v2-3-c
plan: 04
subsystem: docs_guard
tags: [DOCSUP-02, DOCSUP-03, anti-rubber-stamp, ratchet, read-only]
requires:
  - tools/docs_guard/digest.py (28-02)
  - tools/docs_guard/tests/conftest.py::docs_repo (28-02)
provides:
  - tools/docs_guard/ledger.py::load_ledger
  - tools/docs_guard/ledger.py::previous_ledger
  - tools/docs_guard/ledger.py::check_coherence
  - tools/docs_guard/ledger.py::LedgerError
affects:
  - tools/docs_guard/guard.py (28-05 consumes the findings list)
tech-stack:
  added: []
  patterns:
    - "drift.py:129-147 git-show SHAPE, text/TOML-returning variant"
    - "allowlisted committed shape (never a denylist)"
    - "structural read-only proof: public-surface allowlist + static write scan + live negative control"
key-files:
  created:
    - tools/docs_guard/ledger.py
    - tools/docs_guard/tests/test_ledger.py
  modified: []
decisions:
  - "The binding_min ratchet is read from the PREVIOUS COMMITTED ledger, never the working tree — otherwise the same edit that deletes a binding could also lower the bar."
  - "reviewed-no-change is history-free when `previous is None`; only the `updated` half raises `unverified-disposition`. Otherwise D-04 half 1 could not be proven history-free in a no-HEAD tree."
  - "The model-identifier scan is shape-anchored (vendor+model token), not a vendor keyword blocklist, so a binding id naming root CLAUDE.md loads cleanly."
metrics:
  tasks: 2
  commits: 3
  tests: 71 (ledger) / 83 (with 28-02 digest)
---

# Phase 28 Plan 04: Ledger + Disposition Coherence Summary

Read-only review-ledger module implementing DOCSUP-03's anti-rubber-stamp control as three
distinct, greppable reason constants — `disposition-incoherent` (an `updated` claim whose target
digest never moved versus the previous committed ledger), `first_seen-unratified` (a content-bound
disposition with no previously committed row), and `unverified-disposition` (git history
unreadable) — plus the `binding_min` deletion ratchet, with no writer anywhere in the module.

## Tasks completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED — coherence, forbidden-key and no-writer tables | `f92d6a4` | `tools/docs_guard/tests/test_ledger.py` |
| 2 | GREEN — `ledger.py` load / previous-committed / coherence | `8501a01` | `tools/docs_guard/ledger.py` |
| 2 | ruff UP035 follow-up on the test table | `840e15d` | `tools/docs_guard/tests/test_ledger.py` |

## RED evidence (DOCSUP-03)

All RED runs used the inverted form (`! uv run pytest ... -q`), which exits 0 only when the
selection FAILS. Nothing was piped into `head`/`tail`. The throwaway checker loaded the TOML with
no allowlist, returned `None` from `previous_ledger` unconditionally, and reported a finding only
when a stored digest disagreed with the live one.

### `paste_live_digest` — the attack reported CLEAN

The centrepiece. Previous committed row `(S0, T0, reviewed-no-change)`; the source is edited to
`S1`; the ledger is edited to `(S1, T0, "updated")`; **the target document is untouched**. Both
live digests now equal the stored ones, so the digest-only checker returns an EMPTY finding list —
the ledger is green and the attack has succeeded. This is the failure the whole phase turns on, and
it is not a fixture, git, or import error:

```
$ uv run pytest tools/docs_guard/tests/test_ledger.py -k paste_live_digest -q
FF.                                                                      [100%]
____________________ test_coherence_case[paste_live_digest] ____________________
E       AssertionError: paste_live_digest: finding set mismatch — expected [('one', 'disposition-incoherent', 'fail')], got []
E       assert [] == [('one', 'dis...ent', 'fail')]
E         Right contains one more item: ('one', 'disposition-incoherent', 'fail')
tools/docs_guard/tests/test_ledger.py:396: AssertionError
___________________ test_paste_live_digest_names_the_binding ___________________
>       assert findings, "expected a `disposition-incoherent` finding, got none"
E       AssertionError: expected a `disposition-incoherent` finding, got none
E       assert []
tools/docs_guard/tests/test_ledger.py:409: AssertionError
2 failed, 1 passed, 68 deselected in 0.33s
```

### `new_binding_self_blessed` — the self-blessed brand-new binding reported FRESH

Same shape: a brand-new required binding lands together with a `reviewed-no-change` row carrying
its exact live digests. Nothing in history contradicts it, so the checker returns nothing.

```
$ uv run pytest tools/docs_guard/tests/test_ledger.py -k new_binding_self_blessed -q
FFF..                                                                    [100%]
E       AssertionError: new_binding_self_blessed: finding set mismatch — expected [('four', 'first_seen-unratified', 'fail')], got []
E       AssertionError: new_binding_self_blessed_advisory: finding set mismatch — expected [('five', 'first_seen-unratified', 'warn')], got []
_______________ test_new_binding_self_blessed_names_the_binding ________________
>       assert first_seen, "expected a `first_seen-unratified` finding, got none"
E       AssertionError: expected a `first_seen-unratified` finding, got none
E       assert []
3 failed, 2 passed, 66 deselected in 0.53s
```

Note the `2 passed` in that selection: `new_binding_second_commit` (the non-degradation control)
was already GREEN, so the RED state is specifically "the attack row is not caught", never "new
bindings are rejected wholesale".

### `binding_count_regression` — no binding ratchet at all

```
$ uv run pytest tools/docs_guard/tests/test_ledger.py -k binding_count_regression -q
FF.                                                                      [100%]
E       AssertionError: binding_count_regression: finding set mismatch — expected [('', 'binding-count-regression', 'fail')], got []
_______________ test_binding_count_regression_names_both_counts ________________
>       assert regressions, "DID NOT report a binding-count regression"
E       AssertionError: DID NOT report a binding-count regression
E       assert []
2 failed, 1 passed, 68 deselected in 0.32s
```

### `forbidden_key` — every key silently accepted

All eleven rows failed with `DID NOT RAISE`, i.e. the throwaway parsed a ledger carrying a
timestamp / reviewer / prose / model key and returned it as valid:

```
$ uv run pytest tools/docs_guard/tests/test_ledger.py -k forbidden_key -q
>       with pytest.raises(LedgerError) as excinfo:
E       Failed: DID NOT RAISE <class 'tools.docs_guard.ledger.LedgerError'>
tools/docs_guard/tests/test_ledger.py:534: Failed
FAILED ...[reviewed_at]  FAILED ...[date]  FAILED ...[updated_at]  FAILED ...[timestamp]
FAILED ...[reviewer]     FAILED ...[author]  FAILED ...[approved_by]
FAILED ...[excerpt]      FAILED ...[note]    FAILED ...[summary]    FAILED ...[model_key]
11 failed, 60 deselected in 0.07s
```

### `no_writer` — stated explicitly, per the plan's contingency

```
$ uv run pytest tools/docs_guard/tests/test_ledger.py -k no_writer -q
_____________________ test_ledger_module_exposes_no_writer _____________________
E       AssertionError: public surface drifted from the allowlist: unexpected [],
E       missing ['CONTENT_BOUND_DISPOSITIONS', 'DISPOSITIONS', 'LEDGER_PATH', 'LEVEL_FAIL',
E       'LEVEL_NOTE', 'LEVEL_WARN', 'REASON_BINDING_COUNT', 'REASON_BINDING_COUNT_TIGHTEN',
E       'REASON_FIRST_SEEN', 'REASON_INCOHERENT', 'REASON_OPEN_OBLIGATION', 'REASON_STALE',
E       'REASON_UNKNOWN_BINDING', 'REASON_UNVERIFIED']
1 failed, 70 deselected in 0.02s
```

**This is red for the wrong reason and must be read as such.** `unexpected []` is the load-bearing
half: the throwaway exposed **no** writer-shaped name, so this RED does not demonstrate the scan
catching a writer. Per the plan's contingency, the evidence that the scan *can* fail is the LIVE
NEGATIVE CONTROL, which asserts a planted token is flagged and passed against both the throwaway
and the real module:

```
$ uv run pytest tools/docs_guard/tests/test_ledger.py -k negative_control -q   # against the throwaway
1 passed
# test_negative_control_write_scan_flags_planted_token:
#   _write_call_tokens('path.write_text("gotcha")') == ["write_text"]
#   _write_call_tokens("import tomli_w")            == ["tomli_w"]
```

### Non-degradation baseline — GREEN against the throwaway

```
$ uv run pytest tools/docs_guard/tests/test_ledger.py -q \
    -k "honest_update or reviewed_no_change_exact or new_binding_second_commit or binding_count_equal or negative_control"
.........                                                                [100%]
9 passed, 62 deselected in 0.64s
```

`new_binding_second_commit` is the load-bearing one: it was green before the rule landed and green
after, so `first_seen-unratified` cannot have been implemented as "reject every new binding".
`honest_update` plays the same role for the `updated` half; `binding_count_equal` for the ratchet.

## Gate results

| Gate | Result |
|------|--------|
| `uv run pytest tools/docs_guard/tests/test_ledger.py tools/docs_guard/tests/test_digest.py -q` | **83 passed** (71 ledger + 12 digest) |
| `grep -nE 'write_text\|write_bytes\|tomli_w\|os\.replace\|shutil' tools/docs_guard/ledger.py` | empty |
| `grep -n 'unverified-disposition' tools/docs_guard/ledger.py` | matches (`ledger.py:55`) |
| three reason constants pairwise distinct | asserted by `test_the_three_reason_constants_are_pairwise_distinct` |
| `git status --porcelain tools/docs_guard/registry.py contracts` | empty (28-03's file untouched) |
| `uv run ruff check` / `ruff format --check` on both files | clean |
| ledger byte-identity after a full `check_coherence` run | asserted per case (17 rows) |
| commits contain no file deletions | verified `git diff --diff-filter=D f92d6a4~1 HEAD` |

The full suite was deliberately NOT run: 28-03 is concurrently adding `registry.py` in this wave.

## The three reason constants, kept distinct

| Constant | Fact | Remedy |
|----------|------|--------|
| `stale-digest` | the document moved since it was reviewed | review it and re-record the digest |
| `first_seen-unratified` | no human has ever committed a row for this id | land the ledger row in a reviewed commit |
| `unverified-disposition` | git history could not be read at all | fix the checkout/fetch depth, not the docs |

`previous is None` ("history unreadable") and "readable history lacking this id" live in separate
code branches with separate messages, because their remedies differ even where they share a reason.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 - Bug] `tomllib.TOMLDecodeError.lineno` does not exist before Python 3.14**

- **Found during:** Task 2 (first GREEN run — 70 passed, 1 failed)
- **Issue:** `load_ledger`'s corrupt-TOML branch raised `AttributeError: 'TOMLDecodeError' object
  has no attribute 'lineno'`, which would have crashed the gate on exactly the malformed input the
  branch exists to handle (T-28-22 inverted).
- **Fix:** dropped the position from the message entirely rather than version-guarding it — a
  message whose detail varies with the interpreter version is not a stable operator contract. The
  reasoning is recorded as a comment at the raise site.
- **Files modified:** `tools/docs_guard/ledger.py`
- **Commit:** `8501a01`

**2. [Rule 3 - Blocking] ruff UP035 on the committed test file**

- `from typing import Callable` → `from collections.abc import Callable`. Committed separately as
  `840e15d` (`style`) so it does not muddy the `feat` commit's diff.

### Interpretation recorded (not a deviation, but a decision the plan left open)

The plan's step 6 says "compare the live registry binding count against `coverage["binding_min"]`"
while the `binding_count_regression` row says "the **previous committed** ledger has
`binding_min = 3`". These differ, and the difference is load-bearing: reading the threshold from
the working-tree ledger would let the same edit that deletes a binding also lower the bar, which
is the D-06 self-blessing failure in a different costume. The committed value is therefore
authoritative, `check_coherence` takes it from `previous`, and the rationale is a comment on
`_check_binding_count`. Unreadable history means no ratchet check, matching the `previous is None`
posture everywhere else in the module.

The plan's `previous_ledger` correction was honored exactly as instructed: `_git_show_at` is NOT
imported or reused. The shape is copied (fixed argv, `shell=False`, `HEAD:./` prefix,
degrade-to-`None`), `tomllib.loads(stdout.decode("utf-8"))` replaces `json.loads`, the except tuple
widens to `(CalledProcessError, TOMLDecodeError, UnicodeDecodeError, OSError)`, and the divergence
is recorded in the docstring as a real difference from the cited precedent.

## Authentication gates

None.

## Known stubs

None. Every function in `ledger.py` is fully implemented and exercised by the table.

## Threat flags

None. The module introduces no new network endpoint, auth path, or schema at a trust boundary; the
one subprocess it spawns uses fixed argv with `shell=False` and a module-constant path.

## Notes for downstream

- `check_coherence` returns findings and **never** decides an exit code — `guard.classify()`
  (28-05) owns the five-state mapping and the 0/1/3 exit codes.
- `Finding.binding_id` is `""` for the registry-wide binding-count findings; a per-binding consumer
  should filter on that rather than assume every finding names a binding.
- `Finding.level` is `"fail" | "warn" | "note"`. `"note"` is carried only by
  `binding-count-can-tighten`, which is a passing state with a suggestion attached.
- `previous_ledger` returns the raw parsed dict, not `ReviewedRow`s. Committed history is treated
  leniently on purpose: re-validating it against today's allowlist would let a historical shape
  change fail a present-day review.

## Self-Check: PASSED

- `tools/docs_guard/ledger.py` — FOUND
- `tools/docs_guard/tests/test_ledger.py` — FOUND
- commit `f92d6a4` — FOUND
- commit `8501a01` — FOUND
- commit `840e15d` — FOUND
