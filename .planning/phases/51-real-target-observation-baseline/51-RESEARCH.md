# Phase 51: Real-Target Observation Baseline - Research

**Researched:** 2026-07-31
**Domain:** Running the harness's own read-only adoption pipeline (`tools.adoption_scan` /
`tools.adoption_apply`) against a real, isolated pnpm+turbo JS/TS monorepo, and capturing
reproducible evidence of the (possibly wrong) output — no source changes.
**Confidence:** HIGH (every claim below is either a direct code read of this checkout, a live
command run in this environment, or a direct read of the real target's files)

## Summary

This phase adds no code. Its entire job is to invoke the **already-shipped, unmodified**
`tools.adoption_scan` → `tools.adoption_apply draft` → `tools.adoption_apply apply` pipeline
against an isolated `git worktree` of `~/Desktop/2026/FeedbackOps` (pnpm workspace + turbo, 5
JS/TS packages: root, `packages/ui`, `packages/shared`, `apps/frontend`, `apps/backend`), plus two
read-only downstream observations (`tools.memory_regen.package_facts`,
`tools.harness_config.loader.conventions_for`), and write down exactly what happens — citing
`path:line` for every defect.

Direct inspection of the pipeline source (not the code's own comments, which restate an
un-updated suspicion) produces three falsifiable, HIGH-confidence predictions the baseline run
must confirm or refute empirically:

1. **Member discovery (RTA-02) will likely SUCCEED even though `pnpm-workspace.yaml` is
   unrecognized**, because every real workspace member (and the root) ships its own
   `package.json`, and `detect_manifests()`/`detect_candidate_process_boundaries()` key off
   `package.json` presence alone, never off `pnpm-workspace.yaml`. `pnpm-workspace.yaml`'s
   absence from `_MANIFEST_KIND_BY_NAME` (`tools/adoption_scan/detect.py:46-51`) may therefore be
   a defect with **no observable symptom in this specific target's member count** — a distinct,
   separately falsifiable claim from the dependency-edge question (D-16's "two distinct defects"
   framing is right to keep them apart).
2. **The OBS-03 `workspace:*` hypothesis is likely to be REFUTED**, not confirmed. Read literally,
   `_dependencies_from_package_json()` (`tools/adoption_scan/detect.py:273-284`) discards every
   dependency's version string outright — `for name in data.get("dependencies") or {}:` iterates
   dict **keys only**; the value (`"workspace:*"`, `"^1.1.11"`, whatever) is never inspected. Edge
   resolution in `tools/memory_regen/package_facts.py:build_facts()` then matches purely by
   **package name** against `manifest_by_id` (the `name` field each `package.json` itself
   declares). Every FeedbackOps intra-workspace dependency is spelled with the exact npm-scoped
   name (`"@fops/shared": "workspace:*"`) that its target package's own `package.json` declares as
   `"name"` — so the edge should resolve correctly today, contradicting the suspicion recorded in
   REQUIREMENTS.md/CONTEXT.md. The baseline run is what turns this from a prediction into a
   verdict; do not skip running it because the prediction looks confident.
3. **RTA-04 (nearest-wins convention profile with lint/test commands) is very likely to FAIL**, for
   a reason unrelated to pnpm at all: the core `harness/project.toml`'s `[[languages]]` table
   declares only `dotnet` and `python` (lines 26-45) — **no `javascript`/`typescript` entry
   exists**. `conventions_for()` resolves a package's language via `owner.get("language")` against
   this same `[[languages]]` list (`tools/harness_config/loader.py:342`); every FeedbackOps
   package's `language` will resolve to the literal string `"javascript"` (the deliberate default
   `package.json` → `javascript` mapping in `tools/memory_regen/package_facts.py:57-65`), which has
   **no matching `[[languages]]` row**, so `test`/`format`/`bash_scope` all resolve to `None`. This
   is a genuine gap for purpose ① (per-package conventions) independent of the pnpm question, and
   the record should carry it as its own `OBS-D-NN`, not fold it into OBS-03.

**Primary recommendation:** run the pipeline exactly as shipped, in exactly this order — discover
→ draft → apply → package_facts → conventions_for — against the isolated worktree; record every
stage's real stdout/stderr/exit code and the literal JSON excerpts that decide OBS-03, RTA-02, and
RTA-04; do not let the predictions above substitute for running the commands.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Isolated target is a `git worktree` of `~/Desktop/2026/FeedbackOps`, created **outside**
  that checkout's directory (e.g. `~/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline`), via
  `git -C ~/Desktop/2026/FeedbackOps worktree add --detach <path> <develop-SHA>`. Detached HEAD.
  Never a full clone, never nested inside the `develop` working tree.
- **D-02:** Pin the observed commit: `git -C <target> rev-parse HEAD` (today `1d1c8ed`, branch
  `develop`). Every command in the evidence log is replayable against that SHA.
- **D-03:** Byte-unchanged proof captured **before AND after** the run, over the original `develop`
  checkout, as three artifacts: (a) `git status --porcelain=v2 --untracked-files=all`, (b)
  `git rev-parse HEAD` + `git ls-files -s | sha256sum` (tracked index digest), (c) a digest of the
  untracked-path *set* (names only — `node_modules/`, `minio_data/` excluded from content hashing).
  Before/after equality of all three is the RTA-01 precursor evidence; any inequality is itself a
  recorded defect, not a silent retry.
- **D-04:** Disposal — after the evidence record is complete, `git worktree remove --force`; residue
  discarded. Evidence artifacts live in this repo's phase directory, never in the target. Phase 52
  re-creates a clean worktree from scratch.
- **D-05:** Zero writes to FeedbackOps product code. `/adopt apply` writing harness artifacts into
  the *worktree* is in scope; anything touching the target's application source is a defect to
  record, not an accepted behavior.
- **D-06:** Location — `.planning/phases/51-real-target-observation-baseline/`:
  `51-BASELINE-EVIDENCE.md` (human-readable record, the OBS-01 deliverable) + `evidence/` (raw
  `inventory.json`/`plan.json`/`manifest.json` plus per-command stdout/stderr/exit-code capture and
  the before/after isolation digests). No evidence goes into `contracts/`, `docs/adr/`, or
  `docs/reference/` — no constitution-plane member, no derived-plane generator (NG-01).
