# Phase 10: Context-Economy Fan-out/Synthesize Orchestration (v2.0 β) - Pattern Map

**Mapped:** 2026-07-13
**Files analyzed:** 8 (2 new skills, 1 new command, 1 new reference schema, 3 edited surface files, 1 edited enumeration, 2 new tests) + emitted trees
**Analogs found:** 8 / 8 (every new/modified file maps 1:1 onto an existing in-repo pattern)

This is a **harness-authoring** phase. The new/modified files are authored harness surface
(Markdown skills/commands, one JSON-Schema reference), an enumeration edit, structural tests, and
the emitter-regenerated `.opencode/**` + `.claude/**` trees — NOT application code. Every locked
decision (D-01..D-12) already has a proven analog in the repo; the planner should copy the shape,
not invent one.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `harness/skills/fan-out-synthesize/SKILL.md` | skill (workflow procedure) | fan-out → recover → synthesize | `harness/skills/golden-debug/SKILL.md` (progressive-disclosure decision procedure + `references/` depth) | exact |
| `harness/skills/fan-out-synthesize/references/fan-out-return.schema.json` | reference (return contract) | schema/validation | `harness/skills/golden-debug/references/canonicalization-axes.md`, `harness/skills/polyglot-boundary/references/canonicalization-table.md` (byte-copied `references/` file) | role-match (`.json` vs `.md`, same byte-copy path) |
| `harness/skills/context-budget/SKILL.md` | skill (heuristic map) | decision/routing | `harness/skills/gate-model/SKILL.md`, `harness/skills/two-plane-memory/SKILL.md` (heuristic-map skill wired into orchestrator + `/orient`) | exact |
| `harness/commands/fan-out-synthesize.md` | command (thin entry point) | request → subtask | `harness/commands/review.md`, `harness/commands/refresh-memory.md` (`agent:`/`subtask: true` prose command) | exact |
| `harness/agents/orchestrator.md` | agent (primary conductor) | routing/intake | (self — edit existing routing table + intake, same pattern as Phase-8 topology rows) | edit-in-place |
| `harness/commands/orient.md` | command (onboarding) | read-order wiring | (self — edit read-order step 4, same list `gate-model`/`two-plane-memory` live in) | edit-in-place |
| `tools/harness_lint/caps.py` | config (enumeration) | anti-sprawl set | (self — `EXPECTED_SKILLS` frozenset, 9 → 11) | edit-in-place |
| `tools/harness_lint/tests/test_fan_out_return_contract.py` | test (structural) | file/JSON assertions | `tools/harness_lint/tests/test_skills.py` (glob + parse), `test_core_no_example_dep.py` (domain-neutral scan) | role-match |
| `tools/harness_lint/tests/test_context_budget_wiring.py` (or `test_orchestrator_fanout.py`) | test (structural) | body-token assertions | `tools/harness_lint/tests/test_orchestrator_topology.py` (body-token presence gate) | exact |
| `.opencode/skill/**`, `.opencode/command/**`, `.claude/skills/**`, `.claude/commands/**`, `opencode.json`, `tools/harness_emit/emit-manifest.json`, root `AGENTS.md` managed block | derived (emitter-owned) | single-source → dual-runtime emit | existing `.opencode/skill/golden-debug/` + `.claude/skills/golden-debug/` trees | emitter-owned (re-emit, do NOT hand-edit) |

---

## Pattern Assignments

### `harness/skills/fan-out-synthesize/SKILL.md` (skill, fan-out→recover→synthesize)

**Analog:** `harness/skills/golden-debug/SKILL.md` — a progressive-disclosure decision procedure
whose depth lives in a co-located `references/` file. Copy its structure exactly: YAML frontmatter
(name + `description:` folded block) → a "why this matters" opener → numbered procedure steps →
a `## Deeper reference` / `## Related` tail pointing at `references/` and sibling skills.

**Frontmatter shape to copy** (golden-debug lines 1-7 — note the `>-` folded `description:` that
opens with a "Use when …" trigger, no reserved vendor word, no `<`/`>`):
```yaml
---
name: fan-out-synthesize
description: >-
  Use when a task spans a large surface that would balloon a single context — decompose it, fan out
  N read-only analysis subagents, recover schema-bounded citation-bearing summaries, and synthesize
  them WITHOUT the conductor re-reading the raw files.
---
```
Frontmatter is enforced by `test_skills.py`: `name` must equal the parent dir (`fan-out-synthesize`),
match `^[a-z0-9]+(-[a-z0-9]+)*$`, ≤64 chars; `description` ≤1024, must carry a `use`/`when` trigger,
must be disjoint from all other skills' descriptions.

