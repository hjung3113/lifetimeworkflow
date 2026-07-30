---
phase: 48
slug: convention-profiles
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-30
---

# Phase 48 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x + syrupy 5.2.0 (root `pyproject.toml`) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` — not modified by this phase |
| **Quick run command** | `uv run pytest tools/harness_config/tests tools/memory_regen/tests tools/harness_lint/tests/test_commands.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~15 s quick / ~15 s full |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tools/harness_config/tests tools/memory_regen/tests -x`
- **After every plan wave:** `uv run pytest` + `uv run python -m tools.harness_emit` idempotency check
- **Before `/gsd:verify-work`:** full suite green; `stale-derived` and `emit-drift` definitions unchanged
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 48-01-* | 01 | 1 | MONO-05, MONO-06 | — | N/A | unit | `uv run pytest tools/harness_config/tests/test_conventions_for.py -x` | ❌ W0 | ⬜ pending |
| 48-02-* | 02 | 2 | MONO-05 | — | N/A | unit + snapshot | `uv run pytest tools/memory_regen/tests/test_package_facts.py -x` | ✅ extend | ⬜ pending |
| 48-03-* | 03 | 3 | MONO-07 | — | N/A | structural + emit round-trip | `uv run pytest tools/harness_lint/tests/test_commands.py -x` then `uv run python -m tools.harness_emit && git diff --exit-code` | ✅ extend | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tools/harness_config/tests/test_conventions_for.py` — nearest-wins on the real `libs/python`
      vs root pair (keyed on id/dir/nearest-AGENTS.md, NOT on commands, which are identical);
      explicit-default profile for a path outside any package; MONO-06 in the strong falsifiable
      form (edit a `[[languages]]` command in a synthetic cfg → every affected profile's reported
      command changes with no profile edited); a language absent from `[[languages]]` reports no
      commands without raising; a synthetic two-language fixture proving the commands-differ case
- [ ] Extend `tools/memory_regen/tests/test_package_facts.py` — new rendered section covered by
      structural assertions plus the hermetic snapshot; determinism (byte-identical regeneration)
      must still hold with the section present
- [ ] Extend `tools/harness_lint/tests/test_commands.py` — `test_command_count_is_stable` (no such
      assertion exists today; without it criterion 4 is a one-time manual measurement)
- [ ] Framework install: none — pytest + syrupy already resolved

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
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
