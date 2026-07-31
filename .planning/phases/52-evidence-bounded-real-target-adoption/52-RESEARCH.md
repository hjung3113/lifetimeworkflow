# Phase 52: Evidence-Bounded Real-Target Adoption - Research

**Researched:** 2026-07-31
**Domain:** Repair of a Python brownfield-adoption toolchain (`tools/adoption_scan`, `tools/adoption_apply`, `tools/harness_config`) against a real pnpm/turbo JS monorepo, bounded strictly to four evidence-classified defects from Phase 51.
**Confidence:** HIGH for code-location claims (all read directly in this checkout and cross-checked against the real target); MEDIUM for pnpm-workspace.yaml semantics (WebSearch, cross-verified against the real target's file); LOW/flagged where a design choice is explicitly left to Claude's discretion by CONTEXT.md and this research could not close it with certainty (lock-sidecar "ignore set" mechanism).

## Summary

This is a repair phase, not a build phase. Every one of the four defects it may touch (OBS-D-01,
OBS-D-03, OBS-D-04) has an exact, already-read code location, and OBS-D-02 needs a test only. The
research below traces each defect from symptom to the precise function that must change, and — the
decisive finding for planning — identifies which repairs are pure code/test changes and which touch
a `contracts/**/*.schema.json` file (triggering the contract-first gate chain: schema edit →
`/contract-check` → schema-hash drift gate → golden update).

**Primary recommendation:** OBS-D-03 (add `lint` key) and OBS-D-04 (declare lock sidecars) are pure
code+test changes with **zero contract impact** — confirmed by direct inspection of both consumers
and both `contracts/harness/adoption/*.schema.json` files. OBS-D-01 (pnpm workspace scoping) is the
one repair with a real, non-obvious contract-schema decision point: if the `skipped` diagnostic list
(D-08) is added as a new top-level `inventory.json` key, `contracts/harness/adoption/
inventory.schema.json` MUST change (it declares `"additionalProperties": false` and an enumerated
`required` list) — the planner must budget a contract-entry task, `/contract-check`, and a golden
update for this, or find an existing key to reuse instead of adding one.

The real FeedbackOps `pnpm-workspace.yaml` was read directly from the live original checkout
(`~/Desktop/2026/FeedbackOps/pnpm-workspace.yaml`, outside the disposed Phase-51 worktree) and
contains exactly:
```yaml
packages:
  - "apps/*"
  - "packages/*"
```
This is the ground truth the OBS-D-01 repair and its regression fixture must reproduce: two glob
entries, no negation, root implicitly included by pnpm semantics — and it is why
`docs/design-prototype/package.json` is the one non-member manifest observed in Phase 51's
inventory (`.planning/phases/51-real-target-observation-baseline/evidence/discover/inventory.json`:
6 manifests/`candidate_process_boundaries` rows enumerated, only 5 required by RTA-02).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| pnpm workspace member scoping (OBS-D-01) | Backend / tool (`tools/adoption_scan/detect.py`, `scan.py`) | — | Pure Python analysis of a scanned target's file tree; no client/server split in this domain. |
| Package facts / dependency edges (RTA-03) | Backend / tool (`tools/memory_regen/package_facts.py`) | — | Reads manifests directly off disk (or an injected `repo_root`); reused unchanged by this phase, not repaired. |
| Convention profile resolution (OBS-D-03/RTA-04) | Backend / tool (`tools/harness_config/loader.py:conventions_for`) | Config data (`harness/project.toml` `[[languages]]` in the TARGET) | Pure join function; the JS `[[languages]]` row it needs is *data* written into the target at draft/apply time, not harness-side logic. |
| Atomic manifest apply + lock sidecars (OBS-D-04) | Backend / tool (`tools/adoption_apply/apply.py`) | Filesystem (target `.gitignore`) | Concurrency-safe local file writes; the "ignore set" half of D-15 is a target-repo file-system artifact, not a service boundary. |
| Contract schema (possible OBS-D-01 shape change) | Constitution plane (`contracts/harness/adoption/inventory.schema.json`) | — | Governs the artifact shape every downstream tier (draft, apply, review) reads; a shape change here is gated (CODEOWNERS + schema-hash + golden). |

No browser/CDN/database tier exists in this domain — everything is a local CLI tool operating on a
filesystem target, consistent with the rest of this harness.

## User Constraints (from CONTEXT.md)

<user_constraints>

### Locked Decisions

- **D-01:** Phase 52 starts from a **freshly created** worktree (the Phase-51 one is disposed),
  created the Phase-51 way: `git -C ~/Desktop/2026/FeedbackOps worktree add --detach <path> <SHA>`,
  outside the `develop` working tree, detached HEAD.
- **D-02:** Pin the target to `develop`'s HEAD **as read at phase start** (re-read and record the
  literal SHA at run time — `develop` is now past the `1d1c8ed` Phase-51 baseline and past the
  `4f16525` STATE.md snapshot; both are stale). Repairs are proven by repo-local fixtures, not by SHA
  identity with Phase 51.
- **D-03:** SC-1 "byte-unchanged" uses the Phase-51 D-03 three-artifact proof (`status
  --porcelain=v2 --untracked-files=all`; `rev-parse HEAD` + tracked-index digest; untracked path-set
  digest), captured before AND after against a snapshot taken at phase start. Any HEAD/index delta
  is attributed by reconstructing index digests from the target's commit trees, recorded outside the
  OBS-D namespace.
- **D-04:** The worktree is auto-disposed at phase end (`git worktree remove --force`, exit code
  recorded). No human disposal checkpoint.
- **D-05:** Run depth: full discover → draft → apply into the fresh worktree, **after** repairs
  land, plus the Phase-51 D-12 read-only downstream observations
  (`tools.memory_regen.package_facts`, `tools.harness_config.loader:conventions_for`). These
  downstream reads evidence SC-3/SC-4.
