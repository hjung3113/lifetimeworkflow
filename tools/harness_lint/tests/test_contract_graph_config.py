"""TOPO-04 contract-graph CONSISTENCY gate — the compiler stays green on the default configs.

Mirrors test_pipeline_config.py's structural-scan idiom (repo root via parents[3], real config
loaded through the shared loader, assert-agreement / fail-loud). These are the two "must stay green"
anchors the gate protects: the GENERIC core-default project config and the GENERIC default workspace
config must BOTH compile with `diagnostics == []` through `tools.contract_graph.compile_graph` — the
single deterministic resolution/validation layer over `effective_relationships()`.

A future edit that introduces an unresolved authority, a dangling dependent endpoint, or an
authority claiming a contract it does not own would populate `diagnostics` and fail the suite loud,
so a broken relationship graph never resolves silently. The checks reference NO instance overlay
(an instance's own topology lives under its own tree, never the core default).
"""

from __future__ import annotations

from tools.contract_graph import compile_graph
from tools.harness_config import load_project
from tools.workspace_config import load_workspace


def test_core_default_project_compiles_clean() -> None:
    """The GENERIC core-default project config compiles with zero diagnostics."""
    result = compile_graph(load_project())
    assert result["diagnostics"] == [], (
        f"core default project topology produced diagnostics: {result['diagnostics']}"
    )


def test_default_workspace_compiles_clean() -> None:
    """The GENERIC default workspace manifest compiles with zero diagnostics.

    The single cross-repo edge lowers to an authority `member-a:emit` whose contract `greeting`
    resolves via existence-only against the producer member's own `contracts/` tree — proving the
    cross-repo authority-owned-contract resolution path stays green.
    """
    result = compile_graph(load_workspace())
    assert result["diagnostics"] == [], (
        f"default workspace topology produced diagnostics: {result['diagnostics']}"
    )
