---
phase: 5
slug: despecialization
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-09
---

# Phase 5 — Validation Strategy

> Source: `05-RESEARCH.md` §Validation Architecture. Pure refactor/move — ZERO new external packages.
> The phase-wide invariant is: `uv run pytest` (the non-example suite, `testpaths=[libs/python, tools]`)
> stays GREEN, and `uv run python -m tools.contract_drift.drift` reads clean after the move.
> .NET stays egress-deferred: the domain golden actual-run SKIPs; the generic loop runs .NET-free
> via the identity converter (D-01b Q3).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.4,<9 + syrupy 5.2.0 snapshots (root dev group) |
| **Config file** | root `pyproject.toml` (`testpaths = ["libs/python", "tools"]` — `examples/` is deliberately OUT of scope) |
| **Quick run command** | `uv run pytest tools/hooks tools/golden_runner tools/harness_lint tools/harness_config -x -q` |
| **Full suite command** | `uv run pytest` (keep Phase 1-4 suites green) |
| **Drift gate** | `uv run python -m tools.contract_drift.drift` (exit 0 == clean) |
| **Estimated runtime** | ~15–45 s |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/<changed_pkg> -x -q` (+ `tools/hooks/tests/test_commit_gate.py` when the gate is touched).
- **After every plan wave:** `uv run pytest` (full non-example suite) + `uv run python -m tools.contract_drift.drift`.
- **Before `/gsd:verify-work`:** full suite green + drift clean + manual demo of each success criterion (move history-preserved; generic loop runs .NET-free; config = SSOT; core grep clean; token lands an intended contract change).

---

## Per-Requirement Verification Map

| Req / Crit | Behavior | Test Type | Automated Command | File | Plan |
|------------|----------|-----------|-------------------|------|------|
| D-05 | drift + non-empty token → WARN/PASS (exit 0) | unit | `uv run pytest tools/hooks/tests/test_commit_gate.py -x` | ⚠️ extend | 05-01 |
| D-05 | drift + absent token → still BLOCK | unit | same | ⚠️ extend | 05-01 |
| D-05 | drift + empty/blank token → still BLOCK | unit | same | ⚠️ extend | 05-01 |
| D-05 | token ≠ weaken polyglot (staged BOM/CRLF TSV still blocks) | unit | same | ⚠️ extend | 05-01 |
| GEN-03 | permission-matrix scopes derive from `harness/project.toml` (SSOT) | unit | `uv run pytest tools/harness_lint/tests/test_language_config.py -x` | ❌ W0 | 05-04 |
| GEN-03 | each configured language has an existing persona | unit | same | ❌ W0 | 05-04 |
| GEN-03 | loader parses config, stdlib-only (tomllib) | unit | `uv run pytest tools/harness_config/tests/test_loader.py -x` | ❌ W0 | 05-04 |
| GEN-02 | identity converter + golden_dir override (generic loop, no .NET) | unit | `uv run pytest tools/golden_runner/tests/test_identity_converter.py -x` | ❌ W0 | 05-02 |
| GEN-02 | generic sample case PASSES the full loop, no .NET | integration | `uv run pytest tools/golden_runner/tests/test_sample_loop.py -x` | ❌ W0 | 05-02 |
| GEN-02 | root contract→hash→drift clean with sample added | integration | `uv run python -m tools.contract_hash.hash --write && uv run python -m tools.contract_drift.drift` | ✅ engine; assertion new | 05-02 |
| GEN-02 | added seed.tsv is byte-clean (no BOM/CR) | unit | `od -c golden/sample/input/seed.tsv` (no `357 273 277`, no `\r`) | ❌ W0 | 05-02 |
| GEN-02 | docs-sync EXPECTED_PAGES includes the sample page | unit | `uv run pytest tools/docs_sync/tests/test_docs_sync_determinism.py -x` | ⚠️ extend | 05-02 |
| GEN-01 | move is a history-preserving rename (status R) | unit | `git status --short \| grep '^R'` ; `git log --follow examples/log-parser/contracts/log-specs/standard-log.schema.json` | manual/CI | 05-03 |
| GEN-01 | live drift clean AFTER move + rebaseline | integration | `uv run python -m tools.contract_drift.drift` (exit 0) | ✅ engine; assertion new | 05-03 |
| GEN-01 | example gets its own rebaselined manifest | unit | `test -f examples/log-parser/contracts/.hashes/manifest.json` | ❌ W0 | 05-03 |
| GEN-01 | stale snapshots regenerated (docs-sync + 2 .ambr) | snapshot | `uv run pytest tools/docs_sync tools/memory_regen -x` | ⚠️ regen | 05-03 |
| GEN-01 | normalize core + fixtures UNMOVED (uv workspace intact) | suite | `uv run pytest` + `test -d libs/python/normalize -a -d libs/normalize-fixtures` | ✅ must stay green | 05-03 |
| GEN-04 | no core file references `examples/**` | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ❌ W0 | 05-05 |
| GEN-04 | non-example suite green after extraction | suite | `uv run pytest` (examples/ out of testpaths) | ✅ must stay green | 05-05 |
| GEN-04 (SC5) | ADR-0002 present + README index appended (append-only) | structural | `test -f docs/adr/0002-*.md && grep 0002 docs/adr/README.md` | ❌ W0 | 05-05 |
| GEN-04 (SC5) | root docs recast + log-parser specifics in the example | structural | `grep examples/log-parser AGENTS.md && test -f examples/log-parser/README.md` | ❌ W0 | 05-05 |

*Status: ⬜ pending · ✅ green · ❌ red (Wave 0) · ⚠️ extend/regen existing*

---

## Wave 0 Requirements

- [ ] Extend `tools/hooks/tests/test_commit_gate.py` — the four D-05 approval cases (05-01).
- [ ] `harness/project.toml` + `tools/harness_config/{__init__.py,loader.py,pyproject.toml,tests/test_loader.py}` — GEN-03 config slot + loader (new `tools/*` uv member) (05-04).
- [ ] `tools/harness_lint/tests/test_language_config.py` — GEN-03 consistency (config == matrix scopes + personas) (05-04).
- [ ] `tools/golden_runner/tests/test_identity_converter.py` + parametrized `runner.py` — GEN-02 identity converter + golden_dir override (05-02).
- [ ] `contracts/sample/greeting.schema.json` + `golden/sample/**` + `tools/golden_runner/tests/test_sample_loop.py` — GEN-02 default instance (05-02).
- [ ] Extend `tools/docs_sync/tests/test_docs_sync_determinism.py` `EXPECTED_PAGES` (add `greeting` in 05-02; reduce to {format-conventions, greeting} in 05-03).
- [ ] Regenerate `tools/memory_regen/tests/__snapshots__/{test_contracts_index,test_repo_map_determinism}.ambr` after the move (05-03).
- [ ] `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 guard (05-05).
- [ ] `uv sync --all-packages` after adding the `tools/harness_config` member; `uv.lock` re-resolved. Zero new external packages.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The move commit lands through the LIVE pre-commit gate via `GOLDEN_APPROVE_HUMAN` | GEN-01 / D-05 | The token must be set in the human-controlled Claude Code process env (agents may not fabricate it); it is a human ratification, not an automatable step | Human exports `GOLDEN_APPROVE_HUMAN` before the 05-02/05-03/05-05 sessions (or a gitignored `.claude/settings.local.json` `env` block, removed after). NEVER `--no-verify`, NEVER edit `.claude/settings.json` to drop the hook. Verify: the move commit exists and `git log` shows the pre-commit gate ran. |
| Domain golden actual-run (.NET toy-converter) at real parity | GEN-01/02 | .NET egress-blocked (deferred since Phase 1) | Deferred — the moved domain golden tests SKIP when dotnet is absent; the generic loop proves the machinery .NET-free via the identity converter. Real .NET parity runs on GitHub runners in Phase 6. |
| `git log --follow` shows preserved history across the rename | GEN-01 | History-follow is a git behavior, best eyeballed | `git log --follow examples/log-parser/contracts/log-specs/standard-log.schema.json` shows pre-move commits. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [x] `nyquist_compliant: true` set in frontmatter
- [x] Phase-wide invariant encoded: `uv run pytest` (non-example) green + `contract_drift.drift` clean
- [x] Security controls are "do not weaken": token bypasses drift ONLY; polyglot/secret/golden stay hard (tested in 05-01)

**Approval:** pending plan-check. `wave_0_complete` flips true at execution once the Wave 0 scaffolds (config slot + loader + sample instance + guard/consistency/identity tests + commit-gate extension) exist.
