---
phase: 1
slug: constitution-golden-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `01-RESEARCH.md` §Validation Architecture (all 9 REQs → observable commands).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (Python)** | pytest 8.4.x (pin per CLAUDE.md; env resolves 9.1.1 — resolve A1 in Wave 0) + syrupy |
| **Framework (.NET)** | xunit.v3 3.2.2 (minimal smoke on toy converter; golden equivalence is language-neutral) |
| **Config file** | `pyproject.toml` (uv workspace root + pytest config) — created in Wave 0 |
| **Quick run command** | `uv run pytest <touched module>/tests -x` |
| **Full suite command** | `uv run pytest && uv run ruff check . && bash tools/contract-drift/check.sh` |
| **Estimated runtime** | ~30–60 seconds (excludes one-time .NET SDK bootstrap) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest <touched module>/tests -x` (< 30s)
- **After every plan wave:** Run full suite (`uv run pytest && uv run ruff check . && bash tools/contract-drift/check.sh`)
- **Before `/gsd:verify-work`:** two-fixture golden demo green (repr-only PASS / value-regression FAIL) + drift-mutation demo trips the gate + bootstrap smoke green
- **Max feedback latency:** ~30 seconds (quick), ~60 seconds (full)

---

## Per-Task Verification Map

> Task IDs assigned by the planner; rows below are requirement-level anchors the planner MUST cover. Threat refs from `01-RESEARCH.md` §Security Domain.

| Req | Wave | Behavior | Threat Ref | Test Type | Automated Command | File Exists | Status |
|-----|------|----------|------------|-----------|-------------------|-------------|--------|
| BOOT-01 | 0 | `dotnet --version` starts `10.` after bootstrap | — | smoke | `bash tools/bootstrap/verify.sh` | ❌ W0 | ⬜ pending |
| BOOT-02/03 | 0 | uv workspace resolves; SessionStart idempotent (2nd-run cache hit) | slopsquat | smoke | `uv sync --frozen` + cache-hit assert | ❌ W0 | ⬜ pending |
| CONTRACT-01 | 1 | Seed YAML + companion schema validate (Draft 2020-12) | V5 input-val | unit | `uv run check-jsonschema --schemafile <schema> <instance>` | ❌ W0 | ⬜ pending |
| CONTRACT-02 | 1 | Both language cores emit identical canonical output on shared corpus | — | unit (parity) | `uv run pytest libs/python/normalize/tests -x` + `dotnet test libs/dotnet` | ❌ W0 | ⬜ pending |
| CONTRACT-03 (PASS) | 2 | repr-only fixture (BOM/CRLF/decimal/TZ) PASSES golden | — | integration | `uv run pytest tools/golden-runner/tests/test_repr_only.py -x` | ❌ W0 | ⬜ pending |
| CONTRACT-03 (FAIL) | 2 | value-regression fixture FAILS golden | — | integration | `uv run pytest tools/golden-runner/tests/test_value_regression.py -x` | ❌ W0 | ⬜ pending |
| CONTRACT-03 (gate) | 2 | `/golden-approve` refuses baseline write w/o human sign-off | V4 / P9 | unit | `uv run pytest tools/golden-runner/tests/test_approve_gate.py -x` | ❌ W0 | ⬜ pending |
| CONTRACT-04 (drift) | 1 | mutating a §4-5 convention field bumps hash + trips gate | V6 / P14 | unit | `uv run pytest tools/contract-drift/tests/test_convention_mutation.py -x` | ❌ W0 | ⬜ pending |
| CONTRACT-04 (classify) | 1 | breaking vs non-breaking classification | V6 | unit | `uv run pytest tools/contract-drift/tests/test_classify.py -x` | ❌ W0 | ⬜ pending |
| DOCS-01/02 | 1 | Diátaxis dirs + adr/0001 + glossary exist | — | structural | `test -d docs/tutorials && test -f docs/adr/0001-*.md && test -f docs/glossary.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — uv workspace root + pytest config + tool pins (resolve A1: pytest 8.4 pin vs env 9.1.1)
- [ ] `tools/golden-runner/tests/conftest.py` — subprocess / toy-converter fixtures (`subprocess.run([list], shell=False)`)
- [ ] `libs/normalize-fixtures/` — shared `(raw, canonical)` corpus consumed by BOTH Python and .NET cores
- [ ] `components/toy-converter/` csproj + minimal xunit smoke (needs .NET 10 → BOOT-01 first)
- [ ] `tools/bootstrap/verify.sh` — asserts dotnet 10 present + uv resolve
- [ ] Framework install: `uv add --dev pytest syrupy ruff pyright check-jsonschema` + `uv add rfc8785 jsonschema`

*Wave 0 (BOOT-01/02/03) gates everything: no .NET SDK in the ephemeral container, so the toy converter and any `dotnet test` are inert until bootstrap runs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Human promotion of `.received` → `.verified` baseline | CONTRACT-03 | Phase-1 minimal `/golden-approve` = human-in-loop by design (hard CODEOWNERS/plugin enforcement deferred to P4/P5, assumption A2) | Reviewer inspects normalized diff, links an ADR, then promotes; the *refusal path* (no auto-promote) IS automated via `test_approve_gate.py` |

*The refusal/guard behavior is automated; only the affirmative human promotion is manual by design.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
