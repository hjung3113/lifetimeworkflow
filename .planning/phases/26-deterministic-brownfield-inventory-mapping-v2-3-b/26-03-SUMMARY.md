---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
plan: 03
subsystem: tools
tags: [adoption-scan, evidence-classification, disposition-chain, cli, deterministic-scanning, python]

# Dependency graph
requires:
  - phase: 26-01
    provides: "contracts/harness/adoption/{plan,manifest}.schema.json — the ratified plan/manifest artifact shapes this plan's build_plan()/build_manifest() output validates against with zero errors"
  - phase: 26-02
    provides: "tools/adoption_scan/{scan,detect}.py + tests/conftest.py::tmp_minirepo — build_inventory()/enumerate_target()/scan._dump() this plan imports and reuses verbatim, and the single D-06 fixture this plan's tests build on"
provides:
  - "tools/adoption_scan/destinations.py — destination_catalog() (40-row Authoritative Harness Destination Catalog) + disposition() (the total 7-step D-03/D-04 rule chain) + build_manifest()"
  - "tools/adoption_scan/plan.py — classify() (D-02 evidence ladder) + generate_questions() (D-05 content-derived question records) + generate_relationship_candidates() (adoption/ namespace, never-invented-authority) + build_plan()"
  - "tools/adoption_scan/cli.py + __main__.py — python -m tools.adoption_scan: scan -> plan -> destinations -> schema-validate -> write 3 artifacts to a required, target-external --out (D-11)"
affects: [27-brownfield-adoption-apply]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Total disposition rule chain as a single ordered function (7 steps, each an early return) — proven total by a property test iterating all 40 catalog rows, never a partial match/fallthrough"
    - "Evidence classification ladder enforced structurally in classify(): a manifest's own observed classification is mirrored only when the proposal is a DIRECT restatement (member); candidate_process_boundaries' inferred classification is mirrored verbatim; every placement/canonical-command decision (docs-destination, agents-boundary, test-command) is unknown by construction, never auto-promoted"
    - "D-05 content-derived question ids (Q-<sha256(kind+NUL+target)[:12]>) — stable across re-runs, immune to list-position renumbering"
    - "Never-invented-authority structural guard in generate_relationship_candidates() — gates on the proposal's OWN classification field only, with a redundant '?' sentinel check even if a proposal is ever misclassified upstream"
    - "cli.py validates all 3 documents against their ratified schemas BEFORE any write — a schema-validation failure returns exit 1 with zero bytes written, never a partial artifact set"
    - "D-11 --out confinement: symmetric containment check (equal, --out inside --target, --target inside --out) all refuse with exit 2 and zero writes, checked before scan.build_inventory() ever runs"

key-files:
  created:
    - tools/adoption_scan/destinations.py
    - tools/adoption_scan/plan.py
    - tools/adoption_scan/cli.py
    - tools/adoption_scan/__main__.py
    - tools/adoption_scan/tests/test_dispositions.py
    - tools/adoption_scan/tests/test_plan_classification.py
    - tools/adoption_scan/tests/test_schema_conformance.py
    - tools/adoption_scan/tests/test_determinism.py
    - tools/adoption_scan/tests/test_snapshots.py
    - tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr
  modified: []

key-decisions:
  - "Catalog row destinations use concrete representative paths (e.g. 'contracts/harness/adoption/inventory.schema.json' for row 1, '.claude/get-shit-done/README.md' for row 40) rather than the research table's literal glob-pattern/prose strings, so disposition() can be exercised directly and honestly against every row via is_gsd_owned()/resolve_path() without a synthetic-string special case"
  - "languages is deliberately NOT walked into a proposalRecord by classify() — no kind in the ADOPT-02 category list (member/component/relationship/contract-candidate/test-command/docs-destination/agents-boundary) corresponds to raw language presence; multi-language signal is instead surfaced directly as an ambiguous-language question from inventory[\"languages\"], independent of the proposal pipeline, matching the plan's own phrasing ('for every ... ambiguous-language case the inventory recorded')"
  - "excluded-file and collision question kinds are defined in the ratified questionRecord kind enum but NOT exercised by this wave's generate_questions() — an excluded entry structurally carries no sha256 anywhere in the inventory (D-10), and plan.py never re-touches the target filesystem to compute one (which would also violate Pitfall 7: never fingerprint a low-entropy secret via its hash), so there is no valid evidenceRef plan.py could honestly attach to an excluded-secret file today. Left for a future wave when either the evidence contract changes or a different evidence source is identified. Not required by any of the plan's four named Task 2 tests."
  - "generate_relationship_candidates()/generate_questions() 'relationship' proposal handling uses an internal target-string convention ('<contract>::<authority-or-?>-><dependent>') documented in plan.py's own module docstring — the current inventory shape carries no relationship/contract signal at all (ADOPT-01 scope), so classify() never manufactures a 'relationship' proposal from a real scan; the never-invented-authority gating logic is proven directly by unit tests feeding hand-built proposal lists, ready for a future inventory extension"
  - "cli.py's proposed-hash map is {included_entry.path: included_entry.sha256} — i.e. the scanned target's OWN included files are treated as the proposed content at the SAME relative destination path, which is the only proposed-content source available without touching a second (destination) tree in this phase's scope"

