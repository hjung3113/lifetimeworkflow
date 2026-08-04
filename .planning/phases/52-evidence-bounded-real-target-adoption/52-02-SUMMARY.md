---
phase: 52-evidence-bounded-real-target-adoption
plan: 02
subsystem: infra
tags: [adoption-scan, pnpm-workspace, json-schema, tdd, python]

# Dependency graph
requires:
  - phase: 52-01
    provides: "excludedEntry.excluded enum on contracts/harness/adoption/inventory.schema.json carrying non-workspace-member (9th value, additive)"
  - phase: 52-04
    provides: "clean pre-edit detect.py (its Task 3 asserted git diff --quiet on detect.py before this plan's only edit to it)"
provides:
  - "detect.parse_pnpm_workspace_globs(text) — pure, filesystem-free pnpm-workspace.yaml packages: block reader"
  - "detect.is_workspace_member(directory, globs) — pure membership predicate with traversal/absolute-glob rejection"
  - "tools/adoption_scan/tests/conftest.py::tmp_pnpm_workspace — second synthetic fixture (D-06's one exception)"
  - "scan.build_inventory scopes manifests/candidate_process_boundaries to declared pnpm workspace members, recording non-members as excluded (non-workspace-member)"
affects: [53]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure text-in parser mirroring detect_dependencies' precedent: workspace manifest text is read once in scan.py and handed to a filesystem-free detect.py function — never read from disk inside detect.py itself."
    - "D-10 additive branch: a None sentinel (workspace_globs) short-circuits the new scoping branch entirely when no workspace manifest exists, keeping the old code path byte-for-byte reachable."

key-files:
  created: []
  modified:
    - tools/adoption_scan/detect.py
    - tools/adoption_scan/scan.py
    - tools/adoption_scan/tests/conftest.py
    - tools/adoption_scan/tests/test_detect.py
    - tools/adoption_scan/tests/test_scan_exclusions.py

key-decisions:
  - "pnpm-workspace.yaml is deliberately NOT registered in _MANIFEST_KIND_BY_NAME (interfaces section's explicit deviation from D-07's literal wording) — it is taught as its own module-level constant (PNPM_WORKSPACE_MANIFEST) plus a dedicated pure parser/predicate pair instead, since registering it there would emit a 6th manifest record and a duplicate root boundary, defeating RTA-02's exactly-five-members."
  - "Two of the plan's proposed test negative controls (a `../outside/*` traversal glob against a length-mismatched directory, and a bare malformed-YAML string) turned out to be structurally unreachable — the len(glob_parts) != len(directory_parts) guard already rejects them regardless of the explicit `..`/try-except logic, which is this repo's own named signature defect (checks that cannot fail). Replaced with a segment-count-matched traversal case and a None-input case that genuinely exercise the guarded code, confirmed by observed-RED-then-reverted mutation."

requirements-completed: [RTA-02, OBS-02]

# Metrics
duration: ~45min active work
completed: 2026-08-01
---

# Phase 52 Plan 02: pnpm Workspace Member Scoping (OBS-D-01) Summary

**Discovery now scopes `manifests`/`candidate_process_boundaries` to a target's declared pnpm `packages:` globs, excluding a non-member manifest as `non-workspace-member` — the no-workspace-manifest path stays byte-identical, and the REFUTED-OBS-03 dependency function is provably untouched.**

## Performance

- **Tasks:** 3/3 completed
- **Files modified:** 5 (0 created, 5 modified)

## Accomplishments

