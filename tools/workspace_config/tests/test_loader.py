"""Loader unit tests for the MREPO-01 workspace-manifest passthrough (tools.workspace_config).

Mirrors the loader-read half of the GEN-03 precedent: parse the real workspace.toml through the
shared loader and assert the passthrough shape (members/edges) + the split_endpoint() `repo:stage`
helper. Enforcement (dangling members, unresolved edge contracts) lives in the separate consistency
gate tools.harness_lint.tests.test_workspace_config — this file only pins the loader contract.
"""

from __future__ import annotations

from tools.workspace_config import edges, load_workspace, members, split_endpoint


def test_load_workspace_returns_dict() -> None:
    """The manifest parses into a plain dict (binary-mode tomllib.load, no enforcement)."""
    cfg = load_workspace()
    assert isinstance(cfg, dict)
    assert "workspace" in cfg


def test_members_has_two_unique_entries() -> None:
    """The generic default fixture declares exactly 2 members with unique ids."""
    ms = members(load_workspace())
    assert len(ms) == 2
    ids = [m["id"] for m in ms]
    assert len(set(ids)) == 2, f"member ids not unique: {ids}"


def test_edges_has_one_entry() -> None:
    """The generic default fixture declares exactly one cross-repo edge."""
    es = edges(load_workspace())
    assert len(es) == 1
    edge = es[0]
    assert {"from", "to", "contract"} <= set(edge), f"edge missing keys: {edge}"


def test_split_endpoint_repo_qualified() -> None:
    """`repo:stage` splits into (repo, stage) — repo half drives member resolution (MREPO-03)."""
    assert split_endpoint("member-a:emit") == ("member-a", "emit")


def test_split_endpoint_bare_stage_backward_compatible() -> None:
    """A bare `stage` (no colon) → (None, stage): Phase-8 single-repo endpoints stay valid."""
    assert split_endpoint("emit") == (None, "emit")


def test_members_omitted_cfg_loads_default() -> None:
    """Accessors load the default manifest when cfg is omitted (cwd-independent)."""
    assert len(members()) == 2
    assert len(edges()) == 1
