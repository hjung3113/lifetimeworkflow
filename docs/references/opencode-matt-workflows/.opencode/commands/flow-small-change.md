---
description: Implement one bounded change in a single session
agent: flow-small-change
subtask: true
---

# Invocation contract

Workflow role: Small-change implementation owner

User request:

```text
$ARGUMENTS
```

Objective: Align, implement, verify, independently review, and locally commit one small change.
Required starting context: A concrete behavior change that genuinely fits one context window.
Stop condition: One verified local commit; no push and no neighboring work.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