patterns-established:
  - "MARKER_CAPABLE / DERIVED_GLOBS / DISPOSITION_ENUM live in destinations.py as the single source other tools (Phase 27) should import, never retype"
  - "The 40-row catalog + disposition() pair is the reusable totality-proof pattern for any future 'assign exactly one of N outcomes to every known destination' requirement in this repo"

requirements-completed: [ADOPT-02, ADOPT-03]

# Metrics
duration: ~90min
completed: 2026-07-19
---

# Phase 26 Plan 03: Adoption Mapping Plan + Disposition Manifest + CLI Summary

**`tools/adoption_scan/{destinations,plan,cli}.py` complete the ADOPT-01/02/03 pipeline: a total 7-step disposition chain over the 40-row Authoritative Harness Destination Catalog, a D-02 evidence-classification ladder with D-05 content-derived questions and never-invented-authority relationship candidates, and a `python -m tools.adoption_scan` CLI proven byte-identical across a double-run, a seeded-shuffle, and a committed syrupy snapshot.**

## Performance

- **Duration:** ~90 min
- **Started:** 2026-07-19T11:10:00Z (approx, session start)
- **Completed:** 2026-07-19T12:40:43Z
- **Tasks:** 3 of 3
- **Files modified:** 10 (10 created, 0 modified net — one same-plan lint fix to a Task-1-created file)

## Accomplishments

- `destinations.py`: the 40-row Authoritative Harness Destination Catalog (`destination_catalog()`) and the total, ordered 7-step disposition chain (`disposition()`) — GSD-owned lanes excluded from resolution (never dispositioned), constitution-plane paths always win over hash-equal/preserve, marker-merge scoped to exactly `AGENTS.md`/`CLAUDE.md`/`.claude/settings.json`, `libs/normalize-spec.md` special-cased to `human-ratification-required` per D-04.
- `plan.py`: `classify()` walks manifests + the four surface arrays into `proposalRecord`-shaped entries following the D-02 evidence ladder exactly (manifest -> member/observed as a direct restatement; candidate process boundary -> component/inferred mirrored verbatim; doc/AGENTS/test-command placement decisions -> unknown by construction, never auto-promoted). `generate_questions()` emits D-05 content-derived, stable, deterministically-ordered question records. `generate_relationship_candidates()` structurally guarantees a relationship candidate is emitted ONLY when the source proposal's own classification is `observed`/`inferred` — an unresolved authority is always a question with a schema-incomplete `candidate` (no `authority` key), proven to never validate against the ratified `relationship.schema.json`.
- `cli.py` + `__main__.py`: `python -m tools.adoption_scan --target <dir> --out <dir>` wires `scan -> plan -> destinations` into three artifacts, validates all three against their ratified schemas BEFORE any write, refuses (exit 2, zero writes) when `--out` is missing, equal to `--target`, resolves inside `--target`, or resolves as an ancestor containing `--target` (D-11), and refuses when `--target` doesn't exist.
- Full pipeline proven byte-identical across a double independent run into two `tmp_path` output directories (never `git diff`), a seeded-shuffled (seed 1337) enumeration order, and a committed syrupy snapshot of all three artifacts rendered over the D-06 fixture.
- Verified end-to-end with a real smoke invocation against a scratch target tree (`python -m tools.adoption_scan --target /tmp/adopt_smoke_target --out /tmp/adopt_smoke_out`) producing valid `inventory.json`/`plan.json`/`manifest.json`.
- **Full-suite gate (per this plan's own `<definition_of_done>`):** `uv run pytest -q` -> **1003 passed** (982 baseline + 21 new, 0 failed). `uv run python -m tools.contract_drift.drift` -> OK. `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` (GEN-04 guard) -> 18 passed. `uv sync --all-packages && git diff --exit-code uv.lock` -> clean (no lockfile mutation). `uv run ruff check tools/adoption_scan` -> all checks passed.

## Task Commits

Each task was committed atomically:

1. **Task 1: destinations.py — 40-row catalog + total disposition chain** - `6e5c247` (feat)
2. **Task 2: plan.py — evidence ladder, D-05 questions, relationship candidates** - `dd8a2f3` (feat)
3. **Task 3: cli.py — wire the pipeline, write + validate 3 artifacts** - `51ce7f8` (feat)

## Files Created/Modified

- `tools/adoption_scan/destinations.py` - `destination_catalog()` / `disposition()` / `build_manifest()` / `MARKER_CAPABLE` / `DERIVED_GLOBS` / `DISPOSITION_ENUM`
- `tools/adoption_scan/plan.py` - `classify()` / `generate_questions()` / `generate_relationship_candidates()` / `build_plan()`
- `tools/adoption_scan/cli.py` - `main(argv) -> int`, argparse entrypoint with `--target`/`--out`/`--max-file-bytes`
- `tools/adoption_scan/__main__.py` - 3-line shim
- `tools/adoption_scan/tests/test_dispositions.py` - totality, each-of-6-reachable, constitution-always-wins, normalize-spec special case, collision rule (widget_a/widget_b/widget_a_modified), exact-3 marker-capable set, GSD-exclusion (7 tests)
- `tools/adoption_scan/tests/test_plan_classification.py` - every-entry-classified, unresolved-ownership-becomes-question, question-shape-and-ordering, relationship-candidates-validate, classify-over-real-fixture (5 tests)
- `tools/adoption_scan/tests/test_schema_conformance.py` - all-3-artifacts-validate + 5 `--out`/`--target` refusal cases (6 tests)
- `tools/adoption_scan/tests/test_determinism.py` - double-run + seeded-shuffle byte-identical (2 tests)
- `tools/adoption_scan/tests/test_snapshots.py` - committed syrupy snapshot (1 test)
- `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr` - the committed determinism reference

## Decisions Made

See `key-decisions` in frontmatter for the five substantive design decisions this plan required (catalog row representative paths, languages-not-a-proposal-kind, excluded-file/collision scoping, the internal relationship target-string convention, and the proposed-hash map source). All are documented above with rationale; none is a deviation from the plan's `<action>` blocks — the plan's own `<behavior>` prose left these specific wiring choices to implementation discretion (e.g. "recommended" question kind enum, "Task 2 tests" list only 4 named tests, none touching excluded-file/collision).

## Deviations from Plan

**1. [Rule 1 - lint] Wrapped a docstring line in destinations.py exceeding the 100-column ruff limit.**
- **Found during:** Task 3, pre-commit `ruff check` sweep.
- **Issue:** `destination_catalog()`'s docstring line 246 was 101 characters, one over `E501`.
- **Fix:** Wrapped the sentence across two lines, no content change.
- **Files modified:** `tools/adoption_scan/destinations.py` (Task 1's file, fixed in the Task 3 commit since that's when the full-package ruff sweep ran).
- **Verification:** `uv run ruff check tools/adoption_scan` -> all checks passed; `uv run pytest tools/adoption_scan -q` -> unchanged 41 passed.
- **Committed in:** `51ce7f8` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 Rule 1 lint fix, no behavior change)
**Impact on plan:** Cosmetic only. No scope creep.

