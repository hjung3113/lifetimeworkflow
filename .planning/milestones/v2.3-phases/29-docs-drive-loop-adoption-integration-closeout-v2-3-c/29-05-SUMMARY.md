---
phase: 29-docs-drive-loop-adoption-integration-closeout-v2-3-c
plan: 05
subsystem: milestone-closeout
status: PARTIAL — tasks 1 and 2 executed; task 3 is a blocking human checkpoint
tags: [milestone-audit, SC-4, nyquist, tech-debt, human-ratification, v2.3]
requires:
  - .planning/milestones/v2.1-MILESTONE-AUDIT.md (the frontmatter template, D-14)
  - .planning/phases/28-*/28-REVIEW.md + 28-FIXES.md + 28-VERIFICATION.md
  - .planning/phases/27.2-*/27.2-VERIFICATION.md
  - .planning/phases/29-*/29-01..04-SUMMARY.md
provides:
  - .planning/v2.3-MILESTONE-AUDIT.md — the closeout record, verdict `blocked_on_human`
  - .planning/phases/29-*/29-VALIDATION.md — Phase 29's own nyquist record
affects:
  - .planning/REQUIREMENTS.md, .planning/ROADMAP.md, .planning/STATE.md
key-files:
  created:
    - .planning/v2.3-MILESTONE-AUDIT.md
    - .planning/phases/29-docs-drive-loop-adoption-integration-closeout-v2-3-c/29-VALIDATION.md
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
decisions:
  - "DOCSUP-06/07 are NOT marked [x]. They are machinery-complete and gate-tested, but `tools.docs_guard` exits 1 until a human authors the ledger. Marking them complete would be the self-blessing the requirements exist to forbid — recorded as `Machinery complete — BLOCKED on human ratification (RAT-1)` instead. This is a deliberate deviation from the plan's task-2 instruction."
  - "Two red gate items were recorded verbatim and NOT repaired (T-29-21): the `lifecycle-eval` job's step 2 (a NEW finding) and the example .NET golden on macOS."
  - "The five outstanding ratifications are given ids RAT-1..RAT-5 so later phases can cite them individually."
metrics:
  tasks_executed: 2 of 3
  tasks_blocked_on_human: 1
  commits: 1
  fan_in_items_run: 17 commands across 12 SC-4 items
---

# Phase 29 Plan 05: v2.3 Milestone Closeout Summary

The SC-4 fan-in was run once, in full, with every command's exit code and headline number recorded
verbatim; `.planning/v2.3-MILESTONE-AUDIT.md` was written against the v2.1 precedent with a
per-requirement evidence row for all 21 v2.3 requirements, the observed nyquist gaps, all eleven
28-REVIEW findings with dispositions, every standing residual since 26.2, and five outstanding
human ratifications. **Verdict: `blocked_on_human`, 19/21 requirements evidenced.**

## Task 1 — the SC-4 fan-in, actual numbers

Run at commit `bad6749`, working tree clean. Commands read out of `.github/workflows/ci.yml`, not
reconstructed. Nothing was repaired during the run.

| SC-4 item | Exit | Observed |
|---|---|---|
| full `uv run pytest -q` | 0 | **1473 passed, 8 snapshots passed** in 74.05s |
| contract-drift root | 0 | `OK — live manifest matches the committed baseline` |
| contract-drift example | 0 | `OK — live manifest matches the committed baseline` |
| golden root (`tools/golden_runner`) | 0 | **17 passed** |
| golden example (`examples/log-parser/tests`) | **1** | **2 failed, 10 passed** — macOS-host artifact, see below |
| workspace drift (`--workspace`) | 0 | all members clean, every edge resolved |
| workspace pytest set | 0 | **31 passed** |
| stale-derived regen + diff | 0 | 13 reference pages + 15 contracts indexed; diff exit 0, porcelain empty |
| lifecycle runner | 0 | **20/20 fixtures PASS**, `false_downgrades_enforced_zero: true` |
| lifecycle pytest | **2** | **RED at collection** — NEW finding, see below |
| GEN-04 twin | 0 | **24 passed** |
| full `tools/harness_lint` | 0 | **316 passed** |
| docs guard | **1** | **6 × `broken-binding`, 2 × `STALE_ADVISORY`; 8 bindings, 7 uncovered** — expected, no ledger |
| docs guard unit tests | 0 | **244 passed, 1 snapshot** |
| emit round-trip | 0 | **100 artifacts, `git status --porcelain` EMPTY** (untracked-visible, not bare `git diff`) |
| model-identifier lint | 0 | **47 passed** (5 in the `-k model` subset) |
| injector budget | 0 | **22 passed** |
| contract-check | 0 | **2 schema/instance pairs**, both valid |
| `git diff --check` | 0 | clean |

