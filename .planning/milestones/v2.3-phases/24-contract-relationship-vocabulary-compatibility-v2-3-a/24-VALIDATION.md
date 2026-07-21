---
phase: 24
slug: contract-relationship-vocabulary-compatibility-v2-3-a
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-19
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (uv workspace) |
| **Config file** | root `pyproject.toml` (+ new `tools/harness_config/tests/` — Wave 0 creates) |
| **Quick run command** | `uv run pytest tools/harness_config tools/harness_lint -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/harness_config tools/harness_lint -q`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite + contract-drift must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| {N}-01-01 | 01 | 1 | TOPO-01 | — | N/A | unit | `uv run pytest tools/harness_config/tests -q` | ❌ W0 | ⬜ pending |

*Filled by planner/executor. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/harness_config/tests/` package + `conftest.py` — does not exist yet (loader currently tested via `harness_lint`)
- [ ] Fixture home `tools/harness_config/tests/fixtures/` — GEN-04-neutral, NOT under `contracts/`
- [ ] positive/negative topology-record fixture instances

*Framework already installed (pytest in uv workspace) — no install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Human ratification of new schema | TOPO-01 | Constitution-plane change requires human sign-off (machines gate, humans ratify) | Review `relationship.schema.json` + fixtures, then commit `contract_hash --write` baseline update |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
