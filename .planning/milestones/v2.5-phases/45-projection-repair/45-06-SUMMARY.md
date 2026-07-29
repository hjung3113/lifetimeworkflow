---
phase: 45-projection-repair
plan: 06
wave: 5
subsystem: harness-record
tags: [projection-repair, ratchet, residuals, phase-close]
requires: ["45-03", "45-05"]
provides:
  - "corrected persona-template self-descriptions (no deleted-step claims, no `examples/` token)"
  - "a 43-VERIFICATION SC-1 must_have that can actually pass"
  - "a ruff ratchet floor equal to the live measured count"
  - "the phase's four residuals, in writing, with measured evidence"
affects: ["harness/agents/templates", "tools/ruff_baseline", ".planning/phases/43-lifecycle-plane-removal"]
tech-stack:
  added: []
  patterns:
    - "GEN-04 PHRASING RULE — name the instance-scoped golden CODEOWNERS route in words; never write the literal `examples/` token into `tools/`, `harness/` or `libs/`"
key-files:
  created:
    - .planning/phases/45-projection-repair/45-06-SUMMARY.md
  modified:
    - harness/agents/templates/component-engineer.md
    - harness/agents/templates/engineer.md
    - .planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md
    - tools/ruff_baseline/baseline.json
decisions:
  - "D-12 honored: component-engineer.md CORRECTED, not deleted — two live gates and an append-only ADR depend on it"
  - "Ratchet recorded at the LIVE measured 74, not the plan's predicted 79 and not the pre-phase 73"
  - "D-13, D-14, D-24 and the declined SC-1 CODEOWNERS clause recorded, deliberately not fixed"
metrics:
  duration: ~25m
  completed: 2026-07-29
  commits: 3
  core_suite: "876 passed / 7 snapshots"
  instance_suite: "31 passed"
  whole_phase_loc: "57 files changed, 300 insertions(+), 296 deletions(-)"
---

# Phase 45 Plan 06: Record Itself — Template Correction, Verification Wording, Ratchet, Residuals Summary

Corrected the two persona templates to describe only live steps (no `examples/` token, GEN-04 green),
restated `43-VERIFICATION.md`'s unsatisfiable SC-1 `must_have` in the executable-invocation form the
same record already carried, refreshed the ruff ratchet to the live measured 74, and put the phase's
four residuals in writing with their measured evidence.

## Commits

| # | Hash | Message | Files |
|---|------|---------|-------|
| 1 | `f2943cd` | `docs(45-06): correct the persona templates' self-descriptions` | `harness/agents/templates/component-engineer.md`, `harness/agents/templates/engineer.md` |
| 2 | `7e74a2f` | `docs(45-06): restate 43-VERIFICATION SC-1 in its executable-invocation form` | `.planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md` |
| 3 | `c8ae097` | `chore(45-06): refresh the ruff ratchet floor to the live measured count` | `tools/ruff_baseline/baseline.json` |

Every commit ended green on `uv run pytest -q`; commit 1 additionally ended green on the instance leg.

## Task 1 — persona templates CORRECTED, not deleted (D-12, D-06)

**Decision restated:** `harness/agents/templates/component-engineer.md` survives. Deleting it would
red `tools/harness_lint/tests/test_agent_templates.py:33` (`EXPECTED_TEMPLATES` exact-set assertion in
the CORE suite), break `examples/log-parser/tests/test_pipeline_topology.py:115`, and dangle
`docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md:95` — an accepted, append-only,
constitution-plane citation that cannot be repaired without a superseding ADR.

Three corrections in `component-engineer.md`:

- **`:6-11`** — the "`/component` instantiates a COPY of this file …" claim was replaced. Phase 44
  deleted that step. It now reads that a human or agent copies the file by hand into the instance's
  `agents/` directory and that `/component` no longer performs that copy. The WHY-it-lives-under-
  `templates/` explanation (the anti-sprawl gate globs `harness/agents/*.md` non-recursively) is
  preserved verbatim — it is still true and is load-bearing for `test_agent_templates.py`.
- **`:13-14`** — `<STAGE> (its ordinal in the [pipeline])` → `<STAGE> (its ordinal as declared by the
  instance's own pipeline declaration)`. The core `[pipeline]` table was deleted in Phase 44.
