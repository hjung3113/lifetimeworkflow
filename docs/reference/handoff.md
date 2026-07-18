<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Task packet handoff contract

> DERIVED reference — regenerated from `contracts/harness/task-control/handoff.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

Immutable resume snapshot tied to one state revision.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| baseline | object | yes |  |  |
| critical_constraint_ids | array | yes |  |  |
| current_ref | ref | yes |  |  |
| evidence_ids | array | yes |  |  |
| finding_ids | array | yes |  |  |
| goal | string | yes |  |  |
| lane | ref | yes |  |  |
| next_action | string | yes |  |  |
| non_goals | array | yes |  |  |
| phase | ref | yes |  |  |
| state_revision | integer | yes |  |  |
| task_id | ref | yes |  |  |
