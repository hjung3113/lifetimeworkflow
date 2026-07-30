# Phase 48: Convention Profiles - Pattern Map

**Mapped:** 2026-07-30
**Files analyzed:** 7 (5 modified, 2 new/extended tests + 1 test extension already counted)
**Analogs found:** 7 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `tools/harness_config/loader.py` (add `conventions_for`) | service (config query) | request-response (pure join, no I/O when cfg/facts injected) | `effective_packages()` — same file, `loader.py:200-250` | exact (same file, same layering idiom) |
| `tools/harness_config/__init__.py` (export `conventions_for`) | module (lazy re-export) | request-response | how `effective_packages` was added to `__all__`/`__getattr__` — same file, `__init__.py:16-33` | exact |
| `tools/harness_config/tests/test_conventions_for.py` (new) | test | request-response, unit | `tools/harness_config/tests/test_effective_packages.py` (synthetic cfg/facts idiom) | exact |
| `tools/memory_regen/package_facts.py` (extend `render`/`build_facts`) | service (derived-artifact generator) | batch / transform | its own existing `## Packages` / `## Dependency Edges` section layout, `package_facts.py:252-282` | exact (self-analog) |
| `tools/memory_regen/tests/test_package_facts.py` (extend + snapshot) | test | batch, snapshot | its own existing structure tests + `test_render_matches_committed_snapshot` (synthetic fixture, `package_facts.py:335-381` in test file) | exact (self-analog) |
| `harness/commands/component.md` (step 2 body edit) | config / command (Markdown source) | request-response (agent-invoked) | its own existing step 2 text, `component.md:23-26` | exact (self-analog, in-place edit) |
| `tools/harness_lint/tests/test_commands.py` (add `test_command_count_is_stable`) | test | structural | existing assertions in the same file (`test_golden_adjacent_commands_present`, `test_commands.py:58-62`) + the "consistency gate" idiom in `tools/harness_lint/tests/test_pipeline_config.py` | exact |

## Pattern Assignments

### `tools/harness_config/loader.py` — add `conventions_for(path, cfg=None, facts=None)`

**Analog:** `effective_packages()`, same file (`loader.py:200-250`)

**Imports pattern** (already present at top of file, `loader.py:16-19`):
```python
from __future__ import annotations

import tomllib
from pathlib import Path
```
`conventions_for` needs one more stdlib import for the "nearest AGENTS.md" filesystem walk:
`from pathlib import Path` is already imported; use `Path(path).parents` plus `_REPO_ROOT`
(already defined at `loader.py:23`) to anchor the walk and prevent escaping the repo root
(Security note from RESEARCH.md V5).

**Optional-cfg/facts + lazy in-function import pattern** (copy verbatim shape, `loader.py:226-231`):
```python
def effective_packages(cfg: dict | None = None, facts: dict | None = None) -> list[dict]:
    if cfg is None:
        cfg = load_project()
    if facts is None:
        from tools.memory_regen.package_facts import build_facts

        facts = build_facts()
    ...
```
`conventions_for` must follow the identical signature/defaulting convention — this is what makes
it injectable for the falsifiable MONO-06 test (RESEARCH.md Q3) with **no monkeypatch, no temp
file**.

**Core join pattern to write** (new code — composes 3 existing calls + 1 adapter + 1 filesystem
walk; no analog file does this exact join, but every ingredient has one):
```python
def conventions_for(path: str, cfg: dict | None = None, facts: dict | None = None) -> dict:
    if cfg is None:
        cfg = load_project()
    pkgs = effective_packages(cfg, facts)
    dir_pkgs = [p for p in pkgs if "dir" in p]           # ADAPTER — see "Shared Patterns" below
    owner_id = owning_package(dir_pkgs, path)              # REUSED from tools.contract_graph
    owner = next(p for p in dir_pkgs if p["id"] == owner_id)
    lang = next((l for l in languages(cfg) if l["id"] == owner.get("language")), None)
    return {
        "package": owner["id"],
        "dir": owner["dir"],
        "language": owner.get("language"),
        "test": lang["test"] if lang else None,
        "format": lang["format"] if lang else None,
        "bash_scope": lang["bash_scope"] if lang else None,
        "agents_md": _nearest_agents_md(owner["dir"]),
        "is_default": owner["dir"] == ".",
    }
```
Import `owning_package` from `tools.contract_graph` (module-level import is safe here — unlike
`package_facts.build_facts`, `ownership.py` has zero circular-import risk since it imports nothing
from `tools.harness_config`; confirm no cycle before choosing module-level vs in-function import,
mirroring the in-function precedent at `loader.py:229` only if a cycle is found).

