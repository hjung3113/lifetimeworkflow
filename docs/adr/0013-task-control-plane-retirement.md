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
