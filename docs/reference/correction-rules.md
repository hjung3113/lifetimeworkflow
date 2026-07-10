<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# normalization + correction rules catalog (SEED PLACEHOLDER companion schema)

> DERIVED reference — regenerated from `contracts/normalization/correction-rules.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

Draft 2020-12 companion schema for correction-rules.catalog.yaml. Validates normalization_rules + correction_rules array shapes while allowing TBD placeholder values. Seed/example — domain rules Out of Scope (CONTRACT-01).

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| change_policy | object | no |  |  |
| correction_rules | array | yes |  |  |
| description | string | no |  |  |
| id | string | yes |  |  |
| normalization_rules | array | yes |  |  |
| owner | string | no |  |  |
| version | string | no |  |  |
