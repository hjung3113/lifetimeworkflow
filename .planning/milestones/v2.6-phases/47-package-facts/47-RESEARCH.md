# Phase 47: Package Facts - Research

**Researched:** 2026-07-30
**Domain:** This repo's own monorepo tooling (`tools/adoption_scan`, `tools/memory_regen`, `tools/contract_graph`, `tools/harness_config`) — no external ecosystem. Per `ROADMAP.md`, v2.6 runs **no research round**; every claim below is grounded by reading the named modules in this checkout, not web search.
**Confidence:** HIGH (every claim below is `[VERIFIED: this checkout]` — read directly with `path:line` citations — unless marked `[ASSUMED]`)

## Summary

Phase 47 extends four existing, already-battle-tested subsystems rather than building anything new: `tools/adoption_scan/detect.py` (manifest kind detection, currently existence-only), `tools/memory_regen/*` (the committed-derived-artifact idiom, proven by `contracts_index.py`), `tools/harness_config/loader.py` (the `components()`/`pipeline()` passthrough-over-TOML pattern), and `tools/contract_graph/{compile.py,query.py}` (the adjacency/query layer). This checkout has exactly **24 tracked manifests** (20 `pyproject.toml`, 3 `.csproj`, 1 `package.json`, 0 `go.mod`, 0 `Cargo.toml`) and **1 tests/fixtures manifest to exclude** (`tools/adoption_apply/tests/fixtures/polyglot-single/pyproject.toml`), leaving 23 real packages. Measured against the real manifest content, the actual intra-repo dependency edge count today is **exactly 2**, both from `.csproj` `ProjectReference` (`ToyConverter.csproj` → `Normalize.csproj`, `Normalize.Tests.csproj` → `Normalize.csproj`) — no `pyproject.toml` in this repo names another local package as a dependency (no `[tool.uv.sources]` anywhere), and `.claude/package.json` is `{"type":"commonjs"}` with zero dependencies. This is a load-bearing fact for planning: criterion 2's add/remove-a-dependency proof **must** use synthetic fixture manifests, because the production tree barely exercises the edge-parsing code path.

The critical technical seam (Question 1 below) is that `detect.py`'s existing functions are contractually filesystem-access-free — they operate only on `included` entries (`path`/`size`/`sha256`) already assembled by `scan.py`. Dependency **parsing** needs manifest **content** (TOML/JSON/XML text), which `included` entries do not carry. The clean seam is a **new sibling function** in `detect.py` (e.g. `detect_dependencies(path, kind, text)`) that the generator — which already must read files off disk to render markdown — calls with content it read itself. This keeps every existing `detect.py` function's "no filesystem access" invariant intact while satisfying MONO-02's "extend `detect.py`, don't fork it" instruction literally (new function, same module).

`contracts_index.py`'s own docstring says its output is gitignored — that is **stale prose**; `.gitignore:26-27` re-includes `.memory/derived/contracts-index.md` by name, `ci.yml:271-299`'s `stale-derived` job regenerates and diffs it with `git add -A` + `git diff --cached --exit-code`, and `git log` confirms it is a tracked, committed file. The new artifact must follow the **actually-committed** path (gitignore re-inclusion + `stale-derived` regen/diff), not the docstring's stale claim.

