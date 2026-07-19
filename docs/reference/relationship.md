<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Contract relationship record

> DERIVED reference — regenerated from `contracts/harness/topology/relationship.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

Human-ratified Draft 2020-12 shape for ONE contract-relationship record: an authority endpoint and one-or-more dependent endpoints for a tracked contract. Validates a single record's shape and cardinality ONLY (exactly one authority, at least one dependent) — endpoints are bare stable-id strings; no graph-wide resolution, no cross-record uniqueness, no endpoint-existence checks (those belong to the Phase 25 compiler).

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| authority | string | yes |  | Exactly ONE authority endpoint (a bare stable-id string, not an array). |
| contract | string | yes |  | Stable reference to the tracked contract this relationship is about. |
| dependents | array | yes |  | One-or-more dependent endpoints (bare stable-id strings). |
| id | string | yes |  | Stable record id for this relationship. |
| kind | string | no |  | Optional explanatory relationship kind. |
| labels | array | no |  | Optional explanatory labels. |
