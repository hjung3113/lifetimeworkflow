# OpenCode use-case workflows for `mattpocock/skills`

This bundle adds a progress-aware orchestrator, a pure workflow router, use-case-level workflow agents, and a high-risk adversarial review gate around the original English Matt Pocock skills.

It does not translate or replace upstream `SKILL.md` files. Workflow agents load installed upstream skills through OpenCode's native `skill` tool and compose them within explicit use-case boundaries.

## System architecture

```text
User
  ↓
flow-orchestrator (primary, user-facing)
  ├─ answers coordination/status questions directly
  ├─ owns bounded repository context
  ├─ maintains .workflow/PROGRESS.md
  ├─ asks flow-router for classification when specialist work is needed
  ├─ delegates exactly one workflow agent
  └─ reviews and records the returned result
        ↓
flow-router (hidden, pure classifier)
  └─ receives a ROUTING REQUEST only; no repository/tool access
        ↓
selected flow-* subagent
  └─ performs one bounded workflow and returns structured evidence
```

The user normally talks only to `/flow`. Direct workflow commands remain available for expert or recovery use.

## Orchestrator responsibilities

`flow-orchestrator` is the only user-facing coordinator. It:

- preserves the user's original request, objective, definition of done, constraints, non-goals, decisions, artifacts, blockers, and next action;
- reads the command-injected routing snapshot and only a small number of additional files when materially necessary;
- handles conceptual explanations, progress inspection, and coordination-only work directly;
- sends a structured `ROUTING REQUEST` to the hidden router for code changes, planning, debugging, triage, research, conflicts, or formal review;
- records the selected route before delegation;
- sends the chosen workflow a complete `WORKFLOW HANDOFF`;
- checks the returned result for evidence, scope, stop-condition compliance, and contradictions;
- updates `.workflow/PROGRESS.md` through the script rather than editing it directly.

The orchestrator does not implement specialist work itself and does not treat its coordination review as a substitute for code or adversarial review.

## Router contract

`flow-router` is intentionally narrow. It has no read, search, shell, edit, web, skill, question, or task permissions. It only classifies the packet supplied by the orchestrator.

The orchestrator sends:

```text
ROUTING REQUEST
User request:
Current objective:
Definition of done:
Progress state:
Known constraints:
Known non-goals:
Repository evidence:
Available references:
Ambiguities:
```

The router returns:

```text
ROUTING DECISION
Route:
Confidence:
Reason:
Required inputs:
Starting point:
Stop condition:
Expected output:
Routing risks:
```

For questions, status, and coordination-only work, the router may return `DIRECT`. It never invokes a flow itself.

## Workflow handoff contract

After routing, the orchestrator delegates exactly one flow using:

```text
WORKFLOW HANDOFF
Route:
User request:
Goal:
Definition of done:
Why this route:
Progress state:
Prior artifacts:
Repository evidence:
Known constraints:
Required inputs:
Starting point:
Non-goals:
Stop condition:
Expected output:
```

Every public workflow agent also defines its role, required inputs, preconditions, scope gates, upstream skill sequence, non-goals, verification expectations, stop condition, and final output format.

## Progress management

The canonical coordination record is:

```text
.workflow/PROGRESS.md
```

It is managed only by:

```bash
python3 .opencode/workflows/scripts/workflow-progress.py <command> ...
```

The document tracks durable coordination state only:

- objective and definition of done;
- status, phase, active flow, and last outcome;
- constraints and non-goals;
- current handoff;
- decisions, artifacts, blockers, verification, and next action;
- a bounded recent event history.

It must not contain secrets, full chat transcripts, large tool output, or speculative implementation details.

Typical commands:

```bash
python3 .opencode/workflows/scripts/workflow-progress.py init \
  --title "Organization SSO" \
  --goal "Design and plan organization-level SSO" \
  --done "A spec and dependency-aware tickets exist"

python3 .opencode/workflows/scripts/workflow-progress.py show --compact
python3 .opencode/workflows/scripts/workflow-progress.py show --json
python3 .opencode/workflows/scripts/workflow-progress.py route --flow flow-feature --goal "Produce spec and tickets"
python3 .opencode/workflows/scripts/workflow-progress.py result --status completed --summary "Planning completed" --next "/flow-ticket #13"
```

