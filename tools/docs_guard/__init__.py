"""DOCSUP-01..05 human-doc review obligation guard — package public surface.

Public API downstream consumers import::

    from tools.docs_guard import compute, resolve, MissingSourceError
    from tools.docs_guard import load_registry, load_ledger, classify, impact_ids

Re-export is LAZY (PEP 562 ``__getattr__``) on purpose: ``tools`` is a namespace package (no
``tools/__init__.py``) imported by module path, and an eager top-level import here would run during
pytest's conftest-collection bootstrap before the repo root is on ``sys.path``, breaking collection.
Deferring the submodule import until first attribute access keeps the convenient package-level API
without that ordering hazard (mirrors tools/harness_config + tools/harness_perms).

**The surface below is frozen up front, deliberately.** It names every export of the whole phase,
including submodules that have not landed yet, so that the plans adding those submodules add FILES
only and never edit this one — an edit here would be a same-wave file conflict. Consequence: within
the phase, accessing a name whose submodule has not landed yet raises ``ModuleNotFoundError`` (not
``AttributeError``). That is a transient, within-phase condition, not a bug.

The freeze above was a PHASE 28 arrangement; Phase 29 extended the map with ``exclusions``
(DOCSUP-06).
"""

from __future__ import annotations

# Export name -> the submodule that owns it. Frozen for the whole phase (see docstring).
_SUBMODULE_OF: dict[str, str] = {
    # digest.py — the deterministic source+target digest.
    "MissingSourceError": "digest",
    "compute": "digest",
    "resolve": "digest",
    # registry.py — docs/doc-dependencies.toml loader + validation.
    "RegistryError": "registry",
    "load_registry": "registry",
    # ledger.py — the committed review ledger + disposition/digest coherence.
    "LedgerError": "ledger",
    "check_coherence": "ledger",
    "load_ledger": "ledger",
    "previous_ledger": "ledger",
    # guard.py — the five-state classifier.
    "STATES": "guard",
    "classify": "guard",
    # impact.py — contract-graph impact ids (ids only, never fabricated).
    "impact_ids": "impact",
    "impact_map": "impact",
    # exclusions.py — the DOCSUP-06 drafting exclusions (Phase 29).
    "REASON_ACCEPTED_ADR": "exclusions",
    "REASON_CONSTITUTION": "exclusions",
    "REASON_DERIVED": "exclusions",
    "exclusion_reason": "exclusions",
}

__all__ = sorted(_SUBMODULE_OF)


def __getattr__(name: str):  # PEP 562 — lazy re-export from the owning submodule.
    submodule = _SUBMODULE_OF.get(name)
    if submodule is not None:
        if submodule == "digest":
            from tools.docs_guard import digest as module
        elif submodule == "registry":
            from tools.docs_guard import registry as module  # type: ignore[no-redef]
        elif submodule == "ledger":
            from tools.docs_guard import ledger as module  # type: ignore[no-redef]
        elif submodule == "guard":
            from tools.docs_guard import guard as module  # type: ignore[no-redef]
        elif submodule == "exclusions":
            from tools.docs_guard import exclusions as module  # type: ignore[no-redef]
        else:
            from tools.docs_guard import impact as module  # type: ignore[no-redef]
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
