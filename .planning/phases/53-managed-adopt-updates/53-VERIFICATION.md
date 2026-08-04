---
phase: 53-managed-adopt-updates
verified: 2026-08-04T00:00:00Z
status: human_needed
score: 3/3 success criteria verified
re_verification: false
warnings:
  - item: "53-ADOPTION-EVIDENCE.md SC-2 negative half cites an instrument that cannot fail"
    detail: >-
      The evidence document states the cycle-2 no-op is proven by `compare.json`'s
      `changed_paths: []` plus `--require-no-writes`, "which exits non-zero on any non-sidecar
      write". That is false. `rerun-managed-update.py` computes `changed_paths` as a SET DIFFERENCE
      of `git status --porcelain=v2` path sets, which is blind to content rewrites of paths already
      present in the status set — i.e. every one of the 155 destinations after cycle 1. Proven from
      the captures: cycles 3 and 4 each performed a real `update` write, and their
      `worktree.before-apply.status.txt` and `worktree.after-apply.status.txt` are BYTE-IDENTICAL
      with `changed_paths: []`. 53-CONTEXT.md specified "a before/after tree hash of the target";
      a status-path-set diff was substituted. SC-2 still passes on other, real evidence
      (installed-record sha256 equality + the fixture tree-hash/write-spy test), so this is a
      documentation overclaim, not a failed criterion.
    decision_requested: >-
      Either (a) correct 53-ADOPTION-EVIDENCE.md's SC-2 negative-half wording to cite the
      installed-record hash invariant as the load-bearing proof and demote `--require-no-writes`
      to "new-path detection only", or (b) accept as-is. 53-04-SUMMARY.md already discloses a
      narrower version of this ("cannot see content changes to untracked files"); the defect is
      wider than that — it is blind to tracked-modified files too.
  - item: "Mis-target structural refusal claim has no capture"
    detail: >-
      53-ADOPTION-EVIDENCE.md claims "The run driver additionally refuses structurally, before any
      subprocess starts, if --target resolves to the original checkout — that refusal was also
      observed firing." No such driver exists in the repo. The only phase-local scripts are
      `apply-manifest-update-enum.py` and `rerun-managed-update.py`; the latter's only structural
      refusal is `--out must stay under PHASE_ROOT`. No capture file records the guard firing.
      Isolation itself IS independently proven (comparison.json hashes), so this is an unbacked
      sentence, not an isolation failure.
    decision_requested: "Delete or substantiate the sentence."
---

# Phase 53: Managed Adopt Updates — Verification Report

**Phase Goal (ROADMAP.md):** Prove install-to-update behavior, unchanged no-op, and
divergence-safe conflict handling on the real target.
**Verified:** 2026-08-04
**Status:** human_needed — all three success criteria verified; two evidence-document overclaims
require a human decision.
**Stance:** adversarial. Every verdict below was re-derived from raw captures or from the
codebase; no SUMMARY prose was accepted as evidence.

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Deciding evidence |
|---|-------|--------|-------------------|
| SC-1 | The adoption manifest records every file managed by `/adopt` | ✓ VERIFIED | Set equality re-derived in both directions from `cycle-1/compare.json` |
| SC-2 | A re-run updates changed managed content; a re-run with no source or target change is an observable no-op | ✓ VERIFIED (with warning on one instrument) | Positive: `manifest3` update row + recorded hash advance. Negative: installed-record sha256 identity + fixture tree-hash test |
| SC-3 | A target-side divergence produces a conflict report and leaves the file byte-unchanged | ✓ VERIFIED | `cycle-4/diverged-destination.json` + `cycle-4/apply/stderr.txt` |

**Score:** 3/3.

---

### SC-1 — the record covers exactly what was written — **PASS**

Re-derived, not read from prose. From `evidence/cycle-1/compare.json`:

```
installed_record_destinations  = 155 rows
expected_disposition_paths     = 155 (create 152 + marker-merge 3, from disposition_counts)
set(record) == set(written)    -> True
only-in-record  = []
only-in-written = []
```

Cycle-1 stderr is literally `applied=155 updated=0 unchanged=0 conflicts=1 skipped=85 refused=23`,
so `applied + updated = 155` matches the row count.

The record's key set is exactly `{batch_id, destination, installed_sha256}` — re-read from
`cycle-2/draft/.../manifest.json`'s copied `installed[]`. **No timestamp, no run counter.** That is
not merely asserted: cycle 4's record sha256 returns to cycle 1's value
`41de1aa61f31f23202442c6b2277d71b1a15b16c2023ba637369f0d7adb77ec0` **exactly**, which is only
possible if the serialization is content-derived and deterministic. That is a stronger proof of the
no-clock property than the test that asserts the key set.

