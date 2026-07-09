---
phase: 6
slug: ci-gates
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source of truth for the validation architecture: `06-RESEARCH.md` §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (Python)** | pytest 8.4.x (pinned `>=8.4,<9`, pyproject.toml:35); syrupy 5.2.0 |
| **Framework (.NET)** | xunit.v3 3.2.2 + Microsoft.Testing.Platform; net10.0 (runs on GH runner only) |
| **Config file** | `pyproject.toml [tool.pytest.ini_options]` (testpaths = libs/python, tools) |
| **Quick run command** | `uv run pytest tools/harness_config tools/contract_drift tools/golden_runner` |
| **Full suite command** | `uv run pytest` (non-example) + `uv run pytest examples/log-parser/tests` |
| **YAML self-check** | `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` |
| **Estimated runtime** | ~30 seconds (non-example, no .NET locally) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/harness_config tools/contract_drift tools/golden_runner`
- **After every plan wave:** Run `uv run pytest` (full non-example) + `uv run pytest examples/log-parser/tests` (if .NET available)
- **Before `/gsd:verify-work`:** Full non-example suite green + `check-jsonschema` YAML validation of `ci.yml`
- **Max feedback latency:** ~30 seconds (local, .NET-free legs)

---

## Per-Task Verification Map

> Filled by the planner/executor as tasks land. Anchors from RESEARCH §Phase Requirements → Test Map.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-xx | 01 | 1 | CI-01 | — | matrix emitter produces valid JSON from project.toml | unit | `uv run pytest tools/harness_config` | ❌ W0 | ⬜ pending |
| 06-02-xx | 02 | 1 | CI-01 | — | drift CLI accepts `--contracts-dir`/`--baseline` | unit | `uv run pytest tools/contract_drift` | ❌ W0 | ⬜ pending |
| 06-03-xx | 03 | 2 | CI-01 | V1/V10/V14 | workflow YAML structurally valid | smoke | `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` | ✅ | ⬜ pending |
| 06-03-xx | 03 | 2 | CI-02 | — | CODEOWNERS covers constitution + example equivalents | manual/review | (GitHub validates on push) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/harness_config/tests/test_matrix_emit.py` — asserts the matrix JSON shape from `languages()` + new `test_paths` field (covers CI-01)
- [ ] `tools/contract_drift/tests/test_cli_flags.py` — asserts `--contracts-dir`/`--baseline` target the example manifest (covers CI-01 example-drift)
- [ ] Extend `tools/harness_lint/tests/test_language_config.py` — tolerate/verify the new `test_paths` field (RESEARCH A4)
- [ ] Workflow self-validation step (`check-jsonschema` builtin GitHub-workflow schema) wired into a generic job

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CODEOWNERS gates constitution plane at merge | CI-02 | Enforcement is a repo branch-protection setting (out of scope) + GitHub validates CODEOWNERS syntax on push | Confirm `.github/CODEOWNERS` globs cover contracts/·docs/adr/·golden/ + examples/*/{contracts,golden}; document that "require review from code owners" must be enabled in branch protection |
| PR template surfaces on new PRs | CI-02 | GitHub UI behavior; only visible on a real PR | Confirm `.github/pull_request_template.md` renders breaking-change/golden/drift checklist when a PR is opened |
| CI workflow green on a real PR | CI-01 | Requires opening the `claude/…` → default PR (D-B — deferred to explicit user approval); first real .NET run | Only after user go-ahead: open PR, confirm all gate legs + fan-in gate pass |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s (local legs)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
