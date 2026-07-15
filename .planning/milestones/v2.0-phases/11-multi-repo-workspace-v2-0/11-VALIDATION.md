---
phase: 11
slug: multi-repo-workspace-v2-0
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-13
updated: 2026-07-14
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
| 11-01-* | 01 | 1 | MREPO-01 | T-11-01..03 | Loader passthrough + consistency gate rejects dangling member / unresolved edge contract | unit | `uv run pytest tools/workspace_config tools/harness_lint/tests/test_workspace_config.py -q` | created in 11-01 | ⬜ pending |
| 11-02-* | 02 | 2 | MREPO-04 | T-11-04..05 | `repo:stage` edge parses + crosses a repo boundary; core→workspace-member GEN-04 guard flags a synthetic leak (key-scoped exemption) | unit | `uv run pytest tools/harness_lint/tests/test_core_no_workspace_member_dep.py tools/workspace_config/tests/test_endpoints.py -q` | created in 11-02 | ⬜ pending |
| 11-03-* | 03 | 2 | MREPO-03 | T-11-06..09 | Cross-repo drift fails on producer-side contract change / unresolved edge; workspace-aware golden runs an edge-spanning case with widened-not-removed `_confine` | unit | `uv run pytest tools/contract_drift/tests/test_workspace_drift.py tools/golden_runner/tests/test_workspace_golden.py -q` | created in 11-03 | ⬜ pending |
| 11-04-* | 04 | 3 | MREPO-02 | T-11-10..12 | Prose-wired per-repo read-only fan-out (no-sibling-read); emitter round-trips both runtimes byte-identical, no model id, counts unchanged | unit | `uv run pytest tools/harness_lint tools/harness_emit -q` | created in 11-04 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Waves: 11-01 = wave 1; 11-02 + 11-03 = wave 2 (parallel, disjoint files); 11-04 = wave 3 (closeout gate).*

---

## Wave 0 Requirements

All Wave-0 scaffolding is folded into the wave-1 / wave-2 plans that own it (no separate Wave-0 plan);
every consuming task's inputs are created earlier in the same phase before use:

- [x] `tools/workspace_config/` loader + `tools/workspace_config/tests/test_loader.py` + `tools/harness_lint/tests/test_workspace_config.py` — MREPO-01 loader + consistency gate (**11-01**, wave 1; mirrors `test_language_config.py`).
- [x] `tests/fixtures/workspace/` — minimal 2-member fixture INSIDE `REPO_ROOT`, fully baselined (**11-01** Task 2, wave 1; golden_runner `_confine` accepts in-repo roots — L88-102).
- [x] `tools/harness_lint/tests/test_core_no_workspace_member_dep.py` — GEN-04 twin for MREPO-04 (**11-02** Task 1, wave 2; mirror `test_core_no_example_dep.py` incl. live negative controls + key-scoped `workspace.toml` pointer exemption).

*Existing infrastructure (pytest/uv, `contract_drift`, `golden_runner`, `harness_emit`) covers the drift/golden/emit requirements; wave-2 additions are additive.*

*Wave-2 collision note:* 11-02's new GEN-04 guard scans all tracked files under `tools/`, so 11-03's
new test files (`test_workspace_drift.py`, `test_workspace_golden.py`) resolve member roots via
`tools.workspace_config.members()` / `load_workspace()` at runtime (never string literals) — enforced by
`grep -c 'tests/fixtures/workspace' … == 0` acceptance checks so the parallel wave-2 gate stays green.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | All Phase 11 behaviors have automated verification (loaders, gates, drift/golden, emit round-trip are all pytest / check-jsonschema checkable). | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (folded into 11-01 / 11-02)
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-14 (refreshed to match final Nyquist-passing plans — waves 1/2/2/3, guard filename `test_core_no_workspace_member_dep.py`).
