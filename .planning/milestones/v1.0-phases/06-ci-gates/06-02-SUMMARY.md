---
phase: 06-ci-gates
plan: 02
subsystem: infra
tags: [cli, argparse, contract-drift, contract-hash, jcs, sha-256, gen-04]

# Dependency graph
requires:
  - phase: 05-example-relocation
    provides: example manifest at examples/log-parser/contracts/.hashes/manifest.json (matches post-Phase-5 tree)
provides:
  - "drift CLI --contracts-dir/--baseline flags routing to the parameterized run_gate"
  - "hash CLI --contracts-dir/--manifest flags + write_manifest(contracts_dir) threading (Warning-1 fix)"
  - "tree-aware drift rebaseline hint (root vs non-root)"
  - "instance-plane test proving the core CLIs gate the real example manifest by verbatim reuse"
affects: [06-03-ci-workflow, contract-drift, ci-gates]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CLI main(argv) -> exit-code with argparse threading to already-parameterized gate functions (D-01: no re-implementation)"
    - "GEN-04 split: core (tools/) tests use a synthetic tree; instance-referencing proof lives in examples/*/tests (example->core direction)"

key-files:
  created:
    - tools/contract_drift/tests/test_cli_flags.py
    - examples/log-parser/tests/test_contract_drift_cli_flags.py
  modified:
    - tools/contract_drift/drift.py
    - tools/contract_hash/hash.py

key-decisions:
  - "Split the example-referencing test into the instance plane to honor the GEN-04 core-no-example-dep guard (CLAUDE.md hard constraint over plan's single-file artifact)"
  - "Made the hash wrote-summary path robust when --manifest targets outside the repo (Rule 1)"

patterns-established:
  - "argparse wrapper threads flags into existing parameterized functions; defaults keep bare invocation byte-unchanged"
  - "core-plane tests must not name any instance; example-referencing proofs live in the instance test plane"

requirements-completed: [CI-01]

# Metrics
duration: 8min
completed: 2026-07-09
---

# Phase 6 Plan 02: Contract-Drift/Hash CLI Flags Summary

**Added `--contracts-dir`/`--baseline` to the drift CLI and symmetric `--contracts-dir`/`--manifest` to the hash CLI, threading `contracts_dir` through `write_manifest` so CI can gate/rebaseline the example manifest (not only the root) by verbatim tool reuse.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-09T13:11:53Z
- **Completed:** 2026-07-09T13:20:01Z
- **Tasks:** 3 (TDD)
- **Files modified:** 2 modified, 2 test files created

## Accomplishments
- `drift.main()` now parses `--contracts-dir`/`--baseline` and routes them to the already-parameterized `run_gate(contracts_dir, baseline_path)`; bare invocation defaults stay `CONTRACTS_DIR`/`MANIFEST_PATH` (root job byte-unchanged).
- Drift DRIFT message is tree-aware: root prints bare `hash --write`; a non-root tree prints `hash --write --contracts-dir <D> --manifest <B>` (Warning-2 fix).
- Fixed the `write_manifest()` bug (it called bare `build_manifest()` → always ROOT). Signature is now `write_manifest(manifest_path=MANIFEST_PATH, contracts_dir=CONTRACTS_DIR)` and it builds over `contracts_dir` — a human can rebaseline the example manifest without corrupting it with root hashes (Warning-1/T-06-11 fix).
- `hash.main()` gained symmetric `--contracts-dir`/`--manifest` argparse; `--write` threads BOTH.
- Confirmed `uv run python -m tools.contract_drift.drift --contracts-dir examples/log-parser/contracts --baseline examples/log-parser/contracts/.hashes/manifest.json` reads clean (exit 0) via the real flags (previously clean-by-accident because argv was ignored).

## Task Commits

1. **Task 1 (RED): failing drift/hash CLI flag tests** - `39f57d0` (test)
2. **Task 2 (GREEN): --contracts-dir/--baseline argparse on drift main()** - `a24f245` (feat)
3. **Task 3 (GREEN): symmetric hash flags + write_manifest threading + tests** - `f5a6274` (feat)

_Note: the Task-1 RED test was later rewritten in Task 3's commit to use a synthetic tree (GEN-04), with the example-referencing proof moved to the instance plane._

