---
phase: 25
slug: graph-compiler-queries-conductor-proof-v2-3-a
status: draft
nyquist_compliant: false
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

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| {N}-01-01 | 01 | 1 | TOPO-04 | — | N/A | unit | `uv run pytest tools/contract_graph -q` | ❌ W0 | ⬜ pending |

*Filled by planner/executor. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

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
| ADR-0009 human ratification | TOPO-07 | Constitution-plane decision record requires human sign-off (machines gate, humans ratify) | Review ADR-0009 (record/graph model + query semantics + conductor contract), mark accepted |
| harness-emit byte-identical round-trip | TOPO-06 | Conductor surface edits must project to `.opencode/`+`.claude/` with no model ids | Re-run emit; `git diff` on emitted trees confirms byte-identity |

*Other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (esp. the conductor byte-identity proof artifact)
- [ ] No watch-mode flags
- [ ] Feedback latency < 40s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
