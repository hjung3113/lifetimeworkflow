# Phase 25: Graph Compiler, Queries, Conductor, Proof - Research

**Researched:** 2026-07-19
**Domain:** Deterministic graph compilation over an existing config-loader vocabulary; static-analysis consistency gate; cycle-safe graph queries; conductor-surface text generalization; ADR authoring.
**Confidence:** HIGH (all findings grounded in code actually read in this repo — no external library research needed; this phase is 100% internal composition over Phase-24 primitives)

## Summary

Phase 25 is pure composition over what Phase 24 already shipped: `tools/harness_config/loader.py::effective_relationships()` already produces a stable-sorted, deduped list of `{id, contract, authority, dependents}` records for both project and workspace configs — lowering legacy `[pipeline].edges` and unioning explicit `[[contract_graph.relationships]]` rows, raising `ValueError` on the three failure modes. Phase 25 does **not** touch that function's lowering/union logic; it builds a resolution/validation layer *on top* (the compiler + gate), a read-only traversal layer *beside* it (the queries), and edits three prose surfaces (`/pipeline`, `pipeline-map`, `orchestrator.md`) to consume the compiled result instead of the raw `[[components]]`/`[pipeline]` passthrough they read today.

The single highest-risk item is **not** the compiler or queries — both are new, greenfield, and low-risk-to-get-right. It is **TOPO-06's byte-identity requirement**: the existing linear render in `pipeline.md`/`pipeline-map/SKILL.md` (documented literally as "stage N: id (lang) consumes=... produces=..." and "from -> to (contract)") must survive verbatim when the underlying data is still linear, while the SAME render logic must also produce D-01's indented tree for non-linear graphs. Because there is no test today asserting the *exact rendered string* (only structural prose-token tests — `test_orchestrator_topology.py`, "trace the topology" / "stage" / "component" substring checks), "byte-identical" here is a documentation/agent-prose consistency requirement, not a golden-file diff — the planner must decide exactly what artifact proves "unchanged" (see Pitfalls).

**Primary recommendation:** Add ONE new `tools/contract_graph/` package (not folded into `harness_config`) containing `compile.py` (the compiler: resolve + validate → `CompiledGraph` dict of `{relationships, adjacency}`), and `query.py` (direct/reverse/transitive queries over the compiled adjacency, `{ids, paths}` shape, visited-set cycle guard). Wire the new `harness_lint` gate as `tools/harness_lint/tests/test_contract_graph_config.py`, mirroring `test_pipeline_config.py`'s structural-scan idiom exactly. Edit the three conductor-surface `.md` files minimally (add a step that resolves `effective_relationships()`+renders D-01's indented tree when the graph is non-linear; keep the existing linear stage/edge print path as the default render for the still-linear core/instance fixture) and re-run `tools.harness_emit` once at the end.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Graph compilation (resolve + validate) | Tooling / static-analysis (`tools/contract_graph`) | Config-loader (`tools/harness_config`, `tools/workspace_config`) | Compiler consumes loader output; loader stays pure-data passthrough (TOPO-02 invariant preserved) |
| Consistency gate (diagnostics) | Tooling / CI gate (`tools/harness_lint`) | Compiler (`tools/contract_graph`) | Gate is a pytest suite over compiler output, mirroring existing `test_pipeline_config.py`/`test_workspace_config.py` — not a new CLI |
| Authority-owned-contract resolution | Tooling (`tools/contract_drift`) reused | Compiler | Compiler calls into `contract_drift`'s schema-existence resolution (schema glob under `contracts/**`), not a new checker |
| Affected-set queries | Tooling (`tools/contract_graph`) | — | Pure function over compiled adjacency; no persistence, no task-evidence side effect (D-03) |
| Conductor rendering | Agent/skill/command prose (`harness/agents/orchestrator.md`, `harness/commands/pipeline.md`, `harness/skills/pipeline-map/SKILL.md`) | Compiler + queries | Prose surfaces consume compiled/queried data; they do not re-implement resolution or traversal |
| Runtime projection (opencode + Claude) | Emitter (`tools/harness_emit`) | — | Existing glob-discovery emitter re-run with zero code changes (Phase-24 precedent: "ZERO emitter code change" for new source content) |
| Decision record | Human-ratified `docs/adr/0009-*.md` | — | Constitution plane; CODEOWNERS-gated append |

## User Constraints (from CONTEXT.md)

<user_constraints>
### Locked Decisions

