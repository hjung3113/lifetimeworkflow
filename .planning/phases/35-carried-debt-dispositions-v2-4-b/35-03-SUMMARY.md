---
phase: 35-carried-debt-dispositions-v2-4-b
plan: 03
subsystem: planning artifacts / verification record
tags: [DEBT-02, at-closeout, verification, honesty-stamp]
requires:
  - .planning/milestones/v2.3-phases/27-*/ (six PLAN/SUMMARY pairs, 27-REVIEW.md, 27-VALIDATION.md, deferred-items.md)
  - .planning/milestones/v2.3-ROADMAP.md (Phase 27 goal + SCs; 27.1/27.2 insertion rationales)
provides:
  - "27-VERIFICATION.md -- at-closeout, transcription-only, status not_passed_at_close"
affects:
  - ".planning/STATE.md 'nyquist / verification debt' row (reported, NOT written)"
tech-stack:
  added: []
  patterns:
    - "at-closeout verification: the VALIDATION precedent's honesty stamp on a VERIFICATION-shaped body, with citation-per-row and a load-bearing gaps section"
decisions:
  - "AUTHORED rather than written off -- the artifact base is unusually strong (a review with 3 Criticals, an approved VALIDATION, and two follow-on phases that re-verified the output adversarially)."
  - "status is not_passed_at_close, NOT passed. Transcribing the six SUMMARYs alone would have concluded 4/4 and would have been wrong."
  - "SC-2 is recorded as DISPROVEN, because 27-REVIEW.md CR-01/CR-02/CR-03 demonstrate the bypass and Phase 27.1 exists to repair exactly it."
  - "No test was run and no code was read for evidence. Every row cites a pre-existing artifact."
metrics:
  tasks: 4
  commits: 1
  tests_added: 0
---

# Phase 35 Plan 03: Phase 27's Verification Disposition

**Disposition: AUTHORED**, at
`.planning/milestones/v2.3-phases/27-task-local-adoption-workflow-safe-application-v2-3-b/27-VERIFICATION.md`,
with `authored: at-closeout` and `status: not_passed_at_close`.

## Why authored rather than written off

The write-off option exists for a phase whose artifacts cannot substantiate anything. Phase 27's
can, and unusually well: six PLAN/SUMMARY pairs with recorded commands and counts, a `27-REVIEW.md`
carrying **3 Critical / 4 Warning / 2 Info** findings, an approved contemporaneous
`27-VALIDATION.md`, `deferred-items.md`, and — the strongest evidence available for any phase in
this repo — **two inserted phases (27.1, 27.2) that exist specifically to re-verify Phase 27's
output adversarially, and found real defects in it**. Declaring that unusable would discard
evidence, which is a different failure from inventing it.

## The precedent needed both halves, and neither precedent has both

