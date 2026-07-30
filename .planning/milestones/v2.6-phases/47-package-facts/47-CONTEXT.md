# Phase 47: Package Facts - Context

**Gathered:** 2026-07-30
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous) — 3 areas, all accepted as recommended

<domain>
## Phase Boundary

Deliver one committed **derived** package + dependency graph for this checkout: every package with
its manifest path, language and package id, plus dependency edges parsed from the manifests
themselves. Demote `[[components]]` in `harness/project.toml` to an override slot layered over those
derived facts, and let `contract_graph` attribute a contract path to the package that owns it.

**Report-only.** No new gate, no new CI job, nothing injected into SessionStart. `ci.yml`'s job set
and `gate.needs` (`ci.yml:329`) must be unchanged from the phase's base commit; derived freshness
rides the existing `stale-derived` job (`ci.yml:271`).

Out of the boundary: dependency *policy* (allowed/forbidden edges), version/compatibility resolution
(carried EVOL-02), per-package convention profiles (Phase 48), and `/impact` (Phase 49).

</domain>

<decisions>
## Implementation Decisions

### Derived artifact & generator shape
- Artifact is `.memory/derived/package-facts.md` — a markdown table in the same idiom as
  `.memory/derived/contracts-index.md`. Programmatic consumers (Phases 48, 49) import the builder
  function in-process; they never re-parse the rendered markdown.
- Generator lives at `tools/memory_regen/package_facts.py`. Dependency parsing is added **inside**
  `tools/adoption_scan/detect.py` (MONO-02: extend `detect_manifests`, do not fork it), and the
  generator reuses it — no second manifest-detection implementation.
- Package id comes from the manifest's own declared name (`[project].name`, `package.json` `name`,
  `.csproj` basename, `go.mod` module path), falling back to the directory name. The repo-relative
  manifest directory is the stable key.
- Scan scope is git-tracked manifests **excluding** `**/tests/fixtures/**`, so
  `tools/adoption_apply/tests/fixtures/polyglot-single/pyproject.toml` does not become a package.

### Dependency edge semantics
- Edges are **intra-repo only**. External packages are not nodes — the graph describes this
  monorepo, and version bumps must not churn the artifact.
- Both dev and runtime dependencies are recorded; each edge carries a `kind` field distinguishing
  them.
- Parsers per manifest kind: `pyproject.toml` (`[project].dependencies` + uv workspace/sources),
  `package.json` (dependencies + devDependencies), `.csproj` (`ProjectReference`), `go.mod`
  (`require`), `Cargo.toml` (path dependencies).
- An unresolvable dependency is **dropped, never fabricated**: an edge exists only when the named
  dependency resolves to a package present in the derived facts.

### Override slot & contract ownership
- Override match key is `[[components]].id` against the derived package id. A declared component
  with no matching derived package stays declared-only and does **not** error — both live configs
  (`harness/project.toml`, `examples/log-parser/project.toml:34-63`) must load with zero edits.
- Merge is **field-level layering**: the derived record is the base, declared fields win, nothing is
  silently deleted.
