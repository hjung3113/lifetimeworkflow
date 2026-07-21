<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Task packet handoff contract

> DERIVED reference — regenerated from `contracts/harness/task-control/handoff.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

Immutable resume snapshot tied to one state revision.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| artifact_refs | array | yes |  |  |
| baseline | object | yes |  |  |
| changed_paths | array | yes |  |  |
| critical_constraint_ids | array | yes |  |  |
| critical_constraint_refs | array | yes |  |  |
| current_ref | ref | yes |  |  |
| decisions | array | yes |  |  |
| evidence_ids | array | yes |  |  |
| evidence_ref | ref | yes |  |  |
| finding_ids | array | yes |  |  |
| goal | string | yes |  |  |
| lane | ref | yes |  |  |
| next_action | string | yes |  |  |
| non_goals | array | yes |  |  |
| phase | ref | yes |  |  |
| required_read_paths | array | yes |  |  |
| state_ref | ref | yes |  |  |
| state_revision | integer | yes |  |  |
| stop_condition | string\|null | yes |  | Exact task-specific boundary when ratified; null means the task supplied none. |
| task_id | ref | yes |  |  |
| unresolved_items | array | yes |  |  |
