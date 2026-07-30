---
gsd_state_version: 1.0
milestone: v2.7
milestone_name: Real-Target Adoption
status: Defining requirements
last_updated: "2026-07-30T15:59:40.970Z"
last_activity: 2026-07-30 — Milestone v2.7 started
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-30)

**Core value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다 — "어떻게 개발·유지보수·리팩토링하는가"가 실행 가능한 스킬·커맨드·훅으로 박혀 있다.

**Current focus:** none — **v2.6 Minimal Monorepo Core shipped 2026-07-30** and is archived. Next
step is `/gsd:new-milestone` to scope the next cycle.

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-07-30 — Milestone v2.7 started

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
