---
phase: 52-evidence-bounded-real-target-adoption
plan: 06
subsystem: infra
tags: [adoption-scan, adoption-apply, memory-regen, harness-config, worktree-isolation, phase-close]

# Dependency graph
requires:
  - phase: 52-05
    provides: "Fresh detached FeedbackOps worktree pinned at 919d152a…, with discover/draft/apply captures and the apply-write comparison left for this plan to read"
provides:
  - "Target-explicit downstream observations (package-facts.json, conventions.json) proving SC-2/SC-3/SC-4 with literal captured values"
  - "The original develop checkout's after-proof: byte-identical to the before-proof, no external drift this run"
  - "Auto-disposal of the v27-52-adoption worktree (exit 0), with a post-disposal comparison confirming the original checkout stayed unmodified"
  - "52-ADOPTION-EVIDENCE.md: the phase record with SC-1..SC-5 verdicts and the complete OBS-D-01..04 trace ledger (SC-5)"
affects: [53]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Downstream library calls always pass repo_root=/cfg= explicitly, never a bare CLI default, so a green result cannot silently describe the harness checkout instead of the target (D-05/D-12 carried)."
    - "OBS-D trace ledger with executed-not-just-cited pytest node ids: every cell was run (uv run pytest <node id>) before being recorded, not merely referenced by name."

