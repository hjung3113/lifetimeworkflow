# Phase 43: Lifecycle Plane Removal - Discussion Log

> **Audit trail only.** Decisions are captured in CONTEXT.md — this log preserves the alternatives.

**Date:** 2026-07-28
**Phase:** 43-lifecycle-plane-removal
**Mode:** `--auto` — every question auto-resolved to the recommended option, no user prompts.

`[--auto] Selected all gray areas: Blast-radius ownership, Deletion unit/order, Contract split,
Hook removal mechanism, Verification.`

---

## Blast-radius ownership (the phase-shaping question)

| Option | Description | Selected |
|--------|-------------|----------|
| Repair the 5 surviving artifacts in-phase, before deleting | Nothing ships a command that crashes | ✓ |
| Delete the plane; fix surviving callers in Phase 45 (Projection Repair) | Smaller phase; ships broken commands meanwhile | |
| Leave a thin shim so the calls keep working | Contradicts "no residue package" outright | |

**Auto-selection:** `[auto] Blast radius — Q: "Who fixes the surviving commands that invoke the dying
plane?" → Selected: "Repair in-phase, before deleting" (recommended default)`
**Notes:** Scouting found five SURVIVING artifacts that execute deleted modules via `!`-prefixed shell
lines — `checkpoint.md` (`tools.handoff generate|validate|activate`), `orient.md` (`tools.handoff
resume`, `/phase-gate`), `review.md` and `verify-work.md` (`tools.evidence.capture`), and
`orchestrator.md` (`tools.capability list`). CER-07 lists none of them. Option 2 would ship a harness
whose own commands crash; option 3 is the residue the requirement explicitly forbids.

---

## Deletion unit and order

| Option | Description | Selected |
|--------|-------------|----------|
| All 8 packages in one commit, after the repair wave | They are mutually referential — no leaf-first order exists | ✓ |
| Leaf-first, one package per commit | Impossible: the dependency graph has cycles | |
| Delete packages first, repair callers after | Intermediate commits are broken | |

**Auto-selection:** `[auto] Deletion unit — Q: "One commit or staged?" → Selected: "All 8 together,
after repair" (recommended default)`
**Notes:** Verified mutual references across task_control/task_packet/risk_router/evidence/handoff/
discipline/capability/lifecycle_eval. 7021 LOC measured, matching CER-07's figure exactly.

---

## The contract split (a requirements collision)

| Option | Description | Selected |
|--------|-------------|----------|
| Delete 6; leave `gate-registry.json` for Phase 44 | CER-08 names it explicitly with its DATA_CONTRACT_PATHS entry | ✓ |
| Delete all 7 as CER-07's prose says | Both phases would claim the same file | |

**Auto-selection:** `[auto] Contracts — Q: "6 or 7?" → Selected: "6, leave gate-registry for 44"
(recommended default)`
**Notes:** The directory holds exactly 7 files. CER-07 says "the 7 task-control contracts"; CER-08
separately claims `gate-registry.json`. Recorded in the ROADMAP detail section so the two phases do
not collide. `tools/evidence/capture.py` (dying here) is a current reader; after this phase only
Phase-42 provenance docstrings mention it.

---

## Hook removal mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse `RETIRED_SIGNATURES`, then empty it after the re-emit | The mechanism Phase 41 built and validated for this exact case | ✓ |
| Remove the signature from `HARNESS_SIGNATURES` only | Phase 41 proved this makes the group look human-owned and preserves it forever | |

**Auto-selection:** `[auto] Hook removal — Q: "How does the emitted hook group actually go away?" →
Selected: "Reuse RETIRED_SIGNATURES" (recommended default)`
**Notes:** `merge.py:112` currently holds `()`. Phase 41 discovered the failure mode the hard way.

---

## Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Structural absence + collect-only + YAML-resolved needs + a pointer-survival assertion | Mechanical throughout | ✓ |
| Full-suite green only | Misses a dangling CI entry and a silently dropped activeContext pointer | |

**Auto-selection:** `[auto] Verification — Q: "What proves it?" → Selected: "Structural + collect-only
+ YAML needs + pointer assertion" (recommended default)`
**Notes:** The activeContext pointer must be asserted, not eyeballed — it sits adjacent to the block
being cut, which is exactly how a good line gets removed with a bad one. No mutation-proof table owed.

## Claude's Discretion

- Plan/task decomposition and wave count; contract-deletion commit placement; the exact replacement
  wording in the five repaired commands (provided no successor mechanism appears).

## Deferred Ideas

- `gate-registry.json`, `secret_scan`, `deny-domains.*`, `memory_ui`, `strangler_guard`, `/pipeline`,
  `gate-model`, golden relocation → Phase 44. Phase-42 provenance docstrings ride along with
  `gate-registry.json`.
