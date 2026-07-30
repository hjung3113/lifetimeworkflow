---
phase: 2
slug: two-plane-memory-rules
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-08
---

# Phase 2 — Validation Strategy

> Per-phase validation contract. Source: `02-RESEARCH.md` §Validation Architecture (all 4 success criteria + 6 REQs → observable commands).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4,<9 (workspace root `[tool.pytest.ini_options]`, `testpaths` covers `tools`) |
| **Snapshot lib** | syrupy 5.2.0 (dev dep) — committed `.ambr` = determinism reference |
| **Config file** | root `pyproject.toml` — add `tools/memory_regen` coverage |
| **Quick run command** | `uv run pytest tools/memory_regen -x -q` |
| **Full suite command** | `uv run pytest` (must keep Phase-1 drift/golden suites green after adding the member) |
| **Estimated runtime** | ~10–30 s |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/memory_regen -x -q`
- **After every plan wave:** `uv run pytest` (full workspace)
- **Before `/gsd:verify-work`:** full suite green; determinism snapshots stable

---

## Per-Task Verification Map

> Determinism NOTE (research finding): `.memory/derived/` is gitignored (D-03), so a `git diff` determinism test is a silent no-op. Prove regenerate-identical via a committed syrupy snapshot OR generate-twice-and-hash — NOT git diff.

| Criterion / REQ | Behavior | Test Type | Automated Command | File Exists |
|-----------------|----------|-----------|-------------------|-------------|
| Crit-1 / MEM-01/02 | Constitution plane present + marked immutable; `.memory/derived/` gitignored, `.memory/state/` committed | structural | `uv run pytest tools/memory_regen/tests/test_layout.py -x` | ❌ W0 |
| Crit-2 / MEM-03 | repo-map delete+regen byte-identical (snapshot/hash, not git diff) | unit/snapshot | `uv run pytest tools/memory_regen/tests/test_repo_map_determinism.py -x` | ❌ W0 |
| Crit-2 / MEM-03 | contracts-index delete+regen identical + drift status correct (reuses Phase-1 `contract_hash`/`contract_drift`) | unit/snapshot | `uv run pytest tools/memory_regen/tests/test_contracts_index.py -x` | ❌ W0 |
| MEM-03 | tree-sitter parses .py/.cs/.sh → def/ref caps non-empty (ts 0.25 `Query`+`QueryCursor` API) | unit | `uv run pytest tools/memory_regen/tests/test_parse.py -x` | ❌ W0 |
| Crit-3 / RULES-01/02 | Root + per-package AGENTS.md exist; CLAUDE.md pointer; non-negotiables restated per-package (P11) | structural | `uv run pytest tools/memory_regen/tests/test_agents_md.py -x` | ❌ W0 |
| Crit-4 / HOOK-05 | Payload ≤ ~1k budget; provisional banner present; priority-truncate drops repo-map before banner/drift; no full contract bodies | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py -x` | ❌ W0 |
| Crit-4 / HOOK-05 | `.claude/settings.json` SessionStart has all 4 slots (3 existing + injector; coexist not overwrite) | structural | `uv run pytest tools/memory_regen/tests/test_hook_wiring.py -x` | ❌ W0 |
| P13 / Crit-4 | Injected activeContext is a pointer under the provisional banner (ADR/contract wins) | unit | assert in `test_inject_assembler.py` | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red*

---

## Wave 0 Requirements

- [ ] `tools/memory_regen/pyproject.toml` — new uv member + `tree-sitter 0.25.x` + `tree-sitter-python`/`-c-sharp`/`-bash` + `networkx 3.x` (individual grammar wheels — NOT `tree-sitter-language-pack`, which downloads binaries at runtime → non-deterministic); `uv sync`
- [ ] `tools/memory_regen/tests/conftest.py` — tmp source-tree + tmp contracts-tree fixtures
- [ ] `tools/memory_regen/tests/__snapshots__/` — committed syrupy goldens (determinism reference)
- [ ] The 8 test files above
- [ ] Verify root `pyproject.toml` `testpaths` collects `tools/memory_regen`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| opencode-side session.created / chat.system.transform injection actually fires | HOOK-05 | No opencode runtime in this container (authored-only per D-01) | Deferred — verify when opencode runtime is available; the payload assembler (`inject.assemble()`) both runtimes wrap IS unit-tested |

*The Claude SessionStart injector + the shared payload assembler are automated; only the opencode runtime firing is deferred.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
