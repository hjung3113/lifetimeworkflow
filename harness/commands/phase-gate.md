---
description: >-
  Use when starting or resuming a task phase: fail closed on repository identity, state revision,
  required artifacts, blockers, and deterministic constraint-attestation coverage.
agent: orchestrator
---

# /phase-gate — verify task start conditions

The orchestrator is the only transition requester. Before entering or resuming a phase, run:

```sh
python -m tools.task_control phase-gate .workflow/tasks/<task-id> --expected-revision <n> --repo-root <canonical-worktree-root>
```

Pass the expected baseline explicitly when resuming an externally supplied task snapshot:

```sh
python -m tools.task_control phase-gate .workflow/tasks/<task-id> --expected-revision <n> --baseline <commit>
```

The command fails closed and prints the deterministic refresh list if the worktree task path,
HEAD ref, baseline ancestry, state revision, required artifacts, blockers, source hashes, phase
coverage, planned-action mapping, or requested prohibited actions do not match. It checks only
attested IDs and hashes; it does not claim to establish an agent's understanding.

`context-attestation.json` is task-local and contains a top-level `constraints` array. Each item
has `constraint_id`, `source_path`, `source_sha256`, `applies_to_phases`,
`prohibited_action_ids`, `required_evidence_ids`, and `planned_action_mapping`.

Use `python -m tools.task_control attest <task-dir> --attestation <draft.json>` to create or
update it: the tool derives each source path and SHA-256 from `task.json` rather than trusting
the draft. Always pass the orchestrator's canonical worktree root to `--repo-root`.