## Files Created/Modified
- `tools/contract_drift/drift.py` - argparse `--contracts-dir`/`--baseline` in `main()`; tree-aware rebaseline hint; `argparse` import.
- `tools/contract_hash/hash.py` - `write_manifest(manifest_path, contracts_dir)` threading; argparse `--contracts-dir`/`--manifest` in `main()`; robust wrote-summary path; `argparse` import.
- `tools/contract_drift/tests/test_cli_flags.py` - core-plane tests driving the flags against a self-built SYNTHETIC contracts tree (pristine pass / mutated fail / no-flags-root / write-threading regression).
- `examples/log-parser/tests/test_contract_drift_cli_flags.py` - instance-plane tests driving the core CLIs against the real example manifest (pristine pass / mutated fail / write-targets-example).

## Decisions Made
- The plan specified the example-referencing test at `tools/contract_drift/tests/test_cli_flags.py`. That path is a **core plane** file, and the GEN-04/GEN-05 guard (`tools/harness_lint/tests/test_core_no_example_dep.py`, a CLAUDE.md hard invariant) forbids any core file from naming an instance under `examples/` (or carrying domain prose like `equipment`/`standard-log`/`correction-rules`). CLAUDE.md takes precedence over the plan, so the example-referencing proof was moved to the **instance plane** (`examples/log-parser/tests/`, the allowed example→core direction), and the core test was rewritten to use a domain-neutral synthetic tree. Both halves prove the same flag-routing + write-threading behavior.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] GEN-04 core-no-example-dep guard blocked the planned test location**
- **Found during:** Task 3 (full-suite verification)
- **Issue:** The plan placed the example-referencing test in `tools/` (core). The GEN-04 guard RED-flagged it — core planes must not path-reference `examples/` nor carry domain prose. This is a CLAUDE.md hard invariant that overrides the plan's single-file artifact spec.
- **Fix:** Rewrote `tools/contract_drift/tests/test_cli_flags.py` to exercise the flags against a self-built synthetic contracts tree (no instance names); added `examples/log-parser/tests/test_contract_drift_cli_flags.py` (instance plane, allowed to reference `examples/`) carrying the pristine-example-pass / mutated-fail / write-targets-example proof.
- **Files modified:** tools/contract_drift/tests/test_cli_flags.py, examples/log-parser/tests/test_contract_drift_cli_flags.py
- **Verification:** GEN-04 guard suite green (18 passed); full non-example suite green (413 passed); instance test green (3 passed).
- **Committed in:** f5a6274 (Task 3 commit)

**2. [Rule 1 - Bug] Non-repo `--manifest` path crashed the wrote-summary print**
- **Found during:** Task 3 (write-threading test)
- **Issue:** `out.relative_to(REPO_ROOT)` in `hash.main()` raised `ValueError` when `--manifest` targets a path outside the repo (e.g. a tmp rebaseline) — a crash newly reachable now that `--manifest` accepts arbitrary paths.
- **Fix:** Wrapped the relative-path computation in a try/except, falling back to the absolute path.
- **Files modified:** tools/contract_hash/hash.py
- **Verification:** `test_write_threads_contracts_dir_not_root` passes; bare `hash --write` still prints the repo-relative path.
- **Committed in:** f5a6274 (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking/GEN-04 relocation, 1 bug)
**Impact on plan:** The must-have "a pristine example-contracts copy passes / mutated fails through the CLI wrapper" is fully satisfied — relocated to the instance plane per the GEN-04 hard constraint. All other artifacts and locked constraints met. No scope creep.

## Issues Encountered
- A formatter (PostToolUse hook) reflowed `hash.py` mid-edit; re-read before the next edit. Several E501 line-length errors on new docstrings were shortened to satisfy ruff (line-length 100). All resolved.

## Concurrency Note (06-01 in-flight)
Plan 06-01 ran concurrently in the same wave. At completion its uncommitted edits to `.planning/{STATE,ROADMAP,REQUIREMENTS}.md` plus `06-01-SUMMARY.md` and `deferred-items.md` were present in the working tree. Per the task instruction to leave 06-01 files untouched, this plan did NOT stage, edit, or commit those planning files — state/roadmap/requirements reconciliation is left to the orchestrator. This plan committed only its own code + test files (and this SUMMARY). `harness/project.toml` (06-01's file) was left untouched.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The drift + hash CLIs now accept `--contracts-dir`/`--baseline`/`--manifest`, so the Wave-2 CI `drift` job (Plan 03) can gate BOTH the root and example manifests by verbatim tool reuse.
- No new packages; no model identifiers in any artifact.

## Self-Check: PASSED

All created/modified files exist on disk; all task commits (`39f57d0`, `a24f245`, `f5a6274`) present in git history.

---
*Phase: 06-ci-gates*
*Completed: 2026-07-09*
