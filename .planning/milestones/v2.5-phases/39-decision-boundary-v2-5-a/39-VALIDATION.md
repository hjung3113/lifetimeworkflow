---
phase: 39
slug: decision-boundary-v2-5-a
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-26
revised: 2026-07-26
---

# Phase 39 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `39-RESEARCH.md` § Validation Architecture. This phase is decision-record-only
> (prose + frontmatter + `.planning/STATE.md`), so verification is grep-assisted content
> assertion plus a no-regression check on the existing suites. No new test file is added.
>
> **Revised 2026-07-26** per cross-AI review (`39-REVIEWS.md`): verify commands below assert
> exact counts (not `>= N` presence-checks), key STATE.md checks on the unique `v2.5 P39,
> ADR-0012` marker, and require a pre-write dirty-worktree baseline before any diff-based proof.
> This revision keeps this document in sync with `39-01-PLAN.md`/`39-02-PLAN.md` — see those
> files for the full task-level action text.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (existing `core-suite` CI job) — no new automated test added; deliverable is prose/frontmatter, not executable behavior |
| **Config file** | root `pyproject.toml` (pre-existing, unchanged) |
| **Quick run command** | `grep -n "^- \*\*Status:\*\*" docs/adr/0001-*.md docs/adr/0010-*.md docs/adr/0011-*.md docs/adr/0012-*.md` |
| **Full suite command** | `uv run pytest && uv run python -m tools.contract_drift.drift` |
| **Estimated runtime** | ~120 seconds (full), ~1 second (quick) |

---

## Sampling Rate

