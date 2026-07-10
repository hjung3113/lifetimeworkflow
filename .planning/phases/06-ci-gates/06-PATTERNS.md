# Phase 6: CI + Gates (generic) - Pattern Map

**Mapped:** 2026-07-09
**Files analyzed:** 10 (3 CREATE .github, 2 CREATE Wave-0 tests, 5 MODIFY enablers)
**Analogs found:** 7 / 10 (3 .github files are net-new artifact types — no in-repo analog; RESEARCH supplies the verified patterns)

> **Phase nature:** This is a CI/infra phase. It writes almost NO new logic. Two categories:
> (1) `.github/*` orchestration YAML/text with no in-repo analog (planner uses RESEARCH §Patterns 1–3 verbatim), and
> (2) small, well-scoped ENABLER edits + Wave-0 tests on the reused `tools/*` — these have EXACT in-repo analogs and MUST copy them.
> **D-01 non-negotiable:** CI *calls* existing `tools/*` CLIs verbatim; it never re-implements hashing/diff/canonicalization.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.github/workflows/ci.yml` | config (CI orchestration) | event-driven (PR trigger) → batch | RESEARCH §Patterns 1–3 (no in-repo YAML) | no-analog (spec-driven) |
| `.github/CODEOWNERS` | config (merge-gate) | event-driven (review routing) | none in repo; `harness/project.toml` glob-scope model | no-analog (spec-driven) |
| `.github/pull_request_template.md` | config (doc template) | request-response (PR body) | none in repo | no-analog (spec-driven) |
| `tools/harness_config/tests/test_matrix_emit.py` | test | transform (config → matrix JSON) | `tools/harness_config/tests/test_loader.py` | exact |
| `tools/contract_drift/tests/test_cli_flags.py` | test | CRUD-over-fs (tmp tree + CLI) | `tools/contract_drift/tests/test_convention_mutation.py` | exact |
| `harness/project.toml` (MODIFY) | config (SSOT data slot) | transform (data only) | itself — existing `[[languages]]` tables | in-place |
| `tools/harness_config/loader.py` (MODIFY) | utility (config reader) | transform | itself — `languages()` passthrough at loader.py:42 | in-place |
| `tools/contract_drift/drift.py` (MODIFY) | utility (CLI) | request-response (argv → exit) | `tools/contract_hash/hash.py` `main()` (hash.py:71) | exact (sibling CLI) |
| `tools/contract_hash/hash.py` (MODIFY) | utility (CLI) | request-response (argv → exit) | itself — existing `--write` argv idiom (hash.py:71-79) | in-place |
| `tools/harness_lint/tests/test_language_config.py` (MODIFY) | test | transform (config consistency) | itself — existing per-language assertions | in-place |

## Pattern Assignments

### `tools/harness_config/tests/test_matrix_emit.py` (test, transform) — CREATE, Wave 0

**Analog:** `tools/harness_config/tests/test_loader.py` (exact — same package, same purpose: assert the SSOT config shape feeds a downstream consumer).

**Import + repo-root pattern** (test_loader.py:10-17) — copy verbatim, package-level lazy re-export:
```python
from __future__ import annotations

from pathlib import Path

from tools.harness_config import language_bash_scopes, languages, load_project

# test_matrix_emit.py -> tests -> harness_config -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
```

**Assertion idiom** (test_loader.py:20-37) — pure structural, no subprocess, iterate `languages()`, assert per-field presence:
```python
def test_load_project_returns_two_languages() -> None:
    cfg = load_project()
    ids = sorted(lang["id"] for lang in cfg["languages"])
    assert ids == ["dotnet", "python"]

def test_each_language_carries_required_fields() -> None:
    for lang in languages():
        for field in ("id", "bash_scope", "test", "format", "persona"):
            assert str(lang.get(field, "")).strip(), f"{lang.get('id')!r}: missing {field}"
