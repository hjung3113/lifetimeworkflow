---
phase: 29
slug: docs-drive-loop-adoption-integration-closeout-v2-3-c
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-21
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Authored at closeout by plan 29-05 and reconciled against what actually ran, so that a phase
> auditing two missing VALIDATION.md files (27.2, 28) does not silently become a third.
> Source: `29-RESEARCH.md` + `29-CONTEXT.md` D-01..D-15.

**Standing rule for this phase:** every control-shaped change gets its adversarial-input table
authored FIRST and shown RED against pre-fix code. Carried forward unchanged from 27.1 SC-5 and
27.2 SC-4 — a test that cannot fail when the control regresses is not coverage.

**Second standing rule, specific to this phase:** the agent may not author
`docs/.docs-review-ledger.toml`, in the repo or in a scratch directory. A green gate reached by an
agent-authored disposition is exactly the failure Theme C exists to prevent.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (workspace-pinned; no new package) |
| **Config file** | root `pyproject.toml` (uv workspace) |
| **Quick run command** | `uv run pytest tools/docs_guard -q` |
| **Full suite command** | `uv run pytest -q` |
| **Baseline at phase start** | 1459 passed (`28-VERIFICATION.md`, commit `56cbac7`) |
| **Observed at phase end** | **1473 passed, 8 snapshots passed** (commit `bad6749`) |

`uv.lock` unchanged at phase end.

---

## Sampling Rate

- **After every task commit:** the owning module's suite (`tools/docs_guard`,
  `tools/adoption_apply`, `tools/harness_lint`, `tools/harness_emit`)
- **After every plan wave:** `uv run pytest -q` + `uv run python -m tools.contract_drift.drift`
- **Phase gate:** the full SC-4 fan-in, recorded with actual numbers in
  `.planning/v2.3-MILESTONE-AUDIT.md` — never as "green"
- **Max feedback latency:** 12 seconds (quick), 90 seconds (full)

> **Inherited pitfall — do not repeat (D-03).** `emit-drift` uses bare `git diff`, which is blind to
> untracked files. Every emit round-trip in this phase was verified with `git status --porcelain`.
> Plan 29-03 hit the real instance: bare `git diff` reported clean while four newly emitted files
> were untracked.

---

## Per-Task Verification Map

| Task | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Status |
|------|------|------|-------------|------------|-----------------|-----------|-------------------|--------|
| 1–2 | 29-01 | 1 | **SC-1** / DOCSUP-06 | D-06 | `exclusion_reason()` classifies contracts / golden / accepted-ADR / derived / emitted twins, with `./`, `CONTRACTS/`, and `docs/../contracts/` spellings all caught, and a negative control still ALLOWED | unit (15-row table, 6 classes) | `uv run pytest tools/docs_guard/tests/test_exclusions.py -q` | ✅ green |
| 1–2 | 29-01 | 1 | **SC-1** | D-06 | The glob lists are IMPORTED, never retyped — deleting a glob at its home reds named rows repo-wide | unit (3 `is`-identity + 3 per-class deletion proofs) | same file | ✅ green |
| 1 | 29-02 | 1 | **SC-2** / DOCSUP-07 | ADR-0010 3b layers 1+2 | One apply cycle lands the registry proposal AND buckets the ledger destination `refused` before any byte is written; the raised type is `ReviewLedgerRefusal`, NOT a `ConstitutionRefusal` | integration (zero-write spy over `builtins.open` + `tempfile.mkstemp`) | `uv run pytest tools/adoption_apply/tests/test_docs_binding_proposal.py -q` | ✅ green |
| 2 | 29-02 | 1 | **SC-2** | ADR-0010 3b layer 3 | A registry-only binding and a same-commit self-blessed binding cannot classify `FRESH`; a REPOINTED already-ratified id cannot either (CR-03) | integration (hermetic real-`git init` fixture) | `uv run pytest tools/docs_guard/tests/test_selfgreen_end_to_end.py -q` | ✅ green |
| 1–3 | 29-03 | 2 | **SC-1** / DOCSUP-06 | D-02, D-04 | `/docs-update` + `docs-upkeep` emit byte-identically to both runtimes; `EXPECTED_SKILLS` 12→13 and command count 24→25 move in the SAME change; the command body contains NO `.memory/` path at all | lint + emit round-trip | `uv run pytest tools/harness_lint/tests/test_docs_update_wiring.py -q`; `uv run python -m tools.harness_emit` then `git status --porcelain` | ✅ green (100 artifacts, porcelain empty) |
| 1 | 29-04 | 3 | **SC-3** | T-29-16 | Every ledger digest re-derived by CALLING `guard.classify()`, never hand-hashed | tool invocation | `classify(registry_path=…)` | ✅ green |
| 2 | 29-04 | 3 | **SC-3** | T-29-20 | The ledger is authored by a HUMAN, outside an agent session | manual — blocking human gate | none possible | ⬜ **BLOCKED ON HUMAN (RAT-1)** |
| 3 | 29-04 | 3 | **SC-3** | — | One bounded drive-loop edit on the stale `gate-model` prose, visible to the gate | guard before/after | `uv run python -m tools.docs_guard` | ⚠️ partial — target digest moved `4568f3a9… → 8df85e6e…`, but the `0 → 1 → 0` transition is unobservable until RAT-1 (deviation D-2) |
| 4 | 29-04 | 3 | **SC-3** | T-29-20 | Post-ledger confirmation run | manual — blocking human gate | `uv run python -m tools.docs_guard` (expect exit 0) | ⬜ **BLOCKED ON HUMAN (RAT-1)** |
| 1 | 29-05 | 4 | **SC-4** | T-29-18, T-29-21 | All twelve fan-in items run with command + exit code + headline number recorded; nothing repaired mid-run | gate fan-in | see the audit's SC-4 table | ✅ ran — 2 reds recorded verbatim, not repaired |
| 2 | 29-05 | 4 | **SC-4** / DOCSUP-06, 07 | T-29-19, T-29-23 | Every residual, every nyquist gap and every outstanding ratification survives the close | process artifact | per-finding `grep` loop over the audit | ✅ green |

