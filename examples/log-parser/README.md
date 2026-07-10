# `log-parser` — the reference instance

The **semiconductor equipment event-log parser** domain seed for this harness template. It is the
instance the template was de-specialized from (ADR-0002): the domain-specific contracts, converter,
.NET normalize twin, and golden baselines that used to sit at the repo root now live here, under
`examples/log-parser/`, while the domain-neutral **harness core** stays at the root.

## What it is

A reverse-engineered semiconductor equipment-log pipeline, responsibility-separated across a
polyglot boundary:

- **.NET 10** parser/converter (CPU-bound) — `components/toy-converter/` + `libs/dotnet/`.
- **Python** scheduler/collector side — exercised through the core's `tools/golden_runner`.

The two communicate **only across process/file/DB boundaries** (A-model: CLI-spawn + exit codes),
never in-process. This instance exists to prove the harness's guarantees against a real domain.

## How it uses the core

| Core capability (stays at repo root) | How this instance consumes it |
|--------------------------------------|-------------------------------|
| `libs/python/normalize` — language-neutral §4.3–4.6 canonicalization core | The single normalizer for both sides; this instance adds **no** second normalizer. |
| `libs/normalize-fixtures` — shared `(raw, canonical)` corpus | Cross-validates this instance's `libs/dotnet` normalize twin against the Python core. |
| `tools/golden_runner` | Spawns `components/toy-converter` over the A-model boundary, normalizes both sides, diffs vs `.verified`. |
| `tools/contract_drift` + `contracts/.hashes/manifest.json` | Gates schema drift for this instance's `contracts/`. |
| `harness/project.toml` `[instance]` / `[[languages]]` | The active-instance slot that declares this instance's .NET 10 + Python/uv toolchains. |

The dependency is **one-directional**: this instance depends on the core; the core never depends on
it. That invariant is enforced on every test run by
`tools/harness_lint/tests/test_core_no_example_dep.py` (GEN-04).

## Layout

```txt
contracts/     log-specs/ (standard-log) · normalization/ (correction-rules) · reference-data/
               (equipment-master) · state/ (equipment-progress) · .hashes/manifest.json
components/    toy-converter/ — fixture-grade .NET converter
libs/dotnet/   Normalize + Normalize.Tests — the example's .NET language-side normalize twin
skills/        normalization-catalog · pipeline-patterns · dotnet-conventions — instance-owned skills
agents/        dotnet-engineer — the instance's .NET language persona
golden/        repr-only/ (representation-only diff → PASS) · value-regression/ (real diff → FAIL)
tests/         Python golden cases: repr-only, value-regression, recorded-output compare
```

This instance now owns its **domain skills** (`normalization-catalog`, `pipeline-patterns`) and its
**.NET language persona** (`dotnet-engineer`, plus the `dotnet-conventions` skill) — authored assets
relocated from the harness core during the Phase 5.5 authored-surface de-specialization, because they
are domain- or instance-language-specific rather than domain-neutral core.

## Status note — .NET egress deferred (BOOT-01)

This container has **no .NET 10 SDK** (its install hosts are egress-denied). `dotnet test` and the
live toy-converter spawn are therefore **gated-skipped**, and the polyglot golden comparison is
proven green via the **recorded-output twin** under `tests/recorded/`. A SKIP here is expected, not
a failure; the full loop closes once .NET 10 is installed (`tools/bootstrap/install.sh`).

## Adding your own instance instead

See `docs/explanation/template-and-instances.md` for the template↔instance split and a step-by-step
recipe for adding a new `examples/<name>/` instance (its own contracts, goldens, language twin,
manifest, and a `harness/project.toml` language set).
