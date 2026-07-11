"""Thin stdlib loader over the GEN-03 project-config slot (D-03).

Reads ``harness/project.toml`` — the harness's language/toolchain SINGLE SOURCE OF TRUTH — with
stdlib ``tomllib`` (guaranteed by ``requires-python >=3.11``; no external dep). Pure I/O + shape:
NO enforcement logic (that belongs to the consistency test in ``tools.harness_lint``). Keep the
signatures stable — the Phase-6 config-derived CI matrix will import ``language_bash_scopes``.

Semantics:
  * ``load_project`` — parse the TOML into a plain dict (``instance`` table + ``languages`` list).
  * ``language_bash_scopes`` — the set of bash allow-scopes the participating languages imply: the
    union of each language's ``bash_scope`` PLUS the implicit ``"pytest *"`` (Python's test-runner
    carries its own permission-matrix allow-scope alongside ``uv *``). This is exactly the set the
    permission-matrix's language allow-scopes must equal (config = SSOT).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# Repo-root-anchored default so the loader works regardless of the caller's cwd.
# loader.py -> harness_config -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PROJECT = _REPO_ROOT / "harness" / "project.toml"

# Python's test runner carries its own permission-matrix allow-scope ("pytest *") distinct from the
# language's own "uv *" bash_scope. It is implicit in the config (not a per-language field) so the
# SSOT need not repeat it; the helper folds it into the derived scope set.
_IMPLICIT_TEST_SCOPES = frozenset({"pytest *"})


def load_project(path: str | Path = _DEFAULT_PROJECT) -> dict:
    """Load the GEN-03 project config (``harness/project.toml``) as a plain dict.

    Opens in **binary** mode (``tomllib.load`` requires it). Shared by the loader tests and the
    consistency gate so there is exactly one reader of the SSOT slot.
    """
    with Path(path).open("rb") as fh:
        return tomllib.load(fh)


def languages(cfg: dict | None = None) -> list[dict]:
    """Return the configured ``[[languages]]`` tables (loads the default config if omitted).

    Raw passthrough: legs MAY carry an optional ``test_paths`` list (consumed by the Phase-6 CI
    matrix via ``l.get("test_paths", [])``); it flows through unchanged with no signature change.
    """
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("languages", []))


def components(cfg: dict | None = None) -> list[dict]:
    """Return the configured ``[[components]]`` tables (loads the default config if omitted).

    Raw passthrough (mirrors ``languages()``): the pipeline-topology DATA slot flows through
    unchanged — NO enforcement here. The topology consistency gate
    (``tools/harness_lint/tests/test_pipeline_config.py``) owns the well-formedness checks.
    """
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("components", []))


def pipeline(cfg: dict | None = None) -> dict:
    """Return the ``[pipeline]`` table (loads the default config if omitted).

    Raw passthrough: the ``edges`` list (and any future additive keys) flow through unchanged.
    Consistency (endpoints declared, contract in produces/consumes) is enforced by the gate, not
    here.
    """
    if cfg is None:
        cfg = load_project()
    return dict(cfg.get("pipeline", {}))


def language_bash_scopes(cfg: dict | None = None) -> set[str]:
    """Return the derived set of bash allow-scopes: union of ``languages[*].bash_scope`` + implicit
    ``"pytest *"``. This is the set the permission-matrix language allow-scopes must equal."""
    scopes = {lang["bash_scope"] for lang in languages(cfg) if lang.get("bash_scope")}
    return scopes | set(_IMPLICIT_TEST_SCOPES)
