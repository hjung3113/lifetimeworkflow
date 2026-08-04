# Phase 51: Real-Target Observation Baseline - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved with recommended defaults; see 51-DISCUSSION-LOG.md)

<domain>
## Phase Boundary

Run the **current, unmodified** harness against an isolated git worktree of the real FeedbackOps
monorepo and capture reproducible evidence of what it does — before any repair is designed.

**Delivers:** an isolated worktree, a baseline `/adopt` discover → draft → apply attempt against it,
a byte-unchanged proof for the original `develop` checkout, a defect record (symptom · reproducible
path · code location) for every observed adoption defect, and a reproducible verdict on the OBS-03
pnpm `workspace:*` hypothesis.

**Does NOT deliver:** any repair, any source edit under `tools/`, any new contract, command, skill,
gate or CI job. The baseline attempt is *permitted to fail* — failure is the evidence. Repairs are
Phase 52 (OBS-02), and Phase 52 starts from a **freshly created** worktree, not this one's leftovers.
</domain>

<decisions>
## Implementation Decisions

### Worktree provisioning + isolation proof

- **D-01:** The isolated target is a **git worktree of `~/Desktop/2026/FeedbackOps`, created outside
  that checkout's directory** — e.g. `~/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline` — via
  `git -C ~/Desktop/2026/FeedbackOps worktree add --detach <path> <develop-SHA>`. Detached HEAD, so
  no branch of the real repo can be advanced by the run. Not a full clone (a clone hides worktree-vs-
  checkout interactions the adoption run must be observed against), and never a path nested inside
  the `develop` working tree.
- **D-02:** Pin the observed commit: record `git -C <target> rev-parse HEAD` (today `1d1c8ed`,
  branch `develop`) at the start of the record. Every command in the evidence log is replayable
  against that SHA.
- **D-03:** **Byte-unchanged proof is captured before AND after the run**, over the original
  `develop` checkout, as three artifacts: (a) `git status --porcelain=v2 --untracked-files=all`,
  (b) `git rev-parse HEAD` + `git ls-files -s | sha256sum` (tracked index digest), (c) a digest of
  the untracked-path *set* (names only — `node_modules/`, `minio_data/` etc. are excluded from
  content hashing so the proof stays fast and deterministic). Before/after equality of all three is
  the RTA-01 precursor evidence. Any inequality is itself a recorded defect, not a silent retry.
- **D-04:** **Disposal:** after the evidence record is complete, the worktree is removed
  (`git worktree remove --force`) and its residue discarded. Evidence artifacts live in this repo's
  phase directory, never in the target. Phase 52 re-creates a clean worktree from scratch.
- **D-05:** Zero writes to FeedbackOps product code. `/adopt apply` writing harness artifacts into
  the *worktree* is in scope; anything touching the target's application source is a defect to
  record, not an accepted behavior.

### Evidence record: location + shape

- **D-06:** **Location** — `.planning/phases/51-real-target-observation-baseline/`:
  - `51-BASELINE-EVIDENCE.md` — the human-readable record (the OBS-01 deliverable).
  - `evidence/` — raw captured outputs: `inventory.json`, `plan.json`, `manifest.json` produced by
    the run, plus per-command `stdout`/`stderr`/exit-code capture and the before/after isolation
    digests.
  No evidence goes into `contracts/`, `docs/adr/`, or `docs/reference/` — this phase adds **no**
  constitution-plane member and **no** derived-plane generator (NG-01).
- **D-07:** **Per-defect shape** — one section per defect, id `OBS-D-NN`, with exactly these fields:
  `symptom` (what the run produced vs what the purpose requires) · `reproduction` (exact
  `python -m ...` argv, cwd, target SHA, harness SHA, exit code) · `code location` (`path:line`
  citation into this repo) · `purpose tag` (①②③④ or "outside purpose") · `proposed disposition`
  (repair-in-52 / no-change-evidence-backed). A summary table at the top indexes all ids.
- **D-08:** The purpose tag written in Phase 51 is a **proposal, not a binding triage**. Phase 52
  (OBS-02) makes the repair/no-change decision; observations that need no change stay in the record
  as evidence-backed confirmations rather than being deleted.
- **D-09:** Markdown + committed raw JSON only. **No new JSON Schema, no new contract entry, no new
  parser** for the evidence format — the record is read by humans and by Phase 52's planner.

### Baseline run depth + failure policy

- **D-10:** **Push all three stages independently** (discover → draft → apply); do not stop at the
  first failure. When a stage fails, record it and attempt the next stage with whatever artifacts
  exist. If a downstream stage is genuinely un-runnable because its input was never produced, that
  block is itself recorded as a defect (`blocked-by: OBS-D-NN`).
