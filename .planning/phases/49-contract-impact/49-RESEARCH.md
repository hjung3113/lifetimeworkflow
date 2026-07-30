# Phase 49: Contract Impact - Research

**Researched:** 2026-07-30
**Domain:** codebase-internal (contract graph query + package facts join, one thin harness command)
**Confidence:** HIGH — every claim below is grounded in this checkout's own source and was verified
by reading or executing it in this session. No web search per phase scope.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### `/impact` output & invocation
- Takes a **contract path** under `contracts/` — what route step 1 actually lands on — resolved to its
  graph node; a bare node id is also accepted.
- Reports affected **contracts** (direct / reverse / transitive, each with connecting paths), affected
  **packages**, and the owning engineer per side of the declared edge.
- The command file is **thin**: `harness/commands/impact.md` composes a reporter; it is not a script
  with logic embedded in markdown.
- An unknown or unmapped contract gets a **clean refusal that names what was searched** — never an
  empty success, which would read as "nothing is affected" and is the dangerous failure mode for a
  pre-edit evidence step.

#### Reuse discipline
- Traversal is **only** `direct` / `reverse` / `transitive` (`tools/contract_graph/query.py:29,39,55`)
  over `compile_graph()`'s adjacency. A test asserts the reporter defines no walk of its own — no
  second traversal engine (REQUIREMENTS.md forbids a second authority plane).
- Package attribution reuses `owning_package()` and the Phase-47 package facts.
  `tools/contract_graph/ownership.py` stays **untouched**.
- Declared-edge confirmation and per-side owners come from `effective_relationships()` and
  `components()` — the same calls the current route block already names.
- Output is **deterministic**: byte-identical for the same graph + node, all sets sorted, proven by a
  repeat-invocation test.

#### Route wiring & surface accounting
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

### Deferred Ideas (OUT OF SCOPE)
- Caching or persisting impact results — nothing in the route needs it, and a cache would become a
  second source of truth about the graph.
- A gate that fails when a contract change lands without a recorded impact run — that is exactly the
  ceremony v2.5 removed and v2.6 forbids re-adding.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MONO-08 | A developer can run `/impact <contract>` and see which contracts and which packages are affected, built on `contract_graph.query`'s existing `direct`/`reverse`/`transitive` (`query.py:29,39,55`) plus the Phase-47 package facts — no second traversal engine. | Architecture Patterns (Pattern 1 contract→node resolution, Pattern 2 no-second-engine proof, Pattern 3 package-side reuse); Code Examples; Validation Architecture test map rows 1-5. |
| MONO-09 | `/impact` runs on demand only — no SessionStart injection, no gate, no CI job. It fills phase 46's evidence slot in the `contract-change` route. | Common Pitfalls (Pitfall 4 command-count guards, Pitfall 5 injector coupling); Code Examples (the exact one-liner to replace, `orchestrator.md:274-296`); Validation Architecture test map rows 6-9. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Contract-first**: `contracts/` is the single source of truth; code that disagrees with a contract
  is the thing that is wrong. `/impact` reports on this authority, it does not alter it.
- **Polyglot boundary**: language boundary is process/file/DB only — not applicable to this phase
  (pure Python, no cross-language object passing introduced).
- **Memory two-plane discipline**: derived artifacts (`.memory/derived/**`) are never hand-edited and
  are machine-regenerated; this phase touches none of them (`/impact` is on-demand, not derived-plane).
