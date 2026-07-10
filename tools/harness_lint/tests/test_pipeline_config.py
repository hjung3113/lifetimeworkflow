"""PIPE-01 topology CONSISTENCY gate — the generic [[components]] + [pipeline] slot in
harness/project.toml is well-formed and internally agrees (config = SSOT, no codegen).

Mirrors test_language_config.py's structural-scan idiom (repo root via parents[3], real config
loaded through the shared loader, iterate-config / assert-agreement / fail-loud). These checks run
against the GENERIC core default ONLY (source/sink/sample-record) — they must NOT reference any
`examples/` instance. A malformed topology (component naming an undeclared language, an edge with an
unknown endpoint, or a contract absent from the from-component's produces / to-component's consumes)
fails the suite loud so a broken config never resolves silently (T-8-01).
"""

from __future__ import annotations

from tools.harness_config import components, languages, load_project, pipeline


def _component_ids(cfg: dict) -> set[str]:
    return {c["id"] for c in components(cfg)}


def test_component_languages_are_declared() -> None:
    """Every component's `language` names a declared [[languages]].id (cross-slot agreement).

    A component pointing at an undeclared toolchain is a topology the conductor cannot route —
    fail loud naming the offending component id.
    """
    cfg = load_project()
    declared = {lang["id"] for lang in languages(cfg)}
    for comp in components(cfg):
        assert comp["language"] in declared, (
            f"component {comp['id']!r}: language {comp['language']!r} is not a declared "
            f"[[languages]].id (declared: {sorted(declared)})"
        )


def test_component_ids_unique() -> None:
    """No two components share an `id` (a duplicate makes edge endpoints ambiguous)."""
    ids = [c["id"] for c in components(load_project())]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate component id(s): {dupes}"


def test_pipeline_edges_are_well_formed() -> None:
    """Every [pipeline] edge is well-formed against the declared components.

    For each edge: `from`/`to` name declared components, and `contract` is BOTH in the
    from-component's `produces` AND the to-component's `consumes`. A dangling endpoint or a
    contract the endpoints do not actually exchange is a malformed topology — fail loud.
    """
    cfg = load_project()
    by_id = {c["id"]: c for c in components(cfg)}
    for edge in pipeline(cfg).get("edges", []):
        src, dst, contract = edge["from"], edge["to"], edge["contract"]
        assert src in by_id, f"edge {edge!r}: `from` {src!r} is not a declared component"
        assert dst in by_id, f"edge {edge!r}: `to` {dst!r} is not a declared component"
        assert contract in by_id[src].get("produces", []), (
            f"edge {edge!r}: contract {contract!r} not in {src!r}.produces "
            f"({by_id[src].get('produces', [])})"
        )
        assert contract in by_id[dst].get("consumes", []), (
            f"edge {edge!r}: contract {contract!r} not in {dst!r}.consumes "
            f"({by_id[dst].get('consumes', [])})"
        )