## Issues Encountered

None beyond the design-discretion points already documented in Decisions Made. All three tasks' own `<verify>` commands passed on first attempt after implementation; the plan's own `<verify>` block for Task 3 (full package suite + GEN-04 guard + `uv sync` + lockfile diff) and this plan's `<definition_of_done>` full-suite requirement both passed on first run with no red tests to fix.

## Next Phase Readiness

- Phase 26 (all 3 plans: 26-01 constitution schemas, 26-02 scan/detect core, 26-03 plan/destinations/cli) is now complete. `python -m tools.adoption_scan --target <dir> --out <dir>` is a fully working, read-only, deterministic brownfield inventory + mapping-plan + disposition-manifest pipeline.
- **For Phase 27 (brownfield-adoption-apply):** the questionRecord `kind` enum reserves `excluded-file` and `collision` for a future wave — this plan intentionally left them unexercised (see Decisions Made) because the current inventory shape structurally denies a valid `sha256` for an excluded file, and fabricating one would violate D-10/Pitfall 7. Phase 27's task-batch design should account for this: either extend the inventory to carry a legitimate evidence source for excluded/collision questions, or accept these two kinds stay dormant until then.
- **For Phase 27:** `plan.py`'s "relationship" proposal machinery (never-invented-authority gating, `adoption/<contract>/<authority>-><dependent>` id namespace) is implemented and unit-tested but currently dormant in real scans (no relationship/contract signal exists in the ADOPT-01 inventory shape today). If Phase 27 needs relationship detection from a brownfield target, extending `detect.py`/`scan.py` to emit that signal is the natural next step; `plan.py`'s consuming logic is already in place and gated correctly.
- Full test suite: **1003 passed, 0 failed** (not a subset). `contract-drift` OK. No contract or derived-plane files were touched by this plan (Task 3 only added new tool/test files), so there is no `stale-derived` risk to re-verify.
- No blockers carried forward from this plan or this phase.

---
*Phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b*
*Completed: 2026-07-19*

## Self-Check: PASSED

- FOUND: tools/adoption_scan/destinations.py
- FOUND: tools/adoption_scan/plan.py
- FOUND: tools/adoption_scan/cli.py
- FOUND: tools/adoption_scan/__main__.py
- FOUND: tools/adoption_scan/tests/test_dispositions.py
- FOUND: tools/adoption_scan/tests/test_plan_classification.py
- FOUND: tools/adoption_scan/tests/test_schema_conformance.py
- FOUND: tools/adoption_scan/tests/test_determinism.py
- FOUND: tools/adoption_scan/tests/test_snapshots.py
- FOUND: tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr
- FOUND: commit 6e5c247 (Task 1)
- FOUND: commit dd8a2f3 (Task 2)
- FOUND: commit 51ce7f8 (Task 3)
- CONFIRMED: `uv run pytest -q` -> 1003 passed, 0 failed (full suite)
- CONFIRMED: `uv run python -m tools.contract_drift.drift` -> OK
