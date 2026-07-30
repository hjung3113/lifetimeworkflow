# Phase 50a: Harness Authoring - Research

**Researched:** 2026-07-30
**Domain:** repo-internal — a harness authoring skill absorbing an existing skill, plus the emitter/
lint/manifest surface that names it
**Confidence:** HIGH (every claim below is grounded in this checkout; no web search used per phase
convention — v2.6 does no research round against an external ecosystem)

## Summary

This phase does one structural thing — `harness/skills/harness-author/` replaces
`harness/skills/skill-creator/`, widened from skills-only to skills+commands+agents — and one
discipline thing: every default the new skill offers must carry a `path:line` citation that a test
proves resolves in this checkout. The absorption is small in file count (one skill body, one caps
constant, one manifest regenerate, one sibling skill's cross-reference, two emitted-copy pairs) but
the CONTEXT.md's "one change" instruction is real: `caps.py`'s `EXPECTED_SKILLS` and both
`test_skills.py::test_expected_skills_present_no_sprawl` / `test_emit_determinism.py::
test_emitted_skill_set_matches_expected` are three-way-pinned to the same frozenset, so a rename that
touches only the directory will fail three assertions simultaneously — by design, not as three
separate discoveries. `emit-manifest.json` is **derived, not hand-maintained**: it is written by
`manifest.prune_then_write` on every `python -m tools.harness_emit` run and needs no manual edit, only
a re-run. There is no existing citation-resolution test anywhere in this repo — `pointer_index.py`
tracks referrers to memory items (a different problem: "who points at X", not "does this path:line
resolve") — so the criterion-1 citation-integrity test is genuinely new code, best modeled on the
`git ls-files`-scoped scanning idiom already used by `test_core_no_example_dep.py`.

**Primary recommendation:** Sequence the whole absorption as one atomic commit: create
`harness/skills/harness-author/SKILL.md` (skills+commands+agents scope, Step 0 preserved and
generalized, citations that resolve), delete `harness/skills/skill-creator/`, edit `caps.py`'s
`EXPECTED_SKILLS` (swap the string), edit `harness/skills/brownfield-adoption/SKILL.md`'s two
`skill-creator` mentions, re-run `python -m tools.harness_emit` (regenerates `emit-manifest.json`,
both emitted trees, the `AGENTS.md` HARNESS-MANAGED block, and the committed `.ambr` snapshot via
`--snapshot-update`) — then run the four proof commands named in Success Criteria below in one pass,
since a partial commit leaves the pinned-set gates red by construction.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Grounded Q&A authoring flow (the skill body) | Harness authored-surface (`harness/skills/`) | — | Runtime-neutral source; the emitter, not the skill, projects it |
| Citation-integrity proof (`path:line` resolves) | Test tier (`tools/harness_lint/tests/`) | — | Same tier as every other structural skill gate (`test_skills.py`) |
| Pinned skill-name-set gate | Test tier (`tools/harness_lint/`, shared `caps.py`) | Emit tier (`tools/harness_emit/validate.py`) | `caps.py` is the single source both consumers re-import (line 24-25 of `test_skills.py`) |
| Skill/command/agent projection to `.opencode/`+`.claude/` | Emit tier (`tools/harness_emit/`) | — | Sole owner of runtime-shape divergence; never hand-authored |
| Ownership manifest (`emit-manifest.json`) | Emit tier (generated) | — | Written by `manifest.prune_then_write`, never hand-edited |
| Dangling-reference sweep (no tracked file names `skill-creator`) | Test tier (`tools/harness_lint/tests/`, new) | — | Mirrors `test_core_no_example_dep.py`'s `git ls-files`-scoped scan idiom |

## Standard Stack

No new library. This phase is a Markdown-source + Python-test change inside the existing harness
authoring/emit/lint stack. No `Package Legitimacy Audit` section applies — zero packages installed.

### Recommended Project Structure (no new directories; two paths change)
```
harness/skills/
├── harness-author/          # NEW — replaces skill-creator, widened scope
│   ├── SKILL.md
│   └── references/          # optional, per Claude's Discretion (per-kind templates vs. inline)
├── brownfield-adoption/      # EDITED — two skill-creator mentions become harness-author
│   └── SKILL.md
└── skill-creator/            # DELETED
```

## Architecture Patterns

### System Architecture Diagram

```
harness-author SKILL.md (authored, harness/skills/harness-author/)
        │
        │  Step 0: "why can't this live in an existing kind/skill?" (all 3 kinds)
        │  Step 1: shape rules per kind (name/description caps, dir-name match, ...)
        │  Step 2: cite path:line defaults (caps.py, test files, example artifacts)
        ▼
harness_lint/tests/test_skills.py, test_commands.py, test_agents.py   ← "the runnable checks" the
        │  (existing structural gates; harness-author POINTS at them, never restates their numbers)
        ▼
tools.harness_emit (python -m tools.harness_emit)
        │  iter_skills/iter_commands/iter_agents → validate.check_* → project_* → render_markdown
        ▼
   .opencode/{agent,command,skill}/**   .claude/{agents,commands,skills}/**
        │                                        │
        └──────────────┬─────────────────────────┘
                        ▼
        emit-manifest.json (regenerated, prune_then_write)
                        ▼
        CI: emit-drift (git diff --exit-code) — byte-clean or fail
```

A reader tracing "author a new skill" follows: write `harness/skills/<name>/SKILL.md` → run
`test_skills.py -x -q` → run `python -m tools.harness_emit` → `git diff --exit-code` on
`.opencode/`+`.claude/`+`emit-manifest.json` is empty. `harness-author`'s job is to make each of
those four steps concrete for whichever of the three kinds is being authored, with a resolving
citation instead of a restated number.

### Pattern 1: Progressive-disclosure skill body with disjoint routing description
**What:** frontmatter carries `name` (== directory) + `description` (verb-first "Use when… + does…",
a routing trigger token, disjoint from every sibling description); body stays under the ~500-line
warn threshold and defers depth to `references/`.
**When to use:** every `harness/skills/*/SKILL.md`, including the new `harness-author`.
**Example (existing skill, full text read in full):**
```markdown
---
name: context-budget
description: >-
  Use when deciding whether to fan out / delegate a task or work it inline — weighs the surface a
  task would pull into the current context against the room left to reason, and names the signals
  that tip the call to delegation via fan-out-synthesize versus keeping it inline. Consult before
  opening many files into one context.
---
# context-budget
...
## Related
- `harness/skills/fan-out-synthesize/SKILL.md` — the substrate this heuristic routes to...
```
Source: `harness/skills/context-budget/SKILL.md:1-16,41-44`.

### Pattern 2: Anti-sprawl justification as required written content, not a checkbox
**What:** a skill's body opens (or prominently states) *why a new directory was justified*, naming
the specific sibling skills it is disjoint from.
**When to use:** any new skill directory — this is `skill-creator`'s Step 0, which the phase must
generalize to commands and agents too.
**Example:**
```markdown
**Why this is a new skill, not an extension of an existing one:** none of this harness's other
skills (`python-conventions`, `data-contracts`, `skill-creator`,
`polyglot-boundary`, `two-plane-memory`, `fan-out-synthesize`,
`context-budget`) own the discover→draft→apply adoption lifecycle...
That is a genuinely disjoint routing trigger, so a new skill directory is justified
(skill-creator Step 0).
```
Source: `harness/skills/brownfield-adoption/SKILL.md:14-21` — **this exact block is one of the two
sites that must change**: the enumerated sibling list names `skill-creator` (line 15) and the
closing citation names `skill-creator Step 0` (line 21); both must read `harness-author` after the
absorption.

### Pattern 3: Command frontmatter — routes to a persona, `agent:` must resolve
**What:** `description` + `agent:` (+ optional `subtask: true`); body is the `$ARGUMENTS`-driven
mandated-order procedure.
**Example (full text read):** `harness/commands/component.md:1-9` —
```yaml
---
description: >-
  Use when you need to scaffold a new component or library — creates the package tree together with
  a self-sufficient per-package AGENTS.md (restating the non-negotiables) and a test harness, in the
  mandated order. Invoke to stand up a new components/<name>/ or libs/* member correctly.
agent: orchestrator
subtask: true
---
```
The `agent:` value is proven to resolve to a real `harness/agents/<agent>.md` by
`tools/harness_lint/tests/test_agent_referential_integrity.py:42-56` — this is the closest existing
precedent to a "citation resolves" test, though it validates a frontmatter field, not a body-embedded
`path:line` string (see Open Questions / Code Examples below for why it is not directly reusable).

### Pattern 4: Agent frontmatter — dual-representation (opencode `permission` + Claude `tools`)
**What:** one authored block carries both `mode`+`permission` (opencode) and `tools` (Claude); the
emitter SELECTS keys per target, never transpiles.
**Example (full text read):** `harness/agents/curator.md:1-17` — frontmatter shown carries
`mode: subagent`, a `permission` block (`read: allow`, `edit: allow`, `bash: {"*": ask, "uv *":
allow}`, `write: deny`), and `tools: Read, Edit, Bash, Grep, Glob`. Projection is
`tools/harness_emit/project_agent.py:22-23` (`_OPENCODE_KEYS` / `_CLAUDE_KEYS` fixed tuples).

### Anti-Patterns to Avoid
- **Restating a cap number in the skill body:** CONTEXT.md's locked decision — the body must point
  at `tools/harness_lint/caps.py` and the verify test as authority, never restate `_NAME_MAX = 64` /
  `_DESC_MAX = 1024` inline. A restated number is a second source that silently goes stale
  (`caps.py:109-110`).
- **Hand-editing `emit-manifest.json`:** it is a generated ownership manifest
  (`tools/harness_emit/manifest.py:65-94`, `prune_then_write`); a hand edit is overwritten (and
  possibly pruned-wrong) on the next `python -m tools.harness_emit` run.
- **Editing `.opencode/skill/skill-creator/` or `.claude/skills/skill-creator/` directly:** both are
  emitted copies; only the re-emit regenerates them. Deleting the source and re-emitting prunes the
  stale emitted directories automatically (manifest prune step, same file).
- **Splitting the rename across multiple commits:** the three-way pin
  (`caps.py::EXPECTED_SKILLS` ↔ `test_skills.py::test_expected_skills_present_no_sprawl` ↔
  `test_emit_determinism.py::test_emitted_skill_set_matches_expected`) means a directory rename with
  no `caps.py` edit is RED on all three simultaneously, and a `caps.py` edit with no directory rename
  is RED the same way in the other direction. CONTEXT.md's "one change" framing matches this: there
  is no valid intermediate commit state.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Skill/command/agent projection to both runtimes | A second frontmatter-shape templater inside the new skill's `references/` | `tools/harness_emit/{project_skill,project_command,project_agent}.py` (already generic across kinds) | `render_markdown` (`generate.py:117-137`) is already artifact-neutral; the skill should *cite* this, never re-describe transformation rules that could drift from it |
| "Does this path:line resolve" checking | A bespoke one-off script embedded in the skill's `references/` | A new `tools/harness_lint/tests/` module, parallel to `test_agent_referential_integrity.py`'s shape (parse the skill body, regex out `path:line`/anchor citations, assert `Path.is_file()` + line count / anchor-name presence) | Keeps the proof inside the test tier CONTEXT.md already designates as the harness's verification home; a script under `references/` would not run in CI |
| Skill-name-set enumeration | A second frozenset duplicating `EXPECTED_SKILLS` inside the new skill body | `tools/harness_lint/caps.py:139-150` (already the single source both `test_skills.py` and `tools/harness_emit/validate.py` import) | The whole point of `caps.py`'s extraction docstring (`caps.py:1-16`) is "a cap change lands in exactly one place" |

**Key insight:** every mechanism this phase needs already exists in the emit/lint tiers; the
authoring skill's only genuinely new artifact is the citation-integrity test, because nothing in the
repo today checks that a *prose-embedded* `path:line` reference actually resolves.

## Common Pitfalls

### Pitfall 1: Editing `caps.py` without regenerating `emit-manifest.json`/the `.ambr` snapshot
**What goes wrong:** `EXPECTED_SKILLS` flips to `harness-author`, the new skill directory exists, but
`tools/harness_emit/emit-manifest.json` (lines 35, 73 today reference `skill-creator`) and
`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` (lines 2471, 2477, 2807, 2810,
2814) still embed the old name — the manifest is stale until the next `python -m
tools.harness_emit` run, and the snapshot test fails until `--snapshot-update` is run and the new
`.ambr` is committed.
**Why it happens:** the manifest and the snapshot are both derived artifacts that only change on an
explicit regenerate step, not automatically alongside a source edit.
**How to avoid:** run `python -m tools.harness_emit` AND `uv run pytest
tools/harness_emit/tests/test_emit_determinism.py --snapshot-update` in the same commit as the
`caps.py`/directory change.
**Warning signs:** `git status` shows `emit-manifest.json` or the `.ambr` file unchanged after a
skill rename — that means the regenerate step was skipped.

### Pitfall 2: Treating `.planning/` historical hits as part of the "no dangling reference" gate
**What goes wrong:** a `git grep skill-creator` sweep (see Sources below) surfaces ~60 hits, the
overwhelming majority inside `.planning/milestones/`, `.planning/phases/03-*`, `.planning/research/`
— i.e. completed-phase records, PLAN/SUMMARY files, and the v2.0/v2.3/v2.5 archives. These are
append-only historical record, not live product surface; scoping the new dangling-reference test over
the whole tracked tree (rather than the live authored/emitted/config roots) would force editing
immutable history, which contradicts the append-only planning-archive convention this repo already
follows elsewhere (ADRs, `.planning/milestones/`).
**Why it happens:** a naive `git grep`/`git ls-files` sweep with no root scoping treats
`.planning/**` the same as `harness/**`.
**How to avoid:** scope the new test's `git ls-files` invocation to the same kind of explicit root
list `test_core_no_example_dep.py` already uses (`_CORE_ROOTS`, invoked as `git ls-files
*_CORE_ROOTS`, `test_core_no_example_dep.py:90`) — e.g. `AGENTS.md`, `CLAUDE.md`, `harness/`,
`tools/`, `.opencode/`, `.claude/` — and explicitly exclude `.planning/`.
**Warning signs:** the new test fails on `.planning/phases/03-agents-commands-skills/03-05-PLAN.md`
or similar historical files that were never in scope for this phase's absorption.

### Pitfall 3: The pinned-set gates fire on the wrong signal and get treated as "unrelated failures"
**What goes wrong:** an engineer renames the directory, edits `caps.py`, but three tests go red
(`test_skills.py::test_expected_skills_present_no_sprawl`,
`test_emit_determinism.py::test_emitted_skill_set_matches_expected`, and, before the manifest
regenerate, any snapshot/manifest-diff-based CI check) and each is triaged as a separate bug instead
of the single expected consequence of an incomplete one-change commit.
**Why it happens:** the three assertions live in different files/tiers (`tools/harness_lint/tests/`
vs `tools/harness_emit/tests/`) with no cross-reference telling the reader they are the same
invariant checked three times.
**How to avoid:** the plan should list all three as ONE verification step for the same commit, not
three separate "fix a test" tasks — see Validation Architecture below.
**Warning signs:** a plan wave that lands `caps.py` in one task and the directory rename in another.

### Pitfall 4: Forgetting the emitted-copy prune requires re-running the emitter, not `git rm`
**What goes wrong:** `.opencode/skill/skill-creator/SKILL.md` and `.claude/skills/skill-creator/
SKILL.md` are deleted by hand instead of via re-emit; the manifest's prune step
(`manifest.py:81-88`) is what performs the deletion safely (with GSD-lane exclusion and
confinement checks) — a hand `git rm` skips those guards and can also leave `emit-manifest.json`
still listing the (now-deleted) paths until the next emit run overwrites it anyway.
**How to avoid:** delete only the SOURCE (`harness/skills/skill-creator/`), then run `python -m
tools.harness_emit`; let `prune_then_write` remove the two stale emitted directories.
**Warning signs:** `emit-manifest.json` still lists a path with no file on disk (or vice versa) after
a manual deletion.

## Code Examples

### Every currently-tracked hit for `skill-creator` outside `.planning/` (complete change-set, Q1)

Found via `git grep -n "skill-creator" -- .` (whole tracked tree) and cross-checked against
`git ls-files | grep -i '\.ambr$'` for snapshot hits. The list below is every hit that is NOT inside
`.planning/` (which is append-only historical record per Pitfall 2 and out of scope):

| # | File | Line(s) | What must change |
|---|------|---------|-------------------|
| 1 | `harness/skills/skill-creator/SKILL.md` | whole file (46 lines) | DELETE (source moves to `harness-author`) |
| 2 | `harness/skills/brownfield-adoption/SKILL.md` | 15, 21 | edit the sibling-skill enumeration and the Step-0 citation to say `harness-author` |
| 3 | `tools/harness_lint/caps.py` | 143 (inside `EXPECTED_SKILLS`, `caps.py:139-150`) | swap the string `"skill-creator"` → `"harness-author"` |
| 4 | `AGENTS.md` | 108 (inside the `<!-- BEGIN HARNESS-MANAGED -->` block, `AGENTS.md:101-110`) | regenerated automatically by re-emit (`_merge_shared_markdown`, `generate.py:291-317`) — do NOT hand-edit |
| 5 | `tools/harness_emit/emit-manifest.json` | 35, 73 | regenerated automatically by `python -m tools.harness_emit` (`manifest.prune_then_write`) — do NOT hand-edit |
| 6 | `.claude/skills/skill-creator/SKILL.md` | whole file | pruned automatically by re-emit |
| 7 | `.opencode/skill/skill-creator/SKILL.md` | whole file | pruned automatically by re-emit |
| 8 | `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` | 2471, 2477, 2807, 2810, 2814 | regenerate via `uv run pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update`, then commit the new `.ambr` |

**Files that surfaced in the sweep but are correctly OUT of scope (historical/append-only, not
edited by this phase):** every hit under `.planning/` — `.planning/PROJECT.md`,
`.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/milestones/**`,
`.planning/phases/03-*`, `.planning/phases/05.5-*`, `.planning/phases/05.7-*`,
`.planning/phases/08-*`, `.planning/phases/36-*`, `.planning/phases/50a-harness-authoring/
50a-CONTEXT.md` (this phase's own context — expected to keep naming `skill-creator` as the thing
being absorbed), `.planning/research/**`. These are dated records of what was true when written;
editing them would falsify history. `50a-RESEARCH.md` (this file) is likewise expected to keep
naming `skill-creator` throughout, since it documents the absorption.

Confirms the CONTEXT.md list (`50a-CONTEXT.md:89-92`) is complete for the live/current tree: it named
`AGENTS.md`, `emit-manifest.json`, `caps.py`, `brownfield-adoption/SKILL.md`, plus the two emitted
copies — this sweep additionally surfaces the `.ambr` snapshot (item 8), which CONTEXT.md's list did
not name explicitly but which `test_emit_determinism.py:55-81`'s docstring (`"Mirrors the
tools/docs_sync committed-snapshot idiom"`) makes clear must also regenerate.

### `EXPECTED_SKILLS` — the pinned set to edit (Q1, caps.py:139-150)
```python
# tools/harness_lint/caps.py:139-150
EXPECTED_SKILLS = frozenset(
    {
        "python-conventions",
        "data-contracts",
        "skill-creator",          # ← becomes "harness-author"
        "polyglot-boundary",
        "two-plane-memory",
        "fan-out-synthesize",
        "context-budget",
        "brownfield-adoption",
    }
)
```

### `emit-manifest.json` provenance (Q2)
`tools/harness_emit/emit-manifest.json` is **generated**, not hand-maintained. Every run of
`python -m tools.harness_emit` calls `manifest.prune_then_write(written, manifest_path, root)`
(`tools/harness_emit/generate.py:456-457`), which:
1. Computes `current = sorted(_rel(p, root) for p in written)` — the paths just emitted.
2. Deletes any path in the PRIOR manifest that is absent from `current` (unless GSD-owned) —
   `manifest.py:81-88`.
3. Overwrites the manifest with `{"tool": "tools.harness_emit", "paths": current}`,
   `sort_keys=True, indent=2` + trailing LF — `manifest.py:90-93`.

So a rename requires no manual manifest edit: delete the source skill directory, author the new one,
run the emitter, and the manifest (and the two prior `skill-creator` emitted-copy entries) update and
prune themselves. The discovery mechanism for skills is `generate.iter_skills`
(`generate.py:183-194`), which globs `skills/*/SKILL.md` — a directory rename is picked up with zero
code change to the discovery layer.

### What breaks the moment `skill-creator` is deleted with no other edit (Q3 — sequence as ONE commit)
Deleting only `harness/skills/skill-creator/` (no `caps.py` edit, no re-emit) makes RED, in this
order of first-observation if run individually:
1. `tools/harness_lint/tests/test_skills.py::test_expected_skills_present_no_sprawl` — glob finds 7
   directories, `EXPECTED_SKILLS` still lists 8 including `skill-creator`; set mismatch
   (`test_skills.py:53-58`).
2. `tools/harness_emit/tests/test_emit_determinism.py::test_emitted_skill_set_matches_expected` —
   same class of assertion at the emit-tier (`test_emit_determinism.py:99-105`), independently red.
3. `tools/harness_emit/generate.py::emit`'s own runtime guard — `if skills: validate.check_skill_set(...)`
   (`generate.py:361-362`) raises `HarnessEmitError` the next time anyone runs
   `python -m tools.harness_emit`, so CI's `emit-drift` job (`ci.yml` job "Re-emit the harness
   surface", line 242) fails outright rather than producing a diff.
4. `harness/skills/brownfield-adoption/SKILL.md` still enumerates `skill-creator` as a sibling and
   cites "skill-creator Step 0" — no automated test currently catches this (it is prose, not
   frontmatter), which is exactly the gap CONTEXT.md's new "no tracked file references
   `skill-creator`" test is meant to close.
5. `AGENTS.md`'s HARNESS-MANAGED block still lists `skill-creator` until the next successful re-emit
   — but step 3 blocks re-emit from succeeding while `caps.py` is unedited, so this is downstream of
   fixing (1)+(2) first.

Conversely, editing ONLY `caps.py` (swap the string) with the directory still named `skill-creator`
produces the same three failures in the opposite direction (glob finds `skill-creator`, expected set
now wants `harness-author`). **There is no valid intermediate commit state** — the directory
create+delete and the `caps.py` edit must land together, exactly as CONTEXT.md's "one change"
decision states (`50a-CONTEXT.md:46-47`).

### Closest prior art for citation-integrity checking (Q4)
No existing test in this repo validates that a body-embedded `path:line` string resolves to a real
location. The two closest analogs, neither directly reusable as-is:

1. **`tools/harness_lint/tests/test_agent_referential_integrity.py:42-56`** —
   `test_command_agent_resolves_to_real_persona` resolves a **frontmatter field** (`agent:`) to a
   file path (`harness/agents/{agent}.md`), asserting `.is_file()`. This is the right SHAPE
   (parse → resolve → assert existence, fail loud with the offending name) but it checks one
   structured key, not a free-text citation embedded in prose.
2. **`tools/memory_regen/pointer_index.py`** — builds an index of "what points at each memory item"
   by scanning a fixed set of roots line-by-line and recording `{"file", "line", "kind"}` per
   referrer (`pointer_index.py:1-8`). This is the inverse problem: it discovers referrers to a KNOWN
   target, not whether an author-claimed `path:line` string resolves to a real target. It also only
   scans `docs/`, `harness/`, one file, `.memory/README.md`, `AGENTS.md`
   (`pointer_index.py:53-61`) — not the skill body itself as source.
3. **`tools/harness_lint/tests/test_core_no_example_dep.py:80-96`** — `_tracked_core_files()` and
   `_scan_lines()` are the closest MECHANISM for scanning a skill body line-by-line for a regex
   pattern and reporting `(lineno, line)` hits; this is the idiom to reuse for both the new
   citation-integrity test and the new "no dangling `skill-creator` reference" test.

**Conclusion: this must be new code.** A plan for this phase should scope a new
`tools/harness_lint/tests/test_harness_author_citations.py` (or similarly named module) that: (a)
parses `harness/skills/harness-author/SKILL.md`'s body for `path:line`-shaped citations (a regex over
something like `` `[\w./-]+\.\w+:\d+(-\d+)?` ``) or named-anchor citations, and (b) for each, opens
the cited file relative to repo root and asserts either the line exists (line-number form) or the
anchor string (function/test name/frontmatter key) is present in the file's text (anchor form,
matching the CONTEXT.md decision at `50a-CONTEXT.md:38-39`: "Citations anchor on stable names… rather
than bare line numbers").

### Two existing full-body skill shapes to mirror (Q "shapes to mirror")
Already reproduced above under Pattern 1/2 — `context-budget/SKILL.md` (16-line frontmatter+41-line
concise body, no `references/`) and `brownfield-adoption/SKILL.md` (uses a `references/`-free body
but a dense "Related" footer linking to sibling artifacts). `polyglot-boundary/SKILL.md` is the one
skill in the current 8 that DOES carry a `references/` subtree
(`emit-manifest.json:33,71` list `references/canonicalization-table.md`) — worth citing if
`harness-author`'s discretion point ("whether references/ holds per-kind templates") favors the
references pattern; `skill-creator/SKILL.md:44-46` itself already gestures at this ("Keep a template
SKILL.md and a checklist under `references/`") but the CURRENT `skill-creator` directory has no
`references/` subtree on disk — that line was aspirational, never implemented.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `skill-creator`: skills-only meta-authoring skill | `harness-author`: skills+commands+agents meta-authoring skill | This phase (50a) | Widens Step 0's anti-sprawl question to all three emitter-projected kinds; plugins/hooks explicitly stay out (no single-file source shape today, per CONTEXT.md) |
| Caps restated inline in an authoring skill (never was the case here — `skill-creator` already pointed at `caps.py`/`test_skills.py`) | Unchanged discipline, generalized: `harness-author` points at `caps.py` + the three structural test files, never restates a number | This phase reaffirms, does not change, the existing discipline | No regression risk — the pattern already exists in `skill-creator/SKILL.md:40-42` |

**Deprecated/outdated:** `skill-creator` itself — fully superseded, not merely renamed, since its
scope literally grows (skills → skills+commands+agents).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The new citation-integrity test should live under `tools/harness_lint/tests/` (not a new package) | Code Examples §"Closest prior art" | If the planner instead wants it inside `tools/harness_emit/tests/` (emit-time validation) rather than lint-time, the module location and its CI job attachment (`lint` vs `emit-drift`/`core-suite`) shift — either is defensible since `harness_lint` already owns the skill/command/agent structural gates (`test_skills.py`, `test_agents.py`, `test_commands.py`, `test_agent_referential_integrity.py`) and this is one more of the same family. No package addition either way (0 new packages holds). |
| A2 | The "no tracked file references `skill-creator`" test scopes to `AGENTS.md`, `CLAUDE.md`, `harness/`, `tools/`, `.opencode/`, `.claude/` and explicitly excludes `.planning/` | Pitfall 2 | If the intended scope is actually the WHOLE tracked tree including `.planning/`, this phase would need to edit ~50 historical PLAN/SUMMARY/RESEARCH files, which contradicts the append-only planning-archive convention observed everywhere else in this repo (ADRs, milestone archives) — recommend confirming scope explicitly in the plan rather than assuming |
| A3 | `harness-author`'s `references/` question (per-kind templates vs. inline body) has no forcing answer from existing code — `polyglot-boundary` is the only current skill using `references/`, and `skill-creator`'s own `references/` mention was aspirational (directory never created) | Code Examples §"Two existing full-body skill shapes" | Low risk either way — CONTEXT.md explicitly leaves this to Claude's Discretion "subject to the concise-body cap" |

## Open Questions

1. **Should the citation-integrity test require EVERY `path:line`-shaped string in the skill body to
   resolve, or only ones inside an explicit "Grounded defaults" section?**
   - What we know: CONTEXT.md requires "Every offered default carries a `path:line` that resolves"
     (`50a-CONTEXT.md:37`) — this is about offered DEFAULTS specifically, not incidental mentions
     (e.g., a citation inside a code comment example that intentionally shows a non-existent path).
   - What's unclear: whether the skill body will have a structurally distinguishable "defaults"
     region, or whether every citation-shaped string anywhere in the body is fair game for the test.
   - Recommendation: scope the regex to the whole body but exempt fenced code blocks (```...```),
     mirroring how `test_core_no_example_dep.py` already treats `harness/project.toml`'s
     `root =`/`persona =` lines as a sanctioned exemption (`test_core_no_example_dep.py:108-110`) —
     i.e., an explicit, narrow exemption list rather than scanning everything uncritically.

2. **Does the 8→8 pinned-set gate's `caps.py` docstring (lines 122-138) need its own prose edit?**
   - What we know: the comment block above `EXPECTED_SKILLS` narrates the phase-by-phase history of
     every skill addition/removal ("Phase 43... Phase 44... The eight entries below are the whole
     set."); it does not currently mention Phase 50a.
   - What's unclear: whether the plan should append a one-line note continuing that historical
     narration (consistent with the file's own convention) or leave it — the frozenset content is the
     load-bearing part, the docstring is advisory.
   - Recommendation: append one line, consistent with the file's existing self-documenting pattern
     (every prior skill-set change is narrated there).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (`uv run pytest`) |
| Config file | root `pyproject.toml` (workspace); no per-tool pytest.ini found for `tools/harness_lint` or `tools/harness_emit` beyond the shared root config |
| Quick run command | `uv run pytest tools/harness_lint/tests/test_skills.py tools/harness_emit/tests/test_emit_determinism.py -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MONO-10 (grounded Q&A, `path:line` defaults) | Every offered default's citation resolves in this checkout | unit (new) | `uv run pytest tools/harness_lint/tests/test_harness_author_citations.py -x -q` | ❌ Wave 0 — new module |
| MONO-10 (output lands under `harness/` only) | Emit round-trip byte-clean, `.opencode/`/`.claude/` change only via re-emit | integration | `python -m tools.harness_emit && git diff --exit-code -- .opencode .claude opencode.json AGENTS.md CLAUDE.md tools/harness_emit/emit-manifest.json` | ✅ mechanism exists (`ci.yml` "Re-emit the harness surface" job, line 242); the specific diff-scope command is the CI recipe, runnable locally |
| MONO-11 (skill-creator no longer exists, reachable via harness-author) | Structural set gate + reachability review | unit + manual-cited | `uv run pytest tools/harness_lint/tests/test_skills.py::test_expected_skills_present_no_sprawl -x -q` plus a written checklist mapping skill-creator's Step 0 / shape rules / verify step / shared-caps note onto harness-author's body (Specific Ideas §Criterion 3) | ✅ automated part exists; the "reachable" claim needs the new dangling-reference test below as its falsifiable half |
| MONO-11 (skill count 8→8, no dangling `skill-creator` reference) | Tracked-tree sweep | unit (new) | `uv run pytest tools/harness_lint/tests/test_skill_creator_absorbed.py -x -q` (or fold into the citation test module) | ❌ Wave 0 — new module |
| MONO-11 (zero new packages/commands/contracts) | Structural count gates | unit | `uv run pytest tools/harness_lint/tests/test_commands.py -x -q` (command count == 19, unchanged) + manual check `git ls-files 'tools/*/pyproject.toml' \| wc -l` unchanged + `git ls-files contracts/*.schema.json \| wc -l` unchanged | ✅ command-count gate exists (Phase 49 pinned it to 19); package/contract counts checked by absence of new files, no dedicated gate needed |
| Emit determinism (snapshot) | Committed `.ambr` matches re-render | unit | `uv run pytest tools/harness_emit/tests/test_emit_determinism.py -x -q` (requires prior `--snapshot-update` + commit) | ✅ exists, needs regeneration this phase |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_lint/tests/test_skills.py tools/harness_emit/tests/test_emit_determinism.py -x -q`
- **Per wave merge:** `uv run pytest` (full suite) + `python -m tools.harness_emit && git diff --exit-code`
- **Phase gate:** full suite green + `emit-drift`/`lint`/`core-suite` CI jobs green before
  `/verify-work`, per `ci.yml`'s existing `gate.needs` list (`ci.yml:329`, unchanged by this phase —
  MONO-11's "zero new gates" constraint).

### Wave 0 Gaps
- [ ] `tools/harness_lint/tests/test_harness_author_citations.py` (or equivalent name) — new
  citation-resolution proof (Success Criterion 1)
- [ ] A dangling-reference sweep test (new, same or sibling module) — proves no live tracked file
  under the scoped roots names `skill-creator` after the change (CONTEXT.md, `50a-CONTEXT.md:53-54`)
- [ ] `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` regeneration via
  `--snapshot-update` (not a new test, but a required Wave-0-adjacent artifact update)

*(Framework itself — pytest, `parse_frontmatter`, the `git ls-files`-scan idiom — already exists; no
new test framework or fixture infrastructure is needed, only two new test modules.)*

## Project Constraints (from CLAUDE.md)

- No model identifiers in any repo artifact, including the new `harness-author/SKILL.md` body
  (root `CLAUDE.md` binding constraint, restated in `AGENTS.md` "모델 아이덴티티" line and enforced
  structurally by `caps.py`'s `PLACEHOLDER_MODEL` token for agents — skills carry no `model` key at
  all per `project_skill.py:16`, so this is a non-issue for skill bodies specifically, but still
  applies to any prose the new skill writes about agents).
- Contract-first: `contracts/` is the single source of truth; this phase adds zero contracts (MONO-11)
  and touches none.
- Constitution plane is gated (`contracts/`, `docs/adr/`, `docs/glossary.md`) — this phase does not
  write there.
- Derived plane is not hand-edited — `emit-manifest.json`, the two emitted trees, and the `.ambr`
  snapshot are all derived; every plan task must regenerate them via their generator, never hand-edit.
- Core never depends on an instance (GEN-04) — the new skill body must not reference `examples/`.
- GSD workflow enforcement — this research and any subsequent plan/execute work runs through the GSD
  command entry points per root `CLAUDE.md`'s "GSD Workflow Enforcement" section.

## Sources

### Primary (HIGH confidence — direct file reads in this checkout)
- `.planning/phases/50a-harness-authoring/50a-CONTEXT.md` — locked decisions, deferred scope
- `.planning/REQUIREMENTS.md:54-61,107-108` — MONO-10/11 requirement text
- `.planning/ROADMAP.md:450-492` — Phase 50a goal/scope/non-goals/success criteria
- `harness/skills/skill-creator/SKILL.md` — full 46-line source being absorbed
- `harness/skills/brownfield-adoption/SKILL.md`, `harness/skills/context-budget/SKILL.md` — full
  skill-shape examples
- `harness/commands/component.md` — full command-shape example
- `harness/agents/curator.md` — full agent-shape example
- `tools/harness_lint/caps.py` (whole file, 151 lines)
- `tools/harness_lint/tests/test_skills.py` (whole file, 126 lines)
- `tools/harness_lint/tests/test_agent_referential_integrity.py` (whole file, 57 lines)
- `tools/harness_lint/tests/test_core_no_example_dep.py:1-125` — `git ls-files`-scoped scan idiom
- `tools/harness_emit/emit-manifest.json` (whole file), `generate.py` (whole file, 480 lines),
  `manifest.py` (whole file, 95 lines), `project_skill.py`, `project_command.py`, `project_agent.py`
  (whole files)
- `tools/harness_emit/tests/test_emit_determinism.py` (whole file, 106 lines)
- `tools/memory_regen/pointer_index.py:1-80`
- `AGENTS.md` (whole file, 111 lines)
- `git grep -n "skill-creator" -- .` — full tracked-tree sweep (run in this session)
- `git ls-files | grep -i '\.ambr$'` — snapshot inventory (run in this session)

### Secondary / Tertiary
None used — v2.6 explicitly runs no external research round (`.planning/ROADMAP.md:200-202`), and
this phase is entirely repo-internal per the phase brief.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new library; every mechanism cited is read directly from this checkout.
- Architecture: HIGH — emit/lint/manifest flow traced end-to-end via `generate.py`/`manifest.py`.
- Pitfalls: HIGH for the three-way pin and manifest-regeneration pitfalls (directly observed in code);
  MEDIUM for the `.planning/` scoping question (Assumption A2 — the correct scope is inferred from
  repo convention, not stated explicitly in any test).

**Research date:** 2026-07-30
**Valid until:** stable — this is a structural/internal phase with no external dependency; re-verify
only if `tools/harness_emit/` or `tools/harness_lint/caps.py` change again before planning executes.