- **D-07:** Per-defect shape — one section per defect, id `OBS-D-NN`, with exactly: `symptom` ·
  `reproduction` (exact `python -m ...` argv, cwd, target SHA, harness SHA, exit code) ·
  `code location` (`path:line`) · `purpose tag` (①②③④ or "outside purpose") · `proposed disposition`
  (repair-in-52 / no-change-evidence-backed). A summary table at the top indexes all ids.
- **D-08:** The purpose tag written in Phase 51 is a **proposal, not a binding triage**. Phase 52
  (OBS-02) makes the repair/no-change decision; no-change observations stay in the record as
  evidence-backed confirmations rather than being deleted.
- **D-09:** Markdown + committed raw JSON only. No new JSON Schema, no new contract entry, no new
  parser for the evidence format.
- **D-10:** Push all three stages independently (discover → draft → apply); do not stop at the
  first failure. Record a failed stage and attempt the next with whatever artifacts exist. A
  genuinely un-runnable downstream stage is itself recorded as a defect
  (`blocked-by: OBS-D-NN`).
- **D-11:** No repairs, no workarounds, no hand-edited inputs during the baseline. Not one line of
  `tools/` changes in this phase. Hand-editing a `plan.json` to get `apply` to run would destroy
  the evidence — record the block instead.
- **D-12:** After the apply attempt, also run the read-only downstream observations in the worktree
  — package facts (`tools.memory_regen.package_facts`) and nearest-wins convention resolution
  (`tools.harness_config.loader:conventions_for`) — even though RTA-03/RTA-04 are Phase 52
  requirements. These are observations, not repairs, and are where the ②③ purpose defects will
  actually surface.
- **D-13:** Reproducibility metadata is mandatory in the record header: harness commit SHA, target
  commit SHA, `python --version`, `uv --version`, `pnpm --version` if invoked, working directory
  for each command, and the literal argv.
- **D-14:** OBS-03 is evidence-first from the real run, not a synthetic fixture. Verdict is read
  off the run's own `inventory.json` + generated package facts: **confirmed** if a `workspace:*`
  dependency is recorded as a version string (or the `packages/shared`→`apps/frontend`/
  `apps/backend` edges are absent), **refuted** if the workspace edge is already recorded
  correctly. A refutation closes OBS-03 successfully and is stated as such.
- **D-15:** The verdict lives in a dedicated `## OBS-03 verdict` section of
  `51-BASELINE-EVIDENCE.md`, quoting the literal output excerpt that decides it, plus the
  `path:line` of the implicated code (current suspicion: `tools/adoption_scan/detect.py:46-50` and
  `_dependencies_from_package_json`).
- **D-16:** Treat member discovery and dependency-edge recording as two potentially distinct
  defects; record them under separate `OBS-D-NN` ids even if one masks the other.
- **D-17:** No fixture is added to this repo in Phase 51. A minimal reproduction's *shape* may be
  described in the record; committing it is a Phase 52 decision.

### Claude's Discretion

- Exact worktree path, evidence sub-file naming, and the ordering of commands within a stage.
- Whether the raw capture is one log file per command or one combined transcript, as long as every
  command's argv, cwd and exit code are recoverable.
- How many `OBS-D-NN` sections to split a compound failure into, guided by D-16's "separate causes
  get separate ids" rule.

### Deferred Ideas (OUT OF SCOPE)

- Any repair of an observed defect — Phase 52 (OBS-02).
- Committing a minimal pnpm-workspace reproduction fixture — Phase 52, paired with the repair it
  regression-tests (D-17).
- Managed install→update behavior for `/adopt` (manifest of managed files, no-op re-run, divergence
  conflict report) — Phase 53 (MONO-12).
- DEBT-01 shared `"dir"`-filter helper — Phase 54.
- Second target repo (vocpage) — explicitly out of v2.7 until the FeedbackOps adoption completes.
- Changing FeedbackOps product code — out of milestone scope entirely.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OBS-01 | Every adoption defect observed during the baseline has a reproducible record — symptom · reproduction path · code location. | The `OBS-D-NN` shape (D-07) plus the exact invocation contracts documented below (Code Examples) give the planner everything needed to make each defect's `reproduction` field literally re-runnable. The three falsifiable predictions in the Summary are candidate defects the plan should design capture steps around, but the record must state what actually happened, not the prediction. |
| OBS-03 | pnpm `workspace:*` dependencies are recorded as a workspace edge, not a version string — hypothesis confirmed or refuted from real run output. | Prediction 2 above, backed by a direct read of `_dependencies_from_package_json` (discards all version values) and `build_facts()`'s pure-name edge match (`tools/memory_regen/package_facts.py:216-245`), plus the real FeedbackOps manifests' declared dependency names (all exact `@fops/*` scoped names). The plan must still capture the literal `package-facts.md`/edge-list excerpt as the D-15-required verdict citation — the prediction is not itself the evidence. |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Isolation (worktree provisioning, byte-unchanged proof) | Local git / filesystem (this session's shell) | — | `git worktree` is a repo-metadata operation on the *harness operator's* machine, not a component of either codebase; no code in this repo performs it. |
| Discover (inventory/plan/manifest generation) | Backend / CLI tool (`tools.adoption_scan`, Python) | — | Pure read-only Python CLI over an arbitrary `--target`; no server, no browser involved. |
| Draft (task-local batch) | Backend / CLI tool (`tools.adoption_apply draft`) | — | Same tier as discover; writes only to a caller-chosen, target-external batch root. |
| Apply (writes into the worktree) | Backend / CLI tool (`tools.adoption_apply apply`) | Filesystem (the target worktree) | Writes land in the target's filesystem, but the write DECISION and mechanics are entirely in this repo's Python; the target itself has no active role (no build/test/pnpm invocation happens as part of apply). |
| Package facts / dependency edges | Backend / CLI-and-library tool (`tools.memory_regen.package_facts`) | — | Pure Python static analysis over manifest text; no runtime execution of the target's own toolchain (pnpm/turbo never invoked by this phase's Python calls). |
| Convention-profile resolution | Backend / library (`tools.harness_config.loader.conventions_for`) | — | Pure Python join over config + package facts; no filesystem write, no target execution. |
| Evidence capture (argv/cwd/exit/stdout/stderr recording) | This session's orchestration (task-runner shell) | — | Not a capability of either codebase — it is how the plan's tasks are executed and their output logged. |

