---
phase: 10-context-economy-fan-out-synthesize-orchestration-v2-0
plan: 01
subsystem: infra
tags: [fan-out, context-economy, skill, command, json-schema, harness, orchestrator, explorer]

# Dependency graph
requires:
  - phase: 03-skills-commands
    provides: SKILL.md progressive-disclosure shape, references/ byte-copy convention, thin command frontmatter
  - phase: 05-despecialization
    provides: GEN-04 core→example no-dependency guard, domain-neutral core planes
  - phase: 07-emitter
    provides: caps.py EXPECTED_SKILLS single-source-of-truth shared by lints + emit validators
provides:
  - fan-out-synthesize skill (decompose → dispatch N read-only explorer subtasks → recover schema-bounded citation-bearing summaries → orchestrator synthesizes)
  - domain-neutral fan-out-return JSON Schema (Draft 2020-12) co-located under the skill's references/
  - thin /fan-out-synthesize command (agent: orchestrator, subtask: true)
  - EXPECTED_SKILLS enumeration entry (fan-out-synthesize) — anti-sprawl set-equality holds
  - Wave-0 structural gate for the return contract (test_fan_out_return_contract.py)
affects: [10-02 context-budget, 10-03 emit round-trip, phase-11 multi-repo fan-out]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Return-contract as a co-located references/ JSON Schema (D-08), NOT under contracts/ — self-contained, no $ref into the constitution plane"
    - "Fan-out dispatch via the runtime's native task/Task affordance — no bespoke dispatch engine, no new persona (D-03/D-05)"
    - "Schema-bounded citation-bearing return (paths + claims, additionalProperties:false) so the conductor synthesizes without re-reading raw files (ECON-02)"

key-files:
  created:
    - harness/skills/fan-out-synthesize/SKILL.md
    - harness/skills/fan-out-synthesize/references/fan-out-return.schema.json
    - harness/commands/fan-out-synthesize.md
    - tools/harness_lint/tests/test_fan_out_return_contract.py
  modified:
    - tools/harness_lint/caps.py

key-decisions:
  - "Return contract is a self-contained Draft 2020-12 JSON Schema (unit + claims[] of {claim, confidence?, citations[]}, additionalProperties:false at every level) co-located under the skill references/, never under contracts/ (D-07/D-08)"
  - "Dispatch reuses the read-only explorer persona via native task affordance; the return contract is prompt-enforced, not persona-enforced — EXPECTED_PERSONAS stays 5 (D-03/D-05/D-06)"
  - "No runtime conformance validator added — the return is an ephemeral runtime value; the Wave-0 gate is structural over the schema file only (D-09, Open-Q2 SKIP)"

patterns-established:
  - "Pattern 1: context-economy fan-out substrate — workers return paths+claims, conductor synthesizes lean; reusable single-repo substrate Phase 11 (γ) generalizes"

requirements-completed: [ECON-01, ECON-02]

# Metrics
duration: 6min
completed: 2026-07-13
---

# Phase 10 Plan 01: Fan-out/Synthesize Core Surface Summary

**Authored the ECON-01/ECON-02 substrate — a fan-out-synthesize skill (decompose → dispatch N read-only explorer subtasks → recover schema-bounded citation-bearing summaries → orchestrator synthesizes), its co-located domain-neutral Draft 2020-12 return-contract JSON Schema, a thin /fan-out-synthesize command routing to the orchestrator, the anti-sprawl enumeration entry, and the Wave-0 structural gate.**

## Performance

- **Duration:** ~6 min
- **Tasks:** 2
- **Files modified:** 5 (4 created, 1 edited)

## Accomplishments
- `fan-out-synthesize` skill documents the four-step context-economy procedure (decompose → dispatch → recover → synthesize) using the orchestrator's EXISTING task affordance — no bespoke dispatch engine, no new persona.
- `fan-out-return.schema.json` — self-contained Draft 2020-12 schema (`required: [unit, claims]`, `additionalProperties: false` at every level, `claim` documented as "a single terse assertion, NOT a file excerpt", citations = path+lines only). No `$ref` into `contracts/`; domain-neutral.
- Thin `/fan-out-synthesize` command (`agent: orchestrator`, `subtask: true`, prose-only) points at the skill + return contract; usable by a human OR the conductor.
- `fan-out-synthesize` enumerated in `EXPECTED_SKILLS` (9 → 10; the sibling plan adds the 11th) — skill-set equality holds; EXPECTED_PERSONAS untouched (stays 5).
- Wave-0 gate `test_fan_out_return_contract.py` pins existence, JSON validity, Draft 2020-12, closed object, required citation-bearing fields, no `contracts/` `$ref`, and domain-neutrality.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author fan-out-synthesize skill + return-contract schema + enumerate it** - `d2885d8` (feat)
2. **Task 2: Author /fan-out-synthesize command + return-contract Wave-0 test** - `325d3e0` (feat)

## Files Created/Modified
- `harness/skills/fan-out-synthesize/SKILL.md` - The decompose→dispatch→recover→synthesize procedure (ECON-01)
- `harness/skills/fan-out-synthesize/references/fan-out-return.schema.json` - Citation-bearing return contract, Draft 2020-12 (ECON-02)
- `harness/commands/fan-out-synthesize.md` - Thin entry point → agent: orchestrator, subtask: true (ECON-01)
- `tools/harness_lint/caps.py` - Added "fan-out-synthesize" to EXPECTED_SKILLS (anti-sprawl enumeration)
- `tools/harness_lint/tests/test_fan_out_return_contract.py` - Wave-0 structural gate for the return contract (ECON-02)

## Decisions Made
- Kept the return schema self-contained (no `$ref` into `contracts/`) and domain-neutral so GEN-04 core→example independence and the domain contract-drift hash gate are untouched (D-08).
- Reused the read-only `explorer` persona and the orchestrator's native `task` affordance rather than adding a dispatch engine or persona — the return contract is enforced by the skill/command prompt (D-03/D-05/D-06).
- Did NOT add a runtime conformance validator (D-09 / Open-Q2): the return is ephemeral; the Wave-0 gate is structural over the schema file only.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. `uv run pytest tools/harness_lint -q` is green (227 passed) after both tasks.

## Scope Boundary Note
This plan authors the harness SOURCE only. The emit round-trip to `.opencode/` + `.claude/` (and the `emit-manifest.json` / Regime-B `AGENTS.md` block regeneration) is plan 10-03's job and was intentionally NOT performed here.

## Next Phase Readiness
- ECON-01/ECON-02 core surface is authored and structurally gated; ready for plan 10-02 (context-budget skill, ECON-03) and plan 10-03 (emit round-trip).
- `EXPECTED_SKILLS` is at 10 with fan-out-synthesize enumerated; the sibling plan's context-budget addition brings it to 11.

## Self-Check: PASSED

All created files exist (SKILL.md, fan-out-return.schema.json, fan-out-synthesize.md, test_fan_out_return_contract.py) and both task commits are present (`d2885d8`, `325d3e0`).

---
*Phase: 10-context-economy-fan-out-synthesize-orchestration-v2-0*
*Completed: 2026-07-13*
