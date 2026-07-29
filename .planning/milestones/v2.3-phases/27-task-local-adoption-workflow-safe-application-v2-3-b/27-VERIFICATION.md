---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
verified: 2026-07-22T00:00:00Z
authored: at-closeout
status: not_independently_verified_in_phase
score: "SC-3 substantiated; SC-1 and SC-4 substantiated in part with a named unsupported half each; SC-2 green in-phase, reopened by the phase's own review, closed only outside the phase"
overrides_applied: 0
re_verification: null
remediated_by: [27.1, 27.2]
newly_surfaced_open_items: [27-REVIEW IN-01, 27-REVIEW IN-02]
---

# Phase 27: Task-Local Adoption Workflow + Safe Application — Verification Report

> **Authored at closeout, not during execution.** Phase 27 ran and closed without a
> `VERIFICATION.md`; `.planning/v2.3-MILESTONE-AUDIT.md` recorded that absence as debt, and the v2.3
> close explicitly declined to back-fill it on the grounds that a closeout-authored verification
> "claims an authority it cannot have". That objection is right about authority and wrong about
> silence, and this document is written to be the first without being the second.
>
> **This document could not have steered the phase it describes.** It is dated 2026-07-22; Phase 27
> closed on 2026-07-21, and the tree has since moved through phases 27.1, 27.2, 28, 29 and the v2.3
> milestone close. The gap is short in calendar time and large in code: two of those phases exist
> specifically to repair Phase 27. It claims **no prospective authority**, and it is not
> back-dated. Every row below is **transcribed from an
> artifact that already existed** — the six PLAN/SUMMARY pairs, `27-REVIEW.md`, `deferred-items.md`,
> and the Phase 27/27.1/27.2 entries in `.planning/milestones/v2.3-ROADMAP.md`. Where no such
> artifact exists, the row says so and is counted as a gap. Nothing here was inferred from reading
> today's code.
>
> **`27-VALIDATION.md` is cited as intent, never as result.** Its 25 per-task rows all still read
> `⬜ pending` with `❌ W0` file-exists markers; only pre-existing gate rows are `✅`. It is an
> approved *plan* for coverage that was never updated as execution proceeded, so **no row in this
> document is evidenced by it**. See gap G-6.
>
> **Source:** `.planning/milestones/v2.3-ROADMAP.md:600-611` (goal + the four success criteria) ·
> `27-01`..`27-06` SUMMARYs · `27-REVIEW.md` (`status: issues_found`, 3 critical / 4 warning /
> 2 info) · `27-VALIDATION.md` (`status: approved`, 2026-07-21) · `deferred-items.md` ·
> `.planning/milestones/v2.3-ROADMAP.md:630,659` (the 27.1 / 27.2 insertion rationales).

**Phase Goal** (verbatim, `v2.3-ROADMAP.md:602`): 결정론적 plan을 출하된 task control plane 위에서
재개 가능·사람 ratified·비파괴 adoption 워크플로로 전환한다.

**Requirements:** ADOPT-04, ADOPT-05, ADOPT-06, ADOPT-07
**Status:** **not passed at close** — see SC-2. Remediated by the inserted phases 27.1 and 27.2.

---

## Why this report does not say "passed"

Phase 27's six SUMMARYs each record their own plan as complete, and the phase closed green: 1096
tests, contract-drift clean, emit clean (`27-06-SUMMARY.md` § Next Phase Readiness). A closeout
verification that simply transcribed those self-reports would conclude 4/4 and would be **wrong**.

`27-REVIEW.md` — an artifact of the phase itself, dated 2026-07-21 — reports `status:
issues_found` with **three Critical findings**, and states directly:

> "the phase's own stated centerpiece — *'apply.py's constitution refusal is a structural,
> in-process precondition that does not depend on any hook'* — does not hold up under adversarial
> input. […] All three are proven concretely below (bypass demonstrated, not merely reasoned
> about), and none is covered by any existing test."

The v2.3 ROADMAP's rationale for **inserting Phase 27.1** says the same thing independently
(`v2.3-ROADMAP.md:632`): "Phase 27 shipped green — 1096 tests, contract-drift clean, emit clean —
while its three load-bearing controls each failed under an input shape no test supplied."

So the honest finding of this closeout is not that Phase 27's verification was never written. It is
that **Phase 27's verification would have said 4/4 if it had been written from the SUMMARYs**, and
that the review is the artifact that prevents this document from repeating that error.

---

## Goal Achievement

### Observable Truths

