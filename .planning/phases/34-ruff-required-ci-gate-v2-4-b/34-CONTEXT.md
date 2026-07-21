# Phase 34: Ruff as a Required CI Gate - Context

**Gathered:** 2026-07-22
**Status:** Ready for planning
**Mode:** Autonomous — the phase brief fixed the shape (exclude the vendored tree, ratchet the
remainder, wire a blocking job, prove it fails). Grey areas below are decided at the executor's
discretion; every decision cites a measurement in `34-RESEARCH.md`.

<domain>
## Phase Boundary

`ruff check` becomes a **required CI gate**. Today it is not a gate anywhere — zero hits for
`ruff` across `.github/`, and the advisory `/lint` command is permanently red.

Requirement: DEBT-01 (`.planning/REQUIREMENTS.md:53-56`).
Roadmap: `.planning/ROADMAP.md:125-127`.

**IN scope:** the vendored-tree `extend-exclude`; the ruff-classified *safe* autofixes; a
ratcheting per-rule baseline held by a tested tool under `tools/`; a blocking `lint` job in
`ci.yml` wired into `gate.needs`; a recorded fail→pass observation of the gate.

**OUT of scope:** fixing the 403 genuine findings (the requirement says *held*, not fixed);
`ruff format --check` (25 files would reformat — carried, see D-08); widening or narrowing
`[tool.ruff.lint] select`; a pre-commit mirror (no `.pre-commit-config.yaml` exists).

## Constitution-plane note

This phase writes **nothing** under `contracts/`, `docs/adr/`, `golden/`, or `docs/glossary.md`,
and needs no ADR: it adds a CI job and a lint baseline, neither of which is an architectural
decision that supersedes an existing one. `drafts/` is therefore expected to stay empty.

</domain>

<decisions>
## Implementation Decisions

| # | Grey area | Decision | Rationale |
|---|---|---|---|
| D-01 | Which number is true — 617 (docs) or something else | **620**, measured with `--no-cache`. The docs' 617 is a **stale-cache artifact**; two runs of the identical warm-cache command disagreed by 3 during research. | `34-RESEARCH.md` §1. Reproduced ×3 cold, stable. |
| D-02 | Cache handling in the gate | The tool always passes `--no-cache`. | A gate whose verdict depends on `.ruff_cache/` state goes green locally (warm) and red in CI (always cold) for the same code. Non-negotiable; without it the ratchet is noise. |
| D-03 | How the tool reads ruff | `[sys.executable, "-m", "ruff", ...]` with `--output-format=json`, `cwd=REPO_ROOT`. | `python -m ruff` cannot pick up an ambient ruff off `PATH`. JSON gives `code` per diagnostic; `--statistics` is a right-aligned text table and disagreed with JSON on a warm cache. Ruff exit 1 = findings, 2 = usage error — the tool must not read 2 as "clean". |
| D-04 | Baseline keying | **Per-rule totals, repo-wide.** Not per-(file, rule). | Per-(file, rule) reads every file rename as an increase, which forces a `--update` that can raise counts — the escape hatch that makes a ratchet decorative. Per-rule is rename-proof, which lets `--update` be structurally incapable of raising a count. Recorded limit: a one-for-one same-rule swap between two files passes. |
| D-05 | New rule codes | A code absent from the baseline is baseline **0** → fails on first appearance. | A ruff bump that adds an `E`/`F`/`I`/`UP`/`B` check must be a visible decision, not a silent absorption. |
| D-06 | `--update` semantics | Rewrites the baseline, but **refuses with exit 3 if any rule's count would increase**. | Mirrors the repo's existing posture: `tools/docs_guard` never raises its own `uncovered_max`/`binding_min` either. Growing the baseline requires hand-editing a committed JSON file — visible in review. |
| D-07 | Which findings to fix now | Only ruff-classified **safe** fixes (`--fix`, never `--unsafe-fixes`): 24 of them — I001×15, F401×6, UP017×2, UP034×1. Everything else is baselined. | The brief says fix only what is trivially safe. The 3 hidden unsafe fixes and the semantically-loaded B904/B905/B007/F841 are deliberately left in the baseline. |
| D-08 | `ruff format --check` | **Out of scope, recorded as carried debt.** 25 files would reformat. | DEBT-01 names `ruff check`. Reformatting 25 files now would produce a large mechanical diff colliding with in-flight phases 30–33. |
| D-09 | CI job name and shape | Job **`lint`**, modelled on `docs-guard`: tool CLI as the gate + that tool's unit tests. Added to `gate.needs`. | `docs-guard` is the closest analogue in the file — a tool whose exit code *is* the verdict. |
| D-10 | Does the job run bare `ruff check .`? | **No** — the ratchet CLI is the gate. A bare check would make the job permanently red, which is the same non-gate as no job. The bare check becomes a step when the baseline reaches zero. | The whole defect being repaired is a lint nobody can act on. |
| D-11 | Is there a pytest that runs the real ratchet? | **No.** Unit tests are hermetic (synthetic diagnostics, temp baselines). | Otherwise one lint regression reds both `core-suite` and `lint` with two different remedies, breaking the repo's separate-job legibility idiom (`ci.yml:174-176`, `:277-279`). |
| D-12 | How the gate is *observed* failing | A local RED→GREEN cycle against **the exact command CI runs**, both outputs recorded verbatim. | GitHub Actions cannot be dispatched for this branch from here, and a green CI run only ever evidences the passing half. |

</decisions>

<code_context>
## Existing Code Insights

- `pyproject.toml:43-49` — the single `[tool.ruff]` block; `extend-exclude` currently
  `[".dotnet", ".venv", "bin", "obj"]`. No per-member override exists anywhere (verified by grep).
- `pyproject.toml:34` — `members = ["libs/python", "tools/*"]` already globs a new `tools/`
  package in; no members-list edit needed, but `uv sync --all-packages` must be re-run and
  `uv.lock` must not move (zero new external deps).
- `pyproject.toml:39` — root `testpaths = ["libs/python", "tools"]`, so the new tests join
  `core-suite` automatically.
- `.github/workflows/ci.yml` — 11 jobs; `gate.needs` at `:340`. `docs-guard` (`:302-313`) is the
  shape to copy.
- `tools/harness_lint/tests/conftest.py` — the `parents[3]` repo-root `sys.path` insert to copy.
- `tools/docs_guard/pyproject.toml`, `tools/docs_guard/__main__.py` — the virtual-member
  `package = false` / deferred-import entrypoint idiom.
- `harness/commands/lint.md:19` — the advisory `!`ruff check .`` that is red today. Left alone by
  this phase (it is the *in-session* surface, not the gate) but its status is now explainable.
- Installed ruff: **0.15.20** (`ruff~=0.15` pinned at `pyproject.toml:19`).

</code_context>

<specifics>
## Specific Ideas

- Record the real numbers everywhere: 620 → 427 (−193 vendored) → 403 (−24 safe fixes). Never
  restate 617 or "~180" without marking them as the disproven figures they are.
- The RED evidence is the deliverable, not a formality. `34-03-SUMMARY.md` carries both verbatim
  runs.
- Every commit atomic; the autofix commit is its own so a merge conflict with phases 30–33 is
  trivially resolvable.

</specifics>

<deferred>
## Deferred Ideas

- `ruff format --check` as a gate (D-08) — 25 files, needs its own decision.
- Reducing the 403: E501×277 dominates and is a reflow of most long lines under `tools/`.
- Promoting the ratchet to a bare `ruff check .` once the baseline reaches zero.
- A pre-commit mirror — nothing to mirror into today.

</deferred>