- `detect.py` gained a pure, filesystem-free `parse_pnpm_workspace_globs(text)` (narrow line-based `packages:`-block reader, no third-party YAML dependency) and `is_workspace_member(directory, globs)` (per-path-segment `fnmatch` match; workspace root always a member; absolute and `..`-containing globs contribute no members).
- `pnpm-workspace.yaml` was deliberately NOT added to `_MANIFEST_KIND_BY_NAME` — a comment there points at the new `PNPM_WORKSPACE_MANIFEST` constant and explains why (registering it there would emit a 6th manifest record + duplicate root boundary).
- `_dependencies_from_package_json` (the REFUTED OBS-03 site, `detect.py:273`) is provably untouched: its source-digest, re-extracted with `ast.get_source_segment`, equals the plan-time pin `36f3253f152f5b0b7b475499a56bfe9f84128bb89ec8a7c72af5642dc12e76b6`.
- `tools/adoption_scan/tests/conftest.py` gained a second, additive fixture (`tmp_pnpm_workspace`, neutral widget/source/sink vocabulary) — a pnpm workspace with 4 declared members + root + 1 non-member manifest under `docs/design-prototype/`. `tmp_minirepo` is untouched; its committed `test_snapshots.py` syrupy snapshot is unchanged (`git diff --quiet` on `__snapshots__/` succeeds).
- `scan.build_inventory` reads the workspace manifest text once (never inside `detect.py`), and — only when `classify_exclusions` already returned `None` for a recognized manifest name — excludes a non-member manifest as `{"path", "size", "excluded": "non-workspace-member"}`, removing it from both `included` and (transitively, via `detect_manifests`) `manifests`/`candidate_process_boundaries`.
- Against `tmp_pnpm_workspace`, `manifests` and `candidate_process_boundaries` contain exactly the five declared members (asserted by literal set equality, not count), and the one non-member manifest is excluded with the D-20-ratified reason, validated against Plan 01's live schema.
- Against `tmp_minirepo` (no `pnpm-workspace.yaml`), output is byte-identical to the pre-Task-3 baseline (captured SHA-256 digest `00d6d50a…`), and no `non-workspace-member` entry ever appears.
- Full suite green: **1023 passed** (up from 1006 at wave start).

## Task Commits

Each task was committed atomically:

1. **Task 1: Pure pnpm-workspace parsing and membership predicate in detect.py** — `e79f9c7` (feat) — `tools/adoption_scan/detect.py`, `tools/adoption_scan/tests/test_detect.py`
2. **Task 2: Synthetic pnpm workspace fixture (neutral vocabulary, second fixture)** — `491b799` (feat) — `tools/adoption_scan/tests/conftest.py`
3. **Task 3: Wire workspace scoping into build_inventory and record non-members as excluded** — `ba973b8` (feat) — `tools/adoption_scan/scan.py`, `tools/adoption_scan/tests/test_scan_exclusions.py`

## /contract-check / drift evidence

No contract was touched by this plan (the enum value it consumes was ratified in 52-01). `uv run python -m tools.contract_drift.drift` → `contract-drift: OK — live manifest matches the committed baseline.` (exit 0), confirming this plan added no contract surface.

## Files Created/Modified

