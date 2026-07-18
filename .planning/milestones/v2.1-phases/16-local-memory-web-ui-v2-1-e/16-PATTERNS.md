# Phase 16: Local Memory Web UI (v2.1 E) - Pattern Map

**Mapped:** 2026-07-18
**Files analyzed:** 12 new/modified files
**Analogs found:** 11 / 12 (1 file — the progress-stamp writer — has NO existing callable analog; RESEARCH A1 confirmed)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tools/memory_regen/pointer_index.py` | derived-generator | batch / transform | `tools/memory_regen/repo_map.py` + `contracts_index.py` | exact (clone the shape) |
| `tools/memory_regen/tests/test_pointer_index_determinism.py` | test | batch | `tools/memory_regen/tests/test_repo_map_determinism.py` | exact |
| `tools/memory_regen/tests/__snapshots__/test_pointer_index.ambr` | test-fixture | — | `test_repo_map.ambr` (syrupy snapshot over tmp fixture) | exact |
| `tools/memory_ui/pyproject.toml` | config | — | `tools/agree/pyproject.toml` | exact (verbatim clone, rename) |
| `tools/memory_ui/__init__.py` | package-init | — | `tools/agree/__init__.py` (namespace member) | exact |
| `tools/memory_ui/__main__.py` | entrypoint | request-response | `write.py::main` argparse CLI + RESEARCH `serve()` bootstrap | role-match |
| `tools/memory_ui/server.py` | server-shell | request-response | (stdlib `ThreadingHTTPServer`; no in-repo HTTP analog) + `inject.py` DI idiom | partial (stdlib pattern) |
| `tools/memory_ui/routes.py` | route-logic (pure fns) | request-response / CRUD | `tools/memory_regen/inject.py::assemble` (injected-dir DI) + `tools/agree/write.py` writers | role-match |
| `tools/memory_ui/page.py` | view (inlined HTML/JS) | — | (no in-repo analog — single inlined string) | none (use RESEARCH `<specifics>`) |
| `tools/memory_ui/_stamp.py` (progress `updated:` writer) | utility (writer) | file-I/O | frontmatter round-trip via `parse_frontmatter` + `write.py::_dump_frontmatter` | partial (compose from parts) |
| `tools/memory_ui/tests/conftest.py` | test-config | — | `tools/memory_regen/tests/conftest.py` + `tools/agree/tests/conftest.py` | exact |
| `tools/memory_ui/tests/test_routes.py` + `test_referential_integrity.py` | test | request-response / CRUD | `harness_lint/tests/conftest.py::tmp_agreements_tree` corpus + determinism-test idiom | role-match |

Modified (wiring, only if SC2 requires SessionStart wiring — RESEARCH A4/Q3):
`harness/plugins/session-inject.ts` (regen loop line 36) — add `"tools.memory_regen.pointer_index"` to the module list; triggers a Phase-7 emit round-trip to `.opencode/` + `.claude/`.

## Pattern Assignments

### `tools/memory_regen/pointer_index.py` (derived-generator, batch/transform)

**Analog:** `tools/memory_regen/repo_map.py` (module-level path constants + build→render→write→main quartet) and `tools/memory_regen/contracts_index.py` (tabular `.md` render + row assembly).

**Module-level paths + DERIVED header** (`repo_map.py:33-43`, `contracts_index.py:27-33`) — clone verbatim, swapping names:
```python
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
JSON_PATH = DERIVED_DIR / "pointer-index.json"
MD_PATH = DERIVED_DIR / "pointer-index.md"
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/pointer_index.py)"
```

**Symlink-confined file walk** (`repo_map.py:53-71`) — reuse this idiom for the scan roots (D-16-02 discretion: prefer sharing `_iter_source_files`, fixture-parity fallback allowed):
```python
def _iter_source_files(source_roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in source_roots:
        root = Path(root)
        if not root.exists():
            continue
        root_resolved = root.resolve()
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            if lang_for_path(p) is None:          # suffix allow-list gate — mirror for text files
                continue
            resolved = p.resolve()
            if root_resolved != resolved and root_resolved not in resolved.parents:
                continue                          # skip symlinks escaping the subtree
            files.append(p)
    return files
```
Scan roots per D-16-02: `docs/`, `harness/` (recursive), `tools/memory_regen/inject.py`, `.memory/README.md`, `AGENTS.md` (single-file roots). **MUST exclude `.memory/derived/`** from any walk (self-reference churn). Restrict to text suffixes (`.md`, `.ts`, `.py`, `.json`, `.toml`; suffixless like `AGENTS.md` treated as `.md`).

**Deterministic build → sorted dict** (mirror `repo_map.build_graph:88-128` sort discipline and `contracts_index.index_rows:70-80` `for rel in sorted(...)`). Enumerate memory items = state files + `iter_agreement_files(agreements_dir)`; for each scan-root file read line-by-line, record `{file, line, kind}` where `kind ∈ {"path","slug"}`. Word-boundaried slug match (RESEARCH Pattern 2 / A3):
```python
re.search(r"(?<![\w-])" + re.escape(slug) + r"(?![\w-])", line)   # slug 'plan' ≠ 'planner'
```
Sort item keys and each referrer list `(file, line, kind)` before emit.

**write() — dual JSON+MD, mkdir parents, no timestamp** (compose `repo_map.write:188-199` + RESEARCH §Pattern 1 signature). Inject `base_dir`/`scan_roots` so `tmp_path` never leaks into output:
```python
def write(json_path=JSON_PATH, md_path=MD_PATH, *, base_dir=None, scan_roots=None) -> tuple[Path, Path]:
    index = build_index(base_dir=base_dir, scan_roots=scan_roots)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_md(index), encoding="utf-8")
    return json_path, md_path
