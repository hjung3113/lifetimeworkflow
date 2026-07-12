# Phase 7: Single-Source Dual-Runtime Emitter - Pattern Map

**Mapped:** 2026-07-12
**Files analyzed:** 15 new (`tools/harness_emit/**`) + 1 modified (`.github/workflows/ci.yml`)
**Analogs found:** 15 / 16 (1 novel surface: managed-block/signature merge has no exact in-repo twin — pattern composed from two precedents)

## How to read this map

Every new file has a **clone-this-file** analog already in the repo. Phase 7 adds almost no new
machinery — it composes four tested repo patterns:
1. **Determinism codegen** — `tools/docs_sync/generate.py` (`rows→render→write→main`, DERIVED header, `_confine`, sorted keys, no timestamps/floats, syrupy `.ambr`, virtual uv member, `parents[3]` conftest).
2. **Shared frontmatter reader** — `tools/harness_lint/frontmatter.py::parse_frontmatter` (the ONE reader; never re-slice fences).
3. **Cap/shape validators** — `tools/harness_lint/tests/{test_agents,test_skills,test_commands}.py` (the caps live here; import/share constants, do NOT re-declare).
4. **Re-emit-diff drift gate** — `tools/contract_drift/{drift.py,check.sh}` + `.github/workflows/ci.yml` `gate.needs` fan-in.

