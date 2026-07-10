---
phase: 03-agents-commands-skills
plan: 01
subsystem: infra
tags: [permissions, opencode, fnmatch, last-wins, resolver, uv-workspace, config-02]

# Dependency graph
requires:
  - phase: 02-context-memory
    provides: uv workspace + virtual-member pattern (tools/*, package=false) that harness_perms mirrors
provides:
  - "harness/permission-matrix.json — the 15-key opencode permission matrix as pure data (CONFIG-02)"
  - "tools/harness_perms — pure stdlib last-wins bash resolver + path-deny resolver (resolve_bash, resolve_path, load_matrix)"
  - "Unit-proven access posture: dotnet/uv/pytest allow, git push ask, rm -rf deny, unknown→ask; contracts/golden/*.env writes deny"
affects: [phase-04-hooks, contract-guard, secret-hook, opencode.json, phase-06-emitter]

# Tech tracking
tech-stack:
  added: []  # zero new external packages — stdlib fnmatch + json only (T-03-SC honored)
  patterns:
    - "Permission-as-data: matrix lives in harness/*.json; enforcement logic lives in the tested resolver — one source, no divergent re-impls"
    - "Insertion-ordered bash object encodes last-wins; catch-all * FIRST, specifics after (never trailing broad allow, P3)"
    - "Lazy package re-export via PEP 562 __getattr__ to keep a convenient top-level API without breaking pytest conftest-collection bootstrap"

key-files:
  created:
    - harness/permission-matrix.json
    - tools/harness_perms/resolver.py
    - tools/harness_perms/__init__.py
    - tools/harness_perms/pyproject.toml
    - tools/harness_perms/tests/test_resolver.py
    - tools/harness_perms/tests/conftest.py
    - tools/harness_perms/tests/__init__.py
  modified:
    - uv.lock

key-decisions:
  - "Matrix bash object ends with rm -rf*:deny (not a broad allow) — last-wins misordering is the P3 privilege-escalation trap; Task-1 verify asserts the last bash key is not allow"
  - "Path-scoped denies (contracts/**, docs/adr/**, golden/**, *.env, **/*.env) live as data in the matrix and are enforced by resolve_path — opencode's native edit key is not path-globbable (D-03/A2)"
  - "resolver.py is eval/subprocess-free pure fnmatch+json — reusable verbatim by Phase-4 hooks (T-03-04 accept via purity, not runtime guard)"
  - "__init__.py re-exports lazily (PEP 562) rather than eagerly, so importing the package during conftest collection does not require sys.path to be pre-wired"

patterns-established:
  - "Pattern: permission matrix = ordered JSON data + pure tested resolver; hooks consume, never re-implement"
  - "Pattern: virtual uv member with zero external deps registers a member-only uv.lock stanza (no third-party churn)"

requirements-completed: [CONFIG-02]

# Metrics
duration: 12min
completed: 2026-07-08
---

# Phase 3 Plan 01: Permission-matrix data + last-wins glob resolver Summary

