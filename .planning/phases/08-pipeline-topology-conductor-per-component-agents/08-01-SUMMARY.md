---
phase: 08-pipeline-topology-conductor-per-component-agents
plan: 01
subsystem: harness-core-config
tags: [pipeline-topology, harness_config, loader-passthrough, consistency-gate, PIPE-01, GEN-04]
requires:
  - harness/project.toml [[languages]] slot (GEN-03)
  - tools/harness_config loader + PEP 562 lazy re-export idiom
provides:
  - "Generic pipeline-topology DATA slot: [[components]] source/sink + [pipeline] one-edge default"
  - "loader.components() + loader.pipeline() raw passthrough helpers (package re-exported)"
  - "test_pipeline_config.py topology consistency gate (languages declared / ids unique / edges well-formed)"
affects:
  - Plan 08-04 (instance overlay supplies the concrete multi-component topology)
  - conductor routing / /pipeline trace (later plans read components()/pipeline())
tech-stack:
  added: []
  patterns:
    - "Clone the [[languages]] → loader.languages() → test_language_config.py triad verbatim for topology"
    - "Additive-passthrough loader idiom (list(cfg.get(...)) / dict(cfg.get(...))), no enforcement in loader"
    - "Banner-scoped (# BEGIN/END PIPE-01 topology) generic-only DATA block, GEN-04 domain-neutral"
key-files:
  created:
    - tools/harness_lint/tests/test_pipeline_config.py
  modified:
    - harness/project.toml
    - tools/harness_config/loader.py
    - tools/harness_config/__init__.py
    - tools/harness_config/tests/test_loader.py
decisions:
  - "Topology slot is GENERIC-ONLY (source/sink/sample-record) — concrete components deferred to instance overlay (Plan 04) to keep core GEN-04 green"
  - "Consistency (undeclared language / malformed edge) is enforced by the gate test, not the loader — loader stays pure passthrough mirroring languages()"
metrics:
  duration: 6min
  tasks: 2
  files: 5
  completed: 2026-07-10
---

# Phase 08 Plan 01: Generic Pipeline-Topology DATA Slot Summary

Established the PIPE-01 neutral-core mechanism: a generic `[[components]]` + `[pipeline]` topology
default in `harness/project.toml` (two-stage `source`→`sink` line carrying one `sample-record`
contract), `components()`/`pipeline()` passthrough helpers on the loader (lazily re-exported from the
package), and a fail-loud topology consistency gate — all domain-neutral, GEN-04 green.

## What Was Built

**Task 1 — topology slot + loader passthrough (`3623d8b`)**
- `harness/project.toml`: appended a `# BEGIN/END PIPE-01 topology` banner-scoped block with two
  `[[components]]` (`source` stage=1 produces `sample-record`; `sink` stage=2 consumes it, both
  `language="python"`) and a `[pipeline]` table with the single `source→sink` `sample-record` edge.
  Header names the two consumers (loader + gate); ids/labels are strictly generic.
- `tools/harness_config/loader.py`: added `components(cfg=None) -> list[dict]` and
  `pipeline(cfg=None) -> dict`, both `load_project()`-defaulting raw passthrough (no enforcement),
  mirroring `languages()`.
- `tools/harness_config/__init__.py`: added `components`/`pipeline` to `__all__` for the PEP 562
  lazy re-export.

**Task 2 — consistency gate + loader units (`70dc6e9`)**
- `tools/harness_lint/tests/test_pipeline_config.py` (new): `test_component_languages_are_declared`
  (every `component.language` ∈ declared `[[languages]].id`), `test_component_ids_unique`, and
  `test_pipeline_edges_are_well_formed` (endpoints declared + `contract` in from.produces AND
  to.consumes). Fails loud naming the offender.
- `tools/harness_config/tests/test_loader.py`: `test_components_passthrough` +
  `test_pipeline_passthrough`.

## Verification

- `uv run pytest tools/harness_lint tools/harness_config` → 174 passed (was 169; +3 gate +2 loader).
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` → 18 passed (GEN-04 green).
- `awk '/BEGIN PIPE-01 topology/,0' harness/project.toml | grep -Ei 'parser|converter|standard-log|equipment'` → no match.
- Full non-example suite: `uv run pytest` → **418 passed, 3 snapshots passed**.

## Deviations from Plan

None - plan executed exactly as written.

## must_haves Truth Check

- harness/project.toml declares a generic `[[components]]` + `[pipeline]` topology (source/sink/sample-record), zero log-parser specifics — YES.
- `loader.components()`/`loader.pipeline()` return the declared tables unchanged — YES.
- Topology consistency gate fails loud on undeclared language / malformed edge — YES (test_pipeline_config.py).
- GEN-04 core→example guard stays green — YES (18 passed).

## Anti-Sprawl

Adding `test_pipeline_config.py` trips no EXPECTED_* set — the harness_lint pinned sets
(`EXPECTED_PERSONAS`/`EXPECTED_GOLDEN_ADJACENT`/`EXPECTED_SKILLS`) enumerate artifacts, not test
modules. No expected-set update was required.

## Self-Check: PASSED

- FOUND: tools/harness_lint/tests/test_pipeline_config.py
- FOUND commit 3623d8b (Task 1)
- FOUND commit 70dc6e9 (Task 2)
