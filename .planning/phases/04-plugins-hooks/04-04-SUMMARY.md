---
phase: 04-plugins-hooks
plan: 04
subsystem: infra
tags: [hooks, posttooluse, format-on-write, ruff, dotnet-format, normalize, encoding, tdd]

# Dependency graph
requires:
  - phase: 04-02
    provides: tools/hooks/_stdin.py parse_event/read_stdin adapter
  - phase: 01 (normalize core)
    provides: libs/python/normalize/core.py §4.3-4.6 byte-hygiene rule
provides:
  - HOOK-01 PostToolUse format-on-write fixer (BOM strip + CRLF/CR->LF + ruff/dotnet-format)
  - normalize.core.strip_bom_normalize_newlines shared R1+R2 helper (single source, D-02)
affects: [04-06 hook aggregation/registration, opencode.json PostToolUse wiring]

# Tech tracking
tech-stack:
  added: []  # zero new packages — stdlib subprocess + already-pinned ruff (T-04-SC)
  patterns:
    - "Byte-hygiene reuse: format-on-write imports normalize.core rather than re-deriving BOM/LF"
    - "dotnet-gated subprocess: explicit $DOTNET_ROOT/dotnet probe + skip-gracefully (P5, D-05)"
    - "PostToolUse mutate-not-block: FS write (not Claude Write) + idempotency => no re-entry"

key-files:
  created:
    - tools/hooks/format_on_write.py
    - tools/hooks/tests/test_format_on_write.py
  modified:
    - libs/python/normalize/core.py

key-decisions:
  - "Extracted strip_bom_normalize_newlines into normalize.core and had normalize_tsv reuse it, so the §4.3-4.6 R1+R2 byte rule has exactly one definition (D-02, no divergent normalizer)"
  - "format_file writes fixed bytes via the file system and spawns ruff/dotnet as argv subprocesses (shell=False) — never a Claude Write — so the PostToolUse hook cannot re-enter (Open Q3, T-04-10/T-04-12)"
  - "dotnet-format probes an explicit $DOTNET_ROOT/dotnet -> ~/.dotnet/dotnet path and logs a SKIP when absent; the gate still exits 0 (Pitfall 3 / D-05, T-04-11)"

patterns-established:
  - "Reuse-over-reimplement for canonicalization: any new consumer of BOM/LF hygiene imports normalize.core"
  - "Env-limitation is a logged SKIP, never a gate failure"

requirements-completed: [HOOK-01]

# Metrics
duration: 3min
completed: 2026-07-08
---

# Phase 4 Plan 04: HOOK-01 format-on-write PostToolUse gate Summary

**PostToolUse fixer that strips BOM + folds CRLF/CR->LF on every edit (reusing normalize.core §4.3-4.6), runs ruff format for .py via an argv subprocess, and skips dotnet-format gracefully when .NET is absent — idempotent and non-re-entrant.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-07-08T12:48:15Z
- **Completed:** 2026-07-08T12:51:07Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments
- `fix_bytes` / `format_file` canonicalize any Write/Edit target to no-BOM / LF, reusing the single §4.3-4.6 byte rule from `normalize.core` (no divergent normalizer, D-02).
- Idempotency proven by unit test and manual demo: a second pass leaves the file byte-identical (Open Q3 re-entry defused — mutation is an FS write / subprocess, never a Claude Write).
- `.py` targets invoke `ruff format` as a `subprocess.run([argv], shell=False)` child (asserted via a monkeypatched spy); `.cs` targets are dotnet-gated and skip gracefully with a logged `SKIP` when dotnet is absent, always exiting 0 (Pitfall 3 / D-05).

## Task Commits

Each task was committed atomically (TDD RED -> GREEN):

1. **Task 1: Failing format-on-write tests (RED)** - `e365388` (test)
2. **Task 2: Implement format_on_write.py (GREEN)** - `00d2f89` (feat)

_No REFACTOR commit needed — implementation was clean on first GREEN (ruff check + format --check pass)._

