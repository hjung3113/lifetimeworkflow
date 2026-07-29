---
phase: 42-adoption-decoupling-install-set-repair
plan: 04
subsystem: adoption-lifecycle
tags: [python, pytest, install-set, tdd, prod-01]

# Dependency graph
requires: []
provides:
  - "tools/adoption_scan/tests/test_install_completeness.py — a fixture-install test that
    regex-walks every emitted `python -m tools.X` reference and asserts the concrete `.py` file it
    resolves to lands in a real `apply_manifest()` target tree"
  - "tools/adoption_scan/destinations.py::_CATEGORY_GLOBS now carries a `tools/**/*` row, closing
    the gap where commands/CI shipped but the Python those commands invoke did not"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Blanket glob data-row over enumerated per-package list (D-07) — the install-set catalog
      resolves package membership at install time from the live tree, so a future package
      deletion (Phases 43/44) requires zero edit to destinations.py"
    - "Resolve a `python -m tools.X` reference to its concrete `.py` file (not just its parent
      directory) before asserting post-apply existence — a directory-only check is provably
      vacuous here because `**/pyproject.toml` already creates every `tools/<pkg>/` directory"

key-files:
  created:
    - tools/adoption_scan/tests/test_install_completeness.py
  modified:
    - tools/adoption_scan/destinations.py

key-decisions:
  - "D-08 fixture-install test authored and run RED before the fix, per plan mandate."
  - "D-07: exactly one blanket tools/**/* row, not an enumerated per-package list."
  - "D-09: shipping each surviving package's tests/ alongside its source is accepted, not
    filtered."
  - "Deviation (Rule 1 — bug in the plan's literal instruction): the plan's interface block
    specified the row as the literal string `\"tools/**\"`. `Path.glob(\"tools/**\")` matches
    directories only — a trailing `**` component with nothing after it never yields files. Every
    other row in `_CATEGORY_GLOBS` already uses the `**/*` suffix for this exact reason (e.g.
    `\"contracts/**/*\"`, `\"harness/agents/**/*\"`). Landed `\"tools/**\"` first (matching the plan
    literally, commit `0914ec8`), observed the fixture-install test still RED against the fixed
    catalog, diagnosed the pathlib gotcha, and added a follow-up fix commit (`5453894`) switching
    to `\"tools/**/*\"`, consistent with every sibling row. The plan's acceptance-criteria grep
    (`grep -c '\"tools/\\*\\*\"'` == 1) technically no longer matches literally since the row text
    is now `\"tools/**/*\"`, but the substantive success criteria — `_CATEGORY_GLOBS` gains exactly
    one new `tools/`-scoped row and the fixture-install test is GREEN — is met and is what the
    plan's `<success_criteria>` section actually requires."

requirements-completed: [PROD-01]

# Metrics
duration: ~35min
completed: 2026-07-28
---

# Phase 42 Plan 04: Install-Set Repair (PROD-01) Summary

**Closed the install-set gap where every emitted command/skill/CI file shells `uv run python -m tools.X` but `_CATEGORY_GLOBS` shipped none of the Python those commands invoke — proved by a genuinely-RED-first fixture-install test, then fixed with one `tools/**/*` glob row.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-07-28
- **Tasks:** 2/2
- **Files modified:** 2 (one new test file, one existing module)

## Accomplishments

- Authored `tools/adoption_scan/tests/test_install_completeness.py`: regex-walks
  `harness/commands/**/*.md`, `harness/skills/**/*.md`, and `.github/workflows/*.yml` for every
  `python -m tools\.([a-zA-Z0-9_.]+)` reference, resolves each dotted reference to the concrete
  `.py` file it invokes (`<submodule>.py`, or `__main__.py`/`__init__.py` for a bare package), runs
  a real `destination_catalog()` → `harness_proposed_hashes()` → `build_manifest()` →
  `apply_manifest()` pipeline against a fresh `tmp_path`, and asserts every resolved file exists
  post-apply. A companion sanity test (`test_discovers_at_least_twenty_modules`) guards against the
  regex helper silently matching nothing.
- Observed genuine RED against the pre-fix catalog (see "RED Observation" below), committed the
  test alone.
- Added exactly one new `"tools/**/*"` row to `_CATEGORY_GLOBS`, placed immediately after
  `"**/pyproject.toml"`. Confirmed GREEN.
- Verified the glob does not sweep in `__pycache__`/`.pyc`/`.venv` junk (git-tracked filter in
  `destination_catalog()` excludes them by construction — confirmed empirically, not assumed).

## RED Observation (Task 1, required proof)

An earlier draft of the test asserted only `(tmp_path / "tools" / package_name).is_dir()` per the
plan's literal `<behavior>` wording, and **passed on the first run** — a vacuous pass, because
every `tools/<pkg>/pyproject.toml` already ships via the pre-existing `"**/pyproject.toml"` glob
row, which creates the package's parent directory without any of its `.py` source. Per the
fail-fast rule ("if the test passes on the first run, that is a finding — stop and investigate"),
this was diagnosed and the assertion rewritten to resolve each reference to its concrete `.py` file
rather than its containing directory. That version was then run and produced the required RED:

```
FAILED tools/adoption_scan/tests/test_every_referenced_tools_module_lands_in_applied_target
AssertionError: tools.adoption_apply (implemented at tools/adoption_apply/__main__.py) was
referenced by an emitted command/skill/CI workflow but is missing from the applied target tree at
.../tools/adoption_apply/__main__.py
assert False
 +  where False = is_file()
```

