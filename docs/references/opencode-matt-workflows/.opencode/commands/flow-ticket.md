---
description: Implement exactly one ready ticket or small spec
agent: flow-ticket
subtask: true
---

# Invocation contract

Workflow role: Single-ticket implementation owner

User request:

```text
$ARGUMENTS
```

Objective: Complete one unblocked ticket through TDD, independent review, and a local commit.
Required starting context: One exact ticket/spec reference and any relevant branch constraint.
Stop condition: One ticket committed; no push, close, or next-ticket work.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
