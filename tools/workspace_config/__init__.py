"""MREPO-01 workspace-manifest core — thin stdlib loader over the root workspace.toml (multi-repo SSOT).

Public API downstream consumers import::

    from tools.workspace_config import load_workspace, members, edges, split_endpoint

Re-export is LAZY (PEP 562 ``__getattr__``) on purpose: ``tools`` is a namespace package (no
``tools/__init__.py``) imported by module path, and an eager top-level import here would run during
pytest's conftest-collection bootstrap before the repo root is on ``sys.path``, breaking collection.
Deferring the submodule import until first attribute access keeps the convenient package-level API
without that ordering hazard (mirrors tools/harness_config).
"""

from __future__ import annotations

__all__ = ["edges", "load_workspace", "members", "split_endpoint"]


def __getattr__(name: str):  # PEP 562 — lazy re-export from the loader submodule.
    if name in __all__:
        from tools.workspace_config import loader

        return getattr(loader, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
