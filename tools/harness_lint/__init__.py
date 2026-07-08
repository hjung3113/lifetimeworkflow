"""Structural validators for the harness/ single source (D-02/D-04/D-07).

Public API downstream lints import::

    from tools.harness_lint import parse_frontmatter

Re-export is LAZY (PEP 562 ``__getattr__``) on purpose: ``tools`` is a namespace package (no
``tools/__init__.py``) imported by module path, and an eager top-level import here would run during
pytest's conftest-collection bootstrap before the repo root is on ``sys.path``, breaking collection.
Deferring the submodule import until first attribute access keeps the convenient package-level API
without that ordering hazard (mirrors tools/harness_perms).
"""

from __future__ import annotations

__all__ = ["parse_frontmatter"]


def __getattr__(name: str):  # PEP 562 — lazy re-export from the frontmatter submodule.
    if name in __all__:
        from tools.harness_lint import frontmatter

        return getattr(frontmatter, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
