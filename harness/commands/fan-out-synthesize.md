---
description: >-
  Use when a task spans a large surface that would balloon a single context — routes to the
  orchestrator to decompose the work, fan out N read-only workers, recover schema-bounded
  citation-bearing summaries, and synthesize them without re-reading the raw files. Invoke for wide
  reconnaissance a human or the conductor should cover once, cheaply.
agent: orchestrator
subtask: true
---

# /fan-out-synthesize — decompose → dispatch N → recover → synthesize

The entry point for context-economy fan-out. It carries no shell of its own — dispatch is the
runtime's native subtask affordance, not a script — so this command simply hands the workflow to the
conductor and points at the reusable procedure and its return contract.

## The procedure

Follow the **`fan-out-synthesize`** skill as the named procedure: decompose the surface into N
independent analysis units, dispatch one read-only `explorer` worker per unit via the runtime's
native `task`/`Task` affordance, recover each worker's compact return, and synthesize the returns
into a single answer. There is no bespoke dispatch engine and no new persona — the skill is the whole
recipe.

## The return contract

Each worker must return a schema-bounded, citation-bearing summary conforming to
`references/fan-out-return.schema.json` (co-located with the skill): a `unit` plus `claims`, where
every claim is a terse assertion — never a pasted file excerpt — backed by path+line citations. That
bound is what keeps the fan-out from re-inflating the conductor's context.

## Who runs it

The **orchestrator** owns this workflow: it decomposes the request, dispatches the read-only workers,
recovers their compact returns, and synthesizes them without re-opening the raw files it delegated
away. The synthesized result is an ephemeral runtime value — it is not committed and not CI-gated.
