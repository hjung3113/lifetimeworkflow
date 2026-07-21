---
phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
plan: 03
subsystem: harness
tags: [contract-graph, conductor, pipeline, D-01, indented-tree, byte-identity, emit-round-trip, TOPO-06]

# Dependency graph
requires:
  - phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
    plan: 01
    provides: "compile_graph(cfg) -> {relationships, adjacency, diagnostics} — the adjacency the tree render walks"
  - phase: 25-graph-compiler-queries-conductor-proof-v2-3-a
    plan: 02
    provides: "direct/reverse/transitive affected-set queries the orchestrator cites for non-linear routing"
provides:
  - "harness/commands/pipeline.md: existing linear render PLUS a D-01 indented-tree section for branching/cyclic graphs (cycle -> node marker)"
  - "harness/skills/pipeline-map/SKILL.md: matching 'Rendering non-linear graphs' section consuming compile_graph"
  - "harness/agents/orchestrator.md: 'Trace the topology' intake step now cites direct/reverse/transitive for non-linear affected-set routing"
  - "tools/harness_lint/tests/test_conductor_graph_render.py: literal-text byte-identity regression for the linear render + D-01 token presence + anti-sprawl persona gate"
  - ".opencode/ + .claude/: conductor surfaces re-emitted byte-identically, no model identifier"
