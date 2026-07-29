---
phase: 43-lifecycle-plane-removal
plan: 01
subsystem: harness-source-surface
tags: [harness, commands, agents, prose, emit-snapshot, cer-07]

# Dependency graph
requires:
  - phase: 42-adoption-decoupling-install-set-repair
    provides: the delete -> git add -> git commit -- <pathspec> -> verify -> amend-if-red ordering
      discipline (D-12/D-13) this plan reuses for prose edits
provides:
  - "harness/commands/{checkpoint,orient,review,verify-work}.md with every tools.handoff /
    tools.evidence invocation removed at source"
  - "harness/agents/orchestrator.md routing by declared topology/stage + language only — no
    tools.capability, no capabilities.toml, no discipline/lane language, no adversarial-review-panel"
  - "a projection snapshot regenerated in each of the plan's two commits, so no intermediate
    commit in this phase carries a stale test_emit_determinism.ambr"
affects: [43-02, 43-03, 43-04, 43-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "W-4 emit-snapshot rule: any commit touching harness/{agents,commands,skills}/ or
      harness/opencode.json regenerates tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
      in that same commit, verified by a non-updating re-run before staging"
    - "W-1 survival assertions: live-tree gate tests with hardcoded string assertions are RUN as
      an acceptance criterion, not inferred from the diff (D-15)"

key-files:
  created: []
  modified:
    - harness/commands/checkpoint.md
    - harness/commands/orient.md
    - harness/commands/review.md
    - harness/commands/verify-work.md
    - harness/agents/orchestrator.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr

key-decisions:
  - "D-03 honored throughout: every lifecycle step was REMOVED, never replaced. No shim, no
    successor mechanism, no comment-only stub, no TODO was left in place of a removed step."
  - "Deviation A: review.md's trailing two sentences (line 53-54, 'the adapter refuses sensitive
    plaintext...' / 'An open blocker or major finding prevents COMPLETE') were removed along with
    the plan-enumerated lines 49-52. They are finding-capture prose whose subject ('the adapter')
    is tools.evidence.capture and whose object (COMPLETE) is a lifecycle phase; keeping them
    would have left an orphaned pronoun pointing at a module Wave 3 deletes."
  - "Deviation B: checkpoint.md's last Note ('when there is no active task, preserve the existing
    two-file flow') was trimmed to 'the two-file flow is the whole flow' — the conditional it
    describes no longer exists once step 1 is gone. A trim, not a replacement."
  - "Deviation C: the plan's suggested rewrite of orchestrator.md line 98 ('current resolution of
    the routing table below') would have been self-referential, since the sentence sits above the
    table it names. Used the plan's sanctioned 'or equivalent' latitude and pointed it at the
    surviving authority (the declared topology / project.toml) instead."

requirements-completed: [CER-07]

# Metrics
duration: ~25min
completed: 2026-07-28
---

# Phase 43 Plan 01: Repair the Five Surviving Lifecycle Consumers Summary

**Stopped the four surviving commands and the orchestrator agent from shelling or naming any module the lifecycle plane deletes, regenerating the committed projection snapshot in each commit so both commits of the phase's first wave are fully green.**

## Performance

| Metric | Value |
|---|---|
| Tasks | 2/2 |
| Commits | 2 |
| Files modified | 6 |
| Full-suite runs | 3 (baseline + one per task), all green |

## What Was Built

### Task 1 — the four commands (`d38c18b`)

- **`checkpoint.md`** — deleted step 1 (the `tools.handoff generate && validate && activate`
  paragraph and its `!` line) outright; renumbered 2→1, 3→2. In the renumbered step 2, dropped both
  conditional `git add` lines (`active-task.json`, the HANDOFF revision file) and the
  ` && uv run python -m tools.handoff validate ...` tail on the commit line, leaving a plain
  `git add` + `git commit` over `activeContext.md` / `progress.md`. The `updated:` quoted-stamp
  mandate, both state-file pathspecs, and the literal sentence *"git holds the full completed
  history"* all survive — the handoff clauses came out from around them.
- **`orient.md`** — deleted the whole `## 1. Active HANDOFF first (fresh-session resume barrier)`
  section including its `tools.handoff resume` `!` line; renumbered sections 2→1, 3→2, 4→3. In the
  read-order, deleted item 2 (*"Active HANDOFF, when surfaced above — validate it, then run
  `/phase-gate`"*) and renumbered 3→2, 4→3, 5→4. The read-order item naming `context-budget` and
  `fan-out-synthesize` survives the renumbering intact.
- **`review.md`** — removed the finding-capture prose that invoked
  `tools.evidence.capture add-finding`. Step 4's code-reviewer hand-off and re-run-until-clean
  sentences are byte-unchanged.
- **`verify-work.md`** — removed the evidence-capture wrapper paragraph that invoked
  `tools.evidence.capture capture`. The five numbered gate sections and their `!` commands are
  byte-unchanged (`git diff` shows a 6-line deletion and zero insertions in that file).

### Task 2 — the orchestrator (`9056d22`)

`harness/agents/orchestrator.md` now routes on two dimensions — pipeline stage/component, then
language. Removed: the *"Routing by capability is the rule..."* sentence and its
`harness/capabilities.toml` claim; the whole numbered intake step *"Name the capability, then
resolve a provider"* including its `tools.capability list` / `tools.capability route` code block
and the *"a lane's discipline record... missing required disciplines"* enforcement sentence
(intake renumbered to run 1–7 with no gap); the three-dimension routing-table intro (rewritten to
two); the `` `adversarial-review` capability → `` and `` `reconnaissance` capability → `` prefixes
on the code-reviewer and explorer rows; the *"High-risk change needing several review frames
(STRICT+ lane requirement)"* row naming the `adversarial-review-panel` skill (deleted outright, no
successor); the *"Which agents may do this kind of work?"* row and its `tools.capability list`
command; and the closing *"Where a capability declares an allowlist..."* sentence.

Untouched, as required: the `Trace the topology` intake step and its `tools.harness_config` /
`tools.contract_graph` bodies, all four `/pipeline` routing rows (Phase 44's target, not this
phase's), the `context-budget` and `fan-out` references, and the entire YAML frontmatter
(`name: orchestrator`, `mode: primary`, the permission block, `tools:`) — confirmed by grepping the
commit diff for frontmatter keys and getting no hits.

### The W-4 emit-snapshot rule

Both commits ran `uv run pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update -q`
before staging, then re-ran without the flag to exit 0, and both carried
`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` in their
`git commit -- <pathspec>`. Neither commit left the `.ambr` dirty.

## Acceptance Criteria — all held

### Task 1

| Criterion | Result |
|---|---|
| `grep -rn "tools\.handoff\|tools\.evidence"` over the four commands | exit 1, no output |
| `grep -n "phase-gate" harness/commands/orient.md` | exit 1, no output |
| Valid frontmatter + ≥1 numbered step in each of the four | checkpoint 2 steps, orient 7, review 4, verify-work 5; frontmatter parses via `tools.harness_lint.parse_frontmatter` |
| `uv run pytest tools/memory_regen/tests/test_checkpoint_command.py tools/harness_lint/tests/test_context_budget_wiring.py -q` | 7 passed |
| `grep -c "context-budget" orient.md` ≥ 1 / `grep -c "fan-out" orient.md` ≥ 1 | 1 / 1 |
| `uv run pytest tools/harness_emit/tests/test_emit_determinism.py -q` (no `--snapshot-update`) | 4 passed, 1 snapshot passed |
| `.ambr` shows `M` in the same commit; `git status --porcelain` on it empty | both hold (see `d38c18b` name-status) |
| `uv run pytest -q` | 1313 passed |

### Task 2

| Criterion | Result |
|---|---|
| `grep -n "tools\.capability\|capabilities\.toml\|disciplines\.toml\|adversarial-review-panel\|lane's discipline\|missing required disciplines"` | exit 1, no output |
| `grep -c "Trace the topology"` | 1 |
| `grep -c "/pipeline"` | 4 |
| frontmatter unchanged | confirmed — diff carries no `name:`/`mode:`/`permission`/`tools:` lines |
| `uv run pytest tools/harness_lint/tests/test_orchestrator_topology.py tools/harness_lint/tests/test_context_budget_wiring.py -q` | 6 passed |
| `uv run pytest tools/harness_emit/tests/test_emit_determinism.py -q` | 4 passed |
| scoped `awk ... \| grep -c "tools.capability"` over the two orchestrator projections | **0** |
| unscoped whole-`.ambr` count (predicted to stay 6) | **6** — exactly as the plan measured |
| `.ambr` `M` alongside `orchestrator.md`; `git status --porcelain` on it empty | both hold |
| `uv run pytest -q` | 1313 passed |

## Deviations from Plan

Three, all prose-scope, all in the *removal* direction (D-03 preserved — nothing was substituted):

**A. `review.md`: two extra sentences removed beyond the plan's line 49-52.**
The plan named lines 49-52 (the `add-finding` paragraph) and said to leave step 4's first two
sentences intact. Lines 53-54 — *"Do not put diff text, credentials, or PII in findings; the
adapter refuses sensitive plaintext and records only a redaction report. An open blocker or major
finding prevents COMPLETE."* — were in neither set. They were removed because "the adapter" has no
antecedent once the `tools.evidence.capture` sentence is gone, and "prevents COMPLETE" names a
lifecycle phase this phase deletes. The plan's own artifact spec for `review.md` reads *"finding
capture prose removed"*, which this satisfies. No acceptance criterion distinguishes the two
choices; both greps pass either way.

**B. `checkpoint.md`: last Note trimmed.**
*"A checkpoint remains optional; when there is no active task, preserve the existing two-file
flow."* → *"A checkpoint remains optional; the two-file flow is the whole flow."* The conditional
branch it describes ceased to exist when step 1 was deleted. The plan sanctioned intro-prose
updates ("Update the file's intro prose if it still describes the removed handoff step") but the
stale sentence was in Notes, not the intro.

**C. `orchestrator.md` line 98 rewrite wording.**
The plan suggested *"current resolution of the capability registry"* → *"current resolution of the
routing table below"*. That would be self-referential — the sentence sits above the table it names,
so it would claim the table is a resolution of itself. Used the plan's explicit *"(or equivalent;
no registry survives to resolve against)"* latitude and pointed it at the declared topology /
`project.toml`, which is the authority that does survive and which the routing rows already cite.

## Things the Plan Did Not Anticipate

1. **Plan 43-02 shares the working tree, not just the repo.** Wave 1 was described as concurrent on
   a disjoint *file set*, but `git status --porcelain` during Task 1 showed 43-02's in-flight edits
   to `tools/memory_regen/inject.py`, `tools/memory_regen/tests/test_inject_assembler.py`, and
   `tools/handoff/tests/test_handoff.py` sitting uncommitted in the same tree. This makes the
   plan's `uv run pytest -q` exit-0 criterion a **shared** signal: a red there could belong to
   either plan. It stayed green throughout, so nothing was compromised — but the full-suite count
   moved from **1316 (baseline)** to **1313** between the baseline run and Task 1's run, with no
   test file of mine touched. Those 3 tests were removed by 43-02, not by this plan. An executor
   who diffed test counts and treated the drop as its own regression would have chased a ghost.
   Both commits' pathspecs were confirmed clean of 43-02 files via `git diff --cached --name-only`
   before each commit.
2. **`grep -c "/pipeline"` counts lines, not occurrences.** The criterion expects `4` and gets `4`,
   but only because the four `/pipeline` routing rows each carry it on one line — two of them
   carry it twice (`/pipeline, then /golden, /lint`). If a future edit merges or splits those
   rows the count moves without `/pipeline` actually being removed. Worth noting for 43-03/43-04
   if they reuse the pattern.
3. **`verify-work.md`'s intro sentence needed no rewrite.** The plan flagged the wrapper paragraph
   for removal but the sentence immediately above it — *"Run the five gates in order; stop at the
   first hard failure and fix before proceeding."* — reads correctly standalone, so the file
   needed a pure 6-line deletion with zero insertions. Confirmed against the diffstat.

## Commits

| Hash | Description |
|---|---|
| `d38c18b` | `refactor(43-01): stop the four surviving commands from invoking the lifecycle plane` — checkpoint/orient/review/verify-work repaired, `.ambr` regenerated in-commit |
| `9056d22` | `refactor(43-01): route the orchestrator by topology and language only` — capability/discipline/panel language removed, `.ambr` regenerated in-commit |

Both commits used `git commit -- <pathspec>` with `git diff --cached --name-only` inspected first
(D-13). No `git add -A`, no `git add .`, no `git commit -a`, no `git checkout <ref> -- .`. No
emitter run (`python -m tools.harness_emit` is 43-03's, Wave 2). No `.opencode/**` or `.claude/**`
file was touched. `GOLDEN_APPROVE_HUMAN` was never set. No new gate, tool, contract, or dependency
was added.

## Self-Check: PASSED

- All six modified files exist on disk at their declared paths.
- Both commit hashes (`d38c18b`, `9056d22`) resolve in `git log`.
- `uv run pytest -q` green at HEAD (1313 passed, 7 snapshots passed).
- `git status --porcelain -- tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
  is empty at HEAD.
