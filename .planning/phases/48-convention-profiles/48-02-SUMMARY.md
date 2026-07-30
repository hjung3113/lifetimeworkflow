---
phase: 48-convention-profiles
plan: 02
subsystem: infra
tags: [derived-plane, python, harness-config, memory-regen, monorepo]

# Dependency graph
requires:
  - phase: 48
    plan: 01
    provides: "conventions_for(path, cfg=None, facts=None) — pure nearest-wins join, consumed here"
provides:
  - "render(facts, cfg=None) — package_facts.py's Convention Profiles section (MONO-05/MONO-06)"
  - ".memory/derived/package-facts.md — committed artifact now carrying the profile join per package"
affects: [48-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Extend an existing derived-plane generator's render()/build_facts() in place instead of adding a sibling artifact — zero ci.yml/.gitignore diff, rides the existing stale-derived job"
    - "Lazy in-function cross-package import (tools.harness_config.conventions_for inside render()) mirroring loader.py's own reverse-direction lazy import of package_facts"

key-files:
  created: []
  modified:
    - tools/memory_regen/package_facts.py
    - tools/memory_regen/tests/test_package_facts.py
    - tools/memory_regen/tests/__snapshots__/test_package_facts.ambr
    - .memory/derived/package-facts.md

key-decisions:
  - "render()'s new cfg parameter is additive/optional (defaults to None) so write()'s and main()'s existing render(build_facts()) call sites needed zero edits"
  - "None profile fields render as the literal '(none)' string, never a blank cell, per the plan's explicit behavior requirement"
  - "The real nested-pair proof (libs/python vs root) asserts on the agents_md pointer and package/dir, never on test/format — both packages share one python [[languages]] row so their commands are identical (RESEARCH.md Pitfall 2)"

patterns-established:
  - "Any future section added to package_facts.render() should follow the same list-of-lines-then-join table idiom and stay entirely in-memory when asserted against the real tree"

requirements-completed: [MONO-05, MONO-06]

# Metrics
duration: 20min
completed: 2026-07-30
---

# Phase 48 Plan 02: Convention Profiles Rendered into package-facts.md Summary

**Extended `package_facts.render()` with a `## Convention Profiles` table, sourced entirely through `conventions_for()`, and regenerated the committed `.memory/derived/package-facts.md` — zero `ci.yml`/`.gitignore` diff, byte-identical on regeneration.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-07-30T00:21:00Z
- **Completed:** 2026-07-30T00:41:49Z
- **Tasks:** 2 completed
- **Files modified:** 4 (package_facts.py, test_package_facts.py, the `.ambr` snapshot, and the committed `.memory/derived/package-facts.md`)

## Accomplishments
- `render(facts, cfg=None)` now emits a third `## Convention Profiles` section — every `test`/`format`/`bash_scope` cell is a live read via `conventions_for()`, never a restated literal; `None` fields render as `(none)`.
- The committed `.memory/derived/package-facts.md` shows the nested-wins property directly: `logparser-normalize` (`libs/python`) points at `libs/python/AGENTS.md` while `logparser-harness` (`.`, `is_default = true`) points at the root `AGENTS.md`.
- `test_real_tree_render_structure` extended with in-memory-only assertions on this same distinction (never committed to a snapshot — GEN-04).
- The hermetic 4-package synthetic snapshot (`widget-*` fixtures) now also covers the new section; re-verified stably green without `--snapshot-update`.
- Regeneration proven byte-identical via delete + regenerate sha256 comparison (`0dc0a5a0...` both times).
- `git diff --stat -- .github/workflows/ci.yml .gitignore` both empty — the plan's hard no-growth constraint held exactly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend render() with a Convention Profiles section** - `fa9a5f6` (feat)
2. **Task 2: Extend tests + regenerate and commit the artifact** - `306d480` (test)

**Plan metadata:** (this commit)

## Files Created/Modified
- `tools/memory_regen/package_facts.py` - `render()` gains `cfg: dict | None = None`; new `_render_value()` helper (`None` → `"(none)"`); a lazy in-function `from tools.harness_config import conventions_for` builds one profile row per package; module docstring now names MONO-05/MONO-06 alongside MONO-01/MONO-02.
- `tools/memory_regen/tests/test_package_facts.py` - `test_real_tree_render_structure` extended with the in-memory nested-wins assertions (root vs `libs/python` `AGENTS.md` pointer).
- `tools/memory_regen/tests/__snapshots__/test_package_facts.ambr` - `test_render_matches_committed_snapshot`'s entry regenerated to include the new section for the 4 synthetic `widget-*` packages.
- `.memory/derived/package-facts.md` - regenerated; now 23 packages × 3 tables (Packages / Dependency Edges / Convention Profiles).

## Decisions Made
- Kept the cross-module import (`package_facts.py` → `tools.harness_config.conventions_for`) lazy and in-function, matching `loader.py`'s own established convention for the reverse direction, even though no actual import cycle exists in this direction (verified: `tools.harness_config`'s module-level code never imports `tools.memory_regen`).
- Chose to key the nested-wins real-tree proof on `agents_md`/`package`/`dir` rather than `test`/`format`, since `libs/python` and root share the identical `python` language row (documented Pitfall 2 in RESEARCH.md) — asserting on commands there would be a false claim.

