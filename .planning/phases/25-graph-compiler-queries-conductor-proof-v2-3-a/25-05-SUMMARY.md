---
phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
plan: 05
subsystem: constitution-plane
tags: [adr, topology, contract-graph, human-ratification, checkpoint, TOPO-07]
status: checkpoint-reached

# Dependency graph
requires:
  - phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
    plan: 01
    provides: "compile_graph resolution + 3 D-02 diagnostic slugs + WR-02 closure — the compiler model ADR-0009 records"
  - phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
    plan: 02
    provides: "direct/reverse/transitive {ids, paths} cycle-safe queries — the query semantics ADR-0009 records"
  - phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
    plan: 03
    provides: "D-01 indented-tree conductor render + linear byte-identity — the rendering contract ADR-0009 records"
  - phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
    plan: 04
    provides: "TOPO-07 proof fixtures + WR-01 fixture-vocabulary-constraint scan — the disposition ADR-0009 records"
provides:
  - "docs/adr/0009-contract-relationship-graph-model.md (Status: proposed) — the drafted human-ratifiable MADR record for the full Phase-25 graph model"
  - "docs/adr/README.md +1 index row for ADR-0009 (append-only, zero removed lines)"
affects: [TOPO-07, phase-25-closeout, phase-26-brownfield, phase-28-living-docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Machines gate, humans ratify: agent scaffolds Status: proposed; the checkpoint hands ratification to a human who flips proposed -> accepted"
    - "D-04 one-unit ADR: compiler + queries + conductor render recorded together, not as three separate single-topic records"

key-files:
  created:
    - docs/adr/0009-contract-relationship-graph-model.md
  modified:
    - docs/adr/README.md

key-decisions:
  - "ADR-0009 authored with Status: proposed — NOT self-ratified; Task 2 is a blocking human checkpoint (threat T-25-09, self-ratification = elevation of privilege)"
  - "Complements ADR-0002 (template de-specialization) + ADR-0003 (pipeline-topology slot); no Supersedes (net-new decision surface)"
  - "Authority-owned-contract resolution documented as produces-check with existence-only fallback (RESEARCH open-question 3, D-04 requires it recorded)"
  - "README index gets exactly +1 row for 0009; the pre-existing missing 0008 index row is out of scope (deferred, see below)"

requirements-completed: []
requirements-pending-ratification: [TOPO-07]

# Metrics
duration: ~15min
completed: pending-human-ratification
---

# Phase 25 Plan 05: ADR-0009 Contract-Relationship Graph Model (Checkpoint Reached)

**ADR-0009 authored as ONE ratified unit per D-04 — the record/graph model (compiler resolution + three diagnostic slugs), the affected-set query semantics (`direct`/`reverse`/`transitive`, `{ids, paths}`, cycle-safe), and the conductor rendering contract (D-01 indented tree + `(cycle -> <node>)` marker + linear byte-identity) — plus the WR-01 (deferred) / WR-02 (closed) dispositions. Drafted with `Status: proposed`; the phase closes only after a HUMAN ratifies (flips to `accepted`) via the constitution-plane path. The agent did NOT self-ratify.**

## Status: CHECKPOINT REACHED (awaiting human ratification)

Task 1 is complete and committed. Task 2 is a **blocking `checkpoint:human-verify`** — the ADR
must be human-ratified, never agent-self-approved (threat T-25-09, Elevation of Privilege). This
summary reflects the checkpoint-reached state; ratification is pending.

## What Was Built

**Task 1 — Scaffold ADR-0009 (`6b9c15c`)**
- `docs/adr/0009-contract-relationship-graph-model.md` created with `Status: proposed`, mirroring
  ADR-0008's exact section/header structure (`Status`/`Date`/`Deciders`/`Supersedes`/
  `Superseded by`/`Complements`, the "Ratified by human/CODEOWNERS on <date>" footer convention,
  MADR sections). `Complements:` links ADR-0002 and ADR-0003.
