# Phase 51: Real-Target Observation Baseline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-31
**Phase:** 51-real-target-observation-baseline
**Mode:** `--auto --chain` — all gray areas auto-selected, every question answered with the
recommended default. No interactive prompts were shown.
**Areas discussed:** Worktree provisioning + isolation proof, Evidence record location + shape,
Baseline run depth + failure policy, OBS-03 verdict method

---

## Worktree provisioning + isolation proof

| Option | Description | Selected |
|--------|-------------|----------|
| Detached worktree outside the target checkout | `git worktree add --detach` at a sibling path; no branch of the real repo can advance | ✓ (recommended) |
| Worktree nested inside the `develop` working tree | Convenient, but adoption writes land inside the checkout being proved unchanged | |
| Full clone of FeedbackOps | Strongest isolation, but hides worktree-vs-checkout interactions the run should observe | |

**Auto-selected:** Detached sibling worktree — D-01.
**Notes:** Byte-unchanged proof (D-03) captured before *and* after as three artifacts: porcelain=v2
status, HEAD + tracked-index digest, untracked path-set digest. Untracked *content*
(`node_modules/`, `minio_data/`) deliberately excluded so the check stays deterministic. Worktree is
disposed after the record is complete; Phase 52 starts fresh (D-04).

---

## Evidence record location + shape

| Option | Description | Selected |
|--------|-------------|----------|
| `.planning/phases/51-.../` markdown + raw JSON | Phase-local, human-readable record plus committed raw outputs; adds no plane member | ✓ (recommended) |
| A new contract + schema for defect records | Machine-validatable, but adds a 7th contract — violates NG-01 | |
| An ADR per defect | Constitution plane; ADRs are decisions, not observations | |

**Auto-selected:** Phase-local markdown + `evidence/` raw JSON — D-06.
**Notes:** Fixed per-defect field set with stable `OBS-D-NN` ids (D-07); purpose tags ①②③④ recorded
as *proposals* only, binding triage deferred to Phase 52 (D-08); no new parser or schema (D-09).
Stable ids matter because Phase 52's traceability requirement cites them.

---

## Baseline run depth + failure policy

| Option | Description | Selected |
|--------|-------------|----------|
| Push all three stages, record each failure, continue | Maximum evidence per run; blocked stages recorded as `blocked-by` defects | ✓ (recommended) |
| Stop at first failure | Cheapest, but yields one defect per run and hides downstream behavior | |
| Hand-patch inputs so later stages run | Would produce output the shipped harness never produces — destroys the evidence | |

**Auto-selected:** Push all stages, no repairs, no hand-edited inputs — D-10, D-11.
**Notes:** Post-apply read-only observation of `package_facts` and `conventions_for` included even
though RTA-03/04 belong to Phase 52 — that is where the ②③ purpose defects surface (D-12).
Reproducibility metadata (harness SHA, target SHA, tool versions, argv, cwd, exit codes) is
mandatory in the record header (D-13).

---

## OBS-03 verdict method

| Option | Description | Selected |
|--------|-------------|----------|
| Read the verdict off the real run's own output | Evidence-first; confirmed = version string / missing edge, refuted = edge already recorded | ✓ (recommended) |
| Build a synthetic pnpm fixture and test against it | Faster to iterate, but proves something about a fixture, not about the real target | |
| Decide from code reading alone | Cheapest, but the requirement demands a reproducible verdict | |

**Auto-selected:** Evidence-first from the real run — D-14.
**Notes:** Verdict section quotes the literal deciding output plus `path:line` (D-15). Member
discovery (`pnpm-workspace.yaml` absent from `_MANIFEST_KIND_BY_NAME`,
`tools/adoption_scan/detect.py:46-50`) and dependency-edge recording (`workspace:^` swallowed as a
version string) are tracked as **separate** defect ids even if one masks the other (D-16). No
fixture committed in Phase 51 (D-17). Refutation closes OBS-03 successfully.

---

## Claude's Discretion

- Exact worktree path and evidence sub-file naming.
- One log file per command vs a combined transcript, provided argv/cwd/exit-code stay recoverable.
- How finely a compound failure is split into `OBS-D-NN` ids, guided by "separate causes get
  separate ids".

## Deferred Ideas

- Repairs of observed defects → Phase 52 (OBS-02), each with a regression test.
- Committing a minimal pnpm-workspace reproduction fixture → Phase 52, paired with its repair.
- Managed `/adopt` install→update behavior → Phase 53 (MONO-12).
- DEBT-01 shared `"dir"`-filter helper → Phase 54.
- Second target repo (vocpage) → out of v2.7 until FeedbackOps adoption completes.
- Any change to FeedbackOps product code → out of milestone scope.

## Todos

No pending todos matched Phase 51 (`todo.match-phase` returned 0 matches).
