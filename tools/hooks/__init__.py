"""Runtime gate package (HOOK-01..05 plus the resume-attestation gate).

Hosts the shared Claude hook-stdin adapter (``_stdin``) and the gate modules that import it
(``secret_scan`` here; contract-guard / boundary / stop gates in plans 03-05). Public API::

    from tools.hooks import parse_event, emit_deny, emit_block

Re-export is LAZY (PEP 562 ``__getattr__``), mirroring ``tools.harness_perms``: ``tools`` is a
namespace package imported by module path, and an eager top-level import here would run during
pytest's conftest-collection bootstrap before the repo root is on ``sys.path``. Deferring the
submodule import until first attribute access keeps the convenient package-level API without that
ordering hazard.
"""

from __future__ import annotations

__all__ = ["Event", "emit_block", "emit_deny", "parse_event", "read_stdin"]


def __getattr__(name: str):  # PEP 562 — lazy re-export from the _stdin submodule.
    if name in __all__:
        from tools.hooks import _stdin

        return getattr(_stdin, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
