---
phase: 9
slug: self-maintaining-derived-artifacts-curator-v2-0
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-13
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `09-RESEARCH.md` § Validation Architecture. Signals map to SC1–SC5 + MAINT-01..04.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (uv workspace; root `testpaths = tools/ + libs/python`) |
| **Config file** | `pyproject.toml` (root) + per-member `pyproject.toml` |
| **Quick run command** | `uv run pytest tools/harness_emit tools/harness_lint tools/docs_sync tools/memory_regen -x` |
| **Full suite command** | `uv run pytest` (non-example core suite) |
| **Estimated runtime** | ~30 seconds (quick) / ~90 seconds (full core) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/harness_emit tools/harness_lint tools/docs_sync tools/memory_regen -x`
- **After every plan wave:** Run `uv run pytest` (full core) + emit-drift preview: `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode .claude AGENTS.md CLAUDE.md opencode.json`
- **Before `/gsd:verify-work`:** Full core suite green + `stale-derived` / `emit-drift` / GEN-04 jobs green
- **Max feedback latency:** ~90 seconds

---

## Per-Task Verification Map

> Signal-level (task IDs assigned at plan time; the planner maps each signal into a plan/wave/task).

| Signal | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command / Assertion | File Exists | Status |
|--------|-------------|------------|-----------------|-----------|-------------------------------|-------------|--------|
| SC1 curator persona exists, read-mostly, derived-only | MAINT-01 | T-9-01 | Curator cannot write constitution/golden/source (path_deny_globs + contract-guard) | unit | `test_agents.py`: `"curator" in EXPECTED_PERSONAS`; assert constitution paths in `path_deny_globs` | ❌ W0 | ⬜ pending |
| SC1 curator body invokes ONLY existing tools | MAINT-01 | — | No new derivation logic in persona | unit | scan `harness/agents/curator.md` + `refresh-memory.md` → reference only `tools.memory_regen` / `tools.docs_sync` module paths | ❌ W0 | ⬜ pending |
| SC2 `stale-derived` job regenerates + fails on diff | MAINT-02 | T-9-02 | Stale derived plane cannot merge | ci-assert + unit | CI job present in `ci.yml` + `gate.needs`; negative-control: mutate committed page → `git diff --cached --exit-code` fails; clean → passes | ❌ W0 | ⬜ pending |
| SC2 `docs_sync` prunes orphaned pages | MAINT-02 | — | Orphaned reference page removed on regen | unit | `test_docs_sync_*`: stray `docs/reference/x.md` with no schema → `write()` removes it; `README.md` preserved | ❌ W0 | ⬜ pending |
| SC3 no new heavy on-write memory hook | MAINT-03 | — | Commits stay fast/quiet; heavy regen deferred to CI | unit | assert `.claude/settings.json` hook groups + `harness/plugins/*.ts` contain NO `memory_regen`/`docs_sync` on Pre/PostToolUse write path | ❌ W0 | ⬜ pending |
| SC4 `/refresh-memory` exists + `/verify-work` freshness | MAINT-04 | — | Drift caught pre-handoff, not only CI | unit | `refresh-memory` discovered + emitted; `verify-work.md` body contains regen+diff freshness step | ❌ W0 | ⬜ pending |
| SC5 emitter round-trips curator + command to both runtimes, no model id | MAINT-01..04 | — | Both runtimes emitted; no model identifier in artifacts | unit | `test_emit_determinism.py`: re-emit byte-identical; `emit-manifest.json` lists `.opencode/agent/curator.md`, `.claude/agents/curator.md`, both command paths; `check_agent` no-model-id | ⚠️ partial → W0 update manifest | ⬜ pending |
| SC5 core stays example-independent | MAINT-01..04 | — | No example/domain token in curator/command | unit | `test_core_no_example_dep.py` (GEN-04) green | ✅ exists (keep green) | ⬜ pending |
| Determinism: regenerated derived set byte-identical | MAINT-02 | — | Clean tree regenerates to empty diff | ci-assert | `stale-derived` empty diff on freshly-regenerated clean tree | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/harness_lint/caps.py` — `EXPECTED_PERSONAS` 4→5 (add `curator`); update `test_agents.py`
- [ ] `docs/reference/` — reconcile pre-existing drift: delete 4 orphan pages (`correction-rules`, `equipment-master`, `equipment-progress`, `standard-log`), add missing `greeting.md`
- [ ] `tools/docs_sync/generate.py` — add prune-then-write + a prune test
- [ ] `tools/docs_sync/tests/` — update determinism snapshot / EXPECTED_PAGES after reconcile
- [ ] `.github/workflows/ci.yml` — `stale-derived` job + `gate.needs` + negative-control test for the gate logic
- [ ] `tools/harness_emit/emit-manifest.json` — regenerate + commit after adding curator + refresh-memory
- [ ] New tests: hook-posture (no memory regen on on-write path) + curator write-boundary + body-invokes-only-tools
- [ ] Framework install: none — pytest/uv already present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI `stale-derived` job actually red on a real PR with stale derived | MAINT-02 | Requires a live PR run against GitHub Actions | Open a throwaway PR mutating a committed derived page; confirm the `stale-derived` job fails with the actionable fix message |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All signals have an `<automated>` verify or Wave 0 dependency
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (caps bump, docs/reference reconcile, prune, CI job, manifest)
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-13 (plan-checker Dimension 8 PASS — every task carries a concrete `<automated>` command, no MISSING placeholders, sampling continuity 100%)
