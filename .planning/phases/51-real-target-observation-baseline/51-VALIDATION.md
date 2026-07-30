---
phase: 51
slug: real-target-observation-baseline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-31
---

# Phase 51 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `51-RESEARCH.md` §"Validation Architecture".
>
> **Phase shape:** this is an **observation-only** phase. There is no application code to unit-test;
> the deliverable is an evidence record about what a real run produced. A **failing** adoption run
> and a **refuted** OBS-03 hypothesis are both PASSES.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — no application code is written. Validation = evidence-record internal consistency + re-runnability + the no-source-edit guard. |
| **Config file** | none |
| **Quick run command** | `git status --porcelain -- tools/ harness/ contracts/ docs/adr/` (must be EMPTY — the NG-01 / D-11 no-repair guard) |
| **Full suite command** | `uv run pytest` (repo regression suite — must stay green; this phase must not change its result) + manual replay of every argv recorded in `51-BASELINE-EVIDENCE.md` `reproduction` fields |
| **Estimated runtime** | quick ~1s · full suite ~minutes · manual replay ~10 min |

---

## Sampling Rate

- **After every task commit:** `git status --porcelain -- tools/ harness/ contracts/ docs/adr/` is
  empty, AND every changed path is under `.planning/phases/51-real-target-observation-baseline/`.
- **After every plan wave:** before/after isolation digests are recorded and equal; the
  `OBS-D-NN` summary table matches the detail sections 1:1 (no orphan ids either direction).
- **Before `/gsd:verify-work`:** `51-BASELINE-EVIDENCE.md` exists with a non-empty
  `## OBS-03 verdict` section containing a literal quoted output excerpt + `path:line`; and
  `git -C ~/Desktop/2026/FeedbackOps worktree list` shows no leftover Phase-51 worktree (D-04).
- **Max feedback latency:** < 5 seconds for the per-task guard.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 51-01-* | 01 | 1 | OBS-01 (SC-1) | T-51-01 | Worktree writes are confined to the isolated worktree path; original `develop` checkout never written | evidence-diff | `diff before.status.txt after.status.txt && diff before.index.sha256 after.index.sha256 && diff before.untracked-set.sha256 after.untracked-set.sha256` | ❌ W0 — the six digests are this phase's own output | ⬜ pending |
| 51-02-* | 02 | 2 | OBS-01 (SC-2) | T-51-02 | Captured stdout/stderr carries no secret from the target repo into this repo's evidence | structural review | `grep -c '^### OBS-D-' 51-BASELINE-EVIDENCE.md` equals the summary-table row count; each record read for non-empty `symptom` / `reproduction` / `code location` | ❌ W0 — the record is the deliverable | ⬜ pending |
| 51-03-* | 02+ | 2 | OBS-03 (SC-3) | — | N/A | evidence review | `grep -A5 '## OBS-03 verdict' 51-BASELINE-EVIDENCE.md` returns a verdict + literal excerpt; verdict is one of confirmed / refuted | ❌ W0 | ⬜ pending |
| all | all | all | SC-4 (no repair precedes evidence) | — | No source mutation under gated planes | automated | `git status --porcelain -- tools/ harness/ contracts/ docs/adr/` → empty at every commit | ✓ standard git | ⬜ pending |
| all | all | all | regression floor | — | N/A | automated | `uv run pytest` stays green (this phase changes no code, so any new failure is external) | ✓ existing suite | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.planning/phases/51-real-target-observation-baseline/evidence/isolation/{before,after}.{status.txt,index.sha256,untracked-set.sha256}` — the six isolation-proof artifacts (D-03).
- [ ] `.planning/phases/51-real-target-observation-baseline/evidence/` — per-stage argv/cwd/exit-code/stdout/stderr capture + the run's `inventory.json` / `plan.json` / `manifest.json`.
- [ ] `.planning/phases/51-real-target-observation-baseline/51-BASELINE-EVIDENCE.md` — the OBS-01 deliverable.

No framework install is needed — there is no application code. The only Wave-0 "gaps" are the
evidence artifacts themselves, which this phase's tasks create as their primary output.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Each `OBS-D-NN` record carries a non-empty symptom, reproduction, and `path:line` code location | OBS-01 | Automating it needs a parser for the evidence format — **D-09 forbids adding one** (NG-01) | Read `51-BASELINE-EVIDENCE.md`; for each `### OBS-D-NN`, confirm all three fields present and the `path:line` resolves in this checkout |
| OBS-03 verdict is decided by a literal captured output excerpt, not by code reading | OBS-03 | Judgement about whether the quoted excerpt actually decides the claim | Read `## OBS-03 verdict`; confirm the excerpt is quoted from a file under `evidence/` and that confirmed/refuted follows from it |
| Reproduction fields are actually replayable | OBS-01 | Requires a fresh worktree and real command execution | Create a throwaway worktree, replay each recorded argv, compare exit codes and key JSON fields to the recorded excerpts |
| Byte-unchanged proof is honest, not trivially true | SC-1 | Requires reasoning about scope (tracked index + untracked path set; `.git/worktrees/` metadata is expected to change and must be stated, not hidden) | Confirm the proof's stated scope is written down in the record and that `git worktree add`'s own metadata effect on the original checkout is disclosed rather than silently excluded |

---

## Validation Sign-Off

- [ ] Every task has an automated verify or a declared Wave-0 dependency
- [ ] Sampling continuity: the no-source-edit guard runs on EVERY task commit (no 3-task gap possible)
- [ ] Wave 0 covers all MISSING references (isolation digests, evidence capture, evidence record)
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s for the per-task guard
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