**Body shape to copy** (golden-debug uses numbered decision steps + a `## Deeper reference` tail
at lines 69-73 pointing into `references/` and a sibling skill). For fan-out-synthesize the four
named steps are the workflow from the RESEARCH architecture diagram: **1. DECOMPOSE** task into N
independent units → **2. DISPATCH** via the runtime's native `task`/`Task` affordance (NO bespoke
engine — D-03) to `explorer` workers → **3. RECOVER** compact schema-bounded returns → **4.
SYNTHESIZE** (orchestrator, never re-reads raw files — D-06). The tail points at
`references/fan-out-return.schema.json` and at `harness/agents/{explorer,orchestrator}.md`.

**Domain-neutrality constraint:** no `examples/` token, no semiconductor vocab, no model ID — see
Shared Patterns → GEN-04.

---

### `harness/skills/fan-out-synthesize/references/fan-out-return.schema.json` (reference, return contract)

**Analog:** `harness/skills/golden-debug/references/canonicalization-axes.md` and
`harness/skills/polyglot-boundary/references/canonicalization-table.md` — the two existing
`references/` byte-copy files. The emitter's `iter_reference_files` copies **any regular non-symlink
file** verbatim (`read_bytes`/`write_bytes`); only the SKILL.md markdown gets the DERIVED marker, so
a `.json` is carried byte-for-byte to both runtime trees with **no emitter code change** (glob-driven
discovery). Confirmed live: `.opencode/skill/golden-debug/references/canonicalization-axes.md` +
`.claude/skills/golden-debug/references/canonicalization-axes.md` both exist.

**Schema shape** (RESEARCH Pattern 1, planner-refinable per D-09 — the exact field set is planner
discretion): JSON Schema Draft 2020-12, `$id` self-contained (NO `$ref` into `contracts/**`),
`required: ["unit","claims"]`, `additionalProperties: false`, where each claim is
`{claim, confidence?, citations:[{path, lines?, symbol?}]}`. The `claim` description must say "a
single terse assertion, NOT a file excerpt" and citations carry path+lines only — this is what keeps
the return schema-bounded (ECON-02) and stops it smuggling raw file dumps.

**Placement constraint (D-08):** lives under the SKILL's `references/`, NOT under `contracts/`.
Putting it in `contracts/**` would trip the domain contract-drift hash gate and break GEN-04
core-independence.

---

### `harness/skills/context-budget/SKILL.md` (skill, delegate-vs-inline heuristic)

