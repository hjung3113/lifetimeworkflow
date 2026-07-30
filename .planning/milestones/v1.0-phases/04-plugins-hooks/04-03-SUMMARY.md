---
phase: 04-plugins-hooks
plan: 03
subsystem: infra
tags: [hooks, pretooluse, permission-matrix, polyglot-lint, constitution-plane, golden-approve]

# Dependency graph
requires:
  - phase: 04-01
    provides: tools/polyglot_lint lint_bytes (§4.3-4.6 R1-BOM / R2-CRLF byte checks)
  - phase: 04-02
    provides: tools/hooks/_stdin parse_event + emit_deny (Claude hook stdin adapter)
  - phase: 03-01
    provides: tools/harness_perms resolve_path + load_matrix (CONFIG-02 path-deny resolver, D-02)
provides:
  - HOOK-04 contract-guard PreToolUse(Write|Edit) gate (tools/hooks/contract_guard.py)
  - Runtime default-deny of the constitution plane (contracts/·docs/adr/·golden/) with GOLDEN_APPROVE_HUMAN bypass
  - On-write §4.3-4.6 byte-hygiene enforcement on the approved constitution plane (byte-pristine invariant)
affects: [04-04-format-on-write, 04-06-composition, 05-codeowners]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "decide(file_path, content, approved) -> deny dict | None — pure decision fn, main() does I/O"
    - "CONSTITUTION_GLOBS constitution-only subset (mirrors secret_scan SECRET_PATH_GLOBS) — provably disjoint gate domains"
    - "Approval = bool((os.environ.get(APPROVAL_ENV) or '').strip()) — empty/blank string never bypasses"

key-files:
  created:
    - tools/hooks/contract_guard.py
    - tools/hooks/tests/test_contract_guard.py
  modified: []

key-decisions:
  - "CONSTITUTION_GLOBS excludes *.env (secret_scan's domain, W-1) so a .env write is never mislabeled 'constitution plane'"
  - "Approved-but-dirty constitution writes are still denied via reused lint_bytes (D-04 byte-pristine); no second normalizer"
  - "BOM/CRLF on ALLOWED paths returns None — byte hygiene is format-on-write's PostToolUse job (04-04); contract-guard does not preempt it"

patterns-established:
  - "PreToolUse gate = reuse resolver (path decision) + reuse polyglot lint_bytes (byte decision) + reuse _stdin (I/O), stdlib-only, no shell"

requirements-completed: [HOOK-04]

# Metrics
duration: 12min
completed: 2026-07-08
---

# Phase 4 Plan 03: HOOK-04 contract-guard PreToolUse gate Summary

**PreToolUse gate that default-denies constitution-plane writes (contracts/·docs/adr/·golden/) unless a non-empty GOLDEN_APPROVE_HUMAN token is present, and still denies an approved write whose payload carries a BOM/CRLF via the reused POLY-01 lint_bytes.**

## Performance

- **Duration:** ~12 min
- **Tasks:** 2 (TDD: RED then GREEN)
- **Files created:** 2

## Accomplishments
- Constitution plane is now runtime-gated: an agent write to contracts/·docs/adr/·golden/ is denied at PreToolUse time, not just by advisory prose (P8/P11 becomes a runtime fact).
- Human-only bypass: a non-empty GOLDEN_APPROVE_HUMAN value authorizes the write; an empty or whitespace-only value does NOT bypass (T-04-06, Q1 RESOLVED).
- Byte-pristine invariant: even an approved constitution write is denied if its bytes fail lint_bytes (BOM/CRLF), reusing POLY-01 — no second normalizer (T-04-07, D-04).
- Composition invariants honored: uses a constitution-only glob subset (disjoint from secret_scan's *.env domain, W-1); allowed-path byte hygiene is left to format-on-write (04-04), not preempted here.

## Task Commits

Each task was committed atomically (TDD gates):

1. **Task 1: Failing contract-guard tests (RED)** - `23416ff` (test)
2. **Task 2: Implement contract_guard.py (GREEN)** - `a60a1e5` (feat)

_ruff format + check were clean on both files (no separate style commit needed)._

## Files Created/Modified
- `tools/hooks/contract_guard.py` - HOOK-04 PreToolUse gate: CONSTITUTION_GLOBS resolver deny + GOLDEN_APPROVE_HUMAN bypass + lint_bytes on-write enforcement; decide()/main(), stdlib-only, no shell.
- `tools/hooks/tests/test_contract_guard.py` - 17 tests: deny/bypass/allow, unset/non-empty/empty/blank token, approved-constitution-with-BOM/CRLF -> deny, allowed-path-with-BOM/CRLF -> no decision.

## Decisions Made
- Reused `resolve_path` over a module-level `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]` rather than the full matrix `path_deny_globs` union — the *.env subset is secret_scan's domain, keeping the two gates provably non-overlapping (W-1).
- `main()` computes `approved = bool((os.environ.get("GOLDEN_APPROVE_HUMAN") or "").strip())` so empty string and whitespace-only tokens do not bypass.
- `decide()` returns `None` on allowed paths even when the payload has BOM/CRLF, deliberately deferring that hygiene to format-on-write (04-04) to avoid preempting PostToolUse auto-fix (04-06 composition invariant).

## Deviations from Plan

None - plan executed exactly as written. RED test file added one extra guard (whitespace-only token still denies) beyond the required cases, tightening the empty-string invariant; this is within the plan's stated approval semantics, not a scope change.

## Issues Encountered
None.

## Verification
- `uv run pytest tools/hooks/tests/test_contract_guard.py -x -q` -> **17 passed**.
- `uv run pytest` (full suite) -> **287 passed, 2 skipped** (the 2 skips are pre-existing .NET-egress-blocked golden spawn tests, out of scope).
- `ruff format` / `ruff check` on both new files -> clean.
- Manual CLI demo confirmed all four acceptance rows: unapproved contracts write -> deny; `GOLDEN_APPROVE_HUMAN=1` -> silent; `GOLDEN_APPROVE_HUMAN=` (empty) -> deny; `libs/python/foo.py` -> silent.

## TDD Gate Compliance
RED gate (`test(04-03): …` `23416ff`) preceded GREEN gate (`feat(04-03): …` `a60a1e5`); RED confirmed failing via `ModuleNotFoundError` before implementation. No REFACTOR commit needed (implementation clean on first GREEN).

## Next Phase Readiness
- HOOK-04 is complete and satisfies Phase 4 success criterion 1.
- 04-04 (format-on-write PostToolUse) can rely on contract-guard NOT denying BOM/CRLF on allowed paths — the composition seam is honored.
- 04-06 composition can aggregate contract-guard + secret_scan knowing their path domains are disjoint.
- 04-04/04-05 files were left untouched (disjoint scope).

## Self-Check: PASSED

---
*Phase: 04-plugins-hooks*
*Completed: 2026-07-08*
