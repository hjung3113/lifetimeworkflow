"""TOPO-05 affected-set query layer over the compiled contract graph (D-03).

Consumes the ``"adjacency"`` dict produced by ``tools.contract_graph.compile.compile_graph`` — the
authority → sorted[dependents] map — and answers the three "what does changing X affect" shapes
conductor routing (Plan 03) and future documentation-impact reports (DOCSUP) need:

* ``direct(graph, node)``    — one hop along outgoing edges.
* ``reverse(graph, node)``   — one hop along INCOMING edges (predecessors of ``node``).
* ``transitive(graph, node)`` — every node reachable from ``node`` along outgoing edges.

D-03 invariants baked into this module:

* Every result is ``{"ids": [...sorted...], "paths": [[...]]}`` — sorted ids AND the connecting
  path(s), never ids alone. ``paths[i]`` corresponds to ``ids[i]`` and starts at the query node.
* ``transitive`` is CYCLE-SAFE: an iterative visited-set worklist (Pattern 2) bounds traversal to
  O(nodes+edges). A legal cycle terminates — never recurses, stack-overflows, or double-counts.
* Repeated calls on the same graph + start id return byte-identical output (deterministic ordering;
  neighbours are always visited in sorted order so no set-iteration-order leakage).
* The module performs NO file I/O and imports nothing from the task-control / evidence plane. It
  operates purely on the already-compiled in-memory ``graph["adjacency"]`` dict — it creates no new
  task-evidence requirement and preloads no contract body. (Structurally proven by test_query.py.)
"""

from __future__ import annotations

__all__ = ["direct", "reverse", "transitive"]


def direct(graph: dict, node: str) -> dict:
    """Return the direct (one-hop) outgoing dependents of ``node``.

    ``{"ids": sorted[dependents], "paths": [[node, dep], ...]}``. An isolated node (no adjacency
    entry) yields ``{"ids": [], "paths": []}`` — never a ``KeyError``.
    """
    ids = sorted(graph["adjacency"].get(node, []))
    return {"ids": ids, "paths": [[node, dep] for dep in ids]}


def reverse(graph: dict, node: str) -> dict:
    """Return the direct (one-hop) incoming predecessors of ``node``.

    Builds a transposed adjacency (``dependent -> [authorities]``) once from ``graph["adjacency"]``,
    then returns the sorted predecessors of ``node`` with 1-hop paths ``[node, predecessor]``.
    An isolated node yields ``{"ids": [], "paths": []}`` — never a ``KeyError``.
    """
    transposed: dict[str, list[str]] = {}
    for authority, dependents in graph["adjacency"].items():
        for dep in dependents:
            transposed.setdefault(dep, []).append(authority)

    ids = sorted(transposed.get(node, []))
    return {"ids": ids, "paths": [[node, pred] for pred in ids]}


def transitive(graph: dict, node: str) -> dict:
    """Return every node reachable from ``node`` along outgoing edges (cycle-safe).

    Iterative visited-set worklist (research Pattern 2): a node is checked against ``visited``
    BEFORE it is enqueued, so a legal cycle terminates — traversal is bounded to O(nodes+edges), no
    recursion. Neighbours are visited in sorted order, so the recorded (first-found) path for each
    reached node is deterministic across runs.

    ``{"ids": sorted[reachable-excluding-start], "paths": [...]}`` where ``paths[i]`` corresponds to
    ``ids[i]`` and starts at ``node``. An isolated node yields ``{"ids": [], "paths": []}``.
    """
    adjacency = graph["adjacency"]
    visited: set[str] = {node}
    path_of: dict[str, list[str]] = {node: [node]}
    frontier: list[str] = [node]

    while frontier:
        current = frontier.pop(0)
        for nxt in sorted(adjacency.get(current, [])):
            if nxt in visited:
                continue  # cycle terminus / already-reached — never re-enqueue, never recurse
            visited.add(nxt)
            path_of[nxt] = path_of[current] + [nxt]
            frontier.append(nxt)

    ids = sorted(visited - {node})
    return {"ids": ids, "paths": [path_of[i] for i in ids]}
