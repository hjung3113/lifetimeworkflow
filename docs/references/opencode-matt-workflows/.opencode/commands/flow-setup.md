---
description: Configure repository workflow prerequisites only
agent: flow-setup
subtask: true
---

# Invocation contract

Workflow role: Repository workflow bootstrapper

User request:

```text
$ARGUMENTS
```

Objective: Create and verify the upstream issue-tracker, triage-label, and domain-doc contracts.
Required starting context: Optional tracker/layout preferences from the user.
Stop condition: Setup complete or one required setup choice pending.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