- **D-11:** **No repairs, no workarounds, no hand-edited inputs during the baseline.** Not one line
  of `tools/` changes in this phase. Hand-editing a `plan.json` to get `apply` to run would destroy
  the evidence — record the block instead.
- **D-12:** After the apply attempt, also run the **read-only downstream observations** in the
  worktree — package facts (`tools.memory_regen.package_facts`) and nearest-wins convention
  resolution (`tools.harness_config.loader:conventions_for`) — even though RTA-03/RTA-04 are Phase
  52 requirements. These are observations, not repairs, and they are where the ②③ purpose defects
  will actually surface.
- **D-13:** **Reproducibility metadata is mandatory** in the record header: harness commit SHA,
  target commit SHA, `python --version`, `uv --version`, `pnpm --version` if invoked, working
  directory for each command, and the literal argv. A reader must be able to replay the run without
  guessing.

### OBS-03 pnpm `workspace:*` verdict

- **D-14:** **Evidence-first from the real run**, not from a synthetic fixture. The verdict is read
  off the run's own `inventory.json` + generated package facts: **confirmed** if a `workspace:*`
  dependency is recorded as a version string (or the `packages/shared` → `apps/frontend` /
  `apps/backend` edges are absent), **refuted** if the workspace edge is already recorded correctly.
  A refutation closes OBS-03 successfully and is stated as such — it is a milestone output, not a
  failure.
- **D-15:** The verdict lives in a dedicated `## OBS-03 verdict` section of
  `51-BASELINE-EVIDENCE.md`, quoting the **literal output excerpt** that decides it, plus the
  `path:line` of the implicated code (current suspicion: `tools/adoption_scan/detect.py:46-50` and
  `_dependencies_from_package_json`).
- **D-16:** Treat **member discovery** and **dependency-edge recording** as two potentially distinct
  defects. `pnpm-workspace.yaml` is absent from `_MANIFEST_KIND_BY_NAME`
  (`tools/adoption_scan/detect.py:46-50`, which knows only `pyproject.toml` · `package.json` ·
  `go.mod` · `Cargo.toml`), so members may be found *only* via their `package.json` files — a
  different failure from `workspace:^` being swallowed as a version string. Record them under
  separate `OBS-D-NN` ids even if one masks the other.
- **D-17:** No fixture is added to this repo in Phase 51. If a minimal reproduction is useful, its
  *shape* is described in the record; committing it is a Phase 52 decision, bound to a regression
  test for an actual repair.

### Claude's Discretion

- Exact worktree path, evidence sub-file naming, and the ordering of commands within a stage.
- Whether the raw capture is one log file per command or one combined transcript, as long as every
  command's argv, cwd and exit code are recoverable.
- How many `OBS-D-NN` sections to split a compound failure into, guided by D-16's "separate causes
  get separate ids" rule.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone scope + boundary
- `.planning/ROADMAP.md` §"v2.7 Real-Target Adoption" and §"Phase 51: Real-Target Observation
  Baseline" — the four success criteria this phase is judged against; the binding rule that Phase 51
  must finish its evidence record before any repair phase begins.
- `.planning/REQUIREMENTS.md` — OBS-01 and OBS-03 (this phase); RTA-01..04 / OBS-02 (Phase 52, only
  observed here); NG-01 (no growth in commands 19 / skills 8 / contracts 6 / CI jobs / gates).
- `.planning/PROJECT.md` §106 "Why this and not more machinery" and §194-201 — the owner's four-part
  purpose ①②③④ and the binding no-expansion constraint every defect is tagged against.
- `.planning/STATE.md` §"Blockers/Concerns" — the carried MONO-12 block that naming this real target
  is meant to release.

### The code under observation
- `tools/adoption_scan/detect.py` — manifest/language detection; `_MANIFEST_KIND_BY_NAME`
  (lines 46-50) is the OBS-03 primary suspect.
- `tools/adoption_scan/{scan.py,plan.py,destinations.py,cli.py}` — discover stage: inventory → plan →
  manifest.
- `tools/adoption_apply/{batch.py,apply.py,cli.py}` — draft/apply stages: task-local batch,
  atomic/collision-safe application, constitution-plane refusal.
- `tools/memory_regen/package_facts.py` — the dependency-edge output RTA-03 will be judged on;
  `package.json` handling at line ~128.
- `tools/harness_config/loader.py:conventions_for()` — nearest-wins convention profile resolution
  (RTA-04 observation).

