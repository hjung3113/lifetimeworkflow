# Phase 45: Projection Repair - Context

**Gathered:** 2026-07-29
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; see `45-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

After four deletion phases removed ~25k LOC, make the repo's account of itself true again (CER-10,
CER-11). Two halves:

1. **Controls that no longer control anything.** A glob, deny row, or CODEOWNERS route that matches
   zero paths while its comment claims a plane. This is the dangerous half.
2. **Dangling references.** Prose, tests, and templates naming deleted surface.

**Not in this phase:** the product's lifecycle rewrite (`orchestrator.md` routes, the completion
contract, per-skill operative sentences) — that is **Phase 46** (PROD-02…05). No new gate, tool,
contract, or dependency: a "prose freshness checker" is exactly the class this milestone removes, and
`docs_guard` was deleted in Phase 41 on purpose. Do not re-add it.

</domain>

<decisions>
## Implementation Decisions

### The finding that resolves Tier 1: ADR-0012 already decided it

- **D-01:** **`golden/**` is REMOVED from the constitution plane, not repointed.** ADR-0012 clause (d)
  (`docs/adr/0012-...:139-147`) supersedes ADR-0001's four-member declaration "to the extent that
  `golden/**` leaves the constitution-plane core", and then names this exact moment: *"Between this
  ADR's ratification and Phase 44's actual code move, `tools/hooks/contract_guard.py`'s
  `CONSTITUTION_GLOBS` and the pinned test `tools/hooks/tests/test_contract_guard.py:352-375` will
  KNOWINGLY still enforce `golden/**` as a fourth member. This is named here as an expected"*
  transitional state. **Phase 44 made the code move; the removal is now due and needs no new ADR.**
  Phase 44's own recorded reasoning (`44-06-SUMMARY.md:311-316` — "accepted rather than widening
  `CONSTITUTION_GLOBS`, which would be surface growth") reached a defensible outcome by the wrong
  route; the right route is that the member was already superseded.
- **D-02:** Therefore the constitution plane becomes **three members**: `contracts/**`, `docs/adr/**`,
  `docs/glossary.md`. Update every copy of that list together, in one commit — they are duplicated:
  `tools/hooks/contract_guard.py:53` (`CONSTITUTION_GLOBS`), `harness/permission-matrix.json:30`
  (`path_deny_globs`, whose `_note` restates the four members), the pinned test
  `test_contract_guard.py:352-375` (`test_every_declared_plane_member_is_independently_enforced`),
  `.github/CODEOWNERS:30` (`/golden/`, a deleted directory), and `test_resolver.py:60`.
- **D-03:** **The relocated baselines stay gated at the merge, not in-session.** `CODEOWNERS:36`
  (`/examples/*/golden/ @hjung3113`) already covers them and is correct — instance evidence is
  reviewed at the PR per ADR-0012, which is the milestone's whole thesis. Do NOT add an in-session
  hook for them; that would be the surface growth the constraint forbids.
- **D-04:** **The `*.env` deny rows lose their last enforcer — decide, don't drift.**
  `permission-matrix.json:32-33` (`*.env`, `**/*.env`) were enforced only by `secret_scan`, deleted in
  Phase 44; `contract_guard` explicitly excludes them (`contract_guard.py:36-37`), and
  `test_resolver.py:64` still asserts `config/prod.env` → `deny`, keeping a claimed control green.
  **Remove the rows and the assertion together.** A deny nothing performs is a false claim, and
  ADR-0012 already records secret detection at the tool boundary as a permanent residual caught at
  CI/PR review. Re-adding an enforcer is forbidden.

### What "stale" means here — and what it does NOT

- **D-05:** **Three categories are legitimate and must survive.** (a) The relocated
  `examples/log-parser/golden_runner/**` package *implements* the approve gate, so it will keep naming
  it — that is the implementation, not a dangling reference. (b) **History notes that name a retired
  artifact in order to record its retirement** — `caps.py:124,134`, `test_coexist.py:56`,
  `test_commands.py:42`. Phase 43's and Phase 44's executors each refused to strip these to force a
  clean grep, and both were right. (c) Append-only ADR text. **Sweep by meaning, never by token.**
- **D-06:** Real staleness is a **live file describing a control, path, or command that no longer
  exists**. That is the test to apply to every candidate.

### The enumerated surface (verified 2026-07-29)

- **D-07:** Root `AGENTS.md` — `:8-9` ("the true backstop", now false), `:66,67` (`python -m
  tools.golden_runner.runner` / `.approve`), `:84` (engine list naming `golden_runner`). ⚠ `:8-9` and
  `:66-67` sit **outside** the emitter's HARNESS-MANAGED block, so a re-emit will NOT repair them —
  this is exactly why CER-11 names them.
- **D-08:** `tools/hooks/contract_guard.py:9,55,75,89` — `/golden-approve` in live refusal text plus a
  stale `tools/golden_runner/approve.py` path; asserted by `test_contract_guard.py:51,288`.
- **D-09:** `README.md:119`; **`README.ko.md` whole file** — `:79` labels `harness/task-control/`
  (deleted Phase 43), plus stale `golden/` and `tools/golden_runner` lines. ⚠ Every prior deferral list
  named `README.md` and never the Korean file; that gap is why it survived four phases.
- **D-10:** `docs/` — `glossary.md:20`, `how-to/README.md:11`, `how-to/approve-a-golden.md` (whole
  file) carry `/golden-approve`; `how-to/task-lifecycle.md` (8 command blocks, 7 deleted modules),
  `explanation/task-lifecycle-shadow-metrics.md`, `explanation/next-milestone-task-control-plane.md`,
  `adr/README.md`, `explanation/agent-workflow-skillset-design-guide.md` carry Phase-43 plane prose.
  Whole-file deletion is the right answer where a document's entire subject is a deleted plane.
- **D-11:** Drained assertions — `test_topology_relationships.py:54-57` now asserts `[] == []`
  (verified: `effective_relationships(load_project())` returns `[]`);
  `test_install_completeness.py:196` is named `test_discovers_at_least_twelve_modules` while asserting
  `>= 11`; `commit_gate.py:18,60,203` keeps a `SKIP` vocabulary no component can now produce.
- **D-12:** `harness/agents/templates/component-engineer.md` — still shipped and gated, header still
  says "`/component` instantiates a COPY of this file", but Phase 44 deleted that step. Note
  `test_pipeline_topology.py`'s `_CORE_RESOLUTION_DOCS` was repointed AT this file in Phase 44, so it
  is load-bearing for that test — decide deliberately between re-wiring `/component` and correcting
  the template's self-description; do not delete it without checking that test.
- **D-13:** `tools/harness_lint/tests/test_ci_paths.py` hard-requires `examples/**` (3 of 8 discovered
  tokens) while living in the core suite, so deleting the reference instance — which ADR-0002 invites —
  turns the **core** suite red, and `test_core_no_example_dep.py` cannot see it (`_CORE_ROOTS` scans
  neither `pyproject.toml` nor `.github/`).

### The record itself

- **D-14:** **ADR-0008 needs a superseding ADR** — it reads `Status: Accepted`, `Superseded by: —`
  while Phase 43 deleted its plane, and ADR-0012 supersedes 0001 and 0010 but never mentions 0008. In
  a repo whose precedence is "accepted ADRs win a data conflict against code", it currently tells
  agents the deletion was the error. The supersede-don't-edit convention means a NEW ADR, which is
  **human-gated** — surface it for the owner at the milestone-close PR rather than authoring it
  unilaterally, and record the gap either way.
- **D-15:** **Phase 43's ROADMAP SC-1 wording** can never pass as literally written (the
  negative-control fixture at `test_query.py:75-78` must contain the forbidden strings for the
  assertion above it to mean anything). `43-VERIFICATION.md` recorded an executable-invocation
  override; correct the wording rather than leaving it hand-waived.

### Ordering and commit discipline (carried, measured — do not re-derive)

- **D-16:** **Every live-tree-rendering test is repaired in the SAME commit as the change that
  invalidates it.** Phases 43 and 44 produced twenty blockers of this one class between them.
- **D-17:** `git commit -m "<msg>" -- <pathspec>` — message BEFORE `--`. `git rm`/`git mv` already
  stage; a later `git add -- <deleted-path>` exits 128. Never `git add -A` / `git add .` /
  `git commit -a` / `git checkout <ref> -- .`.
- **D-18:** Source-first: edit `harness/**`, then `python -m tools.harness_emit`. Never hand-edit
  `.opencode/**`, `.claude/**`, or root `opencode.json`. ⚠ But note D-07: the `AGENTS.md` sites are
  OUTSIDE the managed block, so a re-emit will not fix them and hand-editing them is correct.
- **D-19:** **Run things, don't read them.** Phase 44's two scratch-clone commit replays found 8
  blockers that three reading-based passes in Phase 43 had missed. Verify per commit.
- **D-20:** `uv run pytest -q` does NOT collect `examples/**` (`testpaths = ["libs/python", "tools"]`).
  Any commit touching the instance needs an explicit `uv run pytest examples/log-parser/...` leg.

### Verification / done-condition

- **D-21:** Done = no glob/deny/CODEOWNERS route matches zero paths while claiming a plane (asserted
  mechanically); the constitution list is three members everywhere it is duplicated; no test asserts a
  deny nothing performs or a tautology a deletion drained; `AGENTS.md`, both READMEs and `docs/` name
  no deleted surface outside ADR text or an explicit history note; `emit-drift`, `stale-derived`,
  `contract-drift`, ruff ratchet green with an empty diff; `uv run pytest -q` green at every commit.
- **D-22:** **No mutation-proof table is owed** — this phase removes claims and adds no control.
- **D-23:** Report whole-phase LOC from `git diff --shortstat` (measured). Expect a small net deletion:
  this phase corrects and deletes prose, it does not remove machinery.

### Claude's Discretion

- Plan/task decomposition and wave count. Tier 1 (D-01…D-04) should land first and separately — it is
  the only security-relevant half.
- Whether whole-file deletions under `docs/` ride with their tier or take one commit.
- Exact replacement wording, provided no successor mechanism appears.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and authority
- `.planning/ROADMAP.md` §"#### Phase 45: Projection Repair" — the four tiers, non-goals, and 8 criteria.
- `.planning/REQUIREMENTS.md` — **CER-10**, **CER-11**.
- **`docs/adr/0012-ci-and-merge-as-decision-authority.md:139-147`** — clause (d). **This is the
  authority for D-01 and it names this exact transitional state.** Read it before touching
  `CONSTITUTION_GLOBS`.
- `docs/adr/0001-walking-skeleton-golden-core.md:48` — the superseded four-member declaration.
- `docs/adr/0002-*` — the template/instance split behind CER-09 and D-13.

### Prior-phase carry-forward
- `.planning/phases/44-non-goal-surface-removal/REVIEW.md` — CR-01/CR-02 and the warnings this phase
  inherits; note CR-01's framing is corrected by D-01.
- `.planning/phases/44-non-goal-surface-removal/44-06-SUMMARY.md` — the 12-item deferral list and the
  recorded constitution downgrade (`:311-316`).
- `.planning/phases/43-lifecycle-plane-removal/REVIEW.md` — the `RETIRED_SIGNATURES` precedent for
  "a control that silently stops protecting anything".

### The surface this phase touches
- `tools/hooks/contract_guard.py:9,36-37,53,55,75,89`; `tools/hooks/tests/test_contract_guard.py:51,288,352-375`.
- `harness/permission-matrix.json:2` (`_note`), `:30`, `:32-33`; `tools/harness_perms/tests/test_resolver.py:60,64`.
- `.github/CODEOWNERS:4,7,30,36`.
- Root `AGENTS.md:8-9,66,67,84`; `README.md:119`; `README.ko.md` (whole).
- `docs/glossary.md:20`; `docs/how-to/{README.md:11,approve-a-golden.md,task-lifecycle.md}`;
  `docs/explanation/{task-lifecycle-shadow-metrics.md,next-milestone-task-control-plane.md,agent-workflow-skillset-design-guide.md}`;
  `docs/adr/README.md`.
- `tools/harness_lint/tests/{test_topology_relationships.py:54-57,test_ci_paths.py}`;
  `tools/adoption_scan/tests/test_install_completeness.py:196`; `tools/hooks/commit_gate.py:18,60,203`;
  `harness/agents/templates/component-engineer.md`.

### Conventions
- `AGENTS.md` (root) — nearest-wins rules (and itself a subject of this phase).
- `.memory/README.md` — two-plane declaration.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- The Phase-43/44 contract + manifest rebaseline procedure, if any contract changes.
- `ruamel.yaml` for any `ci.yml` work — an existing transitive dep. ⚠ If used, set
  `yaml.indent(mapping=2, sequence=4, offset=2)`, `preserve_quotes`, **and `yaml.width`** — Phase 44
  measured a 162-line spurious rewrite without the third knob.
- `tools/harness_perms/resolve_path` — the single glob resolver both the matrix and `contract_guard` use.

### Established patterns
- Emitted trees are derived; `emit-drift` reds on a hand-edit — EXCEPT the `AGENTS.md` sites outside
  the managed block (D-07/D-18).
- `caps.py` count/name declarations hard-fail the emitter before it writes.
- A deny list and its test move together, or the test keeps a dead control green (D-04).

### Integration points
1. `CONSTITUTION_GLOBS` (`contract_guard.py`) ↔ `path_deny_globs` (`permission-matrix.json`) ↔ the
   pinned member test ↔ CODEOWNERS — **four copies of one declaration** (D-02).
2. `secret_scan` (deleted) → the orphaned `*.env` rows → `test_resolver.py:64` (D-04).
3. `/component` (halved in 44) → `component-engineer.md` → `test_pipeline_topology.py`'s
   `_CORE_RESOLUTION_DOCS` (D-12).
4. `test_ci_paths.py` → `examples/**` → the core suite's independence from the instance (D-13).

</code_context>

<specifics>
## Specific Ideas

- The highest-value artifact of this phase is a **mechanical assertion that no declared glob matches
  zero paths**. That is what would have caught CR-01 at Phase 44's commit rather than at its review,
  and it is coverage of an existing declaration, not a new gate — but confirm that framing against
  SC-8 before writing it, because it sits close to the line.
- `permission-matrix.json`'s `_note` restates the four-member list in prose; changing the data without
  the note leaves the file self-contradicting.

</specifics>

<deferred>
## Deferred Ideas

- **PROD-02…05** — the product lifecycle: `orchestrator.md`'s four routes, the six-field completion
  contract, per-skill operative sentences → **Phase 46**.
- **ADR-0008's superseding ADR** (D-14) — human-gated; surface at the milestone-close PR.
- **A general prose-freshness gate** — explicitly refused. It is the class this milestone removes.

</deferred>

---

*Phase: 45-projection-repair*
*Context gathered: 2026-07-29*