**Note:** No capability in this phase touches a browser, an API server, or a CDN tier — the entire
observation surface is CLI + filesystem + git, which is why the map above is intentionally
CLI/backend-only.

## Standard Stack

No new libraries are introduced by this phase (NG-01: zero new dependencies, zero new tooling).
The entire pipeline under observation is already-shipped code in this checkout:

| Tool | Version (verified live in this environment) | Role in this phase |
|------|------|---------------------|
| `git` | 2.50.1 (Apple Git-155) `[VERIFIED: live command]` | Worktree provisioning + isolation proof |
| `uv` | 0.11.6 (this checkout) `[VERIFIED: live command]` | Runs the pipeline via `uv run python -m ...` so the correct (3.11) interpreter is used |
| `python` (uv-managed) | 3.11.15 `[VERIFIED: live command \`uv run python --version\`]` | Required — the **system** `python3` on this machine is 3.9.6, which is BELOW this repo's `requires-python = ">=3.11"` (`pyproject.toml:5`) and cannot even import `tomllib` used throughout `tools/harness_config` and `tools/adoption_scan`. Every command in the plan MUST be prefixed `uv run python -m ...`, never bare `python3 -m ...`. |
| `node` | v22.22.2 `[VERIFIED: live command]` | Present, but this phase never invokes it — FeedbackOps declares `"engines": {"node": ">=22.11.0"}` (root `package.json:8`), satisfied, purely informational since no `pnpm install`/build runs in this phase |
| `pnpm` | 11.1.1 `[VERIFIED: live command]` | Present, but FeedbackOps pins `"packageManager": "pnpm@9.15.0"` (root `package.json:6`) — a version mismatch worth noting in the record if any pnpm invocation is ever attempted, though D-12's downstream observations (`package_facts`, `conventions_for`) are pure Python and never shell out to `pnpm` |

### Alternatives Considered

Not applicable — this phase adds no new tooling; the only "alternative" ever on the table was
whether to hand-write a fixture-based reproduction instead of running the real target, which D-14
explicitly rejects ("evidence-first from the real run, not a synthetic fixture").

## Package Legitimacy Audit

Not applicable. This phase installs no new packages of any kind (no `pip install`, no `npm
install`, no new `pyproject.toml`/`package.json` dependency). Every tool invoked
(`git`, `uv run python -m tools.adoption_scan`, `tools.adoption_apply`, `tools.memory_regen`,
`tools.harness_config`) is already-vendored code in this checkout. The Package Legitimacy Gate
protocol is skipped for this reason, not because it was unavailable.

## Architecture Patterns

### System Architecture Diagram

```
 (this session, local shell)
   │
   │ 1. git -C ~/Desktop/2026/FeedbackOps worktree add --detach <path> 1d1c8ed
   ▼
 isolated worktree  <path>  (detached HEAD @ 1d1c8ed)
   │
   │ 2. uv run python -m tools.adoption_scan --target <path> --out <evidence>/discover
   │      (read-only: enumerate → classify exclusions → hash → detect languages/manifests/
   │       surfaces/candidate boundaries → plan proposals/questions → destination manifest)
   ▼
 <evidence>/discover/{inventory,plan,manifest}.json  (never written into <path>)
   │
   │ 3. uv run python -m tools.adoption_apply draft --task-dir <evidence>/batch \
   │      --target <path>
   │      (re-runs the SAME scan→plan→manifest sequence, batch-id = sha256(target_ref|UTC date)[:16])
   ▼
 <evidence>/batch/artifacts/adoption/<batch-id>/{status,inventory,plan,manifest}.json
   │
   │ 4. uv run python -m tools.adoption_apply apply --task-dir <evidence>/batch \
   │      --batch-id <id> --target <path>
   │      (writes harness-template content INTO <path> per manifest["dispositions"];
   │       refuses constitution-plane destinations; never touches FeedbackOps app source
   │       because none of those paths exist in the catalog)
   ▼
 <path> now contains whatever "create"/"marker-merge" dispositions resolved to
   (e.g. possibly harness/project.toml, AGENTS.md/CLAUDE.md marker splices, tools/**, contracts/**)
   │
   │ 5. downstream, read-only, D-12 (Python API calls, NOT the bare CLI entrypoints — see Pitfall 4)
   │      build_facts(repo_root=<path>)              -> package + dependency-edge facts
   │      conventions_for(pkg_dir, cfg=..., facts=...) -> per-package lint/test/format resolution
   ▼
 evidence excerpts quoted verbatim into 51-BASELINE-EVIDENCE.md's OBS-03/RTA-03/RTA-04 sections
   │
   │ 6. git -C ~/Desktop/2026/FeedbackOps {status --porcelain=v2 --untracked-files=all |
   │      rev-parse HEAD | ls-files -s | sha256sum}   -- run BEFORE step 1 AND after step 7
   ▼
 before/after digest comparison  -> RTA-01 byte-unchanged proof
   │
   │ 7. git -C ~/Desktop/2026/FeedbackOps worktree remove --force <path>  (disposal, D-04)
   ▼
 <path> and all its contents discarded; only .planning/phases/51-*/ evidence survives
```

### Recommended Evidence Directory Structure

