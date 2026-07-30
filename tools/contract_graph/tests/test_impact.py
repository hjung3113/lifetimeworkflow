"""MONO-08 impact-reporter tests — the five behaviors, all on synthetic fixtures.

The live graph is EMPTY on this checkout (``compile_graph()`` on the default core config returns
``{"relationships": [], "adjacency": {}, "diagnostics": []}`` — CER-08 removed the core
``[pipeline].edges``). Every real contract therefore hits clean-refusal today, so the traversal and
composition behaviour cannot be exercised against the live tree at all — every fixture here is a
hand-built synthetic ``cfg`` dict, mirroring ``test_compile.py``'s domain-neutral ``"a"``/``"b"``/
``"widget"`` idiom. Never a literal instance-directory path (GEN-04).

Five behaviors covered, one section each:

1. Traversal reuse over a multi-hop fixture — ``report()``'s direct/reverse/transitive values are
   the SAME as calling ``query.py``'s three functions directly on the same compiled graph.
2. Affected-package attribution — a node in the affected set with a matching ``facts`` package
   entry appears in ``affected_packages``.
3. No-second-traversal-engine structural check — extended per the plan-checker's strengthened
   requirement to ALSO catch a ``for``-over-``adjacency`` re-implementation and any locally-defined
   recursive function, not just a ``while``-shaped re-implementation. Mutation-tested against two
   synthetic violation stubs (a while-frontier stub and a for-over-adjacency stub) to prove the
   check itself is not a check that cannot fail.
4. Three-way distinguishable outcomes — refused / resolved-but-isolated / resolved-with-affected-set
   are asserted to differ (or match) by KEY SET, never by prose alone.
5. Determinism — two calls to ``report()`` on the same graph + contract_path are byte-identical.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from tools.contract_graph import compile_graph, direct, reverse, transitive
from tools.contract_graph import impact as impact_module
from tools.contract_graph.impact import report

# --- shared synthetic fixture (domain-neutral: a/b/c/d, contract "widget") ------------------------


def _fan_out_cfg() -> dict:
    """One authority 'a' fanning out to 'b'/'c'/'d' via contract 'widget' (mirrors
    test_compile.py's test_fan_out_compiles_clean shape)."""
    return {
        "components": [
            {"id": "a", "produces": ["widget"], "consumes": [], "language": "py"},
            {"id": "b", "produces": [], "consumes": ["widget"], "language": "py"},
            {"id": "c", "produces": [], "consumes": ["widget"], "language": "py"},
            {"id": "d", "produces": [], "consumes": ["widget"], "language": "py"},
        ],
        "languages": [{"id": "py", "persona": "harness/agents/py-engineer.md"}],
        "contract_graph": {
            "relationships": [
                {"id": "r1", "contract": "widget", "authority": "a", "dependents": ["b", "c", "d"]},
            ]
        },
    }


# --- behavior 1: traversal reuse over a multi-hop fixture -----------------------------------------


def test_report_composes_direct_reverse_transitive_not_rederived() -> None:
    """report()'s direct/reverse/transitive are the SAME values query.py's functions return
    for the resolved node — proof of composition, not re-derivation."""
    cfg = _fan_out_cfg()
    graph = compile_graph(cfg)
    result = report("contracts/sample/widget.schema.json", cfg=cfg)
    assert result["resolved"] is True
    assert result["node"] == "a"
    assert result["direct"] == direct(graph, "a")
    assert result["reverse"] == reverse(graph, "a")
    assert result["transitive"] == transitive(graph, "a")


def test_report_accepts_a_bare_node_id_directly() -> None:
    """A bare node id (already a key/value in adjacency) resolves without contract-id lookup."""
    cfg = _fan_out_cfg()
    result = report("b", cfg=cfg)
    assert result["resolved"] is True
    assert result["node"] == "b"
    assert result["contract_id"] is None


# --- behavior 2: affected-package attribution ------------------------------------------------------


def test_affected_packages_include_a_matching_facts_entry() -> None:
    """A facts["packages"] entry whose id matches an affected node id (and has a 'dir' key)
    appears in affected_packages."""
    cfg = _fan_out_cfg()
    facts = {
        "packages": [
            {"id": "a", "dir": "pkg/a"},
            {"id": "b", "dir": "pkg/b"},
            {"id": "unaffected", "dir": "pkg/unaffected"},
        ]
    }
    result = report("contracts/sample/widget.schema.json", cfg=cfg, facts=facts)
    assert "a" in result["affected_packages"]
    assert "b" in result["affected_packages"]
    assert "unaffected" not in result["affected_packages"]


def test_affected_packages_excludes_declared_only_components_with_no_dir() -> None:
    """A facts package record with no 'dir' key (declared-only) never reaches owning_package() and
    never appears in affected_packages — the Phase-48 adapter filter is applied, not bypassed."""
    cfg = _fan_out_cfg()
    facts = {"packages": [{"id": "c"}]}  # no "dir" key
    result = report("contracts/sample/widget.schema.json", cfg=cfg, facts=facts)
    assert "c" not in result["affected_packages"]


# --- behavior 3: no-second-traversal-engine structural check (strengthened) -----------------------


def _traversal_violations(source: str) -> list[str]:
    """Return a list of violation tags found in ``source``, empty on a clean pass.

    WR-01 (49-REVIEW.md): the original three-shape check was itself a "check that cannot fail" —
    provably evadable by a one-line variable alias, a set-comprehension, or mutual recursion, none
    of which are exotic rewrites. Strengthened to catch six shapes (three original + three evasions
    demonstrated live in the review):

    1. Any ``ast.While`` node (a hand-rolled frontier/worklist loop).
    2. Any ``ast.For`` node whose iterated expression's source mentions "adjacency" OR names a
       simple local alias assigned from an expression mentioning "adjacency" (``adj =
       graph["adjacency"]; for node in adj:`` no longer evades the substring test by aliasing).
    3. Any comprehension (``ast.comprehension`` — covers list/set/dict comprehensions and generator
       expressions) whose iterated expression mentions "adjacency" or an adjacency alias — not just
       literal ``ast.For`` loops.
    4. Any call-graph CYCLE among module-level functions — a function that (transitively) calls
       itself, whether directly (self-recursion) or via one or more intermediate functions (mutual
       recursion, e.g. ``_walk_a`` calling ``_walk_b`` calling ``_walk_a`` back) — not just a
       function calling itself by its own literal name.
    """
    tree = ast.parse(source)
    violations: list[str] = []

    # Track simple local aliases of an adjacency-mentioning expression (`name = <expr>`), so a
    # for-loop/comprehension iterating the ALIAS is still caught, not just the literal expression.
    adjacency_aliases: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and "adjacency" in ast.unparse(node.value)
        ):
            adjacency_aliases.add(node.targets[0].id)

    def _mentions_adjacency(iter_node: ast.AST) -> str | None:
        iter_src = ast.unparse(iter_node)
        if "adjacency" in iter_src:
            return iter_src
        if isinstance(iter_node, ast.Name) and iter_node.id in adjacency_aliases:
            return iter_src
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            violations.append("while-loop")

    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            hit = _mentions_adjacency(node.iter)
            if hit is not None:
                violations.append(f"for-over-adjacency: {hit}")
        elif isinstance(node, ast.comprehension):
            hit = _mentions_adjacency(node.iter)
            if hit is not None:
                violations.append(f"comprehension-over-adjacency: {hit}")

    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    call_graph: dict[str, set[str]] = {fn.name: set() for fn in funcs}
    for fn in funcs:
        for node in ast.walk(fn):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in call_graph
            ):
                call_graph[fn.name].add(node.func.id)

    for start in call_graph:
        stack: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]
        visited: set[str] = set()
        while stack:
            current, path = stack.pop()
            for callee in call_graph.get(current, ()):
                if callee == start:
                    violations.append(f"recursive-function: {' -> '.join((*path, callee))}")
                elif callee not in visited:
                    visited.add(callee)
                    stack.append((callee, (*path, callee)))

    return violations


