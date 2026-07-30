# Phase 8: Pipeline-Topology Conductor + Per-Component Agents - Pattern Map

**Mapped:** 2026-07-10
**Files analyzed:** 17 new/modified
**Analogs found:** 17 / 17 (every target has an exact or role-match analog already in-repo)

> This phase is **clone-and-adapt**, not novel engineering. Every mechanism already has a live,
> gate-enforced precedent. The load-bearing risk is **placement + consistency** (GEN-04 boundary,
> single-primary anti-sprawl, frozenset counts) — NOT algorithms. Copy the exact idioms below.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `harness/project.toml` (add `[[components]]` + `[pipeline]`) | config | transform (data slot) | same file's `[[languages]]` slot (lines 21-40) | exact |
| `tools/harness_config/loader.py` (add `components()`/`pipeline()`) | loader/utility | transform (passthrough) | same file's `languages()` (lines 42-50) | exact |
| `tools/harness_lint/tests/test_pipeline_config.py` (NEW) | test (structural gate) | transform (consistency) | `tools/harness_lint/tests/test_language_config.py` | exact |
| `tools/harness_config/tests/test_loader.py` (EXTEND) | test (unit) | transform | same file's language unit tests | exact |
| `harness/agents/orchestrator.md` (EVOLVE, stays `mode: primary`) | agent (persona) | event-driven (routing) | same file's routing table + intake (lines 37-67) | exact (self-evolve) |
| `harness/agents/templates/component-engineer.md` (NEW) | agent (template) | event-driven (routing) | `harness/agents/templates/engineer.md` | exact |
| `tools/harness_lint/tests/test_agent_templates.py` (NEW) | test (structural gate) | transform | `tools/harness_lint/tests/test_agents.py` frozenset + parametrized shape | role-match |
| `harness/commands/component.md` (EXTEND) | command (scaffold) | event-driven | `harness/commands/add-language.md` (order-enforcing scaffold) | exact |
| `harness/commands/pipeline.md` (NEW) | command (trace) | request-response (read+render) | `harness/commands/orient.md` (read+render, `agent: orchestrator`) | role-match |
| `harness/skills/pipeline-map/SKILL.md` (NEW) | skill | request-response (progressive disclosure) | `harness/skills/gate-model/SKILL.md` | exact |
| `tools/harness_lint/tests/test_skills.py` (EDIT `EXPECTED_SKILLS` 8→9) | test (frozenset bump) | — | same file, `EXPECTED_SKILLS` (lines 50-61) | exact |
| `examples/log-parser/project.toml` (NEW instance overlay) | config | transform (data slot) | core `harness/project.toml` | role-match |
| `examples/log-parser/agents/{parser,converter,scheduler,collector}.md` (NEW ×4) | agent (persona) | event-driven | `examples/log-parser/agents/dotnet-engineer.md` | exact |
| `examples/log-parser/tests/test_pipeline_topology.py` (NEW, example leg) | test (structural gate) | transform (consistency) | `test_language_config.py` + example `conftest.py` root-wiring | role-match |
| `docs/adr/0003-*.md` (APPEND) | doc (ADR) | — | `docs/adr/0002-general-template-de-specialization.md` | exact |

---

## Pattern Assignments

### `harness/project.toml` — add `[[components]]` + `[pipeline]` (config, transform)

**Analog:** same file, the `[[languages]]` slot.

**Slot idiom to clone** (lines 21-30 — a pure-DATA repeated table, one comment tying it to its
consumers; note the `# matches ...` inline cross-references):
```toml
[[languages]]
id = "dotnet"
bash_scope = "dotnet *"                      # matches permission-matrix.json bash allow-scope
test = "dotnet test"
format = "dotnet format"
sdk_bootstrap = "tools/bootstrap/install.sh" # env has no .NET; bootstrap installs channel 10.0
persona = "examples/log-parser/agents/dotnet-engineer.md"
test_paths = ["examples/log-parser/libs/dotnet/Normalize.Tests/Normalize.Tests.csproj"]
```

**Header-comment idiom** (lines 1-14): the file opens with a "Pure DATA. No enforcement logic lives
here" banner naming its two consumers (`loader.py` + the consistency gate). The new slot MUST add an
analogous banner block naming `components()`/`pipeline()` and `test_pipeline_config.py`.

