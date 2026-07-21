---
description: Resolve and verify the current merge or rebase conflict
agent: flow-conflicts
subtask: true
---

# Invocation contract

Workflow role: Conflict-resolution owner

User request:

```text
$ARGUMENTS
```

Objective: Reconstruct both sides intent, finish the git operation, and verify affected behavior.
Required starting context: The current conflicted worktree plus optional semantic context.
Stop condition: Operation complete and verified, or one precise human decision requested.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
