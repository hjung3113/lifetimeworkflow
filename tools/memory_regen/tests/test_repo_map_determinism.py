"""Tests for the repo-map generator (MEM-03, Task 2, ROADMAP Crit-2, D-04/D-05/D-06).

Pins the guarantees the derived plane depends on:
  (a) determinism — render twice AND write→hash→delete→regenerate are byte-identical (Pitfall 1),
      proven WITHOUT git diff because ``.memory/derived/`` is gitignored (Pitfall 2).
  (b) ranking — PageRank ordering is stable across runs, tie-broken by path (Pattern 2).
  (c) budget — the rendered map is within the ~1k-token (~4000-char) budget (D-07).
  (d) DERIVED marker + no timestamp + no raw float in the body (D-04 / Pitfall 1).
  (e) a committed syrupy snapshot over the tmp fixture = the determinism reference (NOT under
      .memory/, Pitfall 2).

All fixture-based cases key file paths relative to the fixture root (``base_dir``) so the random
``tmp_path`` never leaks into the output — that is what makes the committed snapshot stable.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from tools.memory_regen import repo_map


def _render_fixture(tree: Path) -> str:
    graph = repo_map.build_graph(source_roots=[tree], base_dir=tree)
    return repo_map.render(graph)


def test_render_twice_is_byte_identical(tmp_source_tree: Path) -> None:
    """render(build_graph()) twice over the same tree yields identical text (Pitfall 1)."""
    assert _render_fixture(tmp_source_tree) == _render_fixture(tmp_source_tree)


def test_write_delete_regenerate_is_byte_identical(tmp_path: Path, tmp_source_tree: Path) -> None:
    """write → sha256 → delete → regenerate → identical hash (NOT git diff, Pitfall 2)."""
    out = tmp_path / "derived" / "repo-map.md"
    repo_map.write(output_path=out, source_roots=[tmp_source_tree], base_dir=tmp_source_tree)
    digest_1 = hashlib.sha256(out.read_bytes()).hexdigest()
    out.unlink()
    assert not out.exists()
    repo_map.write(output_path=out, source_roots=[tmp_source_tree], base_dir=tmp_source_tree)
    digest_2 = hashlib.sha256(out.read_bytes()).hexdigest()
    assert digest_1 == digest_2


def test_pagerank_ordering_is_stable(tmp_source_tree: Path) -> None:
    """ranked_files() is order-stable across runs, tie-broken by path (Pattern 2 determinism)."""
    graph = repo_map.build_graph(source_roots=[tmp_source_tree], base_dir=tmp_source_tree)
    first = [rel for rel, _ in repo_map.ranked_files(graph)]
    second = [rel for rel, _ in repo_map.ranked_files(graph)]
    assert first == second
    assert first, "expected at least one ranked file from the polyglot fixture"


def test_render_within_char_budget(tmp_source_tree: Path) -> None:
    """The rendered map respects the ~4000-char (~1k-token) budget (D-07)."""
    graph = repo_map.build_graph(source_roots=[tmp_source_tree], base_dir=tmp_source_tree)
    text = repo_map.render(graph, budget_chars=4000)
    assert len(text) <= 4000


def test_output_carries_derived_marker_and_no_timestamp_or_float(tmp_source_tree: Path) -> None:
    """Header marks DERIVED; body has no timestamp and no raw PageRank float (Pitfall 1)."""
    text = _render_fixture(tmp_source_tree)
    assert text.splitlines()[0].startswith("# DERIVED — do not hand-edit")
    assert "repo_map.py" in text.splitlines()[0]
    # No ISO-ish timestamp anywhere in the body.
    assert not re.search(r"\d{4}-\d{2}-\d{2}", text), "no date/timestamp in a derived artifact"
    # No raw PageRank float (e.g. 0.1735...) — ranking is rank-only.
    assert not re.search(r"0\.\d{3,}", text), "raw PageRank floats must not be printed"


def test_map_lists_fixture_files_with_defs(tmp_source_tree: Path) -> None:
    """The three polyglot fixtures appear in the map with their defs (elided signatures)."""
    text = _render_fixture(tmp_source_tree)
    for name in ("mod.py", "Mod.cs", "mod.sh"):
        assert name in text
    assert "helper" in text


def test_render_matches_committed_snapshot(tmp_source_tree: Path, snapshot) -> None:
    """Committed .ambr snapshot pins render() over the tmp fixture = the determinism reference."""
    assert _render_fixture(tmp_source_tree) == snapshot
