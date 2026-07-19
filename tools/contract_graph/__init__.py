"""TOPO-04 graph compiler core — validation/resolution layer over effective_relationships().

Public API downstream consumers import::

    from tools.contract_graph import compile_graph

Re-export is LAZY (PEP 562 ``__getattr__``) on purpose: ``tools`` is a namespace package (no
``tools/__init__.py``) imported by module path, and an eager top-level import here would run during
pytest's conftest-collection bootstrap before the repo root is on ``sys.path``, breaking collection.
Deferring the submodule import until first attribute access keeps the convenient package-level API
without that ordering hazard (mirrors tools/harness_config + tools/harness_lint).
"""

from __future__ import annotations

__all__ = ["compile_graph"]


def __getattr__(name: str):  # PEP 562 — lazy re-export from the compile submodule.
    if name in __all__:
        from tools.contract_graph import compile

        return getattr(compile, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
