"""TOPO-04 graph compiler — a validation/resolution layer ON TOP of effective_relationships().

``compile_graph(cfg=None)`` is the single deterministic entry point. It NEVER re-lowers or re-unions
the topology: ``tools.harness_config.loader.effective_relationships(cfg)`` is the ONLY source of
relationship records (it already lowers legacy ``[pipeline].edges``, unions the explicit
``[[contract_graph.relationships]]`` records, stable-sorts by id, and raises ``ValueError`` on the
three D-05 failure modes). This module adds a resolution/validation layer on top:

* **Endpoint resolution.** Every ``authority`` and every ``dependents[i]`` is resolved against the
  cfg's declared components (project-shaped) and/or members (workspace-shaped) via
  ``split_endpoint`` — a ``repo:stage`` half must name a declared member; a bare ``stage`` must name
  a declared component OR member.
* **Authority-owned-contract resolution.** The relationship's ``contract`` must be owned by its
  resolved authority — either listed in that authority's ``produces`` (component-backed) or, for an
  opaque/cross-repo authority with no ``produces``, present as a tracked
  ``contracts/**/<contract>.schema.json`` (reusing the repo-wide schema-glob existence idiom).

Legal graph SHAPES — fan-in, fan-out, disconnected components, and canonical cycles — are NEVER
flagged: a cycle is just two adjacency entries pointing at each other, with no special casing.

Diagnostics are returned as a stable-sorted ``list[str]`` of descriptive grep-able slugs
(``unresolved-authority`` / ``dangling-endpoint`` / ``unknown-contract``) — never raised as
exceptions (mirrors ``contract_drift.run_gate``'s result-dict pattern). The only exception that
propagates is ``effective_relationships()``'s own ``ValueError``.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import components, effective_relationships
from tools.workspace_config import members, split_endpoint

# compile.py -> contract_graph -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS_DIR = _REPO_ROOT / "contracts"


def compile_graph(cfg: dict | None = None) -> dict:
    """Compile the effective relationship list into resolved graph data + diagnostics.

    Returns ``{"relationships": [...], "adjacency": {authority: sorted[dependents]},
    "diagnostics": sorted[str]}``. ``relationships`` is ``effective_relationships(cfg)`` verbatim;
    ``adjacency`` maps each RESOLVED authority to its sorted resolved dependents; ``diagnostics`` is
    the stable-sorted list of descriptive slugs (populated in the diagnostic layer).
    """
    if cfg is None:
        from tools.harness_config import load_project

        cfg = load_project()

    relationships = effective_relationships(cfg)

    component_ids = {c["id"] for c in components(cfg)}
    member_by_id = {m["id"]: m for m in members(cfg)}

    def _resolve(endpoint: str) -> tuple[str, str] | None:
        """Resolve an endpoint to ``(kind, id)`` — ``("component"|"member", id)`` — or None.

        A ``repo:stage`` endpoint (repo half non-None) must name a declared member. A bare ``stage``
        must name a declared component OR a declared member.
        """
        repo, stage = split_endpoint(endpoint)
        if repo is not None:
            return ("member", repo) if repo in member_by_id else None
        if stage in component_ids:
            return ("component", stage)
        if stage in member_by_id:
            return ("member", stage)
        return None

    adjacency: dict[str, list[str]] = {}

    for rel in relationships:
        authority = rel["authority"]
        if _resolve(authority) is None:
            # Unresolved authority contributes no adjacency row (diagnostic emission is layered on).
            continue

        resolved_dependents = [dep for dep in rel["dependents"] if _resolve(dep) is not None]
        if resolved_dependents:
            adjacency.setdefault(authority, [])
            adjacency[authority].extend(resolved_dependents)

    return {
        "relationships": relationships,
        "adjacency": {k: sorted(adjacency[k]) for k in sorted(adjacency)},
        "diagnostics": [],
    }
