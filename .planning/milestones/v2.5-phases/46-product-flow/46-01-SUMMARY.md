---
phase: 46-product-flow
plan: 01
subsystem: harness
tags: [orchestrator, routes, delegation-packet, completion-contract, contract-graph, harness-config, harness-emit, syrupy]

# Dependency graph
requires:
  - phase: 43-persona-consolidation
    provides: the persona set the retired routing table named, already reduced to python-engineer / code-reviewer / explorer + instance-declared engineers
  - phase: 44-command-consolidation
    provides: the 17-command live surface every route citation resolves against
  - phase: 45-projection-repair
    provides: the source-first emit discipline (D-17) and the in-commit `--snapshot-update` pattern
provides:
  - Four named product routes in `harness/agents/orchestrator.md` — small-change, bugfix, feature, contract-change
  - A six-field delegation packet and the six-field completion contract, authored as text with no vendored file dependency
  - Per-route Repository evidence blocks computed from live `harness_config` / `contract_graph` calls
  - Five `**Discipline:**` operative sentences replacing the five retired discipline skills (PROD-03)
affects: [46-02 flow command, 46-03 phase verification, v2.6 /impact]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Route sections carry a fixed five-subsection order (When to use / Steps / Repository evidence / Stop condition / Next command) so a weak model can pattern-match across routes"
    - "Repository evidence blocks state the question first, then the calls that answer it today, then an unbackticked forward reference — so a future one-command form drops in without a rewrite"
    - "Section-scoped awk+grep verification for differentiator predicates, because a whole-file grep passes on kept prose"

key-files:
  created: []
  modified:
    - harness/agents/orchestrator.md
    - .opencode/agent/orchestrator.md
    - .claude/agents/orchestrator.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr

key-decisions:
  - "Rewrote intake step 2 (`orchestrator.md:49`) — the plan's single sanctioned exception to the byte-identical KEEP — so the deployed persona's first routing instruction points at `## Routes` rather than at the deleted table"
  - "Kept all three tasks in one commit, as the plan's Task 3 pathspec specifies: a Task-1-only commit would carry `TODO(Task 2)` placeholders and un-emitted runtime trees, and would red emit-drift"
  - "Next command is defined in the Routes preamble as the one command to run when the route's steps are done, so each route ends with a single literal command rather than a menu"
  - "`contract-change` is driven by `transitive()` plus connecting paths, with the non-linear-graph rationale stated inline — the clause no repo-agnostic flow could contain"

patterns-established:
  - "Delegation packet (Objective / Starting context / Write scope / Repository evidence / Stop condition / Return format) is the harness's own six fields; the completion contract is the vendored six, copied as text"
  - "Every route's stop condition is a checkable halt with a named re-route target, never 'when done'"

requirements-completed: [PROD-02, PROD-03, PROD-05]

# Metrics
duration: 22min
completed: 2026-07-29
---

# Phase 46 Plan 01: Product Routes Summary

**The 19-row orchestrator routing table is retired for four named product routes — small-change, bugfix, feature, contract-change — each with a checkable stop condition, the six-field delegation packet, a Repository evidence block built from live `harness_config` / `contract_graph` calls, and one literal next command.**

## Performance

- **Duration:** ~22 min
- **Tasks:** 3
- **Files modified:** 4 (1 source, 2 emitted, 1 snapshot)
- **Commit:** `439b416`

## Accomplishments

- `harness/agents/orchestrator.md` grew **102 → 302 lines**; `grep -c '^|'` → **0** (no table survives).
- Four `## Route:` headings; `research` appears as no route heading (D-06).
- The six-field completion contract present verbatim and in order as six consecutive lines, matching `WORKFLOW_CONTRACTS.md:39-46` word for word — copied as **text**; no `@`-reference, import, or path citation of the vendored bundle appears in the file.
- Exactly **five** `**Discipline:**` sentences (PROD-03), one per route plus the cross-cutting red-before-green line in `## Routes`.
- The persona's self-declaration at `:45` — *"the only planner in the deployed harness"* — is now true rather than aspirational.

## Task Commits

All three tasks landed in **one** commit, which is what the plan's Task 3 pathspec specifies (see *Deviations*):

1. **Tasks 1–3** — `439b416` (feat): `feat(46): four product routes replace the orchestrator routing table (PROD-02, PROD-03, PROD-05)`

`git diff --shortstat HEAD~1 HEAD` → **4 files changed, 1154 insertions(+), 154 deletions(-)** — the first input to D-24's whole-phase LOC report.

`git diff --stat`:

