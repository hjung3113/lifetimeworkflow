---
phase: 52-evidence-bounded-real-target-adoption
plan: 05
subsystem: infra
tags: [adoption-scan, adoption-apply, pnpm-workspace, real-target-evidence, worktree-isolation]

# Dependency graph
requires:
  - phase: 52-02
    provides: "detect.py pnpm-workspace member scoping — scan.build_inventory excludes non-member manifests as non-workspace-member"
  - phase: 52-03
    provides: "conventions_for() permanent lint key + derive_language_rows()/languages.toml splice into applied harness/project.toml"
  - phase: 52-04
    provides: "expected_lock_sidecars/HARNESS_MANAGED_LOCK_SIDECARS + lock-sidecar declaration (never unlinked)"
provides:
  - "Real-target evidence (not a test, D-17) that discover scopes to exactly the five declared pnpm workspace members on FeedbackOps, with docs/design-prototype/package.json excluded as non-workspace-member (RTA-02, SC-2)"
  - "A full discover -> draft -> apply cycle against a freshly provisioned, run-time-pinned detached worktree of FeedbackOps, with literal argv/cwd/stdout/stderr/exit captures for every stage"
  - "An apply-write comparison (worktree.changed-paths.json) proving matches=true, zero product-code writes, and the three lock sidecars declared rather than unlisted (OBS-D-04 real-target proof)"
  - "scripts/compare-worktree-writes.py — phase-local (D-21) porcelain-v2 diff + manifest-driven allowlist comparator, importing expected_lock_sidecars verbatim"
  - "A confirmed-firing --target mis-targeting guard (T-52-15), checked against a synthetic mistargeted argv before being trusted"
