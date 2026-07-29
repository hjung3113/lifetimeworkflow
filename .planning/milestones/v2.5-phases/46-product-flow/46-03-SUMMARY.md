---
phase: 46-product-flow
plan: 03
subsystem: memory
tags: [activeContext, checkpoint, orient, round-trip, phase-verification, PROD-02, PROD-03, PROD-04, PROD-05, D-10, D-23, D-24]

# Dependency graph
requires:
  - phase: 46-product-flow
    plan: 01
    provides: the four `## Route:` sections whose structure SC1–SC4 and SC7 re-assert at the phase tip
  - phase: 46-product-flow
    plan: 02
    provides: "`harness/commands/flow.md` — the 18-command surface SC5 counts and the `+1 command` half of SC8"
provides:
  - "Route / step / next command recorded in `.memory/state/activeContext.md` by the existing `/checkpoint` writer and surfaced by the existing `/orient` reader — the D-10 round-trip demonstrated by a run"
  - The eight-criterion verification record for Phase 46, every line a recorded command output
  - The measured whole-phase LOC (D-24) and the net-surface proof (+1 command, +0 everything else)
affects: [v2.5 milestone-close PR]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The stale-derived replica is only non-vacuous with `tools.docs_sync` included: `docs_sync` is the sole regenerator of `docs/reference`, so diffing that tree after running only the `memory_regen` commands diffs a tree nobody regenerated"
    - "The instance leg must be `uv run pytest examples/log-parser -q` (31 = 14 `tests` + 17 `golden_runner`); scoping to `examples/log-parser/tests` measures 14 and silently skips the .NET golden-parity leg while still looking like a pass"

key-files:
  created:
    - .planning/phases/46-product-flow/46-03-SUMMARY.md
  modified:
    - .memory/state/activeContext.md
    - .memory/state/progress.md

key-decisions:
  - "The round-trip is recorded as writer → pointer → agent reads the file. `/orient`'s injector emits a POINTER to `activeContext.md` and never its body — verified by grepping the payload for `Route:` (0 hits). No inlined body is claimed."
  - "`.memory/derived/contracts-index.md` did not move under regeneration, so the commit pathspec is the two state files only — the plan's conditional handling resolved to 'exclude'."
  - "No mutation-proof table is owed (D-23): this phase adds prose and one command and adds no control, so there is no gate whose bypass could be demonstrated."

requirements-completed: [PROD-02, PROD-03, PROD-04, PROD-05]

# Metrics
duration: ~20min
completed: 2026-07-29
commits: 1
tasks: 2
---

# Phase 46 Plan 03: State Round-Trip and Phase Verification Summary

**Route, step and next command now round-trip through `.memory/state/activeContext.md` via the
already-shipped `/checkpoint` writer and `/orient` reader — demonstrated by a run, not asserted from
a read — and all eight ROADMAP success criteria are green with a recorded command output each.**

## Task 1 — the D-10 round-trip, demonstrated

Commit **`bbf5f2f`** — `chore(46): record the route/step/next state round-trip in the shipped state
plane`, 2 files changed, +31/−15.

The stale v2.1-era body (it still described the MEM2 milestone and pointed at `/gsd:plan-phase 12`,
`updated: "2026-07-16"`) was replaced with the live v2.5 position, and `progress.md` was rewritten
under the same writer contract — `## Recently done (last 5)` bounded at five entries, older ones
**dropped, not appended**, plus `## Remaining`.

**Written** (`activeContext.md:14-16`, under `## In flight`, exactly the shape `/flow` §2 prescribes):

```text
- Route: small-change
- Step: 3 of 3 — make the edit and run `/lint`
- Next command: /verify-work
```

Truthful against the route's own definition: `## Route: small-change` has three steps, step 3 is
"the engineer makes the edit and runs `/lint`", and its **Next command** is `/verify-work`.

**Surfaced** — `uv run python -m tools.memory_regen.inject`, line 39 of a 39-line payload, under the
heading `## Progress log (pointer)`:

```text
.memory/state/activeContext.md — session progress log; git holds the full completed history. On a data conflict, contracts/ADR win. [updated: 2026-07-29]
```

**Read back** — `grep -n '^- Route: \|^- Step: \|^- Next command: '` returns the three lines at
`:14`, `:15`, `:16`.

### The round-trip is pointer-then-read, and is worded down to that

`inject` emits a **pointer** naming the file; it never inlines the body. Both `orient.md` and the
file's own DATA AUTHORITY banner say so, and it is measured here: `grep -c 'Route:'` over the inject
payload is **0**. The chain is therefore **existing writer (`/checkpoint`) → existing reader
(`/orient`) emits a pointer → the agent opens the file the pointer names and reads the three lines**.
No inlined body is claimed. The pointer does carry the freshly-written `[updated: 2026-07-29]`, which
is the observable evidence the reader saw the writer's output.

