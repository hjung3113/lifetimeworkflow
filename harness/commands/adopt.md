---
description: >-
  Use when a human wants to bring an existing (brownfield) repository under this harness's
  contract-first conventions — discovers the target tree and drafts a task-local inventory/plan/
  manifest batch, then applies dispositions safely (atomic, collision-safe, refusing any
  constitution-plane destination before any write). Review of the batch's decisions happens at
  the PR, not inside this command. Invoke to discover, draft, or apply an adoption batch.
agent: orchestrator
subtask: true
---

# /adopt — brownfield adoption: discover, draft, apply

Thin macro over the **already-coded** adoption pipeline. Do NOT re-implement discovery, drafting,
or application logic — `tools.adoption_scan` (discovery) and `tools.adoption_apply` (task-local
batch drafting, atomic/collision-safe apply) already encode the full workflow (ADOPT-04..07).

## Sub-verbs

`$ARGUMENTS` carries the sub-verb as its first token, followed by that sub-verb's own flags, passed
**positionally** to the underlying module — never interpolated into a constructed shell string:

### discover

Read-only scan of a target tree into `inventory.json`/`plan.json`/`manifest.json` under a
required, target-external `--out` directory:

!`python -m tools.adoption_scan $ARGUMENTS`

### draft

Create-or-resume a task-local adoption batch — writes the same three artifacts confined to
`<task-dir>/artifacts/adoption/<batch-id>/`, never outside that root:

!`python -m tools.adoption_apply draft $ARGUMENTS`

### apply

Apply a drafted batch's manifest dispositions against a target root — atomic, collision-safe,
idempotent; refuses any constitution-plane (`contracts/` · `docs/adr/` · `docs/glossary.md`) destination
before any write:

!`python -m tools.adoption_apply apply $ARGUMENTS`

## Notes

- **No arbitrary command execution.** Every invocation above is a fixed `python -m
  tools.adoption_scan`/`tools.adoption_apply <sub-verb>` argv form; `$ARGUMENTS` is passed
  positionally, never woven into a shell string built from manifest/draft/scanned content.
- **Discovery is read-only**; `apply` never touches the constitution plane. Review of an applied
  batch's decisions happens at the PR that carries it, not inside this command. See
  `harness/skills/brownfield-adoption/SKILL.md` for the full discover/draft/review/apply runbook.
