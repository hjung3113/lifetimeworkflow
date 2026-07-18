---
phase: 16
slug: local-memory-web-ui-v2-1-e
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-18
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source of the behavioral map: `16-RESEARCH.md` → `## Validation Architecture` (SC1–SC3, 15-row test map).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (uv workspace) |
| **Config file** | root `pyproject.toml` (workspace); new member `tools/memory_ui/pyproject.toml` |
| **Quick run command** | `uv run pytest tools/memory_ui tools/memory_regen/tests/test_pointer_index.py -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~30–60 seconds (full); quick <10s |

---

## Sampling Rate

- **After every task commit:** Run the quick run command
- **After every plan wave:** Run the full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

> Filled by the planner (task IDs) / executor. Behaviors derive from `16-RESEARCH.md` `## Validation Architecture`.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-XX-XX | XX | 0/1 | MEM2-07 | — | localhost-only bind (never 0.0.0.0) | unit | `uv run pytest tools/memory_ui -q` | ❌ W0 | ⬜ pending |
| 16-XX-XX | XX | 1 | MEM2-07 | — | pointer-index deterministic (write→hash→delete→regenerate) | unit | `uv run pytest tools/memory_regen/tests/test_pointer_index.py -q` | ❌ W0 | ⬜ pending |
| 16-XX-XX | XX | 1 | MEM2-07 | — | edit/retire orphaning surfaced + confirm-gated | unit | `uv run pytest tools/memory_ui -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/memory_ui/tests/` — pure-function route tests (no live socket; injected `agreements_dir`/`state_dir`/`derived_dir`)
- [ ] `tools/memory_regen/tests/test_pointer_index.py` — determinism (regenerate-not-git-diff) + referrer-scan correctness
- [ ] Reuse existing `tmp_agreements_tree` fixture — never write real `.memory/agreements/*`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser renders the single localhost page and view/edit/retire round-trips | MEM2-07 SC1 | Real browser render is outside pytest | `python -m tools.memory_ui`, open `http://127.0.0.1:<port>`, view an agreement/progress item, edit + retire, confirm the orphan prompt appears |

*Automated coverage handles handler logic, pointer-index generation, and orphan detection; only the visual browser round-trip is manual.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
