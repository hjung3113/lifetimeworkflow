# Phase 46: Product Flow - Context

**Gathered:** 2026-07-29
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; see `46-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

The milestone's only **additive** phase, and the one that repays the other seven. Seven phases
removed ~25k LOC of dev-side ceremony; this one gives the **product** — the deployed harness, driven by
a weaker in-house model with no GSD to fall back on — four named routes and one entry point.

PROD-02…05, authored as prose in files that already ship, plus exactly one new command.

**Not in this phase:** anything that enforces route adherence. No route-compliance gate, no router
agent, no state file, no second command. `/impact` and package facts are v2.6.

</domain>

<decisions>
## Implementation Decisions

### Measured corrections — the requirement prose predates phases 43–45

- **D-01:** **PROD-02's "8 dangling citations stripped" is already discharged.** All twelve command and
  module citations in `orchestrator.md` resolve to live artifacts today — `/add-language`,
  `/checkpoint`, `/component`, `/contract-check`, `/fan-out-synthesize`, `/lint`,
  `/new-contract-rule`, `/orient`, `/review`, `/test`, `/verify-work`, `tools.harness_config`,
  `tools.contract_graph`. Phases 43–45 cleaned them. **Verify mechanically; do not redo.**
- **D-02:** **The routing table is 19 rows starting at `:72`**, not the "25-row (`:90-129`)" the
  requirement states — phases 43–44 deleted the personas those rows named. `orchestrator.md` is
  **102 lines**, not 129. Plan against the live file.
- **D-03:** The self-declaration PROD-02 quotes is at **`:45`**, not `:48`.

### What gets authored

- **D-04:** **Four route sections** — `small-change · bugfix · feature · contract-change` — each with an
  explicit **stop condition**, the delegation-packet fields, and the six-field completion contract.
- **D-05:** **The six-field completion contract is copied verbatim**: `Outcome · Artifacts or changes ·
  Verification · Decisions and assumptions · Risks or unresolved items · Next command`. Verified at
  `docs/references/opencode-matt-workflows/WORKFLOW_CONTRACTS.md:39-46`. Copy the *text*, import no file.
- **D-06:** **`research` is deliberately absent as a route.** It terminates in a document, and
  `explorer` + `fan-out-synthesize` + `context-budget` already cover it. Do not add it "for symmetry".
- **D-07:** **`contract-change` exists because it is the one route where this harness is not
  repo-agnostic.** That is the phase's whole differentiator — do not water it down into a generic
  "make a change" route.
- **D-08:** **PROD-03 — five retired discipline skills become ~20 lines of prose** in the file already
  being rewritten: bugfix → reproduce before fixing; feature → settle vocabulary first;
  contract-change → contract entry, then failing case, then code; all → red before green. This is
  prose in an existing file, **not** five new artifacts.
- **D-09:** **PROD-04 — exactly ONE new command**, `harness/commands/flow.md`. Live count is **17**, so
  the post-phase count is **18**. No `.flow/state.md`, no router agent, no new skill, contract, CI job,
  or hook.
- **D-10:** **State reuses what already ships.** Route · step · next command are recorded in
  `.memory/state/activeContext.md` (already installed by `destinations.py:151`), written by the
  existing `/checkpoint` and read by the existing `/orient`. **No new writer, no new reader, no new
  file.**
- **D-11:** **PROD-05 — *Repository evidence* uses only `harness_config` and `contract_graph` facts
  that resolve today**, worded so v2.6's `/impact` slots in without a rewrite.

### The vendored bundle

- **D-12:** **Zero flow artifacts are imported.** `docs/references/opencode-matt-workflows/` (79 files)
  is a pinned **DEV-only** reference and stays one. The mattpocock upstream skills are **not** a product
  dependency even optionally: the vendored contract says *stop* when one is missing
  (`UPSTREAM_SKILLS.md:34-42`), so "degrades gracefully" was false. Copying a sentence of text is fine;
  depending on a file is not.
- **D-13:** That bundle is also the repo's **largest false-positive source** for any sweep — 79 files of
  third-party prose inside `docs/`. Exclude it from every grep in this phase.

### The additive blast radius — the same class, mirrored

- **D-14:** **Adding a command touches the same live-tree-rendering artifacts a deletion does**, and all
  must be repaired in the SAME commit that adds `flow.md`: `tools/harness_emit/tests/test_coexist.py`
  at **`:40` (function name), `:41` (docstring), `:73`, `:74` (assertions)** — 17 → 18;
  `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`, which renders command **bodies**
  and therefore needs `--snapshot-update` in-commit; and `tools/harness_emit/emit-manifest.json`, which
  gains **two** rows (one per runtime tree) and **must be in the commit pathspec** — it self-generates,
  so do not hand-edit it, but do not leave it out either.
- **D-15:** `caps.py` has **no** `EXPECTED_COMMANDS` frozenset (only `EXPECTED_PERSONAS` and
  `EXPECTED_SKILLS`), so a command addition does not trip the emitter's pre-write hard-fail. Confirmed
  — do not go looking for one.
- **D-16:** Phases 43–45 produced **twenty-plus blockers of one class**: a committed artifact rendering
  the live tree with a hardcoded expectation, invalidated by a change, named by no plan. The direction
  reverses here but the class does not. Enumerate before planning.

### Ordering and commit discipline (carried, measured)

- **D-17:** Source-first: author `harness/**`, then `python -m tools.harness_emit`. Never hand-edit
  `.opencode/**`, `.claude/**`, or root `opencode.json`.
- **D-18:** `git commit -m "<msg>" -- <pathspec>` — message BEFORE `--`; `git rm`/`git mv` already
  stage; never `git add -A` / `git add .` / `git commit -a` / `git checkout <ref> -- .`.
- **D-19:** **GEN-04 phrasing rule.** `test_core_no_example_dep.py` scans every tracked file under
  `tools`, `harness`, `libs` for the literal token `examples/`. Route prose that references the
  reference instance must be phrased **without** that token. This red three commits across phases 45.
- **D-20:** `uv run pytest -q` does NOT collect `examples/**` (`testpaths = ["libs/python", "tools"]`).
  Any commit touching the instance needs an explicit instance leg.
- **D-21:** **Run things, don't read them.** Every phase from 40 to 45 found consumers its plan had not
  listed, and every one surfaced from a run.

### Verification / done-condition

- **D-22:** Done = four route sections with stop conditions and the delegation packet; the six-field
  contract verbatim; `research` absent; the 19-row table gone; every cited command/module resolving
  (asserted mechanically, not by eye); five operative sentences present; `ls harness/commands/*.md`
  = **18**; route/step/next round-tripping through `activeContext.md` via the existing pair; evidence
  citing only live `harness_config` / `contract_graph` facts; no vendored file imported;
  `uv run pytest -q` green at every commit with `emit-drift`, `stale-derived`, `contract-drift` and the
  ruff ratchet clean.
- **D-23:** **No mutation-proof table is owed** — this phase adds prose and one command, and adds no
  control. Nothing enforces route adherence, deliberately (see the ROADMAP's accepted consequence).
- **D-24:** Report whole-phase LOC from `git diff --shortstat` (measured). Expect a small net
  **addition** — the only such phase in the milestone.

### Claude's Discretion

- Plan/task decomposition and wave count; the `orchestrator.md` rewrite and the `flow.md` addition are
  separable and the rewrite is the long pole.
- Exact route wording and the shape of each stop condition.
- Whether the five PROD-03 sentences ride with their routes or land as one pass.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and authority
- `.planning/ROADMAP.md` §"#### Phase 46: Product Flow" — scope, the ⚠ corrections, non-goals, accepted
  consequence, 8 criteria.
- `.planning/REQUIREMENTS.md` — **PROD-02, PROD-03, PROD-04, PROD-05**.
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — the DEV/PRODUCT boundary and its operative
  rule ("no product capability may be declined because GSD covers it"). This phase is where that rule
  pays out.
- `docs/adr/0002-*` — the template/instance split constraining D-19.

### Prior-phase carry-forward
- `.planning/phases/45-projection-repair/45-06-SUMMARY.md` — the nine-item milestone-close deferral list
  this phase inherits, including `docs/glossary.md` and D-24's branch-protection finding.
- `.planning/phases/44-.../REVIEW.md` and `.planning/phases/43-.../REVIEW.md` — the recurring
  live-tree-rendering defect class D-16 names.

### The surface this phase touches
- `harness/agents/orchestrator.md` (102 lines; self-declaration `:45`, routing table `:72` ×19 rows).
- `harness/commands/flow.md` (new); `harness/commands/{checkpoint,orient}.md` (read, not edited).
- `tools/harness_emit/tests/test_coexist.py:40,41,73,74`;
  `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`;
  `tools/harness_emit/emit-manifest.json`.
- `docs/references/opencode-matt-workflows/WORKFLOW_CONTRACTS.md:39-46` (read for text; never imported).
- `.memory/state/activeContext.md`; `tools/adoption_scan/destinations.py:151`.

### Conventions
- `AGENTS.md` (root) — nearest-wins rules. ⚠ Its emitter-managed block is now **`:101-110`**.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- `/checkpoint` and `/orient` already write and read `.memory/state/activeContext.md` — D-10's whole
  mechanism exists and ships. This phase adds prose, not plumbing.
- The `--snapshot-update`-inside-the-commit pattern, proven across phases 43–45.

### Established patterns
- Emitted trees are derived; `emit-drift` reds on a hand-edit.
- `emit-manifest.json` self-generates but **must be committed** — omitting it reds `git diff --exit-code`.
- A command count literal lives in exactly one test file (`test_coexist.py`) in four places, including
  the function *name*.

### Integration points
1. `orchestrator.md` → the emitter → both runtime trees → the `.ambr` body snapshot.
2. `flow.md` (new) → `emit-manifest.json` (+2 rows) → `test_coexist.py`'s four count sites.
3. Route state → existing `activeContext.md` → existing `/checkpoint` writer and `/orient` reader.

</code_context>

<specifics>
## Specific Ideas

- The routes are for a **weak model with no GSD habit**. Favour explicit stop conditions and a literal
  next-command over elegance; the delegation packet and completion contract are what make a handoff
  survivable across a context boundary.
- PROD-05 is the differentiator and the easiest thing to fumble into genericness: the vendored flows are
  repo-agnostic, and *these* must cite facts only this harness can compute.

</specifics>

<deferred>
## Deferred Ideas

- `/impact`, package facts, and the `contract_graph` query surface → **v2.6** (phases 47–50).
- The nine-item milestone-close list inherited from Phase 45, including the `docs/glossary.md` two-line
  edit, ADR-0008/ADR-0003's dangling citations, the 982-vs-876 README counts, and D-24's
  branch-protection remedy → **the milestone-close PR**, not this phase.

</deferred>

---

*Phase: 46-product-flow*
*Context gathered: 2026-07-29*
