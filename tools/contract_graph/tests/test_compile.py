"""TOPO-04 compile_graph() tests — the domain-neutral graph compiler over effective_relationships().

Two concerns are proven here:

* **Legal shapes are accepted (Task 1).** A relationship graph containing fan-out, fan-in, a
  disconnected component, or a canonical (legal) cycle compiles with EMPTY diagnostics — these
  structures are structurally legal and are never flagged. The unedited core-default project config
  and the unedited default workspace config both compile clean.
* **Malformed endpoints/contracts emit stable descriptive slugs (Task 2).** unresolved-authority /
  dangling-endpoint / unknown-contract fire exactly once per violated constraint and are stable
  sorted so two runs on the same cfg are byte-identical.

All hand-built fixtures use domain-neutral names (authorities "a"/"b", contract "widget") so this
core-plane test stays GEN-04-clean (no instance-path or domain-prose tokens).
"""

from __future__ import annotations

from tools.contract_graph import compile_graph
from tools.harness_config import load_project
from tools.workspace_config import load_workspace

# --- legal shapes accepted (Task 1) --------------------------------------------------------------


def test_fan_out_compiles_clean() -> None:
    """One authority with 3 dependents (fan-out) → no diagnostics; adjacency is the sorted trio."""
    cfg = {
        "components": [
            {"id": "a", "produces": ["w"], "consumes": []},
            {"id": "b", "produces": [], "consumes": ["w"]},
            {"id": "c", "produces": [], "consumes": ["w"]},
            {"id": "d", "produces": [], "consumes": ["w"]},
        ],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "w", "authority": "a", "dependents": ["b", "c", "d"]},
            ]
        },
    }
    result = compile_graph(cfg)
    assert result["diagnostics"] == []
    assert result["adjacency"]["a"] == sorted(["b", "c", "d"])


def test_same_edge_two_distinct_contracts_dedups_adjacency() -> None:
    """CR-01 regression: one authority reaching the SAME dependent via two DISTINCT contracts is a
    legal shape (effective_relationships dedups on the (authority, contract, dependent) triple, so
    both records survive). Adjacency is contract-agnostic → the dependent MUST appear once, not
    twice, or direct()/reverse() would return duplicate ids+paths (breaks the D-03 sorted-ids
    contract)."""
    cfg = {
        "components": [
            {"id": "a", "produces": ["w1", "w2"], "consumes": []},
            {"id": "b", "produces": [], "consumes": ["w1", "w2"]},
        ],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "w1", "authority": "a", "dependents": ["b"]},
                {"id": "r2", "contract": "w2", "authority": "a", "dependents": ["b"]},
            ]
        },
    }
    result = compile_graph(cfg)
    assert result["diagnostics"] == []
    assert result["adjacency"]["a"] == ["b"]


def test_fan_in_compiles_clean() -> None:
    """3 authorities all pointing at one shared dependent (fan-in) → no diagnostics."""
    cfg = {
        "components": [
            {"id": "a1", "produces": ["c1"], "consumes": []},
            {"id": "a2", "produces": ["c2"], "consumes": []},
            {"id": "a3", "produces": ["c3"], "consumes": []},
            {"id": "s", "produces": [], "consumes": ["c1", "c2", "c3"]},
        ],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "c1", "authority": "a1", "dependents": ["s"]},
                {"id": "r2", "contract": "c2", "authority": "a2", "dependents": ["s"]},
                {"id": "r3", "contract": "c3", "authority": "a3", "dependents": ["s"]},
            ]
        },
    }
    result = compile_graph(cfg)
    assert result["diagnostics"] == []
    assert result["adjacency"]["a1"] == ["s"]
    assert result["adjacency"]["a2"] == ["s"]
    assert result["adjacency"]["a3"] == ["s"]


def test_disconnected_component_compiles_clean() -> None:
    """A dependent that never appears as anyone's authority (a sink leaf) → no diagnostics."""
    cfg = {
        "components": [
            {"id": "iso_a", "produces": ["w"], "consumes": []},
            {"id": "iso_b", "produces": [], "consumes": ["w"]},
        ],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "w", "authority": "iso_a", "dependents": ["iso_b"]},
            ]
        },
    }
    result = compile_graph(cfg)
    assert result["diagnostics"] == []
    assert "iso_b" not in result["adjacency"]  # a pure leaf owns no outgoing edges


