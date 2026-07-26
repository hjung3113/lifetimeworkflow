---
phase: 39
slug: decision-boundary-v2-5-a
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-26
---

# Phase 39 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `39-RESEARCH.md` § Validation Architecture. This phase is decision-record-only
> (prose + frontmatter + `.planning/STATE.md`), so verification is grep-assisted content
> assertion plus a no-regression check on the existing suites. No new test file is added.

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
- **After every plan wave:** Run `uv run pytest` + `uv run python -m tools.contract_drift.drift` + `uv run python -m tools.harness_emit` then `git diff --exit-code` on `.claude/` and `.opencode/` (ADR edits must produce zero emission drift).
- **Before `/gsd:verify-work`:** Full suite green, **excluding the pre-existing out-of-scope `docs-guard` RED** (`task-control-cli-howto` staleness, red before this phase — see RESEARCH § Pitfalls). This phase must neither fix nor worsen it.
- **Max feedback latency:** ~120 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| ADR-0012 authored | 01 | 1 | CER-01 | T-39-01 | Written under the `contract_guard` deny — human-ratified, never bypassed | manual (grep-assisted) | `grep -l "accepted" docs/adr/0012-*.md && grep -ci "supersed" docs/adr/0012-*.md` | ❌ created by this phase | ⬜ pending |
| DEV/PRODUCT boundary clause | 01 | 1 | CER-02 | — | N/A | manual (grep-assisted) | `grep -i "no product capability may be declined" docs/adr/0012-*.md` | ❌ created by this phase | ⬜ pending |
| ADR-0011 accepted | 01 | 1 | CER-01 | T-39-01 | Same constitution-plane gate | manual (grep-assisted) | `grep -E "^- \*\*(Date\|Deciders):\*\* [^—[:space:]]" docs/adr/0011-*.md && grep -c "bc9a6d9" docs/adr/0011-*.md` | ✅ | ⬜ pending |
| ADR-0001 / ADR-0010 superseded | 01 | 1 | CER-01 | T-39-01 | Same constitution-plane gate | manual diff review | `git diff docs/adr/0001-*.md docs/adr/0010-*.md` — only frontmatter lines may differ | ✅ | ⬜ pending |
| ADR index row (0011 + 0012) | 01 | 1 | CER-01 | — | N/A | manual (grep-assisted) | `grep -c "0011\|0012" docs/adr/README.md` | ✅ | ⬜ pending |
| Carried-item dispositions | 02 | 2 | CER-03 | — | N/A | manual (grep-assisted) | `grep -i "obsolete-by-deletion" .planning/STATE.md && grep -i "SEAL-05" .planning/STATE.md \| grep -i withdrawn` | ✅ | ⬜ pending |
| No-regression gate | 02 | 2 | SC-6 | — | N/A | automated | `uv run pytest && uv run python -m tools.contract_drift.drift && uv run python -m tools.harness_emit && git diff --exit-code .claude .opencode` | ✅ | ⬜ pending |

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
| ADR-0012 is a coherent, human-ratified decision (not just keyword-matching prose) | CER-01, CER-02 | Prose quality cannot be asserted by grep; ratification is by definition a human act | Owner reads ADR-0012 end to end and confirms: CI + the merge named as the authority; every v2.5-deleted surface listed; ADR-0001 constitution-member supersession + ADR-0010 retirement stated; bash surface declared a permanent residual by design; DEV/PRODUCT boundary + operative rule stated citing `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` and `generate.py:41-43` |
| Constitution-plane write is human-ratified, not bypassed | CER-01 (V4 access control) | The `GOLDEN_APPROVE_HUMAN` token is by design only exportable by a human | Human exports the token in-session before the ADR-writing task; the plan must contain an explicit checkpoint, and the executor must never edit `contract_guard.py` or the token check to get past the deny |
| ADR-0001's four-member constitution list is knowingly left stale in code | SC-5 | Expected temporary ADR-vs-code inconsistency; `tools/hooks/tests/test_contract_guard.py:352-375` still pins `golden/**` until Phase 44 | Confirm ADR-0012's Consequences section names this inconsistency explicitly and assigns the code change to Phase 44; confirm no test/hook file was touched in this phase |

---

## Validation Sign-Off

- [x] All tasks have an automated or grep-assisted verify command (no Wave 0 dependency exists) — the one `checkpoint:human-verify` task in 39-01 is correctly exempt
- [x] Sampling continuity: every task carries its own verify command — no 3-task gap
- [x] Wave 0 covers all MISSING references (N/A — none)
- [x] No watch-mode flags
- [x] Feedback latency < 120s — the ~120s chained command in `39-02-PLAN.md` Task 2 is an intentional **end-of-wave** gate, not a per-task one; the per-task check is the ~1s quick grep
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-26 (plan-checker verified, 0 blockers)
