# Phase 43: Lifecycle Plane Removal - Context

**Gathered:** 2026-07-28
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; see `43-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

Delete the task-control lifecycle plane **whole** (CER-07): 8 `tools/` packages (**7021 LOC**,
verified), 6 of the 7 task-control contracts, 4 commands, 1 hook, 5 discipline skills, 3
`harness/*.toml` declarations, `.workflow/tasks/`, and the CI `lifecycle-eval` job with its fan-in
entry. Strip `memory_regen`'s active-task block while keeping the activeContext pointer.

**No residue package.** A Python state manager must be unreachable in the product by construction —
not a shim, not a stub, not a deprecation path.

**Not in this phase:** `gate-registry.json` (Phase 44 / CER-08 names it explicitly with its
`DATA_CONTRACT_PATHS` entry), `secret_scan`, `deny-domains.*`, `tools/memory_ui`, the golden stack.

</domain>

<decisions>
## Implementation Decisions

### The finding that reshapes this phase: surviving commands invoke the dying plane

- **D-01:** **CER-07's list is incomplete.** Five SURVIVING artifacts execute modules this phase
  deletes — verified by reading their `!`-prefixed shell lines, not inferred:
  - `harness/commands/checkpoint.md:22,46` runs `tools.handoff generate|validate|activate`
  - `harness/commands/orient.md:21,23,46` runs `tools.handoff resume` and routes to `/phase-gate`
  - `harness/commands/review.md:50-51` runs `tools.evidence.capture add-finding`
  - `harness/commands/verify-work.md:23` runs `tools.evidence.capture capture`
  - `harness/agents/orchestrator.md:52-57` runs `tools.capability list` as its routing step
  Each must be repaired **in this phase**, at `harness/**` source, or the surviving surface ships
  commands that crash. This is not scope creep — it is the deletion's own blast radius.
- **D-02:** **Repair before delete.** Order the work: (1) repair the five surviving artifacts +
  `memory_regen` + the hook wiring so nothing invokes the plane, (2) then delete the plane itself.
  The reverse order leaves intermediate commits whose commands are broken.
- **D-03:** Repair means **removing the lifecycle step, not replacing it**: `/verify-work` keeps its
  gate list minus evidence capture; `/checkpoint` keeps its `.memory/state` writes minus handoff
  generation; `/orient` drops the handoff-resume line and the `/phase-gate` routing; `orchestrator`
  routes by declared topology/stage instead of by `tools.capability list`. No successor mechanism.

### What goes, precisely

- **D-04:** The 8 packages, deleted together in one commit — they are mutually referential
  (`task_control` ↔ `task_packet` ↔ `risk_router` ↔ `evidence` ↔ `handoff` ↔ `discipline` ↔
  `capability` ↔ `lifecycle_eval`), so a leaf-first order does not exist. Measured LOC:
  task_control 1677, handoff 1238, discipline 990, risk_router 877, evidence 783, task_packet 605,
  lifecycle_eval 472, capability 379 = **7021**.
- **D-05:** **6 contracts, not 7.** `contracts/harness/task-control/` holds 7 files; CER-07 says "the
  7 task-control contracts" but CER-08 separately claims `gate-registry.json` with its
  `DATA_CONTRACT_PATHS` entry (`tools/contract_hash/hash.py:32`). Delete `attestation`, `evidence`,
  `handoff`, `state`, `task`, `transitions`; **leave `gate-registry.json` for Phase 44.** Rebaseline
  `contracts/.hashes/manifest.json` with the deletions.
- **D-06:** The hook: `tools/hooks/resume_gate.py` + `harness/plugins/resume-gate.ts` + the emitted
  `.claude/settings.json` hook group. That group is a hand-maintained literal in
  `tools/harness_emit/merge.py`; Phase 41 built `RETIRED_SIGNATURES` for exactly this and left it at
  `()` (`merge.py:112`). **Use it, then empty it again once the re-emit has landed** — that is the
  pattern Phase 41 established and validated.
- **D-07:** 5 discipline skills + their `emit-manifest.json` rows + their `tools/harness_lint/caps.py`
  `EXPECTED_SKILLS` entries (`caps.py:135`). **`EXPECTED_SKILLS` hard-fails the emitter before it
  writes a byte** — Phase 41 hit this and lost a run to it. Update it in the same commit as the
  skill deletion.
- **D-08:** 3 declarations (`harness/{capabilities,disciplines,risk-policy}.toml`) and the tests that
  die with them (`test_capability_wiring.py`, `test_discipline_wiring.py`,
  `test_tests_are_isolatable.py`'s lifecycle assertions).
- **D-09:** `.workflow/tasks/` — **6 git-tracked files**, including a real historical task packet
  (`T-20260718090000-contract-ratification`). Delete the tracked tree; it is lifecycle state, not
  history worth preserving outside git (git keeps it).
- **D-10:** CI job `lifecycle-eval` (`ci.yml:221-231`) + its fan-in `needs` entry (`ci.yml:345`).
  Verify the remaining `needs` **by resolving the YAML**, never by grep (Phase 41's D-14, and the
  `ruamel.yaml` one-liner it proved works — no new dependency).

### memory_regen

- **D-11:** Strip the active-task block, **keep** the activeContext pointer. They are adjacent in the
  same function — read both before cutting. Prove the pointer survives with a test assertion, not by
  reading the output (ROADMAP SC-6).

### Ordering and commit discipline (carried, measured)

- **D-12:** delete/edit → `git add` → `git commit -- <pathspec>` → verify → amend-if-red.
  `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so tracked deletions red until
  staged AND committed. A red before the commit is expected.
- **D-13:** `git commit -- <pathspec>` every time; `git diff --cached --name-only` inspected first.
  Never `git add -A` / `git add .` / `git commit -a`. **Never `git checkout <ref> -- .`**.
- **D-14:** Source-first: edit `harness/**`, then `python -m tools.harness_emit`. Never hand-edit
  `.opencode/**` or `.claude/**`.
- **D-15:** **Run things, don't read them.** Every wave of Phases 41 and 42 found consumers its plan
  had not listed, and every one surfaced from a test run, an emitter run, or a live invocation.
  Expect this phase — the largest deletion — to have more.

### Verification / done-condition

- **D-16:** Done = the 8 package dirs gone and no module imports them (`--collect-only` 0 errors);
  `contracts/harness/task-control/` holds only `gate-registry.json` with a rebaselined manifest and
  `contract-drift` exit 0; no `lifecycle-eval` job and no dangling fan-in entry (YAML-resolved);
  `memory_regen` still emits the activeContext pointer; `uv run pytest -q` green; `emit-drift`,
  `stale-derived`, ruff ratchet clean; `uv.lock` refreshed.
- **D-17:** **No mutation-proof table is owed** — this phase removes gates and adds no control. The
  one exception is D-11's pointer-survival assertion, which is coverage of a retained behavior.
- **D-18:** Report whole-phase LOC from `git diff --stat` (measured, not estimated); expect ≳7021.

### Claude's Discretion

- Plan/task decomposition and wave count (a repair wave then a deletion wave is the natural shape).
- Whether the contract deletion rides with the package deletion or its own commit.
- Exact replacement wording in the five repaired commands, provided no successor mechanism appears.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and authority
- `.planning/ROADMAP.md` §"#### Phase 43: Lifecycle Plane Removal" — scope, non-goals, accepted
  consequence, **8 success criteria**, and the recorded CER-07/CER-08 `gate-registry.json` collision.
- `.planning/REQUIREMENTS.md` — **CER-07**.
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — accepted; names this surface; CI + the merge
  replace the in-session lifecycle gates.

### Prior-phase carry-forward
- `.planning/phases/41-docs-review-plane-removal/41-0{3,4}-SUMMARY.md` — the `RETIRED_SIGNATURES`
  mechanism and why removing a signature alone does NOT drop an emitted hook group; the
  `EXPECTED_SKILLS` emitter hard-fail; the contract-deletion + manifest-rebaseline procedure.
- `.planning/phases/42-.../42-04-SUMMARY.md` — the RED-first discipline that caught a vacuous test and
  a no-op glob in the same plan.
- `.planning/phases/42-.../42-VERIFICATION.md` — the falsify-the-fix verification style to expect.

### The surface this phase touches
- The 8 packages under `tools/`, and `tools/hooks/resume_gate.py`, `harness/plugins/resume-gate.ts`.
- `tools/harness_emit/merge.py:112` (`RETIRED_SIGNATURES`), `emit-manifest.json` rows for the 4
  commands, 5 skills and the plugin.
- `tools/harness_lint/caps.py:135` (`EXPECTED_SKILLS`) and the three wiring tests.
- `harness/{capabilities,disciplines,risk-policy}.toml`; `.workflow/tasks/` (6 tracked files).
- `.github/workflows/ci.yml:221-231`, `:345`.
- `tools/memory_regen/inject.py` — active-task block vs activeContext pointer.
- **The five surviving artifacts of D-01** — `harness/commands/{checkpoint,orient,review,verify-work}.md`
  and `harness/agents/orchestrator.md`.

### Conventions
- `AGENTS.md` (root) — nearest-wins rules; its command/skill index needs the deletions swept.
- `.memory/README.md` — two-plane declaration.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- `RETIRED_SIGNATURES` in `merge.py` — built in Phase 41 for precisely this case, currently `()`.
- The Phase-41/42 contract-deletion + rebaseline procedure (`git rm`, hooks match `Write|Edit` only,
  so no `HARNESS_DEV_BYPASS`; never reach for `GOLDEN_APPROVE_HUMAN`).
- The `ruamel.yaml` fan-in `needs` assertion (already a resolved transitive dep — do not add PyYAML).

### Established patterns
- Emitted trees are derived; `emit-drift` reds on any hand-edit.
- `caps.py` count declarations hard-fail the emitter *before* it writes.
- Deleting a contract moves the hash manifest → rebaseline in the same commit.

### Integration points
1. The 8 packages → each other (mutually referential; delete as one unit).
2. The plane → `tools/hooks/resume_gate.py` → emitted `.claude/settings.json` group (via `merge.py`).
3. The plane → the five surviving commands/agent of D-01 (the blast radius CER-07 missed).
4. `tools/memory_regen/inject.py` → the active-task block (goes) and the activeContext pointer (stays).
5. `harness/*.toml` declarations → `caps.py` + the wiring tests.

</code_context>

<specifics>
## Specific Ideas

- `tools/adoption_scan/scan.py:5` mentions `tools/evidence/capture.py` only in a docstring contrast
  ("which executes subprocesses and mutates task state, both forbidden here") — it is NOT a code
  coupling, but it will name a deleted module afterwards, so sweep the sentence.
- Five hyphenated `contracts/harness/task-control/gate-registry.json` provenance docstrings survive in
  `tools/adoption_scan/**` from Phase 42. They are correct today and become stale when Phase 44
  deletes that file — **carry them to Phase 44**, do not fix here.

</specifics>

<deferred>
## Deferred Ideas

- `gate-registry.json` + its `DATA_CONTRACT_PATHS` entry, `secret_scan`, `deny-domains.*` (incl. the
  stale `ledger_guard` declaration carried from Phase 41), `tools/memory_ui`, `strangler_guard`,
  `/pipeline`, `gate-model`, and relocating the golden stack → **Phase 44** (CER-08, CER-09).
- The Phase-42 provenance docstrings above → Phase 44, with `gate-registry.json`.
- Projection repair → Phase 45.

</deferred>

---

*Phase: 43-lifecycle-plane-removal*
*Context gathered: 2026-07-28*
