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
- **Every commit in this phase ends green.** There is no sanctioned expected-red window and no
  standing list of tolerated failures. Executors are instructed to amend-if-red, so a red must always
  mean a real defect. The one narrow exception is mechanical and never spans a commit: per **D-12**,
  `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so a deletion reads as still-tracked
  in the window BETWEEN `git rm` and `git commit`. Gates therefore run AFTER `git add` +
  `git commit -- <pathspec>`, never before; if still red after the commit, amend.
- **Hardcoded live-tree expectations are repaired in the SAME commit as the change that invalidates
  them.** This is what keeps every commit green, and it decides which plan owns each repair: the
  owner is the plan that makes the invalidating change, not the plan that happens to touch the same
  file. Worked example — `test_settings_coexist.py` carries two literals this phase invalidates.
  `_NEW_GATES` is fixture data, so Plan 43-02 drops its `resume_gate` tuple (verified green on its
  own: `4 passed` with `.claude/settings.json` untouched). `test_expected_slot_counts` reads the live
  emitter-owned `.claude/settings.json`, which only the emitter may change (D-14) — so its `== 8` →
  `== 7` correction belongs to Plan 43-03 Task 1, in the same commit as the emitter run that drops
  the 8th PreToolUse group.
- **`--collect-only` is NOT sufficient on its own for this phase.** Four of the literals this phase
  invalidates are RUNTIME assertions over the live tree, invisible to collection:
  `test_settings_coexist.py::test_expected_slot_counts` (PreToolUse slot count, repaired in 43-03),
  `test_tests_are_isolatable.py` (`tools/lifecycle_eval/tests` literal, repaired in 43-04),
  `test_install_completeness.py` (`>= 20` module-discovery floor, repaired in 43-04), and
  `test_hash.py` (`DATA_CONTRACT_PATHS` expected set, repaired in 43-05). Each wave closes on a FULL
  `uv run pytest -q`.

---

## Per-Task Verification Map

| Task ID | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|-------------|-----------|-------------------|-------------|--------|
| (repair the 5 surviving artifacts) | 1 | CER-07 / D-01 | structural | `grep -rn "tools\.handoff\|tools\.evidence\|tools\.capability" harness/commands/{checkpoint,orient,review,verify-work}.md harness/agents/orchestrator.md` → empty | ✅ | ⬜ pending |
| (the 5 artifacts' own gate tests still pass — W-1) | 1 | CER-07 / D-01, D-15 | unit, live-tree | `uv run pytest tools/harness_lint/tests/test_orchestrator_topology.py tools/harness_lint/tests/test_context_budget_wiring.py tools/memory_regen/tests/test_checkpoint_command.py -q` | ✅ | ⬜ pending |
| (memory_regen strip) | 1 | CER-07 / D-11 | unit | `uv run pytest tools/memory_regen/tests/test_inject_assembler.py -q` (incl. `test_active_context_is_pointer_not_body`) | ✅ | ⬜ pending |
| (hook-signature retirement, `_NEW_GATES` only) | 1 | CER-07 / D-06 | unit | `uv run pytest tools/harness_emit/tests/test_coexist.py tools/hooks/tests/test_settings_coexist.py -q` → green with `.claude/settings.json` untouched | ✅ | ⬜ pending |
| (re-emit + PreToolUse 8→7 + slot-count literal, one commit — B-1) | 2 | CER-07 / D-06, D-14 | gate + unit | `uv run python -c "import json; h=json.load(open('.claude/settings.json'))['hooks']; assert len(h['PreToolUse'])==7 and len(h['PostToolUse'])==4"` ; `uv run pytest tools/hooks/tests/test_settings_coexist.py -q` ; `git log -1 --name-status` shows both files | ✅ | ⬜ pending |
| (delete 8 packages) | 3 | CER-07 | collection + full | `uv run pytest --collect-only -q` exits 0, 0 errors; then `uv run pytest -q` exits 0 | ✅ | ⬜ pending |
| (module-discovery floor — B-2) | 3 | CER-07 | unit, live-tree | `uv run pytest tools/adoption_scan/tests/test_install_completeness.py tools/adoption_scan/tests/test_dispositions.py -q` | ✅ | ⬜ pending |
| (skills/commands/hook + re-emit) | 3 | CER-07 / D-06,D-07 | unit + gate | `uv run pytest tools/harness_lint tools/harness_emit tools/hooks -q` ; `python -m tools.harness_emit && git status --porcelain` empty | ✅ | ⬜ pending |
| (delete 6 contracts + rebaseline) | 4 | CER-07 / D-05 | gate | `uv run python -m tools.contract_drift.drift` exit 0; `test -f contracts/harness/task-control/gate-registry.json` | ✅ | ⬜ pending |
| (contract_hash expected set — B-3) | 4 | CER-07 / D-05 | unit | `uv run pytest tools/contract_hash/tests/test_hash.py -q` | ✅ | ⬜ pending |
| (CI job + fan-in) | 4 | CER-07 / D-10 | structural, YAML-resolved | `uv run python -c "from ruamel.yaml import YAML; d=YAML(typ='safe').load(open('.github/workflows/ci.yml')); n=d['jobs']['gate']['needs']; assert 'lifecycle-eval' not in n and len(n)==10, n"` | ✅ | ⬜ pending |
| (README sweep — B-5) | 4 | CER-07 / D-01 | structural | the structural-absence sweep below, run over `README.md README.ko.md` | ✅ | ⬜ pending |
| (uv.lock refresh) | 4 | CER-07 | gate | `uv sync --all-packages` resolves; 8 members gone from `uv.lock` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Structural absence sweep (extended per W-3/W-4/B-5):**

```
grep -rnE "task_control|task_packet|risk_router|tools\.evidence|tools\.handoff|tools\.discipline|tools\.capability|lifecycle_eval|lifecycle-eval|capabilities\.toml|disciplines\.toml|risk-policy\.toml|\.workflow/tasks|/intake|/phase-gate|/handoff|/discipline|adversarial-review-panel|test-driven-change|domain-modeling|\bclarify\b|\bdiagnose\b" \
  tools/ harness/ contracts/ .github/ .claude/ .opencode/ AGENTS.md .memory/ README.md README.ko.md