```

**What this test adds (CI-01):** assert the matrix-JSON shape built from `languages()` — one leg per language, each carrying `id` + `test` + the NEW `test_paths` list — so the workflow's `setup` step (which reuses `languages()`) emits valid `{"include":[...]}`. Mirror `test_language_bash_scopes_union_includes_implicit_pytest` (test_loader.py:47-50) for the exact-set assertion style. No `conftest.py` needed — the package's PEP-562 lazy re-export (`__init__.py`) makes `from tools.harness_config import languages` resolve during collection.

---

### `tools/contract_drift/tests/test_cli_flags.py` (test, CRUD-over-fs) — CREATE, Wave 0

**Analog:** `tools/contract_drift/tests/test_convention_mutation.py` (exact — same package; builds a tmp contracts tree and drives `run_gate` with a non-default `contracts_dir`, which is precisely the `--contracts-dir`/`--baseline` surface the new flags expose).

**Import + sys.path bootstrap** (test_convention_mutation.py:9-22) — copy verbatim (drift tests self-insert repo root; note the `# noqa: E402` after the path insert):
```python
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import load_baseline, run_gate  # noqa: E402
from tools.contract_hash.hash import REPO_ROOT, schema_hash  # noqa: E402
```

**tmp-tree copy fixture** (test_convention_mutation.py:27-38) — copy the `_copy_contracts(tmp_path)` helper + the pristine-copy-passes sanity test:
```python
def _copy_contracts(tmp_path: Path) -> Path:
    dst = tmp_path / "contracts"
    shutil.copytree(REPO_ROOT / "contracts", dst)
    return dst

def test_unchanged_copy_matches_baseline(tmp_path):
    contracts = _copy_contracts(tmp_path)
    result = run_gate(contracts_dir=contracts)
    assert result["ok"] is True
    assert result["drifted"] == []
```

**What this test adds (CI-01 example-drift):** assert the NEW `main(["--contracts-dir", ..., "--baseline", ...])` argparse routes to `run_gate(contracts_dir, baseline_path)` and returns exit 0 on a pristine copy / exit 1 on a mutated copy. Since `run_gate` is already parameterized (drift.py:133-136), the test drives the CLI wrapper: call `drift.main([...])` (returns `int`) and assert the exit code — the argv→exit contract mirrors how `hash.main(["--write"])` is exercised. Use `tmp_path` (pytest builtin) exactly as the analog does; never mutate the committed baseline.

---

### `harness/project.toml` (config, MODIFY) — Enabler-1, Wave 1

**Analog:** itself — the existing two `[[languages]]` tables (project.toml:21-34). Add an additive `test_paths` array to each table, following the existing field style (inline `#` comment justifying the value).

**Existing table shape to extend** (project.toml:21-34):
```toml
[[languages]]
id = "dotnet"
bash_scope = "dotnet *"
test = "dotnet test"
format = "dotnet format"
sdk_bootstrap = "tools/bootstrap/install.sh"
persona = "examples/log-parser/agents/dotnet-engineer.md"
# ADD: test_paths = ["examples/log-parser/libs/dotnet/Normalize.Tests/Normalize.Tests.csproj"]
#   (3 .csproj + NO .sln → bare `dotnet test` fails; explicit test-project path required — RESEARCH Pitfall 2)

[[languages]]
id = "python"
bash_scope = "uv *"
test = "uv run pytest"
format = "ruff format"
persona = "harness/agents/python-engineer.md"
# ADD: test_paths = ["examples/log-parser/tests"]  (example pytest lives OFF root testpaths — pyproject.toml:39)
```

**Constraint:** the file header (project.toml:1-14) declares it PURE DATA — no logic. Keep the addition data-only; the loader stays the consumer. Data-only additive field will not disturb the GEN-04 core-no-example-dep guard (paths are strings in the instance-supplied slot).

---

### `tools/harness_config/loader.py` (utility, MODIFY) — Enabler-1, Wave 1

**Analog:** itself — `languages()` at loader.py:42-46 is already a pass-through returning the raw `[[languages]]` dicts, so `test_paths` flows through for free (RESEARCH: "already trivially forward-compatible: `l.get("test_paths", [])`").

**Existing passthrough** (loader.py:42-46) — no signature change; at most a docstring note that legs may carry `test_paths`:
```python
def languages(cfg: dict | None = None) -> list[dict]:
    """Return the configured ``[[languages]]`` tables (loads the default config if omitted)."""
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("languages", []))
```

**Guidance:** Keep signatures stable — the module docstring (loader.py:6) explicitly reserves the loader for "the Phase-6 config-derived CI matrix." Consumers read `lang.get("test_paths", [])`; the loader need not add a dedicated accessor unless the planner wants a `language_test_paths()` helper mirroring `language_bash_scopes()` (loader.py:49-53) for symmetry.

---

