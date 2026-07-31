---
gsd_state_version: 1.0
milestone: v2.7
milestone_name: Real-Target Adoption
status: verifying
last_updated: "2026-07-31T18:03:39.185Z"
last_activity: 2026-07-31
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 9
  completed_plans: 6
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-30)

**Core value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다 — "어떻게 개발·유지보수·리팩토링하는가"가 실행 가능한 스킬·커맨드·훅으로 박혀 있다.

**Current focus:** Phase 52 — Evidence-Bounded Real-Target Adoption
2026-08-01. All 6 plans landed. 52-06 read the adopted worktree's own package facts and
convention profiles (SC-2/SC-3/SC-4 proven with literal values), proved the original
`develop` checkout byte-unchanged both immediately after the run and after disposal (no
drift this time — no `external-drift.json` needed), disposed the worktree (exit 0), and
wrote `52-ADOPTION-EVIDENCE.md` with the complete OBS-D-01..04 trace ledger (SC-5). Phase 52
is ready for phase-level verification against `51-BASELINE-EVIDENCE.md`'s OBS-D-01..04.

## Current Position

Phase: 52 (Evidence-Bounded Real-Target Adoption) — READY FOR VERIFICATION
Plan: 6 of 6 (52-06 complete — the phase record, after-proof, and worktree disposal all
landed; see `52-06-SUMMARY.md` and `52-ADOPTION-EVIDENCE.md`)
Status: Phase complete — ready for verification
Last activity: 2026-08-01
worktree of FeedbackOps was provisioned at the run-time develop HEAD (re-read live as
`919d152a56ed096c0fdef12b9bfb892d6ef4ced6` — third movement past both the Phase-51 baseline
`1d1c8ed` and the STATE.md-carried `4f16525`, attributed as expected third-party drift per
D-02). Discover enumerated exactly the five real pnpm workspace members and recorded
`docs/design-prototype/package.json` as `excluded: "non-workspace-member"` (SC-2/RTA-02 proven
on the real target). Draft wrote an unedited batch plus a target-derived `languages.toml`
sidecar. Apply ran once (exit 0, applied=154/skipped=86/refused=23); the new phase-local
`scripts/compare-worktree-writes.py` (D-21) proved `matches: true`, zero product-code writes,
and the three lock sidecars declared rather than unlisted (OBS-D-04 real-target proof). The
`--target` mis-targeting guard was confirmed to fire on a synthetic mistargeted argv before being
trusted. The original FeedbackOps `develop` checkout stayed byte-identical to its before-proof
throughout; no harness code was touched (`git diff --quiet` on `tools/`/`harness/`/`contracts/`);
full suite still green (1023 passed). The fresh worktree was deliberately left in place — 52-06
owns the after-proof and disposal.

Plan 52-06 complete (see 52-06-SUMMARY.md and 52-ADOPTION-EVIDENCE.md): `build_facts` and
`conventions_for` ran against the worktree with the target passed explicitly, proving SC-2/SC-3/
SC-4 with literal captured values (`package-facts.json` shows six packages — five real members
plus `docs/design-prototype`, the expected unscoped `build_facts` result; both `packages/shared`
runtime edges present; every JS package's `lint`/`test` non-null). The original checkout's
after-proof was byte-identical to 52-05's before-proof (no third-party drift this run, so no
`external-drift.json` was needed); the worktree was disposed (`worktree remove --force`, exit 0)
and confirmed absent from the final worktree list. `52-ADOPTION-EVIDENCE.md` records SC-1..SC-5
each with a quoted deciding value and the complete OBS-D-01..04 trace ledger (every cited pytest
node id executed and confirmed passing). Full suite still green (1023 passed); contract-drift OK;
contract count unchanged at 6.

Prior: Plan 52-02 complete (see 52-02-SUMMARY.md): `tools/adoption_scan/
detect.py` gained a pure, filesystem-free `parse_pnpm_workspace_globs`/`is_workspace_member`
pair (pnpm-workspace.yaml deliberately NOT registered in `_MANIFEST_KIND_BY_NAME` — taught as
its own constant + parser instead, per the interfaces section's documented deviation from D-07's
literal wording), and `scan.build_inventory` now scopes `manifests`/`candidate_process_boundaries`
to a target's declared pnpm workspace members, recording any non-member manifest as excluded
with reason `non-workspace-member` (the D-20 enum value ratified in 52-01). The no-workspace-
manifest path (`tmp_minirepo`) stays byte-identical (D-10, proven by a captured pre-change digest

+ the untouched committed snapshot). `_dependencies_from_package_json` (the REFUTED OBS-03 site)

is provably untouched via a source-digest pin. One test-quality deviation recorded: two of the
plan's own proposed mutation-check negative controls were structurally unreachable ("checks that
cannot fail") and were replaced with genuinely discriminating cases, each confirmed by an
observed-RED-then-reverted mutation (see 52-02-SUMMARY.md). Full suite green (1023 passed, up
from 1006). OBS-D-01 is now repaired at the source (RTA-02).

Earlier: Plan 52-04 complete: the 3 marker-merge `.lock`
sidecars are declared as known harness-managed artifacts (`lock_sidecar_for`/`expected_lock_sidecars`/
`HARNESS_MANAGED_LOCK_SIDECARS`, checked against the real filesystem, never unlinked — D-15), a
sidecar left over from a prior run is announced on stderr with wording that claims only provenance,
never "stale" (D-16), and OBS-D-02's `workspace:*`/`workspace:^` edge resolution is locked in by a
regression test with zero production change (D-18). All three observed-RED mutation checks
confirmed (quoted in 52-04-SUMMARY.md). Full suite green (1006 passed, up from 997).

Earlier: Plan 52-03 complete: `conventions_for()` now returns a permanent `lint` key (OBS-D-03/D-11),
and an adopted pnpm target's JavaScript lint/test commands are derived from that target's own
`package.json` scripts at draft time and spliced into the applied `harness/project.toml` (D-12) —
proven by a repo-local end-to-end test. The W-10 Phase-53 re-run consequence (the spliced file no
longer matches `harness_proposed_hashes()`, so a future managed re-run classifies it `conflict` not
no-op) is recorded, not fixed.

Earlier: Plan 52-01 complete: `non-workspace-member`
enum value landed on `inventory.schema.json` via the human-authorized constitution-plane path
(GOLDEN_APPROVE_HUMAN), hash baseline + derived plane regenerated, full suite green (981 passed).

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

- **D-15/D-16 known limitation, recorded for Phase 53 (52-04):** the marker-merge lock-sidecar
  prior-run stderr report cannot distinguish a normal re-run from a crash-interrupted one — under
  D-15's no-unlink rule the sidecar exists on every run after the first. It is a provenance signal,
  not a staleness detector; Phase 53's re-run semantics inherit this as a known gap.

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
