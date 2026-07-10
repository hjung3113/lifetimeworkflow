"""GEN-03 loader unit tests — harness/project.toml parses to the expected language SSOT shape.

Pure structural tests (no subprocess, no runtime): assert the stdlib `tomllib` loader reads the
project-config slot, exposes exactly the two example-instance languages ({dotnet, python}), that
each carries the fields the consumers rely on, and that every referenced persona file exists on
disk. The cross-artifact consistency gate (matrix scopes / personas derive from this config) lives
in tools/harness_lint/tests/test_language_config.py.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import (
    components,
    language_bash_scopes,
    languages,
    load_project,
    pipeline,
)

# test_loader.py -> tests -> harness_config -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_load_project_returns_two_languages() -> None:
    """The example instance declares exactly the .NET 10 + Python(uv) toolchains."""
    cfg = load_project()
    ids = sorted(lang["id"] for lang in cfg["languages"])
    assert ids == ["dotnet", "python"]


def test_instance_root_is_generic_default() -> None:
    """`[instance] root` is the empty generic-default marker for this repo's active instance."""
    cfg = load_project()
    assert cfg["instance"]["root"] == ""


def test_each_language_carries_required_fields() -> None:
    """Every language table exposes the id/bash_scope/test/format/persona the consumers read."""
    for lang in languages():
        for field in ("id", "bash_scope", "test", "format", "persona"):
            assert str(lang.get(field, "")).strip(), f"{lang.get('id')!r}: missing {field}"


def test_persona_files_exist_on_disk() -> None:
    """Each configured persona path resolves to a real file under harness/agents/."""
    for lang in languages():
        persona = _REPO_ROOT / lang["persona"]
        assert persona.is_file(), f"{lang['id']!r}: persona {lang['persona']} not found"


def test_language_bash_scopes_union_includes_implicit_pytest() -> None:
    """The derived scope set is the union of bash_scope values plus the implicit `pytest *`."""
    scopes = language_bash_scopes()
    assert scopes == {"dotnet *", "uv *", "pytest *"}


def test_components_passthrough() -> None:
    """The generic-default topology declares exactly the source/sink components (raw passthrough)."""
    assert {c["id"] for c in components()} == {"source", "sink"}


def test_pipeline_passthrough() -> None:
    """The [pipeline] table carries the single generic source→sink `sample-record` edge."""
    edges = pipeline()["edges"]
    assert len(edges) == 1
    assert edges[0]["contract"] == "sample-record"
