---
phase: 28
slug: human-docs-registry-guard-derived-queue-v2-3-c
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-21
authored: at-closeout
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **Authored at closeout, not during execution.** This phase ran without a VALIDATION.md; the
> `.planning/v2.3-MILESTONE-AUDIT.md` Nyquist table recorded that absence as debt. This document is
> dated today and reconciled against what actually ran — every row is transcribed from the nine
> PLANs' `<automated>` verify blocks, their SUMMARYs, `28-FIXES.md`, `28-REVIEW.md` and
> `28-VERIFICATION.md` (status `human_needed`, 4/4 truths, verified at commit `56cbac7`). It is
> **not** a back-dated artifact and claims no prospective authority it never had.
>
> Source: `28-CONTEXT.md` + `28-RESEARCH.md` + the nine PLANs + `28-VERIFICATION.md`.

**Standing rule for this phase:** every control-shaped change gets its adversarial-input table
authored FIRST and shown RED against pre-fix code, and the RED must fail **for the stated reason**.
This phase is where the rule earned its place: `28-REVIEW.md` found **three Criticals** all of the
same shape — *a control ships GREEN while being bypassable, because every fixture used the one
input spelling the control already handled.* What caught them was adversarial mutation testing by
the reviewer (delete the control, see whether anything reds), not the suite passing.

**Second standing rule, structural to this phase:** the agent may not author
`docs/.docs-review-ledger.toml`, in the repo or in a scratch directory, under any token. A green
gate reached by an agent-authored disposition is exactly the failure this phase exists to prevent.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (workspace-pinned; `tools/docs_guard` added as a uv workspace member in 28-02) |
| **Config file** | root `pyproject.toml` (uv workspace) |
| **Quick run command** | `uv run pytest tools/docs_guard -q` |
| **Full suite command** | `uv run pytest -q` |
| **Observed at phase end (`56cbac7`)** | **1459 passed, 8 snapshots passed** in 73.75s (`28-VERIFICATION.md:76`) |
| **Harness lint at verification** | **316 passed** — higher than the 300 in `28-FIXES.md` because the branch had advanced into Phase 29 (`28-VERIFICATION.md:78`) |
| **Emit round-trip** | **100 artifacts emitted, tree clean** (`28-VERIFICATION.md:79`) |
| **`uv run python -m tools.docs_guard`** | **exit 1** — 6 × `broken-binding`, 2 × `STALE_ADVISORY`, 8 bindings, 7 uncovered, no ratchet (`28-VERIFICATION.md:80`) |

That exit 1 is the **designed pre-ratification state**, not a red gate. See Human-Gated below.

---

## Sampling Rate

- **After every task commit:** the owning module's selection (`tools/docs_guard`,
  `tools/memory_regen`, `tools/adoption_apply`, `tools/harness_lint`)
- **After every plan wave:** `uv run pytest -q` + `uv run python -m tools.contract_drift.drift`
- **Phase gate (28-08 Task 2):** the full fan-in, recorded with actual numbers above — never as
  the word "green"
- **Max feedback latency:** ~8 seconds (module selection), ~74 seconds (full suite)

