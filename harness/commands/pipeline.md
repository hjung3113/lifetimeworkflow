---
description: >-
  Use when you need to trace or visualize the pipeline dataflow and find the owning component agent —
  deterministically renders the declared [[components]]/[pipeline] topology (stage list + edge chain)
  from tools.harness_config and resolves each stage to its component agent file. Invoke to see the
  end-to-end flow or to check which stage owns a contract; there is no live runtime.
agent: orchestrator
subtask: true
---

# /pipeline — render the declared topology dataflow (no live runtime)

The runtime-independent way to see how work flows through the harness. This command **renders
declared config** — the `[[components]]`/`[pipeline]` slot read via `tools.harness_config` — into a
stage list, an edge chain, and a stage→agent resolution. It executes **nothing**: a trace here is a
deterministic read of the topology data, not a run of the pipeline (RESEARCH Open Q#4).

Core renders the generic default; an instance renders its own topology by pointing `load_project`
at its overlay path.

## 1. Load the active topology

```python
from tools.harness_config import components, pipeline, load_project

# core default (generic source/sink line):
comps = components()
edges = pipeline()["edges"]

# instance overlay — pass the instance config path:
cfg = load_project("<instance>/project.toml")
comps = components(cfg)
edges = pipeline(cfg)["edges"]
```

Both helpers are raw passthrough; the topology consistency gate
(`tools/harness_lint/tests/test_pipeline_config.py`) owns well-formedness, so this render trusts the
declared data as-is.

## 2. Print each component as a stage

Sort `comps` by `stage` and print one line per component:

```
stage <stage>: <id> (<language>) consumes=[<consumes...>] produces=[<produces...>]
```

For the core default this reads:

```
stage 1: source (python) consumes=[] produces=[greeting]
stage 2: sink (python) consumes=[greeting] produces=[]
```

## 3. Print the edge chain (the dataflow)

Walk `edges` in order and print each directed hop with the contract that crosses it:

```
<from> -> <to> (<contract>)
```

For the core default:

```
source -> sink (greeting)
```

Each edge is a `{from, to, contract}` — a request flows from `from` to `to` carrying exactly that
one contract. Chain them tail-to-head to see the full path from entry stage to terminal sink.

## 4. Resolve each stage to its owning component agent

Each stage `id` is owned by a component agent derived from
`harness/agents/templates/component-engineer.md`, living in the active instance's `agents/`
directory (declared by `harness/project.toml` `[instance] root`) as `<id>.md` — the derived agent's
`name` equals the component `id` (the `-engineer` suffix names the *template*, not the derived
per-component agents). For every component:

1. Compute the expected agent path `<instance-root>/agents/<id>.md`.
2. Report `stage <id> -> <id>.md` when it exists.
3. **Flag any stage whose agent file is missing** — a stage with no bound owner is a topology gap
   (`stage <id>: NO OWNING AGENT (<id>.md not found)`).

The generic core default carries no derived instance agents, so on the core config every stage is
reported as an unbound gap by design — the concrete owners come from the instance overlay.

## 5. Render the general (branching / cyclic) graph as an indented tree

Steps 2–3 are the render for a topology that IS a single chain — every stage has fan-out and fan-in
of exactly 1. Their example blocks above are the canonical linear output and are **unchanged**. When
the declared topology is **non-linear** (a stage fans out to several dependents, several stages fan
in to one, disconnected sub-graphs, or a legal cycle), render an **additional** view: the compiled
contract graph as an **indented tree** (D-01).

```python
from tools.contract_graph import compile_graph

graph = compile_graph()          # or compile_graph(load_project("<instance>/project.toml"))
adjacency = graph["adjacency"]   # authority -> sorted[dependents]
```

Render rules:

1. **Roots.** Start at each **authority with no incoming edge** (an authority that never appears as
   another authority's dependent), in sorted order. For a fully cyclic graph that has **no** such
   root, start at the lexicographically-first authority so the render is still deterministic.
2. **Indent one level per hop.** Print each node, then recurse into its sorted `adjacency` dependents
   one indentation level deeper — authority above, dependents nested beneath it.
3. **Cycle marker (never recurse twice).** Track the visited set on the current root-to-node path.
   If a dependent is already on that path, print it as a terminal `(cycle -> <node>)` marker
   **instead of** recursing into it again — the exact visited-set-before-recurse discipline
   `tools.contract_graph.query.transitive` uses, so a legal cycle terminates rather than looping.

This tree view is the human-facing surface for branch/fan-in/cycle topologies; the linear
stage-list/edge-chain steps 2–3 remain the render whenever the graph is a single chain.

## Notes

- **No execution.** This is a render of declared config; it never spawns a stage or runs any
  stage implementation. To reason about the flow in prose, read `harness/skills/pipeline-map/SKILL.md`.
- **Read-only.** The command touches neither the constitution plane nor `.memory/state/`.
- **Core stays neutral.** Any example here uses the generic `source`/`sink` ids — never
  instance/domain component names.
