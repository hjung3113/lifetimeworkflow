# Technology Stack

**Analysis Date:** 2026-07-14

## Scope Note

This document covers the **harness core**: `tools/**`, `harness/**`, `libs/**`, `contracts/**`, `.github/workflows/*.yml`, and root config (`pyproject.toml`, `uv.lock`, `AGENTS.md`, `CLAUDE.md`). The reference instance `examples/log-parser/` (which adds .NET 10 + a domain normalize twin) is a secondary, domain-specific consumer of the core and is not deep-dived here — see `examples/log-parser/AGENTS.md`. The `.opencode/` and `.claude/` trees are **generated output**, not source — they are byte-emitted from `harness/` by `tools/harness_emit` and must never be hand-edited (enforced by the `emit-drift` CI job).

## Languages

**Primary:**
- Python 3.11 (`requires-python = ">=3.11"` in `pyproject.toml`, root and every workspace member) - all harness tooling: `tools/**`, `libs/python/**`
- TypeScript (Node, `commonjs` module type per `.claude/package.json`) - opencode plugin adapters: `harness/plugins/*.ts`

**Secondary (instance-supplied, reference only):**
- .NET 10 / C# - parser/converter language for the `examples/log-parser` instance (`examples/log-parser/libs/dotnet/`); declared as a config *slot* in `harness/project.toml`, not a core dependency
- Bash - CI glue, git hooks (`harness/git-hooks/pre-commit`), toolchain bootstrap (`tools/bootstrap/install.sh`)

## Runtime

**Environment:**
- Python 3.11.15 (CPython), resolved via the committed `.venv/pyvenv.cfg` (`prompt = logparser-harness`)
- No system-wide `.NET` in the container by default — `tools/bootstrap/install.sh` installs .NET 10 SDK to `$DOTNET_ROOT` (`$HOME/.dotnet`) via `dotnet-install.sh --channel 10.0` on every SessionStart (idempotent, cache-checked)
- No `.python-version` file present; Python version is pinned via `requires-python` only

**Package Manager:**
- **uv** 0.11.27 (per `.venv/pyvenv.cfg`) — Cargo-style workspace manager
- Lockfile: `uv.lock` present at repo root (single lockfile across the whole workspace)
- Workspace root is a **virtual project** (`[tool.uv] package = false` in root `pyproject.toml`) — the root itself is never built/packaged, only its dependency groups are installed into the shared environment

**uv Workspace Members** (`[tool.uv.workspace]` in root `pyproject.toml`):
- `members = ["libs/python", "tools/*"]`
- `exclude = ["tools/bootstrap"]` (shell-only dir, no `pyproject.toml`, would break `uv sync` if included)
- Every member under `tools/*` is a **virtual member** (`package = false`, no build-system, no wheel built) — each is invoked as `python -m tools.<name>.<entry>`, imported by module path from the shared environment
- `sync` in CI uses `uv sync --all-packages` (a bare `uv sync` would prune tool-member-only deps like `tree-sitter`/`networkx`)

## Frameworks / Toolchain

**Testing:**
- `pytest` >=8.4,<9 (dev group, root `pyproject.toml`) — pinned **below 9.x** deliberately: syrupy 5.2.0 compatibility with pytest 9 is unverified (see comment in `pyproject.toml` and `CLAUDE.md` §Version Compatibility)
- `syrupy` ==5.2.0 — snapshot/golden testing for Python-side fixtures
- `[tool.pytest.ini_options]`: `testpaths = ["libs/python", "tools"]`, `python_files = ["test_*.py", "*_test.py"]`, `addopts = "-ra"`, `minversion = "8.4"`
- Per-`tools/*` member: tests live in a sibling `tests/` dir (e.g. `tools/harness_lint/tests/`, `tools/contract_drift/tests/`)

**Lint/Format:**
- `ruff` ~=0.15 — lint + format, single config in root `pyproject.toml`
  - `[tool.ruff]`: `line-length = 100`, `target-version = "py311"`, `extend-exclude = [".dotnet", ".venv", "bin", "obj"]`
  - `[tool.ruff.lint]`: `select = ["E", "F", "I", "UP", "B"]`
- `pyright` ==1.1.409 — static type checker, `typeCheckingMode = "standard"`, `pythonVersion = "3.11"`, excludes `.dotnet`/`.venv`/`bin`/`obj`/`__pycache__`

**Schema validation:**
- `jsonschema` ==4.26.0 (root runtime dependency) — Draft 2020-12 validation, used by `tools/harness_lint` (e.g. the hermetic `opencode.json` schema gate)
- `check-jsonschema` ==0.37.4 (dev group) — CLI wrapper used by CI's `contract-check` job and `/contract-check`

**Contract-hash / drift toolchain:**
- `rfc8785` ==0.1.4 (root runtime dependency + `tools/contract_hash`, `tools/contract_drift`) — RFC 8785 (JCS) canonicalization for schema-hash SHA-256 baselines (never hand-rolled — see `libs/python/AGENTS.md` / `CLAUDE.md` "Don't Hand-Roll")

