# Phase 10: Context-Economy Fan-out/Synthesize Orchestration (v2.0 β) - Research

**Researched:** 2026-07-13
**Domain:** opencode/Claude agent-harness authoring — a reusable fan-out→synthesize workflow skill + command + return-contract schema + context-budget heuristic skill, single-source→dual-runtime via the Phase-7 emitter
**Confidence:** HIGH (all findings verified against the live repo; no external dependency surface)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Ship BOTH a reusable `fan-out-synthesize` **skill** (progressive-disclosure, runtime-neutral procedure: decompose → dispatch N → recover schema-bounded summaries → synthesize) AND a thin `/fan-out-synthesize` **command** entry point. One shared workflow usable by BOTH a human and the primary orchestrator/conductor (ECON-01).
- **D-02:** The skill/command is the **first-class** artifact — decompose/dispatch/recover/synthesize is a named, executable workflow, not scattered orchestrator prose.
- **D-03:** Dispatch is a **runtime-neutral procedural skill** executed via the orchestrator's **existing Task/subtask affordance** (opencode `task`, Claude `Task`). NO bespoke dispatch tool/engine.
- **D-04:** The session-side `deep-research` skill and the `Workflow` tool are **shape inspiration only**, NOT a runtime dependency of the deployed harness.
- **D-05:** The N analysis subagents **reuse the existing read-only `explorer` persona**; the return contract is enforced by the **skill/command prompt**, not a new persona. `EXPECTED_PERSONAS` stays **5**.
- **D-06:** The primary **orchestrator/conductor synthesizes** the recovered summaries. No new synthesizer persona.
- **D-07:** Enforce a **schema-bounded, citation-bearing return contract**: each subagent returns compact **paths + claims** (cited to file/line), NEVER raw file dumps.
- **D-08:** The return contract is a **harness-authored, domain-neutral JSON Schema reference co-located with the skill** (`references/`-style byte-copy, like `golden-debug`/`polyglot-boundary`) — NOT under the domain `contracts/` constitution plane.
- **D-09:** The return is an **ephemeral runtime value**, not a committed/CI-gated artifact. A lightweight conformance validator is optional planner discretion, not a gate requirement.
- **D-10:** Ship a **dedicated `context-budget` skill** (delegate-vs-inline heuristic), domain-neutral, added to `EXPECTED_SKILLS`.
- **D-11:** Wire the heuristic into **BOTH** the `orchestrator` persona (routing table / intake) AND `/orient` (read-order) — observable and repeatable, matching `gate-model`/`two-plane-memory`.
- **D-12:** Every new agent/skill/command **round-trips the Phase-7 emitter** to BOTH runtimes (opencode primary, Claude secondary) from `harness/` source, carries **no model identifier**, keeps the core example-independent (**GEN-04 green**); new skills enumerated in `EXPECTED_SKILLS`; no new persona.

### Claude's Discretion
- Exact skill/command file names (`fan-out-synthesize`, `/fan-out-synthesize`, `context-budget` are the recommended names), the precise JSON-Schema field set of the return contract, the reference-file layout, and whether a lightweight conformance validator is added. The decisions above fix the WHAT and the boundaries, not the file-level HOW.

### Deferred Ideas (OUT OF SCOPE)
- **Dedicated analyst/summarizer persona** — reuse `explorer` (anti-sprawl). Revisit only if the planner/researcher proves explorer's read-only scope cannot carry the return contract.
- **CI-gated / persisted fan-out artifacts** — the return is an ephemeral runtime value this phase (D-09); persisting + gating recovered summaries is out of scope.
- **Cross-repo fan-out / workspace-level synthesis** — belongs to Phase 11 (MREPO); β is the single-repo substrate γ generalizes.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ECON-01 | `fan-out-synthesize` skill/command (deep-research/`Workflow` shape) — decompose → dispatch N analysis subagents → recover schema-bounded summaries → synthesize; reusable by human AND conductor. | Pattern 1/2 + Architecture Diagram: author the skill + thin `/fan-out-synthesize` command (`agent: orchestrator, subtask: true`); dispatch via native `task`; `explorer` workers; orchestrator synthesizes. |
| ECON-02 | Summary/return contract — subagents return compact, citation-bearing output (paths + claims, not file dumps) so the conductor synthesizes without re-reading raw files. | Pattern 1: domain-neutral JSON Schema in `references/` (byte-copied both runtimes), `claim` = terse assertion, `citations` = path+lines; prompt-enforced, ephemeral (D-09). |
| ECON-03 | delegate-vs-inline context-budget guide/skill wired into orchestrator persona + `/orient`. | Pattern 3: author `context-budget` skill (like `gate-model`); add routing row(s) + intake mention in `orchestrator.md`; add to `/orient` read-order step 4. |


## Summary

