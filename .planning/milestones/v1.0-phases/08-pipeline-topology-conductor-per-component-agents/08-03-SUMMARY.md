---
phase: 08-pipeline-topology-conductor-per-component-agents
plan: 03
subsystem: harness-core-agents
tags: [component-engineer, template, anti-sprawl-gate, component-scaffold, PIPE-03, GEN-04]
requires:
  - harness/agents/templates/engineer.md (the fill-in-the-blanks template idiom)
  - tools/harness_lint/tests/test_agents.py (VALID_MODES / ALLOWED_PERMISSION_KEYS / parse_frontmatter)
  - harness/commands/add-language.md (mandated-order + all-three-or-none Guard idiom)
  - harness/project.toml [[components]]/[pipeline] topology slot (PIPE-01)
provides:
  - "Neutral component-engineer persona template (anti-sprawl-exempt, subagent-mode, least-privilege)"
  - "/component scaffold extension: derive a per-component agent + register the topology component"
  - "test_agent_templates.py — the templates/ anti-sprawl + shape gate (EXPECTED_TEMPLATES)"
affects:
  - Plan 08-04 (instance overlay instantiates the template into concrete per-component agents)
tech-stack:
  added: []
  patterns:
    - "Clone engineer.md template banner + frontmatter + least-priv bash for a per-component persona"
    - "Reuse VALID_MODES/ALLOWED_PERMISSION_KEYS across gates (import, don't re-derive) so they cannot drift"
    - "EXPECTED_TEMPLATES frozenset grows independently of EXPECTED_PERSONAS (templates are NOT personas)"
key-files:
  created:
    - harness/agents/templates/component-engineer.md
    - tools/harness_lint/tests/test_agent_templates.py
  modified:
    - harness/commands/component.md
decisions:
  - "Template is stage-keyed and domain-neutral: routing trigger keys on the <COMPONENT> stage (<STAGE>), not on parser/converter language-side vocabulary — keeps it a pure fill-in-the-blanks scaffold"
  - "The templates/ gate imports VALID_MODES/ALLOWED_PERMISSION_KEYS from test_agents rather than re-declaring them, so the two structural gates stay in lockstep"
  - "EXPECTED_PERSONAS stays 4 — the template lives in agents/templates/ (non-recursive agents/*.md glob), so it is anti-sprawl-exempt like engineer.md"
metrics:
  duration: 7min
  tasks: 3
  files: 3
  completed: 2026-07-10
---

# Phase 08 Plan 03: Neutral component-engineer template + /component scaffold + template gate Summary

PIPE-03 — added the neutral `component-engineer` fill-in-the-blanks persona template (anti-sprawl-exempt
under `harness/agents/templates/`), extended `/component` to derive a per-component agent from it and
register the component in the instance topology slot, and closed the long-standing gap where
`templates/*.md` was validated by nothing with a new structural anti-sprawl + shape gate.

## What Was Built

**Task 1 — component-engineer template (`9d7e1fe`)**
- New `harness/agents/templates/component-engineer.md` cloning the `engineer.md` idiom: the
  not-an-active-persona HTML-comment banner (templates/ placement → non-recursive glob → NOT a core
  persona; `/component` instantiates a COPY into the instance), `name: <COMPONENT>-engineer`,
  `mode: subagent`, `permission` with `read/edit: allow` + `bash {"*": ask, "<BASH_SCOPE>": allow}`,
  `tools: Read, Edit, Bash, Grep, Glob`.
- Description carries a `use`/`when` routing trigger keyed on the component's **stage**
  (`<COMPONENT>` / `<STAGE>` placeholders). New placeholders: `<COMPONENT>`, `<STAGE>`,
  `<LANG>`/`<TOOLCHAIN>`/`<TEST_CMD>`, `<CONSUMES>`/`<PRODUCES>`.
- Body keeps contract-first, §4.3–4.6 process/file/DB-only boundary, golden-gate (never self-bless),
  derived-plane-not-hand-edited; closes with the per-package `AGENTS.md` pointer. Fully domain-neutral
  (placeholders only — GEN-04 clean).