**Derived-memory toolchain** (`tools/memory_regen` only — declared there, not root, so other members' locks stay clean):
- `tree-sitter` ==0.25.2
- `tree-sitter-python` ==0.25.0
- `tree-sitter-c-sharp` ==0.23.5
- `tree-sitter-bash` ==0.25.1
- `networkx` ==3.6.1
- Used for the tree-sitter + personalized-PageRank repo-map generator (`tools/memory_regen/repo_map.py`, gitignored output `.memory/derived/repo-map.md`)

**opencode plugin runtime (TypeScript):**
- `@opencode-ai/plugin` / `@opencode-ai/sdk` (implied by `harness/plugins/*.ts` authoring against the opencode hook API — `execFileSync` from `node:child_process`, no other npm deps observed in-repo)
- `.claude/package.json` declares only `{"type": "commonjs"}` — no dependency manifest for the plugin layer was found at the harness-core level; plugin `.ts` sources are **authored but execution-deferred** (no opencode runtime present in this container — see RESUME NOTE comments in `harness/plugins/session-inject.ts` and `harness/plugins/contract-guard.ts`)

## Key Dependencies

**Critical (root `[project.dependencies]`):**
- `rfc8785` ==0.1.4 - canonical JSON serialization for the contract-hash drift gate (schema-hash SSOT)
- `jsonschema` ==4.26.0 - Draft 2020-12 contract/config validation

**Per-tool-member declared deps (all `[tool.uv] package = false`, virtual members):**
- `tools/contract_hash`: `rfc8785==0.1.4`
- `tools/contract_drift`: `rfc8785==0.1.4`
- `tools/memory_regen`: `tree-sitter`, `tree-sitter-python`, `tree-sitter-c-sharp`, `tree-sitter-bash`, `networkx` (exact pins above)
- `tools/docs_sync`, `tools/golden_runner`, `tools/harness_config`, `tools/harness_emit`, `tools/harness_lint`, `tools/harness_perms`, `tools/hooks`, `tools/polyglot_lint`, `tools/strangler_guard`, `tools/workspace_config`: **zero declared deps** — deliberately stdlib-only (or reuse shared workspace resolvers) to avoid mutating `uv.lock`

**Language-neutral normalize core:**
- `libs/python/normalize` (`libs/python/normalize/core.py`) - stdlib-only (`decimal`/`codecs`/`datetime`) implementation of the §4.3–4.6 polyglot boundary invariants (BOM strip, LF, InvariantCulture decimal, tolerance float compare, UTC ISO-8601, TSV null/escape). Cross-validated against `libs/normalize-fixtures/*.json` (`bom_crlf.json`, `decimal_locale.json`, `null_vs_empty.json`, `tz_iso8601.json`).

## Configuration

**Environment:**
- No `.env` handling observed in the harness core (contracts/config are plain TOML/JSON/Markdown, no secrets management library)
- `harness/project.toml` — the **language/toolchain SSOT slot** (`[instance]` root + `[[languages]]` + `[[components]]`/`[pipeline]` topology); read by `tools/harness_config/loader.py` (stdlib `tomllib`)
- `workspace.toml` — the **multi-repo workspace manifest** (member repos + cross-repo contract edges), one level above `harness/project.toml`; read by `tools/workspace_config` (stdlib `tomllib`)
- `harness/permission-matrix.json` — the 15-key opencode permission data (`bash` last-wins glob scopes, `path_deny_globs` for constitution-plane paths); read by `tools/harness_perms/resolver.py`
- `opencode.json` (repo root) — the emitted opencode runtime config: formatter commands (`dotnet format`, `ruff format`), `instructions` (AGENTS.md pointers only, never contract payloads), permission matrix mirror, and `plugin: ["harness/plugins/session-inject.ts"]`. `model`/`small_model` are **placeholder tier tokens** (`provider/implementer-tier`, `provider/explorer-tier`) — never real model IDs, per the model-identity constraint.

**Build:**
- No compiled build step for the Python tooling (`package = false` everywhere — modules run in place via `python -m`)
- `tools/harness_emit` is the single-source → dual-runtime **generator**: reads `harness/**` and writes `.opencode/**` + the harness slice of `.claude/{agents,commands,skills}` byte-for-byte; CI's `emit-drift` job re-runs it and fails on any diff

## Platform Requirements

**Development:**
- Remote **ephemeral** container — no persistent state assumed between sessions; `tools/bootstrap/install.sh` self-bootstraps .NET 10 + `uv sync --all-packages` on every SessionStart (idempotent, cache-checked, non-fatal on transient failure)
- Python 3.11+ required; `uv` required for all workspace operations (`uv run pytest`, `uv sync`, etc.)
- Working branch: `claude/data-pipeline-harness-8aypct`

**CI/Production:**
- GitHub Actions (`ubuntu-latest` runners) — see `INTEGRATIONS.md` for the full job breakdown
- `astral-sh/setup-uv@v8.3.2` for the Python toolchain, `actions/setup-dotnet@v5.4.0` (`dotnet-version: '10.0.100'`) for the .NET leg (example-instance only)
- No deployment target — this repo IS the harness/tooling artifact, not a deployed service

---

*Stack analysis: 2026-07-14*
