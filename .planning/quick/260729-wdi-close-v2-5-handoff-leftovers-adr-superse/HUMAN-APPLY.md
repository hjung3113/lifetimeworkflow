---
quick_id: 260729-wdi
status: awaiting-human
gate: GOLDEN_APPROVE_HUMAN
---

# Human-gated writes — ready to apply verbatim

Everything below targets the **constitution plane**
(`tools/hooks/contract_guard.py:55` — `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**",
"docs/glossary.md"]`). An agent cannot write any of it: the PreToolUse gate denies the write unless
a human sets `GOLDEN_APPROVE_HUMAN`, and that token must never be forged. `HARNESS_DEV_BYPASS` is
equally refused here — bypassing a gate to tidy the plane it protects makes the gate decorative.

This file is the *draft*, off-plane. The gate still stands between it and `docs/adr/`.

## How to apply

Run Claude Code in a token-holding session, then hand it this file:

```bash
GOLDEN_APPROVE_HUMAN=1 claude
```

Then: "Apply `.planning/quick/260729-wdi-close-v2-5-handoff-leftovers-adr-superse/HUMAN-APPLY.md`
sections A–D verbatim." CODEOWNERS at the merge stays the real ratification.

---

## A. NEW FILE — `docs/adr/0013-task-control-plane-retirement.md`

Save the block below verbatim (it is the whole file).

````markdown
# 13. Task-Control-Plane Retirement and the Append-Only Citation Rule

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-29
- **Deciders:** kimhyojung (CODEOWNERS)
- **Supersedes:** 0008
- **Superseded by:** —
- **Complements:** [ADR-0012](0012-ci-and-merge-as-decision-authority.md), [ADR-0003](0003-pipeline-topology-slot-and-instance-overlay.md)

## Context and Problem Statement

ADR-0012 made CI and the merge the decision authority for v2.5 and superseded ADR-0001 and ADR-0010
by name. It did not name **ADR-0008**, whose entire subject — the `.workflow/tasks/<task-id>/`
task-control plane, its six-phase lifecycle, and its instance risk overlays — Phase 43 deleted
(CER-07, commit `7b72e6e`, −12,383 LOC).

That omission is not cosmetic. This repo's stated precedence is that accepted ADRs win a data
conflict against code. ADR-0008 currently reads `Status: Accepted` / `Superseded by: —`, so as
written it tells every agent that the deletion was the error and the plane should be restored. The
record must be corrected the only way an append-only log allows: a new record.

A second, narrower gap surfaced in Phase 45 (D-14) and needs deciding with it. Two accepted ADRs
cite documents whose subject matter this milestone removed:

- `docs/adr/0008-task-control-plane-lifecycle.md:50` cites
  `docs/explanation/next-milestone-task-control-plane.md` as its "Design authority".
- `docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md:95` cites
  `harness/agents/templates/component-engineer.md`.

Because ADRs are append-only and their text cannot be corrected after ratification, deleting a cited
target creates a **permanently uncorrectable** dangling reference. Phase 45 handled both by keeping
the targets — one with a HISTORICAL header, one corrected in place — rather than deleting them, but
did so as an executor judgment call with no ratified rule behind it. This ADR supplies the rule.

## Decision Drivers

- Accepted ADRs outrank code in a data conflict, so a stale `Accepted` status actively misdirects
  agents — the opposite of what the record exists for.
- Supersede-don't-edit: a past decision is changed by writing a new record, never by rewriting the
  old one's reasoning.
- v2.5's binding constraint — do not answer a gap by adding ceremony. The remedy here is one
  record and two header lines, not a new gate or a link-checking tool.
- An append-only log cannot repair its own citations, so citation targets need a durable rule rather
  than a per-phase judgment call.

## Considered Options

1. **Leave ADR-0008 as `Accepted` and rely on ADR-0012's general thesis.** *Rejected:* ADR-0012
   never names 0008, and the precedence rule then reads the deletion as the defect.