> **Execution trap 1 — the inverted RED gate.** Three plans use `! uv run pytest ...` (28-03:218,
> 28-04:251, 28-09:221). An inverted gate exits 0 on a collection/import error too, which is not a
> RED — it is a broken run masquerading as one. Run RED selections plain and read the output;
> passes reported alongside failures are the proof that collection succeeded.
>
> **Execution trap 2 — the shared git index.** `git commit` publishes the ENTIRE index, not just
> what the preceding `git add` named. Plan 28-01's complete seven-file set was swept into
> `05c06f4`, a commit belonging to 28-09 (`28-01-SUMMARY.md:170-182`, Deviation 2). With
> concurrent executors every commit must be `git commit -- <pathspec>` with
> `git diff --cached --name-only` inspected first.
>
> **Execution trap 3 — bare `git diff` is blind to untracked files.** Plans 28-06:375, 28-08:257
> and 28-09:304 gate on `git diff --exit-code -- .opencode .claude`, which cannot see a NEWLY
> emitted file. Verify emit round-trips with `git status --porcelain` as well. (Carried into
> Phase 29, which hit the real instance, and into the emit-drift CI job.)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Commit | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|--------|--------|
| 28-01-1 | 01 | 1 | DOCSUP-01 | Registry shape lands on the constitution plane as a hash-gated schema; contract drift stays clean | contract + unit | `uv run python -m tools.contract_drift.drift && uv run pytest tools/memory_regen/tests/test_contracts_index.py tools/docs_sync -q` | swept into `05c06f4` (see trap 2) | ✅ green |
| 28-01-2 | 01 | 1 | DOCSUP-01 | Derived reference page + contracts index regenerate for the new schema | derived round-trip | `uv run python -m tools.contract_drift.drift && uv run pytest tools/memory_regen tools/docs_sync -q` | swept into `05c06f4` | ✅ green |
| 28-02-1 | 02 | 1 | DOCSUP-02 | `tools.docs_guard` exists as a uv member with a **frozen public surface** (`__all__`) | import contract | `uv sync --all-packages && uv run python -c "import tools.docs_guard as d; print(sorted(d.__all__))"` | `b32ce44` | ✅ green |
| 28-02-2 | 02 | 1 | DOCSUP-02 | The digest is unambiguous under the `AMBIGUITY_CASES` table — interleaved path + per-file digest, so two different source sets cannot collide | RED→GREEN unit | `uv run pytest tools/docs_guard/tests/test_digest.py -q` | `2dee9bb` (RED) → `c50f150` (GREEN) | ✅ green |
| 28-09-1 | 09 | 1 | DOCSUP-02, DOCSUP-03 | Adversarial review-ledger refusal table is RED against unfixed `adoption_apply`, **plus** a must-stay-allowed control proving no over-refusal | RED gate | `! uv run pytest tools/adoption_apply/tests/test_constitution_refusal.py -k review_ledger -q` | `05c06f4` | ✅ green (RED confirmed) |
| 28-09-2 | 09 | 1 | DOCSUP-02, DOCSUP-03 | The ledger write is refused at the apply choke point **and** at the permission layer; the registry stays agent-writable; both runtime trees round-trip | unit + emit round-trip | `uv run pytest tools/adoption_apply tools/harness_lint/tests/test_opencode_json.py -q && uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude opencode.json` | `246fcac` | ✅ green |
| 28-03-1 | 03 | 2 | DOCSUP-01 | Five DOCSUP-01 rejection classes are RED against an unvalidated registry | RED gate | `! uv run pytest tools/docs_guard/tests/test_registry.py -k rejection -q` | (see 28-03-SUMMARY) | ✅ green (RED confirmed) |
| 28-03-2 | 03 | 2 | DOCSUP-01 | Path escape (incl. a **real symlink** escape), duplicate id, empty required selector, derived/reference target, accepted-ADR edit policy all rejected as SEMANTIC passes after the schema pass — with a 6-row `VALID_CASES` negative control proving no over-refusal | unit | `uv run pytest tools/docs_guard/tests/test_registry.py tools/docs_guard/tests/test_digest.py -q` | `c5f60f6` (spy-harness fix) | ✅ green |
| 28-04-1 | 04 | 2 | DOCSUP-02, DOCSUP-03 | Coherence, forbidden-key and **no-writer** tables RED against unfixed `ledger.py`; the paste-the-live-digest attack is the named case | RED gate | `! uv run pytest tools/docs_guard/tests/test_ledger.py -k paste_live_digest -q` | `f92d6a4` | ✅ green (RED confirmed) |
| 28-04-2 | 04 | 2 | DOCSUP-02, DOCSUP-03 | Ledger is read-only (no writer — grep-confirmed **and** a static write-call scan test); `_ROW_KEYS` is a 4-key allowlist rejecting any other key by name; `updated` is verified against the PREVIOUS COMMITTED ledger | unit | `uv run pytest tools/docs_guard/tests/test_ledger.py tools/docs_guard/tests/test_digest.py -q` | `8501a01` (+ `840e15d` ruff UP035) | ✅ green |
| 28-05-1 | 05 | 3 | DOCSUP-03, DOCSUP-05 | Five states, both ratchets, drift suppression; classification order is **numbered in the source** so it cannot be reordered by accident; `ok=False` only for BROKEN/STALE_REQUIRED | unit | `uv run pytest tools/docs_guard/tests/test_guard.py -q` | `6db057c` | ✅ green |
| 28-05-2 | 05 | 3 | DOCSUP-03 | Graph impact ids are real or empty — `(none)` printed, **never** a fabricated `TBD` (the `OWNER_TBD` never-fabricate house rule) | unit | `uv run pytest tools/docs_guard/tests/test_impact.py -q` | `3264b86` | ✅ green |
| 28-05-3 | 05 | 3 | DOCSUP-03, DOCSUP-05 | CLI maps exits 0/1/3; the report's BROKEN vs STALE_ADVISORY split is legible; drift is not double-reported | unit + live CLI | `uv run pytest tools/docs_guard -q && uv run python -m tools.docs_guard` | `f52dc32` | ✅ green |
| 28-06-1 | 06 | 4 | DOCSUP-04, DOCSUP-05 | The derived queue regenerates **deterministically** (byte-identical, snapshot-pinned) and is gitignored | unit + snapshot | `uv run pytest tools/memory_regen/tests/test_docs_staleness.py -q` | `5dde31b` | ✅ green |
| 28-06-2 | 06 | 4 | DOCSUP-04 | The SessionStart docs pointer is **conditional and droppable** — the never-drop tuple stays `("agreements","banner","drift","task")`, not widened; budget respected | unit | `uv run pytest tools/memory_regen -q` | `f19d2c0` | ✅ green |
| 28-06-3 | 06 | 4 | DOCSUP-04 | `/refresh-memory` chains the queue generator in **both** runtime trees; derived freshness gate holds | emit round-trip + unit | `uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude && uv run pytest tools/harness_lint/tests/test_derived_freshness.py -q` | `bf9e872` | ✅ green |
| 28-07-1 | 07 | 4 | DOCSUP-01, DOCSUP-02, DOCSUP-03 | Eight bindings seeded in the registry and the ledger only **proposed** — the ledger file must NOT exist, and no `.proposed`/`.draft` sidecar either | absence assertion + unit | `test ! -e docs/.docs-review-ledger.toml && uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | `69527e7` | ✅ green |
| 28-07-2 | 07 | 4 | DOCSUP-02 | **HUMAN-ONLY** — author and land the ledger | — | *(none — see Human-Gated)* | — | 🔒 blocked on human (RAT-1) |
| 28-07-3 | 07 | 4 | DOCSUP-03 | `docs-guard` is a **separate CI job** joined into the `gate` fan-in; tolerates exit ≤ 1 pre-ratification | CI-shape assertion | `uv run python -m tools.docs_guard; test $? -le 1` and the `gate.needs` membership check at 28-07-PLAN:351 | `abe1345` | ✅ green |
| 28-08-1 | 08 | 5 | DOCSUP-01..05 | ADR-0010 exists carrying `Status: proposed` **and is indexed** — proposed, not self-accepted | grep assertion | `grep -q 'Status:\*\* proposed' docs/adr/0010-human-docs-review-obligation-model.md && grep -q 0010 docs/adr/README.md` | `4b47d6e` | ✅ green |
| 28-08-2 | 08 | 5 | DOCSUP-01..05 | Phase-closing fan-in: full suite, drift, docs-guard, emit round-trip, whitespace | fan-in | `uv run pytest -q && uv run python -m tools.contract_drift.drift && uv run python -m tools.docs_guard && uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude && git diff --check` | `e9fb934`, `35a2c0e` | ✅ green *(with the documented caveat below)* |
| 28-08-3 | 08 | 5 | DOCSUP-01..05 | **HUMAN-ONLY** — ratify ADR-0010 and the seeded ledger dispositions | — | *(none — see Human-Gated)* | — | 🔒 blocked on human (RAT-2, RAT-3) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky · 🔒 human-gated*

> **Caveat on 28-08 Task 2.** Its command chains `uv run python -m tools.docs_guard` with `&&`,
> which cannot pass before RAT-1 lands — `docs_guard` exits 1 by design while the ledger is absent.
> The phase-closing gate was therefore satisfied by running the members individually and recording
> each result (`28-VERIFICATION.md:72-82`), not by the chained one-liner. This is a defect in the
> *plan's verify block*, not in the phase: a fan-in command whose members include a
> designed-non-zero gate cannot be `&&`-chained. Recorded rather than quietly rewritten.

**Sampling continuity:** every agent-executable task carries an `<automated>` command. The only two
rows without one are the two that are architecturally forbidden to an agent.

---

## Wave 0 Requirements

- [x] `tools/docs_guard` uv workspace member with a frozen `__all__` — created by 28-02 Task 1
      (`b32ce44`), which is itself the wave-1 prerequisite for waves 2-5
- [x] `contracts/harness/docs/doc-dependencies.schema.json` — created by 28-01, hash-gated
- [x] pytest + syrupy — pre-existing

---

## Adversarial-Input / Mutation Evidence

`28-REVIEW.md` found three Criticals; each was closed by **building the missing enforcement**, not
by weakening the claim. Every one of the four post-review controls was then **deleted and the suite
re-run** — all four failed loud, none survived deletion (`28-VERIFICATION.md:49-60`). Tree restored
to `git status --porcelain` empty after each mutation.

| Finding | Disposition | Mutation applied | Test that reds | Observed failure |
|---------|-------------|------------------|----------------|------------------|
| CR-01 | Fixed — suppression scoped to `STALE` **plus** an independent `not blocking_by_id` half | `SUPPRESSIBLE_REASONS` widened to include `BLOCKING_REASONS` AND the `not blocking_by_id` half deleted | `test_self_blessed_binding_is_not_rescued_by_a_drifted_source` | `AssertionError: drift demoted a ratification-authority finding — the self-green escape is open; assert ['note'] == ['fail']` |
| CR-02 | Fixed by **building a real enforcer** (`tools/hooks/ledger_guard.py`) rather than correcting ADR-0010 downward — deleting the claim would have left the write unobstructed and merely stopped saying so | the `Write\|Edit` `ledger_guard` hook group deleted from `merge.py:HARNESS_HOOK_GROUPS` | `test_review_ledger_hook_is_wired_into_the_emitted_pretooluse_set` | `AssertionError: ledger_guard is not wired into the emitted PreToolUse set — ADR-0010's layer 1 is inert` |
| CR-03 | Fixed by keying the history test on `(id, committed (sources,target) pair)` instead of adding a `binding_digest` ledger column — equivalent strength, and the ledger is hand-authored by a human so a third derived digest per row buys nothing | `repointed_ids` forced always-empty (id-only history test restored) | `test_repointing_a_ratified_binding_is_not_fresh` | `AssertionError: a repointed binding inherited its earlier ratification`, with `'findings': [], 'ok': True` |
| WR-01 | Fixed — `uncovered_max` read from the previous COMMITTED ledger, symmetric with `binding_min` | `uncovered_max` read from the working tree | `test_uncovered_max_comes_from_the_committed_ledger` | `AssertionError: the enforced ceiling must be the COMMITTED one; assert 99 == 0` |
| WR-02 | Fixed — control-char pattern in the schema; 6 control-char rejection rows | — | `test_registry.py` class F | — |
| WR-03 | Fixed — impact call sites reduced from two to one | — | — | residual IN-03 remains, see below |
| WR-04 | Fixed | — | — | — |
| IN-01 / IN-02 | Fixed | — | — | — |
| IN-03 | **Accepted residual, not fixed** | — | — | see below |

