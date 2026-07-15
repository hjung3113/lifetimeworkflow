"""Thin stdlib loader over the MREPO-01 workspace-manifest slot (model b).

Reads the root ``workspace.toml`` — the multi-repo SINGLE SOURCE OF TRUTH — with stdlib ``tomllib``
(guaranteed by ``requires-python >=3.11``; no external dep). Pure I/O + shape: NO enforcement logic
(that belongs to the consistency gate in ``tools.harness_lint.tests.test_workspace_config``). This
is the GEN-03 loader shape (``tools/harness_config/loader.py``) raised ONE level: a workspace sits
above a single project.

Semantics:
  * ``load_workspace`` — parse the TOML into a plain dict (``workspace`` table + ``members`` list +
    ``pipeline`` table).
  * ``members`` / ``edges`` — raw passthrough accessors (mirror ``harness_config.languages`` /
    ``pipeline``): each loads the default manifest if omitted and returns a list.
  * ``split_endpoint`` — parse a ``repo:stage`` edge endpoint into ``(repo, stage)``; a bare
    ``stage`` (no colon) → ``(None, stage)`` (single-repo, backward-compatible with the Phase-8
    core/instance topology whose endpoints carry no repo half).

The loader MUST NOT hardcode any member path — it reads ``workspace.toml`` at runtime, so it carries
no member-root token and passes the GEN-04 core→workspace-member guard cleanly (Pitfall 3).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# Repo-root-anchored default so the loader works regardless of the caller's cwd.
# loader.py -> workspace_config -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_WORKSPACE = _REPO_ROOT / "workspace.toml"


def load_workspace(path: str | Path = _DEFAULT_WORKSPACE) -> dict:
    """Load the MREPO-01 workspace manifest (``workspace.toml``) as a plain dict.

    Opens in **binary** mode (``tomllib.load`` requires it). Shared by the loader tests and the
    consistency gate so there is exactly one reader of the SSOT slot.
    """
    with Path(path).open("rb") as fh:
        return tomllib.load(fh)


def members(cfg: dict | None = None) -> list[dict]:
    """Return the configured ``[[members]]`` tables (loads the default manifest if omitted).

    Raw passthrough: each member carries an ``id`` + ``root`` (repo-relative path); a future
    milestone MAY add ``url`` for a remote root — it flows through unchanged with no signature
    change. NO enforcement here (the gate owns uniqueness / existence).
    """
    if cfg is None:
        cfg = load_workspace()
    return list(cfg.get("members", []))


def edges(cfg: dict | None = None) -> list[dict]:
    """Return the ``[pipeline].edges`` list (loads the default manifest if omitted).

    Raw passthrough (mirrors ``harness_config.pipeline`` edge access): each edge carries
    ``from``/``to`` ``repo:stage`` endpoints + a ``contract`` id. Consistency (endpoints declared,
    contract tracked in the producer) is enforced by the gate, not here.
    """
    if cfg is None:
        cfg = load_workspace()
    return list(cfg.get("pipeline", {}).get("edges", []))


def split_endpoint(endpoint: str) -> tuple[str | None, str]:
    """Parse a pipeline edge endpoint into ``(repo, stage)``.

    ``"repo:stage"`` → ``("repo", "stage")`` — the repo half resolves the member root (MREPO-03),
    the stage half is the pipeline endpoint (MREPO-04). A bare ``"stage"`` (no colon) →
    ``(None, "stage")``, keeping the Phase-8 single-repo endpoints backward-compatible.
    """
    if ":" in endpoint:
        repo, stage = endpoint.split(":", 1)
        return repo, stage
    return None, endpoint
