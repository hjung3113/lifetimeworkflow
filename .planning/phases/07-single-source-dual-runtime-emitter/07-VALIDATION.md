---
phase: 7
slug: single-source-dual-runtime-emitter
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-12
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `07-RESEARCH.md` §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x + syrupy 5.2.0 (workspace dev-deps; already in `uv.lock`) |
| **Config file** | root `pyproject.toml` (`[tool.pytest]` testpaths = tools/ + libs/python) |
| **Quick run command** | `uv run pytest tools/harness_emit -x` |
| **Full suite command** | `uv run pytest` (harness core suite — the CI `core-suite` job) |
| **Estimated runtime** | ~15–30 seconds (quick), full suite dominated by existing tools |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/harness_emit -x`
- **After every plan wave:** Run `uv run pytest` (full core suite — includes the `harness_lint` validators the emitter reuses)
- **Before `/gsd:verify-work`:** Full suite green + `emit-drift` diff clean
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

Derived from `07-RESEARCH.md` §Validation Architecture → Phase Requirements → Test Map. Plan/wave/task IDs are refined by the planner; requirement→test mapping is fixed here.

| Requirement | Behavior | Threat Ref | Test Type | Automated Command | File Exists | Status |
|-------------|----------|------------|-----------|-------------------|-------------|--------|
| EMIT-01 | Source frontmatter parses + projects for all 4 artifact types | — | unit | `uv run pytest tools/harness_emit/tests/test_mapping.py -x` | ❌ W0 | ⬜ pending |
| EMIT-02 | Both runtime trees emitted with correct per-runtime shape | — | unit + snapshot | `uv run pytest tools/harness_emit/tests/test_emit_determinism.py -x` | ❌ W0 | ⬜ pending |
| EMIT-02 | Over-cap/invalid artifact FAILS build (no truncate) | T-07-V | unit | `uv run pytest tools/harness_emit/tests/test_validators.py -x` | ❌ W0 | ⬜ pending |
| EMIT-02 | GSD/human files untouched; managed-block merge idempotent | T-07-C | unit | `uv run pytest tools/harness_emit/tests/test_coexist.py tools/harness_emit/tests/test_merge_idempotent.py -x` | ❌ W0 | ⬜ pending |
| EMIT-02 | Manifest owns only emitted files; prunes orphans not GSD | T-07-M | unit | `uv run pytest tools/harness_emit/tests/test_manifest.py -x` | ❌ W0 | ⬜ pending |
| EMIT-02 | Re-emit → clean git diff (drift gate) | — | CI/integration | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` | ❌ W0 (+ ci.yml job) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/harness_emit/pyproject.toml` — virtual uv member, `dependencies = []` (clone `tools/docs_sync`)
- [ ] `tools/harness_emit/tests/conftest.py` — repo-root on `sys.path` (clone `docs_sync`)
- [ ] `tools/harness_emit/tests/__snapshots__/` — syrupy `.ambr` for the projected tree
- [ ] `.github/workflows/ci.yml` — add `emit-drift` job + add to `gate.needs`
- [ ] Framework install: none — pytest/syrupy already in the lockfile

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| opencode actually loads the emitted `.opencode/` tree at runtime | EMIT-02 | opencode not installed in env (CONTEXT out-of-scope); MVP verifies structure/shape only | Deferred to post-opencode-install; emit-time shape validators + snapshot stand in |

*Structural/shape correctness of the emitted opencode surfaces is automated via validators + snapshots; only live-runtime load is manual and deferred.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (test files + snapshots + ci job)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
