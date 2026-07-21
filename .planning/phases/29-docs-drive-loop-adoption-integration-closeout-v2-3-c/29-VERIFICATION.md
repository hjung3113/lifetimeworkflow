---
phase: 29-docs-drive-loop-adoption-integration-closeout-v2-3-c
verified: 2026-07-22T00:00:00Z
verified_at_commit: f6ae4bd
status: human_needed
score: 4/4 success criteria verified
re_verification:
  previous_status: human_needed
  previous_score: "2/4 (SC-1, SC-2); SC-3 blocked on a human-only write; SC-4 partial"
  previous_commit: 1e1ef3b
  gaps_closed:
    - "SC-3 — `docs/.docs-review-ledger.toml` landed (c32c08d). `uv run python -m tools.docs_guard` now exits 0 with 8/8 bindings FRESH, uncovered_max = 7."
    - "RAT-2 — ADR-0010 is `accepted`, Date 2026-07-22, Deciders kimhyojung (ad4e339). `exclusion_reason('docs/adr/0010-...md')` now returns `accepted-adr`, so `registry._adr_status` no longer treats it as a rejection."
    - "SC-4 item `lifecycle-eval` step 2 — no longer red. `tools/lifecycle_eval/tests/conftest.py` exists; `uv run pytest tools/lifecycle_eval` = 3 passed."
    - "SC-4 item `examples/log-parser` golden parity — no longer red. `uv run pytest examples/log-parser/tests` = 14 passed with .NET actually executing (dotnet resolved at ~/.dotnet/dotnet)."
  gaps_remaining: []
  regressions: []
  note: >-
    The lead's change-list was INCOMPLETE. Two of the three "known pre-existing reds" were not
    carried forward at all — they were REPAIRED by two `fix(quick)` commits that landed after the
    prior report (934770e, 26b88df), neither of which was in the list I was given. Both repairs are
    real and I confirmed them by execution, not by reading the commit messages.
human_verification:
  - test: >-
      DECISION — the ledger write-deny is enforced only on the `Write`/`Edit` tool matcher, but the
      bash permission matrix allows `uv *` unprompted. `resolve_bash(matrix['bash'], "uv run python
      -c \"open('docs/.docs-review-ledger.toml','w').write(...)\"")` returns **`allow`**. Decide:
      close this route now, or record it as accepted harness-wide debt with a named owner?
    expected: >-
      A deny that does not depend on which tool spells the write. Options: (a) add a PreToolUse
      `Bash` matcher that resolves redirect/interpreter targets against `path_deny_globs`; (b) narrow
      `uv *` in `harness/permission-matrix.json`; (c) accept and record, acknowledging in ADR-0010
      that clause 3b binds the Write/Edit and adoption-apply paths, not every agent action.
    why_human: >-
      Scope decision, and it touches the constitution plane (ADR-0010 + permission-matrix). Not an
      agent action, and not a Phase-29 regression — `contract_guard` has had the same tool-matcher
      shape since Phase 4, so `contracts/**` and `golden/**` inherit it too.
  - test: >-
      DECISION — 29-04 Task 4 was discharged in OUTCOME but not in LETTER. The human took Option A
      (one seeding round straight to exit 0), not the Option B the prior report recommended. Confirm
      that is the intended disposition and close 29-04, or run the Option B round.
    expected: >-
      SC-3's contract is satisfied either way (8/8 FRESH). The only thing Option B added was a human
      watching the gate move; I obtained that evidence independently (see the Drive-Loop Transition
      Probe below), so the substance is covered even though the letter of Task 4 is not.
    why_human: "Task-closure bookkeeping on a `gate=\"blocking-human\"` checkpoint."
deferred:
  - truth: "RAT-4 — ratify the Phase-28 `HARNESS_DEV_BYPASS` constitution-plane schema write"
    addressed_in: "complete-milestone (v2.3)"
    evidence: ".planning/STATE.md:59-60 records RAT-4 and RAT-5 as outstanding and explicitly NON-BLOCKING for Phase 29. Neither appears in any Phase-29 success criterion."
  - truth: "RAT-5 (merge half) — land ADR-0004/0005/0006/0007 on `main`"
    addressed_in: "complete-milestone (v2.3)"
    evidence: >-
      The repo-config half IS done and independently confirmed — `gh repo view --json defaultBranchRef`
      returns `main` (f009306). The merge itself remains, with the branch 614 commits ahead of
      `origin/main` (.planning/STATE.md:384).
---

# Phase 29: Docs Drive Loop + Adoption Integration + Closeout (v2.3 C) — Verification Report

