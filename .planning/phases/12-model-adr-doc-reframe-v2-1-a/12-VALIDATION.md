---
phase: 12
slug: model-adr-doc-reframe-v2-1-a
status: final
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-14
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Phase 12 is a docs/model/ADR-scaffold phase — most criteria are verified by
> structural asserts (grep/file-exists) and the constitution-gate behavior, not
> a runtime suite. The planner fills the per-task map from the RESEARCH.md
> Validation Architecture section.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (uv workspace) + grep/file-exists structural asserts |
| **Config file** | root `pyproject.toml` (uv workspace) |
| **Quick run command** | `grep`/`test -f` structural asserts per task (no code compile needed) |
| **Full suite command** | `uv run pytest tools/harness_lint` (POLY/GEN structural guards) |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task's structural assert (grep/file-exists).
- **After every plan wave:** Run `uv run pytest tools/harness_lint`.
- **Before `/gsd:verify-work`:** Full structural suite + contract-check green.
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

> Populated by the planner from the RESEARCH.md "Validation Architecture" section.
> Each SC maps to a grepable assert; SC4 (ADR deny) maps to a behavior assert on
> contract-guard (agent Write to `docs/adr/` denied without `GOLDEN_APPROVE_HUMAN`).

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | MEM2-01 | — | N/A | structural | `test -f .memory/agreements/_TEMPLATE.md` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 1 | MEM2-03 | — | N/A | structural | `grep -rn "confirm before trusting\|provisional" <5 surfaces> exits 1` | ✅ | ⬜ pending |
| 12-03-01 | 03 | 2 | MEM2-06 (ADR-0006) | T-12-01 / — | agent Write to `docs/adr/` denied without human token | behavior | contract-guard deny reproduced; ADR-0006 present post-human-ratify | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.memory/agreements/_TEMPLATE.md` — seed file establishes the committed tier (git won't track an empty dir).
- [ ] No new pytest fixtures required — structural asserts use grep/`test -f`.

*Existing harness_lint infrastructure covers the structural guards; no framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ADR-0006 human ratification at merge | MEM2-06 (ADR portion) | Constitution plane is human-gated; CODEOWNERS ratifies at merge — cannot self-approve | Human supplies `GOLDEN_APPROVE_HUMAN` token (or writes the file) then CODEOWNERS review approves the PR touching `docs/adr/` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-14
