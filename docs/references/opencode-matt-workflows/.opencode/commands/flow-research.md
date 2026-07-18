---
description: Produce one bounded cited primary-source research artifact
agent: flow-research
subtask: true
---

# Invocation contract

Workflow role: Primary-source research owner

User request:

```text
$ARGUMENTS
```

Objective: Answer one decision-relevant question and write a cited artifact only.
Required starting context: Research question, why it matters, source/freshness constraints, exclusions, and preferred artifact path.
Stop condition: Cited artifact complete; no spec, tickets, or production changes.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
