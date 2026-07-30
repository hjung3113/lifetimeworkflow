# Phase 40: Self-Gate Teardown - Research

**Researched:** 2026-07-27
**Domain:** Deletion safety / CI gate topology / uv workspace mechanics (pure-deletion phase, no new code)
**Confidence:** HIGH — every claim below is a direct grep/read of this tree, not training knowledge.

## Summary

Phase 40 deletes the skill-registry self-gate: `tools/skill_registry/` (a virtual uv workspace
member), `harness/skills/registry.lock`, the CI job `registry-lock`, its `gate.needs` entry, and the
LANE-04 mirror test `tools/harness_lint/tests/test_skill_registry_lock.py`. A full-tree grep sweep
(question 1) found **zero referents CONTEXT.md missed** — the deletion set in 40-CONTEXT.md is
complete. The only file outside the deletion set that names `registry.lock` is
`docs/explanation/agent-workflow-skillset-design-guide.md`, and it names a different, never-built
concept (vendored-skill provenance) — CONTEXT.md D-05 already excludes it correctly.

CI gate topology (question 2) is simpler than the phase's own risk framing suggests: `registry-lock`
has **no `needs:` clause at all** — it is a fully independent job that does its own
`checkout` → `setup-uv` → `uv sync --all-packages` → check, with no dependency on `setup`. The *only*
edit `registry-lock`'s deletion requires elsewhere in `ci.yml` is removing its name from the `gate`
job's `needs:` list at line 410. No other job's `needs:` or matrix references it.

uv workspace mechanics (question 3) are low-risk: `pyproject.toml:34`'s `members = ["tools/*"]` is a
glob, so deleting the directory alone removes the member; `uv.lock`'s corresponding entry is named
`harness-skill-registry` (not `tools-skill-registry` — the package name in
`tools/skill_registry/pyproject.toml`, not the path) and lives at lines 196-198. `uv lock` regenerates
it; `uv sync --all-packages` proves the regenerated lock installs cleanly. `pyproject.toml:39`
(`testpaths = ["libs/python", "tools"]`) needs **no edit** — it names the parent `tools` directory,
not the deleted subdirectory, and pytest's collection naturally stops finding tests there once the
directory is gone.

**Primary recommendation:** delete everything in one commit in this order — CI job body, then
`gate.needs` entry, then the two Python trees (`tools/skill_registry/`,
`tools/harness_lint/tests/test_skill_registry_lock.py`), then `harness/skills/registry.lock`, then
`uv lock` + `uv sync --all-packages` to refresh `uv.lock` — verify with the closing grep sweep before
committing.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Skill-surface content declaration (the thing being deleted) | Constitution-adjacent tooling (`tools/skill_registry`, a Python CLI) | CI (`registry-lock` job re-runs it at merge time) | It was a derived-plane consistency check, not constitution data itself — `harness/skills/registry.lock` was machine-written, never hand-edited. |
| uv workspace member resolution | Build/toolchain tier (`pyproject.toml` + `uv.lock`) | — | Purely a package-manager concern; unrelated to the harness's own runtime tiers. |
| CI fan-in gate topology | CI tier (`.github/workflows/ci.yml`) | — | `gate.needs` is GitHub Actions' own dependency-resolution mechanism; not touched by any application code. |
| Skill anti-sprawl (name-level, survives this phase) | Emit/validation tier (`tools/harness_lint/caps.py::EXPECTED_SKILLS`, `tools/harness_emit/validate.py`) | — | D-03 (CONTEXT.md): explicitly out of scope, stays untouched. |

This phase performs no capability *work* — it is pure removal — so this map exists chiefly to confirm
the deleted surface (`tools/skill_registry`) sat entirely inside the CI/tooling tier and had no
runtime (browser/server/API/DB) footprint to account for.

## Package Legitimacy Audit

Not applicable — this phase installs no packages; it removes one internal virtual workspace member
(`tools/skill_registry`, source = this repo, not a registry package). No `slopcheck`/registry
verification is required.

## Removal-Safety Sweep (Research Question 1)

