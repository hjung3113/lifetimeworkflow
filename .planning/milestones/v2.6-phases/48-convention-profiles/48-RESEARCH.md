# Phase 48: Convention Profiles - Research

**Researched:** 2026-07-30
**Domain:** This repository's own derived-plane machinery (`tools/memory_regen`,
`tools/contract_graph`, `tools/harness_config`), no external ecosystem.
**Confidence:** HIGH (every claim below is grounded in code read in this session, cited
`path:line`; no web search was performed per the objective).

## Summary

Phase 48 needs no new library, no new artifact file, and no new CI wiring if it is built the way
Phase 47 built its own CI widening: **extend an existing generator's `render()`/`build_facts()`
in place** rather than create a sibling module. `tools/memory_regen/package_facts.py` already
computes exactly the two facts a convention profile needs — a package's `dir` and `language`
(`package_facts.py:184-191`) — and `tools/contract_graph/ownership.py`'s `owning_package()`
already implements the nearest-enclosing-package lookup CONTEXT.md mandates reusing
(`ownership.py:28-65`). `tools/harness_config/loader.py`'s `languages()` already exposes each
language's `test`/`format` commands (`loader.py:42-50`) as pure DATA from `harness/project.toml`.

The one piece of net-new code is a `conventions_for(path)` function — the natural home is
`tools/harness_config/loader.py`, since that module already owns `effective_packages()`
(`loader.py:200-250`, Phase 47's override-layering function) and `languages()`. It joins three
already-existing calls: `effective_packages()` → filter to entries carrying a `"dir"` key (an
**adapter is required** here — see Open Questions / Q2 below) → `owning_package()` → `languages()`
lookup by the winning package's `"language"` field. No second path-matcher, no second command
table.

**Primary recommendation:** Extend `package_facts.render()`/`build_facts()` with one additional
section (`## Convention Profiles` or similar) computed by a new `conventions_for(path)` helper in
`tools/harness_config/loader.py`, wire `/component` step 2 to call it (no new numbered step), and
touch **zero** CI job definitions — the existing `stale-derived` job already regenerates and diffs
`.memory/derived/package-facts.md` byte-for-byte (`ci.yml:271-291`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Nearest-enclosing-package resolution | Derived-plane library (`tools/contract_graph`) | — | `owning_package()` already exists and is explicitly mandated for reuse by CONTEXT.md; no new resolver. |
| Package dir/language facts | Derived-plane library (`tools/memory_regen`) | — | `package_facts.build_facts()` is the single source; Phase 48 reads it, never re-derives it. |
| Language command lookup | Config-layer library (`tools/harness_config`) | — | `languages()` is the SSOT read path for `test`/`format`; a profile must never restate the literal. |
| Query surface (`conventions_for`) | Config-layer library (`tools/harness_config`) | — | Colocates with `effective_packages()`, the function it must call to get the package/component-merged view. |
| `/component` step 2 integration | Command surface (`harness/commands/`) | Runtime-neutral emitter (`tools/harness_emit`) | The command text is the runtime-neutral source; any edit requires re-emit to `.opencode/`+`.claude/`. |
| Committed derived artifact | Derived-plane output (`.memory/derived/`) | CI (`stale-derived` job) | Rides the existing job; no new job tier is introduced. |

## Package Legitimacy Audit

Not applicable — this phase installs no external package. All work is internal Python (stdlib
`tomllib`/`pathlib`, already-vendored). Skipping the slopcheck gate is correct per the protocol's
own scope ("whenever this phase installs external packages").

## User Constraints (from CONTEXT.md)

<user_constraints>

### Locked Decisions

- Profiles are **derived**, not authored: each is a join of the Phase-47 package facts
  (`tools/memory_regen/package_facts.py` → `.memory/derived/package-facts.md`) with the
  `[[languages]]` rows in `harness/project.toml`. No new per-package file exists to drift.
- The query surface is a function in `tools/harness_config` (e.g. `conventions_for(path)`) that both
  agents and `/component` call. **No new command.**
- The repo-wide default is the **root package's record** (the root `pyproject.toml`), not a
  separately hand-written default block.
- Profile fields: package id, package dir, language, the inherited test and format commands, the
  language's `bash_scope`, and a **pointer** to the nearest `AGENTS.md`.
- Resolution **reuses** `tools/contract_graph/ownership.py`'s `owning_package()` segment-based
  nearest-enclosing-package lookup. No second path matcher is written.
- A path with no enclosing package returns the repo-wide default, explicitly marked as the default
  (so a caller can tell "default" from "this package happens to match the default").
- The nested-case proof uses a **real** nested pair — `libs/python` inside the root package — where
  the inner answer differs from the enclosing one. Fixtures may supplement, not replace, this.
- A package whose language is absent from `[[languages]]` yields a profile that reports the language
  with **no commands** rather than raising. A missing toolchain declaration is a gap to report, not
  a crash.
- The profile is populated **inside step 2**, after the self-sufficient `AGENTS.md` write. The
  mandated order stays structure → AGENTS.md → tests; no step 4 is added.
- Step 2's action is: regenerate the derived profile data and assert the new package now resolves.
  It does not write a per-package profile file.
- The derived artifact is **committed** and rides the **existing** `stale-derived` CI job, exactly
  as `.memory/derived/package-facts.md` does — no new job, no new gate.
- The profile **points at** the nearest `AGENTS.md` and never copies its prose. Two sources that
  could disagree is the failure mode being avoided.
- **No new command** (live count 18 → 18), no new gate, no new CI job, nothing injected into
  SessionStart.

### Claude's Discretion

- Whether the derived profile data is a separate artifact or additional section(s) of the existing
  package-facts artifact — pick whichever keeps the committed-derived set smaller while still
  regenerating byte-identically.
- Exact function/module naming and the field spelling in the rendered output.
- Test layout and which fixture cases supplement the real nested-pair proof.

### Deferred Ideas (OUT OF SCOPE)

- A convention-enforcement gate (e.g. failing CI when a package's actual commands diverge) — adding
  a gate contradicts the v2.6 no-growth constraint.
- Generating per-package prose from the profile — would create a second source competing with
  `AGENTS.md`.

</user_constraints>

## Phase Requirements

<phase_requirements>

| ID | Description | Research Support |
|----|-------------|------------------|
| MONO-05 | An agent working in any package can ask which conventions apply there and get the nearest-wins answer | `conventions_for(path)` design (below) built on `owning_package()` (`ownership.py:28`) + `effective_packages()` (`loader.py:200`); real nested-pair proof identified as `libs/python` vs root (see Q4). |
| MONO-06 | Each language's lint and test commands are derived from the existing `[[languages]]` slot, never restated | `languages()` (`loader.py:42`) already reads `test`/`format` from `harness/project.toml`; falsifiable test mechanism identified (see Q3) using the same pass-a-dict-directly idiom `test_effective_packages.py` and `test_topology_relationships.py` already use. |
| MONO-07 | `/component` step 2 populates a convention profile for the new package as part of step 2 | Exact insertion point identified: `harness/commands/component.md:23-26` (step 2's body), no new numbered step; emitter re-run required (see below). |

</phase_requirements>

## Standard Stack

No new library. Everything is stdlib (`tomllib`, `pathlib`, `subprocess` via `git ls-files` already
used by `package_facts.discover_manifests`) plus this repo's own modules:

| Module | Purpose in Phase 48 | Provenance |
|--------|---------------------|------------|
| `tools/memory_regen/package_facts.py` | `build_facts()` → `{"packages": [...], "edges": [...]}`; `render()`/`write()` to extend with a profile section | `[VERIFIED: this checkout, package_facts.py:142-311]` |
| `tools/contract_graph/ownership.py` | `owning_package(packages, contract_path) -> str` (package id) | `[VERIFIED: this checkout, ownership.py:28-65]`; imported via `from tools.contract_graph import owning_package` (`tools/contract_graph/__init__.py:16-18,26`) |
| `tools/harness_config/loader.py` | `languages()`, `effective_packages()` — natural home for the new `conventions_for(path)` | `[VERIFIED: this checkout, loader.py:42-50,200-250]` |
| `harness/project.toml` `[[languages]]` | Single source for `test`/`format`/`bash_scope` | `[VERIFIED: this checkout, harness/project.toml:20-38]` |

**Installation:** none — no `pyproject.toml` dependency addition anywhere in this phase.

## Code Examples (exact signatures, this checkout)

### `package_facts.build_facts()` return shape

```python
# tools/memory_regen/package_facts.py:246-249
return {
    "packages": packages,   # [{"id": str, "manifest": str, "dir": str, "language": str}, ...]
    "edges": [{"from": frm, "to": to, "kind": kind} for frm, to, kind in sorted(edges)],
}
```
Each package dict carries EXACTLY these 4 keys (`package_facts.py:184-191`, and asserted by
`test_real_tree_packages_have_all_keys` in `tools/memory_regen/tests/test_package_facts.py:57-61`).
`dir` is POSIX-relative, `"."` for the root package (`package_facts.py:188`,
`_fallback_id`/`PurePosixPath(path).parent`).

### `owning_package()` — exact signature and packages-arg shape

```python
# tools/contract_graph/ownership.py:28
def owning_package(packages: list[dict], contract_path: str) -> str:
    """packages is [{"id": str, "dir": str, ...}, ...] — only "id" and "dir" are read;
    extra keys ... are ignored."""
```
Raises `ValueError` if no package's `dir` encloses `contract_path` — this can only happen if the
input list omits a `dir == "."` root package (`ownership.py:43-45,55-59`). **It requires every
dict in the list to carry a `"dir"` key** — a dict missing `"dir"` raises `KeyError`, not
`ValueError` (line 51: `package["dir"]` is a bare subscript, no `.get`).

### `loader.effective_packages()` — the field-merge Phase 48 must read through

```python
# tools/harness_config/loader.py:200
def effective_packages(cfg: dict | None = None, facts: dict | None = None) -> list[dict]:
    """Layers [[components]] over the derived package-facts graph (MONO-03)."""
```
Field-level merge: base = derived package record (has `id`/`manifest`/`dir`/`language`); a
matching `[[components]]` entry with the same `id` overwrites same-named fields and ADDS its own
(`stage`/`produces`/`consumes`). **Critical gap for Phase 48:** a `[[components]]` entry with **no
matching derived package id stays declared-only and carries NO `"dir"` field**
(`loader.py:209-216`, proved by `test_component_with_no_matching_package_stays_declared_only_no_raise`
in `tools/harness_config/tests/test_effective_packages.py:33-45`). In THIS checkout today, both
live configs' `[[components]]` entries (`source`/`sink` in `harness/project.toml:63-77`, and the
example instance's `parser`/`converter`/`scheduler`/`collector`) are declared-only — none matches a
real manifest-derived package id yet. **Passing `effective_packages()`'s raw output straight into
`owning_package()` will `KeyError` on those declared-only entries.**

### `loader.languages()` — command lookup

```python
# tools/harness_config/loader.py:42-50
def languages(cfg: dict | None = None) -> list[dict]:
    """Return the configured [[languages]] tables."""
```
Each entry (`harness/project.toml:20-38`) carries: `id`, `bash_scope`, `test`, `format`, and
optionally `sdk_bootstrap`, `persona`, `test_paths`. **There are exactly 2 rows today: `dotnet` and
`python`.** No `lint` field exists — MONO-06's "lint and test commands" maps to this checkout's
actual field names `format` (not `lint`) and `test`; a profile rendering both should use the
literal field names `test`/`format`, not invent a `lint` key that isn't in the config.

## Architecture Patterns

### Recommended Data Flow (conceptual, not files)

```
path (any string) ──> conventions_for(path)
                          │
                          ├─ 1. cfg = load_project()  (or caller-injected cfg — see Q3)
                          ├─ 2. pkgs = effective_packages(cfg)  (Phase-47 override layer)
                          ├─ 3. dir_pkgs = [p for p in pkgs if "dir" in p]   <- ADAPTER (see Q2)
                          ├─ 4. owner_id = owning_package(dir_pkgs, path)    <- REUSED, no 2nd matcher
                          ├─ 5. owner = next(p for p in dir_pkgs if p["id"] == owner_id)
                          ├─ 6. lang = next((l for l in languages(cfg)
                          │              if l["id"] == owner.get("language")), None)
                          ├─ 7. is_default = (owner["dir"] == ".")   <- explicit "default" marker
                          └─ 8. nearest_agents_md = walk owner["dir"] upward on the FILESYSTEM
                                 for the first existing "AGENTS.md" (see Q4/design note below)
                          │
                          v
              {"package": owner["id"], "dir": owner["dir"],
               "language": lang["id"] if lang else owner.get("language"),
               "test": lang["test"] if lang else None,
               "format": lang["format"] if lang else None,
               "bash_scope": lang["bash_scope"] if lang else None,
               "agents_md": nearest_agents_md,
               "is_default": is_default}
```

Step 8's "nearest `AGENTS.md`" is a **filesystem walk over `owner["dir"]`'s ancestors** checking
`Path(ancestor / "AGENTS.md").is_file()`, NOT a second call into `owning_package()` — there is no
existing helper for "nearest ancestor directory containing file X" in this repo (a targeted grep of
`tools/harness_config` and `tools/contract_graph` found none). This is small, stdlib-only
(`pathlib.Path.parents`), and does not compete with `owning_package()`'s package-boundary
resolution — it answers a different question ("where's the nearest doc") over the same directory,
not "which package owns this path".

### Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Nearest-enclosing-package lookup | A second segment-matcher | `tools.contract_graph.owning_package` | CONTEXT.md's explicit constraint; the function is pure, stdlib-only, already tested for the exact semantics needed (deepest-ancestor-wins, deterministic tie-break, root fallback). |
| Package/dir/language facts | Re-parsing manifests | `tools.memory_regen.package_facts.build_facts()` (via `effective_packages()`) | Phase 47 already parses every manifest kind; a second parser would silently diverge from the committed artifact. |
| Command literals | Copy-pasting `dotnet test`/`uv run pytest` into a profile field | `tools.harness_config.loader.languages()` | This is exactly what makes MONO-06 falsifiable — the profile must NEVER contain a command string that isn't a live read of `[[languages]]`. |

**Key insight:** every fact a convention profile needs already has an owning module in this repo;
the entire phase is a join, not new derivation logic.

## Common Pitfalls

### Pitfall 1: `effective_packages()` declared-only entries crash `owning_package()`

**What goes wrong:** Calling `owning_package(effective_packages(cfg), path)` directly raises
`KeyError: 'dir'` the moment a `[[components]]` entry has no matching derived package (true for
BOTH live configs today — `source`/`sink` and the example's four components).
**Why it happens:** `owning_package()` reads `package["dir"]` unconditionally (`ownership.py:51`);
`effective_packages()` deliberately does NOT synthesize a `dir` for declared-only components
(`loader.py:209-216`, the documented MONO-03 divergence).
**How to avoid:** Filter to `[p for p in effective_packages(cfg) if "dir" in p]` before calling
`owning_package()` (adapter step 3 above). A declared-only component (no manifest, no dir) cannot
be resolved by *any* path-based scheme and should not participate in nearest-wins resolution — it
simply isn't reachable by `conventions_for(path)`, which is correct: it has no directory to be
"nearest" to.
**Warning signs:** Any test that calls `conventions_for()` against a synthetic `cfg` carrying a
`[[components]]` entry with no matching derived package must NOT crash — that is the regression
this filter guards.

### Pitfall 2: Assuming `libs/python` differs from root in its LANGUAGE/commands

**What goes wrong:** Choosing the nested-pair proof around "commands differ" fails, because both
the root package (`logparser-harness`, dir `.`) and `libs/python` (`logparser-normalize`, dir
`libs/python`) are `language = "python"` in `.memory/derived/package-facts.md` — there is only ONE
`python` row in `[[languages]]`, so BOTH packages' `test`/`format` commands are identical strings
today. A test asserting "the inner package's command differs from the outer" will fail on the real
tree.
**Why it happens:** `[[languages]]` is keyed by language id, not by package — every python package
shares one row.
**How to avoid:** The real, load-bearing difference between `libs/python` and root is (a) package
`id` (`logparser-normalize` vs `logparser-harness`), (b) `dir` (`libs/python` vs `.`), and — most
usefully for MONO-05's "answer differs" criterion — (c) the **nearest `AGENTS.md` pointer**:
`libs/python/AGENTS.md` exists on disk (confirmed this session) and is nearer than the root
`AGENTS.md`, so `conventions_for("libs/python/normalize/x.py")` must point at
`libs/python/AGENTS.md` while `conventions_for("tools/x/y.py")` (no closer package, no closer
AGENTS.md) points at the root `AGENTS.md`. Assert the difference on `agents_md` + `package`/`dir`,
not on `test`/`format`.
**Warning signs:** A snapshot/assertion keyed only on `test`/`format` strings for this pair will be
a "check that cannot fail" once written — MUTATE it by hand (change `[[languages]] python.test` in
a scratch copy) and confirm it does NOT change the `libs/python` vs root distinction, only the
shared value.

### Pitfall 3: A profile-string test that only echoes the config value it was copied from

**What goes wrong:** A test that builds `cfg["languages"] = [{"id": "python", "test": "X"}]`, calls
`conventions_for(...)`, and asserts `profile["test"] == "X"` is a **check that cannot fail** if the
implementation ever hard-codes `"X"` by accident, because the test only proves equality to a value
it handed in — it never proves the value came from a LIVE READ. See MEMORY.md
`checks-that-cannot-fail.md` — this repo's own recorded pitfall pattern.
**Why it happens:** Copy-the-input-into-the-assertion is the easiest test to write and looks correct.
**How to avoid:** Build TWO cfgs differing only in the `test` string, call `conventions_for()` (or
the profile-render step) against BOTH with everything else held constant (same packages/facts,
`monkeypatch`-free — pass `cfg` directly, mirroring `test_effective_packages.py`'s idiom), and
assert the TWO resulting profiles differ ONLY in the expected field, changing when-and-only-when
the config changes. This is the MONO-06 falsifiable form CONTEXT.md specifies.
**Warning signs:** A test with a single cfg and a single assertion of literal equality.

### Pitfall 4: Editing `harness/commands/component.md` without re-emitting

**What goes wrong:** Step 2's text is edited in `harness/commands/component.md` but
`.opencode/command/component.md` and `.claude/commands/component.md` (the machine-written
projections) are left stale, and `emit-drift` (`ci.yml:235-257`) fails.
**Why it happens:** The emitter (`tools/harness_emit`) treats `harness/commands/*.md` as the
runtime-neutral SOURCE; `.opencode/`/`.claude/` are generated, never hand-edited
(`project_command.py`'s `to_opencode`/`to_claude` projections, `harness_emit/project_command.py:1-40`).
**How to avoid:** After editing `harness/commands/component.md`, run
`uv run python -m tools.harness_emit`, then verify a second immediate re-emit produces zero further
diff (the idempotency check Phase 47's summary explicitly performed — `47-05-SUMMARY.md`). Stage
`.opencode/command/component.md` and `.claude/commands/component.md` alongside the source edit.
**Warning signs:** `emit-drift` job fails in CI, or `git status` shows the source edited but the
two runtime trees unchanged.

## Runtime State Inventory

Not applicable — Phase 48 is neither a rename, refactor, nor migration; it is additive read-path
code plus a derived-artifact extension. No stored data, live service config, OS-registered state,
secrets, or build artifacts reference anything Phase 48 renames.

## Open Questions (the objective's numbered specifics, answered)

### Q1. New artifact vs. additional section(s) of `package-facts.md`

**Recommendation: additional section(s) of the existing `package-facts.md`.**

Trade-off, concretely:

| | New artifact (e.g. `.memory/derived/convention-profiles.md`) | Extend `package-facts.md` |
|---|---|---|
| `.gitignore` | Needs one new re-include line (mirrors `package-facts.md:28`) | Zero change |
| `ci.yml` `stale-derived` job | Needs a new regen call appended to the existing `run:` chain AND a new path in BOTH `git add -A --` and `git diff --cached --exit-code --` lists (mirrors exactly what Phase 47's plan 05 did for `package_facts.md` itself, `47-05-SUMMARY.md`) | Zero change — `package_facts.md` is already in that job's regen command and both path lists (`ci.yml:279,282-283`) |
| `test_ci_stale_derived.py` | `_DERIVED_PATHS` tuple gains a 4th entry, `test_stale_derived_regenerates_all_three_derived_generators` needs renaming again (→ "four") and a new assert line | Zero change to this test file |
| Committed-derived set size | +1 file | +0 files |
| Determinism proof | New `write()`/`render()` pair needs its own byte-identical round-trip test (mirrors `test_package_facts.py`'s pattern 1) | Extend the EXISTING `render()`; the existing determinism tests (`test_render_is_deterministic_over_real_tree`, `test_generate_delete_regenerate_is_byte_identical`) already cover the whole file including the new section — no new test class needed, only new assertions inside the existing ones |
| `curator.md` / `refresh-memory.md` | No change needed IF the new module is still under `tools.memory_regen.*` (the D-06 allow-list checks only the first dotted segment, `test_derived_freshness.py:33,36`) | No change needed (already invokes `tools.memory_regen.package_facts`) |

Extending `package_facts.py` wins on every axis that matters to the v2.6 no-growth constraint:
zero CI-job diff, zero `.gitignore` diff, and the existing determinism/freshness tests keep working
unmodified (their assertions are file-level, not section-level). The only cost is coupling
convention-profile rendering into a module whose docstring currently says "MONO-01/MONO-02" — that
docstring needs a line added noting MONO-05/06/07, which is a one-line doc update, not an
architectural cost.

### Q2. Exact shape `owning_package()` needs; adapter required

Confirmed above (Code Examples + Pitfall 1): `owning_package()` needs `list[dict]` where every
dict has at least `"id"` and `"dir"` (string keys, POSIX-relative dir, `"."` for root). Calling it
directly on `effective_packages()`'s raw output is **unsafe** — declared-only `[[components]]`
entries lack `"dir"` and will `KeyError`. **The required adapter is a one-line filter:**
`[p for p in effective_packages(cfg) if "dir" in p]`. This is a small, local addition to
`conventions_for()` — not a new module, not a modification to `owning_package()` itself (which
must stay a pure, dependency-free lookup per its own docstring, `ownership.py:9-13`).

### Q3. Falsifiable MONO-06 proof mechanism

This repo already has the exact idiom needed, used twice today for config-varying tests with
**no** temp-file fixture and **no** `monkeypatch`: pass a synthetic `cfg`/`facts` dict directly as a
function argument.

- `tools/harness_config/tests/test_effective_packages.py` — every test builds a synthetic `facts`
  dict and/or `cfg` dict inline and calls `effective_packages(cfg, facts)` directly (no file I/O at
  all, e.g. `test_effective_packages.py:14-30`).
- `tools/harness_config/tests/test_topology_relationships.py` — same idiom for
  `effective_relationships(cfg)` (`test_topology_relationships.py:39-48`).

Because `loader.load_project()` is the ONLY function in this module that touches the filesystem
(`loader.py:32-39`), and every other function (`languages`, `components`, `effective_packages`,
`effective_relationships`) accepts an **optional** `cfg`/`facts` parameter that bypasses the file
read entirely, `conventions_for(path, cfg=None, facts=None)` should follow the identical signature
convention. The MONO-06 falsifiable test then becomes:

```python
def test_editing_language_command_changes_every_affected_profile_with_no_profile_edit():
    facts = {"packages": [
        {"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"},
        {"id": "inner", "manifest": "libs/x/pyproject.toml", "dir": "libs/x", "language": "python"},
    ]}
    cfg_v1 = {"languages": [{"id": "python", "test": "OLD", "format": "f", "bash_scope": "uv *"}]}
    cfg_v2 = {"languages": [{"id": "python", "test": "NEW", "format": "f", "bash_scope": "uv *"}]}

    before_root = conventions_for("pyproject.toml", cfg=cfg_v1, facts=facts)
    before_inner = conventions_for("libs/x/whatever.py", cfg=cfg_v1, facts=facts)
    after_root = conventions_for("pyproject.toml", cfg=cfg_v2, facts=facts)
    after_inner = conventions_for("libs/x/whatever.py", cfg=cfg_v2, facts=facts)

    assert before_root["test"] == "OLD" and before_inner["test"] == "OLD"
    assert after_root["test"] == "NEW" and after_inner["test"] == "NEW"
    # No profile-authoring code ran between v1 and v2 — only cfg changed.
```
This is falsifiable in the strong form: if the implementation ever hard-codes a command literal
instead of reading `languages(cfg)`, `after_*["test"]` stays `"OLD"` and the test fails. It mirrors
`test_effective_packages.py`'s and `test_topology_relationships.py`'s established pattern exactly —
no new test mechanism needs to be invented for this repo.

### Q4. The real nested pair for the SC1/MONO-05 proof

Confirmed: `libs/python` (`logparser-normalize`, `pyproject.toml` at `libs/python/pyproject.toml`,
`dir = "libs/python"`) is nested inside the root package (`logparser-harness`, `dir = "."`) per
`.memory/derived/package-facts.md`'s live "Packages" table (verified this session — both rows are
present with those exact dirs). **Their `language` field is IDENTICAL (`python` for both — see
Pitfall 2)**, so the inner-vs-outer difference must be demonstrated on `package`/`dir`/`agents_md`,
not on `test`/`format`. Both `AGENTS.md` files exist on disk today:
`libs/python/AGENTS.md` and the root `AGENTS.md` (confirmed via `find … -name AGENTS.md`, this
session — 7 tracked files total, 3 of them adoption-apply test fixtures under
`tools/adoption_apply/tests/fixtures/**`, matching CONTEXT.md's "7 files tracked, 3 adoption
fixtures" note). This is a genuinely different, disk-verifiable answer for the two paths — no
fixture is *required*, though a synthetic fixture pair with genuinely different languages (e.g. a
`dotnet` package nested inside a `python` root, mirroring the example instance's real
`examples/log-parser/libs/dotnet` vs `examples/log-parser` pair) would additionally exercise the
command-differs case and is recommended as a SUPPLEMENTARY fixture test, per CONTEXT.md's
"Fixtures may supplement, not replace" instruction.

(Note: `examples/log-parser` itself IS a real language-differing nested pair —
`examples/log-parser/libs/dotnet/Normalize` is `csharp` nested inside... but `examples/log-parser`
itself has no root manifest of its own in the current package-facts table, per the "no manifest
exists between an instance's own contracts folder and its own root" documented fallback behavior
(`ownership.py:15-18`). Do not rely on this pair for a language-differs live-tree proof; use the
`libs/python`-vs-root pair for the LIVE-tree assertion and a synthetic dotnet/python fixture for
the command-differs assertion.)

### Q5. Live command count and its assertion mechanism

**Current live count: 18** — confirmed via `ls harness/commands/*.md`: `add-language.md`,
`adopt.md`, `adr.md`, `agree.md`, `build.md`, `checkpoint.md`, `component.md`, `contract-check.md`,
`docs-sync.md`, `fan-out-synthesize.md`, `flow.md`, `lint.md`, `new-contract-rule.md`, `orient.md`,
`refresh-memory.md`, `review.md`, `test.md`, `verify-work.md`.

**No existing test asserts the total count.** `tools/harness_lint/tests/test_commands.py` is
glob-driven (`_command_files()` globs `harness/commands/*.md`, `test_commands.py:49-50`) and
parametrizes over whatever it finds — it structurally validates every command's frontmatter but
never asserts `len(_command_files()) == 18`. It also asserts a NAMED SUBSET must be present
(`EXPECTED_GOLDEN_ADJACENT`, `test_commands.py:44-46,58-62`) but that is a subset-presence check,
not a total-count check. **Criterion 4 ("18 → 18") must therefore be proven procedurally** — run
`ls harness/commands/*.md | wc -l` (or the Python equivalent) before touching `component.md` and
again after, and record both in the plan/verification evidence — not by pointing at an existing
gate, because none exists. Optionally, the plan may ADD a `test_command_count_is_stable()`
regression test asserting `len(_command_files()) == 18` in `test_commands.py`; this is a net-new
test (fine — the no-growth constraint is about commands/gates/jobs, not tests) and would make
future phases' command-count claims self-proving rather than re-measured by hand each time.

### Q6. Validation Architecture — see below.

## State of the Art

No external ecosystem changes apply — this phase is a pure internal join over already-shipped
Phase 47 machinery. There is no "old approach / new approach" axis; skipping this section's table.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `conventions_for(path, cfg=None, facts=None)` is the right signature/location (`tools/harness_config/loader.py`) | Architecture Patterns, Q3 | Low — this is explicitly Claude's discretion per CONTEXT.md ("exact function/module naming"); any equivalent signature satisfies MONO-05/06 as long as it accepts injectable cfg/facts for the falsifiable test. |
| A2 | The nearest-`AGENTS.md` pointer is computed by a fresh filesystem walk over `Path.parents`, not a new package-facts field | Architecture Patterns | Low — alternative designs (e.g. precomputing an `agents_md` field into `package_facts.build_facts()` itself) are equally valid; this is an implementation choice, not a correctness question, since either approach can pass the same tests. |
| A3 | A `test_command_count_is_stable()` test does not violate the "no growth" constraint since it targets test count, not command/gate/job count | Q5 | Low — the ROADMAP's no-growth language names commands/gates/CI-jobs explicitly; a test is unaffected. Flagged only because the planner should confirm this reading before adding the test. |

## Open Questions (residual, not fully resolved by this session)

1. **Should `conventions_for()` accept a raw filesystem path string or something path-relative to
   repo root?**
   - What we know: `owning_package()` operates on POSIX-relative paths matched against `dir`
     fields that are themselves POSIX-relative (`ownership.py:33-34,47`).
   - What's unclear: whether callers (agents, `/component`) will naturally have an absolute path
     or a repo-relative one; a normalization step may be needed at the `conventions_for()`
     boundary.
   - Recommendation: accept a repo-relative POSIX string (mirrors `owning_package`'s own contract)
     and let callers normalize before calling — keeps the function pure and consistent with its one
     dependency.

2. **Exact rendered section layout for the new `package-facts.md` addition** (table columns, header
   text) is unresolved — CONTEXT.md leaves field spelling to Claude's discretion. Recommend mirroring
   the existing `## Packages` / `## Dependency Edges` table style exactly (pipe-table, `DERIVED`
   header already covers the whole file) for visual consistency.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x via `uv run pytest` (repo-standard; see `pyproject.toml` dev deps) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (not modified by this phase) |
| Quick run command | `uv run pytest tools/harness_config/tests tools/memory_regen/tests tools/harness_lint/tests/test_commands.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MONO-05 | `conventions_for(path)` nearest-wins over a real nested pair (`libs/python` vs root) | unit | `uv run pytest tools/harness_config/tests/test_conventions_for.py -x` | ❌ Wave 0 |
| MONO-05 | Path with no enclosing package returns explicit-default profile | unit | same file, additional test function | ❌ Wave 0 |
| MONO-06 | Editing `[[languages]]` changes every affected profile with no profile edited (falsifiable form) | unit | same file, `test_editing_language_command_changes_every_affected_profile_with_no_profile_edit` | ❌ Wave 0 |
| MONO-06 | A package whose language is absent from `[[languages]]` reports no commands, never raises | unit | same file | ❌ Wave 0 |
| MONO-07 | `harness/commands/component.md` step 2 body names the profile-population action, mandated order intact | structural | `uv run pytest tools/harness_lint/tests/test_commands.py -x` (existing, extend if a new assertion is added) | ✅ existing file, extend |
| MONO-07 | Emit round-trip byte-clean after editing `component.md` | integration | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode/command/component.md .claude/commands/component.md` | ✅ mechanism exists (`tools/harness_emit`), no new test file strictly required but recommend extending `tools/harness_emit/tests/test_emit_determinism.py` snapshot |
| SC4 (18→18) | Command count unchanged | manual/procedural | `ls harness/commands/*.md \| wc -l` (before and after; optionally add `test_command_count_is_stable`) | ❌ no existing count assertion (Q5) |
| SC4 (no gate/job growth) | `ci.yml` job set and `gate.needs` byte-unchanged | structural | `git diff --exit-code -- .github/workflows/ci.yml` (should be empty if Q1's recommendation is followed) | N/A — recommend zero diff, not a new test |
| package-facts extension determinism | `render(build_facts())` byte-identical across regen | unit | `uv run pytest tools/memory_regen/tests/test_package_facts.py -x` (existing tests already cover this at file granularity once the new section is added to `render()`) | ✅ existing file, extend assertions |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_config/tests tools/memory_regen/tests -x`
- **Per wave merge:** `uv run pytest` (full suite) + `uv run python -m tools.harness_emit` idempotency check
- **Phase gate:** Full suite green before `/gsd:verify-work`; `stale-derived` and `emit-drift` CI
  jobs green (unchanged job definitions, per Q1).

### Wave 0 Gaps
- [ ] `tools/harness_config/tests/test_conventions_for.py` — covers MONO-05, MONO-06 (new file;
  follows the synthetic-cfg/facts idiom of `test_effective_packages.py`)
- [ ] Extend `tools/memory_regen/tests/test_package_facts.py`'s snapshot fixture and structural
  assertions to cover the new rendered section — covers the package-facts extension
- [ ] Extend `tools/harness_lint/tests/test_commands.py` (optional, recommended) with
  `test_command_count_is_stable()` — covers SC4's count claim with a durable gate instead of a
  one-time manual measurement
- [ ] No new pytest framework/config needed — the existing `uv run pytest` setup fully covers this
  phase's test surface

*(No conftest/fixture gaps: `tmp_path` and synthetic-dict idioms already used throughout
`tools/harness_config/tests` and `tools/memory_regen/tests` cover every case this phase needs.)*

## Security Domain

`security_enforcement` is absent from `.planning/config.json` → treated as enabled per the
protocol default; assessed and found **not materially applicable** to this phase's actual attack
surface.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface — internal derived-plane read-path code, no user identity. |
| V3 Session Management | No | N/A. |
| V4 Access Control | No | N/A — file-scope access is git-controlled, unchanged by this phase. |
| V5 Input Validation | Marginal | `conventions_for(path)` takes an arbitrary string path; `owning_package()` already treats it as an opaque `PurePosixPath` with no filesystem access performed inside `ownership.py` itself (pure string-segment comparison, `ownership.py:47-53`) — no path-traversal surface since nothing is opened by that function. The NEW filesystem walk for "nearest AGENTS.md" (Architecture Patterns, step 8) DOES touch the filesystem — it must stay bounded to `Path.parents` of a repo-relative path and never escape the repo root; this is a design note for the planner, not a hardening gate. |
| V6 Cryptography | No | N/A — no secrets, no crypto in this phase. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via a crafted `path` argument to `conventions_for()` reaching outside the repo when walking for `AGENTS.md` | Tampering / Information Disclosure | Resolve the input path against `_REPO_ROOT` and refuse (or clamp) any resolved path that escapes it, mirroring `package_facts.py`'s own `_REPO_ROOT`-anchored posture (`package_facts.py:48`). Low real-world risk since callers are internal agents/commands, not untrusted external input — noted for completeness, not a blocking gate per the deferred-ideas note (no enforcement gate this phase). |

## Sources

### Primary (HIGH confidence — code read this session, `path:line` cited throughout)
- `tools/memory_regen/package_facts.py` (full file read)
- `tools/contract_graph/ownership.py` (full file read)
- `tools/contract_graph/__init__.py` (re-export mechanism)
- `tools/contract_graph/tests/test_ownership.py` (full file read)
- `tools/harness_config/loader.py` (full file read)
- `tools/harness_config/tests/test_effective_packages.py`, `test_topology_relationships.py`
- `harness/project.toml` (full file read)
- `harness/commands/component.md` (full file read, line-numbered)
- `.github/workflows/ci.yml` (`stale-derived`, `emit-drift`, `gate.needs` sections)
- `tools/harness_lint/tests/test_ci_stale_derived.py`, `test_commands.py`, `test_language_config.py`,
  `test_derived_freshness.py` (full files read)
- `tools/memory_regen/tests/test_package_facts.py` (full file read)
- `tools/harness_emit/project_command.py` (partial read, frontmatter projection)
- `.memory/derived/package-facts.md` (live artifact, confirms `libs/python` vs root dirs/languages)
- `.gitignore` (contents-form re-include pattern, lines 22-28)
- `.planning/phases/47-package-facts/47-05-SUMMARY.md` (the CI-widening precedent this phase should
  mirror IF a new artifact were chosen — used here to justify why it should NOT be chosen)
- `.planning/ROADMAP.md` (`#### Phase 48: Convention Profiles` section, `#### Phase 47`, no-growth
  constraint prose)
- `.planning/REQUIREMENTS.md` (MONO-05/06/07 text)
- `.planning/phases/48-convention-profiles/48-CONTEXT.md` (full file read)
- `CLAUDE.md` (root, project constraints)
- `find … -name AGENTS.md` (live repo, confirms 7 tracked files / 3 fixtures / real `libs/python`
  and root `AGENTS.md` existence)

### Secondary / Tertiary
None — objective explicitly excludes web search; all findings verified directly against this
checkout's code and config.

## Project Constraints (from CLAUDE.md)

- Language boundary = process/file/DB only; no object/in-process cross-language calls. Not
  triggered by this phase (pure Python, single language).
- Derived plane (`docs/reference`, `.memory/derived/*`) is machine-generated only, header
  `DERIVED — do not hand-edit`, no timestamps, byte-identical on regeneration — binds any extension
  to `package_facts.render()`.
- Decisions are append-only ADR; this phase's CONTEXT.md decisions are already locked and should
  not be re-litigated by the plan.
- No model identity in commits/PRs/code comments — applies to all new code/docstrings this phase
  produces.
- GEN-04: nothing under `tools/`, `harness/`, `libs/` may name or path-reference `examples/` —
  binds the synthetic fixtures recommended in Q4/Q3 (domain-neutral ids only, mirroring
  `test_ownership.py`'s and `test_effective_packages.py`'s existing "a"/"b"/"root" convention).
- GSD workflow enforcement: direct file edits outside a GSD command are disallowed; this research
  output itself makes no repo edits.

## Metadata

**Confidence breakdown:**
- Standard stack (reuse map): HIGH — every function/signature cited was read directly this session.
- Architecture (join design + adapter): HIGH for the join logic (all inputs verified); MEDIUM for
  the exact "nearest AGENTS.md" implementation choice (A2 — no existing helper to point at, so this
  is a fresh design, not a verified pattern).
- Pitfalls: HIGH — all four are demonstrated with cited code, not speculation (Pitfall 1 verified by
  reading `effective_packages()`'s own test proving the no-`dir` case exists; Pitfall 2 verified by
  reading the live `package-facts.md`; Pitfall 4 verified by reading Phase 47's own summary).

**Research date:** 2026-07-30
**Valid until:** Stable — this research is grounded in code committed to this checkout as of
2026-07-30; re-validate only if Phase 47's artifacts (`package_facts.py`, `ownership.py`,
`loader.py`) change before Phase 48 executes.
