# Architecture Decision Records (ADR)

*Format: **MADR 4.x** · plane: constitution (human-owned) · policy: **append-only, immutable***

This log is the auditable memory of *why* the harness is shaped the way it is. It complements the
`explanation/` quadrant (evolving narrative) by recording **point-in-time decisions** that must not
be silently rewritten (DOCS-02).

## Convention

- **Numbered & sequential.** Files are `NNNN-kebab-title.md` starting at `0001`. The number is
  permanent and never reused.
- **Append-only.** Add the next-numbered ADR; do not renumber or reorder existing records.
- **Immutable.** Once an ADR is `Status: accepted`, its decision content is **not edited**.
  Fixing typos/links is fine; changing the recorded decision is not.
- **Supersede, don't edit.** To change a past decision, write a **new** ADR that references the
  old one and set the old ADR's `Status: superseded by NNNN` (and the new one's
  `Supersedes: NNNN`). The original stays in place as the historical record.
- **Status values.** `proposed` → `accepted` → (`deprecated` | `superseded by NNNN`).
- **MADR sections.** Title, Status, Context and Problem Statement, Decision Drivers,
  Considered Options, Decision Outcome, Consequences (+ optional Links).

> Rationale: decisions must be **auditable, not silently edited** (threat T-03-01, Repudiation).
> The append-only/supersede rule makes the decision history tamper-evident.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-walking-skeleton-golden-core.md) | Walking-Skeleton Golden Core Architecture | accepted |
| [0002](0002-general-template-de-specialization.md) | General Template De-specialization | accepted |
| [0003](0003-pipeline-topology-slot-and-instance-overlay.md) | Pipeline-Topology Slot and Instance Overlay | accepted |
| [0004](0004-constitution-hook-fail-open-posture.md) | Constitution-Plane Hook Fail-Open Posture on Malformed Stdin | accepted |
| [0005](0005-golden-comparator-structural-only.md) | Golden Comparator Is Structural-Only Pending Column-Aware Canonicalization | accepted |
| [0006](0006-process-memory-channel-and-provenance-reframe.md) | Memory Model: PROCESS/Agreements Channel + Provenance→Data-Authority Reframe | accepted |

*Add a row per ADR. Do not remove rows — mark superseded records in the Status column.*