```
.planning/phases/51-real-target-observation-baseline/
├── 51-RESEARCH.md              # this file
├── 51-BASELINE-EVIDENCE.md      # OBS-01 deliverable: OBS-D-NN records + OBS-03 verdict section
└── evidence/
    ├── isolation/
    │   ├── before.status.txt    # git status --porcelain=v2 --untracked-files=all (pre-run)
    │   ├── before.index.sha256  # git rev-parse HEAD + git ls-files -s | sha256sum
    │   ├── before.untracked-set.sha256
    │   ├── after.status.txt
    │   ├── after.index.sha256
    │   └── after.untracked-set.sha256
    ├── discover/
    │   ├── inventory.json
    │   ├── plan.json
    │   ├── manifest.json
    │   ├── stdout.txt / stderr.txt / exit_code.txt / argv.txt / cwd.txt
    ├── draft/
    │   └── (batch artifacts + stdout/stderr/exit/argv/cwd, same shape)
    ├── apply/
    │   └── (stdout/stderr/exit/argv/cwd; the worktree's own resulting tree state is NOT copied
    │        back here in full — only the specific file excerpts a defect record cites)
    └── downstream/
        ├── package-facts.json   # captured stdout of the build_facts()/render() invocation
        └── conventions.json     # captured stdout of the conventions_for() invocation, per package
```

### Pattern 1: Read-only-by-construction discovery

**What:** `tools.adoption_scan`'s `enumerate_target()` uses `git ls-files -z --cached --others
--exclude-standard` (falls back to a confined walk) and every subsequent step
(`classify_exclusions`, hashing, `detect.py`) only ever calls `open("rb")`/`.stat()` — never
`open("wb")`, never a mutating git command. This is enforced by
`tools/adoption_scan/tests/test_readonly.py`, which snapshots the target tree before/after a full
`build_inventory()` call and asserts byte-identity, including symlink targets.
**When to use:** Confirms discover is genuinely safe to run against the real, unmodified
`develop` checkout indirectly (via the worktree) — no special caution needed beyond running it
against the worktree, not the original checkout directly.
**Example:**
```python
# Source: tools/adoption_scan/tests/test_readonly.py (this checkout)
def test_target_tree_byte_unchanged_after_scan(tmp_minirepo: Path) -> None:
    before = _tree_snapshot(tmp_minirepo)
    scan.build_inventory(tmp_minirepo)
    after = _tree_snapshot(tmp_minirepo)
    assert before == after
```

### Pattern 2: Total, ordered disposition chain — apply never guesses

**What:** `destinations.disposition()` is a 7-step total function: gsd-owned exclusion →
constitution-plane (`human-ratification-required`, wins over everything) → derived-glob
(`derived-regenerate`) → marker-capable (`marker-merge`) → no existing file (`create`) → hash-equal
(`preserve`) → else `conflict`. Every catalog row resolves to exactly one of 6 enum values or is
excluded — proven total by `tools/adoption_scan/tests/test_dispositions.py::test_total`.
**When to use:** The baseline's `manifest.json` output for the worktree is exactly this function
applied to the FeedbackOps target — reading the `dispositions` array tells you, in advance of
`apply`, precisely what will be written and where, without guessing.
**Example:**
```python
# Source: tools/adoption_scan/destinations.py:326-366 (this checkout)
def disposition(rel, target_root, proposed_sha, *, existing_sha=None) -> str | None:
    if is_gsd_owned(rel):
        return None
    if resolve_path(CONSTITUTION_GLOBS, rel) == "deny" or rel == "libs/normalize-spec.md":
        return "human-ratification-required"
    if resolve_path(DERIVED_GLOBS, rel) == "deny":
        return "derived-regenerate"
    if rel in MARKER_CAPABLE:
        return "marker-merge"
    existing = Path(target_root) / rel
    if not existing.exists():
        return "create"
    if existing_sha is None:
        existing_sha = _existing_hash(existing)
    return "preserve" if existing_sha == proposed_sha else "conflict"
