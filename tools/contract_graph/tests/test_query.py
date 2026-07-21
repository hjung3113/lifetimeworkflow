"""TOPO-05 query-layer tests — direct/reverse/transitive over the compiled adjacency (D-03).

Two concerns are proven here:

* **Behavior (Task 1 contract).** direct/reverse return sorted ids AND 1-hop paths; transitive
  walks the whole reachable set, terminates on a legal cycle via the visited-set, handles a
  diamond, and is deterministic (byte-identical across repeated calls). An isolated node returns
  the empty result, never a KeyError.
* **D-03 structural invariant (Task 2).** query.py's SOURCE TEXT is asserted to import nothing
  from the task-control / evidence plane and to perform no file I/O — the concrete, automatable
  proof that the query layer creates no new task-evidence requirement and preloads no contract
  body. It operates purely on the already-compiled in-memory ``graph["adjacency"]`` dict.

All fixtures use domain-neutral node names so this core-plane test stays GEN-04-clean.
"""

from __future__ import annotations

from pathlib import Path

from tools.contract_graph import direct, reverse, transitive
from tools.contract_graph import query as query_module

# --- behavior: direct / reverse (Task 1 contract) ------------------------------------------------


def test_direct_returns_sorted_ids_and_one_hop_paths() -> None:
    """direct on adjacency={'a': ['b','c']} → sorted ids + [['a','b'],['a','c']]."""
    graph = {"adjacency": {"a": ["b", "c"]}}
    assert direct(graph, "a") == {"ids": ["b", "c"], "paths": [["a", "b"], ["a", "c"]]}


def test_reverse_walks_incoming_edges() -> None:
    """reverse on adjacency={'a': ['b'], 'c': ['b']} for 'b' → predecessors ['a','c']."""
    graph = {"adjacency": {"a": ["b"], "c": ["b"]}}
    assert reverse(graph, "b") == {"ids": ["a", "c"], "paths": [["b", "a"], ["b", "c"]]}


# --- behavior: transitive cycle-safety + diamond + determinism (Task 1 contract) -----------------


def test_transitive_terminates_on_two_node_cycle() -> None:
    """A legal 2-node cycle terminates via the visited-set (no recursion/timeout)."""
    graph = {"adjacency": {"a": ["b"], "b": ["a"]}}
    assert transitive(graph, "a") == {"ids": ["b"], "paths": [["a", "b"]]}


def test_transitive_diamond_returns_sorted_ids_with_valid_paths() -> None:
    """Diamond a->b, a->c, b->d, c->d → ids ['b','c','d'] sorted, each with a path from 'a'."""
    graph = {"adjacency": {"a": ["b", "c"], "b": ["d"], "c": ["d"]}}
    result = transitive(graph, "a")
    assert result["ids"] == ["b", "c", "d"]
    for node, path in zip(result["ids"], result["paths"], strict=True):
        assert path[0] == "a"
        assert path[-1] == node


def test_transitive_is_deterministic_across_repeated_calls() -> None:
    """Two calls on the same graph return byte-identical (==) results."""
    graph = {"adjacency": {"a": ["b", "c"], "b": ["d"], "c": ["d"]}}
    assert transitive(graph, "a") == transitive(graph, "a")


# --- D-03 structural invariant: no task-evidence coupling, no file I/O (Task 2) ------------------


def _query_source() -> str:
    return Path(query_module.__file__).read_text(encoding="utf-8")


def test_query_source_never_imports_task_evidence_plane() -> None:
    """query.py imports nothing from the task-control/evidence plane (D-03: no task-evidence)."""
    source = _query_source()
    for forbidden in (
        "import tools.task_packet",
        "import tools.evidence",
        "import tools.task_control",
        "import tools.handoff",
    ):
        assert forbidden not in source, forbidden


def test_query_source_performs_no_file_io() -> None:
    """query.py performs no file I/O (D-03: preloads no contract body — in-memory adjacency)."""
    source = _query_source()
    assert "open(" not in source
    assert ".read_text(" not in source


# --- cycle-safety at scale + isolated-node robustness (Task 2) -----------------------------------


def test_transitive_terminates_with_two_independent_cycles() -> None:
    """Two independent cycles in a 5-node graph both terminate — visited-set bound is the proof."""
    graph = {
        "adjacency": {
            "a": ["b"],
            "b": ["a"],  # cycle 1: a <-> b
            "c": ["d"],
            "d": ["c"],  # cycle 2: c <-> d
            "e": ["a", "c"],  # e reaches both cycles
        }
    }
    # A plain function call is the assertion: no RecursionError / no hang thanks to the visited-set.
    result = transitive(graph, "e")
    assert result["ids"] == ["a", "b", "c", "d"]


def test_isolated_node_returns_empty_never_keyerror() -> None:
    """A node with no adjacency entry yields {'ids': [], 'paths': []} from all three queries."""
    graph = {"adjacency": {"a": ["b"]}}
    empty = {"ids": [], "paths": []}
    assert direct(graph, "isolated") == empty
    assert reverse(graph, "isolated") == empty
    assert transitive(graph, "isolated") == empty
