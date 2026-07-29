---
phase: 44-non-goal-surface-removal
reviewed: 2026-07-29T00:00:00Z
depth: deep
diff_base: 7dbfb3a..HEAD
files_reviewed: 161
findings:
  critical: 2
  warning: 9
  info: 3
  total: 14
status: issues_found
---

# Phase 44: Code Review Report

**Reviewed:** 2026-07-29
**Depth:** deep (161 files, +481 / −6,548, excluding `.planning/`)
**Status:** issues_found

## Summary

The five items the brief asked me to verify hardest are, individually, **correct**:

- **`RETIRED_SIGNATURES` tombstones** (`tools/harness_emit/merge.py:120-124`) list both
  `tools.hooks.resume_gate` and `tools.hooks.secret_scan`, and the new
  `test_retired_signatures_are_permanent_tombstones`
  (`tools/harness_emit/tests/test_settings_merge.py:161-180`) is **not** vacuous: it pins each
  string by explicit membership, so deleting either entry reds the suite. The refactor of
  `test_retired_signature_group_is_dropped_from_a_stale_checkout` into a loop over the whole tuple
  (rather than `[0]`) is a genuine coverage widening.
- **`runner.py`'s relocation anchors are right.** `REPO_ROOT = parents[3]`
  (`examples/log-parser/golden_runner/runner.py:29`) resolves to the repo root, and
  `GOLDEN_DIR = parents[1] / "golden"` (`:38`) resolves to `examples/log-parser/golden/`, which
  exists. `_confine`'s allowlist is unchanged in breadth. No off-by-one.
- **`adoption_scan`'s independently-owned secret constants are untouched** and its redaction still
  works (`scan.py:56,60`); only prose changed.
- **`commit_gate` still fails closed** on drift and on staged-TSV §4.3-4.6 violations, and the
  `:78-79` "degrades to the drift component alone" claim is now accurate.
- **The two deleted `test_pipeline_config.py` tests were genuinely vacuous** once
  `[pipeline].edges` was empty — both loop bodies were unreachable. That deletion was necessary,
  not convenient.

What the phase got wrong is concentrated in one place: **the golden relocation moved the tree but
not the controls that guard it.** `golden/**` is still hardwired into both the in-session
constitution-plane deny (`contract_guard.CONSTITUTION_GLOBS`) and the permission matrix, where it
now matches nothing, while the relocated baselines under `examples/log-parser/golden/` are guarded
by nothing in-session. CODEOWNERS *was* correctly extended to `/examples/*/golden/` — proving the
gap was seen at merge-time and simply not carried to the hook layer.

Beyond that: two secondary controls (`*.env` path deny; the `DATA_CONTRACT_PATHS` seam) are now
data with no enforcer and no test, three assertions were narrowed until they cannot fail, one
command lost more than its stated half, and the core test suite acquired a hard dependency on the
reference instance.

Verified green locally: `uv run pytest -q` → 880 passed; `pytest examples/log-parser/golden_runner`
→ 17 passed; `pytest examples/log-parser/tests` → 14 passed. Emitted trees (`.opencode/`,
`.claude/`, `opencode.json`) carry **no** stale references to deleted surface — the emit is clean
and I found no hand-edit to an emitted tree.

---

## Critical Issues

### CR-01: The relocated golden baselines lost their in-session write protection — `golden/**` is now a dead glob

**File:** `tools/hooks/contract_guard.py:44` (also `:3`, `:89`); `harness/permission-matrix.json:30`

`CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**", "docs/glossary.md"]` still names
the repo-root `golden/` tree. CER-09 deleted that tree; the approved baselines now live at
`examples/log-parser/golden/*/expected/baseline.verified.tsv`. `resolve_path` is a prefix-anchored
glob matcher, so `examples/log-parser/golden/...` does **not** match `golden/**`.

