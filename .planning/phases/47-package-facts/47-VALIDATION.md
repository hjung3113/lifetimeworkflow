---
phase: 47
slug: package-facts
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-30
---

# Phase 47 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (`>=8.4,<9`, root `pyproject.toml:16`) + syrupy 5.2.0 (root `pyproject.toml:17`) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["libs/python", "tools"]`) |
| **Quick run command** | `uv run pytest tools/adoption_scan tools/memory_regen tools/harness_config tools/contract_graph tools/harness_lint -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~30 seconds quick / ~3 min full |

---

## Sampling Rate

- **After every task commit:** the touched package's quick-run command
- **After every plan wave:** `uv run pytest tools/adoption_scan tools/memory_regen tools/harness_config tools/contract_graph tools/harness_lint`
- **Before `/gsd:verify-work`:** `uv run pytest` green AND `uv run python -m tools.harness_emit` re-emit diff clean
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 47-01-* | 01 | 1 | MONO-02 | — | N/A | unit | `uv run pytest tools/adoption_scan/tests/test_detect.py -x` | ✅ (new cases) | ⬜ pending |
| 47-02-* | 02 | 2 | MONO-01, MONO-02 | — | N/A | unit + snapshot | `uv run pytest tools/memory_regen/tests/test_package_facts.py -x` | ❌ W0 | ⬜ pending |
| 47-03-* | 03 | 3 | MONO-03 | — | N/A | unit + structural | `uv run pytest tools/harness_config/tests tools/harness_lint/tests/test_package_facts_override.py -x` | ❌ W0 | ⬜ pending |
| 47-04-* | 04 | 3 | MONO-04 | — | N/A | unit | `uv run pytest tools/contract_graph/tests/test_ownership.py -x` | ❌ W0 | ⬜ pending |
| 47-05-* | 05 | 4 | SC5 (no gate/job growth) | injection into CI shell steps | `stale-derived` never interpolates `${{ github.event.* }}` | structural | `uv run pytest tools/harness_lint/tests/test_ci_stale_derived.py -x` | ✅ needs edit | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/memory_regen/tests/test_package_facts.py` — determinism (delete + regenerate byte-identical), correctness per manifest kind, add/remove-a-dependency fixture proof (MONO-01, MONO-02)
- [ ] `tools/memory_regen/tests/__snapshots__/test_package_facts.ambr` — committed syrupy snapshot, same idiom as `test_contracts_index`
- [ ] Synthetic fixture manifests for all five kinds — the live tree exercises only 2 of 5 edge kinds (both `.csproj` `ProjectReference`), so `pyproject.toml`, `package.json`, `go.mod` and `Cargo.toml` edges MUST be proven on fixtures
- [ ] `tools/harness_lint/tests/test_package_facts_override.py` — MONO-03 consistency gate, mirrors `test_pipeline_config.py`
- [ ] `tools/contract_graph/tests/test_ownership.py` — MONO-04, domain-neutral synthetic fixtures (GEN-04 clean)
- [ ] Framework install: none — pytest + syrupy already in `uv.lock`

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
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
