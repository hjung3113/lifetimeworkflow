# Plan 14-02 — Summary

**Status:** complete · **Executed by:** Codex (gpt-5.6-terra, medium)
**Commits:** `4ab61a3` feat: add agreement provenance lint · `041c07f` test: cover provenance lint failures · `1b7eed2` feat: lint agreement provenance

## What shipped

`tools/harness_lint/provenance.py` — `Violation` / `check_agreement` / `lint_file` / `lint_dir` /
`main`, cloning `tools/polyglot_lint/lint.py`'s runnable-lint shape (D-04). Wired into `/lint`.
`_TEMPLATE.md`'s `added:` is now quoted.

## Decisions honored — verified

- **D-02 ordering:** `isinstance(added, str)` at `provenance.py:43` runs **before**
  `_ISO_DATE.match` at `:51`. A `datetime.date` therefore fails as a clean Violation rather than
  raising `TypeError`. The corrected mechanism holds: `added: 2026-07-16` unquoted parses to a
  `date`; quoted parses to `str`.
- **D-03 (honest scope):** the lint checks SHAPE, not TRUTH. No PreToolUse hook was added — it is
  rejected, not deferred, because it cannot distinguish a genuine stamp from a fabricated one.
- **D-16:** SC2's "follows the stale-derived pattern (regenerate → verify)" is a category error —
  agreements are never regenerated, so there is nothing to regenerate. D-04's runnable-lint + pytest
  shape is the correct reading of the intent.
- **`/lint` owns selection, not the shell:** the macro passes a *directory*; `provenance.main()`
  applies `iter_agreement_files`. A shell-side `grep -v` filter would have made the macro a **third**
  copy of the predicate — the exact drift D-05 forbids, and a new rule `lint.md:14` disallows.

## Verification

Negative controls all green: absent/prefix-less/empty-tail/whitespace-tail provenance, non-ISO date,
unquoted date object, `status: pending`, and `status: retired` **is** linted (not skipped — only
reachable because of D-14). `_TEMPLATE.md` + `README.md` excluded, not flagged.
