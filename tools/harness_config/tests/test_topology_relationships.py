"""TOPO-02/03 tests — contract_graph_relationships() passthrough + effective_relationships().

Proves the additive coexistence seam: the raw-passthrough accessor returns explicit records
unchanged, and effective_relationships() deterministically lowers legacy [pipeline].edges to
authority/dependent records, unions them with explicit records, stable-sorts by id, and raises on
the three D-05 failure modes (duplicate id / duplicate semantic edge / contradiction).

All hand-built failure fixtures use domain-neutral names (authorities "a"/"b", contract "widget")
so this core-plane test stays GEN-04-clean (no examples/ / domain prose tokens).
"""

from __future__ import annotations

import pytest

from tools.harness_config import (
    contract_graph_relationships,
    effective_relationships,
    load_project,
)
from tools.workspace_config import load_workspace


# --- accessor passthrough (TOPO-02) --------------------------------------------------------------


def test_accessor_returns_empty_on_linear_default() -> None:
    """The generic-default configs declare no explicit records → raw passthrough is []."""
    assert contract_graph_relationships(load_project()) == []


def test_accessor_is_raw_passthrough() -> None:
    """The accessor returns the explicit records unchanged (zero validation/normalization)."""
    record = {
        "id": "explicit/widget/a->b",
        "contract": "widget",
        "authority": "a",
        "dependents": ["b"],
    }
    cfg = {"contract_graph": {"relationships": [record]}}
    assert contract_graph_relationships(cfg) == [record]


# --- lowering (TOPO-03, D-04) ---------------------------------------------------------------------


def test_lowers_linear_default_to_single_relationship() -> None:
    """The unedited source→sink/greeting edge lowers with zero config edits."""
    rels = effective_relationships(load_project())
    assert len(rels) == 1
    rel = rels[0]
    assert rel["id"] == "pipeline/greeting/source->sink"
    assert rel["contract"] == "greeting"
    assert rel["authority"] == "source"
    assert rel["dependents"] == ["sink"]


def test_output_is_deterministic() -> None:
    """Two calls on the same cfg yield byte-identical (==) output."""
    cfg = load_project()
    assert effective_relationships(cfg) == effective_relationships(cfg)


def test_output_is_stable_sorted_by_id() -> None:
    """The merged list is sorted by id (construct out-of-alphabetical-order inputs)."""
    cfg = {
        "pipeline": {
            "edges": [
                {"from": "z", "to": "y", "contract": "wc"},
                {"from": "a", "to": "b", "contract": "ac"},
            ]
        },
        "contract_graph": {
            "relationships": [
                {
                    "id": "explicit/mc/m->n",
                    "contract": "mc",
                    "authority": "m",
                    "dependents": ["n"],
                },
            ]
        },
    }
    ids = [rel["id"] for rel in effective_relationships(cfg)]
    assert ids == sorted(ids)
    assert ids == [
        "explicit/mc/m->n",
        "pipeline/ac/a->b",
        "pipeline/wc/z->y",
    ]


def test_union_contains_lowered_and_explicit() -> None:
    """A distinct-id explicit record unions with the lowered edge — both survive."""
    cfg = {
        "pipeline": {"edges": [{"from": "a", "to": "b", "contract": "widget"}]},
        "contract_graph": {
            "relationships": [
                {
                    "id": "explicit/gadget/c->d",
                    "contract": "gadget",
                    "authority": "c",
                    "dependents": ["d"],
                },
            ]
        },
    }
    ids = {rel["id"] for rel in effective_relationships(cfg)}
    assert ids == {"pipeline/widget/a->b", "explicit/gadget/c->d"}


# --- failure taxonomy (TOPO-03, D-05) -------------------------------------------------------------


def test_duplicate_id_raises() -> None:
    """Two records sharing the same id raise deterministically."""
    cfg = {
        "pipeline": {"edges": []},
        "contract_graph": {
            "relationships": [
                {"id": "dup", "contract": "widget", "authority": "a", "dependents": ["b"]},
                {"id": "dup", "contract": "gadget", "authority": "c", "dependents": ["d"]},
            ]
        },
    }
    with pytest.raises(ValueError):
        effective_relationships(cfg)


def test_duplicate_semantic_edge_raises() -> None:
    """Two records producing an identical (authority, contract, dependent) triple raise.

    A multi-dependent record expands to 2 triples; one collides with the single-triple record.
    """
    cfg = {
        "pipeline": {"edges": []},
        "contract_graph": {
            "relationships": [
                {
                    "id": "multi",
                    "contract": "widget",
                    "authority": "a",
                    "dependents": ["b", "c"],
                },
                {
                    "id": "single",
                    "contract": "widget",
                    "authority": "a",
                    "dependents": ["c"],
                },
            ]
        },
    }
    with pytest.raises(ValueError):
        effective_relationships(cfg)


def test_contradiction_raises() -> None:
    """The same contract claimed by two different authorities raises."""
    cfg = {
        "pipeline": {"edges": []},
        "contract_graph": {
            "relationships": [
                {"id": "one", "contract": "widget", "authority": "a", "dependents": ["x"]},
                {"id": "two", "contract": "widget", "authority": "b", "dependents": ["y"]},
            ]
        },
    }
    with pytest.raises(ValueError):
        effective_relationships(cfg)


# --- workspace lowering passthrough (TOPO-02/03, Pitfall 7) ---------------------------------------


def test_workspace_edge_endpoints_pass_through_verbatim() -> None:
    """The unedited workspace repo:stage edge lowers with raw endpoints — no split_endpoint."""
    rels = effective_relationships(load_workspace())
    assert len(rels) == 1
    rel = rels[0]
    assert rel["authority"] == "member-a:emit"
    assert rel["dependents"] == ["member-b:ingest"]
    assert rel["contract"] == "greeting"
    assert rel["id"] == "pipeline/greeting/member-a:emit->member-b:ingest"
