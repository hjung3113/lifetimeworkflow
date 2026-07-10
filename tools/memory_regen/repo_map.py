"""repo-map generator — tree-sitter symbols → networkx PageRank → derived map (MEM-03, Task 2).

The one genuinely new engine of this phase (RESEARCH §Key insight). It walks the harness-core
source subtrees (``libs/python``, ``tools`` — code only, D-06, never ``.planning/``; an instance's
own source is mapped from its own tree), parses each ``.py``/``.cs``/``.sh`` file into def/ref symbols via the
tree-sitter 0.25 layer (:mod:`tools.memory_regen.queries`), builds a directed file→file
graph (edge A→B when A references a symbol defined in B, weighted by count), ranks files
by ``networkx.pagerank`` (importance via reference topology, not size/mtime), and renders
the top-N with elided def signatures into a token-bounded, DERIVED-marked
``.memory/derived/repo-map.md``.

Determinism (delete + regenerate byte-identical — success criterion 2 / D-04, Pitfall 1) is achieved
by: sorted node + edge insertion, ``(-score, path)`` tie-break, NO raw PageRank floats in the body
(rank-only), and NO timestamp anywhere. The determinism is proven by a committed syrupy snapshot and
a write→hash→delete→regenerate test — NOT by ``git diff`` (the target is gitignored, Pitfall 2).

Path traversal defense (T-02-10): each source-root walk is confined to its resolved subtree and
symlinks escaping the tree are skipped — mirroring ``tools.contract_hash.hash``.

Entrypoint: ``python -m tools.memory_regen.repo_map``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
from networkx.algorithms.link_analysis.pagerank_alg import _pagerank_python

from tools.memory_regen.queries import lang_for_path, parse_symbols

# --- paths (derived plane is gitignored + regenerated every session, D-03) --------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
OUTPUT_PATH = DERIVED_DIR / "repo-map.md"

# Code-only source subtrees to map (D-06 — NOT .planning/). Confined + symlink-guarded per walk.
# Harness-core planes only; a downstream instance maps its own tree separately.
DEFAULT_SOURCE_DIRS = ("libs/python", "tools")

# --- stable text (part of the derived-plane contract) -----------------------------------------
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/repo_map.py)"

# Cap on def signatures shown per file (elided) — keeps rows compact within the token budget.
_MAX_DEFS_PER_FILE = 8


def _default_source_roots() -> list[Path]:
    return [_REPO_ROOT / d for d in DEFAULT_SOURCE_DIRS]


def _iter_source_files(source_roots: list[Path]) -> list[Path]:
    """Yield the mappable source files under each root, symlink-confined (T-02-10), sorted."""
    files: list[Path] = []
    for root in source_roots:
        root = Path(root)
        if not root.exists():
            continue
        root_resolved = root.resolve()
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            if lang_for_path(p) is None:
                continue
            resolved = p.resolve()
            # Defense-in-depth: skip anything a symlink points outside the subtree (mirror hash.py).
            if root_resolved != resolved and root_resolved not in resolved.parents:
                continue
            files.append(p)
    return files


def build_graph(
    source_roots: list[Path] | None = None,
    base_dir: str | Path | None = None,
) -> nx.DiGraph:
    """Parse the source subtrees and build the deterministic file→file symbol graph.

    Nodes are file paths (POSIX, relative to ``base_dir``) carrying a sorted ``defs`` tuple. An edge
    ``A → B`` (``weight`` = reference count) is added when file A references a symbol *defined* in a
    different file B. Nodes are inserted in sorted order, then edges in sorted order (Pattern 2) so
    ``networkx.pagerank``'s uniform start vector is order-stable → delete+regen is byte-identical.

    ``base_dir`` defaults to the repo root (keys like ``libs/python/normalize/core.py``); tests pass
    the fixture root so the random ``tmp_path`` never leaks into the output.
    """
    if source_roots is None:
        source_roots = _default_source_roots()
    base = Path(base_dir).resolve() if base_dir is not None else _REPO_ROOT

    files = _iter_source_files(source_roots)

    defs_by_file: dict[str, list[str]] = {}
    refs_by_file: dict[str, list[str]] = {}
    for p in files:
        resolved = p.resolve()
        try:
            rel = resolved.relative_to(base).as_posix()
        except ValueError:
            rel = p.as_posix()
        lang = lang_for_path(p)
        assert lang is not None  # _iter_source_files already filtered
        caps = parse_symbols(p, lang)
        defs_by_file[rel] = caps["def"]
        refs_by_file[rel] = caps["ref"]

    # Symbol → set of files defining it (a ref resolves to every file that defines the name).
    def_index: dict[str, set[str]] = {}
    for rel, defs in defs_by_file.items():
        for name in defs:
            def_index.setdefault(name, set()).add(rel)

    # Accumulate directed edge weights: A references a symbol defined in B (B != A).
    edge_weights: dict[tuple[str, str], int] = {}
    for rel in sorted(refs_by_file):
        for name in refs_by_file[rel]:
            for target in def_index.get(name, ()):
                if target == rel:
                    continue
                edge_weights[(rel, target)] = edge_weights.get((rel, target), 0) + 1

    graph = nx.DiGraph()
    for rel in sorted(defs_by_file):
        graph.add_node(rel, defs=tuple(sorted(set(defs_by_file[rel]))))
    for (a, b), weight in sorted(edge_weights.items()):
        graph.add_edge(a, b, weight=weight)
    return graph


def ranked_files(graph: nx.DiGraph) -> list[tuple[str, float]]:
    """Rank files by PageRank, sorted ``(-score, path)`` (score desc, path asc tie-break).

    Uses networkx's pure-Python PageRank backend (``_pagerank_python``) rather than the
    public ``nx.pagerank`` dispatcher: on networkx 3.6 the public entry routes to
    ``_pagerank_scipy``, which imports numpy/scipy — neither is in the 02-01-pinned
    toolchain (T-02-SC: individual wheels only, ``uv.lock`` resolved once in Wave 1,
    never touched in Wave 2). The pure-Python power iteration is the identical PageRank
    algorithm, dependency-free, and deterministic (uniform start vector over the sorted
    node insertion order → delete+regen byte-identical, Pattern 2).
    """
    if graph.number_of_nodes() == 0:
        return []
    scores = _pagerank_python(graph, weight="weight")
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def render(graph: nx.DiGraph, budget_chars: int = 4000) -> str:
    """Render the DERIVED-marked, rank-ordered, token-bounded repo-map (no floats, no timestamp).

    Files are ordered by PageRank; each row shows the file path + an elided list of its top defs.
    Raw scores are NEVER printed (rank-only — the determinism trap, Pitfall 1). The map is capped to
    ``budget_chars`` (~1k tokens via the char/4 heuristic, D-07): the lowest-ranked rows are dropped
    first (priority-truncate), the header is always kept.
    """
    header = "\n".join(
        [
            f"# {DERIVED_HEADER}",
            "",
            "Importance-ranked code map (tree-sitter symbols -> networkx PageRank over the "
            "reference graph). Rank-ordered, no scores; regenerated each session.",
            "",
        ]
    )

    rows: list[str] = []
    for _position, (rel, _score) in enumerate(ranked_files(graph), start=1):
        defs = graph.nodes[rel].get("defs", ())
        if not defs:
            continue  # isolated file with no definitions — nothing to show
        shown = list(defs[:_MAX_DEFS_PER_FILE])
        remainder = len(defs) - len(shown)
        signature = ", ".join(shown)
        if remainder > 0:
            signature += f", +{remainder} more"
        rows.append(f"{len(rows) + 1}. `{rel}` - {signature}")

    # Greedy priority-truncate: keep header + as many top-ranked rows as fit the char budget.
    out = header
    for row in rows:
        candidate = out + row + "\n"
        if len(candidate) > budget_chars:
            break
        out = candidate
    return out


def write(
    output_path: str | Path = OUTPUT_PATH,
    source_roots: list[Path] | None = None,
    base_dir: str | Path | None = None,
    budget_chars: int = 4000,
) -> Path:
    """Regenerate the derived repo-map and write it (mkdir parents), returning the path."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    graph = build_graph(source_roots=source_roots, base_dir=base_dir)
    out.write_text(render(graph, budget_chars=budget_chars), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI: regenerate ``.memory/derived/repo-map.md`` (`python -m tools.memory_regen.repo_map`)."""
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    graph = build_graph()
    out = write()
    print(
        f"wrote {out.relative_to(_REPO_ROOT)} "
        f"({graph.number_of_nodes()} file(s), {graph.number_of_edges()} edge(s) mapped)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
