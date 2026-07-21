---
phase: 24-contract-relationship-vocabulary-compatibility-v2-3-a
plan: 01
subsystem: api
tags: [json-schema, draft-2020-12, contracts, topology, contract-drift, jsonschema]

# Dependency graph
requires:
  - phase: 18-task-control
    provides: "Draft202012Validator fixture-test idiom + attestation/task per-record schema style"
  - phase: 05-despecialization
    provides: "GEN-04 core→example guard; contract-hash/drift JCS manifest gate"
provides:
  - "contracts/harness/topology/relationship.schema.json — ratified per-record contract-relationship vocabulary (TOPO-01)"
  - "Positive/negative relationship fixtures + Draft202012Validator test coverage"
  - "Rebaselined contract-hash manifest tracking the new schema (drift green)"
affects: [phase-25-compiler, phase-26-brownfield-mapper, contract-graph]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-record topology schema: shape/cardinality only (exactly-one authority scalar, >=1 unique dependents array), no graph resolution"
    - "Fixture plane lives in tools/harness_config/tests/fixtures (TEST plane) not contracts/, keeping GEN-04 green"

key-files:
  created:
    - contracts/harness/topology/relationship.schema.json
    - tools/harness_config/tests/fixtures/relationships/valid/cases.json
    - tools/harness_config/tests/fixtures/relationships/negative/cases.json
    - tools/harness_config/tests/test_relationship_schema.py
    - docs/reference/relationship.md
  modified:
    - contracts/.hashes/manifest.json
    - .memory/derived/contracts-index.md
    - docs/reference/handoff.md
    - docs/reference/task.md
    - tools/docs_sync/tests/test_docs_sync_determinism.py

key-decisions:
  - "D-01: record-level schema (single relationship object), NOT a graph-document array wrapper — array consistency deferred to Phase 25"
  - "D-02: endpoints are bare stable-id strings (authority scalar, dependents non-empty unique array); endpoint resolution deferred to Phase 25"
  - "Ratification = CODEOWNERS-gated rebaseline of contracts/.hashes/manifest.json (machines gate via drift tool, humans ratify at review)"

patterns-established:
  - "Topology contracts mirror task-control per-record style ($schema/$id path-mirror/additionalProperties:false/required)"
  - "New core schema requires holistic derived-plane regen (docs/reference + contracts-index) + manifest rebaseline"

requirements-completed: [TOPO-01]

# Metrics
duration: 18min
completed: 2026-07-19
---

# Phase 24 Plan 01: Contract-Relationship Record Schema Summary

**Ratified Draft 2020-12 per-record relationship schema (`contracts/harness/topology/relationship.schema.json`) enforcing exactly-one authority + one-or-more unique dependents, proven by a Draft202012Validator fixture suite and locked into the contract-hash baseline (drift green).**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-07-19
- **Tasks:** 3
- **Files modified/created:** 11

## Accomplishments
- Authored the constitution-plane relationship vocabulary the rest of v2.3 Theme A consumes — record shape/cardinality only, no graph resolution (D-01/D-02 honored).
- Proved the schema with 1 schema-validity + 3 positive + 6 negative (one per violated constraint) parametrized tests, all domain-neutral so GEN-04 stays clean.
- Rebaselined the JCS SHA-256 manifest (9→10 docs, single key added) so `contract-drift` reports OK with the new schema tracked — the CODEOWNERS-gated ratification checkpoint.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author the ratified relationship record schema** — `7e3630d` (feat)
2. **Task 2: Positive/negative fixtures + schema validation tests** — `7f8d6d7` (test)
3. **Task 3: Ratify — rebaseline contract-hash manifest** — `2a5c234` (chore)

**Deviation (derived-plane regen):** `f1d97b2` (docs)

## Files Created/Modified
- `contracts/harness/topology/relationship.schema.json` — per-record relationship schema (id/contract/authority/dependents + optional kind/labels)
- `tools/harness_config/tests/fixtures/relationships/{valid,negative}/cases.json` — domain-neutral positive/negative fixture instances
- `tools/harness_config/tests/test_relationship_schema.py` — Draft202012Validator parametrized coverage
- `contracts/.hashes/manifest.json` — rebaselined baseline including the new schema
- `docs/reference/relationship.md` — machine-generated reference page (new)
- `.memory/derived/contracts-index.md`, `docs/reference/{handoff,task}.md` — regenerated derived plane
- `tools/docs_sync/tests/test_docs_sync_determinism.py` (+ two `.ambr` snapshots) — EXPECTED_PAGES gains `relationship`; determinism snapshots refreshed