## Deviations from Plan

None - plan executed exactly as written.

## Mutation Check (per plan's explicit requirement)

Ran for real, as instructed by Task 2's action:
1. Temporarily changed the extended assertion from `assert "libs/python/AGENTS.md" not in root_row` to `assert "libs/python/AGENTS.md" not in inner_row` (comparing `libs/python`'s row against itself instead of the root row).
2. `uv run pytest tools/memory_regen/tests/test_package_facts.py::test_real_tree_render_structure -x -q` **FAILED** with `AssertionError: assert 'libs/python/AGENTS.md' not in '...libs/python/AGENTS.md...'` — confirming the mutated form is trivially false (not a "check that cannot fail" in the wrong direction) while the correct form (comparing the two DIFFERENT rows) is the one that actually proves the nested-wins property.
3. Reverted to the correct two-different-rows comparison; re-ran `uv run pytest tools/memory_regen/tests/test_package_facts.py -x -q` → 15 passed.

## Issues Encountered
None.

## Verification Evidence

- `uv run pytest tools/memory_regen/tests/test_package_facts.py -x -q` → 15 passed (all determinism, structure, discovery, per-manifest-kind, and snapshot tests green).
- `uv run pytest tools/memory_regen tools/harness_config tools/harness_lint -q` → 408 passed, zero regressions.
- `uv run pytest tools/memory_regen/tests -x -q` (plan's stated `<verification>` command) → 97 passed.
- Byte-identical regeneration: sha256 `0dc0a5a0ae297851d051318373710966227edafe6f117f1c8c3733c74c4e816a` both before and after delete + regenerate.
- `grep -c "## Convention Profiles" .memory/derived/package-facts.md` → `1`.
- `grep -n "libs/python/AGENTS.md" .memory/derived/package-facts.md` → 1 hit (the `logparser-normalize` profile row).
- `git diff --stat -- .github/workflows/ci.yml` → empty; `git diff --stat -- .gitignore` → empty.
- `grep -n "examples/" tools/memory_regen/tests/test_package_facts.py tools/memory_regen/package_facts.py tools/memory_regen/tests/__snapshots__/test_package_facts.ambr` → no hits (GEN-04 clean).
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` → 18 passed.
- `uv run ruff check tools/memory_regen/package_facts.py tools/memory_regen/tests/test_package_facts.py` → all checks passed.
- `ls harness/commands/*.md | wc -l` → 18 (unchanged; this plan added no command, per SC4).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `.memory/derived/package-facts.md`'s `## Convention Profiles` section is committed and regenerable; Plan 03 (`/component` step 2 integration) can rely on `conventions_for()` resolving newly created packages and on this artifact reflecting them after regeneration.
- No blockers identified.

---
*Phase: 48-convention-profiles*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: tools/memory_regen/package_facts.py
- FOUND: .memory/derived/package-facts.md
- FOUND commit: fa9a5f6
- FOUND commit: 306d480