- **D-06:** Zero writes to FeedbackOps product code. Harness artifacts written into the worktree are
  in scope; anything touching target application source is a defect.
- **D-07:** Repair at the source: teach `tools/adoption_scan/detect.py`
  (`_MANIFEST_KIND_BY_NAME`, `detect.py:46`) the pnpm workspace manifest. When
  `pnpm-workspace.yaml` exists at the target root, the workspace member set is its declared globs;
  manifests outside those globs are not members. Not an ignore-glob blacklist, not a downstream
  filter in draft — the inventory itself must be right (RTA-02).
- **D-08:** Non-member manifests found during the walk are excluded from the inventory but emitted
  in a `skipped` diagnostic list — visible, not silently dropped.
- **D-09:** pnpm only. No speculative `package.json` `workspaces`, Cargo, or uv workspace support
  (NG-01, and Phase-51 D-17's "no fixture without an actual repair").
- **D-10:** When no workspace manifest is present, current recursive manifest discovery is
  unchanged — additive branch only.
- **D-11:** Add `lint` to the fixed key set returned by `conventions_for`
  (`tools/harness_config/loader.py:297`), `None` when the language has no configured value. Shape
  change, not a null to populate — the key is always present.
- **D-12:** JS lint/test commands are derived from the adopted target's own `package.json` scripts
  at draft time and written into the target's emitted `harness/project.toml` `[[languages]]` row —
  not hardcoded JS defaults in the harness template.
- **D-13:** No contract impact for OBS-D-03. `contracts/normalization/format-conventions.schema.json`
  governs §4.3–4.6 canonicalization only, not the per-package convention profile.
- **D-14:** Nearest-wins resolution semantics unchanged — only the key set widens. Every existing
  `conventions_for` resolution test stays green as-is.
- **D-15:** `.AGENTS.md.lock` / `.CLAUDE.md.lock` / `.claude/.settings.json.lock` sidecars are **not
  unlinked** (unlink-after-release is the classic race). They are declared as known
  harness-managed artifacts so the apply comparison's `matches` is true, and added to the target's
  ignore set.
- **D-16:** A stale lock encountered on a later run is reported on stderr, never silently reused.
- **D-17:** Regression tests are repo-local, one per repaired observation, sited next to the tool
  they cover (`tools/adoption_scan/tests/`, `tools/harness_config/tests/`,
  `tools/adoption_apply/tests/`), driven by a synthetic pnpm workspace fixture. The live FeedbackOps
  worktree is confirmation evidence only, never a test dependency.
- **D-18:** OBS-D-02 gets a lock-in test even though it needs no repair: a regression test asserting
  `packages/shared` → `apps/frontend`/`apps/backend` runtime edges resolve from `workspace:*`
  dependencies, so the OBS-03 refutation cannot silently regress.
- **D-19:** Each repair carries an explicit trace line to its OBS-D id and purpose tag. An
  observation with no repair must terminate in either a lock-in test or a written evidence-backed
  confirmation — SC-5 admits no third outcome.

### Claude's Discretion

- Exact fresh-worktree path and evidence sub-file naming.
- Shape of the `skipped` diagnostic list (key name, per-entry fields) in the inventory artifact.
- Synthetic pnpm fixture layout and where it lives, subject to D-17's "next to the tool" siting.
- How the lock-sidecar declaration is expressed (managed-artifact list vs comparison exclusion),
  provided `matches` becomes true without weakening the comparison for real unlisted writes.
- Plan decomposition and task ordering within the phase.

### Deferred Ideas (OUT OF SCOPE)

- **MONO-12 / managed `/adopt` update semantics** — Phase 53.
- **DEBT-01 `"dir"`-filter shared helper** — Phase 54.
- **Second target repo (vocpage)** — Future Requirements.
- **Non-pnpm workspace formats** (npm/yarn `workspaces`, Cargo, uv) — deliberately unbuilt (D-09).
- **OBS-03 (pnpm `workspace:*` edge resolution)** — REFUTED in Phase 51. `detect.py:273` already
  discards version strings and resolves by name; spending any budget "fixing" this is a scope
  violation. OBS-D-02 only gets a lock-in test (D-18), never a code change.

</user_constraints>

## Phase Requirements

<phase_requirements>

| ID | Description | Research Support |
|----|-------------|------------------|
| RTA-01 | Developer runs `/adopt` discover→draft→apply against an isolated FeedbackOps worktree; original `develop` stays byte-unchanged | §4 below: exact command sequence, reusing Phase-51's literal argv and the D-03 three-artifact proof shape. |
| RTA-02 | Discover inventories exactly the 5 real pnpm workspace members | §1: `detect.py:46` manifest-kind table + `scan.py` walk; real `pnpm-workspace.yaml` content confirmed (`packages: ["apps/*", "packages/*"]`); the decisive `inventory.schema.json` `additionalProperties:false` constraint for the `skipped` list. |
| RTA-03 | Package facts show `packages/shared` → `apps/frontend`/`apps/backend` edges | §1 (shared `detect.detect_manifests`/`detect_dependencies` reuse by `package_facts.py`) + §OBS-D-02 lock-in test (no repair needed — already correct). |
| RTA-04 | Each package resolves a nearest-wins convention profile with lint+test commands | §2: `conventions_for()` shape change at `loader.py:297`, all 3 call sites enumerated, blast radius (13 existing tests) named. |
| OBS-02 | Purpose-①②③④ defects repaired with regression tests; no-change observations stay evidence-backed | §5 Validation Architecture: per-SC signal table, repo-local test siting per D-17/D-18. |

</phase_requirements>

## Standard Stack

No new external tooling for the *tests* — everything reuses `pytest`, the repo's own `tools.*`
packages, and stdlib. One genuinely new question is whether OBS-D-01's pnpm-workspace.yaml parsing
needs a YAML library.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `ruamel.yaml` | **0.19.1** [VERIFIED: already resolved in `uv.lock` and importable in this workspace's synced `.venv` — confirmed live: `uv run python -c "import ruamel.yaml; print(ruamel.yaml.__file__)"` succeeded] | Parse `pnpm-workspace.yaml`'s `packages:` glob list | Already a **transitive** dependency of `check-jsonschema` (root `dev` group, `pyproject.toml:20`) — no new download, no new supply-chain surface. Using it directly for a real (if narrow) YAML-parsing need is preferable to hand-rolling a YAML-subset parser (violates "Don't Hand-Roll" for a format with quoted-string, list, and comment edge cases even in its minimal form). |

**Decisive footnote:** `tools/adoption_scan/pyproject.toml:6-9` states as a design invariant: *"Zero
new external packages. All stdlib ... jsonschema (schema-conformance tests) and pytest come from
the workspace root runtime/dev groups; nothing declared here, so `uv sync --all-packages` must not
mutate `uv.lock`."* [VERIFIED: `tools/adoption_scan/pyproject.toml:6-9`] Depending on `ruamel.yaml`
from `detect.py` would depend on a **dev-group-only** transitive package from **non-dev** module
code — fragile if `check-jsonschema` is ever bumped/removed, and it contradicts this file's own
stated invariant. **Planner must either (a) add `ruamel.yaml==0.19.1` as an explicit direct
dependency of `tools/adoption_scan/pyproject.toml`** (confirmed zero `uv.lock` resolution change,
since the version is already pinned by the transitive resolution) **and update that file's own
"zero new external deps" docstring to reflect the one exception, or (b) hand-roll a narrow
line-based `packages:`-block parser** scoped to exactly what pnpm's format needs (a YAML list of
quoted/bare glob strings under one top-level key) — defensible here because the real target's file
is 3 lines and pnpm-workspace.yaml's schema is far narrower than general YAML. Given the module's
explicit zero-dep invariant and the real target's minimal file, **(b) is the lower-blast-radius
choice** unless the fixture needs to also exercise multi-line flow-style lists or comments; either
choice is a legitimate task-level decision, not a research gap.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Narrow hand-rolled `packages:` block parser | `ruamel.yaml` (already resolvable) | `ruamel.yaml` is more robust (handles anchors, flow style, comments) but requires declaring + documenting an exception to `adoption_scan`'s explicit zero-new-deps invariant. |
| `PyYAML` | `ruamel.yaml` | `PyYAML` is NOT currently in `uv.lock` at any level [VERIFIED: absent from a `grep -i yaml uv.lock` package-name scan] — choosing it would be a genuinely new dependency requiring a fresh resolution, unlike `ruamel.yaml` which is already pinned. No reason to introduce a second YAML library when one is already resolved. |

**Installation** (only if option (a) above is chosen):
```bash
# tools/adoption_scan/pyproject.toml — add under [project] dependencies:
#   "ruamel.yaml==0.19.1"
# uv.lock already contains this exact version/hash (transitive via check-jsonschema);
# `uv lock --check` after the edit should show no change to the resolved graph.
```

**Version verification:** `uv run python -c "import ruamel.yaml; print(ruamel.yaml.__version__)"` →
confirmed `0.19.1` live in this checkout's synced environment (2026-07-31).

## Package Legitimacy Audit

No package legitimacy check was run: this phase adds **zero new packages to the dependency graph**.
`ruamel.yaml` (if chosen) is already resolved, hashed, and present in the committed `uv.lock` as a
transitive dependency of `check-jsonschema` (`pyproject.toml` dev group). If the hand-rolled parser
is chosen instead, no package audit applies at all.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| ruamel.yaml | PyPI | long-established (multi-year, `ruamel_yaml-0.19.1`, uploaded 2026-01-02 per `uv.lock:693`) | high (canonical YAML lib for Python config tooling; already a transitive dep of this repo's own `check-jsonschema`) | github.com/ruamel/yaml (well-known upstream) | not run (no new install — already resolved) | Approved (no new install) |

**Packages removed due to slopcheck `[SLOP]` verdict:** none.
**Packages flagged as suspicious `[SUS]`:** none.

## Architecture Patterns

### System Architecture Diagram

```
                    FeedbackOps fresh detached worktree (D-01)
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  /adopt discover  (tools.adoption_scan.__main__)     │
        │  scan.build_inventory(target)                        │
        │    └─ enumerate_target()  (git ls-files / builtin)   │
        │    └─ classify_exclusions()                          │
        │    └─ detect.detect_manifests(included)  ◄─ REPAIR: teach
        │         pnpm-workspace.yaml kind + read its globs     │  OBS-D-01
        │    └─ detect.detect_candidate_process_boundaries()   │  (scan.py/
        │         ◄─ REPAIR: filter dirs by workspace globs;   │   detect.py)
        │           non-members → new `skipped` list (D-08)    │
        └───────────────────────┬───────────────────────────────┘
                                 ▼  inventory.json (contract: inventory.schema.json)
        ┌─────────────────────────────────────────────────────┐
        │  /adopt draft  (tools.adoption_scan.plan / cli)      │
        │    └─ classify() → questions/proposals                │
        │    └─ derive JS lint/test from target package.json   │  ◄─ REPAIR:
        │         scripts → write into emitted                 │    D-12
        │         harness/project.toml [[languages]] JS row     │
        └───────────────────────┬───────────────────────────────┘
                                 ▼  plan.json, manifest.json (manifest.schema.json)
        ┌─────────────────────────────────────────────────────┐
        │  /adopt apply  (tools.adoption_apply.apply)          │
        │    └─ apply_manifest() → apply_disposition()          │
        │    └─ _apply_marker_merge() (AGENTS.md/CLAUDE.md/     │  ◄─ REPAIR:
        │         .claude/settings.json)                        │    D-15/D-16
        │         creates .NAME.lock sidecar (flock-guarded)    │    declare as
        │         ◄─ declare as known artifact, add to target   │    known, not
        │           .gitignore (category already in             │    unlinked
        │           destinations.py:_CATEGORY_GLOBS)             │
        └───────────────────────┬───────────────────────────────┘
                                 ▼  applied target tree
        ┌─────────────────────────────────────────────────────┐
        │  Downstream read-only observations (D-05/D-12)        │
        │    tools.memory_regen.package_facts.build_facts(       │  RTA-03
        │      repo_root=target)  → dependency edges             │
        │    tools.harness_config.loader.conventions_for(         │  RTA-04
        │      pkg_dir, cfg=target_cfg, facts=target_facts)       │  ◄─ REPAIR:
        │      → package/dir/language/test/format/lint/           │    D-11 add
        │        bash_scope/agents_md/is_default                  │    `lint` key
        └─────────────────────────────────────────────────────┘
```

### Recommended Project Structure

No new top-level directories. Repairs land in existing modules; new tests land in existing test
dirs per D-17:
```
tools/adoption_scan/
├── detect.py              # OBS-D-01: pnpm-workspace.yaml kind + glob parsing
├── scan.py                # OBS-D-01: filter candidate_process_boundaries + emit `skipped`
├── tests/
│   ├── conftest.py        # extend tmp_minirepo OR add a second synthetic pnpm-workspace fixture
│   └── test_detect.py     # new pnpm-workspace tests
tools/harness_config/
├── loader.py               # OBS-D-03: `lint` key added to conventions_for()'s return dict
├── tests/test_conventions_for.py  # extend for the new key (13 existing tests to keep green)
tools/adoption_apply/
├── apply.py                # OBS-D-04: declare lock sidecars as known/expected
├── destinations.py          # candidate site for a `LOCK_SIDECARS` constant + .gitignore line data
├── tests/test_atomic_apply.py  # extend at/after :267 comment block
```

### Pattern 1: Injectable-pure functions with optional `cfg`/`facts`
**What:** Every function that needs config/facts state accepts them as optional keyword params,
defaulting to a real load only when omitted (`load_project()`, `build_facts()`).
**When to use:** Any new function this phase adds (e.g. a `parse_pnpm_workspace(text)` helper, or a
`conventions_for` extension) must follow this so tests never need monkeypatch or a temp-file config.
**Example:**
```python
# Source: tools/harness_config/loader.py:297 (existing pattern to extend, not replace)
def conventions_for(path: str, cfg: dict | None = None, facts: dict | None = None) -> dict:
    if cfg is None:
        cfg = load_project()
    ...
```

### Pattern 2: "Own the constant locally" for scan-time detection tables
**What:** `scan.py`/`detect.py` deliberately duplicate small constants (`SECRET_PATH_GLOBS`,
`SECRET_CONTENT_PATTERNS`) rather than importing them from a retired task-control contract, per an
explicit "own it locally" idiom documented in `scan.py:52-71`.
**When to use:** A pnpm-workspace glob-matching helper should be a small, locally-owned pure
function in `detect.py` (mirroring `_dependencies_from_package_json(text)`'s shape: pure function
taking already-read `text`, never touching the filesystem itself) — NOT a filesystem-reading
function, to preserve `detect.py`'s documented "no filesystem access" purity guarantee
(`detect.py:6-8`: *"Operates purely on the `included` list already assembled by `scan.py` ... no
filesystem access here, so detection can never diverge from what was actually hashed"*).

### Anti-Patterns to Avoid
- **Reading `pnpm-workspace.yaml` from disk inside `detect.py`:** breaks the module's own documented
  invariant that detection never diverges from what `scan.py` already hashed. The correct split:
  `scan.py`'s `build_inventory()` (which already has `target: Path` and already opens files for
  `classify_exclusions`) reads the workspace manifest's text once, and passes it to a new pure
  `detect.py` function — exactly the `detect_dependencies(path, kind, text)` precedent
  (`detect.py:360-372`).
- **Filtering workspace membership only in `plan.py` (draft stage):** D-07 explicitly forbids this —
  "not a downstream filter in draft — the inventory itself must be right." The fix belongs in
  `scan.py`/`detect.py`, before `plan.py` ever sees the inventory.
- **Unlinking `.lock` sidecars after use (OBS-D-04):** explicitly called out as the wrong fix by
  D-15 (classic unlink-race — a concurrent holder can `flock` a deleted inode). Do not touch
  `_apply_marker_merge`'s locking logic (`apply.py:292-321`) itself.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| General YAML parsing | A hand-rolled full YAML parser | `ruamel.yaml` (already resolved) OR a narrowly-scoped `packages:`-block-only line parser (acceptable here because pnpm-workspace.yaml's schema for `packages:` is a bounded list-of-glob-strings, not general YAML) | Full YAML has enough edge cases (anchors, multi-doc, flow mappings) that a hand-rolled general parser is a classic footgun; a *narrow* parser scoped to exactly `packages:` + optional `!`-negated entries is a defensible, bounded exception — document the boundary explicitly if chosen. |
| Glob-to-path matching against pnpm semantics | Reusing `pathlib.Path.glob()` unmodified | A small adapter: `Path.glob()` does not support `!`-negation natively and its `**` semantics differ subtly from pnpm's (pnpm's is closer to `micromatch`/`picomatch`). For the real target's exact file (`packages/*`, `apps/*`, no `**`, no negation), a direct glob-per-entry with `Path.glob(pattern)` intersected with candidate manifest directories is sufficient and correctly scoped to the observed input — do not build negation/`**` handling `D-09`/NG-01 explicitly forbid speculative generality here. |
| Comparing before/after target state for "unlisted writes" | A new shared comparison library/module | Reuse the exact plan-inline bash/python idiom Phase 51 already used for `worktree.changed-paths.json`'s `unexpected_paths`/`matches` fields — that logic lives inline in `.planning/phases/51-real-target-observation-baseline/51-02-PLAN.md` task actions, **not** in any `tools/` module, confirming it is intentionally plan-local, not a shared tool that would need to change. |

