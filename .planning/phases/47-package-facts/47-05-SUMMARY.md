---
phase: 47-package-facts
plan: 05
subsystem: infra
tags: [ci-wiring, derived-artifact, stale-derived, no-growth-proof, monorepo]

# Dependency graph
requires:
  - phase: 47-02
    provides: "tools/memory_regen/package_facts.py + .memory/derived/package-facts.md"
provides:
  - "ci.yml's stale-derived job widened (regen + diff) to guard .memory/derived/package-facts.md, job set and gate.needs byte-unchanged"
  - ".memory/derived/package-facts.md committed (re-included via .gitignore contents-form pattern)"
  - "tools/harness_lint/tests/test_ci_stale_derived.py structurally proves the widening (SC5)"
  - "/refresh-memory + curator persona locally regenerate package-facts.md; both runtime trees re-emitted byte-clean"
affects: [48, 49]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Widened an EXISTING gated CI job's regen command + diff path list rather than adding a job — the phase's binding no-growth proof (SC5)"

key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - .gitignore
    - tools/harness_lint/tests/test_ci_stale_derived.py
    - harness/commands/refresh-memory.md
    - harness/agents/curator.md
    - .opencode/agent/curator.md
    - .opencode/command/refresh-memory.md
    - .claude/agents/curator.md
    - .claude/commands/refresh-memory.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - .memory/derived/package-facts.md

key-decisions:
  - "Renamed test_stale_derived_regenerates_both_derived_generators to ...regenerates_all_three_derived_generators (Claude's discretion per plan interfaces note) rather than leaving a stale 'both' name now covering three modules"
  - "Committed the first fresh regeneration of .memory/derived/package-facts.md in Task 1's commit (the moment .gitignore re-includes it), not deferred to a later commit"
  - "Updated the committed emit-determinism snapshot (test_emit_determinism.py) in Task 2's commit since the prose change to curator.md/refresh-memory.md is captured in that snapshot"

patterns-established:
  - "SC5 no-growth proof pattern: widen an existing job's run: command + diff path list + structural test tuple, never add a job/gate/command"

requirements-completed: [MONO-01, MONO-04]

# Metrics
duration: 20min
completed: 2026-07-30
---

# Phase 47 Plan 05: Package Facts CI Wiring Summary

**Widened the existing `stale-derived` CI job (never added one) to regenerate and diff `.memory/derived/package-facts.md`, re-included it via `.gitignore`, structurally proved the widening in `test_ci_stale_derived.py`, and wired `/refresh-memory` + `curator` to regenerate it locally — with both runtime trees re-emitted byte-clean.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-07-30 (session start)
- **Completed:** 2026-07-30
- **Tasks:** 2 completed
- **Files modified:** 11

## Accomplishments

- `.github/workflows/ci.yml`'s `stale-derived` job: `run:` line for "Regenerate the committed-derived set" now chains `&& uv run python -m tools.memory_regen.package_facts`; both the `git add -A --` and `git diff --cached --exit-code --` path lists in "Fail on any stale committed-derived artifact" gained `.memory/derived/package-facts.md`; the failure-echo block's printed fix-commands were widened identically. No other job, no `gate.needs` change.
- `.gitignore` gained exactly one line, `!.memory/derived/package-facts.md`, directly beneath the existing `contracts-index.md` re-inclusion line, same contents-form idiom.
- `tools/harness_lint/tests/test_ci_stale_derived.py`: `_DERIVED_PATHS` widened to 3 entries; `test_stale_derived_regenerates_both_derived_generators` renamed to `test_stale_derived_regenerates_all_three_derived_generators` and gained a third `assert "tools.memory_regen.package_facts" in joined` line — the SC5 proof line.
- `harness/commands/refresh-memory.md` step 2 and `harness/agents/curator.md`'s regen-command bullet list both now mention `package-facts.md` / `tools.memory_regen.package_facts` alongside the existing `contracts_index` reference. Re-emitted via `uv run python -m tools.harness_emit` — only `curator.md` and `refresh-memory.md` changed in both `.opencode/` and `.claude/`; a second immediate re-emit produced zero further diff (idempotent).
- The first fresh regeneration of `.memory/derived/package-facts.md` is now committed (23 packages, 2 edges) — no longer silently gitignored.

## Task Commits

Each task was committed atomically:

1. **Task 1: Widen ci.yml, .gitignore, and the stale-derived structural test** - `746e087` (feat)
2. **Task 2: Wire refresh-memory.md + curator.md, then re-emit both runtimes** - `e510a46` (docs)

**Plan metadata:** (pending — this SUMMARY commit)

## Files Created/Modified

