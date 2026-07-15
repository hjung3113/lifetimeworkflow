# Phase 11: Multi-Repo Workspace (v2.0 γ) - Pattern Map

**Mapped:** 2026-07-13
**Files analyzed:** 12 (8 new, 4 modified/extended)
**Analogs found:** 12 / 12 (all exact or role-match; every analog verified in live code this session)

> This phase is **disciplined reuse**, not invention. Every new capability is a member-scoped
> invocation of an already-parametrized function, or a byte-for-byte mirror of an existing
> config/loader/gate. All analogs below were read live and line numbers verified.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `workspace.toml` (root, NEW) | config (DATA slot) | transform (SSOT read) | `harness/project.toml` | exact (idiom clone, one level up) |
| `tools/workspace_config/loader.py` (NEW) | utility (loader) | file-I/O / transform | `tools/harness_config/loader.py` | exact |
| `tools/workspace_config/__init__.py` (NEW) | utility (package API) | transform | `tools/harness_config/__init__.py` | exact |
| `tools/workspace_config/pyproject.toml` (NEW) | config (uv member) | — | `tools/harness_config/pyproject.toml` | exact |
| `tools/workspace_config/tests/test_loader.py` (NEW) | test (unit) | request-response | `tools/harness_lint/tests/test_language_config.py` (loader-read half) | role-match |
| `tools/harness_lint/tests/test_workspace_config.py` (NEW) | test (consistency gate) | request-response | `test_language_config.py` + `test_pipeline_config.py` | exact |
| `tools/harness_lint/tests/test_core_no_workspace_member_dep.py` (NEW) | test (GEN-04 guard) | batch (git ls-files scan) | `test_core_no_example_dep.py` | exact |
| `tools/contract_drift/drift.py` (EXTEND + new test) | service (gate) | batch / transform | `tools/contract_drift/drift.py::run_gate` (self, reuse verbatim) | exact (reuse-as-is) |
| `tools/golden_runner/runner.py` (EXTEND `_confine`) | service (gate) | file-I/O | `tools/golden_runner/runner.py::_confine` (self) | exact (widen allowlist) |
| `tests/fixtures/workspace/member-{a,b}/…` (NEW) | fixture (data) | file-I/O | `examples/log-parser/contracts/.hashes/manifest.json` + `golden/` tree | role-match |
| `.github/workflows/ci.yml` (EXTEND — new `workspace` job) | config (CI) | event-driven | `drift` / `emit-drift` / `stale-derived` jobs | exact |
| `harness/commands/workspace-analyze.md` (OPTIONAL — only if reuse insufficient) | command | event-driven | `harness/commands/fan-out-synthesize.md` | role-match (deferred; prefer prose wiring) |

---

## Pattern Assignments

### `workspace.toml` (config, DATA slot — MREPO-01)

**Analog:** `harness/project.toml` (verified: `tools/harness_config/loader.py` header L1-14 names it the language SSOT).

**Idiom to clone** — a header comment naming its consumers (loader + gate), then pure DATA, no logic. Mirror `harness/project.toml`'s posture exactly, one level up. The `[instance] root = ""` generic-default convention (see the GEN-04 guard's exemption note, `test_core_no_example_dep.py` L74-85) becomes `[workspace] id = ""`.