def _impact_source() -> str:
    return Path(impact_module.__file__).read_text(encoding="utf-8")


def test_impact_module_calls_the_three_query_functions_and_defines_no_second_engine() -> None:
    """impact.py calls direct()/reverse()/transitive() by name AND the extended structural check
    (while-loop / for-over-adjacency / local recursion) finds zero violations in its own source."""
    source = _impact_source()
    assert "direct(" in source and "reverse(" in source and "transitive(" in source
    assert _traversal_violations(source) == []


# Mutation-test the extended check itself: it must actually trip on both re-implementation shapes,
# not just the while-shaped one. Each stub below is a synthetic (never impact.py's real source)
# module string standing in for a hypothetical re-implementation.


def test_check_traps_a_while_frontier_stub() -> None:
    """A synthetic while-frontier re-implementation trips the check (shape 1)."""
    stub = (
        "def report(contract_path, cfg=None, graph=None, facts=None):\n"
        "    frontier = [contract_path]\n"
        "    visited = set()\n"
        "    while frontier:\n"
        "        current = frontier.pop(0)\n"
        "        visited.add(current)\n"
        "    return {'resolved': True}\n"
    )
    violations = _traversal_violations(stub)
    assert any(v == "while-loop" for v in violations), violations


def test_check_traps_a_for_over_adjacency_stub() -> None:
    """A synthetic for-over-adjacency re-implementation trips the check (shape 2) — the plan-
    checker's warning: a while-only check would NOT catch this shape."""
    stub = (
        "def report(contract_path, cfg=None, graph=None, facts=None):\n"
        "    graph = compile_graph(cfg)\n"
        "    reached = set()\n"
        "    for node in graph['adjacency']:\n"
        "        reached.add(node)\n"
        "    return {'resolved': True}\n"
    )
    violations = _traversal_violations(stub)
    assert any(v.startswith("for-over-adjacency") for v in violations), violations