The one genuinely novel surface is `merge.py` (managed-block splice + settings.json signature merge) and `manifest.py` (ownership/prune) — keep those thin and well-tested; everything else is a clone.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tools/harness_emit/generate.py` (or `emit.py`) | build-tool / generator | transform (source→2 trees) | `tools/docs_sync/generate.py` | exact |
| `tools/harness_emit/__main__.py` | entrypoint | request-response (CLI) | `tools/docs_sync/__main__.py` | exact |
| `tools/harness_emit/__init__.py` | package doc | — | `tools/docs_sync/__init__.py` | exact |
| `tools/harness_emit/pyproject.toml` | config (virtual member) | — | `tools/docs_sync/pyproject.toml` | exact |
| `tools/harness_emit/project_agent.py` | transform (frontmatter projection) | transform | `tools/docs_sync/generate.py` `rows`/`render` + `parse_frontmatter` | role-match |
| `tools/harness_emit/project_command.py` | transform | transform | same as project_agent | role-match |
| `tools/harness_emit/project_skill.py` | transform + file-I/O copy | file-I/O | `docs_sync.write` + `iter_schemas` | role-match |
| `tools/harness_emit/permissions.py` | transform (matrix→15-key) | transform | `harness/permission-matrix.json` + `tools/harness_perms/resolver.py::load_matrix` | role-match |
| `tools/harness_emit/validate.py` | validator (loud-fail gate) | request-response | `tools/harness_lint/tests/test_agents.py` + `test_skills.py` (caps) | role-match |
| `tools/harness_emit/manifest.py` | store (ownership manifest) | CRUD (read/write/prune) | `tools/contract_drift/drift.py` (`load_baseline`/`diff_manifests`) | partial |
| `tools/harness_emit/merge.py` | transform (managed-block/signature merge) | transform | `tools/memory_regen/tests/test_hook_wiring.py` (settings.json shape) — **no exact code twin** | novel |
| `tools/harness_emit/tests/conftest.py` | test wiring | — | `tools/docs_sync/tests/conftest.py` | exact |
| `tools/harness_emit/tests/test_emit_determinism.py` | test | — | `tools/docs_sync/tests/test_docs_sync_determinism.py` | exact |
| `tools/harness_emit/tests/test_mapping.py` | test | — | `test_agents.py` (read-only invariant asserts) | role-match |
| `tools/harness_emit/tests/test_coexist.py` | test | — | `tools/memory_regen/tests/test_hook_wiring.py` | role-match |
| `.github/workflows/ci.yml` (modify: add `emit-drift` job + `gate.needs`) | config (CI) | event-driven | existing `drift` job + `gate` fan-in (same file) | exact |

---

## Pattern Assignments

### `tools/harness_emit/generate.py` (generator, transform) — the spine

**Analog:** `tools/docs_sync/generate.py` (clone the whole skeleton).

**Clone these load-bearing pieces verbatim, adapt names:**

- **Repo-root anchor + paths** (generate.py:26-29) — `tools/harness_emit/generate.py` is at depth `parents[2]` == repo root (same as docs_sync). Set `HARNESS_DIR = REPO_ROOT / "harness"`, `OPENCODE_DIR = REPO_ROOT / ".opencode"`, `CLAUDE_DIR = REPO_ROOT / ".claude"`.
  ```python
  REPO_ROOT = Path(__file__).resolve().parents[2]
  ```
- **Typed error for loud-fail** (generate.py:45-46) — mirror `DocsSyncError`; name it `HarnessEmitError`. Raise it (a) from `_confine` on traversal and (b) from `validate.py` on any HARD cap failure, aborting before any write.
  ```python
  class DocsSyncError(RuntimeError):
      """A generated path escaped the docs/reference/ confinement (T-03-21)."""
  ```
- **`_confine` path-confinement** (generate.py:187-193) — copy VERBATIM. This is the V4 access-control / path-traversal mitigation the security section requires. Call it before EVERY write, once per target tree (`.opencode`, `.claude`). A source `name: ../escape` must be refused, not written.
  ```python
  def _confine(path: Path, base: Path) -> Path:
      resolved = path.resolve()
      base_resolved = Path(base).resolve()
      if base_resolved != resolved and base_resolved not in resolved.parents:
          raise DocsSyncError(f"generated path escapes ... confinement: {resolved}")
      return resolved
  ```
- **`iter_*` sorted discovery** (generate.py:204-219) — clone `iter_schemas` shape: `sorted(root.glob(...))`, resolve-and-skip-outside-subtree (defense-in-depth vs symlink). Emit `iter_agents`/`iter_commands`/`iter_skills` reading `harness/{agents/*.md, commands/*.md, skills/*/SKILL.md}` — but read via `parse_frontmatter`, not `json.loads` (see below).
- **`write` returns written paths** (generate.py:222-239) — `_confine(target, out_dir)` BEFORE `target.write_text(..., encoding="utf-8")`. Return the list for the manifest.
- **DERIVED header discipline** (generate.py:35-38, 151) — emit a "generated by tools.harness_emit — do not hand-edit" HTML-comment first line on generated Markdown. This is also the marker `merge.py` fences with (see merge).
- **Determinism rules** (generate.py docstring:1-18, `_scalar`:52-64) — NO `datetime.now()`, NO raw floats, `json.dumps(sort_keys=True)`, `"\n".join(lines).rstrip("\n") + "\n"` trailing-LF. This is the whole reason the drift gate works.

**Deliberate divergence from docs_sync:** docs_sync reads schemas with stdlib `json`; the emitter reads Markdown with `parse_frontmatter` (below) and re-serializes frontmatter from a **fixed ordered template** per artifact type — do NOT ruamel round-trip (Pitfall 3: round-trip reorders/reflows → drift-gate flaps).

---

### `tools/harness_emit/project_agent.py` (frontmatter projection, transform) — D-04 sole specialization point

**Analog:** the shared reader `tools/harness_lint/frontmatter.py` + the read-only invariant logic in `tools/harness_lint/tests/test_agents.py`.

**Input reader — reuse, never re-implement** (frontmatter.py:26-55):
```python
from tools.harness_lint import parse_frontmatter
frontmatter_dict, body_text = parse_frontmatter(md_text)
```
It is CRLF-safe (`.replace("\r\n","\n")`, §4.3) and uses the ruamel **safe** loader (V5). Don't-Hand-Roll fence slicing.

**The projection table (from RESEARCH Mapping Table, D-04).** Authored `harness/agents/python-engineer.md` frontmatter carries BOTH runtime representations in one block:
```yaml
name: python-engineer
mode: subagent                 # opencode-only key
permission:                    # opencode-only block (15-key)
  read: allow
  edit: allow
  bash: { "*": ask, "uv *": allow, "pytest *": allow }