**Nothing was created.** `.flow/` does not exist (`[ ! -e .flow ]` → true). Across the entire phase
range the only non-`.planning` additions are `harness/commands/flow.md` and its two emitter
projections — no new state file, no new writer, no new reader, no schema for these three fields.

`.memory/derived/contracts-index.md` did **not** move under regeneration, so the plan's conditional
pathspec resolved to excluding it; the commit names the two state files only.

## Task 2 — the eight-criterion verification record

Every row below is a command that was run. Exit codes are literal.

| SC | Criterion | Command | Observed | Exit |
|----|-----------|---------|----------|------|
| **1** | Four route sections, each with an explicit stop condition and the delegation-packet fields | `grep -c '^## Route: ' harness/agents/orchestrator.md`; per-route `awk`-scoped section grep | **4** (`:116` small-change, `:157` bugfix, `:199` feature, `:246` contract-change); each section: Stop condition **1**, Repository evidence **1**, Next command **1**, packet reference **1** (contract-change **2**); `### Delegation packet` defined exactly **once** with its six fields | 0 |
| **2** | Six-field completion contract verbatim; `research` appears as no route | fixed-string containment of the six lines in order vs `WORKFLOW_CONTRACTS.md:39-46`; `grep -c '^## Route: research'` | Six-line block present **verbatim and in order** at `:107-114` under `### Completion contract`; `research` as a route heading → **0** | 0 |
| **3** | The 19-row table gone; every cited command/module resolves, asserted mechanically | `grep -c '^## Routing decision table'`; `grep -c '^\|'`; citation loop | Table heading **0**; pipe-prefixed rows **0**; **10** command citations + **2** module citations, **unresolved: []** | 0 |
| **4** | Each of the five retired discipline skills leaves one operative sentence | `grep -c '^\*\*Discipline:\*\*' harness/agents/orchestrator.md` | **5** — `:87` red-before-green (cross-cutting), `:129` small-change, `:173` bugfix, `:219` feature, `:272` contract-change | 0 |
| **5** | `flow.md` exists and is the only command added; command count 18 | `ls harness/commands/*.md \| wc -l` | **18** | 0 |
| **6** | Route · step · next round-trip via the existing `/checkpoint` → `/orient` pair; no new state file, writer or reader | Task 1 in full (write → `inject` → read back); `[ ! -e .flow ]`; whole-range `A`/`D` scan | Three lines written, pointer surfaced, fields read back; `.flow` absent; only `flow.md` + 2 projections added phase-wide | 0 |
| **7** | Evidence cites only `harness_config` / `contract_graph` facts that resolve; no vendored file imported | live execution of every cited symbol; `git grep -n 'opencode-matt-workflows' -- harness tools libs contracts .opencode .claude/agents .claude/commands .claude/skills README.md AGENTS.md`; `git diff --stat ee5a41c..HEAD -- docs/references/opencode-matt-workflows` | `components() languages() language_bash_scopes() pipeline() effective_relationships()` all return; `direct/reverse/transitive` each → `['ids','paths']`; sweep → **zero hits** (grep exit 1); vendored bundle diff → **empty** | 0 |
| **8** | Suite green; four gates clean; net surface +1 command, +0 everything else | see the SC8 block below | all green; surface proof below | 0 |

### SC3 — the citation loop, enumerated

Ten backticked command citations, each resolving to `harness/commands/<name>.md`:
`/add-language` `/checkpoint` `/contract-check` `/fan-out-synthesize` `/lint` `/new-contract-rule`
`/orient` `/review` `/test` `/verify-work`. Two module citations, each resolving to a real package
directory: `tools.harness_config` → `tools/harness_config/`, `tools.contract_graph` →
`tools/contract_graph/`. Twelve total, **zero unresolved**. This confirms D-01's *claim* at the phase
tip and carries forward Plan 01's correction to D-01's *enumeration*: `/component` is a live command
but is not cited in the file, so the D-01 list over-enumerates by one.

### SC7 — the evidence calls were executed, not read (D-21)

Every symbol the four *Repository evidence* blocks cite was imported and invoked at the phase tip:

```text
components() -> list ok            languages() -> list ok
language_bash_scopes() -> set ok   pipeline() -> dict ok
effective_relationships() -> list ok
direct(g, 'source')     -> ['ids', 'paths']
reverse(g, 'source')    -> ['ids', 'paths']
transitive(g, 'source') -> ['ids', 'paths']
```

