---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
plan: 03
subsystem: infra
tags: [atomic-write, os-link, marker-merge, structural-refusal, python-stdlib]

# Dependency graph
requires:
  - phase: 27-01
    provides: "tools/adoption_apply zero-dependency uv workspace member + batch.py's atomic-create idiom precedent"
  - phase: 27-02
    provides: "contracts/harness/adoption/approval.schema.json (constitution-plane precedent this plan's refusal protects)"
provides:
  - "tools/adoption_apply/apply.py — the ADOPT-05 writer: refuse_if_constitution(), refuse_if_outside_root(), atomic_create(), apply_disposition(), apply_manifest()"
  - "Structural, hook-independent constitution-plane refusal proven by a zero-filesystem-call spy"
  - "Draft-mode artifact-root confinement (refuse_if_outside_root/PathEscapeError) for Plan 27-06's cli.py draft sub-verb"
affects: [27-05, 27-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "apply.py's atomic_create/_atomic_replace are apply.py's own copies of manager.py::_atomic_create/_atomic_replace, operating on raw bytes instead of a JSON dict — a third independently-audited instance of the tempfile.mkstemp+os.link/os.replace+fsync idiom in this repo"
    - "apply_disposition calls refuse_if_constitution FIRST, unconditionally, before any disposition branch — a per-call precondition, never cached once per batch"
    - "apply_manifest catches ConstitutionRefusal per-record (buckets into 'refused', continues) but lets ConcurrentDriftError/UnknownDispositionError propagate (integrity faults abort the whole apply, routine refusals do not)"

key-files:
  created:
    - tools/adoption_apply/apply.py
    - tools/adoption_apply/tests/test_constitution_refusal.py
    - tools/adoption_apply/tests/test_atomic_apply.py
  modified: []

key-decisions:
  - "apply_disposition/apply_manifest use explicit payload/block_bodies dict parameters rather than sourcing content from the manifest itself — the manifest schema's dispositionRecord carries no content field by design (only destination/disposition/reason/evidence); content sourcing from the batch draft's inventory is Plan 27-06's cli.py concern, not this plan's"
  - "create disposition's concurrent-drift check is existence-based, not hash-based: a 'create' disposition means the manifest recorded no existing target at draft time, so ANY existing target at apply time is drift by definition — _existing_hash is still called to enrich the ConcurrentDriftError message, but the branch condition itself needs no stored draft-time hash"
  - "marker-merge for .claude/settings.json needs no manifest-supplied content at all — merge_settings(existing) is fully self-determined by tools.harness_emit.merge.HARNESS_HOOK_GROUPS; only the two Markdown destinations (AGENTS.md/CLAUDE.md) take a block_body parameter"

patterns-established:
  - "Every apply.py public function that could hit the filesystem is preceded, in the same function body, by a raise-first structural guard (refuse_if_constitution or refuse_if_outside_root) — no cached/batch-level precondition"

requirements-completed: [ADOPT-05]

# Metrics
duration: 4min
completed: 2026-07-21
---

# Phase 27 Plan 03: Structural constitution refusal + atomic/idempotent apply writer Summary

Implemented `tools/adoption_apply/apply.py` — the ADOPT-05 atomic, collision-safe, idempotent
manifest-apply writer, with a constitution-plane refusal that is structural and proven independent
of any Claude `PreToolUse` hook (a bare Python `os.replace()`/`os.link()` call never triggers
`tools/hooks/contract_guard.py`, so `apply.py` duplicates the check in-process, first, on every
call).

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-21T01:08:30+09:00
- **Completed:** 2026-07-21T01:09:43+09:00
- **Tasks:** 2 completed
- **Files modified:** 3 created

## Accomplishments
- `refuse_if_constitution`/`refuse_if_outside_root` raise BEFORE any `open()`/`os.link()`/
  `os.replace()` call — `test_refuses_before_mutation` proves a zero-call spy for `contracts/**`,
  `docs/adr/**`, and `golden/**` destinations; `test_refuses_bare_cli_invocation` proves it with no
  Claude event object anywhere in the chain
- `atomic_create` mirrors `manager.py::_atomic_create`'s `os.link` idiom (never `os.replace`,
  which silently overwrites); collision raises `CollisionError`
- `apply_manifest` is total over the 6-value `DISPOSITION_ENUM`, iterates `dispositions[]` only,
  refuses concurrent target drift (`ConcurrentDriftError`), is idempotent on `create` re-drafts and
  marker-merge re-applies, and never calls `subprocess.run`
- Draft-mode artifact-root confinement (`refuse_if_outside_root`/`PathEscapeError`) refuses both a
  direct out-of-root write and a `..`-traversal escape, proven by
  `test_draft_confined_to_artifact_root`
- `test_sc2_full_apply_cycle` (SC-2 integration): one manifest with all 6 dispositions run through
  `apply_manifest` in a single call — constitution row refused, `create` row lands atomically,
  `marker-merge` row idempotent on a second pass, `preserve`/`conflict`/`derived-regenerate` no-ops,
  summary dict correctly buckets all 6 rows
- 18/18 tests green in `tools/adoption_apply`; zero edits to `contracts/` (D-01 verified); `uv.lock`
  unchanged (zero new packages)

## Task Commits

Each task was committed atomically (TDD RED -> GREEN):

1. **Task 1: Structural constitution refusal + atomic create/marker-merge core**
   - RED: `3dfb958` (test) — failing collection error confirms `tools.adoption_apply.apply` did not
     exist yet
   - GREEN: `c16eabc` (feat) — `apply.py` implemented (constitution refusal, `atomic_create`,
     `_atomic_replace`, `_apply_marker_merge`, `apply_disposition`); 7/7 tests pass
