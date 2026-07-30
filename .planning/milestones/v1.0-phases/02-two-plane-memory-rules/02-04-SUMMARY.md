---
phase: 02-two-plane-memory-rules
plan: 04
subsystem: memory
tags: [tree-sitter, networkx, pagerank, repo-map, derived-plane, determinism, syrupy]

# Dependency graph
requires:
  - phase: 02-01
    provides: "memory_regen uv-workspace member + pinned tree-sitter 0.25 / grammar wheels / networkx 3.6.1 toolchain + conftest tmp_source_tree fixture"
  - phase: 02-03
    provides: "sibling generator pattern (contracts_index.py: index/render/write/main + DERIVED marker + committed syrupy snapshot)"
provides:
  - "tools/memory_regen/queries.py — tree-sitter 0.25 def/ref parse layer (Query + QueryCursor), LANGUAGES table for python/c_sharp/bash"
  - "tools/memory_regen/repo_map.py — parse → nx.DiGraph → PageRank → deterministic token-bounded .memory/derived/repo-map.md"
  - "repo-map entrypoint `python -m tools.memory_regen.repo_map` that replaces the empty repo-map section the injector reads"
affects: [inject, session-start-injection, phase-3-config, phase-4-hooks]

# Tech tracking
tech-stack:
  added: []  # all deps pinned in 02-01; no uv.lock change (T-02-SC honored)
  patterns:
    - "tree-sitter 0.25 QueryCursor API (NOT removed Language.query().captures())"
    - "networkx pure-Python PageRank backend (_pagerank_python) — numpy-free ranking"
    - "deterministic derived artifact: sorted node/edge insertion + (-score,path) tie-break + rank-only (no floats) + no timestamp"

key-files:
  created:
    - tools/memory_regen/queries.py
    - tools/memory_regen/repo_map.py
    - tools/memory_regen/tests/test_parse.py
    - tools/memory_regen/tests/test_repo_map_determinism.py
    - tools/memory_regen/tests/__snapshots__/test_repo_map_determinism.ambr
  modified: []

key-decisions:
  - "Used networkx's pure-Python PageRank backend (_pagerank_python) instead of the public nx.pagerank dispatcher, which routes to _pagerank_scipy and imports numpy/scipy — neither pinned in the 02-01 toolchain. Same algorithm, dependency-free, deterministic; keeps uv.lock untouched in Wave 2 (T-02-SC)."
  - "repo-map file paths keyed relative to base_dir (repo root for real runs, fixture root for tests) so the random tmp_path never leaks into output — this is what makes the committed syrupy snapshot stable."
  - "PageRank floats are never printed (rank-only, numbered list); no timestamp anywhere — the two determinism traps (Pitfall 1) eliminated by construction."

patterns-established:
  - "Parse layer / ranking layer separation: queries.parse_symbols() (0.25 API) feeds repo_map.build_graph() → ranked_files() → render()."
  - "Determinism proven WITHOUT git diff (derived/ is gitignored, Pitfall 2): generate-twice sha256 + committed .ambr snapshot."
  - "Path-traversal defense mirrored from contract_hash.hash: resolve + subtree-confine each source root, skip symlinks escaping the tree (T-02-10)."

requirements-completed: [MEM-03]

# Metrics
duration: 15min
completed: 2026-07-08
---

# Phase 2 Plan 04: repo-map Generator Summary

**tree-sitter 0.25 (Query + QueryCursor) parses the monorepo's .py/.cs/.sh into def/ref symbols, a networkx PageRank ranks files by reference topology, and the top-N render with elided signatures into a deterministic, token-bounded, DERIVED-marked `.memory/derived/repo-map.md` that regenerates delete+rerun byte-identically.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-07-08
- **Tasks:** 2 (both TDD: RED → GREEN)
- **Files created:** 5

