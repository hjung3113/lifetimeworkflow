# 8. Task Control Plane Namespace, Authority, Lifecycle, and Overlay

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** Accepted — ratified by human/CODEOWNERS.
- **Date:** 2026-07-19
- **Deciders:** kimhyojung (CODEOWNERS)
- **Supersedes:** —
- **Superseded by:** —
- **Complements:** [ADR-0003](0003-pipeline-topology-slot-and-instance-overlay.md), [ADR-0006](0006-process-memory-channel-and-provenance-reframe.md), [ADR-0007](0007-constitution-gate-dev-enforce-decoupling.md)

## Context and Problem Statement

The harness needs a task-local control plane that joins deterministic risk routing, lifecycle state, evidence, and fresh-session handoff without creating another authority for contracts, ADRs, or derived memory.

## Decision Drivers

- Keep contracts and ADRs authoritative and human-ratified.
- Preserve a domain-neutral core and one-way instance dependency.
- Make high-risk paths fail closed while retaining a low-ceremony FAST path.
- Permit only escalation by instance-owned policy overlays.

## Considered Options

1. Store task state in `.memory/tasks/`. *Rejected:* introduces a third memory authority.
2. Use a five-phase lifecycle. *Rejected:* evidence and handoff failure modes need distinct lifecycle boundaries.
3. Use `.workflow/tasks/<task-id>/` with six operational lifecycle phases. *Proposed.*

## Decision Outcome

**Ratified by human/CODEOWNERS on 2026-07-19.**

1. The task namespace is `.workflow/tasks/<task-id>/`; it owns only task-local intent, state, evidence, immutable HANDOFF snapshots, and artifact pointers.
2. `contracts/` and accepted `docs/adr/` remain policy/decision authority; `.memory/state/` may retain only an active-task pointer; `.memory/derived/` remains generator-owned.
3. Lifecycle progression is `INTAKE`, optional `CLARIFY`/`SPEC`/`PLAN`, `EXECUTE`, `REVIEW`, `VERIFY`, and `COMPLETE`, with `BLOCKED` as a controlled interruption. Transitions use revision CAS and phase gates.
4. Risk overlays are declarative, instance-owned, provenance-recorded, and escalate-only: they cannot lower a core lane or remove required artifacts/gates.

### Consequences

- **Good:** state, evidence, and handoff can be reproduced and checked at named boundaries.
- **Good:** FAST avoids detailed planning and double review unless facts promote risk.
- **Bad / accepted:** a task directory adds durable files that must remain pointer-oriented and must not duplicate contracts or transcripts.

## Approval

Ratified by human/CODEOWNERS (kimhyojung) on 2026-07-19. This decision is now authoritative and append-only.

## Links

- Design authority: `docs/explanation/next-milestone-task-control-plane.md` §Phase 6.
- Evaluation fixtures pending ratification: `.planning/phases/23-lifecycle-evaluation-docs-ci-v2-2-f/23-01-PLAN.md`.
- Runtime-neutral implementation: `tools/task_packet/`, `tools/risk_router/`, `tools/task_control/`, `tools/evidence/`, and `tools/handoff/`.
