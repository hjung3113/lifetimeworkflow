---
description: Diagnose and fix one hard bug through a red-capable loop
agent: flow-bugfix
subtask: true
---

# Invocation contract

Workflow role: Diagnosis-first bug-fix owner

User request:

```text
$ARGUMENTS
```

Objective: Reproduce, minimize, identify, regression-test, fix, verify, review, and locally commit one bug.
Required starting context: Exact symptom, environment, reproduction clues, known-good/bad states, and artifact paths when available.
Stop condition: Verified fix and commit, or a precise statement of missing access/artifacts.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh`
</repository_snapshot>




Treat this command packet as explicit initial context. Verify only what is necessary, preserve the user's constraints, and follow the agent's required output format.
