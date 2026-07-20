"""DOCSUP-05 / D-12 — graph impact ids for a docs report. Ids only, and EMPTY when unmapped.

A pure helper: no filesystem writes, no CLI, no exit codes. It answers exactly one question —
"which endpoints does changing this source affect?" — by walking the chain

    ``contracts/<...>/<stem>.schema.json``  ->  ``<stem>``
        ->  the ``effective_relationships`` record whose ``contract == <stem>``
        ->  that record's ``authority`` endpoint
        ->  ``direct`` + ``transitive`` over ``compile_graph``'s adjacency

Graph nodes are ENDPOINTS, not file paths, which is why the mapping is real work rather than a
lookup. ``tools/contract_graph/query.py:5`` names this consumer by name ("future
documentation-impact reports (DOCSUP)"), so the Phase 25 query API is reused verbatim — no second
traversal is written
here, and in particular ``transitive``'s cycle-safe iterative worklist is inherited rather than
re-implemented.

``reverse()`` is deliberately never called: a docs report asks "what does changing this AFFECT",
which is the OUTGOING direction. ``reverse`` would answer "what feeds this", a different question
whose answer would read as a wrong blast radius.

Only ``ids`` cross the boundary. The query API's ``paths`` are for the conductor's tree render;
putting endpoint chains into a human-doc remediation line would bury the one thing the reader needs
(research Q8).
"""

from __future__ import annotations

from collections.abc import Iterable

from tools.contract_graph.compile import compile_graph
from tools.contract_graph.query import direct, transitive
from tools.harness_config.loader import effective_relationships

__all__ = ["impact_ids"]

_CONTRACTS_PREFIX = "contracts/"
_SCHEMA_SUFFIX = ".schema.json"


def _contract_stem(path: str) -> str | None:
    """``contracts/<...>/<stem>.schema.json`` -> ``<stem>``; anything else -> ``None``.

    Both halves of the test are load-bearing: the ``contracts/`` prefix keeps a same-named schema
    living elsewhere in the tree out of the chain, and the ``.schema.json`` suffix keeps
    ``contracts/README.md`` from being read as a contract named ``README``.
    """
    normalized = path.replace("\\", "/")
    if not normalized.startswith(_CONTRACTS_PREFIX) or not normalized.endswith(_SCHEMA_SUFFIX):
        return None
    stem = normalized.rsplit("/", 1)[-1].removesuffix(_SCHEMA_SUFFIX)
    return stem or None


def _authority_for(stem: str, relationships: list[dict]) -> str | None:
    """The ``authority`` endpoint of the relationship whose ``contract`` is ``stem``, or ``None``.

    ``effective_relationships`` already raises on a contract claimed by two different authorities,
    so a first match is unambiguous by the time it reaches here.
    """
    for record in relationships:
        if record.get("contract") == stem:
            return record.get("authority")
    return None


def impact_ids(source_paths: Iterable[str], cfg: dict | None = None) -> list[str]:
    """Return the sorted, deduplicated endpoint ids a change to ``source_paths`` reaches.

    ``cfg`` is the ``load_project(path=...)`` seam — passing an explicit dict keeps callers (and
    tests) off the live ``harness/project.toml``. The graph is compiled ONCE per call, never once
    per path.

    NEVER FABRICATE. When the path -> stem -> authority chain does not resolve, this returns an
    EMPTY list and nothing else — no placeholder, no ``TBD``, no partial guess. That is the
    ``OWNER_TBD`` house rule (``tools/memory_regen/contracts_index.py:43-45``) applied to the graph,
    and it matters more here than usual for two reasons. First, most sources a human-doc binding
    watches are not tracked contracts at all, so empty is the NORMAL, correct answer rather than a
    degraded one. Second, the path -> node mapping is 28-RESEARCH.md's assumption A5 at MEDIUM
    confidence: if A5 is wrong, this shape yields ids that are missing rather than ids that are
    incorrect. Under-delivering is the safe direction, because a report that names a wrong blast
    radius is still trusted and acted on.
    """
    paths = list(source_paths)
    if not paths:
        return []

    relationships = effective_relationships(cfg)
    graph = compile_graph(cfg)

    found: set[str] = set()
    for path in paths:
        stem = _contract_stem(path)
        if stem is None:
            continue  # not a contract schema -> no node -> no ids (see the docstring)
        authority = _authority_for(stem, relationships)
        if authority is None:
            continue  # a tracked-looking stem with no relationship record -> still no node
        # An authority with no adjacency row (an unresolved endpoint, or a genuine leaf) yields
        # `{"ids": [], "paths": []}` from both queries — never a KeyError, never a guess.
        found.update(direct(graph, authority)["ids"])
        found.update(transitive(graph, authority)["ids"])

    # Explicitly sorted: a `set` must never reach output (the determinism rule this package obeys).
    return sorted(found)
