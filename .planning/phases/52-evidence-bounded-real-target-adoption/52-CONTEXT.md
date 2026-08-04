# Phase 52: Evidence-Bounded Real-Target Adoption - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning
**Mode:** autonomous smart-discuss (4 grey areas proposed, all accepted as recommended)

<domain>
## Phase Boundary

Repair the harness so a full `/adopt` discover → draft → apply cycle succeeds against a **freshly
created** isolated git worktree of the real FeedbackOps monorepo — with every change traced to a
Phase-51 observation (`51-BASELINE-EVIDENCE.md`, OBS-D-01..04) inside purpose ①②③④, and every repair
carrying a regression test.

**Delivers:** repairs for OBS-D-01 (non-member manifest enumerated), OBS-D-03 (convention profile
has no `lint` key and no JS commands), OBS-D-04 (apply leaves unlisted lock sidecars); an
evidence-backed no-change confirmation plus lock-in test for OBS-D-02; a fresh isolated worktree run
proving RTA-01..04; a byte-unchanged proof for the original `develop` checkout with third-party drift
attributed, not hidden.

**Does NOT deliver:** repairs for anything absent from the Phase-51 record; managed `/adopt`
re-run/update semantics (MONO-12 — Phase 53); the `"dir"`-filter shared helper (DEBT-01 — Phase 54);
any new contract, command, skill, gate, or CI job (NG-01).

**Input contract:** `51-BASELINE-EVIDENCE.md` OBS-D-01..04 only. OBS-03 is **refuted** — no budget is
spent repairing pnpm `workspace:*` edge resolution.
</domain>

<decisions>
## Implementation Decisions

### Target worktree, SHA pin, isolation re-proof

- **D-01:** Phase 52 starts from a **freshly created** worktree (the Phase-51 one is disposed),
  created the Phase-51 way: `git -C ~/Desktop/2026/FeedbackOps worktree add --detach <path> <SHA>`,
  outside the `develop` working tree, detached HEAD.
- **D-02:** Pin the target to `develop`'s HEAD **as read at phase start** (`4f16525` at the time of
  discuss; re-read and record the literal SHA at run time). Repairs are proven by repo-local
  fixtures, not by SHA identity with Phase 51, so target movement is not a comparability problem.
- **D-03:** SC-1 "byte-unchanged" uses the Phase-51 D-03 three-artifact proof (`status --porcelain=v2
  --untracked-files=all`; `rev-parse HEAD` + tracked-index digest; untracked path-**set** digest),
  captured before AND after against a snapshot taken at phase start. Any HEAD/index delta is
  attributed by reconstructing index digests from the target's commit trees (the Phase-51
  external-drift method) and recorded outside the OBS-D namespace — third-party drift is never
  filed as an adoption defect, and never silently absorbed either.
- **D-04:** The worktree is **auto-disposed** at phase end (`git worktree remove --force`, exit code
  recorded). No human disposal checkpoint — Phase 51 established and validated the pattern.
- **D-05:** Run depth: the full discover → draft → **apply** cycle into the fresh worktree, executed
  **after** the repairs land, plus the Phase-51 D-12 read-only downstream observations (package facts
  via `tools.memory_regen.package_facts`, nearest-wins conventions via
  `tools.harness_config.loader:conventions_for`). Those downstream reads are what evidence SC-3/SC-4.
- **D-06:** Zero writes to FeedbackOps product code (Phase-51 D-05 carried). Harness artifacts
  written into the worktree are in scope; anything touching target application source is a defect.

### OBS-D-01 — member enumeration scope

- **D-07:** Repair at the source: teach `tools/adoption_scan/detect.py` (`_MANIFEST_KIND_BY_NAME`,
  `detect.py:46`) the **pnpm workspace manifest**. When `pnpm-workspace.yaml` exists at the target
  root, the workspace member set is its declared globs; manifests outside those globs are not
  members. Not an ignore-glob blacklist, and not a downstream filter in draft — the inventory itself
  must be right (RTA-02).
