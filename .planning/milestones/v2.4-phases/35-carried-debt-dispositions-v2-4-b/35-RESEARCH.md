# Phase 35: Carried-Debt Dispositions — Research

**Researched:** 2026-07-22
**Confidence:** HIGH for DEBT-03 and DEBT-04 (both established by running code in this repo, not by
reading about it). MEDIUM-HIGH for DEBT-02, whose entire evidence base is prose written by others.

This phase's research is unusual in that two of the three items are settled by **execution**. Where
that was possible it was done, and the result is recorded here as a finding rather than a plan.

---

## DEBT-04 — `DEF-05-02-1`: does it still reproduce?

### The record

`.planning/STATE.md:295` and `.planning/phases/05-despecialization/deferred-items.md` both carry it:
three tests in `tools/hooks/tests/test_commit_gate.py` — `test_drift_present_blocks`,
`test_golden_skip_does_not_suppress_drift`, `test_from_hook_blocks_commit_on_drift` — monkeypatch
`run_gate` to report drift and assert a BLOCK, but never `delenv("GOLDEN_APPROVE_HUMAN")`. With the
token live in the shell, the 05-01 drift-approval path turns the expected block into a pass, so they
fail only when the session token is exported and are green in CI.

### Finding: it does NOT reproduce. Repaired 2026-07-09 by `ccef8b4`.

| Run | Result |
|---|---|
| `env -u GOLDEN_APPROVE_HUMAN uv run pytest <the 3 tests> -q` | **3 passed** |
| `GOLDEN_APPROVE_HUMAN=phase-35-probe uv run pytest <the 3 tests> -q` | **3 passed** |
| `GOLDEN_APPROVE_HUMAN=phase-35-probe uv run pytest tools/hooks -q` | **112 passed** |

`git log -S'_no_ambient_approval'` finds exactly one commit: `ccef8b4` *test(commit-gate): make
drift-block tests hermetic to ambient GOLDEN_APPROVE_HUMAN* (2026-07-09), whose message ends
"Resolves DEF-05-02-1". So the id was closed in code and the **record was never updated** — the debt
that survived into v2.4 is a bookkeeping debt, not a test defect.

The shipped fix is **broader** than the record's suggestion. The record proposed a per-test
`monkeypatch.delenv` in three places; `ccef8b4` instead added an autouse fixture
(`tools/hooks/tests/test_commit_gate.py:28-38`) covering **every** test in the module, and stripped
`HARNESS_DEV_BYPASS` alongside it for the identical reason — a dev session's opt-out would
false-green the same base-block tests. The approval-path tests set their token in-body, which runs
after the autouse fixture, so they are unaffected. That generalization is worth noting because the
same class of leak could otherwise have re-entered through any test added to the module later.

### Why a green run was not accepted as sufficient

A passing suite cannot distinguish "repaired" from "the symptom relocated". The fixture body was
neutered (both `delenv` calls replaced with `pass`) and the module re-run with the token exported:
**exactly the three named tests failed**, and no others. That is positive evidence the fixture is
the load-bearing repair and that the record's root-cause diagnosis was correct. The mutation was
reverted and the tree verified clean.

**Implication for the plan:** no code change. The work is closing the record accurately and telling
the orchestrator what `STATE.md` should say.

---

## DEBT-03 — compile the graph once per report (28 IN-03)

### Live sites, line numbers verified

The brief's line numbers were checked before being trusted, and one was wrong:

| Claimed | Actual | Note |
|---|---|---|
| `tools/docs_guard/cli.py:233` (comprehension) | **correct** — `{entry["id"]: impact_ids(entry["sources"]) for entry in result["bindings"]}` | inside `main`'s `try`, so its raise is already contained |
| `tools/docs_guard/docs_staleness.py:100` (loop) | **path wrong** — the module is `tools/memory_regen/docs_staleness.py`, and `impact_ids(entry["sources"], cfg)` is indeed at **line 100** | the placement is deliberate and documented (`docs_staleness.py:5-11`, D-06/D-10): the module lives under `memory_regen` so `/refresh-memory` can name it legally |

A third call site exists that the audit did not name: `cli.py:174`, `render`'s fallback for when no
impact map is passed. It has the same shape and is fixed with the same change.

### The residual's framing is a false binary

The residual left this open because closing it "means either changing `impact.py`'s public signature
or adding cached state to a module whose docstring makes a point of being pure". Both horns are
genuinely bad:

- **A cache** contradicts `impact.py:3` ("A pure helper: no filesystem writes, no CLI, no exit
  codes") and `test_module_performs_no_filesystem_write`, which pins that self-description. Worse,
  it has no sound key: `cfg` is a `dict`, which is unhashable, so any memo would either be keyed on
  nothing (wrong across differing `cfg`) or need a hand-rolled canonical serialization of the config
  — real machinery to avoid re-reading a file.
- **A signature change** on `impact_ids` ripples into `cli` (2 sites), `docs_staleness.rows`, and
  `test_impact.py` / `test_report.py` / the guard's own tests, and buys nothing the caller cannot
  get from a second name.

**The third option both call sites are already asking for:** each one builds a
`{binding id: [ids]}` mapping. A batch entry point `impact_map(bindings, cfg)` compiles once and
returns exactly that. `impact_ids` is then untouched — same signature, same behaviour, still pure —
and the traversal is extracted to a private `_ids_for(paths, relationships, graph)` so the two entry
points cannot drift apart. This is the recorded decision; the two rejected alternatives are recorded
**in the `impact_map` docstring**, so a future reader who reaches for a cache finds the reason not to
at the site rather than in a planning file.

### How determinism gets proven

The output must be byte-identical, which is checkable rather than assertable:

```
sha256(python -m tools.docs_guard stdout) = 70247c1b4fb0e8a3079aca95724d4f15ca18f8fd2de6bff9bfad985f24153764
sha256(stderr)                            = e3b0…855   (the empty-input digest — stderr is empty)
exit 0
```

captured **before** the change and re-checked after.

The subtle part is the regression test. A per-binding loop produces the **identical report**, so no
assertion about report content can fail under the regression. The only witness is the **number of
live reads**: monkeypatch `compile_graph` and `effective_relationships` to count, run a report over
three bindings, assert exactly one call each. Four tests result — batch-equals-loop equivalence
(the answer is a rearrangement, never a different result), the compile count, zero compiles at zero
bindings, and no state carried between calls with differing `cfg` (the test a naive cache fails).

### One free improvement, recorded so it is not mistaken for scope creep

`docs_staleness.rows` filtered bindings *inside* the loop, so it compiled the graph once per
**registered** binding even when none qualified. Filtering to the qualifying set before building the
map makes a clean report compile the graph **zero** times. Same output; the ordering just stopped
being wasteful.

---

## DEBT-02 — Phase 27's missing `VERIFICATION.md`

### What the precedent actually is

The brief cites `27.2-VALIDATION.md` and `28-VALIDATION.md`. Both exist and both carry the shape to
copy: frontmatter `authored: at-closeout`, then an opening blockquote stating in plain words that
the document was written at closeout, that the phase ran without it, that it is dated today rather
than back-dated, and that it "claims no prospective authority it never had" — followed by an
explicit list of the artifacts each row was transcribed from.

Note the distinction, because it changes what this phase owes: those two are **VALIDATION** files
(a *strategy* reconstructed after the fact). Phase 27 already **has** a contemporaneous
`27-VALIDATION.md` — `status: approved`, dated 2026-07-21, with a 25-row per-task verification map
synced against the six plans after plan-checker iteration 1. What Phase 27 lacks is the
**VERIFICATION** file, the *outcome* report. The nearest structural precedent for that is
`27.2-VERIFICATION.md` / `28-VERIFICATION.md` — goal, observable-truths table with per-criterion
evidence, required artifacts, key links, behavioral spot-checks, anti-patterns, gaps.

So the document to author is a **VERIFICATION-shaped body carrying the VALIDATION precedent's
honesty stamp**. Neither precedent supplies both halves on its own.

### Why authoring beats writing off

The write-off option is real and exists for a phase whose artifact base cannot substantiate
anything. Phase 27's can: six PLAN/SUMMARY pairs, `27-REVIEW.md`, `27-PATTERNS.md`,
`27-RESEARCH.md`, `deferred-items.md`, the approved `27-VALIDATION.md`, and — unusually strong —
**two follow-on phases (27.1 and 27.2) that existed specifically to re-verify Phase 27's output
adversarially and found real defects in it**. Declaring all of that unusable would discard
evidence, which is a different failure from refusing to invent it.

### The line this document must not cross

Every row is transcribed from an artifact that **already existed**, cited by name. Three things are
therefore forbidden:

1. **A row with no artifact behind it.** It becomes a gap, stated plainly, not a softened row.
2. **Today's test run as phase-time evidence.** The suite is green now; that says the code survived
   nine subsequent phases, not that the phase was verified at close. Any present-tense check is
   labelled as such and kept out of the goal-achievement table.
3. **A verdict the artifacts do not support.** If the SUMMARYs record a claim but nothing
   independently checked it, the row says the claim is *recorded*, not that it is *verified*.

The gaps section is not an appendix here. It is the part that makes the rest of the document
trustworthy, and a reader who skips to it should be able to see exactly what this closeout could
not establish.

---

## Sources

All findings above are from this repository at branch `claude/data-pipeline-harness-8aypct`:
`tools/hooks/tests/test_commit_gate.py`, `tools/docs_guard/{impact,cli}.py`,
`tools/memory_regen/docs_staleness.py`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`,
`.planning/ROADMAP.md`, `.planning/phases/05-despecialization/deferred-items.md`, and the
`.planning/milestones/v2.3-phases/{27,27.2,28}-*/` artifact sets. Commit citations
(`ccef8b4`) and all test counts and digests were produced by running the commands shown.
