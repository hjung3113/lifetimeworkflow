# Change log for the adversarial-review revision

## Orchestrator, router, and context handoff

- Added `flow-orchestrator` as the user-facing primary coordinator.
- Moved bounded repository inspection and durable context ownership to the orchestrator and command snapshots.
- Converted `flow-router` into a hidden, four-step, tool-free classifier with no repository or delegation access.
- Replaced wildcard delegation with explicit orchestrator-to-flow and review-coordinator-to-expert allowlists.
- Added mandatory `ROUTING REQUEST`, `ROUTING DECISION`, and role-specific `WORKFLOW HANDOFF` contracts.
- Added read-only repository and progress snapshots to the relevant slash commands.

## Workflow boundaries

- Split architecture survey from architecture planning.
- Split research artifact production from research-to-plan conversion.
- Added `/flow-feature-resume` for checkpoint plus prototype return handoffs.
- Kept setup as an explicit prerequisite rather than consuming feature/implementation context.
- Enforced one ticket, one bug, one Wayfinder stage, or one git operation per invocation.

## Permissions and modes

- Changed every agent to default-deny permissions.
- Added explicit external-directory denial and common local secret-file read denial.
- Denied workflow edits to `.git/**`, `.opencode/**`, and local secret files.
- Added granular safe read/test command allowances.
- Explicitly denied push, reset, clean, shell deletion, privilege escalation, PR merge, and repository deletion from implementation workflows.
- Added two hidden, read-only review-axis agents.

## Agent and command prompts

- Added role, goal, required inputs, gates, workflow, non-goals, verification, stop condition, and output format to public agents.
- Added role, objective, required context, stop condition, user arguments, and repository snapshot to commands.
- Added explicit context-hygiene and decision-log requirements.

## Models and scripts

- Added tier-based per-agent model configuration without hard-coding a provider.
- Added bounded repository context, upstream-skill/setup preflight, and check-detection scripts.
- Expanded verification to cover permissions, modes, self-call protection, hidden agents, references, models, and helper files.


## Progress orchestrator

- Added `flow-orchestrator` as the user-facing primary agent.
- Converted `flow-router` into a hidden, context-only classifier.
- Added `.workflow/PROGRESS.md` lifecycle management through `workflow-progress.py`.
- Added `/flow-progress`.
- Fixed `repo-context.sh` to inspect the Git repository root when invoked from a subdirectory.

## Adversarial review and script hardening

- Added `flow-adversarial-review` and eight hidden specialist/challenge/synthesis agents.
- Added case-specific design, code/document, debug, refactor, and API/data outputs.
- Added script-managed review workspaces and finding/challenge registration.
- Added implementation design and exchange templates.
- Fixed nested-directory context and preflight behavior.
- Removed pytest false positives based only on a `tests/` directory.
- Added manifest-based installation, stale managed-file cleanup, and centralized backups.
- Split bundle validation from installed-environment diagnosis.
- Added model configuration dry-run and unknown-name validation.