Arithmetic closes on every cycle against the 155-row record:

| cycle | unchanged | updated | recorded-destination conflicts | total |
|---|---|---|---|---|
| 2 | 154 | 0 | 1 (`docs/explanation/next-milestone-task-control-plane.md`) | 155 |
| 3 | 153 | 1 | 1 | 155 |
| 4 | 152 | 1 | 2 (+ `.github/CODEOWNERS`) | 155 |

(`.gitignore` is the third conflict and is correctly NOT in the record — `installed_sha256=none-recorded`.)

Structural exclusion of the record itself is real code, not documentation:
`destinations.py::destination_catalog()` skips `parts[0] == _BOOKKEEPING_DIR_NAME` (`.harness`).

---

### SC-2 — a re-run rewrites only what the harness moved — **PASS** (positive strong, negative sound but mis-instrumented)

#### Positive half — **PASS**

Re-derived from the drafted manifests, not from the evidence prose:

```
manifest3: update rows = ['.memory/README.md']
manifest3 recorded installed_sha256 for .memory/README.md = dca8df52e64b75c2de166fdf1e20c8ca691f2894634e5b4de3203ed99936cfe5
manifest4 recorded installed_sha256 for .memory/README.md = 1a4415ef30ab087a76d73af091d94f99acfbd9a4307c454c22a1554b21d0b080
```

The `update` branch fired on a real target and the record advanced. Cycle 3's compare.json record
sha (`4d3a23a1…`) differs from cycle 1/2's (`41de1aa6…`), and cycle 4 — after the harness mutation
was reverted — returns to `41de1aa6…`. **Cycle 2's record sha equals cycle 1's; cycle 3's differs.**
Both halves of the specific claim under scrutiny are confirmed from the captures.

#### Negative half — PASS on the evidence that holds; the headline instrument is vacuous

What actually holds:

1. `installed_record_sha256` identical between cycle 1 and cycle 2 (`41de1aa6…`). This is a real
   `sha256(record_path.read_bytes())` computed by the driver (line 103 of
   `rerun-managed-update.py`) — content, not status.
2. `tools/adoption_apply/tests/test_update_disposition.py::test_true_no_op_writes_nothing` does a
   genuine before/after content tree hash (`_tree_hashes`) **and** asserts
   `write_spy.call_count == 0`. I mutation-tested this (M5 below) — it reds.
3. Literal cycle-2 stderr `applied=0 updated=0 unchanged=154 conflicts=2 skipped=85 refused=23`.

What does NOT hold — **and this is the finding**:

> 53-ADOPTION-EVIDENCE.md line 51–53: "`compare.json` for cycle 2: `matches: true`,
> `changed_paths: []` … and the driver was run with `--require-no-writes`, which exits non-zero on
> any non-sidecar write."

`changed_paths` is `parse_porcelain_v2_paths(after) - parse_porcelain_v2_paths(before)` — a set
difference over *paths*. Porcelain-v2 carries no worktree content hash (the `1 ...` line's two
object names are HEAD and index, not worktree), and untracked files are bare `? path` lines.
Therefore any rewrite of a path already in the status set is invisible.

Proof from this phase's own captures — cycles 3 and 4 each really wrote a file:

```
cycle-3 before-apply status vs after-apply status : IDENTICAL (158 lines each)
cycle-4 before-apply status vs after-apply status : IDENTICAL (158 lines each)
cycle-3 compare.json changed_paths : []     (while updated=1)
cycle-4 compare.json changed_paths : []     (while updated=1)
```

Had cycle 2 rewritten all 155 managed files, `--require-no-writes` would still have exited 0. It is
a check that cannot fail for the exact class of write SC-2 is about — this repo's signature defect,
appearing in the phase's *proof instrument* rather than in its tests.

53-CONTEXT.md specified the instrument precisely: *"proven by a before/after tree hash of the
target (the Phase-52 `scripts/compare-worktree-writes.py` idiom, D-21)"*. A tree hash was not
implemented for the real-target run; a status-path-set diff was substituted. 53-04-SUMMARY.md
discloses a narrower version of this defect ("cannot see content changes to untracked files"); the
defect is wider — it is blind to tracked-modified files too, as cycles 3/4 show for `AGENTS.md`.

