---
description: Resume feature planning from checkpoint and prototype return handoffs
agent: flow-feature
subtask: true
---

# Invocation contract

Workflow role: Feature planning owner

User request:

```text
$ARGUMENTS
```

Objective: Resume without repeating settled questions, then publish the spec and tickets.
Required starting context: Paths or references to the planning checkpoint and prototype return handoff.
Stop condition: Tickets published and frontier reported; no implementation.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>


The arguments should contain both artifacts when both exist. Treat them as authoritative evidence but verify referenced paths.

Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
