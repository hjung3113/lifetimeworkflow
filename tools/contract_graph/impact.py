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
``_resolve_node``: derive a contract id from the path's filename (mirrors ``compile.py``'s
``_tracked_schemas`` suffix-strip idiom), scan ``effective_relationships()`` for the record naming
that contract, and take its ``authority`` as the node — or accept ``contract_path`` directly when it
is already a bare node id present in the graph.

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
from pathlib import Path

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

__all__ = ["report", "main"]


def _resolve_node(
    contract_path: str, relationships: list[dict], graph: dict
) -> tuple[str | None, str | None]:
    """Resolve ``contract_path`` (or a bare node id) to ``(node, contract_id)``.

    First tries contract-id resolution: derive ``candidate_id`` from the path's filename (the exact
    suffix-strip idiom ``compile.py:46`` already uses) and scan ``relationships`` for the record
    whose ``"contract"`` matches — on a hit, the record's ``"authority"`` IS the node. If no
    relationship names the contract, fall back to bare-node-id resolution: ``contract_path`` is
    accepted directly as the node when it is already a known key or value in
    ``graph["adjacency"]``. Returns ``(None, candidate_id)`` when neither resolves.
    """
    candidate_id = Path(contract_path).name.removesuffix(".schema.json")

    for rel in relationships:
        if rel["contract"] == candidate_id:
            return rel["authority"], candidate_id

    adjacency = graph["adjacency"]
    if contract_path in adjacency or any(contract_path in deps for deps in adjacency.values()):
        return contract_path, None

    return None, candidate_id


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

    node, contract_id = _resolve_node(contract_path, relationships, graph)

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

    contract_owner: str | None = None
    if contract_id is not None:
        try:
            contract_owner = owning_package(dir_pkgs, contract_path)
        except ValueError:
            contract_owner = None

    component_by_id = {c["id"]: c for c in components(cfg)}
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
