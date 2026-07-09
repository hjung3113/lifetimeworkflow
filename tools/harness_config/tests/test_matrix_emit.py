"""CI-01 matrix-shape test — the Phase-6 CI matrix include-list built from languages().

Pure structural test (no subprocess, no runtime): assert the config-derived CI matrix the Wave-2
workflow emits — one leg per language, each carrying `id` + `test` + the `test_paths` list — has
the shape `fromJSON` fans out over. Mirrors test_loader.py's idiom: the package's PEP-562 lazy
re-export (`__init__.py`) makes `from tools.harness_config import languages` resolve during
collection, so no `sys.path` insert / conftest is needed.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import languages, load_project

# test_matrix_emit.py -> tests -> harness_config -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _matrix_include() -> list[dict]:
    """Build the CI matrix include-list the workflow's `setup` step emits from `languages()`.

    One dict per language leg carrying the keys the fan-out job reads: `id`, `test`, `test_paths`
    (raw passthrough via `l.get("test_paths", [])` — the loader surfaces the field unchanged).
    """
    return [
        {"id": leg["id"], "test": leg["test"], "test_paths": leg.get("test_paths", [])}
        for leg in languages(load_project())
    ]


def test_matrix_include_has_one_leg_per_language() -> None:
    """The matrix fans out over exactly the two configured legs ({dotnet, python})."""
    include = _matrix_include()
    assert sorted(leg["id"] for leg in include) == ["dotnet", "python"]


def test_matrix_each_leg_carries_test_command() -> None:
    """Every leg carries a non-empty `test` command (the golden-path invocation)."""
    for leg in _matrix_include():
        assert isinstance(leg["test"], str)
        assert leg["test"].strip(), f"{leg['id']!r}: empty test command"


def test_matrix_each_leg_test_paths_is_str_list() -> None:
    """Every leg's `test_paths` is a list of strings (the shape `fromJSON` fans out over)."""
    for leg in _matrix_include():
        assert isinstance(leg["test_paths"], list), f"{leg['id']!r}: test_paths not a list"
        assert all(isinstance(p, str) for p in leg["test_paths"]), (
            f"{leg['id']!r}: test_paths carries a non-str entry"
        )


def test_matrix_each_leg_declares_a_test_target() -> None:
    """Every leg declares at least one test target — RED until project.toml gains test_paths."""
    for leg in _matrix_include():
        assert leg["test_paths"], f"{leg['id']!r}: no test_paths declared"
