---
phase: 39-decision-boundary-v2-5-a
verified: 2026-07-26T00:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 39: Decision Boundary (v2.5 A) Verification Report

**Phase Goal:** Land one human-ratified ADR-0012 that makes CI + the merge the authority, ratifies
the DEV/PRODUCT boundary with its operative rule, retires the superseded decision records, and
closes the three carried human-ratification items as obsolete-by-deletion.
**Verified:** 2026-07-26
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `docs/adr/0012-ci-and-merge-as-decision-authority.md` exists, `Status: accepted`, non-empty `Date`/`Deciders` | VERIFIED | File exists; `Status: accepted`, `Date: 2026-07-26`, `Deciders: kimhyojung (CODEOWNERS)` confirmed by direct read and grep exact-count checks (all pass) |
| 2 | ADR-0012 names every v2.5-deleted surface (Phases 40-44) component by component, scoped as ratification-time intent | VERIFIED | Clause (b) lists Phase 40/41/43/44 deletions verbatim against `ROADMAP.md` lines 195-234, names Phase 42 as a non-deletion, and includes the explicit "intent at the ratification date... does NOT falsify this ADR" sentence |
| 3 | ADR-0012 states the DEV/PRODUCT boundary + operative rule, citing `_CATEGORY_GLOBS` and `generate.py:41-43` | VERIFIED | Clause (c) cites both file references verbatim and states the "no product capability may be declined..." rule (grep exact-count = 1) |
| 4 | ADR-0012 states the Phase 39 checkpoint is a one-time transition, no standing gate | VERIFIED | Clause (f) contains literal phrase "one-time transition" (occurs 2x — clause + Context section) |
| 5 | ADR-0011 has non-empty `Date`/`Deciders` and records code (`bc9a6d9`) landed before ratification | VERIFIED | `Status: accepted`, `Date: 2026-07-26`, `Deciders: kimhyojung (CODEOWNERS)`; `## Ratification note` section cites `bc9a6d9` (grep count = 1) |
| 6 | ADR-0001 and ADR-0010 carry `Status: superseded by 0012` / `Superseded by:` pointer, decision bodies unedited | VERIFIED | `git show 5b159ea --stat` shows 4 lines changed in each file (2 content lines); `git diff` shows only frontmatter `Status`/`Superseded by` lines changed, body untouched |
| 7 | `docs/adr/README.md` lists 0010 (superseded by 0012), 0011 (accepted), 0012 (accepted), no duplicate rows | VERIFIED | Exactly one row each for 0001/0010/0011/0012 (grep -c = 1 for each), statuses correct |
| 8 | `.planning/STATE.md` records RAT-4, RAT-5, per-tool deny-spelling as obsolete-by-deletion and SEAL-05 as withdrawn, citing ADR-0012, append-only | VERIFIED | Exactly 4 rows carry marker `v2.5 P39, ADR-0012` (3 `obsolete-by-deletion`, 1 `withdrawn`); commit `6edb3bc` diff shows 4 insertions, 0 deletions |
| 9 | The existing suite, contract-drift gate, and emitted trees stay exactly as green/red as before this phase | VERIFIED | `uv run pytest` → 1688 passed; `contract-drift: OK`; `git diff --exit-code .claude .opencode` after re-emit → exit 0 (zero drift); `docs-guard` failing-binding set independently re-run and confirmed to be exactly `{task-control-cli-howto}` (one `fail:` line; `lifecycle-eval-shadow-metrics` is `STALE_ADVISORY`, non-blocking) |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/adr/0012-ci-and-merge-as-decision-authority.md` | New ADR, accepted, six clauses | VERIFIED | Substantive, all six clauses present with cited file paths |
| `docs/adr/0001-walking-skeleton-golden-core.md` | Frontmatter-only supersede edit | VERIFIED | 2 content lines changed, body byte-identical (confirmed via `git show`) |
| `docs/adr/0010-human-docs-review-obligation-model.md` | Frontmatter-only supersede edit | VERIFIED | 2 content lines changed, body byte-identical |
| `docs/adr/0011-gate-right-sizing-dev-light-ci-strong.md` | Frontmatter fill + Ratification note | VERIFIED | `Date`/`Deciders` filled, `bc9a6d9` cited once |
| `docs/adr/README.md` | Index rows for 0010/0011/0012 | VERIFIED | No duplicate rows; correct statuses |
| `.planning/STATE.md` | 4 appended Deferred Items rows | VERIFIED | Exactly 4 rows, correctly tagged, append-only proven (0 deleted lines) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `docs/adr/0001-*.md` | `docs/adr/0012-*.md` | `Superseded by:` pointer | WIRED | `Superseded by: [0012](0012-ci-and-merge-as-decision-authority.md)` present |
| `docs/adr/0010-*.md` | `docs/adr/0012-*.md` | `Superseded by:` pointer | WIRED | Same pattern present |
| `docs/adr/0011-*.md` | commit `bc9a6d9` | `## Ratification note` | WIRED | Note cites commit hash and message |
| `.planning/STATE.md` | `docs/adr/0012-*.md` | prose citation in each new row | WIRED | All 4 new rows cite `docs/adr/0012-ci-and-merge-as-decision-authority.md` by path |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CER-01 | 39-01 | ADR-0012 records CI+merge authority, names deleted surfaces, supersedes 0001/0010, accepts 0011 | SATISFIED | ADR-0012 clauses (a),(b),(d); ADR-0011 accepted |
| CER-02 | 39-01 | ADR-0012 ratifies DEV/PRODUCT boundary + operative rule | SATISFIED | ADR-0012 clause (c) |
| CER-03 | 39-02 | RAT-4/RAT-5/deny-spelling obsolete-by-deletion; SEAL-05 withdrawn | SATISFIED | STATE.md 4 new rows |