- `tools/adoption_scan/detect.py` — `PNPM_WORKSPACE_MANIFEST` constant, `parse_pnpm_workspace_globs`, `is_workspace_member`; `_MANIFEST_KIND_BY_NAME` gains only an explanatory comment (no new key); `_dependencies_from_package_json` untouched (pinned)
- `tools/adoption_scan/scan.py` — `_manifest_kind_for_name` helper (reuses `detect._MANIFEST_KIND_BY_NAME` / `.csproj` rule); `build_inventory` reads the workspace manifest text once and scopes non-member manifests out with the new exclusion reason
- `tools/adoption_scan/tests/conftest.py` — `tmp_pnpm_workspace` fixture (second synthetic tree, D-06's one documented exception)
- `tools/adoption_scan/tests/test_detect.py` — parser/predicate unit tests including hostile-input negative controls
- `tools/adoption_scan/tests/test_scan_exclusions.py` — member-count, non-member-exclusion, D-10 byte-identity, security-precedence, traversal-escape, non-manifest-file-stays-included, and schema-conformance tests

## Decisions Made

See `key-decisions` in frontmatter above (the `_MANIFEST_KIND_BY_NAME` non-registration and the negative-control redesign).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two of the plan's own suggested negative-control test shapes were structurally unreachable ("checks that cannot fail")**
- **Found during:** Task 1, while running the acceptance-criteria mutation checks
- **Issue:** The plan's traversal negative control (`is_workspace_member("outside", ["../outside/*"])`) and its malformed-text negative control (bare strings like `""`, `"not: yaml..."`) both already pass even WITHOUT the specific guard they were meant to exercise: the `len(glob_parts) != len(directory_parts)` segment-count guard rejects the traversal case regardless of the explicit `..`-rejection, and none of the plan's suggested malformed strings ever reach a code path capable of raising (the function's body is pure string manipulation with no operation that can throw on any `str` input), so the wrapping `try`/`except` was never actually exercised by those inputs either.
- **Fix:** Kept the plan's original assertions (still useful regression coverage) and ADDED one genuinely discriminating case to each test: a segment-count-MATCHED traversal glob (`"sub/../sibling/*"` against directory `"sub/../sibling/foo"` — 4 segments on each side, every non-`".."` segment matching) for the traversal control, and a non-`str` (`None`) input for the malformed-text control (this reaches `.splitlines()` and raises `AttributeError` with no `try`/`except`). Both new assertions were verified by applying the corresponding mutation (removing the `..`-rejection; removing the `try`/`except`) in a scratch copy, observing the test go RED with the exact expected failure, then reverting.
- **Files modified:** `tools/adoption_scan/tests/test_detect.py`
- **Verification:** Mutation 1 (traversal): observed `AssertionError: assert True is False` at the new assertion when the `..`-rejection was removed; reverted, test green. Mutation 2 (try/except): observed `AttributeError: 'NoneType' object has no attribute 'splitlines'` at `text.splitlines()` when the wrapping `try`/`except` was removed; reverted, test green.
- **Committed in:** `e79f9c7` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — test-quality bug: two acceptance-criteria negative controls as literally worded would not have caught the regression they claimed to guard against).
**Impact on plan:** No scope creep — the fix strengthened the plan's own mutation-testing requirement rather than weakening it. Both original assertions were kept; the added assertions are the ones that actually red on the targeted mutation.

## Issues Encountered

None beyond the negative-control redesign above. Every other mutation check named in the plan's acceptance criteria (the OBS-03 pin, the B-1 no-filesystem-access gate, the Task-3 non-member-exclusion branch, and the Task-3 security-precedence branch-order) was observed RED on the corresponding mutation and GREEN after revert, exactly as specified — no further surprises.

### Mutation checks performed (observed RED → reverted)

1. **OBS-03 pin (Task 1):** renamed a local inside `_dependencies_from_package_json` in a scratch copy → digest became `5e92b59657b2fa7e71492b6feee69714021fd8c308b1d9be43ff9cb9aa45afa2` (mismatch vs pin) → reverted, digest restored to `36f3253f152f5b0b7b475499a56bfe9f84128bb89ec8a7c72af5642dc12e76b6`.
2. **B-1 no-filesystem-access gate (Task 1):** added a throwaway `Path("x")` line → `grep -nE '\bopen\(|\bPath\(|read_text|read_bytes'` matched (exit 0) → reverted, no match (exit 1).
3. **Traversal rejection (Task 1):** removed the `any(part == ".." for part in glob_parts)` check → `test_workspace_member_traversal_glob_contributes_no_members` failed with `AssertionError: assert True is False` on the segment-count-matched case → reverted, test green.
4. **Malformed-input try/except (Task 1):** replaced `try:`/`except Exception: return []` with a bare `if True:` block → `test_pnpm_workspace_globs_malformed_or_empty_returns_empty_list_never_raises` failed with `AttributeError: 'NoneType' object has no attribute 'splitlines'` → reverted, test green.
5. **Non-member-exclusion branch (Task 3):** deleted the entire `workspace_globs is not None` branch in `build_inventory` → `test_pnpm_non_member_manifest_excluded_and_absent_from_included_and_manifests` failed (`docs/design-prototype/package.json` not found in `excluded`) → reverted, test green.
6. **Security-precedence branch order (Task 3):** swapped the non-member check to run BEFORE `classify_exclusions` → `test_pnpm_security_precedence_preserved_over_non_workspace_member` failed (`'non-workspace-member' == 'vendored'` assertion, got `non-workspace-member`) → reverted, test green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- OBS-D-01 is repaired at the source (RTA-02): a real target's inventory now contains exactly its declared workspace members plus root, with any stray manifest visible as `non-workspace-member` rather than silently enumerated as a 6th candidate process boundary.
- Wave 3 (this plan, alone) closes Phase 52's wave sequence: 52-01 (contract), 52-03/52-04 (wave 2), 52-02 (wave 3, this plan) are all complete. The phase's remaining work (per `52-CONTEXT.md` D-05) is the fresh isolated-worktree discover→draft→apply run against the real target, proving RTA-01..04 end-to-end — not part of this plan's scope.
- Full suite green at 1023 passed; no contract touched; `contracts/` plane untouched by this plan as instructed.

---
*Phase: 52-evidence-bounded-real-target-adoption*
*Completed: 2026-08-01*

## Self-Check: PASSED

All claimed files exist (`tools/adoption_scan/detect.py`, `tools/adoption_scan/scan.py`,
`tools/adoption_scan/tests/conftest.py`, `tools/adoption_scan/tests/test_detect.py`,
`tools/adoption_scan/tests/test_scan_exclusions.py`, this summary) and all three claimed task
commit hashes (`e79f9c7`, `491b799`, `ba973b8`) are present in `git log --oneline --all`.