**CRITICAL (GEN-04):** the core default MUST be **generic** — `id = "source"/"sink"`,
`produces = ["sample-record"]`. Do NOT write `parser`/`converter`/`standard-log`/`equipment`.
The bare words `parser`/`converter` are NOT flagged, but domain contract names ARE (see Shared
Patterns → GEN-04). Recommended generic default shape (from RESEARCH Pattern 1):
```toml
[[components]]
id = "source"            # domain-neutral sample id (NOT parser/converter)
stage = 1
language = "python"      # must match a [[languages]].id
produces = ["sample-record"]
consumes = []

[[components]]
id = "sink"
stage = 2
language = "python"
consumes = ["sample-record"]
produces = []

[pipeline]
edges = [ { from = "source", to = "sink", contract = "sample-record" } ]
```

---

### `tools/harness_config/loader.py` — `components()` + `pipeline()` (loader, transform-passthrough)

**Analog:** same file, `languages()` (lines 42-50).

**Passthrough idiom to clone verbatim** (raw `cfg.get(...)`, loads default if `cfg is None`, NO
enforcement):
```python
def languages(cfg: dict | None = None) -> list[dict]:
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("languages", []))
```

**New helpers** (mirror exactly — list for components, dict for the single `[pipeline]` table):
```python
def components(cfg: dict | None = None) -> list[dict]:
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("components", []))

def pipeline(cfg: dict | None = None) -> dict:
    if cfg is None:
        cfg = load_project()
    return dict(cfg.get("pipeline", {}))
```

**Export note:** `test_language_config.py` imports via `from tools.harness_config import languages,
load_project` — so the new helpers MUST be re-exported from `tools/harness_config/__init__.py`
alongside `languages`/`language_bash_scopes`/`load_project`. Keep the module docstring's "Pure I/O +
shape: NO enforcement logic" contract (lines 1-14).

---

### `tools/harness_lint/tests/test_pipeline_config.py` — NEW (test, consistency gate)

**Analog:** `tools/harness_lint/tests/test_language_config.py` (whole file).

**Repo-root + import idiom** (lines 15-23):
```python
from tools.harness_config import language_bash_scopes, languages, load_project
# test_language_config.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
```

**Consistency-assertion idiom** (lines 48-53 — iterate config, assert agreement, fail-loud message):
```python
def test_each_configured_persona_exists() -> None:
    for lang in languages():
        persona = _REPO_ROOT / lang["persona"]
        assert persona.is_file(), f"{lang['id']!r}: persona {lang['persona']} not found on disk"
```

**New gate body** (from RESEARCH "Code Examples", adapted — component.language ∈ languages; edges
well-formed against produces/consumes):
```python
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
This runs against the **generic core default** — so it must pass on `source`/`sink`/`sample-record`,
never referencing the example.

---

### `tools/harness_config/tests/test_loader.py` — EXTEND (test, unit)

**Analog:** same file (lines 20-50).

**Unit-assert idiom to mirror** (load, assert exact shape):
```python
def test_load_project_returns_two_languages() -> None:
    cfg = load_project()
    ids = sorted(lang["id"] for lang in cfg["languages"])
    assert ids == ["dotnet", "python"]

def test_language_bash_scopes_union_includes_implicit_pytest() -> None:
    scopes = language_bash_scopes()
    assert scopes == {"dotnet *", "uv *", "pytest *"}
