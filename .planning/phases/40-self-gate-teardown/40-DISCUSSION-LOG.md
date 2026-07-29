# Phase 40: Self-Gate Teardown - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-26
**Phase:** 40-self-gate-teardown
**Mode:** `--auto --chain` — no interactive prompts; the recommended option was auto-selected in
every area and logged below.
**Areas discussed:** Commit shape, Dropped guarantee, Scope of "self-gate", uv workspace mechanics,
Docs and prose, Pre-flight safety proof, Verification method

---

## Pre-discussion blocker: malformed roadmap

`gsd-sdk query init.phase-op 40` returned `phase_found: false`;
`gsd-sdk query roadmap.get-phase 40` gave `malformed_roadmap` — "Phase 40 exists in summary list but
missing `### Phase 40:` detail section".

| Option | Description | Selected |
|--------|-------------|----------|
| Stop and ask the user to run `/gsd:phase` | Correct CRUD entry point, but blocks a `--auto --chain` run on a mechanical gap | |
| Author the detail section inline from the summary bullet + design docs + a live tree inventory | Unblocks the chain; the content is derived, not invented | ✓ |
| Discuss without a roadmap section | Leaves no scope anchor for the planner | |

**Choice:** authored `#### Phase 40: Self-Gate Teardown` into `.planning/ROADMAP.md` (goal,
requirements CER-04, scope with file-level citations, non-goals, accepted consequence, 6 success
criteria), sourced from the summary bullet, `.planning/research/v2.5-scoping-FINAL.md:87,97,156`,
`docs/adr/0012-*.md:96-97`, and a live inventory read this session.
**Notes:** `roadmap.get-phase 40` returns `found: true` after the repair.

---

## Commit shape

| Option | Description | Selected |
|--------|-------------|----------|
| One atomic commit | Package, lock, both gate tests, CI job, `gate.needs`, `uv.lock` together | ✓ |
| Staged commits (code, then CI, then lock) | Smaller reviewable steps | |
| Two commits: deletion, then lockfile refresh | Separates generated from authored change | |

**Choice:** one atomic commit (D-01).
**Notes:** every split leaves a broken intermediate tree — `gate.needs` naming an unresolvable job,
or `uv sync --all-packages` failing for every other job. Milestone ordering rules (5) and (8)
independently mandate same-commit for these pairs.

---

## The guarantee being dropped

| Option | Description | Selected |
|--------|-------------|----------|
| No replacement; record the loss in the SUMMARY | Honours the binding constraint and ADR-0012 | ✓ |
| Fold a description hash into an existing gate | Cheaper than a job, but still a new mechanism | |
| Replace with a lint-only advisory check | Precedent says an always-advisory gate trains people to ignore it (`ci.yml:188-190`) | |

**Choice:** no replacement (D-02).
**Notes:** the plan must state what actually survives — `caps.EXPECTED_SKILLS` still catches a skill
added or removed *by name*; `emit-drift` still catches a `harness/` edit that was not re-emitted.
Genuinely lost: a description or `references/` change inside an existing skill that IS re-emitted —
scoping-FINAL risk 4, accepted, not mitigated.

---

## Scope of the word "self-gate"

| Option | Description | Selected |
|--------|-------------|----------|
| Delete the registry lock only; keep `caps.EXPECTED_SKILLS` | CER-04 as written | ✓ |
| Also delete `EXPECTED_SKILLS` and its two consumers | "Maximum de-ceremony" reading | |
| Defer the decision to Phase 45 | Leaves the planner without a boundary | |

**Choice:** keep `EXPECTED_SKILLS` (D-03).
**Notes:** it is a name-set assertion, not the content lock. Ordering rule (6) already makes every
skill-deleting phase edit `caps.py`, and Phase 45 owns the frozenset sweep. Deleting it here would
remove the last name-level guard exactly when phases 41/43/44 begin deleting skills.

---

## uv workspace mechanics

| Option | Description | Selected |
|--------|-------------|----------|
| Remove the dir, `uv lock`, prove with `uv sync --all-packages` | Members is a glob; nothing else to edit | ✓ |
| Add `tools/skill_registry` to `exclude` | Would leave a deleted name in the manifest | |
| Hand-edit `uv.lock:198` | Generated file; regeneration is the contract | |

**Choice:** glob untouched, lockfile regenerated (D-04).
**Notes:** `pyproject.toml:35`'s `exclude` exists only for `tools/bootstrap`, a shell-only directory
with no `pyproject.toml` — not a precedent for deleted members.

---

## Docs and prose

| Option | Description | Selected |
|--------|-------------|----------|
| Leave `agent-workflow-skillset-design-guide.md` alone | Its `registry.lock` is a different, unimplemented concept | ✓ |
| Scrub its three mentions now | Widens a deletion-only phase into prose editing | |

**Choice:** leave it (D-05).
**Notes:** that doc's `registry.lock` is vendored-external-skill provenance (source repo, commit,
license, local diff), not this drift gate. Phase 45 owns prose scrub of deleted surfaces.

---

## Pre-flight safety proof

| Option | Description | Selected |
|--------|-------------|----------|
| Recorded grep sweep before and after, plus an explicit binding check | Makes the referent set evidence, not assumption | ✓ |
| Trust the inventory captured in CONTEXT.md | Cheaper, but the binding check is the one failure mode that reds the fan-in gate | |

**Choice:** recorded sweep + re-run of the binding check (D-06, D-07).
**Notes:** verified this session — `docs/doc-dependencies.toml` holds 8 `[[binding]]` rows and none
names `tools/skill_registry`, `harness/skills/registry.lock`, or `.github/workflows/ci.yml` as a
source, so `docs_guard` cannot classify anything `BROKEN`. Phase 41's "unbind before delete" rule
does not apply here. The plan re-runs the check rather than trusting this line.

---

## Verification method

| Option | Description | Selected |
|--------|-------------|----------|
| Verify by absence + the four existing gates | Deletion-only phase; a new test would be new surface | ✓ |
| Add a test asserting the package is gone | A gate against re-adding something nobody is re-adding | |

**Choice:** absence + existing gates (D-08).
**Notes:** six evidence items — closing grep, `uv run pytest`, `uv sync --all-packages`,
`tools.harness_emit` leaving `git status --porcelain` empty over the emit-drift path set,
contract-drift clean, `tools.ruff_baseline` exit 0.

---

## Claude's Discretion

Auto mode selected the recommended option in every area. Left genuinely open to the planner: step
ordering inside the single commit, the wording of the SUMMARY's accepted-consequence paragraph, and
whether `ci.yml:275-293`'s comment block is removed wholesale or partially.

## Deferred Ideas

- Locking the **command** and **agent** surfaces (carried from `37-CONTEXT.md`) — now
  obsolete-by-deletion; recorded as closed, not lost.
- A cheap replacement for the description-digest guarantee — deliberately not taken; reviving it
  needs a new ADR, since ADR-0012 ratified CI + the merge as the authority instead.
- `caps.py::EXPECTED_SKILLS` removal — Phase 45's frozenset sweep.
- Prose scrub of `docs/explanation/agent-workflow-skillset-design-guide.md` — Phase 45, and only if
  its unrelated `registry.lock` concept is judged confusing.
