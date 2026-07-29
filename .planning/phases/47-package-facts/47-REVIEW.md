---
phase: 47-package-facts
reviewed: 2026-07-30T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - tools/adoption_scan/detect.py
  - tools/adoption_scan/tests/test_detect.py
  - tools/memory_regen/package_facts.py
  - tools/memory_regen/tests/test_package_facts.py
  - tools/memory_regen/tests/__snapshots__/test_package_facts.ambr
  - tools/harness_config/loader.py
  - tools/harness_config/tests/test_effective_packages.py
  - tools/harness_lint/tests/test_package_facts_override.py
  - examples/log-parser/tests/test_package_facts_override_instance.py
  - tools/contract_graph/ownership.py
  - tools/contract_graph/tests/test_ownership.py
  - tools/harness_lint/tests/test_ci_stale_derived.py
  - .github/workflows/ci.yml
  - .gitignore
  - harness/commands/refresh-memory.md
  - harness/agents/curator.md
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
fixed_at: 2026-07-30T00:00:00Z
fix_status: all_fixed
fixed:
  warning: 3
  info: 2
  total: 5
skipped: 0
---

# Phase 47: Code Review Report

**Reviewed:** 2026-07-30
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the package-facts derived-artifact generator (`tools/memory_regen/package_facts.py`),
its five manifest-kind dependency parsers in `tools/adoption_scan/detect.py`, the
`effective_packages()` override-layering in `tools/harness_config/loader.py`,
`owning_package()` attribution in `tools/contract_graph/ownership.py`, and the CI/gitignore/
command wiring that adds `package-facts.md` to the stale-derived gate. Overall the code is
careful about determinism (sorted output, no dict/set-iteration leakage into rendered text,
committed-vs-gitignored plane discipline) and the test suite mostly proves genuine behavior
rather than tautologies — `owning_package()`'s segment-based (not string-prefix) directory
matching correctly avoids the `contracts-extra/x.json` misattribution risk flagged in scope, and
`effective_packages()` copies dicts before merging so caller-owned data is never mutated.

Two concrete correctness gaps were verified by direct reproduction (not just code reading):
Windows-style backslash paths in a `.csproj` `<ProjectReference Include="...">` silently fail to
resolve into a dependency edge, and a Python package whose own declared name differs from a
dependant's reference to it only by hyphen/underscore (a routine PEP 503 equivalence) also
silently drops the edge. Neither crashes — both degrade gracefully to "no edge," consistent with
the module's own "never fabricate" contract, but both produce an incomplete/wrong package graph
that reviewers of `.memory/derived/package-facts.md` will not know to distrust.

## Warnings

### WR-01: `.csproj` ProjectReference paths using backslash separators silently fail to resolve

**File:** `tools/memory_regen/package_facts.py:161-168` (consumes `tools/adoption_scan/detect.py:284-293`)
**Issue:** `_dependencies_from_csproj` returns the raw `Include` attribute value verbatim as
`dep["path"]`. `build_facts()` then does:
```python
own_dir = PurePosixPath(path).parent
normalized = posixpath.normpath(str(own_dir / dep["path"]))
```
`PurePosixPath` treats `\` as an ordinary filename character, not a separator, so a Windows-style
reference (`Include="..\WidgetCore\WidgetCore.csproj"`, which MSBuild accepts on any OS and is
what Visual-Studio-authored `.csproj` files commonly emit) produces a mangled path like
`WidgetApp/..\WidgetCore\WidgetCore.csproj` that can never match a real `manifest_by_path` key
(git-tracked paths are always forward-slash). Verified by direct reproduction:
```
>>> detect.detect_dependencies("WidgetApp/WidgetApp.csproj", "*.csproj",
...   '<ProjectReference Include="..\\WidgetCore\\WidgetCore.csproj" />')
[{'name': '..\\WidgetCore\\WidgetCore.csproj', 'kind': 'runtime',
  'path': '..\\WidgetCore\\WidgetCore.csproj'}]