- **After every task commit:** Run the quick grep assertion for that task's target file.
- **After every plan wave:** Run `uv run pytest` + `uv run python -m tools.contract_drift.drift` + `uv run python -m tools.harness_emit` then `git diff --exit-code` on `.claude/` and `.opencode/` (ADR edits must produce zero emission drift) — gated on a pre-run `git status --porcelain -- .claude .opencode` baseline being clean; if dirty, STOP and report rather than run the check.
- **Before `/gsd:verify-work`:** Full suite green, **excluding the pre-existing out-of-scope `docs-guard` RED** (`task-control-cli-howto` staleness, red before this phase — see RESEARCH § Pitfalls). This phase must neither fix nor worsen it — verified as a failing-binding SET comparison against the documented baseline `{task-control-cli-howto}`, not a substring presence-check.
- **Max feedback latency:** ~120 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| ADR-0012 authored | 01 | 1 | CER-01 | T-39-01 | Written under the `contract_guard` deny — human-ratified via the single session-env-var token path, never bypassed; pre-write baseline recorded before edit | manual (grep-assisted, exact-count) | `test -f docs/adr/0012-ci-and-merge-as-decision-authority.md; test "$(grep -c '^- \*\*Status:\*\* accepted' docs/adr/0012-*.md)" -eq 1; test "$(grep -c '^- \*\*Supersedes:\*\* 0001, 0010' docs/adr/0012-*.md)" -eq 1` | ❌ created by this phase | ⬜ pending |
| ADR-0012 clause (b) precise + time-scoped enumeration | 01 | 1 | CER-01 | — | Component-by-component list, scoped as intent at ratification time (D1) | manual (read-through) | `grep -c "tools/docs_guard\|ledger_guard\|registry.lock" docs/adr/0012-*.md` (presence, content quality confirmed by human read) | ❌ created by this phase | ⬜ pending |
| ADR-0012 one-off-checkpoint clause | 01 | 1 | CER-02 | — | States the Phase 39 human checkpoint is one-time, no standing gate (D2) | manual (grep-assisted) | `test "$(grep -c 'one-time transition' docs/adr/0012-*.md)" -ge 1` | ❌ created by this phase | ⬜ pending |
| DEV/PRODUCT boundary clause | 01 | 1 | CER-02 | — | N/A | manual (grep-assisted) | `test "$(grep -c 'no product capability may be declined' docs/adr/0012-*.md)" -eq 1` | ❌ created by this phase | ⬜ pending |
| ADR-0011 accepted | 01 | 1 | CER-01 | T-39-01 | Same constitution-plane gate; Date/Deciders confirmed by human at checkpoint, not hardcoded | manual (grep-assisted, exact-count) | `test "$(grep -cE '^- \*\*(Date\|Deciders):\*\* [^—[:space:]]' docs/adr/0011-*.md)" -eq 2; test "$(grep -c 'bc9a6d9' docs/adr/0011-*.md)" -eq 1` | ✅ | ⬜ pending |
| ADR-0001 / ADR-0010 superseded | 01 | 1 | CER-01 | T-39-02 | Same constitution-plane gate; diff proven against a recorded pre-write baseline, not a blind `git diff` | manual diff review (baseline-relative, exact-count) | `test "$(grep -c 'Superseded by:.*0012' docs/adr/0001-*.md)" -eq 1; test "$(grep -c 'Superseded by:.*0012' docs/adr/0010-*.md)" -eq 1` — reviewer additionally confirms via `git diff` against the recorded baseline that only frontmatter lines differ | ✅ | ⬜ pending |
| ADR index row (0011 + 0012) | 01 | 1 | CER-01 | — | N/A | manual (grep-assisted, exact-count) | `test "$(grep -c '\[0011\]' docs/adr/README.md)" -eq 1; test "$(grep -c '\[0012\]' docs/adr/README.md)" -eq 1` | ✅ | ⬜ pending |
| Carried-item dispositions | 02 | 2 | CER-03 | T-39-04 | Append-only, keyed on unique `v2.5 P39, ADR-0012` marker; pre-edit baseline recorded | manual (grep-assisted, exact-count) | `test "$(grep -c 'v2.5 P39, ADR-0012' .planning/STATE.md)" -eq 4; test "$(grep 'v2.5 P39, ADR-0012' .planning/STATE.md \| grep -c 'obsolete-by-deletion')" -eq 3; test "$(grep 'v2.5 P39, ADR-0012' .planning/STATE.md \| grep -c 'withdrawn')" -eq 1; test "$(git diff --numstat .planning/STATE.md \| awk '{print $2}')" -eq 0` | ✅ | ⬜ pending |
| No-regression gate | 02 | 2 | SC-6 | T-39-05, T-39-06 | Pre-run baseline for `.claude`/`.opencode` clean; STOP-on-new-failure for pytest/contract-drift; docs-guard checked as a failing-binding SET, not substring | automated | `test -z "$(git status --porcelain -- .claude .opencode)"; uv run pytest; uv run python -m tools.contract_drift.drift; uv run python -m tools.harness_emit; git diff --exit-code .claude .opencode` (plus a manual docs-guard failing-set comparison against `{task-control-cli-howto}`) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*None — this phase is prose/frontmatter-only. No test file, fixture, or framework install is needed
or appropriate for a decision-record phase. Existing infrastructure (`core-suite`, `contract-drift`,
`emit-drift`, `stale-derived`) covers the no-regression half; the content half is grep-assisted.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ADR-0012 is a coherent, human-ratified decision (not just keyword-matching prose) | CER-01, CER-02 | Prose quality cannot be asserted by grep; ratification is by definition a human act | Owner reads ADR-0012 end to end and confirms: CI + the merge named as the authority (without asserting unconfirmed branch-protection enforcement as fact); every v2.5-deleted surface listed component by component, scoped as intent at ratification time; ADR-0001 constitution-member supersession + ADR-0010 retirement stated; bash surface declared a permanent residual by design; DEV/PRODUCT boundary + operative rule stated citing `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` and `generate.py:41-43`; the human checkpoint is stated as a one-off transition step creating no standing gate |
| Constitution-plane write is human-ratified, not bypassed | CER-01 (V4 access control) | The `GOLDEN_APPROVE_HUMAN` token is by design only exportable by a human, via a single session-env-var delivery path | Human exports the token in the session environment before the ADR-writing task (the plan names no alternative delivery path); the plan must contain an explicit checkpoint with a revise-and-re-present loop, and the executor must never edit `contract_guard.py` or the token check to get past the deny |
| ADR-0001's four-member constitution list is knowingly left stale in code | SC-5 | Expected temporary ADR-vs-code inconsistency; `tools/hooks/tests/test_contract_guard.py:352-375` still pins `golden/**` until Phase 44 | Confirm ADR-0012's Consequences section names this inconsistency explicitly (citing the test file path) and assigns the code change to Phase 44; confirm no test/hook file was touched in this phase |
| Pre-write/pre-edit baselines were actually captured, not skipped | (cross-cutting, both plans) | A recorded baseline is what makes the append-only / supersede-don't-edit / zero-emission-drift proofs valid rather than assumed | Confirm each task's SUMMARY records the `git status --porcelain` (and blob-hash, where applicable) baseline captured before any write, and that no task proceeded past a dirty baseline without stopping |

---

## Validation Sign-Off

- [x] All tasks have an automated or grep-assisted verify command (no Wave 0 dependency exists) — the one `checkpoint:human-verify` task in 39-01 is correctly exempt
- [x] Sampling continuity: every task carries its own verify command — no 3-task gap
- [x] Wave 0 covers all MISSING references (N/A — none)
- [x] No watch-mode flags
- [x] Feedback latency < 120s — the ~120s chained command in `39-02-PLAN.md` Task 2 is an intentional **end-of-wave** gate, not a per-task one; the per-task check is the ~1s quick grep
- [x] `nyquist_compliant: true` set in frontmatter
- [x] Verify commands assert exact counts, not `>= N` presence-checks, per the 2026-07-26 revision
- [x] STATE.md checks keyed on the unique `v2.5 P39, ADR-0012` marker, per the 2026-07-26 revision
- [x] Dirty-worktree baseline capture required before every diff-based proof, per the 2026-07-26 revision

**Approval:** approved 2026-07-26 (plan-checker verified, 0 blockers); revised 2026-07-26 to match
`39-01-PLAN.md`/`39-02-PLAN.md` post-review corrections.