# WR-01 (49-REVIEW.md) regression tests: the pre-fix check was evadable by three unremarkable
# rewrites of the SAME violation. Each stub reproduces one evasion verbatim from the review.


def test_check_traps_a_variable_alias_evasion_stub() -> None:
    """`adj = graph["adjacency"]; for node in adj:` no longer evades the for-loop rule by aliasing
    the dict to an ordinary name before the loop (WR-01 evasion 1)."""
    stub = (
        "def report(contract_path, cfg=None, graph=None, facts=None):\n"
        "    adj = graph['adjacency']\n"
        "    reached = set()\n"
        "    for node in adj:\n"
        "        reached.add(node)\n"
        "    return {'resolved': True}\n"
    )
    violations = _traversal_violations(stub)
    assert any(v.startswith("for-over-adjacency") for v in violations), violations


def test_check_traps_a_set_comprehension_evasion_stub() -> None:
    """`{n for n in graph["adjacency"]}` is an ast.SetComp, not an ast.For — the comprehension rule
    inspects it too (WR-01 evasion 2)."""
    stub = (
        "def report(contract_path, cfg=None, graph=None, facts=None):\n"
        "    reached = {n for n in graph['adjacency']}\n"
        "    return {'resolved': True}\n"
    )
    violations = _traversal_violations(stub)
    assert any(v.startswith("comprehension-over-adjacency") for v in violations), violations


def test_check_traps_a_mutual_recursion_evasion_stub() -> None:
    """Two module-level helpers that call each other (`_walk_a` -> `_walk_b` -> `_walk_a`)
    implement a hand-rolled recursive walk with neither calling itself by its own name — the
    call-graph-cycle rule catches the cycle regardless of direction (WR-01 evasion 3)."""
    stub = (
        "def _walk_a(node, graph, visited):\n"
        "    visited.add(node)\n"
        "    return _walk_b(node, graph, visited)\n"
        "\n"
        "def _walk_b(node, graph, visited):\n"
        "    return _walk_a(node, graph, visited)\n"
        "\n"
        "def report(contract_path, cfg=None, graph=None, facts=None):\n"
        "    return {'resolved': True}\n"
    )
    violations = _traversal_violations(stub)
    assert any(v.startswith("recursive-function") for v in violations), violations


# --- behavior 3b: behavioural equivalence, independent of AST shape entirely -----------------------


def test_report_affected_sets_exactly_match_query_functions_for_every_traversal_direction() -> None:
    """A BEHAVIOURAL proof that does not depend on impact.py's source shape at all (WR-01,
    49-REVIEW.md): on a multi-node fixture, report()'s direct/reverse/transitive payloads are
    exactly what calling query.py's three functions directly returns for the SAME node — for every
    node in the fixture, not just one. A re-implemented walk that disagreed anywhere on ids, paths,
    or ordering would fail this regardless of how cleverly it was written (no AST pattern to evade)."""
    cfg = _fan_out_cfg()
    graph = compile_graph(cfg)
    for node_id, contract_path in (
        ("a", "contracts/sample/widget.schema.json"),
        ("b", "b"),
        ("c", "c"),
        ("d", "d"),
    ):
        result = report(contract_path, cfg=cfg)
        assert result["resolved"] is True
        assert result["node"] == node_id
        assert result["direct"] == direct(graph, node_id)
        assert result["reverse"] == reverse(graph, node_id)
        assert result["transitive"] == transitive(graph, node_id)


# --- behavior 4: three-way distinguishable outcomes (refused / isolated / affected) ---------------