Additional structural controls worth naming, because each defeats a *specific* self-green attack:

- **`_ROW_KEYS` is an allowlist** (`ledger.py:73`) — still exactly the four DOCSUP-02 keys. No
  timestamp, no reviewer identity, no prose, no model identifier; any other key is rejected by name.
- **`ledger.py` has no writer** — grep-confirmed *and* pinned by its own static write-call scan test.
- **`ledger_guard.decide()` honours NO token** — denies with `GOLDEN_APPROVE_HUMAN=1` **and**
  `HARNESS_DEV_BYPASS=1` both set (`28-VERIFICATION.md:66-67`), while
  `decide("<root>/docs/doc-dependencies.toml")` returns `None` so the registry stays agent-writable.
- **`_check_updated`** rejects "source moved, target unmoved" as `disposition-incoherent` — this is
  the paste-the-live-digest control.
- **`first_seen-unratified` is a HISTORY test by design** — a self-blessed row and an honest first
  seed row are byte-identical; only a human committing the row separates them.

---

## Human-Gated Verifications

Not "manual because inconvenient" — **structurally forbidden to an agent**, which is the phase's
central deliverable and is itself verified working.

| Behavior | Requirement | Enforcement layers denying the agent | Human action |
|----------|-------------|--------------------------------------|--------------|
| Author `docs/.docs-review-ledger.toml` | DOCSUP-02 | (1) ADR-0010 clause 3b; (2) `tools/hooks/ledger_guard.py` PreToolUse deny honouring **no** token; (3) `adoption_apply` choke-point refusal via `REVIEW_LEDGER_GLOBS` | RAT-1 — byte-exact proposal in `28-07-SUMMARY.md`, re-derived post-edit in `29-04-SUMMARY.md` |
| Ratify ADR-0010 (`proposed` → `accepted`) | DOCSUP-01 | `registry._adr_status` treats a non-accepted ADR as a rejection — a real gate, not a formality. The ADR landed via `HARNESS_DEV_BYPASS` and was never claimed as ratified | RAT-2 |
| Ratify the eight seeded bindings' dispositions | DOCSUP-01/02 | `first_seen-unratified` history test | RAT-3 |
| Confirm operator output is actionable — BROKEN vs STALE_ADVISORY reads correctly | DOCSUP-03 | Message clarity and operator ergonomics are not programmatically checkable | read `uv run python -m tools.docs_guard` once |

