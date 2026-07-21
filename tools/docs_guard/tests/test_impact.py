"""DOCSUP-05 / D-12 — graph impact ids: real where the mapping resolves, EMPTY everywhere else.

Authored before ``impact.py`` and shown RED against a throwaway that fabricated an id from the
schema stem whenever the chain did not resolve. The verbatim output is in ``28-05-SUMMARY.md``.

The table's centre of gravity is the UNMAPPED cases, not the mapped one. Most human-doc sources are
not tracked contracts at all, so ``[]`` is the NORMAL, correct answer — and a fabricated id is
strictly worse than no id, because a report that names a wrong blast radius is trusted and acted
on. That is the ``OWNER_TBD`` never-fabricate house rule
(``tools/memory_regen/contracts_index.py:43-45``) applied to the graph.

Every case drives ``compile_graph(cfg=...)`` from an explicit in-memory cfg (the
``load_project(path=...)`` seam), so the suite is hermetic and does not move when
``harness/project.toml`` does.
"""

from __future__ import annotations

import pytest

from tools.docs_guard import impact

# A four-node chain: parser -> converter -> loader -> reporter. `produces` is declared so the
# compiler's contract-ownership check is satisfied without touching the live contracts/ tree.
CHAIN_CFG: dict = {
    "components": [
        {"id": "parser", "produces": ["greeting"]},
        {"id": "converter", "produces": ["converted"]},
        {"id": "loader", "produces": ["loaded"]},
        {"id": "reporter", "produces": []},
    ],
    "contract_graph": {
        "relationships": [
            {
                "id": "r-greeting",
                "contract": "greeting",
                "authority": "parser",
                "dependents": ["converter"],
            },
            {
                "id": "r-converted",
                "contract": "converted",
                "authority": "converter",
                "dependents": ["loader"],
            },
            {
                "id": "r-loaded",
                "contract": "loaded",
                "authority": "loader",
                "dependents": ["reporter"],
            },
        ]
    },
}

# A legal cycle. `query.transitive` is cycle-safe by construction (iterative visited-set worklist),
# but a hang in a CI gate is indistinguishable from a timeout, so it is ASSERTED, never assumed.
CYCLE_CFG: dict = {
    "components": [
        {"id": "alpha", "produces": ["ca"]},
        {"id": "beta", "produces": ["cb"]},
    ],
    "contract_graph": {
        "relationships": [
            {"id": "r-a", "contract": "ca", "authority": "alpha", "dependents": ["beta"]},
            {"id": "r-b", "contract": "cb", "authority": "beta", "dependents": ["alpha"]},
        ]
    },
}


def test_tracked_contract_yields_direct_and_transitive_ids() -> None:
    """The mapped case: contract path -> schema stem -> authority endpoint -> the query API."""
    assert impact.impact_ids(["contracts/sample/greeting.schema.json"], cfg=CHAIN_CFG) == [
        "converter",
        "loader",
        "reporter",
    ]


def test_midchain_contract_yields_only_its_downstream() -> None:
    """Under-delivery is the safe direction, but the mapped case must still be REAL — an impact
    list that always returned everything would be as useless as one that always returned nothing."""
    assert impact.impact_ids(["contracts/sample/converted.schema.json"], cfg=CHAIN_CFG) == [
        "loader",
        "reporter",
    ]


UNMAPPED_CASES: tuple[tuple[str, list[str]], ...] = (
    # A human doc is not a tracked contract. This is the COMMON case and must be empty, never a
    # guess — it is the input the docs report will hand this function most often.
    ("human_doc", ["docs/how-to/task-lifecycle.md"]),
    # A contracts/ path whose stem has no relationship record.
    ("untracked_stem", ["contracts/sample/untracked-name.schema.json"]),
    # A contracts/ path that is not a schema at all.
    ("not_a_schema", ["contracts/README.md"]),
    # Source code, and the empty input.
    ("source_file", ["src/one.py"]),
    ("empty", []),
)


@pytest.mark.parametrize(
    ("name", "paths"), UNMAPPED_CASES, ids=[case[0] for case in UNMAPPED_CASES]
)
def test_unmapped_paths_are_empty_never_fabricated(name: str, paths: list[str]) -> None:
    result = impact.impact_ids(paths, cfg=CHAIN_CFG)
    assert result == [], f"{name}: expected an empty impact list"
    # Belt and braces against a placeholder sneaking in instead of a real id.
    assert not any(token in result for token in ("TBD", "UNKNOWN", "?"))


def test_declared_contract_with_unresolvable_authority_is_empty() -> None:
    """28-RESEARCH.md's A5 mapping assumption is MEDIUM confidence. When it is wrong the ids come
    back EMPTY rather than incorrect, and that is precisely why this shape was chosen: the compiler
    records an ``unresolved-authority`` diagnostic and contributes no adjacency row, so the chain
    dead-ends instead of guessing."""
    cfg = {
        "components": [{"id": "known", "produces": ["kept"]}],
        "contract_graph": {
            "relationships": [
                {
                    "id": "r-ghost",
                    "contract": "ghost",
                    "authority": "never-declared",
                    "dependents": ["known"],
                }
            ]
        },
    }
    assert impact.impact_ids(["contracts/sample/ghost.schema.json"], cfg=cfg) == []


def test_leaf_authority_has_no_downstream() -> None:
    """``reporter`` produces nothing, so nothing depends on it — empty is correct, not a failure."""
    cfg = {
        "components": [{"id": "reporter", "produces": ["report"]}],
        "contract_graph": {
            "relationships": [
                {
                    "id": "r-report",
                    "contract": "report",
                    "authority": "reporter",
                    "dependents": [],
                }
            ]
        },
    }
    assert impact.impact_ids(["contracts/sample/report.schema.json"], cfg=cfg) == []


