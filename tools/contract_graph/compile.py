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


def _tracked_schemas(contracts_dir: Path) -> set[str]:
    """Return the set of tracked contract ids under ``contracts_dir`` (repo schema-glob idiom).

    Mirrors the ``{p.name.removesuffix(".schema.json") for p in dir.rglob("*.schema.json")}`` check
    used in ``contract_drift.drift`` and both topology gates. A missing directory yields an empty
    set (``rglob`` on an absent path returns nothing) — the caller then reports unknown-contract.
    """
    return {p.name.removesuffix(".schema.json") for p in contracts_dir.rglob("*.schema.json")}


def compile_graph(cfg: dict | None = None) -> dict:
    """Compile the effective relationship list into resolved graph data + diagnostics.

    Returns ``{"relationships": [...], "adjacency": {authority: sorted[dependents]},
    "diagnostics": sorted[str]}``. ``relationships`` is ``effective_relationships(cfg)`` verbatim;
    ``adjacency`` maps each RESOLVED authority to its sorted resolved dependents (unresolved
    endpoints are excluded from adjacency and recorded as diagnostics); ``diagnostics`` is the
    stable-sorted list of descriptive slugs.
    """
    if cfg is None:
        from tools.harness_config import load_project

        cfg = load_project()

    relationships = effective_relationships(cfg)

    component_by_id = {c["id"]: c for c in components(cfg)}
    component_ids = set(component_by_id)
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

    diagnostics: list[str] = []
    adjacency: dict[str, list[str]] = {}

    for rel in relationships:
        authority = rel["authority"]
        resolved_authority = _resolve(authority)

        if resolved_authority is None:
            diagnostics.append(
                f"unresolved-authority: relationship {rel['id']} authority {authority!r} "
                f"is not a declared component or member"
            )
            # Unresolved authority contributes no adjacency row and no contract check.
            continue

        contract_diag = _contract_ownership_diagnostic(
            rel, resolved_authority, component_by_id, member_by_id
        )
        if contract_diag is not None:
            diagnostics.append(contract_diag)

        resolved_dependents: list[str] = []
        for dep in rel["dependents"]:
            if _resolve(dep) is None:
                diagnostics.append(
                    f"dangling-endpoint: relationship {rel['id']} dependent {dep!r} "
                    f"is not a declared component or member"
                )
                continue
            resolved_dependents.append(dep)

        if resolved_dependents:
            adjacency.setdefault(authority, [])
            adjacency[authority].extend(resolved_dependents)

    return {
        "relationships": relationships,
        "adjacency": {k: sorted(adjacency[k]) for k in sorted(adjacency)},
        "diagnostics": sorted(diagnostics),
    }


def _contract_ownership_diagnostic(
    rel: dict,
    resolved_authority: tuple[str, str],
    component_by_id: dict[str, dict],
    member_by_id: dict[str, dict],
) -> str | None:
    """Return an ``unknown-contract`` slug if the resolved authority does not own the contract.

    A component-backed authority carrying a ``produces`` list → require the contract in ``produces``
    (mirrors ``test_pipeline_config.py``'s ownership check). Otherwise (an opaque logical authority,
    a component with no ``produces``, or a cross-repo ``repo:stage`` member) → existence-only: the
    contract must resolve to a tracked ``<root>/contracts/**/<contract>.schema.json`` (mirrors
    ``test_workspace_config.py``'s producer-tree check). The glob root is the repo ``contracts/``
    for a project authority, or the producer member's own ``contracts/`` for a cross-repo authority.
    """
    kind, resolved_id = resolved_authority
    contract = rel["contract"]

    if kind == "component":
        declaration = component_by_id.get(resolved_id, {})
        if "produces" in declaration:
            if contract not in declaration["produces"]:
                return (
                    f"unknown-contract: relationship {rel['id']} contract {contract!r} "
                    f"not owned by authority {rel['authority']!r}"
                )
            return None
        # A component with no `produces` field → fall through to project-root existence-only.
        contracts_dir = _CONTRACTS_DIR
    else:  # member (cross-repo `repo:stage`, or a bare stage that named a member)
        member_root = _REPO_ROOT / member_by_id[resolved_id]["root"]
        contracts_dir = member_root / "contracts"

    if contract not in _tracked_schemas(contracts_dir):
        return (
            f"unknown-contract: relationship {rel['id']} contract {contract!r} "
            f"has no tracked schema"
        )
    return None
