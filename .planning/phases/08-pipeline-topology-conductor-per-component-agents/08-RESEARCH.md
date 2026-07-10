# Phase 8: Pipeline-Topology Conductor + Per-Component Agents - Research

**Researched:** 2026-07-10
**Domain:** Agent-harness authoring (config-as-data TOML slot + persona/command/skill markdown + Python structural-gate tests). No external runtime; pure in-repo files.
**Confidence:** HIGH (entire surface is local codebase, verified by direct read; no stale-training exposure)

## Summary

This phase evolves the harness agent model from per-**language** to pipeline-**aware**, entirely by
adding authored artifacts and one new data slot to an already-mature, well-gated codebase. Every
mechanism this phase needs already has a working precedent in the repo: a **pure-data TOML slot**
(`[[languages]]`) with a **thin stdlib loader** (`tools/harness_config/loader.py`) and a **consistency
gate** (`test_language_config.py`); a **neutral fill-in-the-blanks agent template**
(`harness/agents/templates/engineer.md`) instantiated by an **order-enforcing scaffold command**
(`/add-language`); **anti-sprawl frozenset gates** for personas/skills/commands; and the **GEN-04
core→example one-directional dependency guard**. Phase 8 is almost entirely "clone the `[[languages]]`
pattern for `[[components]]`, clone the `engineer.md` template for `component-engineer`, evolve the
existing single `orchestrator` in place, and demonstrate concretely under `examples/log-parser/`."