def test_legal_cycle_compiles_clean() -> None:
    """A two-node cycle (A↔B, both declared, both contracts owned) → cycles are never flagged."""
    cfg = {
        "components": [
            {"id": "A", "produces": ["cA"], "consumes": ["cB"]},
            {"id": "B", "produces": ["cB"], "consumes": ["cA"]},
        ],
        "contract_graph": {
            "relationships": [
                {"id": "rAB", "contract": "cA", "authority": "A", "dependents": ["B"]},
                {"id": "rBA", "contract": "cB", "authority": "B", "dependents": ["A"]},
            ]
        },
    }
    result = compile_graph(cfg)
    assert result["diagnostics"] == []
    assert result["adjacency"]["A"] == ["B"]
    assert result["adjacency"]["B"] == ["A"]


def test_core_and_workspace_defaults_compile_clean() -> None:
    """The unedited core default AND default workspace both compile with zero diagnostics."""
    assert compile_graph(load_project())["diagnostics"] == []
    assert compile_graph(load_workspace())["diagnostics"] == []


# --- D-02 diagnostic slugs (Task 2) --------------------------------------------------------------


def test_unresolved_authority_slug() -> None:
    """An authority naming no declared component/member → one `unresolved-authority: ` slug."""
    cfg = {
        "components": [{"id": "b", "produces": [], "consumes": ["w"]}],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "w", "authority": "ghost", "dependents": ["b"]},
            ]
        },
    }
    diags = compile_graph(cfg)["diagnostics"]
    unresolved = [d for d in diags if d.startswith("unresolved-authority: ")]
    assert len(unresolved) == 1, diags
    assert "r1" in unresolved[0] and "ghost" in unresolved[0]


def test_dangling_endpoint_slug_keeps_resolved_siblings() -> None:
    """One unresolved dependent → one `dangling-endpoint: ` slug; resolved siblings stay."""
    cfg = {
        "components": [
            {"id": "a", "produces": ["w"], "consumes": []},
            {"id": "b", "produces": [], "consumes": ["w"]},
        ],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "w", "authority": "a", "dependents": ["b", "ghost"]},
            ]
        },
    }
    result = compile_graph(cfg)
    dangling = [d for d in result["diagnostics"] if d.startswith("dangling-endpoint: ")]
    assert len(dangling) == 1, result["diagnostics"]
    assert "r1" in dangling[0] and "ghost" in dangling[0]
    assert result["adjacency"]["a"] == ["b"]  # the resolved sibling survives


def test_unknown_contract_slug_component_produces() -> None:
    """Authority resolves to a component that does NOT list the contract in produces → slug."""
    cfg = {
        "components": [
            {"id": "a", "produces": ["other"], "consumes": []},
            {"id": "b", "produces": [], "consumes": ["w"]},
        ],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "w", "authority": "a", "dependents": ["b"]},
            ]
        },
    }
    diags = compile_graph(cfg)["diagnostics"]
    unknown = [d for d in diags if d.startswith("unknown-contract: ")]
    assert len(unknown) == 1, diags
    assert "r1" in unknown[0] and "w" in unknown[0]


def test_diagnostics_are_stable_sorted() -> None:
    """Two runs on the same malformed cfg produce byte-identical, sorted diagnostic lists."""
    cfg = {
        "components": [{"id": "keep", "produces": [], "consumes": []}],
        "contract_graph": {
            "relationships": [
                {"id": "rZ", "contract": "w", "authority": "ghostZ", "dependents": ["keep"]},
                {"id": "rA", "contract": "w2", "authority": "ghostA", "dependents": ["keep"]},
            ]
        },
    }
    first = compile_graph(cfg)["diagnostics"]
    second = compile_graph(cfg)["diagnostics"]
    assert first == second
    assert first == sorted(first)
    assert len(first) == 2  # one unresolved-authority per malformed relationship