**Primary recommendation:** Build `.memory/derived/package-facts.md` as byte-for-byte the same idiom as `contracts_index.py` (rows → render → write → main, `DERIVED` header, syrupy-pinned determinism, `.gitignore` re-inclusion, joins `stale-derived`'s existing regen command + diff path list — adds no job). Put dependency-content-parsing as new pure functions in `detect.py` fed by content the generator reads; keep `detect_manifests` itself unchanged in signature. Attribute contract ownership with a plain nearest-enclosing-directory string-prefix walk in a new `tools/contract_graph` module (no adjacency, no traversal) — and be aware that under this rule, *both* `contracts/**` and `examples/log-parser/contracts/**` currently resolve to the **same root package** (`logparser-harness` at `.`), because no manifest exists between `examples/log-parser/contracts/` and the repo root.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Manifest kind detection (existence) | Tooling / Derived-plane generator (`tools/adoption_scan`) | — | Already implemented, pure path-based, reused verbatim (MONO-02 explicitly forbids a fork). |
| Dependency edge parsing (content) | Tooling / Derived-plane generator (`tools/adoption_scan` + `tools/memory_regen`) | — | Needs manifest bytes; the generator is the one place in this pipeline already doing disk I/O to render an artifact, so it is the natural content-reading caller. |
| Derived artifact rendering + write | Tooling / Derived-plane generator (`tools/memory_regen`) | — | Mirrors `contracts_index.py` exactly: rows → render → write → main, `DERIVED` header, committed via `.gitignore` re-inclusion. |
| `[[components]]` override merge | Tooling / Config loader (`tools/harness_config`) | — | `loader.py` already owns `components()`; a new `effective_packages()`-style layering function belongs beside it, mirroring `effective_relationships()`'s legacy-lower-then-union shape. |
| Contract → package attribution | Tooling / Graph layer (`tools/contract_graph`) | — | MONO-04 explicitly names this module; reuses `compile.py`'s `_tracked_schemas`-style path-glob idiom, not `query.py`'s adjacency traversal (attribution is a lookup, not a graph query). |
| CI freshness proof | CI / `stale-derived` job (`.github/workflows/ci.yml`) | — | Report-only — rides the **existing** job; no new job, no new gate (binding milestone constraint). |

## Standard Stack

This phase adds **zero new external packages** — every dependency below is already resolved in `uv.lock` and used by sibling generators.

### Core (reused, not new)
| Library | Version (verified in this checkout) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `tomllib` | bundled (py311+) | Parse `pyproject.toml` (`[project].dependencies`) | Already the sole parser in `tools/harness_config/loader.py:18` — no PyPI TOML lib needed. |
| Python stdlib `json` | bundled | Parse `package.json` | Same idiom as `tools/docs_sync` reading `*.schema.json` with stdlib `json` (no new dep). |
| Python stdlib `xml.etree.ElementTree` | bundled | Parse `.csproj` `<ProjectReference>` | `.csproj` is well-formed XML; stdlib `ElementTree` is sufficient (no `lxml`, no new dep) — `[ASSUMED]` choice, not yet used elsewhere in this repo, but consistent with the "stdlib only, zero new deps" convention every `tools/*/pyproject.toml` in this repo states explicitly (e.g. `tools/adoption_scan/pyproject.toml`: "Zero new external packages. All stdlib"). |
| Python stdlib `re` | bundled | Fallback line-based parsing for `go.mod`/`Cargo.toml` `require`/path-dependency stanzas (0 real instances in this checkout, but MONO-02 names both kinds) | `go.mod`'s `require (...)` block and `Cargo.toml`'s `[dependencies]` TOML section — the latter is actually parseable with `tomllib` too since `Cargo.toml` is TOML; only `go.mod` needs line-based parsing since it has no stdlib parser. `[ASSUMED]`: no real `go.mod` exists in this checkout to verify against — the parser must be built and unit-tested against a fixture, never a live sample. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `xml.etree.ElementTree` for `.csproj` | A dedicated MSBuild-project parser package | No such package is in `uv.lock`; `.csproj` `<ProjectReference Include="...">` is one XPath (`.//ProjectReference`), stdlib is sufficient and adds zero supply-chain surface — matches every sibling `tools/*` package's "zero new external packages" posture. |
| stdlib `tomllib` for `Cargo.toml` path deps | A TOML crate-specific parser | `Cargo.toml` is plain TOML; `tomllib` already parses `harness/project.toml` and `pyproject.toml` in this repo — reuse, no new dep. |

**Installation:** none — no `uv add` / `npm install` needed for this phase.

## Package Legitimacy Audit

No external packages are introduced by this phase. `slopcheck`/registry verification is **not applicable** — every parser uses stdlib only, matching the "zero new external packages" posture stated in every sibling `tools/*/pyproject.toml` in this repo (e.g. `tools/adoption_scan/pyproject.toml`, `tools/contract_graph/pyproject.toml`, `tools/docs_sync/pyproject.toml`). If the planner's design later needs `uv.lock` to change, that is itself a signal the design has drifted from this research and should be reconsidered before writing tasks.

**Packages removed due to slopcheck `[SLOP]` verdict:** none (no packages proposed).
**Packages flagged as suspicious `[SUS]`:** none.

## Architecture Patterns

### System Architecture Diagram

```
git-tracked files (repo tree)
        │
        ▼
tools/adoption_scan/detect.py::detect_manifests(included)   [UNCHANGED — path-only, existence]
        │  produces: [{path, kind, classification:"observed", evidence}, ...]
        ▼
NEW: tools/adoption_scan/detect.py::detect_dependencies(path, kind, text)   [pure — no I/O]
        │  caller supplies `text` (the generator read it)
        │  produces: [{"name": <declared-dep-name>, "kind": "runtime"|"dev"}, ...] per manifest
        ▼
NEW: tools/memory_regen/package_facts.py   (the generator — DOES the filesystem read)
        │  1. git ls-files (reuse the same idiom scan.py already uses)
        │  2. filter to the 5 recognized manifest kinds, exclude **/tests/fixtures/**
        │  3. read each manifest's text; kind-dispatch to a parser (pyproject/package.json/csproj/
        │     go.mod/Cargo.toml) that resolves declared dep names to OTHER PACKAGE IDS already
        │     discovered in step 2 — unresolved names are DROPPED, never fabricated
        │  4. package id = manifest-declared name, else directory-name fallback
        │  5. render deterministic markdown table → write .memory/derived/package-facts.md
        ▼
.memory/derived/package-facts.md   (COMMITTED — .gitignore re-inclusion, like contracts-index.md)
        │
        ├──▶ NEW: tools/harness_config/loader.py::effective_packages(cfg)  [MONO-03]
        │        field-level layer: [[components]] entries with matching `id` override; no match
        │        stays declared-only, no error (both harness/project.toml + examples/log-parser/
        │        project.toml keep loading with zero edits)
        │
        └──▶ NEW: tools/contract_graph/<module>.py::owning_package(packages, contract_path)  [MONO-04]
                 pure string-prefix walk: nearest ancestor directory of contract_path that is a
                 known package directory, else fall back to the root package ("." )
        │
        ▼
CI: .github/workflows/ci.yml `stale-derived` job (UNCHANGED job set/gate.needs)
        regen: uv run python -m tools.memory_regen.package_facts  [added to the SAME step]
        diff:  .memory/derived/package-facts.md added to the SAME git add -A / diff --cached list
```

### Recommended Project Structure

```
tools/
├── adoption_scan/
│   └── detect.py              # + detect_dependencies(path, kind, text) and 5 kind-specific
│                               #   parser helpers (pure, content-in / edges-out, no filesystem)
├── memory_regen/
│   ├── package_facts.py       # NEW — the generator: reads git-tracked manifests off disk,
│   │                          #   calls detect.detect_manifests + detect.detect_dependencies,
│   │                          #   assembles package records, renders + writes the markdown table
│   └── tests/
│       └── test_package_facts.py   # mirrors test_contracts_index.py's 3-guarantee shape:
│                                   #   determinism, correctness (fixture add/remove-a-dep), snapshot
├── harness_config/
│   └── loader.py               # + effective_packages(cfg=None, package_facts=None) — mirrors
│                                #   effective_relationships()'s "lower/derive then union with
│                                #   declared, field-level layering" shape
├── contract_graph/
│   ├── ownership.py            # NEW — owning_package(packages, contract_path) pure lookup
│   └── tests/
│       └── test_ownership.py
└── harness_lint/
    └── tests/
        └── test_package_facts_override.py  # MONO-03 consistency gate, mirrors
                                             #   test_pipeline_config.py's structural-scan idiom
.memory/derived/
└── package-facts.md            # NEW committed-derived artifact (mirrors contracts-index.md)
```

### Pattern 1: Content-parsing sibling function, not a signature change

**What:** Add `detect_dependencies(path: str, kind: str, text: str) -> list[dict]` as a **new** function beside `detect_manifests` in `detect.py`, rather than widening `detect_manifests`'s own signature or the shape of `included` entries.
**When to use:** Any time a detection ladder function needs manifest *content* but the module's existing invariant (`tools/adoption_scan/detect.py:6-8`: "no filesystem access here... detection can never diverge from what was actually hashed") must be preserved for every *other* function in the ladder (`detect_languages`, `detect_documentation_surfaces`, etc., which must stay content-free).
**Example (from this checkout's own idiom, `detect.py:100-121`):**
```python
# Source: tools/adoption_scan/detect.py:100-121 (existing, UNCHANGED)
def detect_manifests(included: list[dict]) -> list[dict]:
    """One manifestRecord per recognized manifest file present in included."""
    records: list[dict] = []
    for entry in sorted(included, key=lambda item: item["path"]):
        name = PurePosixPath(entry["path"]).name
        kind = _MANIFEST_KIND_BY_NAME.get(name)
        if kind is None and name.endswith(".csproj"):
            kind = "*.csproj"
        if kind is None:
            continue
        records.append({"path": entry["path"], "kind": kind,
                         "classification": "observed", "evidence": _evidence([entry])})
    return records

# NEW — sibling function, pure, content-in (the generator supplies `text`, never detect.py itself).
def detect_dependencies(path: str, kind: str, text: str) -> list[dict]:
    """Parse declared dependency names + kind ("runtime"|"dev") from one manifest's raw text.

    Pure: given identical (path, kind, text) always returns identical output. Performs NO
    filesystem access itself — the caller (the generator) already reads `text` off disk to
    render the artifact, so this function never diverges from that read.
    """
    ...
```

### Pattern 2: Committed-derived artifact — `.gitignore` re-inclusion, not a directory allowlist

**What:** `.memory/derived/*` is ignored by contents-form glob (`.gitignore:26`), then the ONE committed file is re-included by exact name (`.gitignore:27`) — the directory-form `.memory/derived/` **cannot** be re-included this way (documented as pitfall P3 in the existing comment).
**When to use:** Adding any new committed-derived artifact under `.memory/derived/`.
**Example:**
```gitignore
# Source: .gitignore:20-27 (existing)
.memory/derived/*
!.memory/derived/contracts-index.md
!.memory/derived/package-facts.md      # ADD this line — same contents-form re-inclusion idiom
```

### Pattern 3: `stale-derived` job — join the existing regen + diff, add no job

**What:** `.github/workflows/ci.yml`'s `stale-derived` job (`ci.yml:271-299`) already regenerates `docs/reference` + `contracts-index.md` in one step and diffs both paths in the next. The new artifact is a **third path added to the same two steps** — never a new job.
**Example (source: `ci.yml:278-283`, showing the exact two lines that must widen):**
```yaml
- name: Regenerate the committed-derived set
  run: uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index && uv run python -m tools.memory_regen.package_facts
- name: Fail on any stale committed-derived artifact (untracked-safe)
  run: |
    git add -A -- docs/reference .memory/derived/contracts-index.md .memory/derived/package-facts.md
    if ! git diff --cached --exit-code -- docs/reference .memory/derived/contracts-index.md .memory/derived/package-facts.md; then
```
This also requires updating `tools/harness_lint/tests/test_ci_stale_derived.py`'s `_DERIVED_PATHS` tuple (`test_ci_stale_derived.py:32`) and its two structural assertions (`test_stale_derived_uses_untracked_safe_diff_primitive`, `test_stale_derived_regenerates_both_derived_generators`) to know about the third artifact/module — those tests currently hard-code exactly two paths and two module names and will need a third, or they will pass vacuously without proving the new artifact is actually wired in.

### Anti-Patterns to Avoid
- **Re-scanning the whole repo with `tools.adoption_scan.scan.build_inventory(repo_root)`:** that function hashes and content-inspects (secret patterns, binary detection, source-dump detection) **every** tracked file just to find ~24 manifests — needless work and a needless dependency on the adoption-scan secret-classification path for a report-only artifact. Prefer a lighter `git -C <repo> ls-files -z` enumeration (the same primitive `scan.py:150-159` already uses) filtered directly to the 5 known manifest filenames/suffixes, then hand only those entries to `detect.detect_manifests`.
- **Writing the literal string `"examples/"` or `"components/toy-converter"` anywhere inside `tools/`, `harness/`, or `libs/` source (including docstrings/comments):** `tools/harness_lint/tests/test_core_no_example_dep.py`'s GEN-04 guard (`test_core_no_example_dep.py:53,71,88-106`) scans the **tracked source of every file under `tools/harness/libs`** (not `.memory/`) for these path tokens and fails loud. The generator's *output* (`.memory/derived/package-facts.md`, which legitimately lists `examples/log-parser/project.toml` as a manifest path) is safe — `.memory/` is outside `_CORE_ROOTS = ("tools", "harness", "libs")` (`test_core_no_example_dep.py:44`) — but the generator's own *source code* must never hardcode an `examples/` literal for illustration; keep any example paths in comments generic (`<instance>/...`) or omit them.
- **Modifying `effective_relationships()` or `compile_graph()`'s existing signatures to also carry package data:** MONO-04 wants ownership attribution, not a second traversal engine; add a small pure lookup function instead of threading package facts through the relationship-graph adjacency machinery.
- **Hand-writing a second TOML/JSON reader:** `harness_config/loader.py:18` (`tomllib`) and `contract_hash`/`docs_sync` (stdlib `json`) already establish "one reader per format" as this repo's convention — reuse those idioms, don't add a third.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML parsing | A custom TOML tokenizer | stdlib `tomllib` (already the sole reader for `harness/project.toml`, root `pyproject.toml` via `uv`) | `tomllib` is bundled (py311+), zero new dep, already proven correct on this exact repo's TOML files. |
| JSON parsing | A custom JSON reader | stdlib `json` (already used by `tools/contract_hash`, `tools/docs_sync`) | Same reuse principle; `.claude/package.json` is trivially small (`{"type":"commonjs"}`). |
| `.csproj` XML parsing | A regex over XML | stdlib `xml.etree.ElementTree` | `.csproj` is well-formed XML; a `<ProjectReference Include="...">` XPath is one line and correctly handles attribute quoting/whitespace that a regex would mishandle on edge cases. |
| Confined/deterministic file enumeration | A fresh `os.walk` | The `git -C <target> ls-files -z --cached --others --exclude-standard` idiom already in `scan.py:150-159`, OR the simpler bare `git ls-files` this repo's own guard tests already use (`test_core_no_example_dep.py:90-96`) | Determinism + git-tracked-only scoping is already solved twice in this repo; a third re-implementation risks silently disagreeing with either. |
| Derived-artifact determinism proof | A hand-rolled hash-compare script | `hashlib.sha256` over `write()`'s output, delete + regenerate, exactly as `test_contracts_index.py:71-80` (`test_generate_delete_regenerate_is_byte_identical`) does | This is the proven pattern for this exact success-criterion shape (SC1: "deleting it and regenerating from a clean tree yields a byte-identical file"). |

**Key insight:** Every piece of this phase already has a proven twin somewhere in `tools/`. The work is composition (wire detect.py's new function into a new memory_regen generator, wire that generator's output into a new harness_config layering function and a new contract_graph lookup), not invention.

## Runtime State Inventory

Not applicable — this is a greenfield derived-artifact addition, not a rename/refactor/migration phase. No stored data, live service config, OS-registered state, secrets, or build artifacts are touched by adding a new derived generator and a new committed markdown file.

## Common Pitfalls

### Pitfall 1: Assuming `detect_manifests`'s "no filesystem access" invariant extends to the new dependency-parsing code
**What goes wrong:** Threading file content into `detect_manifests`'s own signature (or into the `included` entries it consumes) would force every OTHER detection function in the ladder (`detect_languages`, `detect_documentation_surfaces`, `detect_ci_surfaces`, etc.) to also carry content, breaking the documented invariant (`detect.py:6-8`) for functions that never needed it.
**Why it happens:** MONO-02's phrasing ("extending `detect_manifests`") reads as "add dependency parsing to that function" rather than "add dependency parsing to that module."
**How to avoid:** Add a new sibling function (Pattern 1 above) that takes `(path, kind, text)` directly; `detect_manifests` itself stays byte-for-byte unchanged.
**Warning signs:** A diff to `detect.py` that changes the `included: list[dict]` shape or `detect_manifests`'s call signature is a sign the seam was placed wrong.

### Pitfall 2: Believing `contracts_index.py`'s docstring that its output is gitignored
**What goes wrong:** A generator built to the docstring's letter (`contracts_index.py:10-14`: "Output... gitignored (D-03)") would use `hashlib`-only determinism proofs and never wire into `stale-derived`'s `git add -A`/diff, silently missing MONO-01's "committed" requirement.
**Why it happens:** The docstring is stale — it was true before the 09-02 phase flipped this specific file to committed-derived (`STATE.md` decision log, phase 09-02: "`contracts-index.md` flipped gitignored->tracked via .gitignore contents-form"), but the prose was never updated.
**How to avoid:** Trust the **executable** artifacts over the docstring: `.gitignore:26-27` (contents-form re-inclusion), `git log -1 -- .memory/derived/contracts-index.md` (returns a real commit — `[VERIFIED: this checkout]` `1e79bf6458b540eae263de0f693d6a03eeb05101`), and `ci.yml:271-299` (the `stale-derived` job's `git add -A` + `git diff --cached --exit-code` over that exact path). `package-facts.md` must follow the same committed path.
**Warning signs:** A plan step that proposes only a syrupy snapshot test (no `.gitignore` edit, no `ci.yml` path-list edit) for the new artifact.

### Pitfall 3: Two distinct GEN-04 token classes can silently trip on generated OR authored content
**What goes wrong:** `test_core_no_example_dep.py` scans `tools/`, `harness/`, `libs/` (not `.memory/`) for the literal substring `"examples/"` and several narrow prose tokens (`test_core_no_example_dep.py:53,57-68`). A `harness/commands/refresh-memory.md` or `harness/agents/curator.md` edit that adds a comment naming a specific example path, or a `tools/memory_regen/package_facts.py` docstring illustrating output with a hardcoded `examples/log-parser/...` string, would trip the guard.
**Why it happens:** The guard is a blunt substring scan over ALL tracked core-plane files, not just code — comments and docstrings count.
**How to avoid:** Keep any illustrative paths in new source under `tools/`/`harness/` generic (`<pkg>/pyproject.toml`, not a literal `examples/log-parser/...` path); the harness/project.toml `[instance] persona =`/`root =`/`test_paths =` lines are the ONE sanctioned exemption (`test_core_no_example_dep.py:81-85,109-113`) and it is key-scoped, not file-scoped.
**Warning signs:** `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` failing after adding the new generator or its command/curator wiring.

### Pitfall 4: `owning_package()` falls back to the root package far more often than intuition suggests
**What goes wrong:** A planner (or reviewer) may expect `examples/log-parser/contracts/log-specs/*.schema.json` to attribute to some `examples/log-parser`-scoped package. Under the ratified "nearest enclosing package directory, falling back to root" rule (CONTEXT.md decision), it does **not** — there is no recognized manifest (`pyproject.toml`/`package.json`/`*.csproj`/`go.mod`/`Cargo.toml`) directly at `examples/log-parser/` (verified: `git ls-files examples/log-parser | grep -E 'pyproject.toml|package.json|\.csproj$'` returns only nested paths under `golden_runner/`, `components/toy-converter/`, `libs/dotnet/*` — none at the instance root). So both `contracts/**` (core) and `examples/log-parser/contracts/**` (instance) attribute to the **same** root package (`logparser-harness` at `.`).
**Why it happens:** `examples/log-parser/project.toml` is a real, load-bearing config file, but it is not one of the 5 MONO-02 manifest kinds — it carries no package identity of its own in this scheme.
**How to avoid:** Document this behavior explicitly in the artifact/tests rather than "fixing" it silently; it is a faithful consequence of the ratified rule, not a bug — but the planner should decide (and the plan should state) whether this coarse attribution is acceptable for MONO-04's "given a contract path, report the package that owns it" criterion, since two very different areas of the tree collapse to one answer.
**Warning signs:** A test asserting `owning_package("examples/log-parser/contracts/...")` returns anything other than the root package id.

### Pitfall 5: Real-tree dependency edges are too sparse to prove MONO-02's criterion 2 without fixtures
**What goes wrong:** A test that only exercises the real repo tree would see exactly 2 edges (both `.csproj`) and 0 Python/JS edges — not enough to demonstrate "removing a dependency from a fixture manifest removes exactly that edge on regeneration" for every manifest kind MONO-02 names.
**Why it happens:** This repo's `pyproject.toml` files are virtual uv workspace members with either zero deps or pinned **external** PyPI packages (`rfc8785`, `jsonschema`, `tree-sitter*`, `networkx`) — none names another local package, and no `[tool.uv.sources]` path-based intra-workspace reference exists anywhere (`grep -rn "tool.uv.sources"` over all 20 `pyproject.toml` files returns nothing). `.claude/package.json` has no `dependencies`/`devDependencies` key at all.
**How to avoid:** Build dedicated fixture manifests per kind (mirrors the existing `tools/adoption_scan/tests/fixtures/` and `tmp_minirepo`/`tmp_contracts_tree` conftest idioms already in this repo) rather than relying on the live tree to prove edge-add/remove behavior.
**Warning signs:** A plan whose only test evidence for MONO-02 is "ran the generator against the real repo and it produced N edges" — that alone cannot prove the removal-detects-removal behavior since there is nothing to remove in the live pyproject/package.json edges.

## Code Examples

### Existing generator idiom to clone verbatim (rows → render → write → main)
```python
# Source: tools/memory_regen/contracts_index.py:51-127 (existing, the template to mirror)
def index_rows(...) -> list[tuple[...]]:
    ...  # assemble, sorted, deterministic

def render(rows: list[tuple[...]]) -> str:
    lines = [f"# {DERIVED_HEADER}", "", ..., "| ... |", "| --- | ... |"]
    for row in rows:
        lines.append(f"| ... |")
    return "\n".join(lines) + "\n"

def write(index_path=INDEX_PATH, ...) -> Path:
    out = Path(index_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(index_rows(...)), encoding="utf-8")
    return out

def main(argv=None) -> int:
    out = write()
    print(f"wrote {out.relative_to(_REPO_ROOT)} (...)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### `[[components]]` override-layering shape to mirror (`effective_relationships()`)
```python
# Source: tools/harness_config/loader.py:90-197 (existing pattern — "lower/derive, union with
# declared, dedup/validate deterministically, sorted output"). A new effective_packages() should
# follow the SAME shape: derived package_facts records are the base, [[components]] entries with
# a matching `id` win at the field level (never silently delete a derived field), and a
# [[components]] entry with NO matching derived package stays declared-only (no ValueError) —
# this is the ONE deliberate divergence from effective_relationships()'s raise-on-mismatch posture,
# because MONO-03 explicitly requires both harness/project.toml and examples/log-parser/project.toml
# to keep loading with ZERO edits even though neither's [[components]] ids ("source"/"sink"/
# "parser"/"converter"/"scheduler"/"collector") match any of the 23 real manifest-derived package
# ids in this checkout today.
```

### `owning_package()` lookup shape to build (new, in `tools/contract_graph`)
```python
# Mirrors the _tracked_schemas() glob-existence idiom already in compile.py:39-46 — a pure lookup,
# not a traversal. No new traversal engine; direct()/reverse()/transitive() in query.py are
# untouched.
def owning_package(packages: list[dict], contract_path: str) -> str:
    """Return the package id whose directory is the nearest ancestor of contract_path.

    packages: [{"id": ..., "path": <manifest-dir-relative-posix>}, ...] from package_facts.
    Falls back to the root package ("." ) when no manifest directory encloses contract_path —
    see Pitfall 4 for why this collapses core AND example contracts/ trees onto one answer today.
    """
```

## State of the Art

Not applicable in the external-ecosystem sense (no library version drift to track — everything is stdlib). The one "state of the art" question is internal: this repo's own convention for committed-vs-gitignored derived artifacts moved once already (phase 09-02, gitignored → committed for `contracts-index.md`); `package-facts.md` should launch directly in the committed state MONO-01 requires, skipping that migration.

**Deprecated/outdated:** `contracts_index.py`'s module docstring line "Output: `.memory/derived/contracts-index.md` (gitignored, D-03)" (`contracts_index.py:10`) is itself stale prose left over from before phase 09-02 — do not copy this line into the new generator's docstring; write "committed-derived" instead.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `xml.etree.ElementTree` (stdlib) is the right tool for `.csproj` `ProjectReference` parsing | Standard Stack / Don't Hand-Roll | Low — `.csproj` is simple, well-formed XML with no namespaces on the relevant elements; if wrong, swapping to a regex or a different stdlib approach is a contained, low-risk change with no dependency implications either way. |
| A2 | `go.mod`'s `require` block needs a hand-written line parser (no stdlib module reads Go module files) | Standard Stack | Low-medium — no real `go.mod` exists in this checkout to validate against; the parser must be built purely against a synthetic fixture and unit-tested there, so a subtle Go-syntax edge case (e.g. `require (...)` vs single-line `require`) could be missed until a real `go.mod` is ever added to this repo. |
| A3 | `package.json`'s single manifest kind maps to language `"javascript"` (not `"typescript"`, even though `.claude/package.json`'s only content is `{"type":"commonjs"}` with no language signal) | Architecture Patterns (implicit in package facts language field) | Low — affects only the reported `language` column for the one `package.json` package in this checkout; does not affect dependency edges (there are none to parse in `.claude/package.json`) or MONO-02/04 correctness. Planner should decide and record this explicitly since MONO-01 requires a `language` field per package. |

## Open Questions

1. **Should `owning_package()`'s root-package fallback for `examples/log-parser/contracts/**` be flagged as a known limitation or treated as acceptable coarse attribution?**
   - What we know: the ratified CONTEXT.md decision ("nearest enclosing package directory... falling back to the root package") is unambiguous and this checkout's manifest layout makes the fallback fire for the entire `examples/log-parser/contracts/` tree (see Pitfall 4).
   - What's unclear: whether MONO-04's success criterion ("given a contract path, `contract_graph` reports the package that owns it") is satisfied by "always the root package" for every example-instance contract, or whether the milestone intends a future phase (48/49, or a later one) to give `examples/log-parser` an identity via its `project.toml`.
   - Recommendation: plan should implement exactly the ratified fallback rule (no invention of a new manifest kind for `project.toml`) and add an explicit test documenting the fallback for at least one real `examples/log-parser/contracts/**` schema path, so the behavior is asserted rather than accidentally emergent.

2. **Does the generator need a full `scan.build_inventory()` call (with its size-cap/binary/secret classification machinery) or a lighter direct `git ls-files` + manifest-name filter?**
   - What we know: `scan.py`'s `build_inventory()` is the existing pattern for producing `included` entries `detect.detect_manifests` expects, but it hashes and content-inspects every tracked file in the target — expensive and semantically mismatched for a report-only package-facts generator that only cares about ~24 manifests.
   - What's unclear: whether reuse-at-function-level purism (this repo's D-07 convention, cited in `scan.py`'s own docstring) favors calling `scan.build_inventory(_REPO_ROOT)` wholesale anyway for consistency, versus a leaner bespoke enumeration.
   - Recommendation: prefer the lighter enumeration (`git -C <repo> ls-files -z`, filtered to the 5 manifest name/suffix patterns before any hashing) — `detect.detect_manifests` only needs `path` to identify kind, and `evidence`/`sha256` are not part of MONO-01's required fields (manifest path, language, package id). This should be a locked decision in the plan, not left implicit.

## Environment Availability

Not applicable — this phase requires no external tools, services, runtimes beyond what is already installed (Python 3.11+/`uv`, already verified working throughout this repo's existing test suite). No new CLI, database, or network dependency is introduced.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (pinned `>=8.4,<9`, root `pyproject.toml:16`) + syrupy 5.2.0 (root `pyproject.toml:17`) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["libs/python", "tools"]`) |
| Quick run command | `uv run pytest tools/adoption_scan tools/memory_regen tools/harness_config tools/contract_graph tools/harness_lint -q` |
| Full suite command | `uv run pytest` (root `testpaths`, per `AGENTS.md` golden-path table) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MONO-01 | Every package listed with manifest path/language/id; delete+regenerate byte-identical | unit + determinism | `uv run pytest tools/memory_regen/tests/test_package_facts.py -x` | ❌ Wave 0 |
| MONO-02 | Dependency edges parsed per manifest kind; unresolvable dropped; fixture add/remove-a-dep proof | unit (fixture-based) | `uv run pytest tools/adoption_scan/tests/test_detect.py tools/memory_regen/tests/test_package_facts.py -x` | ❌ Wave 0 (new cases added to existing `test_detect.py`) |
| MONO-03 | `[[components]]` overrides derived record; both live configs load with zero edits | unit + structural | `uv run pytest tools/harness_config/tests -x tools/harness_lint/tests/test_package_facts_override.py -x` | ❌ Wave 0 (new file) |
| MONO-04 | `contract_graph` reports owning package for a contract path | unit | `uv run pytest tools/contract_graph/tests/test_ownership.py -x` | ❌ Wave 0 (new file) |
| SC5 (no gate/job growth) | `ci.yml` job set + `gate.needs` unchanged; `stale-derived` regen/diff widened, not duplicated | structural | `uv run pytest tools/harness_lint/tests/test_ci_stale_derived.py tools/harness_lint/tests/test_ci_lint_gate.py -x` | ✅ exists, needs editing (`_DERIVED_PATHS` tuple + two assertions in `test_ci_stale_derived.py:32,54-71,74-83`) |

### Sampling Rate
- **Per task commit:** the relevant package's quick-run command above.
- **Per wave merge:** `uv run pytest tools/adoption_scan tools/memory_regen tools/harness_config tools/contract_graph tools/harness_lint`.
- **Phase gate:** `uv run pytest` (full suite) green, plus `uv run python -m tools.harness_emit` re-emit-diff clean (curator.md/refresh-memory.md wiring is emitted to both runtimes) before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/memory_regen/tests/test_package_facts.py` — determinism (delete+regenerate byte-identical), correctness (fixture per manifest kind — add/remove-a-dep), snapshot (mirrors `test_contracts_index.py`'s 3-guarantee shape exactly), covers MONO-01/MONO-02.
- [ ] `tools/memory_regen/tests/__snapshots__/test_package_facts.ambr` — committed syrupy snapshot, same idiom as `contracts_index`'s.
- [ ] Fixture manifests per kind (pyproject.toml with a local-name dependency via `[tool.uv.sources]`-style declaration or a plain external dep to prove drop-unresolvable, package.json with deps+devDependencies, a synthetic `.csproj` with `ProjectReference`, a synthetic `go.mod`, a synthetic `Cargo.toml` with a path dependency) — needed because the live tree only exercises 2 of 5 manifest kinds' edges (Pitfall 5).
- [ ] `tools/harness_lint/tests/test_package_facts_override.py` — MONO-03 consistency gate, mirrors `test_pipeline_config.py`'s idiom: load both `harness/project.toml` and `examples/log-parser/project.toml`, assert `effective_packages()` does not raise and every declared `[[components]]` entry is either an override or stays declared-only.
- [ ] `tools/contract_graph/tests/test_ownership.py` — MONO-04, mirrors `test_compile.py`'s domain-neutral fixture style (synthetic package/contract paths, not live repo paths, to keep the test GEN-04-clean and independent of live-tree drift).
- [ ] Framework install: none — pytest/syrupy already resolved in `uv.lock`.

## Security Domain

Not applicable in the ASVS sense — this phase adds a read-only, report-only derived-artifact generator with no authentication, session, access-control, or cryptography surface. The one relevant "threat pattern" this repo already defends against and this phase must not regress is **prompt/data injection into CI shell steps**: `ci.yml`'s existing `stale-derived` job explicitly never interpolates `${{ github.event.* }}` (verified: `test_ci_stale_derived.py:103-109`, `test_stale_derived_never_interpolates_event_input`) — any edit to that job to add the new artifact's regen/diff commands must preserve that invariant (it trivially does, since the new commands are static strings like the existing ones).

## Sources

### Primary (HIGH confidence — read directly in this checkout)
- `tools/adoption_scan/detect.py` (full file, 251 lines) — manifest kind table, `detect_manifests`, evidence ladder, docstring invariant.
- `tools/adoption_scan/scan.py` (full file, 357 lines) — `build_inventory`, `enumerate_target`, `classify_exclusions`, reuse-at-function-level docstring.
- `tools/adoption_scan/tests/test_detect.py` (first 80 lines) — existing test idiom (`tmp_minirepo` fixture, `_record_by` helper).
- `tools/memory_regen/contracts_index.py` (full file, 128 lines) — the reference generator idiom.
- `tools/memory_regen/tests/test_contracts_index.py` (full file, 116 lines) — the 3-guarantee test shape (determinism/correctness/snapshot).
- `tools/contract_graph/compile.py` (full file, 175 lines) — `compile_graph`, `_tracked_schemas`, `_contract_ownership_diagnostic`.
- `tools/contract_graph/query.py` (full file, 82 lines) — `direct`/`reverse`/`transitive`, D-03 return shape.
- `tools/contract_graph/tests/test_compile.py` (first 60 lines) — domain-neutral fixture style.
- `tools/harness_config/loader.py` (full file, 205 lines) — `load_project`, `components`, `pipeline`, `effective_relationships` (the layering shape to mirror), `language_bash_scopes`.
- `harness/project.toml` (full file, 98 lines) — the core `[[components]]` config (`source`/`sink`, both python).
- `examples/log-parser/project.toml` (full file, 73 lines) — the instance `[[components]]` config (`parser`/`converter` dotnet, `scheduler`/`collector` python).
- `.github/workflows/ci.yml` (full file, 343 lines) — `stale-derived` job (`:259-299`), `gate.needs` (`:329`), full job list.
- `tools/harness_lint/tests/test_ci_stale_derived.py` (full file, 184 lines) — the structural/negative-control test shape that must be widened, not duplicated.
- `tools/harness_lint/tests/test_derived_freshness.py` (full file, 121 lines) — `_ALLOWED_TOOL_MODULES` allowlist (confirms `memory_regen` family is pre-approved), no-on-write-regen invariant.
- `tools/harness_lint/tests/test_pipeline_config.py` (full file, 51 lines) — the config-consistency-gate idiom to mirror for MONO-03.
- `tools/harness_lint/tests/test_core_no_example_dep.py` (full file, 220 lines) — the GEN-04 guard's exact scanned roots, token lists, and the one sanctioned exemption.
- `harness/commands/refresh-memory.md`, `harness/agents/curator.md` (grep on `memory_regen`/`docs_sync`/`contracts_index`) — exact insertion pattern for wiring a new generator into the curator/refresh-memory surfaces.
- `.gitignore` (full file, ~28 lines) — the exact re-inclusion idiom + its own documented pitfall P3.
- `AGENTS.md` (full file) — non-negotiables, golden-path commands, monorepo map.
- `.planning/phases/47-package-facts/47-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (Phase 47 section + v2.6 milestone section), `.planning/STATE.md` (decision log through phase 42).
- Shell verification in this session: `git ls-files` filtered per manifest kind (24 total: 20 pyproject.toml, 3 csproj, 1 package.json, 0 go.mod, 0 Cargo.toml); every `pyproject.toml`'s full content read; `.claude/package.json` content read; every `.csproj` content read; `grep -rn "tool.uv.sources"` (zero hits); `git log -1 -- .memory/derived/contracts-index.md` (confirms committed); `.planning/config.json` (`workflow.nyquist_validation: true`, confirming the Validation Architecture section is required).

### Secondary / Tertiary
None — per the milestone's explicit "no research round" decision, no web search was performed; every claim traces to a file read or shell command in this session.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every tool is stdlib, already proven elsewhere in this exact repo.
- Architecture: HIGH — every pattern cited has a live, working twin read in full in this session.
- Pitfalls: HIGH for Pitfalls 1-3 and 5 (directly evidenced by reading the guard tests and the manifest contents); MEDIUM for Pitfall 4 (the fallback behavior is a correct deduction from the ratified rule + the verified absence of a manifest at `examples/log-parser/`, but its acceptability is a planning judgment call, not a fact).

**Research date:** 2026-07-30
**Valid until:** Stable as long as this checkout's manifest set (24 tracked, 20/3/1/0/0 by kind) and `ci.yml`'s job list are unchanged — re-verify manifest counts before planning if significant time has passed or new packages have been added.