```

**MD render** — clone `contracts_index.render:83-102` (header line `f"# {DERIVED_HEADER}"`, then a stable sorted table). **NO timestamp, no raw float, no wall-clock** anywhere in the body.

**main()** — clone `repo_map.main:202-211` / `contracts_index.main:117-123` (`argv` reserved, `write()`, print `wrote {out.relative_to(_REPO_ROOT)} (...)`, return 0; `python -m tools.memory_regen.pointer_index`).

---

### `tools/memory_regen/tests/test_pointer_index_determinism.py` (test, batch)

**Analog:** `tools/memory_regen/tests/test_repo_map_determinism.py` (read in full).

**write→hash→delete→regenerate byte-identical** (lines 35-44) — clone exactly (NOT `git diff`; target is gitignored):
```python
def test_write_delete_regenerate_is_byte_identical(tmp_path, fixture_tree):
    out = tmp_path / "derived" / "pointer-index.json"
    pointer_index.write(json_path=out, md_path=tmp_path/"derived"/"pointer-index.md",
                        base_dir=fixture_tree, scan_roots=[fixture_tree])
    d1 = hashlib.sha256(out.read_bytes()).hexdigest()
    out.unlink()
    pointer_index.write(json_path=out, md_path=tmp_path/"derived"/"pointer-index.md",
                        base_dir=fixture_tree, scan_roots=[fixture_tree])
    assert d1 == hashlib.sha256(out.read_bytes()).hexdigest()
```

**DERIVED marker + no timestamp + no raw float** (lines 63-71) — clone the regex assertions:
```python
assert text.splitlines()[0].startswith("# DERIVED — do not hand-edit")
assert "pointer_index.py" in text.splitlines()[0]
assert not re.search(r"\d{4}-\d{2}-\d{2}", text)
assert not re.search(r"0\.\d{3,}", text)
```

**Committed syrupy snapshot over tmp fixture** (lines 82-84) — `assert _render_fixture(tree) == snapshot`; key everything to `base_dir` so `tmp_path` never leaks (conftest comment lines 12-13). Add a `test_no_self_reference_and_no_false_positive` (SC2): assert no `.memory/derived/` referrer and slug `plan`≠`planner`.

**Tmp docs/harness fixture** — new fixture (RESEARCH Wave-0 gap): a throwaway tree with a known `.memory/...` path string and an agreement-slug reference, for `file:line` assertions. Model on `conftest.py::tmp_source_tree` (lines 46-69) construction style.

---

### `tools/memory_ui/pyproject.toml` (config)

**Analog:** `tools/agree/pyproject.toml` — clone verbatim, rename only:
```toml
[project]
name = "logparser-memory-ui"
version = "0.0.0"
description = "Local (127.0.0.1) web tool to view/edit/retire .memory items, pointer-aware."
requires-python = ">=3.11"
dependencies = []

