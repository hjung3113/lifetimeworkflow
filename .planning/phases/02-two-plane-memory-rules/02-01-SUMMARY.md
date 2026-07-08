---
phase: 02-two-plane-memory-rules
plan: 01
subsystem: infra
tags: [memory, two-plane, gitignore, uv-workspace, tree-sitter, networkx, pytest]

# Dependency graph
requires:
  - phase: 01-constitution-golden-core
    provides: "uv workspace (members=libs/python + tools/*), tools/contract_hash + tools/contract_drift (reused by 02-03 contracts-index), tools/bootstrap SessionStart wiring, contracts/ constitution plane"
provides:
  - "Two-plane .memory/ skeleton: state/ committed (survives ephemeral container), derived/ gitignored (regenerated)"
  - ".memory/README.md declaring the three planes + DERIVED marker + constitution-immutability declaration (MEM-01)"
  - "tools/memory_regen uv-workspace member (virtual, package=false) with EXACT-pinned tree-sitter 0.25.x + networkx 3.6.1 resolved into uv.lock"
  - "Wave-0 test harness: conftest.py (repo-root sys.path + tmp_source_tree/tmp_contracts_tree fixtures) + test_layout.py (structural, git check-ignore boundary, import gate)"
  - "Bootstrap durability: uv sync --all-packages so member deps persist across every SessionStart"
affects: [02-02-injector, 02-03-contracts-index, 02-04-repo-map, 02-05-agents-md]

# Tech tracking
tech-stack:
  added: [tree-sitter==0.25.2, tree-sitter-python==0.25.0, tree-sitter-c-sharp==0.23.5, tree-sitter-bash==0.25.1, networkx==3.6.1]
  patterns: ["two-plane memory (constitution/derived/state)", "virtual uv-workspace member with EXACT pins", "git check-ignore as the gitignore-boundary test (never git-diff on a gitignored path)", "uv sync --all-packages for polyglot member-dep durability"]

key-files:
  created: [.memory/README.md, .memory/state/activeContext.md, .memory/state/progress.md, tools/memory_regen/pyproject.toml, tools/memory_regen/__init__.py, tools/memory_regen/tests/conftest.py, tools/memory_regen/tests/test_layout.py]
  modified: [.gitignore, tools/bootstrap/install.sh, tools/bootstrap/verify.sh, tools/bootstrap/README.md, uv.lock]

key-decisions:
  - "Individual grammar wheels (tree-sitter-python/-c-sharp/-bash) pinned exactly — NOT tree-sitter-language-pack (runtime binary download breaks determinism/offline)"
  - "Bootstrap install.sh + verify.sh switched to `uv sync --all-packages` — memory_regen is the first member with deps absent from the virtual root, so a bare `uv sync` prunes the toolchain every SessionStart"
  - "Toolchain declared + resolved ONCE here (Wave 1) so Wave-2 plans never contend on uv.lock"

patterns-established:
  - "Two-plane memory layout: .memory/state/ committed, .memory/derived/ gitignored + DERIVED marker"
  - "Gitignore-boundary tests probe with `git check-ignore` (rc0=ignored / rc1=tracked), never `git diff` on a gitignored path (Pitfall 2)"
  - "Virtual uv member conftest mirrors golden_runner: repo-root via parents[3] onto sys.path"

requirements-completed: [MEM-01, MEM-02]

# Metrics
duration: ~20min
completed: 2026-07-08
---

# Phase 2 Plan 01: Two-Plane `.memory/` Layout + `memory_regen` Member Summary

**Two-plane `.memory/` skeleton (state committed / derived gitignored + DERIVED marker + constitution-immutability declaration) and the `tools/memory_regen` uv member with EXACT-pinned tree-sitter 0.25.x + networkx 3.6.1 resolved once into uv.lock.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-08
- **Tasks:** 2 (plus 1 Rule-3 blocking fix)
- **Files modified:** 12 (7 created, 5 modified)

## Accomplishments
- Laid the two-plane `.memory/` tree: `state/` (activeContext + progress, committed, under provisional banners, no secrets/PII) and `derived/` (gitignored, regenerated). `.memory/README.md` names all four constitution members (`contracts/`, `docs/adr/`, `glossary`, `golden/`), carries the `DERIVED` marker, and declares the constitution plane human-owned/immutable-to-agents (MEM-01) with an explicit note that runtime enforcement is Phase-4 contract-guard (NOT built here).
- Refined the gitignore boundary (D-03): appended `.memory/derived/` while keeping `.memory/state/**` tracked. Proven via `git check-ignore` (derived rc0 match, state rc1 tracked).
- Added the `tools/memory_regen` virtual uv-workspace member with EXACT-pinned tree-sitter 0.25.2 + grammar wheels (python 0.25.0 / c-sharp 0.23.5 / bash 0.25.1) + networkx 3.6.1 (T-02-SC), resolved once into `uv.lock` so Wave-2 plans never touch the lock.
- Built the Wave-0 test harness: `conftest.py` (repo-root sys.path via parents[3] mirroring golden_runner, plus `tmp_source_tree` and `tmp_contracts_tree` fixtures for later parse/index tests) and `test_layout.py` (10 structural assertions).

