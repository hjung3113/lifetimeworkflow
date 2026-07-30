---
phase: 45-projection-repair
plan: 05
subsystem: docs-and-derived-plane
tags: [cer-11, projection-repair, docs, two-plane-memory, constitution-plane, deferral]
requires: ["45-04"]
provides:
  - "docs/ free of the two whole-file task-lifecycle corpses, with every inbound link repaired"
  - "docs/how-to/README.md no longer making a false constitution-plane claim"
  - ".memory/README.md two-plane declaration collapsed to three constitution members"
  - "tools/memory_regen/tests/test_layout.py CONSTITUTION_MEMBERS agreeing with it (twelfth copy retired)"
  - "a named, recorded docs/glossary.md deferral to the milestone-close PR"
affects:
  - docs/how-to/README.md
  - docs/explanation/next-milestone-task-control-plane.md
  - docs/explanation/template-and-instances.md
  - .memory/README.md
  - .gitignore
  - tools/memory_regen/tests/test_layout.py
tech-stack:
  added: []
  patterns: ["prose declaration and its asserting test move in one commit (D-16)"]
key-files:
  created:
    - .planning/phases/45-projection-repair/45-05-SUMMARY.md
  modified:
    - docs/how-to/README.md
    - docs/explanation/next-milestone-task-control-plane.md
    - docs/explanation/template-and-instances.md
    - .memory/README.md
    - .gitignore
    - tools/memory_regen/tests/test_layout.py
  deleted:
    - docs/how-to/task-lifecycle.md
    - docs/explanation/task-lifecycle-shadow-metrics.md
decisions:
  - "next-milestone-task-control-plane.md RETAINED with a HISTORICAL header — ADR-0008:50 cites it as design authority and ADRs are append-only, so deleting it would convert a stale-but-resolvable pointer into a permanent dangling constitution-plane reference"
  - "docs/glossary.md deferred to the milestone-close PR (defer-to-pr branch); no HARNESS_DEV_BYPASS, no forged GOLDEN_APPROVE_HUMAN"
  - "PLAN's task-3 context miscounts the glossary defects: it attributes line 20's /golden-approve sentence to :19 as well. Measured: ONE occurrence, on :20 only. The verify leg's 'expect 2' does not hold; recorded, not adjusted"
  - ".memory/README.md:20 and :32 ('four members') corrected alongside the plan-named :13/:25/:29 — collapsing the row without them would leave the file self-contradictory"
metrics:
  duration: ~20 min
  completed: 2026-07-29
---

# Phase 45 Plan 05: docs/ and Derived-Plane Projection Repair Summary

Deleted the two `docs/` files whose entire subject is the task-control plane Phase 43 removed,
repaired every inbound link, collapsed the two-plane constitution declaration from four members to
three in both `.memory/README.md` and the one test that asserts it, and routed the single
constitution-plane target through a recorded human deferral rather than a bypass.

## Commits

| Commit | Task | Scope |
|--------|------|-------|
| `7d61983` | 1 | delete two doc corpses, repair inbound links, retain + annotate the ADR-cited design record |
| `2dcee85` | 2 | collapse the two-plane declaration to three members, plus the asserting test, gitignore and template-split prose |

`7d61983` — `4 files changed, 8 insertions(+), 123 deletions(-)`

```
 docs/explanation/next-milestone-task-control-plane.md |   7 +-
 docs/explanation/task-lifecycle-shadow-metrics.md     |  13 ---
 docs/how-to/README.md                                 |   5 +-
 docs/how-to/task-lifecycle.md                         | 106 ---------------------
```

`2dcee85` — `4 files changed, 18 insertions(+), 10 deletions(-)`

```
 .gitignore                                   |  3 ++-
 .memory/README.md                            | 15 ++++++++++-----
 docs/explanation/template-and-instances.md   |  3 ++-
 tools/memory_regen/tests/test_layout.py      |  7 ++++---
```

## Observed counts

| Point | Core suite | Snapshots | Instance |
|-------|-----------|-----------|----------|
| after `7d61983` | **876 passed** | 7 | — |
| after `2dcee85` | **876 passed** | 7 | **31 passed** |

`uv run python -m tools.harness_emit` → rc 0, `git status --porcelain` empty. Nothing here is emitted.

The plan's measured verify-order note held exactly: Task 1's verify ran AFTER its commit. The
staged-but-uncommitted `git rm`s would have produced the documented false red in
`test_catalog_invariant_to_untracked_local_state`; that pre-commit run was not performed, so no
false red was ever acted on.

## Task 1 — doc corpses

- `git rm docs/how-to/task-lifecycle.md` (106 lines) and
  `docs/explanation/task-lifecycle-shadow-metrics.md` (13 lines).
