---
name: pipeline-map
description: >-
  Use when you need to trace a request across the pipeline dataflow, see which stage produces or
  consumes a given contract, or find the component agent that owns a stage — reads the declared
  [[components]]/[pipeline] topology via tools.harness_config. Consult when routing by stage instead
  of by language, or when an edge's contract does not line up end to end.
---

# pipeline-map

How work flows through the harness as a **map instead of a guess**. The topology is declared data,
not runtime state: a set of `[[components]]` stages joined by `[pipeline]` edges, each edge carrying
one contract. This skill teaches how to read that slot, follow a request from stage to stage, and
resolve any stage to the component agent that owns it. There is **no live execution** here — a trace
is a deterministic read of declared config.

## The topology slot

The declared topology lives in `harness/project.toml` and is read through
`tools.harness_config`. The core ships a generic default (a `source` → `sink` line); an instance
overlay supplies its own concrete stages by passing its config path to `load_project(...)`.

Two shapes matter:

- **`[[components]]`** — one table per stage. Fields:
  - `id` — the stage's unique name (the routing key).
  - `stage` — its ordinal position in the flow (1-based).
  - `language` — which declared `[[languages]]` toolchain implements it.
  - `produces` — the contracts this stage emits (list).
  - `consumes` — the contracts this stage requires as input (list).
- **`[pipeline]`** — the wiring. `edges` is a list of `{from, to, contract}`: a directed hop from
  one component `id` to another, naming the single contract that crosses that boundary.

An edge is well-formed only when both endpoints are declared components AND its `contract` appears
in `from.produces` and in `to.consumes`. That end-to-end match is what makes the dataflow
traceable; the consistency gate (`tools/harness_lint/tests/test_pipeline_config.py`) fails loud when
it breaks.

## Reading it via the loader

```python
from tools.harness_config import components, pipeline, load_project

# core default:
comps = components()          # -> list[dict] with id/stage/language/produces/consumes
edges = pipeline()["edges"]   # -> list[{from, to, contract}]

# instance overlay:
cfg = load_project("path/to/instance/project.toml")
comps = components(cfg)
edges = pipeline(cfg)["edges"]
```

Both helpers are raw passthrough — they return the declared tables unchanged. No enforcement lives
in the loader; the gate owns well-formedness.

## Tracing a request across stages

Follow the flow deterministically, sorting components by `stage`:

1. **Find the entry.** The first stage (lowest `stage`, or the component that appears only as an
   edge `from` and never a `to`) is where a request originates.
2. **Walk the edges.** From the current component `id`, find each edge whose `from` equals it. The
   edge's `contract` is what crosses the boundary; `to` is the next stage. Repeat until you reach a
   component that is never an edge `from` (the terminal sink).
3. **Read the contract at each hop.** The edge names one contract — that is the exact shape handed
   from producer to consumer. To know its fields, open the matching schema under `contracts/`
   (lazy-load: only the contract on the hop you care about).

To answer "which stage handles contract X?": scan `produces` for the emitter and `consumes` for the
receiver — the edge whose `contract == X` names both.

## Rendering non-linear graphs

A single-chain topology (every stage fan-out and fan-in = 1) reads perfectly as the flat stage
list plus edge chain above. But the declared graph can be **non-linear** — one stage fanning out to
several dependents, several stages fanning in to one, disconnected sub-graphs, or a legal cycle. For
those, render the compiled contract graph as an **indented tree** (D-01) instead of a flat chain:

- Compile the graph with `tools.contract_graph.compile_graph` and read its `adjacency` map
  (authority → sorted dependents).
- **Root** at each authority with no incoming edge, in sorted order; for a fully cyclic graph with no
  such root, start at the lexicographically-first authority so the render stays deterministic.
- **Indent one level per hop** — an authority sits above its dependents, each dependent nested one
  level deeper, recursing along the sorted `adjacency` edges.
- **Terminate a cycle** with an explicit `(cycle -> <node>)` marker: track the visited set on the
  current root-to-node PATH only (path-local — NOT a single global set, which would collapse legal
  diamonds/fan-in) and, when a dependent is already on that path, print the marker instead of
  recursing into it again, so a legal cycle never loops. This path-local rule is stricter than
  `tools.contract_graph.query.transitive`'s global visited set (that query only collects the
  reachable id set, not a tree).

`/pipeline` (see **Related**) is the render entry point that prints this tree; use the flat stage
list/edge chain only when the graph is a single chain.

## Resolving a stage to its owning component agent

Each `[[components]]` stage is implemented by a **component agent** derived from the neutral
template `harness/agents/templates/component-engineer.md`. The derived agent lives in the active
instance's own `agents/` directory (the instance root is declared by `harness/project.toml`
`[instance] root`) as `<id>.md` — the derived agent's `name` equals the component `id` (the
`-engineer` suffix names the *template*, not the derived per-component agents).

To find the owner of a stage:

1. Take the component `id`.
2. Look for `<id>.md` under the instance's `agents/` directory.
3. If it is missing, the stage has no bound owner — that is a gap to report (the `/pipeline` command
   flags exactly this).

Routing by stage (not by language) means: identify the stage a request belongs to from the
contract it carries, then dispatch to that stage's `<id>` agent.

## Reasoning from the map

- **"Where does this contract come from?"** → the component whose `produces` lists it.
- **"What breaks if I change this edge's contract?"** → the `from` producer and the `to` consumer
  both, plus the `contracts/` schema — change all together or the gate goes red.
- **"Who do I route this to?"** → resolve the stage `id` → `<id>.md` in the instance.
- **"Is the flow complete?"** → every non-terminal component is some edge's `from`; every
  non-entry component is some edge's `to`. A dangling stage is a topology gap.

## Related

- `harness/commands/pipeline.md` — the `/pipeline` command renders this trace deterministically.
- `harness/commands/component.md` + `harness/agents/templates/component-engineer.md` — how a stage's
  owning agent is derived and registered.
- `harness/skills/two-plane-memory/SKILL.md` — the config slot is constitution-plane data, not
  derived state.
