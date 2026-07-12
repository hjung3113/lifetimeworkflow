"""permission-matrix.json → opencode.json 15-key permission block (EMIT-02 — the one transform).

This is the SINGLE genuine transform in the emitter: the authored CONFIG-02 matrix
(``harness/permission-matrix.json``) carries the 15 opencode permission keys PLUS two resolver-only
fields — ``_note`` (documentation) and ``path_deny_globs`` (path-scoped denies the Python resolver
enforces, since opencode's native ``edit`` key is not path-globbable). Neither is a valid opencode
``permission`` key, so :func:`build_permission_block` STRIPS both, projecting the exact 15 keys.

Last-wins is order-sensitive (Pitfall P3 / T-07-06): the ``bash`` sub-object is authored with the
catch-all ``*`` FIRST and specifics after, so a LATER pattern overrides an earlier one. That order
is SEMANTIC — it MUST survive the projection. :func:`dumps_config` therefore sorts keys everywhere
for determinism EXCEPT the ``bash`` value, which stays in authored insertion order.

The matrix is read through :func:`tools.harness_perms.resolver.load_matrix`, the SAME
order-preserving loader the Phase-4 hooks use — one loader, no second parse.
"""

from __future__ import annotations

import json

# The two resolver-only fields that are NOT valid opencode permission keys (stripped on projection).
_RESOLVER_ONLY_KEYS = ("_note", "path_deny_globs")


def build_permission_block(matrix: dict) -> dict:
    """Project the CONFIG-02 matrix into the opencode ``permission`` block — the 15 valid keys only.

    Strips ``_note`` + ``path_deny_globs`` (resolver-only data). Preserves the authored key order,
    so the ``bash`` sub-object keeps its ``*``-first last-wins ordering (P3 / T-07-06). Values pass
    through unchanged (``allow``/``ask``/``deny`` scalars and the ordered ``bash`` object).
    """
    return {key: value for key, value in matrix.items() if key not in _RESOLVER_ONLY_KEYS}


def _canonicalize(obj: object) -> object:
    """Recursively sort dict keys for deterministic output — EXCEPT a ``bash`` mapping value.

    A dict keyed ``bash`` keeps its AUTHORED insertion order (last-wins semantics, P3); every other
    mapping is re-keyed in sorted order so re-serialization is byte-stable (the ``emit-drift`` gate
    depends on it). Lists and scalars pass through unchanged.
    """
    if isinstance(obj, dict):
        out: dict = {}
        for key in sorted(obj):
            value = obj[key]
            if key == "bash" and isinstance(value, dict):
                out[key] = dict(value)  # authored order preserved — do NOT sort (last-wins, P3)
            else:
                out[key] = _canonicalize(value)
        return out
    if isinstance(obj, list):
        return [_canonicalize(item) for item in obj]
    return obj


def dumps_config(config: dict) -> str:
    """Serialize an opencode config to deterministic JSON (sorted keys, bash order kept) + final LF.

    ``json.dumps(..., indent=2)`` with a PRE-sorted structure (never ``sort_keys=True``, which would
    reorder the ``bash`` glob object and break last-wins). LF newlines, no BOM, no timestamp/float —
    so a second emit reproduces the file byte-for-byte.
    """
    return json.dumps(_canonicalize(config), indent=2, ensure_ascii=False) + "\n"
