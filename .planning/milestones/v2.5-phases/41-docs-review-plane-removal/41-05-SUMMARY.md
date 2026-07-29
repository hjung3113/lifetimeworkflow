---
phase: 41-docs-review-plane-removal
plan: 05
subsystem: infra
tags: [docs-review-plane, deletion, ADR-0012, CER-05, residue-sweep, contract-drift, ci-fan-in, ruff-ratchet]

# Dependency graph
requires:
  - phase: 41-docs-review-plane-removal
    plan: "41-04"
    provides: contracts/harness/docs/doc-dependencies.schema.json + the CI docs-guard job and its
      gate.needs entry deleted, the contracts-index derived plane regenerated — the last
      constitution-plane and CI-plane surface of the docs-review plane, leaving only stale test
      fixtures/prose and an unrefreshed uv.lock for this closing plan
provides:
  - Every remaining test/fixture/docstring reference to the deleted docs-review plane removed
    (D-13): caps.py, test_coexist.py (incl. a second, previously undocumented pre-existing
    failure in its _SEED_SETTINGS fixture), test_settings_coexist.py, test_docs_update_wiring.py
    (deleted outright), test_docs_sync_determinism.py + its snapshot, gate-model/SKILL.md (+ its
    two emitted copies + the emit-determinism snapshot), test_tests_are_isolatable.py,
    test_workspace_member_completeness.py
  - merge.py's RETIRED_SIGNATURES emptied (empirically verified transitional) while the drop
    mechanism itself is kept as reusable infrastructure for Phase 44
  - A second sweep of comment/docstring-only residue beyond this plan's named interfaces list:
    workspace_check.py, ruff_baseline/{__main__.py,pyproject.toml}, discipline/__main__.py,
    task_control/tests/test_task_control.py, adoption_apply/apply.py, test_contract_guard.py
  - uv.lock confirmed already docs_guard-free (refreshed in Plan 01; no new diff needed here)
  - Full done-condition bundle run and green: pytest -q, collect-only, residue sweep (with every
    surviving hit disposed and justified), emit-drift, stale-derived, contract-drift, ruff
    ratchet, and the YAML-resolved gate.needs (11 entries, no docs-guard)
  - REQUIREMENTS.md CER-05 traceability table reconciled with its checklist ([x] since Plan 01)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [pathspec-scoped commits (D-11), residue-sweep-with-justified-exceptions rather than
    a naive zero-hits grep, empirical load-bearing verification before removing a deletion-phase
    mechanism (reused for RETIRED_SIGNATURES, mirrors Plan 01's docs_guard removal precedent)]

key-files:
  created: []
  modified:
    - tools/harness_lint/caps.py (drop docs-upkeep EXPECTED_SKILLS comment sentence)
    - tools/harness_emit/tests/test_coexist.py (26->25 count + docstring, drop stale
      _SEED_SETTINGS ledger_guard row)
    - tools/hooks/tests/test_settings_coexist.py (drop ledger_guard _NEW_GATES row, 9->8
      PreToolUse slot count)
    - tools/harness_lint/tests/test_docs_update_wiring.py (deleted — DOCSUP-06 subject gone)
    - tools/docs_sync/tests/test_docs_sync_determinism.py + its committed snapshot (drop
      doc-dependencies from EXPECTED_PAGES, regenerate render snapshot)
    - harness/skills/gate-model/SKILL.md + .claude/skills/gate-model/SKILL.md +
      .opencode/skill/gate-model/SKILL.md + the emit-determinism snapshot (trim 4 docs-plane
      claims, fix the "other deny domain(s)" count)
    - tools/harness_lint/tests/test_tests_are_isolatable.py,
      tools/harness_lint/tests/test_workspace_member_completeness.py (stale docstring examples)
    - tools/harness_emit/merge.py (RETIRED_SIGNATURES emptied)
    - tools/adoption_apply/apply.py, tools/discipline/__main__.py, tools/ruff_baseline/__main__.py,
      tools/ruff_baseline/pyproject.toml, tools/task_control/tests/test_task_control.py,
      tools/hooks/tests/test_contract_guard.py, tools/harness_lint/workspace_check.py
      (comment/docstring/fixture-example cleanup discovered by the residue sweep, out of the
      plan's named interfaces list)
    - .planning/REQUIREMENTS.md (CER-05 traceability row: "Not started" -> "Complete")

key-decisions:
  - "RETIRED_SIGNATURES (merge.py) empirically re-tested: re-emitting against the real committed
    .claude/settings.json with the ledger_guard entry removed produced a clean git status, and
    removing it ALSO fixed a second, previously undocumented test_coexist.py failure
    (test_seeded_settings_json_reproduced_byte_for_byte, whose _SEED_SETTINGS fixture still
    carried a ledger_guard group that the non-empty RETIRED_SIGNATURES was silently dropping,
    breaking the byte-for-byte assertion). Emptied the tuple, removed the now-stale ledger_guard
    fixture row from _SEED_SETTINGS, and kept the drop mechanism itself (the retired_signatures
    parameter and merge()'s drop branch) as general-purpose infrastructure for the next
    PreToolUse-hook deletion phase (Phase 44) rather than deleting it as dead code — it is
    reusable, not docs-review-specific, and D-06's 'no surface growth' governs adding new
    mechanism, not retaining an existing one at zero entries."
  - "Residue sweep returns 34 hits, not zero — every one is a justified, out-of-scope exception,
    not a real leftover of the enforced docs-review plane. See 'Residue Sweep Disposition' below."
  - "contracts/harness/security/deny-domains.{json,schema.json} and their two DERIVED renderings
    (docs/reference/deny-domains.md, tools/docs_sync's committed .ambr snapshot) are left
    untouched. 41-04-PLAN.md explicitly excluded the .json data file from this phase ('Phase 44
    territory... Do NOT touch it in this plan') because nothing reads or gates on it; the same
    rationale — same subsystem, same non-enforcing declaration, same next-owning phase — extends
    to the schema's own description prose and its two derived copies, none of which are gated
    surfaces either."
  - "REQUIREMENTS.md: reconciled CER-05's traceability-table row ('Not started') with its
    checklist entry (marked [x] since Plan 01) to 'Complete', now that the phase is closing. Did
    not touch CER-01/02/03/04's rows, which show the same [x]-vs-table-'Not started' mismatch
    from prior phases — out of this plan's scope."

requirements-completed: [CER-05]

# Metrics
duration: ~55min
completed: 2026-07-27
---

# Phase 41 Plan 05: Prose/Test Sweep, uv.lock Refresh, Final Verification Summary

**Swept the last 20 files of stale docs-review-plane references out of test fixtures, docstrings, and comments (including two previously-undocumented pre-existing test failures), confirmed `uv.lock` was already docs_guard-free, and ran the full done-condition bundle green (pytest, residue sweep, emit-drift, stale-derived, contract-drift, ruff ratchet, YAML-resolved `gate.needs`) — closing CER-05 and the phase with a measured net -8199 LOC across all five plans.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-07-27 (session start)
- **Completed:** 2026-07-27
- **Tasks:** 3 completed (Task 2 required no new commit — precondition already satisfied)
- **Files modified:** 20 across 3 commits (plus 1 REQUIREMENTS.md fix folded into the plan-metadata commit)

## Accomplishments

- Removed every literal test/prose reference to the deleted docs-review plane named in this
  plan's interfaces section: `caps.py`'s stale comment, `test_coexist.py`'s command count
  (26→25) and docstring narrative, `test_settings_coexist.py`'s `ledger_guard` gate row and slot
  count (9→8), `test_docs_update_wiring.py` (deleted outright — its DOCSUP-06 subject died in
  Plan 03), `test_docs_sync_determinism.py`'s `EXPECTED_PAGES` entry (+ regenerated snapshot),
  `gate-model/SKILL.md`'s four docs-plane claims (+ its two emitted copies + the
  emit-determinism snapshot), and two stale docstring examples (`test_tests_are_isolatable.py`,
  `test_workspace_member_completeness.py`).
- Discovered and fixed a **second, previously undocumented pre-existing failure** in
  `test_coexist.py`: its `_SEED_SETTINGS` fixture still wired a `ledger_guard` PreToolUse group,
  which the (then non-empty) `RETIRED_SIGNATURES` silently dropped during merge, breaking
  `test_seeded_settings_json_reproduced_byte_for_byte`'s byte-for-byte assertion. Removed the
  stale fixture row.
- Empirically resolved the phase-critical `RETIRED_SIGNATURES` decision (merge.py): re-emitted
  against the real committed `.claude/settings.json` with the entry removed — `git status
  --porcelain` came back clean, confirming the entry was transitional. Emptied the tuple, kept
  the general-purpose drop mechanism for Phase 44's future use.
- Found and fixed 7 additional residue hits beyond the plan's named interfaces list —
  `workspace_check.py`, both `ruff_baseline` comment mirrors, `discipline/__main__.py`,
  `task_control/tests/test_task_control.py`'s docstring, `adoption_apply/apply.py`'s stale
  backslash-example comment, and `test_contract_guard.py`'s stale negative-control fixture path —
  all comment/docstring/example-only, zero behavior change.
- Confirmed `uv.lock` was already docs_guard-free (refreshed in Plan 01's `e94493a`); `uv lock`
  and `uv sync --all-packages` both ran clean with zero diff, so Task 2 required no new commit.
- Ran the full phase-closing verification bundle and recorded literal evidence for each:
  `uv run pytest -q` → **1340 passed, 0 failed**; `--collect-only -q` → **1340 collected, 0
  errors**; the residue sweep → **34 hits, every one disposed and justified** (see below);
  emit-drift → clean; stale-derived → clean; `contract-drift` → `OK — live manifest matches the
  committed baseline`; ruff ratchet → `245 findings (baseline 245) — PASS, every rule class at
  its baseline` (the baseline did **not** move — a large deletion did not change ruff's
  per-rule-class finding counts, since it removed no rule-violating code); YAML-resolved
  `gate.needs` → 11 entries, `docs-guard` absent, confirmed via the same `ruamel.yaml` mechanism
  Plan 04 used.
- Reconciled `REQUIREMENTS.md`'s CER-05 traceability-table row ("Not started") with its checklist
  entry (already `[x]` since Plan 01) to "Complete".

## Task Commits

1. **Task 1: Prose and test sweep (D-13)** - `65476ef` (test) — the 8 named files + 4 direct
   regen consequences (2 snapshots + 2 emitted skill copies)
2. **Deviation: empty RETIRED_SIGNATURES (D-12/phase-critical-rule 4)** - `1bf9997` (refactor)
3. **Deviation: additional residue-sweep discoveries** - `27216c7` (docs)
4. **Task 2: Refresh uv.lock** — no commit; precondition already satisfied by Plan 01's `e94493a`,
   re-verified with zero diff (`uv lock` + `uv sync --all-packages` both clean)
5. **Task 3: Final verification wave** — verification-only, no commit; every check passed on the
   first run, no repair needed

**Plan metadata:** this summary + STATE/ROADMAP/REQUIREMENTS updates (final commit)

## Files Created/Modified

- `tools/harness_lint/caps.py` — drop stale docs-upkeep comment sentence
- `tools/harness_emit/tests/test_coexist.py` — 26→25 count, docstring, drop stale
  `_SEED_SETTINGS` `ledger_guard` row
- `tools/hooks/tests/test_settings_coexist.py` — drop `ledger_guard` `_NEW_GATES` row, 9→8
  PreToolUse slot count
- `tools/harness_lint/tests/test_docs_update_wiring.py` — deleted (129 lines)
- `tools/docs_sync/tests/test_docs_sync_determinism.py` + `__snapshots__/test_docs_sync_determinism.ambr`
  — drop `doc-dependencies`, regenerate
- `harness/skills/gate-model/SKILL.md` + `.claude/skills/gate-model/SKILL.md` +
  `.opencode/skill/gate-model/SKILL.md` + `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
  — trim 4 docs-plane claims + fix "other deny domain(s)" count, re-emit, regenerate
- `tools/harness_lint/tests/test_tests_are_isolatable.py`,
  `tools/harness_lint/tests/test_workspace_member_completeness.py` — stale example fixes
- `tools/harness_emit/merge.py` — `RETIRED_SIGNATURES` emptied
- `tools/adoption_apply/apply.py`, `tools/discipline/__main__.py`,
  `tools/ruff_baseline/__main__.py`, `tools/ruff_baseline/pyproject.toml`,
  `tools/task_control/tests/test_task_control.py`, `tools/hooks/tests/test_contract_guard.py`,
  `tools/harness_lint/workspace_check.py` — comment/docstring/fixture-example cleanup
- `.planning/REQUIREMENTS.md` — CER-05 traceability row reconciled to "Complete"

## Decisions Made

See `key-decisions` in frontmatter — three decisions, all documented there with rationale.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `test_coexist.py`'s `_SEED_SETTINGS` fixture carried a stale `ledger_guard` group**
- **Found during:** Task 1, verifying `test_coexist.py` after the `==26`→`==25` edit
- **Issue:** The fixture simulating an "already-wired" settings.json still included a
  `ledger_guard` PreToolUse group; with the (then non-empty) `RETIRED_SIGNATURES` containing
  `tools.hooks.ledger_guard`, `merge_settings` dropped that group during the simulated re-emit,
  breaking `test_seeded_settings_json_reproduced_byte_for_byte`'s byte-for-byte reproduction
  assertion. Confirmed by temporarily restoring the original `RETIRED_SIGNATURES` value and
  re-running the test in isolation (reverted after confirming).
- **Fix:** Removed the stale `ledger_guard` row from `_SEED_SETTINGS`.
- **Files modified:** `tools/harness_emit/tests/test_coexist.py`
- **Verification:** `uv run pytest tools/harness_emit/tests/test_coexist.py -v` — 5/5 passed
- **Committed in:** `65476ef`

**2. [Rule 3 - Blocking] `tools/hooks/tests/test_settings_coexist.py`'s slot-count docstring/assertion went stale**
- **Found during:** post-Task-1 full-suite run
- **Issue:** Removing the `ledger_guard` row from `_NEW_GATES` (per the plan's own instruction)
  left the hardcoded `9 PreToolUse` count in `test_expected_slot_counts` one too high.
- **Fix:** Updated the docstring and assertion to `8 PreToolUse (4 GSD + 4 harness)`.
- **Files modified:** `tools/hooks/tests/test_settings_coexist.py`
- **Committed in:** `65476ef`

**3. [Rule 4 → resolved empirically per phase-critical-rule 4] `merge.py`'s `RETIRED_SIGNATURES`**
- **Found during:** the plan's mandatory "DECISION REQUIRED" step
- **Issue:** Whether the `ledger_guard` entry Plan 03 added to `RETIRED_SIGNATURES` was still
  load-bearing now that the real committed `.claude/settings.json` has carried no `ledger_guard`
  group since Plan 03's re-emit.
- **Fix:** Emptied `RETIRED_SIGNATURES` to `()` after confirming (re-emit + `git status
  --porcelain` clean) it was transitional; kept the mechanism (parameter + drop branch) as
  reusable infrastructure for Phase 44.
- **Files modified:** `tools/harness_emit/merge.py`
- **Committed in:** `1bf9997`

**4. [Rule 1 - Bug, scope-adjacent] 7 additional stale prose/fixture hits found during the residue sweep**
- **Found during:** the residue sweep itself (Task 3), run early to gate Task 1's completeness
- **Issue:** `workspace_check.py`, `ruff_baseline/__main__.py`, `ruff_baseline/pyproject.toml`,
  `discipline/__main__.py`, and `task_control/tests/test_task_control.py` all carried
  comment/docstring mirrors of `docs_guard`/`ledger_guard` not named in this plan's interfaces
  section; `adoption_apply/apply.py` illustrated a backslash-escaping edge case using the deleted
  ledger file as its example; `test_contract_guard.py`'s negative-control fixture used the
  deleted `docs/reference/doc-dependencies.md` as an example non-constitution path.
- **Fix:** Trimmed each comment/docstring reference or swapped the stale example path for a real,
  still-existing one (`docs/glossary.md`, `docs/reference/deny-domains.md`). All comment-only or
  fixture-example changes — zero behavior change, confirmed by re-running the affected packages'
  test suites (303 passed, 0 failed).
- **Files modified:** see list above.
- **Committed in:** `27216c7`

---

**Total deviations:** 4 auto-fixed (2 Rule-1 bugs, 1 Rule-3 blocking fix, 1 phase-mandated
empirical decision). **Impact on plan:** All necessary for the residue sweep (SC-3) and the full
suite (D-15) to go green; no scope creep beyond fixing what the plan's own edits (and the sweep
itself) surfaced as broken or stale.

## Issues Encountered

None beyond the deviations above.

## Residue Sweep Disposition

The sweep (`grep -rnE "docs_guard|docs-guard|docs-review-ledger|ledger_guard|docs-upkeep|docs-update|doc-dependencies" tools/ harness/ contracts/ docs/ .github/ .claude/ .opencode/ AGENTS.md .memory/README.md uv.lock`) returns **34 hits, not zero**. Every hit is a justified, out-of-scope exception — none is a leftover of the enforced docs-review plane:

| Category | Files | Disposition |
|---|---|---|
| Plan-mandated historical narrative | `tools/harness_emit/tests/test_coexist.py:49,51` | This plan's own interfaces section explicitly instructs appending a docstring line naming `/docs-update`, documenting the phase-by-phase count history. Required by the plan itself. |
| Append-only ADR history (D-05) | `docs/adr/0010-*.md` (23 hits), `docs/adr/0011-*.md` (3 hits), `docs/adr/0012-*.md` (5 hits) | ADRs are append-only, supersede-don't-edit. ADR-0010 (the plane's own record, superseded by 0012) and ADR-0012 (the ratifying record, which necessarily quotes what it deletes) both keep their historical text by design. |
| Phase 44 territory (deny-domains subsystem) | `contracts/harness/security/deny-domains.json:81,83,102,112,128`, `contracts/harness/security/deny-domains.schema.json:5`, `docs/reference/deny-domains.md:7`, `tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr:85` | 41-04-PLAN.md explicitly excluded the `.json` data file from this phase ("Phase 44 territory... nothing reads or gates on it. Do NOT touch it in this plan"). The same rationale — same subsystem, same non-enforcing declaration, same next-owning phase — extends to the schema's own description prose and its two DERIVED renderings (neither is hand-edited; both regenerate once Phase 44 fixes the source). |
| GSD-owned namespace collision | `.claude/settings.json:167`, `.claude/gsd-file-manifest.json`, `.claude/agents/gsd-doc-writer.md`, `.claude/agents/gsd-doc-verifier.md`, `.claude/commands/gsd/docs-update.md`, `.claude/commands/gsd/ns-context.md`, `.claude/get-shit-done/**` (7 files) | GSD (`get-shit-done`) is a separate, vendored meta-tool that builds and maintains this repo's own harness — it has its own, unrelated `/gsd:docs-update` workflow command. The regex match is a bare-word collision ("docs-update" as a generic phrase for "update documentation"), not the harness's deleted `/docs-update` slash command. GSD's own tree is out of scope for the harness's CER-05 deletion. |

No hit corresponds to code that still imports, gates on, or enforces the deleted docs-review
plane — confirmed by the green `uv run pytest -q` (1340 passed), the clean `emit-drift`, and the
clean `contract-drift`.

## Total Phase LOC (D-17, measured)

`git diff --stat 711030e^..HEAD` (the commit before Plan 01's first code change, through this
plan's last commit before the metadata commit): **80 files changed, 733 insertions(+), 8932
deletions(-)** — net **-8199 lines** across all five plans. This exceeds the ≳6.3k D-17 estimate
(6110 guard + 233 staleness + hook + ledger + registry + contracts), consistent with the
additional test-fixture, snapshot, and CI-plane deletions folded in along the way.

## Ruff Baseline Status

**Did not move.** `uv run python -m tools.ruff_baseline` reports `245 findings (baseline 245) —
PASS: every rule class is at its baseline`. The phase's large deletion removed no
rule-violating code (the deleted `tools/docs_guard` and its consumers were themselves
ruff-clean), so no rebaseline was run and none was needed. The next phase inherits `245` as the
accurate, unchanged baseline.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

CER-05 is closed: the docs-review plane (`tools/docs_guard`, the ledger, the registry, the hook +
its emitter wiring, the command, the skill, the contract, the CI job, and the staleness queue) is
fully deleted, with zero replacement gate/job/tool added (D-06). The one remaining item from D-15
— the CI fan-in `gate` job going green on the pushed branch — is manual-only per
41-VALIDATION.md and happens after push; every locally-verifiable done-condition is green. No
blockers for Phase 42 (adoption ↔ task-control decoupling, CER-06/PROD-01).

## Self-Check: PASSED

- `test ! -f tools/harness_lint/tests/test_docs_update_wiring.py` — exit 0 (confirmed)
- `grep -c docs-upkeep tools/harness_lint/caps.py` — 0 (confirmed)
- `grep -n "== 2" tools/harness_emit/tests/test_coexist.py` — both `== 25` (confirmed)
- `grep -c ledger_guard tools/hooks/tests/test_settings_coexist.py` — 0 (confirmed)
- `grep -c doc-dependencies tools/docs_sync/tests/test_docs_sync_determinism.py` — 0 (confirmed)
- `grep -c ledger_guard harness/skills/gate-model/SKILL.md` — 0 (confirmed)
- `grep -c docs_guard tools/harness_lint/tests/test_tests_are_isolatable.py` — 0 (confirmed)
- `grep -c ledger_guard tools/harness_lint/tests/test_workspace_member_completeness.py` — 0 (confirmed)
- `grep -c logparser-docs-guard uv.lock` — 0 (confirmed)
- `uv run pytest -q` — 1340 passed, 0 failed (confirmed)
- `uv run pytest --collect-only -q` — 1340 collected, 0 errors (confirmed)
- `uv run python -m tools.contract_drift.drift` — "OK — live manifest matches the committed baseline." (confirmed)
- `uv run python -m tools.ruff_baseline` — "PASS: every rule class is at its baseline." (confirmed)
- YAML-resolved `gate.needs` — 11 entries, `docs-guard` absent (confirmed)
- Commit `65476ef` — FOUND in `git log --oneline`
- Commit `1bf9997` — FOUND in `git log --oneline`
- Commit `27216c7` — FOUND in `git log --oneline`
- `git diff --stat 711030e^..HEAD` — 80 files changed, 733 insertions(+), 8932 deletions(-) (D-17 measured, not estimated)

---
*Phase: 41-docs-review-plane-removal*
*Completed: 2026-07-27*