**Key insight:** Every one of this phase's four repairs has an existing, narrower idiom already in
this codebase to imitate (own-the-constant-locally, injectable-pure-cfg/facts, text-passed-not-read,
plan-inline comparison scripts) — the repair work is "match the established pattern," not "design a
new one."

## Common Pitfalls

### Pitfall 1: Adding `skipped` silently breaks `inventory.schema.json` conformance
**What goes wrong:** `contracts/harness/adoption/inventory.schema.json` declares
`"additionalProperties": false` at the top level and an explicit `required` array
(`inventory.schema.json:6-22`). Emitting a new `skipped` key from `scan.build_inventory()` without
updating this schema makes every artifact schema-conformance test start failing (there is an
existing `tools/adoption_scan/tests/test_schema_conformance.py` that almost certainly validates
against this exact file).
**Why it happens:** The temptation is to treat `skipped` as "just another optional field," but this
schema's whole design (self-contained Draft 2020-12, `additionalProperties: false`,
D-11/D-10-referenced in its own `description`) makes every key change a first-class contract event.
**How to avoid:** Treat the `skipped` list addition as a genuine contract change from the start:
add the key + its `$defs` shape to `inventory.schema.json`, run
`bash tools/contract_drift/check.sh` (or `python -m tools.contract_drift.drift`), and pair it with
whatever golden fixtures the adoption test suite treats as approved output (check
`tools/adoption_scan/tests/test_snapshots.py` for approval-style fixtures this would need to
update). **Alternative that avoids the contract change entirely:** since `excludedEntry` already has
an `excluded` enum with 8 reason values (`inventory.schema.json:106-117`, none of which currently
say "not-a-workspace-member"), consider whether non-member manifests could instead be recorded as
`excluded` entries with a new enum value (e.g. `"non-workspace-member"`) — this is STILL a schema
change (enum extension), but a smaller, more surgical one than a whole new top-level array, and
keeps the "excluded vs included" ladder in one place rather than introducing a second parallel
list. Flagging both options for the planner to choose between; CONTEXT.md leaves the exact shape to
Claude's discretion but does not resolve the contract-impact question either way.

