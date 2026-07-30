---
phase: 01-constitution-golden-core
plan: 03
subsystem: docs
tags: [diataxis, madr, adr, glossary, contract-first, golden, two-plane]

# Dependency graph
requires:
  - phase: 01-constitution-golden-core (01-01)
    provides: bootstrap toolchain + directory conventions the docs describe (SessionStart, verify.sh)
provides:
  - Diátaxis docs skeleton (tutorials/how-to/reference/explanation index pages)
  - reference/ quadrant flagged DERIVED (populated by /docs-sync in Phase 3, DOCS-03)
  - docs/glossary.md ubiquitous-language seed (harness + domain terms)
  - docs/adr/0001 MADR record of the walking-skeleton architecture
  - docs/adr/README.md append-only/immutable/supersede ADR convention
affects: [01-02 (contracts referenced by ADR/glossary), Phase 2 (derived plane), Phase 3 (/docs-sync populates reference/), Phase 4 (polyglot linter reuses §4-5 core)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Diátaxis four-quadrant docs structure with derived reference/ quadrant"
    - "MADR 4.x ADR log: numbered, append-only, immutable, supersede-not-edit"
    - "Single-source glossary (ubiquitous language) — link, never redefine"

key-files:
  created:
    - docs/tutorials/README.md
    - docs/how-to/README.md
    - docs/reference/README.md
    - docs/explanation/README.md
    - docs/glossary.md
    - docs/adr/0001-walking-skeleton-golden-core.md
    - docs/adr/README.md
  modified: []

key-decisions:
  - "reference/ is derived-from-contracts (DOCS-03, Phase 3 /docs-sync) — placeholder only this phase, never hand-authored"
  - "adr/0001 records only decisions locked in CONTEXT.md D-01..D-09 + SKELETON.md — no invented decisions"
  - "MADR append-only/supersede convention chosen so decisions are auditable, not silently edited (threat T-03-01)"

patterns-established:
  - "Diátaxis skeleton: each quadrant is an index README listing placeholder stubs; content grows later"
  - "ADR immutability: supersede via a new numbered ADR + Status cross-links, never edit accepted decisions"

requirements-completed: [DOCS-01, DOCS-02]

# Metrics
duration: 2min
completed: 2026-07-08
---

# Phase 1 Plan 03: Diátaxis Docs Skeleton + Glossary + MADR adr/0001 Summary

**Constitution-plane docs half: four-quadrant Diátaxis skeleton with a contract-derived reference/ placeholder, an ubiquitous-language glossary seed, and MADR adr/0001 immutably recording the walking-skeleton architecture (two-canonicalizer split, A-model boundary, golden human gate, two-plane split).**

## Performance

- **Duration:** 2 min
- **Started:** 2026-07-08T03:12:01Z
- **Completed:** 2026-07-08T03:15:00Z
- **Tasks:** 2
- **Files modified:** 7 (all created)

## Accomplishments
- Diátaxis tree: tutorials/how-to/reference/explanation, each with a purpose-describing index and placeholder page stubs.
- reference/README.md explicitly marks the quadrant as DERIVED from contracts/ via /docs-sync in Phase 3 (DOCS-03) — must not be hand-authored.
- docs/glossary.md seeds harness vocabulary (golden equivalence, normalized comparison, two canonicalizers, RFC 8785/JCS, contract-drift gate, .received/.verified, A-model boundary, constitution vs derived plane, walking skeleton) plus domain terms framed from the parserimprove GLOSSARY.
- docs/adr/0001 (MADR 4.x, Status: accepted) records the locked architecture: A-model CLI boundary, Python-only JCS hasher vs dual-language §4.3–4.6 TSV comparator, shared normalization core reused by Phase-4 linter, .received/.verified human gate (machines gate/humans ratify), contract-first schema-as-source-of-truth, materialized §4-5 conventions for P14 drift, two-plane split.
- docs/adr/README.md documents the numbered/append-only/immutable/supersede-not-edit MADR convention (DOCS-02) with an index table.

## Task Commits

Each task was committed atomically:

1. **Task 1: Diátaxis tree + glossary seed** - `3aa67fc` (docs)
2. **Task 2: MADR adr/0001 + adr/README.md** - `23fb8cc` (docs)

**Plan metadata:** see final docs commit (SUMMARY.md + STATE.md + ROADMAP.md)

## Files Created/Modified
- `docs/tutorials/README.md` - Learning-oriented quadrant index + stubs
- `docs/how-to/README.md` - Task-oriented quadrant index + stubs
- `docs/reference/README.md` - Information-oriented quadrant; flagged DERIVED (Phase 3 DOCS-03)
- `docs/explanation/README.md` - Understanding-oriented quadrant index + stubs
- `docs/glossary.md` - Ubiquitous-language seed (harness + domain terms)
- `docs/adr/0001-walking-skeleton-golden-core.md` - MADR record of the walking-skeleton architecture
- `docs/adr/README.md` - Append-only/immutable/supersede MADR convention + index

## Decisions Made
- Kept all pages as short placeholders per plan (skeleton, not authored content); reference/ intentionally has no hand-authored content.
- ADR content is strictly bounded to decisions locked in CONTEXT.md (D-01..D-09) and SKELETON.md — no new decisions invented.
- Domain glossary terms seeded (not copied verbatim) from the parserimprove GLOSSARY, with the DW-template forbidden-terms note dropped as out of scope for the seed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Docs half of the Phase 1 constitution plane is complete; adr/ is ready to record future decisions immutably.
- reference/ placeholder is in place for Phase 3 /docs-sync (DOCS-03) to populate from contracts/.
- Glossary is ready to expand as contracts (01-02) land domain terms.
- Note: BOOT-01 (.NET 10 install) remains blocked by egress policy per STATE.md — unrelated to this docs plan.

## Self-Check: PASSED

All 7 created files verified on disk; both task commits (3aa67fc, 23fb8cc) present in git history.

---
*Phase: 01-constitution-golden-core*
*Completed: 2026-07-08*