Use `/flow-progress <request>` to inspect or update progress without starting unrelated engineering work.

## Use-case workflows

| Command | Outcome | Workflow boundary |
|---|---|---|
| `/flow` | Coordinate naturally through orchestrator → router → one selected flow | Direct work or one reviewed delegation |
| `/flow-progress` | Inspect or update `.workflow/PROGRESS.md` | Progress management only |
| `/flow-setup` | Configure tracker, triage labels, and domain-doc contracts | Setup only |
| `/flow-feature` | Align a multi-session feature, publish a spec, create tickets | Stops before implementation |
| `/flow-feature-resume` | Resume feature planning from checkpoint/prototype handoffs | Stops after tickets |
| `/flow-small-change` | Align, implement, verify, review, and locally commit one bounded change | One commit, no push |
| `/flow-ticket` | Implement exactly one unblocked ticket/spec | One commit, no next ticket |
| `/flow-bugfix` | Build a red-capable loop, diagnose, regression-test, fix, review, commit | One verified bug fix |
| `/flow-triage` | Verify and move one raw issue/external PR through triage | No implementation |
| `/flow-large-project` | Run exactly one Wayfinder stage | One map stage per invocation |
| `/flow-architecture` | Alias for architecture scan | Survey only |
| `/flow-architecture-scan` | Produce an architecture report and candidate handoff | No design or production edits |
| `/flow-architecture-plan` | Turn one selected candidate into design/spec/tickets | No implementation |
| `/flow-prototype` | Answer one design question with isolated throwaway code | Return handoff only |
| `/flow-research` | Produce one cited primary-source artifact | No planning or production edits |
| `/flow-research-plan` | Convert existing research into a decision and optional spec/tickets | No implementation |
| `/flow-conflicts` | Resolve and verify the current merge/rebase conflict | Completes one git operation |
| `/flow-review` | Coordinate independent Standards and Spec reviews | Read-only findings |
| `/flow-adversarial-review` | Run a high-risk multi-expert challenge and synthesis gate | Review artifacts only; no source edits |

## High-risk adversarial review

Use for explicit requests or C3/C4 work with significant ambiguity, blast radius, irreversibility, security/auth/data/API impact, migration risk, or operational risk.

```text
/flow-adversarial-review <target, case, objective, constraints, and risk rationale>
```

Process:

```text
Eligibility gate
  → Review charter and evidence pack
  → 3–6 independent expert reviews
  → Finding normalization
  → Challenger review for Critical/High findings
  → Conflict adjudication only where needed
  → Independent synthesis
  → FINAL.md validation
```

The workflow avoids all-to-all discussion. Important findings are challenged individually, while only conflicting findings receive additional adjudication.

Review workspaces live under:

```text
.workflow/reviews/<review-id>/
```

Case templates cover:

- design direction and boundaries;
- code/document evaluation and reinforcement;
- debug fix direction, scope, impact, and regression seam;
- refactor as-is/to-be, migration stages, compatibility, and rollback;
- API/data contracts, migration, integrity, rollout, and rollback.

See `ORCHESTRATOR_DESIGN.md`, `ADVERSARIAL_REVIEW_DESIGN.md`, and `ADVERSARIAL_REVIEW_TEMPLATES.md`.

## Context supplied by commands

Every direct slash command provides:

- workflow role;
- unmodified `$ARGUMENTS`;
- one observable objective;
- required starting context;
- exact stop condition;
- a bounded read-only snapshot from `repo-context.sh`;
- progress state where coordination continuity matters.

The router does not construct repository context. The orchestrator owns that responsibility.

## Helper scripts