```

### Anti-Patterns to Avoid

- **Hand-editing any drafted `plan.json`/`manifest.json` to force `apply` to succeed** — explicitly
  forbidden by D-11; it destroys the evidence value of a failure.
- **Invoking the bare `python -m tools.memory_regen.package_facts` CLI and assuming it observed the
  worktree** — it does not; see Pitfall 4 below. The plan must call the Python functions directly
  with an explicit `repo_root`/`cfg` argument.
- **Treating a confident prediction (Summary items 1-3) as a substitute for running the command** —
  D-14 requires the verdict be read off the real run's own output, quoting a literal excerpt.
- **Using the system `python3` (3.9.6) instead of `uv run python`** — every invocation must go
  through `uv run` (see Standard Stack); a bare `python3` will fail on `tomllib` imports used
  throughout the pipeline (Python 3.11+ stdlib only) with an unhelpful `ModuleNotFoundError`, which
  would look like a pipeline defect but is actually an environment-invocation mistake.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Isolating a real repo for a destructive-capable tool | A custom sandbox/copy script | `git worktree add --detach` | Native git primitive; detached HEAD structurally prevents advancing `develop`; D-01 already specifies this. |
| Verifying an adoption run's read-only-ness | A bespoke file-diff script | `git status --porcelain=v2 --untracked-files=all` + `git ls-files -s \| sha256sum` + untracked-path-set digest | These are the exact three artifacts D-03 specifies; they are standard, scriptable, and already proven deterministic by this repo's own `test_readonly.py` pattern for the scan stage. |
| Discovering package facts / dependency edges on the worktree | A new target-aware CLI wrapper around `package_facts`/`loader` | Call `tools.memory_regen.package_facts.build_facts(repo_root=...)` and `tools.harness_config.loader.conventions_for(path, cfg=..., facts=...)` directly as library functions from a short capture script under `evidence/` | Both functions already accept the needed parameters (`repo_root`, `cfg`, `facts`) — no new command or fixture is needed, only a correct call. Writing a *new command* to do this would violate NG-01. |

**Key insight:** Every capability this phase needs already exists in this checkout as a pure,
parameterized function or a CLI with a `--target`/`--out`/`--task-dir` flag. The only place a
"missing feature" appears is `package_facts.main()`/`conventions_for()`'s CLI entrypoints, which
default to this repo's own root with no override flag — the fix for the *baseline* is to call the
library function directly (already supported), not to add a flag (which would be new-command
growth Phase 51 cannot introduce, and is arguably Phase 52/54 territory if ever done at all).

## Common Pitfalls

### Pitfall 1: Bare `python3` silently fails or, worse, silently misbehaves
**What goes wrong:** The system `python3` on this machine is 3.9.6; this repo requires `>=3.11`
and its own `harness_config`/`adoption_scan` modules import stdlib `tomllib` (3.11+ only).
**Why it happens:** `uv` manages a project-local interpreter (verified: `uv run python --version`
→ 3.11.15) that is NOT the same as the ambient `python3` on `PATH`.
**How to avoid:** Every command in every task/reproduction step must be `uv run python -m
tools....`, never bare `python3 -m ...` or `python -m ...`.
**Warning signs:** `ModuleNotFoundError: No module named 'tomllib'` or an import error deep in
`tools.harness_config.loader`.

### Pitfall 2: `package_facts`/`conventions_for` CLI entrypoints are repo-anchored, not target-anchored
**What goes wrong:** `python -m tools.memory_regen.package_facts` (no flags exist) always analyzes
**this harness checkout** (`_REPO_ROOT`, `tools/memory_regen/package_facts.py:49-51,352-361`); it
never accepts a `--target`. Running it as a bare CLI against the worktree observes nothing about
FeedbackOps at all — the run would silently "succeed" while producing entirely irrelevant output,
which could be misread as "package facts worked."
**Why it happens:** `build_facts()`/`write()` accept an optional `repo_root: Path = _REPO_ROOT`
parameter, but `main()` never threads a CLI flag through to it.
**How to avoid:** Capture output via a short Python invocation that calls the library function
directly with an explicit `repo_root`, e.g.
`uv run python -c "import json; from pathlib import Path; from tools.memory_regen.package_facts import build_facts; print(json.dumps(build_facts(repo_root=Path('<worktree>')), indent=2))"`
(exact form is the plan's to finalize; the constraint is *must pass `repo_root` explicitly*).
Similarly, `conventions_for(path, cfg=..., facts=...)` needs an explicit `cfg` — see Pitfall 3.
**Warning signs:** A "package facts" capture that lists this harness's own Python/`.NET` packages
(`libs/python`, `examples/log-parser/...`) instead of `@fops/*` packages is the tell that the
default `repo_root` was used by mistake.

### Pitfall 3: The core `harness/project.toml` has no JS/TS `[[languages]]` entry
**What goes wrong:** Even when `conventions_for()` is correctly pointed at the worktree's package
facts, resolving lint/test/format commands ALSO needs a `cfg` (a `harness/project.toml`-shaped
dict) whose `[[languages]]` includes an entry with `id` matching the package's resolved
`language`. The core config (`harness/project.toml:26-45`, read live in this research) declares
only `dotnet` and `python` — no `javascript`/`typescript` row exists anywhere in this checkout's
default config.
**Why it happens:** `harness/project.toml` is the *log-parser example instance's* declared
toolchain (own file header, lines 1-15), never designed with a JS/TS target in mind; the
`[[languages]]` slot is meant to be swapped per-instance, and nothing in this phase swaps it (that
would be a source edit, forbidden by D-11/NG-01).
**How to avoid:** Do not treat this as a bug to route around — record it as an observation. If
`/adopt apply` created a `harness/project.toml` in the worktree (its disposition is `create` per
Pattern 2's chain, since the file exists in this checkout at that path and the worktree has none),
that created copy is the SAME dotnet+python config, still with no JS/TS entry — so even the
worktree's own freshly-created config cannot satisfy RTA-04 without a repair. This is a real,
citable defect for the OBS-01 record, independent of and additional to the OBS-03 pnpm question.
**Warning signs:** `conventions_for()` returning `{"test": None, "format": None, "bash_scope":
None}` for every FeedbackOps package is the expected (and diagnostic) symptom, not a crash.

### Pitfall 4: `harness/project.toml`'s own `create` disposition may write irrelevant content into the worktree
**What goes wrong:** `destination_catalog()` enumerates every real git-tracked file at
`harness/project.toml` (among ~40+ other paths) in THIS checkout. Since the worktree currently has
no `harness/project.toml`, `disposition()` step 5 resolves it to `create`, and `apply` will copy
this harness's own dotnet+python config verbatim into the FeedbackOps worktree unless something
else refuses it first (it is not GSD-owned, not on the constitution plane, not a derived glob, not
marker-capable — nothing refuses it). This is worth recording as an observation (content copied
into a foreign, unrelated-stack repo) even though D-05 ("apply writing harness artifacts into the
worktree is in scope") means it is not itself an isolation violation.
**Why it happens:** The destination catalog is rule-derived from THIS repo's own tree
(`destinations.py:236-283`), not target-aware; it has no concept of "this destination doesn't make
sense for this target's stack."
**How to avoid:** Record it plainly in the evidence — this is exactly the kind of "purpose"-tagged
observation D-07's `purpose tag (①②③④ or "outside purpose")` field exists for. It likely tags as
outside-purpose-or-①-adjacent (misleading per-package conventions), not a security or isolation
concern.
**Warning signs:** After `apply`, `<worktree>/harness/project.toml` exists and contains `[[languages]]
id = "dotnet"` / `id = "python"`.

### Pitfall 5: Two workspace-YAML-adjacent surprises worth a note either way
**What goes wrong (a):** FeedbackOps root has BOTH a `pnpm-lock.yaml` and `pnpm-workspace.yaml`;
neither is recognized by `_MANIFEST_KIND_BY_NAME`, but this is expected — see Summary prediction 1
— and by itself should not block member discovery.
**What goes wrong (b):** FeedbackOps ships config in a mix of extensions (`biome.json`,
`turbo.json`, `.mjs` scripts under `scripts/`, `.ts`/`.tsx` app code) — `.mjs` is NOT in
`_LANGUAGE_BY_EXTENSION` (`tools/adoption_scan/detect.py:30-43`; only `.js`/`.jsx`/`.ts`/`.tsx` are
listed), so `scripts/check-boundaries.mjs` and friends will not register as a detected language
occurrence, and if the tree has both `.ts` and any `.js`/`.jsx` file an `ambiguous-language`
question will be emitted (`plan.py:262-287`) — expected, not a bug, but worth citing as an example
of a real `questionRecord` the baseline should show verbatim.
**How to avoid:** Just record what discover actually emits for `languages`/`ambiguous-language`;
do not treat either as a defect unless it blocks a downstream success criterion.

## Code Examples

Verified, exact invocation forms for each stage (argv confirmed by reading `argparse` wiring in
`tools/adoption_scan/cli.py` and `tools/adoption_apply/cli.py`, this checkout):

### Discover
```bash
# Source: tools/adoption_scan/cli.py:46-53 (this checkout) — --target and --out both required,
# --out must not resolve inside/equal/containing --target (checked structurally before any write).
uv run python -m tools.adoption_scan \
  --target ~/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline \
  --out .planning/phases/51-real-target-observation-baseline/evidence/discover
```

### Draft
```bash
# Source: tools/adoption_apply/cli.py:198-209 (this checkout) — --task-dir is a caller-chosen
# directory (the .workflow/tasks/ lifecycle plane this comment historically referenced was DELETED
# in v2.5 phase 43 — any directory works; batch.py only needs to create
# <task-dir>/artifacts/adoption/<batch-id>/ under it).
uv run python -m tools.adoption_apply draft \
  --task-dir .planning/phases/51-real-target-observation-baseline/evidence/draft \
  --target ~/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline
# batch_id printed to stderr as part of "wrote <path>" lines; also readable from
# <task-dir>/artifacts/adoption/<batch-id>/status.json (content-derived: sha256(target_ref|UTC date)[:16])
```

### Apply
```bash
# Source: tools/adoption_apply/cli.py:198-217 (this checkout) — --batch-id must match the id
# draft produced; --target here is the SAME worktree path (writes land there, per D-05).
uv run python -m tools.adoption_apply apply \
  --task-dir .planning/phases/51-real-target-observation-baseline/evidence/draft \
  --batch-id <batch-id-from-draft-status.json> \
  --target ~/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline
```

### Downstream package facts (D-12) — direct library call, not the bare CLI (Pitfall 2)
```bash
uv run python -c "
import json
from pathlib import Path
from tools.memory_regen.package_facts import build_facts
facts = build_facts(repo_root=Path('$HOME/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline'))
print(json.dumps(facts, indent=2, sort_keys=True))
"
```

### Downstream convention profile (D-12) — needs an explicit `cfg` too (Pitfall 3)
```bash
uv run python -c "
import json
from pathlib import Path
from tools.harness_config.loader import conventions_for, load_project
from tools.memory_regen.package_facts import build_facts

target = Path('$HOME/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline')
facts = build_facts(repo_root=target)
# If /adopt apply created <target>/harness/project.toml (Pitfall 4), load THAT copy — it is still
# the dotnet+python config (no source edit made it JS/TS-aware); load_project(default) is the
# harness's own config, used only if the worktree copy is absent.
project_toml = target / 'harness' / 'project.toml'
cfg = load_project(project_toml) if project_toml.is_file() else load_project()
for pkg in facts['packages']:
    print(pkg['id'], '->', json.dumps(conventions_for(pkg['dir'], cfg=cfg, facts=facts)))
"
```

### Isolation proof (D-03)
```bash
# BEFORE (run against the ORIGINAL checkout, never the worktree) and AFTER, identical commands:
git -C ~/Desktop/2026/FeedbackOps status --porcelain=v2 --untracked-files=all > before.status.txt
git -C ~/Desktop/2026/FeedbackOps rev-parse HEAD > before.head.txt
git -C ~/Desktop/2026/FeedbackOps ls-files -s | sha256sum > before.index.sha256
git -C ~/Desktop/2026/FeedbackOps status --porcelain=v2 --untracked-files=all \
  | awk '{print $NF}' | sort | sha256sum > before.untracked-set.sha256
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `.workflow/tasks/<id>/artifacts/adoption/<batch-id>/` under a lifecycle-tracked task | Any caller-chosen `--task-dir`; the entire `.workflow/` lifecycle plane was deleted | Phase 43 (v2.5, 2026-07-28) | Some in-repo comments (e.g. `destinations.py`'s docstring citing `.workflow/tasks/T-0001/task.json` as an illustrative placeholder) still read as if the lifecycle plane exists; it does not (`ls .workflow` → no such directory in this checkout today). The plan should use a plain evidence-scoped directory as `--task-dir`, not attempt to recreate `.workflow/tasks/`. |
| A gated promote/approval stage between draft and apply | Review happens at the PR (ADR-0012); no in-pipeline gate | Phase 42 (v2.5) | Confirmed directly in `tools/adoption_apply/tests/test_cli.py`'s own docstring: "The former ADOPT-06 promote/approval gate is deleted (D-01); the review moves to the PR." Nothing to wait on between draft and apply in this baseline. |

**Deprecated/outdated:** Any research or prior-phase comment implying a `.workflow/tasks/` task
directory is required for `/adopt draft`/`apply` is stale — the CLI accepts any directory.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The predictions in the Summary (member discovery likely succeeds; OBS-03 likely refuted; RTA-04 likely fails on the language-config gap) are code-read-derived, HIGH-confidence hypotheses, **not yet run against the real target** at research time (the pipeline was not executed end-to-end against FeedbackOps during this research pass — only individual manifests were read by hand and the code paths traced). | Summary, Pitfalls 2-4 | If the baseline run disagrees with these predictions (e.g., some other exclusion rule in `scan.py` drops a package.json, or turbo/biome config triggers an unanticipated question/exclusion), the plan must trust the RUN's actual output over this document's predictions — D-14 already requires this discipline explicitly. |
| A2 | `pnpm --version` (11.1.1) and `node --version` (v22.22.2) as observed in this research session will still be the versions present when the plan executes; this is an ambient-environment fact, not a code fact, and could differ in a different execution environment. | Standard Stack, Environment Availability | Low risk — D-13 requires capturing the ACTUAL versions in the record header at run time regardless, so a drift here is self-correcting as long as the plan re-captures rather than copies this document's numbers. |
| A3 | No FeedbackOps manifest, script, or config file contains a secret-shaped literal that would trip `scan.py`'s `SECRET_CONTENT_PATTERNS`/`SECRET_PATH_GLOBS` — this was not exhaustively checked (only the 5 `package.json` files and `pnpm-workspace.yaml` were read); a `.env`, `minio_data/` credential file, or embedded token elsewhere in the tree was not ruled out. | Security Domain | If such content exists it would be legitimately EXCLUDED from `inventory.json` (never hashed, never echoed — D-08 in `scan.py`'s own design) — this is the correct behavior, not a defect, but the evidence record should note if any `excluded: "secret-content"`/`"secret-path"` entries appear so the reader isn't surprised by files silently missing from `included`. |

## Open Questions (RESOLVED)

1. **(RESOLVED by an execution-time evidence check) Will `/adopt apply` actually attempt any write inside `node_modules/`, `minio_data/`, or other
   large untracked directories?**
   - What we know: `enumerate_target()` uses `git ls-files --cached --others --exclude-standard`,
     which respects `.gitignore` — `node_modules/`/`minio_data/` are almost certainly gitignored in
     a pnpm+turbo repo, so they should never appear in `included`/`excluded` at all (git simply
     never lists them).
   - What's unclear: This was not directly verified against FeedbackOps's actual `.gitignore`
     content in this research pass.
   - Resolution: Plan 51-02 Task 1 now writes `discover/enumeration-check.json`, quotes the literal
     `enumeration_mode` from discover inventory (or labels a draft-inventory fallback), and records
     explicit `node_modules`/`minio_data` matches across `included` and `excluded`. If neither
     inventory exists, it records `blocked` under the discover OBS-D id instead of asserting the
     expected exclusion. This closes the planning question while preserving the run as authority.

2. **(RESOLVED) Does `apply` ever need `--out`?**
   - What we know: `apply`'s argparse only defines `--task-dir`, `--batch-id`, `--target` — no
     `--out` flag exists on `apply` (only `discover`'s bare `tools.adoption_scan` CLI has `--out`).
   - What's unclear: Nothing — this was directly confirmed by reading `cli.py`'s `argparse`
     wiring; flagging here only so the plan does not invent a nonexistent `--out` flag for `apply`.
   - Resolution: No. Plans use exactly the three-flag form shown in Code Examples for `apply` and
     never invent `--out`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| git | worktree isolation, discover's `git ls-files` fallback path | ✓ | 2.50.1 | — |
| uv | correct-interpreter invocation of every `python -m tools....` command | ✓ | 0.11.6 | — |
| uv-managed Python | `tomllib`/repo code requiring `>=3.11` | ✓ (via `uv run`) | 3.11.15 | — |
| system `python3` | none (must NOT be used directly — Pitfall 1) | ✓ but WRONG version | 3.9.6 | Always invoke via `uv run python`, never bare `python3` |
| node | FeedbackOps `engines` constraint (informational only — this phase never runs node) | ✓ | v22.22.2 | — |
| pnpm | Not invoked by this phase's Python calls; FeedbackOps pins `pnpm@9.15.0` via `packageManager` | ✓ but version-mismatched (11.1.1 vs pinned 9.15.0) | 11.1.1 | Record the mismatch if D-13's "pnpm --version if invoked" ever becomes literally true; otherwise no action needed since this phase never shells out to pnpm |
| `~/Desktop/2026/FeedbackOps` | The real target itself | ✓ | branch `develop` @ `1d1c8ed` | — |

**Missing dependencies with no fallback:** none.

**Missing dependencies with fallback:** system `python3`'s wrong version — fallback is simply
"always use `uv run python`" (already this repo's documented convention per `AGENTS.md` §C).

## Validation Architecture

This phase's "test framework" is the evidence record itself — there is no application code to
unit-test, and the phase's success criteria are about *what a real run produced*, which only a
real run (not a mock/unit test) can validate. The table below maps each ROADMAP success criterion
to how it is checked, honoring the instruction that a refuted OBS-03 hypothesis is a PASS, not a
failure.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None (no unit-test framework applies to an evidence-capture phase); validation is the evidence record's own internal consistency plus re-runnability |
| Config file | none |
| Quick run command | `git -C .planning/phases/51-real-target-observation-baseline status --porcelain` (confirms only planning-artifact files changed — a fast pre-commit sanity check, not a test) |
| Full suite command | Manual replay: re-run every argv cited in `51-BASELINE-EVIDENCE.md`'s `reproduction` fields from a fresh worktree and diff exit codes / key JSON fields against the recorded excerpts |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| Success Criterion 1 (baseline run + byte-unchanged proof) | discover/draft/apply attempted in order; original checkout unchanged | manual/evidence-replay | `diff before.index.sha256 after.index.sha256 && diff before.status.txt after.status.txt && diff before.untracked-set.sha256 after.untracked-set.sha256` | ❌ Wave 0 — these three digest files are the phase's own deliverable, created by its tasks, not pre-existing |
| Success Criterion 2 (every defect has symptom · reproduction · code location) | every `OBS-D-NN` record in `51-BASELINE-EVIDENCE.md` has all three fields non-empty | manual review (structural, not automatable without a new parser — D-09 forbids adding one) | grep-based spot check: `grep -c '^### OBS-D-' 51-BASELINE-EVIDENCE.md` vs a manual read confirming each has `symptom`/`reproduction`/`code location` | ❌ Wave 0 — the record itself is this phase's output |
| Success Criterion 3 (OBS-03 reproducible verdict) | `## OBS-03 verdict` section quotes a literal excerpt + `path:line` | manual review against the captured `evidence/downstream/package-facts.json` (or the discover-stage `inventory.json`'s dependency data) | `grep -A5 '## OBS-03 verdict' 51-BASELINE-EVIDENCE.md` | ❌ Wave 0 |
| Success Criterion 4 (no repair precedes the evidence record) | zero diffs under `tools/`, `harness/`, `contracts/`, `docs/adr/` for the duration of this phase | automatable | `git status --porcelain -- tools/ harness/ contracts/ docs/adr/` (expect empty) at every commit in this phase | ✓ — this is a standard `git` invocation, always available |

### Sampling Rate
- **Per task commit:** `git status --porcelain -- tools/ harness/ contracts/ docs/adr/` (must be
  empty — NG-01/D-11 enforcement) plus a check that only `.planning/phases/51-*/` paths changed.
- **Per wave merge:** re-verify the before/after isolation digests are still recorded and equal, and
  that the `OBS-D-NN` summary table's ids match the detail sections 1:1.
- **Phase gate:** `51-BASELINE-EVIDENCE.md` exists, has a non-empty `## OBS-03 verdict` section
  with a literal quoted excerpt, and the worktree has been disposed of (`git worktree list` at
  `~/Desktop/2026/FeedbackOps` shows no leftover entry) before `/gsd:verify-work` runs.

