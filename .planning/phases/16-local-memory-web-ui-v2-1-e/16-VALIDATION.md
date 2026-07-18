---
phase: 16
slug: local-memory-web-ui-v2-1-e
status: approved
nyquist_compliant: true
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
| 16-01-01 | 01 | 0 | MEM2-07 | — | uv member `tools/memory_ui` enrolled; lockfile green | unit | `uv sync --locked` | ❌ W0 | ⬜ pending |
| 16-01-02 | 01 | 0 | MEM2-07 | T-16-01 | RED tests pin generator/route APIs (tmp-injected, no socket, no real agreement writes) | unit | `uv run pytest tools/memory_regen/tests/test_pointer_index.py -q` | ❌ W0 | ⬜ pending |
| 16-01-03 | 01 | 0 | MEM2-07 | T-16-03 | RED tests pin orphan/route logic on tmp fixtures | unit | `uv run pytest tools/memory_ui -q` | ❌ W0 | ⬜ pending |
| 16-02-01 | 02 | 1 | MEM2-07 | — | pointer-index DERIVED-marked, keyed item→[{file,line,kind}] | unit | `uv run pytest tools/memory_regen/tests/test_pointer_index.py -q` | ❌ W0 | ⬜ pending |
| 16-02-02 | 02 | 1 | MEM2-07 (SC2) | — | deterministic: write→hash→delete→regenerate byte-identical; no wall-clock | unit | `uv run pytest tools/memory_regen/tests/test_pointer_index.py -q` | ❌ W0 | ⬜ pending |
| 16-03-01 | 03 | 2 | MEM2-07 (SC1) | T-16-02 | agreements add/retire via `tools.agree.write` only; anti-invent `--because`; stamp writer clock-free | unit | `uv run pytest tools/memory_ui -q` | ❌ W0 | ⬜ pending |
| 16-03-02 | 03 | 2 | MEM2-07 (SC3) | T-16-03 | orphan surfaced + confirm-gated; never auto-rewrites external docs | unit | `uv run pytest tools/memory_ui -q` | ❌ W0 | ⬜ pending |
| 16-04-01 | 04 | 2 | MEM2-07 (SC2) | T-16-04 | generator wired into SessionStart/`/orient`/`/refresh-memory`; no constitution mutation | unit | `uv run pytest tools/memory_regen -q` | ❌ W0 | ⬜ pending |
| 16-04-02 | 04 | 2 | MEM2-07 | T-16-08 | emit round-trip to both runtimes; no model id; emit-drift clean | unit | `uv run pytest tools/harness_emit -q` | ❌ W0 | ⬜ pending |
| 16-05-01 | 05 | 3 | MEM2-07 (SC1) | T-16-05 | HTTP shell binds 127.0.0.1 ONLY (never 0.0.0.0) | unit | `uv run pytest tools/memory_ui -q` | ❌ W0 | ⬜ pending |
| 16-05-02 | 05 | 3 | MEM2-07 | T-16-06 | single inlined page, no external fetch | unit | `uv run pytest tools/memory_ui -q` | ❌ W0 | ⬜ pending |
| 16-06-01 | 06 | 4 | MEM2-07 (SC1/SC3) | — | browser round-trip: view/edit/retire + orphan-confirm dialog | manual | see Manual-Only Verifications | ❌ W0 | ⬜ pending |

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

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (16-01 establishes the test infra)
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter
- [ ] `wave_0_complete` flips true at execution time when Wave-0 (16-01) tests are in place

**Approval:** approved 2026-07-18 (plan-checker confirmed every auto/tdd task carries a fast, non-watch-mode automated command with no sampling gaps)