The single load-bearing design decision (Open Question #1) is **where the concrete 4-component
log-parser topology lives**. Because edge contracts bind to domain schema names (`standard-log`,
`equipment-progress`) and the GEN-04 guard flags those exact tokens anywhere under `tools/`,
`harness/`, `libs/`, the concrete topology **cannot** sit in the core `harness/project.toml` without
growing the guard's line-exemption surface. The clean, ADR-0002-faithful answer is a **new
`examples/log-parser/project.toml` instance overlay** (under `examples/`, which GEN-04 never scans),
with the core `harness/project.toml` carrying only a **generic default** topology. This also mirrors
the phase text literally ("the instance's project.toml slot").

**Primary recommendation:** Clone the proven `[[languages]]` slot → loader passthrough → consistency
gate triad for a new `[[components]]` + `[pipeline]` topology slot; keep the **generic default** in
core `harness/project.toml` and put the **concrete log-parser 4-component topology in a new
`examples/log-parser/project.toml`** whose consistency test runs in the example test leg (not the
core suite). Evolve the existing `orchestrator` in place (still `mode: primary`, still the only
entry in `EXPECTED_PERSONAS`). Add `component-engineer` to `harness/agents/templates/`, a
`pipeline-map` core skill (grow `EXPECTED_SKILLS` 8→9), and a `/pipeline` command (auto-covered by
the glob-driven command gates). Append **ADR-0003** to record the topology slot + instance-overlay
mechanism (constitution-plane write → lands via `GOLDEN_APPROVE_HUMAN`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Generic topology declaration (shape/default) | Core config data (`harness/project.toml`) | — | PIPE-01: pure DATA slot, domain-neutral, mirrors `[[languages]]` |
| Topology read/passthrough | Core loader (`tools/harness_config/loader.py`) | — | Thin stdlib `tomllib` reader; no enforcement logic here |
| Topology consistency enforcement | Core gate (`tools/harness_lint/tests/`) | — | Mirror `test_language_config.py`; SSOT tamper-evidence |
| Topology-aware routing | Core persona (`harness/agents/orchestrator.md`) | — | PIPE-02: evolve the single primary in place |
| Per-component engineer scaffold | Core template (`harness/agents/templates/`) | Core command (`/component`) | PIPE-03: neutral fill-in-the-blanks, instance instantiates |
| Concrete 4-component demo | Instance (`examples/log-parser/`) | — | PIPE-04: domain-specific, must stay off core (GEN-04) |
| Pipeline visualization/trace | Core skill + command (`pipeline-map`, `/pipeline`) | — | PIPE-05: neutral mechanism |
| Core→example no-dependency + anti-sprawl | Core gates (`test_core_no_example_dep.py`, template/persona tests) | — | PIPE-06: extend existing guards |

---

<user_constraints>
## User Constraints

> No `08-CONTEXT.md` exists in the phase directory at research time. The constraints below are the
> **locked decisions captured in the ROADMAP Phase 8 entry and the task brief** — the planner MUST
> honor them verbatim.

### Locked Decisions
- **Build BOTH** the neutral core mechanism (topology slot + conductor + `component-engineer`
  template) **AND** the concrete `examples/log-parser/` demonstration (4 component agents +
  instance topology). Not one or the other.
- **EVOLVE the existing primary `orchestrator`** into the topology-aware conductor. **No second
  primary, no new tier.** The persona set stays exactly one primary.
- Core (`harness/`, `tools/`, `contracts/` generic, `libs/python`) stays **domain-neutral and
  depends on NO instance** (GEN-04). The new topology slot in core carries a **generic default**
  with zero log-parser specifics.
- The pipeline topology is a **pure DATA slot** (like `[instance]`/`[[languages]]`). Do NOT hardcode
  parser/converter/scheduler/collector into the core — those belong only in the log-parser instance.
- The new `component-engineer` template must be **added to the persona anti-sprawl exemption** (like
  `engineer.md`); the evolved conductor must stay a **single primary orchestrator**.
- **Single-source → multi-runtime:** agents authored once, emitted to both `.opencode/` and
  `.claude/`. **Phase 7's emit surface must remain unaffected.**
- **Language boundary = process/file/DB only.** The conductor models edge CONTRACTS between stages,
  not in-process calls.

### Claude's Discretion
- Exact TOML table names/keys for the topology slot (`[[components]]` fields; `[pipeline]` vs
  `[[edges]]` for edges) — recommend a shape (see Standard Stack).
- Whether `/pipeline` is a new command or an extension of `/component` (recommend: new command +
  `/component` extension for the scaffold half).
- Whether the topology consistency gate is a new test file or extends `test_language_config.py`
  (recommend: new `test_pipeline_config.py` mirroring it).

### Deferred Ideas (OUT OF SCOPE)
- Actual pipeline component IMPLEMENTATION logic (parser/converter/scheduler/collector algorithms) —
  the harness is the deliverable, not the components (per REQUIREMENTS "Out of Scope").
- B-model gRPC/message-queue topology (EXT-01, v2) — keep the A-model file/DB/CLI boundary.
- Runtime execution of the routing (opencode plugin live-loading) — authored-source only, consistent
  with the Phase-4/Phase-7 authored-then-emit posture.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-01 | Generic pipeline-topology DATA slot in `harness/project.toml` (`[[components]]`/`[pipeline]`: id·stage·language ref·edge contracts consumes/produces) + `loader.py` passthrough + GEN-03-style consistency gate; zero example dependency (GEN-04 green). | `[[languages]]` slot + `loader.languages()` + `test_language_config.py` are the exact template to clone (see Standard Stack, Pattern 1). |
| PIPE-02 | Evolve the primary `orchestrator` into a topology-aware conductor: read declared topology, model parser→converter→scheduler→collector dataflow + edge contracts, route by stage/component (not only language). Updated routing table + intake. Stays ONE primary. | `harness/agents/orchestrator.md` current routing table + intake procedure (Pattern 2); `EXPECTED_PERSONAS` gate keeps it single-primary. |
| PIPE-03 | Neutral `component-engineer` template under `harness/agents/templates/` (anti-sprawl-exempt like `engineer.md`) + scaffold/register command binding per-component agents to declared topology components (`/component` extension or complement). | `engineer.md` template + `/add-language` order-enforcing scaffold are the pattern (Pattern 3). |
| PIPE-04 | End-to-end demo in `examples/log-parser/`: 4 component agents (parser/converter/scheduler/collector) + log-parser topology declared in the instance's `project.toml` slot; conductor traces the full flow. | Existing `examples/log-parser/agents/dotnet-engineer.md` is the per-instance persona precedent; **new instance overlay file** (Open Question #1). |
| PIPE-05 | Executable pipeline model: topology-trace `pipeline-map` skill + `/pipeline` command that visualizes/traces dataflow and locates the right component agent. | Skill format + `EXPECTED_SKILLS` gate (Pattern 4); glob-driven command gates auto-cover `/pipeline`. |
| PIPE-06 | Guards/tests: GEN-04 core→example no-dependency guard + persona anti-sprawl extended to conductor + `component-engineer` template; topology-slot consistency gate. | `test_core_no_example_dep.py`, `test_agents.py`, new `test_pipeline_config.py` (Common Pitfalls, Validation Architecture). |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md / AGENTS.md / ADRs)

Treat these with locked-decision authority; research must not recommend anything that contradicts them.

- **Contract-first.** `contracts/` is the single source of truth; code that disagrees with a
  contract is wrong. A contract/schema change trips the drift gate and needs a paired golden update.
- **Polyglot §4.3–4.6 boundary invariants.** Cross-language equivalence only after the shared
  canonicalization core. Language boundary = **process/file/DB only** — never in-process object
  passing. (Directly constrains PIPE-02: conductor models edge CONTRACTS, not in-process calls.)
- **Constitution plane is gated — machines gate, humans ratify.** No agent writes to `contracts/`,
  `docs/adr/`, or `golden/`. ADRs are append-only / supersede-not-edit. An intentional
  constitution-plane change lands through the **live** gates via the human-set `GOLDEN_APPROVE_HUMAN`
  token — never `--no-verify`, never a bash bypass. (Constrains the ADR-0003 landing.)
- **Derived plane is not hand-edited.** `.memory/derived/` regenerates from `tools/memory_regen`.
- **Model-identity constraint.** No model identifiers in repo artifacts (commits, PRs, code
  comments, persona `model:` fields — only the `provider/explorer-tier` / `provider/implementer-tier`
  placeholder tokens are permitted).
- **ADR-0002 (c):** the active instance declares toolchains as DATA in `harness/project.toml`; the
  core hardcodes no language. `[instance] root` / `persona =` / `test_paths =` are the ONE sanctioned
  place a core-plane file may name an instance path (GEN-04 line exemption).
- **GEN-04 invariant:** nothing under `tools/`, `harness/`, `libs/` imports or path-references
  `examples/**`, nor carries the moved-asset prose tokens (`standard-log`, `equipment`,
  `correction-rules`, `libs/dotnet`, `wafer`, `설비`, `dotnet-engineer`, `dotnet-conventions`,
  `normalization-catalog`, `pipeline-patterns`). **`parser`/`converter`/`scheduler`/`collector` and
  bare `dotnet`/`.NET`/`normalize`/`log-parser` are explicitly NOT flagged** (general terms).

## Standard Stack

No external packages are installed by this phase. It uses only what is already pinned and present.

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python stdlib `tomllib` | 3.11 (`requires-python >=3.11`) | Parse the topology slot in `loader.py` | Already the loader's sole dependency `[VERIFIED: tools/harness_config/loader.py]` |
| pytest | 8.4.x (`minversion = "8.4"`) | Structural gates for slot/persona/skill/command | Root `[tool.pytest.ini_options]`, `testpaths = ["libs/python", "tools"]` `[VERIFIED: pyproject.toml]` |
| uv | 0.11.x | Test runner invocation `uv run pytest` | Golden-path command `[VERIFIED: AGENTS.md]` |
| `tools/harness_lint/frontmatter.py` (`parse_frontmatter`) | in-repo | Parse agent/command/skill frontmatter in gates | Shared parser reused by every structural gate `[VERIFIED: test_agents.py imports it]` |

### Supporting (in-repo patterns to clone — NOT new deps)
| Artifact | Purpose | Clone into |
|----------|---------|------------|
| `tools/harness_config/loader.py` `languages()` | Pure passthrough helper | `components()` + `pipeline()` helpers |
| `tools/harness_lint/tests/test_language_config.py` | GEN-03 consistency gate | `test_pipeline_config.py` |
| `tools/harness_config/tests/test_loader.py` | Loader unit tests | topology loader unit tests |
| `harness/agents/templates/engineer.md` | Neutral fill-in-the-blanks persona | `component-engineer.md` template |
| `harness/commands/add-language.md` | Order-enforcing scaffold | `/component` extension for component-agent binding |
| `examples/log-parser/agents/dotnet-engineer.md` | Per-instance component-bound persona | 4 concrete component agents |

**Installation:** None. `uv sync` already resolves the workspace; no `uv add` in this phase.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `examples/log-parser/project.toml` overlay | Concrete topology in core `harness/project.toml` + grow GEN-04 exemption | Rejected — edge contracts name `standard-log`/`equipment` which GEN-04 flags; grows core→example coupling; fights success criterion 1 "ZERO example dependency in core". See Open Question #1. |
| New `test_pipeline_config.py` | Extend `test_language_config.py` | Either works; a new file keeps the GEN-03 language gate untouched and mirrors the one-file-per-concern idiom. |
| `[[components]]` + `[[edges]]` tables | Embed `consumes`/`produces` arrays inline per component | Inline arrays (recommended) are simpler and mirror `[[languages]]`; a separate `[[edges]]` table is only worth it if edges carry their own metadata. |

## Package Legitimacy Audit

**Not applicable.** This phase installs **zero** external packages — it authors in-repo markdown
(agents/commands/skills), adds a TOML data slot, extends a stdlib loader, and adds pytest structural
gates. All tooling (`tomllib`, `pytest`, `uv`, `ruff`, `pyright`) is already pinned and present from
Phases 1–6. No registry lookup or slopcheck run is warranted.

## Architecture Patterns

### System Architecture Diagram

```txt
                       harness/project.toml  (CORE, domain-neutral)
                       ┌─────────────────────────────────────────┐
                       │ [instance] root=""                        │
                       │ [[languages]]  dotnet / python            │
   PIPE-01 (generic) ─▶│ [[components]] GENERIC DEFAULT (sample)   │
                       │ [pipeline]     GENERIC DEFAULT edges       │
                       └───────────────┬───────────────────────────┘
                                       │ read (pure passthrough)
                                       ▼
        tools/harness_config/loader.py   load_project → components() / pipeline()
                                       │
              ┌────────────────────────┼─────────────────────────────┐
              ▼                        ▼                              ▼
  test_pipeline_config.py     harness/agents/orchestrator.md   /pipeline command
  (CORE consistency gate:     (CONDUCTOR: reads topology,      + pipeline-map skill
   generic slot valid,         routes by stage/component)      (trace dataflow →
   component.language ∈                                          find component agent)
   languages, GEN-04 green)
              │
              ▼  scaffold binds per-component agents from the template
     harness/agents/templates/component-engineer.md  ──(/component ext)──▶ instance agents

  ─────────────────────────────  GEN-04 boundary (core never reads below) ─────────────
                       examples/log-parser/project.toml  (INSTANCE overlay, PIPE-04)
                       ┌─────────────────────────────────────────┐
                       │ [[components]] parser·converter·          │
                       │   scheduler·collector (stage, language,   │
                       │   consumes/produces = REAL contracts)     │
                       │ [pipeline] parser→converter→scheduler→    │
                       │            collector edges                 │
                       └───────────────┬───────────────────────────┘
                                       ▼
     examples/log-parser/agents/{parser,converter,scheduler,collector}.md
     examples/log-parser/tests/test_pipeline_topology.py  (runs in EXAMPLE leg, not core suite)
```

### Recommended Project Structure (files this phase adds/edits)
```txt
harness/
├── project.toml                         # EDIT: add generic [[components]] + [pipeline] default
├── agents/
│   ├── orchestrator.md                  # EDIT: topology-aware routing table + intake (PIPE-02)
│   └── templates/
│       ├── engineer.md
│       └── component-engineer.md         # NEW: neutral component-bound persona template (PIPE-03)
├── commands/
│   ├── component.md                      # EDIT: bind a component agent from the template (PIPE-03)
│   └── pipeline.md                       # NEW: /pipeline trace command (PIPE-05)
└── skills/
    └── pipeline-map/SKILL.md             # NEW: topology-trace skill (PIPE-05) → EXPECTED_SKILLS 8→9

tools/
├── harness_config/loader.py             # EDIT: components() + pipeline() passthrough (PIPE-01)
├── harness_config/tests/test_loader.py   # EDIT/ADD: topology loader unit tests
└── harness_lint/tests/
    ├── test_pipeline_config.py           # NEW: generic topology consistency gate (PIPE-01/06)
    └── test_agents.py                    # EDIT: template anti-sprawl extension (PIPE-06)

examples/log-parser/
├── project.toml                          # NEW: instance overlay — concrete 4-component topology (PIPE-04)
├── agents/{parser,converter,scheduler,collector}.md   # NEW: 4 component agents (PIPE-04)
└── tests/test_pipeline_topology.py       # NEW: instance topology consistency (runs in example leg)

docs/adr/0003-*.md                        # NEW: append-only ADR (topology slot + instance overlay)
```

### Pattern 1: Pure-data slot → thin loader passthrough → consistency gate (clone `[[languages]]`)
**What:** The exact triad GEN-03 established. A TOML table is pure data; `loader.py` exposes a
`list[dict]`/`dict` with `cfg.get(...)`; a `harness_lint` test asserts the hardcoded consumers agree
with the config (no codegen — "derived not hardcoded" via a consistency assertion).
**When to use:** PIPE-01 topology slot.
**Recommended TOML shape (generic default in core `harness/project.toml`):**
```toml
# PIPE-01 pipeline-topology slot — pure DATA (mirrors [[languages]]). Generic default only.
# The active instance overrides these tables from its own examples/<name>/project.toml overlay.
[[components]]
id = "source"            # domain-neutral sample id (NOT parser/converter)
stage = 1
language = "python"      # must match a [[languages]].id
produces = ["sample-record"]   # generic edge-contract label
consumes = []

[[components]]
id = "sink"
stage = 2
language = "python"
consumes = ["sample-record"]
produces = []

[pipeline]
# edges as ordered stage pairs; each edge's contract is the produces∩consumes label
edges = [ { from = "source", to = "sink", contract = "sample-record" } ]
```
**Loader helpers (mirror `languages()`):**
```python
# Source: clone of tools/harness_config/loader.py languages()  [CITED: loader.py:42-50]
def components(cfg: dict | None = None) -> list[dict]:
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("components", []))

def pipeline(cfg: dict | None = None) -> dict:
    if cfg is None:
        cfg = load_project()
    return dict(cfg.get("pipeline", {}))
```
**Consistency gate (mirror `test_language_config.py`):** assert every `component["language"]` is in
`{l["id"] for l in languages()}`; every `[pipeline].edges[*].contract` appears in some component's
`produces` AND some component's `consumes` (dataflow well-formedness); stages are contiguous/ordered.

### Pattern 2: Evolve the single primary in place (no second primary)
**What:** `orchestrator.md` is `mode: primary` with a **Routing decision table** (work shape →
persona/command) and an **Intake → decompose** procedure. Topology-awareness = add rows/columns
keyed on pipeline **stage/component**, and an intake step that reads the declared topology and traces
stage→stage edge contracts before delegating.
**When to use:** PIPE-02.
**Minimal edit (keeps it ONE primary — `EXPECTED_PERSONAS` unchanged):**
- Description: add "routes by pipeline stage/component using the declared topology" alongside the
  existing language-boundary language.
- Add an intake step: "**Trace the topology** — read `[[components]]`/`[pipeline]` (via
  `tools.harness_config`); identify which stage/component the request touches and its upstream/
  downstream edge contracts."
