"""GEN-03 project-config core (D-03) — thin stdlib loader over harness/project.toml (language SSOT).

Public API downstream consumers import::

    from tools.harness_config import load_project, languages, language_bash_scopes, components, pipeline

Re-export is LAZY (PEP 562 ``__getattr__``) on purpose: ``tools`` is a namespace package (no
``tools/__init__.py``) imported by module path, and an eager top-level import here would run during
pytest's conftest-collection bootstrap before the repo root is on ``sys.path``, breaking collection.
Deferring the submodule import until first attribute access keeps the convenient package-level API
without that ordering hazard (mirrors tools/harness_perms + tools/harness_lint).
"""

from __future__ import annotations

__all__ = ["components", "language_bash_scopes", "languages", "load_project", "pipeline"]


def __getattr__(name: str):  # PEP 562 — lazy re-export from the loader submodule.
    if name in __all__:
        from tools.harness_config import loader

        return getattr(loader, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