**Verdict:** SC-2's negative half is still supported by (1) and (2) above, so the criterion is met.
The *stated* proof is not. Warning raised, human decision requested.

WR-07 and WR-08 closure verified in code and test, not prose:
`test_project_toml_survives_reapply_as_preserve` (post-splice bytes recorded → re-adopt is
`preserve`, not permanent `conflict`) and `test_sidecar_is_spliced_on_the_update_path`
(asserts `"NOT spliced" not in output` on the update path).

---

### SC-3 — a target-side edit is reported, never overwritten — **PASS**

From `evidence/cycle-4/diverged-destination.json`:

```json
{"destination": ".github/CODEOWNERS",
 "pre_apply_sha256":  "be23af81e526c5699298c6ca4e2ba834f3f86b7f558fc15a8c9969e4b8630ebd",
 "post_apply_sha256": "be23af81e526c5699298c6ca4e2ba834f3f86b7f558fc15a8c9969e4b8630ebd",
 "byte_unchanged": true}
```

Pre == post, exactly. From `evidence/cycle-4/apply/stderr.txt`, literal:

```
conflict destination=.github/CODEOWNERS installed_sha256=ade9ff75048f3c4334b4c94199d01af5b1fef1121b78e70716f7070cbc1a3b2f current_sha256=be23af81e526c5699298c6ca4e2ba834f3f86b7f558fc15a8c9969e4b8630ebd
```

Exit code `0` (`cycle-4/apply/exit-code.txt`) — the run did not abort; conflicts rose 2→3, exactly
one new divergence; the drafted manifest carries the `conflict` disposition row. The stderr summary
is generated by real code (`cli.py:360-367`), and the `conflict` counter is populated from
`apply_manifest`'s buckets.

Note this criterion is *not* dependent on the weak `changed_paths` instrument — the byte-unchanged
claim is a direct pre/post sha256 of the file. SC-3's evidence is sound.

---

## Boundary, ordering, and scope checks

### v2.7 binding boundary (ROADMAP.md:231, re-checked by Phase 54 SC-2) — **PASS**

Counted on disk, not read from a claim:

```
contracts/**/*.schema.json  -> 6   (inventory, manifest, plan, relationship, format-conventions, greeting)
harness/commands/*.md       -> 19
harness/skills/*/           -> 8
```

The extension landed as `$defs.installedRecord` + one optional top-level `installed[]` inside the
existing `manifest.schema.json`. No sibling schema. Phase 54 will not be red-on-arrival.

### Contract-first ordering — **PASS**

From `git log`, in commit order:

```
d297ebe  feat(53-01): author off-plane manifest-schema update-enum applier   (script only, 1 file)
334d4c8  feat(53-01): extend manifest schema with `update` ...               (contracts/ + contracts/.hashes/ ONLY)
979eb41  chore(53-01): run /contract-check ... regenerate the derived plane
5ed57e7  feat(53-02): distinguish a harness-side move from a target-side edit (FIRST code emitting `update`)
```

`git log -- contracts/harness/adoption/manifest.schema.json` shows `334d4c8` as the only Phase-53
touch, and `git show --stat 334d4c8` confirms it changed exactly two files, no code. The contract
landed three commits before any code could emit `update`. Constitution-plane write pattern
(off-plane script → human runs it) was followed.

### Scope cuts held — **PASS**

```
grep -rn "conflicts\.json"  tools/ contracts/ harness/  -> (no matches)
grep -rn "source_sha256"    tools/ contracts/ harness/  -> 1 match: manifest.schema.json:146,
                                                            a description explaining WHY it is absent
grep -rn "return 3|exit(3)" tools/adoption_apply tools/adoption_scan -> (no matches)
```

No `conflicts.json` artifact, no second stored hash, no distinct exit code. `cli.py` returns only
0 and 1. The banned items did not creep back.

---

## Anti-vacuous sampling — five mutations run by this verifier

The recorded mutation tables were **not** taken on trust. I selected and ran five mutations myself,
observed each, and restored each. Baseline before and after: `1075 passed`; `git status --short`
empty.

