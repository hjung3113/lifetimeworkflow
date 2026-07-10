---
name: data-contracts
description: >-
  Use when reading, changing, or validating anything under contracts/ — TSV/column specs,
  reference data, or state shapes. Covers the contract-first rule, the JSON Schema Draft 2020-12
  shape, check-jsonschema validation, and the RFC 8785 schema-hash contract-drift gate that
  trips when a contract (or a §4-5 convention) changes without a paired golden update.
---

# data-contracts

`contracts/` is the single source of truth — the constitution plane. Code that disagrees with a
contract is wrong; fix the code, not the contract. This skill is the map of that plane and its
gates.

## Layout

```
contracts/
├── sample/           greeting.schema.json             (generic default instance, GEN-02)
├── format-conventions.schema.json                     (§4.3–4.6 materialized, P14 hash target)
├── <domain-spec>/    <name>.spec.yaml + .schema.json
├── <rules>/          <name>.catalog.yaml + .schema.json
├── <reference>/      <name>.master.yaml + .schema.json
└── <state>/          <name>.progress.yaml + .schema.json
```

The `<…>/` dirs are an instance's own domain contracts; the shipped generic default is
`contracts/sample/greeting.schema.json`, and `format-conventions.schema.json` is the language-neutral
core convention target.

- **YAML spec** = human-readable skeleton. **Companion `.schema.json`** (JSON Schema Draft
  2020-12) = the validated, hashed source of truth.
- `golden/` is a **separate top-level sibling**, not `contracts/golden/`.
- Seeds are example placeholders (CONTRACT-01) — real domain values are Out of Scope. The point is
  to seed the plumbing that enforces contracts, not to fill them.

## Validation

- Validate an instance against its schema: `check-jsonschema --schemafile <schema> <instance>`.
- Both languages validate against the SAME schema: JsonSchema.Net (.NET) and jsonschema (Python).

## The drift gate (contract-first, enforced)

- `tools/contract_drift/check.sh` canonicalizes every `contracts/**/*.schema.json` with **RFC 8785
  (JCS)**, SHA-256s each into `.hashes/manifest.json`, and fails when a hash moves without a paired
  golden/approval update.
- `format-conventions.schema.json` materializes the §4.3–4.6 conventions as const/enum fields, so a
  convention flip (e.g. `bom: false → true`) bumps the hash exactly like a column reorder (P14).
- Changes are classified breaking (existing case output changes) vs non-breaking (new case added).

## Non-negotiables

Never write `contracts/` from agent/code paths — it is CODEOWNERS-gated. Use `tools/contract_hash`
and `tools/contract_drift`; do not re-hash schemas in a second place (a divergent hash impl defeats
the gate, P14).

## Deeper reference

Keep a walkthrough of adding a schema field under `references/`. See `contracts/README.md`.
