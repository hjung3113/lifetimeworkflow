# Plan 14-01 — Summary

**Status:** complete · **Executed by:** Codex (gpt-5.6-terra, medium) in Orca worktree `phase14-codex`
**Commits:** `da4f307` refactor: share agreement selection predicate · `377ca7e` test: share agreement fixture corpus · `6c0a813` test: cover agreement predicate parity

## What shipped

`tools/harness_lint/agreements.py` — `iter_agreement_files()` + `load_agreement()`, the L1–L4
file-selection predicate extracted from `inject.py`'s inline `_agreements_block`. Import direction is
`memory_regen → harness_lint`, adding zero new edges (D-18: `inject.py:15` already imported
`parse_frontmatter` from there).

## Decisions honored — verified, not assumed

- **D-14 (share L1–L4 only):** L5 (`status == "active"`) **stays** in `inject.py:98`. `agreements.py`
  mentions active-status only in a docstring. This is what keeps D-01's `status ∈ {active,retired}`
  rule enforceable — a `status: pending` typo reaches the lint instead of being filtered out first.
- **D-17 (gate widening in the SAME task):** `test_inject_determinism.py` now loops the wall-clock
  scan over **both** `tools/memory_regen/inject.py` and `tools/harness_lint/agreements.py`, and
  `test_negative_control_wallclock_scan_flags_planted_token` proves the scan actually bites. Without
  this the extraction would have moved code out from under a live gate with no test going red.
- **D-05/D-18:** one shared predicate, not two hand-kept copies. Fixture corpus relocated to
  `harness_lint/tests/conftest.py` with `memory_regen` re-exporting it (cross-member conftest is not
  visible; duplicating would have reintroduced the drift D-05 forbids).
- **D-06:** non-recursive `glob`, no symlink follow, confined.

## Verification

`uv run pytest tools/harness_lint tools/memory_regen -q` → 0 failed. Byte-identity determinism and
the ~4000-char budget both still green post-extraction.