- **D-08:** Non-member manifests found during the walk (e.g. `docs/design-prototype/package.json`)
  are **excluded from the inventory but emitted in a `skipped` diagnostic list** — visible, not
  silently dropped, so a mis-scoped glob is debuggable from the artifact alone.
- **D-09:** **pnpm only.** The observed target is pnpm; the kind table stays extensible but no
  speculative `package.json` `workspaces`, Cargo, or uv workspace support is added (NG-01
  no-growth, and Phase-51 D-17's "no fixture without an actual repair").
- **D-10:** When no workspace manifest is present, the current recursive manifest discovery is
  **unchanged**. All existing adoption fixtures must stay green — this is an additive branch, not a
  replacement.

### OBS-D-03 — convention profile shape + JS commands

- **D-11:** Add `lint` to the fixed key set returned by `conventions_for`
  (`tools/harness_config/loader.py:297`), `None` when the language has no configured value. This is
  a **shape change**, not a null to populate: the key is always present for every language, matching
  the existing `test`/`format`/`bash_scope` treatment.
- **D-12:** JS lint/test commands are **derived from the adopted target's own `package.json`
  scripts** at draft time and written into the target's emitted `harness/project.toml`
  `[[languages]]` row — not hardcoded JS defaults in the harness template. The harness must adapt to
  the target, not assume it.
- **D-13:** **No contract impact.** `contracts/normalization/format-conventions.schema.json` governs
  the §4.3–4.6 canonicalization conventions only, not the per-package convention profile. No new
  contract entry, no schema-hash/golden pairing needed (NG-01). If planning discovers a contract
  *does* govern this shape, contract-first order applies and `/contract-check` runs.
- **D-14:** nearest-wins resolution semantics are **unchanged** — only the key set widens. Every
  existing `conventions_for` resolution test stays green as-is.

### OBS-D-04 lock residue + traceability

- **D-15:** The `.AGENTS.md.lock` / `.CLAUDE.md.lock` / `.claude/.settings.json.lock` sidecars are
  **not unlinked**. Unlinking an flock sidecar after releasing it is the classic unlink race (a
  concurrent holder ends up flocking a deleted inode and mutual exclusion silently breaks) — the
  guard in `tools/adoption_apply/apply.py:306` is correct as written. Instead the sidecars are
  **declared as known harness-managed artifacts** so the apply comparison's `matches` is true, and
  they are added to the target's ignore set.
- **D-16:** A stale lock encountered on a later run is **reported on stderr**, never silently
  reused — a visible signal beats a quiet resume.
- **D-17:** Regression tests are **repo-local**, one per repaired observation, sited next to the tool
  they cover (`tools/adoption_scan/tests/`, `tools/harness_config/tests/`,
  `tools/adoption_apply/tests/`), driven by a **synthetic pnpm workspace fixture**. The live
  FeedbackOps worktree is confirmation evidence only and is never a test dependency — the suite must
  pass on a machine that has never seen the target.
- **D-18:** **OBS-D-02 gets a lock-in test** even though it needs no repair: a regression test
  asserting the `packages/shared` → `apps/frontend` / `apps/backend` runtime edges resolve from
  `workspace:*` dependencies, so the OBS-03 refutation cannot silently regress. It is recorded as an
  evidence-backed confirmation, not deleted (Phase-51 D-08).
- **D-19:** Each repair carries an explicit trace line to its OBS-D id and purpose tag. An
  observation with **no** repair must still terminate in either a lock-in test or a written
  evidence-backed confirmation — SC-5 admits no third outcome.

### Post-research decisions (locked after 52-RESEARCH.md surfaced the contract cost)

- **D-20 (supersedes D-08's shape only, not its intent):** the non-member manifest diagnostic is
  recorded by **extending the existing `excludedEntry.excluded` enum** in
  `contracts/harness/adoption/inventory.schema.json` with one new reason value — **not** by adding a
  parallel top-level `skipped` array. The schema is `additionalProperties: false` with an enumerated
  `required` list, so a new top-level key is the larger contract-shape change; an additive enum value
  reuses existing machinery. Both paths change the schema hash, so this remains a **contract-first**
  change: contract entry first, then `/contract-check` (check-jsonschema + RFC 8785 schema-hash drift
  gate) and the paired golden update. The contract **count stays 6** — NG-01 holds.
- **D-21 (resolves the D-15 open question):** the lock-sidecar declaration lives in **phase-local
  comparison scope**, mirroring Phase 51, where the `matches`/`unexpected_paths` logic was plan-inline
  rather than a shared tool. No write into the target's `.gitignore` (it is a governed disposition
  destination but is **not** marker-capable — there is no safe merge primitive against an existing
  target `.gitignore` today), and no pull-in of `manifest.schema.json`, which research confirmed has
  zero impact from this phase. No new surface — NG-01 holds.

### Claude's Discretion

- Exact fresh-worktree path and evidence sub-file naming.
- The new `excluded` enum value's literal name and any per-entry fields it implies (D-20).
- Synthetic pnpm fixture layout and where it lives, subject to D-17's "next to the tool" siting.
- How the lock-sidecar declaration is expressed (managed-artifact list vs comparison exclusion),
  provided `matches` becomes true without weakening the comparison for real unlisted writes.
- Plan decomposition and task ordering within the phase.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/adoption_scan/detect.py` — `_MANIFEST_KIND_BY_NAME` (`:46`) is the manifest-kind table to
  extend; `_dependencies_from_package_json` (`:273`) already discards version strings and matches by
  name, which is *why* OBS-03 was refuted. Do not "fix" it.
- `tools/memory_regen/package_facts.py:216` — produces the dependency edges SC-3 asserts.
- `tools/harness_config/loader.py:297` — `conventions_for()`, an injectable-pure function
  (`cfg`/`facts` params) that is fully testable without monkeypatch or a temp config.
- `tools/adoption_apply/apply.py:306` — `_apply_marker_merge`, the flock-guarded atomic
  read-merge-write; `tools/adoption_apply/tests/test_atomic_apply.py:267` is the existing comparison
  test to extend.

### Established Patterns
- Injectable-pure functions with optional `cfg`/`facts` so tests need no filesystem.
- The `"dir"`-key adapter comment convention: a deliberate deviation is documented inline with its
  review id (e.g. `WR-02 (48-REVIEW.md)`) — new repairs cite their OBS-D id the same way.
- Constitution plane (`contracts/`, `docs/adr/`, goldens) is human-gated; derived plane is
  regenerated, never hand-edited.

### Integration Points
- `harness/project.toml` `[[languages]]` — where the derived JS lint/test commands land in the
  target.
- The adoption artifact triple (`inventory.json` → `plan.json` → `manifest.json`) — the `skipped`
  diagnostic list and the lock-sidecar declaration both surface here.

</code_context>

<specifics>
## Specific Ideas

- OBS-03 is **refuted** and closed. `detect.py:273` is correct; spending any Phase-52 budget
  "repairing" pnpm `workspace:*` resolution is an explicit scope violation.
- STATE.md's carried note is authoritative: `conventions_for` has **no `lint` key at all** — plan for
  a shape change, not a value fill.
- Phase-51's `sk-proj-…` / `sk-ant-api03-…` secret-scan gap is recorded-only; it lives in Phase-51
  plan-inline checks, not a shipped gate, and is **not** in scope here.

</specifics>

<deferred>
## Deferred Ideas

- **MONO-12 / managed `/adopt` update semantics** — Phase 53. Phase 52 installs; re-run-as-update is
  explicitly the next phase's goal.
- **DEBT-01 `"dir"`-filter shared helper** — Phase 54 (surface reduction).
- **Second target repo (vocpage)** — Future Requirements; reproducibility check only after
  FeedbackOps adoption lands.
- **Non-pnpm workspace formats** (npm/yarn `workspaces`, Cargo, uv) — deliberately unbuilt until a
  real target needs one (D-09).

</deferred>