**Why `28-VERIFICATION.md` is `human_needed` and not `passed`** (`:145-147`, verbatim):

> "None. All four ROADMAP success criteria are achieved in the codebase, verified independently of
> the SUMMARY narrative, and each of the four post-review controls survives its own deletion test.
> The phase is not `passed` solely because it is **blocked on human ratification by design** — the
> two blocking gates are precisely the ones an agent is architecturally forbidden to close, and the
> enforcement of that forbiddance is itself the phase's central deliverable and is verified working."

---

## Accepted Residuals

| ID | Residual | Recorded in | Why accepted |
|----|----------|-------------|--------------|
| IN-03 | The contract graph is recompiled once per binding in the report path (`cli.py:233` comprehension, `docs_staleness.py:100` loop) | `28-FIXES.md:265-286`; carried into `29-05-PLAN.md:119` tech_debt | Correctness unaffected (deterministic result). Closing it means changing `impact.py`'s public signature (rippling into `docs_staleness.rows`, `cli`, three test modules) or adding cached state to a module whose docstring makes a point of being pure — both deserve their own adversarial row for cache invalidation. |
| — | `tools/hooks/secret_scan.py:44-47` — shape-anchored `PATTERNS` hardcoded in the module instead of read from the contract | `29-CONTEXT.md` D-15, `29-05-PLAN.md:97`, `ROADMAP.md:595/645/676` | Carried since 26.2; fenced out of 26.2, 27.1, 27.2 **and** 28, and carried into the v2.3 close rather than allowed to vanish. |
| — | `harness/skills/gate-model/SKILL.md` stale `path_deny_globs` prose | `28-VERIFICATION.md:141-143` (⚠️ PARTIAL) | The verifier warned that `29-04` was the designated discharge vehicle but contained no occurrence of `ledger_guard`, risking a correction that names `*.env` but not `ledger_guard`. **Discharged in Phase 29** — 29-04's bounded prose fix moved this binding's `target_digest` from `4568f3a9` to `8df85e6e`, which is why RAT-1 must be authored against the POST-edit tree. |

