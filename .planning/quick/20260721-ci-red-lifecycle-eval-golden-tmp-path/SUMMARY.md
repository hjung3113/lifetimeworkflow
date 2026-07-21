---
quick_id: 260721-cy3
slug: ci-red-lifecycle-eval-golden-tmp-path
date: 2026-07-21
status: complete
commits:
  - 934770e  # fix(quick): put repo root on sys.path for isolated lifecycle_eval pytest run
  - 26b88df  # fix(quick): decide toy-converter path confinement on real paths, not spellings
  - 933291b  # chore(quick): ignore instance golden .received baselines, not just the root tree
files_modified:
  - tools/lifecycle_eval/tests/conftest.py
  - examples/log-parser/components/toy-converter/Program.cs
  - .gitignore
---

# Quick Summary: the two CI reds from the v2.3 audit are closed

Both defects were recorded in `.planning/v2.3-MILESTONE-AUDIT.md` (`gaps.integration`) and
deliberately left unrepaired by the Phase 29 closeout, per T-29-21 — a closeout that repairs on the
way past reports a state that never existed. They are repaired here as their own task, so the
audit's recorded state stays true and the repair carries its own evidence.

Neither was a Phase 28/29 regression; both predate this milestone.

> **Authorship note.** This SUMMARY was written by the orchestrator, not by the executor that made
> the fixes — the executor went idle without producing one. Every number below was re-run and
> observed directly rather than copied from an executor report.

## Fix 1 — `lifecycle-eval` CI job step 2 no longer errors at collection

`tools/lifecycle_eval/tests/conftest.py` added, mirroring `tools/harness_lint/tests/conftest.py:20-23`:
`parents[3]` repo-root resolve, inserted only if absent.

**RED, before the fix** — running the exact `ci.yml:194` command:

```
tools/lifecycle_eval/tests/test_runner.py:8: in <module>
    from tools.lifecycle_eval.runner import FIXTURES, LifecycleEvalError, evaluate, load_fixtures, verify_negative_fixtures
E   ModuleNotFoundError: No module named 'tools'
=========================== short test summary info ============================
ERROR tools/lifecycle_eval/tests/test_runner.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

**GREEN, after** — `uv run pytest tools/lifecycle_eval` → **3 passed in 12.89s**, exit 0.

The blind spot worth naming: under the FULL suite this module always imported fine, because a
sibling member's conftest had already inserted the repo root by the time it was collected. Only the
isolated command — the one CI actually runs — failed. Same class as the rest of this milestone's
findings: green under one invocation, red under the one that matters.

## Fix 2 — `IsConfined` decides on real paths, not spellings

`examples/log-parser/components/toy-converter/Program.cs` — the confinement check compared paths
with `StringComparison.Ordinal`. On macOS `/var` is a symlink to `/private/var`, so pytest's
`tmp_path` (`/private/var/folders/...`) and .NET's `Path.GetTempPath()` (`/var/folders/...`) are two
spellings of one directory, and the Ordinal compare falsely tripped. Both sides are now resolved to
their real paths before comparison.

The guard was **not** weakened — canonicalization, not relaxation; a genuine escape is still
refused.

This is Phase 27.1's CR-01 lesson applied to the instance side: a confinement check that compares
raw strings is bypassable — or, as here, falsely trippable — by a spelling.

**Observed, not assumed:** the .NET toolchain WAS available and the toy converter actually ran.
`uv run pytest examples/log-parser/tests` → **14 passed in 4.11s**, where the audit recorded
2 failed / 10 passed with `toy-converter exited 3: path confinement violation`.

## Deviation — `.gitignore` (commit `933291b`), outside the plan's declared `files_modified`

Direct fallout of fix 2: the instance golden tests now actually execute on this host for the first
time, so they emit `baseline.received.tsv` artifacts that were previously never produced, and those
dirtied the working tree.

The ignore rule was root-anchored (`golden/**/baseline.received.tsv`), covering only the core tree.
It is now unanchored (`**/golden/**/baseline.received.tsv`) so an instance's own golden tree
(`examples/<name>/golden/`) is covered too.

**Confirmed it does not over-reach:** the change widens the ignore for `.received` only.
`.verified` baselines are constitution-plane and remain tracked — verified with `git check-ignore`
against the live files:

```
tracked-ok: examples/log-parser/golden/value-regression/expected/baseline.verified.tsv
tracked-ok: examples/log-parser/golden/repr-only/expected/baseline.verified.tsv
```

`.received` → `.verified` promotion still runs only through `/golden-approve` (P9). Nothing about
the human gate changed.

## Gate numbers (all re-run and observed at `933291b`)

| Gate | Result |
|---|---|
| `uv run pytest tools/lifecycle_eval` (exact `ci.yml:194`) | **3 passed**, exit 0 |
| `uv run pytest examples/log-parser/tests` | **14 passed** |
| `uv run pytest -q` (full) | **1473 passed**, 8 snapshots |
| `python -m tools.contract_drift.drift` | OK — manifest matches baseline |
| `uv run pytest tools/harness_lint -q` (incl. GEN-04) | **316 passed** |
| `python -m tools.harness_emit` + `git status --porcelain` | clean |

Full suite held at 1473 — neither fix moved it, as required.

## Untouched

`contracts/`, `docs/adr/`, `golden/` baselines, `docs/.docs-review-ledger.toml` (human-only),
STATE/ROADMAP/REQUIREMENTS. No model identifier. GEN-04 core→example independence green — the
`Program.cs` change is instance-side, and nothing under `tools/`, `libs/`, or `harness/` gained an
`examples/` reference.

## Does not affect the outstanding human gates

The v2.3 ratifications are untouched and still outstanding: the hand-authored review ledger,
ADR-0010's `proposed → accepted` flip, the eight seeded bindings, and the `HARNESS_DEV_BYPASS`
schema write from plan 28-01. `docs-guard` remains red by design until the ledger exists.
