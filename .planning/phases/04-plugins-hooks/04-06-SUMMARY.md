---
phase: 04-plugins-hooks
plan: 06
subsystem: infra
tags: [claude-hooks, opencode-plugins, settings-json, pretooluse, posttooluse, polyglot-lint, gate-wiring, runtime-enforcement]

# Dependency graph
requires:
  - phase: 04-plugins-hooks (plans 01-05)
    provides: the four unit-proven python gates (contract_guard, secret_scan, commit_gate, format_on_write) + the POLY-01 tools.polyglot_lint.lint engine
  - phase: 02-memory
    provides: harness/plugins/session-inject.ts (the authored-only/deferred opencode stub shape mirrored here)
provides:
  - "Four Phase-4 gates wired as LIVE, coexisting Claude hooks (append-only into .claude/settings.json; every GSD guard preserved)"
  - "A structural coexist test asserting all 11 GSD command substrings survive AND the four new gates register under the correct event/matcher (7 PreToolUse, 4 PostToolUse)"
  - "Four authored opencode plugin stubs (contract-guard/secret-scan tool.execute.before; format-on-write/polyglot-lint tool.execute.after) sharing the single python enforcement contract — execution deferred (D-01)"
  - "POLY-01 in-session call site via /lint (completing the on-write + in-session + CI-deferred triad of success-criterion-2)"