2. **Edit ADR-0008's body to describe the retirement.** *Rejected:* violates append-only; the
   historical record of what was decided on 2026-07-19 must survive intact.
3. **Delete ADR-0008 and its cited design document.** *Rejected:* removes the record of a real
   ratified decision and creates exactly the uncorrectable dangling citation this ADR forbids.
4. **New superseding ADR + status-header update on 0008 + a durable citation rule.** *Chosen* —
   matches the precedent ADR-0012 set for 0001 and 0010.

## Decision Outcome

**Ratified by human/CODEOWNERS on 2026-07-29.**

### (a) ADR-0008 is superseded in full

The `.workflow/tasks/<task-id>/` namespace, the `INTAKE`/`CLARIFY`/`SPEC`/`PLAN`/`EXECUTE`/`REVIEW`/
`VERIFY`/`COMPLETE` lifecycle with revision-CAS transitions, and the escalate-only instance risk
overlays are **retired**. They were harness machinery for verifying the harness's own process —
precisely what ADR-0012 replaces with CI and the merge. Phase 43 executed the removal; this record
is the decision that removal cites.

Retired with it, and confirmed absent from the tree: `.workflow/`, `tools/task_packet/`,
`tools/risk_router/`, `tools/task_control/`, `tools/evidence/`, and `tools/handoff/`. ADR-0008's
"Links" section still names all six. That text is immutable and is now **historical**: it records
what once existed, not what an agent should expect to find. Reading it as live is the error this
record corrects.

The product-side lifecycle is **not** retired by this ADR — ADR-0012 clause (c) already drew that
boundary, and Phase 46 shipped the four routes plus `/flow` that occupy it. This clause retires the
*harness's* task-control plane only.

### (b) A cited target of an accepted ADR is never deleted

Once an accepted ADR cites a path, that path may be **corrected** or **marked historical**, but not
removed, because the citing text can never be repaired. Concretely, and ratifying what Phase 45 did:

- `docs/explanation/next-milestone-task-control-plane.md` is **kept** under a HISTORICAL header
  stating that the controls, paths, and commands it describes no longer exist.
- `harness/agents/templates/component-engineer.md` is **kept and corrected in place**; two live
  gates depend on it independently of ADR-0003.

ADR-0003's citation at `:95` therefore stands as written and needs no correction — the target is
live and accurate. This clause exists so the next deletion phase does not have to re-derive that.

This is a rule about **cited targets**, not a general no-delete rule: a document no ADR cites is
deleted normally.

### (c) No new enforcement

No link checker, no citation gate, no CI job is added. Per ADR-0012 the merge is the authority, and
per v2.5's binding constraint the default answer to "should we also gate this?" is no. Clause (b) is
a rule for humans and agents to follow at review, enforced by CODEOWNERS on the constitution plane.

### Consequences

- **Good:** the ADR log stops asserting that a deleted plane is current, so the precedence rule now
  points agents at the truth instead of away from it.
- **Good:** deletion phases get a ratified answer to "may I delete this cited file?" instead of
  re-deriving it, as Phases 43-45 each had to.
- **Bad / accepted:** the repository permanently keeps at least one document whose only remaining
  purpose is to satisfy an append-only citation. That cost is the price of an immutable log, and it
  is bounded — one file today.
- **Bad / accepted:** clause (b) is unenforced by machine, so a future deletion can still break a
  citation. Detection is CODEOWNERS review at the PR, consistent with ADR-0012.

## Links

- Supersedes: [ADR-0008](0008-task-control-plane-lifecycle.md) — the retired record.
- Authority for the retirement: [ADR-0012](0012-ci-and-merge-as-decision-authority.md), whose thesis
  this applies to the one plane it did not name.
- Executed by: Phase 43 (Lifecycle Plane Removal, `7b72e6e`); the citation targets were settled in
  Phase 45 (Projection Repair, `41d0c92`) and are ratified here.
