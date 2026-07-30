---
description: >-
  Use when you need to scaffold a new component or library — creates the package tree together with
  a self-sufficient per-package AGENTS.md (restating the non-negotiables) and a test harness, in the
  mandated order. Invoke to stand up a new components/<name>/ or libs/* member correctly.
agent: orchestrator
subtask: true
---

# /component — scaffold a new component/lib (structure + AGENTS.md + tests)

Scaffolds a new package in the **mandated order** so a member is never created without its rules
or its test harness (Pattern 4, P11). The component name comes from `$ARGUMENTS`.

## Mandated order (do not skip a step)

1. **Structure first** — create the package tree under `components/<name>/` (or `libs/<name>/`)
   with the language-appropriate project file:
   - Python member → `pyproject.toml` (uv workspace member — matches
     `members = ["libs/python", "tools/*", "components/*"]`; a missing project file fails `uv sync`).
   - .NET member → `<Name>.csproj`.

2. **Self-sufficient per-package AGENTS.md** — write `components/<name>/AGENTS.md` that
   **RESTATES the non-negotiables verbatim** (contract-first, §4.3–4.6 boundary invariants,
   constitution-plane-is-gated, derived-not-hand-edited). Codex replaces nested AGENTS.md rather
   than concatenating, so the file must be self-sufficient — never inherit-only (P11). As part of
   this same step, regenerate the derived package-facts artifact (`uv run python -m
   tools.memory_regen.package_facts`) and assert the newly scaffolded package now resolves its
   own convention profile — e.g. `python -c "from tools.harness_config import conventions_for;
   print(conventions_for('components/<name>/...'))"` should report the new package's own id, not
   fall through to the repo-wide default.

3. **Test harness** — add the test scaffold (Python `tests/` + a failing placeholder test, or the
   .NET xunit.v3 test project) so the member is verifiable from creation.

## Guard

- The order is enforced: structure → self-sufficient AGENTS.md → tests. A member without its
  per-package rules or without a test harness is incomplete. The profile-regeneration and
  `conventions_for` resolution check belongs inside step 2 — it is not a new step.
- Stage new files individually when committing; do not blanket-add the working tree.