Recommended shape (field names are Claude's discretion per CONTEXT — the *idiom* is load-bearing, not the names):
```toml
# WORKSPACE manifest — the multi-repo SINGLE SOURCE OF TRUTH (MREPO-01). Pure DATA, no logic.
# Consumers:
#   * tools/workspace_config/loader.py — stdlib tomllib reader; members()/edges() passthrough.
#   * tools/harness_lint/tests/test_workspace_config.py — the consistency gate.
[workspace]
id = ""                       # "" = generic default (mirror [instance] root = "")
[[members]]
id = "member-a"
root = "tests/fixtures/workspace/member-a"   # repo-relative; keep INSIDE REPO_ROOT (Pitfall 1)
[[members]]
id = "member-b"
root = "tests/fixtures/workspace/member-b"
[pipeline]
edges = [ { from = "member-a:emit", to = "member-b:ingest", contract = "greeting" } ]
```

**Note:** endpoints recommended as `repo:stage` so MREPO-03 (drift/golden member resolution via the `repo` half) and MREPO-04 (topology via the `stage` half) share ONE table.

---

### `tools/workspace_config/loader.py` (utility, loader — MREPO-01)

**Analog:** `tools/harness_config/loader.py` (read in full; the template shape).

**Repo-root anchor pattern** (loader.py L21-24) — clone the `parents[2]` climb and the repo-root-anchored default so the loader is cwd-independent:
```python
# loader.py -> harness_config -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PROJECT = _REPO_ROOT / "harness" / "project.toml"
```
→ For workspace: `_DEFAULT_WORKSPACE = _REPO_ROOT / "workspace.toml"`.

**Binary-mode `tomllib.load` reader** (loader.py L32-39) — the ONE sanctioned reader; `tomllib` requires binary mode:
```python
def load_project(path: str | Path = _DEFAULT_PROJECT) -> dict:
    with Path(path).open("rb") as fh:
        return tomllib.load(fh)
```
→ Clone as `load_workspace(path=_DEFAULT_WORKSPACE)`.

**Raw passthrough accessors, NO enforcement** (loader.py L42-74 — `languages()`, `components()`, `pipeline()`) — each loads the default cfg if omitted and returns a list/dict passthrough. Enforcement belongs to the gate, never here:
```python
def languages(cfg: dict | None = None) -> list[dict]:
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("languages", []))
```
→ Clone as `members(cfg=None)` → `cfg.get("members", [])` and `edges(cfg=None)` → `cfg.get("pipeline", {}).get("edges", [])`.

**Guard-clean note (Pitfall 3):** the loader must NOT hardcode any member path — it reads `workspace.toml` at runtime, so it carries no member token and passes the new GEN-04 guard cleanly.

---

### `tools/workspace_config/__init__.py` (utility, package API — MREPO-01)

**Analog:** `tools/harness_config/__init__.py` (read in full — L1-24).

**PEP 562 lazy re-export** (the WHOLE file) — `tools` is a namespace package (no `tools/__init__.py`); an eager import here breaks pytest conftest-collection. Defer via `__getattr__`. Mirror byte-for-byte, swapping the `__all__` names:
```python
__all__ = ["components", "language_bash_scopes", "languages", "load_project", "pipeline"]

def __getattr__(name: str):  # PEP 562 — lazy re-export from the loader submodule.
    if name in __all__:
        from tools.harness_config import loader
        return getattr(loader, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```
→ `__all__ = ["edges", "load_workspace", "members"]`; import `from tools.workspace_config import loader`.

---

### `tools/workspace_config/pyproject.toml` (config, uv member — MREPO-01)

**Analog:** `tools/harness_config/pyproject.toml` (read in full — L1-13).

**Virtual (non-packaged) stdlib-only uv member** — `dependencies = []`, `package = false`, `requires-python >=3.11`. Mirror exactly; must never mutate `uv.lock`:
```toml
[project]
name = "logparser-workspace-config"   # or template-neutral name
requires-python = ">=3.11"
dependencies = []                       # stdlib-only (tomllib); never touch uv.lock
[tool.uv]
package = false                          # virtual member, imported by module path
```

**Registration note (RESEARCH Wave 0):** run `uv sync --all-packages` to register the new member in `uv.lock` — bare `uv sync` prunes tool-member deps (STATE precedent 02-01; CI already uses `--all-packages` everywhere, ci.yml L45/82/98/131/151/167/184/209).

---

### `tools/harness_lint/tests/test_workspace_config.py` (test, consistency gate — MREPO-01 + MREPO-04 parse)

**Analog:** `tools/harness_lint/tests/test_language_config.py` + `test_pipeline_config.py` (both read in full).

**Structural-test idiom** (both files L19-23) — repo root via `parents[3]`, real config loaded through the shared loader, iterate-config / assert-agreement / fail-loud. No subprocess, no runtime:
```python
# test_pipeline_config.py -> tests -> harness_lint -> tools -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
```

**Member-exists check** — mirror `test_each_configured_language_has_test_paths` (test_language_config.py L61-74). Use `.exists()` NOT `.is_file()` (roots are dirs, exactly like the note at L67):
```python
for lang in languages():
    paths = lang.get("test_paths", [])
    for p in paths:
        assert (_REPO_ROOT / p).exists(), f"{lang['id']!r}: test_paths {p} not found on disk"
```
→ For members: assert each `[[members]].id` unique + `(_REPO_ROOT / m["root"]).exists()`.

**Edge endpoint well-formedness** — mirror `test_pipeline_edges_are_well_formed` (test_pipeline_config.py L50-70): build `by_id` map, assert each edge `from`/`to` names a declared member. Parse `repo:stage` → member id first (MREPO-04):
```python
by_id = {c["id"]: c for c in components(cfg)}
for edge in pipeline(cfg).get("edges", []):
    src, dst, contract = edge["from"], edge["to"], edge["contract"]
    assert src in by_id, f"edge {edge!r}: `from` {src!r} is not a declared component"
```
→ `repo:stage` parse: `endpoint.split(":", 1)[0]` is the member id (bare stage → single-repo, backward-compat).

**Edge contract resolves to a tracked schema** — mirror `test_edge_contracts_have_a_tracked_schema` (test_pipeline_config.py L73-88), but glob under the **producer member's** root, not repo-root `contracts/`:
```python
schemas = {p.name.removesuffix(".schema.json") for p in _CONTRACTS_DIR.rglob("*.schema.json")}
for edge in pipeline(load_project()).get("edges", []):
    assert edge["contract"] in schemas, f"edge {edge!r}: contract {edge['contract']!r} has no tracked schema"
```
→ `_CONTRACTS_DIR` becomes `<producer_member_root> / "contracts"`.

---

### `tools/harness_lint/tests/test_core_no_workspace_member_dep.py` (test, GEN-04 guard twin — MREPO-04)

**Analog:** `tools/harness_lint/tests/test_core_no_example_dep.py` (read in full — the entire clone target).

**`git ls-files` core scan + self-exclusion** (L88-106) — scan tracked files under `("tools","harness","libs")`, subprocess `shell=False`, EXCLUDE this guard file itself (its negative-control literals would flag it):
```python
_CORE_ROOTS = ("tools", "harness", "libs")
_SELF = Path(__file__).resolve()
completed = subprocess.run(["git", "ls-files", *_CORE_ROOTS], cwd=_REPO_ROOT,
                           capture_output=True, text=True, check=True)
# ... skip resolved == _SELF
```

**Key-scoped sanctioned-pointer exemption** (L81-85, L109-113 — the CRITICAL pattern for Pitfall 3). The existing guard exempts `harness/project.toml`'s `root =`/`persona =`/`test_paths =` lines only:
```python
_INSTANCE_ROOT_FILE = "harness/project.toml"
_INSTANCE_POINTER_LINE = re.compile(r"\s*(root|persona|test_paths)\s*=")
def _is_instance_pointer_line(rel_path: str, line: str) -> bool:
    return rel_path == _INSTANCE_ROOT_FILE and _INSTANCE_POINTER_LINE.match(line) is not None
```
→ New guard: `_WORKSPACE_FILE = "workspace.toml"`, exempt `root =` and edge `from`/`to`/`contract =` pointer lines — **key-scoped**, ADR-0002(c) precedent. Forbidden token = member-root path tokens (resolved from `workspace.toml` at test time).

**Live negative controls** (L157-182) — a synthetic member-path ref MUST be flagged (scan can't silently no-op), plus a NON-pointer leak control mirroring `test_negative_control_flags_nonexempt_project_toml_leak` (L213-219):
```python
def test_negative_control_flags_nonexempt_project_toml_leak() -> None:
    hits = _scan_lines(_INSTANCE_ROOT_FILE, 'sdk_bootstrap = "examples/leak/x.sh"')
    assert hits, "a non-pointer examples/ leak in project.toml must be flagged"
```
→ Prove a `member = "tests/fixtures/workspace/..."` leak on a NON-pointer key IS still flagged.

---

### `tools/contract_drift/drift.py` (service, cross-repo drift — MREPO-03)

**Analog:** `tools/contract_drift/drift.py` itself (read in full — reuse `run_gate` VERBATIM per member).

**`run_gate` is ALREADY parametrized** (L134-163) — takes `contracts_dir` + `baseline_path`; do NOT add a new signature (anti-pattern). Each member has its OWN `contracts/.hashes/manifest.json`:
```python
def run_gate(contracts_dir=CONTRACTS_DIR, baseline_path=MANIFEST_PATH) -> dict:
    baseline = load_baseline(baseline_path)
    live = build_manifest(contracts_dir)
    delta = diff_manifests(live, baseline)
    ...
```
→ Cross-repo drift iterates members: `run_gate(contracts_dir=mroot/"contracts", baseline_path=mroot/"contracts/.hashes/manifest.json")`. Do NOT merge manifests (Pitfall 2 — `build_manifest` keys are `.parent`-relative, L146, so `contracts/...` keys collide across members).

**Cross-repo edge-resolution check (the ONE genuinely new bit)** — after per-member gates, resolve each edge's contract in its PRODUCER member (research Code Examples):
```python
for edge in edges(cfg):
    producer = by_id[edge["from"].split(":", 1)[0]]      # repo:stage → repo
    schemas = {p.name.removesuffix(".schema.json") for p in (producer/"contracts").rglob("*.schema.json")}
    assert edge["contract"] in schemas, f"edge {edge!r}: contract not tracked in producer"
```

**`shell=False` argv discipline** (L115-131, `_git_show`) — never interpolate manifest data into a shell (Security §). Preserve this in any new subprocess call.

---

### `tools/golden_runner/runner.py` (service, workspace-aware golden — MREPO-03)

**Analog:** `tools/golden_runner/runner.py` itself (read in full — extend `_confine`, reuse everything else).

**`golden_dir` override ALREADY exists** (L56-57 `case_dir`, L206-212 `run_golden_case`) — `run_golden_case(..., golden_dir=None)` and `case_dir(case, golden_dir)` already override the case root. Do NOT add a new signature — pass the member-scoped `golden_dir`:
```python
def case_dir(case: str, golden_dir: Path | None = None) -> Path:
    return (golden_dir or GOLDEN_DIR) / case
```

**`_confine` allowlist widening (THE one real hazard — Pitfall 1, L88-102):** today allows only `REPO_ROOT` + `/tmp` + `$TMPDIR`. A member root outside the repo raises `GoldenRunnerError`:
```python
def _confine(path: Path) -> Path:
    resolved = path.resolve()
    allowed_roots = (REPO_ROOT.resolve(), Path(os.path.realpath("/tmp")),
                     Path(os.environ.get("TMPDIR", "/tmp")).resolve())
    for root in allowed_roots:
        try:
            resolved.relative_to(root); return resolved
        except ValueError:
            continue
    raise GoldenRunnerError(f"path escapes confinement (repo/temp): {resolved}")
```
→ **Extend `allowed_roots` to include declared member roots**, threaded in as a parameter — WIDEN the allowlist, never remove the guard. Add a negative-control test proving a path outside every member root is STILL rejected. For the in-repo demo fixture, confinement passes unchanged (members are a `REPO_ROOT` subtree).

**Demo converter:** use the built-in `identity` converter (L216-219 — `converter="identity"`, no .NET) so the fixture goes green without .NET egress.

---

### `tests/fixtures/workspace/member-{a,b}/…` (fixture, data — MREPO-03 demo)

**Analog:** `examples/log-parser/contracts/.hashes/manifest.json` (committed-derived baseline) + the root `golden/` case tree.

**Ship fully baselined (Pitfall 5)** — a workspace with declared members but no baselined artifacts either errors or silently passes an empty gate. Each member needs its OWN committed `contracts/.hashes/manifest.json`:
```bash
python -m tools.contract_hash.hash --write \
  --contracts-dir tests/fixtures/workspace/member-a/contracts \
  --manifest tests/fixtures/workspace/member-a/contracts/.hashes/manifest.json
```
Plus one cross-repo edge and one golden case (seed + `expected/baseline.verified.tsv`) that spans it, run via the `identity` converter. Keep the fixture INSIDE `REPO_ROOT` (Pitfall 1). Print a visible SKIP on a zero-edge workspace (mirror CI `contract-check` L113-115 nullglob SKIP).

---

### `.github/workflows/ci.yml` (config, CI — MREPO-03)

**Analog:** the `drift` job (L121-135) + `emit-drift` (L179-189) + `stale-derived` (L203-231) separate-job pattern; fan-in via `gate.needs` (L240).

**Separate-job idiom** — a NEW `workspace` job, NOT folded into per-repo `drift`/`golden` (anti-pattern). Mirror the `drift` job's checkout → setup-uv → `uv sync --all-packages` → run-CLI shape:
```yaml
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.0
      - uses: astral-sh/setup-uv@v8.3.2
      - name: Sync workspace (all packages)
        run: uv sync --all-packages
      - name: Drift gate — example contracts manifest
        run: uv run python -m tools.contract_drift.drift --contracts-dir examples/log-parser/contracts --baseline examples/log-parser/contracts/.hashes/manifest.json
```
→ New `workspace` job iterates members + edges (cross-repo drift + spanning golden case).

**Fan-in registration** — add `workspace` to `gate.needs` (L240): `needs: [setup, lang-tests, contract-check, drift, golden, core-suite, emit-drift, stale-derived, workspace]`. The `gate` job (L239-253) fails on any upstream failure via `join(needs.*.result, ',')`.

**Security posture (preserve):** pinned actions, `permissions: contents: read`, NO event interpolation (matrix/data from repo-owned files only — L18-23).

---

### `harness/commands/workspace-analyze.md` (command — OPTIONAL, MREPO-02, DEFERRED)

**Analog:** `harness/commands/fan-out-synthesize.md` + `harness/skills/fan-out-synthesize/SKILL.md`.

**CONTEXT/RESEARCH strongly prefer PROSE wiring over new surface.** Reuse the existing `/fan-out-synthesize` entry point; a member repo is already a valid fan-out unit (SKILL.md: "one per directory, subsystem, contract, or question"). Add a thin command ONLY if reuse ergonomics prove insufficient (Claude's discretion at plan time).

**If a command/skill IS added (Pitfall 4):** it MUST round-trip `python -m tools.harness_emit` to BOTH runtimes, carry NO model id (placeholder-tier only), and bump `EXPECTED_SKILLS`/`EXPECTED_PERSONAS` frozensets in `tools/harness_lint/caps.py` (L129) or `check_skill_set` fails and `emit-drift` reds on `git diff --exit-code` (ci.yml L188-189).

---

## Shared Patterns

### Repo-root anchor via `parents[N]`
**Source:** loaders use `parents[2]` (`loader.py` L23, `runner.py` L29, `drift.py` via `contract_hash`); tests under `harness_lint/tests/` use `parents[3]` (`test_language_config.py` L23, `test_pipeline_config.py` L20, `test_core_no_example_dep.py` L41).
**Apply to:** every new loader (`parents[2]`) and every new gate test under `harness_lint/tests/` (`parents[3]`).

### Config = SSOT, no codegen (GEN-03 consistency-gate)
**Source:** `test_language_config.py` L1-13 docstring + L39-45.
**Apply to:** `test_workspace_config.py`. The manifest is authoritative; a structural test asserts agreement (edges resolve, no dangling member) — never generate code from it.

### `repo:stage` endpoint parse (backward-compatible)
**Source:** RESEARCH Code Examples (new helper); backward-compat with bare-stage `test_pipeline_config.py` endpoints.
**Apply to:** `test_workspace_config.py`, cross-repo drift, cross-repo golden resolution.
```python
def split_endpoint(endpoint: str) -> tuple[str | None, str]:
    if ":" in endpoint:
        repo, stage = endpoint.split(":", 1)
        return repo, stage
    return None, endpoint    # bare stage → single-repo (Phase-8 core stays UNCHANGED)
```

### `shell=False` argv subprocess discipline
**Source:** `drift.py` `_git_show` L115-131; `test_core_no_example_dep.py` `git ls-files` L90-96; `runner.py` converter spawn.
**Apply to:** every new subprocess call — never interpolate manifest/member strings into a shell.

### `uv sync --all-packages` for tool-member registration
**Source:** ci.yml uses it in all 7 jobs (L45, L82, L98, L131, L151, L167, L184, L209); STATE precedent 02-01.
**Apply to:** registering `tools/workspace_config` in `uv.lock`; the new `workspace` CI job.

---

## No Analog Found

None. Every file has a strong in-repo analog (verified live this session). This phase is purely additive over v1.0+α+β with zero external packages.

---

## Metadata

**Analog search scope:** `tools/harness_config/`, `tools/contract_drift/`, `tools/golden_runner/`, `tools/harness_lint/tests/`, `harness/`, `.github/workflows/`, `examples/log-parser/`.
**Files scanned (read in full or targeted):** `tools/harness_config/{loader.py,__init__.py,pyproject.toml}`, `tools/harness_lint/tests/{test_language_config.py,test_pipeline_config.py,test_core_no_example_dep.py}`, `tools/contract_drift/drift.py`, `tools/golden_runner/runner.py` (L1-70, L70-140, L206-221), `.github/workflows/ci.yml`, `harness/skills/fan-out-synthesize/*`.
**Line numbers verified against live code:** `_confine` L88-102, GEN-04 exemption L81-85/L109-113, `run_gate` L134-163, `run_golden_case` L206-220, `check_skill_set` caps L129 (per research), `gate.needs` ci.yml L240.
**Pattern extraction date:** 2026-07-13