Net effect: the PreToolUse `Write|Edit` deny that implemented Pitfall P9 ("no agent self-blesses a
golden") for baseline files now matches zero paths in this repo. An agent can write
`examples/log-parser/golden/sample/expected/baseline.verified.tsv` directly, with no
`GOLDEN_APPROVE_HUMAN` token, and the hook returns `None` (allow).

This is not covered by the ADR-0012 "CI and merge are the authority" posture, because:
- ADR-0012's Phase-44 enumeration (`docs/adr/0012-...:113-117`) records the relocation but says
  nothing about dropping `golden/**` from the constitution plane;
- `contract_guard.py:40-42` explicitly states the four plane members are declared by ADR-0001 §48
  and "adding or removing a member therefore requires a superseding ADR, never an edit here alone."
  The relocation dropped a member *de facto* without that ADR;
- CODEOWNERS **was** updated (`.github/CODEOWNERS:37` adds `/examples/*/golden/`), showing the team
  understood instance goldens still need gating — the hook layer was simply left behind.

**Why no test caught it:** `tools/hooks/tests/test_contract_guard.py:62,124,361` and
`tools/harness_perms/tests/test_resolver.py:60` all exercise `golden/**` against *synthetic* string
paths (`"golden/case/expected/x.tsv"`, `"golden/case.verified"`). Glob resolution never touches the
filesystem, so those assertions stay green forever regardless of whether the directory exists. This
is a claimed control with a green test and no subject.

**Failure scenario:** An agent asked to "make the golden pass" edits
`examples/log-parser/golden/sample/expected/baseline.verified.tsv` to match its own converter
output. `contract_guard` allows the write. `commit_gate` allows the commit (the golden-parity
component was removed in `fc69d10`, and polyglot only lints `.tsv` for BOM/CRLF, which a
self-blessed baseline passes). CI's `golden` job then goes **green**, because the case now compares
against the mutated baseline. The only remaining catch is a human noticing the `.verified` diff in
the PR — the exact "agent self-bless" the two-file `.received`/`.verified` split exists to make
impossible. For: anyone reviewing a PR from this repo or any template consumer who copies the hook.

**Fix:** Extend the plane to cover instance goldens (and re-point the deny message at `:89`), and
add a filesystem-grounded assertion so the glob cannot go dead again:

```python
# tools/hooks/contract_guard.py
CONSTITUTION_GLOBS = [
    "contracts/**",
    "docs/adr/**",
    "golden/**",              # template-consumer root tree
    "examples/*/golden/**",   # instance overlay tree (mirrors CODEOWNERS /examples/*/golden/)
    "examples/*/contracts/**",
    "docs/glossary.md",
]
```

```python
# tools/hooks/tests/test_contract_guard.py — anti-vacuity backstop
def test_every_constitution_glob_matches_a_real_tracked_path(repo_root) -> None:
    """A plane glob that matches nothing on disk is a control with no subject."""
    tracked = subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True,
                             text=True, shell=False).stdout.splitlines()
    for glob in CONSTITUTION_GLOBS:
        assert any(resolve_path([glob], p) == "deny" for p in tracked), (
            f"constitution glob {glob!r} matches no tracked file — dead deny"
        )
```

Add a paired ADR entry recording the plane's new membership, since `contract_guard.py:40-42` and
`harness/permission-matrix.json:2` both require one. `harness/permission-matrix.json:30` needs the
same edit (it is source; re-emit afterwards — do not hand-edit `opencode.json`).

---

### CR-02: `path_deny_globs`' `*.env` entries are now enforced by no hook, while a green test asserts they are

**File:** `harness/permission-matrix.json:32-33`; `tools/harness_perms/tests/test_resolver.py:64`

`secret_scan` was the sole consumer that fed the secret half of `path_deny_globs` (`*.env`,
`**/*.env`) into a live PreToolUse deny. It is deleted. `contract_guard` is now the only remaining
`resolve_path` hook and it **deliberately excludes** those entries — the phase itself rewrote that
comment: "`*.env` is outside this gate's domain" (`contract_guard.py:18,36-37`).

So `harness/permission-matrix.json` still ships two deny rows that nothing enforces, and
`tools/harness_perms/tests/test_resolver.py:64` still asserts
`resolve_path(matrix["path_deny_globs"], "config/prod.env") == "deny"` — a passing test that proves
only that the *resolver function* works, never that anything calls it with those globs.

Removing the enforcement was the sanctioned CER-08 decision (ADR-0012: no replacement job). Leaving
the **data and the test** behind is under-deletion, and it is precisely the "claimed control that
does not exist" defect class that ADR-0012 §(a) and
`tools/harness_lint/workspace_check.py:24-27` both name as the thing this milestone exists to
remove.

**Failure scenario:** A future maintainer reads `permission-matrix.json`, sees `*.env` denied, and
reasonably concludes agent sessions cannot write secrets to `.env` files. They are wrong: nothing
blocks it. Worse, the matrix `_note` at `:2` still says "`path_deny_globs` are the constitution/**secret**
path-scoped denies the resolver enforces" — an active false statement in a human-gated data file.

**Fix:** Either delete the two rows and the `:64` assertion (matching the "no replacement" decision),
or re-point them at a live enforcer. If deleted, update the `_note` at `:2` to drop "secret" from the
description. Do not leave the data without an enforcer.

---

## Warnings

### WR-01: Root `AGENTS.md` — the canonical agent rules file — documents two commands that now raise `ModuleNotFoundError`

**File:** `AGENTS.md:66,67` (also `:79`, `:84`)

```
| Golden equivalence runner … | `python -m tools.golden_runner.runner` |
| Promote a golden baseline …  | `python -m tools.golden_runner.approve --approve --adr <id>` |
```

`tools/golden_runner/` no longer exists. `:79` documents a root-level `golden/` plane directory that
was deleted, and `:84` lists `golden_runner` among the `tools/` engine packages. Per `CLAUDE.md`,
`AGENTS.md` is *the* nearest-wins rules file agents read first — this is not incidental doc drift.

Note this is **not** in the deferred-to-Phase-45 set (which covers `README.md:119`, `README.ko.md`,
`contract_guard.py:9,55,75,89`, three `docs/` carriers, and
`test_install_completeness.py:196`). `AGENTS.md` was missed.

**Failure scenario:** An agent onboarding via `/orient` reads the golden-path command table, runs
`python -m tools.golden_runner.runner`, gets `No module named tools.golden_runner`, and has no
pointer to `examples/log-parser/golden_runner`. It then either fabricates a path or reports the
golden loop as broken.

**Fix:** Re-point both rows at `examples/log-parser/golden_runner` (or mark the runner as
instance-owned and drop the rows from the *core* table), remove the root `golden/` line at `:79`,
and drop `golden_runner` from the `tools/` list at `:84`. Beware: `tools/memory_regen/tests/test_agents_md.py:39`
asserts the literal `"golden/"` appears in `AGENTS.md` — it currently also matches `:91`
(`examples/<instance>/ Own contracts/, golden/, …`), so removing `:79` alone stays green, but the
gate is pinning a structural claim that is now only true inside an instance.

### WR-02: `examples/log-parser/README.md` points at the pre-relocation path — and nothing collects it

**File:** `examples/log-parser/README.md:14,25`

Both lines still say `tools/golden_runner`, and `:14` calls it "the **core's** `tools/golden_runner`"
— the precise claim CER-09 inverted. `[tool.pytest.ini_options] testpaths = ["libs/python", "tools"]`
means `uv run pytest` never collects anything under `examples/`, so no gate can see this.

**Failure scenario:** A reader following the instance README to run the golden loop gets a
nonexistent path, and is told the runner is core-owned when the whole point of CER-09 was that it
is instance-owned.

**Fix:** `tools/golden_runner` → `examples/log-parser/golden_runner` in both rows; reword `:14`'s
"the core's" to "this instance's".

### WR-03: `/component` lost more than its topology half — the component-agent derivation procedure went with it, orphaning a live template

**File:** `harness/commands/component.md` (whole `## Mandated order` + `## Guard` sections removed in `f28a9cd`); `harness/agents/templates/component-engineer.md:6,13`

The plan scoped this to "`/component`'s topology-registration half." Step 2 (register the
`[pipeline]` edge) and step 3 (topology gate) are correctly that half. **Step 1 was not**: it was
the only instruction anywhere for deriving a per-component agent from
`harness/agents/templates/component-engineer.md`. That template is still shipped, still gated
(`tools/harness_lint/tests/test_agent_templates.py:33` requires it), and is now the pinned
"core resolution doc" that `examples/log-parser/tests/test_pipeline_topology.py:115` reads — but
no command instructs anyone to instantiate it.

The template's own header is now self-describing a control that no longer exists:
`:6` "`/component` instantiates a COPY of this file", and `:13` "`<STAGE>` (its ordinal in the
`[pipeline]`)" — the core `[pipeline]` table was deleted in the same phase.