### Pitfall 2: `conventions_for()`'s `dir_pkgs` filter and stderr diagnostic must survive the `lint`-key edit untouched
**What goes wrong:** `loader.py:297-353` has load-bearing logic between the docstring and the
return statement (the `"dir" not in p and "manifest" in p` malformed-record diagnostic at
`loader.py:331-338`, and the `dir_pkgs` filter it feeds). A careless edit that only touches the
final `return {...}` dict (adding `"lint": lang["lint"] if lang else None`) is safe, but if the edit
also touches `languages(cfg)` shape assumptions, it could silently break `tools/contract_graph/
impact.py:178-185`'s own copy of the identical "dir"-key filter adapter (documented explicitly as a
DEBT-01 duplication, deferred to Phase 54 — do not fix it here, just don't let it silently diverge
from `loader.py`'s new key).
**Why it happens:** Two call sites (`package_facts.py:319`, `impact.py`) both consume
`conventions_for()`'s return shape; a third (`tools/harness_config/tests/test_conventions_for.py`,
13 existing tests) asserts the exact key set today.
**How to avoid:** Grep-verify all three call sites after the edit
(`grep -rn "conventions_for(" --include="*.py" .`) and run the full `tools/harness_config` +
`tools/contract_graph` test suites, not just the touched module's own tests.
**Warning signs:** Any test asserting `set(profile.keys()) == {...}` without `lint` in the literal
will fail loudly — that is the intended, correct failure (D-11 is a deliberate shape change), not a
regression to chase.

