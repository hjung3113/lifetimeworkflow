# Phase 53 — Managed adopt updates: real-target evidence

**Requirement:** MONO-12. **Target:** `/Users/hyojung/Desktop/2026/FeedbackOps` (read-only) via a
fresh detached worktree at `/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-53-rerun`.
**Harness HEAD at run:** `caf2447d420008136d31eb311cd83f6216cf61ff`.
**Target `develop` re-read live at run start:** `a4e8e646b5c0169cf4f1978e64adc8b97dad66a9`.

Every value below is quoted from the captures under `evidence/`, not paraphrased.

## The four cycles

```
cycle 1  applied=155 updated=0 unchanged=0   conflicts=1 skipped=85 refused=23
cycle 2  applied=0   updated=0 unchanged=154 conflicts=2 skipped=85 refused=23
cycle 3  applied=0   updated=1 unchanged=153 conflicts=2 skipped=85 refused=23
cycle 4  applied=0   updated=1 unchanged=152 conflicts=3 skipped=85 refused=23
```

| cycle | installed record sha256 | rows |
|---|---|---|
| 1 | `41de1aa61f31f23202442c6b2277d71b1a15b16c2023ba637369f0d7adb77ec0` | 155 |
| 2 | `41de1aa61f31f23202442c6b2277d71b1a15b16c2023ba637369f0d7adb77ec0` | 155 |
| 3 | `4d3a23a1e3bac1d5417de9fc4b38e510a5cad01a138b00d56ace8c225eea52e6` | 155 |
| 4 | `41de1aa61f31f23202442c6b2277d71b1a15b16c2023ba637369f0d7adb77ec0` | 155 |

Cycle 4 returning to cycle 1's value is correct, not a coincidence: cycle 3's harness-side mutation
was reverted before cycle 4, so cycle 4's `update` restored the original bytes and the record
returned to the original hash.

---

## SC-1 — the record covers exactly what was written — **PASS**

Cycle 1 stderr: `applied=155 updated=0 unchanged=0 conflicts=1 skipped=85 refused=23`.
`installed_record_destinations` length: **155**. `applied + updated = 155 + 0 = 155`.

The two sets are equal **in both directions** — 155 rows against 155 written destinations, with no
row present that was not written and no written destination missing a row. The record carries no
timestamp and no run-counter key; its exact key set is asserted by
`tools/adoption_apply/tests/test_installed_record.py`, so a future `last_run_at` addition reds that
test rather than slipping in.

---

## SC-2 — a re-run rewrites only what the harness moved — **PASS** (both halves)

### Negative half — an unchanged re-run is a true no-op

Cycle 2 stderr, literal: `applied=0 updated=0 unchanged=154 conflicts=2 skipped=85 refused=23`.