`direct` / `reverse` / `transitive` are module-level functions taking `(graph, node)`, which is the
form the `contract-change` evidence block cites — they are not graph methods.

### SC8 — greenness

| Check | Command | Observed | Exit |
|---|---|---|---|
| Root suite | `uv run pytest -q` | **881 passed**, 7 snapshots passed, 0 failures | 0 |
| Instance leg (D-20) | `uv run pytest examples/log-parser -q` | **31 passed** | 0 |
| — sub-leg, as CI step 1 | `uv run pytest examples/log-parser/tests -q` | 14 passed | 0 |
| — sub-leg, as CI step 2 | `uv run pytest examples/log-parser/golden_runner -q` | 17 passed | 0 |
| emit-drift replica | `tools.harness_emit` then `git diff --exit-code -- .opencode opencode.json .claude/{agents,commands,skills} AGENTS.md CLAUDE.md .claude/settings.json` | no drift | 0 / 0 |
| stale-derived replica | `tools.docs_sync` **and** `tools.memory_regen.contracts_index`, then `git diff --exit-code -- docs/reference .memory/derived/contracts-index.md` | 6 reference pages regenerated, 6 contracts indexed, **no diff** | 0 / 0 / 0 |
| contract-drift replica | `uv run python -m tools.contract_drift.drift` | `OK — live manifest matches the committed baseline.` | 0 |
| ruff ratchet | `uv run python -m tools.ruff_baseline` | `74 findings (baseline 74)` — `PASS: every rule class is at its baseline.` | 0 |
| ratchet's own tests | `uv run pytest tools/ruff_baseline -q` | 27 passed | 0 |
| Tree | `git status --porcelain` | empty | — |

**881, not 876 and not 877.** The baseline moved at `4df76db`: five parametrized ids follow the new
command file — four from `tools/harness_lint/tests/test_commands.py` and one from
`test_agent_referential_integrity.py`. The `test_coexist` function was renamed, not added.

**The instance leg is 31, and the scoping matters.** Root `testpaths` is `["libs/python", "tools"]`,
so `examples/**` is not collected by the root run. `examples/log-parser/tests` alone measures **14**
and silently skips the 17-test .NET golden-parity leg that CI runs as a separate step — which still
reads as a pass. The whole-directory form was used. No commit in this phase touches the instance, so
this leg is a **confirmation of no regression**, not a requirement of any commit.

**The stale-derived replica includes `docs_sync` deliberately.** `docs_sync` is the only regenerator
of `docs/reference`; without it the `docs/reference` half of the diff compares a tree nobody
regenerated and is trivially clean. Run in the true form it still exits 0, so nothing was hidden —
but the replica can now detect what it claims to guard.

### SC8 — the net-surface proof

```text
$ git diff --name-status ee5a41c..HEAD -- harness/agents harness/skills harness/plugins \
      harness/git-hooks contracts .github/workflows uv.lock pyproject.toml
M	harness/agents/orchestrator.md
# A/D count: 0        uv.lock and pyproject.toml absent

$ git diff --name-status ee5a41c..HEAD -- harness/commands
A	harness/commands/flow.md
# A count: 1
```

**+1 command, +0 everything else** — no gate, tool, contract, skill, agent, hook, CI job, state file
or dependency. `uv.lock` never appears in the phase range (T-46-SC: zero packages installed).

Whole-phase `name-status`, for completeness — 18 paths, of which the only non-`.planning` additions
are the new command and its two emitter projections:

```text
M .claude/agents/orchestrator.md          A .claude/commands/flow.md
M .memory/state/activeContext.md          M .memory/state/progress.md
M .opencode/agent/orchestrator.md         A .opencode/command/flow.md
M AGENTS.md                               M README.md
M harness/agents/orchestrator.md          A harness/commands/flow.md
M tools/harness_emit/emit-manifest.json
M tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
M tools/harness_emit/tests/test_coexist.py
+ 5 A entries under .planning/phases/46-product-flow/
```

## D-24 — whole-phase LOC, measured

```text
$ git diff --shortstat ee5a41c..HEAD -- . ':(exclude).planning'
 13 files changed, 1518 insertions(+), 177 deletions(-)
```

**A net addition of +1341 lines** — the milestone's only additive phase, against seven that removed
~25k LOC of dev-side ceremony. Roughly half of the insertions are the `.ambr` body snapshot, which
renders both runtime projections and therefore moves at ~2× the source.

Reported for the record, the bare whole-tree form including planning documents:
`git diff --shortstat ee5a41c..HEAD` → **18 files changed, 2935 insertions(+), 177 deletions(-)**
(net **+2758**). The excluding-`.planning` figure is the one that describes the shipped surface.

