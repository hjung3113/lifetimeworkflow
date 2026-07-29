# Phase 46: Product Flow - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-07-29 · **Mode:** `--auto` — every question auto-resolved to the recommended option.
**Areas discussed:** Route set, Completion contract provenance, State mechanism, Evidence genericness,
Additive blast radius

`[--auto] Selected all gray areas.`

---

## Route set

| Option | Description | Selected |
|--------|-------------|----------|
| Four routes: small-change · bugfix · feature · contract-change | Matches PROD-02; `contract-change` is the one non-repo-agnostic route | ✓ |
| Add `research` as a fifth | Symmetry with the vendored flows | |
| Two routes (change · contract-change) | Smaller surface | |

**Auto-selection:** `[auto] Route set → "Four routes" (recommended default)`
**Notes:** `research` is deliberately absent — it terminates in a document, and `explorer` +
`fan-out-synthesize` + `context-budget` already cover it; adding it would be surface without a stop
condition. Two routes collapse the distinction that makes this harness worth deploying:
`contract-change` is the single route where the harness is **not** repo-agnostic.

---

## Completion-contract provenance

| Option | Description | Selected |
|--------|-------------|----------|
| Copy the six-field text verbatim; import nothing | Text is not a dependency | ✓ |
| Reference the vendored file from the route prose | Creates a DEV-only dependency in a product artifact | |
| Reword it | Loses the contract's recognizability across handoffs | |

**Auto-selection:** `[auto] Completion contract → "Copy verbatim, import nothing" (recommended default)`
**Notes:** Verified at `WORKFLOW_CONTRACTS.md:39-46`. The vendored bundle is pinned DEV-only, and its own
`UPSTREAM_SKILLS.md:34-42` says to **stop** when an upstream skill is missing — so "degrades gracefully"
was false and a runtime dependency on it is forbidden. Copying prose is not depending on a file.

---

## State mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Record route · step · next in the shipped `.memory/state/activeContext.md` | Writer and reader already exist and already install | ✓ |
| A new `.flow/state.md` | PROD-04 forbids it by name | |
| A router agent holding state | A new agent — surface growth | |

**Auto-selection:** `[auto] State → "Reuse activeContext.md" (recommended default)`
**Notes:** `destinations.py:151` already installs the file; `/checkpoint` already writes it and
`/orient` already reads it. This phase adds prose, not plumbing — net +1 command, +0 everything else.

---

## Evidence genericness

| Option | Description | Selected |
|--------|-------------|----------|
| Cite only live `harness_config` + `contract_graph` facts, worded so `/impact` slots in later | The differentiator; forward-compatible with v2.6 | ✓ |
| Generic "check the affected files" prose | Indistinguishable from the vendored repo-agnostic flows | |
| Wait for v2.6's `/impact` | Leaves the routes evidence-free for a milestone | |

**Auto-selection:** `[auto] Evidence → "Live harness facts, /impact-ready wording" (recommended default)`
**Notes:** This is the easiest thing in the phase to fumble into genericness. The vendored flows are
repo-agnostic; these must cite facts only this harness can compute.

---

## Additive blast radius

| Option | Description | Selected |
|--------|-------------|----------|
| Treat the addition as the same defect class as a deletion; repair count literals in-commit | Twenty-plus blockers across 43–45 came from this class | ✓ |
| Add the command, fix counts in a follow-up commit | Leaves a red commit | |

**Auto-selection:** `[auto] Blast radius → "Same class, repair in-commit" (recommended default)`
**Notes:** Adding `flow.md` invalidates `test_coexist.py:40,41,73,74` (17→18), the `.ambr` body snapshot
(needs `--snapshot-update` in-commit), and `emit-manifest.json` (+2 rows, self-generated but must be in
the pathspec). `caps.py` has no `EXPECTED_COMMANDS`, so the emitter's pre-write hard-fail does not apply
— confirmed, so nobody should go hunting for one.

## Claude's Discretion

- Plan/task decomposition; the `orchestrator.md` rewrite is the long pole and is separable from `flow.md`.
- Exact route wording and stop-condition shape.
- Whether the five PROD-03 sentences ride with their routes or land as one pass.

## Deferred Ideas

- `/impact`, package facts, the `contract_graph` query surface → v2.6.
- The nine-item milestone-close list inherited from Phase 45 → the milestone-close PR.
