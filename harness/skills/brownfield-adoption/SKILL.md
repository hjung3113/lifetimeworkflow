---
name: brownfield-adoption
description: >-
  Use when you need to bring an existing (brownfield) repository under this harness's contract-first
  conventions — teaches the discover, draft, apply lifecycle for an UNKNOWN target tree whose
  contracts are not yet known, backed by tools.adoption_scan and tools.adoption_apply. Review of an
  applied batch happens at the PR (ADR-0012), not as a gated stage inside the pipeline. Consult when
  planning how to onboard a repo, not when the contracts already exist and only need authoring or
  checking.
---

# brownfield-adoption

**Why this is a new skill, not an extension of an existing one:** none of this harness's other
skills (`python-conventions`, `data-contracts`, `harness-author`,
`polyglot-boundary`, `two-plane-memory`, `fan-out-synthesize`,
`context-budget`) own the discover→draft→apply adoption lifecycle. The closest
candidate — `data-contracts` — is about authoring or checking contracts already
known to exist, not about discovering an UNKNOWN brownfield tree and proposing what its contracts
might be. That is a genuinely disjoint routing trigger, so a new skill directory is justified
(harness-author Step 0).

This skill teaches the three-stage adoption runbook: a target repository is scanned read-only, a
task-local batch drafts what would change, and the batch is then safely applied to the target — no
gated review stage sits between draft and apply, and no `decisions` (or similar) artifact is
produced or consumed anywhere in the pipeline. Review happens where every other change in this
harness is reviewed: at the PR that carries the applied batch (ADR-0012).

## Stage 1: discover

`tools.adoption_scan` walks a target tree **read-only** and writes `inventory.json`/`plan.json`/
`manifest.json` to a required, target-external `--out` directory (never inside the target — an
adoption scanner that wrote inside its own scanned target could see its own prior output as target
content on a second run). The manifest resolves every catalog destination to exactly one of six
dispositions (`create`/`preserve`/`conflict`/`marker-merge`/`derived-regenerate`/
`human-ratification-required`) via a total, ordered rule chain — never a silent default.

## Stage 2: draft

`tools.adoption_apply.batch.create_or_resume_batch` creates, or safely resumes, a task-local batch
under `<task-dir>/artifacts/adoption/<batch-id>/`. The batch id is content-derived from
`(target_ref, discover-time UTC date)`: a same-day re-discover against an unchanged `target_ref`
resumes the SAME batch directory without mutating it. Every write during drafting is confined to
the batch root — `tools.adoption_apply.apply.refuse_if_outside_root` refuses both a direct
out-of-root write and a `..`-traversal escape attempt.

## Stage 3: apply

`tools.adoption_apply.apply.apply_manifest` applies the batch's dispositions against a target
root: atomic and collision-safe (`create` never silently overwrites), idempotent (a second apply
against an unchanged target is a no-op), and structurally refuses every constitution-plane
(`contracts/` · `docs/adr/` · `docs/glossary.md`) destination before any filesystem write — independent of
any Claude tool-call hook, since a bare CLI/CI invocation has no hook in the loop at all.

Re-running a batch manages the files `/adopt` previously installed, recorded at the target's
`.harness/adoption/installed.json`: unchanged source and target means no writes and an
`applied=0 updated=0 unchanged=N conflicts=0` summary; changed harness content updates its managed
file; and a target-side edit is reported on stderr as a conflict while that file remains
byte-unchanged. Conflicts leave other safe rows running and do not change the command's exit status;
the drafted `manifest.json` is the conflict report.

## Related

- `harness/commands/adopt.md` — the `/adopt` command invokes each stage's module by a fixed
  `python -m tools.adoption_scan`/`tools.adoption_apply <sub-verb>` argv form.
- `harness/skills/data-contracts/SKILL.md` — authoring/checking contracts already known to exist,
  the disjoint sibling concern this skill does not cover.