[tool.uv]
package = false
```
Auto-enrolled by root `members = ["libs/python", "tools/*"]`; `uv sync` once → ~4 deterministic zero-resolution lock lines (14-CONTEXT D-19 precedent).

---

### `tools/memory_ui/routes.py` (route-logic, request-response / CRUD)

**Analog:** `tools/memory_regen/inject.py::assemble` (injected-dir DI, `inject.py:128-133`) + `tools/agree/write.py` (the writers routes delegate to).

**Injected-dir signature** (mirror `assemble(..., derived_dir=, state_dir=, agreements_dir=)`) so tests never touch real planes and never open a socket. Pure functions returning `(status:int, headers:dict, body:bytes)`:
```python
def retire_agreement(slug, *, agreements_dir, derived_dir, confirm=False) -> tuple[int, dict, bytes]:
    orphans = pointer_lookup(slug, derived_dir=derived_dir)   # regenerate inline then read (Pitfall 4)
    if orphans and not confirm:
        return 409, {"Content-Type": "application/json"}, json.dumps({"orphans": orphans}).encode()
    path = agree_write.retire(slug, agreements_dir=agreements_dir)   # SANCTIONED writer, never bypass
    return 200, {"Content-Type": "application/json"}, json.dumps({"retired": path.name}).encode()
```

**Add path — anti-invent `--because` guard** (`write.py:47-79`). The UI exposes a REQUIRED field and passes it verbatim; surface `AgreementRefused` to the page, never fabricate:
```python
from tools.agree.write import add, retire, AgreementRefused
try:
    add(slug, title, rule, because=user_supplied_because, added=date.today().isoformat(),
        related=related, agreements_dir=agreements_dir)
except AgreementRefused as exc:
    ...  # return the REFUSED: message; do NOT retry with a fabricated because
```

**List/parse agreements — reuse shared parsers, never re-roll** (`harness_lint/agreements.py:18-43`):
```python
from tools.harness_lint.agreements import iter_agreement_files, load_agreement  # fail-closed, confined, sorted
from tools.harness_lint import parse_frontmatter                                 # CRLF-safe split
```

**Slug/path confinement (V5)** — reuse `write.py::_target_for` semantics (`write.py:33-44`): validate `^[a-z0-9]+(?:-[a-z0-9]+)*$`, no `_`-prefix, `resolve().relative_to(base)`; reject traversal on any item/slug param.

---

### `tools/memory_ui/server.py` (server-shell, request-response)

**Analog:** stdlib `ThreadingHTTPServer` + `BaseHTTPRequestHandler` (no in-repo HTTP precedent; RESEARCH §Localhost bootstrap). Handler is a THIN dispatch shell delegating to `routes.py` pure functions.

**Localhost-only bind (D-16-01 — the security boundary)** — hardcode `127.0.0.1`, never `0.0.0.0`/`""`, never accept a `--host` flag:
```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
def serve(port: int = 8765) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), MemoryUIHandler)
    httpd.serve_forever()
