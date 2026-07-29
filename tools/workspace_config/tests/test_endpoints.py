"""repo:stage endpoint parse + cross-boundary edge semantics (MREPO-04 topology generalization).

Proves the observable "a declared edge can cross a repo boundary" behavior in the WORKSPACE layer:
a repo-qualified ``repo:stage`` endpoint parses into ``(member, stage)`` and the fixture's one edge
spans two distinct members (from-member != to-member). A bare ``stage`` (no colon) stays a
single-repo endpoint, backward-compatible with the Phase-8 core topology.

The generalization lives ONLY in the workspace layer; only workspace manifest edges cross repos.
CER-08 (Phase 44) removed the core default edge DATA, and with it the companion check that pinned
those core endpoints as unqualified — it had no subject left to assert against.
"""

from __future__ import annotations

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
