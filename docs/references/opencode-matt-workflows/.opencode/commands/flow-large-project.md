---
description: Run exactly one Wayfinder stage
agent: flow-large-project
subtask: true
---

# Invocation contract

Workflow role: Wayfinder stage owner

User request:

```text
$ARGUMENTS
```

Objective: Chart a new map, resolve one frontier decision, or collapse a fully cleared map into spec and tickets.
Required starting context: A loose destination or one existing map reference.
Stop condition: Exactly one stage complete and next frontier/command reported.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