## Accomplishments
- **Parse layer (Task 1):** `queries.py` exposes a `LANGUAGES` table (python/c_sharp/bash → grammar module + extensions + tags query) and `parse_symbols()` built on the validated tree-sitter **0.25** API — `ts.Query(lang, q)` + `ts.QueryCursor(query).captures(root)` — never the removed `Language.query().captures()` chain (Pitfall 3, guarded by a test that inspects executable code with docstrings stripped). Non-empty def captures confirmed for all three languages.
- **Ranking + render (Task 2):** `repo_map.py` walks the confined code subtrees (`libs/python`, `libs/dotnet`, `tools`, `components` — code only, D-06), builds an `nx.DiGraph` (edge A→B when A references a symbol defined in B, weight = ref count), ranks with networkx PageRank, and renders the top-N with elided def lists inside a ~4000-char budget. Real-repo output: 36 files / 68 edges, **3713 chars**, correctly surfacing `golden_runner/runner.py` and `repo_map.py` at the top by reference topology.
- **Determinism proven three ways:** generate-twice byte-identical (pytest, sha256), committed syrupy `.ambr` snapshot, and a real-repo delete+regenerate sha256 match (`ae895ab…` == `ae895ab…`). Derived output confirmed gitignored (`git check-ignore` passes).

## Task Commits

1. **Task 1 (RED): failing parse test** — `83b6c7d` (test)
2. **Task 1 (GREEN): tree-sitter 0.25 parse layer** — `b3890ee` (feat)
3. **Task 2 (RED): failing determinism + snapshot test** — `da98846` (test)
4. **Task 2 (GREEN): PageRank repo-map generator** — `44a61a7` (feat)

**Plan metadata:** committed separately with this SUMMARY + STATE + ROADMAP.

## Files Created
- `tools/memory_regen/queries.py` — tree-sitter 0.25 def/ref parse layer; `LANGUAGES` table + `parse_symbols()` + `lang_for_path()`.
- `tools/memory_regen/repo_map.py` — `build_graph()` / `ranked_files()` / `render()` / `write()` / `main()`; parse → PageRank → deterministic token-bounded `.memory/derived/repo-map.md`.
- `tools/memory_regen/tests/test_parse.py` — non-empty def/ref captures per language + Pitfall-3 removed-API guard + no-DeprecationWarning.
- `tools/memory_regen/tests/test_repo_map_determinism.py` — render-twice + write/delete/regenerate byte-identical, stable ordering, char budget, DERIVED/no-timestamp/no-float, syrupy snapshot.
- `tools/memory_regen/tests/__snapshots__/test_repo_map_determinism.ambr` — committed determinism reference.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] networkx PageRank required numpy (absent from the pinned toolchain)**
- **Found during:** Task 2 (first GREEN test run).
- **Issue:** The public `nx.pagerank` dispatcher on networkx 3.6.1 routes to `_pagerank_scipy`, which imports numpy — `ModuleNotFoundError: No module named 'numpy'`. numpy/scipy are NOT in the 02-01-pinned toolchain (individual grammar wheels + networkx only), and 02-01 explicitly locked "Wave-2 never touches uv.lock" (T-02-SC).
- **Fix:** Called networkx's own pure-Python PageRank backend `_pagerank_python` (from `networkx.algorithms.link_analysis.pagerank_alg`) — the identical PageRank algorithm, dependency-free, verified deterministic (uniform start over sorted node insertion; handles isolated nodes). No new dependency, `uv.lock` untouched. Documented inline in `ranked_files()`.
- **Files modified:** `tools/memory_regen/repo_map.py`
- **Commit:** `44a61a7`

**2. [Rule 1 - Bug] Pitfall-3 guard test over-matched the module docstring**
- **Found during:** Task 1 GREEN.
- **Issue:** The test asserted `".query(" not in inspect.getsource(queries)`, but the module docstring narrates the removed `Language.query(s)` API for documentation — a false positive.
- **Fix:** Scoped the guard to `queries.parse_symbols`'s executable source with comment lines and docstrings stripped (via `ast`), so it checks real code, not prose.
- **Files modified:** `tools/memory_regen/tests/test_parse.py`
- **Commit:** `b3890ee`

## Verification
- `uv run pytest tools/memory_regen/tests/test_parse.py tools/memory_regen/tests/test_repo_map_determinism.py -x` → **15 passed** (incl. snapshot).
- `uv run pytest` (full workspace) → **82 passed, 2 skipped** (skips = pre-existing .NET egress deferral, 01-06).
- `python -m tools.memory_regen.repo_map` → writes `.memory/derived/repo-map.md`, DERIVED header, 3713 ≤ 4000 chars.
- Generate → sha256 → delete → regenerate → sha256 identical; output gitignored.

## Known Stubs
None — the repo-map is fully wired to real source and produces a non-empty ranked map.

## Self-Check: PASSED

All 5 created files exist on disk; all 4 task commits (83b6c7d, b3890ee, da98846, 44a61a7) present in history.