- **GEN-04**: nothing under `tools/`, `harness/`, `libs/` — tests and docstrings included — may name or
  path-reference `examples/`. `impact.py` and its tests must use domain-neutral fixture names (mirror
  `test_compile.py`/`test_query.py`'s `"a"`/`"b"`/`"widget"` convention), never a literal
  `examples/log-parser/...` string, per the pitfall Phase 47's `ownership.py`/`test_ownership.py`
  already hit and fixed (`47-04-SUMMARY.md`).
- **No model identifiers in repo artifacts**: commits, PR text, code comments must not name a model.
- **GSD Workflow Enforcement**: file-changing work in this repo goes through a GSD entry point
  (`/gsd-execute-phase` etc.) — noted for the planner, not itself a code constraint on `impact.py`.
- **v2.6 no-growth constraint** (binding, ROADMAP.md/REQUIREMENTS.md): default answer to "should we
  also gate X?" is NO. This phase is the ONE sanctioned surface addition (+1 command); +0 gates, +0 CI
  jobs, +0 contracts, +0 external deps are hard limits, not aspirations.

## Summary

`/impact <contract>` is a pure composition of code that already exists: `tools/contract_graph/query.py`'s
`direct`/`reverse`/`transitive` over `compile_graph()`'s adjacency, plus `owning_package()` +
`effective_packages()` for the package side. The one genuinely new piece of logic Phase 49 must write
is the **contract-path → graph-node resolution step**, because a graph node in this codebase is a
**component/member id string** (e.g. `"source"`, `"parser"`), never a contract path or contract id.
`compile.py`'s `adjacency` keys/values are `rel["authority"]` / `rel["dependents"]` strings —
`rel["contract"]` is an edge *label*, not a node. Resolving "contract path in, node out" means: derive
the contract id from the path (`Path(...).name.removesuffix(".schema.json")`, the exact idiom
`compile.py:46` already uses), search `effective_relationships()` for a record whose `"contract"`
field equals that id, and take that record's `"authority"` as the node. If no relationship names the
contract, there is no node — that is the clean-refusal path, and it is not an edge case in this
checkout: it is the ONLY path today.

**Live-graph fact (verified by execution this session):** `compile_graph()` on the default (core)
config returns `{"relationships": [], "adjacency": {}, "diagnostics": []}` — CER-08 (Phase 44)
deleted the core's `[pipeline].edges`, and the core's `[contract_graph]` table is empty. Every one of
the 6 tracked contracts in this checkout (`normalization/format-conventions`, `sample/greeting`,
`harness/topology/relationship`, `harness/adoption/{plan,inventory,manifest}`) is therefore
**unreferenced by any relationship** — `/impact` on any real contract path in this checkout hits the
clean-refusal branch, never the traversal branch. Fixtures (synthetic `cfg` dicts, following
`test_query.py`/`test_compile.py`'s domain-neutral `"a"`/`"b"`/`"widget"` idiom) are **mandatory** to
exercise and prove the non-refusal path — the live tree cannot do it.

**Primary recommendation:** write `tools/contract_graph/impact.py` as a thin function
`report(contract_path, cfg=None, graph=None, facts=None) -> dict` that (1) resolves contract-path →
node via `effective_relationships()`, refusing cleanly if unresolved, (2) calls `direct`/`reverse`/
`transitive` unmodified on the resolved node, (3) maps every id in the union of those three id-sets
plus the query node itself to an owning package via `owning_package()` + `effective_packages()`,
reusing the exact `"dir"`-key adapter filter Phase 48 built in `conventions_for()`
(`tools/harness_config/loader.py:320-338`) rather than re-deriving it, and (4) returns a fully sorted,
deterministic dict. `harness/commands/impact.md` stays a thin macro that shells out to this function
(mirrors `component.md`'s `python -c` idiom) and `orchestrator.md`'s `contract-change` route's
*Repository evidence* block is replaced, not augmented.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Graph traversal (direct/reverse/transitive) | `tools/contract_graph/query.py` (existing) | — | REQUIREMENTS.md/CONTEXT.md forbid a second traversal engine; MONO-08 names these three functions by signature. |
| Graph compilation (adjacency from config) | `tools/contract_graph/compile.py` (existing) | `tools/harness_config` (`effective_relationships`) | `compile_graph()` is the only legal producer of `adjacency`; `impact.py` must call it, never re-derive adjacency. |
| Contract-path → node resolution | **new**, `tools/contract_graph/impact.py` | `effective_relationships()` for the contract→authority lookup | This lookup does not exist anywhere in the codebase today — it is the one new piece of logic. |
| Package attribution | `tools/contract_graph/ownership.py` (`owning_package`, existing, untouched) | `tools/harness_config/loader.py` (`effective_packages`) | CONTEXT.md: "ownership.py stays untouched." `impact.py` calls it, does not modify it. |
| Declared-edge / owner-per-side confirmation | `tools/harness_config/loader.py` (`effective_relationships`, `components`) | — | Same calls the current inline one-liner already names (`orchestrator.md:282`). |
| Command surface / routing | `harness/commands/impact.md` (new, thin) | `harness/agents/orchestrator.md` (edit site) | Command composes the reporter; it is not a script with logic embedded in markdown (CONTEXT.md). |
| Runtime projection | `tools/harness_emit` (existing, unmodified) | — | New command file is picked up by the existing glob-driven `iter_commands()`; no emitter code changes needed. |

## Standard Stack

No external dependency additions — CONTEXT.md and REQUIREMENTS.md forbid it (+0 external deps). This
phase is 100% composition of existing in-repo modules plus stdlib.

### Core (existing, reused verbatim)
| Module | Function | Signature (verified) | Purpose |
|--------|----------|----------------------|---------|
| `tools/contract_graph/query.py` | `direct(graph, node)` | `query.py:29` — returns `{"ids": sorted[str], "paths": [[node, dep], ...]}` | one-hop outgoing |
| `tools/contract_graph/query.py` | `reverse(graph, node)` | `query.py:39` — same shape, one-hop incoming (transposed adjacency) | one-hop incoming |
| `tools/contract_graph/query.py` | `transitive(graph, node)` | `query.py:55` — same shape, full reachable set (start excluded), cycle-safe iterative worklist | full reachable set |
| `tools/contract_graph/compile.py` | `compile_graph(cfg=None)` | `compile.py:49` — returns `{"relationships": [...], "adjacency": {authority: sorted[dependents]}, "diagnostics": sorted[str]}` | compiles config → graph |
| `tools/contract_graph/ownership.py` | `owning_package(packages, contract_path)` | `ownership.py:28` — returns package id `str`; raises `ValueError` naming the path if unenclosed | contract → owning package |
| `tools/harness_config/loader.py` | `effective_relationships(cfg=None)` | `loader.py:95` — sorted list of `{"id","contract","authority","dependents"[,"kind","labels"]}` | declared-edge source (also the contract→authority lookup table `impact.py` must scan) |
| `tools/harness_config/loader.py` | `components(cfg=None)` | `loader.py:58` — raw `[[components]]` passthrough | per-side owner/engineer lookup |
| `tools/harness_config/loader.py` | `effective_packages(cfg=None, facts=None)` | `loader.py:205` — `[[components]]` layered over `package_facts.build_facts()["packages"]`, sorted by id | the `packages` argument `owning_package()` needs |
| `tools/harness_config/loader.py` | `conventions_for(path, cfg=None, facts=None)` | `loader.py:296` | reference for the exact dir-key adapter pattern (not called directly — its filter is duplicated locally, see below) |

**Version verification:** N/A — zero external packages. All functions above exist in this checkout
today (verified by direct `Read`/execution in this session, 2026-07-30).

## Package Legitimacy Audit

Not applicable — this phase installs **zero** external packages (+0 external deps per CONTEXT.md/
ROADMAP.md). `slopcheck` was not run; there is nothing to check.

## Architecture Patterns

### System Architecture Diagram

```
 developer
    │
    │ /impact <contracts/foo/bar.schema.json>   (or a bare node id)
    ▼
 harness/commands/impact.md  (thin — one shell/python invocation, no embedded logic)
    │
    ▼
 tools/contract_graph/impact.py :: report(contract_path, cfg=None, graph=None, facts=None)
    │
    ├─1─▶ resolve contract id from path
    │        contract_id = Path(contract_path).name.removesuffix(".schema.json")
    │        (mirrors compile.py:46's _tracked_schemas idiom — same suffix-strip rule)
    │
    ├─2─▶ scan effective_relationships(cfg)  [loader.py:95]
    │        find rel where rel["contract"] == contract_id  →  node = rel["authority"]
    │        │
    │        ├─ NOT FOUND ──▶ CLEAN REFUSAL: report what was searched
    │        │                (contract_id derived, N relationships scanned, 0 matched)
    │        │                — never an empty "affected: []" success
    │        │
    │        └─ FOUND (or contract_path IS already a bare node id — accepted directly
    │           per CONTEXT.md) ──▶ node resolved, continue
    │
    ├─3─▶ graph = compile_graph(cfg)          [compile.py:49]   (or use injected graph=)
    │        direct(graph, node)    [query.py:29]
    │        reverse(graph, node)   [query.py:39]
    │        transitive(graph, node)[query.py:55]
    │        — union of ids: {node} ∪ direct.ids ∪ reverse.ids ∪ transitive.ids
    │
    ├─4─▶ facts = effective_packages(cfg, facts)   [loader.py:205]
    │        dir_pkgs = [p for p in facts if "dir" in p]   (Phase-48 adapter filter, reused)
    │        for each affected node-id (a component/member id, NOT itself a path):
    │            resolve the OWNING SIDE's declared component record via components(cfg)
    │            (the node IS already a component/member id — no owning_package() path-walk
    │             needed for the node itself; owning_package() is for the CONTRACT's path)
    │        owning_package(dir_pkgs, contract_path) → package that owns the CONTRACT file itself
    │
    ├─5─▶ per-side owners: components(cfg) keyed by rel["authority"] / each dependent id
    │
    ▼
 deterministic dict: {contract, node, direct, reverse, transitive, owners, package} — all
 lists/sets sorted, no wall-clock, no float — byte-identical on repeat invocation
    │
    ▼
 rendered report (Claude's discretion on layout) ── OR ── clean-refusal message
```

### Recommended Project Structure
```
tools/contract_graph/
├── query.py         # unchanged — direct/reverse/transitive
├── compile.py        # unchanged — compile_graph
├── ownership.py       # unchanged — owning_package
├── impact.py          # NEW — the one module this phase adds (CONTEXT.md: "a new module in an
│                       #        existing package, so no new tools/ package is created")
└── tests/
    └── test_impact.py # NEW
harness/commands/
└── impact.md           # NEW — thin command file
```

### Pattern 1: Contract-path → node resolution (the one new algorithm)
**What:** Given a `contracts/**/<id>.schema.json` path (or a bare node id), find the graph node it
maps to.
**When to use:** Always, as `impact.py`'s first step — this has no existing implementation anywhere
in the codebase to reuse; it is genuinely new but genuinely small (a linear scan, no new data
structure).
**Example (uses the exact suffix-strip idiom `compile.py:46` already established for the same
purpose — contract-id-from-filename):**
```python
# Source: tools/contract_graph/compile.py:39-46 (the idiom to mirror, not to import — that
# function operates on a directory glob, not a single path)
def _tracked_schemas(contracts_dir: Path) -> set[str]:
    return {p.name.removesuffix(".schema.json") for p in contracts_dir.rglob("*.schema.json")}

# impact.py's own resolution step (new):
def _resolve_node(contract_path: str, cfg: dict) -> tuple[str, str] | None:
    """Return (node, contract_id) or None if unresolved."""
    candidate_id = Path(contract_path).name.removesuffix(".schema.json")
    for rel in effective_relationships(cfg):
        if rel["contract"] == candidate_id:
            return rel["authority"], candidate_id
    return None, candidate_id
```
Note: `contract_path` is accepted as EITHER a path under `contracts/` OR a bare node id (CONTEXT.md).
A bare node id has no `.schema.json` suffix to strip, so `_resolve_node` must also short-circuit:
if `contract_path` is itself a key or a value present in `graph["adjacency"]` (i.e. already a known
node), treat it as the node directly rather than trying contract-id resolution first.

### Pattern 2: No second traversal engine (falsifiable, per CONTEXT.md/MONO-08)
**What:** `impact.py` must literally call `direct`/`reverse`/`transitive` and MUST NOT contain its own
BFS/DFS/queue/stack/recursive walk.
**When to use:** Structural test, mirroring `tools/contract_graph/tests/test_query.py:71`
(`test_query_source_never_imports_task_evidence_plane`)'s source-scan idiom, and
`ownership.py`'s own Phase-47 self-proof (see `47-04-SUMMARY.md`: it greps its own source for
`direct|reverse|transitive` and asserts `0` hits, to prove it is NOT a second traversal engine).
Phase 49 needs the OPPOSITE assertion for `impact.py`: it MUST call these three names (so a
different test — "impact.py contains no `while`/`for` loop that mutates a frontier/visited set of
its own" is the true "no second engine" proof; merely grepping for the presence of `direct`/
`reverse`/`transitive` calls only proves reuse, not absence-of-reimplementation).
**Example test shape:**
```python
# Source: pattern mirrors tools/contract_graph/tests/test_query.py's own source-scan tests
def test_impact_module_calls_the_three_query_functions_and_defines_no_walk() -> None:
    src = Path("tools/contract_graph/impact.py").read_text(encoding="utf-8")
    assert "direct(" in src and "reverse(" in src and "transitive(" in src
    # Negative: no independent frontier/visited-set walk of impact.py's own.
    assert "frontier" not in src
    assert "visited" not in src
    # AST-level is stronger than substring: assert no local function in impact.py contains a
    # `while` loop (query.py's transitive() is the only worklist in the package; impact.py should
    # have none).
    import ast
    tree = ast.parse(src)
    while_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.While)]
    assert while_nodes == [], "impact.py defines its own iterative walk — a second traversal engine"
```

### Pattern 3: Package-side reuse — the exact Phase-48 adapter, not a re-derivation
**What:** Phase 48 discovered that `effective_packages()` can yield declared-only `[[components]]`
records with no `"dir"` key (`owning_package()` requires `"dir"` unconditionally and would raise a
bare `KeyError`). Phase 48's fix lives entirely inside `conventions_for()` — `ownership.py` itself
was deliberately left untouched.
**Where (verified, `tools/harness_config/loader.py:320-338`):**
```python
# Source: tools/harness_config/loader.py:320-338 (conventions_for's body — this IS the adapter to
# mirror; conventions_for() itself is NOT directly reusable for impact.py's purpose because it
# resolves ONE package for a PATH under that package's dir, whereas impact.py needs
# owning_package(dir_pkgs, contract_path) for the CONTRACT's own path — same filter, different call).
pkgs = effective_packages(cfg, facts)
for p in pkgs:
    if "dir" not in p and "manifest" in p:
        print(f"...malformed record...", file=sys.stderr)  # diagnostic, never silent drop
dir_pkgs = [p for p in pkgs if "dir" in p]
owner_id = owning_package(dir_pkgs, path)
```
**Answering the explicit question — can `impact.py` call `conventions_for()` or `effective_packages()`
instead of duplicating the filter?** `effective_packages()` — YES, call it directly (it is the
package-facts source `impact.py` needs). `conventions_for()` itself — NO, do not call it as a
black box: its signature takes a **path inside a package** and returns ONE package's convention
profile (test/format/bash_scope/agents_md) — a different question than "which package owns this
CONTRACT path, and what are the affected packages for this NODE." `impact.py` should import
`effective_packages` + `owning_package` directly and **replicate the 5-line `"dir"`-key filter
verbatim** (it is 5 lines, well short of "no second traversal engine" territory — the graph
traversal is the thing that must not be re-implemented, and a `dir`-key list-comprehension filter is
not a traversal engine). This is the one small, sanctioned duplication; `ownership.py` stays
untouched either way.

### Anti-Patterns to Avoid
- **Re-walking `graph["adjacency"]` by hand inside `impact.py`:** even a "just for display ordering"
  loop over `adjacency` risks becoming a de facto second traversal. All node-set computation must
  come from calling `direct`/`reverse`/`transitive`; `impact.py` may only iterate over the **outputs**
  of those calls (e.g. to attribute packages), never over `adjacency` itself.
- **Returning an empty-but-"success" report on an unresolved contract:** CONTEXT.md is explicit —
  this is "the dangerous failure mode for a pre-edit evidence step" (reads as "nothing is affected").
  The refusal path must be a visibly different shape (or at minimum an explicit `"resolved": false`
  field with a `"searched"` list), never structurally identical to a real empty-neighbourhood result
  (which IS legal — an isolated node with `direct.ids == []` is a true, correct answer per
  `query.py:33` and `test_query.py:109`'s `test_isolated_node_returns_empty_never_keyerror`). The
  report format must let a caller tell "resolved, genuinely isolated" apart from "could not resolve
  at all."
- **Modifying `ownership.py` or `compile.py` or `query.py`:** all three are explicitly "stays
  untouched" per CONTEXT.md; any diff to these files during this phase is a scope violation on the
  no-second-authority-plane rule.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Graph traversal (1-hop/reverse/transitive) | a BFS/DFS over `adjacency` inside `impact.py` | `query.py`'s `direct`/`reverse`/`transitive` | REQUIREMENTS.md forbids a second authority plane; MONO-08 names these exact functions. |
| Package ownership lookup | a new path-prefix matcher | `ownership.py`'s `owning_package()` | Already handles nearest-enclosing + deterministic tie-break + root fallback; CONTEXT.md: "stays untouched." |
| Package-facts source | re-parsing `.memory/derived/package-facts.md` | `tools.memory_regen.package_facts.build_facts()` via `effective_packages()` | `build_facts()` is the documented single public entry point (`47-02-SUMMARY.md`: "the single public entry point Phase 48/49 will import in-process — never re-parsing the rendered markdown"). |
| Declared-edge confirmation / owner name | a second config reader | `effective_relationships()` + `components()` | Same calls the current route block already names (`orchestrator.md:282`). |

**Key insight:** every "don't hand-roll" item here already has exactly one committed, tested,
documented implementation elsewhere in this repo; Phase 49's only genuinely original code is the
~10-line contract-path → node resolution function, because that specific join (contract id →
authority via `effective_relationships()`) has never been written before this phase.

## Common Pitfalls

### Pitfall 1: Treating a contract path as a graph node
**What goes wrong:** Calling `direct(graph, "contracts/sample/greeting.schema.json")` (or even
`direct(graph, "greeting")`) directly — the adjacency dict is keyed by **component/member id**
strings like `"source"`/`"parser"`, never by contract id or path. This silently returns
`{"ids": [], "paths": []}` (the isolated-node fallback, `query.py:33`) for EVERY contract, which is
indistinguishable from "correctly resolved, genuinely no dependents" — exactly the dangerous failure
mode CONTEXT.md warns about, except triggered by a resolution bug rather than a genuinely unknown
contract.
**Why it happens:** `rel["contract"]` (the schema id) and `rel["authority"]`/`rel["dependents"]`
(component/member ids, the actual node vocabulary) are easy to conflate because both are plain
strings and a relationship record mentions both.
**How to avoid:** Always resolve contract → node via `effective_relationships()` (Pattern 1) BEFORE
calling any `query.py` function. Never pass a value straight from `Path(contract_path).stem` into
`direct`/`reverse`/`transitive`.
**Warning signs:** A test that asserts `direct(graph, "some-contract-id")["ids"] == []` without first
asserting that `"some-contract-id"` is a genuine node in `graph["adjacency"]` is testing the wrong
thing — it will pass identically whether resolution is correct or entirely absent.

### Pitfall 2: Testing against the live tree and concluding traversal "works"
**What goes wrong:** `compile_graph()` on the core config returns `{"adjacency": {}, ...}` (verified
this session — CER-08 removed core `[pipeline].edges`; core `[contract_graph]` is empty). Every real
contract in this checkout hits clean-refusal. A test suite that only exercises the live tree will
ALWAYS take the refusal branch and never actually prove `direct`/`reverse`/`transitive` composition
works end-to-end inside `impact.py`.
**Why it happens:** It is tempting to test against `contracts/sample/greeting.schema.json` because it
already exists and is tracked — but it is not wired into any relationship in the core config.
**How to avoid:** Use synthetic `cfg` fixtures (mirroring `test_compile.py`'s domain-neutral
`{"components": [...], "contract_graph": {"relationships": [...]}}` shape, e.g. authorities `"a"`/
`"b"`/`"c"`, contract `"widget"`) to build a graph WITH edges, and inject it via `impact.py`'s
`cfg=`/`graph=` parameters, exactly like `owning_package()`'s and `conventions_for()`'s existing
injectable-pure-function convention.
**Warning signs:** A test suite for `impact.py` with zero references to a hand-built `cfg` dict or
`compile_graph(cfg)` call — everything running against the module-level default — has not actually
exercised the traversal path.

### Pitfall 3: Confusing "the node" with "the package that owns the contract FILE"
**What goes wrong:** After resolving `node = rel["authority"]` (a component id, e.g. `"parser"`),
calling `owning_package(dir_pkgs, node)` instead of `owning_package(dir_pkgs, contract_path)`.
`owning_package()` expects a **filesystem path** (it does `PurePosixPath(contract_path).parts`,
`ownership.py:47`) — passing a bare component id like `"parser"` produces a 1-part tuple that will
spuriously match ONLY the root package (`dir="."`always encloses a 1-segment path) or raise, silently
masking a real resolution bug.
**Why it happens:** Both "the node" and "the contract's owning package" answer an "ownership" flavored
question, inviting the same function to be reused for both without checking the argument type each
expects.
**How to avoid:** Two separate lookups: (a) `owning_package(dir_pkgs, contract_path)` — which package
directory contains the **contract schema file itself** (answers "who edits this contract"); (b) for
each node in the affected set, look up its declared component record via `components(cfg)` keyed by
id — which package/engineer owns that **pipeline stage** (answers "who implements this side of the
edge"). These are two different, both-needed pieces of information (CONTEXT.md: "the owning engineer
per side of the declared edge" AND "affected packages").
**Warning signs:** A single call site producing both "owning package" and "per-side owner" from the
same `owning_package()` invocation.

### Pitfall 4: `test_command_count_is_stable` / `test_command_names_are_stable` drift
**What goes wrong:** Adding `harness/commands/impact.md` without updating
`tools/harness_lint/tests/test_commands.py`'s `test_command_count_is_stable` (currently
`assert len(_command_files()) == 18`, `test_commands.py:99`) and `EXPECTED_COMMAND_NAMES`
(currently an 18-name frozenset NOT including `"impact"`, `test_commands.py:52-73`) fails CI/local
suite the instant the new file lands — by design (both tests are the Phase-48-built guard rails,
purpose-built to force exactly this update).
**Why it happens:** Easy to add the command file and the orchestrator wiring and forget the two
pinned-constant tests exist (they were added in Phase 48, a different phase, for a different command).
**How to avoid:** In the SAME commit/plan step that adds `harness/commands/impact.md`, change
`== 18` → `== 19` and add `"impact"` to `EXPECTED_COMMAND_NAMES`. CONTEXT.md explicitly calls this
"the guard working as designed, not an obstacle to route around."
**Warning signs:** `uv run pytest tools/harness_lint/tests/test_commands.py -x` failing after adding
the command file is the EXPECTED intermediate state, not a bug — the plan should include the constant
bump as an explicit step, not a surprise fix.

### Pitfall 5: SessionStart injector coupling
**What goes wrong:** Any temptation to add a pointer to `/impact` or contract-impact summaries into
`tools/memory_regen/inject.py`'s `assemble()` sections (agreements/banner/drift/contracts/repomap/
active) — even a one-line mention — violates MONO-09 ("no SessionStart injection") and criterion 3.
**Why it happens:** `inject.py`'s `_contracts_summary()` already reads `.memory/derived/
contracts-index.md`, and it can look like a natural place to also surface impact info.
**How to avoid:** Do not touch `tools/memory_regen/inject.py` at all in this phase. Verified this
session: `inject.assemble()` reads only `derived_dir`/`state_dir`/`agreements_dir` file contents and
`run_gate()` — it has zero code path that could reference commands, `contract_graph`, or `impact.py`
even indirectly, so the safest and simplest proof is "this file's diff is empty" plus the existing
determinism tests in `tools/memory_regen/tests/test_inject_determinism.py` staying green unmodified.
**Warning signs:** A diff touching `tools/memory_regen/inject.py`, `.claude/hooks/memory-inject.sh`,
or `harness/plugins/session-inject.ts` anywhere in this phase's commits.

## Code Examples

### Existing three-function shape (source: `tools/contract_graph/query.py:29-81`, verified)
```python
def direct(graph: dict, node: str) -> dict:
    ids = sorted(graph["adjacency"].get(node, []))
    return {"ids": ids, "paths": [[node, dep] for dep in ids]}
# reverse() and transitive() share this exact {"ids": [...], "paths": [...]} return shape.
```

### Existing compile_graph() call convention (source: `tools/contract_graph/compile.py:49-127`)
```python
graph = compile_graph()  # cfg=None -> loads harness/project.toml via load_project()
# graph == {"relationships": [...], "adjacency": {...}, "diagnostics": [...]}
```

### The exact inline one-liner `/impact` replaces (source: `harness/agents/orchestrator.md:281-283`)
```bash
uv run python -c "from tools.harness_config import components, effective_relationships; from tools.contract_graph import compile_graph, direct, reverse, transitive; graph = compile_graph(); node = 'NODE'; print(direct(graph, node)); print(reverse(graph, node)); print(transitive(graph, node)); print(effective_relationships()); print(components())"
```
This is the literal string to delete from the *Repository evidence* block (`contract-change` route,
`harness/agents/orchestrator.md` lines 274-296) and replace with a pointer to `/impact <contract>`.
The five-subsection structure (*When to use* / *Steps* / *Repository evidence* / *Stop condition* /
*Next command*, `orchestrator.md:75-76`) must survive unchanged — only the evidence block's CONTENT
changes, not the section headers or their order. `orchestrator.md`'s "A single-command form of this
block is planned; these calls are the interface it will preserve" sentence (present in all three
other routes, e.g. `orchestrator.md:147-148,191-192,238-239`, and again at `orchestrator.md:294-295`
for `contract-change`) is the standing forward-reference this phase discharges specifically for
`contract-change` — leave the sibling routes' identical sentences untouched (they still reference a
"planned" single-command form for THEIR OWN evidence blocks, which is out of this phase's scope).

### Thin command file shape to mirror (source: `harness/commands/component.md:1-8`, `lint.md:1-10`)
```markdown
---
description: >-
  Use when <trigger>. Invoke to <what it computes>.
agent: <persona-slug>
subtask: true
---

# /impact — <one-line>

<short prose>

!`uv run python -c "from tools.contract_graph.impact import report; print(report('$ARGUMENTS'))"`
```
Both example commands (`component.md`, `lint.md`) use `description` (routing paragraph containing
`"Use"`/`"when"` — required by `test_description_is_routing_signal`, `test_commands.py:126-137`),
`agent` (a well-formed lowercase-hyphen slug — `test_agent_field_well_formed`, `test_commands.py:
141-155`), and `subtask: true`. `agent:` should be `orchestrator` (mirrors `component.md`'s
`agent: orchestrator`) since `/impact` is invoked from within the `contract-change` route the
orchestrator owns, and per CONTEXT.md's discretion clause the CLI entry point may be either
`python -m tools.contract_graph.impact` or a bare function call — either satisfies "command file stays
thin."

## State of the Art

Not applicable — no external ecosystem drift to track; this is a pure internal composition phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `agent: orchestrator` is the correct persona for `impact.md` (vs. e.g. `python-engineer`) | Code Examples | Low — CONTEXT.md leaves function names/signatures/CLI-entry-point to discretion but does not explicitly name the `agent:` field; `orchestrator` is inferred from the command's role inside the orchestrator-owned `contract-change` route. If wrong, only the frontmatter `agent:` value needs a one-line change; `test_agent_field_well_formed` only checks slug well-formedness, not a specific value, so this would not be caught by an existing test. |

**If this table is empty:** N/A — see A1 above; everything else in this research is `[VERIFIED]` by
direct `Read`/execution of this checkout's own code in this session (no `[CITED]`/web sources — phase
scope is codebase-grounded only, no web search).

## Open Questions

1. **Should `impact.py`'s report distinguish "resolved to a node with zero neighbours in all three
   directions" from "resolved to a node, and it genuinely has some neighbours" in its rendered
   output, or is the raw `{"ids": [], "paths": []}` shape from each of `direct`/`reverse`/
   `transitive` sufficient?**
   - What we know: both are legitimate, both must render distinguishably from the CONTRACT-UNRESOLVED
     refusal case (Pitfall 1/CONTEXT.md).
   - What's unclear: whether the planner wants an explicit `"isolated": true` flag or whether
     "all three of direct/reverse/transitive returned an empty ids list, AND resolution itself
     succeeded (a `resolved: true` / `node: <id>` field is present)" is self-evidently enough
     distinction.
   - Recommendation: leave to Claude's discretion per CONTEXT.md ("the rendered layout ... provided
     it is deterministic") — but the PLAN should require a test asserting the refusal case and the
     genuinely-isolated case render as structurally different dict shapes (different top-level keys
     or an explicit boolean), not just different string content, so the distinction is machine-
     checkable, not just eyeball-checkable.

2. **Does `impact.py` need its own `cfg=None, graph=None, facts=None` injectable-pure-function
   signature (mirroring `owning_package`/`conventions_for`), or is `contract_path` the only
   parameter the command needs to pass?**
   - What we know: every reused function in this call chain (`compile_graph`, `effective_packages`,
     `conventions_for`) follows the "optional cfg/facts, defaults to the real repo" convention
     specifically so tests can inject synthetic fixtures without monkeypatching (Pitfall 2 above
     depends on this).
   - What's unclear: nothing structurally — this is a near-certain "yes, mirror the convention" —
     flagging only because CONTEXT.md explicitly leaves `impact.py`'s signature to discretion and the
     planner should make the injectable-params decision explicit in the plan rather than have it fall
     out implicitly during implementation.
   - Recommendation: adopt the injectable-pure-function convention; it is the only way Pitfall 2's
     test (traversal over a live-empty graph) becomes possible.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via `uv run pytest`) — `pyproject.toml:37-39`, `testpaths = ["libs/python", "tools"]` |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tools/contract_graph tools/harness_lint/tests/test_commands.py -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MONO-08 | `/impact` reports affected contracts (direct/reverse/transitive) via existing query functions, on a synthetic multi-hop fixture | unit | `uv run pytest tools/contract_graph/tests/test_impact.py -k traversal -x` | ❌ Wave 0 |
| MONO-08 | `/impact` reports affected packages via `owning_package()` + `effective_packages()` | unit | `uv run pytest tools/contract_graph/tests/test_impact.py -k package -x` | ❌ Wave 0 |
| MONO-08 | No second traversal engine (AST scan: no `while`/independent frontier in `impact.py`) | unit/structural | `uv run pytest tools/contract_graph/tests/test_impact.py -k no_second_engine -x` | ❌ Wave 0 |
| MONO-08 | Unknown/unmapped contract gets a clean, distinguishable refusal (never empty success) | unit | `uv run pytest tools/contract_graph/tests/test_impact.py -k refusal -x` | ❌ Wave 0 |
| MONO-08 | Output is byte-identical on repeat invocation (same graph + node) | unit | `uv run pytest tools/contract_graph/tests/test_impact.py -k determinism -x` | ❌ Wave 0 |
| MONO-09 | SessionStart injector output is byte-identical with/without this phase (no diff to `inject.py`) | regression | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py -q` (must stay green, unmodified) + `git diff --stat -- tools/memory_regen/inject.py harness/plugins/session-inject.ts .claude/hooks/memory-inject.sh` must be empty | ✅ (existing suite; this phase's job is to NOT need a new one) |
| MONO-09 | No CI job/hook references `/impact` | regression | `grep -rn "impact" .github/workflows/ci.yml` → 0 hits; `git diff --stat -- .github/workflows/ci.yml` empty from phase base commit | ✅ (grep, no new test file needed) |
| MONO-09 (surface accounting) | Command count 18 → 19, names include `impact` | regression | `uv run pytest tools/harness_lint/tests/test_commands.py -k "stable" -x` | ✅ exists, needs constant bump (`test_commands.py:99,52-73`) |
| Route wiring | `orchestrator.md`'s `contract-change` route names `/impact`, keeps 5 subsections, drops the inline one-liner | structural/manual | `grep -c "Repository evidence" harness/agents/orchestrator.md` == 4 (unchanged count across all 4 routes); `grep -n "uv run python -c.*direct(graph, node); print(reverse" harness/agents/orchestrator.md` → 0 hits (one-liner removed) | ❌ Wave 0 (new grep assertion, or a `test_orchestrator.py` addition if one exists — check at plan time) |
| Emit round-trip | New `impact.md` + edited `orchestrator.md` project cleanly to both runtimes, byte-clean | integration | `uv run python -m tools.harness_emit.generate` then `git status --porcelain .opencode .claude` twice in a row (idempotent) — mirrors `48-03-SUMMARY.md`'s verified idempotency check | ✅ pattern exists (Phase 48), apply to new files |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/contract_graph tools/harness_lint/tests/test_commands.py -q`
- **Per wave merge:** `uv run pytest -q` (full suite; confirm the pre-existing 923+ test baseline, per
  `48-03-SUMMARY.md`, only grows by the new `impact.py` tests and shrinks nowhere)
- **Phase gate:** Full suite green before `/gsd:verify-work`; additionally confirm
  `git diff --stat -- .github/workflows/ci.yml` is empty (no-growth gate check, MONO-09) and
  `git diff --stat -- tools/memory_regen/inject.py` is empty (injector-untouched proof).

### Wave 0 Gaps
- [ ] `tools/contract_graph/tests/test_impact.py` — covers MONO-08 (traversal reuse, package
      attribution, no-second-engine AST scan, refusal-vs-empty distinction, determinism)
- [ ] No new fixtures/conftest needed beyond what `test_compile.py`/`test_query.py` already establish
      as the domain-neutral synthetic-`cfg` idiom (copy the pattern inline; no shared fixture file
      exists today and creating one is not required by scope)
- [ ] Framework install: none — pytest is already the repo's sole test framework, already a dev
      dependency, no version change needed for this phase

## Environment Availability

Skipped — this phase has no external dependencies (code/config-only changes: one new Python module,
one new Markdown command file, one edited Markdown agent file, two edited test-constant literals).
`uv`/`pytest`/`python` are already required and present for the whole repo's existing suite; nothing
new is introduced.

## Security Domain

`security_enforcement` is not set in `.planning/config.json` — treated as enabled per instruction.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface — `/impact` is a local, on-demand read-only report over already-tracked repo files. |
| V3 Session Management | no | No session concept involved. |
| V4 Access Control | no | No new access boundary; `impact.py` reads the same config files every other `tools/contract_graph`/`tools/harness_config` module already reads with the same repo-local trust level. |
| V5 Input Validation | yes | `contract_path` (a CLI argument, effectively user/agent-supplied) must be validated before use: (a) never used to construct a filesystem path that escapes the repo (mirrors `_nearest_agents_md`'s bounded-walk pattern, `loader.py:258-293`, which explicitly guards a relative-escaping or absolute `dir_` value with `candidate.relative_to(_REPO_ROOT)` before any filesystem touch); (b) an unresolvable value produces the clean-refusal path, never a raw exception/traceback surfaced to the user, and never a fabricated "found" result. |
| V6 Cryptography | no | No cryptographic operation in this phase. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via a crafted `contract_path` argument (e.g. `../../../etc/passwd` or an absolute path) reaching a filesystem read | Tampering / Information Disclosure | `impact.py` should validate `contract_path` the same way `_nearest_agents_md` validates `dir_` (`loader.py:258-293`) — resolve, then `relative_to(_REPO_ROOT)` (or simply never open the path at all: the resolution step only needs the **filename**, `Path(contract_path).name.removesuffix(".schema.json")`, and never reads the file's contents — so there is no read to protect in the common case; only guard if a future variant adds file-content inspection). |
| Command injection via `$ARGUMENTS` interpolated into a shell one-liner in `impact.md` | Tampering | Mirror `component.md`'s existing `python -c` pattern, which already passes `$ARGUMENTS` as a Python string literal inside a `-c` script (same risk class as the existing `lint.md`/`component.md` commands, not a new one this phase introduces) — do not widen the shell surface beyond what those two already-shipped commands use. |
| A malformed/adversarial `[[contract_graph.relationships]]` config record causing `impact.py` to raise an unhandled exception instead of a clean refusal | Denial of Service (of the evidence step, not the repo) | `effective_relationships()` already raises `ValueError` with a diagnostic message on the three documented malformed-config shapes (`loader.py:95-202`) — `impact.py` should let that propagate as-is (it is already a loud, diagnosable failure, not a silent one) rather than swallowing it into a fake "resolved" result. |

## Sources

### Primary (HIGH confidence — direct `Read`/execution in this session, 2026-07-30)
- `tools/contract_graph/query.py` — full file read; `direct`/`reverse`/`transitive` signatures and
  docstrings, lines 29-81
- `tools/contract_graph/compile.py` — full file read; `compile_graph()` signature/behavior, lines
  49-127; `_tracked_schemas` idiom, lines 39-46
- `tools/contract_graph/ownership.py` — full file read; `owning_package()` signature/behavior, lines
  28-65
- `tools/contract_graph/__init__.py` — lazy PEP 562 re-export dict, lines 1-40
- `tools/harness_config/loader.py` — full file read; `effective_relationships`, `components`,
  `effective_packages`, `conventions_for`, `_nearest_agents_md`, lines 1-360
- `harness/agents/orchestrator.md` — full file read; the `contract-change` route and its evidence
  block, lines 246-302, and the sibling routes' identical "single-command form is planned" sentences
- `harness/commands/component.md`, `harness/commands/lint.md` — full files read; thin-command shape
- `tools/harness_lint/tests/test_commands.py` — full file read; `test_command_count_is_stable`
  (line 92-99, literal `18`), `test_command_names_are_stable` (line 102-115, `EXPECTED_COMMAND_NAMES`
  frozenset lines 52-73)
- `tools/harness_emit/generate.py` — `iter_commands` (lines 157-169), `emit()` command-plan wiring
  (lines 349-354, 386-396) — glob-driven, no per-command code change needed for a new file
- `tools/harness_emit/project_command.py` — full file read; opencode vs Claude frontmatter projection
- `tools/memory_regen/inject.py` — full file read; `assemble()` has zero coupling to commands/
  contract_graph
- `tools/memory_regen/tests/test_inject_determinism.py` — full file read; existing determinism/
  snapshot tests to keep green unmodified
- `tools/contract_graph/tests/test_compile.py`, `test_query.py` — grep'd for domain-neutral fixture
  idiom (`"a"`/`"b"`/`"widget"` names) and existing test function names
- `.planning/phases/47-package-facts/47-02-SUMMARY.md`, `47-04-SUMMARY.md` — `build_facts()` as
  single public entry point; `owning_package()`'s deliberate untouched-by-anything posture
- `.planning/phases/48-convention-profiles/48-01-SUMMARY.md`, `48-03-SUMMARY.md` — the dir-key
  adapter filter's exact rationale and location; command-count-stable test's origin and mutation-proof
- Live execution: `uv run python -c "from tools.contract_graph.compile import compile_graph; ..."` —
  confirmed `compile_graph()` on the default config returns empty adjacency/relationships/diagnostics
- Live execution: `git ls-files` / `find` — confirmed 6 tracked `contracts/**.schema.json` files in
  this checkout
- `.planning/config.json` — confirmed `workflow.nyquist_validation: true` (Validation Architecture
  section required) and `mode: yolo`/`granularity: standard`

### Secondary / Tertiary
None — phase scope explicitly excludes web search; all findings are Primary/HIGH.

## Metadata

**Confidence breakdown:**
- Standard stack (existing functions to reuse): HIGH — every signature verified by direct file read.
- Architecture (contract→node resolution): HIGH — verified against `compile.py`'s own suffix-strip
  idiom and confirmed empty-graph behavior by live execution.
- Pitfalls: HIGH — each pitfall traced to a specific, cited line range or a live-executed fact.

**Research date:** 2026-07-30
**Valid until:** No expiry driver — this is a closed-codebase research pass with no external
dependency; stays valid until the cited line numbers/functions themselves change (i.e., effectively
until this phase lands, since nothing else in the roadmap touches these files before Phase 49).
