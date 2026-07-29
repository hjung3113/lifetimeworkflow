# Phase 44: Non-Goal Surface Removal - Context

**Gathered:** 2026-07-29
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; see `44-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

Two requirements, one theme — the harness stops carrying surface that v2.5 declared a non-goal:

1. **CER-08 — delete the non-goal surface.** `secret_scan` (no replacement job),
   `deny-domains.{json,schema.json}`, `gate-registry.json` and their `DATA_CONTRACT_PATHS` entries,
   `tools/memory_ui` (1756 LOC), `tools/strangler_guard` (240 LOC) + `/strangler-step`, `/pipeline` +
   skill `pipeline-map` + `[pipeline].edges`, skill `gate-model`, and `/component`'s
   topology-registration half.
2. **CER-09 — relocate the golden stack** to `examples/log-parser/`. Not delete: **move**. The core
   stops promising golden parity; each instance owns that evidence.

**Not in this phase:** projection repair — `caps.py` frozensets, `emit-manifest.json`,
`HARNESS_SIGNATURES`, `docs/reference/**`, `AGENTS.md`, `.memory/derived/**` reconciliation is
**Phase 45** (CER-10/CER-11). This phase deletes and relocates; 45 makes the projection consistent.
Do not pre-empt it beyond what is needed to keep each commit green.

</domain>

<decisions>
## Implementation Decisions

### The finding that reshapes this phase: CER-09 is a relocation across a workspace boundary

- **D-01:** **`examples/**` is NOT a uv workspace member.** Root `pyproject.toml:34` declares
  `members = ["libs/python", "tools/*"]` with `exclude = ["tools/bootstrap"]` — root-scoped globs
  only. Moving `tools/golden_runner` under `examples/log-parser/` therefore removes it from the
  workspace: it stops being installed, and `uv run python -m tools.golden_runner...` stops resolving.
  This is the single hardest thing in the phase and **no other CER-08 deletion has this property**.
- **D-02:** **Four live importers already exist in the example** and they import the *core* path
  today: `examples/log-parser/tests/{test_value_regression,test_repr_only,test_compare_recorded}.py`
  and `conftest.py:28` all do `from tools.golden_runner.runner import ...`. `conftest.py:3` records
  that these tests were already moved out of `tools/golden_runner/tests/` by an earlier phase — so
  CER-09 finishes a migration that is half-done, it does not start one.
- **D-03:** **Relocate to `examples/log-parser/golden_runner/`, NOT to
  `examples/log-parser/tools/golden_runner/`.** A second directory named `tools/` under the example
  creates two roots for the same `tools.*` import namespace — an ambiguity that resolves by
  `sys.path` order and would fail differently in CI than locally. A distinct top-level package name
  removes the class of bug entirely.
- **D-04:** **Add the relocated package to `[tool.uv.workspace] members`** as an explicit path entry.
  This is a **DATA row in an existing config key**, not a new mechanism — the same reasoning that
  settled Phase 42's D-07 (`tools/**` glob: "a data row, not a mechanism"). It is not surface growth:
  no new gate, tool, contract, or dependency. ⚠ `tools/harness_lint/workspace_check.py` and
  `test_workspace_member_completeness.py` read that glob — the relocated dir MUST carry a
  `pyproject.toml` in the same commit that adds the member, or every `uv` invocation in the repo
  fails and the PreToolUse guards take the session down (that file's own docstring documents this
  exact self-sealing failure).
- **D-05:** **Root `golden/` (4 files, 16K) folds into `examples/log-parser/golden/`**, which already
  exists. The CI `golden` job's step 1 is labelled "root identity golden (converter-agnostic,
  .NET-free)"; once the core makes no parity promise there is no core-side golden to run, so the two
  steps collapse into the example's. Preserve history with `git mv` where the path allows it.

### CER-08 — how deep each deletion goes

- **D-06:** **`secret_scan` is a live PreToolUse hook, not a package.** CER-08's prose implies
  `tools/secret_scan/`; there is none. It is `tools/hooks/secret_scan.py` +
  `tools/hooks/tests/test_secret_scan.py` + `harness/plugins/secret-scan.ts` + a `HARNESS_SIGNATURES`
  entry (`merge.py:91`) + an emitted hook-group literal (`merge.py:180`) + prose in
  `harness/commands/review.md:24`. All of it goes, **with no replacement** — not a lighter hook, not
  a CI job, not a pre-commit entry.
- **D-07:** **`merge.py`'s `RETIRED_SIGNATURES` must gain `"tools.hooks.secret_scan"` and must NOT be
  cleared afterwards.** This is the Phase-43 defect that four verification passes and a live-emitter
  reproduction were needed to find. Removing a signature from `HARNESS_SIGNATURES` alone leaves the
  emitted group looking human-owned, so any checkout still holding the pre-44 `.claude/settings.json`
  keeps invoking a deleted module → guard exits non-zero → PreToolUse denies every Write/Edit/Bash,
  with the repair locked behind the outage. `merge.py:111` now carries
  `("tools.hooks.resume_gate",)` as a permanent tombstone — **append, never clear.** Phase 43's
  reversal of its own D-06 is the precedent.
- **D-08:** **`tools/adoption_scan` keeps its own secret patterns.** Phase 42 inlined
  `SECRET_PATH_GLOBS` (`scan.py:54`) and `SECRET_CONTENT_PATTERNS` (`:60`) locally, and `scan.py:15,53`
  explicitly document that they are NOT the hook's. Deleting the hook must not touch adoption's
  redaction, and the proof is that adoption's redaction tests pass **unchanged**.
- **D-09:** **`deny-domains.*` deletion self-clears two stale declarations** — `deny-domains.json:81,102`
  names `tools.hooks.ledger_guard` (deleted in Phase 41, carried ever since) and the schema
  description at `:5,77` names `tools.deny_domains.registry`, a module that has **never existed**
  (verified: no such path). Both debts close for free; do not open a separate task for them.
- **D-10:** **`gate-registry.json` finally goes**, closing Phase 43's recorded CER-07/CER-08
  collision, together with its `DATA_CONTRACT_PATHS` entry (`hash.py:32`) and the **5 hyphenated
  provenance docstrings** in `tools/adoption_scan/**` carried from Phase 42. Phase 43 narrowed
  `test_hash.py`'s expected set to `{gate-registry.json}`; this phase moves that assertion again —
  in the same commit as the deletion.
- **D-11:** **`/component` loses its SECOND "Mandated order" section only.** Verified by reading:
  `component.md:15-30` (structure → per-package AGENTS.md → test harness) is the ① mechanism CER-08
  says survives; `:37-66` (derive the component agent, register the topology slot, keep the
  consistency gate green) plus its `## Guard — component binding` at `:68` is the half that goes.
  CER-08's "steps 1–3 survive" refers to the first section, not the second.
- **D-12:** **`[pipeline]` removal has the widest blast radius in the phase.** Eight
  `tools/harness_lint/tests/*` read the topology, including `test_pipeline_config.py` (the
  consistency gate, which dies with the slot), `test_orchestrator_topology.py`,
  `test_conductor_graph_render.py`, and `test_contract_graph_config.py`. `harness_config/loader.py`'s
  `pipeline()` passthrough goes too. ⚠ `[[components]]` and the TOPO-02
  `[contract_graph.relationships]` slot **survive** — `effective_relationships()` lowers the linear
  edge on demand, so removing `[pipeline]` must not break the contract-graph seam.
- **D-13:** **`tools/memory_ui` (1756 LOC) has no consumer outside itself** — verified. It is the
  cleanest deletion in the phase and should not be over-planned.

### Ordering and commit discipline (carried, measured — do not re-derive)

- **D-14:** **Every live-tree-rendering test is repaired in the SAME commit as the deletion that
  invalidates it.** Phase 43 found twelve instances of the opposite across four verification passes.
  The known surfaces here: `test_emit_determinism.ambr` (renders command/skill/agent BODIES plus
  `harness/opencode.json` — any `harness/{agents,commands,skills}/**` edit invalidates it),
  `docs_sync`'s `EXPECTED_PAGES` (loses `deny-domains`), `caps.py`'s `EXPECTED_SKILLS` (loses
  `pipeline-map`, `gate-model`, `golden-testing`, `golden-debug`) which **hard-fails the emitter
  before it writes a byte**, `test_settings_coexist.py`'s PreToolUse slot count, `test_commands.py`,
  `test_contract_guard.py:330`, `DATA_CONTRACT_PATHS` membership in `test_hash.py`, and
  `test_install_completeness.py`'s module-discovery floor — which **resolves each discovered ref to a
  real `.py` file**, not merely counts them.
- **D-15:** delete/move → `git add` → `git commit -- <pathspec>` → verify → amend-if-red.
  `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so tracked deletions red until
  staged AND committed. That red is intra-commit and expected; **no commit may END red.**
- **D-16:** `git commit -m "<msg>" -- <pathspec>` — message BEFORE `--`. Putting `-m` after `--`
  makes git parse the message as a pathspec and abort; two agents lost a commit to this in Phase 43.
  Never `git add -A` / `git add .` / `git commit -a` / `git checkout <ref> -- .`.
- **D-17:** Source-first: edit `harness/**`, then `python -m tools.harness_emit`. Never hand-edit
  `.opencode/**`, `.claude/**`, or root `opencode.json`.
- **D-18:** **Run things, don't read them.** Every phase from 40 through 43 found consumers its plan
  had not listed, and every one surfaced from a test run, an emitter run, or a live invocation —
  never from a diff. Phase 43's decisive verification was a scratch-clone commit replay.

### Verification / done-condition

- **D-19:** Done = the CER-08 paths gone with no surviving invoker; a stale-checkout re-emit drops
  the `secret_scan` group (asserted by extending
  `test_retired_signature_group_is_dropped_from_a_stale_checkout`, which Phase 43 added for exactly
  this); `contracts/harness/` free of `deny-domains.*` and `gate-registry.json` with a rebaselined
  manifest and `contract-drift` exit 0; the golden stack resolving under `examples/log-parser/` with
  BOTH the `golden` job and the `workspace` job's `test_workspace_golden.py` path repointed
  (YAML-resolved, never grep); `uv run pytest -q` green at every commit; `emit-drift`,
  `stale-derived`, ruff ratchet clean; `uv.lock` refreshed.
- **D-20:** **No mutation-proof table is owed** — this phase removes a gate (`secret_scan`) and adds
  no control. The one exception is D-19's stale-checkout assertion, which is coverage of a retained
  behavior, extended rather than newly invented.
- **D-21:** Report whole-phase LOC from `git diff --shortstat` (measured, not estimated). Expect a
  smaller net deletion than Phase 43's −12,383 because CER-09 **moves** rather than deletes.

### Claude's Discretion

- Plan/task decomposition and wave count (CER-08 deletions and the CER-09 relocation are largely
  independent and may parallelize; the relocation is the long pole).
- Whether the contract deletions ride with their package deletions or take their own commit.
- The exact new package name under `examples/log-parser/` (D-03 fixes the shape, not the spelling).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and authority
- `.planning/ROADMAP.md` §"#### Phase 44: Non-Goal Surface Removal" — scope, non-goals, accepted
  consequence, 8 success criteria, and the three recorded corrections to the requirement prose.
- `.planning/REQUIREMENTS.md` — **CER-08**, **CER-09**.
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — accepted; names this surface and records
  `secret_scan` + `ledger_guard` as permanent residuals caught at CI/PR review.
- `docs/adr/0002-*` — the general-template de-specialization ADR whose clause (b) is CER-09's ground.

### Prior-phase carry-forward (read before planning — this is where the cost was)
- `.planning/phases/43-lifecycle-plane-removal/43-VERIFICATION.md` — 8/8, and the gate holes it names.
- `.planning/phases/43-lifecycle-plane-removal/REVIEW.md` — 21 findings; **CR-01 is the
  `RETIRED_SIGNATURES` defect D-07 must not repeat.**
- `.planning/phases/43-lifecycle-plane-removal/43-0{1..5}-SUMMARY.md` — the contract-deletion +
  manifest-rebaseline procedure, the `EXPECTED_SKILLS` emitter hard-fail, and the measured ordering rule.
- `.planning/phases/42-.../42-VERIFICATION.md` — the falsify-the-fix verification style to expect.

### The surface this phase touches
- `tools/hooks/secret_scan.py`, `harness/plugins/secret-scan.ts`, `tools/harness_emit/merge.py:91,111,180`.
- `contracts/harness/security/deny-domains.{json,schema.json}`,
  `contracts/harness/task-control/gate-registry.json`, `tools/contract_hash/hash.py:30-34`,
  `contracts/.hashes/manifest.json`.
- `tools/memory_ui`, `tools/strangler_guard`, `harness/commands/strangler-step.md`.
- `harness/project.toml:77-80` (`[pipeline].edges`), `tools/harness_config/loader.py`,
  the eight `tools/harness_lint/tests/*` that read the topology.
- `harness/commands/{pipeline,component}.md`, `harness/skills/{pipeline-map,gate-model}/`.
- `tools/golden_runner/` (791 LOC), root `golden/`, `harness/commands/{golden,golden-approve}.md`,
  `harness/skills/{golden-testing,golden-debug}/`, `examples/log-parser/tests/*` (4 importers),
  `.github/workflows/ci.yml:157-168` (`golden`) and `:336` (`workspace`).
- Root `pyproject.toml:29-35` (`[tool.uv.workspace]`), `tools/harness_lint/workspace_check.py`.

### Conventions
- `AGENTS.md` (root) — nearest-wins rules; its command/skill index needs the deletions swept (45 owns
  the reconciliation, but nothing may point at a corpse mid-phase).
- `examples/log-parser/AGENTS.md` and `examples/log-parser/README.md` — the instance's own rules; both
  describe `tools/golden_runner` as core-owned and must follow the relocation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- **`RETIRED_SIGNATURES` (`merge.py:111`)** — now a permanent tombstone tuple with one entry, plus
  `test_retired_signature_group_is_dropped_from_a_stale_checkout` in
  `tools/harness_emit/tests/test_settings_merge.py`, written in Phase 43 to reconstruct the stale
  group from whatever signature is retired. **Extending it for `secret_scan` is a one-line change.**
- The Phase-41/42/43 contract-deletion + rebaseline procedure (`git rm`, then rebaseline
  `contracts/.hashes/manifest.json` in the same commit; `contract_guard`'s PreToolUse hook matches
  `Write|Edit` only, never `Bash`, so `git rm` needs no `HARNESS_DEV_BYPASS`).
- The `ruamel.yaml` fan-in `needs` resolver (an already-resolved transitive dep — **do not add PyYAML**).
- `sys.path.insert` conftest idiom already used by `examples/log-parser/tests/conftest.py`.

### Established patterns
- Emitted trees are derived; `emit-drift` reds on any hand-edit.
- `caps.py` count/name declarations hard-fail the emitter *before* it writes.
- Deleting a contract moves the hash manifest → rebaseline in the same commit.
- A workspace member directory without a `pyproject.toml` breaks EVERY `uv` invocation repo-wide and
  fails the PreToolUse guards closed — create the member and its `pyproject.toml` in one step.

### Integration points
1. `secret_scan` → `merge.py` signature + hook-group literal → emitted `.claude/settings.json`
   (and every stale checkout — D-07).
2. `deny-domains` / `gate-registry` → `DATA_CONTRACT_PATHS` → manifest → `docs_sync` `EXPECTED_PAGES`
   → `docs/reference/**` → two syrupy snapshots.
3. `[pipeline]` → `harness_config/loader.py` → eight `harness_lint` tests → `/component`'s second half.
4. `tools/golden_runner` → 4 example test importers → uv workspace membership → 2 CI jobs.

</code_context>

<specifics>
## Specific Ideas

- The relocation is the long pole and the only part that can silently half-land: a moved package that
  is not a workspace member still *imports* fine under `sys.path` manipulation in a local pytest run,
  while `uv run` in CI resolves nothing. **Verify with `uv run`, not bare `pytest`.**
- `examples/log-parser/golden/` already exists with `value-regression/` and `repr-only/` subtrees, so
  root `golden/sample/` folds into a live directory, not an empty one.
- CER-09's text omits the `workspace` CI job (`ci.yml:336`) — it runs
  `tools/golden_runner/tests/test_workspace_golden.py`. Repointing only the `golden` job leaves the
  cross-repo gate pointing at a moved path.

</specifics>

<deferred>
## Deferred Ideas

- **Projection repair** — `caps.py` frozensets, `emit-manifest.json`, `HARNESS_SIGNATURES` hygiene,
  `docs/reference/**`, `AGENTS.md:52-62`'s golden-path table (relocated by CER-09), `.memory/derived/**`
  → **Phase 45** (CER-10/CER-11).
- **Stale prose in human-owned docs** — `docs/how-to/task-lifecycle.md` (8 command blocks invoking 7
  deleted modules), `docs/explanation/task-lifecycle-shadow-metrics.md`,
  `docs/explanation/next-milestone-task-control-plane.md`, plus `docs/how-to/README.md`,
  `docs/adr/README.md` and `docs/explanation/agent-workflow-skillset-design-guide.md` → **Phase 45**.
  Carried out of Phase 43's review; `docs/` sits outside every sweep the harness runs, and
  `tools/docs_guard` was deleted in Phase 41, so nothing gates them.
- **ADR-0008 supersession** — ADR-0008 still reads `Status: Accepted`, `Superseded by: —` while the
  plane it governs was deleted in Phase 43; ADR-0012 supersedes 0001 and 0010 but never mentions 0008.
  In a repo whose stated precedence is "accepted ADRs win a data conflict against code", it currently
  tells agents the deletion was the error. Resolving it needs a NEW ADR (the repo's
  supersede-don't-edit convention) → **Phase 45, or a human call at milestone close.**
- **ROADMAP SC-1 wording (Phase 43)** — as literally written it can never pass, because the
  negative-control fixture at `tools/contract_graph/tests/test_query.py:75-78` must contain the
  forbidden strings for the assertion above it to mean anything. The verifier recorded an
  executable-invocation override; the wording should be corrected rather than hand-waived.

</deferred>

---

*Phase: 44-non-goal-surface-removal*
*Context gathered: 2026-07-29*
