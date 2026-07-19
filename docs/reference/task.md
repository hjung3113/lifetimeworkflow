<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Task packet task contract

> DERIVED reference — regenerated from `contracts/harness/task-control/task.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

Human-ratified shape for immutable task intent and routing inputs.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| acceptance_criteria | array | yes |  |  |
| constraints | array | yes |  |  |
| decision_refs | array | yes |  |  |
| goal | string | yes |  |  |
| lane | ref | yes |  |  |
| non_goals | array | yes |  |  |
| risk_decision | object | yes |  | Canonical router output captured at deterministic intake. |
| risk_inputs | object | yes |  |  |
| stop_condition | string | no |  | Human-ratified task-specific boundary that a fresh session must restore exactly. |
| task_id | ref | yes |  |  |