---

## Gap Analysis

| Requirement | Classification | Evidence |
|-------------|----------------|----------|
| DOCSUP-01 registry + validation | **COVERED** | 6 test classes / ~26 rejection rows incl. a real symlink escape and a `DERIVED_GLOBS`-generated class, plus a 6-row `VALID_CASES` negative control; live CLI exit **3** observed |
| DOCSUP-02 committed ledger shape | **COVERED (machinery) / HUMAN-GATED (first row)** | `_ROW_KEYS` 4-key allowlist, no-writer proven statically, three-layer write denial mutation-proven. The first ledger row is RAT-1 and cannot be agent-produced |
| DOCSUP-03 five states + coherence | **COVERED** | first-match-wins with BROKEN ordered first; `ok=False` only for BROKEN/STALE_REQUIRED; both ratchets read from the COMMITTED ledger; CR-01/CR-03 mutation-proven |
| DOCSUP-04 derived queue + injector | **COVERED** | generator run twice → identical md5 `a099a684…`; never-drop tuple confirmed not widened; 12 injector + 22 stale-derived/docs_sync tests green |
| DOCSUP-05 no double-report of drift | **COVERED** | `_drifted_paths` carries the PATH only; `test_drift_findings_not_restated` |

**No MISSING rows. No PARTIAL rows among agent-executable requirements.** The two human-gated rows
are un-ratified, not unbuilt. The only reason this phase was Nyquist-non-compliant was the absence
of this document, not the absence of coverage.

---

## Validation Sign-Off

- [x] All agent-executable tasks have an `<automated>` verify command
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 74s full suite
- [x] Human-gated rows are named with their enforcement layers, not silently omitted
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** authored at closeout 2026-07-21, reconciled against `28-VERIFICATION.md`
(`human_needed`, 4/4 truths, commit `56cbac7`). Phase closure itself remains blocked on RAT-1/RAT-2.