**Task 2 — templates/ anti-sprawl + shape gate (`3994b1d`)**
- New `tools/harness_lint/tests/test_agent_templates.py` pointing `_TEMPLATES_DIR = _AGENTS_DIR / "templates"`.
  `EXPECTED_TEMPLATES = frozenset({"engineer", "component-engineer"})`; `test_templates_no_sprawl`
  asserts the stem set equals it exactly. Parametrized shape checks (subagent mode, permission keys ⊂
  valid set, least-privilege bash `*: ask` + a scoped allow, routing-trigger description). Reuses
  `VALID_MODES`/`ALLOWED_PERMISSION_KEYS`/`parse_frontmatter` from `test_agents` (no drift).

**Task 3 — /component component-binding scaffold (`ad628ec`)**
- Edited `harness/commands/component.md`: added a "## Mandated order (keep the three in sync) — when
  the package maps to a topology component" section cloning `add-language.md`'s numbered-step +
  all-three-or-none Guard idiom: (1) derive the `component-engineer` agent from the template into the
  instance `agents/` filling every placeholder from the `[[components]]` entry; (2) register/verify the
  `[[components]]` + `[pipeline]` edge; (3) keep `test_pipeline_config.py` green. Frontmatter
  `agent: orchestrator`, `subtask: true` unchanged (referential integrity intact). Domain-neutral body.

## Verification

- `uv run pytest tools/harness_lint/tests/test_agent_templates.py -x` → passed (no_sprawl + parametrized shape).
- `uv run pytest tools/harness_lint/tests/test_agents.py::test_expected_personas_present_no_sprawl` → passed (EXPECTED_PERSONAS still 4).
- `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_agent_referential_integrity.py` → passed.
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` → 18 passed (GEN-04 green — no `examples/`/`libs/dotnet`/domain token in any new core file incl. docstrings/prose).
- Full non-example suite: `uv run pytest` → **430 passed, 3 snapshots passed** (was 421 at 08-02; +9 from the templates gate).

## Deviations from Plan

None - plan executed exactly as written.

## must_haves Truth Check

- A neutral component-engineer template exists under `harness/agents/templates/` and is NOT counted as a core persona — YES (EXPECTED_PERSONAS stays 4; template lives in the non-recursive-glob subdir).
- `/component` binds a per-component agent from the template and registers the component in the instance topology slot — YES (mandated-order section + Guard).
- A structural gate validates `templates/` contains exactly `{engineer, component-engineer}`, each subagent-mode with valid least-privilege perms and a routing-trigger description — YES (`test_agent_templates.py`).

## Threat Register Check

- T-8-01 (over-broad bash) — mitigated: template grants only `{"*": ask, "<BASH_SCOPE>": allow}`; `test_template_bash_is_least_privilege` + permission-subset check enforce it.
- T-8-05 (persona sprawl via template placement) — mitigated: `test_templates_no_sprawl` pins EXPECTED_TEMPLATES; EXPECTED_PERSONAS stays 4.
- T-8-04 (model identifier leak) — mitigated: placeholders only, no real model identifier; existing model-identity gates green.

## Anti-Sprawl

Adding `test_agent_templates.py` trips no EXPECTED_* artifact set (test modules are not enumerated).
The new template is the FIRST member of a NEW pinned set (`EXPECTED_TEMPLATES`) it introduces — it is
NOT counted against `EXPECTED_PERSONAS` (still 4). No persona-set update required.

## Known Stubs

None — the template is an intentional fill-in-the-blanks scaffold (placeholders by design, like
`engineer.md`); Plan 04 instantiates it into concrete per-component agents under the instance.

## Self-Check: PASSED

- FOUND: harness/agents/templates/component-engineer.md
- FOUND: tools/harness_lint/tests/test_agent_templates.py
- FOUND: harness/commands/component.md (modified)
- FOUND commit 9d7e1fe (Task 1)
- FOUND commit 3994b1d (Task 2)
- FOUND commit ad628ec (Task 3)
