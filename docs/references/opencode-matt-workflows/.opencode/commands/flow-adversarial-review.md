---
description: Run a formal multi-expert adversarial review for a high-risk design, code/document change, debug direction, refactor, or API/data decision
agent: flow-adversarial-review
subtask: true
---

# Invocation contract

Workflow role: High-risk adversarial review coordinator

User request:

```text
$ARGUMENTS
```

Objective: Independently review the target, challenge important findings, and produce an adjudicated case-specific final report.
Required starting context: Target reference, case type or enough evidence to infer it, objective, definition of done, constraints, and risk rationale.
Stop condition: A validated `.workflow/reviews/<review-id>/FINAL.md`; no edits to the reviewed target.

## Repository snapshot

<repository_snapshot>
!`bash .opencode/workflows/scripts/repo-context.sh --review --format json`
</repository_snapshot>
