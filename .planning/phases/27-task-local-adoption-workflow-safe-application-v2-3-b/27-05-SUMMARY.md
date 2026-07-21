---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
plan: 05
subsystem: testing
tags: [adoption, fixtures, pytest, sc-3, gen-04, polyglot, crlf-bom]

# Dependency graph
requires:
  - phase: 27-01
    provides: "tools/adoption_apply pyproject.toml + tests/conftest.py sys.path wiring"
  - phase: 27-03
    provides: "tools.adoption_apply.apply — apply_manifest/apply_disposition/atomic_create/refuse_if_constitution"
  - phase: 27-04
    provides: "tools.adoption_apply.approval (not directly exercised by this plan, but wave-3 sibling)"
provides:
  - "tools/adoption_apply/tests/fixtures/{polyglot-single,client-server,partial-collision-crlf}/ — 3 checked-in, domain-neutral, SC-3 fixture trees"
  - "tools/adoption_apply/tests/test_fixtures.py — one end-to-end test per fixture driving the real scan->plan->manifest->apply pipeline"
affects: [27-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "build_manifest(inventory, target, proposed_hashes, catalog=...) — custom catalog + proposed_hashes decouple a fixture-scoped destination set from the live harness_scan destination_catalog()/harness_proposed_hashes(), which enumerate/hash THIS checkout's own files (orthogonal to what a target-side fixture needs)."
    - "Fixture trees are copied into tmp_path before every pipeline run (shutil.copytree) — the checked-in fixture under tools/adoption_apply/tests/fixtures/ is never mutated by apply_manifest's writes."
    - "subprocess.run spied with wraps=subprocess.run (not stubbed) — proves 'no arbitrary command execution' by asserting every recorded call is one of scan.py's two fixed, target-scoped git invocations, rather than literal zero calls (scan.py legitimately shells out to git for enumeration/target_ref — see Deviations)."

key-files:
  created:
    - tools/adoption_apply/tests/fixtures/polyglot-single/{pyproject.toml,AGENTS.md,widget_a.py,widget_a_copy.py,widget_b.py,widget_b_modified.py}
    - tools/adoption_apply/tests/fixtures/client-server/member-a/AGENTS.md
    - tools/adoption_apply/tests/fixtures/client-server/{member-a,member-b}/** (copied from tests/fixtures/workspace/{member-a,member-b})
    - tools/adoption_apply/tests/fixtures/partial-collision-crlf/{AGENTS.md,widget_a.py,widget_a_copy.py,widget_a_modified.py,widget_b.py}
    - tools/adoption_apply/tests/test_fixtures.py
  modified: []

key-decisions:
  - "polyglot-single and partial-collision-crlf are NEW static checked-in trees (never tmp_minirepo-materialized) per 27-PATTERNS.md's explicit D-07 finding."
  - "client-server extends tests/fixtures/workspace/{member-a,member-b} verbatim (cp -r), adding one adoption-relevant AGENTS.md to member-a only."
  - "partial-collision-crlf's mandatory CRLF/BOM input is the target's AGENTS.md itself — AGENTS.md is MARKER_CAPABLE, so it always routes through harness_emit.merge.splice_managed_block, the ONE apply.py code path that calls _normalize on existing text; this makes the CRLF/BOM normalization assertion meaningful (traced through real production code) rather than an ad hoc bytes comparison."
  - "Each test builds its own small catalog + proposed_hashes dict (using build_manifest's existing catalog/proposed_hashes parameters) instead of the live destination_catalog()/harness_proposed_hashes(), which scan THIS harness checkout's real files — irrelevant to a target-side fixture's disposition mix."

patterns-established:
  - "SC-3 fixture-proof shape: _run_pipeline(target, catalog, proposed_hashes, payloads=, block_bodies=) → {inventory, plan, manifest, summary}, reused (never triplicated) across all 3 fixture tests."

requirements-completed: [ADOPT-07]

# Metrics
duration: 45min
completed: 2026-07-21
---

# Phase 27 Plan 05: SC-3 Adoption Fixtures + End-to-End Pipeline Tests Summary

**3 checked-in, domain-neutral fixture trees (polyglot-single, client-server, partial-collision-crlf) each driven end-to-end through the real `scan.build_inventory` → `plan.build_plan` → `destinations.build_manifest` → `apply.apply_manifest` pipeline, proving disposition-mix correctness, idempotent re-apply, per-member write confinement, and genuine CRLF/BOM normalization via `harness_emit.merge._normalize`.**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-07-21
- **Tasks:** 2/2 completed
- **Files modified:** 17 created (11 fixture files across 3 trees + 6 copied member-a/member-b files, plus 1 test file)

## Accomplishments

- Closed SC-3: all 3 required fixtures (single-repo polyglot, 2-repo client/server, partial-adoption/collision with CRLF/BOM) pass end to end through the unmodified, already-shipped scan/plan/destinations/apply pipeline.
- `polyglot-single` demonstrates the full disposition mix in one fixture: `preserve` (`pyproject.toml`, `widget_a.py` via a hash-equal companion), `conflict` (`widget_b.py` via a hash-different companion), `marker-merge` (`AGENTS.md`), and `create` (`widget_c.py`, no existing file).
- `client-server` extends the existing `tests/fixtures/workspace/{member-a,member-b}` two-member layout with one adoption-relevant addition (`AGENTS.md`) in `member-a` only, and proves structurally (via before/after tree snapshots) that an apply cycle run against one member never writes into the other.
- `partial-collision-crlf` is the sole fixture carrying genuine CRLF+BOM bytes (`AGENTS.md`, `\xef\xbb\xbf` prefix + `\r\n` line endings), routed through the marker-merge disposition so the post-apply bytes are asserted against `harness_emit.merge._normalize`'s own documented transform — not an invented expectation.
- Every fixture test also proves idempotence (byte-identical full-tree snapshot after a second identical pipeline run) and a subprocess-call proof (see Deviations for the exact assertion shape).

## Task Commits

1. **Task 1: polyglot-single + client-server fixture trees** - `7f6b508` (test)
2. **Task 2: partial-collision-crlf fixture + end-to-end test_fixtures.py** - `13df97e` (test)

_No separate feat/refactor commits — this plan is fixtures + tests only, per its own constraint (no production code under `tools/adoption_apply/{apply,batch,approval}.py` touched)._

## Files Created/Modified

- `tools/adoption_apply/tests/fixtures/polyglot-single/*` - static target tree: manifest (`pyproject.toml`), unmarked `AGENTS.md`, hash-equal `widget_a.py`/`widget_a_copy.py`, hash-different `widget_b.py`/`widget_b_modified.py`
- `tools/adoption_apply/tests/fixtures/client-server/{member-a,member-b}/*` - copied from `tests/fixtures/workspace/{member-a,member-b}`, plus a new `member-a/AGENTS.md`
- `tools/adoption_apply/tests/fixtures/partial-collision-crlf/*` - static target tree: BOM+CRLF `AGENTS.md`, hash-equal `widget_a.py`/`widget_a_copy.py`, hash-different companion `widget_a_modified.py`, `widget_b.py`
- `tools/adoption_apply/tests/test_fixtures.py` - `_run_pipeline` helper + `test_polyglot_single_end_to_end`, `test_client_server_end_to_end`, `test_partial_collision_crlf_end_to_end`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test-correctness clarification] "Zero subprocess.run calls" reinterpreted as "zero non-fixed-argv calls"**
- **Found during:** Task 2, while designing the subprocess-execution proof required by the plan's `<behavior>` block (d) and threat T-27-05-01.
- **Issue:** The plan's literal text ("a spy... records zero calls for any of the three fixtures") is unsatisfiable when driving the REAL, unmocked pipeline: `tools.adoption_scan.scan.enumerate_target`/`_target_ref` legitimately shell out to `git -C <target> ls-files ...` / `git -C <target> rev-parse HEAD` as part of their own already-shipped, already-tested behavior (unchanged by this plan) — those calls are unconditionally made by `scan.build_inventory`, so any spy patched via `unittest.mock.patch("subprocess.run", ...)` across the whole cycle necessarily records a nonzero `call_count`, even though `apply.py`/`batch.py`/`approval.py` themselves never call `subprocess` at all (already proven structurally by `test_atomic_apply.py::test_no_arbitrary_command_execution_structural`).
- **Fix:** `_assert_only_fixed_git_calls` spies with `wraps=subprocess.run` (the real implementation still runs, so `scan.py`'s enumeration/target-ref behavior is exercised faithfully, not stubbed) and asserts every recorded call's argv is exactly one of the two fixed, target-scoped shapes `["git", "-C", <target>, "ls-files", ...]` / `["git", "-C", <target>, "rev-parse", "HEAD"]` — i.e., proving no argv is ever derived from manifest/draft/scanned CONTENT, which is the actual security property T-27-05-01/ADOPT-07 ("임의 command 미실행") requires. This is a stronger, more faithful proof than a literal zero-call assertion would have been (which would have forced either mocking `scan.py` internals — violating the plan's own "never a mocked/stubbed subset of that chain" instruction — or silently making the assertion vacuous).
- **Files modified:** `tools/adoption_apply/tests/test_fixtures.py`
- **Commit:** `13df97e`

**2. [Rule 1 - Bug] `client-server` fixture's member-b `AGENTS.md` disposition corrected from `create` to `marker-merge`**
- **Found during:** Task 2, first test run (`test_client_server_end_to_end` failed with `AssertionError: assert 'marker-merge' == 'create'`).
- **Issue:** `AGENTS.md` is in `MARKER_CAPABLE`, and `tools.adoption_scan.destinations.disposition()`'s 7-step chain resolves `marker-merge` at step 4 — BEFORE step 5's existing-file check — so a `MARKER_CAPABLE` destination is ALWAYS `marker-merge`, regardless of whether the target file exists yet. My initial test comment/assertion assumed `create` for member-b's (absent) `AGENTS.md`; this was a test-authoring error, not a production-code bug (`apply.py`'s `_apply_marker_merge` correctly handles a non-existent target by treating `existing_text` as empty).
- **Fix:** Corrected the assertion and surrounding comment to `marker-merge`; added an assertion that the merged content lands correctly even when no prior file existed.
- **Files modified:** `tools/adoption_apply/tests/test_fixtures.py`
- **Commit:** `13df97e`

## Known Stubs

None — every fixture destination in every catalog is exercised by a real payload/block_body and asserted against real applied bytes.

## Threat Flags

None — this plan introduces no new network endpoint, auth path, or schema change. The fixture trees and test file operate entirely within the already-audited `scan`/`plan`/`destinations`/`apply` trust boundary; see the plan's own `<threat_model>` (T-27-05-01, T-27-05-02) for the mitigations this plan's tests were built to prove, both closed as described above.

## Issues Encountered

- Full-suite collateral: after committing `polyglot-single`/`client-server`'s fixture `AGENTS.md` files (Task 1) but before committing `partial-collision-crlf`/`test_fixtures.py` (still untracked at that point), `tools/adoption_scan/tests/test_dispositions.py::test_catalog_covers_real_nested_agents_md` failed — that Phase-26 structural test enumerates every on-disk `AGENTS.md` (tracked or not) and asserts it is a subset of `destination_catalog()`'s rows, but `destination_catalog()` deliberately filters to git-TRACKED files only (its own documented CR-01 fix, to keep the catalog reproducible on a clean checkout). An untracked-but-present `AGENTS.md` therefore fails that subset check by design. This resolved itself once Task 2's fixture files were committed (making them tracked) — no code change was needed, and the full suite is green at 1082/1082 (was 1079/1079 before this plan). Documented here for visibility, not as a deviation, since no plan file or production code was touched to resolve it.

## Verification Results

- `uv run pytest tools/adoption_apply/tests/test_fixtures.py -q` → 3 passed
- `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` → 18 passed (GEN-04 green)
- `uv run pytest tools/adoption_apply -q` → 28 passed
- `uv run pytest -q` (full suite) → 1082 passed (was 1079 before this plan; +3 new tests, 0 regressions)
- `uv run python -m tools.contract_drift.drift` → OK
- `uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude` → clean, no drift
- `git diff --exit-code uv.lock` → unchanged (no new package)

## Self-Check: PASSED

- FOUND: `tools/adoption_apply/tests/fixtures/polyglot-single/AGENTS.md`
- FOUND: `tools/adoption_apply/tests/fixtures/client-server/member-a/AGENTS.md`
- FOUND: `tools/adoption_apply/tests/fixtures/partial-collision-crlf/AGENTS.md`
- FOUND: `tools/adoption_apply/tests/test_fixtures.py`
- FOUND commit `7f6b508` in `git log --oneline --all`
- FOUND commit `13df97e` in `git log --oneline --all`