def test_results_are_sorted_and_deduplicated_across_inputs() -> None:
    """Two inputs whose blast radii overlap must not yield a duplicated id."""
    result = impact.impact_ids(
        [
            "contracts/sample/greeting.schema.json",
            "contracts/sample/converted.schema.json",
            "docs/how-to/unmapped.md",
        ],
        cfg=CHAIN_CFG,
    )
    assert result == ["converter", "loader", "reporter"]
    assert result == sorted(result)
    assert len(result) == len(set(result))


def test_repeated_calls_are_byte_identical() -> None:
    first = impact.impact_ids(["contracts/sample/greeting.schema.json"], cfg=CHAIN_CFG)
    second = impact.impact_ids(["contracts/sample/greeting.schema.json"], cfg=CHAIN_CFG)
    assert first == second


def test_cycle_terminates() -> None:
    """A legal cycle is just two adjacency entries pointing at each other. If this ever hangs, the
    gate hangs, and a hung CI gate is indistinguishable from a timeout."""
    assert impact.impact_ids(["contracts/sample/ca.schema.json"], cfg=CYCLE_CFG) == ["beta"]


def test_paths_are_never_returned_to_the_caller() -> None:
    """Research Q8 — ids only. ``paths`` from the query API are for the conductor tree render, not
    a docs report; leaking them would put endpoint chains in a human-doc remediation line."""
    result = impact.impact_ids(["contracts/sample/greeting.schema.json"], cfg=CHAIN_CFG)
    assert all(isinstance(entry, str) for entry in result)
    assert not any(isinstance(entry, list) for entry in result)


def test_module_performs_no_filesystem_write() -> None:
    """``impact.py`` is a PURE helper — no writes, no CLI (the plan's shape constraint)."""
    from pathlib import Path

    source = Path(impact.__file__).read_text(encoding="utf-8")
    for token in ("write_text", "write_bytes", "argparse", "shutil.copy"):
        assert token not in source, f"impact.py contains {token!r}"


# --- 28 IN-03 / DEBT-03: compile ONCE per report, not once per binding -------------------------
# These are the tests that go red if the batch entry point regresses to a per-binding loop. The
# equivalence test pins the ANSWER (a rearrangement, never a different result); the counting tests
# pin the SAVING (which equivalence alone cannot see, because a per-binding loop is equally correct
# and merely wasteful).

_THREE_BINDINGS = [
    {"id": "b-greeting", "sources": ["contracts/sample/greeting.schema.json"]},
    {"id": "b-converted", "sources": ["contracts/sample/converted.schema.json"]},
    {"id": "b-unmapped", "sources": ["docs/how-to/nothing.md"]},
]


def test_impact_map_equals_a_per_binding_impact_ids_loop() -> None:
    """The batch answer is byte-identical to the loop it replaces — including the EMPTY entries.

    If this ever diverges, the report's content changed, which is precisely what the compile-once
    rearrangement was not allowed to do.
    """
    batched = impact.impact_map(_THREE_BINDINGS, cfg=CHAIN_CFG)
    looped = {
        entry["id"]: impact.impact_ids(entry["sources"], cfg=CHAIN_CFG) for entry in _THREE_BINDINGS
    }
    assert batched == looped
    assert batched["b-unmapped"] == [], "an unmapped binding must be present with an EMPTY list"


def test_impact_map_compiles_the_graph_exactly_once(monkeypatch) -> None:
    """N bindings, ONE ``compile_graph`` and ONE ``effective_relationships`` call.

    Counting the live reads is the only way to observe 28 IN-03: the defect was never a wrong
    answer, it was the same config parsed and the same adjacency rebuilt once per binding to produce
    an answer that cannot vary between iterations. A per-binding loop passes every assertion about
    the RESULT, so the result cannot be what guards this.
    """
    calls: list[str] = []
    real_compile = impact.compile_graph
    real_relationships = impact.effective_relationships

    monkeypatch.setattr(
        impact, "compile_graph", lambda cfg: (calls.append("compile"), real_compile(cfg))[1]
    )
    monkeypatch.setattr(
        impact,
        "effective_relationships",
        lambda cfg: (calls.append("relationships"), real_relationships(cfg))[1],
    )

    impact.impact_map(_THREE_BINDINGS, cfg=CHAIN_CFG)

    assert calls.count("compile") == 1, f"compiled {calls.count('compile')}x for 3 bindings"
    assert calls.count("relationships") == 1


def test_impact_map_with_no_bindings_compiles_nothing(monkeypatch) -> None:
    """Zero bindings must not touch the config at all — the common case for a clean report."""
    calls: list[str] = []
    monkeypatch.setattr(impact, "compile_graph", lambda cfg: calls.append("compile"))
    monkeypatch.setattr(impact, "effective_relationships", lambda cfg: calls.append("rel"))

    assert impact.impact_map([], cfg=CHAIN_CFG) == {}
    assert calls == []


def test_impact_map_holds_no_state_between_calls() -> None:
    """No cache: the rejected alternative was memoizing inside a module that advertises purity.

    A second call with a DIFFERENT cfg must answer for that cfg, which a naive module-level memo
    keyed on nothing would get wrong.
    """
    first = impact.impact_map(_THREE_BINDINGS, cfg=CHAIN_CFG)
    other = impact.impact_map(
        [{"id": "b-ca", "sources": ["contracts/sample/ca.schema.json"]}], cfg=CYCLE_CFG
    )
    again = impact.impact_map(_THREE_BINDINGS, cfg=CHAIN_CFG)

    assert other == {"b-ca": ["beta"]}
    assert again == first, "a cfg-blind cache would have leaked the CYCLE_CFG answer back"