- Routing table: add a **Component** column or new rows mapping stage → the component agent (parser/
  converter/scheduler/collector in the active instance), falling back to the language engineer when
  no component agent is declared.
**Anti-pattern:** adding a second `mode: primary` "conductor" persona — this **breaks
`test_expected_personas_present_no_sprawl`** and violates the locked "single primary" decision.

### Pattern 3: Neutral template + order-enforcing scaffold (clone `engineer.md` + `/add-language`)
**What:** `engineer.md` lives in `templates/` (excluded from the non-recursive `agents/*.md` glob →
not counted as a core persona). `/add-language` copies it into the instance, fills `<PLACEHOLDER>`s,
registers it in `project.toml`, and keeps the three edits (persona/config/matrix) in sync under a
consistency gate.
**When to use:** PIPE-03 `component-engineer` template + the `/component` scaffold extension.
**`component-engineer.md` template placeholders:** `<COMPONENT>` (e.g. parser), `<STAGE>`,
`<LANG>`/`<TOOLCHAIN>` (from the component's `language` ref → the `[[languages]]` toolchain),
`<CONSUMES>`/`<PRODUCES>` (edge contracts). Frontmatter must be `mode: subagent`, least-privilege
`bash` (component's language scope only), routing-signal description with a "use/when" trigger.

### Pattern 4: Skill authoring under the shared cap gate
**What:** `harness/skills/<name>/SKILL.md`, frontmatter `name` (== dir name, ≤64, `^[a-z0-9]+(-[a-z0-9]+)*$`)
+ `description` (≤1024, carries a "use/when" trigger, unique). Body >500 lines only WARNs. Depth goes
in `references/`. Adding a skill means adding its name to `EXPECTED_SKILLS` (currently 8).
**When to use:** PIPE-05 `pipeline-map` skill (→ `EXPECTED_SKILLS` becomes 9).

### Anti-Patterns to Avoid
- **Concrete topology in core `harness/project.toml`.** Edge contracts naming `standard-log`/
  `equipment-progress` trip GEN-04; component ids alone (`parser`…`collector`) do not, but the
  *contracts* do. Keep concrete topology in the instance overlay.
- **A core test that path-references `examples/`.** A NEW file under `tools/` containing the string
  `examples/log-parser` trips `test_core_no_example_dep.py` (only that guard file self-excludes).
  The instance topology test must live under `examples/log-parser/tests/`.
- **Duplicating the normalizer / passing objects across the boundary.** Edge contracts describe
  file/DB handoffs, not in-process calls (§4.3–4.6).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parse the topology slot | A custom TOML/regex reader | Extend `loader.py` with `tomllib` | Single reader of the SSOT; matches `languages()` |
| Enforce "derived not hardcoded" | A codegen step that emits the routing table | A **consistency test** (D-03 "codegen is overkill") | Precedent: `test_language_config.py` asserts agreement |
| Prevent core→example leakage | A bespoke import linter | Extend the existing GEN-04 guard's token/scan model | Already live, negative-control-proven |
| Instantiate per-component agents | Hand-author 4 divergent personas | Derive from `component-engineer.md` template via `/component` | Fill-in-the-blanks parity; keeps instance personas uniform |
| Frontmatter parsing in gates | Per-test fence slicing | `parse_frontmatter` from `tools.harness_lint` | Shared, already used by every structural gate |

**Key insight:** Phase 8 has near-zero novel engineering — its risk is **consistency/placement**, not
algorithms. The correct posture is "clone the established quadruple (slot/loader/gate/template) and
respect the GEN-04 boundary," which is exactly what the existing tests will enforce for you.

## Runtime State Inventory

> This is an authoring/config phase (no databases, services, OS registrations, or secrets). The
> analog of "runtime state" here is **in-code registered sets** (frozensets/expected-counts) and
> **derived artifacts** that must be updated in lockstep with new files, or gates fail.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastore holds pipeline/topology state. Verified: `grep` of `tools/` for topology found only unrelated `repo_map`/`commit_gate` matches. | none |
| Live service config | None — no external service. | none |
| OS-registered state | None. | none |
| Secrets/env vars | `GOLDEN_APPROVE_HUMAN` is the only relevant env var — required to land the new ADR-0003 (constitution-plane write) through the live commit gate. Not a new secret; existing approval token. | set token when committing `docs/adr/0003-*.md` |
| Build artifacts / in-code registered sets | (1) `EXPECTED_SKILLS` frozenset in `test_skills.py` (currently 8) must gain `pipeline-map`. (2) `EXPECTED_PERSONAS` in `test_agents.py` must stay `{orchestrator, python-engineer, code-reviewer, explorer}` (conductor is the evolved orchestrator, NOT a new entry). (3) `.memory/derived/` (repo-map, contracts-index) regenerates — new schema files (if any) flow into `contracts-index`; run `tools.memory_regen` after. (4) Root `testpaths = ["libs/python", "tools"]` — the instance topology test under `examples/` runs only via the config-derived CI leg, NOT `uv run pytest` at root. | update (1), verify (2), regenerate (3), account for (4) in Validation |

## Common Pitfalls

### Pitfall 1: Concrete edge contracts trip GEN-04 if placed in core
**What goes wrong:** Putting `produces = ["standard-log"]` or a path to
`examples/log-parser/contracts/...` in `harness/project.toml` (or in any core test) red-flags
`test_core_no_example_dep.py`.
**Why it happens:** GEN-04 scans `tools/`, `harness/`, `libs/` for `examples/` paths AND the prose
tokens `standard-log`, `equipment`, `correction-rules`, `libs/dotnet`, etc.
**How to avoid:** Keep the concrete topology in `examples/log-parser/project.toml`; keep the core
slot's default generic (`source`/`sink`/`sample-record`). Only `root`/`persona`/`test_paths` lines
are exempt in `project.toml` — do NOT rely on adding more exemptions.
**Warning signs:** `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` fails with a
`core→example dependency/prose leak` offender line.

### Pitfall 2: Accidentally creating a second primary
**What goes wrong:** Authoring a new `conductor.md` with `mode: primary`.
**Why it happens:** "Conductor" reads like a new role.
**How to avoid:** Evolve `orchestrator.md` in place; the conductor IS the orchestrator. Keep
`EXPECTED_PERSONAS` unchanged.
**Warning signs:** `test_expected_personas_present_no_sprawl` fails with "persona set drift".

### Pitfall 3: Template counted as a persona (or template left unvalidated)
**What goes wrong:** Putting `component-engineer.md` directly in `harness/agents/` makes it a 5th
persona → anti-sprawl fails. Conversely, `templates/engineer.md` is currently validated by **no**
test (the `agents/*.md` glob is non-recursive).
**How to avoid:** Put `component-engineer.md` in `harness/agents/templates/` (exempt, like
`engineer.md`). For PIPE-06 "extend anti-sprawl to the template," add a **new** small test that
validates the `templates/` dir contains exactly `{engineer, component-engineer}` and each passes the
structural rules (subagent mode, valid permission keys, routing-trigger description) — closing the
current gap where templates are unchecked.
**Warning signs:** `test_expected_personas_present_no_sprawl` fails (wrong placement), or the template
ships with malformed frontmatter that no gate catches (missing new test).

### Pitfall 4: `/pipeline` command referential integrity
**What goes wrong:** `/pipeline` with `agent: <something>` that has no `harness/agents/<agent>.md`.
**Why it happens:** `test_agent_referential_integrity.py` resolves every command's `agent:` to a real
persona file.
**How to avoid:** Set `/pipeline` `agent: orchestrator` (the conductor traces topology). It's then
auto-covered — the glob-driven command gates need no edits.

### Pitfall 5: Instance test invisible to `uv run pytest`
**What goes wrong:** `examples/log-parser/tests/test_pipeline_topology.py` never runs under root
`uv run pytest` (root `testpaths` excludes `examples/`), so a broken instance topology looks green.
**How to avoid:** Success criterion 4 ("full non-example `uv run pytest` green") is satisfied by the
CORE suite. The instance topology test runs in the **example test leg** (`test_paths` in
`project.toml` → the Phase-6 CI matrix). Ensure the planner runs BOTH legs at the phase gate.

## Code Examples

### Consistency gate skeleton (mirror `test_language_config.py`)
```python
# Source: clone of tools/harness_lint/tests/test_language_config.py  [CITED: test_language_config.py]
from tools.harness_config import components, pipeline, languages, load_project

def test_component_languages_are_declared() -> None:
    lang_ids = {l["id"] for l in languages()}
    for c in components(load_project()):
        assert c["language"] in lang_ids, f"{c['id']}: unknown language {c['language']!r}"

def test_pipeline_edges_are_well_formed() -> None:
    cfg = load_project()
    by_id = {c["id"]: c for c in components(cfg)}
    for edge in pipeline(cfg).get("edges", []):
        assert edge["from"] in by_id and edge["to"] in by_id
        assert edge["contract"] in by_id[edge["from"]].get("produces", [])
        assert edge["contract"] in by_id[edge["to"]].get("consumes", [])
```

### Template anti-sprawl extension (new small gate, PIPE-06)
```python
# NEW tools/harness_lint/tests/test_agent_templates.py (closes the templates/ validation gap)
_TEMPLATES = _AGENTS_DIR / "templates"
EXPECTED_TEMPLATES = frozenset({"engineer", "component-engineer"})

def test_templates_no_sprawl() -> None:
    names = {p.stem for p in _TEMPLATES.glob("*.md")}
    assert names == set(EXPECTED_TEMPLATES)
# + parametrized: each template is subagent-mode, permission keys ⊂ VALID, description has a trigger.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-**language** engineers (`dotnet-engineer` covers parser+converter; `python-engineer` covers scheduler+collector) | Per-**component** engineers bound to declared topology stages | This phase (PIPE) | 4 component agents in the instance; conductor routes by stage/component |
| Orchestrator routes by work-shape + language boundary | Orchestrator (conductor) also reads topology + routes by stage/component | PIPE-02 | Single primary, richer intake |
| One `harness/project.toml` holds instance language values (root="") | Add an `examples/log-parser/project.toml` overlay for concrete topology | PIPE-04 (recommended, Open Q#1) | New instance-config discovery in loader; ADR-0003 |

**Deprecated/outdated:** none — this is additive. The `pipeline-patterns` **instance** skill
(`examples/log-parser/skills/`) is about run-scenario carryover state, NOT topology; the new
`pipeline-map` **core** skill is distinct (topology trace). Keep both; names are unambiguous.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The concrete instance topology should live in a **new `examples/log-parser/project.toml`** (loader gains instance-overlay discovery), not in core `harness/project.toml`. | Open Question #1, Standard Stack | If the user prefers single-file, the plan shifts to growing the GEN-04 line-exemption; larger core coupling. Needs confirmation. |
| A2 | Adding the topology slot + instance-overlay mechanism warrants an **append-only ADR-0003** landed via `GOLDEN_APPROVE_HUMAN`. | Runtime State Inventory, Sources | If no ADR is wanted, the constitution-plane write step is skipped; but ADR-0002 precedent strongly implies one. |
| A3 | `[[components]]` with inline `consumes`/`produces` arrays + a `[pipeline].edges` list is the right TOML shape (vs a separate `[[edges]]` table). | Pattern 1 | Cosmetic; the loader/gate adapt to whatever shape is locked. |
| A4 | The 4 instance component agents are **instance-owned** under `examples/log-parser/agents/` (like `dotnet-engineer`), not core. | Pattern 3, PIPE-04 | If placed in core, GEN-04 + anti-sprawl fail. High confidence given precedent. |
| A5 | "Extend persona anti-sprawl to the template" = add a **new** `templates/` validation test (templates are currently unvalidated). | Pitfall 3, Code Examples | If the intent was only to keep `component-engineer` out of the persona count, a lighter change suffices. Recommend the new test regardless (closes a real gap). |
| A6 | Phase 7 emitter is not yet built, so "Phase 7 emit surface unaffected" = the new authored artifacts follow the existing `harness/{agents,commands,skills}` shape so a future emitter can consume them unchanged. | User Constraints | Low — additive markdown in the canonical dirs is exactly what the emitter will target. |

## Open Questions

1. **Where does the concrete log-parser topology live, and how does the loader find it?** *(the one
   load-bearing decision — surface in discuss-phase)*
   - What we know: edge contracts bind to domain schema names (`standard-log`, `equipment-progress`)
     which GEN-04 flags anywhere in core; the phase text says "the instance's project.toml slot"; the
     current loader reads only the single `harness/project.toml` (`[instance] root=""`).
   - What's unclear: (a) introduce `examples/log-parser/project.toml` + a loader
     `load_instance_project(root)` / overlay merge; vs (b) keep one file and extend the GEN-04
     line-exemption to topology keys.
   - Recommendation: **(a)** — cleanest ADR-0002 story, keeps core generic (success criterion 1),
     matches the phase text, and the instance overlay lives under `examples/` (GEN-04 never scans it).
     Decide how the active instance is selected (e.g. `[instance] root` points at the overlay, or the
     core default topology is empty-but-shaped and the example test reads its own file directly).
2. **Does `[instance] root` change from `""`?** If the loader reads an instance overlay, the active
   instance may need to be named. Changing `root` could interact with `test_instance_root_is_generic_default`
   (asserts `root == ""`). Recommendation: keep the core default's `root=""`, and have the example's
   overlay be read by the **example** test directly (path-local), so no core assertion changes.
3. **`/component` extension vs new scaffold command for binding component agents?** Recommendation:
   extend `/component` (it already scaffolds package + AGENTS.md + tests) to also derive a
   component-engineer persona from the template when the new package maps to a topology component;
   keep `/pipeline` purely for trace/visualization.
4. **How much dataflow "tracing" does `/pipeline` actually do at authoring time?** With no live
   runtime, `/pipeline` is a **read + render** of the declared topology (list components by stage,
   print edges + contracts, point to the owning component agent). Recommendation: scope it to a
   deterministic render of the loader output — no execution.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | loader, gates | ✓ | 3.11 | — |
| uv | `uv run pytest` | ✓ | 0.11.x (env had 0.8.17→bumped) | — |
| pytest | structural gates | ✓ | 8.4.x | — |
| `tomllib` | topology parse | ✓ (stdlib) | 3.11 | — |
| .NET 10 SDK | (NOT needed this phase) | ✗ (egress-deferred, BOOT-01) | — | Phase 8 is data/agent/Python-test only; the 4 .NET-side component agents are authored markdown, not compiled — no `dotnet` invocation required. |

**Missing dependencies with no fallback:** none. **Missing with fallback:** .NET 10 — irrelevant to
this phase's deliverables (authoring, not compiling).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (`minversion = "8.4"`) via `uv run pytest` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]`, `testpaths = ["libs/python", "tools"]` |
| Quick run command | `uv run pytest tools/harness_lint tools/harness_config -x` |
| Full core suite | `uv run pytest` (currently ~413 passed) |
| Instance leg | `uv run pytest examples/log-parser/tests` (config-derived CI target; NOT in root `testpaths`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | Loader passthrough returns declared components/pipeline | unit | `uv run pytest tools/harness_config/tests/test_loader.py -x` | ❌ Wave 0 (extend) |
| PIPE-01 | Generic topology slot is internally consistent (component.language ∈ languages; edges well-formed) | structural gate | `uv run pytest tools/harness_lint/tests/test_pipeline_config.py -x` | ❌ Wave 0 |
| PIPE-01/06 | Core carries no example dependency (GEN-04) after edits | guard | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ✅ (must stay green) |
| PIPE-02 | Orchestrator stays the single primary; no sprawl | structural gate | `uv run pytest tools/harness_lint/tests/test_agents.py::test_expected_personas_present_no_sprawl -x` | ✅ (assert unchanged) |
| PIPE-02 | Orchestrator description/routing carries topology/stage signal | structural | new assertion in `test_agents.py` or `test_pipeline_config.py` (grep routing table for stage/component) | ❌ Wave 0 (optional) |
| PIPE-03 | `component-engineer` template exists, is subagent-mode, valid perms, NOT counted as a persona | structural gate | `uv run pytest tools/harness_lint/tests/test_agent_templates.py -x` | ❌ Wave 0 |
| PIPE-03 | `/component` (or scaffold) resolves to a real persona | integration | `uv run pytest tools/harness_lint/tests/test_agent_referential_integrity.py -x` | ✅ (auto-covers) |
| PIPE-04 | Instance declares 4 components; each binds a real agent file + real contract; edges well-formed | instance structural | `uv run pytest examples/log-parser/tests/test_pipeline_topology.py -x` | ❌ Wave 0 (example leg) |
| PIPE-04 | 4 component agents parse + are subagent-mode least-privilege | instance structural | same file (glob `examples/log-parser/agents/*.md`) | ❌ Wave 0 |
| PIPE-05 | `pipeline-map` skill within caps, unique routing desc; set is exactly 9 | structural gate | `uv run pytest tools/harness_lint/tests/test_skills.py -x` | ✅ (bump `EXPECTED_SKILLS`) |
| PIPE-05 | `/pipeline` command frontmatter + routing + agent resolves | structural + integration | `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_agent_referential_integrity.py -x` | ✅ (glob auto-covers) |
| PIPE-06 | Full core suite green; GEN-04/05 + persona + template gates green | full suite | `uv run pytest` | ✅ + Wave 0 additions |

### Sampling Rate
- **Per task commit:** the specific new/edited gate for that task, e.g.
  `uv run pytest tools/harness_lint/tests/test_pipeline_config.py -x` (Nyquist: sample the exact
  invariant the task touches).
- **Per wave merge:** `uv run pytest tools/harness_lint tools/harness_config` (all structural gates +
  loader units) — catches cross-artifact drift (a component naming an undeclared language, a command
  with a dangling agent).
- **Phase gate:** `uv run pytest` (full core, must stay green — success criterion 4) **AND**
  `uv run pytest examples/log-parser/tests` (instance leg — the concrete 4-component demo). Both must
  be green before `/gsd:verify-work`. Also re-run `tools/memory_regen` if any schema/contract file
  was added.

### Wave 0 Gaps
- [ ] `tools/harness_lint/tests/test_pipeline_config.py` — generic topology consistency gate (PIPE-01/06)
- [ ] `tools/harness_config/tests/test_loader.py` — extend with `components()`/`pipeline()` passthrough asserts (PIPE-01)
- [ ] `tools/harness_lint/tests/test_agent_templates.py` — template anti-sprawl + shape (PIPE-03/06); closes the current gap where `templates/*.md` is validated by nothing
- [ ] `examples/log-parser/tests/test_pipeline_topology.py` — instance topology + 4-agent structural gate (PIPE-04); runs in the example leg
- [ ] Edit `test_skills.py` `EXPECTED_SKILLS` 8→9 (add `pipeline-map`) (PIPE-05)
- [ ] Confirm `test_agents.py` `EXPECTED_PERSONAS` stays 4 (conductor = evolved orchestrator) (PIPE-02)

## Security Domain

`security_enforcement` is not set in `.planning/config.json` → treat as enabled, but this phase's
attack surface is minimal (authoring markdown + a data slot + Python tests; no auth, network,
crypto, or untrusted input).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | yes (harness-internal) | Least-privilege persona `bash` scopes; `component-engineer` grants only its component's language scope. Constitution-plane writes (`docs/adr/0003`) gated by `contract-guard` + `GOLDEN_APPROVE_HUMAN`. |
| V5 Input Validation | yes | The consistency gate validates the topology slot shape (component.language ∈ languages, edges well-formed) — malformed config fails loud, never silently. |
| V6 Cryptography | no | — |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Over-broad `bash` allow on a new component agent | Elevation of Privilege | Template grants only `<COMPONENT language's bash_scope>`; everything else `ask`. Mirror `python-engineer`/`dotnet-engineer`. |
| Core silently grows an example dependency | Tampering (boundary erosion) | GEN-04 guard with live negative controls (already enforced). |
| Agent self-blessing a constitution-plane change (the new ADR) | Repudiation / Elevation | `contract-guard` denies `docs/adr/**` writes without the human-set `GOLDEN_APPROVE_HUMAN` token. |
| Model-identity leak into new agent `model:` fields | Info Disclosure (policy) | `test_no_real_model_identifier` — only `provider/*-tier` placeholders allowed. |

## Sources

### Primary (HIGH confidence — direct codebase read this session)
- `harness/project.toml`, `tools/harness_config/loader.py` — the `[[languages]]` slot + passthrough pattern to clone (PIPE-01)
- `tools/harness_lint/tests/test_language_config.py`, `test_loader.py` — GEN-03 consistency-gate + loader-unit idioms
- `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 guard: scanned roots, prose tokens, line-exemption mechanics
- `tools/harness_lint/tests/test_agents.py`, `test_skills.py`, `test_commands.py`, `test_agent_referential_integrity.py` — anti-sprawl frozensets + structural/referential gates
- `harness/agents/orchestrator.md`, `python-engineer.md`, `templates/engineer.md`; `examples/log-parser/agents/dotnet-engineer.md` — persona/template patterns (PIPE-02/03/04)
- `harness/commands/add-language.md`, `component.md` — order-enforcing scaffold pattern (PIPE-03)
- `docs/adr/0002-general-template-de-specialization.md` — ADR-0002 (a)/(b)/(c) constraints + approval-path posture
- `pyproject.toml` — pytest config, `testpaths = ["libs/python","tools"]` (instance-leg invisibility)
- `.planning/REQUIREMENTS.md` (PIPE-01..06), `ROADMAP.md` (Phase 8 goal + success criteria), `STATE.md`, `AGENTS.md`, `examples/log-parser/{README,AGENTS}.md`, `CLAUDE.md`

### Secondary / Tertiary
- None required — this phase is fully specified by the local codebase; no external documentation or WebSearch was needed.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every pattern verified by direct read of the exact files to clone.
- Architecture: HIGH — additive to a mature, gate-enforced structure; the one fork (topology location) is explicitly surfaced as Open Question #1 with a reasoned recommendation.
- Pitfalls: HIGH — derived from the actual guard/gate code (GEN-04 tokens, non-recursive globs, `testpaths`, frozensets).

**Research date:** 2026-07-10
**Valid until:** 2026-08-09 (30 days — stable internal codebase; re-verify only if Phase 7 emitter lands first and reshapes `harness/` authoring conventions)