### `tools/contract_drift/drift.py` (utility CLI, MODIFY) — Enabler-2, Wave 1

**Analog:** `tools/contract_hash/hash.py` `main()` (hash.py:71-79) — the SIBLING CLI in the same drift/hash pair. Its `argv` handling is the idiom to extend into argparse; `run_gate` is already parameterized so only `main()` changes.

**Current stub to replace** (drift.py:165-179) — the `# noqa` literally flags the reserved-for-flags intent:
```python
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    result = run_gate()
    ...
```

**Already-parameterized target** (drift.py:133-136) — the flags map 1:1 onto these params:
```python
def run_gate(
    contracts_dir: str | Path = CONTRACTS_DIR,
    baseline_path: str | Path = MANIFEST_PATH,
) -> dict:
```

**Sibling argv idiom to mirror** (hash.py:71-79) — same `argv = sys.argv[1:] if argv is None else argv` entry; extend with `argparse` adding `--contracts-dir` and `--baseline`, then `run_gate(contracts_dir=args.contracts_dir, baseline_path=args.baseline)`. Keep the `main(argv=None) -> int` + `raise SystemExit(main())` (drift.py:182-183) contract so `test_cli_flags.py` can call `main([...])` directly. Defaults stay `CONTRACTS_DIR`/`MANIFEST_PATH` (imported at drift.py:22-27) so the bare invocation is unchanged for the root job.

---

### `tools/contract_hash/hash.py` (utility CLI, MODIFY) — Enabler-2, Wave 1

**Analog:** itself — the existing `--write` argv check (hash.py:71-79). Add matching `--contracts-dir`/`--manifest` argparse so the example manifest can be rebuilt/compared, mirroring the drift-CLI change for symmetry.

**Existing argv idiom** (hash.py:71-79):
```python
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--write" in argv:
        out = write_manifest()
        ...
    else:
        print(json.dumps(build_manifest(), indent=2, sort_keys=True))
    return 0
```

**Parameterized targets already present:** `build_manifest(contracts_dir=CONTRACTS_DIR)` (hash.py:42) and `write_manifest(manifest_path=MANIFEST_PATH)` (hash.py:62). Add `--contracts-dir`/`--manifest` and thread them through; keep `--write` behavior. Keep `main(argv=None) -> int` + `SystemExit(main())` (hash.py:82-83).

---

### `tools/harness_lint/tests/test_language_config.py` (test, MODIFY) — Enabler-1, Wave 1

**Analog:** itself — the existing per-language assertions (test_language_config.py:48-58). Add a test that tolerates/verifies the new `test_paths` field, following the exact `for lang in languages()` idiom already in the file.

**Existing per-language assertion to mirror** (test_language_config.py:55-58):
```python
def test_each_configured_language_has_test_command() -> None:
    for lang in languages():
        assert str(lang.get("test", "")).strip(), f"{lang['id']!r}: empty test command"
```

**What to add (A4 in RESEARCH):** a `test_each_configured_language_has_test_paths()` (or tolerance check) asserting `lang.get("test_paths", [])` is a `list[str]` and, where present, points at real paths under `_REPO_ROOT` (mirror `test_each_configured_persona_exists`, test_language_config.py:48-52, which does `(_REPO_ROOT / lang["persona"]).is_file()` — for `test_paths`, check `.exists()` since `.csproj` is a file but pytest dirs are directories). CRITICAL: the SSOT-equality gate `test_matrix_language_scopes_equal_config` (test_language_config.py:39-45) must STILL pass — `test_paths` is additive and does not touch `language_bash_scopes()`, so run this suite after the project.toml bump to confirm the new field does not perturb the scope equality (A4 verification).

---

## Shared Patterns

### Test import/bootstrap convention (all new/edited Python tests)
**Source:** `tools/harness_config/tests/test_loader.py:10-17` (namespace-package via package `__init__`) and `tools/contract_drift/tests/test_convention_mutation.py:14-22` (explicit `sys.path.insert`).
**Apply to:** both Wave-0 test files.
**Rule:** `tools` is a namespace package (no `tools/__init__.py`); tests either (a) rely on a package `__init__` PEP-562 lazy re-export (harness_config) or (b) self-insert `_REPO_ROOT = Path(__file__).resolve().parents[3]` onto `sys.path` before importing `tools.*` (contract_drift), with `# noqa: E402` on the deferred imports. Match the analog PACKAGE's existing convention — do not mix.
```python
_REPO_ROOT = Path(__file__).resolve().parents[3]   # tests -> pkg -> tools -> repo root
```