*Status: ⬜ pending/blocked · ✅ green · ❌ red · ⚠️ partial*

---

## Wave 0 Requirements

- [x] `tools/docs_guard/tests/test_exclusions.py` — the 6-class adversarial spelling table with a
      negative control that must stay ALLOWED, RED-first against the absent classifier
- [x] `tools/adoption_apply/tests/test_docs_binding_proposal.py` — zero-write spy patching the REAL
      publish primitives (`builtins.open`, `tempfile.mkstemp`), not a wrapper the code could bypass
- [x] `tools/docs_guard/tests/test_selfgreen_end_to_end.py` — hermetic real-`git init` fixture, so
      the `previous committed ledger/registry` retrieval is exercised for real
- [x] `tools/harness_lint/tests/test_docs_update_wiring.py` — an ASSERT-THE-ABSENCE lint (no glob
      literal, no derived-queue path), because D-04's fresh-clone false green is a shape a later
      edit could reintroduce
- [x] Framework install: none

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Authoring `docs/.docs-review-ledger.toml` | DOCSUP-06, DOCSUP-07 (SC-3) | The ledger is the greenness authority. Three layers deny the agent write and NO token opens any of them — not `GOLDEN_APPROVE_HUMAN`, not `HARNESS_DEV_BYPASS`. A self-blessed row and an honest seed row are byte-identical; only the human commit separates them | `29-04-SUMMARY.md`, Option A or B; author against the POST-edit tree |
| Ratifying the eight seeded bindings' dispositions | DOCSUP-07 | `first_seen-unratified` is a HISTORY test by design | Confirm each (sources, target) pair is an obligation you accept, before its first `[[reviewed]]` row |
| Flipping ADR-0010 `proposed` → `accepted` | DOCSUP-01..07 (Phase 28 carry) | It landed under `HARNESS_DEV_BYPASS`, which is explicitly NOT a ratification; `registry._adr_status` treats a non-accepted ADR as a rejection | Read clause 3b; fill Date and Deciders; update `docs/adr/README.md` |
| Milestone closeout approval | SC-4 | An audit's `gaps`/`nyquist`/`tech_debt` rows are judgement records | Blocking `checkpoint:human-verify` in plan 29-05 task 3 |

---

## Validation Sign-Off

- [x] Every plan's control-shaped task authored its adversarial table first with the RED run
      recorded (29-01 task 1 before task 2; 29-02 mutation-proves each claim)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter
- [x] The two human-only tasks are recorded as BLOCKED, never as green — 29-04 tasks 2 and 4 are
      `gate="blocking-human"` and were not attempted

**Approval:** authored at closeout by plan 29-05 and reconciled against the executed record
(`29-01`..`29-04` SUMMARYs) rather than written ahead of the phase. Two rows remain blocked on
human ratification and are carried into `.planning/v2.3-MILESTONE-AUDIT.md` as RAT-1..RAT-3.