**Analog:** `harness/skills/gate-model/SKILL.md` (the closest — a heuristic *map* skill: "Why the
harness stops you, as a map instead of a surprise" → a reasoning procedure → a `## Related` tail)
and `harness/skills/two-plane-memory/SKILL.md` (a decision-forcing table: "The decision the plane
forces"). Copy `gate-model`'s shape: frontmatter with a "Use when …" trigger → a one-paragraph
statement of the single invariant the heuristic protects → a decision procedure (numbered, or a
"You want to… | … | Allowed?"-style table like two-plane-memory lines 50-55) → `## Related`.

**Frontmatter shape** (gate-model lines 1-7): the `description` must be disjoint from
fan-out-synthesize and the existing 9 (Pitfall 4). Frame it as the delegate-vs-inline decision:
"Use when deciding whether to fan out / delegate a task or work it inline …".

**Body:** the delegate-vs-inline heuristic (when the surface is large enough to balloon one context
→ fan out via `fan-out-synthesize`; when it fits → inline). `## Related` points at
`harness/skills/fan-out-synthesize/SKILL.md` and `/orient`, mirroring how `gate-model`'s
`## Related` (lines 61-63) points at `two-plane-memory` and `golden-debug`.

---

### `harness/commands/fan-out-synthesize.md` (command, thin entry point)

**Analog:** `harness/commands/review.md` and `harness/commands/refresh-memory.md` — thin commands
that route to a persona with `agent:` + `subtask: true`. `/review` is the best analog for a
**prose-only** body (no deterministic shell to run — RESEARCH Open Q3 recommends prose-only).

**Frontmatter to copy** (review.md lines 1-8):
```yaml
---
description: >-
  Use when a task spans a large surface that would balloon a single context — decomposes the work,
  fans out N read-only analysis subagents, recovers schema-bounded citation-bearing summaries, and
  synthesizes them without the conductor re-reading the raw files. Invoke for wide reconnaissance.
agent: orchestrator
subtask: true
---
```
Enforced by `test_commands.py`: `description` must carry a `use`/`when` routing trigger (not a bare
label); `agent` must be a well-formed slug (`^[a-z0-9]+(-[a-z0-9]+)*$`) — use `orchestrator` (a real
persona, checked by `test_agent_referential_integrity.py`); `subtask` must be a boolean.

**Body shape (prose-only, like review.md):** an `# /fan-out-synthesize — decompose → dispatch N →
recover → synthesize` H1, then prose that (a) points at the `fan-out-synthesize` skill as the
procedure, (b) points at the return contract `references/fan-out-return.schema.json`, and (c) hands
the workflow to the `orchestrator` (who dispatches `explorer` workers and synthesizes). Do NOT add a
`!`shell`` block — dispatch is the runtime's native `task` affordance, not a shell command.

---

### `harness/agents/orchestrator.md` (agent, EDIT — routing rows + intake)

**Analog:** self. The routing decision table (lines 65-84) and the intake procedure (lines 43-57)
are the exact seams — the same seams Phase 8 extended for topology. **Additive edit only** (do not
remove existing tokens, or `test_orchestrator_topology.py` regresses).

**Routing rows to add** (append to the table at lines 65-84, mirroring the existing `gate-model`
row at line 80: `| "Is this allowed / why is it blocked?" | (self) | gate-model skill |`):
```
| Large surface to cover / would balloon one context | (self) fan out | fan-out-synthesize skill, /fan-out-synthesize |
| "Should I delegate this or work inline?" | (self) | context-budget skill |
```

**Intake step to add** (the numbered intake procedure at lines 44-57 has steps 1-6; add a
delegate-vs-inline decision as a named, observable step so ECON-03 "observable and repeatable" is
satisfied — e.g. between "Classify the work shape" (step 2) and "Trace the topology" (step 3), or
as a sub-note on step 2). Reference the `context-budget` skill by name.

---

### `harness/commands/orient.md` (command, EDIT — read-order step 4)

**Analog:** self. Read-order step 4 (lines 38-40) is the exact list `gate-model` and
`two-plane-memory` already live in:
```
4. The relevant **skill** for the work shape: `polyglot-boundary` (§4.3–4.6), `golden-debug` (red
   golden), `data-contracts` (contracts/), `gate-model` (what's gated), `two-plane-memory` (planes).
```
**Additive edit:** append `context-budget` (delegate-vs-inline) and `fan-out-synthesize`
(large-surface coverage) to that skill list — same one-line-per-skill shape.

---

### `tools/harness_lint/caps.py` (config, EDIT — EXPECTED_SKILLS 9 → 11)

**Analog:** self. Current frozenset (lines 127-139):
```python
EXPECTED_SKILLS = frozenset(
    {
        "python-conventions",
        "golden-testing",
        "data-contracts",
        "skill-creator",
        "golden-debug",
        "polyglot-boundary",
        "gate-model",
        "two-plane-memory",
        "pipeline-map",
    }
)
```
**Edit:** add `"fan-out-synthesize"` and `"context-budget"` (9 → 11). This is the SINGLE
enumeration edit — `test_skills.py::test_expected_skills_present_no_sprawl` asserts
`set(dir_names) == set(EXPECTED_SKILLS)`, and the emit-time `validate.check_skill_set` raises
`HarnessEmitError` ("skill set drift") if a skill dir exists without a matching entry (Pitfall 2).
`EXPECTED_PERSONAS` (lines 57-59) stays **5** — no new persona (D-05). Update the stale comment above
the set (lines 122-126) if desired, but only the two-element addition is load-bearing.

---

### `tools/harness_lint/tests/test_fan_out_return_contract.py` (test, NEW — Wave 0)

**Analog:** `test_skills.py` (glob + `parse_frontmatter` + `_REPO_ROOT = parents[3]`) for the
file-discovery idiom, and `test_core_no_example_dep.py` for the domain-neutrality scan idiom.

**Assertions (ECON-02):** `references/fan-out-return.schema.json` exists; `json.loads` parses it;
it declares `$schema` = Draft 2020-12; it has NO `$ref` into `contracts/**`; it carries no
`examples/`/domain token (keep domain-neutral so GEN-04 stays green). Use
`_REPO_ROOT = Path(__file__).resolve().parents[3]` exactly as the sibling tests do.

---

### `tools/harness_lint/tests/test_context_budget_wiring.py` (test, NEW — Wave 0)

**Analog:** `tools/harness_lint/tests/test_orchestrator_topology.py` — copy it near-verbatim. It
reads `harness/agents/orchestrator.md` via `parse_frontmatter`, lowercases the body, and asserts
token presence:
```python
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ORCHESTRATOR = _REPO_ROOT / "harness" / "agents" / "orchestrator.md"

def _read() -> tuple[dict, str]:
    fm, body = parse_frontmatter(_ORCHESTRATOR.read_text(encoding="utf-8"))
    return fm, body
```
**Assertions (ECON-03):** `context-budget` and `fan-out` (and/or `fan-out-synthesize`) tokens appear
in `orchestrator.md` body AND `orient.md` body (read the second file the same way). Add a NEW test
rather than editing `test_orchestrator_topology.py` (RESEARCH A4 — additive, so the existing topology
token assertions stay green). Keep it domain-neutral (GEN-04).

---

## Shared Patterns

### Emitter round-trip (D-12) — applies to ALL new/edited `harness/` surface
**Source:** `tools/harness_emit/` (glob-driven `iter_skills`/`iter_commands`/`iter_reference_files`).
**Apply to:** every new skill, the command, the reference `.json`.
After authoring in `harness/`, run `uv run python -m tools.harness_emit`, then COMMIT the regenerated
derived trees: `.opencode/skill/{fan-out-synthesize,context-budget}/**`,
`.opencode/command/fan-out-synthesize.md`, the `.claude/` twins, `opencode.json`,
`tools/harness_emit/emit-manifest.json`, and the auto-spliced root `AGENTS.md` managed block. These
trees are DERIVED (marker on line 2) — never hand-edit them; the emit-drift CI gate re-emits and runs
`git diff --exit-code`. Confirmed layout: `.opencode/skill/<name>/SKILL.md` + `references/` and
`.claude/skills/<name>/SKILL.md` + `references/` (mirrors the live `golden-debug` trees).

### Anti-sprawl enumeration (D-05/D-12)
**Source:** `tools/harness_lint/caps.py` — `EXPECTED_SKILLS` (single source shared by lints AND emit
validators), `EXPECTED_PERSONAS`.
**Apply to:** add the two skill names to `EXPECTED_SKILLS` (9 → 11). `EXPECTED_PERSONAS` stays 5 —
the return contract is enforced by the skill/command **prompt**, not a new persona.

### Domain-neutrality / GEN-04 (D-12)
**Source:** `tools/harness_lint/tests/test_core_no_example_dep.py` — scans tracked `tools/`,
`harness/`, `libs/` for `examples/`, moved-asset proper nouns, and semiconductor vocab
(`equipment`, `wafer`, `설비`, …).
**Apply to:** the two SKILL.md bodies, the JSON schema, the command, and both new tests must carry
no `examples/` token, no domain vocab, and no real model ID. The return schema must be self-contained
(no `$ref` into `contracts/**`). Also honor the placeholder-model rule — do not pin any model
(precedent: `explorer` uses the placeholder `provider/explorer-tier`, never a real ID).

### Read-only worker reuse (D-05)
**Source:** `harness/agents/explorer.md` (lines 1-31) — `mode: subagent`, `edit: deny`, tools =
`Read, Grep, Glob`, and it already "returns concrete file paths and line references" (line 27) —
exactly the citation shape ECON-02 wants. Reuse **verbatim** as the fan-out worker; no frontmatter
change. `is_read_only` (`caps.py:91-103`) keeps it write-denied in both runtimes.

## No Analog Found

None. Every new/modified file maps onto an existing in-repo pattern. The only "new-shape" artifact is
the return-contract `.json` under `references/` — but the byte-copy *path* is identical to the two
existing `.md` reference files (`iter_reference_files` is content-agnostic), so it is a role-match,
not a gap. The planner should prefer these real analogs over RESEARCH.md's illustrative snippets
(which were themselves derived from these same files).

## Metadata

**Analog search scope:** `harness/skills/`, `harness/commands/`, `harness/agents/`,
`tools/harness_lint/`, `tools/harness_emit/`, `.opencode/`, `.claude/`.
**Files scanned (read in full or targeted):** golden-debug SKILL + reference, gate-model SKILL,
two-plane-memory SKILL, review/refresh-memory/orient commands, orchestrator/explorer agents,
caps.py, test_skills/test_commands/test_orchestrator_topology/test_core_no_example_dep, emitted
`golden-debug` trees.
**Pattern extraction date:** 2026-07-13
