---
phase: 53-managed-adopt-updates
plan: 04
status: complete
requirements: [MONO-12]
commits:
  - c4f1d79  feat(53-04): phase-local re-run driver for the managed-update proof
  - d7821d2  docs(53-04): document re-run semantics and re-emit the runtime projections
  - 460b53c  fix(53-04): close the outer HARNESS-MANAGED fence so the splice is idempotent
  - caf2447  fix(53-04): make an unchanged re-run of /adopt a true no-op
  - 24343e2  docs(53-04): four-cycle real-target evidence and the SC verdicts
key-files:
  created:
    - .planning/phases/53-managed-adopt-updates/scripts/rerun-managed-update.py
    - .planning/phases/53-managed-adopt-updates/53-ADOPTION-EVIDENCE.md
    - .planning/phases/53-managed-adopt-updates/evidence/
  modified:
    - tools/harness_emit/merge.py
    - tools/adoption_scan/scan.py
    - tools/adoption_scan/destinations.py
    - tools/adoption_apply/apply.py
    - harness/commands/adopt.md
    - harness/skills/brownfield-adoption/SKILL.md
completed: 2026-08-04
---

# 53-04 — Real-target proof, and the three defects it found

All three MONO-12 success criteria now have a real-target verdict backed by quoted values. See
`53-ADOPTION-EVIDENCE.md` for the full captures; this summary records what happened and what it cost.

## What was built

- **`rerun-managed-update.py`** — the phase-local re-run driver. Imports the lock-sidecar allowlist
  rather than restating it, knows the `update` disposition (a Phase-52-era driver would have reported
  every legitimate update as unexpected), records the installed-record hash and destinations per
  cycle, confines all output under the phase directory, and has `--require-no-writes` as a runnable
  gate rather than a human reading a diff. Both guards were observed firing before being trusted.
- **Documentation + re-emit** — `adopt.md` and the brownfield-adoption skill now state what a second
  `/adopt` run does. Both runtime projections regenerated; re-emit idempotent. Live surface unchanged:
  19 commands, 8 skills, 6 contracts.
- **Three production fixes** the evidence run forced (below).

## The run

```
cycle 1  applied=155 updated=0 unchanged=0   conflicts=1 skipped=85 refused=23
cycle 2  applied=0   updated=0 unchanged=154 conflicts=2 skipped=85 refused=23
cycle 3  applied=0   updated=1 unchanged=153 conflicts=2 skipped=85 refused=23
cycle 4  applied=0   updated=1 unchanged=152 conflicts=3 skipped=85 refused=23
```

SC-1 PASS (155 record rows == 155 applied+updated, both directions). SC-2 PASS both halves (cycle 2
literal `applied=0 updated=0 unchanged=154` with the record sha256 identical to cycle 1; cycle 3
fires `update` on `.memory/README.md` and the recorded hash advances `dca8df52…` → `1a4415ef…`).
SC-3 PASS (`.github/CODEOWNERS` post-apply sha256 equals pre-apply exactly, named on stderr with both
hashes, exit 0).

Original checkout byte-identical before/after/post-disposal; worktree disposed; mis-target guard
proven to fire against a hand-written mis-targeted argv before the run.

## The first run FAILED, and that was the point

```
cycle 2 (first run)  applied=3 updated=0 unchanged=131 conflicts=22
```

Three defects, none of them a Phase-53 regression, none reachable from the fixtures:

1. **Scanner-excluded destinations could never leave `conflict`** (`caf2447`). 21 of the 22 conflicts
   were files adopt itself wrote one cycle earlier — every `tools/*/pyproject.toml`
   (`non-workspace-member`) plus four `generated` files. `_EXCLUDED_SENTINEL` can equal neither the
   proposed nor the recorded hash, so the `update` branch was unreachable for them. Fixed by
   splitting the exclusion classes: content-based refusals keep the sentinel and the forced conflict;
   scope-based exclusions resolve their hash normally. A content-excluded destination is asserted to
   still conflict and still never be re-read, so the fix cannot drift into "re-read everything".

2. **`marker-merge` rewrote unconditionally** (`caf2447`), advancing the installed record on a no-op
   cycle. Now skipped and counted `unchanged` when the merged bytes already match.

3. **The marker splice was corrupting the target** (`460b53c`). `AGENTS.md` and `CLAUDE.md` gained one
   extra `<!-- END HARNESS-MANAGED -->` on *every* run — four after three runs.
   `splice_managed_block` used `find(END_MARKER)`, but the body legitimately contains an inner fence
   (the harness's own emitter block), so it replaced only up to the inner END and appended a fresh
   outer one. Fixed with `rfind` in the shared function, so the emitter's own callers are fixed by the
   same guard. `.claude/settings.json` was the control — byte-identical throughout, because
   `merge_settings` was already idempotent.

Defect 3 was unbounded corruption of a third party's file. The full suite was green while it was
happening. Only running the real target repeatedly exposed it.

## Deviations

- **Task 2 required three production fixes the plan did not anticipate.** The plan assumed the
  mechanism built in 53-01..03 would make the re-run a no-op; on the real target it did not, for
  three independent reasons. The fixes are required BY SC-2, so they are not scope creep, but they
  were not in the plan's task list.
- **The plan's `git diff --quiet -- tools/ contracts/` gate is incompatible with its own Task 3.**
  Editing `adopt.md`/`SKILL.md` necessarily moves
  `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`, a derived artifact of those
  files. `contracts/` stayed clean throughout, which is the part that matters.
- **The driver's porcelain-based `changed_paths` cannot see content changes to untracked files.**
  `.harness/adoption/installed.json` is untracked, so a rewrite of it left `changed_paths` empty and
  `matches: true` even while the record hash was advancing. The record-hash invariant is what caught
  it. Noted because a future reader could over-trust `matches`.

## Verification

- Full suite: **1075 passed**; `uv run python -m tools.ruff_baseline`: 67/67 **PASS**
- `uv run python -m tools.contract_drift.drift`: exit 0; `git diff --quiet -- contracts/`: clean
- Contract count 6, commands 19, skills 8 — the v2.7 binding boundary is intact
- Plan Task 2 verify block: all assertions pass, including `NO-OP REWROTE THE RECORD` and
  `UPDATE DID NOT ADVANCE THE RECORD`
- Scope-cut guard: `conflicts.json`, `source_sha256`, exit code 3 appear nowhere in
  `tools/adoption_apply/` or `tools/adoption_scan/`

## Self-Check: PASSED