- **D-01 (conductor rendering):** `/pipeline` and `pipeline-map` render the graph as an **indented tree** rooted at authority endpoints descending to dependents. A cycle is rendered with an explicit terminal marker (e.g. `(cycle → <node>)`) rather than recursing. The existing linear topology output stays byte-identical (TOPO-06 hard requirement). NOT edge-list, NOT adjacency-map for the human-facing surface (an adjacency structure may still exist internally for queries — see D-03).
- **D-02 (gate diagnostics):** Diagnostics are **descriptive, grep-able slugs** (e.g. `unresolved-authority`, `dangling-endpoint`, `unknown-contract`), matching the existing `harness_lint` gate convention (GEN-04, POLY-01, GEN-03). Stable across runs. NOT numbered `TOPO-C001`-style codes.
- **D-03 (query output shape):** Queries return **sorted ids AND the connecting path(s)** — not ids alone. Cycle-safe via a visited-set so traversal terminates on legal cycles. Deterministic ordering. Queries create **no new task-evidence requirement** and **do not preload contract bodies** (TOPO-05 invariant).
- **D-04 (ADR-0009 scope):** ADR-0009 records the **full model landed this phase**: the record/graph model + the affected-set query semantics + the conductor rendering contract, as ONE ratified unit. ADR-0009 was reserved but NOT created in Phase 24 — authored and human-ratified HERE.
- **Carried forward from Phase 24 (do not re-decide):** Namespaced lowered ids `pipeline/<contract>/<from>-><to>`; endpoints are **opaque strings** (no `split_endpoint`, no `repo:stage` parsing at the vocabulary layer — but endpoint RESOLUTION against declared components/members IS TOPO-04's new job this phase). `effective_relationships()` is the single lowering+union path; stable sort-by-id; raises `ValueError` on duplicate id / duplicate semantic edge / contradiction.

### Claude's Discretion

- Compiler module location (extend `tools/harness_config/` vs a new `tools/contract_graph/` module) — **researcher recommends new `tools/contract_graph/`** (see Standard Stack rationale below).
- Internal graph data structure (adjacency map is fine internally even though D-01 fixes the human-facing render).
- Exact slug spellings, and query function signatures — provided outputs are deterministic and repo-confined.
- Exact indented-tree glyphs and the cycle-marker wording, provided the existing linear output is byte-identical.

### Deferred Ideas (OUT OF SCOPE)

- Brownfield adoption (ADOPT-*) — Phases 26–27.
- Living Docs (DOCSUP-*) — Phases 28–29 (consume this phase's affected-set queries for graph-impact reports).
- Version/semver compatibility engine, topology runtime/broker, second orchestrator, impact-driven task-evidence policy — OUT of scope for v2.3. D-03 explicitly forbids the query layer from creating task-evidence requirements.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TOPO-04 | Domain-neutral compiler + `harness_lint` gate: stably-ordered repo-confined graph data + stable diagnostic slugs; validates endpoints + authority-owned-contract resolution; accepts fan-in/fan-out/disconnected/canonical cycles. | See "Compiler" + "Consistency Gate" sections below; reuses `effective_relationships()` (loader.py:90–176) for the record list and `contract_drift`-style schema-glob resolution (drift.py / test_pipeline_config.py:73–88 / test_workspace_config.py:74–105) for authority-owned-contract existence. |
| TOPO-05 | Direct/reverse/transitive affected-set queries, cycle-terminating, `{ids, paths}` shape, no task-evidence, no contract-body preload. | See "Affected-set queries" section; visited-set BFS/DFS pattern, pure function over compiled adjacency. |
| TOPO-06 | Generalize `/pipeline`, `pipeline-map`, `orchestrator.md` to consume canonical graph; preserve linear byte-identity; render branches/cycles (D-01); round-trip byte-identical; no new command/persona. | See "Conductor generalization" section; existing files read verbatim (pipeline.md, pipeline-map/SKILL.md, orchestrator.md) plus `tools/harness_emit/generate.py` round-trip mechanics. |
| TOPO-07 | Generic non-linear proof fixtures (fan-out, request/response separate records, event fan-out, legal cycle, cross-repo authority); log-parser instance unchanged; GEN-04 green; human-ratified ADR-0009. | See "Proof fixtures" + "ADR-0009" sections; GEN-04 guard mechanics (`test_core_no_example_dep.py`) and Phase-24 non-contiguous-path precedent (`test_topology_relationships.py` per 24-02-SUMMARY.md). |
</phase_requirements>

## Standard Stack

### Core

| Component | Location | Purpose | Why Standard (this repo's convention) |
|-----------|----------|---------|----------------------------------------|
| `tools/contract_graph/` (NEW package) | new `tools/*` uv member | Compiler (`compile.py`) + queries (`query.py`) | Mirrors the existing `tools/contract_drift`, `tools/workspace_config`, `tools/harness_config` one-module-per-concern layout; a "compiler + queries" concern is distinct enough from "config loading" to warrant its own package rather than bloating `harness_config` (which Phase 24 explicitly kept as "raw passthrough... no validation/traversal/discovery/policy" — D-03 in 24-CONTEXT). Putting resolution logic in `harness_config` would violate that already-ratified boundary. |
| `tools/harness_lint/tests/test_contract_graph_config.py` (NEW) | new gate test file | Consistency gate | Exact structural-scan idiom already used by `test_pipeline_config.py` / `test_workspace_config.py` (repo-root via `parents[3]`, load via shared loader, iterate/assert/fail-loud). No new gate *mechanism* — same pytest suite pattern the CI `gate` job already runs. |
| stdlib only (`json`, `pathlib`) | — | All graph/query logic | Every existing `tools/*` module here (loader.py, drift.py, workspace_config) is stdlib-only; no new dependency needed for compilation/traversal over an already-parsed list of dicts. |

**No new third-party packages required.** This phase is glue/logic over existing stdlib-parsed TOML + JSON Schema data — there is nothing to install, so the Package Legitimacy Audit below is empty by design.

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `tools/contract_drift/drift.py` glob pattern (`{p.name.removesuffix(".schema.json") for p in dir.rglob("*.schema.json")}`) | Authority-owned-contract existence check | Reuse the EXACT pattern already used three times in this repo (`test_pipeline_config.py:82`, `test_workspace_config.py:97-99`, `drift.py` `workspace_drift` at line 281-284) rather than inventing a fourth. This is "reuse drift" per the CONTEXT canonical refs — not `drift.run_gate` itself (which diffs hashes), but the same schema-existence resolution idiom drift's workspace-edge check already established. |
| `tools/workspace_config/loader.py::split_endpoint` | Cross-repo authority resolution (repo:stage) | TOPO-04 fixture #5 ("cross-repo authority resolution") — reuse `split_endpoint` to resolve a `repo:stage` authority endpoint against declared `[[members]]`, exactly as `test_workspace_config.py::test_edge_contracts_tracked_in_producer` already does for legacy edges. |
| `tools/harness_lint/__init__.py::parse_frontmatter` | Read `orchestrator.md`/command/skill frontmatter in tests | Already used by `test_orchestrator_topology.py`; any new prose-token gate test for the conductor edits should reuse it rather than hand-slicing `---` fences. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `tools/contract_graph/` package | Extend `tools/harness_config/` in place | Rejected: Phase 24 explicitly ratified `harness_config` accessors as policy-free raw passthrough (D-03, "NO validation, traversal, discovery, or policy"). Adding compiler/resolution logic there would silently re-scope an already-shipped, tested module and risk regressing its "raw passthrough" test coverage. A sibling package keeps the boundary Phase 24 drew intact. |
| Reusing `contract_drift.run_gate`/hash machinery directly for authority-owned-contract check | Writing a bespoke existence check | The existing drift machinery answers "did the schema BYTES change since baseline", not "does a schema file exist for this contract id". The correct reuse target is the **existence-glob idiom** already duplicated 3x in this repo (not `run_gate`) — recommend extracting it once into a small shared helper `tools/contract_drift/existence.py` (or leave duplicated a 4th time, consistent with `IN-01` in 24-REVIEW.md which already accepts duplication as the established convention here). Planner's call; either is consistent with existing patterns. |
| BFS-based transitive query with explicit visited-set | Recursive DFS with a decorator-based memoization (`functools.lru_cache`) | Recursion depth on a legal cycle risks `RecursionError` on pathological inputs and is harder to reason about for path-collection; an explicit worklist/visited-set loop (iterative BFS or DFS) is the standard cycle-safe traversal and trivially proves termination (frontier shrinks — visited only grows, graph is finite). |

## Package Legitimacy Audit

No external packages are installed by this phase — the compiler, gate, and queries are pure Python stdlib logic over already-parsed config dicts and JSON Schema files already tracked in this repo. Package Legitimacy Gate is **not applicable**.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| — none — | — | — | — | — | — | N/A — no installs this phase |

**Packages removed due to slopcheck [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```
harness/project.toml, workspace.toml, examples/log-parser/project.toml   (TOML config, human/instance-authored)
        │
        ▼
tools.harness_config / tools.workspace_config
  .effective_relationships(cfg) ──────► [ {id, contract, authority, dependents}, ... ]   (Phase 24, UNCHANGED)
        │
        ▼
tools.contract_graph.compile  (NEW — Phase 25)
  ├─ resolve authority/dependent endpoints against declared [[components]] / [[members]]
  ├─ resolve authority-owned contract existence (reuse contract_drift-style schema glob)
  ├─ build adjacency map: authority -> [dependent, ...]  (internal structure, D-03-sanctioned)
  ├─ validate: dangling endpoint / unresolved authority / unknown contract
  │       └─ on failure: raise/collect descriptive slug diagnostics (D-02)
  └─ on success: return CompiledGraph { relationships (sorted), adjacency (sorted) }
        │
        ├──────────────► tools.harness_lint.tests.test_contract_graph_config  (NEW gate)
        │                    asserts zero diagnostics on the core/instance default configs;
        │                    positive fixtures prove fan-in/fan-out/disconnected/cycle ACCEPTED;
        │                    negative fixtures prove each slug fires exactly once
        │
        └──────────────► tools.contract_graph.query  (NEW — Phase 25)
                              direct(id) / reverse(id) / transitive(id)
                              → { ids: [...sorted], paths: [[...]] }, visited-set cycle-safe
                                    │
                                    ▼
                    ┌───────────────┴────────────────┐
                    ▼                                ▼
      harness/agents/orchestrator.md         harness/commands/pipeline.md
      (routes using affected-set on a        harness/skills/pipeline-map/SKILL.md
       contract/component change)            (render: D-01 indented tree,
                                               linear case renders byte-identical
                                               to today's stage/edge print)
                    │
                    ▼
      tools.harness_emit  (re-run, ZERO code change — glob discovery)
                    │
        ┌───────────┴────────────┐
        ▼                        ▼
   .opencode/                .claude/
   (agent/command/skill,     (agent/command/skill,
    byte-identical re-emit)   byte-identical re-emit)
```

### Recommended Project Structure

```
tools/
├── contract_graph/                    # NEW package (Phase 25)
│   ├── __init__.py                    # PEP 562 lazy re-export, mirrors harness_config/__init__.py
│   ├── compile.py                     # compile(cfg) -> CompiledGraph; validate(); diagnostics
│   ├── query.py                       # direct()/reverse()/transitive() over CompiledGraph
│   ├── pyproject.toml                 # uv workspace member (package=false, mirrors harness_config)
│   └── tests/
│       ├── fixtures/
│       │   └── graphs/
│       │       ├── valid/cases.json       # fan-in, fan-out, disconnected, canonical-cycle, cross-repo
│       │       └── negative/cases.json    # dangling-endpoint, unresolved-authority, unknown-contract
│       ├── test_compile.py
│       └── test_query.py
tools/harness_lint/tests/
└── test_contract_graph_config.py      # NEW gate — mirrors test_pipeline_config.py idiom
docs/adr/
└── 0009-<slug>.md                     # NEW — human-ratified (D-04)
```

### Pattern 1: Compiler as validate-then-return, never raise-and-crash on caller-facing paths

**What:** The compiler (`tools/contract_graph/compile.py`) should return a result object/dict carrying BOTH the compiled graph AND a `diagnostics: list[str]` field (slugs), rather than raising exceptions for gate-detectable conditions. Exceptions are reserved for genuinely-malformed input (mirroring `effective_relationships()`'s existing `ValueError` raises for its three failure modes, which the compiler calls first and lets propagate).

**When to use:** The gate test (`test_contract_graph_config.py`) needs to assert "the default config compiles with zero diagnostics" (positive) AND "this malformed fixture produces diagnostic X" (negative) — a raise-only design makes the negative-fixture assertions awkward (`pytest.raises` per slug) whereas a `diagnostics` list lets one test iterate all expected slugs cleanly, matching how `contract_drift.run_gate` already returns `{"ok": bool, "drifted": [...]}` rather than raising.

**Example:**
```python
# Source: pattern observed in tools/contract_drift/drift.py:177-216 (run_gate returns a result dict,
# never raises, for exactly this reason — the CLI and the gate test both need to enumerate findings).
def compile_graph(cfg: dict | None = None) -> dict:
    """Compile effective_relationships() into a validated, repo-confined graph.

    Returns {"relationships": [...sorted by id...], "adjacency": {authority: [sorted dependents]},
    "diagnostics": [...sorted descriptive slugs...]}. diagnostics is empty iff every endpoint
    resolves and every authority owns a tracked contract. Fan-in/fan-out/disconnected components/
    canonical cycles are all structurally legal and never appear in diagnostics.
    """
    rels = effective_relationships(cfg)  # Phase-24 function; ValueError propagates unchanged
    ...
```

### Pattern 2: Cycle-safe visited-set traversal for transitive queries

**What:** Iterative BFS/DFS with an explicit `visited: set[str]` that is checked BEFORE enqueueing a node's neighbors, guaranteeing termination on a legal cycle (D-01's `(cycle → <node>)` marker and D-03's cycle-safety are the SAME underlying guarantee, applied to render vs. query respectively).

**When to use:** Both `query.transitive()` (TOPO-05) and the conductor's indented-tree renderer (TOPO-06/D-01) need this exact guard — implement it once in `tools/contract_graph/query.py` (e.g. `_walk(adjacency, start, visited=None)` generator) and have BOTH the query functions and (if the render logic is centralized in Python rather than pure prose) the tree-render helper reuse it, rather than writing the cycle guard twice.

**Example:**
```python
# Pattern (not sourced from an existing file — this is new Phase-25 logic; iterative worklist
# is the standard cycle-safe graph-traversal idiom, not tied to any specific library).
def transitive(adjacency: dict[str, list[str]], start: str) -> dict:
    visited: set[str] = {start}
    paths: dict[str, list[str]] = {start: [start]}
    frontier = [start]
    while frontier:
        node = frontier.pop(0)
        for nxt in adjacency.get(node, []):
            if nxt in visited:
                continue  # cycle terminus — do not re-enqueue, do not recurse
            visited.add(nxt)
            paths[nxt] = paths[node] + [nxt]
            frontier.append(nxt)
    ids = sorted(visited - {start})
    return {"ids": ids, "paths": [paths[i] for i in ids]}
```

### Anti-Patterns to Avoid

- **Re-implementing `effective_relationships()`'s lowering/union inside the compiler:** the compiler must call the existing function and treat its output as the sole input — any parallel TOML-reading or edge-lowering logic inside `tools/contract_graph` duplicates Phase-24's ratified single-path guarantee (TOPO-03) and risks silent divergence between "what the compiler sees" and "what `/pipeline` reads directly".
- **Changing `effective_relationships()`'s signature or return shape:** downstream Phase 24 tests (`test_topology_relationships.py`) and this phase's compiler both depend on the exact `{id, contract, authority, dependents}` dict shape; a signature change here is an unreviewed breaking change to already-shipped, tested code.
- **A second graph interpreter in the conductor prose:** `/pipeline`, `pipeline-map`, and `orchestrator.md` must describe reading the SAME compiled/queried output — not re-describe raw `effective_relationships()`/adjacency construction independently in prose (that would create the "second interpreter" TOPO-06 explicitly forbids).
- **A new command or persona for graph queries:** the scoping is explicit — "no new graph command or persona" (TOPO-06). Affected-set queries surface through the EXISTING `/pipeline` command and `orchestrator.md` intake step, never a new `/graph-query` command or a `graph-analyst` persona.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Legacy-edge lowering + union + dedup | A second lowering function in the compiler | `tools.harness_config.effective_relationships()` (loader.py:90-176) | Already ships stable-sort, 3-failure-mode taxonomy, cfg-agnostic (works for both `load_project()` and `load_workspace()` output). Re-implementing risks drift from the ratified Phase-24 semantics. |
| Contract-existence check | A bespoke schema-existence scanner | The glob idiom already used 3x: `{p.name.removesuffix(".schema.json") for p in dir.rglob("*.schema.json")}` (`test_pipeline_config.py:82`, `test_workspace_config.py:97-99`, `drift.py:281-284`) | Reuse "don't fork" per CONTEXT canonical refs — this is literally the drift-adjacent existence check already established, not a new concept. |
| Cross-repo (repo:stage) endpoint parsing | A new parser for `authority`/`dependent` endpoint strings | `tools.workspace_config.split_endpoint()` | Already handles `repo:stage` → `(repo, stage)` and bare `stage` → `(None, stage)`; this is the exact shape TOPO-04's "cross-repo authority resolution" fixture needs. |
| Frontmatter parsing for any new conductor-surface test | Hand-sliced `---` fence splitting | `tools.harness_lint.parse_frontmatter` | Already the shared idiom (`test_orchestrator_topology.py:27`, `test_commands.py`); avoids a second frontmatter parser. |
| Runtime projection to `.opencode/`+`.claude/` | Manual copy/edit of the two runtime trees | `python -m tools.harness_emit` (glob discovery — zero code change needed per Phase-24/Phase-10 precedent) | The emitter already discovers new/changed `harness/{agents,commands,skills}/**` content by glob; every prior phase that edited conductor-surface `.md` files re-ran the SAME emitter unchanged (10-03, 15-01 summaries: "ZERO emitter code change"). |

**Key insight:** Every "don't hand-roll" item above is not a third-party library avoidance — it's an *intra-repo* reuse discipline. This phase's entire risk surface is accidentally re-implementing something Phase 24 (or an earlier phase) already built and tested, because the new compiler/gate/queries sit directly on top of that machinery.

## Common Pitfalls

### Pitfall 1: Breaking the linear render's byte-identity while adding the D-01 indented-tree path

**What goes wrong:** Editing `pipeline.md`/`pipeline-map/SKILL.md` to describe "read the compiled graph, render as an indented tree" naturally tempts rewriting the ENTIRE render section, including the existing linear stage-list/edge-chain steps 2–3 in `pipeline.md` (currently: `stage <n>: <id> (<lang>) consumes=[...] produces=[...]` and `<from> -> <to> (<contract>)`).
**Why it happens:** The two render modes (linear print vs. indented tree) look similar enough that a single edit pass may "unify" them into one new format, silently changing the linear output.
**How to avoid:** Treat the indented-tree render as an ADDITIONAL section/step describing the general (branching/cyclic) case, and explicitly keep the existing linear print steps verbatim as what happens when the compiled graph IS a single chain (fan-out=1 everywhere, no branch). Since there is no golden-file test asserting the exact rendered string today, the planner must define what "byte-identical" is checked against — recommend either (a) a new fixture-driven test asserting the exact printed lines for the core two-stage `source→sink` topology, or (b) explicitly documenting in the plan that "byte-identical" is verified by manual diff of the prose file's linear-case section (git diff on `pipeline.md`/`SKILL.md` showing the linear steps' TEXT unchanged) since no render code executes today — these are Markdown *instructions* for an agent to follow, not a runnable function.
**Warning signs:** Any edit to `pipeline.md`/`pipeline-map/SKILL.md` that touches the numbered example blocks under "For the core default this reads:" — those exact lines are the closest thing to a byte-identity target in this repo.

### Pitfall 2: Changing `effective_relationships()` or `contract_graph_relationships()` signatures

**What goes wrong:** Adding a `resolved=True` kwarg or similar to loader.py "for convenience" breaks the Phase-24 contract that these functions stay raw-passthrough/pure-lowering with stable signatures (documented explicitly: "the compiler/queries consume THIS, signatures stay stable").
**Why it happens:** It can feel natural to thread compiler options through the loader while touching the same file.
**How to avoid:** All compiler logic lives in `tools/contract_graph/`, importing `effective_relationships` and `contract_graph_relationships` unchanged. Do not edit `tools/harness_config/loader.py` or `tools/workspace_config/loader.py` in this phase except possibly to fix WR-02 (bare `KeyError` → `ValueError`) if the planner chooses to close it — and even then, only add a guard, never change the return shape or add parameters.

### Pitfall 3: A query recursing forever (or exhausting `RecursionError`) on a legal cycle

**What goes wrong:** A naive recursive `transitive(node)` that calls itself on every dependent without a visited-set check infinite-loops (or stack-overflows) on the TOPO-07 "one legal cycle" fixture — precisely the case D-03 requires the queries to terminate on.
**Why it happens:** Recursive graph traversal is the natural first draft; the visited-set guard is easy to omit when hand-writing a quick DFS.
**How to avoid:** Use the iterative worklist pattern in Pattern 2 above; write the "legal cycle" fixture FIRST (TDD) so any recursive draft fails loudly (timeout/RecursionError) before the visited-set guard is added.

### Pitfall 4: Compiler re-implementing lowering/union instead of consuming `effective_relationships()`

**What goes wrong:** Since the compiler needs "endpoint resolution against declared components/members" (new this phase) it might seem simplest to re-read `[pipeline].edges` + `[[contract_graph.relationships]]` directly and re-derive authority/dependents inline, rather than calling `effective_relationships()`.
**Why it happens:** The compiler needs MORE information (component/member declarations) than `effective_relationships()` returns, so it's tempting to bypass the loader function and read the raw config sections directly "since we're already reading the config for components anyway."
**How to avoid:** Call `effective_relationships(cfg)` for the relationship list, and separately call `components(cfg)`/`languages(cfg)` (or `members(cfg)` for workspace) for the endpoint-declaration set — two independent reads of the SAME loaded `cfg`, never a re-derivation of relationships from raw edges.

### Pitfall 5: Accidentally creating a new command or persona

**What goes wrong:** It's tempting to add `/graph-query` as a dedicated entry point for TOPO-05's affected-set queries, or a `graph-analyst` persona to "own" the compiler.
**Why it happens:** The queries are genuinely new capability; giving them their own surface feels like good UX.
**How to avoid:** TOPO-06 and the v2.3 scoping FINAL §4 ("No second orchestrator, router, graph command, or specialist persona") are explicit and non-negotiable. Affected-set queries are exposed only as (a) a Python API other tooling/agents call, and (b) prose additions to the EXISTING `/pipeline` command and `orchestrator.md` routing table (e.g. a new routing-table ROW, not a new persona column).

### Pitfall 6: The emit round-trip drifting because a conductor-surface edit isn't re-emitted

**What goes wrong:** Editing `harness/commands/pipeline.md`, `harness/skills/pipeline-map/SKILL.md`, or `harness/agents/orchestrator.md` without re-running `python -m tools.harness_emit` leaves `.opencode/` and `.claude/` stale — exactly the Phase-13/14/15 "gate-theft" bug documented in STATE.md ("`test_projected_tree_matches_committed_snapshot` ... someone updated the `.ambr` and stole this gate").
**Why it happens:** The runtime-neutral source and the two projected trees are physically separate files; nothing forces a re-emit at edit time.
**How to avoid:** Re-run the emitter as the LAST step before any snapshot/`.ambr` update, exactly matching the established sequence (source edit → emit → commit the projected trees → THEN regenerate/verify the determinism snapshot, never `--snapshot-update` first). Verify with `git diff --stat` showing the emitted trees changed alongside the source, and confirm no model ID leaked into the emitted `.opencode/agent/orchestrator.md` etc.

### Pitfall 7: WR-01 (non-injective lowered-id construction) surfacing as real collisions in TOPO-07 fixtures

**What goes wrong:** Phase 24's `24-REVIEW.md` WR-01 flags that the lowered id `pipeline/<contract>/<from>-><to>` is not injective when endpoints/contract ids contain `/` or `->`. TOPO-07's proof fixtures include "cross-repo authority resolution" — cross-repo endpoints use `repo:stage` syntax and MAY be adjacent to a `->`-containing string if a fixture author isn't careful, silently colliding two distinct edges into a false "duplicate id" `ValueError`.
**Why it happens:** The fixture author reasonably assumes ids "can never collide" (the old docstring's claim, itself flagged as unenforced by WR-01).
**How to avoid:** Either (a) keep all TOPO-07 fixture endpoint/contract strings free of `/` and `->` (simplest, no code change), or (b) have the planner schedule a task to close WR-01 (switch the id-join to a JSON-encoded triple per the 24-REVIEW.md suggested fix) BEFORE authoring fixtures that might exercise the collision. Given the compiler/gate is "the natural place to close them if the planner chooses" (CONTEXT canonical refs), recommend the planner make an explicit go/no-go call on WR-01/WR-02 as a named task rather than silently avoiding the collision in fixture design (which would leave the underlying bug live for a future phase to rediscover).

## Code Examples

### Reading the compiled graph from a conductor surface (illustrative, Python-side helper the prose points at)

```python
# Source: pattern composition over tools/harness_config/loader.py (effective_relationships,
# read verbatim above) + new tools/contract_graph/compile.py — no existing file has this exact
# function; shown as the shape the planner's compiler task should produce.
from tools.harness_config import load_project, effective_relationships, components
from tools.contract_graph.compile import compile_graph

cfg = load_project()                    # or load_project("<instance>/project.toml")
graph = compile_graph(cfg)              # {"relationships": [...], "adjacency": {...}, "diagnostics": [...]}
assert graph["diagnostics"] == []       # core/instance defaults must compile clean
```

### Existing linear render this phase must preserve verbatim for the linear case (source: harness/commands/pipeline.md:44-53, 63-66)

```
stage 1: source (python) consumes=[] produces=[greeting]
stage 2: sink (python) consumes=[greeting] produces=[]
```
```
source -> sink (greeting)
```

## State of the Art

| Old Approach (Phase 24 and earlier) | Current Approach (Phase 25) | When Changed | Impact |
|--------------------------------------|------------------------------|---------------|--------|
| `/pipeline`, `pipeline-map` read `[[components]]`/`[pipeline]` DIRECTLY via `components()`/`pipeline()` (linear-only, no relationship-graph awareness) | Same surfaces ALSO consume the compiled `effective_relationships()` graph, rendering branches/cycles via D-01's indented tree | This phase (25) | Conductor becomes graph-aware without a second command/persona; linear rendering must remain the byte-identical special case |
| Endpoint/contract existence unchecked for the general relationship vocabulary (Phase 24 explicitly deferred "endpoint resolution + graph-wide consistency" to Phase 25) | New `harness_lint` gate validates every relationship's authority/dependent endpoints + authority-owned contract existence | This phase (25) | First point at which a malformed `[[contract_graph.relationships]]` record fails CI, not just schema-shape validation |

**Deprecated/outdated:** None — this is additive; the legacy linear `[pipeline]` path and its existing gate (`test_pipeline_config.py`) are untouched and continue to run alongside the new gate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A new `tools/contract_graph/` package (vs. extending `harness_config`) is the correct module boundary | Standard Stack / Alternatives Considered | Low — this is an internal code-organization choice explicitly left to "Claude's Discretion" in CONTEXT.md; either location is functionally equivalent as long as `harness_config`'s existing raw-passthrough contract is not touched. If the planner disagrees, only file paths in tasks change, not the underlying logic. |
| A2 | "Byte-identical" for the conductor prose surfaces (TOPO-06) is best proven by keeping the existing example-output text blocks in `pipeline.md`/`SKILL.md` unedited, since no runnable render function exists today to golden-test | Common Pitfalls / Pitfall 1 | Medium — if the planner instead wants a NEW runnable render function with its own golden test, that is a larger scope addition (a Python renderer, not just prose) than this research assumed; flagged explicitly in Pitfall 1 as a decision the planner must make. |
| A3 | The authority-owned-contract check should reuse the "schema-glob existence" idiom (not `contract_drift.run_gate`'s hash-diff machinery) | Don't Hand-Roll | Low — the CONTEXT canonical refs say "reuse `tools/contract_drift/drift.py`... do not re-implement contract existence checks," which could be read as literally calling into `drift.py`. Read closely, `drift.py` has no standalone "does contract X have a schema" function — the existence check is inlined at each call site (`test_pipeline_config.py`, `test_workspace_config.py`, `workspace_drift`). This research interprets "reuse drift" as reusing that established idiom/pattern, not a literal function import, since no such function exists to import. The planner may choose to extract one first. |

**If this table is empty:** N/A — see above.

## Open Questions (RESOLVED)

> All three resolved during planning; each plan implements the recommendation. Markers added post-plan-check.

1. **Does the compiler need a CLI entrypoint (like `python -m tools.contract_drift.drift`) or is it Python-API-only?**
   - **RESOLVED:** API-only for Phase 25 — no CLI added (25-01). A DOCSUP CLI is deferred to Phase 28 if needed.
   - What we know: `contract_drift` has a `main()`/argparse CLI because it's invoked from CI shell scripts (`check.sh`). The graph gate, by contrast, is a pytest suite (like `test_pipeline_config.py`), which needs no separate CLI.
   - What's unclear: Whether Phase 28/29 (Living Docs, DOCSUP) will want a CLI-invokable "print affected set for path X" tool outside pytest.
   - Recommendation: Skip a CLI for Phase 25 (queries are a Python API consumed by conductor prose + gate tests); let Phase 28 add one if/when DOCSUP's graph-impact reports need shell invocation — don't speculatively build it now.

2. **Exact slug vocabulary beyond the three named in D-02 (`unresolved-authority`, `dangling-endpoint`, `unknown-contract`)**
   - What we know: D-02 names exactly these three as examples ("e.g.").
   - What's unclear: Whether "contradiction" (one contract, two authorities — already an `effective_relationships()` `ValueError`, not a gate diagnostic) needs its own slug at the gate layer, or whether that failure mode stays an exception (crashes the gate test outright, as it does for `test_topology_relationships.py` today) rather than becoming a collected diagnostic.
   - Recommendation: Let `effective_relationships()`'s three `ValueError` modes stay hard crashes (unchanged, TOPO-03 territory); the NEW gate's diagnostic slugs are exactly the THREE new TOPO-04 concerns (endpoint declared-against-components/members, authority owns the contract, contract exists) — do not conflate the two layers.
   - **RESOLVED:** Only the three named D-02 slugs (`unresolved-authority`, `dangling-endpoint`, `unknown-contract`) implemented at the gate layer (25-01); the three `effective_relationships()` `ValueError` modes stay hard crashes (unchanged).

3. **Where does "authority owns the contract" resolve for a component-level authority vs. a bare id?**
   - What we know: `test_pipeline_config.py::test_pipeline_edges_are_well_formed` checks `contract in by_id[src].get("produces", [])` for the LEGACY edge case — i.e. "ownership" there means "the from-component declares this contract in `produces`". For an EXPLICIT `[[contract_graph.relationships]]` record, there is no `produces`/`consumes` concept (Phase 24 explicitly deferred that) — an authority is just an opaque endpoint string.
   - What's unclear: For an explicit record whose `authority` is, say, a bare component id, does "authority-owned contract resolution" mean (a) the authority's `produces` list contains the contract (same rule as legacy edges), or (b) merely that the contract has a tracked schema SOMEWHERE (existence only, no ownership-by-produces check)?
   - Recommendation: Implement (a) when the authority resolves to a declared `[[components]]`/`[[members]]` id with a `produces` field, falling back to (b) existence-only when the authority endpoint doesn't map to a `produces`-bearing declaration (e.g. an opaque logical id with no component backing) — document this fallback explicitly in the ADR-0009 model, since it's a genuine design decision D-04 says the ADR must record.
   - **RESOLVED:** produces-check-with-existence-fallback (a→b) implemented in 25-01 Task 2 and recorded in ADR-0009 (25-05).

## Environment Availability

No external dependencies for this phase — Python stdlib (`tomllib`, `json`, `pathlib`) already verified present and in use by every module this phase builds on (`tools/harness_config`, `tools/workspace_config`, `tools/contract_drift`). No CLI tools, services, or runtimes beyond the repo's existing `uv`/`pytest` toolchain are needed.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ (stdlib `tomllib`) | Compiler/query modules | ✓ | matches `requires-python >=3.11` (existing repo constraint) | — |
| pytest | New gate + unit tests | ✓ | 8.4.x (existing repo pin) | — |
| `uv` | Test/dep management | ✓ | 0.11.x (existing repo pin) | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (existing repo pin, `pyproject.toml` `testpaths = ["libs/python", "tools"]`) |
| Config file | `pyproject.toml` (repo root) |
| Quick run command | `uv run pytest tools/contract_graph -q` / `uv run pytest tools/harness_lint/tests/test_contract_graph_config.py -q` |
| Full suite command | `uv run pytest -q` (full non-example suite; example leg runs separately per existing convention) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TOPO-04 | Compiler produces stably-ordered, repo-confined graph + slug diagnostics; validates endpoints/authority-owned-contract; accepts fan-in/fan-out/disconnected/cycle | unit | `uv run pytest tools/contract_graph/tests/test_compile.py -x` | ❌ Wave 0 (new package) |
| TOPO-04 | Gate wired into `harness_lint` mirroring `test_pipeline_config.py` | integration (consistency gate) | `uv run pytest tools/harness_lint/tests/test_contract_graph_config.py -x` | ❌ Wave 0 |
| TOPO-05 | direct/reverse/transitive queries: `{ids, paths}`, cycle-safe, deterministic | unit | `uv run pytest tools/contract_graph/tests/test_query.py -x` | ❌ Wave 0 |
| TOPO-05 | No task-evidence requirement selected, no contract-body preload | negative/structural | `uv run pytest tools/contract_graph/tests/test_query.py -k no_evidence_or_body_preload -x` | ❌ Wave 0 |
| TOPO-06 | `/pipeline`/`pipeline-map`/`orchestrator.md` prose updated; linear case documented byte-identical | structural (prose-token / frontmatter) | `uv run pytest tools/harness_lint/tests/test_orchestrator_topology.py -x` (extend) + a new prose assertion in a sibling test | ✅ existing file extended, ❌ new assertions |
| TOPO-06 | Round-trip byte-identical to both runtimes, no model ID | emit-drift (existing CI job) | `python -m tools.harness_emit && git diff --exit-code -- .opencode .claude` | ✅ existing gate, mechanically re-run |
| TOPO-07 | Generic non-linear fixtures (fan-out, req/resp split, event fan-out, legal cycle, cross-repo) pass; linear regression unchanged; GEN-04 green | fixture-driven unit + structural | `uv run pytest tools/contract_graph/tests/fixtures -q` + `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | ❌ Wave 0 (fixtures) / ✅ GEN-04 test exists |
| TOPO-07 | ADR-0009 human-ratified | manual/human checkpoint | N/A — `docs/adr/` is CODEOWNERS-gated, no automated pass/fail | N/A |

### Sampling Rate

- **Per task commit:** `uv run pytest tools/contract_graph tools/harness_lint/tests/test_contract_graph_config.py -q`
- **Per wave merge:** `uv run pytest -q` (full non-example suite) + `uv run python -m tools.contract_drift.drift` + `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` + emit-drift re-run
- **Phase gate:** Full suite green + emit-drift clean + GEN-04 twins green + ADR-0009 ratified before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tools/contract_graph/__init__.py` + `pyproject.toml` — new uv workspace member (mirror `tools/harness_config/pyproject.toml` package=false, PEP-562 lazy re-export)
- [ ] `tools/contract_graph/compile.py` — compiler implementation
- [ ] `tools/contract_graph/query.py` — query implementation
- [ ] `tools/contract_graph/tests/fixtures/graphs/{valid,negative}/cases.json` — TOPO-04/07 fixtures (fan-in, fan-out, disconnected, canonical-cycle, cross-repo, request/response-as-separate-records, event fan-out)
- [ ] `tools/contract_graph/tests/test_compile.py`, `test_query.py`
- [ ] `tools/harness_lint/tests/test_contract_graph_config.py` — the new gate
- [ ] Framework install: none — `uv sync` already covers the workspace; adding a new member follows the exact pattern Phase 5 (`05-02`) used to add `tools/harness_config` as a member (per STATE.md history)

*Wave 0 is substantial because this phase is greenfield for the compiler/query package; the gate/prose edits, by contrast, extend already-existing test files with established idioms.*

## Security Domain

> `security_enforcement` is absent from `.planning/config.json` — treated as enabled per the default rule.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | no | N/A — no auth surface in this phase |
| V3 Session Management | no | N/A |
| V4 Access Control | yes | CODEOWNERS-gated `docs/adr/` write for ADR-0009 (existing constitution-plane control, unchanged) |
| V5 Input Validation | yes | The compiler is the V5 control point: it validates untrusted-shape TOML/JSON config records (endpoints, contract ids) before they reach any conductor prose or downstream Phase 28/29 doc-impact reporting. Mirrors the existing pattern (`test_workspace_config.py`'s docstring: "workspace.toml is parsed input (untrusted config text)... V5 input validation"). |
| V6 Cryptography | no | N/A — no crypto in this phase (contract-hash/JCS machinery is Phase 24/earlier, untouched) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Path traversal via a malicious/malformed endpoint or member root string reaching filesystem globbing (`(producer_root / "contracts").rglob(...)`) | Tampering | `_confine`-style guard already used elsewhere in this repo (`golden_runner._confine`, docs_sync `write()` confinement); compiler must resolve any filesystem path it constructs from config-derived strings the same way, staying "repo-confined" per TOPO-04's explicit requirement. |
| Unbounded/adversarial cyclic graph causing resource exhaustion in traversal | Denial of Service (bounded case: local dev tooling, not a network-facing service) | Visited-set cycle termination (D-03) is itself the mitigation — finite visited set bounds traversal to O(nodes+edges) regardless of cycle structure. |
| A config author naming a contract id that collides with an unrelated schema via the non-injective lowered-id join (WR-01) | Tampering (integrity of the "no collision" guarantee) | See Pitfall 7 — either constrain fixture/id vocabulary or fix the join to be injective (JSON-encoded triple). |

## Sources

### Primary (HIGH confidence — read directly from this repo)
- `.planning/phases/25-graph-compiler-queries-conductor-proof-v2-3-a/25-CONTEXT.md` — locked decisions D-01..D-04, canonical refs
- `.planning/REQUIREMENTS.md` — TOPO-04..07 exact text
- `.planning/research/v2.3-scoping-FINAL.md` — Theme A + Phase 25 design-of-record
- `.planning/phases/24-.../24-01-SUMMARY.md`, `24-02-SUMMARY.md`, `24-REVIEW.md` — what Phase 24 shipped + WR-01/WR-02
- `tools/harness_config/loader.py` (full file read) — `effective_relationships()`, `contract_graph_relationships()`, `components()`, `pipeline()`
- `tools/workspace_config/loader.py` (full file read) — `members()`, `edges()`, `split_endpoint()`, `contract_graph_relationships()`
- `contracts/harness/topology/relationship.schema.json` — the ratified per-record schema
- `harness/commands/pipeline.md`, `harness/skills/pipeline-map/SKILL.md`, `harness/agents/orchestrator.md` — the three conductor surfaces (full text read)
- `tools/harness_lint/tests/test_pipeline_config.py`, `test_workspace_config.py`, `test_orchestrator_topology.py`, `test_core_no_example_dep.py` (full files read) — gate idiom + GEN-04 guard
- `tools/contract_drift/drift.py` (full file read) — schema-existence idiom, `workspace_drift`, `run_gate` return shape
- `tools/harness_emit/generate.py` (partial read) — emitter round-trip mechanics, glob discovery, DERIVED marker
- `docs/adr/` directory listing — confirms highest existing ADR is 0008, so 0009 is next
- `harness/project.toml`, `workspace.toml` (full text read) — current empty `[contract_graph]` slots, existing linear topology
- `.planning/STATE.md` — project history, emit round-trip gate-theft precedent, GEN-04 discipline
- `.planning/config.json` — `workflow.nyquist_validation: true` (Validation Architecture section required)

### Secondary (MEDIUM confidence)
- None — no external library/framework claims were made in this research; every recommendation is grounded in code read directly from this repository.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no external packages; all recommendations are internal module-boundary choices verified against ratified Phase-24 constraints read directly from source.
- Architecture: HIGH — compiler/query/gate design directly extends patterns read verbatim from `tools/harness_config`, `tools/contract_drift`, `tools/harness_lint`.
- Pitfalls: HIGH for reuse/signature/cycle risks (grounded in code read); MEDIUM for the exact "byte-identical" proof mechanism for conductor prose (Pitfall 1 / Assumption A2) since no runnable render function or golden test exists today for that surface — this is a genuine open design question the planner must resolve, not a knowledge gap.

**Research date:** 2026-07-19
**Valid until:** Stable — this is intra-repo composition with no external-ecosystem currency risk; re-verify only if Phase 24's shipped interfaces (`effective_relationships`, schema) change before Phase 25 executes.
