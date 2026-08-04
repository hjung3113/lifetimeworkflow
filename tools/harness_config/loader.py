"""Thin stdlib loader over the GEN-03 project-config slot (D-03).

Reads ``harness/project.toml`` — the harness's language/toolchain SINGLE SOURCE OF TRUTH — with
stdlib ``tomllib`` (guaranteed by ``requires-python >=3.11``; no external dep). Pure I/O + shape:
NO enforcement logic (that belongs to the consistency test in ``tools.harness_lint``). Keep the
signatures stable — the Phase-6 config-derived CI matrix will import ``language_bash_scopes``.
Also home to ``conventions_for`` (MONO-05/MONO-06) — the nearest-wins join between package facts
and the ``[[languages]]`` config that answers "which conventions apply at this path?".

Semantics:
  * ``load_project`` — parse the TOML into a plain dict (``instance`` table + ``languages`` list).
  * ``language_bash_scopes`` — the set of bash allow-scopes the participating languages imply: the
    union of each language's ``bash_scope`` PLUS the implicit ``"pytest *"`` (Python's test-runner
    carries its own permission-matrix allow-scope alongside ``uv *``). This is exactly the set the
    permission-matrix's language allow-scopes must equal (config = SSOT).
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from tools.contract_graph import owning_package

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
    parses to ``cfg["contract_graph"]["relationships"]``. Graph resolution is Phase-25 compiler
    work.
    """
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("contract_graph", {}).get("relationships", []))