Full-tree grep (excluding `.git/`, `__pycache__/`, `.planning/`, `.claude/get-shit-done/`) for
`skill_registry`, `registry-lock`, `registry\.lock`, `SkillRegistryError`, `LOCK_PATH`,
`EXPECTED_SKILLS` — run 2026-07-27, results below.

### `skill_registry` referents (all inside the deletion set, or already-known exceptions)

| File | Line(s) | Disposition |
|------|---------|-------------|
| `uv.lock` | 198 | `source = { virtual = "tools/skill_registry" }` — regenerate via `uv lock` |
| `tools/skill_registry/registry.py` | 149 | in deletion set |
| `tools/skill_registry/__main__.py` | 12, 26, 31 | in deletion set |
| `tools/skill_registry/tests/conftest.py` | 1,3,6,9,18 | in deletion set |
| `tools/skill_registry/tests/test_skill_registry.py` | 15,16,221,230,236 | in deletion set |
| `tools/harness_lint/tests/test_skill_registry_lock.py` | 9,17,28 | in deletion set (LANE-04 mirror test) |
| `docs/adr/0012-ci-and-merge-as-decision-authority.md` | 96 | **out of scope, correct** — a ratified, immutable ADR naming what was deleted; append-only, never edited (see below) |
| `harness/skills/registry.lock` | 224 | in deletion set |
| `.github/workflows/ci.yml` | 302 | in deletion set (the CI job body) |

### `registry-lock` referents

| File | Line(s) | Disposition |
|------|---------|-------------|
| `tools/harness_lint/tests/test_skill_registry_lock.py` | 3 | in deletion set |
| `docs/adr/0012-ci-and-merge-as-decision-authority.md` | 97 | out of scope, correct (append-only ADR) |
| `.github/workflows/ci.yml` | 275, 294, 410 | in deletion set (job comment block, job name, `gate.needs` entry) |

### `registry\.lock` referents (file list)

`tools/skill_registry/{registry.py,pyproject.toml,tests/test_skill_registry.py,__main__.py}`,
`tools/harness_lint/tests/test_skill_registry_lock.py`,
`docs/adr/0012-ci-and-merge-as-decision-authority.md`,
`docs/explanation/agent-workflow-skillset-design-guide.md`, `.github/workflows/ci.yml` — the same set,
plus **one file not otherwise enumerated**: `docs/explanation/agent-workflow-skillset-design-guide.md`.

**Verified disposition of the one extra hit:** read at lines 555-600 and 660-668. This document
describes a *hypothetical/vendored* harness design (Korean prose, a different directory layout
entirely — `CONSTITUTION.md`, `risk-policy.yaml`, `workflows/`, `tasks/<TASK-ID>/`) where
`registry.lock` means **"승인 스킬 버전·해시"** (approved skill version/hash for *vendored external*
skills) and a file-ownership table listing `registry.lock` as owned by "관리자/CI" with the forbidden
action "자동 최신 버전 무검증 설치" (auto-installing latest version without verification) — i.e. it is
about **upstream-fork provenance tracking**, not this repo's skill-surface content-drift gate. This
confirms CONTEXT.md D-05's claim precisely: **do not touch this file.**

### Additional referents checked and found clean (all requested in the task brief)

| Location checked | Result |
|---|---|
| `.pre-commit-config.yaml` (repo root or anywhere at depth ≤2) | Does not exist in this repo — no referent possible. |
| `Makefile` / `justfile` | Neither exists in this repo — no referent possible. |
| `harness/` (source Markdown for commands/skills/agents) | Only `harness/skills/registry.lock` itself (the file being deleted). No `harness/commands/*.md` or `harness/skills/*/SKILL.md` documents `uv run python -m tools.skill_registry`. |
| `.opencode/` and `.claude/` (emitted trees, excluding vendored `.claude/get-shit-done/`) | **Zero hits.** Confirms CONTEXT.md's claim: `registry.lock` is not an emitted artifact — `tools/harness_emit/emit-manifest.json` has zero `registry` matches (checked directly, see below) and no committed emitted file references it. |
| `tools/harness_emit/emit-manifest.json` | Zero `registry` matches — confirmed by direct grep. |
| `tools/ruff_baseline/baseline.json` | Zero `skill_registry` matches — confirmed by direct grep; the ratchet gate cannot regress from this deletion. |
| `AGENTS.md` (root) / `CLAUDE.md` (root) | Zero matches for `skill_registry`, `registry.lock`, or `registry-lock` in either file. |