**Phase 29 added ZERO CI jobs and ZERO `gate.needs` entries (D-11). `git diff --check` remains a
verification command, never a job (D-12).**

### The two reds, recorded not repaired

**NEW finding — the `lifecycle-eval` job's step 2 is red, platform-independently.**
`uv run pytest tools/lifecycle_eval` (`ci.yml:194`, the command as written) errors at collection:
`ModuleNotFoundError: No module named 'tools'`. `tools/lifecycle_eval/tests/` is the only tools
member's tests dir carrying neither `__init__.py` nor a repo-root-inserting `conftest.py` — every
sibling has one (`tools/harness_lint/tests/conftest.py:20-23`). Under the full suite it imports
fine by side effect of a sibling conftest, which is why 1473 pass while the isolated job command
errors. Step 1 of the same job is green.

**Example .NET golden — a macOS-host artifact, not a repo defect.** `toy-converter exited 3: path
confinement violation`. pytest's `tmp_path` realpaths to `/private/var/folders/…` while .NET's
`Path.GetTempPath()` returns the `/var/folders/…` spelling, and `IsConfined`
(`examples/log-parser/components/toy-converter/Program.cs:163-183`) compares with
`StringComparison.Ordinal`. The job runs `ubuntu-latest`, where both are `/tmp`.

**Whitespace note.** `git diff --check` is clean only because the tree is clean.
`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` carries **983** committed
trailing-whitespace lines (980 at the Phase-29 base) — a syrupy generator artifact in a derived
snapshot, not hand-authored debt.

## Task 2 — the audit

`.planning/v2.3-MILESTONE-AUDIT.md`, v2.1 frontmatter shape: `milestone` / `milestone_name` /
`audited` / `status` / `scores` / `gaps` / `nyquist` / `outstanding_ratifications` / `tech_debt`.

- **21 requirement evidence rows** — TOPO-01..07, ADOPT-01..07, DOCSUP-01..07 — each citing the
  artifact that proves it. STATE.md's percentages appear nowhere as evidence; the audit instead
  carries an explicit note that the SDK's `completed_phases` / `percent` counters are a mechanical
  SUMMARY-file count and OVERSTATE, since Phases 28 and 29 are not closed.
- **Nyquist, as observed by `ls` this session** (not as the plan's `<interfaces>` predicted — 28
  gained a VERIFICATION.md after planning): VALIDATION.md absent for **27.2 and 28**;
  VERIFICATION.md absent for **27 and 29**. Recorded as partial, never back-filled.
- **`29-VALIDATION.md` authored**, so a phase auditing two missing VALIDATION.md files does not
  become a third. Its two human-only rows are recorded as BLOCKED, never as green.

### tech_debt — nothing dropped

All eleven 28-REVIEW findings with dispositions checked against the tree rather than assumed:
CR-01 `86ecad5`, CR-02 `ef793a8`, CR-03 `2b504a6`, WR-01 `d49bdc9`, WR-02 `d6a7f63`, WR-03
`59870d9`, WR-04 `d17e764`, IN-01 `b329fce`, IN-02 `1810085` — all **fixed**; **IN-03 accepted**
as the residual (graph recompiled per binding; re-verified live at `cli.py:233` and
`docs_staleness.py:100`).