- Contract → package attribution uses the **nearest enclosing package directory** of the contract
  path, falling back to the root package. No hand-maintained ownership table (that would violate
  MONO-02's no-hand-maintained-lists rule).
- The attribution lands inside `tools/contract_graph`, reusing `compile.py` / `query.py`. No new
  tool package, no new command, no gate.

### Resolved after research (2026-07-30)
- **Root-package fallback is accepted, and must be asserted, not implied.** No manifest exists at
  `examples/log-parser/`, so under nearest-enclosing-package attribution both the core `contracts/**`
  and the instance's contracts resolve to the **root package**. That is the correct answer for this
  checkout — adding a manifest purely to change attribution would be surface growth. A test must
  assert this fallback explicitly so the behaviour is recorded rather than accidental.
- **Enumeration is a light `git ls-files` walk, not `scan.build_inventory()`.** MONO-01's required
  fields need no hashing, secret classification or evidence refs; reusing the full inventory would
  pull that machinery in for nothing. Manifest *recognition* still comes from `detect.py` — only the
  file enumeration is light.
- **Dependency parsing enters as a sibling function** (e.g. `detect_dependencies(path, kind, text)`)
  in `tools/adoption_scan/detect.py`, fed content by the generator, so `detect_manifests` keeps its
  "no filesystem access here" invariant intact.
- **Edge proofs run on synthetic fixtures.** The live tree yields only 2 real intra-repo edges (both
  `.csproj` `ProjectReference`); `pyproject.toml`, `package.json`, `go.mod` and `Cargo.toml` edge
  parsing plus the add/remove-a-dependency criterion must be proven on fixture manifests.
- **`tools/harness_lint/tests/test_ci_stale_derived.py` must be edited**, not merely left passing:
  its `_DERIVED_PATHS` tuple and assertions hard-code the two current derived paths, and widening
  them is what proves the new artifact rides the existing job (SC5) instead of a new one. The job's
  "never interpolate `${{ github.event.* }}`" invariant stays intact.

### Claude's Discretion
- Exact column set and row ordering of the rendered markdown table (must be deterministic and
  byte-identical on regeneration).
- Internal function/module naming and the split between `detect.py` additions and generator-side
  assembly.
- Test layout, fixture manifests used to prove the add/remove-a-dependency criterion.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/adoption_scan/detect.py` — `_MANIFEST_KIND_BY_NAME` (`:41-47`) recognizes `pyproject.toml`,
  `package.json`, `go.mod`, `Cargo.toml`; `*.csproj` is a suffix special-case (`:107-108`).
  `detect_manifests` (`:100-121`) records `path`/`kind`/`classification`/`evidence` on the D-02
  `observed` evidence ladder — existence only, zero dependency parsing today.
- `tools/memory_regen/contracts_index.py` — the reference derived generator: ~80% reuse of existing
  builders, `DERIVED — do not hand-edit` header, no timestamps, byte-identical regeneration proven
  by a committed syrupy snapshot.
- `tools/contract_graph/{compile.py,query.py}` — compiled adjacency plus `direct` / `reverse` /
  `transitive` (`query.py:29,39,55`), deterministic sorted output, cycle-safe, no file I/O.
- `tools/harness_config/loader.py` — `components()` / `pipeline()` passthrough helpers over
  `harness/project.toml`.

### Established Patterns
- Derived plane: generated under `tools/`, never hand-edited, byte-identical on regeneration,
  `DERIVED — do not hand-edit (<generator path>)` header.
- Config is pure DATA (`harness/project.toml` header): no enforcement logic in the TOML, consistency
  enforced by `tools/harness_lint` tests instead of codegen.
- GEN-04: the core must not depend on `examples/**` — guarded by
  `tools/harness_lint/tests/test_core_no_example_dep.py`.

### Integration Points
- `stale-derived` CI job (`ci.yml:271`) regenerates `docs/reference` +
  `.memory/derived/contracts-index.md` and diffs; the new artifact joins that command and diff list
  rather than adding a job.
- `/refresh-memory` and the `curator` persona drive the same regen locally.
- 24 recognized manifests are tracked today (20 `pyproject.toml`, 3 `.csproj`, 1 `package.json`),
  one of which is an adoption test fixture and is excluded by decision.

</code_context>

<specifics>
## Specific Ideas

- The artifact must satisfy the milestone's binding no-growth constraint: report-only, +0 gates,
  +0 CI jobs, +0 commands, nothing injected into SessionStart.
- Criterion 2 needs a *fixture-level* proof: removing a dependency from a fixture manifest removes
  exactly that edge on regeneration.

</specifics>

<deferred>
## Deferred Ideas

- External-dependency nodes / version data — deliberately out; revisit only with EVOL-02 (contract
  versioning / compatibility engine), which is already carried.
- Dependency policy (allowed/forbidden edges) — would be a gate, which this milestone forbids.

</deferred>