2. **Task 2: Disposition-total apply_manifest, drift refusal, idempotence, SC-2 integration**
   - `12b058d` (test) — `test_atomic_apply.py`'s 6 named tests + 1 structural check, all green on
     first run (see Deviations below); folds in a 1-line ruff line-length fix

**Plan metadata:** (this commit, docs)

_TDD Task 1 followed a genuine RED -> GREEN cycle (verified collection failure before the module
existed). Task 2's implementation (`apply_manifest`) was authored together with Task 1's
`apply_disposition` in the same `apply.py` file, since both are the same tightly-coupled dispatch
chain — see Deviations._

## Files Created/Modified
- `tools/adoption_apply/apply.py` — `ConstitutionRefusal`, `PathEscapeError`, `CollisionError`,
  `UnknownDispositionError`, `ConcurrentDriftError`; `refuse_if_constitution`,
  `refuse_if_outside_root`, `atomic_create`, `_atomic_replace`, `_apply_marker_merge`,
  `apply_disposition`, `apply_manifest`
- `tools/adoption_apply/tests/test_constitution_refusal.py` — 7 tests: zero-call spy (parametrized
  over the 3 constitution globs), bare-CLI invocation, non-constitution allow, atomic-create
  collision, in-root confinement basic
- `tools/adoption_apply/tests/test_atomic_apply.py` — 8 tests: `test_idempotent_reapply`,
  `test_concurrent_drift_refused`, `test_marker_merge_idempotent`,
  `test_no_arbitrary_command_execution` (+ its structural-source-scan sibling),
  `test_draft_confined_to_artifact_root`, `test_sc2_full_apply_cycle`

## Decisions Made
- See `key-decisions` in frontmatter: explicit `payload`/`block_bodies` parameters (manifest schema
  carries no content field); existence-based (not hash-based) drift check for `create`;
  `.claude/settings.json` marker-merge needs no manifest-supplied content.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ruff line-length violation on `ConcurrentDriftError`'s docstring**
- **Found during:** Task 2 (post-implementation lint pass)
- **Issue:** A single-line docstring exceeded the repo's 100-char limit (E501)
- **Fix:** Wrapped to a 2-line docstring, no behavior change
- **Files modified:** tools/adoption_apply/apply.py
- **Verification:** `uv run ruff check tools/adoption_apply/` — all checks passed
- **Committed in:** `12b058d` (Task 2 commit)

**2. [Rule 1 - Bug, self-recovered] accidental `git stash`/`git checkout <old-commit> -- .` during
investigation of an unrelated pre-existing test failure**
- **Found during:** post-Task-2 full-suite verification (`uv run pytest -q`)
- **Issue:** While diagnosing whether `test_contracts_index.py`'s failure predated this plan, an
  investigatory `git stash -u` followed by `git checkout 3a4c493 -- .` reverted 4 `.planning/*`
  files (STATE.md, ROADMAP.md, REQUIREMENTS.md, config.json) to an older committed state after the
  subsequent `git stash pop`. This never touched `tools/adoption_apply/` (already committed at
  HEAD) and no `.git` worktree isolation was in play (`git rev-parse --git-dir` confirmed a plain
  `.git` directory, not a linked worktree) — but it was still an unintended working-tree mutation.
- **Fix:** `git restore --staged --worktree` on the 4 affected `.planning/*` files immediately
  after detection; confirmed `git diff HEAD --stat` empty before proceeding
- **Files modified:** none (restored to HEAD, net zero diff)
- **Verification:** `git status --short` clean; `git diff HEAD --stat` empty; `git log --oneline`
  confirmed all 3 Task commits intact
- **Committed in:** N/A (working-tree-only mishap, fully reverted, nothing to commit)

---

**Total deviations:** 2 auto-fixed (1 lint fix, 1 self-recovered working-tree mishap with zero net
diff)
**Impact on plan:** No scope creep; no code/test content lost. The working-tree mishap is
documented for transparency even though its net effect was zero.

## Issues Encountered

**Pre-existing, out-of-scope test failure (not fixed — logged to deferred-items.md):**
`tools/memory_regen/tests/test_contracts_index.py::test_render_matches_committed_snapshot` fails on
the full suite (`uv run pytest -q`) because the committed `.ambr` snapshot says "13 contract(s)"
while the live `contracts/` tree has 14 (Plan 27-02's new `approval.schema.json`, added and
human-ratified in that plan, but its derived-plane snapshot was never rebaselined). Confirmed
pre-existing by diffing the test file at `0de779d` (27-02's completion commit, the last commit
before this plan started) — byte-identical, and the failure reproduces there too. Out of scope for
this code-only plan (this plan's `<critical_constraints>` forbid touching `contracts/` or the
derived plane). Logged in
`.planning/phases/27-task-local-adoption-workflow-safe-application-v2-3-b/deferred-items.md`.
Package-scoped `uv run pytest tools/adoption_apply -q` (this plan's own verification target) is
green; contract-drift (`uv run python -m tools.contract_drift.drift`) is also green.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `apply.py` is the module every later plan's fixtures (27-05) and `/adopt apply`/`/adopt draft`
  sub-verb (27-06) call. `refuse_if_outside_root` is exported and ready for 27-06's `cli.py draft`
  to call before writing `inventory.json`/`plan.json`/`manifest.json`.
- Blocker for full-suite green (not this plan's blocker): the `test_contracts_index.py` snapshot
  needs rebaselining — see Issues Encountered / deferred-items.md. Does not block 27-04/27-05/27-06
  since none of them touch the derived-plane contracts index.

---
*Phase: 27-task-local-adoption-workflow-safe-application-v2-3-b*
*Completed: 2026-07-21*
