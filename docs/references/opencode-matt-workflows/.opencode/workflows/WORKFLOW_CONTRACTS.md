# Workflow contracts

## Router handoff contract

The router delegates one workflow with:

```text
WORKFLOW HANDOFF
Route:
User request:
Goal:
Why this route:
Repository evidence:
Known constraints:
Required inputs:
Starting point:
Non-goals:
Stop condition:
Expected output:
```

Repository evidence must include only observed facts. The router should not pre-solve the task.

## Direct command contract

Every command supplies:

- the role being invoked;
- the user's unmodified arguments;
- one observable objective;
- required starting context;
- the workflow stop condition;
- a bounded read-only repository snapshot.

## Agent completion contract

Every public workflow agent finishes with:

```text
Outcome
Artifacts or changes
Verification
Decisions and assumptions
Risks or unresolved items
Next command
```

## Context hygiene

- Setup is a separate workflow and is never silently run inside a feature or implementation session.
- Feature alignment, spec synthesis, and ticket creation remain in one child session.
- Each implementation ticket receives a fresh child session.
- Prototype detours cross sessions through checkpoint and return handoffs.
- Research and architecture scanning stop before planning; separate commands convert selected evidence into plans.
- Review axes run in separate hidden read-only subagents.


## Progress-aware orchestrator

`flow-orchestrator` is the user-facing primary agent. It maintains `.workflow/PROGRESS.md` through `workflow-progress.py`, asks the hidden `flow-router` for a classification, delegates the selected workflow, and reviews the returned coordination result. The router is a pure classifier and does not read the repository or invoke flows.

Use `/flow <request>` for normal work and `/flow-progress <request>` to inspect or update progress.