```
 .claude/agents/orchestrator.md                     | 264 +++++++++--
 .opencode/agent/orchestrator.md                    | 264 +++++++++--
 harness/agents/orchestrator.md                     | 264 +++++++++--
 .../tests/__snapshots__/test_emit_determinism.ambr | 516 ++++++++++++++++++---
 4 files changed, 1154 insertions(+), 154 deletions(-)
```

The `.ambr` moves at ~2× the source because it renders the persona body into **both** projected trees.

## Files Created/Modified

- `harness/agents/orchestrator.md` — source persona; table retired, four routes + delegation packet + completion contract authored. 302 lines.
- `.opencode/agent/orchestrator.md` / `.claude/agents/orchestrator.md` — emitter projections (never hand-edited, D-17).
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — regenerated in the same commit via `--snapshot-update`.

## Measured Structure

Per-route structural confirmation (each count is 1 inside the `awk`-extracted `## Route:` section):

| Route | When to use | Steps | Repository evidence | Stop condition | Next command | Discipline |
|---|---|---|---|---|---|---|
| small-change | 1 | 1 | 1 | 1 | 1 | 1 |
| bugfix | 1 | 1 | 1 | 1 | 1 | 1 |
| feature | 1 | 1 | 1 | 1 | 1 | 1 |
| contract-change | 1 | 1 | 1 | 1 | 1 | 1 |

**Every one of the four routes carries an explicit stop condition and points at the shared `### Delegation packet`, which is present exactly once.** Whole-file totals: `## Route: ` = 4, `**Discipline:**` = 5, `Stop condition` = 6, `Repository evidence` = 6, `^|` = 0.

`Stop condition` and `Repository evidence` come to **6**, not the guard's `-ge 5` floor: four routes + the delegation-packet bullet + the `## Routes` preamble sentence that enumerates the five subsection names. The floor of 5 still holds and still fails on a stripped route, since the per-route presence loop runs alongside it.

Each route's *Next command*: small-change → `/verify-work`; bugfix → `/verify-work`; feature → `/checkpoint`; contract-change → `/verify-work`.

## Citations After the Rewrite

**Ten** backticked command citations, all resolving to `harness/commands/<name>.md`:

```
/add-language  /checkpoint  /contract-check  /fan-out-synthesize  /lint
/new-contract-rule  /orient  /review  /test  /verify-work
```

**Two** module citations, both resolving to a real package directory: `tools.harness_config`, `tools.contract_graph`. Ten + two = the twelve D-01 counts. `/flow` is not cited (it does not exist at this commit); no `python -m` form of either package appears.

### D-01 enumeration correction

D-01's *claim* — all citations in `orchestrator.md` resolve — **holds**, and is now asserted mechanically by the Task 2 loop rather than by eye. Its *enumeration* is one name loose: it lists `/component`, which is a live command (`harness/commands/component.md` exists) but was **not** actually cited in the file at plan time and is not cited after the rewrite either. The claim is correct; the list over-enumerates by one.

## Repository Evidence — what each route computes

- **small-change** — owner + toolchain + bash scope: `components()`, `languages()`, `language_bash_scopes()`.
- **bugfix** — owner plus reverse dependencies: `components()`, then `compile_graph()` → `reverse()`, so the failing test lands at the consuming boundary rather than inside the implementation.
- **feature** — declared pipeline shape and the edges the capability lands between: `pipeline()`, `components()`, `effective_relationships()`, `compile_graph()` → `direct()`.
- **contract-change** — the full affected set with connecting paths: `compile_graph()` → `direct()` / `reverse()` / `transitive()`, plus `effective_relationships()` for the declared edge and `components()` for the owning engineer on each side. The block states inline that `transitive()` and its paths are *read, not eyeballed*, because the compiled graph is not guaranteed linear and a branch/fan-in/cycle puts nodes in the affected set no single hop shows — the clause that makes this route non-repo-agnostic (D-07).

Every call above was **executed**, not just cited (D-21): all seven `harness_config` functions and all four `contract_graph` functions import and run at package level, and `direct` / `reverse` / `transitive` each returned `dict_keys(['ids', 'paths'])` as documented. The forward reference to v2.6's one-command form is **unbackticked prose** in all four blocks, so the citation loop stays green.

## Decisions Made

- Intake step 2 rewritten to `2. **Pick a route** (`## Routes` below) → exactly one of the four; the route names the command and the persona.` — the plan's fenced literal, applied verbatim. Steps 1 and 3–7 and the `:45` self-declaration are byte-identical.
- `Next command` semantics are stated once in the `## Routes` preamble ("the one literal command to run when the route's steps are done — never a menu") so a weak driver does not have to infer them per route.
- Route prose refers to "the instance registers in `project.toml`" / "the declared instance" and never uses the `examples/` token or any GEN-05 domain noun (D-19).