```

Expected: **exit 1, no output**, `.planning/**` exempt. Three deliberate extensions over the
previous revision:

1. **Hyphenated spellings.** `task-control` does NOT match `task_control`, and
   `risk-policy.toml` / `capabilities.toml` / `disciplines.toml` match no underscore pattern at all.
   This bit Phase 42 (five hyphenated provenance docstrings survived both of its greps) and it bit
   this phase too: `tools/adoption_scan/destinations.py:158`'s `"harness/risk-policy.toml"` glob and
   `tools/harness_lint/caps.py:129,133`'s comment block were invisible to every earlier sweep.
2. **The 4 command slugs and 5 skill slugs** deleted in Wave 3 — a surviving `/phase-gate` or
   `adversarial-review-panel` reference is a broken instruction even though it names no module.
   `\bclarify\b` / `\bdiagnose\b` are word-bounded because both are ordinary English words; expect to
   review those matches by hand rather than requiring zero blindly.
3. **`README.md` and `README.ko.md` are now IN the path list.** They were in neither this list nor
   ROADMAP SC-1's, which is precisely how `README.md:131`'s
   `uv run python -m tools.lifecycle_eval.runner` instruction and the hardcoded `lifecycle-eval`
   fan-in list survived two review rounds. Plan 43-05 Task 2 sweeps them; this list keeps future
   phases from re-losing them. `/pipeline` must still be present in `README.md` — it is Phase 44's to
   remove, not this phase's.

**What a botched removal looks like:**
- a surviving command still shelling a deleted module → the harness ships a command that crashes
  (five such artifacts already identified, five more found by research);
- a surviving README still telling a reader to run a deleted module → the same failure class, one
  layer out, with no gate above it until this revision (B-5);
- a `conftest.py` importing a deleted package → collection error, not a test failure;
- `caps.py`'s `EXPECTED_SKILLS` not updated → the emitter hard-fails **before writing a byte**;
- `RETIRED_SIGNATURES` not used → the emitted hook group is treated as human-owned and survives forever;
- `DATA_CONTRACT_PATHS` dropping `gate-registry.json` → Phase 44's target vanishes early;
- a hardcoded live-tree count/literal (`== 8` PreToolUse, `>= 20` modules, `== 25` commands, the
  `transitions.json` expected set, a committed `.ambr`) repaired in a DIFFERENT commit from the change
  that invalidated it → a RUNTIME red that `--collect-only` cannot see, spanning a plan boundary and
  teaching executors to tolerate reds;
- the activeContext pointer removed along with the adjacent active-task block → SC-6 fails silently;
- an over-broad harness edit deleting a literal a live gate test asserts (`/pipeline`,
  `context-budget`, `fan-out`, "git holds the full completed history") → W-1's failure class.

---

## Wave 0 Requirements

None — existing infrastructure covers every requirement. This phase deletes and edits; it adds no
test file, fixture, or framework.

---

## Deferred / carry-forward (NOT this phase's scope)

| Item | Evidence (live-verified 2026-07-28) | Why deferred | Owner |
|------|--------------------------------------|--------------|-------|
| Three human-owned Diátaxis docs survive describing the removed plane in stale prose: `docs/how-to/task-lifecycle.md` (106 lines, 11 dying-surface references), `docs/explanation/next-milestone-task-control-plane.md` (504 lines, 19 references), `docs/explanation/task-lifecycle-shadow-metrics.md` (13 lines, framed on the same plane) | `grep -cE "task_control\|risk_router\|lifecycle_eval\|tools\.handoff\|tools\.evidence\|tools\.capability\|/phase-gate\|/intake\|/handoff\|\.workflow/tasks"` over each file. **Note:** the originally-reported broken-link failure mode does NOT exist — these three carry no markdown link into `docs/reference/{task,state,evidence,handoff,attestation}.md`. The residue is stale prose, not dangling links. | No link checker or docs-prose gate exists, and `docs/` is outside every structural sweep, so this lands silently either way. Rewriting human-owned Diátaxis prose is not a deletion-phase concern and would push Phase 43 past its context budget. `docs/` is deliberately NOT added to the sweep above, because doing so would make the sweep red for a condition this phase is not chartered to fix. | **Phase 45 (projection repair)** |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The five repaired commands still read coherently as commands | CER-07 / D-03 | Whether `/checkpoint` or `/orient` still has a coherent job after its lifecycle step is removed is an editorial judgment, not an assertion | Read each repaired command end-to-end; confirm no dangling "then run X" referring to a removed step, and that the command's stated purpose still matches what it does |
| Both READMEs still read coherently after the B-5 sweep | CER-07 / D-01 | Whether the feature table, command tour, and milestone-history blocks still make sense as prose after five deletions is editorial, not assertable | Read `README.md` and `README.ko.md` top to bottom; confirm no orphan heading, no "위 6개 phase"-style back-reference to a deleted section, no numbered quickstart gap, and that the v2.2 milestone entry reads as an accurate shipped-then-removed record rather than a falsified history |

---

## Validation Sign-Off

- [ ] Every task has an automated verify command (table above)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0: nothing owed
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s (collect-only) / < 60s (full)
- [ ] `nyquist_compliant: true` set in frontmatter
- [ ] Every commit in the phase ends green — no sanctioned expected-red window, no standing list of
      tolerated failures; every hardcoded live-tree expectation is repaired in the same commit as the
      change that invalidates it
- [ ] `README*.md` is in the structural-absence path list

**Approval:** pending