### Wave 0 Gaps
- [ ] `.planning/phases/51-real-target-observation-baseline/evidence/isolation/{before,after}.*` —
  the six isolation-proof artifacts (D-03) don't exist until the first task runs.
- [ ] `51-BASELINE-EVIDENCE.md` itself — the OBS-01 deliverable, created by this phase's tasks.
- No test-framework install is needed (there is no application code); the only "gap" is the
  evidence files themselves, which the plan's tasks create as their primary output.

## Security Domain

This phase introduces no new code, no new endpoint, no new dependency, and touches no
authentication/session/crypto surface — the ASVS table below is included per protocol but every
row resolves to "not applicable" or "already covered by existing, unmodified controls."

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface touched or created |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A — the only access-control-flavored logic exercised (constitution-plane refusal in `apply.py`/`destinations.py`) is pre-existing, unmodified code being *observed*, not authored here |
| V5 Input Validation | partial | `tools.adoption_scan.scan`'s existing secret-content/secret-path classifiers and `apply.py`'s existing path-escape/symlink/constitution refusals are the standard controls already in place; this phase's job is to observe whether they behave correctly against a real external tree, not to author new validation |
| V6 Cryptography | no | No crypto code touched; `sha256` hashing used throughout is content-addressing, not a security boundary |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation (already shipped, observed not authored) |
|---------|--------|---------------------------------------------------------------|
| Path traversal / absolute-path escape during `apply` writes | Tampering | `refuse_unsafe_destination()` (`tools/adoption_apply/apply.py:109-201`) — already covers `..`-segments, absolute paths, symlink escapes, directory-shaped destinations, non-directory-ancestor collisions |
| Constitution-plane write via case-variant/symlink spelling | Elevation of Privilege | `refuse_if_constitution()` reused from `tools.hooks.contract_guard.CONSTITUTION_GLOBS`, called structurally in-process (independent of any Claude tool-call hook) |
| Secret leakage from a scanned target into a committed evidence artifact | Information Disclosure | `scan.py`'s `classify_exclusions()` never records content or an excerpt for an excluded file — only `{path, size, excluded}` (D-10 in that module); the evidence-capture plan must preserve this discipline when quoting `inventory.json`/`manifest.json` excerpts into `51-BASELINE-EVIDENCE.md` (never quote raw file content from FeedbackOps beyond what the pipeline itself already surfaces in its own JSON output) |