tools: Read, Edit, Bash, Grep, Glob   # Claude-only key
```
- **opencode target** `.opencode/agent/<name>.md`: keep `name, description, mode, permission`; `tools` optional. Emit `bash` sub-keys in **authored insertion order** (last-wins is semantic — do NOT sort them; sorting breaks `*`-first, Pitfall 3).
- **Claude target** `.claude/agents/<name>.md`: keep `name, description, tools`; **DROP** `mode` + `permission`; keep `model` only if present (and only the placeholder tier).

**Read-only invariant must survive BOTH projections** — port `is_read_only` (test_agents.py:85-97) into `validate.py` and assert it on each projected output, not just the source:
```python
def is_read_only(fm: dict) -> bool:
    perm = _permission(fm)
    for key in ("edit", "bash", "write"):
        if str(perm.get(key, "deny")) == "allow":
            return False
    tools = str(fm.get("tools", ""))
    return not any(tok in tools for tok in ("Write", "Bash", "Edit"))
```
`code-reviewer.md` (`edit: deny, bash: deny, write: deny` / `tools: Read, Grep, Glob`) must stay read-only in the opencode block AND the Claude allowlist after projection.

---

### `tools/harness_emit/project_command.py` (transform)

**Analog:** `project_agent` (same `parse_frontmatter` + ordered-template re-serialize).

Authored `harness/commands/build.md`:
```yaml
description: >- ...
agent: orchestrator
subtask: true
```
- **opencode** `.opencode/command/<name>.md`: keep `description, agent, subtask`.
- **Claude** `.claude/commands/<name>.md`: keep `description`; drop `agent`+`subtask` (no Claude equivalent). Body `` !`shell` `` + `$ARGUMENTS` shared by both.
- 18 commands under `harness/commands/*.md`. Claude emits to `.claude/commands/*.md` (top-level); GSD commands live under `.claude/commands/gsd/` → **no collision** (verify in `test_coexist.py`).

---

### `tools/harness_emit/project_skill.py` (transform + file-I/O copy)

**Analog:** `docs_sync.write`/`iter_schemas` for the tree walk; simplest projection (divergence = None).

- Source: `harness/skills/<name>/SKILL.md` (+ optional `references/` — `golden-debug`, `polyglot-boundary` have one).
- Both targets keep `name, description` identically; copy `references/**` byte-for-byte to `.opencode/skill/<name>/references/` AND `.claude/skills/<name>/references/`.
- 9 skills (EXPECTED_SKILLS in test_skills.py:51-63). Caps identical both runtimes.

---

### `tools/harness_emit/permissions.py` (transform, matrix→opencode.json 15-key)

**Analog:** `tools/harness_perms/resolver.py::load_matrix` (the ONE matrix reader) + `harness/permission-matrix.json` shape.

**Reuse the loader** (resolver.py:52-55) — preserves key order (last-wins depends on it):
```python
def load_matrix(path=...) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
```
**The transform:** project the 15 opencode keys from `permission-matrix.json` into `opencode.json`'s `permission` block. Note the authored `harness/opencode.json` already carries a PARTIAL `permission` block (`edit`, `bash`, `webfetch`, `external_directory`) — the emitter owns `opencode.json` wholesale and writes the full 15-key block from the matrix. Strip the non-opencode keys (`_note`, `path_deny_globs`) — those are resolver data, not opencode config. Keep the `bash` object in **authored insertion order** (catch-all `*` FIRST — Pitfall 3 / P3, documented in the matrix `_note`).

**The 15 valid keys** (test_agents.py:24-42): `read, edit, bash, glob, grep, list, task, external_directory, todowrite, question, webfetch, websearch, lsp, skill, doom_loop`. (`write` is NOT native — deny-only alias.)

---

### `tools/harness_emit/validate.py` (loud-fail gate) — EMIT-02 criterion 3

**Analog:** `tools/harness_lint/tests/test_skills.py` + `test_agents.py`. **Import/share the cap constants — do NOT re-declare (Don't-Hand-Roll).**

| Rule | Source-of-truth constant | Severity |
|------|--------------------------|----------|
| skill `name` ≤64, slug regex, == dir | `test_skills.py:31` `_NAME_MAX=64`, `_NAME_RE` | HARD |
| skill `description` ≤1024, no `<>`, no reserved word | `test_skills.py:32,41-44` `_DESC_MAX=1024` | HARD |
| skill body >500 lines | `test_skills.py:33` `_BODY_WARN_LINES=500` | **WARN** (`warnings.warn`, never reject — D-07) |
| agent `permission` keys ⊆ 15 | `test_agents.py:24-47` `VALID_PERMISSION_KEYS` | HARD |
| agent `mode` ∈ {primary,subagent,all} | `test_agents.py:49` `VALID_MODES` | HARD |
| read-only personas no write/shell in BOTH | `test_agents.py:85-97` `is_read_only` | HARD |
| `model` == `provider/explorer-tier` only | `test_agents.py:162-170` | HARD |

**≤200-vs-≤1024 resolved to 1024** (test_skills.py:29 "the 200-vs-1024 correction"). Use 1024.

**Loud-fail semantics (Pitfall 1):** validate source AND projected output **before any write**; on HARD failure raise `HarnessEmitError` and exit non-zero **writing nothing** (assert empty tmp tree in `test_validators.py`). NEVER `[:1024]`-slice / `.truncate(` a description. Body>500 → `warnings.warn` (mirror test_skills.py:135-147), still emits.

---

### `tools/harness_emit/manifest.py` (ownership store, CRUD-prune) — D-03

**Analog (partial):** `tools/contract_drift/drift.py` `load_baseline`/`diff_manifests` (JSON baseline read + set-diff idiom).

```python
def load_baseline(baseline_path=...) -> dict[str, str]:
    return json.loads(Path(baseline_path).read_text(encoding="utf-8"))

def diff_manifests(live, baseline) -> dict[str, list[str]]:
    changed = sorted(k for k in live if k in baseline and live[k] != baseline[k])
    added = sorted(k for k in live if k not in baseline)
    removed = sorted(k for k in baseline if k not in live)
    return {"changed": changed, "added": added, "removed": removed}
```
**Prune-then-write** (Regime A): read PREVIOUS manifest → delete now-absent owned paths → write current set → write `emit-manifest.json` with `json.dumps(sort_keys=True, indent=2)` + trailing LF. **GSD safety:** target globs MUST exclude `gsd-*`, `.claude/get-shit-done/**`, `.claude/hooks/**`, `.claude/commands/gsd/**`. Harness agents (`orchestrator`, `python-engineer`, `code-reviewer`, `explorer`) carry no `gsd-` prefix → verified no collision (all `.claude/agents/*` are `gsd-*`; see coexistence data below).

---

### `tools/harness_emit/merge.py` (managed-block + signature merge) — D-03, NOVEL

**No exact code twin** — the closest shape reference is `tools/memory_regen/tests/test_hook_wiring.py` (the settings.json contract this merge must preserve).

**Regime B-md (`AGENTS.md`, `CLAUDE.md`)** — HTML-comment marker splice:
```
<!-- BEGIN HARNESS-MANAGED (generated by tools.harness_emit — do not hand-edit) -->
...emitted block...
<!-- END HARNESS-MANAGED -->
```
Replace ONLY between markers; preserve outside verbatim; append once if markers absent (idempotent thereafter). Hand-roll as a small string splice (two markers, no lib).

**Regime B-json (`.claude/settings.json`)** — signature-matched hook-group replacement. Parse JSON → remove any hook group whose command matches a harness signature → re-insert harness groups in deterministic order → write `json.dumps(sort_keys=True, indent=2)` + trailing LF. **The coexistence contract this MUST preserve** (test_hook_wiring.py:15-40):
```python
EXISTING_COMMANDS = ["gsd-check-update.js", "gsd-session-state.sh", "tools/bootstrap/install.sh"]
INJECTOR_COMMAND = "memory-inject.sh"
# assert len(settings["hooks"]["SessionStart"]) == 4  (3 GSD + injector survive)
```
**Pitfall 4 (double-wiring):** the harness hook entries + `memory-inject.sh` are ALREADY hand-wired by Phases 2/4. The merge must reproduce the existing `settings.json` **byte-for-byte** (idempotent) OR the plan consciously migrates that wiring under emit ownership and updates `test_hook_wiring.py` in the same wave. Decide explicitly — do not silently produce a 5th SessionStart group.

---

### `tools/harness_emit/__main__.py` + `__init__.py` + `pyproject.toml` (virtual member)

**Analogs (clone exactly):**
- `__main__.py` — `tools/docs_sync/__main__.py`:
  ```python
  from tools.harness_emit.generate import main
  if __name__ == "__main__":
      raise SystemExit(main())
  ```
- `main()` CLI — generate.py:242-253 (print `wrote <rel>` per file, summary line, `return 0`).
- `pyproject.toml` — `tools/docs_sync/pyproject.toml` VERBATIM shape: `requires-python = ">=3.11"`, `dependencies = []`, `[tool.uv] package = false`. Zero new deps → `uv sync --all-packages` must NOT mutate `uv.lock`.
- `__init__.py` — keep import-light (docstring only) so conftest wires `sys.path` first (docs_sync/__init__.py pattern). If a package-level convenience API is wanted, use the PEP-562 lazy `__getattr__` re-export from `harness_config/__init__.py`.

---

### `tools/harness_emit/tests/**`

**Analog:** `tools/docs_sync/tests/` idiom.

- **conftest.py** — clone docs_sync/tests/conftest.py VERBATIM (adjust comment). `parents[3]` puts repo root on `sys.path`:
  ```python
  _REPO_ROOT = Path(__file__).resolve().parents[3]
  if str(_REPO_ROOT) not in sys.path:
      sys.path.insert(0, str(_REPO_ROOT))
  ```
- **test_emit_determinism.py** — clone `test_docs_sync_determinism.py`: (a) `render` twice byte-identical (lines 37-40); (b) emit→sha256→delete→regenerate→identical (lines 43-60); (c) committed **syrupy** `.ambr` snapshot of the projected tree (lines 63-69). Snapshot dir: `tools/harness_emit/tests/__snapshots__/`.
- **test_mapping.py** — assert opencode output has `mode`+`permission` and NO Claude leakage; Claude output has `tools` and NO `permission`; `is_read_only` survives both (port test_agents.py:173-181).
- **test_coexist.py** — seed a fixture `.claude/` with `gsd-*` agents/commands + GSD settings.json → assert every GSD file byte-unchanged; manifest lists only harness paths; extend test_hook_wiring.py assertions (4 groups, 3 GSD survive).
- **test_validators.py** — over-cap desc / invalid perm key / non-bool subtask → raises, writes nothing (assert empty tmp tree). 600-line body → warns, still emits.
- Pin the emitted set the way test_skills.py/test_agents.py pin `EXPECTED_SKILLS`/`EXPECTED_PERSONAS` (anti-drift).

---

### `.github/workflows/ci.yml` (modify: add `emit-drift` job) — D-02, criterion 4

**Analog:** the existing `drift` job (ci.yml:125-135) + `gate` fan-in (ci.yml:178-179), same file.

Add one job mirroring the `drift` job structure (checkout@v7.0.0, setup-uv@v8.3.2, `uv sync --all-packages`), then re-emit + `git diff --exit-code`:
```yaml
emit-drift:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v7.0.0
    - uses: astral-sh/setup-uv@v8.3.2
    - run: uv sync --all-packages
    - run: uv run python -m tools.harness_emit
    - run: git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json
```
Then add `emit-drift` to `gate.needs` (ci.yml:179) so it joins the non-bypassable fan-in:
```yaml
gate:
  needs: [setup, lang-tests, contract-check, drift, golden, core-suite, emit-drift]
```
Optional local twin: a `tools/harness_emit/check.sh` mirroring `tools/contract_drift/check.sh` (`set -euo pipefail`; `exec uv run python -m tools.harness_emit`).

---

## Shared Patterns

### Frontmatter reading (all projectors)
**Source:** `tools/harness_lint/frontmatter.py` (lines 26-55) — `from tools.harness_lint import parse_frontmatter`.
**Apply to:** `project_agent.py`, `project_command.py`, `project_skill.py`, `validate.py`.
CRLF-safe, ruamel safe-loader (V5). The one reader — never re-slice fences.

### Cap constants (validators)
**Source:** `tools/harness_lint/tests/test_skills.py` (`_NAME_MAX=64`, `_DESC_MAX=1024`, `_BODY_WARN_LINES=500`, `_NAME_RE`, `_RESERVED_WORDS`, `_XML_CHARS`) + `test_agents.py` (`VALID_PERMISSION_KEYS`, `VALID_MODES`, `is_read_only`).
**Apply to:** `validate.py`, `test_validators.py`.
Import or factor into a shared module so a cap change lands in ONE place (Don't-Hand-Roll). Consider extracting these constants out of the test files into `tools/harness_lint/` proper so both the tests and the emitter import them.

### Determinism / byte-identical write (all writers)
**Source:** `tools/docs_sync/generate.py` (docstring:1-18, `render`:139-181, `write`:222-239).
**Apply to:** every write path.
LF, no BOM, UTF-8; `json.dumps(sort_keys=True)`; DERIVED header first line; `"\n".join(...).rstrip("\n") + "\n"`; NO `datetime.now()`, NO raw floats. **Exception:** the `bash` last-wins matrix keeps AUTHORED insertion order (semantic — sorting breaks `*`-first).

### Path confinement (all writers) — security V4 / STRIDE-Tampering
**Source:** `tools/docs_sync/generate.py::_confine` (lines 187-193).
**Apply to:** every target before `write_text`. A traversal-shaped `name` (`../escape`) is refused, not written.

### Virtual uv-workspace member (package layout)
**Source:** `tools/docs_sync/pyproject.toml` (+ `harness_config/__init__.py` PEP-562 lazy re-export).
**Apply to:** `tools/harness_emit/pyproject.toml`, `__init__.py`, `tests/conftest.py`.
`package = false`, `dependencies = []`, invoked `python -m tools.harness_emit`, `parents[3]` conftest.

### Re-emit-diff drift gate
**Source:** `tools/contract_drift/{drift.py,check.sh}` + `.github/workflows/ci.yml` `drift` job & `gate.needs`.
**Apply to:** `emit-drift` CI job + optional `manifest.py` diff helpers.

---

## Coexistence facts (verified this session — feed `test_coexist.py`)

- `.claude/agents/` currently holds **only** `gsd-*.md` (32 files) → harness's `orchestrator/python-engineer/code-reviewer/explorer` have **no name collision**.
- `.claude/commands/` holds only the `gsd/` subdir → harness top-level `.claude/commands/*.md` do not collide.
- `.claude/settings.json` `hooks.SessionStart` = exactly 4 groups (3 GSD + `memory-inject.sh`), asserted by `tools/memory_regen/tests/test_hook_wiring.py`. The emitter's settings merge must keep it at 4 (Pitfall 4).
- `.opencode/` does NOT exist yet (greenfield first emit) — must be committed, not gitignored (`.gitignore` only ignores `.memory/derived/` + `.claude/settings.local.json`).
- GSD-owned, NEVER touch: `.claude/get-shit-done/`, `.claude/hooks/`, `.claude/gsd-*.json`, `.claude/package.json`.

---

## No Analog Found

| File | Role | Data Flow | Reason | Fallback |
|------|------|-----------|--------|----------|
| `tools/harness_emit/merge.py` | transform | transform | No in-repo managed-block-splice or JSON signature-merge code exists. `test_hook_wiring.py` fixes the *contract* (4 groups, GSD survival) but not an implementation. | Hand-roll two thin functions (marker splice for md, parse→filter→reinsert for settings.json) per RESEARCH §"Manifest + Managed-Block Merge"; MEDIUM-confidence design, cover heavily with `test_merge_idempotent.py`. |

Everything else has a concrete in-repo analog above.

---

## Metadata

**Analog search scope:** `tools/` (docs_sync, contract_drift, harness_lint, harness_config, harness_perms, memory_regen), `harness/`, `.claude/`, `.github/workflows/`.
**Files scanned (read this session):** docs_sync/{generate.py, pyproject.toml, __main__.py, __init__.py, tests/conftest.py, tests/test_docs_sync_determinism.py}; contract_drift/{drift.py, check.sh}; harness_lint/{frontmatter.py, tests/test_agents.py, tests/test_skills.py}; harness_config/{loader.py, __init__.py, tests/test_matrix_emit.py}; harness_perms/resolver.py; memory_regen/tests/test_hook_wiring.py; .github/workflows/ci.yml; harness/{permission-matrix.json, opencode.json, agents/python-engineer.md, agents/code-reviewer.md, commands/build.md}; full harness/ + .claude/ tree listing.
**Pattern extraction date:** 2026-07-12
</content>
</invoke>