## Files Created/Modified
- `tools/hooks/format_on_write.py` - HOOK-01 PostToolUse fixer: `fix_bytes` (BOM/LF), `resolve_dotnet` (explicit-path probe), `format_file` (byte-fix + ruff/dotnet-format gated), `main` (exit 0 always).
- `tools/hooks/tests/test_format_on_write.py` - 15 tests: byte-fix, idempotency, normalize.core reuse, ruff subprocess spy, .cs gated-skip (no raise, no spawn), main() exit-0 / SKIP-on-stderr / malformed-stdin.
- `libs/python/normalize/core.py` - Extracted `strip_bom_normalize_newlines` (R1+R2) as the shared single source; `normalize_tsv` now delegates to it (behavior unchanged — corpus parity stays green).

## Decisions Made
- Reused `normalize.core` for the byte rule by extracting a granular `strip_bom_normalize_newlines` helper (both the TSV comparator and this hook call it) instead of importing internals or copying two lines — this is the D-02 "no divergent normalizer" invariant made structural.
- Chose `dotnet format --include <path>` as the (gated, never-executed-here) .NET formatter argv; it is only spawned when the explicit dotnet path exists, which it does not in this env.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Enabling reuse] Extracted shared `strip_bom_normalize_newlines` into normalize.core**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** The plan's locked constraint requires reusing the §4.3-4.6 rule from `libs/python/normalize/core.py` (D-02), but `core.py` exposed the BOM/LF rule only inlined inside `normalize_tsv` (which also sorts rows — destructive for source files). There was no granular reuse point.
- **Fix:** Extracted the R1+R2 step into `strip_bom_normalize_newlines(raw) -> str` and refactored `normalize_tsv` to call it. `format_on_write.fix_bytes` imports the same function, so the rule has exactly one definition. Behavior of `normalize_tsv` is identical.
- **Files modified:** libs/python/normalize/core.py
- **Verification:** Full suite green (337 passed, 2 pre-existing dotnet-absent skips) — `test_corpus_parity.py` cross-language parity unaffected.
- **Committed in:** `00d2f89` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 enabling-reuse refactor)
**Impact on plan:** The refactor is the cleanest way to satisfy the plan's own D-02 reuse constraint; no behavior change, no scope creep. `core.py` is a Phase-1 artifact disjoint from concurrent 04-03/04-05 hook files.

## Issues Encountered
- `xxd` is not installed in the env; used `od -An -tx1` for the manual byte-verification demo instead. No impact.

## TDD Gate Compliance
- RED gate: `e365388` (`test(...)`) — suite failed with ImportError (module absent) before implementation.
- GREEN gate: `00d2f89` (`feat(...)`) — all 15 tests pass.
- Sequence valid (test commit precedes feat commit).

## Verification Results
- `uv run pytest tools/hooks/tests/test_format_on_write.py -x -q` -> **15 passed**.
- `uv run pytest` (full suite) -> **337 passed, 2 skipped** (both skips are the pre-existing dotnet-absent golden-runner end-to-end tests, unrelated to this plan).
- Manual demo: BOM+CRLF `/tmp/f.txt` -> bytes `61 0a 62 0a` (`a\nb\n`, no BOM/CR); second run byte-identical (idempotent YES); `.cs` with dotnet absent -> `SKIP: dotnet absent (...)` on stderr, exit 0, file byte-fixed.
- `ruff check` + `ruff format --check` clean on all three files.

## Next Phase Readiness
- HOOK-01 fixer is ready for 04-06 to register as the PostToolUse(Write|Edit) hook in the opencode/Claude hook config.
- Concurrent plans 04-03 (contract-guard) and 04-05 left untouched (disjoint scope).

## Self-Check: PASSED

- FOUND: tools/hooks/format_on_write.py
- FOUND: tools/hooks/tests/test_format_on_write.py
- FOUND: .planning/phases/04-plugins-hooks/04-04-SUMMARY.md
- FOUND commit: e365388 (test RED)
- FOUND commit: 00d2f89 (feat GREEN)

---
*Phase: 04-plugins-hooks*
*Completed: 2026-07-08*
