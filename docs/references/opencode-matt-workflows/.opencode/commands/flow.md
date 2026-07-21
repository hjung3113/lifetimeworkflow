---
description: Start or continue engineering work through the progress-aware orchestrator
agent: flow-orchestrator
subtask: false
---

# Orchestrator invocation

Objective: Coordinate this request, update durable progress, and delegate one specialist workflow only when needed.
Stop condition: Direct work is completed or one delegated workflow result has been reviewed and recorded.

User request:

```text
$ARGUMENTS
```

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh --routing`
</repository_snapshot>

## Progress snapshot

<progress_snapshot>
!`python3 .opencode/workflows/scripts/workflow-progress.py show --compact`
</progress_snapshot>

Maintain `.workflow/PROGRESS.md`, handle direct coordination work when appropriate, and use the router only when a specialist workflow is needed.