```
For any live-socket smoke test bind port `0` and read `server.server_address[1]` (Pitfall 2).

---

### `tools/memory_ui/_stamp.py` (progress `updated:` writer, file-I/O) — NO DIRECT ANALOG

**Gap (RESEARCH A1 / Open Q1):** `/checkpoint` is a MARKDOWN command (`harness/commands/checkpoint.md:18-20`), not a Python callable. There is no existing state-stamp writer to clone. **Compose** from existing parts:
- Read/split via `tools.harness_lint.parse_frontmatter` (`frontmatter.py:26-55`).
- Write a QUOTED-date scalar `updated: "YYYY-MM-DD"` (checkpoint.md is explicit: quoted so it round-trips as a string, not a YAML date object) preserving the rest of the frontmatter + rewriting the body.
- For the quoted-string dump, mirror `write.py::_dump_frontmatter` (`write.py:21-30`, `YAML(typ="safe")`, `default_style='"'`).
- The state frontmatter shape is `activeContext.md:1-3` → `updated: "2026-07-16"` (single key today).
- This is a WRITE-path date (allowed, like `/checkpoint`); it must NOT introduce a clock into `inject.py::assemble` (the read path stays deterministic — `inject.py:134-137`).

---

### `tools/memory_ui/tests/conftest.py` (test-config)

**Analog:** `tools/memory_regen/tests/conftest.py:27-38` (sys.path `parents[3]` + re-export the shared agreements corpus):
```python
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIBS_PYTHON = _REPO_ROOT / "libs" / "python"
for _p in (str(_REPO_ROOT), str(_LIBS_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.harness_lint.tests.conftest import (  # noqa: E402, F401
    tmp_agreements_tree,   # synthetic active+retired+_TEMPLATE+README corpus — never real agreements
)
```
`tools/agree/tests/conftest.py` is the minimal `parents[3]` variant if no agreements corpus is needed for a given test module.

---

### `tools/memory_ui/tests/test_routes.py` + `test_referential_integrity.py` (test)

**Analog:** `harness_lint/tests/conftest.py::tmp_agreements_tree` (lines 34-88) — the injected `tmp_path` corpus so tests NEVER write real agreements and NEVER open a socket. Thread `agreements_dir=`/`derived_dir=`/`state_dir=` into every route call (Pitfall 2). Assert `retire` flips `status: retired` in place (never deletes — `write.py:82-99`), that `add` with blank `because` raises `AgreementRefused`, that orphan-with-referrers returns 409 and does NOT write, and that a confirmed retire proceeds with referrers untouched.

---

## Shared Patterns

### DERIVED-plane generator contract
**Source:** `tools/memory_regen/repo_map.py:33-43,188-199` + `contracts_index.py:83-114`
**Apply to:** `pointer_index.py`
- Module-level `_REPO_ROOT = Path(__file__).resolve().parents[2]`, `DERIVED_DIR`, output paths, `DERIVED_HEADER` string.
- `build → render → write → main` quartet; `mkdir(parents=True, exist_ok=True)` before write.
- Deterministic sort of everything before emit; `json.dumps(..., indent=2, sort_keys=True)`.
- **No timestamp, no wall-clock, no raw float** in the body.
- Verified by regenerate-and-hash + syrupy snapshot, NEVER `git diff` (`.memory/derived/*` gitignored — `.gitignore:19-24`; only `contracts-index.md` is negated/committed, pointer-index is NOT).

### Dependency-injection for testability (no live socket, no real writes)
**Source:** `tools/memory_regen/inject.py:128-133` (`assemble(..., derived_dir=, state_dir=, agreements_dir=)`)
**Apply to:** `routes.py`, `pointer_index.build/write` (`base_dir=`, `scan_roots=`), all UI tests
Every function that touches a plane takes the dir as a keyword arg defaulting to the real constant; tests pass `tmp_path`.

### Sanctioned writers — reuse, never reinvent (D-16-04)
**Source:** `tools/agree/write.py:47-99` (`add`/`retire`, `AgreementRefused`)
**Apply to:** all UI agreement write actions
Provenance stamp + YAML-safe `--because` + flip-in-place retire + anti-invent refusal are preserved only by calling these. `tools/memory_regen` and the UI must NEVER author `.memory/agreements/*` directly (tier contract, `.memory/agreements/README.md:4-5`).

### Shared parsers — one reader, never re-slice
**Source:** `tools/harness_lint/agreements.py:18-43`, `tools/harness_lint/frontmatter.py:26-55`
**Apply to:** listing/parsing agreements and state files in `routes.py`, `pointer_index.py`, `_stamp.py`
`iter_agreement_files` (sorted, confined, `_`/README-excluded), `load_agreement` (fail-closed), `parse_frontmatter` (CRLF-safe, ruamel safe loader).

### Virtual workspace member layout
**Source:** `tools/agree/pyproject.toml`, `tools/agree/tests/conftest.py`, `tools/memory_regen/tests/conftest.py`
**Apply to:** `tools/memory_ui/` (new member) and its tests
Zero-dep `pyproject.toml` (`package = false`); tests wire `sys.path` from `parents[3]` (`tools` is a namespace package, no `tools/__init__.py`).

### Localhost bind = the security boundary (D-16-01)
**Source:** RESEARCH §Localhost bootstrap; no auth code exists by design
**Apply to:** `server.py`, `__main__.py`
Hardcode `("127.0.0.1", port)`; never `0.0.0.0`/`""`; never accept `--host`; assert the bind in tests.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tools/memory_ui/page.py` | view (inlined HTML/JS) | — | No in-repo HTML/frontend precedent. Author per RESEARCH `<specifics>`: one self-contained page, no framework, no CDN, no external fetch ("local only" literally true). |
| `tools/memory_ui/_stamp.py` | utility (writer) | file-I/O | No Python callable stamps `updated:` today — `/checkpoint` is a markdown command (RESEARCH A1). COMPOSE from `parse_frontmatter` + a quoted-date scalar dump (see Pattern Assignment above); do not clone one file. |
| `tools/memory_ui/server.py` | server-shell | request-response | Partial only — stdlib `ThreadingHTTPServer`/`BaseHTTPRequestHandler`, no in-repo HTTP server to clone; the DI + localhost patterns above still apply to the dispatch logic. |

## Metadata

**Analog search scope:** `tools/memory_regen/`, `tools/agree/`, `tools/harness_lint/`, `harness/commands/`, `harness/plugins/`, `.memory/state/`, `.gitignore`
**Files scanned:** 13 (read fully or targeted)
**Pattern extraction date:** 2026-07-18
