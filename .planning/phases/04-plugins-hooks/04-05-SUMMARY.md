---
phase: 04-plugins-hooks
plan: 05
subsystem: testing
tags: [hooks, commit-gate, contract-drift, polyglot, golden-parity, permission-matrix, pre-commit, tdd]

# Dependency graph
requires:
  - phase: 04-01
    provides: tools/polyglot_lint.lint_file (§4.3-4.6 boundary linter)
  - phase: 04-02
    provides: tools/hooks/_stdin (Claude hook stdin adapter — parse_event/read_stdin/emit_block)
  - phase: 01-06
    provides: tools/golden_runner (resolve_dotnet, run_golden_case) + tools/contract_drift.run_gate
  - phase: 03
    provides: tools/harness_perms resolver + harness/permission-matrix.json (CONFIG-02)
provides:
  - HOOK-03 composed commit-gate (contract-drift + polyglot + golden-parity) with exit 0/1
  - dotnet-gated golden-parity SKIP that never suppresses drift/polyglot (D-06)
  - success-criterion-4 permission order-resolution proof suite over the real matrix
  - committed harness/git-hooks/pre-commit shim invoking the composed gate
affects: [phase-4-verification, ci-gates, opencode-hook-wiring]

# Tech tracking
tech-stack:
  added: []  # zero new packages — composes in-repo drift/golden/polyglot + stdlib (T-04-SC)
  patterns:
    - "Composition-over-reimplementation (D-02): the gate imports run_gate/lint_file/run_golden_case and re-rolls none of them"
    - "Env-gated component SKIP that logs but never suppresses sibling gates (D-06)"
    - "git-subcommand token-walk classifier (no regex, no shell) for the --from-hook Bash matcher (T-04-14)"

key-files:
  created:
    - tools/hooks/commit_gate.py
    - tools/hooks/tests/test_commit_gate.py
    - tools/harness_perms/tests/test_order_resolution.py
    - harness/git-hooks/pre-commit
  modified: []

key-decisions:
  - "Polyglot component lints only staged *.tsv (the A-model wire boundary) — source CRLF is out of scope, keeps the live gate quiet"
  - "--from-hook returns Claude PreToolUse block (exit 2 + block JSON); the plain CLI / pre-commit path stays 0/1"
  - "pre-commit shim is committed source under harness/git-hooks/ — NOT installed into .git/hooks (env-specific)"

patterns-established:
  - "GateResult dataclass (PASS|FAIL|SKIP) aggregated: any FAIL blocks, SKIP is inert"
  - "Test doubles monkeypatch the reused asset names ON the commit_gate module to drive each branch without live .NET/contracts"

requirements-completed: [HOOK-03]

# Metrics
duration: 5min
completed: 2026-07-08
---

# Phase 4 Plan 05: HOOK-03 Commit-Gate Composition + Order-Resolution Proof Summary

**A composed, non-bypassable-by-model git commit-gate that blocks on contract-drift or a §4.3-4.6 staged-TSV violation, gracefully SKIPs golden-parity when .NET is absent, plus a proof suite that the shipped permission matrix resolves last-wins / default-deny / constitution-deny.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-07-08T12:47:50Z
- **Completed:** 2026-07-08T12:52:20Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files created:** 4

## Accomplishments
- `commit_gate.py` composes three built-once assets (D-02): `contract_drift.run_gate`, `polyglot_lint.lint_file` over staged `*.tsv`, and the `golden_runner` parity loop — re-implementing none of them (no re-hash, no byte-diff).
- Golden-parity is dotnet-GATED via the `resolve_dotnet()` explicit-path probe: absent → `SKIP` (logged), while contract-drift + polyglot ALWAYS run — an env limitation can never silently disable a real gate (D-06 / T-04-13). A dedicated test asserts the SKIP does not swallow a drift block.
- `--from-hook` engages ONLY on `git commit`, classified by a token-walk (handles `VAR=val` env prefixes, `/usr/bin/git`, and `-C`/`-c` global opts) — never a naive regex or shell interpolation (T-04-14). Emits a PreToolUse block (exit 2) on failure.
- `test_order_resolution.py`: success-criterion-4 proof over the REAL `harness/permission-matrix.json` — last-wins (specific overrides catch-all), default-deny (`ask`) on unmatched, no trailing catch-all allow (P3 — asserts no `allow` rule matches an arbitrary command), `rm -rf` deny, and constitution/secret plane (`contracts/**`, `docs/adr/**`, `golden/**`, `*.env`) deny.
- Committed `harness/git-hooks/pre-commit` shim (`uv run python -m tools.hooks.commit_gate`) with a one-line install note; deliberately not installed into `.git/hooks`.