def test_refused_isolated_and_affected_reports_are_key_set_distinguishable() -> None:
    """The refused shape's key set differs from the resolved shapes'; isolated and affected share
    the same key set (both are legitimately resolved — the distinction is the 'isolated' value,
    never a shape difference)."""
    cfg = _fan_out_cfg()
    # Extend the fixture with a genuinely isolated node: authority "iso" with zero dependents.
    cfg["components"].append(
        {"id": "iso", "produces": ["gadget"], "consumes": [], "language": "py"}
    )
    cfg["contract_graph"]["relationships"].append(
        {"id": "r2", "contract": "gadget", "authority": "iso", "dependents": []}
    )

    refused = report("contracts/sample/does-not-exist.schema.json", cfg=cfg)
    isolated = report("contracts/sample/gadget.schema.json", cfg=cfg)
    affected = report("contracts/sample/widget.schema.json", cfg=cfg)

    assert refused["resolved"] is False
    assert "node" not in refused
    assert "isolated" not in refused

    assert isolated["resolved"] is True
    assert isolated["isolated"] is True
    assert "node" in isolated

    assert affected["resolved"] is True
    assert affected["isolated"] is False

    assert set(refused.keys()) != set(isolated.keys())
    assert set(isolated.keys()) == set(affected.keys())


def test_isolated_node_resolves_identically_via_bare_id_and_via_contract_path() -> None:
    """CR-02 (49-REVIEW.md) regression: a legitimately isolated authority ('iso', zero dependents)
    must resolve the SAME way whether addressed by its contract path or its bare node id — not
    silently refused when addressed directly by id. The pre-fix `contract_path in adjacency or
    any(contract_path in deps ...)` check falsely refused this because compile_graph() never lists
    a zero-dependent authority in adjacency at all."""
    cfg = _fan_out_cfg()
    cfg["components"].append(
        {"id": "iso", "produces": ["gadget"], "consumes": [], "language": "py"}
    )
    cfg["contract_graph"]["relationships"].append(
        {"id": "r2", "contract": "gadget", "authority": "iso", "dependents": []}
    )

    via_path = report("contracts/sample/gadget.schema.json", cfg=cfg)
    via_bare_id = report("iso", cfg=cfg)

    assert via_path["resolved"] is True
    assert via_bare_id["resolved"] is True
    assert via_path["isolated"] is True
    assert via_bare_id["isolated"] is True
    assert via_path["node"] == via_bare_id["node"] == "iso"


# --- behavior 5: determinism -----------------------------------------------------------------------


def test_report_is_deterministic_across_repeated_calls() -> None:
    """Two report() calls with the identical cfg/contract_path return byte-identical (==) dicts."""
    cfg = _fan_out_cfg()
    first = report("contracts/sample/widget.schema.json", cfg=cfg)
    second = report("contracts/sample/widget.schema.json", cfg=cfg)
    assert first == second


def test_report_json_dump_is_deterministic_across_repeated_calls() -> None:
    """json.dumps(report(...), sort_keys=True) is string-identical across repeated invocations —
    proves determinism survives the exact serialization main() uses."""
    cfg = _fan_out_cfg()
    dump_a = json.dumps(report("contracts/sample/widget.schema.json", cfg=cfg), sort_keys=True)
    dump_b = json.dumps(report("contracts/sample/widget.schema.json", cfg=cfg), sort_keys=True)
    assert dump_a == dump_b


# --- behavior 6: CR-01 path-containment (traversal/collision) refusal ------------------------------


def test_traversal_path_is_refused_not_collided_onto_the_real_contract() -> None:
    """CR-01 (49-REVIEW.md) regression: a `../` traversal path that merely ENDS in the real
    contract's filename must NOT resolve to the same node as the real path — it must be refused.
    Pre-fix, both returned byte-identical, fully-confident reports."""
    cfg = _fan_out_cfg()
    real = report("contracts/sample/widget.schema.json", cfg=cfg)
    bogus = report("contracts/WRONG-DIR/../../etc/widget.schema.json", cfg=cfg)

    assert real["resolved"] is True
    assert bogus["resolved"] is False
    assert bogus.get("contract_id") is None


def test_absolute_traversal_path_is_refused() -> None:
    """An absolute path is rejected outright — never treated as a resolvable contract path."""
    cfg = _fan_out_cfg()
    result = report("/etc/widget.schema.json", cfg=cfg)
    assert result["resolved"] is False
    assert result.get("contract_id") is None