````

## B. EDIT — `docs/adr/0008-task-control-plane-lifecycle.md`

Only the two header lines. **Do not touch the body** — append-only.

Line 5, current:

```
- **Status:** Accepted — ratified by human/CODEOWNERS.
```

replacement:

```
- **Status:** superseded by 0013
```

Line 9, current:

```
- **Superseded by:** —
```

replacement:

```
- **Superseded by:** [0013](0013-task-control-plane-retirement.md)
```

*(Precedent: ADR-0001:5,9 and ADR-0010:5,9 carry exactly this shape after 0012 superseded them.)*

## C. EDIT — `docs/adr/README.md`

Existing row:

```
| [0008](0008-task-control-plane-lifecycle.md) | Task Control Plane Namespace, Authority, Lifecycle, and Overlay | accepted |
```

replacement:

```
| [0008](0008-task-control-plane-lifecycle.md) | Task Control Plane Namespace, Authority, Lifecycle, and Overlay | superseded by 0013 |
```

Then **append** (never reorder, never remove a row) after the 0012 row:

```
| [0013](0013-task-control-plane-retirement.md) | Task-Control-Plane Retirement and the Append-Only Citation Rule | accepted |
```

## D. EDIT — `docs/glossary.md`

Quoted verbatim from `.planning/phases/45-projection-repair/45-05-SUMMARY.md:159-180`.

**Do not touch `:13`, `:19`, `:21`, or any other row.** `:21` ("no agent self-blesses a golden") is
still true and must survive. The plan's claimed third defect at `:19` **does not exist** — measured:
`/golden-approve` occurs once in the whole file, on `:20`.

`docs/glossary.md:20`, current:

```
| **`.received` / `.verified`** | The two-file golden split: `.received` is machine-proposed output; `.verified` is the human-promoted, approved baseline. Promotion is the `/golden-approve` step. |
```

replacement:

```
| **`.received` / `.verified`** | The two-file golden split: `.received` is machine-proposed output; `.verified` is the human-promoted, approved baseline. Promotion requires a human `GOLDEN_APPROVE_HUMAN` ratification, gated again by CODEOWNERS at merge. |
```

`docs/glossary.md:23`, current:

```
| **Constitution plane** | Human-owned, gated source of truth: `contracts/`, `golden/`, `docs/adr/`, `docs/glossary.md`. Changed only through review (CODEOWNERS) and the golden/drift gates. |
```

replacement:

```
| **Constitution plane** | Human-owned, gated source of truth: `contracts/`, `docs/adr/`, `docs/glossary.md` (ADR-0001's fourth member, root `golden/`, is superseded by ADR-0012 clause (d); instance baselines live at `examples/<instance>/golden/`). Changed only through review (CODEOWNERS) and the golden/drift gates. |
```

## After applying

```bash
uv run pytest -q                       # expect 881 passed
uv run python -m tools.contract_drift  # expect exit 0
git grep -n 'Superseded by: —' -- docs/adr/    # 0013 only
```

The constitution plane must also stay byte-pristine: the gate re-checks BOM/CRLF even on an approved
write (`contract_guard.decide`), so save as UTF-8 without BOM, LF endings.

## Still open after this — D-24

Not a file change. Branch protection on `main` requires the `gate` check (strict) but has no
`required_pull_request_reviews` block and `enforce_admins` is false, so CODEOWNERS auto-requests
review without being able to block a merge. `require_code_owner_reviews=true` is **not** a
straightforward fix: GitHub forbids self-approval, so a solo repo needs a second account or a
per-merge admin waiver — already considered and declined in v2.3 RAT-5. Options: (a) accept the
residual as documented, consistent with ADR-0012; (b) add a second account; (c) a machine-side check
on golden baseline diffs in v2.6, now that v2.5's no-growth constraint has closed.