## Task Commits

1. **Task 1: Failing commit-gate tests + order-resolution proof suite (RED)** - `f2aa4dc` (test)
2. **Task 2: commit_gate.py composition + committed pre-commit shim (GREEN)** - `ecf3cce` (feat)

**Plan metadata:** _(final docs commit)_

## Files Created/Modified
- `tools/hooks/commit_gate.py` - HOOK-03 composition; `main()` exits 0/1, `--from-hook` exits 2 on block
- `tools/hooks/tests/test_commit_gate.py` - drift/polyglot/dotnet-skip branch tests + token-walk classifier + --from-hook
- `tools/harness_perms/tests/test_order_resolution.py` - success-criterion-4 order-resolution proof over the real matrix
- `harness/git-hooks/pre-commit` - committed POSIX-sh shim → `python -m tools.hooks.commit_gate`

## Decisions Made
- **Polyglot scope = staged `*.tsv` only.** The linter is the §4.3-4.6 *wire boundary* engine; linting arbitrary staged source for CRLF would be noisy and out of the boundary's intent. Keeps the live gate green on a normal commit (source `.py`, `.md`).
- **Two exit-code regimes.** The pre-commit shim and in-session CLI use `main()` → 0 (allow) / 1 (block). The `--from-hook` Claude Bash matcher wraps that and returns exit 2 + a `{"decision":"block"}` JSON (the PreToolUse block protocol) so it works correctly if wired as a Bash hook. This keeps the primary blocking surface the git pre-commit shim (T-04-16 — Stop is not the surface).
- **Shim is source, not installed.** `harness/git-hooks/pre-commit` is version-controlled; installation into `.git/hooks` is an env-specific one-liner documented in the shim header.

## Deviations from Plan

None - plan executed exactly as written. (One in-flight fix to my own RED test's stdout-parsing assertion — the `--from-hook` block JSON is the last stdout line after the composition PASS/SKIP lines — folded into the GREEN commit; not a plan deviation.)

## Issues Encountered
- Initial `test_from_hook_blocks_commit_on_drift` parsed all of stdout as JSON, but `run_composition()` prints component PASS/SKIP lines to stdout before the block JSON. Fixed the test to parse the last non-empty stdout line. Ruff E501 line-length on a few long docstring/assert lines — reflowed; `ruff check` + `ruff format --check` both clean.

## User Setup Required
None - no external service configuration required. (Optional local install: `cp harness/git-hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`.)

## Next Phase Readiness
- Phase 4 success criterion 4 is proved: the commit-gate blocks on drift/polyglot and the order-resolution suite is green over the real matrix.
- Live behavior confirmed in this env (dotnet absent): `python -m tools.hooks.commit_gate` → drift PASS, polyglot PASS, golden-parity SKIP, exit 0.
- Full suite: 337 passed, 2 skipped (pre-existing golden e2e spawn skips — .NET egress-blocked, per 01-06). No new skips introduced.
- Golden-parity FAIL path is exercised only by unit doubles here; a live .NET runtime is needed to confirm the end-to-end golden block (tracked by the same 01-06 deferral).

## Self-Check: PASSED

- All 4 created files present on disk.
- Both task commits (`f2aa4dc` test, `ecf3cce` feat) exist in history.
- No unexpected file deletions in either commit.

---
*Phase: 04-plugins-hooks*
*Completed: 2026-07-08*
