---
phase: 49
slug: contract-impact
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-30
---

# Phase 49 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (+ syrupy where snapshots apply) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` — not modified by this phase |
| **Quick run command** | `uv run pytest tools/contract_graph tools/harness_lint/tests/test_commands.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~15 s |

---

## Sampling Rate

- **After every task commit:** quick run command above
- **After every plan wave:** `uv run pytest -q` + `uv run python -m tools.harness_emit` idempotency
- **Before `/gsd:verify-work`:** full suite green; `git diff --stat` EMPTY for
  `.github/workflows/ci.yml` and `tools/memory_regen/inject.py`
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 49-01-* | 01 | 1 | MONO-08 | — | N/A | unit | `uv run pytest tools/contract_graph/tests/test_impact.py -x` | ❌ W0 | ⬜ pending |
| 49-02-* | 02 | 2 | MONO-08, MONO-09 | — | N/A | structural + emit round-trip | `uv run pytest tools/harness_lint/tests/test_commands.py -k stable -x`; `uv run python -m tools.harness_emit` then clean `git status` | ✅ extend | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tools/contract_graph/tests/test_impact.py` — MONO-08 across five behaviours, all on
      **synthetic fixtures** (mandatory: the live graph is empty, so the live tree cannot exercise
      traversal at all):
      - traversal reuse over a multi-hop fixture (direct / reverse / transitive)
      - affected-package attribution
      - no-second-traversal-engine structural check that can actually fail
      - the three-way distinction: refused vs resolved-but-isolated vs resolved-with-affected-set
      - byte-identical output on repeat invocation
- [ ] Bump `tools/harness_lint/tests/test_commands.py` — count `18` → `19` and add `"impact"` to
      `EXPECTED_COMMAND_NAMES` (both are designed to fail until updated)
- [ ] Route-wiring assertion — the inline `uv run python -c` one-liner is gone from
      `harness/agents/orchestrator.md`, all four routes still carry a *Repository evidence*
      subsection, and the route names `/impact`
- [ ] Framework install: none

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | — | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