**Error handling pattern:** `effective_packages()` and `owning_package()` already raise/degrade
correctly (`ValueError` from `owning_package` only if no root package exists — should never happen
in practice per `ownership.py:43-45`). `conventions_for` adds NO new raise path for the
"language absent from `[[languages]]`" case — that must degrade to `lang = None` → all three
command fields `None`, never raise (CONTEXT.md decision, RESEARCH.md Pitfall/Q — mirrors
`effective_packages`'s "declared-only, never raise" posture at `loader.py:209-216`).

---

### `tools/harness_config/__init__.py` — export `conventions_for`

**Analog:** same file, the existing `__all__` list + `__getattr__` dispatch (`__init__.py:16-33`)

**Exact pattern to copy** (one-line addition to `__all__`, zero other code changes — the
`__getattr__` body is already generic and needs no per-symbol branch):
```python
__all__ = [
    "components",
    "contract_graph_relationships",
    "conventions_for",          # <- ADD (alphabetical, mirrors existing sort order)
    "effective_packages",
    "effective_relationships",
    "language_bash_scopes",
    "languages",
    "load_project",
    "pipeline",
]
```
The `__getattr__` function (`__init__.py:28-33`) needs **no edit** — it already does
`getattr(loader, name)` generically for anything in `__all__`.

---

### `tools/harness_config/tests/test_conventions_for.py` (new)

**Analog:** `tools/harness_config/tests/test_effective_packages.py` (full file, 75 lines)

**Idiom to copy exactly** — no `build_facts()`, no `load_project()`, no `monkeypatch`, no
temp-file config; synthetic `facts`/`cfg` dicts passed straight into the function under test,
domain-neutral ids (`"a"`, `"b"`, `"root"` — never `examples/*` literals, GEN-04):
```python
# mirrors test_effective_packages.py:14-30 shape
from tools.harness_config import conventions_for

def test_editing_language_command_changes_every_affected_profile_with_no_profile_edit() -> None:
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
```
This exact test is prescribed verbatim in RESEARCH.md Q3 (`48-RESEARCH.md:366-383`) — copy it,
do not re-derive it.

**Real-tree nested-pair test** (no analog — new, but uses the live-tree read idiom from
`test_package_facts.py:30-34`'s `package_facts.build_facts()` real-tree calls, applied here via
`load_project()`/default `facts=None`):
```python
def test_real_nested_pair_libs_python_vs_root_differ_on_package_and_agents_md() -> None:
    inner = conventions_for("libs/python/normalize/x.py")
    outer = conventions_for("tools/some_module/y.py")
    assert inner["package"] != outer["package"]
    assert inner["dir"] == "libs/python"
    assert inner["agents_md"] == "libs/python/AGENTS.md"
    assert outer["is_default"] is True
    assert outer["agents_md"] == "AGENTS.md"
    # commands are IDENTICAL for this pair (Pitfall 2) — do NOT assert test/format differ here.
    assert inner["test"] == outer["test"]
```

**No-enclosing-package / explicit-default test:**
```python
def test_path_outside_any_package_returns_explicit_default() -> None:
    facts = {"packages": [{"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"}]}
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}
    profile = conventions_for("some/unowned/path.py", cfg=cfg, facts=facts)
    assert profile["is_default"] is True
    assert profile["package"] == "root"
```

**Language-absent-from-`[[languages]]`-degrades test** (mirrors
`test_component_with_no_matching_package_stays_declared_only_no_raise`,
`test_effective_packages.py:33-45`, same "degrade, never raise" idiom):
```python
def test_package_whose_language_is_absent_from_languages_reports_no_commands() -> None:
    facts = {"packages": [{"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "rust"}]}
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}
    profile = conventions_for("a/whatever.rs", cfg=cfg, facts=facts)
    assert profile["language"] == "rust"
    assert profile["test"] is None
    assert profile["format"] is None
```

**Supplementary synthetic commands-differ fixture** (recommended by RESEARCH.md Q4, a
two-language synthetic pair proving the case the real tree cannot):
```python
def test_synthetic_two_language_nested_pair_commands_differ() -> None:
    facts = {"packages": [
        {"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"},
        {"id": "inner", "manifest": "inner/inner.csproj", "dir": "inner", "language": "csharp"},
    ]}
    cfg = {"languages": [
        {"id": "python", "test": "pytest", "format": "ruff", "bash_scope": "uv *"},
        {"id": "csharp", "test": "dotnet test", "format": "dotnet format", "bash_scope": "dotnet *"},
    ]}
    outer = conventions_for("top.py", cfg=cfg, facts=facts)
    inner = conventions_for("inner/x.cs", cfg=cfg, facts=facts)
    assert outer["test"] != inner["test"]
```

---

### `tools/memory_regen/package_facts.py` — extend `render()`/`build_facts()`

**Analog:** its own existing `## Packages` table section, `package_facts.py:264-270`

**Section layout pattern to copy** (mirror the pipe-table style exactly for the new
`## Convention Profiles` section; header text follows `DERIVED_HEADER`, `package_facts.py:53`):
```python
# package_facts.py:264-270 (existing "## Packages" section — mirror this shape)
lines += [
    "",
    "## Packages",
    "",
    "| id | manifest | dir | language |",
    "| --- | --- | --- | --- |",
]
for pkg in facts["packages"]:
    lines.append(f"| {pkg['id']} | {pkg['manifest']} | {pkg['dir']} | {pkg['language']} |")
```
New section (append after `## Dependency Edges`, `package_facts.py:272-280`), computed by calling
`tools.harness_config.conventions_for` per package `dir` — NOT re-deriving the join in this
module (would violate "Don't Hand-Roll" from RESEARCH.md). This creates a NEW dependency
`package_facts.py` → `tools.harness_config` — verify no import cycle (`tools.harness_config`
already imports `tools.memory_regen.package_facts` lazily inside `effective_packages`,
`loader.py:229`; a module-level import here would be circular — use the same
**in-function/lazy import** pattern `loader.py:229` uses, or compute the join inline in
`package_facts.py` without importing `conventions_for` at all if a cycle is confirmed).

**Determinism/no-timestamp constraint** (already enforced by existing tests — verify the new
section obeys the same constraint, `package_facts.py` module docstring lines 16-19, and
`DERIVED_HEADER` at line 53): no wall-clock, no raw float, stable sort — reuse `sorted(...,
key=...)` idiom already used for `packages.sort(key=lambda pkg: pkg["manifest"])`
(`package_facts.py:192`).

---

### `tools/memory_regen/tests/test_package_facts.py` — extend structural tests + snapshot

**Analog:** its own existing tests, especially:
- `test_real_tree_render_structure` (`test_package_facts.py:64-80`) — extend to also assert the
  new section header/no-timestamp/non-empty on the LIVE tree, in-memory only (never committed,
  GEN-04 constraint — this pattern is already followed at lines 64-80, do not deviate).
- `test_render_matches_committed_snapshot` (`test_package_facts.py:335-381`) — the hermetic,
  synthetic, domain-neutral fixture repo (git-plumbing `tmp_path` idiom) is the ONLY place a
  snapshot may be taken. **Extend THIS fixture's synthetic packages to include the new profile
  fields in the expected rendered output** rather than adding a second snapshot test — the
  existing fixture already has cross-language packages (`pyproject.toml` + `package.json` +
  `.csproj`, lines 350-368) suitable for exercising differing profiles.

**Explicit warning (CONTEXT.md + this session's regression history):** a snapshot must NEVER be
taken over `package_facts.build_facts()` / `package_facts.render()` called against the REAL repo
tree (no `repo_root` override) — that would embed `examples/log-parser/**` paths into a file
under `tools/`, tripping GEN-04's `test_core_no_example_dep.py` guard. This exact regression
happened in Phase 47 and was fixed by switching to the synthetic fixture at
`test_package_facts.py:347-368` — do not reintroduce it. Any new assertions covering the profile
section on the real tree must stay **in-memory** (call `build_facts()`/`render()` directly in the
test body and assert on the returned string, as `test_real_tree_render_structure` already does),
never write that output to a `.ambr`/syrupy snapshot file.

---

### `harness/commands/component.md` — step 2 body edit

**Analog:** its own existing step 2 text (`component.md:23-26`)

**Current text to extend** (append the profile-population action to step 2, do NOT add a step 4):
```markdown
2. **Self-sufficient per-package AGENTS.md** — write `components/<name>/AGENTS.md` that
   **RESTATES the non-negotiables verbatim** (contract-first, §4.3–4.6 boundary invariants,
   constitution-plane-is-gated, derived-not-hand-edited). Codex replaces nested AGENTS.md rather
   than concatenating, so the file must be self-sufficient — never inherit-only (P11).
```
Append (same numbered step, same bullet, or a sub-bullet under step 2 — CONTEXT.md: "no step 4 is
added"): regenerate `.memory/derived/package-facts.md` (`uv run python -m
tools.memory_regen.package_facts`) and assert `conventions_for("components/<name>/...")` now
resolves to the new package (not raising / not falling through to the default). This mirrors the
"Guard" section's existing enforced-order framing (`component.md:31-35`) — add the assertion as
part of the guard language, not a new numbered step.

**Re-emit requirement (Pitfall 4, RESEARCH.md):** after editing `harness/commands/component.md`,
run `uv run python -m tools.harness_emit` and stage the resulting diffs in
`.opencode/command/component.md` and `.claude/commands/component.md` — these are
machine-projected, never hand-edited (`tools/harness_emit/project_command.py`). Verify a second
immediate re-emit is a no-op (idempotency), mirroring
`tools/harness_emit/tests/test_emit_determinism.py`'s sha256-per-file comparison idiom.

---

### `tools/harness_lint/tests/test_commands.py` — add `test_command_count_is_stable`

**Analog:** existing assertions in the same file, especially `test_golden_adjacent_commands_present`
(`test_commands.py:58-62`) for the "glob → assert on the resulting set" shape, plus the
consistency-gate idiom in `tools/harness_lint/tests/test_pipeline_config.py`
(`test_component_ids_unique`, `test_pipeline_config.py:46`+) for "assert a derived count/set
property, not a presence subset."

**Pattern to copy** (uses the file's own existing `_command_files()` helper,
`test_commands.py:49-50` — do not write a second glob):
```python
def test_command_count_is_stable() -> None:
    """Live command count is pinned at 18 (v2.6 no-growth constraint) — RESEARCH.md Q5.

    Failing this test on a legitimate new command means bumping the constant deliberately, not a
    regression by itself; it converts a one-time manual measurement into a durable, self-proving
    gate for future phases' "N -> N" claims.
    """
    assert len(_command_files()) == 18
```
Place it near `test_golden_adjacent_commands_present` (same section of the file, both are
module-level "assert on the whole `_command_files()` set" tests, unlike the
`@pytest.mark.parametrize`-per-file tests below them).

## Shared Patterns

### Optional-`cfg`/`facts` injectable-pure-function signature
**Source:** `tools/harness_config/loader.py:200` (`effective_packages`), `loader.py:90`
(`effective_relationships`)
**Apply to:** `conventions_for(path, cfg=None, facts=None)` — the ONLY function in this module
that touches the filesystem is `load_project()` (`loader.py:32-39`); every other function accepts
an optional injectable `cfg`/`facts` to bypass file I/O for tests. `conventions_for` must follow
this convention exactly — it is what makes the MONO-06 falsifiable test possible without
`monkeypatch` or a temp-file config.
```python
if cfg is None:
    cfg = load_project()
```

### The `"dir"`-key adapter filter (explicitly called out by the assignment)
**Source:** RESEARCH.md Pitfall 1 + Q2 (`48-RESEARCH.md:238-253,338-346`); NOT present in any
existing file — this is new, local, one-line code that must live in `conventions_for()` itself.
**Apply to:** `tools/harness_config/loader.py`'s new `conventions_for` function, immediately before
calling `owning_package()`.
```python
dir_pkgs = [p for p in effective_packages(cfg, facts) if "dir" in p]
owner_id = owning_package(dir_pkgs, path)
```
**Do NOT** add this filter inside `tools/contract_graph/ownership.py` — that module's docstring
(`ownership.py:9-13`) mandates it stay a pure, dependency-free, unconditional-`package["dir"]`
lookup (`ownership.py:51`, a bare subscript, deliberately no `.get`). `ownership.py` must be
**touched by nothing in this phase**.

### Nearest-enclosing-package lookup — reuse, never reimplement
**Source:** `tools/contract_graph/ownership.py:28-65` (`owning_package`)
**Apply to:** `conventions_for()` exclusively. No second path-matcher, no second command table
(CONTEXT.md explicit constraint). Import as `from tools.contract_graph import owning_package`
(package already re-exports it, mirrors how `tools/harness_config/__init__.py` re-exports its own
symbols — check `tools/contract_graph/__init__.py:16-18,26` for the exact import path before
writing the new code).

### Derived-plane render/write/main triad
**Source:** `tools/memory_regen/package_facts.py:252-311` (`render`, `write`, `main`)
**Apply to:** No new triad is created — `render()`/`write()`/`main()` are extended in place, not
duplicated (CONTEXT.md/RESEARCH.md Q1: extend, don't add a sibling artifact). The existing
`DERIVED_HEADER` (`package_facts.py:53`), no-timestamp, byte-identical-on-regen contract
(`package_facts.py:16-19`) binds the new section too.

### GEN-04 domain-neutral test ids
**Source:** `tools/harness_config/tests/test_effective_packages.py` header comment (lines 3-4) and
`tools/contract_graph/ownership.py` module docstring (lines 15-18)
**Apply to:** every new test in `test_conventions_for.py` and any new fixtures in
`test_package_facts.py` — use `"a"`/`"b"`/`"root"`/`"inner"`/`"widget-*"` style ids, never
`examples/log-parser/**` literals. Real-tree assertions (the one exception, `libs/python` vs
root) are permitted only as IN-MEMORY assertions, never committed to a snapshot file.

## No Analog Found

None — every file in scope has at least a role-match or exact self-analog. The only genuinely
new composition (the `conventions_for` join itself, and the filesystem walk for "nearest
`AGENTS.md`") has no direct analog because RESEARCH.md confirms no existing helper answers
"nearest ancestor directory containing file X" — this is flagged as MEDIUM confidence (A2 in
RESEARCH.md's Assumptions Log) rather than a missing-analog gap; the design is small and
stdlib-only (`pathlib.Path.parents`) and should stay bounded to `_REPO_ROOT` per the V5 security
note.

## Metadata

**Analog search scope:** `tools/harness_config/`, `tools/memory_regen/`, `tools/contract_graph/`,
`tools/harness_lint/tests/`, `harness/commands/`, `tools/harness_emit/tests/`
**Files scanned:** `loader.py`, `__init__.py` (harness_config), `package_facts.py`,
`ownership.py`, `test_effective_packages.py`, `test_package_facts.py`, `component.md`,
`test_commands.py`, `test_emit_determinism.py` (partial), `test_pipeline_config.py` (partial)
**Pattern extraction date:** 2026-07-30