**Finding for the return summary: CONTEXT.md's referent set is complete. No missed referent.** The
only surface-level surprise is that the sweep surfaces one *additional* file
(`docs/explanation/agent-workflow-skillset-design-guide.md`) beyond the deletion set — but this is
already named and correctly excluded by CONTEXT.md D-05, so it changes nothing about the plan; it
only confirms D-05 was verified accurately.

## Architecture Patterns

### CI Gate Topology (Research Question 2)

```
git push / PR
      │
      ▼
┌─────────┐
│  setup  │  (emits language matrix; NOT a dependency of registry-lock)
└────┬────┘
     │ needs: setup
     ▼
┌─────────────┐   ┌──────────────┐   ┌───────┐   ┌────────┐  ...  ┌────────────────┐
│ lang-tests  │   │contract-check│   │ drift │   │ golden │       │ registry-lock  │──┐
└─────────────┘   └──────────────┘   └───────┘   └────────┘       │ (NO `needs:` —  │  │
                                                                    │  self-contained,│  │
                                                                    │  own checkout + │  │
                                                                    │  own uv sync)   │  │
                                                                    └─────────────────┘  │
                                                                                          ▼
                                                                              ┌──────────────────┐
                                                                              │ gate (fan-in)     │
                                                                              │ needs: [... ,     │
                                                                              │  registry-lock,   │
                                                                              │  ...]             │
                                                                              │ if: always()      │
                                                                              └──────────────────┘
```

**Verified, directly answering the question:**