- **`:46`** — the `golden/` CODEOWNERS-entry pointer → **the instance-scoped golden CODEOWNERS route**.

`harness/agents/templates/engineer.md:39` — the identical pointer, repointed with the identical wording.

Front-matter `name`/`description` and every `<PLACEHOLDER>` token are untouched (the instance test
resolves against them).

**GEN-04 phrasing rule obeyed.** Both route sentences reuse the exact wording already live at
`harness/agents/python-engineer.md:29` and recorded in `45-01-SUMMARY.md:111` / `45-03-SUMMARY.md:85`:
`promotion is human review at the PR (the instance-scoped golden CODEOWNERS route).` No `examples/`
token was written into `harness/`. The dedicated guard leg
(`test_core_no_example_dep.py` + `test_cross_repo_authority.py`) ran green **before** the commit —
22 passed.

### Task 1 gate table

| Check | Command | Exit | Observed |
|-------|---------|------|----------|
| core suite | `uv run pytest -q` | 0 | 876 passed, 7 snapshots |
| **instance leg (D-20, mandatory)** | `uv run pytest examples/log-parser -q` | 0 | 31 passed |
| GEN-04 guards | `uv run pytest .../test_core_no_example_dep.py .../test_cross_repo_authority.py -q` | 0 | 22 passed |
| emitted trees untouched | `uv run python -m tools.harness_emit && git status --porcelain` | 0 | only the two edited templates dirty — 69 artifacts re-emitted byte-identical |
| stale-claim signature | `grep -n 'instantiates a COPY\|\[pipeline\]' component-engineer.md` | 1 | no output |
| route pointers repointed | `git grep -n '`golden/`' -- harness/agents/templates` | 1 | no output |

**Flagged for Phase 46, not done here:** re-wiring `/component` to restore the copy step is product
work, not projection repair.

## Task 2 — the unsatisfiable verification wording (D-15)

`43-VERIFICATION.md:8`, before:

```
  - must_have: "SC-1 — the ROADMAP's literal bare-token grep over tools/ harness/ contracts/ .github/ .claude/ .opencode/ returns nothing"
```

after:

```
  - must_have: 'SC-1 — the executable-invocation sweep `(python -m tools\.|from tools\.|import tools\.)` over the six product-surface paths tools/ harness/ contracts/ .github/ .claude/ .opencode/ returns zero real invocations of the deleted packages'
```

This is the form the same record already carries at `:16-17`. `reason`, `accepted_by` and
`accepted_at` are intact — the criterion is corrected, the override is not re-litigated. The scalar
was switched from double- to single-quoted YAML because `\.` is not a legal escape in a YAML
double-quoted scalar; the frontmatter was re-parsed with `yaml.safe_load` to confirm.

**`tools/contract_graph/tests/test_query.py` was NOT touched.** The four forbidden strings at
`:75-78` (`import tools.task_packet`, `import tools.evidence`, `import tools.task_control`,
`import tools.handoff`) are the negative control for the assertion above them; stripping them to
force a clean grep would delete the control. Phase 43's and Phase 44's executors each refused this
and both were right (D-05).

**D-15's ROADMAP half is confirmed MOOT.** Verified by running, not by assertion:
`ls .planning/milestones/` → `v2.0-*`, `v2.1-*`, `v2.3-*`, `v2.4-REQUIREMENTS.md` — **there is no
v2.5 milestone archive**. The live ROADMAP Phase 43 entry (`.planning/ROADMAP.md:227-233`) carries a
one-line `**Success:**` sentence and **no numbered success criteria**. There is nothing in the
ROADMAP to reword.

| Check | Command | Exit | Observed |
|-------|---------|------|----------|
| core suite | `uv run pytest -q` | 0 | 876 passed, 7 snapshots |
| corrected wording present | `grep -n 'python -m tools' 43-VERIFICATION.md` | 0 | hits at `:8` (the corrected must_have), `:16`, `:37` |
| negative control survives | `git grep -c 'task_control' test_query.py` | 0 | `1` matching **line**; `grep -o \| wc -l` → 1 occurrence — >0, control intact |

## Task 3 — the ratchet, run last (CER-10, D-23)

