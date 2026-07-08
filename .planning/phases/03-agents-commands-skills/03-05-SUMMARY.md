---
phase: 03-agents-commands-skills
plan: 05
subsystem: harness-skills
tags: [skills, progressive-disclosure, structural-validation, anti-sprawl]
requires:
  - tools/harness_lint/frontmatter.py (Plan 02 shared parser)
provides:
  - harness/skills/{dotnet-conventions,python-conventions,golden-testing,data-contracts}/SKILL.md (SKILL-01)
  - harness/skills/{skill-creator,normalization-catalog,pipeline-patterns}/SKILL.md (SKILL-02)
  - tools/harness_lint/tests/test_skills.py (structural cap gate)
affects:
  - Phase-6 emitter (consumes harness/skills as neutral source)
tech-stack:
  added: []
  patterns:
    - progressive disclosure (frontmatter always-loaded + concise body + references/ pointer)
    - shared identical caps for opencode AND Claude (200-vs-1024 correction)
    - glob-driven structural validator reusing parse_frontmatter
key-files:
  created:
    - harness/skills/dotnet-conventions/SKILL.md
    - harness/skills/python-conventions/SKILL.md
    - harness/skills/golden-testing/SKILL.md
    - harness/skills/data-contracts/SKILL.md
    - harness/skills/skill-creator/SKILL.md
    - harness/skills/normalization-catalog/SKILL.md
    - harness/skills/pipeline-patterns/SKILL.md
    - tools/harness_lint/tests/test_skills.py
  modified: []
decisions:
  - "Caps are identical for both runtimes (name ≤64, desc ≤1024 HARD; body >500 WARN) per RESEARCH 200-vs-1024 correction — single shared rule set, no per-runtime divergence."
  - "Body line-count over 500 uses warnings.warn (advisory), never an assertion — matches D-07."
  - "Descriptions authored verb-first + disjoint; test pins exactly 7 skill dirs so an 8th fails loudly (anti-sprawl P8/T-03-18)."
metrics:
  duration: 12min
  tasks: 3
  files: 8
  completed: 2026-07-08
---

# Phase 3 Plan 05: Skills (7) + Structural Cap Validator Summary

Authored the seven progressive-disclosure skills (4 core + skill-creator meta + 2 domain) as `harness/skills/<name>/SKILL.md` with disjoint verb-first routing descriptions reflecting the real repo, plus `test_skills.py` enforcing the shared name/description caps, regex, dir-name match, reserved-word/XML-tag bans, and the exactly-7 anti-sprawl set — with body length as warn-only.

## What Was Built

- **Four core skills (SKILL-01):**
  - `dotnet-conventions` — .NET 10 SDK / xunit.v3 / Verify.XunitV3 / JsonSchema.Net + §4.3–4.6 emit rules (no-BOM, LF, InvariantCulture, UTC), reflecting `libs/dotnet/AGENTS.md`.
  - `python-conventions` — uv workspace + lockfile discipline, ruff, pyright, pytest/syrupy, module-path invocation, reflecting `libs/python/AGENTS.md`.
  - `golden-testing` — `tools.golden_runner` normalized-equivalence (no byte-diff), `.received`/`.verified` + syrupy, human-gated `/golden-approve` (exit-3 refusal), "machines gate, humans ratify".
  - `data-contracts` — contract-first, `contracts/` layout, JSON Schema Draft 2020-12, `check-jsonschema`, RFC 8785 schema-hash drift gate incl. `format-conventions.schema.json` (P14).
- **Meta + domain skills (SKILL-02):**
  - `skill-creator` — forces the anti-sprawl "why not an existing skill?" question (P8) BEFORE authoring, then the caps/shape/verify checklist.
  - `normalization-catalog` — data-driven maker/model rule kinds (normalization vs correction; enrichment vs fix), `(input,expected)` case shape, breaking-vs-non-breaking change policy, reflecting `contracts/normalization/`.
  - `pipeline-patterns` — carryover/state shapes + live/rework/catchup scenario patterns and the incremental≡full-reprocess equivalence discipline, reflecting `contracts/state/`.
- **Structural cap validator:** `tools/harness_lint/tests/test_skills.py` — glob-driven over `harness/skills/*/SKILL.md`, reuses `parse_frontmatter`; 30 parametrized/aggregate checks.

## Verification

- `uv run pytest tools/harness_lint/tests/test_skills.py -x -q` → 30 passed.
- `uv run pytest tools/harness_lint -q` → 98 passed.
- `uv run pytest -q` (full) → 198 passed, 2 skipped (known .NET egress deferral, 01-06).

Acceptance reasoning: `test_description_within_caps_and_routes` asserts `len(desc) <= 1024`, so a 1025-char description FAILS; `test_body_line_cap_only_warns` calls `warnings.warn` with no assertion, so a 600-line body only WARNS — matching D-07.

## Deviations from Plan

None — plan executed exactly as written. No auto-fixes, no authentication gates.

## Known Stubs

None. The skills are authored knowledge documents reflecting real repo facts; where domain values are placeholders (CONTRACT-01 seeds), each skill states so explicitly and points at the constitution plane, which is intentional and out of scope per CONTRACT-01.

## Self-Check: PASSED

- All 8 created files exist on disk (verified below).
- All 3 task commits present in git log.