## Decisions Made
- Kept the schema strictly record-level: `authority` is a scalar string (enforces exactly-one), `dependents` is `minItems:1 + uniqueItems:true` (enforces one-or-more, no duplicates). No `components`/`members`/endpoint-existence concept (verified absent) — that is Phase 25's compiler.
- Fixtures placed in the TEST plane (`tools/harness_config/tests/fixtures/`), never under `contracts/`, so the GEN-04 core→example guard stays green.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Regenerated the committed-derived plane for the new schema**
- **Found during:** Post-Task-3 full-suite verification
- **Issue:** Adding a core schema makes the committed-derived plane stale — `docs_sync` and `contracts_index` auto-discover all `contracts/**/*.schema.json`, so a `relationship.md` page + contracts-index row were missing and the hardcoded `EXPECTED_PAGES` set + two determinism `.ambr` snapshots no longer matched. The plan's `files_modified` did not anticipate the derived-plane fan-out.
- **Fix:** Ran `tools.docs_sync.generate` + `tools.memory_regen.contracts_index` (machine regen, never hand-edit), added `relationship` to `EXPECTED_PAGES`, and refreshed the two `docs_sync`/`contracts_index` determinism snapshots (these are determinism references, distinct from the emit projected-tree gate STATE.md warns against touching).
- **Note:** The regen is holistic, so it also swept in **pre-existing** stale drift in `docs/reference/handoff.md` and `docs/reference/task.md` (their committed pages lagged their schemas at the base commit `90166dd`, independent of this plan — the same class of derived debt STATE.md documents). Verified those 4 snapshot tests already failed at `90166dd` before any Task-1 change.
- **Verification:** `uv run pytest -q` → 914 passed (was 4 pre-existing failures).
- **Committed in:** `f1d97b2`

**2. [Rule 1 - Bug] Plan `<verify>` grep pattern is malformed (deliverable unaffected)**
- **Found during:** Task 1 verification
- **Issue:** The plan's `<verify><automated>` uses `grep -q '"draft/2020-12/schema"'` — a leading `"` immediately before `draft` that no `$schema` URL in the repo carries (it fails even against `attestation.schema.json`, the exemplar the plan says to mirror).
- **Fix:** None needed to the deliverable. The authoritative `<acceptance_criteria>` requires the exact string `"$schema": "https://json-schema.org/draft/2020-12/schema"`, which the schema contains (verified programmatically). Documented the malformed verify command for the plan-checker.
- **Verification:** All Task-1 acceptance criteria pass via a Python assertion harness + `Draft202012Validator.check_schema`.
- **Committed in:** n/a (no deliverable change)

---

**Total deviations:** 2 (1 Rule-3 blocking derived regen, 1 Rule-1 plan-tooling bug with no deliverable impact)
**Impact on plan:** Rule-3 regen was required to keep the suite/stale-derived gate green with the new schema; it incidentally cleaned pre-existing derived drift. No scope creep into contracts logic. All plan success criteria met.

## Issues Encountered
- Full suite showed 4 failures after the schema landed; root-caused as pre-existing derived-plane debt (present at base commit) compounded by the new schema. Resolved via holistic machine-regeneration (see Deviation 1).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `relationship.schema.json` is the ratified vocabulary Phase 25 (compiler) and Phase 26 (brownfield mapper) build on. Record shape/cardinality is locked; endpoint resolution + graph-wide consistency are the explicit Phase 25 scope.
- Constitution-plane note: the manifest rebaseline lands under `contracts/.hashes/` (CODEOWNERS-gated); real human ratification is the PR/merge review, consistent with the standing solo-author CODEOWNERS caveat in STATE.md.

---
*Phase: 24-contract-relationship-vocabulary-compatibility-v2-3-a*
*Completed: 2026-07-19*

## Self-Check: PASSED

All created files verified on disk; all task commits (7e3630d, 7f8d6d7, 2a5c234, f1d97b2) present in history; manifest tracks the new schema key.
