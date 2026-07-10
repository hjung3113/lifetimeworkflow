---
phase: 04-plugins-hooks
plan: 01
subsystem: testing
tags: [polyglot, linter, normalization, tsv, boundary, stdlib, uv-workspace, tdd]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "libs/python normalize.core (normalize_cell/normalize_tsv, §4.3-4.6) + libs/normalize-fixtures/*.json shared corpus"
  - phase: 01-foundation
    provides: "tools/golden_runner sys.path shim pattern for importing normalize.core from a tools/ member"
  - phase: 03-agents-commands-skills
    provides: "tools/harness_perms PEP 562 lazy re-export idiom for a namespace-package uv member"
provides:
  - "tools/polyglot_lint: the shared §4.3-4.6 rule engine (lint_bytes/lint_tsv/lint_file -> [Violation]; main -> exit 0/1)"
  - "Detection-by-normalization POLY-01 linter reusing normalize.core (no second normalizer)"
  - "Corpus-parity proof (identity + fixture corpus) that the linter shares the Phase-1 core"
affects: [HOOK-04, HOOK-03, on-write-hook, commit-gate, phase-05-ci]

# Tech tracking
tech-stack:
  added: []  # zero external deps — stdlib + in-repo normalize.core only; uv.lock gained the member entry only
  patterns:
    - "Detection-by-normalization: a linter detects a §4.3-4.6 breach by diffing a cell against normalize.core output (RESEARCH Pattern 5)"
    - "uv virtual workspace member (package=false, dependencies=[]) reusing libs/python via the golden_runner sys.path shim"
    - "PEP 562 lazy package re-export to avoid conftest-collection import ordering hazards"

key-files:
  created:
    - "tools/polyglot_lint/lint.py"
    - "tools/polyglot_lint/__init__.py"
    - "tools/polyglot_lint/pyproject.toml"
    - "tools/polyglot_lint/tests/__init__.py"
    - "tools/polyglot_lint/tests/conftest.py"
    - "tools/polyglot_lint/tests/test_lint.py"
    - "tools/polyglot_lint/tests/test_corpus_parity.py"
  modified:
    - "uv.lock"

key-decisions:
  - "Rule codes mirror libs/normalize-spec.md: R1-BOM, R2-CRLF, R7-tsv (column-shift), R3-decimal, R5-datetime, R6-null"
  - "R6-null detects the leaked internal sentinel '<NULL>' in wire TSV; the agreed wire null token '\\N' is canonical and never flagged (even in a typed column)"
  - "Cell non-canonicality guard: normalize_cell(cell,kind) != cell AND cell != null_token — so a legit null in a decimal/datetime column is not a false positive"
  - "Corpus-parity proven two ways: function identity (lint.normalize_cell IS core.normalize_cell) + reproducing libs/normalize-fixtures/*.json canonical values"

patterns-established:
  - "Detection-by-normalization for polyglot boundary linting (reuse, never re-implement the normalizer)"
  - "New uv workspace member must ship its pyproject.toml in the same commit the member dir first appears (tools/* glob requires it)"

requirements-completed: [POLY-01]

# Metrics
duration: 14min
completed: 2026-07-08
---

# Phase 4 Plan 01: POLY-01 Polyglot-Boundary Linter Summary

**Stdlib-only §4.3-4.6 boundary linter (BOM · CRLF · TSV column-shift · decimal-locale · timezone · null-vs-empty) that detects violations by diffing raw input against the shared Phase-1 normalize.core — provably no second normalizer.**

## Performance

- **Duration:** ~14 min
- **Completed:** 2026-07-08
- **Tasks:** 2 (both TDD)
- **Files created:** 7 (+1 modified: uv.lock)

