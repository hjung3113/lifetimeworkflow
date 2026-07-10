---
phase: 01-constitution-golden-core
plan: 02
subsystem: contracts
tags: [json-schema, draft-2020-12, yaml, check-jsonschema, contract-first, constitution-plane, p14]

# Dependency graph
requires:
  - phase: 01-01
    provides: uv workspace + check-jsonschema/jsonschema pinned (BOOT-02) — the validator toolchain
provides:
  - 4 seeded parserimprove contract YAMLs in contracts/{log-specs,normalization,reference-data,state}/ (TBD placeholders preserved)
  - 4 companion Draft 2020-12 .schema.json validating each seed instance
  - format-conventions.schema.json materializing §4.3-4.6 conventions as const/enum fields (P14 drift-hash target)
  - Top-level golden/README.md (constitution-plane sibling of contracts/)
  - contracts/README.md flagging seeds as example placeholders (not domain truth)
affects: [01-05-contract-drift-gate, 01-06-golden-runner, contract-hash, format-conventions]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contract-first dual: YAML human spec + companion .schema.json (Draft 2020-12) = validated/hashed source of truth (D-06)"
    - "P14 fix: cross-cutting §4.3-4.6 conventions materialized as const-valued schema fields so drift hash covers convention changes, not only column reorders"
    - "golden/ is a TOP-LEVEL constitution-plane sibling of contracts/ (no contracts/golden/ nesting) (D-06/D-07)"

key-files:
  created:
    - contracts/log-specs/standard-log.spec.yaml
    - contracts/log-specs/standard-log.schema.json
    - contracts/normalization/correction-rules.catalog.yaml
    - contracts/normalization/correction-rules.schema.json
    - contracts/normalization/format-conventions.schema.json
    - contracts/reference-data/equipment-master.yaml
    - contracts/reference-data/equipment-master.schema.json
    - contracts/state/equipment-progress.yaml
    - contracts/state/equipment-progress.schema.json
    - golden/README.md
    - contracts/README.md
  modified: []

key-decisions:
  - "format-conventions.schema.json embeds convention values as JSON Schema const/enum so the schema text itself (RFC 8785 -> SHA-256) is the P14 hash target — flipping bom false->true mutates the hash"
  - "Added an example decimal column (param_value) to standard-log so one fixture exercises §4.4 TZ + §4.6 decimal-locale + BOM/LF together (RESEARCH Open Question 1)"
  - "Companion schemas use additionalProperties:true + minimal required keys so TBD placeholder values validate while structure is enforced"

patterns-established:
  - "Every contracts/*.{yaml,catalog.yaml} has a companion .schema.json; check-jsonschema --schemafile <schema> <instance> is the validation contract"
  - "Seed files carry an explicit SEED PLACEHOLDER banner distinguishing example values from domain truth (Out of Scope)"

requirements-completed: [CONTRACT-01]

# Metrics
duration: 5min
completed: 2026-07-08
---

# Phase 1 Plan 02: Seed Constitution Plane + Companion Schemas Summary

**4 parserimprove seed contracts + 4 companion Draft 2020-12 schemas + a P14 format-conventions.schema.json (§4.3-4.6 materialized as const fields) + top-level golden/README.md, all validated by check-jsonschema**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-07-08T03:15:39Z
- **Completed:** 2026-07-08T03:20:38Z
- **Tasks:** 2
- **Files modified:** 11 created

## Accomplishments
- Seeded the four constitution-plane contract YAMLs (standard-log spec, correction-rules catalog, equipment-master, equipment-progress) into `contracts/` with all `TBD`/`owner: TBD` placeholder markers preserved and an explicit SEED PLACEHOLDER banner on each.
- Authored a companion Draft 2020-12 `.schema.json` per seed; `check-jsonschema` validates all four instances with exit 0 and all five schemas are meta-valid.
- Authored `format-conventions.schema.json` materializing the §4.3-4.6 conventions (encoding, bom, newline, decimal_sep, culture, float_compare, row_ordering, timezone, null_token, tsv_escape, interval) as `const`/`enum` fields — the P14 drift-hash target for Plan 05.
- Seeded the top-level `golden/README.md` as a constitution-plane sibling of `contracts/` (no `contracts/golden/` subdirectory) and added `contracts/README.md` flagging placeholder status and the golden/ layout.

## Task Commits

1. **Task 1: Seed contracts + top-level golden/README** - `c0748b6` (feat)
2. **Task 2: Companion schemas + format-conventions.schema.json (P14)** - `ec3915a` (feat)

## Files Created/Modified
- `contracts/log-specs/standard-log.spec.yaml` - Seeded TSV log spec (3 seed columns + example decimal column)
- `contracts/log-specs/standard-log.schema.json` - Companion schema (format block + columns array)
- `contracts/normalization/correction-rules.catalog.yaml` - Seeded normalization/correction rule catalog
- `contracts/normalization/correction-rules.schema.json` - Companion schema (rule array shapes)
- `contracts/normalization/format-conventions.schema.json` - §4.3-4.6 conventions materialized as const/enum (P14 hash target)
- `contracts/reference-data/equipment-master.yaml` - Seeded reference-data master
- `contracts/reference-data/equipment-master.schema.json` - Companion schema (entities block)
- `contracts/state/equipment-progress.yaml` - Seeded state/carryover model
- `contracts/state/equipment-progress.schema.json` - Companion schema (storage/progress/carryover)
- `golden/README.md` - Top-level golden constitution-plane README (sibling of contracts/)
- `contracts/README.md` - Constitution-plane marker: human-owned, seeds are example placeholders

## Decisions Made
- **Const-embedded conventions for P14:** `format-conventions.schema.json` encodes each §4.3-4.6 value as a `const` (bom=false, newline="lf", decimal_sep=".", timezone="utc-iso8601", null_token="\\N", etc.). This puts the values inside the schema text so the Plan-05 RFC 8785 → SHA-256 hash trips when a convention flips, closing the P14 blind spot.
- **Example decimal column added to standard-log:** per RESEARCH Open Question 1, added `param_value` (decimal, flagged example/SEED) so a single fixture touches TZ + decimal-locale + BOM/LF at once. No domain-confirmed values invented.
- **Permissive-but-structured companion schemas:** `additionalProperties:true` with minimal `required` keys lets TBD placeholder values validate while still enforcing the structural shape (format block, columns items, rule arrays, entity keys).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. All `check-jsonschema` validations and meta-validations passed on first run. (uv emits a harmless `UV_NATIVE_TLS` deprecation warning; unrelated to this plan.)

## User Setup Required
None - no external service configuration required. Pure Python/YAML/JSON-Schema, no .NET or network dependency.

## Next Phase Readiness
- Contract seeds + companion schemas are in place; Plan 05 (contract-drift gate, CONTRACT-04) can now build its hashed manifest over `contracts/**/*.schema.json` including `format-conventions.schema.json`.
- Plan 06 (golden runner, CONTRACT-03) has the standard-log spec + top-level `golden/` structure to build fixtures against.
- No blockers introduced. The .NET-side items remain gated by the pre-existing BOOT-01 egress blocker (unrelated to this plan).

## Self-Check: PASSED

All 12 created files present, both task commits (`c0748b6`, `ec3915a`) exist, and the `contracts/golden` nesting guard holds (top-level `golden/` only).