Meanwhile `[[components]]` is still a live, gated data slot
(`tools/harness_lint/tests/test_pipeline_config.py`) with a live consumer:
`harness/agents/orchestrator.md:82-86` still routes "Change on a declared pipeline stage/component
→ **owning component engineer** (`project.toml`)".

**Failure scenario:** A user runs `/component collector`. The command creates the package, AGENTS.md
and tests, but never declares a `[[components]]` entry and never derives the component agent. The
orchestrator's stage/component routing table then permanently falls through to the
"no declared component engineer → language engineer" fallback row, and every new component silently
loses its least-privilege persona. Nothing reds.

**Fix:** Restore step 1 (template derivation + `[[components]]` registration) to
`harness/commands/component.md` without the `[pipeline]`-edge parts of steps 2-3; update
`component-engineer.md:13` to stop referencing the deleted `[pipeline]` ordinal. Alternatively, if
the component-agent surface is also a non-goal, delete `component-engineer.md`, its
`test_agent_templates.py` entry and the orchestrator's two component-routing rows in one move — but
do not leave the artifact without its procedure.

### WR-04: `test_output_is_deterministic` now asserts `[] == []`

**File:** `tools/harness_config/tests/test_topology_relationships.py:54-57`

```python
def test_output_is_deterministic() -> None:
    cfg = load_project()
    assert effective_relationships(cfg) == effective_relationships(cfg)
```

