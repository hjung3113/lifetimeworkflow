"""CONFIG-02 permission core (D-03) — pure last-wins bash resolver + path-deny resolver.

Public API the Phase-4 contract-guard / secret hooks import unchanged::

    from tools.harness_perms import resolve_bash, resolve_path, load_matrix

Re-export is LAZY (PEP 562 ``__getattr__``) on purpose: ``tools`` is a namespace package
(no ``tools/__init__.py``) imported by module path, and an eager top-level import here would
run during pytest's conftest-collection bootstrap before the repo root is on ``sys.path``,
breaking collection. Deferring the submodule import until first attribute access keeps the
convenient package-level API without that ordering hazard.
"""

from __future__ import annotations

__all__ = ["load_matrix", "resolve_bash", "resolve_path"]


def __getattr__(name: str):  # PEP 562 — lazy re-export from the resolver submodule.
    if name in __all__:
        from tools.harness_perms import resolver

        return getattr(resolver, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