This is a **harness-authoring** phase, not an application phase. The deliverable is authored
Markdown surface (`harness/skills/*/SKILL.md`, `harness/commands/*.md`) plus one JSON-Schema
reference file, an edit to the existing `orchestrator` persona and `/orient` command, a two-line
enumeration change in `tools/harness_lint/caps.py`, and re-emit of the whole surface to
`.opencode/` + `.claude/`. There is **no external package**, no framework selection, no runtime
engine to build. Every locked decision (D-01..D-12) maps onto an existing, proven pattern already
in the repo — the phase is deliberately a thin composition over Phase-3/5.7/7/9 machinery.

The four moving parts: (1) a `fan-out-synthesize` **skill** (progressive-disclosure procedure:
decompose → dispatch N `explorer` subtasks → recover schema-bounded summaries → orchestrator
synthesizes) plus a thin `/fan-out-synthesize` **command** entry point routing to `agent:
orchestrator`; (2) a domain-neutral **return-contract JSON Schema** co-located under the skill's
`references/` subtree (byte-copied to both runtimes exactly like `golden-debug`/`polyglot-boundary`
do — NOT under `contracts/`); (3) a `context-budget` **skill** (delegate-vs-inline heuristic) wired
into the orchestrator routing table/intake AND `/orient` read-order, mirroring how `gate-model` and
`two-plane-memory` are surfaced today; (4) the emit round-trip + anti-sprawl/GEN-04 test updates.

**Primary recommendation:** Author two new skills (`fan-out-synthesize` with a `references/`
JSON-Schema, `context-budget`), one thin command (`/fan-out-synthesize` → `agent: orchestrator,
subtask: true`), edit `orchestrator.md` (routing rows + intake step) and `orient.md` (read-order
step 4), add both skill names to `EXPECTED_SKILLS` in `caps.py`, add structural tests, then run
`python -m tools.harness_emit` and commit the regenerated `.opencode/`+`.claude/` trees +
`emit-manifest.json`. `EXPECTED_PERSONAS` stays 5; no new persona; GEN-04 stays green because
everything is domain-neutral.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Decompose task → N subtasks | `orchestrator` persona (primary, `task: allow`) | `fan-out-synthesize` skill (the procedure it follows) | Only the primary plans/delegates; the skill is the named procedure it executes (D-02/D-06). |
| Dispatch N analysis subagents | `orchestrator` via existing `task` affordance | `explorer` persona (the reused read-only worker) | D-03 forbids a bespoke dispatch engine; D-05 reuses `explorer`. Dispatch = the runtime's native Task/subtask. |
| Return schema-bounded summary | `explorer` subtask (prompt-enforced) | return-contract JSON Schema (`references/`) | D-07/D-09: contract enforced by prompt + documented shape, ephemeral runtime value, not a persona and not a CI-gated file. |
| Synthesize recovered summaries | `orchestrator` persona | `fan-out-synthesize` skill (synthesis step) | D-06: the conductor synthesizes; no new synthesizer persona. |
| Delegate-vs-inline routing decision | `orchestrator` routing table + intake | `context-budget` skill + `/orient` read-order | D-10/D-11: heuristic is a first-class skill surfaced at both named integration points. |
| Single-source → dual-runtime emit | `tools/harness_emit` (Phase-7) | emit-drift CI gate | D-12: every new surface round-trips; validators loud-fail, never truncate. |

## Standard Stack

This phase introduces **no new libraries**. It composes existing in-repo tooling. The relevant
"stack" is the authored-surface conventions and the tooling that validates/emits them.

### Core (existing machinery reused — do NOT rebuild)
| Component | Location | Purpose | Why Standard |
|-----------|----------|---------|--------------|
| Phase-7 emitter | `tools/harness_emit/` (`generate.py`, `project_skill.py`, `project_command.py`, `validate.py`) | Projects `harness/` source → `.opencode/` + `.claude/`, byte-deterministic | The mandated single-source→dual-runtime pipeline (D-12). `iter_skills`/`iter_commands` are glob-driven — new files are picked up with **no emitter code change**. [VERIFIED: repo `generate.py:183-194`] |
| Skill cap/enumeration source | `tools/harness_lint/caps.py` (`EXPECTED_SKILLS`, `EXPECTED_PERSONAS`) | Single source of truth for anti-sprawl + caps, shared by lints AND emit validators | A cap/enumeration change lands in exactly one place. [VERIFIED: repo `caps.py:127-139`, `validate.py:18-31`] |
| `explorer` persona | `harness/agents/explorer.md` | The reused read-only fan-out worker (Read/Grep/Glob, cheap tier, `edit: deny`) | D-05: reuse verbatim; returns "file paths and line references" — already the citation shape ECON-02 wants. [VERIFIED: repo `explorer.md:26-28`] |
| `orchestrator` persona | `harness/agents/orchestrator.md` | Primary conductor, `task: allow`, routing table + intake procedure | D-03/D-06: runs dispatch and synthesizes; already extended in Phase 8 (topology) — same edit pattern. [VERIFIED: repo `orchestrator.md:10-17,43-84`] |
| `references/` byte-copy convention | `harness/skills/{golden-debug,polyglot-boundary}/references/` | Progressive-disclosure depth copied byte-for-byte to both runtimes | D-08: the emit path for the return-contract schema. `iter_reference_files` copies ANY regular file (a `.json` schema works). [VERIFIED: repo `project_skill.py:39-59`, `generate.py:412-420`] |

