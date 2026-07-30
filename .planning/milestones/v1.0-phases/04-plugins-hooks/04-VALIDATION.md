---
phase: 4
slug: plugins-hooks
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-08
---

# Phase 4 — Validation Strategy

> Source: `04-RESEARCH.md` §Validation Architecture. Claude hooks fire+testable HERE; opencode plugins authored-only (deferred); golden-parity real .NET run deferred (.NET-gated).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4,<9 (root dev group) |
| **Config file** | root `pyproject.toml` (`testpaths` covers `tools`) |
| **Quick run command** | `uv run pytest tools/polyglot_lint tools/hooks tools/harness_perms -x -q` |
| **Full suite command** | `uv run pytest` (keep Phase-1/2/3 suites green) |
| **Estimated runtime** | ~15–40 s |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/<changed_pkg> -x -q`
- **After every plan wave:** `uv run pytest`
- **Before `/gsd:verify-work`:** full suite green + manual demo of each success criterion (contracts edit blocked; BOM/CRLF TSV fails linter; secret blocked; commit-gate non-zero on drift)

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | File |
|-----|----------|-----------|-------------------|------|
| POLY-01 | BOM/CRLF raw → violation; clean → none | unit | `uv run pytest tools/polyglot_lint/tests/test_lint.py -x` | ❌ W0 |
| POLY-01 | non-canonical decimal/datetime/null cell → violation (shares `normalize.core`) | unit | same | ❌ W0 |
| POLY-01 | TSV column-shift (uneven tabs) → violation | unit | same | ❌ W0 |
| POLY-01 | linter canonical == `normalize_tsv`/`normalize_cell` on `libs/normalize-fixtures/*.json` (no drift) | unit | `tools/polyglot_lint/tests/test_corpus_parity.py` | ❌ W0 |
| HOOK-04 | write to `contracts/**`/`adr/**`/`golden/**` w/o approval → `permissionDecision:"deny"`; with NON-EMPTY `GOLDEN_APPROVE_HUMAN` token → no decision; empty-string token → still deny | unit | `tools/hooks/tests/test_contract_guard.py` | ❌ W0 |
| HOOK-04 | source-path write (`libs/python/foo.py`) → allowed; BOM/CRLF on an ALLOWED path → no contract-guard decision (format-on-write's job); BOM/CRLF on an APPROVED constitution path → still deny | unit | same | ❌ W0 |
| HOOK-02 | real secret (AWS key/PEM) in content or `*.env` path → deny; benign fixture → allow; constitution-plane path w/o secret → NOT denied (contract-guard's domain; secret_scan uses SECRET_PATH_GLOBS subset) | unit | `tools/hooks/tests/test_secret_scan.py` | ❌ W0 |
| POLY-01 (composition) | `GOLDEN_APPROVE_HUMAN` unblocks a constitution write end-to-end when secret_scan + contract-guard both fire (secret_scan does not shadow the bypass) | unit | `tools/hooks/tests/test_secret_scan.py` + `test_contract_guard.py` | ❌ W0 |
| POLY-01 (in-session) | `/lint` invokes `python -m tools.polyglot_lint.lint` over tracked boundary files (in-session call site); ruff/dotnet blocks preserved | structural | `tools/hooks/tests/test_lint_command_wires_polyglot.py` | ❌ W0 |
| HOOK-01 | BOM+CRLF file → LF/no-BOM after; format twice == once (idempotent, via subprocess not Write) | unit | `tools/hooks/tests/test_format_on_write.py` | ❌ W0 |
| HOOK-01 | dotnet absent → `.cs` path skips gracefully | unit | same | ❌ W0 |
| HOOK-03 | drift present → block/non-zero; clean → 0 | unit | `tools/hooks/tests/test_commit_gate.py` | ❌ W0 |
| HOOK-03 | polyglot violation in staged file → block | unit | same | ❌ W0 |
| HOOK-03 | dotnet absent → golden-parity SKIP (not fail) | unit | same | ❌ W0 |
| Crit-4 | last-wins (specific > catch-all); default-deny (`ask`) unmatched; `rm -rf`→deny | unit | `tools/harness_perms/tests/test_order_resolution.py` (or extend test_resolver.py) | ⚠️ extend |
| Crit-4 | constitution-plane edit (`contracts/`/`adr/`/`golden/`) resolves to deny | unit | same | ⚠️ extend |
| Coexist | after `.claude/settings.json` edit, all pre-existing GSD hook commands still present | unit | `tools/hooks/tests/test_settings_coexist.py` | ❌ W0 |
| Hook I/O | each hook: crafted stdin JSON → asserted exit + decision JSON | unit | per-gate test invoking main()/subprocess with stdin fixture | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red*

---

## Wave 0 Requirements

- [ ] `tools/polyglot_lint/{__init__.py,lint.py,pyproject.toml,tests/test_lint.py,tests/test_corpus_parity.py}` — POLY-01 (reuse `libs/python/normalize` core, no re-implementation; POLY trick = normalize a copy, diff vs raw)
- [ ] `tools/hooks/{__init__.py,_stdin.py,pyproject.toml}` + `tests/` — shared stdin adapter + gate tests (three-layer idiom: pure core + main(argv) + stdin adapter)
- [ ] `tools/hooks/tests/test_settings_coexist.py` — asserts GSD SessionStart(4)/PreToolUse(4)/PostToolUse(3) hooks preserved after append
- [ ] Extend `tools/harness_perms/tests/` — crit-4 order-resolution suite
- [ ] Framework already present (pytest locked); `uv sync --all-packages` after adding members. Zero new external packages.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| opencode plugin (`tool.execute.before/after`) actually fires | HOOK-01..04 | opencode runtime absent (D-01) — authored-only stub | Deferred — verify when opencode installed; the shared Python enforcement logic IS unit-tested |
| commit-gate runs REAL golden parity (.NET) | HOOK-03 | .NET egress-blocked (D-06) | Deferred — gate SKIPs golden-parity gracefully when dotnet absent (tested); other gates (drift, polyglot) run live |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 40s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** signed off 2026-07-08 (post plan-check revision — 4 blockers + 2 warnings resolved: secret_scan glob subset, contract-guard polyglot scoping, POLY-01 in-session /lint wiring, Q1/Q2/Q3 resolved, empty-token hardening). `wave_0_complete` flips true at execution.