**15-key opencode permission matrix as ordered JSON data plus a pure stdlib fnmatch last-wins bash resolver and path-scoped deny resolver, unit-proven (dotnet→allow, git push --force→ask, rm -rf→deny, unknown→ask; contracts/golden/*.env writes→deny) and reusable verbatim by Phase-4 hooks.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-07-08
- **Tasks:** 2 (Task 2 is TDD: RED → GREEN)
- **Files created:** 7 | **Files modified:** 1 (uv.lock)

## Accomplishments
- `harness/permission-matrix.json` — all 15 permission keys (read, edit, bash, glob, grep, list, task, external_directory, todowrite, question, webfetch, websearch, lsp, skill, doom_loop) with allow/ask/deny; `external_directory` default ask; bash as an insertion-ordered `*`-first last-wins object; `path_deny_globs` for the constitution/secret planes.
- `tools/harness_perms/` uv virtual member (`package = false`, stdlib only) exporting `resolve_bash`, `resolve_path`, `load_matrix`.
- 12 unit tests encode last-wins, default-deny, and path-deny cases against the REAL shipped matrix; all green. Full workspace suite: 100 passed, 2 pre-existing .NET-egress skips. Ruff clean.

## Task Commits

1. **Task 1: Author the 15-key permission matrix data** — `590f769` (feat)
2. **Task 2 (TDD RED): failing resolver tests + uv member** — `9b6cda8` (test)
3. **Task 2 (TDD GREEN): implement pure last-wins resolver** — `dbe357f` (feat)

_No REFACTOR commit — GREEN code was clean (ruff passed, no duplication)._

## Files Created/Modified
- `harness/permission-matrix.json` — CONFIG-02 permission data: 15 keys + ordered bash last-wins + path_deny_globs. Pure data, no logic.
- `tools/harness_perms/resolver.py` — `resolve_bash` (last matching fnmatchcase glob wins, default-deny fallthrough), `resolve_path` (deny on constitution/secret globs), `load_matrix` (single repo-root-anchored loader; no eval/subprocess/shell).
- `tools/harness_perms/__init__.py` — lazy PEP-562 re-export of the three public symbols.
- `tools/harness_perms/pyproject.toml` — virtual uv member, `requires-python >=3.11`, zero deps.
- `tools/harness_perms/tests/test_resolver.py` — 12 behavior cases loading the real matrix.
- `tools/harness_perms/tests/conftest.py` — repo-root sys.path wiring (mirrors memory_regen).
- `tools/harness_perms/tests/__init__.py` — test package marker.
- `uv.lock` — registers the `logparser-harness-perms` virtual member stanza only (zero external packages).

## Decisions Made
- **Bash object never ends with a broad allow.** Terminal rule is `rm -rf*:deny`; the Task-1 verify asserts `bash[last] != "allow"`, closing the P3 last-wins escalation trap (T-03-01).
- **Path denies are data, resolved by `resolve_path`.** opencode's native `edit` key is not path-globbable (D-03/A2), so `contracts/**`, `docs/adr/**`, `golden/**`, `*.env`, `**/*.env` are enforced by the resolver — the portable, Phase-4-reusable enforcement point (T-03-02/03).
- **Resolver is pure fnmatch+json.** No `eval`, no `subprocess`, no shell — the injection threat (T-03-04) is dispositioned "accept" by construction rather than by a runtime guard.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `tools/harness_perms/tests/conftest.py` (not in the plan's file list)**
- **Found during:** Task 2 (RED — test collection)
- **Issue:** `tools` is a namespace package (no `tools/__init__.py`); pytest could not import `tools.harness_perms` during collection (`ModuleNotFoundError: No module named 'tools'`), so the tests could not run at all.
- **Fix:** Added a conftest that prepends the repo root to `sys.path`, mirroring the established `tools/memory_regen/tests/conftest.py` idiom for virtual uv members.
- **Files modified:** tools/harness_perms/tests/conftest.py
- **Verification:** `uv run pytest tools/harness_perms/tests/` collects and runs (12 passed).
- **Committed in:** `9b6cda8` (RED commit)

**2. [Rule 3 - Blocking] `__init__.py` re-exports lazily (PEP 562) instead of eagerly**
- **Found during:** Task 2 (RED — test collection)
- **Issue:** An eager top-level `from tools.harness_perms.resolver import ...` in `__init__.py` runs during pytest's conftest-collection bootstrap (before the conftest wires `sys.path`), deadlocking collection with `ModuleNotFoundError: No module named 'tools'`.
- **Fix:** Deferred the submodule import behind a module `__getattr__`, so `from tools.harness_perms import resolve_bash` still works for Phase-4 hooks but nothing imports the submodule until first attribute access (after path is wired). Satisfies the plan's "re-export" requirement without the ordering hazard.
- **Files modified:** tools/harness_perms/__init__.py
- **Verification:** Collection succeeds; top-level import path exercised by the tests (12 passed).
- **Committed in:** `9b6cda8` (RED commit)

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking test-infrastructure issues intrinsic to virtual-member/namespace-package import). No scope creep; both are mechanical enablers for the planned tests.

## Issues Encountered
- **uv.lock churn expectation.** The plan's acceptance criterion says "uv.lock unchanged — stdlib only." Registering a new virtual member necessarily appends the member's own stanza (name + `source = { virtual = ... }`) — exactly as `tools/memory_regen` did in Phase 2. The diff adds **zero external/third-party packages**; a second `uv sync --all-packages` is a no-op (lock stable). The intent of the criterion / T-03-SC ("no new external packages") is satisfied; the member-registration line is unavoidable and benign.

## Known Stubs
None — the resolver is fully implemented; the RED stub was replaced in GREEN (`dbe357f`).

## User Setup Required
None — no external service configuration required. Zero new packages, stdlib only.

## Next Phase Readiness
- **Phase-4 hooks (contract-guard / secret) can import `tools.harness_perms` unchanged:** `resolve_bash(matrix["bash"], cmd)` and `resolve_path(matrix["path_deny_globs"], path)` with `load_matrix()` as the shared loader.
- `harness/opencode.json` (CONFIG-01, a later Phase-3 plan) can embed the same bash matrix under `permission.bash` — the JSON data is copy-ready.
- No blockers introduced. The .NET-egress skips (2) are pre-existing and unrelated (BOOT-01).

## Self-Check: PASSED

All 8 declared files exist on disk; all 3 task commits (`590f769`, `9b6cda8`, `dbe357f`) present in git history.

---
*Phase: 03-agents-commands-skills*
*Completed: 2026-07-08*
