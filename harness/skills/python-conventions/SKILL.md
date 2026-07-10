---
name: python-conventions
description: >-
  Use when writing or reviewing Python code in libs/python or tools (the scheduler/collector
  side and the harness tooling). Covers the uv workspace and lockfile discipline, ruff
  lint+format, pyright typing, pytest + syrupy testing, and module-path (`uv run python -m ...`)
  invocation.
---

# python-conventions

How Python code is written in this monorepo. The Python side owns the scheduler, collector, and
the harness tooling (`tools/*`); it crosses the language boundary only via process/file/DB.

## Env & dependencies

- **uv workspace** — one root `pyproject.toml`, one lockfile. Run everything through uv:
  `uv run pytest`, `uv run python -m tools.<pkg> ...`.
- Add deps with `uv add` (or `uv add --package <member> <pkg>`). Never pip/poetry/pyenv; never
  hand-edit `uv.lock`.
- Each new `tools/*` member needs its own `pyproject.toml` or `uv sync` prunes it. Bootstrap runs
  `uv sync --all-packages`.

## Quality gates

- **Tests:** `uv run pytest` (full) or `uv run pytest libs/python -x -q` (scoped). Prove
  determinism of derived artifacts with **syrupy** snapshots (see golden-testing).
- **Lint + format:** **ruff** (lint AND format — replaces black/isort/flake8). One config in
  `pyproject.toml`.
- **Types:** **pyright** (LSP-native), not mypy.
- Pin pytest to `>=8.4,<9` for now; syrupy 5.2.0. Do not adopt Astral `ty` yet.

## Idioms

- Invoke tools by module path (`python -m tools.golden_runner.runner`), not by file path — it
  keeps the uv workspace import graph honest.
- Subprocess spawns use a list argv with `shell=False` — never build a shell string from
  arguments (command-injection guard).
- Namespace-package members re-export lazily (PEP 562) to avoid conftest-collection deadlock.
- Stdlib-first for the normalization core (`decimal`/`codecs`/`datetime`).

## Non-negotiables

Contract-first; never write the constitution plane (`contracts/`, `docs/adr/`, `golden/`) from
Python; derived plane (`.memory/derived/`) is regenerated, never hand-edited. See
`libs/python/AGENTS.md` for the self-sufficient per-package rules.

## Deeper reference

Keep extended recipes (a syrupy determinism test, a uv member scaffold) under `references/` —
the body stays scannable (progressive disclosure).