## Accomplishments
- `tools/polyglot_lint/lint.py`: `lint_bytes` / `lint_tsv` / `lint_file` → `list[Violation]`, plus `main(argv)` that exits 0 clean / 1 on any violation with rule code + detail to **stderr** (fail loud).
- Encodes six §4.3-4.6 rules: R1-BOM, R2-CRLF, R7-tsv (uneven tab counts), R3-decimal, R5-datetime, R6-null — the shared rule engine HOOK-04 (on-write) and HOOK-03 (commit-gate) will both call.
- Reuses `libs/python` `normalize.core` (`normalize_cell` / `normalize_tsv`) via the golden_runner sys.path shim — decimal/datetime/null non-canonicality is detected by diffing each cell against the core, never a re-implementation (D-02/D-03 built-once).
- `test_corpus_parity.py` proves zero drift two ways: **function identity** (`lint.normalize_cell is normalize.core.normalize_cell`) and reproduction of every `libs/normalize-fixtures/*.json` canonical value.
- Registered as a zero-dep `package=false` uv workspace member; `uv.lock` gains only the member entry (no external packages — T-04-SC accept posture holds).

## Task Commits

1. **Task 1: Failing rule + corpus-parity tests (RED)** — `fb71bf6` (test)
2. **Task 2: Implement lint.py detection-by-normalization + uv member (GREEN)** — `f869eaf` (feat)

_TDD: RED commit precedes GREEN commit; no refactor commit needed (implementation clean on first green)._

## Files Created/Modified
- `tools/polyglot_lint/lint.py` — the §4.3-4.6 rule engine (lint_bytes/lint_tsv/lint_file/main + `Violation` frozen dataclass)
- `tools/polyglot_lint/__init__.py` — PEP 562 lazy re-export of lint_bytes/lint_tsv/lint_file/main/Violation
- `tools/polyglot_lint/pyproject.toml` — uv virtual member (package=false, dependencies=[])
- `tools/polyglot_lint/tests/__init__.py` — test package marker
- `tools/polyglot_lint/tests/conftest.py` — sys.path wiring (repo root + libs/python), mirrors golden_runner
- `tools/polyglot_lint/tests/test_lint.py` — per-rule violation + fail-loud CLI proofs (12 tests)
- `tools/polyglot_lint/tests/test_corpus_parity.py` — identity + fixture-corpus drift proof (6 tests)
- `uv.lock` — registers the `logparser-polyglot-lint` virtual member (metadata only)

## Decisions Made
- **R6-null semantics:** with detection-by-normalization there is no schema-free way to flag null-vs-empty confusion, but the internal comparison sentinel `<NULL>` leaking into wire TSV is an unambiguous §4.3 boundary bug — so R6-null flags a literal `<NULL>` cell while the agreed wire null token `\N` stays canonical (never flagged, even inside a decimal/datetime column via the `cell != null_token` guard).
- **Rule codes** follow `libs/normalize-spec.md` numbering (R1/R2/R3/R5/R6/R7) so the linter's output is traceable to the canonical spec.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Shipped `pyproject.toml` in the RED (test) commit instead of the GREEN commit**
- **Found during:** Task 1 (RED)
- **Issue:** The root uv workspace declares `members = ["tools/*"]`; the moment `tools/polyglot_lint/` exists, `uv run`/`uv sync` **refuses to start** (`Workspace member … is missing a pyproject.toml`). Without it, the RED suite could not run at all — it errored on a broken workspace, not on the intended "module absent" signal, and every other package's tests would also fail to run at that commit.
- **Fix:** Authored `tools/polyglot_lint/pyproject.toml` (the Task-2 template, package=false, zero deps) during Task 1 so the RED commit's working tree is uv-valid. RED then failed for the correct reason (`ImportError: cannot import name 'lint'`).
- **Files modified:** tools/polyglot_lint/pyproject.toml
- **Verification:** `uv run pytest tools/polyglot_lint/tests -x -q` errored on the absent lint module (RED), then passed 18/18 after Task 2 (GREEN).
- **Committed in:** `fb71bf6` (RED commit)

