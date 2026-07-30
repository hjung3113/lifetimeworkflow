"""MONO-04 contract -> owning-package attribution — a PURE lookup, not a traversal.

``owning_package(packages, contract_path)`` answers "given a contract path, which package owns
it?" using the nearest-enclosing-package-folder rule (CONTEXT.md "Override slot & contract
ownership"): the winner is the package whose ``"dir"`` is the deepest ancestor of
``contract_path``, falling back to the root package (``dir == "."``) when no other package
encloses the path.

This module does NOT touch ``compile.py``'s adjacency or call any of ``query.py``'s one-hop or
reachability functions — it is a sibling pure-lookup utility mirroring ``compile.py``'s
``_tracked_schemas`` glob-existence idiom (path-string comparison, no graph, no second traversal
engine). It also never imports ``tools.memory_regen.package_facts`` itself: the caller passes
``build_facts()["packages"]`` in, keeping this module dependency-free.

The root-package fallback is a DELIBERATE, ratified consequence of "no manifest exists between an
instance's own contracts folder and its own root" (CONTEXT.md "Resolved after research") — not
a bug. It is asserted explicitly by this module's test suite using a synthetic instance-style
fixture path, never a literal live example path (GEN-04).
"""

from __future__ import annotations

from pathlib import PurePosixPath

__all__ = ["owning_package"]


def owning_package(packages: list[dict], contract_path: str) -> str:
    """Return the id of the package that owns ``contract_path``.

    ``packages`` is ``[{"id": str, "dir": str, ...}, ...]`` (only ``"id"`` and ``"dir"`` are
    read; extra keys such as ``"manifest"``/``"language"`` from ``build_facts()`` are ignored).
    Each package's ``"dir"`` is a POSIX-relative folder path — ``"."`` for the repo root, or
    e.g. ``"tools/contract_graph"`` for a nested package.

    A package "encloses" ``contract_path`` when the path's parts start with that package's
    ``dir``'s parts (the ``dir="."`` package encloses every path, since every path's parts start
    with the empty parts sequence). Among all enclosing packages, the WINNER is the one whose
    ``dir`` has the most path segments (the nearest/deepest ancestor). Ties (two packages
    declaring the identical ``dir``) are broken by sorted ``"id"`` — deterministic, never
    dict/set-iteration-order dependent.

    Raises ``ValueError`` naming ``contract_path`` if no package encloses it (this can only
    happen when ``packages`` omits a root (``dir == "."``) package — a malformed input for any
    realistic caller, since a root package always exists in practice). Never fabricates an owner.
    """
    path_parts = PurePosixPath(contract_path).parts

    enclosing: list[dict] = []
    for package in packages:
        dir_parts = () if package["dir"] == "." else PurePosixPath(package["dir"]).parts
        if path_parts[: len(dir_parts)] == dir_parts:
            enclosing.append(package)

    if not enclosing:
        raise ValueError(
            f"owning_package: no package (not even a root package with dir='.') encloses "
            f"{contract_path!r}"
        )

    def _depth(package: dict) -> int:
        return 0 if package["dir"] == "." else len(PurePosixPath(package["dir"]).parts)

    enclosing.sort(key=lambda package: (-_depth(package), package["id"]))
    return enclosing[0]["id"]
