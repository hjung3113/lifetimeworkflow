---
description: >-
  Publish a deterministic immutable HANDOFF for one active task revision. Use before changing
  sessions; it records references and hashes, never a conversation transcript.
agent: orchestrator
---

# /handoff — immutable fresh-session snapshot

1. Generate and validate the revision-bound snapshot. Do not hand-edit it or copy task, evidence,
   artifact, contract, ADR, secret, or PII bodies into it.

   !`uv run python -m tools.handoff generate .workflow/tasks/<task-id>`

   !`uv run python -m tools.handoff validate .workflow/tasks/<task-id>`

2. For a later session, read only its pointers, then validate it. A stale revision, ref, or
   artifact is a failure: regenerate; never auto-correct a HANDOFF.

   !`uv run python -m tools.handoff fresh-session .workflow/tasks/<task-id>/handoffs/revision-<n>.json`

3. Before EXECUTE, REVIEW, or VERIFY, run `/phase-gate` for the handoff revision. Validation and
   phase-gate are both required resume barriers.
