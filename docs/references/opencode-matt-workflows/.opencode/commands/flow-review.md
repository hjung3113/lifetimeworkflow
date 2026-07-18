---
description: Review one diff independently on Standards and Spec axes
agent: flow-review
subtask: true
---

# Invocation contract

Workflow role: Read-only review coordinator

User request:

```text
$ARGUMENTS
```

Objective: Validate a fixed point and produce separate Standards and Spec reports.
Required starting context: A required fixed point and the originating issue/spec reference when known.
Stop condition: Findings reported only; no edits.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
