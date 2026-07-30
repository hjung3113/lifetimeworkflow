---
phase: 50a
slug: harness-authoring
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-30
---

# Phase 50a — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x + syrupy 5.2.0 |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` — not modified by this phase |
| **Quick run command** | `uv run pytest tools/harness_lint tools/harness_emit -q` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~15 s |

---

## Sampling Rate

- **After every task commit:** quick run command above
- **After the atomic absorption commit:** `uv run pytest -q` + `uv run python -m tools.harness_emit`
  (must succeed, then be idempotent)
- **Before `/gsd:verify-work`:** full suite green; skills == 8; commands == 19
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 50a-01-* | 01 | 1 | MONO-10 | — | N/A | structural | `uv run pytest tools/harness_lint/tests/test_harness_author.py -x` | ❌ W0 | ⬜ pending |
| 50a-02-* | 02 | 2 | MONO-10, MONO-11 | — | N/A | structural + emit round-trip | `uv run pytest tools/harness_lint tools/harness_emit -q`; then `uv run python -m tools.harness_emit` twice | ✅ extend | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tools/harness_lint/tests/test_harness_author.py` — every `path:line` citation in a skill body
      (outside fenced code blocks) resolves to a tracked file, and where a name anchor is cited the
      name is present. Mechanical template: `test_core_no_example_dep.py:80-96`. **No prior art
      exists — this is new test code.**
- [ ] A no-dangling-reference assertion — no tracked file outside `.planning/` references
      `skill-creator` after the change
- [ ] A reachability check for MONO-11 that can fail — `skill-creator`'s load-bearing content
      (Step-0 anti-sprawl question, the name regex / dir-name-match / description-cap shape rules, the
      shared-caps note, the verify command) must be present in `harness-author`, asserted rather than
      claimed
- [ ] Update the three-way pin **as one step**: `caps.py:139-150` `EXPECTED_SKILLS`,
      `test_skills.py::test_expected_skills_present_no_sprawl`,
      `test_emit_determinism.py::test_emitted_skill_set_matches_expected`
- [ ] Regenerate `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
      (`--snapshot-update`) — it embeds the skill name at lines 2471, 2477, 2807, 2810, 2814
- [ ] Framework install: none

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
