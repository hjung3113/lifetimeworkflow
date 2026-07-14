"""MREPO-01 workspace-manifest CONSISTENCY gate — workspace.toml is well-formed and internally
agrees (config = SSOT, no codegen). Raises the GEN-03 gate discipline
(test_language_config.py + test_pipeline_config.py) one level to the multi-repo manifest.

Mirrors those files' structural-scan idiom (repo root via parents[3], real manifest loaded through
the shared tools.workspace_config loader, iterate-config / assert-agreement / fail-loud). No
subprocess, no runtime. A malformed manifest — a member root that does not exist, a duplicate member
id, an edge endpoint naming an undeclared member, or an edge contract not tracked in its PRODUCER
member's tree — fails the suite loud so a broken workspace never resolves silently (MREPO-01).

`workspace.toml` is parsed input (untrusted config text): the checks below validate every member and
edge (V5 input validation), and the member-existence check resolves each root on disk (the in-repo
fixture roots are REPO_ROOT subtrees; the Wave-3 golden `_confine` keeps the path-escape guard).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.workspace_config import edges, load_workspace, members, split_endpoint

# test_workspace_config.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _by_id(cfg: dict) -> dict[str, dict]:
    return {m["id"]: m for m in members(cfg)}


def test_member_ids_unique() -> None:
    """No two members share an `id` (a duplicate makes edge-endpoint resolution ambiguous)."""
    ids = [m["id"] for m in members(load_workspace())]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate member id(s): {dupes}"


def test_each_member_root_exists() -> None:
    """Every `[[members]].root` resolves to a directory on disk (no dangling member).

    Use `.exists()` NOT `.is_file()` — roots are directories (mirrors
    test_each_configured_language_has_test_paths, whose python leg names a dir).
    """
    for m in members(load_workspace()):
        root = _REPO_ROOT / m["root"]
        assert root.exists(), f"member {m['id']!r}: root {m['root']!r} not found on disk"


def test_edge_endpoints_name_declared_members() -> None:
    """Every edge `from`/`to` parses via split_endpoint to a DECLARED member id.

    A `repo:stage` endpoint whose member half is undeclared fails loud — the "no dangling edge
    endpoint" check (mirror test_pipeline_edges_are_well_formed's endpoint check, generalized to
    repo-qualified endpoints).
    """
    cfg = load_workspace()
    by_id = _by_id(cfg)
    es = edges(cfg)
    if not es:
        pytest.skip(
            "workspace declares zero edges — nothing to gate (visible SKIP, not silent pass)"
        )
    for edge in es:
        for role in ("from", "to"):
            member_id, _stage = split_endpoint(edge[role])
            assert member_id in by_id, (
                f"edge {edge!r}: `{role}` endpoint {edge[role]!r} resolves to member "
                f"{member_id!r}, which is not a declared [[members]].id "
                f"(declared: {sorted(by_id)})"
            )


def test_edge_contracts_tracked_in_producer() -> None:
    """Every edge `contract` resolves to a tracked schema under the PRODUCER member's tree.

    The cross-repo analogue of test_edge_contracts_have_a_tracked_schema: glob under the producer
    member's own `contracts/` (the `from` endpoint's member half), NOT the repo-root `contracts/`.
    A contract with no `<producer>/contracts/**/<contract>.schema.json` points the consumer at a
    dead reference — fail loud.
    """
    cfg = load_workspace()
    by_id = _by_id(cfg)
    es = edges(cfg)
    if not es:
        pytest.skip(
            "workspace declares zero edges — nothing to gate (visible SKIP, not silent pass)"
        )
    for edge in es:
        producer_id, _stage = split_endpoint(edge["from"])
        producer_root = _REPO_ROOT / by_id[producer_id]["root"]
        schemas = {
            p.name.removesuffix(".schema.json")
            for p in (producer_root / "contracts").rglob("*.schema.json")
        }
        assert edge["contract"] in schemas, (
            f"edge {edge!r}: contract {edge['contract']!r} has no tracked schema under producer "
            f"{producer_id!r} ({by_id[producer_id]['root']}/contracts/**); "
            f"found schemas: {sorted(schemas)}"
        )
