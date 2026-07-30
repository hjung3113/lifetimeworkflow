---
phase: 51
slug: real-target-observation-baseline
status: approved
nyquist_compliant: true
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
| **Full suite command** | `uv run --frozen pytest` (repo regression suite — must stay green without rewriting `uv.lock`) + manual replay of every argv recorded in `51-BASELINE-EVIDENCE.md` `reproduction` fields |
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
- **Max feedback latency:** < 5 seconds for each auto task's leading source guards; the final
  `uv run --frozen pytest` phase gate is intentionally a minutes-scale full-suite exception.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 51-01-01 | 01 | 1 | OBS-01 (SC-1) | T-51-04 | Capture real pre-run SHAs/digests; current checkout HEAD may differ from develop | content assertions | 40-hex/64-hex greps + non-empty digest checks + no-source-edit guard | ❌ W0 — evidence is created during execution | ⬜ pending |
| 51-01-02 | 01 | 1 | OBS-01 (SC-1) | T-51-01 | Approval only; no command, file write, or commit | checkpoint:decision | Human selects `approve`; Task 51-01-03 performs the command | ✓ plan structure | ⬜ pending |
| 51-01-03 | 01 | 1 | OBS-01 (SC-1) | T-51-01 | Exact detached external worktree; five provision sidecars | command/content assertions | exit/sidecar checks + worktree SHA/detached/path checks + no-source-edit guard | ❌ W0 | ⬜ pending |
| 51-02-01 | 02 | 2 | OBS-01 (SC-1/2) | T-51-08 | Discover/draft captured independently; secret block occurs before commit; enumeration question recorded | command/content/security | sidecars + enumeration_mode/node_modules/minio_data assertions + secret scan + no-source-edit guard | ❌ W0 | ⬜ pending |
| 51-02-02 | 02 | 2 | OBS-01 (SC-1) | T-51-06 | Approval only; no apply command, evidence write, or commit | checkpoint:decision | Human selects `approve` or `defer`; Task 51-02-03 records either outcome | ✓ plan structure | ⬜ pending |
| 51-02-03 | 02 | 2 | OBS-01 (SC-1/2) | T-51-06/07/08 | Apply or blocked outcome has five sidecars; changed paths are data-bearing; secret block precedes commit | command/content/security | sidecars/blocked id + changed-path keys/boolean + secret scan + no-source-edit guard | ❌ W0 | ⬜ pending |
| 51-02-04 | 02 | 2 | OBS-01, OBS-03 (SC-2/3) | T-51-08/09 | Target-explicit package-facts and conventions captures; secret block precedes commit | command/content/security | two JSON parses + eight sidecar checks + positive/negative repo anchor + secret/source guards | ❌ W0 | ⬜ pending |
| 51-02-05 | 02 | 2 | OBS-01, OBS-03 (SC-1/3) | T-51-08/10 | Hardcoded five members/three edges; convention keys; shaped after-proof; four isolation booleans | evidence assertions | member/edge/result/convention greps + after SHA/digest checks + secret/source guards | ❌ W0 | ⬜ pending |
| 51-03-01 | 03 | 3 | OBS-01, OBS-03 (SC-2/3) | T-51-15 | Summary/detail ids equal; every section has five fields; verdict word is present | structural evidence | `comm -3` id sets + per-section awk field check + scoped verdict grep + no-source-edit guard | ❌ W0 | ⬜ pending |
| 51-03-02 | 03 | 3 | OBS-01 (SC-1) | T-51-16 | Disposal approval only; no command, file write, or commit | checkpoint:decision | Human selects `approve`; Task 51-03-03 performs exact-path removal | ✓ plan structure | ⬜ pending |
| 51-03-03 | 03 | 3 | OBS-01 (SC-1) | T-51-16 | Exact worktree disposal and post-disposal re-capture of all four D-03 dimensions | command/content assertions | five sidecars + final SHA/digests + post_disposal booleans + no-source-edit guard | ❌ W0 | ⬜ pending |
| 51-03-04 | 03 | 3 | OBS-01, OBS-03 (SC-1..4) | T-51-12..17 | Final secret/id/verdict sweep; no source mutation; frozen regression run | phase gate | secret scan + id-set/verdict checks + `uv run --frozen pytest` + no-source-edit guard | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- **Run-produced:** `.planning/phases/51-real-target-observation-baseline/evidence/isolation/{before,after}.{status.txt,index.sha256,untracked-set.sha256}` — the six isolation-proof artifacts (D-03).
- **Run-produced:** `.planning/phases/51-real-target-observation-baseline/evidence/` — per-stage argv/cwd/exit-code/stdout/stderr capture + the run's `inventory.json` / `plan.json` / `manifest.json`.
- **Run-produced:** `.planning/phases/51-real-target-observation-baseline/51-BASELINE-EVIDENCE.md` — the OBS-01 deliverable.

No framework install is needed — there is no application code. The only Wave-0 "gaps" are the
evidence artifacts themselves, which this phase's tasks create as their primary output.
Accordingly, `wave_0_complete: false` is intentional on this approved strategy: the unchecked
items are run-produced evidence deliverables, not missing test infrastructure or an unplanned gate.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Each `OBS-D-NN` record's cited `path:line` resolves and its field values are semantically non-empty | OBS-01 | Plan 51-03-01 now machine-checks id-set equality and exactly one of each field label per section with grep/awk; resolving citations and judging semantic content still require a reader, while D-09 continues to forbid adding a parser | Read `51-BASELINE-EVIDENCE.md`; for each `### OBS-D-NN`, follow the cited `path:line` and confirm the value describes the captured observation |
| OBS-03 verdict is decided by a literal captured output excerpt, not by code reading | OBS-03 | Judgement about whether the quoted excerpt actually decides the claim | Read `## OBS-03 verdict`; confirm the excerpt is quoted from a file under `evidence/` and that confirmed/refuted follows from it |
| Reproduction fields are actually replayable | OBS-01 | Requires a fresh worktree and real command execution | Create a throwaway worktree, replay each recorded argv, compare exit codes and key JSON fields to the recorded excerpts |
| Byte-unchanged proof is honest, not trivially true | SC-1 | Requires reasoning about scope (tracked index + untracked path set; `.git/worktrees/` metadata is expected to change and must be stated, not hidden) | Confirm the proof's stated scope is written down in the record and that `git worktree add`'s own metadata effect on the original checkout is disclosed rather than silently excluded |

---

## Validation Sign-Off

- [x] Every auto task has an automated verify; decision checkpoints perform no work and no commit
- [x] Sampling continuity: the no-source-edit guard runs in EVERY auto task before its commit
- [x] Wave 0 covers all MISSING references (isolation digests, evidence capture, evidence record)
- [x] `wave_0_complete: false` intentionally denotes run-produced evidence that cannot pre-exist execution; it is compatible with approval and `nyquist_compliant: true`
- [x] No watch-mode flags
- [x] Feedback latency < 5s for each leading per-task source guard; the final frozen full suite is the documented phase-gate exception
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-07-31
