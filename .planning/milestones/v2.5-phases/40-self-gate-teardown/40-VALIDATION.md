---
phase: 40
slug: self-gate-teardown
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-27
---

# Phase 40 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> **Deletion phase.** The validation subject is *absence and non-regression*, not new behavior.
> Source: `40-RESEARCH.md` §"Validation Architecture"; contract: `40-CONTEXT.md` D-08.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.x (existing — `pyproject.toml:37` `dev = ["pytest>=8.4,<9", ...]`) |
| **Config file** | `pyproject.toml:38-41` `[tool.pytest.ini_options]` — unchanged by this phase |
| **Quick run command** | `uv run pytest tools/harness_lint -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | quick ~15s · full ~120s |

The quick command is scoped to `tools/harness_lint` because that is the one surviving test directory
that loses a file (`tests/test_skill_registry_lock.py`). A dangling import there is the fastest
observable failure of a mis-ordered deletion.

---

## Sampling Rate

- **After the deletions, before staging:** run the closing grep sweep **and**
  `uv run pytest tools/harness_lint -q`.
- **Before the commit is finalized:** run the full suite plus all six D-08 evidence commands.
  This phase is a single wave and a single atomic commit (D-01) — the phase gate *is* the wave gate.
- **Before `/gsd:verify-work`:** full suite green.
- **Max feedback latency:** ~120 seconds (full suite).

---

## Per-Task Verification Map

| # | Requirement | Behavior verified | Test type | Automated command | Expected | Exists? |
|---|-------------|-------------------|-----------|-------------------|----------|---------|
| V-1 | CER-04 | No `skill_registry` / `registry.lock` / `registry-lock` referent survives | absence (shell) | `grep -rn "skill_registry\|registry-lock\|registry\.lock" tools/ harness/ .github/ pyproject.toml uv.lock` | exit 1 (no match) | N/A — shell assertion |
| V-2 | CER-04 | Only the two documented prose survivors remain repo-wide | absence (shell) | same grep over `docs/` | only `docs/adr/0012-*.md:96-97` and `docs/explanation/agent-workflow-skillset-design-guide.md:564,595,663` | N/A — shell assertion |
| V-3 | CER-04 | `gate.needs` has no dangling job | source assertion | `grep -n "needs:" .github/workflows/ci.yml` | 2 lines (`:80`, `:410`); `:410` contains no `registry-lock` | ✅ existing file |
| V-4 | CER-04 | Suite collects and passes with no dangling import | regression | `uv run pytest` | exit 0, no `ModuleNotFoundError` at collection | ✅ existing |
| V-5 | CER-04 | Workspace resolves after member removal | regression | `uv sync --all-packages` | exit 0 | ✅ existing |
| V-6 | CER-04 | Emitted trees unmoved by this deletion | regression (local mirror of CI `emit-drift`) | `uv run python -m tools.harness_emit` then `git add -A -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` then `git diff --cached --exit-code -- <same path set>` | empty diff | ✅ existing |
| V-7 | CER-04 | Committed-derived plane not left stale | regression (local mirror of CI `stale-derived`) | `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index` then `git add -A -- docs/reference .memory/derived/contracts-index.md` then `git diff --cached --exit-code -- docs/reference .memory/derived/contracts-index.md` | empty diff | ✅ existing |
| V-8 | CER-04 | Contract plane untouched | regression | `uv run python -m tools.contract_drift.drift` | exit 0, clean | ✅ existing |
| V-9 | CER-04 | Lint debt does not regress | regression (ratchet) | `uv run python -m tools.ruff_baseline` | exit 0 | ✅ existing |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. All rows ⬜ pending until execution.*

**V-7 rationale.** ROADMAP Success Criterion 4 names **both** `emit-drift` and `stale-derived`.
V-6 covered only the former; V-7 was inserted next to it so the two diff-based gates read together
(the former contract-drift and ruff rows shifted to V-8 and V-9). `stale-derived` is a distinct CI job (`ci.yml:316-338`) over a different
path set — `docs/reference` + `.memory/derived/contracts-index.md`. It is expected to pass trivially
(no `skill_registry` referent exists in either path), but the SUMMARY must be able to cite it rather
than rely on an unstated assumption.

**Known non-blocking staleness:** `.memory/derived/repo-map.md` carries symbols from
`tools/skill_registry/registry.py` and will be stale after the deletion. It is NOT in
`stale-derived`'s tracked path set and is regenerated on the next `/orient` or `/refresh-memory`, so
it gates nothing. D-06's sweep path list deliberately omits `.memory/` — this is recorded as a known
residue, not a defect to fix inside this phase.

**Sampling continuity:** the phase is one commit, so the "no 3 consecutive tasks without automated
verify" rule is satisfied trivially — every deletion task is followed by V-1 and V-4 before staging.

---

## Wave 0 Requirements

**None — existing test infrastructure covers all phase requirements.**

This is a deletion phase with no new behavior to specify. The verifications that matter are one
absence-grep (not a pytest artifact) and five pre-existing gates, all of which already exist and
already pass on the current pre-deletion tree. The only structural change to the test tree is a
*removal* — `tools/skill_registry/tests/{conftest.py,test_skill_registry.py}` and
`tools/harness_lint/tests/test_skill_registry_lock.py` disappear with the code they exercise. That is
part of the deletion set, not a gap to fill.

**No new test may be added** (CONTEXT.md D-02, D-08 and the milestone's binding constraint). A test
asserting "the package is gone" would be new surface guarding against nothing.

---

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Test instructions |
|----------|-------------|------------|-------------------|
| The CI `gate` fan-in actually resolves after the `needs` edit | CER-04 | GitHub Actions validates the job graph at dispatch, not locally; a dangling `needs` entry is a workflow-level failure no local command reproduces | Push the branch and confirm the `gate` job starts (does not fail to resolve). This is the merge-time authority per ADR-0012 — it is expected to be the final proof, not a pre-merge blocker. |

---

## Validation Sign-Off

- [ ] V-1..V-9 all green
- [ ] Sampling continuity satisfied (single-commit phase)
- [ ] Wave 0 empty by design — confirmed, not skipped
- [ ] No watch-mode flags used
- [ ] No new test, tool, gate or CI job added (net surface change is deletion-only)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