### Runbook + governing decisions
- `harness/commands/adopt.md` — the exact sub-verb argv forms (`discover` / `draft` / `apply`) the
  baseline must invoke; discovery is read-only, apply refuses constitution-plane destinations.
- `harness/skills/brownfield-adoption/SKILL.md` — the full discover → draft → apply runbook and the
  ADR-0012 rule that review happens at the PR, not as an in-pipeline gate.
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` — CI + the merge are the decision authority;
  do not add in-session enforcement to compensate for anything observed here.
- `AGENTS.md` (root) — nearest-wins agent rules; constitution-plane-is-gated, derived-not-hand-edited.

### Target
- `~/Desktop/2026/FeedbackOps` — pnpm workspace + turbo; members root · `packages/ui` ·
  `packages/shared` · `apps/frontend` · `apps/backend`; branch `develop` @ `1d1c8ed` at scoping time.
  Its `pnpm-workspace.yaml`, `package.json`, and per-package manifests are the observation inputs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`/adopt` is already a thin macro** over `tools.adoption_scan` / `tools.adoption_apply` — the
  baseline invokes the shipped pipeline verbatim (`python -m tools.adoption_scan <args>`,
  `python -m tools.adoption_apply draft|apply <args>`). Nothing new is written to run the baseline.
- **`--out` is required and target-external** on discover, and draft confines artifacts to a batch
  root — so evidence capture already has a sanctioned, non-target destination.
- **`apply` structurally refuses constitution-plane destinations** (`contracts/`, `docs/adr/`,
  `docs/glossary.md`) before any write; that refusal path is part of what the baseline observes, not
  something to re-verify by hand.
- **`git worktree`** provides the isolation primitive; no bespoke sandbox is needed.

### Established Patterns
- **Evidence over assertion:** a defect record without a reproducible path and a `path:line` code
  location does not satisfy OBS-01.
- **No-growth constraint (NG-01):** this phase may add planning artifacts only. Any temptation to add
  a schema, gate, fixture or command to "hold the evidence" is out of bounds.
- **Refutation is a valid outcome** (OBS-03 is written as a hypothesis) — the record must be able to
  say "already correct" without that reading as phase failure.
- **Two-plane memory:** evidence is neither constitution nor derived plane; it is `.planning/` phase
  material and stays there.

### Integration Points
- Phase 51's `51-BASELINE-EVIDENCE.md` is the **sole input contract** for Phase 52: every Phase-52
  change must trace to an `OBS-D-NN` id in it. Ids are therefore stable and must not be renumbered.
- Downstream observation commands (`package_facts`, `conventions_for`) run against the worktree after
  apply; their output excerpts become the RTA-03/RTA-04 baseline Phase 52 measures improvement from.

</code_context>

<specifics>
## Specific Ideas

- The original `develop` checkout has large untracked directories (`node_modules/`, `minio_data/`) —
  the byte-unchanged proof hashes the **tracked index** and the untracked **path set**, not untracked
  content, so the check stays deterministic and fast (D-03).
- Current OBS-03 suspicion is concrete and citable: `_MANIFEST_KIND_BY_NAME` in
  `tools/adoption_scan/detect.py:46-50` recognizes four manifest kinds and `pnpm-workspace.yaml` is
  not among them; `_dependencies_from_package_json` may accept `workspace:^` as a version string.
  The baseline must confirm or refute this from real output rather than from reading the code.
- The FeedbackOps checkout is all JS/TS — `_LANGUAGE_BY_EXTENSION` covers `.ts/.tsx/.js/.jsx`, so a
  language-detection failure would be a *surprise* and worth an explicit note either way.

</specifics>

<deferred>
## Deferred Ideas

- **Any repair of an observed defect** — Phase 52 (OBS-02), bounded to purposes ①②③④ and each with a
  regression test.
- **Committing a minimal pnpm-workspace reproduction fixture** — Phase 52, paired with the repair it
  regression-tests (D-17).
- **Managed install→update behavior for `/adopt`** (manifest of managed files, no-op re-run,
  divergence conflict report) — Phase 53 (MONO-12).
- **DEBT-01 shared `"dir"`-filter helper** between `conventions_for()` and `impact.py:report()` —
  Phase 54.
- **Second target repo (vocpage)** for reproducibility of the repairs — explicitly out of v2.7 until
  the FeedbackOps adoption completes.
- **Changing FeedbackOps product code** — out of milestone scope entirely.

</deferred>

---

*Phase: 51-Real-Target Observation Baseline*
*Context gathered: 2026-07-31*
