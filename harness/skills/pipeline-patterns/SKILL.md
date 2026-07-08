---
name: pipeline-patterns
description: >-
  Use when reasoning about pipeline run scenarios or carryover/state — how equipment-progress
  storage, progress keys, and carryover shapes flow between runs. Covers the live/rework/catchup
  scenario patterns from the state contract and the carryover discipline that keeps incremental
  runs equivalent to a full reprocess.
---

# pipeline-patterns

How the scheduler/collector pipeline reasons about state across runs. The state contract
(`contracts/state/equipment-progress.yaml` + schema) defines the storage, progress, and carryover
shapes; this skill is the map of the scenarios that consume them.

## State shape

- **storage** — where progress lives (`type`, `role`).
- **progress** — the resumption cursor: `keys` (identity of a unit of work) + `fields` (what
  advances).
- **carryover** — state that must survive from one run into the next: `keys`, `fields`, and a
  `note`. Carryover is the correctness linchpin — dropping it silently makes an incremental run
  diverge from a full reprocess.

## Scenario patterns (parserimprove)

- **live** — steady-state incremental: process new events past the last progress cursor; carryover
  seeds the boundary so the first new event has its predecessor context.
- **rework** — reprocess a bounded window (a correction landed): the window is re-run and its
  output must match what a clean full run would produce for that window.
- **catchup** — a backlog after a gap: process forward from a stale cursor; carryover must be
  reconstructed for the gap boundary, not assumed fresh.

The equivalence discipline: **an incremental run (live/rework/catchup) must be golden-equivalent to
a full reprocess** over the same span. Carryover exists so that equivalence holds at run
boundaries. Verify it with the golden runner (see the golden-testing skill).

## Seeds are placeholders

The state model is seeded (CONTRACT-01) — `TBD` values are examples, the real carryover/state model
is Out of Scope. The plumbing (schema + gate) is what is seeded here.

## Deeper reference

Keep a per-scenario boundary walkthrough under `references/`. See `contracts/state/`.
