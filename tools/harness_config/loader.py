"""Thin stdlib loader over the GEN-03 project-config slot (D-03).

Reads ``harness/project.toml`` — the harness's language/toolchain SINGLE SOURCE OF TRUTH — with
stdlib ``tomllib`` (guaranteed by ``requires-python >=3.11``; no external dep). Pure I/O + shape:
NO enforcement logic (that belongs to the consistency test in ``tools.harness_lint``). Keep the
signatures stable — the Phase-6 config-derived CI matrix will import ``language_bash_scopes``.

Semantics:
  * ``load_project`` — parse the TOML into a plain dict (``instance`` table + ``languages`` list).
  * ``language_bash_scopes`` — the set of bash allow-scopes the participating languages imply: the
    union of each language's ``bash_scope`` PLUS the implicit ``"pytest *"`` (Python's test-runner
    carries its own permission-matrix allow-scope alongside ``uv *``). This is exactly the set the
    permission-matrix's language allow-scopes must equal (config = SSOT).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# Repo-root-anchored default so the loader works regardless of the caller's cwd.
# loader.py -> harness_config -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PROJECT = _REPO_ROOT / "harness" / "project.toml"

# Python's test runner carries its own permission-matrix allow-scope ("pytest *") distinct from the
# language's own "uv *" bash_scope. It is implicit in the config (not a per-language field) so the
# SSOT need not repeat it; the helper folds it into the derived scope set.
_IMPLICIT_TEST_SCOPES = frozenset({"pytest *"})


def load_project(path: str | Path = _DEFAULT_PROJECT) -> dict:
    """Load the GEN-03 project config (``harness/project.toml``) as a plain dict.

    Opens in **binary** mode (``tomllib.load`` requires it). Shared by the loader tests and the
    consistency gate so there is exactly one reader of the SSOT slot.
    """
    with Path(path).open("rb") as fh:
        return tomllib.load(fh)


def languages(cfg: dict | None = None) -> list[dict]:
    """Return the configured ``[[languages]]`` tables (loads the default config if omitted).

    Raw passthrough: legs MAY carry an optional ``test_paths`` list (consumed by the Phase-6 CI
    matrix via ``l.get("test_paths", [])``); it flows through unchanged with no signature change.
    """
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("languages", []))


def components(cfg: dict | None = None) -> list[dict]:
    """Return the configured ``[[components]]`` tables (loads the default config if omitted).

    Raw passthrough (mirrors ``languages()``): the pipeline-topology DATA slot flows through
    unchanged — NO enforcement here. The topology consistency gate
    (``tools/harness_lint/tests/test_pipeline_config.py``) owns the well-formedness checks.
    """
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("components", []))


def pipeline(cfg: dict | None = None) -> dict:
    """Return the ``[pipeline]`` table (loads the default config if omitted).

    Raw passthrough: the ``edges`` list (and any future additive keys) flow through unchanged.
    Consistency (endpoints declared, contract in produces/consumes) is enforced by the gate, not
    here.
    """
    if cfg is None:
        cfg = load_project()
    return dict(cfg.get("pipeline", {}))


def contract_graph_relationships(cfg: dict | None = None) -> list[dict]:
    """Return the ``[[contract_graph.relationships]]`` tables (loads the default config if omitted).

    Raw passthrough (mirrors ``components()`` / ``pipeline()``): the TOPO-02 contract-relationship
    DATA slot flows through UNCHANGED — NO validation, traversal, discovery, or policy (D-03). The
    two-level ``.get`` mirrors ``workspace_config.edges``: ``[[contract_graph.relationships]]``
    parses to ``cfg["contract_graph"]["relationships"]``. Graph resolution is Phase-25 compiler work.
    """
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("contract_graph", {}).get("relationships", []))


def effective_relationships(cfg: dict | None = None) -> list[dict]:
    """Lower every legacy ``[pipeline].edges`` entry to an authority/dependent relationship and union
    it with the explicit ``[[contract_graph.relationships]]`` records (TOPO-03).

    Lowering (D-04): each edge ``{from, to, contract}`` becomes
    ``{"id": "pipeline/<contract>/<from>-><to>", "contract": contract, "authority": from,
    "dependents": [to]}`` — the namespaced id can never collide with a human-authored explicit id.
    ``from`` / ``to`` are treated as OPAQUE strings and passed through verbatim: this function never
    calls ``split_endpoint`` or interprets a ``repo:`` half (that resolution is Phase 25). Because it
    reads only ``cfg["pipeline"]["edges"]`` + ``cfg["contract_graph"]["relationships"]`` — both plain
    dict/list shapes present in BOTH ``load_project()`` and ``load_workspace()`` output — the same
    function serves project and workspace configs.

    The merged list is stable-sorted by ``id`` for deterministic output (no ``set`` iteration order
    or wall-clock in the output path). Raises ``ValueError`` with a deterministic, stable-sorted
    diagnostic on any of the three failure modes (D-05):

    * (a) **duplicate id** — the same ``id`` appears on two records;
    * (b) **duplicate semantic edge** — the same ``(authority, contract, dependent)`` triple appears
      twice (every record's ``dependents`` list is expanded into one triple per dependent first);
    * (c) **contradiction** — one ``contract`` is claimed by two different ``authority`` values.

    Pure: no I/O beyond the passed/loaded ``cfg`` dict.
    """
    if cfg is None:
        cfg = load_project()

    lowered = [
        {
            "id": f"pipeline/{edge['contract']}/{edge['from']}->{edge['to']}",
            "contract": edge["contract"],
            "authority": edge["from"],
            "dependents": [edge["to"]],
        }
        for edge in cfg.get("pipeline", {}).get("edges", [])
    ]
    merged = lowered + contract_graph_relationships(cfg)

    # (a) duplicate id — deterministic (sorted) diagnostic.
    id_seen: set[str] = set()
    dup_ids: set[str] = set()
    for rel in merged:
        rid = rel["id"]
        if rid in id_seen:
            dup_ids.add(rid)
        id_seen.add(rid)
    if dup_ids:
        raise ValueError(
            "effective_relationships: duplicate relationship id(s): " + ", ".join(sorted(dup_ids))
        )

    # (b) duplicate semantic edge — expand each record to (authority, contract, dependent) triples.
    triple_seen: set[tuple[str, str, str]] = set()
    dup_triples: set[tuple[str, str, str]] = set()
    # (c) contradiction — one contract mapped to more than one distinct authority.
    contract_authorities: dict[str, set[str]] = {}
    for rel in merged:
        authority = rel["authority"]
        contract = rel["contract"]
        contract_authorities.setdefault(contract, set()).add(authority)
        for dependent in rel["dependents"]:
            triple = (authority, contract, dependent)
            if triple in triple_seen:
                dup_triples.add(triple)
            triple_seen.add(triple)
    if dup_triples:
        raise ValueError(
            "effective_relationships: duplicate semantic edge(s) (authority, contract, dependent): "
            + ", ".join(str(t) for t in sorted(dup_triples))
        )

    contradictions = {
        contract: authorities
        for contract, authorities in contract_authorities.items()
        if len(authorities) > 1
    }
    if contradictions:
        detail = ", ".join(
            f"{contract} claimed by {sorted(authorities)}"
            for contract, authorities in sorted(contradictions.items())
        )
        raise ValueError(
            "effective_relationships: contradiction — contract claimed by multiple authorities: "
            + detail
        )

    return sorted(merged, key=lambda rel: rel["id"])


def language_bash_scopes(cfg: dict | None = None) -> set[str]:
    """Return the derived set of bash allow-scopes: union of ``languages[*].bash_scope`` + implicit
    ``"pytest *"``. This is the set the permission-matrix language allow-scopes must equal."""
    scopes = {lang["bash_scope"] for lang in languages(cfg) if lang.get("bash_scope")}
    return scopes | set(_IMPLICIT_TEST_SCOPES)
