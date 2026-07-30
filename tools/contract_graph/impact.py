"""MONO-08 impact reporter — composes, never re-implements, the existing traversal/attribution layers.

``report(contract_path, cfg=None, graph=None, facts=None)`` answers "what does changing this
contract reach?" by composing three already-shipped engines: ``tools.contract_graph.query``'s
``direct``/``reverse``/``transitive`` over ``tools.contract_graph.compile.compile_graph()``'s
adjacency, ``tools.harness_config.loader``'s ``effective_relationships()``/``effective_packages()``,
and ``tools.contract_graph.ownership.owning_package()``. This module defines NO independent
traversal of its own — mirroring ``ownership.py``'s own "pure lookup, not a traversal" posture, the
inverse discipline applies here: every id-set this module returns comes from calling one of the
three query functions by name; it never walks ``graph["adjacency"]`` itself to derive a reachable
set.

A graph node in this codebase is a component/member id (e.g. ``"source"``, ``"parser"``) — never a
contract path or contract id (``compile.py``'s adjacency is keyed by ``rel["authority"]`` /
``rel["dependents"]``). The one genuinely new piece of logic this module adds is
``_resolve_node``: validate the path is not absolute and carries no ``..`` traversal segment (CR-01,
49-REVIEW.md), derive a contract id from the validated path's filename (mirrors ``compile.py``'s
``_tracked_schemas`` suffix-strip idiom), scan ``effective_relationships()`` for the record naming
that contract, and take its ``authority`` as the node — or accept ``contract_path`` directly when it
is already a DECLARED component or member id (CR-02, 49-REVIEW.md — checked against
``components()``/``members()``, never against ``compile_graph()``'s ``adjacency``, which omits
every legitimately isolated, zero-dependent node).

An unresolved contract path produces a report shape with a DIFFERENT key set than a resolved report
(``"resolved": False`` plus only ``contract_path``/``contract_id``/``searched`` — no ``"node"``, no
``"isolated"``, no traversal keys). This is deliberate: a pre-edit evidence step that collapses
"could not resolve your contract" into "resolved, nothing affected" is the dangerous failure mode
CONTEXT.md warns against. Resolved-but-isolated (``"isolated": True``, zero neighbours in all three
directions) and resolved-with-affected-set (``"isolated": False``) share the SAME key set — the
distinction there is a real, meaningful boolean, not a shape difference — because both are
legitimately resolved answers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath

from tools.contract_graph.compile import compile_graph
from tools.contract_graph.ownership import owning_package
from tools.contract_graph.query import direct, reverse, transitive
from tools.harness_config.loader import (
    components,
    effective_packages,
    effective_relationships,
    languages,
    load_project,
)
from tools.workspace_config import members

__all__ = ["report", "main"]


def _normalize_contract_path(contract_path: str) -> str | None:
    """Return a POSIX-normalized ``contract_path``, or ``None`` if it escapes containment.

    CR-01 (49-REVIEW.md): the pre-fix ``_resolve_node`` derived a contract id purely from the
    path's final filename component, so any path that merely *ended* in the right leaf name —
    including a wrong-directory typo or a ``../`` traversal — resolved identically to the real
    contract and returned a fully-confident report for the WRONG contract. This is the minimum
    fix the review names explicitly: refuse any path that is absolute or contains a ``..``
    segment BEFORE a candidate id is ever derived from it, so a traversal payload can never reach
    the filename-matching step at all. (A stronger fix — matching the full path against the real
    tracked ``contracts/**/<id>.schema.json`` glob — is not applied here because relationship
    records only carry a bare contract id, not a directory; see the module docstring.)
    """
    normalized = contract_path.replace("\\", "/")
    p = PurePosixPath(normalized)
    if p.is_absolute():
        return None
    if ".." in p.parts:
        return None
    return str(p)


def _resolve_node(
    contract_path: str,
    relationships: list[dict],
    component_ids: set[str],
    member_ids: set[str],
) -> tuple[str | None, str | None, str | None]:
    """Resolve ``contract_path`` (or a bare node id) to ``(node, contract_id, safe_path)``.

    First tries contract-id resolution: reject the path outright (CR-01) if it is absolute or
    contains a ``..`` traversal segment; otherwise derive ``candidate_id`` from the normalized
    path's filename (the exact suffix-strip idiom ``compile.py:46`` already uses) and scan
    ``relationships`` for the record whose ``"contract"`` matches — on a hit, the record's
    ``"authority"`` IS the node, and ``safe_path`` is the normalized path (safe to hand to
    ``owning_package()`` — see WR-03).

    If no relationship names the contract, fall back to bare-node-id resolution: ``contract_path``
    is accepted directly as the node when it names a DECLARED component or member id
    (``component_ids`` / ``member_ids`` — CR-02). ``compile_graph()``'s ``adjacency`` is NOT used
    for this check: it only ever contains an authority with at least one resolved dependent, so a
    legitimately isolated node (zero dependents, zero references) is never a key or value there —
    checking membership in ``adjacency`` falsely refuses every isolated node when addressed by its
    bare id, even though the identical node resolves fine via its contract path.

    Returns ``(None, candidate_id, None)`` when neither resolves (``candidate_id`` is ``None`` too
    when the path itself was rejected by the CR-01 containment check).
    """
    normalized = _normalize_contract_path(contract_path)
    candidate_id = None
    if normalized is not None:
        candidate_id = Path(normalized).name.removesuffix(".schema.json")
        for rel in relationships:
            if rel["contract"] == candidate_id:
                return rel["authority"], candidate_id, normalized

    if contract_path in component_ids or contract_path in member_ids:
        return contract_path, None, None

    return None, candidate_id, None


def report(
    contract_path: str,
    cfg: dict | None = None,
    graph: dict | None = None,
    facts: dict | None = None,
) -> dict:
    """Report the affected contracts/packages/owners for a change to ``contract_path``.

    ``contract_path`` may be a path under ``contracts/`` (resolved to its graph node via a
    declared relationship) or a bare node id (accepted directly when already present in the
    graph). Follows the repo's injectable-pure-function convention (``cfg``/``graph``/``facts``
    default to the real repo, but tests inject synthetic data with no monkeypatching).

    Refusal shape (unresolved): ``{"resolved": False, "contract_path", "contract_id", "searched"}``
    — no traversal keys at all.

    Resolved shape: ``{"resolved": True, "contract_path", "contract_id", "node", "isolated",
    "direct", "reverse", "transitive", "affected_contracts", "affected_packages",
    "contract_owner", "owners"}``. All sets/lists sorted — byte-identical on repeat invocation.
    """
    if cfg is None:
        cfg = load_project()

    relationships = effective_relationships(cfg)
    if graph is None:
        graph = compile_graph(cfg)

    component_by_id = {c["id"]: c for c in components(cfg)}
    member_by_id = {m["id"]: m for m in members(cfg)}

    node, contract_id, safe_path = _resolve_node(
        contract_path, relationships, set(component_by_id), set(member_by_id)
    )

    if node is None:
        return {
            "resolved": False,
            "contract_path": contract_path,
            "contract_id": contract_id,
            "searched": len(relationships),
        }

    d = direct(graph, node)
    r = reverse(graph, node)
    t = transitive(graph, node)
    node_set = {node} | set(d["ids"]) | set(r["ids"]) | set(t["ids"])
    isolated = d["ids"] == [] and r["ids"] == [] and t["ids"] == []

    affected_contracts = sorted(
        {
            rel["contract"]
            for rel in relationships
            if rel["authority"] in node_set or set(rel["dependents"]) & node_set
        }
    )

    pkgs = effective_packages(cfg, facts)
    # ADAPTER: reuse the exact "dir"-key filter conventions_for() applies (loader.py:330-338) —
    # owning_package() reads package["dir"] unconditionally; never call it on an unfiltered list.
    dir_pkgs = [p for p in pkgs if "dir" in p]
    affected_packages = sorted({p["id"] for p in dir_pkgs if p["id"] in node_set})

    # WR-03 (49-REVIEW.md): only ever pass `safe_path` — the CR-01-validated, normalized path —
    # to owning_package(), never the raw `contract_path`. Its root-package fallback matches EVERY
    # path (including an absolute path or a `../` traversal), so a confident non-null
    # `contract_owner` must never be attributed from an unvalidated string.
    contract_owner: str | None = None
    if contract_id is not None and safe_path is not None:
        try:
            contract_owner = owning_package(dir_pkgs, safe_path)
        except ValueError:
            contract_owner = None

    language_by_id = {lang["id"]: lang for lang in languages(cfg)}
    owners: dict[str, str | None] = {}
    for node_id in sorted(node_set):
        comp = component_by_id.get(node_id)
        lang_id = comp.get("language") if comp else None
        lang = language_by_id.get(lang_id) if lang_id is not None else None
        owners[node_id] = lang.get("persona") if lang else None

    return {
        "resolved": True,
        "contract_path": contract_path,
        "contract_id": contract_id,
        "node": node,
        "isolated": isolated,
        "direct": d,
        "reverse": r,
        "transitive": t,
        "affected_contracts": affected_contracts,
        "affected_packages": affected_packages,
        "contract_owner": contract_owner,
        "owners": owners,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m tools.contract_graph.impact <contract-path-or-node-id>``.

    Prints ``json.dumps(result, indent=2, sort_keys=True)`` to stdout — ``sort_keys`` is the
    determinism proof's mechanism (byte-identical regardless of internal dict-construction order).
    Returns ``0`` when resolved, ``1`` on clean refusal, ``2`` on missing argument.
    """
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(
            "usage: python -m tools.contract_graph.impact <contract-path-or-node-id>",
            file=sys.stderr,
        )
        return 2

    result = report(argv[0])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["resolved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
