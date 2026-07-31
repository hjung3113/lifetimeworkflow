---
gsd_state_version: 1.0
milestone: v2.7
milestone_name: Real-Target Adoption
status: executing
last_updated: "2026-07-31T17:01:05.839Z"
last_activity: 2026-07-31
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 9
  completed_plans: 1
  percent: 11
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-30)

**Core value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다 — "어떻게 개발·유지보수·리팩토링하는가"가 실행 가능한 스킬·커맨드·훅으로 박혀 있다.

**Current focus:** Phase 52 — Evidence-Bounded Real-Target Adoption
2026-07-31, verified 4/4. Next is Phase 52 (Evidence-Bounded Real-Target Adoption), whose sole input
contract is `51-BASELINE-EVIDENCE.md`'s OBS-D-01..04.

## Current Position

Phase: 52 (Evidence-Bounded Real-Target Adoption) — EXECUTING
Plan: 2 of 6
Status: Ready to execute
Last activity: 2026-08-01 -- Plan 52-01 complete (see 52-01-SUMMARY.md): `non-workspace-member`
enum value landed on `inventory.schema.json` via the human-authorized constitution-plane path
(GOLDEN_APPROVE_HUMAN), hash baseline + derived plane regenerated, full suite green (981 passed).
Plan 52-02 is next.

**Phase 51 outcome — OBS-03 REFUTED (a milestone output, not a failure).** `tools/adoption_scan/
detect.py:273` discards dependency version strings and matches by package name, so pnpm `workspace:*`
already resolves correctly; both `@fops/frontend → @fops/shared` and `@fops/backend → @fops/shared`
runtime edges were captured. Phase 52 must NOT spend budget repairing this. Four defects recorded as
OBS-D-01..04 (stable ids; do not renumber).

**Carried into Phase 52:**

- Phase 52 SC-4 wants lint + test commands, but `conventions_for`
  (`tools/harness_config/loader.py:297`) has **no `lint` key at all** — a shape change, not a null to
  populate. Traces to OBS-D-03.

- Re-pin the target SHA: FeedbackOps `develop` is now `4f16525`, six commits past the `1d1c8ed`
  baseline; the Phase-51 worktree is disposed, so Phase 52 starts from a fresh one (D-04).

- **Verification override (human-directed, recorded):** ROADMAP SC-1's "byte-unchanged" is satisfied
  in substance but not literally — the target's `develop` advanced six times mid-run from unrelated
  third-party work. Index digests were independently reconstructed from the target's commit trees,
  proving 100% of the delta is commit movement and 0% is a Phase-51 write. Attributed in
  `evidence/isolation/external-drift.json`, deliberately kept out of the OBS-D namespace.

## Blockers/Concerns

[Issues that affect future work]

- **[BLOCKED — carried] MONO-12 / phase 50b (managed `/adopt` install-update):** blocked on a hard
  *external* precondition — a real multi-package target repo. This checkout has only synthetic
  targets (three adoption fixtures + the in-repo 2-member demo workspace), and `/adopt` writes into
  its target, so unrelated repos were not used. **Human action:** name a real multi-package target
  repo, then re-plan phase 50b against it. Nothing in the code is missing.

- **[Tech debt — v2.6]** the `"dir"`-key filter adapter is copy-duplicated between
  `tools/harness_config/loader.py:conventions_for()` and `tools/contract_graph/impact.py:report()`.
  Verified not divergent today; a shared helper would remove the drift risk.

- **[Tech debt — v2.6]** `/impact` cannot distinguish a typo'd contract path from a
  tracked-but-unwired one while the contract graph is empty; they separate once relationships exist.

- **[Tech debt — v2.6]** the citation gate exempts fenced code blocks, and numeric-range citations
  verify the anchor falls inside the range rather than matching content exactly.

- **[BLOCKING — carried from Phase 1] BOOT-01 .NET 10 install egress-denied:**
  `tools/bootstrap/install.sh` + `verify.sh` are committed and correct, but the .NET 10 download
  hosts are blocked by this container's egress policy. **Human action:** allowlist those hosts (or
  ship a pre-installed .NET 10), then run `bash tools/bootstrap/install.sh && bash
  tools/bootstrap/verify.sh`. All .NET-side execution stays gated until then.

- Research flag: opencode.ai is proxy-403'd; re-verify hook event names, the permission-matrix
  semantics and skill size caps against live docs when next touching those surfaces.

## Notes

Full v2.6 history: `.planning/milestones/v2.6-ROADMAP.md`, `.planning/milestones/v2.6-REQUIREMENTS.md`,
`.planning/milestones/v2.6-phases/`, audit at `.planning/v2.6-MILESTONE-AUDIT.md`.
