---
phase: 11
slug: multi-repo-workspace-v2-0
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-13
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (uv workspace) |
| **Config file** | root `pyproject.toml` (existing) |
| **Quick run command** | `uv run pytest tools/workspace_config tools/harness_lint -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run the quick command scoped to the touched module.
- **After every plan wave:** Run `uv run pytest -q` (full non-example suite).
- **Before `/gsd:verify-work`:** Full suite + re-emit-diff + stale-derived + cross-repo gates green.
- **Max feedback latency:** 5 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-* | 01 | 1 | MREPO-01 | — | Loader passthrough + consistency gate rejects dangling member / unresolved edge contract | unit | `uv run pytest tools/workspace_config -q` | ❌ W0 | ⬜ pending |
| 11-02-* | 02 | 2 | MREPO-04 | — | `repo:stage` edge parses; core→workspace-member GEN-04 guard fails on a synthetic leak | unit | `uv run pytest tools/harness_lint/tests/test_core_no_workspace_dep.py -q` | ❌ W0 | ⬜ pending |
| 11-03-* | 03 | 3 | MREPO-03 | — | Cross-repo drift fails on producer-side contract change; workspace-aware golden runs an edge-spanning case | unit | `uv run pytest tools/contract_drift tools/golden_runner -q` | ✅ | ⬜ pending |
| 11-04-* | 04 | 4 | MREPO-02 | — | Per-repo read-only fan-out worker returns schema-bounded citations; any new command round-trips the emitter | unit | `uv run pytest tools/harness_emit -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/workspace_config/tests/test_workspace_config.py` — loader + consistency-gate stubs for MREPO-01 (mirror `test_language_config.py`).
- [ ] `tools/harness_lint/tests/test_core_no_workspace_dep.py` — GEN-04 twin for MREPO-04 (mirror `test_core_no_example_dep.py`, incl. negative controls).
- [ ] `tests/fixtures/workspace/` — minimal 2-member workspace fixture INSIDE `REPO_ROOT` (golden_runner `_confine` rejects roots outside repo — L88-102).

*Existing infrastructure (pytest/uv, `contract_drift`, `golden_runner`, `harness_emit`) covers drift/golden/emit requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | All Phase 11 behaviors have automated verification (loaders, gates, drift/golden, emit round-trip are all pytest-checkable). | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