Verified live: `effective_relationships(load_project())` returns `[]`. The core default now declares
neither `[pipeline].edges` nor explicit `[[contract_graph.relationships]]` rows, so this compares
two empty lists. The deleted sibling `test_lowers_linear_default_to_single_relationship` was what
made this fixture non-empty; deleting it drained this one without anyone noticing.

`test_accessor_returns_empty_on_linear_default` (`:34`) is similarly weakened — its name claims a
"linear default" that no longer exists, and it now asserts empty for two independent reasons.

**Failure scenario:** A regression that makes `effective_relationships` non-deterministic (e.g. a
`set()` introduced into the union/sort path) ships green, because the one test named for
determinism runs on an empty input. `test_output_is_stable_sorted_by_id` (`:60-84`) uses a synthetic
cfg and still constrains, so the loss is partial — but the *named* determinism guard is dead.

**Fix:** Point it at a synthetic multi-edge cfg (reuse the one at `:60-77`) so the comparison has
subject matter:

```python
def test_output_is_deterministic() -> None:
    cfg = {"pipeline": {"edges": [{"from": "z", "to": "y", "contract": "wc"},
                                  {"from": "a", "to": "b", "contract": "ac"}]}}
    first = effective_relationships(cfg)
    assert first and first == effective_relationships(cfg)
```

### WR-05: `DATA_CONTRACT_PATHS` is an empty seam whose only test was deleted — the branch is now dead *and* uncovered

**File:** `tools/contract_hash/hash.py:33,58`; `tools/contract_hash/tests/test_hash.py` (deletion of `test_build_manifest_includes_ratified_data_contracts_and_detects_registry_mutation`)

`DATA_CONTRACT_PATHS: tuple[Path, ...] = ()` is documented at `:30-32` as a "retained extension
seam." With the tuple empty, line 58
(`candidates.update(root / rel for rel in DATA_CONTRACT_PATHS if (root / rel).is_file())`) can never
add a candidate, and the sole test that exercised the data-contract path — including its explicit
negative control proving the entry came from `DATA_CONTRACT_PATHS` rather than the fixture — was
removed in the same phase.

