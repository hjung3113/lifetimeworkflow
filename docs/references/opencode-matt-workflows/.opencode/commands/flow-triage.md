---
description: Triage one raw issue or external pull request
agent: flow-triage
subtask: true
---

# Invocation contract

Workflow role: Maintainer-facing intake owner

User request:

```text
$ARGUMENTS
```

Objective: Verify the claim and apply one approved upstream triage outcome or agent brief.
Required starting context: One issue/PR reference, or an explicit request to list items needing attention.
Stop condition: Tracker outcome applied or exact missing information listed; no implementation.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