### Supporting (the wiring precedents to copy)
| Precedent | Location | What to Mirror |
|-----------|----------|----------------|
| Heuristic-skill-wired-into-orchestrator | `gate-model`, `two-plane-memory` skills + `orchestrator.md` routing rows + `orient.md` step 4 | `context-budget` wiring shape (D-10/D-11). `gate-model` is already a routing-table row ("Is this allowed / why is it blocked?" → `gate-model` skill) and an `/orient` read-order entry. [VERIFIED: repo `orchestrator.md:80`, `orient.md:39-40`] |
| Skill+command pairing | `/refresh-memory` (→ `agent: curator`), `/review` (→ `agent: code-reviewer`) | `/fan-out-synthesize` → `agent: orchestrator, subtask: true` (D-01). Phase-9 both-command-and-agent shape. [VERIFIED: repo `refresh-memory.md:1-8`, `review.md:1-7`] |
| Structural test pattern | `tools/harness_lint/tests/test_skills.py`, `test_commands.py`, `test_orchestrator_topology.py` | The tests the planner must add/update (skill-set equality, command frontmatter, orchestrator body-token assertions). [VERIFIED: repo] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff / Why rejected |
|------------|-----------|-------------------------|
| Reuse `explorer` as fan-out worker | New dedicated `analyst`/`summarizer` persona | D-05 defers this: it bumps `EXPECTED_PERSONAS` past 5 (anti-sprawl). See "Open Questions" for the explicit sufficiency check the planner must make. |
| Return-contract in `references/` | Return-contract under `contracts/` constitution plane | D-08 forbids: `contracts/` is the CODEOWNERS-gated instance data plane; putting a harness mechanism there trips the domain contract-drift gate and breaks GEN-04 core-independence. |
| Prompt-enforced ephemeral return | CI-gated / persisted fan-out summary artifacts | D-09: the return is an ephemeral runtime value; persisting+gating is explicitly deferred (see Deferred Ideas). |
| Skill-driven procedure via native `task` | Bespoke dispatch tool/engine (`Workflow`-like) | D-03/D-04: `deep-research`/`Workflow` are **shape inspiration only**; the emitted harness must not assume either exists. |

## Package Legitimacy Audit

**Not applicable.** This phase installs **no external packages** in any ecosystem. All work is
authored Markdown + JSON-Schema files and edits to existing Python test/enumeration modules using
the already-pinned in-repo toolchain (`uv`, `pytest`, stdlib `json`/`jsonschema` already present).
No `npm`/`pip`/`cargo` install occurs. slopcheck gate is vacuously satisfied.

## Architecture Patterns

### System Architecture Diagram (the fan-out→synthesize data flow)

```
   human OR orchestrator (primary, task: allow)
              │  invokes
              ▼
   /fan-out-synthesize  (thin command, agent: orchestrator, subtask: true)
              │  points at
              ▼
   fan-out-synthesize SKILL  (the named procedure)
              │
       ┌──────┴───────── 1. DECOMPOSE task into N independent analysis units
       │
       │  2. DISPATCH (native task/Task affordance — NO bespoke engine)
       ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐        N parallel read-only subtasks,
   │explorer │   │explorer │   │explorer │  ...   each pinned to the return contract
   │ (unit 1)│   │ (unit 2)│   │ (unit N)│        by the SKILL/command PROMPT
   └────┬────┘   └────┬────┘   └────┬────┘
        │ returns     │ returns     │ returns  ← schema-bounded, citation-bearing
        │ {claims[],  │             │            (paths + file:line + claim), NOT file dumps
        ▼ citations[]}▼             ▼
   ┌────────────────────────────────────────┐  3. RECOVER — conductor holds only the
   │  orchestrator collects N compact returns│     compact summaries, never the raw files
   └───────────────────┬────────────────────┘
                       │  4. SYNTHESIZE (orchestrator, D-06)
                       ▼
              single synthesized result  ← conductor never re-reads the raw files (ECON-02)

   ── validated shape ──
   return contract JSON Schema  (references/fan-out-return.schema.json)
   byte-copied to  .opencode/skill/fan-out-synthesize/references/  +  .claude/skills/…/references/

   ── routing observability (ECON-03) ──
   context-budget SKILL ──wired-into──▶ orchestrator routing table + intake  AND  /orient read-order
```

