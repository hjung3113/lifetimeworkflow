---
quick_id: 260721-cy3
slug: ci-red-lifecycle-eval-golden-tmp-path
date: 2026-07-21
type: quick
autonomous: true
files_modified:
  - tools/lifecycle_eval/tests/conftest.py
  - examples/log-parser/components/toy-converter/Program.cs
---

# Quick: close the two CI reds the v2.3 milestone audit found

Both were surfaced by `.planning/v2.3-MILESTONE-AUDIT.md` (`gaps.integration`) and deliberately
NOT repaired by the closeout — a closeout that repairs on the way past reports a state that never
existed (T-29-21). They are repaired here, as their own task, so the audit's recorded state stays
true and the fix has its own evidence.

Neither is a Phase 28/29 regression. Both predate this milestone's work.

## Fix 1 — `lifecycle-eval` CI job step 2 errors at collection

`.github/workflows/ci.yml:194` runs `uv run pytest tools/lifecycle_eval`. Reproduced:

```
tools/lifecycle_eval/tests/test_runner.py:8: in <module>
    from tools.lifecycle_eval.runner import FIXTURES, LifecycleEvalError, evaluate, load_fixtures, verify_negative_fixtures
E   ModuleNotFoundError: No module named 'tools'
=========================== short test summary info ============================
ERROR tools/lifecycle_eval/tests/test_runner.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

**Cause.** `tools/lifecycle_eval/tests/` is the only `tools/*` member's test dir carrying neither
`__init__.py` nor a `conftest.py` that inserts the repo root into `sys.path`. These are *virtual*
uv-workspace members — not pip-installed — so each member's tests must put the repo root on the
path themselves; `tools` is a namespace package (no `tools/__init__.py`), so the insert is what
makes `from tools.lifecycle_eval...` resolve.

**Why the full suite hides it.** Under `uv run pytest` (whole repo) a sibling member's conftest has
already inserted the repo root by the time this module is imported, so collection succeeds. Only
the isolated job command — the one CI actually runs — fails. That is the same class of blind spot
this milestone kept hitting: green under one invocation, red under the one that matters.

**Fix.** Add `tools/lifecycle_eval/tests/conftest.py` mirroring
`tools/harness_lint/tests/conftest.py:20-23` verbatim in shape: `parents[3]` repo-root resolve,
insert only if absent.

**RED gate.** `uv run pytest tools/lifecycle_eval` must fail with the `ModuleNotFoundError` above
BEFORE the conftest lands, and pass after. Run it plainly and read the output — an inverted `!`
gate exits 0 on a collection error, which is exactly what is being fixed here.

## Fix 2 — `golden` job step 2 red on macOS only

`uv run pytest examples/log-parser/tests` → 2 failed, 10 passed, `toy-converter exited 3: path
confinement violation`.

**Cause.** `IsConfined` (`examples/log-parser/components/toy-converter/Program.cs:163-183`) compares
paths with `StringComparison.Ordinal`. On macOS pytest's `tmp_path` realpaths to
`/private/var/folders/...` while .NET's `Path.GetTempPath()` returns the `/var/folders/...`
spelling of the same directory — `/var` is a symlink to `/private/var`. Ordinal comparison of two
spellings of one path fails. On the job's `ubuntu-latest` runner both are `/tmp`, so the comparison
holds and CI is green.

**Fix.** Resolve both sides to their real paths before comparing, so the guard decides on the
canonical path rather than on a spelling. This is the same lesson as Phase 27.1's CR-01
(`./contracts/x` vs `contracts/x` vs `CONTRACTS/x`): a confinement check that compares raw strings
is bypassable — or, as here, falsely trippable — by a spelling.

**Do not weaken the guard.** Confinement must still refuse a genuine escape; the fix is
canonicalization, not relaxation. Keep a case that proves a real escape is still refused.

**Constraint.** `examples/log-parser/` is the reference INSTANCE, not the core — GEN-04 core→example
independence must stay green (`tools/harness_lint/tests/test_core_no_example_dep.py`). This fix
touches only the instance side, which is legal.

**Gate.** The .NET SDK may be absent in this environment; if so, the golden job's step 2 cannot be
executed here. Record that honestly rather than claiming a pass — the audit's own posture.

## Acceptance

- `uv run pytest tools/lifecycle_eval` exits 0 (the exact ci.yml:194 command).
- The `IsConfined` comparison is canonical-path based, with the escape case still refused.
- Full suite stays at **1473 passed**; `contract_drift` OK; `uv run pytest tools/harness_lint -q`
  green (GEN-04 included); `python -m tools.harness_emit` then `git status --porcelain` clean.
- No constitution-plane edit; no model identifier; §4.3-4.6 byte hygiene.