Per-commit inputs: `439b416` → 4 files, +1154/−154; `4df76db` → 8 files, +333/−8; `bbf5f2f` →
2 files, +31/−15.

## D-23 — no mutation-proof table is owed

This phase adds **prose and one command, and adds no control**. There is no gate, hook, assertion or
CI job introduced anywhere in the range, so there is nothing whose bypass could be demonstrated by
mutating an input. Nothing enforces route adherence, deliberately: per ADR-0012 CI and the merge are
the authority, and a route-compliance gate would be exactly the ceremony this milestone removed
(T-46-12, disposition **accept**).

## Deviations from Plan

**None.** Both tasks executed exactly as written, and all four of the plan's pre-measured corrections
held under measurement:

1. **881, not 876** — confirmed at the tip.
2. **`uv run pytest examples/log-parser -q` → 31** — confirmed, and the 14/17 split was measured
   separately to show what the narrower path would have skipped.
3. **`docs_sync` in the stale-derived replica** — included; the true form exits 0.
4. **`contracts-index.md` does not move** — confirmed; the conditional pathspec resolved to
   excluding it, and the commit named the two state files only.

One observation that is a wording refinement rather than a deviation: SC1's "delegation-packet
fields" are defined **once** in `### Delegation packet` and referenced per route by the token
`packet` — `bugfix` and `contract-change` say "a packet" / "its own packet" rather than the two-word
phrase "delegation packet". The measured predicate (≥1 packet reference per route, plus exactly one
`### Delegation packet` section defining the six fields) is satisfied by all four routes. This
matches Plan 01's claim; the count above uses the token so the number is reproducible.

No Rule 1 / 2 / 3 auto-fix triggered. No Rule 4 checkpoint was reached. Zero packages installed.

## Threat register disposition

| Threat ID | Disposition | Evidence at the tip |
|---|---|---|
| T-46-09 | mitigate | The three route fields carry no secret, token, credential or PII; the file's banner is intact and unmodified. |
| T-46-10 | mitigate | Every criterion above is a recorded command output with its exit code, replayable in a scratch clone; the surface claim is a `git diff --name-status` over the phase range, not a narrative. |
| T-46-11 | mitigate | The stale-derived replica diffs `docs/reference` and the committed `contracts-index.md` **after** regeneration by both `docs_sync` and `memory_regen.contracts_index`. Exit 0. |
| T-46-12 | accept | Stated in the D-23 section above. |
| T-46-SC | accept | `uv.lock` absent from the phase-range diff; zero packages installed. |

## Threat Flags

None. This plan introduces no network endpoint, auth path, file-access pattern, or schema change.

## Known Stubs

None.

## Requirements traceability

| Requirement | Recorded command output |
|---|---|
| **PROD-02** | SC1 route count 4 · SC2 six-field verbatim + `research` absent · SC3 table gone (`^\|` → 0) + 12/12 citations resolving |
| **PROD-03** | SC4 `grep -c '^\*\*Discipline:\*\*'` → 5, one per route plus the cross-cutting red-before-green line |
| **PROD-04** | SC5 `ls harness/commands/*.md \| wc -l` → 18 · SC6 the round-trip run · SC8 surface diff = exactly one `A` |
| **PROD-05** | SC7 every cited `harness_config` / `contract_graph` symbol executed and returning · zero-hit vendored sweep |

## Commits

- `bbf5f2f` — `chore(46): record the route/step/next state round-trip in the shipped state plane`
  (2 files, +31/−15)

Task 2 writes only this SUMMARY; the phase-doc commit belongs to the orchestrator, not this plan.
`.planning/STATE.md` and `.planning/ROADMAP.md` were deliberately left untouched.

## Residual for the milestone-close PR

Carried forward unchanged, nothing added by this plan:

- The nine-item deferral list inherited from `45-06-SUMMARY.md` — `docs/glossary.md`'s two-line edit,
  ADR-0008 / ADR-0003's dangling citations, the 982-vs-live README counts, and D-24's
  branch-protection remedy.
- v2.6 (phases 47–50): `/impact`, package facts, and the `contract_graph` query surface — the
  one-command form each *Repository evidence* block already forward-references in unbackticked prose,
  so those blocks need no rewrite when it lands.

## Self-Check: PASSED

- `.planning/phases/46-product-flow/46-03-SUMMARY.md` — FOUND
- `.memory/state/activeContext.md` — FOUND, carries `Route:` / `Step:` / `Next command:`
- `.memory/state/progress.md` — FOUND, `## Recently done (last 5)` bounded at 5
- commit `bbf5f2f` — FOUND in `git log`

---
*Phase: 46-product-flow*
*Completed: 2026-07-29*