affects: [52-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "D-21 phase-local comparator: a porcelain-v2 before/after diff classified against two allowlists (manifest create/marker-merge destinations + imported expected_lock_sidecars), never a shared tools/ module."
    - "Guard-fires-on-synthetic-input verification before trusting a defensive regex in an automated verify step (documented in this SUMMARY per the plan's acceptance criteria)."

key-files:
  created:
    - .planning/phases/52-evidence-bounded-real-target-adoption/scripts/compare-worktree-writes.py
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/metadata/*
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/isolation/*
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/discover/*
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/draft/*
    - .planning/phases/52-evidence-bounded-real-target-adoption/evidence/apply/*
  modified: []

key-decisions:
  - "The target's develop HEAD was re-read live at run time (D-02): 919d152a56ed096c0fdef12b9bfb892d6ef4ced6 — neither the Phase-51 baseline (1d1c8ed) nor STATE.md's carried note (4f16525), both stale. This third movement is attributed as expected third-party drift, not filed as an OBS-D."
  - "The live pnpm-workspace.yaml still declares packages: [\"apps/*\", \"packages/*\"] — unchanged since Phase 51/52 planning, so the D-02 re-verification found no drift in the glob set itself."
  - "compare-worktree-writes.py computes expected_disposition_paths as every manifest record whose disposition is create or marker-merge (the only two branches apply_disposition ever writes through), rather than trusting an externally-recorded applied list — this makes the comparator self-contained and re-derivable from the manifest alone."

requirements-completed: [RTA-01, RTA-02]

# Metrics
duration: ~35min active work
completed: 2026-08-01
---

# Phase 52 Plan 05: Real-Target Discover -> Draft -> Apply Cycle Summary

**A freshly provisioned, run-time-pinned detached worktree of the real FeedbackOps monorepo received a full discover -> draft -> apply cycle from the repaired harness: discover enumerated exactly the five declared pnpm workspace members (excluding `docs/design-prototype/package.json` as `non-workspace-member`), and apply wrote only expected disposition destinations plus the three declared lock sidecars — `matches: true`, zero product-code writes, original `develop` checkout byte-unchanged throughout.**

## Performance

- **Duration:** ~35 min active work
- **Started:** 2026-07-31T17:42:04Z
- **Completed:** 2026-07-31T17:48:39Z (evidence capture); repo commits timestamped 2026-08-01 per commit metadata
- **Tasks:** 3/3 completed
- **Files modified:** 34 created (0 modified) — 17 metadata/isolation artifacts (Task 1), 20 discover/draft artifacts (Task 2), 9 apply/comparator artifacts (Task 3, one file — the comparator script — outside `evidence/`)

## Accomplishments

- **Task 1 — phase-start metadata + isolation before-proof + fresh worktree.** Re-read the target's live `develop` HEAD (`919d152a56ed096c0fdef12b9bfb892d6ef4ced6`) and its live `pnpm-workspace.yaml` (unchanged glob set), captured the D-03 four-artifact before-proof against the ORIGINAL checkout (`status --porcelain=v2 --untracked-files=all`, `rev-parse HEAD`, tracked-index SHA-256, untracked-path-set SHA-256, `worktree list`) before any external write, then provisioned `git worktree add --detach /Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-52-adoption 919d152a…` (exit 0). Confirmed detached (`symbolic-ref -q HEAD` fails) and confirmed the original checkout's status was byte-identical immediately after provisioning.
- **Task 2 — discover + draft.** `tools.adoption_scan` ran once against the worktree (exit 0); its `inventory.json`'s `target_ref` equals the pinned SHA exactly. The repaired discover enumerated exactly the five real workspace members (`.`, `apps/backend`, `apps/frontend`, `packages/shared`, `packages/ui`) as both `manifests` and `candidate_process_boundaries`, and recorded `docs/design-prototype/package.json` as `excluded: "non-workspace-member"` — the SC-2/RTA-02 real-target proof. `member-comparison.json` computed both verdict booleans from the artifact (`members_equal_expected_five: true`, `non_member_recorded: true`). `tools.adoption_apply draft` ran once (exit 0), writing an unedited batch (`7bc665fa91e12a8a`) plus a `languages.toml` sidecar (`id = "javascript"`, `lint`/`test`/`format` derived from the target's own `package.json` scripts, OBS-D-03/D-12).
- **Task 3 — apply + write-comparison proof.** `tools.adoption_apply apply` ran once with the batch id read verbatim from `status.json` (exit 0; `applied=154 skipped=86 refused=23`). Before trusting the `--target` mis-targeting guard, it was fired against a synthetic mis-targeted argv line ending in the original checkout path and confirmed to match (and confirmed NOT to match the real, worktree-targeted `argv.txt`) — see Guard Verification below. The new phase-local `scripts/compare-worktree-writes.py` (D-21, not a `tools/` module) parses the before/after `git status --porcelain=v2` captures, derives `changed_paths`, and classifies them against `expected_disposition_paths` (every manifest `create`/`marker-merge` destination) and `expected_lock_sidecars` (imported verbatim from `tools.adoption_apply.apply.expected_lock_sidecars`, never retyped). Result: `matches: true`, `unexpected_paths: []`, `product_code_paths: []` (D-06), and the three lock sidecars (`.AGENTS.md.lock`, `.CLAUDE.md.lock`, `.claude/.settings.json.lock`) land in `expected_lock_sidecars` and are absent from `unexpected_paths` — the OBS-D-04 repair's real-target proof.
- Original FeedbackOps `develop` checkout's `status --porcelain=v2 --untracked-files=all` remained byte-identical to `before.status.txt` at the end of every task. `git diff --quiet -- tools/ harness/ contracts/` confirms this plan changed no harness code. Full suite still green: **1023 passed**, `contract-drift: OK`.
- The fresh worktree was deliberately NOT disposed (52-06 owns the after-proof and disposal); `git worktree list` confirms it is still present.

## Guard Verification (T-52-15, plan-mandated)

Before trusting the automated `--target`-mistargeting guard used in Task 3's verify step, its regex
(`--target[[:space:]]+/Users/hyojung/Desktop/2026/FeedbackOps($|[[:space:]])`) was run once against
a hand-written synthetic argv line ending in the original checkout path:

```
uv run python -m tools.adoption_apply apply --task-dir X --batch-id Y --target /Users/hyojung/Desktop/2026/FeedbackOps
```

The guard MATCHED (fired) against this synthetic line, confirming it would have caught a real
mis-targeted run. The guard was then run against the real `evidence/apply/argv.txt` and did NOT
match — the real run targeted the worktree, never the original checkout.

## Task Commits

Each task was committed atomically:

1. **Task 1: Phase-start metadata, original-checkout before-proof, and fresh worktree provisioning** — `11a1623` (feat)
2. **Task 2: Discover and draft against the worktree with complete captures** — `62ed25b` (feat)
3. **Task 3: Apply, then prove every write is an expected write** — `33977ca` (feat)

## Files Created/Modified

- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/metadata/` — harness/target SHAs, live tool versions, verbatim `pnpm-workspace.yaml` copy
- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/isolation/` — D-03 before-proof, provisioning captures, worktree head/detached-state confirmation, before/after-apply worktree status, README disclosing `.git/worktrees/**` administrative-metadata scope exclusion
- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/discover/` — five argv/cwd/stdout/stderr/exit-code sidecars, `inventory.json`/`plan.json`/`manifest.json`, `member-comparison.json`
- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/draft/` — five sidecars, the unedited batch (`artifacts/adoption/7bc665fa91e12a8a/`), `languages-toml-present.txt`, copied `languages.toml`
- `.planning/phases/52-evidence-bounded-real-target-adoption/evidence/apply/` — five sidecars, `worktree.changed-paths.json`
- `.planning/phases/52-evidence-bounded-real-target-adoption/scripts/compare-worktree-writes.py` — new phase-local comparator (created)

## Decisions Made

See `key-decisions` in frontmatter above (D-02 re-verification result, and the self-contained `expected_disposition_paths` derivation choice).

## Deviations from Plan

None — plan executed exactly as written. All three tasks' automated `<verify>` blocks pass; every acceptance criterion (SHA freshness, detached HEAD, byte-unchanged original checkout, both member-comparison booleans genuinely computed, the guard-fires-on-synthetic-input check, `matches`/`product_code_paths` computed values) was satisfied without code change.

## Issues Encountered

- The comparator script's initial `REPO_ROOT = Path(__file__).resolve().parents[3]` under-counted directory levels for a script nested at `.planning/phases/52-.../scripts/` (four levels below repo root, not three), causing `ModuleNotFoundError: No module named 'tools'` on first run. Corrected to `parents[4]` before any evidence was captured — not a plan deviation, a script-authoring correction made before Task 3's first commit.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 52-06 can proceed directly to the phase-record after-proof and worktree disposal: the worktree at `/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-52-adoption` is left in place, pinned at `919d152a…`, with `applied=154 skipped=86 refused=23` from this plan's apply run as its current state.
- All must-haves and artifacts named in this plan's frontmatter are present and verified: `target.develop.sha.txt`, `before.index.sha256`, `discover/inventory.json`, `apply/worktree.changed-paths.json`, and the key-links chain (SHA -> provision argv -> discover -> draft batch id -> apply argv -> expected_lock_sidecars import) all resolve.
- Full suite green (1023 passed), `contract-drift: OK`, no harness code touched — 52-06's phase-level verification against `51-BASELINE-EVIDENCE.md`'s OBS-D-01..04 can cite this plan's evidence directly.

---
*Phase: 52-evidence-bounded-real-target-adoption*
*Completed: 2026-08-01*

## Self-Check: PASSED

All claimed files exist (`scripts/compare-worktree-writes.py`, `evidence/metadata/target.develop.sha.txt`,
`evidence/discover/inventory.json`, `evidence/discover/member-comparison.json`,
`evidence/apply/worktree.changed-paths.json`, this summary) and all four claimed commit hashes
(`11a1623`, `62ed25b`, `33977ca`, `ef46b53`) are present in `git log --oneline --all`.