| # | Mutation (exact) | File | Observed node id | Result |
|---|------------------|------|------------------|--------|
| M1 | `end_idx = existing.rfind(END_MARKER)` → `existing.find(...)` | `tools/harness_emit/merge.py:55` | `tools/harness_emit/tests/test_merge_idempotent.py::test_nested_body_uses_the_outer_end_marker` | **RED** (1 failed, 7 passed) |
| M2 | `if payload == (existing_text.encode(...) ...)` → `if False:` | `tools/adoption_apply/apply.py` | `tools/adoption_apply/tests/test_atomic_apply.py::test_marker_merge_idempotent` | **RED** (1 failed, 257 passed) |
| M3 | update branch `return "update"` → `return "conflict"` | `tools/adoption_scan/destinations.py` | `test_dispositions.py::{test_update_is_reachable_when_the_recorded_hash_matches, test_build_manifest_threads_installed_records, test_build_manifest_unrecorded_divergence_conflicts_not_updates, test_scope_excluded_destination_preserves_or_updates_from_its_recorded_hash}` + `test_update_disposition.py::{test_update_fires_when_the_harness_source_moves, test_sidecar_is_spliced_on_the_update_path}` | **RED** (6 failed, 252 passed) |
| M4 | `installed_hashes.get(destination)` → `.get(destination, existing_sha)` | `tools/adoption_scan/destinations.py::build_manifest` | `test_dispositions.py::test_build_manifest_unrecorded_divergence_conflicts_not_updates` (+6 others incl. the CR-01 pair and the artifact snapshot) | **RED** (7 failed, 251 passed) |
| M5 | `if records != previous:` → `if True:` | `tools/adoption_apply/cli.py:350` | `tools/adoption_apply/tests/test_update_disposition.py::test_true_no_op_writes_nothing` (`assert 0 == write_spy.call_count`) | **RED** (1 failed, 121 passed) |

M4 independently reproduces 53-02-SUMMARY's headline mutation row, with the **same** node id — the
recorded evidence for the replacement of vacuous mutation (a) is real, and the guard it replaced it
with genuinely attacks T-53-07 (a destination with no recorded hash resolving to `update`).

M5 independently confirms 53-03's replacement of the vacuous tree-hash no-op test: the surviving
assertion is `write_spy.call_count == 0`, which distinguishes "did not write" from "wrote the same
bytes". (53-03-SUMMARY says `call_count == 1`; the live test asserts `== 0`, which is the stronger
and correct form — cosmetic doc drift only.)

M1 and M2 are my own additions — the two Task-2 production fixes carried no mutation table. Both
regression tests are non-vacuous.

One honest negative: the `installed_sha is not None and` conjunct at
`destinations.py` step 7 is genuinely unreachable-dead (`existing_sha` is always a real digest by
that point). The code says so in a comment and 53-02-SUMMARY adjudicated it openly rather than
faking a red. I confirm the adjudication is correct and the retained conjunct is harmless
defence-in-depth, not a load-bearing guard being passed off as one.

---

## Repository health — **PASS**

| Check | Command | Result |
|---|---|---|
| Full suite | `uv run pytest -q` | **1075 passed**, 8 snapshots passed, 16.83s |
| Lint ratchet | `uv run python -m tools.ruff_baseline` | `67 findings (baseline 67)` — PASS |
| Contract drift | `uv run python -m tools.contract_drift.drift` | `OK — live manifest matches the committed baseline` |
| Working tree | `git status --short` | empty, before and after all five mutations |
| Debt markers in phase-touched files | `grep -nE "TBD\|FIXME\|XXX"` | Only pre-existing `TBD` in the *owner column* of generated `contracts-index` tables and normalization snapshot placeholders. **No new debt markers.** |

### Isolation of the third-party checkout — **PASS**

`evidence/isolation/comparison.json` is internally consistent: `before_head == after_head ==
final_head = bc9788bc…`, index sha256 and untracked-set sha256 identical across before / after /
post-disposal, `disposal_exit_code: 0`. `evidence/disposal/worktree-list.txt` shows the
`v27-53-rerun` worktree absent. `external-drift.json` attributes the checkout's branch movement to
third-party activity outside the run window. **I did not read or touch anything under
`/Users/hyojung/Desktop/2026/FeedbackOps*`.**

Caveat: the "mis-target guard proven to fire" sentence has no backing artifact (see warning 2).
Isolation is independently established by the hash triple above regardless.

---

## Judgement — were the three Task-2 production fixes required, or scope creep?

**All three were required by SC-2. None is scope creep.** Reasoning per fix:

**1. Exclusion-class split (`caf2447`, `scan.py` + `destinations.py`).**
`build_manifest` passed `_EXCLUDED_SENTINEL` as `existing_sha` for every excluded destination. The
sentinel can equal neither `proposed_sha` nor `installed_sha`, so for those destinations the chain
terminated at `conflict` unconditionally — the `update` branch was *unreachable*, and 21 files adopt
itself had written one cycle earlier were reported as conflicts forever. **Required:** SC-2 says a
re-run with no change is a no-op; 21 permanent false conflicts is the opposite. The seam is correct
— the fix names the distinction the sentinel was conflating (`REHASHABLE_EXCLUSION_REASONS =
{non-workspace-member, generated}` are *scope* exclusions; `binary/secret-content/size-capped/
symlink-escape` are *content refusals* and keep the sentinel). It does not weaken WR-03's
"never re-read a file the scanner refused to hash", and the negative control is asserted, so the fix
cannot drift into "re-read everything". M3/M4 both red through this path.

**2. Conditional `marker-merge` write (`caf2447`, `apply.py`).**
`_apply_marker_merge` returned `None` and always called `_atomic_replace`. **Required:** an
unconditional rewrite on a no-op cycle is a write, and it advanced the installed record. The change
is minimal (return `bool`, one equality check, one summary bucket). Regression test non-vacuous —
M2 reds `test_marker_merge_idempotent`.

**3. `find` → `rfind` in `splice_managed_block` (`460b53c`, `harness_emit/merge.py`).**
The most consequential. This was **unbounded corruption of a third party's file**: one extra
`<!-- END HARNESS-MANAGED -->` per run, four after three runs. **Required** — a corrupting write is
neither an update nor a no-op — and arguably a latent SC-3-class safety bug as well.

*Was the shared function the right seam?* **Yes.** The bug was a violation of the function's own
documented contract (module docstring: "markers PRESENT → replace ONLY the content between them";
"a second call is byte-identical"). The adopt call site was merely the first caller to pass a body
containing an inner fence. Guarding at the call site would have left `harness_emit`'s own callers
holding the same latent bug for any future fenced body. This is the root-cause fix, and it is one
line.

*Blast radius on the emitter, checked rather than assumed:* `git show --stat 460b53c` touches only
`merge.py` and its test — **`tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` was
not modified by that commit** (it moved later in `d7821d2`, from the `adopt.md`/SKILL.md doc edits).
Live `AGENTS.md` and `CLAUDE.md` each contain exactly one `END HARNESS-MANAGED`, so `find` and
`rfind` are identical for the emitter's own inputs — zero behavioural change for existing callers,
correct behaviour for the new one. Correct seam, correctly bounded.

*Is its regression test non-vacuous?* **Yes, and it is well-designed.** It asserts two things:
idempotence (`once == twice`) *and* `once.count(_END) == nested_body.count(_END) + 1`. The commit
message's stated reason for the second assertion is right — a mutation that dropped the outer fence
entirely would stay idempotent while destroying the contract, so idempotence alone would be
vacuous. M1 confirms the test reds under the actual pre-fix behaviour. The same commit also
strengthened `test_malformed_single_marker_raises` into a parametrised
`test_malformed_fences_raise` covering the `END`-before-`BEGIN` case that `rfind` newly makes
reachable — that is the right defensive pairing.

The plan-vs-reality gap is real and was disclosed: 53-04's plan assumed the mechanism from
53-01..03 would make the re-run a no-op, and on the real target it did not, for three independent
reasons no fixture reproduced. That assumption's failure is the phase's most valuable output.

---

## Gaps Summary

**No blockers.** All three MONO-12 success criteria are met on the real target and are re-derivable
from the raw captures. The v2.7 binding boundary is intact by count on disk (6/19/8), contract-first
ordering is confirmed by commit order, all three scope cuts held, the suite and both gates are
green, and the working tree is clean.

Two warnings, both in the evidence *narrative* rather than the delivered behaviour:

1. **The headline no-op instrument cannot fail.** `--require-no-writes` / `changed_paths` detects
   only *new paths*, and the phase's own cycles 3 and 4 prove it: real writes, byte-identical
   before/after status captures, `changed_paths: []`. The CONTEXT-specified before/after tree hash
   was never implemented for the real-target run. SC-2 survives on the installed-record hash
   invariant and the fixture tree-hash + write-spy test, but the evidence document names the wrong
   proof as load-bearing. A future reader following that document would trust a vacuous gate — the
   precise failure mode this repo has a standing rule against.

2. **One unbacked isolation sentence** (the "run driver refuses structurally / observed firing"
   claim) with no such driver and no capture. Isolation itself is proven independently.

Neither warning blocks Phase 54. Both are corrections to `53-ADOPTION-EVIDENCE.md`.

---

_Verified: 2026-08-04_
_Verifier: gsd-verifier (goal-backward, adversarial stance)_
