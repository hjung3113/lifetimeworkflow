---
description: Answer one design question with isolated throwaway code
agent: flow-prototype
subtask: true
---

# Invocation contract

Workflow role: Disposable-evidence builder

User request:

```text
$ARGUMENTS
```

Objective: Build the cheapest runnable artifact that answers one decision question and return a decision-rich handoff.
Required starting context: Prefer a checkpoint handoff naming one question and the originating workflow.
Stop condition: Return handoff written; no production implementation or commit.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