This is the correct, non-vacuous proof: `tools/adoption_apply/pyproject.toml` (matched by the
pre-existing `**/pyproject.toml` glob) had already created the `tools/adoption_apply/` directory,
but `__main__.py` — the actual code `/adopt` (etc.) shells out to — was absent from the applied
target, confirming PROD-01's defect.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the fixture-install test and observe it RED against the pre-fix catalog** -
   `6061f1d` (test)
2. **Task 2: Add the tools/** glob row and confirm the fixture-install test turns GREEN** -
   `0914ec8` (feat) — landed the plan's literal `"tools/**"` row text
3. **Follow-up fix (Rule 1 — see Deviations above), still within Task 2's scope**: `5453894` (fix)
   — corrected the glob to `"tools/**/*"` after `0914ec8` proved insufficient (test remained RED)

**Plan metadata:** (this commit, immediately following)

## Files Created/Modified

- `tools/adoption_scan/tests/test_install_completeness.py` (new) — the fixture-install test, D-08's
  deliverable, the one new file this phase adds
- `tools/adoption_scan/destinations.py` — `_CATEGORY_GLOBS` gained one `"tools/**/*"` row after
  `"**/pyproject.toml"`

## Decisions Made

- D-07/D-08/D-09 as specified in CONTEXT.md — see frontmatter `key-decisions`.
- Deviation (Rule 1 — auto-fixed bug in the plan's literal glob text) — see frontmatter
  `key-decisions` for full detail and commit references.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `"tools/**"` (as the plan's interface block specified literally) does not
match files under `Path.glob`**
- **Found during:** Task 2, immediately after landing the plan's literal row text and re-running
  the fixture-install test
- **Issue:** `pathlib.Path.glob("tools/**")` — a trailing `**` component with nothing following it
  — resolves to every recursive **directory** under `tools/`, never a file. `destination_catalog()`
  filters `candidate.is_file()`, so the row silently contributed zero rows beyond what other globs
  already covered; the fixture-install test stayed RED after commit `0914ec8`.
- **Fix:** Changed the row to `"tools/**/*"`, matching the `**/*` suffix convention every other
  `_CATEGORY_GLOBS` row already uses (`"contracts/**/*"`, `"harness/agents/**/*"`, etc.).
- **Files modified:** `tools/adoption_scan/destinations.py`
- **Commit:** `5453894`

## Issues Encountered

None beyond the Rule 1 deviation above (which is the expected shape of this phase's work — the
whole point of Task 1's RED-first requirement is to catch exactly this class of "looks fixed but
isn't" mistake before it ships).

## User Setup Required

None - no external service configuration required.

## Verification

- `uv run pytest tools/adoption_scan/tests/test_install_completeness.py -x -v` -> 2 passed (GREEN,
  after `5453894`)
- `uv run pytest tools/adoption_scan -q` -> 87 passed (up from 85 in 42-03-SUMMARY.md: +2 new
  tests, no regression)
- `uv run pytest tools/adoption_scan/tests/test_snapshots.py -q` -> 1 passed (unaffected by catalog
  growth, per RESEARCH.md)
- `uv run pytest --collect-only -q` (whole repo) -> 1315 tests collected, exit 0
- `grep -c '"tools/\*\*/\*"' tools/adoption_scan/destinations.py` -> 1 (exactly one new row; see
  Deviations above for why the row text differs from the plan's literal `"tools/**"` — grepping for
  the plan's exact literal string now returns 0, which is expected and correct)
- Junk-sweep check: `destination_catalog()` filtered to `tools/` rows (317 total) contains zero
  `__pycache__`/`.pyc`/`.venv` entries — confirmed by direct enumeration, not assumed from the
  git-tracked filter's docstring
- `git log --oneline -5` shows 3 new commits for this plan (2 tasks + 1 in-scope follow-up fix),
  Task 1's commit preceding both Task 2 commits

**Changed LOC (D-17, from `git diff --stat` across the plan's full commit range):**
2 files changed, 118 insertions(+) (`test_install_completeness.py` +117 new file;
`destinations.py` net +1)

## Next Phase Readiness

- Every `tools.X` module an emitted command/skill/CI workflow invokes now demonstrably lands in a
  fresh install via a real `apply_manifest()` run — PROD-01 is closed with a regression-guarding
  test, not just a one-time manual check.
- The `tools/**/*` row is a blanket glob, so Phases 43/44 deleting `tools/task_control` (and any
  other package) requires zero edit to `destinations.py` or this test — the test will simply stop
  discovering references to the deleted package's modules (per the emitted-command sweep those
  phases also own) and stop asserting their existence.
- No blockers for Plan 05 (`harness/**` rewrites + re-emit) or Phase 43/44.

## Self-Check: PASSED

All claimed files and commit hashes verified present in the working tree and git history:
- `test -f tools/adoption_scan/tests/test_install_completeness.py` -> found
- `git log --oneline --all | grep -q 6061f1d` -> found
- `git log --oneline --all | grep -q 0914ec8` -> found
- `git log --oneline --all | grep -q 5453894` -> found

---
*Phase: 42-adoption-decoupling-install-set-repair*
*Completed: 2026-07-28*