### Recommended Source Structure (files to author/modify)

```
harness/
├── skills/
│   ├── fan-out-synthesize/
│   │   ├── SKILL.md                              # NEW — the decompose→dispatch→recover→synthesize procedure
│   │   └── references/
│   │       └── fan-out-return.schema.json        # NEW — domain-neutral return contract (JSON Schema Draft 2020-12)
│   └── context-budget/
│       └── SKILL.md                              # NEW — delegate-vs-inline heuristic (progressive disclosure)
├── commands/
│   └── fan-out-synthesize.md                     # NEW — thin entry point: agent: orchestrator, subtask: true
└── agents/
    └── orchestrator.md                           # EDIT — add fan-out routing row(s) + context-budget row + intake step
harness/commands/orient.md                        # EDIT — add context-budget (+ optionally fan-out-synthesize) to read-order step 4
tools/harness_lint/caps.py                        # EDIT — EXPECTED_SKILLS += {"fan-out-synthesize","context-budget"} (9 → 11)
tools/harness_lint/tests/                         # ADD/UPDATE structural tests (see Validation Architecture)
# then RE-EMIT (python -m tools.harness_emit) → regenerates & you COMMIT:
.opencode/{skill,command}/…  .claude/{skills,commands}/…  opencode.json  tools/harness_emit/emit-manifest.json
# Regime-B merged (auto, do not hand-edit): root AGENTS.md managed block (agent/command/skill index)
```