## Deviations from Plan

**One, and it is the plan's own instruction rather than a departure from it.**

**1. [Plan-literal] Three tasks, one commit**

- **Found during:** Task 1, resolving the executor's per-task commit protocol against the plan text.
- **Issue:** The default protocol commits after each task. The plan places its single commit in Task 3, with a pathspec covering all four files.
- **Resolution:** Followed the plan. A Task-1-only commit would have committed `TODO(Task 2)` placeholders and un-emitted runtime trees, redding the emit-drift replica — and the plan's standing rule is that every commit ends green. Tasks 1 and 2 were each verified against their own `<verify>` block before proceeding; only the commit was deferred.
- **Verification:** Task 1 verify block green (`grep -c '^|'` → 0, `harness_lint` 262 passed); Task 2 verify block green (`harness_lint` + `harness_config` + `contract_graph`, 323 passed); Task 3 verify block green post-commit.

**Total deviations:** 1 (commit granularity, plan-directed). No auto-fixes were required — no Rule 1/2/3 trigger fired.
**Impact on plan:** None. Zero packages installed, zero files added, zero tests added or removed — net +0 on every axis the phase constrains.

## Issues Encountered

**None.** Every one of the plan's six replay-established warnings held exactly as written:

1. The `:49` carve-out was real — `grep -c '^|'` is 0 and `table below` had no other occurrence, so leaving `:49` alone would have left step 2 pointing at nothing while every other predicate stayed green.
2. The section-scoped predicates were kept unsimplified. Confirmed the hazard is live: the kept intake prose at `:64` contains `transitive`, so a whole-file grep would indeed pass with `contract-change`'s evidence block deleted.
3. `contract-change` reads nothing like `small-change` — its order is fixed (contract entry → failing case → code → `/contract-check` → golden pair) and its stop condition is topology-specific.
4. `research` is present only as a one-sentence explicit non-route in the preamble, never as a `## Route:` heading.
5. No `python -m tools.harness_config` / `python -m tools.contract_graph` form was written; the v2.6 forward reference is unbackticked.
6. No `examples/` token and no GEN-05 domain noun entered the file — `test_core_no_example_dep.py` green on the first run.

Two mechanical notes, both anticipated by the plan:

- The `.ambr` snapshot moved, exactly as predicted, and was closed with `--snapshot-update` inside the same commit (1 snapshot updated).
- `AGENTS.md` and `CLAUDE.md` came back **unmodified** from the emitter, as the plan expected — the HARNESS-MANAGED block is a sorted name index and this plan changes no name. Neither needed to enter the pathspec.

**Nothing the plan did not anticipate.**

## Verification

| Check | Expected | Observed |
|---|---|---|
| `grep -c '^## Route: '` | 4 | **4** |
| `research` as a route heading | absent | **absent** |
| `grep -c '^\*\*Discipline:\*\*'` | 5 | **5** |
| `grep -q 'table below'` | no match | **no match** |
| intake step 2 matches `^2\. \*\*[^*]+\*\*.*Routes` | match | **match** |
| `grep -c '^\|'` | 0 | **0** |
| `Stop condition` / `Repository evidence` | ≥ 5 each, ≥ 1 per route | **6 / 6**, 1 per route |
| `transitive` inside `## Route: contract-change` | present | **present** |
| six-field contract, six consecutive lines in order | present | **present** |
| citation loop (10 commands, 2 modules) | exit 0 | **exit 0** |
| `uv run pytest -q` | 876 passed / 7 snapshots | **876 passed / 7 snapshots** |
| `uv run python -m tools.ruff_baseline` | at baseline | **74 findings (baseline 74), PASS** |
| emit-drift replica, post-commit | exit 0 | **exit 0** |
| `git status --porcelain` | empty | **empty** |

The pre-commit emit-drift false red the plan warns about was avoided by running the replica only after the commit, as instructed.

## Next Phase Readiness

- **ROADMAP SC1, SC2, SC3, SC4 and the PROD-05 half of SC7 are satisfied at `439b416`.** SC5, SC6, SC7's count half and SC8's whole-phase form remain with Plans 02 and 03.
- Plan 02 may now add `harness/commands/flow.md` (17 → 18). Note for it: this plan deliberately does **not** cite `/flow`, so Plan 02 owns wiring the entry point to these route names — and unlike this plan it adds a new file, so its pathspec needs `git add` and must carry `emit-manifest.json` (+2 rows) and `test_coexist.py`'s four count sites (D-14).
- No blockers. Working tree clean, suite green at 876.

---
*Phase: 46-product-flow*
*Completed: 2026-07-29*