Success criteria verbatim from `.planning/milestones/v2.3-ROADMAP.md:606-611`.

| # | Truth (ROADMAP SC) | Status | Evidence — and the artifact it is transcribed from |
|---|---|---|---|
| SC-1 | `.workflow/tasks/<id>/artifacts/adoption/<batch>/` batch가 안전하게 재개되고, 변경된 draft/ref/revision이 승인을 무효화한다. | ◐ **SPLIT** — resume + invalidation substantiated; **enforcement half unsupported** | **Resume:** `27-01-SUMMARY.md` — "batch.py implements batch_id_for/create_or_resume_batch/read_status/update_status per the plan's `<behavior>` block; all 4 tests in test_batch_layout.py green, including the two named Nyquist rows (test_resume_safely, test_batch_uses_existing_cas)". **Invalidation:** `27-04-SUMMARY.md` — "3 INDEPENDENT single-axis invalidation tests (draft-only, revision-only, ref-only — each holding the other two axes constant), 1 positive control, and test_sc1_full_resume_cycle proving SC-1's full sentence end to end", with the binding "(draft_hash, task_revision, git_ref), each recomputed FRESH at every check_valid call". **What is NOT supported:** the criterion is about approval *invalidation*, and invalidation is proven only at the `check_valid` unit level. `27-REVIEW.md` **CR-03** states `check_valid` "is imported and exercised only by its own unit test" and that the write path never calls it. **So this row must not be read as "human ratification gates apply" — it did not.** A correctly-invalidated approval was never consulted before a write. That enforcement gap is CR-03's subject and was closed only in 27.1 (`27.1-VERIFICATION.md` truth 3, `cli.py:148`, exit 4). |
| SC-2 | `contracts/`·`docs/adr/`·`golden/` destination이 mutation 전에 거부되고, 비-헌법 apply가 atomic·collision-safe·idempotent하다. | ◐ **GREEN IN-PHASE, REOPENED BY THE PHASE'S OWN REVIEW, CLOSED OUTSIDE THE PHASE** | This row is deliberately neither green nor failed, because both readings are false. **In-phase it passed:** `27-03-SUMMARY.md` records "refuse_if_constitution/refuse_if_outside_root raise BEFORE any open()/os.link()/os.replace() call — test_refuses_before_mutation proves a zero-call spy for contracts/\*\*, docs/adr/\*\*, and golden/\*\* destinations", plus `test_sc2_full_apply_cycle` running one manifest with all 6 dispositions through `apply_manifest`, and "18/18 tests green". **Then the phase's own review reopened it:** `27-REVIEW.md` **CR-01** (`apply.py:74-84`) — the refusal glob-matches the raw destination string with no normalization, so `a/../contracts/x.json` and (on this repo's own case-insensitive APFS) `CONTRACTS/x.json` bypass it; **CR-02** (`apply.py:213`, `188-237`) — no confinement, an absolute destination discards `target_root`; **CR-03** — the ratification gate is decoupled from the write path. Review § Summary: "**none is covered by any existing test.**" **And Phase 27 never dispositioned them:** no Phase 27 artifact records a fix, an acceptance, or a deferral for CR-01/02/03. **Closure exists only outside this phase** — `27.1-VERIFICATION.md` / `27.1-03-SUMMARY.md`. The atomic/collision-safe/idempotent half was never disputed: review § Summary calls "the atomic-write primitives (`atomic_create`/`_atomic_replace`), the batch CAS layout […] well constructed and match their stated contracts". |
| SC-3 | 3개 fixture(polyglot 단일·2-레포 client/server·partial/collision, 최소 하나 CRLF/BOM)가 통과한다. | ✓ SUBSTANTIATED | `27-05-SUMMARY.md` § Verification Results records `uv run pytest tools/adoption_apply/tests/test_fixtures.py -q` → **3 passed**, and creates all three fixture trees. The CRLF/BOM requirement is met deliberately rather than incidentally: "partial-collision-crlf's mandatory CRLF/BOM input is the target's AGENTS.md itself — AGENTS.md is MARKER_CAPABLE, so it always routes through `harness_emit.merge.splice_managed_block`, the ONE apply.py code path that calls `_normalize` on existing text; this makes the CRLF/BOM normalization assertion meaningful (traced through real production code) rather than an ad hoc bytes comparison." |
| SC-4 | `/adopt` + `brownfield-adoption` skill이 두 런타임에 byte-identical 왕복(새 persona 없음, 모델 id 없음)한다. | ◐ **SPLIT** — round-trip substantiated; **"모델 id 없음" rests on an unrecorded grep** | **Round-trip:** `27-06-SUMMARY.md` — "Both runtime trees (.opencode/, .claude/) re-emitted from the widened harness/ source and confirmed byte-identical on a SECOND re-emit (`git diff --exit-code -- .opencode .claude` clean) — SC-4", `uv run pytest tools/harness_emit -q` → **47 passed**, with the gate-theft-avoidance ordering stated explicitly (suite green **before** the committed trees were touched). `27-05-SUMMARY.md` independently records the emit round-trip "clean, no drift". **No new persona:** structurally checked — `test_commands.py`/`test_skills.py` → **147 passed**. **What is weaker than it looks:** the "모델 id 없음" half rests on the SUMMARY's phrase "and a grep for model-name tokens" — **no command and no output are recorded**. It is a prose assertion, not a transcribable result. See gap G-2. |

**Score.** Not expressible as N/4, and forcing it to be would misreport the phase. **SC-3** is
substantiated outright. **SC-1** and **SC-4** are each substantiated for their principal claim with
a *named unsupported half* (enforcement; model-id grep). **SC-2** was green in-phase, reopened by
the phase's own review with three undispositioned Criticals, and closed only in 27.1.

### Required Artifacts

Every row transcribed from the `key-files.created` block of the named SUMMARY. Existence is recorded
as the SUMMARY recorded it; this document did not re-check the tree.

| Artifact | Recorded by | Status |
|---|---|---|
| `tools/adoption_apply/{pyproject.toml,__init__,__main__,batch}.py` + `tests/{conftest,test_batch_layout}.py` | `27-01-SUMMARY.md` (Self-Check: PASSED, commits `159388f`, `3e6db96`, `9f00fc8`) | ✓ RECORDED |
| `contracts/harness/adoption/approval.schema.json` + `docs/reference/approval.md` + rebaselined `contracts/.hashes/manifest.json` | `27-02-SUMMARY.md` (Self-Check: PASSED, commit `c5e91bb`) | ✓ RECORDED |
| `tools/adoption_apply/apply.py` + `tests/{test_constitution_refusal,test_atomic_apply}.py` | `27-03-SUMMARY.md` (commit `12b058d`) | ✓ RECORDED — but see SC-2; the file existed and its controls were incomplete |
| `tools/adoption_apply/approval.py` + `tests/test_approval_invalidation.py` | `27-04-SUMMARY.md` | ✓ RECORDED |
| 3 fixture trees + `tests/test_fixtures.py` | `27-05-SUMMARY.md` (Self-Check: PASSED, commit `13df97e`) | ✓ RECORDED |
| `tools/adoption_apply/cli.py` + `tests/test_cli.py` + `harness/commands/adopt.md` + `harness/skills/brownfield-adoption/SKILL.md` + both emitted runtime trees | `27-06-SUMMARY.md` (Self-Check: PASSED, commits `aacae02`, `bf0c4c3`) | ✓ RECORDED |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `batch.py` | `task_control/manager.py`'s CAS idiom | **copied, not imported** — deliberate, to avoid a private cross-package import (`27-01-SUMMARY.md` key-decisions) | WIRED (as recorded) |
| `approval.py::promote` | `golden_runner/approve.py`'s three-signal refusal order | same `GOLDEN_APPROVE_HUMAN` env var reused rather than a second adoption-specific variable (`27-04-SUMMARY.md`) | WIRED (as recorded) |
| `cli.py` | `batch.py` / `apply.py` / `approval.py` | argparse subparsers with `set_defaults(func=...)`, "each handler importing and calling only the already-audited […] functions" (`27-06-SUMMARY.md`) | WIRED (as recorded) |
| **`apply` write path** | **`approval.check_valid()`** | — | **NOT WIRED at close.** `27-REVIEW.md` CR-03: "called nowhere outside its own unit test", while `brownfield-adoption/SKILL.md` told its reader that promotion gates the apply. |

### Behavioral Spot-Checks

**These are the phase's own recorded runs, transcribed. This document ran nothing.** The counts are
quoted exactly as written; none is rounded or inferred.

| Behavior | Command | Result as recorded | Recorded in |
|---|---|---|---|
| Adoption package suite | `uv run pytest tools/adoption_apply -q` | 4 passed | `27-01-SUMMARY.md` |
| Workspace/lockfile stability | `uv sync --all-packages`; `git diff --exit-code uv.lock` | clean, exits 0 | `27-01-SUMMARY.md` |
| Contract drift | `uv run python -m tools.contract_drift.drift` | exits 0 / OK | `27-02-SUMMARY.md` (orchestrator-verified), `27-05-SUMMARY.md` |
| Package suite (27-03) | `uv run pytest tools/adoption_apply -q` | 18/18 green | `27-03-SUMMARY.md` |
| **Full suite (27-03)** | `uv run pytest -q` | **RED** — `test_contracts_index.py::test_render_matches_committed_snapshot`, ".ambr says 13 contract(s)" vs live 14. Declared pre-existing at `0de779d` and deferred, not fixed | `27-03-SUMMARY.md`, `deferred-items.md` |
| Full suite (after 27-04) | `uv run pytest -q` | 1079 passed (was 1072; +7 new, 0 regressions) | `27-04-SUMMARY.md` |
| Fixture end-to-end | `uv run pytest tools/adoption_apply/tests/test_fixtures.py -q` | **3 passed** | `27-05-SUMMARY.md` |
| GEN-04 core→example independence | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | 18 passed | `27-05-SUMMARY.md` |
| Full suite (after 27-05) | `uv run pytest -q` | 1082 passed (was 1079; +3 new, 0 regressions) | `27-05-SUMMARY.md` |
| Emit round-trip | `uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude` | clean, no drift | `27-05-SUMMARY.md` |
| Emitter suite | `uv run pytest tools/harness_emit -q` | 47 passed | `27-06-SUMMARY.md` |
| Command/skill lint | `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_skills.py -q` | 147 passed | `27-06-SUMMARY.md` |
| Full suite at phase close | `uv run pytest -q` | 1096 passed (up from the 1082 pre-plan baseline) | `27-06-SUMMARY.md` |

Suite-count sequence across the phase: **1072 → 1079 (27-04) → 1082 (27-05) → 1096 (27-06)**.
27-01 and 27-03 record package-scoped counts only, and **27-03's full-suite run is red**, so
**1096 is the only defensible phase-final figure.**

**What the green suite did and did not mean.** Every number above is real. `27-REVIEW.md` and the
27.1 insertion rationale both make the same point about them: the suite was green *and* three
load-bearing controls were bypassable, because "`apply.py`'s own test suite proves the *narrow*
cases (`refuse_if_constitution` on a literal `contracts/x.json` string) but never a
traversal/absolute/case variant". A green suite is evidence about the tests that exist, not about
the ones that do not.

### Review Findings

Transcribed from `27-REVIEW.md` (`reviewed: 2026-07-21`, 52 files, `status: issues_found`).

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| CR-01 | Critical | `refuse_if_constitution` bypassed by `..`-traversal or case-variant destination (`apply.py:74-84`) | Closed by Phase **27.1** (its ROADMAP insertion rationale names this bypass explicitly) |
| CR-02 | Critical | No destination confinement — absolute-path/`..` destination writes outside `target_root` | Closed by Phase **27.1** |
| CR-03 | Critical | `approval.check_valid()` never consulted by the write path — the ADOPT-06 gate is decoupled from `apply` | Closed by Phase **27.1** |
| WR-01 | Warning | `_apply_marker_merge` does an unlocked read-modify-write; concurrent applies can race (`apply.py:166-185`) | Open in 27; fixed per **27.1** (`fcntl.flock`, `apply.py:246-249`). Its regression test was later re-flagged as 27.1's WR-07 and closed in **27.2** |
| WR-02 | Warning | `check_valid` raises instead of returning `False` when a draft artifact is missing (`approval.py:172-187`, `57-63`) | Open in 27; `27.1-VERIFICATION.md` records it as **only partially** fixed there; full closure attributed to **27.2** (its WR-06, 12-row corruption table) |
| WR-03 | Warning | `manifest.schema.json`'s `destination` has no path-shape constraint. The review itself says "flagged here for the record, not to be auto-fixed by an agent" | Open in 27; fixed per **27.1**. `27.2-VERIFICATION.md` § Residual Tracking still records "`manifest.schema.json` still admits `"."`/`"./"`/`"a/"` (runtime-only closure per D-08)" |
| WR-04 | Warning | `_cmd_apply` never re-validates `manifest.json` against its schema before use (`cli.py:138-159`) | Open in 27; fixed per **27.1** |
| **IN-01** | Info | `apply.py` docstring's security claim is broader than what the code proves (`apply.py:1-37`) | **NO DISPOSITION IN ANY ARTIFACT, IN ANY PHASE.** See G-3. |
| **IN-02** | Info | `_recompute_draft_hash` hashes bytes in a fixed order but never validates their `sha256`/schema shape (`approval.py:57-63`) | **NO DISPOSITION IN ANY ARTIFACT, IN ANY PHASE.** See G-3. |

> **Do not conflate IN-01/IN-02 with 27.1's same-numbered findings.** Phase 27.1's `IN-01`/`IN-02`
> are **different findings that reuse the IDs**. Reading 27.1's dispositions as covering these two is
> the specific error this note exists to prevent — an earlier draft of this document made it.
>
> `27-REVIEW.md` also records: "## Structural Findings (fallow) — None provided for this review — no
> `<structural_findings>` block was supplied."

### Deferred Items

From `deferred-items.md` (one item):

| Item | Status |
|---|---|
| **27-03**: `tools/memory_regen/tests/test_contracts_index.py::test_render_matches_committed_snapshot` fails — committed `.ambr` says "13 contract(s)", live tree has 14 after 27-02's `approval.schema.json`. Confirmed pre-existing at `0de779d` (byte-identical test file, failure reproduces there). Deferred as out of scope for a code-only plan. | Recorded as resolved in substance by the phase close — `27-06-SUMMARY.md` records the full suite green at 1096, which the snapshot mismatch would have reddened. **No artifact states who rebaselined it.** See Gaps G-4. |

### Anti-Patterns and Process Notes

Recorded because the SUMMARYs recorded them, not because this document found them.

| Item | Recorded in | Note |
|---|---|---|
| `HARNESS_DEV_BYPASS=1` permitted the 27-02 constitution-plane mechanical write | `27-02-SUMMARY.md` | The SUMMARY is careful and explicit that this is "the mechanical-write permission only, NOT a substitute for or conflated with the human ratification recorded here", and records a separate blocking `checkpoint:human-verify` in which the operator reviewed the schema text, the manifest diff, the derived-plane diff, and the A1 design call — plus five independent orchestrator checks. This is the same provenance shape later tracked milestone-wide as RAT-4. |
| Working-tree mishap during 27-03 | `27-03-SUMMARY.md` § Deviations | An investigatory `git stash -u` + `git checkout 3a4c493 -- .` reverted four `.planning/*` files; detected, restored, net-zero diff, `git diff HEAD --stat` confirmed empty. Self-reported rather than hidden. |
| SC-3's "zero `subprocess.run` calls" reinterpreted | `27-05-SUMMARY.md` § Deviations | The plan's literal wording was unsatisfiable against the real pipeline (`scan.py` legitimately shells out to `git`). Resolved by spying with `wraps=subprocess.run` and asserting every argv is one of two fixed target-scoped shapes — i.e. that **no argv is ever derived from manifest/draft/scanned content**, which is the property ADOPT-07 actually requires. Recorded here because it is a case of a plan's letter being weaker than its intent, and the executor saying so. |
| Two `.ambr` snapshot updates (27-02 docs-sync, 27-06 emit) | `27-02`, `27-06` SUMMARYs | Both recorded as additive-only / ordering-safe, with 27-06 explicitly running the suite green **before** touching the committed runtime trees. |

---

## Gaps Summary

These are the things this closeout **could not establish**. They are the reason the document is
trustworthy where it does make a claim, so they are not an appendix.

- **G-1 — No contemporaneous verification exists, and this is not one.** Every SC row above is a
  transcription of a *self-report* plus, where it exists, a *review* of that self-report. No
  independent phase-time verifier re-derived Phase 27's claims against the codebase the way
  `27.2-VERIFICATION.md` did for 27.2 (where the verifier re-ran the concurrency test with `flock`
  neutered and reconciled RED claims against pre-fix source). That difference is exactly why SC-2's
  failure was found by the reviewer rather than by a verifier, and why it was found at all only
  because a review happened.
- **G-2 — SC-4's "모델 id 없음" half rests on an unrecorded grep.** The no-new-persona half is
  structurally checked (`test_commands.py`/`test_skills.py`, 147 passed). The no-model-identifier
  half is asserted in prose — "and a grep for model-name tokens" — with **no command and no output
  recorded**. It must not be read as a verified negative.
- **G-3 — `27-REVIEW.md` IN-01 and IN-02 have NO disposition in ANY artifact, in ANY phase.** They
  are not known to be fixed and not known to be accepted; they are simply unaddressed in the record.
  **This is a genuinely open, previously unrecorded pair surfaced by the DEBT-02 sweep, not a
  Phase 27 fact that was already tracked.** They are recorded as open in
  `.planning/phases/35-carried-debt-dispositions-v2-4-b/deferred-items.md` so they survive this
  document. **They are distinct from 27.1's same-numbered IN-01/IN-02**, which are different
  findings that reuse the IDs.
- **G-4 — The `deferred-items.md` snapshot mismatch has no recorded closure.** The full suite is
  recorded green at phase close, which implies the `.ambr` was rebaselined, but **no artifact says
  by whom or in which commit.** The closure is inferred from a test count, which is weaker than a
  citation.
- **G-5 — Test counts are transcribed, not reproduced.** 1079 / 1082 / 1096 / 47 / 147 / 18 / 3 / 4
  are quoted exactly as the SUMMARYs wrote them. This document did not re-run any of them, and a
  re-run today would measure a tree that phases 27.1, 27.2, 28 and 29 have since changed — a
  different thing, not better evidence.
- **G-7 — the phase's evidence is prose, not machine output.** Three specifics, because they bound
  how much any row above can be trusted: (a) **no file:line citation exists in any of the six
  SUMMARYs** — every file:line reference in the phase comes from `27-REVIEW.md` and therefore cites
  a *defect*, never passing evidence, so an "evidence at file:line" column could not be filled;
  (b) **only two numeric exit codes exist phase-wide** (27-06's exit 3 for `promote`, 27-01's
  "exits 0" for `uv sync`) — every other gate is recorded as prose "clean"/"green"/"OK"; (c)
  **27-02 records no numeric pass count at all** — its `tools/docs_sync` run is recorded as having
  FAILED, then resolved by `--snapshot-update` ("18 insertions, 0 deletions"), with no post-fix
  count stated.
- **G-8 — two plans' literal acceptance criteria were relaxed at execution time.** 27-05's "zero
  `subprocess.run` calls" became "zero non-fixed-argv calls"; 27-06's sketched
  `apply_manifest(..., batch_dir=)` was superseded by the real signature. Both are recorded and
  reasoned in their SUMMARYs, but it means **a row quoting a PLAN's criterion verbatim would not
  match what was actually proven** — which is why the rows above quote SUMMARYs rather than PLANs.
- **G-6 — `27-VALIDATION.md`'s per-task status column was never filled in.** All 25 rows still read
  `⬜ pending` with `❌ W0` file-exists markers, despite the phase having completed. The validation
  contract was approved and then not updated as execution proceeded, so it cannot serve as
  independent per-task evidence — only as evidence of what coverage was *intended*.

## Human Verification Required

None outstanding **for Phase 27 itself** — its Critical findings were remediated by the inserted
phases 27.1 and 27.2, both of which have their own verification reports, and 27.2's is `status:
passed` at 5/5 with verifier-run mutation evidence.

Three items are for a human, and the third is the only one that is actually outstanding work:

1. **SC-2's three Criticals were never dispositioned inside Phase 27.** They were closed in 27.1,
   which is why the phase is not marked failed — but the phase closed with them open and unanswered.
   Whether the ROADMAP's Phase 27 checkbox should reflect that is a bookkeeping decision outside
   this document's authority.
2. **SC-1's enforcement half and SC-4's model-id half were never evidenced.** Both are now stated as
   such rather than carried as implied passes.
3. **G-3 — `27-REVIEW.md` IN-01 and IN-02 are genuinely open and were previously unrecorded.** They
   are the one item here that needs a decision rather than a note: either a disposition (including
   an explicit "accepted, will not fix" with a reason) or promotion to a requirement. They are
   tracked at `.planning/phases/35-carried-debt-dispositions-v2-4-b/deferred-items.md` as
   `P27-IN-01` / `P27-IN-02` so they cannot be lost again.

---

## What this phase's record actually demonstrates

Worth stating plainly, because it is the reusable lesson and it is *in* the artifacts rather than
invented here: Phase 27 shipped with a green 1096-test suite, a clean contract-drift gate, a clean
emit round-trip, and six SUMMARYs each reporting their plan complete — and its central safety
control was bypassable by a `..` in a string. What caught it was `27-REVIEW.md`, an adversarial read
that went looking for input shapes no test supplied. The two phases inserted immediately after
(27.1, 27.2) exist entirely because of that review.

That is the same finding the v2.4 requirements later generalize as LANE-02 ("4 of its 10 phases
exist because adversarial review found real defects"). Phase 27 is the case study.

---

_Authored at closeout: 2026-07-22 — transcribed from pre-existing artifacts only._
_This document verifies nothing prospectively and did not execute any check of its own._
