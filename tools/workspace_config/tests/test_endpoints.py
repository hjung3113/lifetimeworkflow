"""repo:stage endpoint parse + cross-boundary edge semantics (MREPO-04 topology generalization).

Proves the observable "a declared edge can cross a repo boundary" behavior in the WORKSPACE layer:
a repo-qualified ``repo:stage`` endpoint parses into ``(member, stage)`` and the fixture's one edge
spans two distinct members (from-member != to-member). A bare ``stage`` (no colon) stays a
single-repo endpoint, backward-compatible with the Phase-8 core topology.

The generalization lives ONLY in the workspace layer. This test also pins the anti-regression
invariant (Pattern 5): the Phase-8 core ``harness/project.toml`` ``[pipeline]`` edges are UNCHANGED —
their endpoints carry NO repo qualifier (no ``:``). The core single-repo default is not generalized;
only the workspace manifest edges cross repos.
"""

from __future__ import annotations

from tools.harness_config import load_project, pipeline
from tools.workspace_config import edges, load_workspace, split_endpoint


def test_split_endpoint_repo_qualified_members() -> None:
    """``repo:stage`` splits into (member, stage) — the repo half drives member resolution (MREPO-03),
    the stage half is the pipeline endpoint (MREPO-04)."""
    assert split_endpoint("member-a:emit") == ("member-a", "emit")
    assert split_endpoint("member-b:ingest") == ("member-b", "ingest")


def test_split_endpoint_bare_stage_is_single_repo() -> None:
    """A bare ``stage`` (no colon) → (None, stage): the Phase-8 core single-repo endpoint form stays
    valid (backward-compatible)."""
    assert split_endpoint("emit") == (None, "emit")


def test_fixture_edge_crosses_repo_boundary() -> None:
    """The real manifest's one edge spans a repo boundary: from-member != to-member (member-a →
    member-b). This is the observable MREPO-04 "edge crosses a repo boundary" behavior."""
    es = edges(load_workspace())
    assert len(es) == 1, f"fixture must declare exactly one cross-repo edge (got {len(es)})"
    edge = es[0]
    from_member, from_stage = split_endpoint(edge["from"])
    to_member, to_stage = split_endpoint(edge["to"])
    assert from_member == "member-a" and from_stage == "emit", edge
    assert to_member == "member-b" and to_stage == "ingest", edge
    assert from_member != to_member, (
        f"edge {edge!r} does not cross a repo boundary: from-member == to-member ({from_member!r})"
    )


def test_core_pipeline_edges_stay_single_repo() -> None:
    """Anti-regression (Pattern 5): the Phase-8 core ``harness/project.toml`` ``[pipeline]`` edges are
    UNCHANGED — every endpoint is a bare stage carrying NO ``:`` repo qualifier. The generalization
    lives only in the workspace layer, never the core default topology."""
    core_edges = pipeline(load_project()).get("edges", [])
    assert core_edges, "core [pipeline] must declare at least one edge (default topology)"
    for edge in core_edges:
        for endpoint in (edge["from"], edge["to"]):
            assert ":" not in endpoint, (
                f"core edge {edge!r} endpoint {endpoint!r} carries a repo qualifier — the Phase-8 "
                f"single-repo topology must stay unchanged (only workspace edges cross repos)"
            )
            # split_endpoint agrees the core endpoint has no repo half.
            assert split_endpoint(endpoint)[0] is None, endpoint