**Failure scenario:** A future phase re-ratifies a data contract and adds it back to the tuple. The
existence check, the symlink defense-in-depth at `:62`, and the `contracts/`-relative key derivation
at `:64` are all unexercised for that branch, so a path-normalization bug (e.g. a `rel` that
resolves outside `contracts/` and is silently dropped) ships with a green suite and the contract is
never hashed — meaning the drift gate does not gate it, which is the failure mode the whole
schema-hash design exists to prevent.

**Fix:** Keep the seam but keep it covered — restore the deleted test as a `monkeypatch`-driven one
that injects a synthetic entry into `DATA_CONTRACT_PATHS`, so it exercises the branch independently
of whether the live tuple happens to be empty.

### WR-06: The core test suite now hard-requires the reference instance — GEN-04's direction is inverted where its guard cannot see

**File:** `tools/adoption_scan/tests/test_install_completeness.py:85-172` (new); `pyproject.toml:34`; `.github/workflows/ci.yml:168,170,320`

The new `test_every_ci_pytest_path_argument_resolves` is good coverage in principle, but running its
extractor against the live repo yields 8 path arguments, of which **3 are `examples/**`**:

```
('ci.yml', 'golden',    'examples/log-parser/golden_runner')
('ci.yml', 'golden',    'examples/log-parser/tests')
('ci.yml', 'workspace', 'examples/log-parser/golden_runner/tests/test_workspace_golden.py')
```

That test lives under `tools/` and **is** collected by the core `uv run pytest`. So a core-plane test
now fails if the instance overlay is absent. `pyproject.toml:34` adds the same coupling at the
workspace level (`members = [..., "examples/log-parser/golden_runner"]`).

`tools/harness_lint/tests/test_core_no_example_dep.py` cannot catch either: it scans only tracked
files under `tools/`, `harness/`, `libs/` (`_CORE_ROOTS`, `:41`), so neither the root
`pyproject.toml` nor `.github/workflows/ci.yml` is in its scan set.

**Failure scenario:** A downstream adopter does exactly what `docs/explanation/template-and-instances.md`
and ADR-0002 invite — deletes `examples/log-parser/` and adds their own instance. `uv run pytest`
(the core suite, the thing that is supposed to prove the *template* is healthy) goes **red** in
`tools/adoption_scan`, and CI's `golden` and `workspace` jobs go red, for reasons that have nothing
to do with their code. The template's own "core depends on no instance" promise is falsified by its
own test suite.

I confirmed the *milder* half is safe: `uv` tolerates a `members` entry whose directory is missing
(verified in a scratch workspace — `uv sync` resolves without error), so this is not the
self-sealing PreToolUse outage that `workspace_check.py` guards. The damage is a red suite, not a
bricked session.

**Fix:** Filter the discovered set to core-plane paths, or skip `examples/**` tokens when the
instance root declared by `harness/project.toml [instance] root` is absent:

```python
missing = [
    (w, j, t) for w, j, t in discovered
    if not (repo_root / t).exists()
    and not (t.startswith("examples/") and not (repo_root / "examples").is_dir())
]
```

Also extend `_CORE_ROOTS` in `test_core_no_example_dep.py` (or add a sibling scan) to cover
`pyproject.toml` and `.github/workflows/`, so the next core→instance reference is caught by the
guard that exists for exactly that purpose.

### WR-07: `commit_gate` still speaks a `SKIP` vocabulary no component can produce

**File:** `tools/hooks/commit_gate.py:18,60,203`

After the golden-parity amputation, `check_drift` and `check_polyglot` return only `PASS` or `FAIL`.
Three surviving statements describe a third state:

- `:18` — "``main`` exits 0 iff every **non-skipped** component passes"
- `:60` — `"""One component's outcome: ``PASS`` | ``FAIL`` | ``SKIP`` + a human-readable detail."""`
- `:203` — "A SKIP never blocks and never suppresses a sibling FAIL (T-04-13)."

