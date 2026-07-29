---
phase: 35-carried-debt-dispositions-v2-4-b
plan: 02
subsystem: docs-guard / contract-graph impact
tags: [DEBT-03, IN-03, purity, determinism, batch-entry-point]
requires:
  - tools/contract_graph/{compile,query}.py
  - tools/harness_config/loader.py::effective_relationships
provides:
  - tools/docs_guard/impact.py::impact_map -- pure batch entry point, one compile per report
  - tools/docs_guard/impact.py::_ids_for -- the traversal shared by both entry points
affects:
  - tools/docs_guard/cli.py (main + render)
  - tools/memory_regen/docs_staleness.py::rows
  - tools/docs_guard/tests/test_report.py (the degradation test now patches impact_map)
tech-stack:
  added: []
  patterns:
    - "batch entry point instead of memoization, when the expensive setup is shared across a known-up-front input set"
    - "count-the-live-reads regression test, for a defect the output cannot witness"
decisions:
  - "REJECTED memoizing inside impact_ids: mutable state in a module whose opening line advertises purity, and cfg is an unhashable dict so the memo has no sound key."
  - "REJECTED widening impact_ids's signature: ripples into cli, docs_staleness.rows and three test modules to buy nothing a second name does not."
  - "CHOSEN a new pure impact_map(bindings, cfg). Both call sites already built a {binding id: ids} mapping, so the batch shape is what they were asking for."
  - "Both rejections are recorded IN THE DOCSTRING, not only here -- the reader who reaches for a cache must meet the reason at the site."
metrics:
  tasks: 4
  commits: 1
  tests_added: 6
---

# Phase 35 Plan 02: Compile the Contract Graph Once Per Report

28 IN-03 closed. The report is byte-identical; the repeated work is gone; the decision that kept it
open for three carries is recorded at the call site rather than in a planning file.

## What Landed

| Task | Deliverable | Commit |
|------|-------------|--------|
| 1-4 | `impact_map` + both call sites converted + 6 regression tests | `8cb8458` |

## The Sites — one line number in the brief was wrong

Checked before being trusted:

| Claimed | Actual |
|---|---|
| `tools/docs_guard/cli.py:233` (comprehension) | **correct** |
| `tools/docs_guard/docs_staleness.py:100` (loop) | **path wrong** — the module is `tools/memory_regen/docs_staleness.py`; line 100 is right. Its placement under `memory_regen` is deliberate and documented (`docs_staleness.py:5-11`, D-06/D-10). |

A **third** site the audit did not name: `cli.py:174`, `render`'s no-impact-passed fallback, same
shape. Converted with the same change.

## The Decision

The residual framed this as a binary — change `impact.py`'s public signature, or add cached state to
a module whose docstring makes a point of being pure. Both horns are genuinely bad, and the binary
is false.

**Rejected — a cache.** It contradicts `impact.py:3` ("A pure helper: no filesystem writes, no CLI,
no exit codes"), which `test_module_performs_no_filesystem_write` exists to pin. It also has no
sound key: `cfg` is a `dict` and therefore unhashable, so a memo would either be keyed on nothing
(and answer the wrong `cfg`) or require a hand-rolled canonical serialization of the config — real
machinery, to avoid re-reading a file.

**Rejected — a signature change.** `impact_ids(source_paths, cfg)` would have to grow a
pre-compiled-graph parameter, rippling into `cli` (two sites), `docs_staleness.rows`, and the test
modules, to buy nothing a second name does not.

**Chosen — a new pure batch entry point, `impact_map(bindings, cfg)`.** It compiles once and returns
`{binding id: [ids]}`, which is *exactly what both call sites were already constructing by hand*.
`impact_ids` keeps its signature and behaviour byte-for-byte; the traversal moved to a private
`_ids_for(paths, relationships, graph)` so the two entry points cannot drift apart, and the live
reads moved to `_compile(cfg)`.

Both rejections are written into the `impact_map` docstring. A planning file is not where a future
maintainer reaching for `functools.cache` will look.

## Determinism — proven, not asserted

| | sha256 |
|---|---|
| `python -m tools.docs_guard` **stdout**, before and after | `70247c1b4fb0e8a3079aca95724d4f15ca18f8fd2de6bff9bfad985f24153764` (identical) |
| **stderr**, before and after | `e3b0c442…7852b855` — the empty-input digest; stderr is empty |
| exit code | `0` both sides |

`diff` of both streams is empty.

## The regression tests, and why they count calls

A per-binding loop renders the **identical report**. The defect was never a wrong answer, only
repeated work — so no assertion about report content can fail under the regression, and an
output-only test would pass under exactly the thing it exists to catch. The witness has to be the
number of live reads.

Six tests, in `test_impact.py` and `test_report.py`:

| Test | What breaks it |
|---|---|
| `test_impact_map_equals_a_per_binding_impact_ids_loop` | the batch answer diverging from the loop, including the EMPTY entries |
| `test_impact_map_compiles_the_graph_exactly_once` | a regression to per-binding compiling (3 bindings, asserts exactly 1 `compile_graph` and 1 `effective_relationships`) |
| `test_impact_map_with_no_bindings_compiles_nothing` | touching the config when there is nothing to answer for |
| `test_impact_map_holds_no_state_between_calls` | **a cfg-blind cache** — a `CHAIN_CFG` call, a `CYCLE_CFG` call, then `CHAIN_CFG` again |
| `test_report_compiles_the_graph_once_for_many_bindings` | the same regression at the CLI level, through `main` |
| `test_report_text_is_unchanged_by_the_batch_impact_path` | any character of rendered output moving between the batch and loop paths |

## One improvement beyond the brief, recorded so it is not mistaken for scope creep

`docs_staleness.rows` filtered bindings *inside* its loop, so it compiled once per **registered**
binding even when none qualified. Filtering to the qualifying set before building the map makes a
clean report compile the graph **zero** times. Same output; the ordering just stopped being
wasteful.

## Ripple

`test_report.py::test_config_error_in_impact_cannot_escape_the_exit_contract` patched
`cli.impact_ids` to prove the 0/1/3 exit contract survives a broken graph config. `cli` no longer
calls that name, so the patch now targets `cli.impact_map` — the call site that can actually raise —
and its docstring was corrected to say `main()` calls it once per report rather than `render()`
calling it per binding. Recorded rather than quietly rewritten: had it been left alone it would have
failed with `AttributeError`, and it did, which is how it was caught.

## Verification

| Check | Result |
|---|---|
| `uv run pytest -q` | **1506 passed**, 8 snapshots passed |
| `uv run python -m tools.contract_drift.drift` | `contract-drift: OK — live manifest matches the committed baseline`, exit 0 |
| `uv run python -m tools.docs_guard` | exit 0, output byte-identical to baseline |
| `uv run ruff check` / `format --check` on the six touched files | clean |
| `uv.lock` | unchanged (no package added) |

## Residuals

None. The remaining ruff findings under `tools/memory_regen/` (`inject.py`, `repo_map.py`,
`test_agents_md.py`, `test_inject_determinism.py`, `test_pointer_index.py`,
`test_inject_assembler.py`) are **pre-existing**, in files this plan did not modify, and belong to
DEBT-01 / Phase 34 — which is executing concurrently. Touching them here would collide.