>>> normalized  # what build_facts() computes
'WidgetApp/..\\WidgetCore\\WidgetCore.csproj'   # never equals 'WidgetCore/WidgetCore.csproj'
```
The edge is dropped exactly like an external/unresolvable reference — no error, no warning — so
a repo whose `.csproj` files were authored/edited on Windows loses real intra-repo dependency
edges from the derived graph with no signal that anything went wrong.
**Fix:** Normalize `Include` path separators before building the POSIX path, e.g.:
```python
include_posix = include.replace("\\", "/")
entries.append({"name": include_posix, "kind": "runtime", "path": include_posix})
```
in `_dependencies_from_csproj`, or equivalently in `build_facts()` before the `own_dir / dep["path"]` join.

**Resolution:** fixed — commit `379af8a`. `_dependencies_from_csproj` now normalizes `Include`
backslashes to forward slashes before the entry is built. Regression test:
`tools/adoption_scan/tests/test_detect.py::test_csproj_project_reference_backslash_separators_normalized`
(reproduces the exact reported repro case) — failed before the fix (asserted normalized path
mismatched the raw backslash string), passed after.

### WR-02: No PEP 503 name normalization when matching declared vs. referenced Python package names

**File:** `tools/adoption_scan/detect.py:257-259` (`_dependency_bare_name`), `tools/memory_regen/package_facts.py:169-172` (id-based edge resolution)
**Issue:** `_package_id()` uses a pyproject's own `[project].name` verbatim, and
`_dependencies_from_pyproject` / edge resolution in `build_facts()` matches a dependency's bare
name against that id via exact string equality (`if target_id in manifest_by_id`). Per PEP
503/508, `Foo_Bar`, `foo-bar`, and `foo.bar` are the SAME canonical distribution name to any real
resolver (pip/uv), but this code treats them as distinct strings. Verified by direct
reproduction: a package declared `name = "widget_core"` and a dependant declaring
`dependencies = ["widget-core"]` (the far more common on-disk convention, hyphenated) produced
`edges: []` — the real intra-repo dependency is silently dropped, matching this phase's own
review-focus warning ("a name that fails to normalize silently drops a real edge").
**Fix:** Normalize both sides (case-fold, collapse `[-_.]+` to a single `-`) before comparing/
indexing, e.g. add a small `_normalize_pep503(name: str) -> str` helper and key
`manifest_by_id`/`id_by_manifest` and the dependency lookup through it, per PEP 503 §"Normalized
Names".

**Resolution:** fixed — commit `6eb2a74`. Added `_normalize_pep503()` in `package_facts.py` and a
PEP-503-normalized lookup index scoped to `pyproject.toml` packages only (kept narrow so
`package.json`/`go.mod`/`Cargo.toml` name conventions, which are not PEP 503, are never folded
together with Python's). The rendered package id still comes from the manifest's own declared
name — normalization is comparison-only, per the fix's own framing. Regression test:
`tools/memory_regen/tests/test_package_facts.py::test_pyproject_dependency_matches_declared_name_across_pep503_variants`
(uses the review's own `widget_core`/`widget-core` example) — failed before the fix
(`edges: []`), passed after, and additionally asserts the rendered id stays `widget_core`
(declared form), never the normalized form.

### WR-03: Manifest reads can crash the whole generator on any encoding/parse failure

**File:** `tools/memory_regen/package_facts.py:137` (`text = (repo_root / path).read_text(encoding="utf-8")`) and the per-kind parsers it feeds (`tomllib.loads`, `json.loads`, `ET.fromstring`) in `tools/adoption_scan/detect.py`
**Issue:** `build_facts()` reads every discovered manifest with a hard `encoding="utf-8"` and
passes the text straight into `tomllib.loads` / `json.loads` / `ET.fromstring` with no
try/except anywhere in the call chain. A manifest that is not valid UTF-8 (e.g. an XML-declared
`encoding="utf-16"` `.csproj`, or a stray BOM-only file), or one that is syntactically malformed
TOML/JSON/XML (a common transient state while a developer edits a manifest — this generator is
invoked from `/refresh-memory` and the CI stale-derived gate, not on a hermetically validated
tree), raises an unhandled `UnicodeDecodeError`/`tomllib.TOMLDecodeError`/`json.JSONDecodeError`/
`xml.etree.ElementTree.ParseError` that aborts the entire regeneration rather than degrading
gracefully for the one bad manifest.
**Fix:** Wrap the per-manifest read+parse in a try/except that logs/skips the offending manifest
(or surfaces a clear, single-manifest-scoped error) instead of letting the whole run die on one
malformed file; align with the module's own stated "never fabricate, never crash on partial
input" posture used elsewhere (e.g. `detect_dependencies` returning `[]` for an unrecognized
kind rather than raising).

**Resolution:** fixed — commit `d790cd6`. `build_facts()` now wraps the per-manifest
`read_text` (catching `OSError`/`UnicodeDecodeError`) and the `_package_id`/`detect_dependencies`
parse calls (catching `tomllib.TOMLDecodeError`/`json.JSONDecodeError`/
`xml.etree.ElementTree.ParseError`) individually per manifest. On failure: the package is still
listed (directory-name fallback id, since the declared name could not be read), no dependency
edges are derived from that one manifest, and a `package_facts: ...` message is printed to
stderr — no new artifact column, no new contract, per the fix-scope constraint. Regression test:
`tools/memory_regen/tests/test_package_facts.py::test_malformed_manifest_does_not_crash_generator`
— failed before the fix (uncaught `tomllib.TOMLDecodeError` aborted `build_facts()`), passed
after (package still listed, stderr message present).

## Info

### IN-01: `.csproj` dependency detection has no XML-namespace fallback for legacy-style project files

**File:** `tools/adoption_scan/detect.py:284-293`
**Issue:** `root.findall(".//ProjectReference")` only matches unqualified elements. Legacy
(pre-SDK-style) `.csproj` files commonly declare
`xmlns="http://schemas.microsoft.com/developer/msbuild/2003"` on the `<Project>` root, which
puts every child element (including `ProjectReference`) into that namespace; `findall` with an
unqualified tag name then silently matches nothing. All `.csproj` files in this repo today are
SDK-style (no `xmlns`), so this does not currently bite, but the parser will silently produce
zero dependencies for any legacy-style project someone adds later — no error, just a package with
no outgoing edges.
**Fix:** Either detect and strip/qualify the default namespace before `findall`, or explicitly
try `.//{http://schemas.microsoft.com/developer/msbuild/2003}ProjectReference` as a fallback when
the unqualified search returns nothing.