affects: [plan-25-04-proof, TOPO-06, TOPO-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive-only surface generalization: the general (branching/cyclic) render is an ADDITIONAL section; the linear stage-list/edge-chain steps stay byte-identical (git diff shows zero removed lines)"
    - "Byte-identity as a falsifiable test, not a manual diff: hardcoded literal-string assertions against the exact shipped example lines fail loud on any future rewrite"
    - "Gate-theft-avoidance ordering: source edit -> emit -> commit projected trees -> only THEN regenerate the determinism snapshot (never --snapshot-update first)"
    - "Anti-sprawl via imported constant: persona-unchanged asserted against imported EXPECTED_PERSONAS, never a re-hardcoded count"

key-files:
  created:
    - tools/harness_lint/tests/test_conductor_graph_render.py
  modified:
    - harness/commands/pipeline.md
    - harness/skills/pipeline-map/SKILL.md
    - harness/agents/orchestrator.md
    - .opencode/agent/orchestrator.md
    - .opencode/command/pipeline.md
    - .opencode/skill/pipeline-map/SKILL.md
    - .claude/agents/orchestrator.md
    - .claude/commands/pipeline.md
    - .claude/skills/pipeline-map/SKILL.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr

key-decisions:
  - "The D-01 tree render is appended as a NEW numbered step (step 5) in pipeline.md and a NEW '## Rendering non-linear graphs' section in the skill — the linear steps 1-4 and their example blocks are untouched, satisfying TOPO-06's byte-identity invariant literally (proven by zero removed lines in git diff --unified=0)"
  - "TOPO-06 byte-identity is proven by a hardcoded literal-string test against the exact shipped lines ('stage 1: source (python) consumes=[] produces=[greeting]', 'source -> sink (greeting)'), since these prose files carry no runnable render function"
  - "orchestrator.md's 'Trace the topology' step is EXTENDED with one sentence citing direct/reverse/transitive — no new routing-table row, no new persona, no new command reference (prose enrichment only)"
  - "No new command and no new persona: EXPECTED_PERSONAS stays 5, test_coexist stays 23 commands — the graph becomes usable through the EXISTING surface (TOPO-06 core intent)"
  - "Projected trees committed (497741a) BEFORE the determinism-snapshot regen (5d0c4bb) — the CI replica (re-emit && git diff --exit-code) is the real proof, not a green suite over a stolen snapshot"

patterns-established:
  - "A prose-surface byte-identity requirement is enforceable as an automated literal-string regression when the surface has no runnable function"

requirements-completed: [TOPO-06]

# Metrics
duration: ~15min
completed: 2026-07-19
---

# Phase 25 Plan 03: Graph-Aware Conductor Surfaces (Linear Render Byte-Identical) Summary

**Generalized the three EXISTING conductor surfaces — `/pipeline`, `pipeline-map`, and `orchestrator.md` — to consume the compiled contract graph (Plan 01) and affected-set queries (Plan 02), rendering non-linear topologies as D-01's indented tree with an explicit `(cycle -> <node>)` terminal marker, while keeping today's linear render provably byte-identical (a hardcoded literal-text regression), adding no new command or persona, and round-tripping byte-identically to both runtimes with no model identifier.**

## What shipped

- **Task 1 — surface edits (`d9ff339`).** `pipeline.md` gains step 5 ("Render the general (branching / cyclic) graph as an indented tree"): compile the graph, root at each authority with no incoming edge (lexicographically-first authority for a fully cyclic graph), indent one level per hop, and print an already-visited node as a terminal `(cycle -> <node>)` marker reusing `tools.contract_graph.query`'s visited-set-before-recurse discipline. `pipeline-map/SKILL.md` gains a matching `## Rendering non-linear graphs` section. `orchestrator.md`'s step 4 gains one sentence citing `direct`/`reverse`/`transitive` for non-linear affected-set routing. All existing linear-case text untouched (`git diff --unified=0` shows **0 removed lines**).
- **Task 2 — byte-identity regression (`691d656`).** New `test_conductor_graph_render.py` with literal-string assertions on the exact linear lines (`stage 1: source (python) consumes=[] produces=[greeting]`, `stage 2: sink ...`, `source -> sink (greeting)`), D-01 cycle/indent-or-tree token presence on both surfaces, and an anti-sprawl gate asserting the persona set equals imported `EXPECTED_PERSONAS` and orchestrator stays single `mode: primary`.
- **Task 3 — emit round-trip (`497741a` trees, `5d0c4bb` snapshot).** Re-ran `tools.harness_emit` (zero emitter code change) projecting all three edits into `.opencode/{agent,command,skill}` + `.claude/{agents,commands,skills}` — 6 projected files, +110 lines, **0 removed**, **no model identifier**. Committed the trees, then regenerated the projected-tree determinism `.ambr` snapshot (the one sanctioned red gate), in that order.

## Verification

- `uv run pytest tools/harness_lint/tests/test_conductor_graph_render.py tools/harness_lint/tests/test_orchestrator_topology.py tools/harness_emit/tests/test_coexist.py -q` → **passed** (36 + 5).
- `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode .claude` → **exit 0** (emit-drift clean, idempotent re-emit).
- `uv run pytest -q` (full suite) → **952 passed, 0 failed**.
- Anti-sprawl confirmed: persona set = 5 (`EXPECTED_PERSONAS` unchanged); command count = 23 (`test_coexist`, no new command).
- Model-identifier scan over all six projected copies → none found.

## Deviations from Plan

None — plan executed exactly as written. The re-emit produced the expected sanctioned failure in `test_emit_determinism.py::test_projected_tree_matches_committed_snapshot`; per the plan's `read_first` note and STATE.md's Phase-13/14/15 gate-theft lesson, this was resolved by regenerating the snapshot AFTER the projected-tree commit landed (`497741a` before `5d0c4bb`), never via a `--snapshot-update` that would bless un-emitted trees.

## Known Stubs

None. The three surfaces are agent-instruction prose (no runtime); every reference resolves to a committed Plan 01/02 function (`compile_graph`, `direct`/`reverse`/`transitive`).

## Threat Model

Both registered threats mitigated as planned:
- **T-25-05 (Tampering, linear-render drift):** Task 2's literal-text regression makes any change to the linear render a CI-visible automated failure.
- **T-25-06 (Repudiation, stale projected tree):** Task 3 re-runs the emitter and asserts `git diff --exit-code` after a second re-emit, proving the committed trees are the current deterministic projection.

No new security-relevant surface introduced (all edits are agent-instruction prose + a read-only test).

## Self-Check: PASSED

- Created file `tools/harness_lint/tests/test_conductor_graph_render.py` — FOUND.
- Created file `25-03-SUMMARY.md` — FOUND.
- Commits `d9ff339`, `691d656`, `497741a`, `5d0c4bb` — all FOUND.
