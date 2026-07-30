# Phase 41: Docs-Review Plane Removal - Context

**Gathered:** 2026-07-27
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; see `41-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

Delete the **human-doc review-obligation plane** in its entirety (CER-05, v2.5 A). The plane is:
the 8 `[[binding]]` rows and their registry, the human-authored review ledger, `tools/docs_guard`
(6110 LOC), the `ledger_guard` hook and its `path_deny_globs` entry, `/docs-update`, skill
`docs-upkeep`, `contracts/harness/docs/*`, and the CI `docs-guard` job with its fan-in `needs` entry.

After this phase **no gate requires a human-authored artifact to go green** — the docs-review plane
is the last of the five such gates v2.5 retires. Enforcement authority is ADR-0012 (CI + the merge),
already accepted; this phase ratifies nothing and adds nothing.

**Not in this phase:** adoption ↔ task-control decoupling (Phase 42), the lifecycle plane (Phase 43),
`gate-model` / `secret_scan` / `pipeline` deletion (Phase 44), projection repair (Phase 45).

</domain>

<decisions>
## Implementation Decisions

### Deletion scope — what leaves with the plane

- **D-01:** Delete exactly the CER-05 list: `tools/docs_guard/**`, `docs/.docs-review-ledger.toml`,
  `tools/hooks/ledger_guard.py`, the `docs/.docs-review-ledger.toml` entry in
  `harness/permission-matrix.json:34` (`path_deny_globs`), `harness/commands/docs-update.md`,
  `harness/skills/docs-upkeep/**`, `harness/plugins/ledger-guard.ts`, `contracts/harness/docs/**`,
  and the CI `docs-guard` job (`.github/workflows/ci.yml:317-351`) plus its entry in the fan-in
  `needs:` list (`:381`).
- **D-02:** **The registry goes too.** `docs/doc-dependencies.toml` (8 bindings) and its derived
  reference page `docs/reference/doc-dependencies.md` have no consumer once the guard is gone —
  `tools.docs_guard` is stated in CI's own comment to be its *only* validator. Delete both, delete
  `contracts/harness/docs/doc-dependencies.schema.json`, and **rebaseline
  `contracts/.hashes/manifest.json`** in the same commit as the contract removal.
- **D-03:** **The derived staleness queue goes too.** `tools/memory_regen/docs_staleness.py` (233 LOC)
  imports `tools.docs_guard` (`:158`); delete it with `tools/memory_regen/tests/test_docs_staleness.py`,
  the `("docs", _docs_staleness_pointer(...))` injector row (`inject.py:82,217`) and
  `tools/memory_regen/tests/test_inject_docs_pointer.py`. This is a scope *clarification*, not an
  expansion: it is machinery of the same plane, it is named nowhere else in v2.5, and leaving it
  strands an import of a deleted package. (Phase 43 separately strips `memory_regen`'s *active-task*
  block — different block, do not conflate.)
- **D-04:** **The adoption docs-binding proposal goes too** — DOCSUP-07's "`/adopt` PROPOSES registry
  rows" path, incl. `tools/adoption_apply/tests/test_docs_binding_proposal.py` and the
  `doc-dependencies` proposal branch in `adoption_apply`/`adoption_scan`. It proposes rows into a
  registry that will not exist. Only the docs-registry proposal belongs here; the rest of adoption
  decoupling stays Phase 42's.
- **D-05:** **Explicitly NOT deleted here:** `tools/docs_sync` + `/docs-sync` (generated Diátaxis
  reference — a different machine), `docs/adr/0010-*.md` (append-only, already `superseded by 0012`),
  `harness/skills/gate-model/**` (Phase 44 deletes it; 41 only trims its docs-plane claims),
  `tools/discipline` (Phase 43), and `.planning/**` history.

### Replacement policy

- **D-06:** **No replacement of any kind.** No advisory/warn-only docs job, no severity flip, no
  successor gate. The severity-flip alternative is provably dead: `guard.py:383-399` classifies
  `BROKEN` before every staleness check and `cli.py:6-13` exits 1 on `BROKEN` regardless of severity,
  and every v2.5 deletion produces `BROKEN`. Owner's binding constraint: the surface may not grow.
- **D-07:** **No new ADR.** ADR-0012 is `accepted` (2026-07-26) and supersedes ADR-0010; Phase 41
  cites it. Do not edit ADR-0010 (supersede-don't-edit); do not author a ratification of any kind.
- **D-08:** The v2.3-era blocking constraint *"do not author `docs/.docs-review-ledger.toml`"* is
  satisfied by **deleting** the file. Deleting the ledger is not authoring a disposition row. No
  commit in this phase may add or modify a `[[reviewed]]` row on the way to removal.

### Ordering and commit discipline

- **D-09:** **Unbind first.** Task 1 removes the 8 `[[binding]]` rows + the ledger; only then does a
  later task delete the guard, the hook, the contracts and the CI job. Counting is done from
  `grep -c '^\[\[binding\]\]' docs/doc-dependencies.toml` (= 8), never from prose.
- **D-10:** Per-task ordering is **delete → stage → commit → verify → amend-if-red**, NOT
  verify-before-commit — Phase 40's measured carry-forward: `tools/adoption_scan` reads git, not the
  filesystem (`destinations.py:217` `git ls-files`), so a tracked-file deletion reds ~3 tests until
  staged and committed (`test_catalog_invariant_to_untracked_local_state` is red by construction
  while uncommitted).
- **D-11:** `git commit -- <pathspec>` every time, with `git diff --cached --name-only` inspected
  immediately before. Never `git add -A` / `git add .` / `git commit -a` (28-01 anti-pattern).

### Surviving references and re-emit

- **D-12:** **Source-first, then emit.** Edit `harness/**` only, then run
  `python -m tools.harness_emit`; never hand-edit `.opencode/**` or `.claude/**`. Remove the
  corresponding rows from `tools/harness_emit/emit-manifest.json` (`:18,41,71,89,101`) and the
  `ledger_guard` hook group from the emitted `.claude/settings.json` (`:165`) via its source.
- **D-13:** **Prose + test sweep lands in this phase**, not deferred: `AGENTS.md:106-107` (command +
  skill indexes), `harness/skills/gate-model/SKILL.md` (docs-plane claims only),
  `.memory/README.md` (the "third path-deny domain" sentence), `harness/permission-matrix.json:2`
  (`_note` prose), `tools/harness_lint/caps.py:128-129,151`, and the tests that assert the wiring:
  `test_docs_update_wiring.py`, `tools/hooks/tests/test_settings_coexist.py`,
  `tools/harness_emit/tests/test_coexist.py`, `test_tests_are_isolatable.py`,
  `test_workspace_member_completeness.py`, `tools/docs_sync/tests/test_docs_sync_determinism.py`.
  Comment-only mirrors in `tools/ruff_baseline/**` may keep or drop their docstring reference — no
  behavior rides on it.
- **D-14:** After removing the job, confirm the fan-in `needs:` has **no dangling entry**, resolved
  as YAML (Phase 40's method), not by grep.

### Verification / done-condition

- **D-15:** Done = **CI fan-in gate green**, plus: full `uv run pytest -q` green; residue sweep
  returns 0 hits outside `.planning/` for
  `docs_guard|docs-guard|docs-review-ledger|ledger_guard|docs-upkeep|docs-update|doc-dependencies`;
  `emit-drift`, `stale-derived`, `contract-drift` (rebaselined manifest) and `ruff-ratchet` clean.
- **D-16:** **No mutation-proof table is owed.** The anti-pattern rule ("author the adversarial input
  table first, prove RED") governs changes that ADD or claim a control. This phase adds none — its
  proof is the residue sweep plus the green fan-in. Recorded here so review does not demand one.
- **D-17:** LOC removed is reported as evidence (expect ≳6.3k: 6110 guard + 233 staleness + hook +
  ledger + registry + contracts), counted from `git diff --stat`, not estimated.

### Claude's Discretion

- Task decomposition and plan count.
- Whether the prose/test sweep (D-13) is one task or is folded into each deletion task.
- Whether the derived reference page removal rides with the contract removal commit or its own.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and authority
- `.planning/ROADMAP.md` §"v2.5 De-ceremony", Phase 41 bullet — the phase's fixed boundary and its
  success condition; also the owner's binding constraint ("the surface may not grow") and the
  DEV/PRODUCT boundary paragraph.
- `.planning/REQUIREMENTS.md` — **CER-05** (lines 49-55), the requirement this phase discharges.
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — **accepted**; CI + the merge are the
  authority; supersedes ADR-0001 and ADR-0010. The record Phase 41 cites instead of ratifying.
- `docs/adr/0010-human-docs-review-obligation-model.md` — the plane being deleted, `superseded by
  0012`. Read for what the plane *claimed*; do **not** edit (append-only).
- `docs/adr/0011-gate-right-sizing-dev-light-ci-strong.md` — dev-light/CI-strong, the `HARNESS_DEV_LIGHT`
  short-circuit at `.claude/settings.json:165`.
- `docs/adr/0007-constitution-gate-dev-enforce-decoupling.md` — `HARNESS_DEV_BYPASS` semantics for the
  `contracts/harness/docs/**` removal (a constitution-plane write).
- `.planning/research/v2.5-scoping-FINAL.md` — the scoping panel behind the milestone.

### Prior-phase carry-forward
- `.planning/phases/40-self-gate-teardown/40-01-SUMMARY.md` — the deletion-phase ordering measurement
  (3→1→0) that D-10 encodes; the CI `needs`-resolution method D-14 reuses.
- `.planning/phases/40-self-gate-teardown/40-CONTEXT.md`, `40-UAT.md` — the immediately preceding
  deletion phase's shape.
- `.planning/.continue-here.md` §"Critical Anti-Patterns" — the blocking table (happy-path fixtures,
  inverted `!` gate, `git commit` publishing the shared index). Note its `<current_state>` is v2.3-era
  and stale; the anti-patterns are not.

### The plane's own surface (delete targets)
- `tools/docs_guard/{guard,cli,ledger,registry,impact,digest,exclusions}.py` — `guard.py:383-399` and
  `cli.py:6-13` are the proof that a severity flip cannot work.
- `docs/doc-dependencies.toml` (8 `[[binding]]` rows), `docs/.docs-review-ledger.toml` (90 lines),
  `docs/reference/doc-dependencies.md`, `contracts/harness/docs/doc-dependencies.schema.json`.
- `tools/hooks/ledger_guard.py`, `harness/plugins/ledger-guard.ts`,
  `harness/permission-matrix.json:2,34`, `.claude/settings.json:165`.
- `.github/workflows/ci.yml:317-351` (job) and `:381` (fan-in `needs`).
- `tools/memory_regen/docs_staleness.py`, `tools/memory_regen/inject.py:82,217`.
- `tools/harness_emit/emit-manifest.json:18,41,71,89,101`.

### Conventions
- `AGENTS.md` (root) — nearest-wins agent rules; its command/skill index is a D-13 edit target.
- `.memory/README.md` — two-plane declaration; the ledger's "third path-deny domain" sentence dies.
- `docs/adr/0001-walking-skeleton-golden-core.md:48` — the constitution-member list (superseded by
  0012; relevant because `contracts/harness/docs/**` is a constitution-plane path).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- **Phase 40's teardown shape** is the template: delete source → drop the emit-manifest rows →
  re-emit → drop the CI job + `needs` entry → sweep tests. One plan sufficed there.
- **`tools/harness_emit`** already owns projection into both runtime trees; deletions propagate by
  re-emit, so no `.opencode/` / `.claude/` file is ever hand-removed.
- **`contracts/.hashes/manifest.json` + `tools.contract_drift`** already handle add/remove of a
  contract; removal is a rebaseline, an established move.

### Established patterns
- **Emitted trees are derived** — hand-editing them reds `emit-drift`.
- **`adoption_scan` reads git, not the filesystem** (`destinations.py:217`) — hence D-10's ordering.
- **Separate-job CI idiom** — `docs-guard` is its own job precisely so it can be removed as a unit.
- **Ratchet-style lint** — `tools/ruff_baseline` counts; deleting 6.3k LOC moves the baseline, so the
  ratchet file may need a rebaseline in the same commit.

### Integration points
1. `harness/` source → `emit-manifest.json` → `.opencode/` + `.claude/` (re-emit).
2. `harness/permission-matrix.json` → `tools/harness_perms/resolver.py` → hooks (`ledger_guard`,
   `contract_guard` share the resolver — touch only the ledger entry).
3. `tools.docs_guard` → `tools/memory_regen/docs_staleness.py` → `.memory/derived/docs-staleness.md`
   → `inject.py` SessionStart pointer.
4. `tools.docs_guard` ← `tools/adoption_apply` (DOCSUP-07 proposal path).
5. `.github/workflows/ci.yml` job → fan-in `needs:` (`:381`).

</code_context>

<specifics>
## Specific Ideas

- The CI comment block at `ci.yml:317-340` documents the plane's exit-code semantics; it is deleted
  with the job — do not relocate the prose elsewhere "for the record". The ADRs hold the history.
- Count bindings mechanically (`grep -c '^\[\[binding\]\]'` = 8). A loose grep counts 9 because a
  prose line mentions the marker.
- Report the removal as measured LOC (`git diff --stat`), matching Phase 40's evidence style.

</specifics>

<deferred>
## Deferred Ideas

- **Full `gate-model` skill deletion** — Phase 44 (CER-08). Phase 41 trims only its docs-plane claims.
- **Adoption ↔ task-control decoupling, `_CATEGORY_GLOBS` install-set repair** — Phase 42 (CER-06,
  PROD-01). Only the docs-registry proposal path is in 41's scope.
- **`memory_regen` active-task block strip** — Phase 43 (CER-07). Distinct from D-03's docs block.
- **`ruff check` scope / vendored-tree excludes** — settled in Phase 34; not reopened here.

</deferred>

---

*Phase: 41-docs-review-plane-removal*
*Context gathered: 2026-07-27*
