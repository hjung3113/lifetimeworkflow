# Phase 40: Self-Gate Teardown - Context

**Gathered:** 2026-07-26
**Status:** Ready for planning
**Mode:** `--auto` — every gray area auto-resolved at the recommended option. Each decision below
records its rationale and the file it was verified against, so the SUMMARY can be judged against a
stated intent.

> **Roadmap repair performed during this session.** Phase 40 existed only as a summary bullet;
> `gsd-sdk query roadmap.get-phase 40` returned `malformed_roadmap` ("missing `#### Phase 40:` detail
> section"). The detail section was authored into `.planning/ROADMAP.md` from the summary bullet plus
> `.planning/research/v2.5-scoping-FINAL.md:87,97,156` and a live inventory of the tree before
> discussion continued. That section is now the phase's scope anchor.

<domain>
## Phase Boundary

Delete the **skill-registry self-gate** — `tools/skill_registry/` (611 LOC), the declaration file
`harness/skills/registry.lock`, the LANE-04 mirror test `tools/harness_lint/tests/test_skill_registry_lock.py`,
the CI job `registry-lock` and its `gate.needs` entry — so that no later v2.5 phase can delete a
skill and be blocked by a declaration *about* the skill tree.

This is the first pure-deletion phase of v2.5 and it **must precede every skill deletion** in phases
41, 43 and 44: `tools/skill_registry/registry.py:44,105-110` recomputes the skill surface from
`harness/skills/**` and fails on any diff against the committed lock.

Requirement: **CER-04** (`.planning/REQUIREMENTS.md:44`).
Roadmap entry: `.planning/ROADMAP.md` → `#### Phase 40: Self-Gate Teardown`.
Authority to delete is already ratified: `docs/adr/0012-ci-and-merge-as-decision-authority.md:96-97`
names this exact surface.

**IN scope:**
- `tools/skill_registry/` — `registry.py`, `__main__.py`, `__init__.py`, `pyproject.toml`,
  `tests/conftest.py`, `tests/test_skill_registry.py`.
- `harness/skills/registry.lock` (8462 bytes, 24 declared skills).
- `tools/harness_lint/tests/test_skill_registry_lock.py` (50 LOC).
- CI job `registry-lock` (`.github/workflows/ci.yml:275-303`, comment block included) **and** its
  entry in `gate.needs` (`.github/workflows/ci.yml:410`).
- `uv.lock` refresh (`uv.lock:198` — `source = { virtual = "tools/skill_registry" }`).

**OUT of scope:**
- Deleting any skill. Skill deletion starts in Phase 41. Phase 40 only removes what would block it.
- `tools/harness_lint/caps.py::EXPECTED_SKILLS` and its consumers — see D-03.
- Any other CI job, hook, contract, emitted artifact, command or agent.
- A replacement gate of any kind — see D-02 and the milestone's binding constraint.
- Prose scrub of `docs/explanation/agent-workflow-skillset-design-guide.md` — see D-05.
</domain>

<decisions>
## Implementation Decisions

### Commit shape

- **D-01 — One atomic commit for the whole teardown.** The package deletion, the lock deletion, both
  gate tests, the CI job, the `gate.needs` entry and the refreshed `uv.lock` land together.
  *Rationale:* every intermediate split is a broken tree. Deleting the job before its `needs` entry
  leaves `gate` depending on a job GitHub Actions cannot resolve; deleting the package before
  `uv.lock` is refreshed breaks `uv sync --all-packages` for every other job. Milestone ordering
  rules (5) and (8) both mandate same-commit for exactly these two pairs.

### The guarantee being dropped

- **D-02 — No replacement gate. Record the loss; do not re-mechanize it.** The milestone's binding
  constraint is explicit ("the surface may not grow without retiring at least as much"), and
  ADR-0012 makes CI + the merge the authority.
  *What actually survives after teardown* (verified this session, so the plan does not overstate the
  loss):
  - a skill being **added or removed by name** is still caught — `tools/harness_lint/caps.py:137`
    `EXPECTED_SKILLS`, asserted by `tools/harness_emit/validate.py:182-183` and
    `tools/harness_emit/tests/test_emit_determinism.py:100-104`;
  - a `harness/` edit that was **not re-emitted** is still caught by CI `emit-drift`
    (`ci.yml:251-263`).
  - *Genuinely lost:* a **description rewrite or an authored `references/` file change inside an
    existing skill** that IS re-emitted in the same commit — it re-emits cleanly, passes
    `emit-drift`, and silently changes agent routing. This is scoping-FINAL risk 4
    (`.planning/research/v2.5-scoping-FINAL.md:156`) and is **accepted**, not mitigated. The plan
    must state it in the SUMMARY rather than quietly dropping it.

### Scope of the word "self-gate"

- **D-03 — `caps.py::EXPECTED_SKILLS` stays. It is not the registry lock.** The lock is a
  *content* declaration (per-skill description digest, source-file digests, emitted target paths in
  both runtimes, the disciplines naming it — Phase 37 D-09/D-11). `EXPECTED_SKILLS` is a *name-set*
  anti-sprawl assertion consumed by the emitter's own validator.
  *Rationale:* milestone ordering rule (6) already requires every skill add-or-delete to edit
  `caps.py` in the same commit, and Phase 45 owns the final frozenset sweep. Deleting
  `EXPECTED_SKILLS` here would remove the last name-level guard at precisely the moment phases
  41/43/44 start deleting skills — a net loss of safety for no CER-04 benefit, and it would drag
  `validate.py` + `test_emit_determinism.py` into a phase scoped as pure deletion.

### uv workspace mechanics

- **D-04 — Remove the directory, then refresh the lockfile; do not touch the members glob.**
  `pyproject.toml:34` is `members = ["tools/*"]` — a glob, so removing `tools/skill_registry/`
  removes the member with no `pyproject.toml` edit. No `exclude` entry is added (`exclude` at
  `pyproject.toml:35` exists only for `tools/bootstrap`, a shell-only dir with no `pyproject.toml`).
  Refresh with `uv lock`, then prove with `uv sync --all-packages`. Adding an `exclude` entry would
  leave a name of a deleted thing in the manifest — the exact residue Phase 45 has to scrub.

### Docs and prose

- **D-05 — Leave `docs/explanation/agent-workflow-skillset-design-guide.md:564,595,663` alone.** Its
  `registry.lock` is a *different, never-implemented* concept (provenance for vendored external
  skills: source repo, commit, license, local diff), not this drift gate. Phase 45 owns the prose
  scrub of surfaces this milestone deletes; touching an unrelated doc here widens a deletion-only
  phase.

### Pre-flight safety proof

- **D-06 — Prove the referent set before deleting, and record the sweep.** The plan opens with a
  recorded `grep -rn "skill_registry\|registry-lock\|registry\.lock"` over `tools/ libs/ harness/
  .github/ docs/ pyproject.toml uv.lock .claude/ .opencode/` (excluding `.git/`, `.planning/`,
  `__pycache__/`, and `.claude/get-shit-done/`), and the same grep re-run at the end must return
  only the ADR-0012 and `docs/explanation/...` lines that D-05 keeps.
- **D-07 — Phase 41's "unbind before delete" rule does NOT apply here — verified, not assumed.**
  `docs/doc-dependencies.toml` holds 8 `[[binding]]` rows; **none** names `tools/skill_registry`,
  `harness/skills/registry.lock`, or `.github/workflows/ci.yml` as a source, and none targets a file
  this phase deletes. So `tools.docs_guard` cannot classify anything `BROKEN` from this teardown and
  the `docs-guard` CI job stays green. The plan should re-run this check rather than trusting this
  line, because it is the single failure mode that would red the fan-in gate.

### Verification method

- **D-08 — Verify by absence plus the four existing gates; add no new test.** Acceptance evidence:
  (1) the closing grep from D-06; (2) `uv run pytest` green with no collection error;
  (3) `uv sync --all-packages` resolves; (4) `uv run python -m tools.harness_emit` leaves
  `git status --porcelain` empty over the emit-drift path set (`ci.yml:262`) — deleting a
  *declaration about* `harness/skills/` must not move either emitted tree; (5) contract-drift clean
  (this phase touches no `contracts/` entry and no `tools/contract_hash/hash.py` path list);
  (6) `uv run python -m tools.ruff_baseline` still exits 0 (it only ratchets down; the baseline holds
  no `skill_registry` entries, so deletion cannot raise it).

### Claude's Discretion

Auto mode selected the recommended option in every area above. Genuinely free for the planner:
the ordering of steps *inside* the single commit, the exact wording of the SUMMARY's
accepted-consequence paragraph, and whether the CI comment block at `ci.yml:275-293` is removed
wholesale or partially. None of these change the delivered surface.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decision authority (read first)
- `docs/adr/0012-ci-and-merge-as-decision-authority.md` §"Phase 40 — Self-Gate Teardown"
  (`:96-97`) — the ratified authority to delete this exact surface; CI + the merge are the authority.
- `.planning/ROADMAP.md` → `#### Phase 40: Self-Gate Teardown` — scope, non-goals, success criteria.
- `.planning/ROADMAP.md` → v2.5 header, "Ordering rules that must hold inside every phase" — rules
  (5) CI job + `gate.needs` same commit, (6) `harness/` change re-emits + skill add/delete edits
  `caps.py`, (7) never hand-edit `.claude/` or `.opencode/`, (8) a deleted `harness/` artifact's
  dedicated gate test dies in the same commit.
- `.planning/REQUIREMENTS.md:44` — CER-04 as written.

### Why this surface exists (what is being undone)
- `.planning/phases/37-capability-routing-registry-lock-v2-4-c/37-CONTEXT.md` D-09/D-10/D-11/D-12 —
  the original design intent of the lock, its hashing contract, and why it was a separate CI job.
  Required reading for D-02: it states precisely what the lock caught that `emit-drift` does not.
- `.planning/research/v2.5-scoping-FINAL.md:87` (the phase's one-line scope), `:97` (ordering rule 1),
  `:156` (accepted risk 4 — silent routing change after the lock is gone).

### The code being deleted
- `tools/skill_registry/registry.py` — `LOCK_PATH` (`:42`), the recompute-vs-lock diff
  (`:44,105-110`), `build_registry` (`:149`), `load_lock` (`:163-169`).
- `tools/skill_registry/__main__.py` — the `--check` / `--write` CLI (`:26,31,37,64,66,86`).
- `tools/skill_registry/tests/test_skill_registry.py` (262 LOC), `tools/skill_registry/tests/conftest.py`
  (21 LOC — the repo-root `sys.path` shim every virtual workspace member needs).
- `tools/harness_lint/tests/test_skill_registry_lock.py` (50 LOC) — the in-suite mirror of the CI job.
- `harness/skills/registry.lock:224` — `"tool": "tools.skill_registry"`.

### The gates that must stay green
- `.github/workflows/ci.yml:275-303` (`registry-lock`, delete) and `:410` (`gate.needs`, edit).
- `.github/workflows/ci.yml:251-263` (`emit-drift`) and `:177-185` (`core-suite`) — untouched, must
  stay green.
- `docs/doc-dependencies.toml` — 9 `[[binding]]` rows; D-07's no-BROKEN proof re-runs against this.
- `tools/harness_lint/caps.py:137` (`EXPECTED_SKILLS`), `tools/harness_emit/validate.py:182-183`,
  `tools/harness_emit/tests/test_emit_determinism.py:100-104` — the surviving name-level guard
  (D-03), untouched.
- `pyproject.toml:29-35` (`[tool.uv.workspace]` members glob + exclude), `uv.lock:198`.

### Repo working rules
- `AGENTS.md` (root) — nearest-wins agent rules; contract-first, constitution-plane-is-gated,
  derived-not-hand-edited.
- `harness/skills/two-plane-memory/SKILL.md` — which files are human-owned vs auto-regenerated.

</canonical_refs>

<code_context>
## Existing Code Insights

All citations read from source this session (2026-07-26).

### Reusable assets
- **No new code is written in this phase.** The only "asset" is the existing red→green evidence
  shape: `uv run pytest`, `uv run python -m tools.harness_emit`, `uv run python -m tools.contract_drift`,
  `uv run python -m tools.ruff_baseline`.
- `tools/lifecycle_eval/tests/conftest.py` and `tools/harness_lint/conftest.py` are the sibling
  `sys.path` shims that `tools/skill_registry/tests/conftest.py:18` mirrors — they stay, so removing
  one member does not disturb collection for the others.

### Established patterns that constrain this phase
- **Fan-in `needs` is a hard list, not a glob** (`ci.yml:410`). A deleted job MUST be removed from it
  in the same commit or the workflow fails to resolve. This is milestone ordering rule (5).
- **Workspace members are a glob** (`pyproject.toml:34` `members = ["tools/*"]`) but `uv.lock` pins
  each member explicitly (`uv.lock:198`). The glob needs no edit; the lock does.
- **`harness/skills/registry.lock` is NOT an emitted artifact** — `tools/harness_emit/emit-manifest.json`
  contains zero `registry` matches, and no `.opencode/` or `.claude/` path references it. Deleting it
  must therefore produce an empty `emit-drift` diff; a non-empty one means something else moved.
- **Nothing outside `tools/` imports the package.** The complete importer set is
  `tools/skill_registry/**` itself plus `tools/harness_lint/tests/test_skill_registry_lock.py:17`.
  `tools/skill_registry/registry.py:21` merely *mentions* `caps.EXPECTED_SKILLS` in a docstring — it
  is a comment, not an import, so D-03's decision to keep `EXPECTED_SKILLS` creates no dangling edge.

### Integration points (all removals, no additions)
- `.github/workflows/ci.yml` — one job block removed, one `needs` list edited.
- `uv.lock` — one virtual-member entry removed by regeneration.
- Everything else is file deletion.

</code_context>

<specifics>
## Specific Ideas

- **State the dropped guarantee in the SUMMARY, in one sentence, in the plain form:** after this
  phase, editing a skill's `description` changes agent routing with no gate objecting. A deletion
  phase that quietly loses a guarantee is how the next milestone re-invents it.
- **The teardown is the enabling step, not the value.** Phase 40's value is measured in Phase 41:
  the first skill deletion must not require a lock rewrite. Plan the verification so that fact is
  demonstrable, e.g. by noting which command Phase 41 no longer has to run
  (`uv run python -m tools.skill_registry --write`).
- **Do not hand-edit `.claude/` or `.opencode/`** (ordering rule 7). If either tree moves, the cause
  is `harness/`, and the fix is a re-emit — not an edit.
- **Deletion-only means the diff is deletion-only.** If the plan produces a net-new file anywhere
  outside `.planning/`, that is a scope defect, not a detail.

</specifics>

<deferred>
## Deferred Ideas

- **Locking the command and agent surfaces** the way LANE-04 locked skills (carried from
  `37-CONTEXT.md` deferred list) — **now obsolete-by-deletion.** v2.5 removes the skill lock; the
  generalization must not be revived. Recorded here so a future reader sees it was closed, not lost.
- **A cheap replacement for the description-digest guarantee** (e.g. folding a description hash into
  an existing gate rather than a new job) — deliberately NOT taken (D-02). If it is ever revisited,
  it needs a new ADR, because ADR-0012 ratified CI + the merge as the authority instead.
- **`caps.py::EXPECTED_SKILLS` removal** — belongs to Phase 45's frozenset sweep, not here (D-03).
- **Prose scrub of `docs/explanation/agent-workflow-skillset-design-guide.md`** — Phase 45 (D-05),
  and only if that doc's unrelated vendored-skill `registry.lock` concept is judged confusing.

</deferred>

---

*Phase: 40-Self-Gate Teardown*
*Context gathered: 2026-07-26*