No orphaned requirements found for this phase — REQUIREMENTS.md maps only CER-01/02/03 to Phase 39, all three are declared in the plans' `requirements:` frontmatter and satisfied.

**Note (non-blocking, informational):** `.planning/REQUIREMENTS.md`'s "## Traceability" table (lines 179-181) still lists CER-01/02/03 as "Not started," while the requirement bullets themselves (lines 28, 34, 40) are checked `[x]`. This table was not in either plan's `files_modified` and updating it was not a stated must-have or success criterion for this phase — it is a pre-existing bookkeeping table not covered by this phase's scope. Recommend a follow-up doc touch-up but it does not affect goal achievement.

### Anti-Patterns Found

None in files created/modified by this phase. The two `TBD`/`OWNER_TBD` string matches found by the debt-marker scan are pre-existing prose inside ADR-0001 (line 46, describing the historical "TBD markers" convention) and ADR-0010 (line 367, describing the "OWNER_TBD house rule") — both are inside the untouched body text of files this phase only edited at the frontmatter level, confirmed by the diff review above. Not new debt introduced by this phase.

### Human Verification Required

None. The phase's sole human-verify checkpoint (39-01 Task 1) was already completed in-session per the context supplied: human replied "approved" with confirmed `Date: 2026-07-26` / `Deciders: kimhyojung (CODEOWNERS)`, and the write proceeded via the already-active `HARNESS_DEV_BYPASS` opt-out (a human-directed deviation from the plan's literal `GOLDEN_APPROVE_HUMAN` path, documented in 39-01-SUMMARY.md and treated as accepted per task instructions, not a gap).

### Gaps Summary

No gaps found. All 9 derived observable truths verified against the actual codebase (not SUMMARY claims): ADR-0012 exists and is substantively complete across all six required clauses; ADR-0001/0010 supersession is proven against the actual commit diff (not assumed); ADR-0011 acceptance is proven; the README index has no duplicate rows; STATE.md's four dispositions are proven via independent grep re-run; and the full no-regression gate (pytest 1688 passed, contract-drift OK, zero emission drift, docs-guard failing-binding set unchanged at exactly `{task-control-cli-howto}`) was independently re-executed by this verifier, not taken from the SUMMARY's reported numbers.

---

_Verified: 2026-07-26_
_Verifier: Claude (gsd-verifier)_