**Phase Goal:** bounded 사람 대면 docs 워크플로를 추가하고 adoption seeding을 연결하며 세 테마를 전체 게이트 fan-in으로 닫는다.
**Verified:** 2026-07-22, at commit `f6ae4bd`, working tree clean before and after this run.
**Status:** `human_needed` — all four success criteria VERIFIED; two decisions escalated, neither blocking the goal.
**Re-verification:** Yes — after the human's RAT-1/2/3 discharge. Previous status `human_needed` @ `1e1ef3b`, 2/4.

Every number below was produced by running the command in this session. The lead's change-list, the
SUMMARY files and `.planning/v2.3-MILESTONE-AUDIT.md` were treated as hypotheses to falsify. Nothing
in the working tree was modified: the one mutation experiment was run in a throwaway `git worktree`
under the scratchpad, which was removed afterwards.

## What Changed Since `1e1ef3b`

Twenty commits. The four the lead named are real and do what they claim. **Two more that the lead
did not name materially changed the verdict** — they repaired the two SC-4 reds I was told to expect
to still be red:

| Commit | Effect | Confirmed by |
|---|---|---|
| `c32c08d` | ledger landed, 90 lines, author `kimhyojung <hjung3113@gmail.com>` | guard exit 0, 8/8 FRESH |
| `ad4e339` | ADR-0010 `proposed` → `accepted` | `sed -n '5,7p'` + live `exclusion_reason` |
| `b443c79` | STATE.md / audit records RAT-1/2/3 | read |
| `f009306` | default branch back to `main` | `gh repo view` → `main` |
| **`934770e`** *(not in the lead's list)* | **added `tools/lifecycle_eval/tests/conftest.py`** | `pytest tools/lifecycle_eval` → **3 passed**, was exit 2 |
| **`26b88df`** *(not in the lead's list)* | **`IsConfined` decided on real paths, not spellings** | `pytest examples/log-parser/tests` → **14 passed**, was 2 failed |

I checked `git merge-base --is-ancestor` for both: each landed **after** `1e1ef3b`, so the prior
report's observation of them as red was correct at the time. These are not regressions and not
things I repaired — they were already fixed when I arrived.

## Goal Achievement

### Observable Truths (the four ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC-1 | `/docs-update` + `docs-upkeep` emit byte-identically to both runtimes; the five exclusions are a TESTED gate | ✓ VERIFIED | Identity assertions intact at `test_exclusions.py:166,170,174`; all five classes classify correctly live; emit round-trip is a fixed point |
| SC-2 | `/adopt` can propose a binding but cannot self-review it to green | ✓ VERIFIED | Ledger DENY holds with **both** bypass tokens set; registry stays writable; 314 tests green |
| SC-3 | required seed documents are fresh or exactly dispositioned | ✓ VERIFIED | `uv run python -m tools.docs_guard` → **exit 0**, 8 bindings, **8/8 FRESH**, uncovered 7 = `uncovered_max` |
| SC-4 | the full fan-in is green | ✓ VERIFIED | **16 of 16** executed gate commands exit 0 — table below |

**Score: 4/4 verified.** Up from 2/4.

### SC-1 — still verified after the constitution-plane change

`6d74a50` added `docs/glossary.md` as a fourth constitution member after the prior report, which
changes the set SC-1's classifier consumes. I re-ran the classifier rather than assuming the prior
mutation proofs still bound:

```
contracts/sample/greeting.schema.json           -> constitution-plane
docs/adr/0010-human-docs-review-obligation-model.md -> accepted-adr
golden/x.tsv                                    -> constitution-plane
docs/reference/api.md                           -> derived-plane
.memory/derived/repo-map.md                     -> derived-plane
docs/glossary.md                                -> constitution-plane
docs/how-to/task-lifecycle.md                   -> None      # correctly NOT excluded
```

The three identity assertions still bind `exclusions` to the homes (`contract_guard`, `destinations`,
`registry`), so a locally retyped list still cannot keep the proofs green. `CONSTITUTION_GLOBS` at
`tools/hooks/contract_guard.py:53` now carries four members and `exclusions` picks that up by
identity, not by copy — which is exactly what the identity assertion is for, and it is the reason
this change did not silently desynchronize the classifier.

Note the ADR row: at `1e1ef3b` ADR-0010 was `proposed`, so it did **not** classify `accepted-adr`.
RAT-2 is observable in the classifier's output, not only in the file's frontmatter.

Emit round-trip: `uv run python -m tools.harness_emit` wrote **100 artifacts** and
`git status --porcelain` came back **empty**. `uv run pytest tools/harness_lint -q` → **323 passed**
(the claimed number; 316 at the prior report — the delta is the glossary-plane tests from `732a0d5`
/`6d74a50`).

### SC-2 — verified; the three layers hold, with one scope correction

Live check with **both** bypass tokens exported:

```
GOLDEN_APPROVE_HUMAN=1 HARNESS_DEV_BYPASS=1
  docs/.docs-review-ledger.toml -> DENY
  docs/doc-dependencies.toml    -> allow      # DOCSUP-07 needs /adopt to propose rows
  docs/glossary.md              -> allow      # ledger_guard's scope; contract_guard owns this one
```

`uv run pytest tools/adoption_apply/tests/test_docs_binding_proposal.py
tools/adoption_apply/tests/test_constitution_refusal.py tools/docs_guard/tests/` → **314 passed**.

**Scope correction — see the human decision item.** The deny is enforced by a PreToolUse hook whose
matcher is `Write|Edit` (`.claude/settings.json:160-168`) and by an opencode plugin that returns
early unless `input.tool` is `write` or `edit` (`.opencode/plugin/ledger-guard.ts:70`). The bash
matrix allows `uv *` unprompted, so:

```
resolve_bash(matrix['bash'], "cat > docs/.docs-review-ledger.toml")                      -> 'ask'
resolve_bash(matrix['bash'], "uv run python -c \"open('docs/.docs-review-ledger.toml','w')...\"") -> 'allow'
```

This does not falsify SC-2 as written — SC-2 is about `/adopt`, and the adoption-apply path raises
`ReviewLedgerRefusal` in code regardless of which tool called it. But the prior report's stronger
sentence, "**No agent action can satisfy SC-3**", is not true as stated, and neither is ADR-0010
clause 3b's universal phrasing. I looked specifically for this milestone's recurring defect — a
control that ships green while bypassable — because the prior report said it went looking and did
not find one. This is one. It is **pre-existing and harness-wide**, not a Phase-29 regression:
`contract_guard` has the same tool-matcher shape, so `contracts/**` and `golden/**` inherit it. It
is recorded nowhere I could find (`grep -i bash` across `docs/adr/*.md`, `AUDIT-FINDINGS.md`,
`v2.3-MILESTONE-AUDIT.md`), which is why it is escalated rather than filed as already-known.

### SC-3 — verified, and the drive loop was observed moving

`uv run python -m tools.docs_guard` → **exit 0**:

```
docs-guard: 8 binding(s); 7 uncovered human-authored document(s) (uncovered_max = 7).
docs-guard: OK
```

All eight bindings `[FRESH]`, each with `digest delta: source X -> X; target Y -> Y`. Zero broken,
zero stale. `[coverage]` in the ledger sets `uncovered_max = 7` and `binding_min = 8`, matching the
live counts exactly — the ratchets are set at the observed values, not slack.

The ledger's own header documents why every seed row is `reviewed-no-change`/`REVIEWED_STILL_CURRENT`
and never `updated` (there is no previous committed ledger to have been updated *from*; `updated`
would classify `unverified-disposition` and fail closed). That reasoning is correct and it is the
reason the human's Option A worked in one round.

#### Drive-Loop Transition Probe — the evidence Option B was supposed to produce

SC-3's real risk is a gate that is green because it never moves. I tested this in a **throwaway
`git worktree` at HEAD** under the scratchpad, so the working tree was never touched:

| Step | Action | `docs_guard` exit | Observed |
|---|---|---|---|
| 0 | baseline | **0** | 8/8 FRESH |
| 1 | append one comment line to `docs/glossary.md` (**advisory** binding) | **0** | `[STALE_ADVISORY] normalize-spec-glossary`, `warn: stale-digest` |
| 2 | revert; append one comment line to `docs/how-to/task-lifecycle.md` (**required** binding) | **1** | `[STALE_REQUIRED] task-control-cli-howto`, `fail: stale-digest`, `docs-guard: FAILED` |
| 3 | revert | **0** | green again |

Worktree removed; `git status --porcelain` on the real tree is empty. The gate **is** seen to move
green → red → green on a real document edit, and it correctly discriminates advisory (warn, exit 0)
from required (fail, exit 1). That is the property Option B existed to demonstrate, and it now
rests on an executed observation rather than on inference from a digest delta.

**On the ledger's provenance.** The commit is authored `kimhyojung <hjung3113@gmail.com>` — but that
is the same git identity every agent commit in this repo carries, so authorship metadata alone
cannot distinguish a human row from a self-blessed one. The structural argument is the write-path
deny, which I verified holds for `Write`/`Edit` and does *not* hold for the `uv run python` route.
I am **not** suggesting the ledger is anything other than what the lead says it is; I am recording
that the harness cannot currently *prove* it, which is the same gap as the decision item above.

### SC-4 — fan-in, independently observed. Every gate green.

Run at `f6ae4bd`, clean tree, macOS host, `dotnet` resolved at `~/.dotnet/dotnet`. Nothing repaired
during the run.

| # | SC-4 item | Command | Exit | Observed |
|---|---|---|---|---|
| 1 | full pytest | `uv run pytest -q` | **0** | **1500 passed, 8 snapshots** in 85.20s |
| 2 | contract-drift (root) | `tools.contract_drift.drift` | **0** | live manifest matches baseline |
| 2b | contract-drift (example) | `--contracts-dir examples/log-parser/contracts --baseline .../manifest.json` | **0** | clean |
| 3 | golden (root identity) | `uv run pytest tools/golden_runner` | **0** | **17 passed** |
| 3b | golden (example .NET parity) | `uv run pytest examples/log-parser/tests` | **0** | **14 passed** — was 2 failed/10 passed |
| 4 | workspace drift | `tools.contract_drift.drift --workspace` | **0** | 2 members clean, 1 edge resolved |
| 4b | cross-repo pytest set (`ci.yml:331`) | the five paths | **0** | **31 passed** |
| 5 | stale-derived | `docs_sync && memory_regen.contracts_index`, then porcelain | **0** | porcelain over `docs/reference` + `.memory/derived` **empty** |
| 6 | lifecycle (runner) | `tools.lifecycle_eval.runner` | **0** | green |
| 6b | lifecycle (tests, `ci.yml:194`) | `uv run pytest tools/lifecycle_eval` | **0** | **3 passed** — was exit 2, collection error |
| 7 | GEN-04 twin + model-id + injector budget | `pytest -k "model_id or injector or budget or core_no_example"` | **0** | **42 passed** |
| 7b | full harness lint | `uv run pytest tools/harness_lint -q` | **0** | **323 passed** |
| 8 | docs guard | `uv run python -m tools.docs_guard` | **0** | 8 bindings, **8/8 FRESH** — was exit 1 |
| 8b | docs guard unit (`ci.yml:310`) | `pytest tools/docs_guard tools/memory_regen/tests/test_docs_staleness.py -q` | **0** | **252 passed, 1 snapshot** |
| 9 | emit-drift | `tools.harness_emit` then `git status --porcelain` | **0** | **100 artifacts, porcelain EMPTY** |
| 12 | `git diff --check` | `git diff --check` | **0** | clean |

**16 of 16 exit 0.** SC-4's enumerated list — `uv run pytest` + contract-drift + golden + workspace
drift + stale-derived + lifecycle + GEN-04 twin + docs guard + emit-drift + model-identifier lint +
injector budget + `git diff --check` — is green item-for-item. This is the criterion that was
`PARTIAL` at `1e1ef3b`; both reds are gone, and neither was papered over.

One correction to my own process: my first example-instance contract-drift run reported 19 spurious
drift rows because I passed `--contracts-dir` with the *root* manifest. The flag is `--baseline`,
not `--manifest`, and `ci.yml:143` pairs them correctly. Re-run with the paired baseline: exit 0.
Recording this because a verifier's own invocation error is exactly the kind of thing that becomes a
fabricated regression report.

### Pre-existing conditions — confirmed unchanged, not repaired

| Condition | Expected | Observed | Verdict |
|---|---|---|---|
| `ruff check .` baseline | ~617 errors | **`Found 617 errors`**, 40 fixable | ✓ unchanged, exactly |
| `lifecycle-eval` CI step 2 | red, Phase-23 debt | **now GREEN** — `conftest.py` added by `934770e` | ✗ lead's premise stale; repaired before I arrived |
| `examples/log-parser` `IsConfined` | red on macOS | **now GREEN** — real-path fix in `26b88df` | ✗ lead's premise stale; repaired before I arrived |

I did not repair anything. The two stale premises were already resolved in commit history; I
verified that by `git merge-base --is-ancestor` plus execution, not by trusting the commit subjects.

### 29-04 blocking-human task disposition

| Task | Gate | `done` condition | Verdict |
|---|---|---|---|
| Task 2 — HUMAN authors and lands the review ledger | `blocking-human` | "A human has landed the ledger and `uv run python -m tools.docs_guard` exits 0" | ✓ **DISCHARGED** — `c32c08d`, guard exit 0 |
| Task 4 — HUMAN re-records the reviewed row and closes SC-3 | `blocking-human` | "A human has **replaced** the `gate-model-permission-surface` row and the guard exits 0" | ⚠️ **DISCHARGED IN OUTCOME, NOT IN LETTER** |

Task 4 presupposed Option B: a stale transition, then a replacement row with `disposition = "updated"`.
The human took Option A — all eight rows seeded at once, none `updated`. So no row was ever
"replaced," and the ledger's own header explains (correctly) why `updated` would have been *wrong*
in a first-ever ledger. Note also that the seeded `gate-model-permission-surface` target digest is
`62f43f7682be`, a third value distinct from both the `4568f3a9…` and `8df85e6e…` in 29-04-SUMMARY.md
— the ledger header flags that proposal as stale and says not to use it, which is accurate.

SC-3 is the contract and SC-3 is satisfied. The only thing Option B would have added is a human
watching the gate move, and the Drive-Loop Transition Probe above supplies that observation. My call
is that Task 4 should be closed as discharged-via-Option-A, but that is the human's bookkeeping
call, not mine — hence the decision item.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|---|---|---|---|
| `.claude/settings.json:160-168`, `.opencode/plugin/ledger-guard.ts:70`, `harness/permission-matrix.json` `bash."uv *"` | The ledger (and constitution) write-deny is enforced per **tool matcher** (`Write`/`Edit`), while `uv *` is an unprompted `allow`, giving a covered path an uncovered spelling | ⚠️ **WARNING** | The strongest claims in ADR-0010 clause 3b and in the prior report ("no agent action can satisfy SC-3") are overclaimed. Pre-existing and harness-wide — `contract_guard` shares the shape — so not a Phase-29 regression, and SC-2's literal `/adopt` predicate still holds. Unrecorded anywhere; escalated as a decision. |
| `harness/permission-matrix.json` `path_deny_globs` | `docs/reference/**` and `.memory/derived/**` still absent; no PreToolUse hook denies them | ⚠️ WARNING | Carried forward unchanged from the prior report. Two of SC-1's five exclusion classes are enforced at the DECISION layer plus the detective `stale-derived` job, not by a preventive runtime deny. Not a Phase-29 defect — SC-1 asks for a tested classifier and that is what shipped. |
| `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` | committed trailing whitespace | ℹ️ INFO | Syrupy artifact in a derived snapshot; `git diff --check` clean on a clean tree. Already in the audit. |

No debt-marker gate violations: no unreferenced `TBD`/`FIXME`/`XXX` in the phase's modified files.

### Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| DOCSUP-06 | ✓ **SATISFIED** | Was "machinery complete, BLOCKED on RAT-1". The block is gone: guard exit 0, 8/8 FRESH. Classifier live-checked across all five classes; 323 harness-lint + 252 docs-guard tests green; emit is a fixed point at 100 artifacts. |
| DOCSUP-07 | ✓ SATISFIED | All three layers live; ledger denied with both tokens set; registry writable; 314 tests green. Subject to the tool-matcher scope note above. |

### Gaps Summary

**No gaps.** All four success criteria are verified by executed commands, and the two items the prior
report escalated as blocking are both resolved — one by the human's ratification work, one by two
repairs that predated this verification and that the lead's brief did not mention.

Status is `human_needed` rather than `passed` for two escalations, **neither of which blocks the
phase goal**:

1. **The tool-matcher scope of the ledger deny.** `uv run python -c "open(ledger,'w')"` resolves to
   `allow`. SC-2 as written survives this, because SC-2 is about the `/adopt` path and that path
   refuses in code. But the surrounding prose overclaims, and this is the fourth consecutive
   milestone in which the recurring defect is a control that is green in the shape it was tested and
   open in a shape it was not. It is pre-existing and harness-wide, so repairing it inside a closeout
   would be the wrong discipline — but recording it as a decision rather than letting the
   overclaimed sentence stand is the right one.
2. **29-04 Task 4's letter vs. outcome.** Bookkeeping on a `blocking-human` checkpoint.

RAT-4 and the merge half of RAT-5 are deferred to `complete-milestone`; STATE.md records both as
non-blocking and neither appears in a Phase-29 success criterion. The repo-config half of RAT-5 is
independently confirmed done — the GitHub default branch is `main`.

One process note for the lead, offered because it changed the verdict: three of the premises I was
handed were stale, all in the same direction — two "known reds" were already fixed, and the
change-list omitted the two commits that fixed them. Had I verified against the brief instead of
against the repository, I would have reported two regressions that do not exist.

---

_Verified: 2026-07-22 at commit `f6ae4bd`_
_Verifier: gsd-verifier (goal-backward, adversarial stance)_
