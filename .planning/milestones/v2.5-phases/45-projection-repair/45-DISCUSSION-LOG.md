# Phase 45: Projection Repair - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-29
**Phase:** 45-projection-repair
**Mode:** `--auto --chain` — every question auto-resolved to the recommended option, no user prompts.
**Areas discussed:** The emptied constitution glob, Orphaned deny rows, Sweep semantics, Docs residue
depth, Verification

`[--auto] Selected all gray areas: The emptied constitution glob, Orphaned deny rows, Sweep semantics,
Docs residue depth, Verification.`

---

## The emptied constitution glob (`golden/**`)

| Option | Description | Selected |
|--------|-------------|----------|
| Remove `golden/**` from the constitution plane entirely | ADR-0012 clause (d) already superseded it; relocated baselines are instance evidence gated by CODEOWNERS at the merge | ✓ |
| Repoint it to `examples/*/golden/**` | Keeps an in-session deny over the relocated baselines | |
| Leave it; CODEOWNERS is the compensating control | Phase 44's recorded position | |

**Auto-selection:** `[auto] Constitution glob — Q: "Remove, repoint, or leave?" → Selected: "Remove
entirely" (recommended default)`
**Notes:** **The repo's own record decided this, not a judgment call.** `docs/adr/0012-...:139-147`
clause (d) supersedes ADR-0001's four-member list "to the extent that `golden/**` leaves the
constitution-plane core", and then names this exact moment: *"Between this ADR's ratification and
Phase 44's actual code move, `contract_guard`'s `CONSTITUTION_GLOBS` and the pinned test … will
KNOWINGLY still enforce `golden/**` as a fourth member. This is named here as an expected"*
transitional state. Phase 44 made the move, so the removal is due and needs no new ADR. Option 2 would
re-add a member the ADR removed. Option 3 leaves a glob matching zero paths while its comment claims a
plane — measured: all 7 relocated baselines match NOTHING. Phase 44's own reasoning
(`44-06-SUMMARY.md:311-316`, "widening would be surface growth") reached a defensible outcome by the
wrong route. Recorded that the declaration is duplicated in FOUR places that must move together.

---

## Orphaned `*.env` deny rows

| Option | Description | Selected |
|--------|-------------|----------|
| Remove the rows and the test assertion together | A deny nothing performs is a false claim | ✓ |
| Keep the rows as documentation of intent | Leaves a green test asserting a dead control | |
| Re-add an enforcer | Forbidden by the binding constraint | |

**Auto-selection:** `[auto] Deny rows — Q: "What happens to *.env now that secret_scan is gone?" →
Selected: "Remove rows and assertion together" (recommended default)`
**Notes:** `permission-matrix.json:32-33` was enforced only by `secret_scan` (deleted in Phase 44);
`contract_guard` explicitly excludes those rows at `:36-37`, and `test_resolver.py:64` still asserts
`config/prod.env` → `deny`. Option 2 is the precise defect this milestone exists to remove — a claimed
control that does not exist, kept green by its own test. Option 3 is the surface growth the constraint
answers with NO, and ADR-0012 already records secret detection at the tool boundary as a permanent
residual caught at CI/PR review.

---

## Sweep semantics — what counts as stale

| Option | Description | Selected |
|--------|-------------|----------|
| Sweep by meaning: a live file describing a control/path/command that no longer exists | Preserves implementation, history notes, and ADR text | ✓ |
| Sweep by token: remove every mention of a deleted name | Mechanical, and destroys the record | |

**Auto-selection:** `[auto] Sweep semantics — Q: "How is stale defined?" → Selected: "By meaning"
(recommended default)`
**Notes:** Three categories are legitimate and must survive: (a) the relocated `golden_runner` package
*implements* the approve gate and will keep naming it; (b) **history notes that name a retired artifact
in order to record its retirement** (`caps.py:124,134`, `test_coexist.py:56`, `test_commands.py:42`) —
a Phase-43 executor and a Phase-44 executor each independently refused to strip these to force a clean
grep, and both were right; (c) append-only ADR text. Option 2 would have deleted the repo's own
retirement record to satisfy a regex.

---

## Docs residue depth

| Option | Description | Selected |
|--------|-------------|----------|
| Delete whole files whose entire subject is a deleted plane; correct prose elsewhere | Honest; no half-repaired documents | ✓ |
| Correct prose everywhere, delete nothing | Leaves how-tos for workflows that no longer exist | |
| Defer `docs/` again | It has already been deferred twice | |

**Auto-selection:** `[auto] Docs depth — Q: "Correct or delete?" → Selected: "Delete whole corpses,
correct the rest" (recommended default)`
**Notes:** `docs/how-to/task-lifecycle.md` carries 8 command blocks invoking 7 deleted modules; its
whole subject is the plane Phase 43 removed. `docs/` sits outside every sweep the harness runs and
`tools/docs_guard` was deleted in Phase 41, so nothing gates any of it — which is why this survived
two prior deferrals. Recorded that `README.ko.md` appears in NO prior deferral list because every list
named `README.md`; that gap is why it survived four phases.

---

## Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Mechanical zero-match assertion + per-commit green + explicit examples leg | Catches the CR-01 class at commit time, not at review | ✓ |
| Structural greps at phase end | What Phase 44 did; CR-01 escaped to the review | |
| A prose-freshness CI gate | A new gate — forbidden | |

**Auto-selection:** `[auto] Verification — Q: "What proves the phase done?" → Selected: "Zero-match
assertion + per-commit green" (recommended default)`
**Notes:** The highest-value artifact here is an assertion that **no declared glob matches zero paths**
— exactly what would have caught CR-01 at Phase 44's commit rather than at its review. Recorded that it
is coverage of an existing declaration rather than a new gate, but flagged that it sits close to the
SC-8 line and the framing must be confirmed before it is written. Option 3 is refused outright: a
prose-freshness checker is the class this milestone removes, and `docs_guard` was deleted on purpose.
No mutation-proof table is owed — the phase removes claims and adds no control.

## Claude's Discretion

- Plan/task decomposition and wave count; Tier 1 lands first and separately as the only
  security-relevant half.
- Whether whole-file `docs/` deletions ride with their tier or take one commit.
- Exact replacement wording, provided no successor mechanism appears.

## Deferred Ideas

- PROD-02…05, the product lifecycle → Phase 46.
- ADR-0008's superseding ADR → human-gated; surface at the milestone-close PR.
- A general prose-freshness gate → explicitly refused.