Run **before** update: `ruff ratchet: 74 findings (baseline 84)` → `improved E501: baseline 84 -> found 74`, PASS.

`uv run python -m tools.ruff_baseline --update` → `baseline updated: 74 findings across 1 rules`.

Post-update re-run: `ruff ratchet: 74 findings (baseline 74)` → `PASS: every rule class is at its
baseline.` **Zero delta.**

| | value |
|---|---|
| committed baseline before | 84 |
| pre-phase live count (at `6c41989`) | 73 |
| plan's predicted post-phase count | 79 |
| **measured and recorded** | **74** |

The plan predicted 79 and the pre-phase value was 73; the live measurement at phase close is **74**.
Per instruction the measured value was recorded, not checked against a prediction. The rise from 73
is expected (this phase's prose corrections lengthen lines) and the value stays under the old 84, so
CI was green throughout — what was fixed is a committed derived count that no longer described
reality (D-06), not a CI failure. The JSON was regenerated by the tool, never hand-edited.

## Phase gate — full table, observed exit codes

| Gate | Command | Exit | Observed |
|------|---------|------|----------|
| core suite | `uv run pytest -q` | **0** | 876 passed, 7 snapshots |
| instance suite | `uv run pytest examples/log-parser -q` | **0** | 31 passed |
| emit-drift | `uv run python -m tools.harness_emit` | **0** | 69 artifacts emitted |
| contract-drift | `uv run python -m tools.contract_hash.hash` | **0** | manifest reproduced |
| docs-sync | `uv run python -m tools.docs_sync.generate` | **0** | 6 reference pages regenerated |
| memory-regen | `uv run python -m tools.memory_regen.contracts_index` | **0** | 6 contracts indexed |
| **combined derived diff** | `git status --porcelain` after all four | **0** | **empty** |
| ruff ratchet | `uv run python -m tools.ruff_baseline` | **0** | 74 findings / baseline 74, zero delta |
| declaration sweep A | `git grep -n '"golden/\*\*"' -- tools harness .github` | **1** | no output |
| declaration sweep B | `python -c "assert CONSTITUTION_GLOBS == path_deny_globs == [contracts/**, docs/adr/**, docs/glossary.md]"` | **0** | `declarations OK` |
| declaration sweep C | `git grep -n '`golden/`\|`golden/\*\*`' -- harness .claude .opencode` | **1** | no output |
| `golden-approve` sweep | `git grep -n 'golden-approve' -- . ':!.planning/' ':!docs/adr/' ':!docs/references/' ':!examples/' ':!CLAUDE.md' ':!docs/glossary.md' ':!tools/harness_emit/tests/test_coexist.py' ':!tools/harness_lint/tests/test_commands.py'` | **1** | no output |

(exit 1 on a `git grep` sweep = no match = the required outcome.)

**No derived generator dirtied the tree.** No CER-10 finding at phase close.

### D-23 — whole-phase LOC

The user-specified measurement, excluding the tracked `.planning/` plane:

```
git diff --shortstat 2360808..HEAD -- . ':(exclude).planning'
 57 files changed, 300 insertions(+), 296 deletions(-)
```

Net **+4 lines** across the code/doc planes over the phase's 17 commits — a wash, as expected for a
phase that corrects and deletes prose rather than removing machinery. For completeness:
`2360808..HEAD` whole-tree (i.e. including `.planning/`) is `63 files changed, 1368 insertions(+),
297 deletions(-)`; the plan's stated base `354dbdf..HEAD` is `69 files changed, 3157 insertions(+),
297 deletions(-)` — both dominated by `.planning/` plan and summary documents, which is why the
figure is reported from the code/doc paths.

ROADMAP SC-8 holds: **net +0 gates, tools, contracts, dependencies.** No package-manager install ran
anywhere in Phase 45; `uv.lock` is untouched by all six plans.

---

# The four residuals (this is the deliverable)

## (a) D-14 — TWO accepted ADRs cite documents this milestone made stale

**ADR-0008** (`docs/adr/0008-task-control-plane-lifecycle.md`):
- `:50` — *"Design authority: `docs/explanation/next-milestone-task-control-plane.md` §Phase 6."*
  The target **survives** (plan 45-05 deliberately retained it precisely because an append-only ADR
  cites it, and gave it a HISTORICAL header at commit `7d61983`) — so the citation resolves, but it
  now points at a document explicitly marked historical.
- `:52` — *"Runtime-neutral implementation: `tools/task_packet/`, `tools/risk_router/`,
  `tools/task_control/`, `tools/evidence/`, and `tools/handoff/`."* **All five packages were deleted
  in Phase 43.** This citation genuinely dangles.
- Header `:5` still reads **`Status: Accepted`** and `:9` **`Superseded by: —`**, while Phase 43
  deleted the entire plane the ADR decides.

**ADR-0003** (`docs/adr/0003-pipeline-topology-slot-and-instance-overlay.md`):
- `:95` — *"Per-component engineers are instantiated from a neutral, anti-sprawl-exempt
  `harness/agents/templates/component-engineer.md` template into the instance's own `agents/`."*
  Phase 44 removed `/component`'s copy step. **This defect had never been named before Phase 45.**
  It is precisely why the template was corrected rather than deleted (D-12): deleting the file would
  make an append-only citation permanently uncorrectable.

**Both need a human-authored superseding ADR. Neither was authored here** — the constitution plane is
append-only and human-owned; an executor writing an ADR would be the exact self-blessing the harness
forbids.

## (b) D-13 — the core suite's coupling to the reference instance, at its MEASURED extent

`git rm -r examples/` reds **SIX tests across FOUR modules**:

1. `tools/adoption_scan/tests/test_install_completeness.py::test_every_ci_pytest_path_argument_resolves`
2. `tools/contract_graph/tests/test_cross_repo_authority.py::test_reference_instance_config_is_untouched`
3. `tools/harness_config/tests/test_loader.py::test_persona_files_exist_on_disk`
4. `tools/harness_config/tests/test_topology_relationships.py::test_instance_config_needs_no_explicit_records`
5. `tools/harness_lint/tests/test_language_config.py::test_each_configured_persona_exists`
6. `tools/harness_lint/tests/test_language_config.py::test_each_configured_language_has_test_paths`

— **not** the single test CONTEXT D-13 names, and that test is not even at the path CONTEXT gives:
`tools/harness_lint/tests/test_ci_paths.py` **does not exist** (re-confirmed absent at phase close).

**DECISION: defer whole, do not partially fix.** Four of the six fail because `harness/project.toml`'s
`[instance]` slot points at the reference instance — which is precisely ADR-0002's design: *the
instance is DATA in a slot*. Fixing only the accidental `ci.yml` coupling would manufacture a false
claim that the core is instance-independent while five real couplings remain. Making the slot
optional is a design change, not projection repair.

*(The 6-test extent is carried forward from the phase's research measurement; it was not re-measured
at close, because re-measuring requires deleting `examples/` — a destructive git operation outside
this plan's mandate.)*

### The GEN-04 guard is TWO-SIDED — both halves bit this phase

- **It cannot see half of (b).** `_CORE_ROOTS = ("tools", "harness", "libs")`
  (`test_core_no_example_dep.py:44`) scans neither `pyproject.toml` nor `.github/`, so the guard is
  structurally blind to both the CI-path coupling and the workspace coupling above.
- **It scans every prose line in those three trees in full** — which is exactly the trees plans 01,
  03 and 06 rewrite prose in. The replay measured **five core-plane sentences RED-ing the guard
  (2 failed / 872)** because they named the literal instance golden path. That is why plans 01, 03
  and 06 each carry a GEN-04 PHRASING RULE.

**Record the rule as a standing convention, not a one-off workaround:** any sentence written into
`tools/`, `harness/` or `libs/` that needs to refer to the instance golden route must name it in
words — *"the instance-scoped golden CODEOWNERS route"* — and must never contain the literal
`examples/` token.

## (c) D-24 — CODEOWNERS is advisory; the remedy is a repo setting no file here can perform

D-01 removed the last **in-session** control on golden self-blessing. Re-probed at phase close (not
restated from research):

```
gh api repos/hjung3113/lifetimeworkflow/branches/main/protection
```

- `required_status_checks`: `{"strict": true, "contexts": ["gate"]}`
- **`required_pull_request_reviews`: the key is ABSENT ENTIRELY** — "Require review from Code Owners"
  is OFF, and so is "Require a pull request before merging"
- `enforce_admins.enabled`: **`false`**
- `required_signatures`: false · `required_linear_history`: false · `required_conversation_resolution`: false

So `.github/CODEOWNERS:36` (`/examples/*/golden/ @hjung3113`) auto-requests the owner as a reviewer
**without being able to block the merge** — exactly as `.github/CODEOWNERS:9-16` warns in its own
ENFORCEMENT CAVEAT block. The required `gate` check does **not** close this: CI validates against
whatever baseline is committed, so a mutated `baseline.verified.tsv` makes CI green.

**One-toggle remedy for the owner, to be surfaced at the milestone-close PR:**

```
gh api -X PUT repos/hjung3113/lifetimeworkflow/branches/main/protection/required_pull_request_reviews \
  -f require_code_owner_reviews=true
```

**Solo-repo caveat, already documented at `.github/CODEOWNERS:18-23`:** GitHub does not let an author
approve their own PR. With `@hjung3113` as both sole code owner and author of most PRs, the
requirement cannot be satisfied by self-review — it needs a second account with access, or an
admin waiver per merge. That is a user-controlled workflow choice, not a defect.

Per D-03 and D-24, **no in-session control was added to compensate.** That is the surface growth the
v2.5 milestone constraint forbids.

## (d) SC-1's CODEOWNERS clause — DECLINED in plan 02, with the reason

Carried forward here so the phase's own verification does not read it as an unexplained miss.
Plan 02 declined to add a CODEOWNERS-shaped assertion (recorded at commit `84ef919`,
`docs(45-02): record the SC-1 glob-liveness assertions and the declined CODEOWNERS clause`). The
reason: CODEOWNERS routing is a **merge-time, repo-settings** authority (ADR-0012), and a new
in-session test asserting it would be net surface growth that also could not observe the setting that
actually decides the outcome — see (c). What plan 02 built instead is the mechanical, satisfiable
half: `test_agents.py:243` and `tools/hooks/tests/test_contract_guard.py:419` each assert that no
declared path glob matches **zero** git-tracked files ("a deny glob with no subject is a dead
control"). That is the liveness property SC-1 was reaching for, expressed in something the suite can
actually see.

---

# Additional residuals recorded this wave (NOT fixed — for owner decision)

These are outside plan 45-06's four, but were measured during waves 1–5 and belong in the phase-close
record.

| # | Location | What is stale | Why it was left |
|---|----------|---------------|-----------------|
| R-1 | `tools/hooks/contract_guard.py:40-41` | *"Deliberately EXCLUDES `*.env`, which is outside this gate's domain (W-1)"* — references the secret surface Phase 44 removed | The sentence is a scoping note, not a claim about a live module; correcting it is prose churn against a code file at phase close |
| R-2 | `harness/permission-matrix.json` `_note` | *"…in Phase 4, by the contract-guard / secret hooks that import that resolver verbatim"* — the secret hook is gone | Same; 1 occurrence, measured with `grep -o \| wc -l` |
| R-3 | `README.md:12` (badge), `README.md:107`, `README.ko.md:60` | advertise a **982-test** suite; the actual core suite is **876** | **D-06 scopes staleness to deleted modules, commands and paths — not to counts.** Correctly left by plan 04, but the numbers are wrong and need an owner decision (a badge is a derived count with no generator) |
| R-4 | `docs/glossary.md:20` and `:23` | plan 45-05 task 3 resolved to `defer-to-pr`; two line replacements pending, quoted verbatim in `45-05-SUMMARY.md:159-181` | Constitution plane — deferred to the milestone-close PR under a human's hand. `:13`, `:19`, `:21` must NOT be touched. The plan's claimed third defect at `:19` **does not exist** (measured: one `/golden-approve` occurrence, on `:20` only) |

R-4 is why this plan's `golden-approve` sweep carries the `':!docs/glossary.md'` exclusion. If the
owner ratifies the glossary edits at the PR, drop that exclusion and require zero hits there too.

---

# Things that did not hold as the plan predicted

| Plan's expectation | Observed | Action |
|---|---|---|
| ratchet lands at **79** | **74** | Recorded the measurement. Per instruction the value is measured, not checked against a prediction. It is above the pre-phase 73 (expected) and below the old 84 (CI green throughout). |
| `docs/how-to/approve-a-golden.md` exists (CONTEXT D-10, ROADMAP) | **ABSENT** — deleted before this phase | Nothing to do; both records are stale about it. |
| `harness/skills/golden-testing/`, `harness/skills/golden-debug/` (DO-NOT-TOUCH list + one pathspec) | **ABSENT** — Phase 44 deleted them | Nothing to touch; not a blocker. |
| `.github/CODEOWNERS` has 4 route lines (a wave-1 verify comment) | **5** route lines (`:30-32`, `:35-36`) | 5 is the intended state — the two surviving instance routes were collapsed into one bullet while both survive. |
| `AGENTS.md` emitter-managed block at `:100-109` | `:101-110` | Shifted one line in wave 3b. |
| wave-2 assertions at `test_agents.py:233` / `test_contract_guard.py:412` | `test_agents.py:243` / `tools/hooks/tests/test_contract_guard.py:419` | Offset by docstrings the plan itself mandated. The contract-guard test lives under `tools/hooks/tests/`, not `tools/harness_lint/tests/`. |
| `git grep -c` counts occurrences | it counts matching **LINES** | Every count in this record that matters was re-measured with `grep -o \| wc -l`. |
| `tools/harness_lint/tests/test_ci_paths.py` (CONTEXT D-13's cited path) | **does not exist** | Confirms the D-13 record above. |

Nothing in this list was "absorbed": each was recorded rather than adjusted, and no plan text, test or
source file was edited to make a stale prediction come true.

---

# Complete deferral list for the milestone-close PR

1. **Human-authored superseding ADR** covering ADR-0008 (status still `Accepted`, `Superseded by: —`;
   `:52` cites five deleted `tools/` packages) **and** ADR-0003 (`:95` describes `/component` copying
   the template). — residual (a)
2. **D-13 core→instance coupling** — 6 tests / 4 modules; a design decision about whether
   `harness/project.toml`'s `[instance]` slot becomes optional. Not projection repair. — residual (b)
3. **Branch protection toggle** —
   `gh api -X PUT repos/hjung3113/lifetimeworkflow/branches/main/protection/required_pull_request_reviews -f require_code_owner_reviews=true`
   (plus the solo-repo second-reviewer caveat). — residual (c)
4. **`docs/glossary.md:20` and `:23`** — two line replacements, quoted verbatim in
   `45-05-SUMMARY.md:159-181`, under a human's hand on the constitution plane. — R-4
5. **README test-count staleness** — `README.md:12`, `README.md:107`, `README.ko.md:60` say 982; the
   suite is 876. Owner decision: correct the numbers, or generate the badge. — R-3
6. **`contract_guard.py:40-41` and `harness/permission-matrix.json` `_note`** — both still reference
   the removed secret surface. — R-1, R-2
7. **Phase 46: re-wire `/component`** to restore the template copy step, or ratify by ADR that the
   copy is permanently manual. — flagged in Task 1
8. **ROADMAP SC-1's implied CI-green half** (inherited from Phase 43's deferral) — CI triggers on
   `pull_request:` only, so it can only go green at the milestone PR.
9. **GEN-04 PHRASING RULE as a standing convention** — record it where future phase planners will see
   it, not only in three plan bodies. — residual (b)

---

## Success criteria

- [x] Both persona templates describe only live steps; neither deleted; neither carries an `examples/` token
- [x] `43-VERIFICATION.md:8` states a criterion that can pass
- [x] The ratchet floor equals the live measured count (74) with zero delta
- [x] All four residuals written down with their measured evidence
- [x] ROADMAP SC-7: `emit-drift`, `stale-derived`, `contract-drift` and the ruff ratchet all green with an empty diff; `uv run pytest -q` green at every commit of the phase
- [x] ROADMAP SC-8: net +0 gates, tools, contracts, dependencies

## Self-Check: PASSED

- `harness/agents/templates/component-engineer.md` — FOUND
- `harness/agents/templates/engineer.md` — FOUND
- `.planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md` — FOUND
- `tools/ruff_baseline/baseline.json` — FOUND, `"total": 74`
- commit `f2943cd` — FOUND
- commit `7e74a2f` — FOUND
- commit `c8ae097` — FOUND