affects: [05-ci, 06-emitter, opencode-wiring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Append-only shared-config merge: never rewrite/reorder existing settings.json objects; assert-survival test guards the append (Pitfall 1 / T-04-17)"
    - "Authored-only/deferred opencode stub: RESUME-NOTE banner + execFileSync argv (never shell string) shelling the SAME python contract as the live Claude hook (D-01)"
    - "Presence-safe fail-loud macro: loop git ls-files '*.tsv' -> single POLY-01 engine, accumulate non-zero, no-op/exit 0 when zero files"

key-files:
  created:
    - tools/hooks/tests/test_settings_coexist.py
    - harness/plugins/contract-guard.ts
    - harness/plugins/secret-scan.ts
    - harness/plugins/format-on-write.ts
    - harness/plugins/polyglot-lint.ts
    - tools/hooks/tests/test_lint_command_wires_polyglot.py
  modified:
    - .claude/settings.json
    - harness/commands/lint.md

key-decisions:
  - "Appended gate slots to .claude/settings.json (never rewrote existing GSD objects); coexist test asserts all 11 GSD command substrings survive + the four gates register under the correct event/matcher"
  - "opencode stubs authored-only and NOT registered in harness/opencode.json (only session-inject.ts stays wired) — execution deferred per D-01; hook names A1 MEDIUM, re-verify at opencode wiring"
  - "secret_scan matcher is Read|Write|Edit (guards reads of secret material too); commit_gate matcher is Bash with --from-hook so it token-walks the git commit stdin"

patterns-established:
  - "Coexist-test-first for any shared-config edit: RED asserts new wiring absent, GREEN after append, survival assertions guard the GSD guards"
  - "One enforcement contract, N runtime envelopes: Claude hook + opencode stub both shell the identical python -m tools.hooks.* / tools.polyglot_lint.lint"

requirements-completed: [HOOK-01, HOOK-02, HOOK-03, HOOK-04, POLY-01]

# Metrics
duration: 5min
completed: 2026-07-08
---

# Phase 4 Plan 06: Wire the four gates into the live Claude runtime + author opencode stubs + POLY-01 in /lint Summary

**The four Phase-4 gates now fire as LIVE, coexisting Claude hooks (7 PreToolUse / 4 PostToolUse, every GSD guard preserved), four authored opencode stubs share the single python enforcement contract, and POLY-01 gains an in-session /lint call site.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-08T12:56:52Z
- **Completed:** 2026-07-08T13:01:40Z
- **Tasks:** 3
- **Files modified:** 8 (6 created, 2 modified)

## Accomplishments
- Appended 3 PreToolUse slots (contract_guard `Write|Edit`; secret_scan `Read|Write|Edit`; commit_gate `Bash` with `--from-hook`) + 1 PostToolUse slot (format_on_write `Write|Edit`) to `.claude/settings.json` — append-only, all 11 GSD guards preserved. These hooks went live in-session; subsequent Write/Edit/commit exercised the gates and all legitimate harness commits passed cleanly.
- `test_settings_coexist.py` proves both directions: every GSD command substring survives AND each new gate registers under the correct event/matcher (`7 4` slot counts asserted).
- Authored four opencode plugin stubs mirroring `session-inject.ts` (EXECUTION DEFERRED banner, `execFileSync` argv not shell) — deny gates on `tool.execute.before`, mutate/report on `tool.execute.after` — none wired into `opencode.json`.
- Wired POLY-01 into `/lint` via a presence-safe fail-loud macro over tracked `*.tsv` files, completing success-criterion-2's on-write + in-session + CI-deferred triad.

## Task Commits

Each task was committed atomically:

1. **Task 1: Coexist test first, then append settings.json slots** - `5b5f6a6` (feat)
2. **Task 2: Author opencode plugin stubs (deferred, not run)** - `bc8dbf4` (feat)
3. **Task 3: Wire POLY-01 into the /lint command** - `5c47223` (feat)

**Plan metadata:** _(this docs commit)_

## Files Created/Modified
- `.claude/settings.json` - Appended 3 PreToolUse + 1 PostToolUse gate slots (GSD slots untouched); now 7 PreToolUse / 4 PostToolUse.
- `tools/hooks/tests/test_settings_coexist.py` - Structural coexist proof (11 GSD substrings survive + 4 gates registered + slot counts + commit_gate `--from-hook`).
- `harness/plugins/contract-guard.ts` - Authored opencode `tool.execute.before` deny stub -> `tools.hooks.contract_guard`.
- `harness/plugins/secret-scan.ts` - Authored opencode `tool.execute.before` deny stub -> `tools.hooks.secret_scan`.
- `harness/plugins/format-on-write.ts` - Authored opencode `tool.execute.after` mutate stub -> `tools.hooks.format_on_write`.
- `harness/plugins/polyglot-lint.ts` - Authored opencode `tool.execute.after` report stub -> `tools.polyglot_lint.lint` (path argv).
- `harness/commands/lint.md` - Appended `## Polyglot boundary (§4.3-4.6) — POLY-01` presence-safe macro; frontmatter description updated.
- `tools/hooks/tests/test_lint_command_wires_polyglot.py` - Asserts /lint references `tools.polyglot_lint.lint` and still runs `ruff check` + dotnet-gated block (no regression).

## Decisions Made
- **Append-only, never rewrite:** the single critical risk was clobbering a GSD guard on the shared config; mitigated by append + survival test (T-04-17).
- **Stubs not wired:** `harness/opencode.json` still registers only `session-inject.ts`; the four new stubs are authored/deferred (D-01) pending A1 hook-name re-verification.
- **commit_gate `--from-hook`:** wired on the `Bash` matcher so it reads the untrusted Bash stdin and token-walks for `git commit` — no naive regex.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. The gates going live mid-session was the intended behavior; every legitimate harness commit (settings.json, .ts stubs, lint.md, tests) passed the now-live commit_gate cleanly (no contract drift, no staged TSV, allowed paths), and the contract_guard/secret_scan PreToolUse gates did not deny any of the non-constitution, secret-free edits.

## Known Stubs

The four `harness/plugins/*.ts` files are **intentional authored-only stubs** (D-01): they carry the EXECUTION DEFERRED resume-note banner, are not registered in `opencode.json`, and are not executed here (no opencode runtime). They document — and share — the identical `python -m tools.hooks.*` / `tools.polyglot_lint.lint` contract the live Claude hooks enforce. Resolution deferred to the opencode-wiring pass (re-verify A1 hook names). This is the same deferral posture as the pre-existing `session-inject.ts`.

## Verification Results
- `uv run pytest tools/hooks/tests/test_settings_coexist.py tools/hooks/tests/test_lint_command_wires_polyglot.py -x -q` -> **8 passed**.
- `uv run pytest` (full suite) -> **345 passed, 2 skipped** (up from 337; the 2 skips are the pre-existing .NET-absent golden spawns).
- `python -c "import json;d=json.load(open('.claude/settings.json'));print(len(d['hooks']['PreToolUse']),len(d['hooks']['PostToolUse']))"` -> **`7 4`**.

## Next Phase Readiness
- Runtime-enforcement layer complete for HOOK-01/02/03/04 + POLY-01 (Claude side live; opencode side authored/deferred).
- Phase 5 (CI): the third POLY-01 call site (CI) and a settings.json/opencode.json emitter parity check remain. The gates are ready to be invoked from a CI matrix job.

## Self-Check: PASSED

All 6 created files + SUMMARY.md exist on disk; all three task commits (`5b5f6a6`, `bc8dbf4`, `5c47223`) present in git history.

---
*Phase: 04-plugins-hooks*
*Completed: 2026-07-08*