## Sources

### Primary (HIGH confidence — direct code read, this checkout, 2026-07-31)
- `tools/adoption_scan/{cli.py,detect.py,scan.py,plan.py,destinations.py}` — discover stage argv,
  detection rules, disposition chain
- `tools/adoption_apply/{cli.py,batch.py,apply.py}` — draft/apply argv, batch layout, atomic-write
  and refusal mechanics
- `tools/memory_regen/package_facts.py` — dependency-edge resolution, `repo_root`/`cfg` parameters,
  the `main()`/CLI's lack of a target flag
- `tools/harness_config/loader.py` — `conventions_for()`, `effective_packages()`, the
  `harness/project.toml`-anchored `_DEFAULT_PROJECT`
- `harness/project.toml` — the core `[[languages]]` table (dotnet + python only, no JS/TS)
- `harness/commands/adopt.md`, `harness/skills/brownfield-adoption/SKILL.md` — the documented
  runbook, cross-checked against the code above (no material disagreement found; the only drift is
  a stale illustrative `.workflow/tasks/` path in `destinations.py`'s own docstring, noted in State
  of the Art)
- `tools/adoption_scan/tests/{test_readonly.py,test_dispositions.py}`,
  `tools/adoption_apply/tests/test_cli.py` — proof of read-only-ness, disposition totality, and the
  deleted-lifecycle-plane confirmation
