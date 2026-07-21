---
phase: 16-local-memory-web-ui-v2-1-e
plan: 02
subsystem: memory-derived-generators
tags: [pointer-index, derived-plane, determinism, syrupy, reference-scanner, MEM2-07, SC2]

# Dependency graph
requires:
  - phase: 16-local-memory-web-ui-v2-1-e
    provides: 16-01 RED tests pinning build_index/render_md/write/DERIVED_HEADER + tmp_pointer_scan_tree fixture
  - phase: 02-memory-planes
    provides: tools/memory_regen DERIVED-generator template (repo_map.py) — cloned shape
  - phase: 14-write-path-anti-churn
    provides: tools.harness_lint.agreements.iter_agreement_files (read-only agreement enumeration)
provides:
  - tools/memory_regen/pointer_index.py — DERIVED reference-scanner generator (SC2)
  - .memory/derived/pointer-index.{json,md} — the "what points to each memory item" index (gitignored)
  - Committed syrupy snapshot pinning render_md determinism over the tmp fixture
affects: [16-03-routes (Referrers panel reads pointer-index.json), 16-05-referential-integrity (orphan check)]

# Tech tracking
tech-stack:
  added: []  # stdlib only (json/re/sys/pathlib); no lock change (T-16-SC)
  patterns:
    - "DERIVED-generator quartet cloned from repo_map.py: module-level paths + DERIVED_HEADER, build_index → render_md → write → main"
    - "Path-hit preferred over word-boundaried slug-hit per item/line (re.search with (?<![\\w-]) ... (?![\\w-]) boundaries)"
    - "Determinism proven by write→hash→delete→regenerate byte-identical + committed .ambr snapshot — NEVER git diff (target gitignored, Pitfall 2)"

key-files:
  created:
    - tools/memory_regen/pointer_index.py
    - tools/memory_regen/tests/__snapshots__/test_pointer_index.ambr
  modified: []

key-decisions:
  - "Cloned repo_map.py's symlink-confined walk idiom as a local _iter_scan_files (fixture-parity fallback per D-16 discretion) — handles both single-file and recursive-dir scan roots with an allow-list (.md/.ts/.py/.json/.toml; suffixless=.md) and excludes .memory/derived/"
  - "Enumerated memory items via read-only iter_agreement_files (active + retired) so items with zero referrers still appear (empty list) — the orphan check needs the full item set"
  - "Path-hit wins over slug-hit on the same item/line (AGENTS.md line carrying .memory/agreements/plan.md records kind:path only, not a duplicate slug)"

requirements-completed: [MEM2-07]

# Metrics
duration: 10min
completed: 2026-07-18
---

# Phase 16 Plan 02: Pointer-Index DERIVED Generator Summary

**Built the load-bearing new engine of Phase 16 — a deterministic DERIVED reference-scanner (`tools/memory_regen/pointer_index.py`) that enumerates memory items (state files + active/retired agreements) and scans a fixed set of roots to answer "what points to this memory item" into gitignored `.memory/derived/pointer-index.{json,md}` (SC2); the 6 RED tests from 16-01 are now GREEN and the syrupy determinism snapshot is committed.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-18
- **Tasks:** 2
- **Files:** 2 (2 created, 0 modified)

## Accomplishments
- `build_index()` enumerates the two `.memory/state` files + every agreement (active AND retired, via read-only `iter_agreement_files`), each present even with zero referrers (empty list), and records referrers as sorted `{file, line, kind}` with `kind in {path, slug}`.
- Referrer matching: a scanned line hitting the item's `.memory/...` POSIX path → `kind:"path"`; for agreements only, the slug as a word-boundaried token (`(?<![\w-])<slug>(?![\w-])`) → `kind:"slug"`. Path-hit is preferred over slug-hit per item/line, and slug `plan` correctly does NOT match `planner`.
- `render_md()`/`write()`/`main()` complete the generator quartet: `.md` first line carries the DERIVED header naming `pointer_index.py`; `.json` is `json.dumps(index, indent=2, sort_keys=True) + "\n"`. No timestamp, no raw float anywhere.
- Symlink-confined, `.memory/derived/`-excluded walk (T-16-01 / T-16-11); writes ONLY under `.memory/derived/` — never opens agreements for write (tier contract T-16-10).
- Committed `.ambr` snapshot over the tmp fixture as the byte-identical determinism reference (no tmp/absolute-path leaks).

## Task Commits

1. **Task 1: `build_index()` scan over fixed roots** — `9e24b66` (feat)
2. **Task 2: `render_md`/`write`/`main` + committed syrupy snapshot** — `ae9e697` (test)

## Files Created
- `tools/memory_regen/pointer_index.py` — DERIVED reference-scanner generator (stdlib-only; ~215 lines).
- `tools/memory_regen/tests/__snapshots__/test_pointer_index.ambr` — committed determinism snapshot.

## Decisions Made
- **Local `_iter_scan_files` over importing `repo_map._iter_source_files`.** The pointer scanner needs a different suffix policy (text allow-list + suffixless-as-`.md`) and must handle single-file scan roots (e.g. `AGENTS.md`) and a `.memory/derived/` exclusion the repo-map walk does not — the plan sanctions a suffix-gated local copy as the fixture-parity fallback. Symlink-confinement idiom is preserved verbatim.
- **Path-hit preferred over slug-hit per item/line.** A line carrying `.memory/agreements/plan.md` (which also contains the bare token `plan`) records exactly one `kind:"path"` referrer, not a duplicate `slug` — matches the plan's "prefer full-path hit" rule and keeps referrer lists minimal.
- **Full item set even at zero referrers.** Items are seeded with empty lists before scanning so the downstream orphan check (16-05) sees every memory item, not just referenced ones.

## Deviations from Plan

None — plan executed exactly as written. The `render_md`/`write`/`main` quartet (Task 2 code) was authored alongside `build_index` in a single module file, but committed in two atomic steps: Task 1 (build_index, verified by its two scan tests) then Task 2 (the committed `.ambr` snapshot + full-suite green). No `--snapshot-update` was re-run to mask a failure — the snapshot was generated once and matched the expected fixture output on first run.

## Verification
- `uv run pytest tools/memory_regen/tests/test_pointer_index.py -q` → **6 passed** (determinism, header/no-timestamp, no-self-reference/word-boundary, snapshot, referrer-shape, render-twice).
- `uv run python -m tools.memory_regen.pointer_index` writes both `.memory/derived/pointer-index.json` and `.md`; `.md` first line = the DERIVED header naming `pointer_index.py`.
- Determinism: write → sha256 → delete → regenerate → **identical hash** (`1f03d8cc…`), NOT git diff.
- `grep -E '[0-9]{4}-[0-9]{2}-[0-9]{2}' .memory/derived/pointer-index.*` → nothing (no timestamp).
- `git check-ignore` confirms both derived artifacts are gitignored; the `.ambr` snapshot carries no `/tmp`/`tmp_path` fragments.
- No regression: full `tools/memory_regen/tests` → **75 passed**. The `tools/memory_ui` route/orphan tests remain RED (9 failed) — expected, owned by waves 16-03/16-05.

## Next Phase Readiness
- 16-03 can now wire the UI Referrers panel to read `.memory/derived/pointer-index.json`.
- 16-05 can read the same index for the referential-integrity orphan check.
- No blockers introduced.

## Self-Check: PASSED

Both created files exist on disk; both task commits (`9e24b66`, `ae9e697`) are present in git history.

---
*Phase: 16-local-memory-web-ui-v2-1-e*
*Completed: 2026-07-18*