Plus, each re-verified present in the tree: `tools/hooks/secret_scan.py:44-47` (patterns hardcoded,
carried unchanged since 26.2); 27.2's AD-01, AD-02, the D-04 deviation and the pre-existing `I001`
on `tools/adoption_apply/cli.py` (`ruff check` → `Found 1 error`); 27.1's IN-02 (flock/NFS) and
WR-08 (parent-dir symlink TOCTOU) — kept distinguishable from 28's identically-numbered IN-02; the
`examples/**` instance-overlay seam left open by 28-CONTEXT D-14; `emit-drift`'s bare `git diff`
untracked blindness (15-REVIEW CR-01, still bare at `ci.yml:213`); the new `lifecycle-eval`
finding; `ruff check` not being a CI gate at all; and DEF-05-02-1.

### The five outstanding human gates, in discharge order

1. **RAT-1** — hand-author `docs/.docs-review-ledger.toml` from the byte-exact proposal in
   `29-04-SUMMARY.md`, **against the POST-edit state**: 29-04's bounded `gate-model` prose fix moved
   that binding's `target_digest` from `4568f3a9…` to `8df85e6e…`. Option A is one round straight to
   exit 0; Option B is two rounds and observes the `0 → 1` leg for real.
2. **RAT-3** (discharged inside RAT-1) — ratify the eight seeded bindings' dispositions before their
   first `[[reviewed]]` rows. A self-blessed row and an honest seed row are byte-identical.
3. **RAT-2** — review ADR-0010 and flip `Status: proposed` → accepted, filling Date and Deciders
   (both em-dashes today).
4. **RAT-4** — the Phase-28 constitution-plane schema write (`doc-dependencies.schema.json`, plan
   28-01) landed via `HARNESS_DEV_BYPASS` per ADR-0007. That is **not** a human ratification.
   Recorded as outstanding.
5. **RAT-5** — ADR-0004/0005/0006/0007 remain unmerged to `main`, and CODEOWNERS cannot fire on a
   solo-authored PR.

## Deviations from Plan

**D-1 [judgement] DOCSUP-06/07 were NOT marked `[x]` in REQUIREMENTS.md.**
- Found during: task 2 bookkeeping.
- Issue: the plan says "mark DOCSUP-06 and DOCSUP-07 `[x]`". Both are machinery-complete, but
  `tools.docs_guard` exits 1 until a human authors the ledger, and DOCSUP-07's own text requires a
  "정상 사람-review 변경" that has not happened.
- Resolution: the Traceability rows read `Machinery complete — BLOCKED on human ratification
  (RAT-1)` with a short prose note explaining why, and the audit scores 19/21 to match. Ticking the
  box would have been the self-blessing Theme C exists to forbid, and would have contradicted the
  audit written in the same commit.

**D-2 [observed, not predicted] the plan's `<interfaces>` nyquist state was stale.** It recorded
"VERIFICATION.md ABSENT for 27 and 28"; `28-VERIFICATION.md` has since been written
(`status: human_needed`, 4/4 truths). The audit records the `ls` observed this session, per the
plan's own instruction to populate `nyquist` from task 1's observation.

**D-3 [reported, not forced] two red fan-in items.** Recorded verbatim as `gaps.integration` rows
with root causes, per T-29-21. Neither was repaired; the `lifecycle-eval` fix is listed under
"Recommended before close (non-blocking)".

## Scope respected

`docs/.docs-review-ledger.toml` was **not** created, drafted, staged or committed — anywhere,
including the scratchpad. ADR-0010 was not touched and remains `Status: proposed`.
`GOLDEN_APPROVE_HUMAN` and `HARNESS_DEV_BYPASS` were neither set nor forged. No `git add -A`/`.`/
`-a`; no `git clean`/`stash`/`reset --hard`/blanket restore. No model identifier, no wall-clock
timestamp and no human identity in any new artifact; `git diff --check` clean, LF/no-BOM throughout.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change — this plan writes
planning documents only.

## Self-Check

- `.planning/v2.3-MILESTONE-AUDIT.md` — FOUND (21 requirement rows; all 14 residual ids present)
- `.planning/phases/29-…/29-VALIDATION.md` — FOUND
- `.planning/REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` — FOUND (modified)
- `docs/.docs-review-ledger.toml` — **ABSENT, as required**
- ADR-0010 — still `Status: proposed`, Date and Deciders still em-dashes

## Self-Check: PASSED