The brief named `27.2-VALIDATION.md` / `28-VALIDATION.md`. Those supply the **honesty stamp**
(`authored: at-closeout` frontmatter plus an opening note stating the document was written at
closeout, is dated today rather than back-dated, could not have steered the phase, and "claims no
prospective authority it never had"), but they are **VALIDATION** files — a reconstructed *strategy*.

Phase 27 already **has** a contemporaneous `27-VALIDATION.md` (`status: approved`, 25-row per-task
map). What it lacks is the **VERIFICATION** — the *outcome* report. The body shape for that comes
from `27.2-VERIFICATION.md` / `28-VERIFICATION.md`: goal, observable-truths table, required
artifacts, key links, behavioral spot-checks, gaps.

So the document authored is a **VERIFICATION-shaped body carrying the VALIDATION precedent's
stamp**. Recorded because the brief's framing implied one precedent supplied both, and it does not.

## The finding that mattered

Transcribing the six SUMMARYs alone would have produced **4/4 passed**. That would have been wrong,
and the artifact that prevents it is one the phase itself produced.

`27-REVIEW.md` (`status: issues_found`) states that the phase's own stated centerpiece — apply.py's
structural constitution refusal — "does not hold up under adversarial input", with three Criticals
proven by demonstrated bypass:

- **CR-01** — `refuse_if_constitution` glob-matches the raw destination with no normalization, so
  `a/../contracts/x.json` and (on this repo's own case-insensitive APFS) `CONTRACTS/x.json` are not
  denied.
- **CR-02** — no destination confinement at all; an absolute path writes outside `target_root`.
- **CR-03** — `approval.check_valid()` "is called nowhere outside its own unit test", so the
  ADOPT-06 gate that plan 27-04 was built for never gates the write — while the shipped skill told
  its reader that promotion gates the apply.

The v2.3 ROADMAP's Phase 27.1 insertion rationale says the same thing independently: "Phase 27
shipped green — 1096 tests, contract-drift clean, emit clean — while its three load-bearing controls
each failed under an input shape no test supplied."

**SC-2 is therefore recorded as DISPROVEN and the phase status as `not_passed_at_close`.** Reporting
it as met, when an entire inserted phase exists to repair exactly it, would have been a lie by
omission — and would have been the *specific* form of manufactured authority DEBT-02 forbids.

Score: **3 of 4 criteria substantiated; 1 disproven.** SC-2's second half (atomic / collision-safe /
idempotent) is substantiated and was explicitly praised by the same review, so the criterion is
split rather than failed wholesale.

## What was refused

Six things did not go into the document:

| Refused | Why |
|---|---|
| Any row without a citation | D-08. Every row names the artifact it came from. |
| Running the suite today and counting it as phase-time evidence | A green tree today reflects phases 27.1/27.2/28/29, not Phase 27's close. **No check of any kind was executed for this document.** |
| Reading today's code to fill an evidence gap | It would produce claims about the repaired code, presented as verification of the phase that shipped it broken. |
| SC-4's "no new persona / no model id" half as verified | No artifact records that check for this phase. Marked "(as recorded)" and raised as gap **G-2**. |
| A disposition for review findings WR-04 and IN-02 | Nothing in Phase 27, 27.1 or 27.2 mentions them. They are recorded as **unaddressed in the record** — not as fixed, and not as open. Gap **G-3**. |
| A closure citation for the `deferred-items.md` snapshot mismatch | The full suite is recorded green at close, which *implies* a rebaseline, but no artifact names the commit. Inference from a test count, flagged as gap **G-4**. |

## Gaps recorded (G-1 .. G-6)

G-1 no contemporaneous independent verification exists · G-2 SC-4's persona/model-id half
unsubstantiated · G-3 WR-04 and IN-02 have no recorded disposition anywhere · G-4 the deferred
snapshot mismatch has no recorded closure · G-5 all test counts are transcribed, not reproduced ·
**G-6** — found while reading: `27-VALIDATION.md`'s 25 per-task rows still all read `⬜ pending`
with `❌ W0` markers despite the phase completing, so it evidences *intended* coverage only and
cannot serve as per-task outcome evidence.

## Deviations

One factual error was introduced and corrected before commit: an early draft said the document was
written "roughly a year of project-time" after Phase 27. Phase 27 closed **2026-07-21** and this is
**2026-07-22** — one calendar day, though four phases of code. Corrected to state the real gap.
Recorded rather than silently fixed, because a document whose entire warrant is transcription
fidelity does not get to be sloppy about a date.

## Verification

| Check | Result |
|---|---|
| `authored: at-closeout` in frontmatter | present (line 4) |
| Opening note states written-at-closeout, not back-dated, no prospective authority | present |
| Every SC row cites a pre-existing artifact | yes — 4/4 |
| Constitution-plane paths in the diff | **none** — the diff is one file under `.planning/` |
| `git status` clean at plan end | yes |

## What STATE.md Should Say

`.planning/STATE.md` was **not** touched. Its "nyquist / verification debt" row should move from
`open` to `resolved`:

> | nyquist / verification debt | Phase 27 has no `VERIFICATION.md`. **RESOLVED 2026-07-22 (Phase 35
> / DEBT-02): authored at closeout with an `authored: at-closeout` stamp, transcription-only, status
> `not_passed_at_close` (3/4 substantiated, SC-2 disproven by `27-REVIEW.md` CR-01/02/03 and
> remediated by phases 27.1/27.2). Six gaps recorded (G-1..G-6).** | **resolved** | v2.3 close |

Note the milestone-audit line that motivated the original deferral — "a closeout-authored
verification of a long-finished phase claims an authority it cannot have" — was right about
authority and is answered by the stamp, not contradicted by it.

## Residuals

- **WR-04 and IN-02 (G-3) have no disposition in any artifact.** Recording them was all this plan
  could honestly do; deciding them is a separate act and would deserve its own record.
- **G-6** — `27-VALIDATION.md`'s never-updated status column is a live process observation, not just
  a Phase 27 fact: an approved validation contract whose rows are never ticked cannot function as
  evidence later. Worth a decision at some point; not acted on here.