### Pattern 1: Return-contract JSON Schema co-located in `references/` (D-07/D-08)
**What:** A `.json` JSON-Schema file under `harness/skills/fan-out-synthesize/references/`. The
emitter's `iter_reference_files` copies **any regular file** byte-for-byte to both runtime trees —
it is markdown-agnostic, so a `.json` is carried verbatim with no special handling.
**When to use:** Whenever a skill needs progressive-disclosure depth that both runtimes must see.
**Recommended schema shape (domain-neutral, planner may refine field set — D-09 "planner discretion"):**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "harness/skills/fan-out-synthesize/references/fan-out-return.schema.json",
  "title": "Fan-out analysis subagent return",
  "description": "Compact, citation-bearing summary a fan-out worker returns to the conductor. Paths + claims, never raw file dumps.",
  "type": "object",
  "required": ["unit", "claims"],
  "additionalProperties": false,
  "properties": {
    "unit":        { "type": "string", "description": "The analysis unit this subagent was assigned (from decompose)." },
    "status":      { "type": "string", "enum": ["complete", "partial", "not-found"] },
    "claims": {
      "type": "array",
      "description": "The findings — each a terse claim backed by a citation. This is the whole payload the conductor synthesizes from.",
      "items": {
        "type": "object",
        "required": ["claim", "citations"],
        "additionalProperties": false,
        "properties": {
          "claim":      { "type": "string", "description": "A single terse assertion (one fact), NOT a file excerpt." },
          "confidence": { "type": "string", "enum": ["high", "medium", "low"] },
          "citations": {
            "type": "array", "minItems": 1,
            "items": {
              "type": "object",
              "required": ["path"],
              "additionalProperties": false,
              "properties": {
                "path":  { "type": "string", "description": "Repo-relative file path." },
                "lines": { "type": "string", "description": "Line or range, e.g. \"42\" or \"42-58\"." },
                "symbol":{ "type": "string", "description": "Optional symbol/heading anchor." }
              }
            }
          }
        }
      }
    },
    "open_questions": { "type": "array", "items": { "type": "string" }, "description": "Gaps the worker could not resolve within its unit." }
  }
}
```
**Note:** No `$ref` to `contracts/**` — this schema is self-contained and domain-neutral so GEN-04
stays green and it never touches the domain contract-drift hash gate.

### Pattern 2: Thin command → orchestrator (D-01)
**What:** `harness/commands/fan-out-synthesize.md` frontmatter mirrors `/refresh-memory` and
`/review`: `description:` (routing paragraph carrying a "use"/"when" trigger — enforced by
`test_commands.py`), `agent: orchestrator`, `subtask: true`. Body is prose (the `!`shell`` body
form is optional — `/review` step 3 shows a command can be mostly prose that hands off to a
persona). The command is the entry point; the SKILL is the reusable procedure.
**When to use:** Any first-class workflow that a human OR the conductor invokes (ECON-01 "one shared
workflow, not two").

### Pattern 3: Heuristic skill wired at two named integration points (D-10/D-11)
**What:** `context-budget` SKILL.md authored like `gate-model` (map/decision-procedure prose). Wire
it in exactly as `gate-model` is wired: (a) a **row in the orchestrator routing table** (work shape
→ skill), and (b) an **entry in `/orient` read-order step 4** (the "relevant skill for the work
shape" list). Optionally add an intake-step mention in `orchestrator.md` so the delegate-vs-inline
decision is a named, observable step (ECON-03 "observable and repeatable").
**Example (orchestrator routing rows to add):**
```
| Large surface to cover / would balloon one context | (self) fan out | fan-out-synthesize skill, /fan-out-synthesize |
| "Should I delegate this or work inline?" | (self) | context-budget skill |
```
**Example (`/orient` read-order step 4 addition):** add `context-budget` (delegate-vs-inline) and
`fan-out-synthesize` (large-surface coverage) to the skill list alongside `gate-model`/`two-plane-memory`.

### Anti-Patterns to Avoid
- **Building a dispatch engine / a new `tool()`:** D-03 forbids it. Dispatch is the runtime's native
  `task` (opencode) / `Task` (Claude) affordance the orchestrator already holds (`task: allow`).
- **Adding a fan-out/analyst persona:** D-05 — `EXPECTED_PERSONAS` stays 5. The return contract is
  enforced by the **skill/command prompt**, not by a persona's frontmatter.
- **Putting the return schema under `contracts/`:** D-08 — trips the domain contract-drift hash gate
  and breaks GEN-04 core-independence.
- **Hand-editing `.opencode/` or `.claude/` trees:** they are DERIVED (marker on line 2). Author in
  `harness/`, then re-emit. A hand-edit is caught by the emit-drift CI gate.
- **Assuming `deep-research`/`Workflow` exist at runtime:** D-04 — shape inspiration only.
- **Leaking a domain token** (`examples/`, semiconductor vocab, a real model ID) into any new file:
  GEN-04 guard (`test_core_no_example_dep.py`) + the placeholder-model validator loud-fail.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Project skill/command to both runtimes | A bespoke copy/transpile step | `python -m tools.harness_emit` (glob-driven `iter_skills`/`iter_commands`) | New files are auto-discovered; emitter is byte-deterministic and the CI emit-drift gate depends on it. [VERIFIED: `generate.py:342-411`] |
| Dispatch N subagents | A custom dispatch tool/engine | Orchestrator's native `task`/`Task` affordance | D-03 non-negotiable (reuse, not rebuild). |
| Copy `references/` depth to runtimes | Manual file copies | Emitter `iter_reference_files` byte-copy | Handles confinement + symlink safety; carries `.json` verbatim. [VERIFIED: `project_skill.py:39-59`] |
| Enforce skill caps / anti-sprawl | Per-test hardcoded caps | `caps.py` single source (`EXPECTED_SKILLS`, `_DESC_MAX`, …) | One edit place; shared by lints + emit validators. |
| Validate schema conformance of the return | A custom validator (unless planner opts in) | `jsonschema` (already a workspace dep) — but D-09 makes it **optional** | The return is an ephemeral runtime value; a lightweight conformance validator is planner discretion, not a gate requirement. |

**Key insight:** In this repo, "adding surface" is almost entirely **authoring + enumerating +
re-emitting**. The generators/validators are glob-driven and already exist; the only code change is
the two-element `EXPECTED_SKILLS` addition in `caps.py`. Everything else is Markdown/JSON + tests.

## Common Pitfalls

### Pitfall 1: Forgetting to re-emit + commit the derived trees
**What goes wrong:** Author in `harness/` but don't run the emitter → `.opencode/`/`.claude/` are
stale → CI **emit-drift** gate fails (re-emit + `git diff --exit-code` over the manifest path set).
**Why it happens:** The two-tree + `emit-manifest.json` + Regime-B `AGENTS.md` block are all
regenerated by one command; easy to skip.
**How to avoid:** After authoring, run `uv run python -m tools.harness_emit`, then commit ALL of:
`.opencode/skill/{fan-out-synthesize,context-budget}/**`, `.opencode/command/fan-out-synthesize.md`,
the `.claude/` twins, the regenerated `opencode.json`, `tools/harness_emit/emit-manifest.json`, and
the auto-spliced root `AGENTS.md` managed block. **Warning sign:** `git status` shows changes under
`.opencode/`/`.claude/` you didn't hand-make — that's expected; commit them.

### Pitfall 2: Skill-set drift loud-fail at emit time
**What goes wrong:** Add a new `harness/skills/<name>/` dir but forget to add `<name>` to
`EXPECTED_SKILLS` → `validate.check_skill_set` raises `HarnessEmitError` ("skill set drift") and the
emitter writes nothing; symmetrically, `test_skills.py::test_expected_skills_present_no_sprawl` fails.
**Why it happens:** Anti-sprawl is enforced by exact set-equality (`set(names) == EXPECTED_SKILLS`).
**How to avoid:** Edit `caps.py` `EXPECTED_SKILLS` to include BOTH new skills (9 → 11) in the same
change that adds the directories. [VERIFIED: `validate.py:181-187`, `test_skills.py:53-58`]

### Pitfall 3: Description that reads as a label, not a routing signal
**What goes wrong:** A SKILL.md/command `description:` without a "use"/"when" trigger token fails
`test_skills.py::test_description_within_caps_and_routes` / `test_commands.py::test_description_is_routing_signal`.
**How to avoid:** Start every description with "Use when …". Also: no reserved vendor words
(`anthropic`/`claude`) and no `<`/`>` chars in name/description. [VERIFIED: `test_skills.py:85-105`, `caps.py:116-119`]

### Pitfall 4: Duplicate/overlapping descriptions
**What goes wrong:** `test_descriptions_are_disjoint` fails if two skills share an identical
(lowercased, stripped) description → ambiguous routing.
**How to avoid:** `fan-out-synthesize` and `context-budget` descriptions must be clearly distinct
from each other and from the existing 9. [VERIFIED: `test_skills.py:108-111`]

### Pitfall 5: A domain/model leak tripping GEN-04 or the model-identity validator
**What goes wrong:** A literal `examples/` token or semiconductor vocab in a new core file trips
`test_core_no_example_dep.py`; a real model ID trips the placeholder-model regex. (Precedent: 08-01
had a literal `examples/` token in a test file leak the guard.)
**How to avoid:** Keep both skills, the schema, and the command strictly domain-neutral; pin no
model. **Warning sign:** any concrete instance name in the new surface.

## Code Examples

### Command frontmatter (mirror `/refresh-memory`, `/review`)
```markdown
---
description: >-
  Use when a task spans a large surface that would balloon a single context — decomposes the work,
  fans out N read-only analysis subagents, recovers schema-bounded citation-bearing summaries, and
  synthesizes them without the conductor re-reading the raw files. Invoke for wide reconnaissance.
agent: orchestrator
subtask: true
---
# /fan-out-synthesize — decompose → dispatch N → recover → synthesize
...prose that points at the fan-out-synthesize skill and the return contract...
```
Source shape: [VERIFIED: `harness/commands/refresh-memory.md:1-8`, `project_command.py:21-22`]

### `EXPECTED_SKILLS` edit (caps.py)
```python
EXPECTED_SKILLS = frozenset(
    {
        "python-conventions", "golden-testing", "data-contracts", "skill-creator",
        "golden-debug", "polyglot-boundary", "gate-model", "two-plane-memory", "pipeline-map",
        "fan-out-synthesize",   # NEW (ECON-01)
        "context-budget",       # NEW (ECON-03)
    }
)
```
[VERIFIED: `caps.py:127-139`] — note test docstrings say "four enumerated core skills" (stale
prose); the assertion is `set(names) == set(EXPECTED_SKILLS)`, so only this edit is needed, no
numeric hardcode to chase.

## Runtime State Inventory

> Not a rename/refactor phase (greenfield authored surface). Included briefly because the phase adds
> enumerated state the emitter/gates track.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastore keys involved. | None (verified: phase adds Markdown/JSON only). |
| Live service config | None — no external service config. | None. |
| OS-registered state | None. | None. |
| Enumerated harness state | `EXPECTED_SKILLS` in `caps.py` (9 → 11); `emit-manifest.json` owned-path set (auto-pruned/written by emitter). | Edit `caps.py`; re-emit regenerates the manifest — commit it. |
| Build artifacts / derived trees | `.opencode/` + `.claude/` skill/command trees + `opencode.json` + root `AGENTS.md` managed block are DERIVED. | Re-emit (`python -m tools.harness_emit`) and commit; never hand-edit. |

## State of the Art

Not applicable — no external ecosystem moving under us. The "state of the art" here is the repo's
own established patterns (Phase 3 skills, Phase 5.7 lifecycle skills like `gate-model`, Phase 7
emitter, Phase 9 curator both-command-and-agent). All are current and green as of this milestone.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The exact JSON-Schema field set of the return contract (`unit`/`claims`/`citations`/…) | Pattern 1 | LOW — D-09 explicitly makes the precise field set planner/researcher discretion; the shape shown is a recommendation, not a locked contract. |
| A2 | A `.json` file under `references/` is byte-copied by the emitter with no special-casing | Pattern 1, Don't Hand-Roll | LOW — verified: `iter_reference_files` copies any regular non-symlink file; only markdown gets the DERIVED marker (skills SKILL.md), reference files are raw `read_bytes`/`write_bytes`. [VERIFIED: `generate.py:412-420`] |
| A3 | `/orient` read-order step 4 is the correct wiring point for a heuristic skill pointer | Pattern 3 | LOW — verified: that step already lists `gate-model`/`two-plane-memory` for exactly this purpose. [VERIFIED: `orient.md:38-40`] |
| A4 | Adding routing rows + an intake mention to `orchestrator.md` will not break the existing `test_orchestrator_topology.py` token assertions | Validation Architecture | LOW — that test only asserts presence of `topology`/`trace the topology`/`stage`/`/pipeline` tokens; additive edits don't remove them. Planner should add a NEW test asserting the fan-out/budget tokens rather than modify the topology test. [VERIFIED: `test_orchestrator_topology.py:42-61`] |

**All other claims in this research are [VERIFIED] against the live repo.**

## Open Questions

1. **Is `explorer`'s read-only scope sufficient to carry the schema-bounded return contract?**
   - What we know: `explorer` returns "file paths and line references" (Read/Grep/Glob only) — this
     is already the paths+citations shape ECON-02 wants; the return contract is prompt-enforced, not
     persona-enforced, so no frontmatter change to `explorer` is needed.
   - What's unclear: whether analysis units that require *synthesis-within-a-unit* (not just
     locate+cite) exceed a cheap-tier read-only reconnaissance persona.
   - Recommendation: proceed with `explorer` (D-05 default). The deferred `analyst` persona is
     unlocked ONLY if the planner proves insufficiency; document the decision either way.

2. **Add a lightweight conformance validator for the return contract, or not?**
   - What we know: D-09 makes it optional planner discretion; the return is an ephemeral runtime
     value, not a CI-gated file. `jsonschema` is already a workspace dependency.
   - Recommendation: **skip a runtime validator** for β (keep the phase thin; enforce via prompt +
     the documented schema). If added, scope it to a `--check`-style dev helper, not a CI gate — so
     it does not contradict "ephemeral, not gated."

3. **Does `/fan-out-synthesize` need a `!`shell`` body, or is prose-only acceptable?**
   - What we know: `/review` is largely prose that hands off to a persona; `/orient`/`/refresh-memory`
     run shell. The fan-out workflow has no deterministic shell to run (dispatch is the runtime's
     task affordance).
   - Recommendation: prose-only body pointing at the skill + return contract, like `/review`.

## Validation Architecture

> `workflow.nyquist_validation: true` — section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via `uv run pytest`); structural gates in `tools/harness_lint/tests/`, emit gates in `tools/harness_emit/tests/` |
| Config file | root `pyproject.toml` / uv workspace (per-member `pyproject.toml`); `conftest.py` present in `tools/harness_lint/tests/` |
| Quick run command | `uv run pytest tools/harness_lint/tests/test_skills.py tools/harness_lint/tests/test_commands.py -x` |
| Full suite command | `uv run pytest` (non-example suite; example leg runs separately with .NET egress skips) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ECON-01 | `fan-out-synthesize` skill + `/fan-out-synthesize` command exist, valid frontmatter, in `EXPECTED_SKILLS` | structural | `uv run pytest tools/harness_lint/tests/test_skills.py tools/harness_lint/tests/test_commands.py` | ✅ (glob-driven — auto-covers new files once caps.py updated) |
| ECON-01 | Command `agent:` resolves to real persona (`orchestrator`) | integration | `uv run pytest tools/harness_lint/tests/test_agent_referential_integrity.py` | ✅ (glob-driven) |
| ECON-02 | Return-contract schema is present, valid JSON, byte-copied to both runtimes | structural | NEW test: assert `references/fan-out-return.schema.json` exists + `json.loads` parses + is domain-neutral | ❌ Wave 0 |
| ECON-03 | `context-budget` skill wired into orchestrator routing + `/orient` read-order | structural | NEW test (mirror `test_orchestrator_topology.py`): assert `context-budget`/`fan-out` tokens in `orchestrator.md` body AND `orient.md` body | ❌ Wave 0 |
| D-05/D-12 | `EXPECTED_PERSONAS` stays 5; no new persona; emit round-trips both runtimes | structural + emit | `uv run pytest tools/harness_lint/tests/test_agents.py tools/harness_emit/tests/` + re-emit `git diff --exit-code` | ✅ (test_agents pins persona set) |
| D-12/GEN-04 | New core surface has no `examples/` dependency | structural | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` | ✅ (glob-driven over core planes) |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_lint/tests/test_skills.py tools/harness_lint/tests/test_commands.py -x`
- **Per wave merge:** `uv run python -m tools.harness_emit && git diff --exit-code` (emit-drift) + `uv run pytest tools/harness_lint/tests tools/harness_emit/tests`
- **Phase gate:** full non-example `uv run pytest` green + emit-drift clean before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/harness_lint/tests/test_fan_out_return_contract.py` — asserts the `references/fan-out-return.schema.json` exists, parses as JSON, declares `$schema` Draft 2020-12, and contains no domain/`examples/` token (ECON-02).
- [ ] `tools/harness_lint/tests/test_context_budget_wiring.py` (or extend a new `test_orchestrator_fanout.py`) — asserts `context-budget` + fan-out routing tokens appear in `orchestrator.md` body AND `orient.md` read-order (ECON-03). Mirror `test_orchestrator_topology.py` structure; keep domain-neutral so GEN-04 stays green.
- [ ] Confirm `test_skills.py` / `test_commands.py` pick up the new files with **no edit** (they are glob-driven) — only `caps.py` `EXPECTED_SKILLS` needs the 2-element addition.
- [ ] (Optional, planner discretion per Open Q2) a conformance validator + its test — recommended SKIP for β.

## Security Domain

> `security_enforcement` not set in config → treated as enabled. This is an authoring phase with no
> auth/session/crypto/network surface; applicability is minimal but the repo's existing gate posture
> still governs.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth surface) |
| V3 Session Management | no | — |
| V4 Access Control | yes (weakly) | Fan-out workers reuse `explorer` — **read-only** (`edit: deny`, tools = Read/Grep/Glob), enforced by `is_read_only` in both projections. Least-privilege preserved; no worker gains write. |
| V5 Input Validation | yes | Return-contract JSON Schema bounds the subagent output shape (paths+claims), preventing unbounded/free-form returns. Optional `jsonschema` conformance (D-09). |
| V6 Cryptography | no | — |

### Known Threat Patterns for this harness
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| A fan-out worker writing files (privilege creep) | Elevation of Privilege | Reuse read-only `explorer`; `is_read_only` gate blocks any write/shell affordance in both runtimes. [VERIFIED: `caps.py:91-103`] |
| A real model ID leaking into emitted surface | Information Disclosure | Placeholder-model regex validator loud-fails at emit (`check_agent`/`check_opencode_config`). |
| Hand-edited derived tree diverging from source | Tampering | emit-drift CI gate (re-emit + `git diff --exit-code`). |
| Return contract used to smuggle raw file contents (defeats context economy) | — (design integrity) | Schema `claim` is "a single terse assertion, NOT a file excerpt"; `citations` carry path+lines only. Prompt + `additionalProperties: false` bound it. |

## Environment Availability

> No new external dependencies. The existing toolchain suffices.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | run tests + emitter | ✓ (repo-standard) | 0.11.x (per CLAUDE.md) | — |
| `pytest` | structural/emit gates | ✓ (workspace dev dep) | 8.4.x | — |
| `jsonschema` | (optional) return-contract conformance | ✓ (already a workspace dep, used by `check_opencode_config`) | 4.26.0 | Skip conformance (D-09) |
| .NET 10 SDK | NOT needed this phase | ✗ (egress-blocked) | — | Irrelevant — no .NET surface in Phase 10 |

**Missing dependencies with no fallback:** None — Phase 10 is authored surface + Python tests only;
the outstanding .NET egress blocker (BOOT-01) does not gate this phase.

## Sources

### Primary (HIGH confidence — live repo, this session)
- `harness/agents/orchestrator.md`, `harness/agents/explorer.md` — reuse targets (D-03/D-05/D-06).
- `harness/commands/{orient,refresh-memory,review}.md` — command shape + skill-wiring precedents.
- `harness/skills/{golden-debug,polyglot-boundary,gate-model}/` — `references/` byte-copy convention + heuristic-skill shape.
- `tools/harness_emit/{generate.py,project_skill.py,project_command.py,validate.py,emit-manifest.json}` — the emit pipeline + loud-fail validators + owned-path set.
- `tools/harness_lint/caps.py` — `EXPECTED_SKILLS` (9), `EXPECTED_PERSONAS` (5), `is_read_only`.
- `tools/harness_lint/tests/{test_skills,test_commands,test_orchestrator_topology,test_agent_referential_integrity}.py` — the test patterns to add/update.
- `.planning/phases/10-…/10-CONTEXT.md` (D-01..D-12), `.planning/REQUIREMENTS.md` §ECON, `.planning/STATE.md` (Phase 7/9 precedents), `CLAUDE.md`.

### Secondary / Tertiary
- None required — no external lookup needed for an internal authoring phase.

## Metadata

**Confidence breakdown:**
- Standard stack (reused machinery): HIGH — every reuse target read and verified in-repo this session.
- Architecture (fan-out flow + wiring points): HIGH — maps 1:1 onto existing `gate-model`/`/orient`/emitter patterns.
- Pitfalls: HIGH — derived from the actual loud-fail validators and gate tests (`validate.py`, `test_skills.py`, emit-drift).
- Return-contract field set: MEDIUM (A1) — shape verified emittable; exact fields are D-09 planner discretion.

**Research date:** 2026-07-13
**Valid until:** 2026-08-13 (stable — internal harness patterns; no fast-moving external dependency).
