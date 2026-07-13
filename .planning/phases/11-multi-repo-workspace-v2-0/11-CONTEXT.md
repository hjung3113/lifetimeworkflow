# Phase 11: Multi-Repo Workspace (v2.0 γ) - Context

**Gathered:** 2026-07-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Declare and operate several repos as ONE workspace. Raise the `harness/project.toml` GEN-03 slot
pattern one level into a **workspace manifest**; run the Phase-10 β fan-out/synthesize per-repo with
workspace-level synthesis (no single context holds all repos); extend contract-drift/golden gates
across repo boundaries; and generalize the Phase-8 pipeline topology so a declared edge can cross a
repo boundary — all while the core depends on no workspace member (GEN-04 generalized to
core→workspace-member). Satisfies MREPO-01..04.

**Reuse, do NOT rebuild:** `harness/project.toml` + `tools/harness_config/loader.py` (slot+loader
pattern to raise), the Phase-10 `fan-out-synthesize` substrate + `context-budget` heuristic,
`tools/contract_drift` + `tools/golden_runner`, the Phase-8 `[pipeline]` topology, the
`tools/harness_lint/tests/test_core_no_example_dep.py` GEN-04 guard (to generalize), and the Phase-7
emitter.

**In scope:** workspace model + manifest, repo-scoped fan-out/synthesis, cross-repo drift/golden
gates, repo-crossing pipeline edges + generalized GEN-04 guard, and a minimal demo fixture.
**Out of scope:** any change to the constitution/golden planes' human-owned posture; a bespoke
workspace runtime/daemon; rebuilding the fan-out substrate; domain features of member repos.
</domain>

<decisions>
## Implementation Decisions

### Workspace model & manifest (the γ KEY DECISION — now resolved)
- **Model b — workspace manifest as pure DATA**, raising the `project.toml` slot pattern one level.
  No enforcement logic in the manifest (mirrors project.toml / permission-matrix.json data-only posture).
- New **top-level `workspace.toml`** (TOML, mirrors `project.toml`'s shape); NOT an extension of
  project.toml (a workspace sits one level above a single project).
- Declares **member repos** (id + root path/url) **and cross-repo edges** (producer repo → contract
  id → consumer repo). Edges reference contract ids, not inlined schemas.
- A stdlib `tomllib` **loader passthrough + consistency gate**: every edge's contract must resolve in
  its producer repo and no member may dangle. Mirror `tools/harness_config/loader.py` +
  `tools/harness_lint/tests/test_language_config.py` (the GEN-03 consistency-gate precedent). Config =
  SSOT, no codegen.

### Repo-scoped fan-out / synthesis (MREPO-02 — reuse Phase-10 β)
- Reuse the Phase-10 `fan-out-synthesize` substrate **as-is**: one read-only worker per member repo →
  workspace-level synthesis. No bespoke workspace orchestrator.
- Worker scope is **per-repo, read-only, schema-bounded citation returns** (paths + claims, never raw
  file dumps); a worker does NOT read sibling repos — this is what keeps any single context from
  holding every repo at once.
- The **orchestrator/conductor dispatches** the fan-out, deciding whether to fan out via the
  `context-budget` heuristic.
- Reuse the existing `/fan-out-synthesize` entry point; add a thin workspace-scoped entry only if the
  planner finds it necessary (Claude's discretion at plan time).

### Cross-repo gates (MREPO-03)
- Extend `tools/contract_drift` to resolve a manifest edge's contract **in the producer repo** and
  check the consumer's expectation; **fail on cross-repo drift**.
- The golden runner gains **workspace-aware path resolution** so a golden case whose edge spans a repo
  boundary runs against the correct member roots.
- Gates run as a **workspace-level CI job** iterating members + edges (mirrors the Phase-7 emit-drift /
  Phase-9 stale-derived separate-job pattern), not folded into per-repo CI.
- Constitution plane stays **human-owned per repo**; machines gate, humans ratify (invariant unchanged).

### Pipeline topology generalization + GEN-04 (MREPO-04)
- Generalize the Phase-8 `[pipeline]` edge schema so an endpoint can be a **repo-qualified stage**
  (e.g. `repo:stage`), letting a declared edge cross a repo boundary.
- **Generalize GEN-04:** add a guard test proving the core never imports or path-references a workspace
  member (mirror `test_core_no_example_dep.py`'s core→example guard; core→workspace-member,
  single-direction).
- Any new agent/command **round-trips the Phase-7 emitter to BOTH runtimes** (opencode primary, Claude
  secondary), carries **no model identifier**, and keeps the core example-independent.
- Ship the **mechanism in core PLUS a minimal 2-member workspace fixture** to exercise the gates
  (mirrors the Phase-8 build-BOTH mechanism-and-demo pattern). The demo is minimal — just enough to
  drive the cross-repo drift/golden/topology gates green.

### Claude's Discretion
- Exact `workspace.toml` schema field names, the precise loader/gate module layout, the CI job wiring,
  and whether a thin workspace-scoped fan-out entry command is warranted — all planner/researcher
  detail. The decisions above fix the WHAT and the boundaries.
</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `harness/project.toml` + `tools/harness_config/loader.py`: the pure-DATA slot + `tomllib` loader
  passthrough pattern to raise one level into `workspace.toml`.
- `tools/harness_lint/tests/test_language_config.py`: the GEN-03 consistency-gate precedent to mirror
  for the workspace manifest gate.
- Phase-10 `fan-out-synthesize` skill/command + `context-budget` skill: the per-repo fan-out substrate
  and the delegate-vs-inline heuristic.
- `tools/contract_drift/drift.py` + `tools/golden_runner/runner.py`: extend across repo boundaries.
- Phase-8 `[pipeline]` topology (via `tools/harness_config`): generalize edges to cross repos.
- `tools/harness_lint/tests/test_core_no_example_dep.py`: the GEN-04 guard to generalize to
  core→workspace-member.
- Phase-7 emitter (`tools/harness_emit`): round-trip any new agent/command to both runtimes.

### Established Patterns
- Slot-as-DATA (GEN-03): config is the single source of truth, a loader reads it, a consistency test
  gates divergence — no codegen. `workspace.toml` follows this exactly, one level up.
- Separate-CI-job gate (Phase-7 emit-drift, Phase-9 stale-derived): the cross-repo gate mirrors it.
- Fan-out → schema-bounded citation-bearing summary → synthesize (Phase-10): applied per-repo.
- core→X single-direction dependency guard (GEN-04): generalized from example to workspace-member.

### Integration Points
- New `workspace.toml` at repo root; loader + consistency gate under `tools/`.
- Workspace-level CI job alongside the existing emit-drift / stale-derived / matrix jobs.
- Emitter manifest + both runtime trees gain any new workspace agent/command surface.
</code_context>

<specifics>
## Specific Ideas

- Keep `workspace.toml` byte-for-byte in the GEN-03 idiom: pure data, header comment naming its
  consumers (loader + gate), no logic.
- The minimal demo is a fixture to turn the gates green, not a product — two tiny member repos with a
  single cross-repo edge and one golden case that spans it.
</specifics>

<deferred>
## Deferred Ideas

- A dedicated `/workspace-analyze` command (vs reusing `/fan-out-synthesize`) — only if planning shows
  the reuse ergonomics are insufficient. Not committed here.
- A richer workspace runtime/daemon or remote-repo fetching — out of scope for the manifest-first MVP
  (model b); revisit in a future milestone if multi-repo operation demands it.

### Reviewed Todos (not folded)
None — no pending todos matched Phase 11.
</deferred>

---

*Phase: 11-Multi-Repo Workspace*
*Context gathered: 2026-07-13*
