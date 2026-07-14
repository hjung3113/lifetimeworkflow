# Coding Conventions

**Analysis Date:** 2026-07-14

**Scope:** This document maps the harness CORE — `tools/**`, `harness/**`, `libs/python/**`,
`contracts/**`. `examples/log-parser/**` is a downstream instance that follows the same rules
(see `examples/log-parser/AGENTS.md`) but is secondary reference here.

## Naming Patterns

**Package/module dirs (`tools/<name>/`):**
- `snake_case`, one concern per package: `contract_drift`, `contract_hash`, `golden_runner`,
  `harness_config`, `harness_emit`, `harness_lint`, `harness_perms`, `hooks`, `memory_regen`,
  `polyglot_lint`, `strangler_guard`, `workspace_config`, `docs_sync`, `bootstrap`.
- Each package is a `uv` workspace member (own `pyproject.toml`) except `tools/bootstrap`
  (shell-only, explicitly excluded from `[tool.uv.workspace] exclude` in root `pyproject.toml`).

**Files inside a package:**
- The primary logic module is named after the verb/noun it performs, not `main.py`:
  `runner.py`, `drift.py`, `hash.py`, `guard.py`, `resolver.py`, `loader.py`, `generate.py`.
- A package gets `__main__.py` only when it needs `python -m tools.<pkg>` (bare package, no
  submodule) to dispatch to a specific function — e.g. `tools/harness_emit/__main__.py`,
  `tools/strangler_guard/__main__.py`, `tools/docs_sync/__main__.py`. Packages invoked via
  `python -m tools.<pkg>.<module>` (e.g. `tools.golden_runner.runner`,
  `tools.contract_drift.drift`) skip `__main__.py` and put `if __name__ == "__main__":
  raise SystemExit(main())` at the bottom of the module itself.

**Functions:**
- `snake_case`, verb-first: `run_gate`, `load_baseline`, `diff_manifests`, `resolve_dotnet`,
  `case_dir`, `seed_path`, `verified_path`.
- Private/internal helpers prefixed `_`: `_confine`, `_hashable`, `_index`, `_stdin` (module).

**Classes:**
- `PascalCase`. Custom exceptions end in `Error` and subclass `RuntimeError` (not bare
  `Exception`) unless the class specifically models a *refusal* rather than a failure — see
  Error Handling below. Data holders use `@dataclass(frozen=True)` (e.g. `GoldenResult`).

**Test files:**
- `tools/<pkg>/tests/test_<thing>.py`, `libs/python/normalize/tests/test_<thing>.py`. Function
  names read as an assertion: `test_clean_tree_exits_zero`, `test_dotnet_absent_skips_golden_not_fail`.

**Spec-ID references in docstrings:**
- Module and function docstrings tag the originating spec item in parens/caps, e.g.
  `(CONTRACT-03, D-01/D-02/D-03)`, `(HOOK-03, D-02, D-06)`, `(EMIT-02)`, `(GEN-04)`. Preserve
  this tagging style when adding new modules — it's how spec traceability is kept without a
  separate traceability doc.

## Code Style

**Formatting + linting: ruff (single tool, lint AND format)**
- Config lives in root `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 100
  target-version = "py311"
  extend-exclude = [".dotnet", ".venv", "bin", "obj"]

  [tool.ruff.lint]
  select = ["E", "F", "I", "UP", "B"]
  ```
- Rule sets: `E` (pycodestyle errors), `F` (pyflakes), `I` (import sort/isort-equivalent), `UP`
  (pyupgrade — modern syntax), `B` (bugbear — common footguns). No black/isort/flake8 — ruff
  replaces all three.
- Every module opens with `from __future__ import annotations` (deferred annotation
  evaluation; consistent across all `tools/**` and `libs/python/**` modules).
- Enforced on write by the `format_on_write` hook (`tools/hooks/format_on_write.py`).

**Types: pyright, not mypy**
```toml
[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "standard"
exclude = ["**/.dotnet", "**/.venv", "**/bin", "**/obj", "**/__pycache__"]
```
- `standard` mode (not `strict`). Use modern union syntax (`Path | None`, `str | None`) — not
  `Optional[...]` — consistent with the `UP` ruff rule set targeting py311.

## Import Organization

**Order (ruff `I` rule, isort-equivalent):**
1. `from __future__ import annotations` (always first, own line)
2. stdlib (`os`, `sys`, `json`, `subprocess`, `argparse`, `dataclasses`, `pathlib`, `hashlib`, ...)
3. third-party (`jsonschema`, `pytest`, `rfc8785`)
4. first-party `tools.*` / project-internal imports

**No path aliases.** Cross-package imports use the fully-qualified module path, e.g.:
```python
from tools.contract_hash.hash import CONTRACTS_DIR, MANIFEST_PATH, REPO_ROOT, build_manifest
from tools.workspace_config import edges, load_workspace, members, split_endpoint
from tools.golden_runner.runner import received_path, verified_path
```