- `tools/hooks/contract_guard.py` — `CONSTITUTION_GLOBS` definition
- `tools/harness_emit/manifest.py` — `is_gsd_owned()` exclusion predicate
- `~/Desktop/2026/FeedbackOps/{pnpm-workspace.yaml,package.json}`,
  `~/Desktop/2026/FeedbackOps/{packages/ui,packages/shared,apps/frontend,apps/backend}/package.json`
  — read live in this research session; the literal declared dependency names/edges quoted in the
  Summary are copied verbatim from these files
- `.planning/{CONTEXT.md (51-),REQUIREMENTS.md,ROADMAP.md,STATE.md,config.json}`, root `AGENTS.md` —
  read live in this research session

### Secondary (MEDIUM confidence)
- None — no external web sources were needed; this phase's entire domain is internal code + one
  real, directly-readable target repository.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every version number was captured via a live command in this exact
  environment during this research session, not recalled from training data.
- Architecture: HIGH — every invocation form (argv, flags, defaults) was read directly from
  `argparse` wiring in this checkout, not inferred from documentation.
- Pitfalls: HIGH for Pitfalls 1-4 (each traced to specific `path:line` code); MEDIUM for Pitfall 5
  (extension list read directly, but the actual `.gitignore`/full file listing of FeedbackOps was
  not exhaustively enumerated in this pass — noted as Open Question 1).

**Research date:** 2026-07-31
**Valid until:** This research is tied to a specific pinned commit of both repos
(`lifetimeworkflow` at the current branch tip, FeedbackOps `develop` @ `1d1c8ed`). It should be
treated as valid only until either repo's relevant code changes — re-verify the `path:line`
citations if `tools/adoption_scan`, `tools/adoption_apply`, `tools/memory_regen/package_facts.py`,
`tools/harness_config/loader.py`, or FeedbackOps's manifests change before this phase executes.