The brief asked specifically whether `:81`'s "degrades to drift+golden rather than crashing" was
fixed — it was, and is now accurate. These three were missed in the same sweep.

**Failure scenario:** A reader auditing the Bash PreToolUse guard reads `:203` and concludes some
component may skip, then spends time looking for the skip path — or, worse, a future contributor
adds a component that returns `"SKIP"` believing the semantics at `:203` are implemented. They are
not: `GateResult.blocked` (`:67-68`) only special-cases `"FAIL"`, so a `SKIP` would print as a
non-blocking line, which happens to be correct — but by accident, with no test
(`test_dotnet_absent_skips_golden_not_fail` was deleted).

**Fix:** Narrow all three to `PASS | FAIL`, or restore a test that pins the `SKIP` semantics if the
state is meant to remain reachable.

### WR-08: `commit_gate.staged_files()` fails **open** for the polyglot component — and the sibling that covered for it is gone

**File:** `tools/hooks/commit_gate.py:74-93`

A `git` failure (`OSError` or non-zero exit) returns `[]`, which makes `check_polyglot([])` return
`PASS` — "no §4.3-4.6 violations in staged TSV" — for a tree it never inspected. The module docstring
at `:12` and `run_composition`'s at `:201` both assert polyglot "ALWAYS runs."

This is pre-existing, but the phase changed its blast radius: this used to be one of three
components, and is now one of two, so a git hiccup silently reduces the Bash gate to drift alone.

**Failure scenario:** A commit made from a worktree/submodule context where
`git diff --cached` exits non-zero (a broken index, a `GIT_DIR` mismatch, a partially-initialized
worktree) sails through the polyglot gate. A BOM'd or CRLF `.tsv` — the exact §4.3 defect the gate
exists for — lands on the wire boundary, and CI's polyglot leg is the only remaining catch.

**Fix:** Distinguish "no staged files" from "could not determine staged files" and return
`FAIL`/`SKIP` explicitly on the latter:

```python
def staged_files() -> list[str] | None:
    """Return staged paths, or None when git could not be consulted (caller must not treat as clean)."""
    ...
    if proc.returncode != 0:
        return None
```
…then have `check_polyglot(None)` return a `FAIL` (or an explicit, logged `SKIP` if fail-open is the
ratified posture) rather than a `PASS` claiming a clean inspection.

### WR-09: New test imports `ruamel.yaml` into a package that declares zero external dependencies

**File:** `tools/adoption_scan/tests/test_install_completeness.py:23`

`from ruamel.yaml import YAML` was added to `tools/adoption_scan`, whose `pyproject.toml:6-9` states
"Zero new external packages. All stdlib… nothing declared here." `ruamel.yaml` is not declared
anywhere in the repo — `tools/harness_lint/pyproject.toml:6` records that it is only present as a
**transitive** dependency of `check-jsonschema`.

Under the v2.5 no-surface-growth rule this is a new (undeclared, transitively-sourced) dependency in
a package that documents having none. It is a smaller version of the sanctioned coverage extension,
but the dep story is not.

**Failure scenario:** `check-jsonschema` is bumped past a release that swaps `ruamel.yaml` for
another YAML backend (it has no API contract obliging it to keep it). `uv sync` succeeds, `uv.lock`
resolves, and then the **entire** `tools/adoption_scan` test module fails at *collection* with
`ModuleNotFoundError` — taking down `test_catalog_excludes_tools_tests_and_fixtures` and the module-
reference gates alongside the two new CI-path tests.

**Fix:** Reuse the repo's existing frontmatter/YAML seam (`tools.harness_lint.parse_frontmatter`
already owns the `ruamel` dependency and is declared for it), or add an explicit
`dependencies = ["ruamel.yaml"]` to `tools/adoption_scan/pyproject.toml` and correct the "zero
external packages" comment. Do not rely on a transitive dep of an unrelated dev tool.

---

## Info

### IN-01: `tools/hooks/pyproject.toml:4` description was left ungrammatical by the deletion

