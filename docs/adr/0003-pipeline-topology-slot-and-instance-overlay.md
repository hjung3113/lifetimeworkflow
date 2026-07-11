# 3. Pipeline-Topology Slot and Instance Overlay

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-10
- **Deciders:** Phase 8 planning (Pipeline-Topology Conductor + Per-Component Agents, PIPE-01..06)
- **Supersedes:** —
- **Superseded by:** —
- **Complements:** [ADR-0002](0002-general-template-de-specialization.md) (general template de-specialization) — extends its core→instance split to the pipeline-topology dimension; **not** superseded.

## Context and Problem Statement

ADR-0002 re-scoped the repo into a domain-neutral **core** plus swappable **instances** under
`examples/`, enforcing the one-directional core→instance dependency with the GEN-04 guard
(`tools/harness_lint/tests/test_core_no_example_dep.py`). It located the active instance's
**languages/toolchains** as a pure-DATA slot (`[[languages]]` in `harness/project.toml`), read by a
thin loader and kept honest by a consistency gate — but it said nothing about the **pipeline
topology**: which components exist, what stage each occupies, and which edge contracts flow between
them.

Phase 8 evolves the agent model from per-**language** to pipeline-**aware**: the primary orchestrator
must route by pipeline **stage/component**, and each declared component may bind its own least-privilege
engineer. That requires the topology to be declared *somewhere* as data. The load-bearing question this
ADR records: **where does the concrete pipeline topology live** — the CONCRETE 4-component log-parser
chain (`parser→converter→scheduler→collector`) whose edges bind to **domain schema names**
(`standard-log`, `equipment-progress`) — given that GEN-04 flags those exact tokens anywhere under
`tools/`, `harness/`, `libs/`? Put the concrete topology in core and GEN-04 goes red; leave the
topology undeclared and the conductor has nothing to route against.

## Decision Drivers

- **GEN-04 must stay green — the primary driver.** Edge contracts bind to domain schema names
  (`standard-log`, `equipment-progress`) which the GEN-04 guard flags anywhere under `tools/`,
  `harness/`, `libs/`. The concrete topology **cannot** sit in core `harness/project.toml` without
  growing the guard's line-exemption surface and re-coupling core to a domain — the exact erosion
  ADR-0002 forbids. The only layout that holds GEN-04 green is keeping the concrete topology out of
  every scanned core root.
- The core must stay a **cloneable, domain-neutral template**: a downstream user adopts it for a
  *different* pipeline shape, so the core may declare only a generic *shape/default*, never the
  log-parser's concrete stages.
- The mechanism should **reuse the proven ADR-0002 triad** (pure-DATA TOML slot → thin `tomllib`
  loader passthrough → consistency-test SSOT), not invent a second config-reading path.
- The locked Phase-8 decision: **evolve the single primary `orchestrator` in place** — one primary,
  no new tier, no second `mode: primary` conductor (persona anti-sprawl, `EXPECTED_PERSONAS` stays 4).
- The language boundary is **process/file/DB only**: topology edges model **file/DB handoff
  contracts** between stages, never in-process object passing.

## Considered Options

1. **Concrete topology in core `harness/project.toml`, grow the GEN-04 exemption.** *Rejected:* the
   edge contracts name domain schemas (`standard-log`, `equipment-progress`) that GEN-04 flags; making
   them legal means widening the guard's line-exemption surface until the boundary no longer bites —
   re-coupling core to a single domain, the precise erosion ADR-0002 was written to prevent.
2. **Declare no topology; keep routing language-only.** *Rejected:* forecloses the phase goal (route
   by pipeline stage/component); the conductor would have no declared dataflow to trace and component
   agents nothing to bind to.
3. **Generic default in core + concrete topology as an instance overlay (chosen).** The core
   `harness/project.toml` carries only a **generic default** topology (`source→sink`, `sample-record`);
   the CONCRETE log-parser topology lives in a separate **`examples/log-parser/project.toml` overlay**
   under `examples/` (which GEN-04 never scans), read path-locally by the example test leg. One
   mechanism, two data files, GEN-04 green.

## Decision Outcome

**Chosen: Option 3 — pipeline-topology as a pure-DATA slot with a generic core default and a concrete
instance overlay**, with these locked decisions:

**(a) Topology is a pure-DATA slot cloned from the `[[languages]]` triad.** A `[[components]]`
(`id`/`stage`/`language`/`consumes`/`produces`) + `[pipeline]` (`edges` as `{from,to,contract}`)
table set is declared as data, read by `loader.components()`/`loader.pipeline()` as **pure passthrough**
(no enforcement in the loader), and kept honest by a **consistency gate**
(`tools/harness_lint/tests/test_pipeline_config.py`): every `component.language` ∈ declared
`[[languages]]`, component ids unique, and every edge `contract` present in the upstream `produces`
**and** the downstream `consumes`. This mirrors ADR-0002's GEN-03 language triad verbatim — "derived,
not hardcoded" is proven by a consistency assertion, not codegen.

**(b) Generic default in core; concrete topology in the instance overlay — because of GEN-04.** The
core `harness/project.toml` declares only a **GENERIC default** topology (a two-stage
`source→sink` line carrying one `sample-record` contract), with zero log-parser specifics. The
**CONCRETE per-instance topology** — the log-parser `parser(1)→converter(2)→scheduler(3)→collector(4)`
chain with its real domain edge contracts (`standard-log`, `equipment-progress`) — lives in a separate
**`examples/log-parser/project.toml` overlay**. This split is driven **primarily by GEN-04**: the
domain contract names are guard-flagged tokens under core roots, so keeping them under `examples/`
(never scanned by GEN-04) is the *only* layout that holds the core→example boundary green. The core
`[instance] root` stays `""`; the example test leg reads its overlay path-locally via
`load_project(examples/log-parser/project.toml)`, so no core assertion changes.

**(c) The conductor is the evolved single-primary orchestrator — no new tier.** Topology-awareness is
added **in place** to the existing `harness/agents/orchestrator.md` (`mode: primary`): a new
"trace the topology" intake step and stage/component routing rows. There is **no** second
`mode: primary` "conductor" persona — `EXPECTED_PERSONAS` stays the four enumerated core personas, and
the persona anti-sprawl gate (`test_agents.py`) is extended with a conductor-signal assertion proving
the routing role landed on the one primary. Per-component engineers are instantiated from a neutral,
anti-sprawl-exempt `harness/agents/templates/component-engineer.md` template into the instance's own
`agents/` — invisible to the core persona count.

**(d) Instance topology consistency runs only in the example leg.** The concrete-topology gate
(`examples/log-parser/tests/test_pipeline_topology.py`) lives under `examples/` — off the root
`testpaths = ["libs/python", "tools"]` — so it runs in the **example test leg**
(`uv run pytest examples/log-parser/tests`), not the core suite. The phase gate therefore requires
**both** legs green: the full core suite proves the generic slot + GEN-04 + persona/template gates,
and the example leg proves the concrete 4-component demo. This is the topology analogue of ADR-0002's
core-is-language-neutral posture: the neutral mechanism is core-tested, the domain instantiation is
instance-tested.

### Consequences

- **Good:** the core stays a domain-neutral, cloneable template (a downstream user swaps the overlay
  for a different pipeline shape); the concrete topology's domain names never touch a scanned core
  root, so GEN-04 stays green through the closeout; the topology reuses the proven `[[languages]]`
  triad rather than a new config path.
- **Good:** one primary persona, richer intake — the conductor routes by stage/component *and*
  language without a new tier; component engineers stay least-privilege (each component's language
  toolchain only) and instance-owned.
- **Neutral:** the topology is declared in **two** places (a generic core default + a concrete
  instance overlay); this is intentional — the core default is the shape a downstream instance
  overrides, not dead weight.
- **Bad / accepted:** a broken instance topology is invisible to the root `uv run pytest` (the example
  test is off `testpaths`), so the phase gate MUST run the example leg explicitly; the .NET-side
  component agents are authored markdown (the two example .NET golden-spawn cases stay
  egress-deferred / skipped locally per BOOT-01), not compiled — this ADR records authoring, not a
  live pipeline run.

## Links

- Complements [ADR-0002](0002-general-template-de-specialization.md) — general template de-specialization (not superseded).
- Generic slot: `harness/project.toml` (`[[components]]` + `[pipeline]`, PIPE-01). Instance overlay: `examples/log-parser/project.toml` (PIPE-04).
- Enforced by: `tools/harness_lint/tests/test_pipeline_config.py` (core consistency gate), `tools/harness_lint/tests/test_core_no_example_dep.py` (GEN-04), `tools/harness_lint/tests/test_agents.py` (persona anti-sprawl + conductor signal), `examples/log-parser/tests/test_pipeline_topology.py` (instance leg).
- Sources: `.planning/phases/08-pipeline-topology-conductor-per-component-agents/{08-RESEARCH.md (Open Question #1), 08-01-SUMMARY.md, 08-04-SUMMARY.md, 08-06-PLAN.md}`.