**Cross-workspace-member import (`libs/python` from `tools/*`):** `libs/python` is a virtual uv
workspace member, not pip-installed into the other members' environments, so consumers thread it
onto `sys.path` manually at import time, guarded and commented:
```python
REPO_ROOT = Path(__file__).resolve().parents[2]  # <pkg> -> tools -> repo root
_LIBS_PYTHON = REPO_ROOT / "libs" / "python"
if str(_LIBS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_LIBS_PYTHON))

from normalize.core import normalize_tsv  # noqa: E402
```
Reuse this exact pattern (with the `# noqa: E402` on the deferred import) for any new module
that needs the `libs/python/normalize` core.

## Module-Layout / CLI Idiom

**One concern per `tools/<name>/` package**, invoked via `python -m tools.<name>[.<module>]` —
never by file path (`python tools/golden_runner/runner.py`). This keeps the uv workspace import
graph (and `sys.path`) honest. Golden-path commands are catalogued in root `AGENTS.md`:
```bash
uv run pytest
bash tools/contract_drift/check.sh                 # or: python -m tools.contract_drift.drift
python -m tools.contract_hash.hash
python -m tools.golden_runner.runner
python -m tools.golden_runner.approve --approve --adr <id>
python -m tools.memory_regen.repo_map
python -m tools.memory_regen.contracts_index
python -m tools.memory_regen.inject
python -m tools.harness_emit
```

**`REPO_ROOT` anchor pattern.** Every module that needs repo-relative paths resolves them once
near the top from `Path(__file__).resolve().parents[N]` (N = depth from repo root), commented
with the derivation, e.g. `tools/golden_runner/runner.py:29` (`parents[2]`), `tools/harness_emit
/generate.py:38` (`parents[2]`). Never hardcode an absolute path or rely on CWD.

**CLI entry pattern (`argparse`, not click/typer):**
```python
def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("case", help="...")
    parser.add_argument("--approve", action="store_true", help="...")
    args = parser.parse_args(argv)
    ...
    return 0  # or 1 / 2 / 3, see Exit-Code Semantics

if __name__ == "__main__":
    raise SystemExit(main())
```
`main()` takes an optional `argv: list[str] | None` so it is unit-testable without spawning a
subprocess (tests call `main(["--approve", "--adr", "ADR-0001"])` directly).

## Exit-Code Semantics

Exit codes are a deliberate, repo-wide vocabulary — not incidental. When adding a new gate/hook,
reuse this table rather than inventing a new code:

| Code | Meaning | Example |
|------|---------|---------|
| `0` | pass / allow / clean | `contract_drift.drift` no divergence; `commit_gate` all checks pass |
| `1` | fail / block (generic gate failure) | `contract_drift.drift` divergence found; `polyglot_lint.lint` §4.3–4.6 violation; `commit_gate` internal fail path |
| `2` | Claude **PreToolUse block** code specifically (hook-wrapper context, not a bare CLI) | `commit_gate.py` `--from-hook` wrapper blocking a `git commit` |
| `3` | **refusal** — a human-ratification gate was not satisfied (distinct from a plain failure) | `golden_runner/approve.py` (`GoldenApprovalRefused`); `strangler_guard/guard.py` (missing baseline) |

Exit 3 specifically signals "this is not a bug to fix, it's a promotion that needs an explicit
human act" (`--approve` + `--adr` + `GOLDEN_APPROVE_HUMAN` token) — never conflate it with exit 1.

## Error Handling

**Custom exception classes, one per package, subclassing `RuntimeError`:**
```python
class GoldenRunnerError(RuntimeError):
    """The converter failed to run (non-zero exit) or a path escaped its confinement."""

class HarnessEmitError(RuntimeError):
    ...

class DocsSyncError(RuntimeError):
    ...
```
Location: defined at the top of the package's primary module (`tools/golden_runner/runner.py:39`,
`tools/harness_emit/generate.py:51`, `tools/docs_sync/generate.py:47`). Raised for: a converter
subprocess failing, a path escaping its confinement, a HARD validation gate tripping before any
write (loud-fail, no partial writes).

**Refusal exceptions are a distinct shape from failure exceptions** — they subclass plain
`Exception` (not `RuntimeError`) because they are an *expected, structured* outcome (a human
gate not yet satisfied), not a bug:
```python
class GoldenApprovalRefused(Exception):
    """Promotion .received → .verified refused (missing human sign-off / ADR / received file)."""
```
CLI `main()` catches the refusal explicitly and maps it to exit 3:
```python
try:
    verified = promote(args.case, approve=args.approve, adr=args.adr, human_token=args.confirm)
except GoldenApprovalRefused as exc:
    print(str(exc))
    return 3
```

