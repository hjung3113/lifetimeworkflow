# Phase 47 — Deferred Items

Out-of-scope discoveries logged during execution (not fixed by the discovering plan, per the
executor's scope-boundary rule: only auto-fix issues directly caused by the current task's own
changes).

## Plan 47-03

- **`tools/harness_lint/tests/test_core_no_example_dep.py::test_core_has_no_example_dependency`
  fails at baseline (pre-existing, introduced by Plan 47-02's commit `2fb246f`).**
  `tools/memory_regen/tests/__snapshots__/test_package_facts.ambr` — the committed syrupy
  snapshot of `render(build_facts())` over the real tree — contains literal `examples/log-parser/
  ...` manifest paths (4 real `.csproj`/`pyproject.toml` packages under the example instance),
  which trips the GEN-04 core-plane `examples/` path-token scanner. Verified pre-existing by
  temporarily moving all three of this plan's new test files aside and re-running
  `uv run pytest tools/harness_lint -q`: the same single failure reproduces on the unmodified
  Plan-47-02 baseline (266 passed, 1 failed — identical offender set).
  Not fixed here: it is unrelated to Plan 47-03's `effective_packages()` work (`tools/harness_
  config/loader.py`, `tools/harness_lint/tests/test_package_facts_override.py`,
  `examples/log-parser/tests/test_package_facts_override_instance.py`), all of which pass clean
  and introduce zero new `examples/` literals under `tools/`, `harness/`, `libs/` (confirmed via
  `grep -rn "examples/" tools/harness_config tools/harness_lint/tests/test_package_facts_override.py`
  → zero hits).
  Likely fix (future plan): either (a) exempt `tools/memory_regen/tests/__snapshots__/*.ambr`
  files from the GEN-04 scanner (committed-derived test snapshots, not source dependency), or
  (b) have the `package_facts.py` generator/its snapshot fixture scrub `examples/` package rows
  before the guard runs. Left as a decision for whoever picks this up — outside 47-03's boundary
  (report-only phase, +0 gates/CI/commands).
