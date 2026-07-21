# Orchestrator design

## Purpose

`flow-orchestrator` separates user-facing continuity and coordination from pure route classification and specialist execution. The user maintains one conversation with the orchestrator; the router only chooses a flow from a complete context packet.

## Responsibilities

The orchestrator owns:

- current objective and definition of done;
- durable constraints, non-goals, and decisions;
- bounded repository evidence;
- active artifacts, blockers, and prior flow results;
- `.workflow/PROGRESS.md` lifecycle;
- router request construction;
- workflow handoff construction;
- post-flow coordination review and progress update.

It may answer conceptual, explanatory, status, and coordination-only requests directly. It must route specialist work rather than implementing it itself.

## Boundaries

The orchestrator:

- does not write source files;
- does not load upstream implementation skills;
- does not perform formal code or adversarial review itself;
- does not silently expand a delegated flow;
- delegates exactly one specialist flow per routing cycle;
- may request one corrective continuation from the same flow when the result is materially incomplete but still within the original stop condition.

## Context lifecycle

At the beginning of substantive work:

1. Read the command-injected repository snapshot.
2. Read the compact progress snapshot.
3. Reconcile the request with existing active work.
4. Initialise or update the progress objective when necessary.
5. Read only additional files that materially improve routing or handoff quality.
6. Preserve observed facts separately from assumptions.

The orchestrator sends the router only the information required to select a workflow. It sends the selected workflow a richer handoff containing execution-relevant references and boundaries.

## Progress state

`.workflow/PROGRESS.md` is the human-readable canonical record. The script owns its machine-managed sections and writes updates atomically. Durable state is kept; transient chat, secrets, speculative code details, and large outputs are excluded.

## Failure handling

- Missing workflow setup routes to `flow-setup`.
- Missing required references are surfaced in the routing decision or flow preflight.
- Contradictory progress and user intent are reconciled before delegation.
- Unsupported or incomplete flow results are not recorded as completed.
- High-risk decisions may be sent to `flow-adversarial-review` when explicitly requested or justified by recorded C3/C4 risk.

## Why the router is pure

Repository discovery and continuity require session context and are therefore orchestrator responsibilities. Keeping the router tool-free prevents it from becoming a second coordinator, avoids duplicated exploration, makes routing reproducible, and removes self-delegation and hidden implementation risk.