- **Decision Outcome records the full model as one unit (D-04):**
  1. **Record/graph model** — Phase-24 `relationship.schema.json` shape + additive `[contract_graph]`
     slot + `effective_relationships()` lowering/union (consumed, not re-implemented); this phase's
     `compile_graph()` endpoint resolution + adjacency; the **authority-owned-contract resolution as
     a produces-check with existence-only fallback**; the three D-02 slugs `unresolved-authority` /
     `dangling-endpoint` / `unknown-contract`; fan-in/fan-out/disconnected/cycle explicitly legal.
  2. **Affected-set query semantics** — D-03 `direct`/`reverse`/`transitive` returning `{ids, paths}`,
     cycle-safe via a visited-set, creating no task-evidence requirement and preloading no contract body.
  3. **Conductor rendering contract** — D-01 indented tree rooted at authorities with a
     `(cycle -> <node>)` terminal marker; the existing linear render stays byte-identical; no new
     command or persona (TOPO-06).
- **Dispositions recorded:** WR-01 (deferred, fixture-vocabulary-constrained, Plan-04 corpus scan is
  the enforcement) and WR-02 (closed, `ValueError` guard, Plan 01 Task 3) — so the decision trail is
  traceable from ADR to code.
- Links section points at the schema, `effective_relationships()`, `tools/contract_graph/`, the three
  conductor surfaces, and the proof fixtures.
- `docs/adr/README.md` gained exactly **one** new row referencing `0009-` (append-only, zero removed
  lines).

**Task 2 — Human ratification** — NOT PERFORMED BY THE AGENT. Blocking checkpoint returned to the
orchestrator for genuine human sign-off. Status remains `proposed`.

## Verification

- Task-1 automated gate: `test -f docs/adr/0009-*.md && grep -q unresolved-authority && grep -q
  transitive && grep -q cycle && grep -q 0009 docs/adr/README.md` → **GATE PASS**.
- README diff: `git diff --unified=0` shows **+1 line, 0 removed** (append-only honored).
- Status assertion: `grep -i status` → `- **Status:** proposed` (NOT accepted — no self-ratification).

## Deviations from Plan

### Deferred (out of scope)

**1. Pre-existing missing ADR-0008 index row in `docs/adr/README.md`**
- **Found during:** Task 1 (adding the 0009 row).
- **Issue:** The README index table jumped from 0007 to (now) 0009 — the accepted ADR-0008 row was
  never added to the index in its own plan.
- **Decision:** NOT fixed here. The plan's acceptance criterion is strict (`README gains exactly one
  new row referencing 0009-, line-count diff +1, zero removed lines`), and the missing 0008 row is a
  separate ADR's indexing gap on a CODEOWNERS-gated constitution-plane file — out of this plan's
  scope. Logged for a follow-up index-repair pass. Left the table strictly +1.

Otherwise none — Task 1 executed exactly as written.

## Checkpoint Details (for the orchestrator / human ratifier)

- **Type:** human-verify (blocking; NOT auto-approvable — ADR ratification)
- **Draft to review:** `docs/adr/0009-contract-relationship-graph-model.md`
- **How to verify:** Read the ADR in full; confirm it accurately reflects (1) the compiler's
  endpoint/contract resolution + three diagnostic slugs; (2) the query layer's `{ids, paths}` shape
  and cycle-safety; (3) the conductor's indented-tree render + linear byte-identity; (4) the WR-01
  (deferred) / WR-02 (closed) dispositions. Confirm `docs/adr/README.md` gained exactly one row and
  no existing row was altered.
- **Resume signal:** Reply "ratified" / "accepted" to flip `Status: proposed` -> `Status: accepted`
  (and stamp the two `<date>` placeholders in the Decision Outcome + Approval footer), or describe a
  correction needed before ratification.
- **On ratification, the continuation agent must also:** advance STATE.md plan counter, mark TOPO-07
  complete, update ROADMAP.md phase progress, and make the final metadata commit closing the phase.

## Threat Model

- **T-25-09 (Elevation of Privilege — self-ratification):** MITIGATED. The agent authored the ADR at
  `Status: proposed` and STOPPED at the blocking human checkpoint; it never set `Status: accepted`
  itself and did not use any dev-bypass to self-land the ratification. The constitution-plane write
  path (contract_guard / CODEOWNERS) is unchanged by this phase.

## Self-Check: PASSED

- FOUND: docs/adr/0009-contract-relationship-graph-model.md (Status: proposed)
- FOUND: docs/adr/README.md +1 row for 0009 (zero removed lines)
- FOUND commit: 6b9c15c (Task 1)
- Task 2 intentionally NOT executed — awaiting human ratification (checkpoint state, not a failure).

---
*Phase: 25-graph-compiler-queries-conductor-proof-v2-3-a*
*Status: checkpoint reached — human ratification pending before phase closeout*