- **`docs/how-to/approve-a-golden.md` no-op recorded.** `ls` returned
  `No such file or directory`. It was removed in an earlier phase. CONTEXT D-10 and the ROADMAP
  both still list it as a whole file to delete; **both are stale.** The live defect was only the
  inbound link, which this commit removed.
- `docs/how-to/README.md`: the `:3` plane claim now reads *hand-authored, agent-writable — NOT
  constitution plane*, citing the resolver's `allow`; the `approve-a-golden.md` and
  `task-lifecycle.md` bullets are gone.
- **`docs/explanation/next-milestone-task-control-plane.md` was NOT deleted.** It carries a
  one-line HISTORICAL header naming Phase 43's deletion, ADR-0008's design-authority citation and
  the append-only rule, cross-referencing ADR-0012. Its `:330` link to the deleted how-to was
  rewritten to a non-pointer historical note referring to that header, so the deletion created no
  new dangler. Its remaining `handoff` / `task_control` / `risk_router` tokens are covered by the
  header per SC-5 and were deliberately not stripped.
- `README.ko.md:81` confirmed already cleared by plan 04. No cross-plan edit was needed or made.

Verify legs, all green: inbound-link sweep empty; **both preserved negative-control fixtures
survived at count 1 each** (`tools/harness_perms/tests/test_resolver.py`,
`tools/hooks/tests/test_contract_guard.py` — located by content, since Wave 1's three deletions
shifted their line numbers off the plan's `≈:71` / `≈:323`); deleted-module sweep over `docs/` empty.

## Task 2 — derived-plane and template-split prose

- `.memory/README.md`: CONSTITUTION row and member list drop root `golden/`; baselines re-scoped to
  `examples/<instance>/golden/` promoted by a human `GOLDEN_APPROVE_HUMAN` ratified through the
  CODEOWNERS `/examples/*/golden/` route; ADR-0012 clause (d) supersession pointer added beside the
  ADR-0001 citation. `:28` (both gates live) left alone as instructed.
- **`tools/memory_regen/tests/test_layout.py` rode in the same commit** (D-16). `CONSTITUTION_MEMBERS`
  collapsed to three; the `:17` comment and `:56` docstring reworded to "three" with the ADR-0012
  note. The assertion body, the test name and every other test in the module were untouched. As
  predicted, the test is not parametrized, so the suite total did not move.
- `.gitignore`: the `/golden-approve` comment restated as human ratification. The unanchored
  `**/golden/**/baseline.received.tsv` pattern at `:17` and its `:15-16` explanation untouched.
- `docs/explanation/template-and-instances.md`: `golden_runner` is no longer called a core tool;
  the direction is now stated as the instance-side runner importing the core.

## Deliberate no-change verdicts

| File | Reason |
|------|--------|
| `docs/explanation/agent-workflow-skillset-design-guide.md` (791 lines) | Its `handoff`, `/intake`, `/grill`, `/plan`, `/ship` tokens name EXTERNAL skill ecosystems it surveys, never this repo's shipped surface. By D-06 none is stale; editing would be sweeping by token, which D-05 forbids. |
| `docs/adr/README.md` | Measured accurate — the index correctly shows 0001 and 0010 superseded by 0012. Its only defect is ADR-0008 reading `accepted`, which IS D-14 and is human-gated. Constitution plane. |
| `CLAUDE.md:42,48,73` | Names `/golden-approve` inside a GSD-managed block regenerated from `PROJECT.md`; an edit here can be silently reverted by a GSD regeneration. |
| `tools/harness_emit/tests/test_coexist.py:56`, `tools/harness_lint/tests/test_commands.py:42` | Name `/golden-approve` inside a RETIREMENT RECORD. Narrating a retirement is not describing a live control, so by D-06 they are accurate history. They are why the sweep carries those two exclusions. |
| `docs/references/opencode-matt-workflows/**` | Vendored third-party bundle, 79 files. Not this repo's self-description. Excluded from every sweep by design. |

## Task 3 — `docs/glossary.md`: DEFERRED (checkpoint resolved `defer-to-pr`)

**Nothing was written. `docs/glossary.md` is byte-identical to HEAD.** The
`contract_guard` PreToolUse hook denies writes to it; `HARNESS_DEV_BYPASS` is forbidden by the plan
(bypassing the gate to tidy the plane the gate protects would falsify this phase's thesis), and a
`GOLDEN_APPROVE_HUMAN` token can only be set by a human. No write was attempted.

**SC-5 therefore has exactly one named, accepted open item.** It is cross-referenced to D-14's
ADR-0008 / ADR-0003 dangling-citation gap and lands with it at the milestone-close PR, where a
human ratifies the constitution plane — which is ADR-0012's whole thesis.

This branch relies on the `':!docs/glossary.md'` exclusion carried by this plan's task-2 sweep and
by plan 06's phase-close sweep. **That exclusion is a named deferral, not a blind spot.**

### What remains to be done, verbatim

Two lines are stale (**not three — see the criterion that did not hold, below**).

`docs/glossary.md:20`, current text:

```
| **`.received` / `.verified`** | The two-file golden split: `.received` is machine-proposed output; `.verified` is the human-promoted, approved baseline. Promotion is the `/golden-approve` step. |
```

proposed replacement:

```
| **`.received` / `.verified`** | The two-file golden split: `.received` is machine-proposed output; `.verified` is the human-promoted, approved baseline. Promotion requires a human `GOLDEN_APPROVE_HUMAN` ratification, gated again by CODEOWNERS at merge. |
```

`docs/glossary.md:23`, current text:

```
| **Constitution plane** | Human-owned, gated source of truth: `contracts/`, `golden/`, `docs/adr/`, `docs/glossary.md`. Changed only through review (CODEOWNERS) and the golden/drift gates. |
```

proposed replacement:

```
| **Constitution plane** | Human-owned, gated source of truth: `contracts/`, `docs/adr/`, `docs/glossary.md` (ADR-0001's fourth member, root `golden/`, is superseded by ADR-0012 clause (d); instance baselines live at `examples/<instance>/golden/`). Changed only through review (CODEOWNERS) and the golden/drift gates. |
```

Do not touch `:13`, `:19`, `:21` or any other row. `:21` ("no agent self-blesses a golden") is still
true and must survive.

## Criteria that did not hold

**1. Task 3's third defect does not exist, and its verify leg's expected count is wrong.**

The plan's task-3 context lists three stale claims and its verify leg states
`git grep -c 'golden-approve' docs/glossary.md` → *defer-to-pr: expect 2*.

Measured: **1**, and `grep -o ... | wc -l` confirms **one occurrence in the whole file**, on `:20`.

The plan attributes the sentence *"…Promotion is the `/golden-approve` step."* to **both** `:19`
and `:20`. It occurs only on `:20`. Line `:19` is the **Contract-drift gate** row, whose actual text
ends *"…classifies the change breaking vs non-breaking."* — it never names `/golden-approve`, and
its phrase "without a paired golden update" remains accurate because instance goldens still exist.
`:19` requires no repair.

Per instruction this was recorded rather than adjusted: no edit was made to the plan, the glossary,
or the verify expectation. The deferral above therefore carries **two** replacement lines, not three.

## Deviations from plan

**1. [Rule 1 — internal contradiction] `.memory/README.md:20` and `:32` corrected to "three"**

- **Found during:** Task 2
- **Issue:** The plan names `:13`, `:25` and `:29` only. But `:20` reads "Its **four** members are:"
  immediately above the list, and `:32` reads "onto any of the **four** members". Collapsing the row
  and the bullet list without these would have left the file asserting four members while listing
  three — a self-contradiction introduced by this very commit.
- **Fix:** both reworded to "three". No other prose touched.
- **Commit:** `2dcee85`

**2. [scope note] `:25` re-scoped rather than deleted**

The plan offered either. The bullet was removed from the three-member list (so the list reads
exactly three) and its promotion mechanism restated as a following note about
`examples/<instance>/golden/`. This keeps the `GOLDEN_APPROVE_HUMAN` / CODEOWNERS fact, which other
documents depend on, without implying a fourth member. No surface growth: net one line.

## Anything the plan did not anticipate

- **The two preserved fixtures had moved again.** The plan predicted `≈:71` and `≈:323` after plan
  01's deletions. Both were located by content instead of line number, as instructed. Both survived
  at count 1.
- **`git grep -c` counts matching LINES, not occurrences.** Even had `:19` carried a mention, the
  plan's "expect 2" would only be reachable if the two mentions sat on different lines. This is
  worth noting for plan 06's phase-close sweep, which uses the same idiom.
- Nothing else. Every other measured fact in the briefing held exactly: 876 after both commits,
  instance 31, the Task 1 verify-order inversion, and the `test_layout.py` twelfth-copy coupling.

## Self-Check: PASSED

- `docs/how-to/task-lifecycle.md` — MISSING (deleted, intended)
- `docs/explanation/task-lifecycle-shadow-metrics.md` — MISSING (deleted, intended)
- `docs/explanation/next-milestone-task-control-plane.md` — FOUND, contains `HISTORICAL`
- `tools/memory_regen/tests/test_layout.py` — FOUND, contains `CONSTITUTION_MEMBERS` (three)
- `docs/how-to/README.md` — FOUND
- commit `7d61983` — FOUND
- commit `2dcee85` — FOUND
- `docs/glossary.md` — unchanged vs HEAD, tree clean