| Script | Purpose |
|---|---|
| `repo-context.sh` | Git-root-aware bounded context; routing, implementation, and review modes; optional JSON and focus paths |
| `workflow-preflight.sh` | Checks selected upstream skills and workflow-specific setup requirements; text or JSON output |
| `detect-checks.sh` | Suggests evidence-backed verification commands without executing them; does not infer pytest from `tests/` alone |
| `workflow-progress.py` | Atomically manages `.workflow/PROGRESS.md` and its machine state |
| `adversarial-review.py` | Creates review workspaces and registers findings, challenges, final dispositions, and validation |
| `configure-models.py` | Applies tier or per-agent model overrides; supports dry-run and validation |
| `verify-bundle.py` | Validates bundle definitions, permissions, references, hidden-agent isolation, scripts, and contracts |
| `doctor.py` | Diagnoses an installed project, upstream skills, setup, executability, and local environment |
| `verify.py` | Compatibility wrapper around bundle verification and environment diagnosis |

See `SCRIPT_REVIEW_IMPLEMENTATION.md` for the script changes and their rationale.

## Permission design

All agents begin with:

```yaml
permission:
  "*": deny
```

Then each role opts into only what it needs.

Important boundaries:

- Orchestrator: bounded reads, progress/context scripts, git inspection, router plus explicit flow allowlist; no edits, web, or skills.
- Router: no tool access at all; pure classification.
- Planning: common documentation/tracker paths allowed; other edits ask.
- Research: web access, writes restricted to research artifacts.
- Prototype: automatic writes only under `.scratch/prototypes/**`; other edits ask.
- Architecture scan and review: no production edits.
- Implementation: edits and common checks allowed; push, reset, clean, destructive deletion, privilege escalation, PR merge, and repository deletion denied.
- Adversarial experts: hidden and read-only; coordinator may only write review artifacts.
- External-directory access denied everywhere.

See `SECURITY_AND_PERMISSIONS.md`.

## Per-agent models

Agent frontmatter supports `model: provider/model-id`. Models are unset by default so subagents inherit the invoking primary model.

```bash
cp models.example.json models.local.json
python3 configure-models.py models.local.json /path/to/project --dry-run
python3 configure-models.py models.local.json /path/to/project --backup
```

Use tier assignments for router, planning, coding, review, research, and prototype roles, with per-agent overrides where needed. See `MODEL_GUIDE.md`.

## Install

```bash
./install.sh /path/to/project
./install-original-skills.sh /path/to/project
```

The installer maintains a managed-file manifest, removes stale bundle-managed files, and preserves user-modified managed files under:

```text
.opencode/workflows/backups/<timestamp>/
```

The upstream installer is interactive. Select the skills listed in `UPSTREAM_SKILLS.md`.

Run setup once:

```text
/flow-setup
```

## OpenCode layout

```text
.opencode/
  agents/
    flow-orchestrator.md
    flow-router.md
    flow-*.md
  commands/
    flow.md
    flow-progress.md
    flow-*.md
  workflows/
    scripts/
      repo-context.sh
      workflow-preflight.sh
      detect-checks.sh
      workflow-progress.py
      adversarial-review.py
    configure-models.py
    models.example.json
    ORCHESTRATOR_DESIGN.md
    ADVERSARIAL_REVIEW_DESIGN.md
    ADVERSARIAL_REVIEW_TEMPLATES.md
    SCRIPT_REVIEW_IMPLEMENTATION.md
    MODEL_GUIDE.md
    WORKFLOW_CONTRACTS.md
    SECURITY_AND_PERMISSIONS.md
```

## Recommended use

```text
/flow-setup
/flow Add organization-level SSO
```

The orchestrator may select feature planning, a small change, bugfix, research, review, or another flow. For ticket execution, each ticket remains a fresh bounded workflow:

```text
/flow Implement ticket #13
```

Direct commands remain available:

```text
/flow-feature <idea>
/flow-ticket <ticket-reference>
/flow-adversarial-review <review target>
```

## Validation

```bash
python3 verify-bundle.py
python3 doctor.py /path/to/project
opencode debug config
```

`opencode debug config` requires the OpenCode CLI and is the final runtime configuration check.
