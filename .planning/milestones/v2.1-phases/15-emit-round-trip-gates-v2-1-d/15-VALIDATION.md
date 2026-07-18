---
phase: 15
slug: emit-round-trip-gates-v2-1-d
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-16
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `15-RESEARCH.md` § Validation Architecture (measured against this working tree, not inferred).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 + syrupy (`.ambr` snapshots) |
| **Config file** | root `pyproject.toml` — `testpaths = ["libs/python", "tools"]`, `addopts = "-ra"` |
| **Quick run command** | `uv run pytest tools/harness_emit -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~2 seconds (full suite measured at 1.53s) |

**Baseline at phase start:** 1 failed / 658 passed. The single red is the sanctioned
`test_projected_tree_matches_committed_snapshot`. Expected at phase end: **0 failed / 659 passed**.

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tools/harness_emit -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite green (0 failed / 659 passed) **plus** the manual
  re-emit + `git diff --exit-code` replica below — the suite alone cannot prove the committed
  trees are current.
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 15-01-XX | 01 | 1 | MEM2-06 | — | N/A | integration | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` | ⚠️ CI-only, run manually | ⬜ pending |
| 15-01-XX | 01 | 1 | MEM2-06 | — | N/A | unit | `uv run pytest tools/harness_emit/tests/test_coexist.py::test_all_20_commands_emit_to_both_trees` | ✅ | ⬜ pending |
| 15-01-XX | 01 | 1 | MEM2-06 | — | N/A | snapshot | `uv run pytest tools/harness_emit/tests/test_emit_determinism.py::test_projected_tree_matches_committed_snapshot` | ✅ (red → green on regen) | ⬜ pending |
| 15-01-XX | 01 | 1 | MEM2-06 | — | N/A | unit | `uv run pytest tools/harness_emit/tests/test_emit_determinism.py::test_emit_twice_byte_identical` | ✅ | ⬜ pending |
| 15-02-XX | 02 | 2 | MEM2-06 | — | No model identifier in any repo artifact (CLAUDE.md constraint) | unit | `uv run pytest tools/harness_lint/tests/test_opencode_json.py tools/harness_lint/tests/test_agents.py -k model` | ✅ | ⬜ pending |
| 15-02-XX | 02 | 2 | MEM2-06 | — | N/A | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` | ✅ | ⬜ pending |
| 15-02-XX | 02 | 2 | MEM2-06 | — | N/A | suite | `uv run pytest` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.* No framework install, no new fixtures.

One structural gap is **knowingly left open**: no local test reads the committed `.opencode/` /
`.claude/` trees — `test_projected_tree_matches_committed_snapshot` renders from `harness/` source
and never reads them. Filling it would add emitter-adjacent test surface beyond MEM2-06's scope in a
change-no-code phase. It is carried in `15-RESEARCH.md` § Open Questions as a follow-up candidate,
and mitigated here by the mandated manual re-emit + `git diff` replica.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Committed `.opencode/` + `.claude/` trees match a fresh emit (emit-drift clean) | MEM2-06 | No local test reads the committed trees; only the CI `emit-drift` job diffs them. Replicating it locally is a shell gate, not a pytest case. | Run `uv run python -m tools.harness_emit`, then `git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json`. A clean exit **after** the emit's own writes are committed proves drift-free. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (none — existing infrastructure suffices)
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Gate-theft guard (phase-specific):** `--snapshot-update` alone turns the suite green while the
committed trees still lack `/agree`. Regenerating the `.ambr` is legitimate (SC1's "fixtures
updated") **only after** the emitter has actually run and its output is committed. Snapshot-update
before emit is gate theft and must fail review.

**Approval:** approved 2026-07-16 (gsd-plan-checker Dimension 8 walkthrough 8a–8e passed against 15-01/15-02)