**2. [Rule 3 - Blocking] Added `tools/polyglot_lint/tests/conftest.py` (not in the plan's file list)**
- **Found during:** Task 1 (RED)
- **Issue:** The tests import `from tools.polyglot_lint import …` (needs repo root on sys.path) and, in the parity test, `from normalize.core import …` (needs libs/python on sys.path). `tools` is a namespace package, so the tests must wire their own path — exactly as `tools/golden_runner/tests/conftest.py` and `tools/harness_perms/tests/conftest.py` do.
- **Fix:** Added a conftest.py inserting repo root + libs/python, mirroring the established in-repo idiom the plan directed me to follow.
- **Files modified:** tools/polyglot_lint/tests/conftest.py
- **Verification:** Both test modules import and run under `uv run pytest`.
- **Committed in:** `fb71bf6` (RED commit)

**3. [Rule 3 - Blocking] `uv.lock` gained the member entry**
- **Found during:** Task 2 (GREEN)
- **Issue:** `uv sync --all-packages` registers the new virtual member in `uv.lock`. The threat model's T-04-SC says "uv.lock unchanged (no install surface)".
- **Fix:** Committed `uv.lock` — the change is a **member-registry entry only** (`source = { virtual = "tools/polyglot_lint" }`); **no external package** was added, so T-04-SC's intent (zero new dependency install surface) is preserved. This is the same benign member-registration every prior `package=false` tools/* member produced.
- **Files modified:** uv.lock
- **Verification:** `git diff uv.lock` shows only the `logparser-polyglot-lint` virtual-member lines; `uv sync` reports "Resolved 43 packages" with no downloads.
- **Committed in:** `f869eaf` (GREEN commit)

---

**Total deviations:** 3 auto-fixed (all Rule 3 - blocking, all forced by the uv-workspace / namespace-package mechanics).
**Impact on plan:** No scope creep. All three are the mechanically-required consequences of adding a new `tools/*` uv member; the plan's task/file split assumed pyproject in Task 2, but the workspace glob forces it into Task 1. No behavior deviated from the plan's intent.

## Issues Encountered
- Two `tools/hooks/tests/*` files briefly showed as modified in the working tree after `uv run` — this was **stat-only** dirtiness (identical content and mode; empty `git diff`). Cleared with `git update-index --refresh`. Left untouched (out of scope for POLY-01, and no real change).

## Threat Flags
None — no new security-relevant surface beyond the plan's threat_model. The linter is read-only over byte streams, spawns nothing, and adds zero external dependencies (T-04-SC accept posture verified).

## Test Results
- **Package suite:** `uv run pytest tools/polyglot_lint/tests -x -q` → **18 passed** (12 rule/CLI + 6 corpus-parity).
- **Full suite:** `uv run pytest` → **270 passed, 2 skipped** (the 2 skips are the pre-existing .NET-egress-blocked golden spawn tests from 01-06; no Phase 1-3 regression).
- **CLI fail-loud demo:** a BOM TSV → `polyglot-lint: FAIL [R1-BOM] …` on stderr, exit 1.
- **No re-implemented normalizer:** `grep -c "def _norm_decimal\|utf-8-sig" tools/polyglot_lint/lint.py` → 0.

## Next Phase Readiness
- POLY-01 rule engine is ready to be composed by HOOK-04 (on-write) and HOOK-03 (commit-gate) — a single `lint_file(path, kinds)` call surface returning `[Violation]`, with `main` giving the fail-loud CLI/exit-code contract those hooks need.
- No blockers introduced. `.NET`-side golden spawn remains deferred (BOOT-01 egress), unrelated to this plan.

---
*Phase: 04-plugins-hooks*
*Completed: 2026-07-08*

## Self-Check: PASSED

All 7 created files verified present + SUMMARY.md; both task commits (fb71bf6 RED, f869eaf GREEN) exist in git log.
