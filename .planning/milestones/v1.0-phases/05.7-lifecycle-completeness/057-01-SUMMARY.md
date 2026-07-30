---
phase: 5.7
plan: "01"
slug: must-have-inner-loop
wave: 1
status: complete
created: 2026-07-09
---

# Phase 5.7 · Plan 01 — SUMMARY (MUST-HAVE, LIFE-01..05)

Fixed the broken contract→implement→test→debug inner loop. All domain-neutral; guard sets updated
in-wave; non-example suite green.

## Delivered
- **LIFE-01** `harness/commands/contract-check.md` — thin macro: `check-jsonschema` over
  `contracts/**` schema/instance pairs (presence-safe) + `tools.contract_drift.drift` RFC-8785 gate.
  Resolves the dangling `/contract-check` referenced by `new-contract-rule` + `CLAUDE.md`.
- **LIFE-02** `harness/skills/golden-debug/` (SKILL.md + `references/canonicalization-axes.md`) — the
  7-axis red-golden decision tree (discriminator + fix-side per axis); reuses `tools.golden_runner`
  `.received`/`.verified`.
- **LIFE-03** `harness/skills/polyglot-boundary/` (SKILL.md + `references/canonicalization-table.md`)
  — the §4.3–4.6 invariants as a single source-of-truth pointer to `libs/normalize-spec.md`.
- **LIFE-04** `harness/agents/templates/engineer.md` (neutral engineer template, OUTSIDE the persona
  glob) + `harness/commands/add-language.md` (derive persona into the instance + register in
  `project.toml` + matrix scope — three-in-sync, GEN-03 safe). `python-engineer` = reference
  instantiation.
- **LIFE-05** `git mv new-normalization-rule.md → new-contract-rule.md`, naming neutralized;
  `CLAUDE.md`/instance-skill references updated; no dangling command.

## Guards
- `EXPECTED_SKILLS` += `golden-debug`, `polyglot-boundary`. `test_commands` (subset) + referential
  integrity green (all commands → real personas). Prose guard clean on new core assets.

## Verification
- `uv run pytest tools/harness_lint` green; full non-example `uv run pytest` green.
- `/contract-check` exercised: step 1 presence-safe SKIP (schemas convention-only), step 2 drift OK.
