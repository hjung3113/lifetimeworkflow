# Phase 6 — Deferred / Out-of-Scope Items

Items discovered during execution that are OUTSIDE the current plan's scope (per the executor
scope-boundary rule: only auto-fix issues directly caused by the current task's changes).

## From 06-01 execution (2026-07-09)

### GEN-04 guard failure owned by concurrent plan 06-02

- **Failing test:** `tools/harness_lint/tests/test_core_no_example_dep.py::test_core_has_no_example_dependency`
- **Offender:** `tools/contract_drift/tests/test_cli_flags.py:49` —
  `schema = contracts / "state" / "equipment-progress.schema.json"` carries the GEN-05 prose
  token `equipment`, which the core→example guard flags as a domain-vocabulary leak in a
  core-plane (`tools/`) file.
- **Origin:** Introduced by 06-02 commit `39f57d0` (`test(06-02): add failing drift/hash CLI flag
  tests for example manifest`), interleaved on the shared branch AFTER 06-01's Task-1 commit.
  Not caused by any 06-01 change.
- **Why not fixed here:** Explicitly instructed to leave concurrent 06-02 files untouched; and the
  offending line is a `schema =` assignment, NOT a `harness/project.toml` instance-pointer line, so
  it is correctly OUTSIDE 06-01's key-scoped (`root|persona|test_paths`) + file-scoped
  (`harness/project.toml` only) exemption. Widening the guard to cover it would over-broaden GEN-04
  and defeat the negative control.
- **Resolution owner:** 06-02 — must decide whether its example-manifest CLI test should name the
  example schema by a non-triggering means, reference it out of the core `tools/` plane, or whether
  the guard's prose handling needs a 06-02-side adjustment.
- **Verification once resolved:** `uv run pytest` full non-example suite exits 0 (currently
  `412 passed, 1 failed`; `412 passed` with this single test deselected).