- `.github/workflows/ci.yml` - `stale-derived` job's regen `run:` line, both `git add -A --`/`git diff --cached --exit-code --` path lists, and the failure-echo fix-command text widened to cover `package-facts.md`.
- `.gitignore` - one new re-inclusion line for `package-facts.md`.
- `tools/harness_lint/tests/test_ci_stale_derived.py` - `_DERIVED_PATHS` widened to 3 entries; regen-modules assertion function renamed and gained a third assertion.
- `harness/commands/refresh-memory.md` - step 2's regen line + paragraph widened.
- `harness/agents/curator.md` - new "Package facts (committed-derived)" bullet.
- `.opencode/agent/curator.md`, `.opencode/command/refresh-memory.md`, `.claude/agents/curator.md`, `.claude/commands/refresh-memory.md` - re-emitted from the two harness source files above.
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` - updated to match the prose change (`--snapshot-update`).
- `.memory/derived/package-facts.md` - first committed regeneration (23 packages, 2 edges).

## Decisions Made

- Renamed `test_stale_derived_regenerates_both_derived_generators` to `test_stale_derived_regenerates_all_three_derived_generators` (the plan explicitly left this naming to Claude's discretion) since "both" would be stale once a third module-string assertion was added.
- Committed `.memory/derived/package-facts.md`'s first fresh regeneration in Task 1's commit, the same commit that makes `.gitignore` stop excluding it — avoiding an interim state where the file is trackable but not yet tracked.
- Updated the committed `test_emit_determinism.ambr` snapshot in Task 2's commit (the prose changes to `curator.md`/`refresh-memory.md` are captured verbatim inside that snapshot's projected-tree text) rather than leaving it stale.

## Deviations from Plan

None (Rule 3 - blocking issue, self-resolved). The plan's Task 2 acceptance criteria did not explicitly anticipate the committed `test_emit_determinism.ambr` snapshot going stale after the prose edit + re-emit, but the full-suite run surfaced it as a single expected snapshot failure; updated via `--snapshot-update` per the repo's own golden-approval idiom, then re-verified the full suite green. This is a mechanical consequence of the plan's own instructed edit, not a scope change.

## Issues Encountered

None.

## SC5 No-Growth Proof (hard constraint)

**Job set unchanged** (`git show HEAD~2:.github/workflows/ci.yml | grep -E "^  [a-z-]+:$"` vs current — identical, `JOB SET UNCHANGED` confirmed by `diff`).

**`gate.needs` byte-unchanged:**
```
needs: [setup, lang-tests, contract-check, drift, golden, core-suite, lint, emit-drift, stale-derived, workspace]
```
identical before and after (line 329, unchanged in both `git show HEAD~2` and the working tree).

**`stale-derived` never interpolates `${{ github.event.* }}`:** `test_stale_derived_never_interpolates_event_input` — untouched by this plan — passes both before and after the widening (`uv run pytest tools/harness_lint/tests/test_ci_stale_derived.py -x -q` → 8 passed).

## Mutation Verification (acceptance criterion — "every new assertion must be able to fail")

Per the hard constraints: temporarily mutated the new assertion string in
`test_stale_derived_regenerates_all_three_derived_generators` from
`"tools.memory_regen.package_facts"` to `"tools.memory_regen.package_facts_BOGUS"`.
- Result: `AssertionError: stale-derived must regen package-facts via tools.memory_regen.package_facts` — the test FAILED as expected, proving the assertion is falsifiable.
- Reverted immediately (the working-tree edit was reapplied via the Edit tool after an accidental `git checkout --` discard); full suite re-confirmed green.

## GEN-04 Compliance

`grep -rn "examples/" tools/memory_regen tools/harness_lint/tests/test_ci_stale_derived.py` → zero hits.

## Idempotent Re-emit Proof

`uv run python -m tools.harness_emit` run a second and third time immediately after the first produced no further `git status --short` diff — confirmed idempotent, matching the `emit-drift` CI job's exact re-emit-diff-clean check.

## SessionStart Injector Non-Interference

`grep -rn "package_facts\|package-facts" tools/memory_regen/inject.py .opencode/plugin/session-inject.ts` → zero hits. Neither this plan nor Plan 47-02 touched the injector; the SessionStart payload assembly is byte-identical with and without this phase by construction (no reference to the new artifact exists anywhere in the injection path).

## Full Suite

`uv run pytest -q` → 912 passed (911 unchanged + 1 updated snapshot), 8 snapshots passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 47 (package-facts) is now complete across all 5 plans: detection (47-01), the generator + committed artifact (47-02), the override slot + contract-ownership attribution (47-03/47-04), and this plan's CI wiring / no-growth proof (47-05).
- `.memory/derived/package-facts.md` is a durably committed, gate-guarded derived artifact; Phase 48 (per-package convention profiles) and Phase 49 (`/impact`) can rely on `build_facts()` (in-process) or the committed markdown remaining fresh.
- No architectural changes; no new gate, job, command, or contract introduced anywhere in the phase.

---
*Phase: 47-package-facts*
*Completed: 2026-07-30*