**Loud-fail, no partial writes.** Validation that can raise does so *before* any file write
(`tools/harness_emit/validate.py`: "Two HARD gates, both raising `HarnessEmitError` BEFORE any
write"). Never write-then-rollback.

**Subprocess spawns:** always a list argv, always `shell=False` — never build a shell string
from arguments (command-injection guard, called out repeatedly: `tools/golden_runner/runner.py`,
`tools/hooks/commit_gate.py`). Resolve the child binary via an **explicit absolute path**, never
a bare `PATH` lookup:
```python
def resolve_dotnet() -> str:
    root = os.environ.get("DOTNET_ROOT") or os.path.join(os.path.expanduser("~"), ".dotnet")
    return os.path.join(root, "dotnet")
```

## Path Confinement (`_confine`)

Every module that writes files outside a fixed, known location defines (or reuses the pattern
of) a `_confine(path, allowed_roots=None) -> Path` helper that resolves a path and verifies it
falls under an allowlist of roots, raising the package's own `*Error` on escape. Canonical
implementation, `tools/golden_runner/runner.py:88-110`:
```python
def _confine(path: Path, allowed_roots: tuple[Path, ...] | None = None) -> Path:
    """Resolve and confine a path to the repo, the system temp area, or a declared member root."""
    resolved = path.resolve()
    roots = (
        REPO_ROOT.resolve(),
        Path(os.path.realpath("/tmp")),
        Path(os.environ.get("TMPDIR", "/tmp")).resolve(),
    )
    if allowed_roots:
        roots = roots + tuple(Path(r).resolve() for r in allowed_roots)
    for root in roots:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    raise GoldenRunnerError(f"path escapes confinement (repo/temp/member): {resolved}")
```
- Base allowlist is always `(REPO_ROOT, /tmp, $TMPDIR)`.
- `allowed_roots` is an **additive** widening only — never remove the base roots.
- Other packages clone this shape verbatim under their own name/error class:
  `tools/harness_emit/generate.py` and `tools/harness_emit/manifest.py` /
  `project_skill.py` (confinement to `.opencode/` / `.claude/`), `tools/docs_sync/generate.py`
  (confinement to `docs/reference/`).
- When adding a new file-writing tool, copy this function (parametrize `REPO_ROOT` and the
  error class) rather than inventing a new confinement scheme.

## Determinism Discipline (derived-artifact writers)

Any module that writes a derived/generated artifact (`docs_sync`, `memory_regen`, `harness_emit`)
follows the same non-negotiable recipe, stated explicitly in each module's docstring:

- **No `datetime.now()` / timestamps / floats** in output — the only way to guarantee
  `generate → hash → delete → regenerate` is byte-identical.
- **LF line endings, no BOM, UTF-8** output.
- A **DERIVED "do not hand-edit" marker** as the first line of every generated file.
- Determinism is proven by a **committed syrupy snapshot**, never `git diff` (a target dir can
  be gitignored).

## Comments

- Module docstrings are load-bearing: they state the spec-ID tag, the invariant being protected,
  and *why* (not just what). Treat the docstring as documentation of a decision, not boilerplate.
- Inline comments explain the *risk being guarded against* (e.g. "an env limitation can NEVER
  silently disable a real gate (D-06 / Pitfall 3 / T-04-13)") — prefer this style over restating
  the code.
- No JSDoc-equivalent; Python docstrings (`"""..."""`) are the only documentation form, on
  modules, public functions, and dataclasses.

## Module Design

- **Exports:** no `__all__` convention observed; packages re-export selectively at the
  `__init__.py` level only where cross-package imports need it (e.g. `tools/contract_hash`
  exposes `CONTRACTS_DIR`, `MANIFEST_PATH`, `REPO_ROOT`, `build_manifest` for `contract_drift`
  to import).
- **No barrel files** beyond the package's own `__init__.py`.
- **Namespace-package members re-export lazily (PEP 562)** to avoid conftest-collection
  deadlock (stated in `harness/skills/python-conventions/SKILL.md`).

## Non-Negotiables (apply to every module you touch)

These are restated per-package in `AGENTS.md` files (root, `libs/python/AGENTS.md`,
`examples/log-parser/AGENTS.md`) rather than inherited-only, because different agent runtimes
merge nested `AGENTS.md` differently:

1. **Contract-first.** `contracts/**` is the single source of truth. Code that disagrees with a
   contract is wrong — fix the code. A contract change carries a paired golden + contract-drift
   gate update (schema-hash moving without a paired golden update fails CI).
2. **§4.3–4.6 polyglot boundary invariants** (only relevant when writing/reading a TSV wire
   file): UTF-8 with BOM stripped, forced LF, InvariantCulture `.` decimals, tolerance-aware
   float compare, deterministic key/row ordering, UTC ISO-8601 timestamps, explicit TSV
   escape + null-vs-empty token. Language boundary is process/file/DB only — never in-process
   object passing across Python/.NET.
3. **Constitution plane is gated.** Never write to `contracts/`, `docs/adr/`, or `golden/` from
   code or as an agent. These are human-owned/CODEOWNERS-gated; ADRs are append-only
   (supersede, never edit); nothing self-blesses a golden baseline.
4. **Derived plane is never hand-edited.** `.memory/derived/`, `docs/reference/`, `.opencode/`,
   `.claude/{agents,commands,skills}` are regenerated by `tools/memory_regen`, `tools/docs_sync`,
   `tools/harness_emit` respectively. Delete + rerun must reproduce them byte-identically.
   Decisions belong in append-only ADRs, never in a derived artifact.
5. **Lazy-load rule.** Do not preload full contract bodies into context; use the injected
   contracts-index / repo-map pointers and read a specific contract only when the task needs it.

---

*Convention analysis: 2026-07-14*
