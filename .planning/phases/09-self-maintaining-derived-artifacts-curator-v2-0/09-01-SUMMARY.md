---
phase: 09-self-maintaining-derived-artifacts-curator-v2-0
plan: 01
subsystem: derived-artifacts / docs-sync
tags: [docs-sync, prune-then-write, derived-plane, reconcile, confinement]
requires:
  - "tools/docs_sync/generate.py::write (existing write path + _confine)"
  - "contracts/sample/greeting.schema.json, contracts/normalization/format-conventions.schema.json"
provides:
  - "docs_sync.write() prune-then-write: orphaned <name>.md deleted under _confine, README.md preserved"
  - "docs/reference tracked set reconciled to {README.md, format-conventions.md, greeting.md}"
  - "greeting.md reference page (was missing) — precondition for a green stale-derived gate (Plan 04)"
affects:
  - ".github/workflows/ci.yml stale-derived gate (Plan 04) — now regenerates clean"
tech-stack:
  added: []
  patterns:
    - "prune-then-write with per-delete path confinement (mirror of harness_emit prune_then_write)"
key-files:
  created:
    - docs/reference/greeting.md
  modified:
    - tools/docs_sync/generate.py
    - tools/docs_sync/tests/test_docs_sync_determinism.py
  deleted:
    - docs/reference/correction-rules.md
    - docs/reference/equipment-master.md
    - docs/reference/equipment-progress.md
    - docs/reference/standard-log.md
decisions:
  - "Prune test added in Task 1 RED phase (TDD) rather than Task 2; Task 2 (a) thereby satisfied"
  - "Delete-confinement reuses existing _confine(page, out_dir) before unlink (ASVS V12) — no new security primitive"
metrics:
  duration: 12min
  completed: 2026-07-13
  tasks: 2
  files: 7
---

# Phase 09 Plan 01: docs/reference Reconcile + docs_sync Prune-Then-Write Summary

Gave `tools/docs_sync.write()` a confined prune-then-write step and reconciled the pre-existing
`docs/reference/` drift (removed 4 Phase-5 orphan domain pages, generated the missing `greeting.md`)
so the committed-derived docs half regenerates byte-clean before the `stale-derived` CI gate lands.

## What Was Built

- **Prune-then-write in `docs_sync.write()`** — after writing one page per current schema, the
  generator enumerates `sorted(out_dir.glob("*.md"))` and deletes any page whose stem is not a
  current schema name. `README.md` is exempt by exact name; every delete target passes
  `_confine(page, out_dir)` before `unlink()`, so a prune can never escape `docs/reference/`
  (ASVS V12). The prune is deterministic (sorted) and has zero effect on written-page bytes, so
  delete + regenerate stays byte-identical (Pitfall P12 preserved).
- **Prune test** (`test_prune_removes_orphan_pages_preserves_readme`) — drops a schema-less
  `no-such-schema.md` + a `README.md` in a `tmp_path` out dir, calls `write()`, and asserts the
  stray is pruned while `README.md` is preserved unmodified.
- **Live-tree reconcile** — `git rm` of the 4 orphan domain pages left by the Phase-5 domain move
  (`correction-rules`, `equipment-master`, `equipment-progress`, `standard-log` — no backing
  schema) and added the generated `greeting.md`. Tracked set is now exactly
  `{README.md, format-conventions.md, greeting.md}`; a fresh `python -m tools.docs_sync` produces
  zero diff.
- **Docstring fix** — the stale "5 seed schemas → 5 pages" module/`write()` docstring now states
  the prune-then-write behavior (one page per current schema, orphans removed, README.md preserved).

## How It Works

`write()` builds a `current` set of schema names as it writes pages, then a second loop prunes:
`for page in sorted(out_dir.glob("*.md")): if page.name == "README.md" or page.stem in current: continue; _confine(page, out_dir).unlink()`.
Running the generator on the live tree performed the reconcile itself (deleted the 4 orphans on
disk, wrote `greeting.md`); the deletions + new file were then staged.

## Verification

- `uv run pytest tools/docs_sync -x` — 10 passed / 1 snapshot passed.
- `uv run ruff check tools/docs_sync/` — all checks passed.
- `git ls-files docs/reference/` == `{README.md, format-conventions.md, greeting.md}`.
- Second `uv run python -m tools.docs_sync` leaves `git status --porcelain -- docs/reference` clean
  (byte-identical regen).
- GEN-04 core→example guard (`test_core_no_example_dep.py`) still green after orphan removal.

## Deviations from Plan

### Adjustments

**1. [TDD sequencing] Prune test authored in Task 1 RED, not Task 2**
- **Found during:** Task 1 (marked `tdd="true"`).
- **Detail:** TDD requires a failing test before implementation, and the only new behavior is the
  prune. The prune test the plan assigned to Task 2 (a) was therefore written and committed in
  Task 1's RED phase (`test(09-01)` commit), then made green by the implementation. Task 2 (a)'s
  requirement is satisfied by that same test; Task 2 reduced to the live-tree reconcile.
- **Files:** `tools/docs_sync/tests/test_docs_sync_determinism.py`

**2. [Rule 1 - lint] Fixed two over-length lines in the modified test file**
- **Found during:** Task 1 GREEN (ruff).
- **Detail:** One long line was introduced by the new prune-test docstring (fixed); one was a
  pre-existing 101-char comment (line 23) in the same file — shortened opportunistically so the
  file I modified stays ruff-clean (`keep ruff green` project convention).
- **Files:** `tools/docs_sync/tests/test_docs_sync_determinism.py`

## Known Stubs

None.

## Threat Flags

None — no new network/auth/schema surface. The one delete path introduced is confined via the
pre-existing `_confine` primitive (threat T-9-01-01 mitigated as planned); prune deletes only
pages absent from the current schema set (T-9-01-02 mitigated); no package installs (T-9-01-SC).

## Self-Check: PASSED

- Created/modified files verified present: `docs/reference/greeting.md`, `tools/docs_sync/generate.py`, `09-01-SUMMARY.md`.
- Commits verified in git log: fdb1de0 (test), 922b346 (feat), 66dad78 (fix), d4c35a4 (docs).