def effective_relationships(cfg: dict | None = None) -> list[dict]:
    """Lower every legacy ``[pipeline].edges`` entry to an authority/dependent relationship and
    union it with the explicit ``[[contract_graph.relationships]]`` records (TOPO-03).

    Lowering (D-04): each edge ``{from, to, contract}`` becomes
    ``{"id": "pipeline/<contract>/<from>-><to>", "contract": contract, "authority": from,
    "dependents": [to]}`` — the namespaced id can never collide with a human-authored explicit id.
    ``from`` / ``to`` are treated as OPAQUE strings and passed through verbatim: this function
    never calls ``split_endpoint`` or interprets a ``repo:`` half (that resolution is Phase 25).
    Because it reads only ``cfg["pipeline"]["edges"]`` + ``cfg["contract_graph"]["relationships"]``
    — both plain dict/list shapes present in BOTH ``load_project()`` and ``load_workspace()``
    output — the same function serves project and workspace configs.

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

    # (WR-02) Guard malformed local shape BEFORE indexing. The lowering comprehension indexes
    # edge['contract'/'from'/'to'] and the dedup loops index rel['id'/'contract'/'authority'/
    # 'dependents']; a raw edge or explicit record missing any required key must surface a
    # ValueError naming the offending record — never an opaque bare KeyError. This is an additive
    # guard only: signature and return shape are unchanged (this is NOT endpoint/graph resolution,
    # which stays deferred to the Phase-25 compiler).
    raw_edges = cfg.get("pipeline", {}).get("edges", [])
    for edge in raw_edges:
        missing = {"from", "to", "contract"} - edge.keys()
        if missing:
            raise ValueError(
                f"effective_relationships: pipeline edge missing key(s) {sorted(missing)}: {edge!r}"
            )
    for rel in contract_graph_relationships(cfg):
        missing = {"id", "contract", "authority", "dependents"} - rel.keys()
        if missing:
            raise ValueError(
                "effective_relationships: relationship record missing key(s) "
                f"{sorted(missing)}: {rel!r}"
            )

    lowered = [
        {
            "id": f"pipeline/{edge['contract']}/{edge['from']}->{edge['to']}",
            "contract": edge["contract"],
            "authority": edge["from"],
            "dependents": [edge["to"]],
        }
        for edge in raw_edges
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


def effective_packages(cfg: dict | None = None, facts: dict | None = None) -> list[dict]:
    """Layer ``[[components]]`` over the derived package-facts graph (MONO-03).

    Field-level merge: the derived package record (from ``package_facts.build_facts()``) is the
    BASE, every field present on a declared ``[[components]]`` entry with the same ``id``
    OVERWRITES the same-named base field, and any field present on only one side (base-only
    ``manifest``/``dir``, or component-only ``stage``/``produces``/``consumes``) survives into the
    merged record unchanged — nothing is silently deleted from either side.

    ONE deliberate divergence from :func:`effective_relationships`'s raise-on-mismatch posture: a
    ``[[components]]`` entry with no matching derived package id stays DECLARED-ONLY and never
    raises — no fabricated ``manifest``/``dir``/``language`` fields are synthesized for it. Both
    the core config and the example instance's overlay must keep loading with zero edits even
    though none of their declared component ids match a real manifest-derived package id in this
    checkout today; that "no match -> declared-only, no error" behavior is the load-bearing proof
    here, not an edge case.

    Any derived package with no overriding ``[[components]]`` entry passes through unchanged.

    ``facts`` defaults to a lazy call to ``tools.memory_regen.package_facts.build_facts()`` (an
    in-function import, mirroring ``compile_graph``'s deferred ``from tools.harness_config import
    load_project`` — avoids a heavy/circular import at module load).

    The merged+declared-only+passthrough set is stable-sorted by ``id`` (mirrors
    ``effective_relationships``'s ``sorted(merged, key=lambda rel: rel["id"])``).
    """
    if cfg is None:
        cfg = load_project()
    if facts is None:
        from tools.memory_regen.package_facts import build_facts

        facts = build_facts()

    by_id: dict[str, dict] = {pkg["id"]: dict(pkg) for pkg in facts["packages"]}

    merged: list[dict] = []
    seen_ids: set[str] = set()
    for comp in components(cfg):
        comp_id = comp["id"]
        seen_ids.add(comp_id)
        if comp_id in by_id:
            record = {**by_id[comp_id], **comp}
        else:
            record = dict(comp)
        merged.append(record)

    for pkg_id, pkg in by_id.items():
        if pkg_id not in seen_ids:
            merged.append(pkg)

    return sorted(merged, key=lambda pkg: pkg["id"])


def _nearest_agents_md(dir_: str) -> str | None:
    """Return the POSIX-relative path of the nearest ``AGENTS.md`` enclosing ``dir_``.

    Walks ``_REPO_ROOT / dir_`` and its ``.parents``, checking each candidate for an
    ``AGENTS.md`` file, stopping once ``_REPO_ROOT`` itself has been checked (never inspects
    anything above the repo root — T-48-01's bounded-walk mitigation). Returns ``None`` if no
    candidate has an ``AGENTS.md``.

    Contract for out-of-root ``dir_`` (CR-01, 48-REVIEW.md): a relative-escaping value
    (``"../../etc"``) or an absolute value (``"/etc"`` — ``_REPO_ROOT / "/etc"`` silently
    discards ``_REPO_ROOT`` per pathlib join semantics) is validated and rejected with a scoped
    ``ValueError`` BEFORE any filesystem walk happens — fail closed, never a traversal above the
    repo root and never an unhandled ``ValueError`` from deep inside the loop. A non-existent-but
    in-repo ``dir_`` or the empty string are both fine: they resolve to a path inside
    ``_REPO_ROOT`` (the empty string resolves to ``_REPO_ROOT`` itself) and fall through to the
    normal walk.
    """
    candidate = (_REPO_ROOT / dir_).resolve()
    try:
        candidate.relative_to(_REPO_ROOT)
    except ValueError:
        raise ValueError(
            f"_nearest_agents_md: dir_={dir_!r} resolves outside the repo root "
            f"({candidate}) — refusing to walk above _REPO_ROOT"
        ) from None

    for probe in (candidate, *candidate.parents):
        if (probe / "AGENTS.md").is_file():
            return (
                probe.relative_to(_REPO_ROOT).as_posix() + "/AGENTS.md"
                if probe != _REPO_ROOT
                else "AGENTS.md"
            )
        if probe == _REPO_ROOT:
            break
    return None


def conventions_for(path: str, cfg: dict | None = None, facts: dict | None = None) -> dict:
    """Answer "which conventions apply at ``path``?" (MONO-05/MONO-06).

    A pure join over ``effective_packages()`` (Phase-47 package facts layered with
    ``[[components]]``) and the ``[[languages]]`` config: resolves the nearest-enclosing package
    via ``owning_package()`` (reused unchanged from ``tools.contract_graph``, never
    reimplemented), then looks up that package's language's commands.

    Follows the module's optional-``cfg``/``facts`` injectable-pure-function convention
    (``effective_packages``, above) — the only filesystem touch when both are injected is the
    ``_nearest_agents_md`` walk, which makes this function fully testable without monkeypatch or
    a temp-file config.

    Returns a dict with exactly these keys: ``package``, ``dir``, ``language`` (the raw
    ``owner.get("language")`` value — visible even when absent from ``[[languages]]``), ``test``,
    ``format``, ``lint`` (``None`` when the matched language row declares no ``lint`` command — a
    permanent key, not a null awaiting a future value, OBS-D-03/D-11), ``bash_scope`` (all
    ``None`` when the language has no matching ``[[languages]]`` row — never raises on a missing
    row), ``agents_md`` (nearest-enclosing ``AGENTS.md``, or ``None`` if none found), and
    ``is_default`` (``True`` iff the resolved package's ``dir`` is the repo root, ``"."``).
    """
    if cfg is None:
        cfg = load_project()

    pkgs = effective_packages(cfg, facts)
    # ADAPTER: owning_package() reads a bare package["dir"] subscript unconditionally — a
    # declared-only component (no "dir" key, see effective_packages's Pitfall 1) would raise a
    # bare KeyError there. Filter it out here; never inside ownership.py (kept untouched/pure).
    #
    # WR-02 (48-REVIEW.md): "dir" in p on its own can't tell a LEGITIMATE declared-only
    # component (no "dir", also no "manifest" — it never came from build_facts()) apart from a
    # MALFORMED derived-package record (has "manifest", meaning it came from build_facts() or a
    # component overriding one, but is missing "dir" for some other reason). The latter must not
    # be silently dropped with no trace — surface it on stderr so a data bug stays visible instead
    # of letting an unrelated ancestor package quietly "win" ownership of its path.
    for p in pkgs:
        if "dir" not in p and "manifest" in p:
            print(
                f"conventions_for: package {p.get('id')!r} has 'manifest' but no 'dir' — "
                "excluded from ownership resolution (malformed record, not a declared-only "
                "component)",
                file=sys.stderr,
            )
    dir_pkgs = [p for p in pkgs if "dir" in p]
    owner_id = owning_package(dir_pkgs, path)
    owner = next(p for p in dir_pkgs if p["id"] == owner_id)
    lang = next((entry for entry in languages(cfg) if entry["id"] == owner.get("language")), None)

    return {
        "package": owner["id"],
        "dir": owner["dir"],
        "language": owner.get("language"),
        # CR-03 (52-REVIEW.md): `.get`, never a subscript — same reason as `lint` below. A
        # `[[languages]]` row may legitimately omit a command it has none of (the adoption-derived
        # javascript row omits `format` when the target's package.json declares no `format`
        # script), and the documented contract for these keys is already "None when the row
        # declares no such command". A bare subscript made an omitted key a KeyError, which is
        # what forced the earlier `""` workaround that broke the adopted target's CI.
        "test": lang.get("test") if lang else None,
        "format": lang.get("format") if lang else None,
        # OBS-D-03 (51-BASELINE-EVIDENCE.md) — purpose 1: the profile had no lint key at all
        # (D-11 shape change). `.get`, never a subscript: neither of this repo's own `[[languages]]`
        # rows (dotnet/python) declares `lint`, so a bare `lang["lint"]` would KeyError here.
        "lint": lang.get("lint") if lang else None,
        "bash_scope": lang.get("bash_scope") if lang else None,
        "agents_md": _nearest_agents_md(owner["dir"]),
        "is_default": owner["dir"] == ".",
    }


def language_bash_scopes(cfg: dict | None = None) -> set[str]:
    """Return the derived set of bash allow-scopes: union of ``languages[*].bash_scope`` + implicit
    ``"pytest *"``. This is the set the permission-matrix language allow-scopes must equal."""
    scopes = {lang["bash_scope"] for lang in languages(cfg) if lang.get("bash_scope")}
    return scopes | set(_IMPLICIT_TEST_SCOPES)
