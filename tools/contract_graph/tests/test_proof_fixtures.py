"""TOPO-07 domain-neutral proof fixtures — the non-linear shapes the general relationship model
promises, proven against Plan-01's compiler and Plan-02's queries.

Every scenario in ``fixtures/graphs/valid/cases.json`` is a small list of domain-neutral relationship
records (no domain vocabulary, no instance-path tokens) forming one named non-linear topology:

* ``shared-contract-fanout``  — one authority, one contract, three dependents (fan-out).
* ``request-response-split``  — request and response modeled as TWO SEPARATE relationship records,
  not one bidirectional record.
* ``event-fanout``            — one authority publishing to N INDEPENDENT dependent relationships,
  each a distinct record.
* ``legal-cycle``             — a canonical multi-node cycle (a→b→c→a) that compiles clean AND on
  which ``transitive`` terminates.

Each scenario's records are wrapped into a synthetic cfg (``{"components": [...],
"contract_graph": {"relationships": [...]}}``, ``pipeline`` empty so ``effective_relationships``
unions cleanly with zero legacy edges) whose components are DERIVED from the records themselves —
every endpoint becomes a component, each authority ``produces`` its contract and each dependent
``consumes`` it — so the compiler resolves every endpoint and every authority owns its contract.

A final corpus-wide scan encodes the WR-01 disposition (DEFERRED code fix, fixture-vocabulary
constrained): every ``id`` / ``contract`` / ``authority`` / ``dependents[*]`` string across the ENTIRE
corpus is asserted to contain neither the substring ``/`` nor ``->`` — an automated, falsifiable
guard that the fixtures never trigger the non-injective lowered-id join (24-REVIEW.md WR-01), rather
than a documentation-only claim.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.contract_graph import compile_graph, transitive

# test_proof_fixtures.py -> tests -> contract_graph -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CASES_PATH = Path(__file__).resolve().parent / "fixtures" / "graphs" / "valid" / "cases.json"


def _load_corpus() -> list[dict]:
    return json.loads(_CASES_PATH.read_text(encoding="utf-8"))


def _scenario(name: str) -> list[dict]:
    """Return the record list for the named scenario (fails loud if the fixture is missing)."""
    for group in _load_corpus():
        if group["name"] == name:
            return group["records"]
    raise AssertionError(f"scenario {name!r} not found in fixture corpus {_CASES_PATH}")


def _cfg_from_records(records: list[dict]) -> dict:
    """Synthesize a compilable cfg from bare relationship records.

    Every endpoint (authority or dependent) becomes a declared component; each authority
    ``produces`` its record's contract and each dependent ``consumes`` it. This makes every endpoint
    resolvable and every authority the owner of its contract, so a well-formed scenario compiles with
    empty diagnostics — the fixture proves the SHAPE, not endpoint-declaration bookkeeping.
    """
    produces: dict[str, set[str]] = {}
    consumes: dict[str, set[str]] = {}
    for rel in records:
        produces.setdefault(rel["authority"], set()).add(rel["contract"])
        consumes.setdefault(rel["authority"], set())
        for dep in rel["dependents"]:
            consumes.setdefault(dep, set()).add(rel["contract"])
            produces.setdefault(dep, set())

    endpoints = sorted(set(produces) | set(consumes))
    components = [
        {
            "id": ep,
            "produces": sorted(produces.get(ep, set())),
            "consumes": sorted(consumes.get(ep, set())),
        }
        for ep in endpoints
    ]
    return {"components": components, "contract_graph": {"relationships": records}}


# --- non-linear shape proofs ---------------------------------------------------------------------


def test_shared_contract_fanout_compiles_clean() -> None:
    """One authority, one contract, three dependents → empty diagnostics; adjacency is the sorted trio."""
    records = _scenario("shared-contract-fanout")
    result = compile_graph(_cfg_from_records(records))
    assert result["diagnostics"] == []
    assert result["adjacency"]["hub"] == sorted(["leaf-alpha", "leaf-beta", "leaf-gamma"])


def test_request_response_are_two_separate_records() -> None:
    """Request and response are TWO distinct records (not one bidirectional record) → both directions
    appear as SEPARATE adjacency entries, all with empty diagnostics."""
    records = _scenario("request-response-split")
    assert len(records) == 2  # two distinct records, not one bidirectional record
    assert {r["id"] for r in records} == {"req-flow", "resp-flow"}
    result = compile_graph(_cfg_from_records(records))
    assert result["diagnostics"] == []
    # Each direction is its own adjacency edge — client→server AND server→client, independently.
    assert result["adjacency"]["client"] == ["server"]
    assert result["adjacency"]["server"] == ["client"]


def test_event_fanout_records_are_independent() -> None:
    """One authority publishing to N INDEPENDENT dependent relationships (each a distinct record) →
    empty diagnostics; the authority's adjacency is the sorted union of every subscriber."""
    records = _scenario("event-fanout")
    assert len(records) == 3  # three independent records, not one many-dependent record
    assert all(r["authority"] == "publisher" for r in records)
    result = compile_graph(_cfg_from_records(records))
    assert result["diagnostics"] == []
    assert result["adjacency"]["publisher"] == sorted(
        ["subscriber-one", "subscriber-two", "subscriber-three"]
    )


def test_legal_cycle_compiles_and_transitive_terminates() -> None:
    """A canonical multi-node cycle (node-a→node-b→node-c→node-a) compiles clean AND transitive()
    terminates, returning the sorted reachable set with the query node never re-entered as a
    dependent-of-itself entry."""
    records = _scenario("legal-cycle")
    graph = compile_graph(_cfg_from_records(records))
    assert graph["diagnostics"] == []
    assert graph["adjacency"]["node-a"] == ["node-b"]
    assert graph["adjacency"]["node-b"] == ["node-c"]
    assert graph["adjacency"]["node-c"] == ["node-a"]

    result = transitive(graph, "node-a")
    assert result["ids"] == ["node-b", "node-c"]  # terminates, start excluded, no double-count
    # Every recorded path starts at the query node and ends at its id — and never revisits node-a.
    for node_id, path in zip(result["ids"], result["paths"], strict=True):
        assert path[0] == "node-a"
        assert path[-1] == node_id
        assert path.count("node-a") == 1  # the start appears once, never re-entered


# --- WR-01 disposition: deferred fix, fixture vocabulary automatically constrained ---------------


def test_wr01_corpus_avoids_lowered_id_collision_vocabulary() -> None:
    """WR-01 (DEFERRED): every id/contract/authority/dependent string across the ENTIRE corpus
    excludes both ``/`` and ``->`` — an automated corpus scan proving the fixtures never exercise the
    non-injective lowered-id join, rather than a documentation-only claim."""
    forbidden = ("/", "->")
    offenders: list[str] = []
    for group in _load_corpus():
        for rel in group["records"]:
            strings = [rel["id"], rel["contract"], rel["authority"], *rel["dependents"]]
            for value in strings:
                for token in forbidden:
                    if token in value:
                        offenders.append(
                            f"scenario {group['name']!r} record {rel['id']!r}: "
                            f"{value!r} contains forbidden {token!r}"
                        )
    assert not offenders, "WR-01 fixture-vocabulary constraint violated:\n" + "\n".join(offenders)