def test_multi_dot_contract_filename_resolves_by_full_suffix_strip() -> None:
    """A `<pkg>.<name>.schema.json`-style multi-dot filename still strips exactly the
    `.schema.json` suffix (not just the last dot-segment) to derive its candidate id."""
    cfg = _fan_out_cfg()
    cfg["contract_graph"]["relationships"].append(
        {"id": "r3", "contract": "a.b", "authority": "a", "dependents": ["b"]}
    )
    result = report("contracts/sample/a.b.schema.json", cfg=cfg)
    assert result["resolved"] is True
    assert result["contract_id"] == "a.b"


def test_contract_path_with_no_extension_derives_the_whole_filename_as_candidate_id() -> None:
    """A path with no `.schema.json` extension derives a candidate id equal to the whole filename
    (removesuffix is a no-op) — refused when no relationship names that exact id, never crashes on
    the missing extension."""
    cfg = _fan_out_cfg()
    result = report("contracts/sample/widget-no-ext", cfg=cfg)
    assert result["resolved"] is False
    assert result["contract_id"] == "widget-no-ext"


def test_empty_string_contract_path_is_refused() -> None:
    """An empty string is refused cleanly — never crashes, never collides with a real contract."""
    cfg = _fan_out_cfg()
    result = report("", cfg=cfg)
    assert result["resolved"] is False


def test_trailing_slash_contract_path_is_refused() -> None:
    """A path with a trailing slash (its filename component is empty) is refused cleanly."""
    cfg = _fan_out_cfg()
    result = report("contracts/sample/", cfg=cfg)
    assert result["resolved"] is False


# --- behavior 8: WR-02 "searched" is actually informative ------------------------------------------


def test_refusal_searched_field_names_the_contract_ids_actually_checked() -> None:
    """WR-02 (49-REVIEW.md) regression: 'searched' is the sorted list of contract ids checked, not
    a bare count that is identical for every refusal regardless of what was searched."""
    cfg = _fan_out_cfg()
    result = report("contracts/sample/does-not-exist.schema.json", cfg=cfg)
    assert result["resolved"] is False
    assert result["searched"] == ["widget"]


# --- behavior 9: WR-03 contract_owner is never attributed from an unvalidated path ------------------


def test_contract_owner_is_null_for_a_traversal_path_never_root_fallback_attributed() -> None:
    """WR-03 (49-REVIEW.md) regression: a refused (traversal) path must never reach
    owning_package() at all — no confident, root-fallback-attributed contract_owner leaks through
    for a path that failed CR-01's containment check."""
    cfg = _fan_out_cfg()
    facts = {"packages": [{"id": "a", "dir": "."}]}  # root package would match EVERY path.
    result = report("contracts/WRONG-DIR/../../etc/widget.schema.json", cfg=cfg, facts=facts)
    assert result["resolved"] is False
    assert "contract_owner" not in result


# --- behavior 7: CR-03 refusal vs. internal-error exit codes are distinct --------------------------


def test_main_exits_1_on_clean_refusal_and_3_on_internal_error_not_the_same_code() -> None:
    """CR-03 (49-REVIEW.md) regression: a clean refusal and an unhandled exception from report()'s
    dependencies must NOT share exit code 1 — refusal is 1, an internal error is 3."""
    refusal_exit = impact_module.main(["definitely-not-a-real-node"])
    assert refusal_exit == 1

    def _boom(*args: object, **kwargs: object) -> dict:
        raise ValueError("boom")

    original_report = impact_module.report
    impact_module.report = _boom
    try:
        crash_exit = impact_module.main(["anything"])
    finally:
        impact_module.report = original_report

    assert crash_exit == 3
    assert crash_exit != refusal_exit


# --- behavior 10: WR-04 malformed-package diagnostic parity with conventions_for() ------------------


def test_malformed_package_record_prints_the_same_stderr_diagnostic_as_conventions_for(
    capsys,
) -> None:
    """WR-04 (49-REVIEW.md) regression: a facts package record with 'manifest' but no 'dir' (the
    malformed-record case, not a legitimate declared-only component) prints an stderr diagnostic —
    the exact case conventions_for() already surfaces at its sibling call site, no longer silently
    dropped here."""
    cfg = _fan_out_cfg()
    facts = {"packages": [{"id": "a", "manifest": "some/manifest.json"}]}
    report("contracts/sample/widget.schema.json", cfg=cfg, facts=facts)
    captured = capsys.readouterr()
    assert "manifest" in captured.err
    assert "dir" in captured.err
