---
description: Survey architecture and produce a candidate handoff
agent: flow-architecture-scan
subtask: true
---

# Invocation contract

Workflow role: Architecture surveyor

User request:

```text
$ARGUMENTS
```

Objective: Find evidence-backed deepening opportunities and produce the original report plus one selected candidate handoff.
Required starting context: An optional domain/module focus; otherwise survey the repository broadly but read-only.
Stop condition: Survey complete and candidate handoff produced; no design or implementation.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