**Resolution:** fixed — commit `0ebc199`. `_dependencies_from_csproj` now falls back to
`.//{http://schemas.microsoft.com/developer/msbuild/2003}ProjectReference` (exactly the
suggested fallback) whenever the unqualified `findall` returns no matches. Regression test:
`tools/adoption_scan/tests/test_detect.py::test_csproj_project_reference_legacy_msbuild_namespace_fallback`
(legacy-style `<Project xmlns="...msbuild/2003" ...>` fixture) — failed before the fix (0
entries parsed), passed after.

### IN-02: `package.json` parsing assumes `dependencies`/`devDependencies` values are objects

**File:** `tools/adoption_scan/detect.py:273-281` (`_dependencies_from_package_json`)
**Issue:** `for name in data.get("dependencies", {})` will raise `TypeError` if a manifest
declares `"dependencies": null` (valid JSON, occasionally seen from hand-edited or
programmatically-emitted `package.json` files) — `.get()`'s default only applies when the key is
absent, not when it is present-but-null. Low likelihood in this repo's own manifests, but the
function's docstring ("version values ignored") implies more input tolerance than it actually
has.
**Fix:** `for name in (data.get("dependencies") or {})` (same pattern for `devDependencies`).

**Resolution:** fixed — commit `f5c7d01`. Applied verbatim: both the `dependencies` and
`devDependencies` loops in `_dependencies_from_package_json` now use `data.get(...) or {}`.
Regression test:
`tools/adoption_scan/tests/test_detect.py::test_package_json_null_dependencies_does_not_raise`
(`"dependencies": null, "devDependencies": null`) — failed before the fix (`TypeError:
'NoneType' object is not iterable`), passed after (`entries == []`).

---

_Reviewed: 2026-07-30_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