The `secret_scan` clause was cut mid-sentence: *"…shared by every PreToolUse/PostToolUse/Stop gate,
Gates reuse the CONFIG-02 resolver…"* — a dangling comma followed by a capitalized sentence
fragment. This string is packaging metadata, so it is user-visible in `uv` output.
**Fix:** `…Stop gate. Gates reuse the CONFIG-02 resolver…`.

### IN-02: `_CONTRACTS_DIR` is now dead in `test_pipeline_config.py`

**File:** `tools/harness_lint/tests/test_pipeline_config.py:24`

Its only consumer was `test_edge_contracts_have_a_tracked_schema`, deleted in the same commit. Ruff
does not flag unused module-level bindings, so it will linger.
**Fix:** Delete line 24.

### IN-03: `pyproject.toml:31` still describes `tools/*` as containing the golden-runner

**File:** `pyproject.toml:31`

`# tools/*      = repo-level Python tools (golden-runner, contract-hash/drift — later plans).`
The new `examples/log-parser/golden_runner` member added at `:34` is also undocumented in that
comment block, which is the natural place to record *why* a literal instance path is a workspace
member.
**Fix:** Move "golden-runner" out of the `tools/*` gloss and add a one-line note for the new member.

---

## Verified Clean (checked, no finding)

- **Emitted trees** — `git grep` across `.opencode/`, `.claude/` and `opencode.json` for every
  deleted command/skill/plugin/hook token returns zero hits (the only match is an unrelated GSD
  workflow doc). No hand-edit to an emitted tree; emit-determinism snapshots and `emit-drift` are
  consistent with the source.
- **`EXPECTED_SKILLS` 10→8** (`tools/harness_lint/caps.py:139-150`) — still an exact-equality
  frozenset over 8 live skills; still constrains both directions (anti-sprawl and anti-loss).
- **`EXPECTED_GOLDEN_ADJACENT` 8→6** (`tools/harness_lint/tests/test_commands.py:43-45`) — still 6
  real command stems; the `missing = EXPECTED - names` check still has subject matter.
- **Command count 21→17** (`tools/harness_emit/tests/test_coexist.py:73-74`) — asserts equality, not
  a floor; still reds on either growth or loss.
- **Module-discovery floor 12→11** (`test_install_completeness.py:199-210`) — the live discovered
  count is 11, so the floor sits exactly at the live value. It remains non-vacuous (a matcher that
  broke would drop below 11) and the docstring correctly forbids raising it further.
- **`docs_sync` `EXPECTED_PAGES`** — `deny-domains` correctly dropped; the frozenset still
  enumerates 5+ live pages and the `.ambr` snapshot was regenerated consistently.
- **Persona anti-sprawl** — although `test_conductor_graph_render.py` was deleted whole (including
  its `test_persona_set_unchanged`), the equivalent exact-set gate survives at
  `tools/harness_lint/tests/test_agents.py:65-70`. No loss.
- **`test_endpoints.py`'s deleted `test_core_pipeline_edges_stay_single_repo`** — it opened with
  `assert core_edges, "core [pipeline] must declare at least one edge"`, so it *would* have red'd
  rather than gone vacuous. Deleting it was correct once the data was removed; the workspace-layer
  coverage at `:20-43` still constrains the generalization.
- **`adoption_scan` redaction** — `SECRET_PATH_GLOBS` (`scan.py:56`) and `SECRET_CONTENT_PATTERNS`
  (`scan.py:60-…`) are byte-unchanged; only surrounding prose was edited. No behavior change.
- **`merge.py` hook-group removal** — the `Read|Write|Edit` secret-scan group was removed from
  `HARNESS_HOOK_GROUPS`, `HARNESS_SIGNATURES`, the live `.claude/settings.json`, and the
  `_SEED_SETTINGS` fixture in `test_coexist.py`, consistently. `test_settings_coexist.py:111-114`
  correctly tightened 7→6 PreToolUse slots.

---

_Reviewed: 2026-07-29_
_Reviewer: gsd-code-reviewer_
_Depth: deep_