### Pitfall 3: `harness/project.toml`'s `[[languages]]` schema has no formal contract — but two consumers assume its shape
**What goes wrong:** `harness/project.toml` is pure DATA with no JSON-schema contract governing it
(`loader.py` docstring: "Pure I/O + shape: NO enforcement logic — that belongs to
`tools.harness_lint`'s consistency test"). Writing a derived JS `[[languages]]` row into a *target's*
emitted `harness/project.toml` at draft time (D-12) must still supply every key the existing
`tools/harness_lint/tests/test_language_config.py` consistency gate expects for a language table
(`id`, `bash_scope`, `test`, `format`, and now presumably `lint`) — but that gate runs against
**this repo's own** `harness/project.toml`, not the target's emitted copy, so it will not catch a
malformed target row. The only thing that WILL catch it is `conventions_for()` being called against
the target's own config at the downstream-observation step (D-05).
**Why it happens:** No schema exists for `[[languages]]` rows; consistency is enforced by a gate
that is scoped to this repo, not to adopted targets.
**How to avoid:** The regression test for D-12 (JS lint/test derivation) should assert the emitted
`[[languages]]` row's exact key set against what `conventions_for()` (post-D-11) expects to read,
not just "a JS row exists" — otherwise a malformed row could pass silently until the real-target run.

### Pitfall 4: `refuse_unsafe_destination`'s constitution-plane check is case-lowered — a `.gitignore` line addition for lock sidecars must go through the same `create`/`preserve`/`conflict` chain, not a bespoke write
**What goes wrong:** `.gitignore` is already a real row in `destinations.py:_CATEGORY_GLOBS` (line
180), meaning the harness's OWN `.gitignore` is already a governed adoption destination
(`create`/`preserve`/`conflict` depending on whether the target has one). If D-15's "added to the
target's ignore set" is implemented as a bespoke direct-write bypassing `apply_disposition()`, it
sidesteps `refuse_unsafe_destination`'s constitution/confinement checks and the idempotence
guarantee every other destination gets.
**Why it happens:** `.gitignore` is NOT in `MARKER_CAPABLE` (`destinations.py:117`), so if the
target already has a `.gitignore` (as FeedbackOps' pnpm/turbo monorepo certainly does), the
disposition chain's existing-file comparison will likely resolve to `conflict` for a plain content
edit — meaning simply appending 3 lines to the harness's *template* `.gitignore` will not
automatically merge into an existing target `.gitignore`.
**How to avoid:** This is a genuinely open design question, not resolved by this research — flag it
for the planner as **Open Question 1** below rather than assume a mechanism.
**Warning signs:** A "silently overwrites the target's real `.gitignore`" bug, or a `conflict`
disposition where the phase's own success proof needed the lines to land.

## Runtime State Inventory

Not a rename/refactor/migration phase in the DEBT-01/renaming sense — skip.

## Code Examples

### The existing `(path, kind, text)` pure-parser pattern to extend for pnpm-workspace.yaml
```python
# Source: tools/adoption_scan/detect.py:273-284 (existing, to imitate — not a real pnpm parser)
def _dependencies_from_package_json(text: str) -> list[dict]:
    """Parse ``dependencies`` (runtime) and ``devDependencies`` (dev) keys; version values
    ignored."""
    data = json.loads(text)
    entries: list[dict] = []
    for name in data.get("dependencies") or {}:
        entries.append({"name": name, "kind": "runtime"})
    for name in data.get("devDependencies") or {}:
        entries.append({"name": name, "kind": "dev"})
    return entries
```
A `parse_pnpm_workspace_globs(text: str) -> list[str]`-shaped function belongs beside this,
following the identical "pure function over already-read text" contract.

### The existing malformed-record stderr-diagnostic idiom to extend if a JS row is missing a key
```python
# Source: tools/harness_config/loader.py:330-338 — the pattern for surfacing a data defect on
# stderr rather than silently dropping/crashing, reusable for a malformed derived [[languages]]
# JS row (Pitfall 3 above).
for p in pkgs:
    if "dir" not in p and "manifest" in p:
        print(
            f"conventions_for: package {p.get('id')!r} has 'manifest' but no 'dir' — "
            "excluded from ownership resolution (malformed record, not a declared-only "
            "component)",
            file=sys.stderr,
        )
```

### Confirmed real-target ground truth (read directly, not from Phase-51 evidence)
```bash
$ cat ~/Desktop/2026/FeedbackOps/pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```
`[VERIFIED: read live from ~/Desktop/2026/FeedbackOps/pnpm-workspace.yaml on 2026-07-31]` — this is
the exact glob shape the OBS-D-01 repair and its synthetic fixture must reproduce.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `detect.py` recognizes 4 manifest kinds (`pyproject.toml`, `package.json`, `go.mod`,
`Cargo.toml`) + `*.csproj` suffix, with no workspace-scoping concept | Add a 5th, pnpm-specific
workspace-manifest recognition + scoping step (this phase, pnpm only per D-09) | Proposed by this
phase | `candidate_process_boundaries`/`manifests` (and, if not carefully scoped, `package_facts`
for THIS repo too — verified to be a no-op here since this repo has no `pnpm-workspace.yaml`) become
workspace-aware for the first time. |

**Deprecated/outdated:** none — this is additive, not a replacement of an existing approach (D-10
requires the no-workspace-manifest path stays byte-identical).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `check-jsonschema`'s `ruamel.yaml` dependency will remain resolvable at the pinned `0.19.1` version through this phase's execution window | Standard Stack | Low — `uv.lock` is committed; the version is fixed regardless of upstream changes unless someone re-runs `uv lock --upgrade`. |
| A2 | pnpm's glob-matching semantics for `!`-negation and `**` (WebSearch-sourced, not verified against pnpm's own source or a live `pnpm` binary in this environment) are as described (last-match-wins, negation via `!`-prefix) | Don't Hand-Roll table | Medium if the fixture/regression test exercises negation or `**` — but D-09/NG-01 scope this phase to exactly the real target's file, which uses neither, so the risk is contained to speculative generality the phase should not build anyway. |
| A3 | No existing `tools/adoption_scan/tests/test_schema_conformance.py` or `test_snapshots.py` assertion already accounts for a `skipped`/non-member-manifest concept (i.e., the contract-impact finding in Pitfall 1 is real, not already handled) | Common Pitfalls / Standard Stack | Medium — these two test files were not read line-by-line in this research pass (only located); the planner's task-authoring step should read them before deciding whether `inventory.schema.json` truly needs a change or whether an existing hook already covers it. |

## Open Questions

1. **Mechanism for "the target's ignore set" (D-15's second half)**
   - What we know: `.gitignore` is already a governed adoption destination
     (`destinations.py:_CATEGORY_GLOBS` line 180) subject to the 6-value disposition chain; it is
     NOT marker-capable, so an existing target `.gitignore` most likely resolves to `conflict` on a
     naive content diff rather than auto-merging new lines.
   - What's unclear: whether D-15 intends (a) patching the *harness template's own* `.gitignore`
     (this repo's, under `_REPO_ROOT`) so a future `create`-disposition install carries the lines
     into a target with no pre-existing `.gitignore`, (b) making `.gitignore` marker-capable (a
     bigger design change touching `MARKER_CAPABLE` and the merge idiom), or (c) treating "ignore
     set" as scoped only to this **phase's own** apply-vs-comparison logic (an allowlist in the
     phase-52 evidence script, not a real file write into the target at all) — mirroring how Phase
     51's `matches`/`unexpected_paths` logic was itself plan-inline, not a `tools/` module.
   - Recommendation: default to (c) — cheapest, lowest-risk, and consistent with the precedent that
     comparison/evidence logic in this milestone lives in the phase's own plan-inline scripts, not
     in a shared tool. Only pursue (a)/(b) if the planner decides the *literal* target repository
     must gain a durable `.gitignore` change as a first-class adoption artifact (which the CONTEXT.md
     wording "added to the target's ignore set" arguably implies, but does not require).

2. **Which contract-impact path for OBS-D-01's `skipped` list (Pitfall 1)**
   - What we know: `inventory.schema.json`'s `additionalProperties: false` + `required` array means
     any new top-level key is a schema-hash-visible contract change; an alternative is extending the
     existing `excludedEntry.excluded` enum instead of adding a parallel array.
   - What's unclear: which shape the planner/discuss-phase prefers, and whether it changes the
     phase's contract-count budget (NG-01 counts contracts by file, not by key — adding a key to an
     existing schema file does NOT increase the "6 contracts" count, only a *new* schema file would).
   - Recommendation: extending the existing `excludedEntry.excluded` enum (adding e.g.
     `"non-workspace-member"`) is very likely the lower-risk path: no new `$defs` shape, no new
     top-level array, and it reuses the ladder's existing "excluded ≠ missed" guarantee. This still
     requires the standard contract-drift + golden-update chain, but is a smaller diff than a new
     `skipped` array with its own record shape.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `git` (worktree subcommands) | RTA-01 fresh worktree creation/disposal | ✓ [VERIFIED: Phase 51 already used this successfully; `git worktree` commands available] | system git | — |
| `~/Desktop/2026/FeedbackOps` real repo, `develop` branch | The whole phase's real-target run | ✓ [VERIFIED: read directly, `pnpm-workspace.yaml` present] | HEAD advanced past both `1d1c8ed` and `4f16525` — re-read at run time per D-02 | — |
| `uv` / the repo's own `.venv` | Running `tools.adoption_scan`/`tools.adoption_apply`/`tools.memory_regen`/`tools.harness_config` modules | ✓ [VERIFIED: `uv run python -c "import ruamel.yaml"` succeeded live] | project-pinned | — |
| pnpm / node (to independently verify FeedbackOps' own workspace resolution, e.g. `pnpm ls -r`) | Not required — the harness never shells out to pnpm; all analysis is manifest-file-based | not probed (not needed) | — | — |

No missing dependency blocks this phase.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (pinned `>=8.4,<9`, `pyproject.toml:16`) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["libs/python", "tools"]`) |
| Quick run command | `uv run pytest tools/adoption_scan tools/harness_config tools/adoption_apply -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RTA-02 / OBS-D-01 | pnpm-workspace.yaml scopes members; non-member manifest is excluded + recorded | unit | `uv run pytest tools/adoption_scan/tests/test_detect.py -k pnpm -x` | ❌ Wave 0 — new test + new synthetic fixture needed |
| RTA-02 / OBS-D-01 | No-workspace-manifest path stays byte-identical (D-10) | regression (existing) | `uv run pytest tools/adoption_scan/tests -q` (full existing suite must stay green) | ✅ existing suite covers this as a non-regression baseline |
| RTA-04 / OBS-D-03 | `conventions_for()` always returns a `lint` key, `None` when unset | unit | `uv run pytest tools/harness_config/tests/test_conventions_for.py -x` | ❌ Wave 0 — extend existing file (13 existing tests must stay green + new assertions) |
| RTA-04 / OBS-D-03 | Adopted JS package's derived `[[languages]]` row carries real `lint`/`test` from `package.json` scripts | unit | `uv run pytest tools/adoption_scan/tests -k draft -x` (exact test name TBD by planner) | ❌ Wave 0 |
| OBS-D-04 | Apply leaves no *unlisted* (non-lock-sidecar) artifacts; lock sidecars are declared/expected | unit | `uv run pytest tools/adoption_apply/tests/test_atomic_apply.py -x` (extend the block at/after `:267`) | ❌ Wave 0 — extend existing file |
| OBS-D-04 | A stale lock is reported on stderr, not silently reused (D-16) | unit | `uv run pytest tools/adoption_apply/tests/test_atomic_apply.py -k stale_lock -x` | ❌ Wave 0 |
| OBS-D-02 (lock-in, no repair) | `packages/shared`→`apps/frontend`/`apps/backend` runtime edges resolve from `workspace:*` deps | unit | `uv run pytest tools/memory_regen/tests -k workspace_edge -x` (verify exact test dir/module name at task-authoring time — not directly located in this research pass) | ❌ Wave 0 |
| RTA-01/RTA-03 | Real-target evidence: byte-unchanged proof, package-facts edges, apply success | **non-CI evidence artifact** (real worktree run), never a test dependency (D-17, CONTEXT D-17 explicit) | phase-directory evidence capture (argv/stdout/stderr/exit-code files, mirroring Phase 51's `evidence/` layout) | N/A — not a repo test by design |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/adoption_scan tools/harness_config tools/adoption_apply -q`
- **Per wave merge:** `uv run pytest` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`, plus the one-shot real-target run
  recorded as evidence (not gating CI — SC-1/SC-3/SC-4's real-target proof is confirmation, per
  CONTEXT D-17).

### Wave 0 Gaps
- [ ] `tools/adoption_scan/tests/` — a second synthetic fixture (or an extension of `conftest.py`'s
  `tmp_minirepo`) that adds a `pnpm-workspace.yaml` + a non-member manifest under a path like
  `docs/design-prototype/package.json`, mirroring the real target's shape exactly (widget/source/sink
  vocabulary per GEN-04, never FeedbackOps-specific naming) — covers RTA-02/OBS-D-01.
- [ ] `tools/harness_config/tests/test_conventions_for.py` — extend for the new `lint` key (13
  existing tests must stay green; new assertions for the key's presence/`None` default).
- [ ] `tools/adoption_apply/tests/test_atomic_apply.py` — extend for lock-sidecar
  declared-as-known/expected behavior and the stale-lock stderr report (D-16).
- [ ] A regression test module for OBS-D-02's lock-in (exact siting TBD — likely
  `tools/memory_regen/tests/` alongside `package_facts.py`'s existing tests, not directly located in
  this pass; planner should confirm the existing test directory name before authoring).
- [ ] Framework install: none — `pytest` already present and pinned.

## Security Domain

`security_enforcement` is not set to `false` in `.planning/config.json` (absent → enabled per the
protocol), so this section is included, scoped honestly to what actually applies in a local-CLI,
no-network, no-auth domain.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface in this domain (local filesystem tool). |
| V3 Session Management | No | N/A. |
| V4 Access Control | Partial | The constitution-plane refusal (`refuse_if_constitution`, `apply.py:81-91`) and confinement (`refuse_if_outside_root`, `apply.py:94-106`) are this domain's access-control analogue — unchanged by this phase, reused as-is. |
| V5 Input Validation | Yes | The pnpm-workspace glob parser (new code, OBS-D-01) must validate the YAML/text structure defensively — reuse the existing "own the exception locally, degrade per-file, never crash the whole run" idiom already used for malformed manifests (`package_facts.py:176-182`'s `_MANIFEST_PARSE_ERRORS` catch). |
| V6 Cryptography | No | No crypto in this domain; `sha256` usage here is content-addressing, not a security control. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via a hostile `pnpm-workspace.yaml` glob (e.g. a glob resolving outside the target root) | Tampering | Reuse the existing confined-walk idiom (`scan.py:131-137`'s `_confined()` check) — any glob-expanded directory must be re-validated as a descendant of the scanned target root before being treated as a member, exactly as `_builtin_walk`/`classify_exclusions` already do for every other path. |
| Symlink-based read-through at a marker-merge destination during lock-sidecar handling | Spoofing/Tampering | Already mitigated, unchanged: `_read_target_no_symlink` (`apply.py:270-289`) refuses to follow a symlink at the destination itself; this phase's lock-sidecar declaration work must not touch this function. |
| Malformed/hostile `package.json` `scripts` block used to derive JS `lint`/`test` commands (D-12) | Tampering | The derived commands are **written into `harness/project.toml` as data**, never executed during draft/apply — no `subprocess` call is made against them at this phase (mirrors `apply.py`'s own documented invariant: "this module never builds a subprocess argv from manifest/draft content ... it never calls subprocess at all", `apply.py:35-37`). If a later phase or command ever *runs* these derived commands, that is a new trust boundary outside this phase's scope — flag but do not build a mitigation now (NG-01 no speculative hardening). |

## Sources

### Primary (HIGH confidence — read directly in this checkout)
- `tools/adoption_scan/detect.py` (full file) — manifest-kind table, dependency parsers, evidence-classification ladder.
- `tools/adoption_scan/scan.py` (full file) — `build_inventory`, `enumerate_target`, `classify_exclusions`.
- `tools/adoption_scan/destinations.py` (partial, :1-260) — `MARKER_CAPABLE`, `_CATEGORY_GLOBS` (`.gitignore` at line 180), `DISPOSITION_ENUM`.
- `tools/adoption_apply/apply.py` (full file) — `_apply_marker_merge`, lock-sidecar creation, `refuse_unsafe_destination`.
- `tools/adoption_apply/tests/test_atomic_apply.py` (:1-320) — existing lock-sidecar test-avoidance comment (`:265-270`).
- `tools/harness_config/loader.py` (full file) — `conventions_for`, `effective_packages`, call-site-adjacent comments.
- `tools/memory_regen/package_facts.py` (:1-330) — `build_facts`, `discover_manifests`, manifest/dependency reuse from `detect.py`.
- `contracts/harness/adoption/inventory.schema.json`, `contracts/harness/adoption/manifest.schema.json` (full files).
- `tools/adoption_scan/pyproject.toml`, root `pyproject.toml`, `uv.lock` — dependency graph verification (`ruamel.yaml` transitive presence, `check-jsonschema` as its source).
- `~/Desktop/2026/FeedbackOps/pnpm-workspace.yaml` — read live, 2026-07-31: `packages: ["apps/*", "packages/*"]`.
- `.planning/phases/51-real-target-observation-baseline/evidence/discover/inventory.json` — the real OBS-D-01 symptom data (6 manifests/boundaries, 5 required).
- `AGENTS.md` (root) — non-negotiables, harness-emitted surface counts (19 commands, 8 skills).
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `52-CONTEXT.md`, `51-BASELINE-EVIDENCE.md` — phase scope and carried notes.

### Secondary (MEDIUM confidence)
- WebSearch: pnpm-workspace.yaml `packages:` glob/negation semantics (pnpm.io/pnpm-workspace_yaml, pnpm.io/filtering) — cross-verified against the real target's actual (simpler, non-negated) file.

### Tertiary (LOW confidence)
- None retained without an attempted verification step above.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `ruamel.yaml`'s transitive presence and version were confirmed live, not assumed.
- Architecture: HIGH — every code location cited was read directly in this checkout in this session.
- Pitfalls: HIGH for the contract-schema pitfalls (schemas read directly); MEDIUM for the exact blast radius of `test_schema_conformance.py`/`test_snapshots.py` (located, not fully read — flagged as A3).

**Research date:** 2026-07-31
**Valid until:** ~14 days (the real FeedbackOps target is actively moving — `develop` advanced 6+ commits between Phase 51's discuss and STATE.md's last note; re-verify the live `pnpm-workspace.yaml` content at phase-start per D-02 rather than trusting this document's captured snapshot if more than ~2 weeks elapse).
