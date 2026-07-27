---
phase: 43
slug: lifecycle-plane-removal
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-28
---

# Phase 43 — Validation Strategy

> Per-phase validation contract. Derived from `43-RESEARCH.md` §"Validation Architecture".
> **Deletion-only, no new artifact.** Per CONTEXT.md **D-17** no mutation-proof / adversarial-input
> table is owed — this phase removes gates and adds no control. The one behavioral assertion that
> matters is D-11's: the activeContext pointer must SURVIVE the removal of the adjacent active-task
> block, and an existing test already covers it.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via `uv run pytest` (uv workspace; `testpaths = ["libs/python", "tools"]`) |
| **Config file** | root `pyproject.toml:37-39` |
| **Quick run command** | `uv run pytest --collect-only -q` — 0 errors proves no dangling import |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | quick ~5s · full ~50s |

---

## Sampling Rate

- **After every task commit:** `uv run pytest --collect-only -q`. For the largest deletion in the
  milestone the dangling-import class is the dominant failure mode, and collection catches it in
  seconds where the full suite takes a minute.
- **After every wave:** full `uv run pytest -q`.
- **Before `/gsd:verify-work`:** full suite green + `contract-drift` exit 0 + the YAML-resolved
  `gate.needs` assertion + `emit-drift` / `stale-derived` / ruff ratchet clean.
- **Ordering caveat (D-12):** gates run AFTER `git add` + `git commit -- <pathspec>`, never before —
  `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so tracked deletions red until
  staged and committed. A red before the commit is expected; amend if still red after.

---

## Per-Task Verification Map

| Task ID | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|-------------|-----------|-------------------|-------------|--------|
| (repair the 5 surviving artifacts) | 1 | CER-07 / D-01 | structural | `grep -rn "tools\.handoff\|tools\.evidence\|tools\.capability" harness/commands/ harness/agents/` → empty | ✅ | ⬜ pending |
| (memory_regen strip) | 1 | CER-07 / D-11 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py -q` (incl. `test_active_context_is_pointer_not_body`) | ✅ | ⬜ pending |
| (delete 8 packages) | 2 | CER-07 | collection | `uv run pytest --collect-only -q` exits 0, 0 errors | ✅ | ⬜ pending |
| (delete 6 contracts + rebaseline) | 2 | CER-07 / D-05 | gate | `uv run python -m tools.contract_drift.drift` exit 0; `test -f contracts/harness/task-control/gate-registry.json` | ✅ | ⬜ pending |
| (skills/commands/hook + re-emit) | 2 | CER-07 / D-06,D-07 | unit + gate | `uv run pytest tools/harness_lint tools/harness_emit tools/hooks -q` ; `python -m tools.harness_emit && git status --porcelain` empty | ✅ | ⬜ pending |
| (CI job + fan-in) | 2 | CER-07 / D-10 | structural, YAML-resolved | `uv run python -c "from ruamel.yaml import YAML; d=YAML(typ='safe').load(open('.github/workflows/ci.yml')); n=d['jobs']['gate']['needs']; assert 'lifecycle-eval' not in n and len(n)==10, n"` | ✅ | ⬜ pending |
| (uv.lock refresh) | 2 | CER-07 | gate | `uv sync --all-packages` resolves; 8 members gone from `uv.lock` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Structural absence sweep:**

```
grep -rnE "task_control|task_packet|risk_router|tools\.evidence|tools\.handoff|tools\.discipline|tools\.capability|lifecycle_eval" \
  tools/ harness/ contracts/ .github/ .claude/ .opencode/ AGENTS.md .memory/
```

Expected: **exit 1, no output**, `.planning/**` exempt. Note the hyphenated spelling too —
`task-control` does NOT match `task_control` (this bit Phase 42; five hyphenated provenance
docstrings survived both of its greps). Sweep both.

**What a botched removal looks like:**
- a surviving command still shelling a deleted module → the harness ships a command that crashes
  (five such artifacts already identified, five more found by research);
- a `conftest.py` importing a deleted package → collection error, not a test failure;
- `caps.py`'s `EXPECTED_SKILLS` not updated → the emitter hard-fails **before writing a byte**;
- `RETIRED_SIGNATURES` not used → the emitted hook group is treated as human-owned and survives forever;
- `DATA_CONTRACT_PATHS` dropping `gate-registry.json` → Phase 44's target vanishes early;
- the activeContext pointer removed along with the adjacent active-task block → SC-6 fails silently.

---

## Wave 0 Requirements

None — existing infrastructure covers every requirement. This phase deletes and edits; it adds no
test file, fixture, or framework.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The five repaired commands still read coherently as commands | CER-07 / D-03 | Whether `/checkpoint` or `/orient` still has a coherent job after its lifecycle step is removed is an editorial judgment, not an assertion | Read each repaired command end-to-end; confirm no dangling "then run X" referring to a removed step, and that the command's stated purpose still matches what it does |

---

## Validation Sign-Off

- [ ] Every task has an automated verify command (table above)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0: nothing owed
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s (collect-only) / < 60s (full)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