### CLI `main(argv)` → exit-code convention (both enabler CLIs)
**Source:** `tools/contract_hash/hash.py:71-83`, `tools/contract_drift/drift.py:165-183`.
**Apply to:** the drift + hash `main()` edits.
```python
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ...
    return 0            # or 1 on gate failure
if __name__ == "__main__":
    raise SystemExit(main())
```
Keep `main` returning `int` and testable via `main([...])`; the `check.sh` wrapper (`exec uv run python -m tools.contract_drift.drift "$@"`, check.sh:12) forwards argv unchanged, so new flags reach `main` in CI with no wrapper edit.

### Reused CLI entrypoints CI shells verbatim (D-01 — the workflow, not new code)
**Source (evidence, do NOT re-implement):**
- contract-drift: `uv run python -m tools.contract_drift.drift` (root) + `... --contracts-dir examples/log-parser/contracts --baseline examples/log-parser/contracts/.hashes/manifest.json` (after Enabler-2). check.sh:12.
- contract-hash: `python -m tools.contract_hash.hash [--write]` (hash.py:71).
- golden root identity: `uv run pytest tools/golden_runner` — NOT the CLI (runner `main()` defaults `converter=dotnet`; identity path is proven by `test_sample_loop.py:26` calling `run_golden_case("sample", out, converter="identity")`).
- golden example .NET: `uv run pytest examples/log-parser/tests` (`require_dotnet` cases RUN once .NET is installed).
- contract-check: `uv run check-jsonschema --schemafile <schema> <inst>` looped over `contracts/**` AND `examples/**/contracts/**` (RESEARCH §Pattern 2; loop authored in `harness/commands/contract-check.md:28`).
**Apply to:** the three generic jobs in `ci.yml`. Every job runs `uv sync --all-packages` first (RESEARCH Pitfall 4 — bare `uv sync` prunes tool-member deps).

## No Analog Found

The `.github/*` files are net-new artifact TYPES for this repo (verified: `find .github` → none exist). The planner takes patterns from RESEARCH.md (all verified there), not from an in-repo analog:

| File | Role | Data Flow | Reason / Source to use |
|------|------|-----------|------------------------|
| `.github/workflows/ci.yml` | config | event-driven → batch | First workflow in repo. Use RESEARCH §Patterns 1–3 verbatim: `setup` matrix-emitter (reuses `tools.harness_config.loader.languages()` → `$GITHUB_OUTPUT`), `fromJSON` per-language fan-out, 3 generic jobs, `if: always()` fan-in `gate`. Pin `actions/checkout@v7.0.0`, `actions/setup-dotnet@v5.4.0` (`dotnet-version: '10.0.100'` EXACT), `astral-sh/setup-uv@v8.3.2`. Add top-level `permissions: { contents: read }`. Self-validate via `check-jsonschema --builtin-schema vendor.github-workflows`. |
| `.github/CODEOWNERS` | config | event-driven | No prior CODEOWNERS. Map constitution-plane globs (`/contracts/`, `/docs/adr/`, `/golden/`) + example equivalents (`/examples/*/contracts/`, `/examples/*/golden/`) → `@hjung3113` (D-A). Document: hard enforcement needs branch-protection "require review from code owners" (advisory otherwise); note solo-repo self-approval nuance. The glob-scope model loosely echoes `harness/project.toml`'s instance-slot posture but there is no code analog. |
| `.github/pull_request_template.md` | config (doc) | request-response | No prior PR template. Lightweight breaking-change / golden-update / contract-drift checklist (D-04). No model identifiers (CLAUDE.md constraint). |

## Metadata

**Analog search scope:** `tools/harness_config/`, `tools/contract_drift/`, `tools/contract_hash/`, `tools/harness_lint/`, `tools/golden_runner/`, `harness/`, `.github/` (absent), and repo-wide test-file inventory.
**Files scanned:** loader.py, project.toml, drift.py, hash.py, check.sh, harness_config/__init__.py, test_loader.py, test_language_config.py, test_classify.py, test_convention_mutation.py, test_sample_loop.py (head), harness_lint conftest.py, pyproject.toml (pytest config); plus a full `find tools -name test_*.py` inventory (34 test modules).
**Pattern extraction date:** 2026-07-09