1. **Does any job other than `gate` reference `registry-lock`?** No. `grep -n "needs:"
   .github/workflows/ci.yml` returns exactly two lines in the whole file: line 80
   (`lang-tests: needs: setup`) and line 410 (the `gate` job's fan-in list). `registry-lock` itself
   (`ci.yml:294-303`) has **no `needs:` clause** — it is a top-level job with its own `checkout`,
   `setup-uv`, and `uv sync --all-packages` steps (`ci.yml:296-300`), fully independent of `setup`.

2. **Is `setup` a dependency of `registry-lock` that becomes orphaned?** No — `registry-lock` never
   depended on `setup` in the first place (verified above), so deleting `registry-lock` orphans
   nothing. `setup`'s own consumer (`lang-tests`) is untouched by this phase.

3. **Exact line range to delete:** `.github/workflows/ci.yml:275-303` — this spans the comment block
   starting `# ── registry-lock ──` (line 275) through the job body ending at the `--check` step
   (line 303), verified by direct read. Whether to delete the comment block wholesale or partially is
   explicitly left to planner discretion (CONTEXT.md "Claude's Discretion").

4. **Exact edited `gate.needs:` content.** Current (`ci.yml:410`):
   ```yaml
   needs: [setup, lang-tests, contract-check, drift, golden, core-suite, lint, lifecycle-eval, emit-drift, registry-lock, stale-derived, docs-guard, workspace]
   ```
   Edited (remove `registry-lock`, no other token touched):
   ```yaml
   needs: [setup, lang-tests, contract-check, drift, golden, core-suite, lint, lifecycle-eval, emit-drift, stale-derived, docs-guard, workspace]
   ```

### uv Workspace Removal Mechanics (Research Question 3)

- **Installed uv version (this environment):** `uv 0.11.6 (65950801c 2026-04-09 aarch64-apple-darwin)`
  — verified via `uv --version`. (Note: `ci.yml` pins `astral-sh/setup-uv@v8.3.2` for the CI runner,
  which may resolve a newer uv than the local dev shell's 0.11.6; both understand `members = [...]`
  glob semantics identically for this operation, so the version delta does not affect this phase.)
- **`pyproject.toml:34`:** `members = ["libs/python", "tools/*"]` (glob). Deleting
  `tools/skill_registry/` removes the member automatically — **no edit to `pyproject.toml` needed**,
  confirming CONTEXT.md D-04.
- **`pyproject.toml:35`:** `exclude = ["tools/bootstrap"]` — unrelated, no edit.
- **`uv.lock` entry (lines 196-198), verified exact text:**
  ```toml
  [[package]]
  name = "harness-skill-registry"
  version = "0.0.0"
  source = { virtual = "tools/skill_registry" }
  ```
  Note the package `name` is `harness-skill-registry` (from `tools/skill_registry/pyproject.toml`'s
  `[project].name`), **not** a path-derived string — grep for `harness-skill-registry` if searching
  `uv.lock` directly rather than the path string.
- **Command sequence:** delete the directory first, then run `uv lock` to regenerate the lockfile
  (removes the `harness-skill-registry` package block; the resolver detects the member's directory no
  longer matches the `tools/*` glob), then `uv sync --all-packages` to prove the regenerated lock
  installs cleanly for every remaining member. `uv lock` alone rewrites the lockfile in-place; `uv
  sync --all-packages` is the separate verification step CONTEXT.md D-04 already specifies — needed
  because `uv lock` only recomputes the resolution graph, it does not by itself prove every other
  workspace member's environment still installs against the new lock.
- **Expected lockfile diff scope:** the `harness-skill-registry` `[[package]]` block removed, plus
  possibly the top-level lockfile hash/version stamp if uv tracks one; no other package's entry should
  change, since no other member depends on `tools/skill_registry` (see "Nothing outside `tools/`
  imports the package" in CONTEXT.md `<code_context>`, corroborated by the sweep above finding zero
  cross-package imports).
- **`pyproject.toml:39` `testpaths = ["libs/python", "tools"]`:** verified — **no edit needed**. This
  points at the parent `tools/` directory, not the deleted subdirectory; pytest's collection walk
  simply finds one fewer test module once `tools/skill_registry/tests/` no longer exists. This mirrors
  how `tools/bootstrap`'s exclusion works at the `uv` layer without needing a parallel `testpaths`
  carve-out.

### Recommended Task Ordering Inside the Single Commit

Not a new project structure (nothing is scaffolded) — this is the safe internal sequencing for the one
atomic commit CONTEXT.md D-01 mandates. Recommended order (verification-friendly, not strictly forced
by any tool — CONTEXT.md leaves the internal order to planner discretion):

1. Run the opening grep sweep (D-06) and record its output.
2. Delete `tools/skill_registry/` (all files, including `tests/` and any `__pycache__/`).
3. Delete `harness/skills/registry.lock`.
4. Delete `tools/harness_lint/tests/test_skill_registry_lock.py`.
5. Edit `.github/workflows/ci.yml`: remove lines 275-303 (job + its comment block) and edit line 410's
   `gate.needs` list.
6. Run `uv lock` then `uv sync --all-packages` to refresh and prove `uv.lock`.
7. Run the full verification suite (below) and the closing grep sweep.
8. Commit everything as one change.

This order deletes the *thing being checked* before the *check itself* only within the same commit —
which is safe, because nothing between these steps is a separate commit boundary. See "What Breaks If
the Order Is Wrong" below for why this specific order still matters for local iteration even though
the final commit is atomic.

## Common Pitfalls (Research Question 4 — What Breaks If The Order Is Wrong)

### Pitfall 1: CI job deleted but `gate.needs` still lists it
**What goes wrong:** GitHub Actions fails the entire workflow at parse/dispatch time with an error
resembling `Job 'gate' depends on unknown job 'registry-lock'.` — the workflow never runs any job; it
is a hard YAML-graph validation failure, not a test failure.
**Why it happens:** `needs:` is validated against the set of job names declared in the same workflow
file at parse time; a dangling reference is a structural error, not a runtime skip.
**How to avoid:** always edit `ci.yml:410` in the same diff hunk as deleting `ci.yml:275-303` —
CONTEXT.md's ordering rule (5) and milestone ordering rule (5) both name this exact pair.
**Warning signs:** none locally (this only manifests on GitHub's own workflow dispatch) — this is why
the closing grep sweep re-running `grep -n "registry-lock" .github/workflows/ci.yml` before commit is
the only local proxy for this failure mode.

### Pitfall 2: package dir deleted but `uv.lock` not refreshed
**What goes wrong:** `uv sync --all-packages` (used by nearly every CI job in this workflow, and by
local dev bootstrapping) fails because the lockfile's `source = { virtual = "tools/skill_registry" }`
entry points at a path that no longer exists. The exact uv error is a resolution/IO error naming the
missing directory (uv treats a stale virtual-member path in the lock as an invalid lock state needing
re-resolution).
**Why it happens:** `uv.lock` pins each workspace member's location explicitly (not just the glob); the
directory and the lock entry must move together.
**How to avoid:** run `uv lock` (regenerate) immediately after deleting the directory, in the same
commit, before running any other `uv sync`/`uv run` command that depends on the workspace resolving.
**Warning signs:** any local `uv run pytest` or `uv sync` invoked between the directory deletion and
the `uv lock` refresh will fail — this is the reason step 2 (delete dir) should be followed promptly
by step 6 (`uv lock` + `uv sync --all-packages`) before running the verification suite, even though
final commit atomicity means this ordering constraint doesn't leak outside the local working session.

### Pitfall 3: `test_skill_registry_lock.py` survives its import target
**What goes wrong:** `tools/harness_lint/tests/test_skill_registry_lock.py:17` does
`from tools.skill_registry.registry import LOCK_PATH, build_registry, diff_lock, dumps, load_lock` —
if `tools/skill_registry/` is deleted but this test file is not, pytest collection fails with
`ModuleNotFoundError: No module named 'tools.skill_registry'` at collection time, which (depending on
pytest config) can abort the entire collection run for `tools/harness_lint/` rather than failing just
this one test file.
**Why it happens:** this file is explicitly the LANE-04 "in-suite mirror of the CI job" (per
CONTEXT.md) — it imports the same module the CI job's `--check` invocation exercises, so it shares the
identical fate as the CI job itself.
**How to avoid:** delete this test file in the same commit as the package it imports — ordering rule
(8) in the v2.5 milestone header exists specifically for this failure mode ("a deleted `harness/`
artifact's dedicated gate test dies in the same commit").
**Warning signs:** `uv run pytest` immediately surfaces a collection error naming the missing module —
this is the loudest and earliest local failure mode of the three, and is exactly what acceptance
criterion 3 in the ROADMAP's Phase 40 detail section checks for ("no collection error from a removed
package").

## Don't Hand-Roll

Not applicable — this phase adds no code. There is no "don't hand-roll" concern for a deletion-only
phase; the equivalent guidance is the milestone's binding constraint already quoted in CONTEXT.md D-02:
build no replacement mechanism for the lost guarantee.

## Runtime State Inventory

Not applicable in the schema's sense (no rename/migration of a name across stored data, live service
config, OS-registered state, secrets, or build artifacts) — but the phase does have an analogous
"what still refers to the deleted thing after deletion" question, which is exactly what the Removal-
Safety Sweep section above answers exhaustively. No additional inventory category applies: this
repository has no external datastore, no live-service configuration outside git, no OS-registered
task/service state, and no secret keyed on this string. The closest analogue —"uv.lock", a build
artifact — is explicitly covered above.

## Verification Commands (Research Question 5)

All commands below are exact, taken from `ci.yml`'s own invocations of these tools (not invented),
mapped to CONTEXT.md D-08's six evidence items.

### 1. Closing grep sweep (D-06)
```bash
grep -rn "skill_registry\|registry-lock\|registry\.lock" \
  tools/ libs/ harness/ .github/ docs/ pyproject.toml uv.lock .claude/ .opencode/ \
  --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.claude/get-shit-done
```
**Expected exit/output:** the only surviving matches should be
`docs/adr/0012-ci-and-merge-as-decision-authority.md` (append-only ADR, correctly retained per D-05's
logic extended to ADR immutability — an ADR is never edited to remove a historical reference) and
`docs/explanation/agent-workflow-skillset-design-guide.md` (D-05's explicitly-kept different concept).
Any other surviving hit is a missed referent.

### 2. Full suite, no collection error
```bash
uv run pytest
```
**Expected exit code:** `0`. A `ModuleNotFoundError` naming `tools.skill_registry` (Pitfall 3 above)
would surface here first.

### 3. Workspace resolves
```bash
uv sync --all-packages
```
**Expected exit code:** `0`, after `uv lock` has already regenerated `uv.lock` (see uv mechanics
above). Run `uv lock` first as a separate, explicit step to make the lockfile diff auditable before
`uv sync` proves it installs.

### 4. Emit-drift clean (D-08 item 4) — exact command + exact path set
This is the identical invocation `ci.yml:251-263` uses; run it locally to reproduce the CI check:
```bash
uv run python -m tools.harness_emit
git add -A -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json
git diff --cached --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json
```
**Expected exit code:** `0` on the final `git diff --cached --exit-code` — deleting a declaration
*about* `harness/skills/` (not an emitted artifact itself, confirmed above via
`emit-manifest.json`'s zero `registry` matches) must not move either emitted tree.
**Note:** `git add -A` here is scoped to those specific paths, not the whole tree — this stages any
emit-produced changes for the diff check without staging the deletion itself; run this on a clean
working tree state where the deletions from steps 1-5 of the ordering section are already made but not
yet committed, OR run it in its own scratch checkout, to avoid the deletions themselves polluting the
`--cached` diff of the *emitted* paths (they shouldn't, since the emitted paths are disjoint from the
deleted paths, but running in a clean state removes any ambiguity).

### 5. Contract-drift clean (D-08 item 5)
```bash
uv run python -m tools.contract_drift.drift
```
**Expected exit code:** `0`. This phase touches no `contracts/**/*.schema.json` and no
`tools/contract_hash/hash.py` path list (verified: `grep -n "skill_registry\|registry"
tools/contract_hash/hash.py` returns nothing — the only path list entry near that area is
`harness/task-control/gate-registry.json`, unrelated).
If a workspace-wide check is also desired (this repo has one, unrelated to this phase but part of the
existing fan-in):
```bash
uv run python -m tools.contract_drift.drift --workspace
```

### 6. Ruff baseline still exits 0 (D-08 item 6)
```bash
uv run python -m tools.ruff_baseline
```
**Expected exit code:** `0`. Verified: `tools/ruff_baseline/baseline.json` has zero `skill_registry`
entries (direct grep), so this deletion can only shrink the ratchet's tracked findings, never grow
them — the ratchet only fails on rule-count *growth*.

### Guarded forms for tools the environment may lack
None of the six verification commands above require the .NET SDK or any other toolchain absent from
this environment — the entire deletion set and its verification path is pure-Python/uv/CI-YAML. No
guarded/fallback form is needed for this phase. (Contrast with golden-parity or lang-tests jobs
elsewhere in `ci.yml`, which do require `dotnet` — those jobs are untouched by this phase and are not
part of its verification set.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Skill surface guarded by a content-hash lock file (`registry.lock`) checked by a dedicated CI job (`registry-lock`) | Skill surface guarded only by name-level anti-sprawl (`caps.py::EXPECTED_SKILLS`) + emit-drift (source→emitted-tree fidelity) | This phase (40) | A skill's `description` or an authored `references/` file can change silently, re-emit cleanly, and pass every remaining gate — this is the accepted, recorded loss (CONTEXT.md D-02, scoping-FINAL risk 4). No replacement is planned or should be proposed. |

**Deprecated/outdated:** `tools/skill_registry` itself, and the `uv run python -m tools.skill_registry
--write` workflow a skill author previously had to run before committing a skill change — this
command simply no longer exists after this phase, and Phase 41 (skill deletion) is the first
beneficiary of not needing it (per CONTEXT.md's Specific Ideas).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `astral-sh/setup-uv@v8.3.2` (the CI-pinned uv) resolves the `tools/*` glob and lockfile format identically to the locally-installed uv 0.11.6 | uv Workspace Removal Mechanics | Low — both versions are well within uv's stable workspace-glob feature window; if CI's uv produces a materially different lockfile shape, the CI `gate` would catch it before merge (this is exactly what CI is for), so the risk is caught by the very gate this phase relies on, not silently missed. |

**If this table is sparse:** All other claims in this research were verified directly against the tree
via `grep`, `Read`, or `uv --version` in this session — no claim here rests on training-data recall of
this specific repository's contents.

## Open Questions (RESOLVED)

1. **RESOLVED: Should the CI comment block (`ci.yml:275-293`) be removed wholesale or partially?**
   - What we know: CONTEXT.md explicitly defers this to planner discretion — "whether the CI comment
     block at `ci.yml:275-293` is removed wholesale or partially... None of these change the delivered
     surface."
   - What's unclear: nothing technical is unclear; this is a stylistic choice with zero functional
     consequence, already flagged as free by CONTEXT.md.
   - RESOLVED — Recommendation: remove the entire comment block (lines 275-293) along with the job body
     (294-303) — the comment exclusively describes the job being deleted (it explains why
     `registry-lock` is "a DISTINCT concern from emit-drift"), so a partial removal would leave dangling
     prose describing a job that no longer exists, which is a worse outcome than the "wholesale"
     option CONTEXT.md itself frames as equally valid. This recommendation carries no new risk since
     CONTEXT.md already declared both options acceptable.

2. **RESOLVED (out of scope): Is branch protection actually enforcing `gate` as a required status check?**
   - What we know: ADR-0012 clause (a) itself states "This ADR does not assert that CODEOWNERS review
     is enforced by GitHub branch protection as an operational fact; branch protection was not
     confirmed during this phase's research (see 39-REVIEWS.md, Codex finding)."
   - What's unclear: whether an unenforced branch protection setting would let a red `gate` merge
     anyway, which would matter if this phase's deletion accidentally broke something the local
     verification commands miss.
   - RESOLVED — Recommendation: out of scope for Phase 40 to resolve (it is an ADR-0012-level finding, not a
     Phase-40 gap) — the planner should rely on the exact local verification commands in this document
     (all six D-08 items) rather than assuming CI-gate enforcement is the only safety net.

## Environment Availability

Skipped — this phase's own verification set requires no external dependency beyond `uv` (already
confirmed installed at 0.11.6) and Python's standard library via `uv run`. No `.NET`, no database, no
network service is invoked by any of the six verification commands above.

## Validation Architecture (Research Question 6)

For a pure-deletion phase, "test framework" in the conventional sense (new test files, new fixtures)
does not apply — CONTEXT.md D-08 is explicit: **verify by absence plus the four existing gates; add no
new test.** This section maps that instruction onto the Nyquist validation-architecture shape so the
planner can still produce a Wave-0/sampling-rate plan, with the understanding that Wave 0 is
**empty by design**.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (existing, `pyproject.toml:37` `dev = ["pytest>=8.4,<9", ...]`) |
| Config file | `pyproject.toml:38-41` `[tool.pytest.ini_options]` — unchanged by this phase |
| Quick run command | `uv run pytest tools/harness_lint -q` (scoped re-check of the one test dir that loses a file) |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CER-04 | `tools/skill_registry`, `registry.lock`, and CI `registry-lock` no longer exist; `gate.needs` has no dangling entry | absence/grep | `grep -rn "skill_registry\|registry-lock\|registry\.lock" tools/ harness/ .github/ pyproject.toml uv.lock` (expect only the two documented ADR/prose survivors) | N/A — this is a shell assertion, not a pytest file |
| CER-04 | Full suite collects and passes with no dangling import | regression (existing) | `uv run pytest` | ✅ already exists (no Wave 0 gap) |
| CER-04 | `uv.lock` resolves after member removal | regression (existing tooling) | `uv sync --all-packages` | ✅ already exists (no Wave 0 gap) |
| CER-04 | Emitted trees unmoved by this deletion | regression (existing CI job, run locally) | `uv run python -m tools.harness_emit && git add -A -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json && git diff --cached --exit-code -- <same paths>` | ✅ already exists (no Wave 0 gap) |
| CER-04 | Contract-drift and ruff-baseline stay clean | regression (existing) | `uv run python -m tools.contract_drift.drift`; `uv run python -m tools.ruff_baseline` | ✅ already exist (no Wave 0 gap) |

### Sampling Rate
- **Per task commit:** since this is one atomic commit (D-01), there is exactly one "per task"
  sample point: run the closing grep sweep + `uv run pytest tools/harness_lint -q` immediately after
  making all deletions, before staging.
- **Per wave merge:** this phase is a single wave / single commit — the phase gate *is* the wave gate.
  Run the full suite (`uv run pytest`) plus all six D-08 commands.
- **Phase gate:** full suite green (`uv run pytest`, `uv sync --all-packages`, `harness_emit` diff
  clean, `contract_drift`, `ruff_baseline`) before `/gsd:verify-work`.

### Wave 0 Gaps
**None — existing test infrastructure covers all phase requirements.** This is a deletion phase with
no new behavior to specify; the "tests" that matter are the absence-grep (not a pytest artifact) and
the four pre-existing CI gates, all of which already exist and already pass on the current (pre-
deletion) tree. No new test file, fixture, or framework install is needed. The only structural change
to the test tree is a *removal*: `tools/skill_registry/tests/{conftest.py,test_skill_registry.py}` and
`tools/harness_lint/tests/test_skill_registry_lock.py` disappear along with the code they exercise —
this is itself part of the deletion set, not a gap to fill.

## Security Domain

Not applicable — `security_enforcement` is not referenced anywhere in `.planning/config.json`'s
observed keys and this phase adds no input-handling, authentication, session, or cryptography surface;
it is pure deletion of internal CI/tooling. No ASVS category applies to a phase that removes a build-
time consistency check and touches no request path, no stored data, and no secret.

## Sources

### Primary (HIGH confidence — read directly this session, 2026-07-27)
- `.planning/phases/40-self-gate-teardown/40-CONTEXT.md` — locked decisions D-01..D-08, deletion set, deferred ideas
- `.planning/REQUIREMENTS.md:44-48` — CER-04 as written
- `.planning/ROADMAP.md` — v2.5 header ordering rules (1)-(8); `#### Phase 40: Self-Gate Teardown` full detail section
- `.planning/STATE.md:1-250` — milestone/phase status, decision log
- `docs/adr/0012-ci-and-merge-as-decision-authority.md:96-97` — ratified deletion authority for this exact surface
- `.github/workflows/ci.yml` (full file, grepped for `needs:`; read lines 38-80, 240-303, 395-415) — gate topology, exact job bodies
- `pyproject.toml` (full file read) — workspace members glob, exclude, testpaths, pytest config
- `uv.lock:185-210` — exact `harness-skill-registry` package block
- `docs/doc-dependencies.toml:20-115` — all 9 `[[binding]]` rows, none naming the deleted surface
- `docs/explanation/agent-workflow-skillset-design-guide.md:555-600,660-668` — confirms the unrelated vendored-skill `registry.lock` concept
- `tools/contract_hash/hash.py:32` (grepped) — path list contains no skill_registry entry
- Live `grep -rn` sweeps across `tools/ libs/ harness/ .github/ docs/ pyproject.toml uv.lock .claude/ .opencode/` (excluding `.git/`, `__pycache__/`, `.planning/`, `.claude/get-shit-done/`) for all six terms named in the research brief
- `uv --version` — local uv 0.11.6 confirmed installed

### Secondary (MEDIUM confidence)
- None — no WebSearch or external source was needed; this is entirely an in-repo question per the task's own constraint.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Removal-safety sweep: HIGH — direct grep over the full tree, cross-checked against CONTEXT.md's enumerated set with zero discrepancies found.
- CI gate topology: HIGH — direct read of the exact job definitions and the sole two `needs:` occurrences in the file.
- uv workspace mechanics: HIGH — direct read of `pyproject.toml`, `uv.lock`, and local `uv --version`; the only soft spot (A1) is whether CI's pinned uv version behaves identically, mitigated by CI itself being the final gate.
- Pitfalls: HIGH — each failure mode is derived from reading the actual code paths (`gate.needs` YAML validation semantics, `uv.lock`'s virtual-member pinning, the actual `from tools.skill_registry...` import line) rather than generic uv/CI knowledge.

**Research date:** 2026-07-27
**Valid until:** This research is tied to the exact current state of `ci.yml`, `pyproject.toml`, and
`uv.lock` in this repo — it becomes stale the moment any of those three files changes for an unrelated
reason (e.g., another phase adding a CI job before Phase 40 lands). Given the milestone's strict serial
DAG (`39 → 40 → 41 → ...`), no such change is expected before Phase 40 executes; treat as valid until
Phase 40 lands or any of the three files above changes, whichever comes first.
