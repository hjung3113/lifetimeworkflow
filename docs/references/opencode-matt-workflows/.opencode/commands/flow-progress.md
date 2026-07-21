---
description: Inspect or update the orchestrator-managed project progress record
agent: flow-orchestrator
subtask: false
---

# Progress request

Objective: Inspect or update the canonical progress record without starting unrelated workflow work.
Stop condition: The requested progress operation is complete and the current next action is reported.

```text
$ARGUMENTS
```

Current progress:

<progress_snapshot>
!`python3 .opencode/workflows/scripts/workflow-progress.py show`
</progress_snapshot>

Handle this as progress-management work. Do not route unless the request explicitly asks to resume substantive engineering work.