## Task Commits

1. **Task 1: Two-plane layout + gitignore boundary + constitution marker** — `fcb506b` (feat)
2. **Task 2: memory_regen member + Wave-0 test harness** — `e9c9a35` (feat)
3. **Rule-3 fix: bootstrap `uv sync --all-packages` durability** — `9d8c3e8` (fix)

**Plan metadata:** committed separately (docs: complete plan)

## Files Created/Modified
- `.memory/README.md` — three-plane declaration + DERIVED marker + constitution-immutability note
- `.memory/state/activeContext.md`, `.memory/state/progress.md` — committed provisional state stubs (no secrets/PII)
- `.gitignore` — `.memory/derived/` ignore rule (state stays tracked)
- `tools/memory_regen/pyproject.toml` — virtual member, EXACT tree-sitter/networkx pins
- `tools/memory_regen/__init__.py` — member docstring
- `tools/memory_regen/tests/{__init__,conftest,test_layout}.py` — Wave-0 harness (10 tests)
- `tools/bootstrap/{install.sh,verify.sh,README.md}` — `uv sync --all-packages` durability fix
- `uv.lock` — five pins resolved

## Decisions Made
- Individual grammar wheels pinned exactly, not `tree-sitter-language-pack` (runtime download breaks determinism/offline — RESEARCH §Alternatives).
- Toolchain resolved once in Wave 1 (this plan) to keep the lock stable for downstream plans.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Bootstrap `uv sync` pruned the new member deps every SessionStart**
- **Found during:** Task 2 (verifying the toolchain is durably installed)
- **Issue:** `memory_regen` is the first workspace member whose deps are absent from the virtual root. A bare `uv sync` (run by `tools/bootstrap/install.sh` on every SessionStart, and asserted by `verify.sh`) syncs only the root package and **uninstalls** tree-sitter/networkx — silently removing the derived-plane toolchain the whole phase depends on. Confirmed empirically: plain `uv sync` reported `Uninstalled 5 packages` and `import tree_sitter` then failed.
- **Fix:** Switched `install.sh` to `uv sync --all-packages` and `verify.sh` to `uv sync --frozen --all-packages` (installs every member's pinned deps, not just the root's). Updated `tools/bootstrap/README.md` to match.
- **Files modified:** tools/bootstrap/install.sh, tools/bootstrap/verify.sh, tools/bootstrap/README.md
- **Verification:** `uv sync --all-packages` installs the 5 packages; `uv run pytest` full suite green (44 passed, 2 pre-existing .NET-deferred skips); imports exit 0.
- **Committed in:** `9d8c3e8`

---

**Total deviations:** 1 auto-fixed (1 Rule-3 blocking)
**Impact on plan:** The fix is required for the plan's own success criterion ("pinned deps installed") to hold durably in the ephemeral container. No scope creep — a two-line command change plus doc sync, confined to the bootstrap seam this task first stressed.

## Issues Encountered
- `verify.sh` fails fast on the pre-existing BOOT-01 blocker (.NET 10 SDK egress-denied) before reaching its uv line, so it could not be run end-to-end here; the install-side `uv sync --all-packages` path was exercised directly instead and is green. This is an existing, documented blocker (STATE.md), not introduced by this plan.

## Threat Flags
None — no new network endpoints, auth paths, or trust-boundary schema changes. The two threat-register items (T-02-SC supply-chain pins, T-02-01 state secrets) were mitigated in-plan (exact pins; no-secret-value grep gate in test_layout.py).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Stable two-plane layout + resolved toolchain in place. 02-02 (injector), 02-03 (contracts-index, reuses contract_hash/_drift), 02-04 (repo-map, tree-sitter + PageRank), and 02-05 (AGENTS.md) all land against this base without touching `uv.lock`.
- Carry-forward blocker (unchanged): .NET 10 SDK egress-denied (BOOT-01) — irrelevant to this all-Python phase but keeps `verify.sh` from running end-to-end.

## Self-Check: PASSED

All 9 claimed files exist on disk; all 3 task/fix commits (`fcb506b`, `e9c9a35`, `9d8c3e8`) present in git history.

---
*Phase: 02-two-plane-memory-rules*
*Completed: 2026-07-08*
