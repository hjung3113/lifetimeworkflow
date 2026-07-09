---
phase: 05-despecialization
plan: 05
subsystem: testing
tags: [pytest, guard-test, adr, madr, template, monorepo, diataxis, contract-guard]

# Dependency graph
requires:
  - phase: 05-03
    provides: history-preserving domain move to examples/log-parser/ (semiconductor seed + libs/dotnet twin relocated)
  - phase: 05-04
    provides: harness/project.toml language/instance config slot + GEN-03 consistency gate
provides:
  - GEN-04 core→example single-direction dependency guard (tools/harness_lint/tests/test_core_no_example_dep.py) with live negative controls
  - Root docs recast to the reusable-template shape (AGENTS.md monorepo map + CLAUDE.md identity)
  - Log-parser instance docs (examples/log-parser/{AGENTS.md,README.md}) + Diátaxis explanation (docs/explanation/template-and-instances.md)
  - ADR-0002 (accepted, complements ADR-0001) recording the de-specialization, landed via the human approval path
affects: [phase-5.5, GEN-05, phase-6-ci, template-consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structural guard test (git ls-files subprocess, shell=False) enforcing a one-directional core→instance dependency, with self-proving negative controls"
    - "Reusable-template repo shape: domain-neutral core at root + swappable instances under examples/<name>/"
    - "Constitution-plane ADR landed through the live contract-guard gate via GOLDEN_APPROVE_HUMAN (drift-only, no --no-verify)"

key-files:
  created:
    - tools/harness_lint/tests/test_core_no_example_dep.py
    - docs/adr/0002-general-template-de-specialization.md
    - examples/log-parser/AGENTS.md
    - examples/log-parser/README.md
    - docs/explanation/template-and-instances.md
  modified:
    - AGENTS.md
    - CLAUDE.md
    - docs/adr/README.md
    - libs/python/normalize/core.py
    - libs/python/AGENTS.md
    - tools/memory_regen/repo_map.py
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/memory_regen/tests/test_agents_md.py

key-decisions:
  - "GEN-04 guard is SCOPE A (CODE deps only): flags examples/ path refs, import examples, and the moved components/toy-converter token; does NOT flag bare libs/dotnet prose (authored-surface genericization deferred to GEN-05)."
  - "Stale-ref sweep extended to two test-file narrative comments that embedded examples/log-parser/ literals (reworded, comments only) so the must-have truth 'nothing path-references examples/**' holds literally and the pure line-scan guard passes."
  - "CLAUDE.md project identity reframed via a NEW non-managed 'Template & Instances (ADR-0002)' section rather than editing the GSD-managed source:PROJECT.md block (which regen would clobber and which test_agents_md guards indirectly)."
  - "ADR-0002 records the normalize split with the CORRECT rationale — python normalize+fixtures STAY as language-neutral core tooling; libs/dotnet MOVES because 'core is language-neutral' (not the invalid uv/GEN-04 packaging reason)."

patterns-established:
  - "Guard test with live negative controls: a synthetic core string containing each forbidden token is asserted flagged, so the scan can never silently no-op."
  - "Template↔instance split documented in Diátaxis explanation + per-instance nearest-wins AGENTS.md + instance README."

requirements-completed: [GEN-04]

# Metrics
duration: 15min
completed: 2026-07-09
---

# Phase 5 Plan 05: De-specialization Guard + Template Docs Recast + ADR-0002 Summary

**GEN-04 core→example single-direction dependency guard (git ls-files scan with live negative controls), root docs recast to the reusable-template shape, and MADR ADR-0002 landed through the live contract-guard gate via GOLDEN_APPROVE_HUMAN.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-09
- **Completed:** 2026-07-09
- **Tasks:** 2
- **Files modified:** 13 (5 created, 8 modified)

## Accomplishments
- Guard test proves the one-directional core→instance invariant: nothing under `tools/`, `harness/`, `libs/` imports or path-references `examples/**` (or the moved `components/toy-converter`), with three live negative controls + a sanctioned `[instance] root` exemption.
- Swept stale `libs/dotnet`/`components` refs (core.py docstring, libs/python/AGENTS.md, repo_map DEFAULT_SOURCE_DIRS) and two test-comment `examples/` literals so the core tree is genuinely dependency-clean.
- Recast root `AGENTS.md` monorepo map + `CLAUDE.md` identity to the reusable-template shape (domain-neutral core + `examples/<instance>/` seeds); moved log-parser specifics into `examples/log-parser/{AGENTS.md,README.md}`; added the Diátaxis `template-and-instances.md` explanation.
- Wrote ADR-0002 (accepted, complements ADR-0001), landed through the live gate (no `--no-verify`); appended the append-only index row.
- Full non-example suite green: **366 passed** (guard included; the DEF-05-02-1 token-leak tests did not trip in this run).

## Task Commits

Each task was committed atomically through the live gate (GOLDEN_APPROVE_HUMAN active, no `--no-verify`):

1. **Task 1: Core→example no-dependency guard + stale-ref sweep (GEN-04)** — `5d32e0b` (test)
2. **Task 2: Template docs recast + ADR-0002** — `23a9dc8` (docs)

## Files Created/Modified
- `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 guard: scans tracked core files for `examples/` refs / `import examples` / `components/toy-converter`; excludes self; exempts `[instance] root`; 3 live negative controls.
- `docs/adr/0002-general-template-de-specialization.md` — MADR ADR (accepted): generic re-scope, precise normalize split, language slot, drift-only approval path; complements ADR-0001.
- `docs/adr/README.md` — appended the `0002` index row (append-only; 0001 untouched).
- `AGENTS.md` — monorepo map recast to core/instance template shape (retains the members `test_agents_md.py` asserts: `contracts/`, `golden/`, `libs/python`, `tools/`, `.memory/`).
- `CLAUDE.md` — added non-managed "Template & Instances (ADR-0002)" section; fixed the moved `libs/dotnet/AGENTS.md` pointer.
- `examples/log-parser/AGENTS.md` — new nearest-wins per-instance rules (restated non-negotiables + instance-local rules).
- `examples/log-parser/README.md` — new instance doc (what it is, how it uses the core, .NET egress-deferred note).
- `docs/explanation/template-and-instances.md` — new Diátaxis explanation (split + how to add an instance).
- `libs/python/normalize/core.py`, `libs/python/AGENTS.md`, `tools/memory_regen/repo_map.py` — stale `libs/dotnet`/`components` refs genericized.
- `tools/docs_sync/tests/test_docs_sync_determinism.py`, `tools/memory_regen/tests/test_agents_md.py` — reworded narrative comments to drop `examples/` literals (comments only, behavior-neutral).

## Decisions Made
- **Guard is SCOPE A (CODE deps only):** flags `examples/` path refs, `import examples`, and the moved `components/toy-converter` token; does not flag bare `libs/dotnet` prose (deferred to GEN-05) — over-reaching would RED legitimately-deferred content.
- **Normalize split rationale (ADR-0002):** python `normalize` + `normalize-fixtures` STAY as the harness's language-neutral core tooling (uv member, core-imported); `libs/dotnet` MOVES as the example's language-side impl because "core is language-neutral" — explicitly NOT the invalid uv/GEN-04 packaging reason.
- **CLAUDE.md reframing placement:** added a new non-managed section instead of editing the GSD-managed `source:PROJECT.md` block (regen-safe + keeps `test_agents_md` profile-block-untouched green).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded two test-file narrative comments carrying `examples/log-parser/` literals**
- **Found during:** Task 1 (guard authoring)
- **Issue:** `tools/docs_sync/tests/test_docs_sync_determinism.py:23` and `tools/memory_regen/tests/test_agents_md.py:23,43` carried `examples/log-parser/` in narrative comments (added by 05-03). The plan assumed zero `examples/` refs in core ("root='' → no examples/ refs"); a pure line-scan guard would flag these, and the must-have truth "nothing path-references examples/**" requires them gone.
- **Fix:** Reworded the comment lines to "the log-parser example / example instance" (dropped the literal path). Comments only — behavior-neutral; both test files stay green.
- **Files modified:** tools/docs_sync/tests/test_docs_sync_determinism.py, tools/memory_regen/tests/test_agents_md.py
- **Verification:** guard + both affected test modules green; full suite 366 passed.
- **Committed in:** `5d32e0b` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to make the one-directional invariant literally hold and keep the suite green. No scope creep — the guard's SCOPE A (bare `libs/dotnet` prose) was preserved; only `examples/` literals were removed.

## Issues Encountered
- The GEN-03/DEF-05-02-1 concern (3 commit_gate drift-block tests leaking the live `GOLDEN_APPROVE_HUMAN` token) did **not** manifest in this run — the full non-example suite passed 366/366 with the token active. No action needed here; DEF-05-02-1 remains tracked.

## User Setup Required
None - no external service configuration required. (The `GOLDEN_APPROVE_HUMAN` token was already active in the session env; it should be removed after the constitution-plane change lands, per 05-RESEARCH Q3 — never commit the token.)

## Next Phase Readiness
- Phase 5 success criteria 4 (core→example guard, non-example suite green) and 5 (template docs + ADR-0002) are met — this is the final Phase 5 plan.
- Deferred to GEN-05 (Phase 5.5): authored-surface genericization of bare `libs/dotnet` prose (dotnet-engineer persona, dotnet-conventions/normalization-catalog/pipeline-patterns skills, new-normalization-rule command, libs/normalize-spec.md / libs/python/AGENTS.md / core.py residual prose).
- Standing blocker: BOOT-01 .NET 10 SDK egress-denied — the example's .NET side stays proven via the recorded-output twin until the install hosts are allowlisted.

## Self-Check: PASSED

---
*Phase: 05-despecialization*
*Completed: 2026-07-09*