The deciding value is the **per-file content digest** of the whole worktree taken immediately before
and after each apply (53-CONTEXT.md's "before/after tree hash"):

| cycle | files whose CONTENT changed | which |
|---|---|---|
| 1 | 159 | the 155 written destinations + 3 lock sidecars + the installed record |
| 2 | **0** | — |
| 3 | 2 | `.memory/README.md`, `.harness/adoption/installed.json` |
| 4 | 2 | `.memory/README.md`, `.harness/adoption/installed.json` |

Cycle 2 changed **nothing on disk**. Not "nothing unexpected" — nothing at all. Cycle 2's installed
record sha256 is identical to cycle 1's (`41de1aa61f31…`), which is the same fact seen from the
record's side.

**Read the `changed_paths` field with care.** It is a `git status --porcelain=v2` *path-set*
difference and is therefore blind to a file whose content was rewritten while its path stayed in the
set — which, after cycle 1, is every managed destination. `changed_paths` is `[]` for cycles 3 and 4
too, and those cycles demonstrably wrote a file. The path-set delta is a supporting signal, not the
proof; `content_changed_paths` and the record hash are what decide SC-2. The first version of this
document named `--require-no-writes` on the path-set delta as the proof, which it never was.

The instrument was then proven able to fail, in `evidence/isolation/instrument-guards.txt`. Given
cycle 2's real captures and a copy of its after-tree in which exactly ONE already-present file
carries a different digest — path set untouched:

```
control  (unmutated after-tree)                        -> exit=0
mutated  (one file's CONTENT differs)                  -> exit=1
SAME mutation, tree digests omitted (path-set only)    -> exit=0
```

The third line is the point: the old instrument passes the very mutation the new one catches.

The two cycle-2 conflicts are both correct and neither is a managed-file rewrite:

```
conflict destination=.gitignore installed_sha256=none-recorded current_sha256=3ce726ba31ada08c9ef2a8ecd71d9ba331c7273c47b80c068319a8ec296cf00f
conflict destination=docs/explanation/next-milestone-task-control-plane.md installed_sha256=04355882a5b99a14dfd4e60324792984a76a37f1cc5239b0e40449d2e377701d current_sha256=04355882a5b99a14dfd4e60324792984a76a37f1cc5239b0e40449d2e377701d
```

`.gitignore` is a pre-existing target file adopt never wrote — `installed_sha256=none-recorded` is
exactly the T-53-07 guard doing its job: no recorded hash, therefore never `update`. The second is
excluded by the scanner as `secret-content`, a content-based refusal that holds its sentinel by
design (never re-read), so it stays `conflict`. Neither file is written.

### Positive half — a harness-side move fires `update`

Cycle 3 appended one comment line to the harness's own `.memory/README.md`, then drafted and
applied. Manifest 3's `update` rows: `['.memory/README.md']` — the branch is not dead code.

Recorded `installed_sha256` for that destination:

```
before cycle 3 (manifest 3): dca8df52e64b75c2de166fdf1e20c8ca691f2894634e5b4de3203ed99936cfe5
after  cycle 3 (manifest 4): 1a4415ef30ab087a76d73af091d94f99acfbd9a4307c454c22a1554b21d0b080
```

The record advanced. The harness mutation was reverted immediately after the cycle;
`git diff --quiet -- .memory/README.md` succeeds.

---

## SC-3 — a target-side edit is reported, never overwritten — **PASS**

Cycle 4 appended one line to `.github/CODEOWNERS` inside the worktree — a destination cycle 1 wrote
and cycle 3 did not touch.

```json
{
  "destination": ".github/CODEOWNERS",
  "pre_apply_sha256": "be23af81e526c5699298c6ca4e2ba834f3f86b7f558fc15a8c9969e4b8630ebd",
  "post_apply_sha256": "be23af81e526c5699298c6ca4e2ba834f3f86b7f558fc15a8c9969e4b8630ebd",
  "byte_unchanged": true
}
```

The post-apply hash equals the pre-apply hash **exactly** — byte-unchanged, not merely "different
from the harness content". Independently confirmed from the other side: cycle 4's
`content_changed_paths` is `['.harness/adoption/installed.json', '.memory/README.md']` and
`.github/CODEOWNERS` is **absent** from it, so the conflicted file was not among the files written.
The apply names it on stderr with both hashes:

```
conflict destination=.github/CODEOWNERS installed_sha256=ade9ff75048f3c4334b4c94199d01af5b1fef1121b78e70716f7070cbc1a3b2f current_sha256=be23af81e526c5699298c6ca4e2ba834f3f86b7f558fc15a8c9969e4b8630ebd
```

Exit code: `0` — the other rows were still processed. Conflicts rose 2 → 3, exactly the one new
divergence. The drafted `manifest.json` carries the `disposition: "conflict"` row; there is no
separate conflict artifact and no exit code by number.

---

## Isolation — the original checkout was never written to

```json
{
  "before_head": "146d7fb0956861340e4704a92ff5c349825af5d2",
  "after_head": "146d7fb0956861340e4704a92ff5c349825af5d2",
  "head_equal": true, "index_equal": true,
  "untracked_equal": true, "status_equal": true,
  "post_disposal": { "equal_to_before": true, "disposal_exit_code": 0 }
}
```

The mis-targeting guard was **proven to fire before it was trusted**, and the proof is captured in
`evidence/isolation/instrument-guards.txt` rather than merely asserted here: against a hand-written
argv line ending in `--target /Users/hyojung/Desktop/2026/FeedbackOps` the anchored pattern matched
(the verify block would exit 1), and against the legitimate worktree path it did not match.

Third-party movement of the checkout is attributed in `evidence/isolation/external-drift.json`, not
left unexplained: the checkout sits on `feature/293-presubmit-similar-voc` and moved twice during
this phase's work. All of that is outside this run's window; within the window the checkout was
byte-identical throughout. The worktree is disposed and absent from `git worktree list`.

---

## What the real target found that the fixtures could not

The first evidence run **failed SC-2** and the failure was worth more than the pass. It is recorded
here because a green re-run should not erase the reason the gate existed.

```
cycle 2 (first run)  applied=3 updated=0 unchanged=131 conflicts=22
```

Three defects, none of them a Phase-53 regression, all invisible to the fixtures:

1. **A scanner-excluded destination could never leave `conflict`.** 21 of the 22 conflicts were
   files adopt itself had written one cycle earlier — every `tools/*/pyproject.toml`
   (`non-workspace-member`: a Python pyproject in a pnpm repo) plus four `generated` files.
   `build_manifest` passed `_EXCLUDED_SENTINEL` as `existing_sha`, which can equal neither the
   proposed nor the recorded hash, so the new `update` branch was **unreachable** for them. Fixed by
   splitting the exclusion classes: content-based refusals (`binary`, `secret-content`,
   `size-capped`, `symlink-escape`) keep the sentinel and the forced conflict; scope-based
   exclusions (`non-workspace-member`, `generated`) resolve their hash normally. The negative
   control is asserted so the fix cannot drift into "re-read everything".

2. **`marker-merge` rewrote unconditionally**, which also advanced the installed record on a no-op
   cycle. Now skipped and counted `unchanged` when the merged bytes already match.

3. **The marker splice was not idempotent — it was corrupting the target.** `AGENTS.md` and
   `CLAUDE.md` gained one extra `<!-- END HARNESS-MANAGED -->` on *every* run; after three runs the
   file ended with four consecutive END markers. `splice_managed_block` located the region with
   `find(END_MARKER)` — the FIRST end — but the body legitimately contains an inner fence (the
   harness's own emitter block), so it replaced only up to the inner END and appended a fresh outer
   one. Fixed with `rfind` in the shared function, so every caller including the emitter is fixed by
   one guard. `.claude/settings.json` was the control: byte-identical across all runs throughout,
   because `merge_settings` was already idempotent.

Defect 3 was unbounded corruption of a third party's file. No fixture reproduced it, and no test
suite caught it — only running the real thing four times in a row did.
