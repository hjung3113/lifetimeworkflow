---
phase: 25
slug: graph-compiler-queries-conductor-proof-v2-3-a
status: validated
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-19
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (uv workspace) |
| **Config file** | root `pyproject.toml` (+ new `tools/contract_graph/tests/`) |
| **Quick run command** | `uv run pytest tools/contract_graph tools/harness_lint -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/contract_graph tools/harness_lint -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite + contract-drift + harness-emit round-trip must be green
- **Max feedback latency:** 40 seconds

---

## Per-Task Verification Map

| Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|------|------|-------------|-----------|-------------------|-------------|--------|
| 25-01 (compiler + gate + WR-02 close) | 1 | TOPO-04 | unit | `uv run pytest tools/contract_graph tools/harness_lint -q` | ❌ W0 | ⬜ pending |
| 25-02 (affected-set queries) | 2 | TOPO-05 | unit | `uv run pytest tools/contract_graph -q` | ❌ W0 | ⬜ pending |
| 25-03 (indented-tree render + linear byte-identity + emit round-trip) | 3 | TOPO-06 | regression | `python -m tools.harness_emit && git diff --exit-code -- .opencode .claude` | ✅ | ⬜ pending |
| 25-04 (non-linear proof fixtures + WR-01 corpus scan) | 3 | TOPO-07 | fixture | `uv run pytest tools/contract_graph -q` | ❌ W0 | ⬜ pending |
| 25-05 (ADR-0009) | 4 | TOPO-07 | manual-gate | human ratification (see Manual-Only) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Per-task detail in each PLAN.md `<verify><automated>`.*

---

## Wave 0 Requirements

- [ ] `tools/contract_graph/` package + `tests/` + `conftest.py` — new sibling module (does not exist)
- [ ] Non-linear proof fixtures in the test plane (GEN-04-safe, non-contiguous `Path` for instance refs)
- [ ] A concrete artifact/golden that proves conductor LINEAR render byte-identity (open design item A2 — the planner must choose the proof mechanism, since `pipeline.md`/`pipeline-map` are prose, not runnable today)

*Framework already installed (pytest) — no install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ADR-0009 human ratification | TOPO-07 | Constitution-plane decision record requires human sign-off (machines gate, humans ratify) | Review ADR-0009 (record/graph model + query semantics + conductor contract), mark accepted (25-05 checkpoint task) |

*The harness-emit byte-identical round-trip is AUTOMATED in 25-03 Task 3 (`python -m tools.harness_emit && git diff --exit-code -- .opencode .claude`), not manual. Only the ADR ratification is a genuine human gate.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (esp. the conductor byte-identity proof artifact)
- [ ] No watch-mode flags
- [ ] Feedback latency < 40s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
