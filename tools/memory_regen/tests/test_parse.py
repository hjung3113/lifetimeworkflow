"""Tests for the tree-sitter parse layer (MEM-03, Task 1, ROADMAP Crit-2 / RESEARCH Pattern 1).

Pins the two guarantees the repo-map depends on:
  (a) parse correctness — parsing the tmp_source_tree ``.py`` / ``.cs`` / ``.sh`` fixtures (one def +
      one ref each) yields NON-EMPTY ``def`` captures per language (refs where the grammar exposes
      them), via the tree-sitter 0.25 ``Query`` + ``QueryCursor`` API.
  (b) Pitfall-3 guard — the parse path does NOT touch the removed ``Language.query`` /
      ``Query.captures`` 0.24-era API (which throws ``AttributeError`` on 0.25). We assert the code
      uses the ``QueryCursor`` seam and that a full parse raises no ``AttributeError``.
"""

from __future__ import annotations

import inspect
import warnings
from pathlib import Path

import pytest

from tools.memory_regen import queries


_EXT_LANG = {".py": "python", ".cs": "c_sharp", ".sh": "bash"}


@pytest.mark.parametrize("filename", ["mod.py", "Mod.cs", "mod.sh"])
def test_parse_yields_nonempty_def_captures(tmp_source_tree: Path, filename: str) -> None:
    """Each language fixture returns a non-empty ``def`` list via the 0.25 QueryCursor API."""
    path = tmp_source_tree / filename
    lang_name = _EXT_LANG[path.suffix]
    caps = queries.parse_symbols(path, lang_name)
    assert caps["def"], f"expected non-empty def captures for {filename}, got {caps!r}"
    assert "helper" in caps["def"] or "Helper" in caps["def"]


def test_python_ref_captures_present(tmp_source_tree: Path) -> None:
    """The Python fixture references ``helper`` — refs must be captured (topology for PageRank)."""
    caps = queries.parse_symbols(tmp_source_tree / "mod.py", "python")
    assert "helper" in caps["ref"]


def test_languages_table_covers_three_grammars() -> None:
    """LANGUAGES maps python/c_sharp/bash → (grammar module, extensions, query string)."""
    assert set(queries.LANGUAGES) == {"python", "c_sharp", "bash"}
    for name, spec in queries.LANGUAGES.items():
        assert spec.extensions, f"{name} must declare file extensions"
        assert "@def" in spec.query, f"{name} query must capture @def"


def test_ext_to_lang_resolves_each_language() -> None:
    """Extension → language resolution covers .py/.cs/.sh (the repo-map walk keys off this)."""
    assert queries.lang_for_path(Path("x.py")) == "python"
    assert queries.lang_for_path(Path("X.cs")) == "c_sharp"
    assert queries.lang_for_path(Path("x.sh")) == "bash"
    assert queries.lang_for_path(Path("x.txt")) is None


def test_parse_path_uses_querycursor_not_removed_api() -> None:
    """Pitfall 3 guard: source uses the 0.25 QueryCursor seam, not lang.query()/Query.captures()."""
    src = inspect.getsource(queries)
    assert "QueryCursor" in src, "must use the tree-sitter 0.25 QueryCursor API"
    # The removed 0.24-era chained call must not appear.
    assert ".query(" not in src, "must NOT call the removed Language.query() API"


def test_parse_emits_no_deprecation_or_attribute_error(tmp_source_tree: Path) -> None:
    """A full parse of every fixture raises no AttributeError and emits no DeprecationWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        for filename in ("mod.py", "Mod.cs", "mod.sh"):
            path = tmp_source_tree / filename
            caps = queries.parse_symbols(path, _EXT_LANG[path.suffix])
            assert isinstance(caps["def"], list)