```
Add analogous `test_components_passthrough` / `test_pipeline_passthrough` asserting the generic
default (`source`/`sink`, one edge with `contract == "sample-record"`). Note `parents[3]` here too
(loader tests live one dir deeper: `tests -> harness_config -> tools -> repo root`).

---

### `harness/agents/orchestrator.md` — EVOLVE in place (persona, event-driven routing)

**Analog:** the file's own current routing table + intake (self-evolution — do NOT create a new file).

**MUST STAY** `mode: primary`, `name: orchestrator` (lines 2-16). `EXPECTED_PERSONAS` in
`test_agents.py` stays `{orchestrator, python-engineer, code-reviewer, explorer}` (line 53) — the
conductor IS the evolved orchestrator, not a 5th persona.

**Intake procedure to extend** (lines 37-48) — add a "Trace the topology" step:
```markdown
## Intake → decompose (minimal procedure)
1. **Orient** if cold — `/orient` regenerates the derived plane and prints the pointer payload.
2. **Classify the work shape** (table below) → pick the persona/command.
3. **Decompose** into small, ordered, least-privilege subtasks; note each subtask's gate.
```
Insert a step: *"**Trace the topology** — read `[[components]]`/`[pipeline]` via
`tools.harness_config`; identify which stage/component the request touches and its upstream/
downstream edge contracts."*

**Routing table to extend** (lines 49-67 — Markdown 3-col `| Work shape | Route to | Entry |`):
```markdown
| Work shape | Route to | Entry command / skill |
|---|---|---|
| An instance's parser/converter (native toolchain) change | **instance engineer** (`project.toml`) | `/golden`, `/lint` |
```
Add rows keyed on pipeline **stage/component** → the instance's component agent
(parser/converter/scheduler/collector), falling back to the language engineer when no component
agent is declared. Add `/pipeline` (trace) as the entry for "Which component owns this stage?".
Keep the description routing-trigger tokens (`use`/`when`) — `test_description_is_routing_signal`
greps for them.

---

### `harness/agents/templates/component-engineer.md` — NEW (agent template)

**Analog:** `harness/agents/templates/engineer.md` (whole file).

**Placement guard:** MUST live in `harness/agents/templates/` — the persona gate globs
`harness/agents/*.md` **non-recursively** (test_agents.py line 65-66 `_AGENTS_DIR.glob("*.md")`), so
templates are NOT counted as core personas. Putting it in `harness/agents/` breaks anti-sprawl.

**Template header + placeholder idiom** (engineer.md lines 1-27 — HTML comment explaining it is not
active, `<PLACEHOLDER>` slots, `mode: subagent`, least-privilege bash):
```markdown
---
# ENGINEER PERSONA TEMPLATE — not an active persona.
# ... globs harness/agents/*.md non-recursively, so a template in this subdirectory is NOT counted ...
name: <LANG>-engineer
description: >-
  Use when a <LANG> change in this instance's parser/converter side is requested — implements
  <LANG>, runs <TOOLCHAIN> and its tests, and keeps the boundary contract-first. Invoke when a
  golden runner or contract on the <LANG> side needs work.
mode: subagent
permission:
  read: allow
  edit: allow
  bash:
    "*": ask
    "<BASH_SCOPE>": allow
tools: Read, Edit, Bash, Grep, Glob
---
```

**New placeholders** (from RESEARCH Pattern 3): `<COMPONENT>` (e.g. parser), `<STAGE>`,
`<LANG>`/`<TOOLCHAIN>` (from the component's `language` ref), `<CONSUMES>`/`<PRODUCES>` (edge
contracts). Description MUST carry a `use`/`when` trigger and route by **stage/component**. Keep the
body's contract-first / §4.3–4.6 / golden-gate boilerplate (engineer.md lines 29-45).

---

### `tools/harness_lint/tests/test_agent_templates.py` — NEW (test, template anti-sprawl gate)

**Analog:** `tools/harness_lint/tests/test_agents.py` — clone its frozenset + parametrized shape
asserts, but point `_TEMPLATES` at `harness/agents/templates/` (closes the current gap: templates
are validated by NOTHING today).

**Frozenset-count idiom** (test_agents.py lines 51-53, 94-100):
```python
EXPECTED_PERSONAS = frozenset({"orchestrator", "python-engineer", "code-reviewer", "explorer"})

def test_expected_personas_present_no_sprawl() -> None:
    names = {_load(p).get("name") for p in _agent_files()}
    assert names == set(EXPECTED_PERSONAS), (
        f"persona set drift: got {sorted(str(n) for n in names)}, "
        f"expected {sorted(EXPECTED_PERSONAS)}"
    )
```

**New gate** (from RESEARCH "Code Examples"):
```python
_TEMPLATES = _AGENTS_DIR / "templates"
EXPECTED_TEMPLATES = frozenset({"engineer", "component-engineer"})

def test_templates_no_sprawl() -> None:
    names = {p.stem for p in _TEMPLATES.glob("*.md")}
    assert names == set(EXPECTED_TEMPLATES)
```
Reuse test_agents.py's `parse_frontmatter` import (line 17), `VALID_PERMISSION_KEYS` (lines 24-42),
`VALID_MODES` (line 49), and its parametrized checks (`test_mode_valid_when_present`,
`test_permission_keys_are_valid_subset`, `test_description_is_routing_signal`) so each template is
subagent-mode, valid-perm-keys, routing-trigger description.

---

### `harness/commands/component.md` — EXTEND (command, scaffold)

**Analog:** `harness/commands/add-language.md` (order-enforcing three-edit scaffold).

**Mandated-order idiom to clone** (add-language.md lines 22-38 — numbered steps that keep the
persona / `project.toml` / matrix edits in sync so the consistency gate passes):
```markdown
## Mandated order (keep the three in sync)
1. **Derive the persona from the template.** Copy `harness/agents/templates/engineer.md` into the
   active instance's own `agents/` directory ... as `<lang>-engineer.md`. Fill every `<PLACEHOLDER>`.
2. **Register the language in `project.toml`.** Append a `[[languages]]` table with `id`,
   `bash_scope`, `test`, ... and `persona = "<instance>/agents/<lang>-engineer.md"`.
3. **Add the matching bash scope to the permission matrix.** ...
```
Add a step to `component.md` (frontmatter `agent: orchestrator`, `subtask: true` — lines 6-7): when
the new package maps to a declared topology **component**, derive a `component-engineer` persona from
the template into the instance and register the component in the instance's `[[components]]` slot,
so `test_pipeline_topology.py` (example leg) stays green. Keep the "All three or none" Guard idiom
(add-language.md lines 41-51).

---

### `harness/commands/pipeline.md` — NEW (command, read+render trace)

**Analog:** `harness/commands/orient.md` (read-and-render command, `agent: orchestrator`).

**Frontmatter idiom** (orient.md lines 1-8):
```markdown
---
description: >-
  Use at the start of a session to get oriented — regenerates the derived memory plane ... and
  prints the same pointer-only, drift-aware payload ... Invoke when onboarding or resuming cold.
agent: orchestrator
subtask: true
---
```
**Referential-integrity guard** (Pitfall 4): set `agent: orchestrator` (a real persona file at
`harness/agents/orchestrator.md`) — `test_agent_referential_integrity.py` (lines 42-56) resolves
every command's `agent:` to a real file, and `test_commands.py` (lines 33-44) greps the description
for a `use`/`when` trigger. Both glob-driven → `/pipeline` is auto-covered with NO test edits.
Scope: deterministic **read + render** of `components()`/`pipeline()` output (list by stage, print
edges + contracts, point to the owning component agent) — no execution (RESEARCH Open Q4).

---

### `harness/skills/pipeline-map/SKILL.md` — NEW (skill)

**Analog:** `harness/skills/gate-model/SKILL.md`.

**Frontmatter idiom** (gate-model lines 1-7 — `name` == dir name, `description` with `use`/`when`
trigger, no `<>`/vendor words):
```markdown
---
name: gate-model
description: >-
  Use when a write is blocked or you need to reason about what is gated and why — maps the
  constitution plane, the machines-gate/humans-ratify rule ... Consult when an edit ... is refused.
---
```
**Rules enforced by `test_skills.py`:** dir name == frontmatter `name`, ≤64 chars, regex
`^[a-z0-9]+(-[a-z0-9]+)*$` (so `pipeline-map` is valid), description ≤1024 with a trigger and
disjoint from all others, body >500 lines only WARNs. Depth goes in a `references/` subdir.

**REQUIRED lockstep edit** — `tools/harness_lint/tests/test_skills.py` `EXPECTED_SKILLS` (lines
50-61) MUST gain `"pipeline-map"` (8 → 9), or `test_expected_skills_present_no_sprawl` fails:
```python
EXPECTED_SKILLS = frozenset({
    "python-conventions", "golden-testing", "data-contracts", "skill-creator",
    "golden-debug", "polyglot-boundary", "gate-model", "two-plane-memory",
    "pipeline-map",   # <- ADD (PIPE-05)
})
```

---

### `examples/log-parser/project.toml` — NEW instance overlay (config)

**Analog:** core `harness/project.toml` (same slot shape) — but this file carries the **concrete**
4-component topology (GEN-04 never scans `examples/`, so domain contract names are allowed here).

Declare `[[components]]` parser(stage 1)→converter(2)→scheduler(3)→collector(4) with real
`language` refs (`dotnet` for parser/converter, `python` for scheduler/collector) and real
`consumes`/`produces` edge contracts (e.g. `standard-log`, `equipment-progress`), plus a
`[pipeline].edges` list. The concrete-topology-lives-in-instance decision is RESEARCH Open Q#1 (A1) —
record it in ADR-0003. Keep core `[instance] root = ""` unchanged (Open Q#2 / `test_instance_root_
is_generic_default` asserts `root == ""`).

---

### `examples/log-parser/agents/{parser,converter,scheduler,collector}.md` — NEW ×4 (personas)

**Analog:** `examples/log-parser/agents/dotnet-engineer.md` (whole file).

**Per-instance component persona idiom** (dotnet-engineer.md lines 1-16 — `mode: subagent`,
least-privilege bash allow scoped to the component's toolchain, routing-trigger description, Claude
`tools` allowlist):
```markdown
---
name: dotnet-engineer
description: >-
  Use when a parser or converter change is requested on the .NET 10 side — implements
  C# code, runs `dotnet build` and `dotnet test`, and keeps golden/contract parity green.
  Invoke when a migration step touches parser or converter internals ...
mode: subagent
permission:
  read: allow
  edit: allow
  bash:
    "*": ask
    "dotnet *": allow
tools: Read, Edit, Bash, Grep, Glob
---
```
Each of the 4 gets its own `name` (`parser`/`converter`/`scheduler`/`collector`), a `use`/`when`
description keyed on its **stage**, and a bash allow matching its `language` toolchain
(`dotnet *` for parser/converter, `uv *` for scheduler/collector). Body closes with "Read
`<package>/AGENTS.md` before touching that package" (dotnet-engineer.md line 33). These are
instance-owned → invisible to core `EXPECTED_PERSONAS` (that gate globs core `harness/agents/` only).

---

### `examples/log-parser/tests/test_pipeline_topology.py` — NEW (test, example leg)

**Analog:** `test_language_config.py` (consistency-gate body) + `examples/log-parser/tests/
conftest.py` (example root-wiring: `parents[3]` to repo root, `parents[1]` to `_EXAMPLE_ROOT`).

**Example-leg root wiring** (conftest.py lines 20-33):
```python
# tests -> log-parser -> examples -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLE_ROOT = Path(__file__).resolve().parents[1]  # examples/log-parser
```
Load the **instance** overlay directly (`load_project(_EXAMPLE_ROOT / "project.toml")` — `load_project`
already takes a `path` arg, loader.py line 32), then assert: 4 components; each `language` ∈ the
instance's declared languages; each component binds a real agent file under
`examples/log-parser/agents/*.md`; edges well-formed (produces∩consumes) — mirroring
`test_pipeline_edges_are_well_formed`.

**Placement guard (Pitfall 5):** this file MUST live under `examples/log-parser/tests/`. Root
`testpaths = ["libs/python", "tools"]` (pyproject) excludes `examples/`, so it runs ONLY in the
example leg (`uv run pytest examples/log-parser/tests`). A core-plane copy would trip
`test_core_no_example_dep.py` (the string `examples/log-parser` in a `tools/` file is a leak).

---

### `docs/adr/0003-*.md` — APPEND (ADR)

**Analog:** `docs/adr/0002-general-template-de-specialization.md` (whole structure).

**MADR idiom** (0002 lines 1-11 — title, plane banner, Status/Date/Deciders/Supersedes, Context,
Decision Drivers, Considered Options, Decision Outcome with lettered locked decisions (a)-(d),
Consequences, Links):
```markdown
# 2. General Template De-specialization
*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*
- **Status:** accepted
- **Date:** 2026-07-09
- **Supersedes:** —
- **Complements:** [ADR-0001](0001-walking-skeleton-golden-core.md) ...
```
ADR-0003 records: the `[[components]]`/`[pipeline]` topology slot + the **instance-overlay**
mechanism (concrete topology in `examples/log-parser/project.toml`, generic default in core) — the
RESEARCH A1/A2 decisions. Append-only; a new row in `docs/adr/README.md` index.

**Landing guard:** `docs/adr/**` is constitution-plane — `contract_guard` denies the write unless the
human-set `GOLDEN_APPROVE_HUMAN` token is in the env (0002 decision (d); RESEARCH Runtime State
Inventory). NEVER `--no-verify` / bash bypass. This is the ONE constitution-plane write in the phase.

---

## Shared Patterns

### GEN-04 core→example boundary (applies to EVERY core file this phase touches)
**Source:** `tools/harness_lint/tests/test_core_no_example_dep.py`
**Apply to:** `harness/project.toml`, `loader.py`, all `tools/harness_lint/tests/*` additions,
`orchestrator.md`, `component-engineer.md`, `pipeline.md`, `pipeline-map/SKILL.md`.

The guard scans tracked files under `tools/`, `harness/`, `libs/` for `examples/` path refs AND the
prose tokens (lines 53-68):
```python
_PATH_TOKENS = ("examples/", "components/toy-converter")
_PROSE_TOKENS = ("dotnet-engineer", "dotnet-conventions", "normalization-catalog",
    "pipeline-patterns", "libs/dotnet", "equipment", "standard-log", "correction-rules",
    "wafer", "설비")
```
**Explicitly NOT flagged** (safe to use in core, per the module docstring lines 20-26):
`parser` / `converter` / `scheduler` / `collector` / bare `dotnet` / `.NET` / `normalize` /
`log-parser`. So a core generic default may name component *roles* but NEVER domain *contracts*.
Only the `root =` / `persona =` / `test_paths =` lines in `harness/project.toml` are exempt
(lines 81-85) — do NOT add new exemptions.

### Frontmatter parsing in every structural gate
**Source:** `tools/harness_lint/frontmatter.py` (`parse_frontmatter`), imported as
`from tools.harness_lint import parse_frontmatter`.
**Apply to:** `test_pipeline_config.py`, `test_agent_templates.py` (and reused by all existing
agent/command/skill gates). Never hand-slice `---` fences — `test_agents.py` line 17, `test_skills.py`
line 23, `test_commands.py` line 27 all import it.

### Repo-root anchoring in tests
**Source:** every gate uses `_REPO_ROOT = Path(__file__).resolve().parents[3]` for files under
`tools/harness_lint/tests/` and `tools/harness_config/tests/`; example-leg tests use `parents[3]`
(repo root) + `parents[1]` (example root). Match the depth to the file's location.

### In-code registered sets that MUST move in lockstep (or gates fail)
| Set | File | Action |
|-----|------|--------|
| `EXPECTED_SKILLS` (8) | `test_skills.py:50-61` | ADD `pipeline-map` → 9 |
| `EXPECTED_PERSONAS` (4) | `test_agents.py:53` | UNCHANGED (conductor = evolved orchestrator) |
| `EXPECTED_TEMPLATES` (new) | `test_agent_templates.py` (NEW) | `{engineer, component-engineer}` |

---

## No Analog Found

None. Every target file has an exact or role-match in-repo analog (this phase is deliberately
"clone the established slot/loader/gate/template quadruple"). The only genuinely new structural
seam is the **instance-overlay loader discovery** (`load_project(path=...)` already supports a custom
path — loader.py line 32 — so even that reuses the existing signature rather than adding a new one).

## Metadata

**Analog search scope:** `harness/project.toml`, `harness/agents/`, `harness/agents/templates/`,
`harness/commands/`, `harness/skills/`, `tools/harness_config/`, `tools/harness_lint/tests/`,
`examples/log-parser/{agents,tests}/`, `docs/adr/`.
**Files scanned (read in full):** 15 analog files.
**Pattern extraction date:** 2026-07-10

## PATTERN MAPPING COMPLETE

**Phase:** 8 - Pipeline-Topology Conductor + Per-Component Agents
**Files classified:** 17
**Analogs found:** 17 / 17

### Coverage
- Files with exact analog: 11
- Files with role-match analog: 6
- Files with no analog: 0

### Key Patterns Identified
- The `[[languages]]` → `loader.languages()` → `test_language_config.py` triad is cloned verbatim
  for `[[components]]`/`[pipeline]` → `components()`/`pipeline()` → `test_pipeline_config.py`
  (pure-DATA slot + thin passthrough + consistency gate; no codegen).
- The single primary `orchestrator` is EVOLVED in place (routing table + intake), never duplicated —
  `EXPECTED_PERSONAS` stays 4; `component-engineer.md` goes in `templates/` (non-recursive glob) so
  it is not counted as a persona.
- GEN-04 boundary is the dominant constraint: generic default (`source`/`sink`/`sample-record`) in
  core, concrete 4-component log-parser topology in `examples/log-parser/project.toml`; component
  *role* words are safe in core but domain *contract* names are not. ADR-0003 lands via
  `GOLDEN_APPROVE_HUMAN`.

### File Created
`/home/user/lifetimeworkflow/.planning/phases/08-pipeline-topology-conductor-per-component-agents/08-PATTERNS.md`

### Ready for Planning
Pattern mapping complete. The planner can reference each analog path + excerpt directly in the
PLAN.md action sections.
