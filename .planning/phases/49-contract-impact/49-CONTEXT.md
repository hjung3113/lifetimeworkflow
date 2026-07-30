# Phase 49: Contract Impact - Context

**Gathered:** 2026-07-30
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous) — 3 areas, all accepted as recommended

<domain>
## Phase Boundary

Deliver one `/impact <contract>` command that reports the affected **contracts** (direct, reverse,
transitive, with connecting paths) and the affected **packages** for a contract change, built
entirely on existing engines: `contract_graph.query`'s three functions plus the Phase-47 package
facts. It fills the `contract-change` route's *Repository evidence* slot in
`harness/agents/orchestrator.md`, replacing an inline `uv run python -c` one-liner.

**On demand only** — no SessionStart injection, no gate, no CI job, no hook reference. Commands go
18 → 19; that is the one sanctioned surface addition in v2.6, and the Phase-48 count/name guards are
updated in the same change.

Out of the boundary: contract versioning/compatibility (carried EVOL-02), caching impact results,
any gate on impact output.

</domain>

<decisions>
## Implementation Decisions

### `/impact` output & invocation
- Takes a **contract path** under `contracts/` — what route step 1 actually lands on — resolved to its
  graph node; a bare node id is also accepted.
- Reports affected **contracts** (direct / reverse / transitive, each with connecting paths), affected
  **packages**, and the owning engineer per side of the declared edge.
- The command file is **thin**: `harness/commands/impact.md` composes a reporter; it is not a script
  with logic embedded in markdown.
- An unknown or unmapped contract gets a **clean refusal that names what was searched** — never an
  empty success, which would read as "nothing is affected" and is the dangerous failure mode for a
  pre-edit evidence step.

### Reuse discipline
- Traversal is **only** `direct` / `reverse` / `transitive` (`tools/contract_graph/query.py:29,39,55`)
  over `compile_graph()`'s adjacency. A test asserts the reporter defines no walk of its own — no
  second traversal engine (REQUIREMENTS.md forbids a second authority plane).
- Package attribution reuses `owning_package()` and the Phase-47 package facts.
  `tools/contract_graph/ownership.py` stays **untouched**.
- Declared-edge confirmation and per-side owners come from `effective_relationships()` and
  `components()` — the same calls the current route block already names.
- Output is **deterministic**: byte-identical for the same graph + node, all sets sorted, proven by a
  repeat-invocation test.

### Route wiring & surface accounting
- The `contract-change` route's *Repository evidence* block becomes `/impact`; the inline
  `uv run python -c "..."` one-liner is **removed**, not kept alongside. Two ways to get the same
  evidence is how they drift apart.
- Command count goes **18 → 19**. `test_command_count_is_stable` and `test_command_names_are_stable`
  (both added in Phase 48) are updated to 19 and to include `impact` **in the same change** — the
  guards working as designed, not an obstacle to route around.
- Nothing is added to SessionStart; a test asserts the injector's assembled output is byte-identical.
- The reporter lives at `tools/contract_graph/impact.py` — a new module in an **existing** package, so
  no new `tools/` package is created.

### Claude's Discretion
- The rendered layout of the report (sections, ordering within a section) provided it is deterministic.
- Function names and signatures inside `impact.py`.
- Whether the CLI entry point is `python -m tools.contract_graph.impact` or a function the command
  invokes, provided the command file stays thin.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/contract_graph/query.py` — `direct` (`:29`), `reverse` (`:39`), `transitive` (`:55`); each
  returns `{"ids": sorted[...], "paths": [[...]]}`, cycle-safe, no file I/O, deterministic.
- `tools/contract_graph/compile.py` — `compile_graph()` producing the `adjacency` map.
- `tools/contract_graph/ownership.py` — `owning_package()`, pure segment-based nearest-enclosing
  lookup with root fallback (Phase 47). To be reused, not modified.
- `tools/harness_config/loader.py` — `effective_relationships()`, `components()`,
  `effective_packages()`, `conventions_for()` (Phase 48).
- `tools/memory_regen/package_facts.py` + `.memory/derived/package-facts.md` — the committed package
  and dependency facts (Phase 47).

### Established Patterns
- Commands are authored runtime-neutral under `harness/` and projected to `.opencode/` + `.claude/`
  by `tools.harness_emit`; the generated trees are never hand-edited.
- Consistency gates live in `tools/harness_lint/tests/`; the command surface is pinned by
  `test_command_count_is_stable` and `test_command_names_are_stable`.
- GEN-04: nothing under `tools/`, `harness/`, `libs/` may name or path-reference `examples/` —
  tests, comments and docstrings included.

### Integration Points
- `harness/agents/orchestrator.md` — the `contract-change` route's *Repository evidence* block is the
  edit site; the route's five subsections (*When to use*, *Steps*, *Repository evidence*, *Stop
  condition*, *Next command*) and their order must survive.
- Route step 2 ("compute the affected set … before editing anything") and step 6 (golden inspection
  "for every component in the affected set") are the two places that consume impact output — the
  report must actually answer both.
- `.claude/commands/gsd` is the dev-side GSD tree, not an emitted command; command-surface counting
  must not confuse it for one.

</code_context>

<specifics>
## Specific Ideas

- Criterion 2 needs a real proof, not a claim: assert the reporter's affected sets are the same
  objects `query.py`'s three functions return, and that `impact.py` contains no independent traversal
  (a check that would fail if someone re-implemented a walk).
- Criterion 3's byte-identical injector proof should compare the assembled injector output before and
  after, not merely grep for the string `impact`.

</specifics>

<deferred>
## Deferred Ideas

- Caching or persisting impact results — nothing in the route needs it, and a cache would become a
  second source of truth about the graph.
- A gate that fails when a contract change lands without a recorded impact run — that is exactly the
  ceremony v2.5 removed and v2.6 forbids re-adding.

</deferred>
