---
name: context-budget
description: >-
  Use when deciding whether to fan out / delegate a task or work it inline — weighs the surface a
  task would pull into the current context against the room left to reason, and names the signals
  that tip the call to delegation via fan-out-synthesize versus keeping it inline. Consult before
  opening many files into one context.
---

# context-budget

Before you start reading, decide *where* the reading happens. Every task protects one invariant:
**a single context must not balloon.** The more raw material one agent pulls in, the less room it
has to reason and the sooner it forgets its early findings — so the delegate-vs-inline call is not a
matter of taste, it is budget discipline. This skill makes that call a named, repeatable step
instead of a habit: look at the surface first, then choose the cheaper place to spend context.

## The one invariant

Context is finite and non-renewable within a session. Reading is the dominant spend. A task whose
raw material would crowd out the reasoning space must be delegated so the *workers* absorb the
reading cost and the conductor stays lean — it synthesizes from compact returns rather than from the
files themselves. Working such a task inline trades away the very budget the answer needs.

## The decision the budget forces

| The task in front of you… | Spend context by… | Because |
|---|---|---|
| Touches many files / spans several independent units / would exceed one working context | **Delegate** — fan out via `fan-out-synthesize` | the workers read; the conductor holds only paths + claims |
| Fits comfortably in the room left — few files, one unit, a local edit | **Work inline** | delegation overhead buys nothing when the surface is already small |
| Is small now but its answer hinges on one thinly-cited claim | **Work inline, then delegate one narrow probe** | pull only the missing evidence, not the whole surface |

## Reading the signals

Delegate when **any** hold: the surface is many files or directories; the units are independent and
compose without overlap; ingesting it all would leave too little room to reason or would drop early
findings. Work inline when the surface is one unit, a handful of files, or a local change a single
pass resolves. When unsure, size the surface first (an `explorer` pass counts references cheaply)
rather than opening everything into the conductor's own context to find out.

## Related
- `harness/skills/fan-out-synthesize/SKILL.md` — the substrate this heuristic routes to when the
  call is "delegate": decompose → dispatch read-only workers → recover compact returns → synthesize.
- `/orient` — the read-order that surfaces this heuristic alongside the other decision skills.
