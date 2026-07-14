---
phase: 10
slug: context-economy-fan-out-synthesize-orchestration-v2-0
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-13
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (uv workspace) |
| **Config file** | pyproject.toml (root uv workspace) |
| **Quick run command** | `uv run pytest tools/harness_lint tools/harness_emit -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/harness_lint tools/harness_emit -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | ECON-02 | — | N/A | unit | `uv run pytest tools/harness_lint -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Populated by the planner from PLAN.md tasks; this is a scaffold row.*

---

## Wave 0 Requirements

- [ ] Return-contract JSON Schema structural test (ECON-02) — schema is valid Draft 2020-12, required citation-bearing fields present, `additionalProperties: false`.
- [ ] `EXPECTED_SKILLS` enumeration test (anti-sprawl) — new skills added (9 → 11); `EXPECTED_PERSONAS` stays 5.
- [ ] orchestrator + `/orient` context-budget wiring test (ECON-03).
- [ ] emit round-trip / emit-drift `git diff --exit-code` over the new skill + command surface (D-12).

*Existing pytest + harness_lint/harness_emit infrastructure covers execution; the above are the new stubs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fan-out workflow end-to-end (dispatch N explorers → recover schema-bounded summaries → synthesize) | ECON-01 | Runtime subagent dispatch is not exercised by the emitted-static test suite; the skill is a procedure, and the return is an ephemeral runtime value (D-09) | Invoke `/fan-out-synthesize` on a sample multi-file task; confirm workers return citation-bearing summaries and the orchestrator synthesizes without re-reading raw files |

*Populated further by the planner; runtime orchestration behavior is prose-enforced, not statically testable.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
