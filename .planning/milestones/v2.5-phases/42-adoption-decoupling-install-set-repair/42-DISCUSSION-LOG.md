# Phase 42: Adoption Decoupling + Install-Set Repair - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-28
**Phase:** 42-adoption-decoupling-install-set-repair
**Mode:** `--auto --chain` — every question auto-resolved to the recommended option, no user prompts.
**Areas discussed:** Approval-gate removal depth, Secret-pattern ownership, Install-set scope,
Residue/prose, Verification

`[--auto] Selected all gray areas: Approval-gate removal depth, Secret-pattern ownership, Install-set
scope, Residue/prose, Verification.`

---

## Approval-gate removal depth

| Option | Description | Selected |
|--------|-------------|----------|
| Delete the ADOPT-06 gate whole (module, `promote` subcommand, apply refusal, tests, orphaned contract) | Nothing survives that gates on a removed binding | ✓ |
| Keep `approval.py`, drop only the task-revision element and the env token | Smaller diff; leaves a gate that refuses on nothing | |
| Keep the gate, swap `GOLDEN_APPROVE_HUMAN` for an adoption-specific token | Preserves a local human gate | |

**Auto-selection:** `[auto] Approval-gate depth — Q: "How much of the ADOPT-06 gate goes?" → Selected:
"Delete the gate whole" (recommended default)`
**Notes:** `approval.py` is not a module that merely imports task-control — it *is* the gate, binding
`(draft_hash, task_revision, git_ref)` (`:11-16`) behind `GOLDEN_APPROVE_HUMAN` (`:45`). CER-06
removes both the revision element and the token, so option 2 ships a gate that gates nothing —
ceremony with a refusal message. Option 3 invents a new human-authored gate, which is the exact thing
v2.5 takes from five to zero, and the binding constraint answers it with NO. Consequence recorded in
the ROADMAP: adoption's real review becomes the PR (ADR-0012).

---

## Secret-pattern ownership after inlining

| Option | Description | Selected |
|--------|-------------|----------|
| Module-level tuple in `scan.py` beside `SECRET_PATH_GLOBS` | Follows the constant already owned locally for this reason | ✓ |
| A new local JSON data file under `tools/adoption_scan/` | Keeps them as data; adds a file | |
| Leave the `gate-registry.json` read until Phase 44 deletes it | No work now; leaves the coupling CER-06 names | |

**Auto-selection:** `[auto] Secret patterns — Q: "Where do the patterns live?" → Selected:
"Module-level tuple beside SECRET_PATH_GLOBS" (recommended default)`
**Notes:** `scan.py:52-54` already owns `SECRET_PATH_GLOBS` for precisely this reason — the inline
follows a precedent instead of establishing a second idiom. Option 2 adds a file to a
deletion-oriented milestone. Option 3 fails CER-06 outright. **Live-tree correction:** there are
**8** patterns, not the 7 the requirement prose claims; all 8 copy byte-identical, and the proof is
that the existing redaction tests pass *unchanged*.

---

## Install-set scope (`_CATEGORY_GLOBS`)

| Option | Description | Selected |
|--------|-------------|----------|
| Blanket `tools/**` glob | A data row; resolves at install time, so 43/44's deletions self-apply | ✓ |
| Enumerate the surviving packages explicitly | Precise today; needs re-editing in both Phase 43 and 44 | |
| Defer until after 43/44 have deleted their packages | Avoids churn; leaves the product inert for two more phases | |

**Auto-selection:** `[auto] Install-set scope — Q: "Blanket glob or explicit list?" → Selected:
"Blanket `tools/**` glob" (recommended default)`
**Notes:** PROD-01's own words are "the fix is a data row, not a mechanism". The glob is also the
*more robust* choice against the rest of the milestone: it resolves against the then-current tree, so
packages deleted in 43/44 simply stop shipping, where an explicit list would silently ship stale names
until someone re-edited it twice. Accepted consequence: the packages' `tests/` ship too — filtering
them would be a mechanism.

---

## Residue and prose

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite the stale docstrings on their own terms, in-phase | Nothing points at a module Phase 43 deletes; SC-1's grep passes | ✓ |
| Leave the docstrings; they are comments | SC-1's grep fails; a doc points at a corpse | |

**Auto-selection:** `[auto] Residue — Q: "What about the docstring-only task-control references?" →
Selected: "Rewrite in-phase" (recommended default)`
**Notes:** **Live-tree correction:** the ~60-LOC atomic create/replace the requirement asks to inline
is *already inlined* (`apply.py:207,241`); only the "Mirrors `tools.task_control.manager...`" prose is
stale. So this is a prose task, not a re-implementation — worth knowing before a planner budgets for
60 lines of work that already exists.

---

## Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Grep assertions + an unset-env `draft → apply` run + a fixture-install test | Mechanical; proves the product property, not just the diff | ✓ |
| Grep assertions only | Proves the imports are gone, not that adoption still runs | |
| Add a CI job asserting the install set stays complete | A new gate — forbidden by the binding constraint | |

**Auto-selection:** `[auto] Verification — Q: "What proves the phase done?" → Selected: "Greps +
unset-env run + fixture-install test" (recommended default)`
**Notes:** The fixture-install test is the phase's most valuable artifact — the first thing that would
catch the product shipping inert again. Recorded that it is *coverage*, not a contributor-facing gate,
so it does not violate the no-new-gates constraint. No mutation-proof table is owed (D-16): this phase
removes a gate and adds no control.

## Claude's Discretion

- Plan/task decomposition and wave count.
- Whether the contract deletion rides with the `approval.py` deletion or gets its own commit.
- The fixture-install test's location and fixture shape.

## Deferred Ideas

- `gate-registry.json`, `secret_scan`, `deny-domains.*` deletion → Phase 44 (CER-08), including the
  stale `ledger_guard` declaration carried out of Phase 41.
- `tools/task_control` + lifecycle plane deletion → Phase 43 (CER-07).
- Filtering `tests/` out of the shipped install set → follow-up, not this phase.
