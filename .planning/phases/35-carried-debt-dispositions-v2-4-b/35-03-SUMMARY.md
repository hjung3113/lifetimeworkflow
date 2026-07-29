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
  - "AUTHORED rather than written off -- the artifact base is unusually strong (a review with 3 Criticals, and two follow-on phases that re-verified the output adversarially)."
  - "status is not_independently_verified_in_phase. Transcribing the six SUMMARYs alone would have concluded 4/4 and would have been wrong."
  - "SC-2 is recorded as NEITHER green NOR failed: green in-phase, reopened by the phase's own review with three UNDISPOSITIONED Criticals, closed only in 27.1."
  - "SC-1 and SC-4 are SPLIT rows -- each has a named unsupported half (enforcement via CR-03; the model-id grep). The score is deliberately not expressed as N/4."
  - "27-VALIDATION.md is cited as INTENT only -- its 25 rows are all still pending, so it evidences nothing."
  - "27-REVIEW IN-01/IN-02 are recorded as newly-surfaced OPEN items in phase-35 deferred-items.md, NOT as resolved -- 27.1's same-numbered findings are different findings reusing the IDs."
  - "No test was run and no code was read for evidence. Every row cites a pre-existing artifact."
metrics:
  tasks: 4
  commits: 2
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
| Marking IN-01/IN-02 resolved from 27.1's same-numbered findings | Those are **different findings reusing the IDs**. Phase 27's two have no disposition anywhere, and are now recorded as open items rather than absorbed. Gap **G-3**. |
| A score expressed as N/4 | Two criteria are split and one is neither green nor failed. Forcing a fraction would have hidden exactly the parts worth reading. |
| A closure citation for the `deferred-items.md` snapshot mismatch | The full suite is recorded green at close, which *implies* a rebaseline, but no artifact names the commit. Inference from a test count, flagged as gap **G-4**. |

## Gaps recorded (G-1 .. G-8)

- **G-1** no contemporaneous independent verification exists (there is no `27-VERIFICATION.md`; the
  milestone audit says ADOPT-04..07 "are evidenced through 27.1/27.2 instead")
- **G-2** SC-4's "모델 id 없음" half rests on an unrecorded grep — prose, no command, no output
- **G-3** `27-REVIEW.md` **IN-01 and IN-02** have no disposition in any artifact in any phase —
  newly surfaced, now recorded as open in phase-35 `deferred-items.md`
- **G-4** the deferred snapshot mismatch has no recorded closure (inferable from a later green
  suite, never cited)
- **G-5** all test counts are transcribed, not reproduced
- **G-6** `27-VALIDATION.md`'s 25 per-task rows all still read `⬜ pending` / `❌ W0` despite the
  phase completing — it evidences *intended* coverage only
- **G-7** the phase's evidence is prose, not machine output: **no file:line citation exists in any
  of the six SUMMARYs** (every file:line in the phase comes from the review and cites a defect);
  only **two** numeric exit codes exist phase-wide; 27-02 records no pass count at all
- **G-8** two plans' literal acceptance criteria were relaxed at execution time, so a row quoting a
  PLAN verbatim would not match what was proven — which is why every row quotes SUMMARYs

## Deviations — three corrections, one of them serious

The first draft was committed (`90d1ce0`) and then corrected after review feedback. Recording all
three, because a document whose entire warrant is transcription fidelity does not get to quietly
fix its own transcription errors.

1. **Serious — IN-01 was reported as dispositioned when it is not.** The first draft wrote
   IN-01 as "overtaken by the CR-01/CR-02 fixes in 27.1". That is **wrong**: Phase 27.1's review has
   its own `IN-01`/`IN-02` which are **different findings that reuse the IDs**. Phase 27's IN-01 and
   IN-02 have **no disposition in any artifact, in any phase**. This is exactly the ID-collision
   trap, and falling into it manufactured a closure that does not exist — the precise failure mode
   DEBT-02 forbids. Both are now recorded as open in
   `.planning/phases/35-carried-debt-dispositions-v2-4-b/deferred-items.md`.
2. **WR-04 was reported as undispositioned when it is dispositioned.** The first draft put it in
   gap G-3; it is in fact fixed per 27.1. The error ran in the opposite direction to (1) — it
   understated the record — but it is the same failure of care.
3. **A date claim was wrong.** An early draft said the document was written "roughly a year of
   project-time" after Phase 27. Phase 27 closed **2026-07-21**; this is **2026-07-22** — one
   calendar day, though four phases of code. Corrected before the first commit.

**Also revised for accuracy after review:** SC-1 and SC-4 were upgraded from flat "✓ SUBSTANTIATED
(as recorded)" to **split rows** naming their unsupported halves; SC-2 was changed from "✗
DISPROVEN" to the three-part "green in-phase / reopened by the phase's own review / closed outside
the phase", because both "green" and "failed" are false readings; `27-VALIDATION.md` was demoted
from the evidence base to intent-only; and gaps **G-7** (no file:line citations, only two numeric
exit codes phase-wide, 27-02 records no pass count) and **G-8** (two plans' literal acceptance
criteria relaxed at execution time) were added.

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
> / DEBT-02): authored at closeout with an `authored: at-closeout` stamp, transcription-only,
> status `not_independently_verified_in_phase`. SC-3 substantiated; SC-1 and SC-4 split with a
> named unsupported half each; SC-2 green in-phase, reopened by `27-REVIEW.md` CR-01/02/03 (which
> Phase 27 never dispositioned) and closed only in 27.1. Eight gaps recorded (G-1..G-8).**
> | **resolved** | v2.3 close |

A **second** row should be ADDED, because the sweep surfaced something that was not previously
tracked anywhere:

> | review debt (newly surfaced) | **`27-REVIEW.md` IN-01 and IN-02 have no disposition in any
> artifact, in any phase** — not fixed, not accepted, not deferred. Found during the Phase-35
> DEBT-02 sweep; distinct from 27.1's same-numbered findings, which reuse the IDs. Recorded in
> `.planning/phases/35-carried-debt-dispositions-v2-4-b/deferred-items.md` as P27-IN-01 / P27-IN-02.
> | **open** | Phase 35 |

Note the milestone-audit line that motivated the original deferral — "a closeout-authored
verification of a long-finished phase claims an authority it cannot have" — was right about
authority and is answered by the stamp, not contradicted by it.

## Residuals

- **P27-IN-01 / P27-IN-02 (G-3) are open and now recorded.** Recording them was all this plan could
  honestly do; deciding them is a separate act and deserves its own record. See
  `deferred-items.md` in this phase directory.
- **G-6** — `27-VALIDATION.md`'s never-updated status column is a live process observation, not just
  a Phase 27 fact: an approved validation contract whose rows are never ticked cannot function as
  evidence later. Worth a decision at some point; not acted on here.
- **A note on why (a) still beat (b).** The instruction was that if outcome (a) would need more
  caveats than substance, the write-off (b) is the better answer. Judged (a), and the caveats are
  the reason rather than an argument against it: SC-3 is substantiated outright, SC-1 and SC-4 are
  substantiated for their principal claims, and the single most valuable line in the document —
  that a phase can close green on 1096 tests with its central safety control bypassable — is a
  *finding*, not a caveat. A write-off would have deleted that finding along with the caveats.
