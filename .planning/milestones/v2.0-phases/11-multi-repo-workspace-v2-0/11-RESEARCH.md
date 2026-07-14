# Phase 11: Multi-Repo Workspace (v2.0 γ) - Research

**Researched:** 2026-07-13
**Domain:** Harness self-extension (Python/stdlib tooling) — raise the GEN-03 config-slot pattern one level into a workspace manifest; extend contract-drift / golden / pipeline-topology gates across repo boundaries; generalize the GEN-04 no-dependency guard.
**Confidence:** HIGH (every extension point read in-repo; all decisions locked in CONTEXT.md; zero external packages)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Workspace model & manifest (γ KEY DECISION — RESOLVED):**
- **Model b — workspace manifest as pure DATA**, raising the `project.toml` slot pattern one level. No enforcement logic in the manifest (mirrors `project.toml` / `permission-matrix.json` data-only posture).
- New **top-level `workspace.toml`** (TOML, mirrors `project.toml`'s shape); NOT an extension of `project.toml` (a workspace sits one level above a single project).
- Declares **member repos** (id + root path/url) **and cross-repo edges** (producer repo → contract id → consumer repo). Edges reference contract ids, not inlined schemas.
- A stdlib `tomllib` **loader passthrough + consistency gate**: every edge's contract must resolve in its producer repo and no member may dangle. Mirror `tools/harness_config/loader.py` + `tools/harness_lint/tests/test_language_config.py`. Config = SSOT, no codegen.

**Repo-scoped fan-out / synthesis (MREPO-02 — reuse Phase-10 β):**
- Reuse the Phase-10 `fan-out-synthesize` substrate **as-is**: one read-only worker per member repo → workspace-level synthesis. No bespoke workspace orchestrator.
- Worker scope is **per-repo, read-only, schema-bounded citation returns** (paths + claims, never raw file dumps); a worker does NOT read sibling repos.
- The **orchestrator/conductor dispatches** the fan-out via the `context-budget` heuristic.
- Reuse the existing `/fan-out-synthesize` entry point; add a thin workspace-scoped entry only if the planner finds it necessary (Claude's discretion).

**Cross-repo gates (MREPO-03):**
- Extend `tools/contract_drift` to resolve a manifest edge's contract **in the producer repo** and check the consumer's expectation; **fail on cross-repo drift**.
- The golden runner gains **workspace-aware path resolution** so a golden case whose edge spans a repo boundary runs against the correct member roots.
- Gates run as a **workspace-level CI job** iterating members + edges (mirrors Phase-7 emit-drift / Phase-9 stale-derived separate-job pattern), not folded into per-repo CI.
- Constitution plane stays **human-owned per repo**; machines gate, humans ratify (invariant unchanged).

**Pipeline topology generalization + GEN-04 (MREPO-04):**
- Generalize the Phase-8 `[pipeline]` edge schema so an endpoint can be a **repo-qualified stage** (e.g. `repo:stage`), letting a declared edge cross a repo boundary.
- **Generalize GEN-04:** add a guard test proving the core never imports or path-references a workspace member (mirror `test_core_no_example_dep.py`; core→workspace-member, single-direction).
- Any new agent/command **round-trips the Phase-7 emitter to BOTH runtimes** (opencode primary, Claude secondary), carries **no model identifier**, keeps the core example-independent.
- Ship the **mechanism in core PLUS a minimal 2-member workspace fixture** to exercise the gates. Minimal — just enough to drive cross-repo drift/golden/topology gates green.

### Claude's Discretion
- Exact `workspace.toml` schema field names, the precise loader/gate module layout, the CI job wiring, and whether a thin workspace-scoped fan-out entry command is warranted.

### Deferred Ideas (OUT OF SCOPE)
- A dedicated `/workspace-analyze` command (vs reusing `/fan-out-synthesize`) — only if planning shows reuse ergonomics insufficient. Not committed.
- A richer workspace runtime/daemon or remote-repo fetching — out of scope for the manifest-first MVP (model b).
- Any change to the constitution/golden planes' human-owned posture; a bespoke workspace runtime/daemon; rebuilding the fan-out substrate; domain features of member repos.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MREPO-01 | Workspace model + manifest — raise the `harness/project.toml` slot pattern one level; declare member repos + cross-repo edges (producer→contract→consumer). | §Standard Stack (new `workspace.toml` + `tools/workspace_config` loader), §Pattern 1 (slot-as-DATA), §Pattern 2 (consistency gate mirroring `test_language_config.py`). Wave 1. |
| MREPO-02 | repo-scoped subagents + β fan-out/synthesis across repos (per-repo analysis → workspace synthesis); no single context holds all repos. | §Pattern 4 (reuse Phase-10 `fan-out-synthesize` as-is; worker unit = one member repo). Wave 4. Reuse-only; likely doc/skill wiring, optional thin command. |
| MREPO-03 | Cross-repo contract-drift / golden gates — extend Phase-6 CI + `contract_drift` across the workspace. | §Pattern 3 (`run_gate(contracts_dir=, baseline_path=)` is already parametrized; drift CLI already takes `--contracts-dir`/`--baseline`), §Golden path resolution (`golden_dir` override + `_confine` pitfall), §CI (workspace job mirroring emit-drift/stale-derived). Wave 3. |
| MREPO-04 | Generalize Phase-8 pipeline topology so an edge crosses a repo boundary (repo-qualified stage endpoints). | §Pattern 5 (`repo:stage` endpoint parsing in the edge gate), §GEN-04 generalization (new `test_core_no_workspace_member_dep.py`), §Emit round-trip. Wave 2. |
</phase_requirements>

## Summary

This is a **pure harness self-extension phase in Python**, with every architectural decision already
locked by CONTEXT.md. There is **nothing to invent and no external package to install** — the work is
to *raise* and *widen* four existing, already-parametrized mechanisms, each of which has a precise
in-repo precedent to mirror byte-for-byte in idiom:

1. **Config-slot-as-DATA** (`harness/project.toml` + `tools/harness_config/loader.py` +
   `tools/harness_lint/tests/test_language_config.py`) → a new top-level **`workspace.toml`** + a
   parallel **`tools/workspace_config`** loader + a **`test_workspace_config.py`** consistency gate.
2. **Contract-drift** (`tools/contract_drift/drift.py::run_gate`) — *already* takes
   `contracts_dir` / `baseline_path` and the CLI *already* takes `--contracts-dir` / `--baseline`
   (proven by the CI `drift` job gating the example manifest). Cross-repo drift = iterate members
   (verbatim reuse per member) **plus** a new edge-resolution check (producer contract exists,
   consumer expects it).
3. **Golden runner** (`tools/golden_runner/runner.py`) — `run_golden_case(..., golden_dir=None)`
   already overrides the case root; the one real hazard is `_confine`, which today allows only
   `REPO_ROOT` + temp and would **reject a member root outside the repo** (see Pitfall 1).
4. **Pipeline topology** (`[pipeline]` edges in `project.toml` + `test_pipeline_config.py`) —
   generalize the `from`/`to` endpoint to a **`repo:stage`** form; add a **generalized GEN-04 guard**
   (`core → workspace-member`) mirroring `test_core_no_example_dep.py`.

Cross-cutting: the whole thing ships as **mechanism in core + a minimal 2-member in-repo fixture**;
any new agent/command **re-runs the Phase-7 emitter** (glob discovery — zero emitter code change) to
both runtimes with no model id; the new GEN-04 twin keeps the core independent of every member.

**Primary recommendation:** Create `workspace.toml` (root, pure DATA, GEN-03 idiom) + a parallel
`tools/workspace_config` loader + a `test_workspace_config.py` consistency gate FIRST (Wave 1), land
the 2-member fixture alongside it, then widen drift → golden → pipeline → fan-out over that manifest,
reusing the already-parametrized CLIs verbatim. Do not build a workspace daemon, do not re-parametrize
what is already parametrized, and watch `golden_runner._confine` for cross-root path rejection.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Workspace manifest (member repos + cross-repo edges) | Config/DATA slot (`workspace.toml`) | — | Model b: pure data, no logic — mirrors `project.toml`/`permission-matrix.json` posture. |
| Manifest parse + passthrough | Core tooling (`tools/workspace_config`) | — | stdlib `tomllib` reader; no enforcement (belongs to the gate). |
| Manifest well-formedness (edges resolve, no dangling member) | Core tests (`tools/harness_lint/tests/test_workspace_config.py`) | — | GEN-03 consistency-gate precedent: config = SSOT, no codegen. |
| Cross-repo contract-drift | Core tooling (`tools/contract_drift`) | CI (workspace job) | `run_gate` already parametrized per contracts tree; add edge-resolution check + iterate members. |
| Cross-repo golden parity | Core tooling (`tools/golden_runner`) | CI (workspace job) | `golden_dir` override exists; extend `_confine` to member roots. |
| Repo-qualified pipeline edges | Config/DATA (`workspace.toml` edges) + core gate | — | Generalize `[pipeline]` endpoint to `repo:stage`. |
| core → workspace-member no-dependency | Core tests (new GEN-04 twin) | — | Single-direction template invariant; mirror `test_core_no_example_dep.py`. |
| Per-repo fan-out / workspace synthesis | Reused skill/command (Phase-10) + orchestrator | — | Reuse-as-is: worker unit = one member repo; conductor synthesizes; `context-budget` gates delegation. |
| Dual-runtime projection of any new surface | Core emitter (`tools/harness_emit`) | — | Glob discovery; re-run projects to `.opencode/` + `.claude/`, no model id. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | **3.11.15** (in env) | Tooling runtime | `requires-python >=3.11` — needed for stdlib `tomllib`. `[VERIFIED: python3 --version]` |
| `tomllib` | stdlib (3.11+) | Parse `workspace.toml` | Zero external dep; the exact reader `tools/harness_config/loader.py` already uses (binary-mode `tomllib.load`). `[VERIFIED: python3 -c import tomllib]` |
| uv | **0.11.27** (in env) | Workspace/dep manager, test runner | Already the project's manager; `uv run pytest`. `[VERIFIED: uv --version]` |
| pytest | 8.4.x (workspace-pinned) | Consistency/guard tests | Every gate in this repo is a structural pytest. `[VERIFIED: uv.lock / CLAUDE.md stack]` |

### Supporting (all in-repo, reuse verbatim)
| Module | Purpose | When to Use |
|--------|---------|-------------|
| `tools/harness_config/loader.py` | The passthrough-loader template to clone one level up | Mirror its `load_project`/`languages`/`components`/`pipeline` shape for `tools/workspace_config`. |
| `tools/contract_drift/drift.py` | `run_gate(contracts_dir, baseline_path)` + `classify()` + `build_manifest()` | Reuse verbatim per member; add a cross-repo edge-resolution check on top. |
| `tools/contract_hash/hash.py` | `build_manifest(contracts_dir)` — keys relative to `contracts_dir.parent` | Each member repo keeps its OWN `contracts/.hashes/manifest.json` (exactly like `examples/log-parser/contracts/.hashes/manifest.json`). |
| `tools/golden_runner/runner.py` | `run_golden_case(..., golden_dir=)`, `compare()`, `_confine()` | Reuse; extend `_confine` allowed-roots to include member roots. |
| `tools/harness_emit` (`generate.py`) | Glob-discovery emitter → both runtimes | Re-run if a new command/skill is added; no emitter code change. |
| `harness/skills/fan-out-synthesize` + `context-budget` | The Phase-10 fan-out substrate + delegate heuristic | Reuse as-is; unit = one member repo. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `tools/workspace_config` module | Reuse `tools/harness_config.load_project()` directly on `workspace.toml` | `load_project` is generic TOML→dict and *would* parse it, but a dedicated module gives named `members()`/`edges()` passthroughs and a clean parallel to the GEN-03 precedent. **Recommend the dedicated module** (mirrors the pattern the planner/checker expect); it MAY internally reuse `load_project` for the raw read. |
| Repo-level edges `{producer, contract, consumer}` | Repo-qualified stage edges `{from="repoA:stage", to="repoB:stage", contract}` | MREPO-01 says "producer repo → contract id → consumer repo"; MREPO-04 says "endpoint = repo-qualified stage". **Recommend a single edge table whose endpoints are `repo:stage`** so MREPO-03 and MREPO-04 share one representation (repo part drives drift/golden member resolution; stage part drives topology). See Open Q1. |
| In-repo 2-member fixture | Real sibling repos on disk | Sibling repos outside `REPO_ROOT` trip `golden_runner._confine` and CI checkout. **Keep the demo fixture INSIDE the repo** (e.g. `tests/fixtures/workspace/<member>/`) so it is a subtree of `REPO_ROOT` — matches CONTEXT "minimal fixture to turn gates green". |

**Installation:** None. No new packages. `tomllib` is stdlib; all other modules are in-repo uv members.

## Package Legitimacy Audit

**Not applicable — this phase installs no external packages.** All new code is Python stdlib
(`tomllib`, `pathlib`, `subprocess`, `hashlib`) plus in-repo uv members. No npm/PyPI/crates additions,
so there is no slopcheck surface. `[VERIFIED: codebase — new work reuses existing modules only]`

## Architecture Patterns

### System Architecture Diagram

```txt
                        ┌───────────────────────────────────────────────┐
   workspace.toml  ───▶ │  tools/workspace_config/loader.py             │
   (root, pure DATA)    │  load_workspace() · members() · edges()       │  raw passthrough
   [[members]] id+root  │  (stdlib tomllib, binary read, NO logic)      │  (no enforcement)
   [[edges]] repo:stage └───────────────┬───────────────────────────────┘
   + contract id                        │ dict
             ┌────────────────┬─────────┼───────────────────┬───────────────────────┐
             ▼                ▼         ▼                    ▼                       ▼
   ┌──────────────────┐  ┌─────────────────────┐  ┌───────────────────┐   ┌──────────────────┐
   │ test_workspace_  │  │ cross-repo DRIFT     │  │ cross-repo GOLDEN │   │ generalized      │
   │ config.py        │  │ (extend drift.py)    │  │ (extend runner.py)│   │ GEN-04 guard     │
   │ (consistency     │  │ per member:          │  │ resolve golden_dir│   │ test_core_no_    │
   │  gate, MREPO-01) │  │  run_gate(dir,base)  │  │  under member root│   │ workspace_       │
   │ edges resolve,   │  │ + edge check:        │  │  (_confine widened│   │ member_dep.py    │
   │ no dangling      │  │  producer contract   │  │   to member roots)│   │ (MREPO-04)       │
   │ member           │  │  exists, consumer    │  │  compare via §4-5 │   │ core planes ↛    │
   └──────────────────┘  │  expects it (MREPO-03)  │  core (MREPO-03)  │   │ member paths     │
                         └──────────┬───────────┘  └─────────┬─────────┘   └──────────────────┘
                                    │                        │
                                    ▼                        ▼
                         ┌──────────────────────────────────────────────┐
                         │  .github/workflows/ci.yml — NEW `workspace`   │
                         │  job (separate, added to gate.needs) mirrors  │
                         │  emit-drift / stale-derived separate-job idiom│
                         └──────────────────────────────────────────────┘

   ORTHOGONAL (reuse-as-is, MREPO-02):
   orchestrator ──context-budget heuristic──▶ /fan-out-synthesize ──▶ N read-only explorer workers
     one worker per MEMBER REPO (read-only, no sibling reads) ──▶ schema-bounded citation returns
     ──▶ conductor synthesizes at workspace level (no single context holds every repo)
```

### Recommended Project Structure
```txt
workspace.toml                                    # NEW — root, pure DATA (GEN-03 idiom, one level up)
tools/
├── workspace_config/                             # NEW — parallels tools/harness_config/
│   ├── __init__.py                               #   PEP 562 lazy re-export (mirror harness_config)
│   ├── loader.py                                 #   load_workspace() · members() · edges()
│   ├── pyproject.toml                            #   package=false uv member (mirror harness_config)
│   └── tests/
├── contract_drift/drift.py                       # EXTEND — cross-repo edge resolution (reuse run_gate)
├── golden_runner/runner.py                       # EXTEND — _confine allowed-roots += member roots
└── harness_lint/tests/
    ├── test_workspace_config.py                  # NEW — MREPO-01 consistency gate
    └── test_core_no_workspace_member_dep.py      # NEW — MREPO-04 GEN-04 twin
tests/fixtures/workspace/                          # NEW — minimal 2-member demo (INSIDE repo root)
├── member-a/contracts/**/*.schema.json + .hashes/manifest.json + golden/<case>/
└── member-b/contracts/... (consumes member-a's contract across the one edge)
.github/workflows/ci.yml                           # EXTEND — new `workspace` job + gate.needs entry
```

### Pattern 1: Slot-as-DATA, one level up (MREPO-01)
**What:** `workspace.toml` is byte-for-byte in the GEN-03 idiom — a header comment naming its
consumers (loader + gate), pure data, no logic.
**When to use:** The manifest itself. Mirror the `harness/project.toml` header block verbatim.
**Example (recommended shape — field names are Claude's discretion):**
```toml
# Source: mirror of harness/project.toml header idiom (verified in-repo)
# WORKSPACE manifest — the multi-repo SINGLE SOURCE OF TRUTH (MREPO-01). Pure DATA, no logic.
# Consumers:
#   * tools/workspace_config/loader.py — stdlib tomllib reader; members()/edges() passthrough.
#   * tools/harness_lint/tests/test_workspace_config.py — the consistency gate (every edge's
#     contract resolves in its producer member; no member dangles). Config = SSOT, no codegen.

[workspace]
id = ""                       # "" = the generic default workspace (mirror [instance] root = "")

[[members]]
id = "member-a"
root = "tests/fixtures/workspace/member-a"     # repo-relative path (or url in a future milestone)

[[members]]
id = "member-b"
root = "tests/fixtures/workspace/member-b"

# Cross-repo edges: producer member → contract id → consumer member.
# Endpoints recommended as `repo:stage` so MREPO-03 (drift/golden) and MREPO-04 (topology) share
# ONE table — the repo part resolves member roots, the stage part is the pipeline endpoint.
[pipeline]
edges = [
  { from = "member-a:emit", to = "member-b:ingest", contract = "greeting" },
]
```

### Pattern 2: Passthrough loader (MREPO-01)
**What:** `tools/workspace_config/loader.py` mirrors `tools/harness_config/loader.py` exactly —
binary-mode `tomllib.load`, repo-root-anchored default path, raw passthrough accessors, NO
enforcement.
**Example:**
```python
# Source: tools/harness_config/loader.py (verified in-repo) — mirror its shape
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]          # loader → workspace_config → tools → root
_DEFAULT_WORKSPACE = _REPO_ROOT / "workspace.toml"

def load_workspace(path=_DEFAULT_WORKSPACE) -> dict:
    with Path(path).open("rb") as fh:                     # binary mode — tomllib requires it
        return tomllib.load(fh)

def members(cfg: dict | None = None) -> list[dict]:
    if cfg is None: cfg = load_workspace()
    return list(cfg.get("members", []))

def edges(cfg: dict | None = None) -> list[dict]:
    if cfg is None: cfg = load_workspace()
    return list(cfg.get("pipeline", {}).get("edges", []))
```

### Pattern 3: Consistency gate — config = SSOT, no codegen (MREPO-01)
**What:** `test_workspace_config.py` mirrors `test_language_config.py` + `test_pipeline_config.py`:
structural test, repo-root via `parents[3]`, iterate config / assert agreement / fail loud.
**Assertions to encode (all directly precedented):**
- Every `[[members]].id` unique; every `root` exists on disk (mirror `test_each_configured_persona_exists` / `test_each_configured_language_has_test_paths`, use `.exists()` not `.is_file()` since roots are dirs).
- Every edge `from`/`to` names a declared member (parse `repo:stage` → member id must be in the declared set) — mirror `test_pipeline_edges_are_well_formed`'s endpoint check.
- **Every edge `contract` resolves to a tracked `<producer_root>/contracts/**/<contract>.schema.json`** — the cross-repo analogue of `test_edge_contracts_have_a_tracked_schema` (which used `contracts/**` at repo root; here glob under the *producer member's* root).
- No member dangles (every declared member is referenced by ≥0 edges is fine; but no edge may reference an undeclared member — that is the "no dangling edge endpoint" check).

### Pattern 4: Reuse Phase-10 fan-out — unit = one member repo (MREPO-02)
**What:** No new engine, no new persona. The `fan-out-synthesize` skill already says a good unit is
"one per directory, subsystem, contract, or question." A **member repo** is exactly such a unit.
**When to use:** Workspace-wide reconnaissance/analysis. The orchestrator decomposes by member,
dispatches one read-only `explorer` per member (Read/Grep/Glob, `edit: deny`), each returns claims
cited to `<member_root>/...` paths conforming to `references/fan-out-return.schema.json`, the conductor
synthesizes without re-reading. **A worker never reads a sibling member** — that is what keeps any
single context from holding every repo (MREPO-02's core guarantee, already the substrate's design).
**Discretion (CONTEXT):** Reuse `/fan-out-synthesize` as the entry point. Only add a thin
workspace-scoped command if reuse ergonomics prove insufficient — if added, it MUST round-trip the
emitter and bump `EXPECTED_SKILLS`/command counts (see Pitfall 4). Prefer prose wiring
(orchestrator routing row / skill note that "a member repo is a fan-out unit") over new surface.

### Pattern 5: Repo-qualified pipeline endpoint (MREPO-04)
**What:** Generalize the `[pipeline]` edge endpoint from a bare stage id to `repo:stage`. Parsing is a
single `endpoint.split(":", 1)` → `(member_id, stage)`. A bare stage (no colon) remains a
single-repo edge (backward-compatible with the Phase-8 core/instance topology).
**Where:** The workspace consistency gate parses `repo:stage`; the cross-repo drift/golden resolvers
use the `repo` half to pick the member root. Keep the Phase-8 `test_pipeline_config.py` (core, bare
stages) UNCHANGED — the generalization lives in the new workspace gate so the core default stays a
generic single-repo `source→sink` line (GEN-04 green).

### Anti-Patterns to Avoid
- **Re-parametrizing what is already parametrized.** `run_gate` and the drift CLI already accept
  `contracts_dir`/`baseline`; `run_golden_case` already accepts `golden_dir`. Do NOT add new
  signatures — pass member-scoped values into the existing ones.
- **Folding cross-repo gates into per-repo CI.** CONTEXT mandates a *separate* workspace job (mirror
  emit-drift/stale-derived). Do not touch the existing `drift`/`golden` jobs' semantics.
- **A single shared workspace manifest at `contracts/.hashes/`.** Each member keeps its OWN manifest
  (`build_manifest` keys are relative to `contracts_dir.parent`; example already proves per-tree
  baselines). Cross-repo drift iterates member manifests + checks edges — it does not build one giant
  manifest.
- **Members outside the repo in the demo.** Keep the fixture a subtree of `REPO_ROOT` (Pitfall 1).
- **Editing the Phase-8 core `[pipeline]` gate to accept `repo:stage`.** That would leak workspace
  semantics into the single-repo core default. Generalize in the new workspace gate only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parse `workspace.toml` | A hand TOML reader | stdlib `tomllib` (binary read) | Exactly what `harness_config.load_project` uses; zero dep. |
| Per-member schema hashing | A new hasher | `tools.contract_hash.build_manifest(contracts_dir=<member>/contracts)` | RFC 8785 + SHA-256 already correct; keys already tree-relative. |
| Drift classification | New breaking/non-breaking logic | `tools.contract_drift.classify()` / `run_gate()` | Already parametrized per contracts tree; CI already gates two trees this way. |
| Golden normalize+diff across repos | New comparator | `golden_runner.compare()` / `run_golden_case(golden_dir=)` | §4.3-4.6 canonicalizing compare; never byte-diff. |
| Dispatch N workers over members | A workspace orchestrator/daemon | Phase-10 `fan-out-synthesize` (runtime-native `task`/`Task`) | CONTEXT forbids a bespoke engine; substrate is reuse-as-is. |
| Project new surface to both runtimes | Hand-write `.opencode/`+`.claude/` | Re-run `python -m tools.harness_emit` | Glob discovery; byte-identical, validated, no model id. |
| core→member dependency guard | A bespoke import scanner | Clone `test_core_no_example_dep.py` (git ls-files + token scan) | Live negative-controls + sanctioned-pointer exemption already solved. |

**Key insight:** This phase's value is *disciplined reuse*. Almost every "new" capability is a
member-scoped invocation of a CLI/function that already accepts the scoping parameter. The only
genuinely new code is: `workspace.toml` (data), the `workspace_config` loader (≈40 lines mirroring
`harness_config`), two gate tests (mirroring existing gates), a small cross-repo edge-resolution
check, one `_confine` widening, and one CI job.

## Runtime State Inventory

> Included because this phase adds config + a new manifest that other tools resolve against. This is
> not a rename/migration, but the state-resolution surface is worth an explicit inventory.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None** — no databases/datastores; `workspace.toml` + per-member manifests are the only new persisted artifacts, both git-tracked. | none |
| Live service config | **None** — no external service holds workspace state (model b is manifest-first; daemon/remote-fetch explicitly deferred). | none |
| OS-registered state | **None** — no OS-level registrations; CI is the only automation surface (a new `workspace` job in `ci.yml`). | add CI job |
| Secrets/env vars | `DOTNET_ROOT` / `$HOME/.dotnet` read by `golden_runner.resolve_dotnet()` (unchanged); `GOLDEN_APPROVE_HUMAN` drift-approval token (unchanged). No new secret/env names introduced. | none |
| Build artifacts / committed-derived | Each member repo carries its OWN `contracts/.hashes/manifest.json` (committed-derived baseline, like `examples/log-parser/contracts/.hashes/manifest.json`). The 2-member fixture must ship pre-baselined manifests or the drift gate has nothing to compare. | generate fixture manifests via `python -m tools.contract_hash.hash --write --contracts-dir <member>/contracts --manifest <member>/contracts/.hashes/manifest.json` |

**Emitter-owned derived surface:** If a new command/skill is added, `.opencode/` + `.claude/` +
`opencode.json` + `emit-manifest.json` + the `AGENTS.md` managed block are re-emitted (machine-write,
CI-verified by `emit-drift`). If NO new surface is added, none of these change.

## Common Pitfalls

### Pitfall 1: `golden_runner._confine` rejects member roots outside the repo
**What goes wrong:** `_confine` (runner.py L88-102) allows only `REPO_ROOT`, `/tmp`, and `$TMPDIR`.
A golden case whose seed/baseline lives under a member repo *outside* `REPO_ROOT` raises
`GoldenRunnerError("path escapes confinement")`.
**Why it happens:** Phase-1 hardening confined paths to repo+temp against traversal (T-06-02).
**How to avoid:** For the minimal demo, **keep members INSIDE `REPO_ROOT`** (`tests/fixtures/workspace/...`)
so confinement passes unchanged. For the general workspace-aware resolution, **widen `_confine`'s
`allowed_roots` to include the declared member roots** (resolved from `workspace.toml`), threaded in as
a parameter — do not remove the guard, extend its allowlist. Add a negative-control test proving a
path outside every member root is still rejected.
**Warning signs:** `GoldenRunnerError` on a cross-repo golden case; a member root that is an absolute
path or `../` sibling.

### Pitfall 2: `build_manifest` key-base assumption across member roots
**What goes wrong:** `build_manifest(contracts_dir)` keys paths relative to `contracts_dir.parent`
(hash.py L50-59), so keys look like `contracts/...`. If you point it at `<member>/contracts`, keys are
still `contracts/...` (good — each member's manifest is self-relative), but a naive cross-member
*merge* would collide identical `contracts/...` keys across members.
**Why it happens:** The base is `.parent`, deliberately, so real-tree and tmp-tree keys match.
**How to avoid:** Do NOT merge member manifests. Gate each member's manifest against its OWN baseline
(the drift CLI's `--contracts-dir`/`--baseline` per member — exactly the CI `drift` job's two-tree
pattern). The cross-repo layer is a *separate* edge-resolution check, not a merged manifest.
**Warning signs:** Duplicate-key overwrites; a single `.hashes/manifest.json` claiming to cover
multiple repos.

### Pitfall 3: GEN-04 guard sees `workspace.toml` pointer lines
**What goes wrong:** `test_core_no_example_dep.py` scans `git ls-files tools harness libs`.
`workspace.toml` at repo root is NOT under those roots, so member `root =` paths there won't trip the
*existing* example-dep guard. BUT the NEW `test_core_no_workspace_member_dep.py` must itself define a
sanctioned pointer exemption for `workspace.toml`'s `root =` lines (mirror the `[instance] root` /
`persona =` / `test_paths =` exemption in the existing guard, L81-113), or the workspace-member guard
will flag the manifest's own member-path data as a leak.
**Why it happens:** The manifest is the ONE sanctioned place a config file names a member — the same
ADR-0002(c) pattern the instance pointer uses.
**How to avoid:** In the new guard, exempt `workspace.toml`'s `root =` (and any `from`/`to` endpoint)
lines exactly as the existing guard exempts `project.toml`'s pointer lines; keep the exemption
**key-scoped** (a non-pointer `member` leak must still flag — mirror
`test_negative_control_flags_nonexempt_project_toml_leak`). Also: `tools/workspace_config/loader.py`
must NOT hardcode any member path — it reads `workspace.toml` at runtime, so it carries no member
token and passes the guard cleanly.
**Warning signs:** The new guard reds on `workspace.toml`; the loader hardcodes `tests/fixtures/...`.

### Pitfall 4: Emitter anti-sprawl counts (`EXPECTED_SKILLS` / `EXPECTED_PERSONAS`)
**What goes wrong:** `validate.check_skill_set` asserts the emitted skill set EQUALS
`EXPECTED_SKILLS` (caps.py L129 — currently 11). Adding a skill without bumping the frozenset fails
the emit validation; the command index is discovered by glob (no count) but the `AGENTS.md` managed
block + `emit-manifest.json` + `.opencode`/`.claude` trees all change and the `emit-drift` CI job
fails until re-emitted and committed.
**Why it happens:** Deliberate anti-sprawl gate (P8).
**How to avoid:** Prefer NO new surface (wire fan-out via prose in existing orchestrator/skill —
CONTEXT allows this). If a thin workspace command/skill IS added: bump the relevant frozenset in
`caps.py`, re-run `python -m tools.harness_emit`, commit the regenerated trees, ensure no real model
id (placeholder-tier only), and update the emitter fixture twins (`.ambr` snapshots + command count).
**Warning signs:** `check_skill_set` failure; `emit-drift` job red on `git diff --exit-code`.

### Pitfall 5: The 2-member fixture has no baseline → gates no-op or error
**What goes wrong:** Drift needs a committed `manifest.json` per member; golden needs a
`baseline.verified.tsv`; a workspace with declared members but no baselined artifacts either errors
or silently passes an empty gate (the CI `contract-check` job already guards against silent no-op
with a VISIBLE SKIP — mirror that discipline).
**How to avoid:** Ship the fixture fully baselined: per-member `contracts/.hashes/manifest.json`
(via `contract_hash --write`), one cross-repo edge, and one golden case that spans the edge with a
committed `.verified` baseline. Print a visible SKIP if a workspace declares zero edges (mirror
CI `contract-check` L113-115).
**Warning signs:** A gate that passes on an empty/edge-less workspace without saying so.

## Code Examples

### Cross-repo drift: reuse `run_gate` per member + edge resolution
```python
# Source: tools/contract_drift/drift.py::run_gate + tools/contract_hash.build_manifest (verified in-repo)
from pathlib import Path
from tools.contract_drift.drift import run_gate
from tools.contract_hash.hash import build_manifest
from tools.workspace_config import load_workspace, members, edges

def workspace_drift(ws_path=None) -> dict:
    cfg = load_workspace(ws_path) if ws_path else load_workspace()
    root = Path(__file__).resolve().parents[2]              # or workspace.toml's dir
    by_id = {m["id"]: root / m["root"] for m in members(cfg)}
    results = {}
    # 1) per-member drift — verbatim reuse (each member has its own .hashes/manifest.json)
    for mid, mroot in by_id.items():
        cdir = mroot / "contracts"
        results[mid] = run_gate(contracts_dir=cdir, baseline_path=cdir / ".hashes" / "manifest.json")
    # 2) cross-repo edge resolution — producer contract exists; (consumer expectation check)
    for edge in edges(cfg):
        producer = by_id[edge["from"].split(":", 1)[0]]      # repo:stage → repo
        schemas = {p.name.removesuffix(".schema.json")
                   for p in (producer / "contracts").rglob("*.schema.json")}
        assert edge["contract"] in schemas, (
            f"edge {edge!r}: contract not tracked in producer {edge['from']!r}")
    return results
```

### Repo-qualified endpoint parse (MREPO-04)
```python
def split_endpoint(endpoint: str) -> tuple[str | None, str]:
    """`repo:stage` → ('repo','stage'); bare `stage` → (None,'stage') (single-repo, backward-compat)."""
    if ":" in endpoint:
        repo, stage = endpoint.split(":", 1)
        return repo, stage
    return None, endpoint
```

### Generalized GEN-04 guard (skeleton — clone the example-dep guard)
```python
# Source: tools/harness_lint/tests/test_core_no_example_dep.py (verified in-repo) — mirror it
# Scan git ls-files over ("tools","harness","libs"); forbid member-root path tokens in core files;
# EXEMPT workspace.toml `root =` / edge `from`/`to` pointer lines (key-scoped, ADR-0002(c) precedent);
# include a live negative control (synthetic member-path ref IS flagged) + a non-pointer leak control.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-project config slot (`harness/project.toml` `[instance]`) | Workspace manifest one level up (`workspace.toml` `[workspace]` + `[[members]]`) | This phase (γ) | Multi-repo declared as ONE workspace; same slot-as-DATA discipline. |
| Drift gates one contracts tree (root) + one example tree | Drift iterates N member trees + resolves cross-repo edges | This phase (MREPO-03) | Contract-first extends across repo boundaries; reuse of already-parametrized `run_gate`. |
| Pipeline edge endpoint = bare stage (single repo) | Endpoint = `repo:stage` (may cross a repo boundary) | This phase (MREPO-04) | Topology spans repos; core default stays single-repo (GEN-04). |
| Fan-out unit = directory/subsystem | Fan-out unit = member repo | This phase (MREPO-02) | Same Phase-10 substrate; workspace-level synthesis, no single context holds all repos. |

**Deprecated/outdated:** none — this phase is purely additive over v1.0+α+β.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `workspace.toml` field names (`[workspace]`, `[[members]]` id/root, `[pipeline].edges` with `repo:stage` endpoints) are a recommendation; CONTEXT explicitly leaves exact names to the planner. | Standard Stack / Pattern 1 | Low — planner may rename; structure/idiom is the load-bearing part, not the names. |
| A2 | A single edge table with `repo:stage` endpoints can serve BOTH MREPO-03 (drift/golden member resolution) and MREPO-04 (topology). | Alternatives / Pattern 5 / Open Q1 | Medium — if planner prefers a separate repo-level `{producer,contract,consumer}` table, drift/topology use two tables instead of one. Both satisfy the requirements. |
| A3 | The minimal 2-member fixture should live inside `REPO_ROOT` (e.g. `tests/fixtures/workspace/`) to avoid `_confine`/CI-checkout issues. | Structure / Pitfall 1 | Low — CONTEXT says "two tiny member repos… minimal"; in-repo subtree matches that and is safest. |
| A4 | No new agent/command/skill is strictly required (fan-out reuse can be prose-wired), so the emitter may not need re-running at all. | Pattern 4 / Pitfall 4 | Low — if a thin command IS added, the emit round-trip + count bumps are well-precedented (Phase-10 did exactly this). |
| A5 | `tools/workspace_config` should be a NEW uv member paralleling `tools/harness_config` (rather than reusing `harness_config.load_project` directly). | Alternatives | Low — either works; the parallel module matches the pattern the plan-checker expects. |

## Open Questions

1. **One edge table or two? — RESOLVED (planning): single `repo:stage` edge table chosen.** Recommend a single `[pipeline].edges` table with `repo:stage`
   endpoints (repo part → drift/golden member resolution; stage part → topology). CONTEXT phrases
   MREPO-01 as "producer repo → contract id → consumer repo" and MREPO-04 as "repo-qualified stage."
   - What we know: Both are satisfiable; a unified `{from:"repo:stage", to:"repo:stage", contract}`
     table subsumes the repo-level form.
   - What's unclear: Whether the planner wants an explicit repo-level dependency view too.
   - Recommendation: Unify on `repo:stage`; the consistency gate derives the repo-level
     producer/consumer from the endpoints. Field naming is planner discretion (A1).
   - **RESOLVED (planning):** Adopted the single `[pipeline].edges` `repo:stage` table — one table
     serves both MREPO-03 (repo half → member resolution) and MREPO-04 (stage half → topology); the
     consistency gate derives the repo-level producer/consumer from the endpoints. See 11-01 Task 1.

2. **Does the general (non-demo) case need remote/url member roots? — RESOLVED (planning): local-only roots + commented `# url =` seam.** CONTEXT defers remote-repo
   fetching (out of scope for model b). Recommend: `root` is a repo-relative (or absolute local) path
   only; leave a commented `# url = ...` seam for the future milestone, but the gate/drift/golden
   resolve local paths only this phase.
   - **RESOLVED (planning):** Member `root` is a repo-relative local path this phase; a commented
     `# url = ...` seam is added to `workspace.toml` for the deferred remote-repo milestone. See
     11-01 Task 1 + CONTEXT Deferred Ideas.

3. **Should `_confine` widening land now or only for the demo? — RESOLVED (planning): widen now, threaded param.** Recommend widening `_confine` to
   accept declared member roots as a threaded parameter now (small, testable, negative-control
   guarded) so the mechanism is real even though the demo members sit inside the repo — matches
   "ship mechanism + minimal fixture."
   - **RESOLVED (planning):** `_confine` is widened now via an additive threaded `allowed_roots`
     parameter with a negative-control test — the escape guard is extended, never removed. See
     11-03 Task 2.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | all new tooling | ✓ | 3.11.15 | — |
| `tomllib` | manifest parse | ✓ (stdlib 3.11+) | — | — |
| uv | test/workspace | ✓ | 0.11.27 | — |
| pytest | gates | ✓ | 8.4.x (uv.lock) | — |
| `rfc8785` | contract_hash (reused) | ✓ (existing dep) | 0.1.4 | — |
| .NET 10 SDK | golden `.NET` parity (example leg only) | ✗ (egress-blocked in this env) | — | Demo uses the `identity` converter (`run_golden_case(converter="identity")`) — no .NET needed; .NET legs run on GitHub runners (CI `golden` job installs 10.0.100). |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** .NET 10 SDK — the cross-repo golden **demo** should use the
language-agnostic `identity` converter (already in `runner.py`) so the fixture goes green without .NET,
exactly as the root `sample/greeting` generic golden does. Reserve real .NET parity for the example/CI
leg.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (via uv workspace) |
| Config file | root `pyproject.toml` `[tool.pytest]` `testpaths` (tools/ + libs/python; excludes examples/) |
| Quick run command | `uv run pytest tools/workspace_config tools/harness_lint/tests/test_workspace_config.py -x` |
| Full suite command | `uv run pytest` (core: tools/ + libs/python — includes GEN-03/GEN-04 guards) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MREPO-01 | Manifest loads; edges resolve; no dangling member; each edge contract tracked in producer | unit/structural | `uv run pytest tools/harness_lint/tests/test_workspace_config.py -x` | ❌ Wave 1 |
| MREPO-01 | Loader passthrough (`load_workspace`/`members`/`edges`) | unit | `uv run pytest tools/workspace_config/tests -x` | ❌ Wave 1 |
| MREPO-03 | Cross-repo drift: per-member `run_gate` + producer-contract resolution fails on drift | integration | `uv run pytest tools/contract_drift -x` (new cross-repo case) | ❌ Wave 3 |
| MREPO-03 | Workspace-aware golden: `run_golden_case` resolves member `golden_dir`; `_confine` widened | integration | `uv run pytest tools/golden_runner -x` (new cross-repo case + negative control) | ❌ Wave 3 |
| MREPO-04 | Repo-qualified `repo:stage` endpoints parse + gate | unit | (in `test_workspace_config.py`) | ❌ Wave 2 |
| MREPO-04 | core → workspace-member no-dependency + live negative controls + pointer exemption | guard | `uv run pytest tools/harness_lint/tests/test_core_no_workspace_member_dep.py -x` | ❌ Wave 2 |
| MREPO-02 | Fan-out reuse wiring (orchestrator/skill routes a member as a unit); optional command round-trips emitter | structural | `uv run pytest tools/harness_emit -x` (only if new surface) | ❌ Wave 4 (only if new surface) |
| cross-cutting | Full core suite green (no regression in existing 537+ tests) | full | `uv run pytest` | ✅ existing |

### Sampling Rate
- **Per task commit:** the quick run for the touched module (`test_workspace_config.py` / the extended tool's own dir).
- **Per wave merge:** `uv run pytest` (full core suite — GEN-03/GEN-04 guards included) + `uv run python -m tools.harness_emit && git diff --exit-code …` if any surface changed.
- **Phase gate:** full suite green + new workspace CI job green + `emit-drift`/`stale-derived` clean before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/workspace_config/{__init__.py,loader.py,pyproject.toml,tests/}` — new uv member (mirror `tools/harness_config`).
- [ ] `tools/harness_lint/tests/test_workspace_config.py` — MREPO-01 consistency gate.
- [ ] `tools/harness_lint/tests/test_core_no_workspace_member_dep.py` — MREPO-04 GEN-04 twin.
- [ ] `tests/fixtures/workspace/member-{a,b}/…` — 2-member demo, pre-baselined manifests + one spanning golden case.
- [ ] New `tools/contract_drift` + `tools/golden_runner` cross-repo test cases (extend existing suites).
- [ ] Register `tools/workspace_config` in `uv.lock` (`uv sync --all-packages`) — new in-repo member; bare `uv sync` prunes tool-member deps (STATE precedent 02-01).

## Security Domain

> `security_enforcement` key absent in config → treated as enabled. This phase is config/tooling with
> no auth/network/session/crypto surface, so most ASVS categories are N/A; the live surface is
> untrusted-manifest parsing and filesystem path resolution.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth surface) |
| V3 Session Management | no | — |
| V4 Access Control | partial | Constitution-plane write-deny unchanged (per-repo human-owned); machines gate / humans ratify preserved. |
| V5 Input Validation | **yes** | `workspace.toml` is parsed input — the consistency gate validates every member/edge; stdlib `tomllib` (no eval); reject undeclared endpoints / missing roots loud. |
| V6 Cryptography | no | Reuses existing RFC 8785 + SHA-256 (contract_hash) — never hand-rolled. |
| V12 Files & Resources | **yes** | Path confinement — `golden_runner._confine` + `contract_hash` symlink defense-in-depth (root-not-in-parents check) must extend to member roots without weakening the guard. |

### Known Threat Patterns for {TOML-manifest-driven tooling}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious `root`/edge path escaping the workspace (`../`, absolute) | Tampering / Elevation | Resolve + confine to declared member roots; keep `_confine` allowlist (widen, never remove); negative-control test proves an out-of-root path is rejected. |
| Symlinked member `contracts/` pointing outside its tree | Tampering | Reuse `build_manifest`'s existing `root not in resolved.parents` symlink defense (hash.py L54-57). |
| Silent no-op gate on an empty/edge-less workspace | Repudiation (false pass) | Visible SKIP on zero edges (mirror CI `contract-check` L113-115). |
| Subprocess injection via member/edge strings | Tampering | All subprocess calls are `shell=False` argv lists (drift `_git_show`, golden `run_converter`) — never interpolate manifest data into a shell (also the CI "no event interpolation" posture). |
| Agent self-blessing a cross-repo golden/contract | Elevation | Constitution plane stays human-owned per repo; `GOLDEN_APPROVE_HUMAN` + CODEOWNERS unchanged. |

## Project Constraints (from CLAUDE.md / AGENTS.md)

- **Contract-first:** `contracts/` (per member) is SSOT; code that disagrees with a contract is wrong. Cross-repo drift enforces this across boundaries.
- **Two-plane memory:** derived plane is machine-written + CI-verified, never hand-edited. Per-member `.hashes/manifest.json` and any emitter output are committed-derived; regenerate, never hand-edit.
- **Machines gate, humans ratify:** constitution plane (contracts/adr/golden) human-owned per repo — unchanged by this phase.
- **GEN-04 single-direction:** core (`tools`/`harness`/`libs`) depends on NO instance AND (new this phase) NO workspace member. Enforced by the new guard twin.
- **Emitter round-trip:** any new agent/skill/command is authored in `harness/` and projected to BOTH `.opencode/` (primary) + `.claude/` (secondary) by `tools.harness_emit`; **no model identifier** in any repo artifact (placeholder-tier only).
- **Polyglot boundary = process/file/DB only:** golden comparison is always via the §4.3-4.6 core, never a byte-diff; A-model CLI spawn with `shell=False`.
- **Model identity:** no model id in commits/PRs/agents/config (placeholder `provider/explorer-tier` only).
- **PR/CI enforcement preferred over heavy per-commit hooks:** the cross-repo gate is a separate CI job (mirror emit-drift/stale-derived), not a per-commit local hook.

## Sources

### Primary (HIGH confidence — read in-repo this session)
- `harness/project.toml` — GEN-03/PIPE-01 slot-as-DATA idiom + header-comment consumer naming.
- `tools/harness_config/loader.py` — `tomllib` passthrough loader shape to mirror.
- `tools/harness_lint/tests/test_language_config.py` + `test_pipeline_config.py` — consistency-gate precedent (SSOT, no codegen; endpoint/contract-resolution checks).
- `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 guard (git ls-files scan, sanctioned pointer exemption, live negative controls) to generalize.
- `tools/contract_drift/drift.py` — `run_gate(contracts_dir, baseline_path)`, `classify()`, CLI `--contracts-dir`/`--baseline` (already cross-tree).
- `tools/contract_hash/hash.py` — `build_manifest(contracts_dir)` key-base + symlink defense.
- `tools/golden_runner/runner.py` — `run_golden_case(golden_dir=)`, `compare()`, `_confine()` allowed-roots, `identity` converter.
- `.github/workflows/ci.yml` — separate-job gate pattern (drift/golden/emit-drift/stale-derived) + `gate.needs` fan-in + config-derived matrix.
- `tools/harness_emit/generate.py` + `tools/harness_lint/caps.py` — glob-discovery emitter, `EXPECTED_SKILLS`/`EXPECTED_PERSONAS` anti-sprawl counts.
- `harness/skills/fan-out-synthesize/SKILL.md` + `harness/commands/{fan-out-synthesize,pipeline,add-language}.md` — Phase-10 substrate + command idiom.
- `examples/log-parser/project.toml` + `examples/log-parser/tests/test_pipeline_topology.py` + `examples/log-parser/contracts/.hashes/manifest.json` — instance-overlay path-local load precedent + per-tree manifest.
- `.planning/{REQUIREMENTS.md,STATE.md}`, `CLAUDE.md`, root `AGENTS.md`, `11-CONTEXT.md` — requirements, locked decisions, non-negotiables, phase history.

### Secondary / Tertiary
- None required — no external documentation needed (no new packages; all patterns are in-repo).

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — every reused module read in-repo; no external deps; versions verified in env.
- Architecture: **HIGH** — every extension point is an already-parametrized function/CLI with a read precedent; decisions locked by CONTEXT.
- Pitfalls: **HIGH** — each pitfall traced to a specific line (`_confine` L88-102, `build_manifest` L50-59, GEN-04 exemption L81-113, `check_skill_set` caps L129).

**Research date:** 2026-07-13
**Valid until:** stable (in-repo patterns; ~30 days) — no fast-moving external surface.
