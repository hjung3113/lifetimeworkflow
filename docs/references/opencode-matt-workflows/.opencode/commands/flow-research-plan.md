---
description: Turn an existing research artifact into a decision and optional plan
agent: flow-research-plan
subtask: true
---

# Invocation contract

Workflow role: Research-to-decision planning owner

User request:

```text
$ARGUMENTS
```

Objective: Settle the project-specific decision and, only when requested, publish spec and tickets.
Required starting context: One cited research artifact plus the project decision and whether implementation planning is desired.
Stop condition: Decision recorded, or tickets published when explicitly requested; no implementation.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
