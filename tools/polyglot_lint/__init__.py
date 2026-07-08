"""POLY-01 polyglot-boundary linter (D-03) — the shared §4.3-4.6 rule engine.

Public API the Phase-4 on-write (HOOK-04) / commit-gate (HOOK-03) hooks import unchanged::

    from tools.polyglot_lint import lint_bytes, lint_tsv, lint_file

Re-export is LAZY (PEP 562 ``__getattr__``), mirroring tools/harness_perms: ``tools`` is a
namespace package (no ``tools/__init__.py``) imported by module path, and lint.py runs a
``sys.path`` shim + a top-level ``from normalize.core import ...`` at import time. Deferring the
submodule import until first attribute access keeps the convenient package-level API without
forcing that shim to run during pytest's conftest-collection bootstrap.
"""

from __future__ import annotations

__all__ = ["Violation", "lint_bytes", "lint_file", "lint_tsv", "main"]


def __getattr__(name: str):  # PEP 562 — lazy re-export from the lint submodule.
    if name in __all__:
        from tools.polyglot_lint import lint

        return getattr(lint, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
