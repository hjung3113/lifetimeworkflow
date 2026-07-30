---
phase: 5.5
slug: authored-surface
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-09
---

# Phase 5.5 — Validation Strategy

> Source: `055-RESEARCH.md` §Validation Architecture. Pure authored-surface move + prose sweep +
> a test extension — ZERO new external packages. The phase-wide invariant is: `uv run pytest`
> (the non-example suite) stays GREEN, and after the whole phase the extended GEN-04 guard reads
> exactly 0 core-prose domain tokens. No constitution plane (`contracts/adr/golden`) is touched —
> so NO `GOLDEN_APPROVE_HUMAN` token is required anywhere in this phase.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `>=8.4,<9` via `uv run pytest` (no snapshots added this phase) |
| **Config file** | uv workspace root `pyproject.toml` (`examples/` deliberately OUT of testpaths) |
| **Quick run command** | `uv run pytest tools/harness_lint -x -q` |
| **Full suite command** | `uv run pytest` (keep Phase 1–5 suites green) |
| **Guard-only run** | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x -q` |
| **Estimated runtime** | ~15–45 s |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/harness_lint -x -q` (+ the changed-package suite for the 055-02 sweep, e.g. `tools/contract_drift tools/memory_regen tools/docs_sync`).
- **After every plan wave:** `uv run pytest` (full non-example suite).
- **Phase gate (before `/gsd:verify-work`):** full suite green + `git grep` for the guard tokens across `tools/ harness/ libs/` (excluding the guard file) returns empty + manual demo of each success criterion.

---

## Per-Requirement Verification Map

| Req / Crit | Behavior | Test Type | Automated Command | File | Plan |
|------------|----------|-----------|-------------------|------|------|
| GEN-05 / demo1 | Exactly the 4 core skills remain (no sprawl) | unit | `uv run pytest tools/harness_lint/tests/test_skills.py::test_expected_skills_present_no_sprawl -x` | ⚠️ edit `EXPECTED_SKILLS` (7→4) | 055-01 |
| GEN-05 / demo1 | Exactly the 4 core personas remain (no sprawl) | unit | `uv run pytest tools/harness_lint/tests/test_agents.py::test_expected_personas_present_no_sprawl -x` | ⚠️ edit `EXPECTED_PERSONAS` (5→4) | 055-01 |
| GEN-05 / demo1 | No command dangles to a moved persona | integration | `uv run pytest tools/harness_lint/tests/test_agent_referential_integrity.py -x` | ⚠️ repoint strangler-step `agent:` | 055-01 |
| GEN-05 / demo1 | `project.toml` personas resolve on disk | unit | `uv run pytest tools/harness_lint/tests/test_language_config.py::test_each_configured_persona_exists -x` | ⚠️ repoint `dotnet.persona` path | 055-01 |
| GEN-05 / demo1 | The move is a history-preserving rename (status R) | manual/CI | `git status --short \| grep '^R'` ; `git log --follow examples/log-parser/agents/dotnet-engineer.md` | manual | 055-01 |
| GEN-05 / demo2 | `data-contracts` + `new-normalization-rule` bodies carry 0 semiconductor vocab | unit | `! git grep -nE 'equipment\|standard-log\|correction-rules' -- harness/skills/data-contracts harness/commands/new-normalization-rule.md` | ⚠️ genericize prose | 055-02 |
| GEN-05 / demo2 | Contract-first order + drift-gate prose unchanged | suite | `uv run pytest` (encodes the logic; nothing regresses) | ✅ must stay green | 055-02 |
| GEN-05 / demo3 (pre) | Every core (`tools/harness/libs`) guard token removed/reworded | unit | `! git grep -nE 'dotnet-engineer\|dotnet-conventions\|normalization-catalog\|pipeline-patterns\|libs/dotnet\|equipment\|standard-log\|correction-rules' -- tools harness libs ':!tools/harness_lint/tests/test_core_no_example_dep.py'` | ⚠️ sweep comments/fixtures | 055-02 |
| GEN-05 / D-05 | Example docs record the moved skills + persona | structural | `grep -q normalization-catalog examples/log-parser/AGENTS.md && grep -q dotnet-engineer examples/log-parser/AGENTS.md` | ⚠️ update instance docs | 055-02 |
| GEN-05 / demo3 | Core planes carry 0 domain prose tokens (guard extended) | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ❌ EXTEND (`_PROSE_TOKENS` + per-token negative-control) | 055-03 |
| GEN-05 / demo3 | `project.toml` instance pointer (`persona = examples/…`) is exempt | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py::test_instance_pointer_persona_is_exempt -x` | ❌ Wave 0 (new positive test) | 055-03 |
| GEN-05 / demo3 | Each new prose token's scan is live (cannot no-op) | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -k negative -x` | ❌ Wave 0 (per-token negative control) | 055-03 |
| GEN-05 / demo4 | Non-example suite green (expected-lists + guard updated) | suite | `uv run pytest` | ✅ phase-wide invariant | all |

*Status: ⬜ pending · ✅ green · ❌ red (Wave 0) · ⚠️ edit/extend existing*

---

## Wave 0 Requirements

- [ ] `tools/harness_lint/tests/test_skills.py` — reduce `EXPECTED_SKILLS` to `{python-conventions, golden-testing, data-contracts, skill-creator}` (055-01).
- [ ] `tools/harness_lint/tests/test_agents.py` — reduce `EXPECTED_PERSONAS` to `{orchestrator, python-engineer, code-reviewer, explorer}` (055-01).
- [ ] `tools/harness_lint/tests/test_core_no_example_dep.py` — add `_PROSE_TOKENS`, extend `_scan_lines`, generalize `_is_instance_root_line`→pointer-line (`root =` + `persona =`), one negative-control per new token, and `test_instance_pointer_persona_is_exempt` (055-03).
- [ ] No NEW test *file* is created — all edits extend existing modules (RESEARCH §Wave 0 Gaps).
- [ ] No `uv sync` needed — no package member added. `uv.lock` unchanged. Zero new external packages.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `git log --follow` shows preserved history across the 4 renames | GEN-05 / demo1 | History-follow is a git behavior, best eyeballed | `git log --follow examples/log-parser/agents/dotnet-engineer.md` (and one moved skill's SKILL.md) shows pre-move commits. |
| Moved skills/agents lose core structural validation | GEN-05 (open question) | The glob-driven caps/frontmatter tests no longer cover assets under `examples/`; the example has no equivalent validator yet | DEFER to Phase 7's emit-time validators (per CLAUDE.md "Emit-time validators"). Noted so it is not silently lost (RESEARCH Open Question 1). |

---

## Validation Sign-Off

- [x] All tasks have an `<automated>` verify or a Wave 0 dependency
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING/EXTEND references (2 anti-sprawl frozensets + the guard extension)
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [x] `nyquist_compliant: true` set in frontmatter
- [x] Phase-wide invariant encoded: `uv run pytest` (non-example) green + post-phase `git grep` of guard tokens over `tools/harness/libs` (minus guard file) empty
- [x] Security control is "tamper-evident, live": the prose scan has one negative-control per token (`wafer`/`설비` are 0-occurrence guaranteed-live anchors); no constitution-plane write, so no `GOLDEN_APPROVE_HUMAN` token in this phase

**Approval:** pending plan-check. `wave_0_complete` flips true at execution once the Wave 0 scaffolds (the two reduced frozensets in 055-01 + the extended guard in 055-03) exist and the full non-example suite is green.
