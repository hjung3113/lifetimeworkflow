---
phase: 02-two-plane-memory-rules
plan: 05
subsystem: rules
tags: [agents-md, nearest-wins, contract-first, p11, claude-md, monorepo]

# Dependency graph
requires:
  - phase: 02-01
    provides: two-plane .memory/ layout + committed state / gitignored derived boundary
  - phase: 02-02
    provides: non-ignorable SessionStart injector (the runtime backstop AGENTS.md prose defers to)
  - phase: 01
    provides: Phase-1 tooling referenced by golden-path (contract_drift, golden_runner, contract_hash)
provides:
  - Root AGENTS.md — monorepo map, golden-path command table, 5 non-negotiable rules, lazy-load
  - libs/python/AGENTS.md + libs/dotnet/AGENTS.md — language-local rules + restated non-negotiables (P11)
  - CLAUDE.md 'Agent Rules — see AGENTS.md' pointer section (GSD-managed blocks untouched)
  - tools/memory_regen/tests/test_agents_md.py — structural test (existence, restatement, pointer, profile-intact)
affects: [phase-03-config, phase-04-hooks, opencode-emitter]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Nearest-wins AGENTS.md: root full rules + per-package refinement"
    - "P11 backstop: non-negotiables restated per-package (never inherit-only) AND carried by the injector"
    - "CLAUDE.md pointer-not-duplicate: single source is AGENTS.md"

key-files:
  created:
    - AGENTS.md
    - libs/python/AGENTS.md
    - libs/dotnet/AGENTS.md
    - tools/memory_regen/tests/test_agents_md.py
  modified:
    - CLAUDE.md

key-decisions:
  - "Per-package AGENTS.md placed at libs/python + libs/dotnet (real code trees; components/* are placeholders) — A5."
  - "CLAUDE.md pointer inserted in the non-managed gap between GSD workflow-end and profile-start blocks — no GSD block edited."
  - "Non-negotiables restated verbatim per-package (contract-first, §4.3-4.6 boundary, constitution-gated, derived-not-hand-edited) — P11: Codex replaces nested AGENTS.md rather than concatenating."

patterns-established:
  - "P11 backstop: prose is advisory; injector (02-02) + Phase-4 hooks are the true enforcement."
  - "Structural rules test asserts restatement (not inheritance) + GSD profile block integrity."

requirements-completed: [RULES-01, RULES-02]

# Metrics
duration: 9min
completed: 2026-07-08
---

# Phase 2 Plan 5: Nearest-wins AGENTS.md rules layer Summary

**Root + per-package (Python/.NET) AGENTS.md resolving nearest-wins, with the non-negotiables restated per-package (P11 backstop) and a CLAUDE.md pointer — enforced by a 6-assertion structural test.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-08T07:26Z
- **Completed:** 2026-07-08T07:35Z
- **Tasks:** 2
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments
- Root `AGENTS.md`: monorepo map (constitution/derived planes + polyglot layout), golden-path command table wired to the Phase-1 tools (`tools.contract_drift`, `tools.golden_runner`, `tools.contract_hash`, `uv run pytest`, memory_regen), 5 non-negotiable rules, and the lazy-load rule (the mechanism the 02-02 injector implements).
- Per-package `libs/python/AGENTS.md` (uv/pytest/ruff/pyright) and `libs/dotnet/AGENTS.md` (dotnet/xunit.v3/Verify.XunitV3/JsonSchema.Net), each **self-sufficient** — restating contract-first, the §4.3–4.6 boundary invariants (BOM/LF/InvariantCulture/UTC/TSV-null), and constitution-plane-is-gated, rather than inheriting them (P11).
- `CLAUDE.md` pointer section added in the non-GSD-managed gap; the GSD profile/workflow/skills blocks are untouched.
- Structural test `test_agents_md.py` (6 assertions) — green; full workspace suite still green (88 passed, 2 expected .NET-egress skips).

## Task Commits

1. **Task 1: Root AGENTS.md + CLAUDE.md pointer** - `079efe4` (feat)
2. **Task 2: Per-package AGENTS.md + structural test** - `8ba6fa9` (feat)

**Plan metadata:** (final docs commit — this SUMMARY + STATE + ROADMAP)

## Files Created/Modified
- `AGENTS.md` - Root rules: monorepo map, golden-path table, non-negotiables, lazy-load
- `libs/python/AGENTS.md` - Python-local rules + restated non-negotiables (P11)
- `libs/dotnet/AGENTS.md` - .NET-local rules + restated non-negotiables (P11)
- `CLAUDE.md` - Added 'Agent Rules — see AGENTS.md' pointer section (GSD blocks intact)
- `tools/memory_regen/tests/test_agents_md.py` - Structural test for the rules layer

## Decisions Made
- **Placement (A5):** per-package files at `libs/python` + `libs/dotnet` (real code today; `components/*` are placeholders) — either resolves nearest-wins.
- **CLAUDE.md insertion point:** the blank gap between `<!-- GSD:workflow-end -->` and `<!-- GSD:profile-start -->` — keeps every GSD-managed block byte-identical (T-02-13 mitigation).
- **Restatement over inheritance:** each per-package file repeats the invariants because merge semantics differ per runtime (P11); a dedicated test asserts the restatement is present.

## Deviations from Plan

None - plan executed exactly as written.

The Task 1 acceptance grep (`grep -q 'contract-first'`) is case-sensitive lowercase; the initial draft only had capitalized "Contract-first" headings, so a lowercase occurrence was added to the closing paragraph before committing. This was a within-task adjustment to meet the stated acceptance criterion, not a scope change.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Rules layer complete — Phase 3 (CONFIG) can wire opencode `instructions`/plugin surface to these AGENTS.md, and Phase 4 (hooks) turns the advisory non-negotiables into hard enforcement (contract-guard, polyglot-boundary linter).
- This is the LAST plan of Phase 2 — all four Phase-2 success criteria (two-plane layout, derived regeneration, nearest-wins rules, non-ignorable injection) are now met.

## Self-Check: PASSED

All 4 created files + 1 modified file present on disk; both task commits (`079efe4`, `8ba6fa9`) exist in git history.

---
*Phase: 02-two-plane-memory-rules*
*Completed: 2026-07-08*