key-files:
  created:
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/downstream/*
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/isolation/after.*
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/isolation/comparison.json
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/disposal/*
    - .planning/phases/52-evidence-bounded-real-target-adoption/52-ADOPTION-EVIDENCE.md
  modified: []

key-decisions:
  - "No external-drift.json was written: unlike Phase 51, develop did not move during this plan's own window, so comparison.json's four booleans (status/head/index/untracked-set) are all true before AND after disposal — the plan's conditional attribution step correctly did not fire."
  - "downstream/member-comparison.json is a NEW file (not an overwrite of discover/member-comparison.json from 52-05): it restates the inventory's five-member verdict alongside build_facts's honest six-package count, with docs/design-prototype named as the expected unscoped non-member (W-5) rather than filtered out to manufacture a false five-way agreement."

requirements-completed: [RTA-01, RTA-03, RTA-04, OBS-02]

# Metrics
duration: ~30min active work
completed: 2026-08-01
---

# Phase 52 Plan 06: Downstream Observations, After-Proof, Disposal, and the Phase Record Summary

**The adopted FeedbackOps target's own package facts and convention profiles prove SC-2/SC-3/SC-4 with literal values, the original `develop` checkout is proven byte-unchanged (no drift this run), the worktree is disposed (exit 0), and `52-ADOPTION-EVIDENCE.md` closes the phase with every OBS-D-01..04 observation terminating in an executed, passing regression test.**

## Performance

- **Duration:** ~30 min active work
- **Tasks:** 3/3 completed
- **Files modified:** 27 created (0 modified) — 13 downstream evidence artifacts (Task 1), 6 isolation after-proof + 8 disposal artifacts (Task 2), 1 phase record (Task 3)

## Accomplishments

- **Task 1 — target-explicit downstream observations.** `build_facts(repo_root=<WORKTREE>)` and
  `conventions_for(pkg["dir"], cfg=<worktree cfg>, facts=<worktree facts>)` ran against the real
  worktree, both argv captures naming the worktree path explicitly (never a bare CLI default).
  `package-facts.json` shows six packages (five real workspace members plus
  `docs/design-prototype`, the expected unscoped `build_facts` result — W-5); the two
  `packages/shared` runtime edges (`@fops/frontend → @fops/shared`, `@fops/backend →
  @fops/shared`) are both present (`workspace-edge-comparison.json`:
  `both_runtime_edges_present: true`). Every package's convention profile, read from
  `<WORKTREE>/harness/project.toml` (`config_source` recorded), carries a non-null `lint`
  (`"pnpm run lint"`) and `test` (`"pnpm run test"`) — `convention-comparison.json`:
  `all_js_packages_have_lint_and_test: true`. The new `downstream/member-comparison.json`
  restates the inventory's five-member verdict alongside `build_facts`'s honest six-package
  count, reporting `six_packages_one_non_member: true` and stating plainly that this divergence
  is expected behavior of an unscoped code path, not an SC-2 failure.
- **Task 2 — after-proof and disposal.** The original checkout's `after.*` captures
  (status/HEAD/index/untracked-set/worktree-list) were byte-identical to the `before.*` captures
  from 52-05: `head_equal: true`, `index_equal: true`, `status_equal: true`,
  `untracked_set_equal: true` — no third-party `develop` movement occurred during this plan's
  window, so no `external-drift.json` was required (correctly; the plan's attribution step is
  conditional on a false boolean). `git worktree remove --force
  /Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-52-adoption` (the exact single-path form,
  no glob, no `prune`) exited `0`; the path no longer exists and is absent from
  `final.worktree-list.txt`. Post-disposal comparison confirms the original checkout stayed
  unmodified after disposal as well.
- **Task 3 — the phase record.** `52-ADOPTION-EVIDENCE.md` carries a reproducibility header, the
  isolation/drift section, one row per SC-1..SC-5 each quoting a literal value from its named
  evidence file, a complete OBS-D-01..04 trace ledger (every cell's pytest node id executed and
  confirmed passing — see below), OBS-03 restated as refuted-and-locked-in with zero Phase-52
  budget spent on it, a scope-fence statement (contract count still 6; command/skill counts
  unchanged) carrying the three Phase-53 consequences (W-10 `harness/project.toml` re-run
  classification, W-3 prior-run-report-is-provenance-not-staleness, W-5 `build_facts` unscoped),
  and the disposal result. The model-identifier guard was confirmed to fire on a genuine scratch
  identifier and stay clean on this file's mandated `.CLAUDE.md.lock` / `.claude/settings.json`
  mentions.
- Full suite green throughout: **1023 passed**, 8 snapshots passed; `contract-drift: OK`; contract
  count unchanged at 6.

## Task Commits

Each task was committed atomically:

1. **Task 1: Target-explicit downstream observations and the SC-2/SC-3/SC-4 verdicts** — `ef8fc9a` (feat)
2. **Task 2: Original-checkout after-proof with drift attribution, then auto-dispose the worktree** — `374646d` (feat)
3. **Task 3: Write the phase record and the SC-5 trace ledger** — `9b90a4f` (docs)

## OBS-D trace ledger node-id execution (quoted from `52-ADOPTION-EVIDENCE.md`, confirmed run here)

```
uv run pytest -q \
  tools/adoption_scan/tests/test_scan_exclusions.py::test_pnpm_non_member_manifest_excluded_and_absent_from_included_and_manifests \
  tools/adoption_scan/tests/test_scan_exclusions.py::test_pnpm_workspace_exactly_five_members \
  tools/memory_regen/tests/test_package_facts.py::test_workspace_star_dependency_edges_resolve_by_name \
  tools/harness_config/tests/test_conventions_for.py::test_lint_value_is_read_from_the_matched_language_row_not_hardcoded \
  tools/adoption_apply/tests/test_cli.py::test_end_to_end_pnpm_target_resolves_lint_and_test_through_real_config \
  tools/adoption_apply/tests/test_atomic_apply.py::test_expected_lock_sidecars_matches_filesystem_after_every_marker_merge \
  tools/adoption_apply/tests/test_atomic_apply.py::test_prior_run_lock_sidecar_is_reported_on_stderr
7 passed in 0.61s
```

## Files Created/Modified

- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/downstream/` — `package-facts.json`/`conventions.json` + argv/cwd/stderr/exit-code sidecars, `workspace-edge-comparison.json`, `convention-comparison.json`, `member-comparison.json` (new, distinct from `evidence/discover/member-comparison.json`)
- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/isolation/` — `after.*` captures, `comparison.json` (four booleans + `post_disposal` block)
- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/disposal/` — `argv.txt`/`cwd.txt`/`stdout.txt`/`stderr.txt`/`exit-code.txt`, `final.*` captures
- `.planning/phases/52-evidence-bounded-real-target-adoption/52-ADOPTION-EVIDENCE.md` — the phase record

## Decisions Made

See `key-decisions` in frontmatter above (no `external-drift.json` needed; the new
`downstream/member-comparison.json` file's honest six-vs-five reporting).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The phase record's own model-identifier-guard explanation paragraph tripped the guard it was documenting**
- **Found during:** Task 3, running the automated `<verify>` block
- **Issue:** The first draft of `52-ADOPTION-EVIDENCE.md` quoted the mandated verify check's
  literal `sed`/`grep` command line verbatim (including its `'claude|gpt|opus|sonnet|codex'`
  alternation pattern) to document B-2's confirmed-firing observation. Quoting the pattern's own
  literal text made the guard fire against the phase record itself, since the words in the
  regex's own source are, textually, exactly what it matches.
- **Fix:** Rewrote the paragraph to describe the guard's strip-then-match mechanism and the
  observed exit-code behavior in prose, without literally reproducing the alternation pattern's
  match terms. Re-ran the verify block: clean.
- **Files modified:** `.planning/phases/52-evidence-bounded-real-target-adoption/52-ADOPTION-EVIDENCE.md`
- **Verification:** `sed -E '...' "$F" | grep -Eiq 'claude|gpt|opus|sonnet|codex'` exits 1 (no match) against the corrected file; a separate scratch copy with an appended genuine model-identifier line was confirmed to still trip the same check (exit 0), proving the guard itself was not weakened.
- **Committed in:** `9b90a4f` (Task 3 commit, corrected before commit — no separate fix commit needed)

---

**Total deviations:** 1 auto-fixed (Rule 1 — a documentation self-reference bug caught by the plan's own verify step before commit, not a weakening of the guard).
**Impact on plan:** None — corrected before the Task 3 commit; the guard's discriminating power was independently re-confirmed against a genuine scratch identifier both before and after the fix.

## Issues Encountered

None beyond the one deviation above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 52 is complete: all six plans (52-01..52-06) landed, every Phase-51 OBS-D observation
  (OBS-D-01..04) terminates in an executed, passing regression test or an evidence-backed
  no-change confirmation, and SC-1..SC-5 are each backed by a quoted literal value from a named
  evidence artifact.
- Phase 53 (Managed Adopt Updates) can proceed with the three carried consequences already on
  record in `52-ADOPTION-EVIDENCE.md`'s scope-fence section: the `harness/project.toml` splice
  will classify as `conflict` on a Phase-53 re-run (W-10, expected, not a defect to chase); the
  prior-run lock-sidecar stderr report is provenance-only, never a staleness signal (W-3);
  `build_facts` remains an unscoped path reporting six packages on this real target (W-5).
- The worktree at `/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-52-adoption` is disposed;
  Phase 53 will need to provision its own fresh worktree per its own plan's decisions.
- Full suite green (1023 passed, 8 snapshots), `contract-drift: OK`, contract count unchanged at
  6, no harness code touched by this plan (only `.planning/` evidence and the phase record).

---
*Phase: 52-evidence-bounded-real-target-adoption*
*Completed: 2026-08-01*

## Self-Check: PASSED

All claimed files exist (`evidence/downstream/package-facts.json`, `evidence/downstream/conventions.json`,
`evidence/downstream/member-comparison.json`, `evidence/isolation/comparison.json`,
`evidence/disposal/exit-code.txt`, `52-ADOPTION-EVIDENCE.md`, this summary) and all three claimed
task commit hashes (`ef8fc9a`, `374646d`, `9b90a4f`) are present in `git log --oneline --all`.
