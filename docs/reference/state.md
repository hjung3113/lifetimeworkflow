<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Task packet state contract

> DERIVED reference — regenerated from `contracts/harness/task-control/state.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

Current revision and repository context for a task packet.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| baseline | object | yes |  |  |
| blockers | array | yes |  |  |
| completed_items | array | yes |  |  |
| current_ref | ref | yes |  |  |
| evidence_integrity | object | no |  |  |
| next_action | string | yes |  |  |
| phase | ref | yes |  |  |
| revision | integer | yes |  |  |
| task_id | ref | yes |  |  |
| transition | — | yes |  |  |
