"""MONO-03 unit tests — effective_packages() layers [[components]] over derived package facts.

All fixtures are synthetic (never build_facts() against the real repo, never load_project() over
a real config) — this file proves the merge shape in isolation, hermetically. Domain-neutral ids
("a"/"b") mirror test_topology_relationships.py's own register so this core-plane test stays
GEN-04-clean.
"""

from __future__ import annotations

from tools.harness_config import effective_packages


def test_declared_field_overrides_derived_field() -> None:
    """A declared component's field wins over the same-named derived field; unshared fields survive."""
    facts = {
        "packages": [
            {"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "python"},
        ]
    }
    cfg = {"components": [{"id": "a", "language": "dotnet", "stage": 1}]}

    result = effective_packages(cfg, facts)

    assert len(result) == 1
    record = result[0]
    assert record["language"] == "dotnet"  # override wins
    assert record["manifest"] == "a/pyproject.toml"  # derived-only field survives
    assert record["dir"] == "a"  # derived-only field survives
    assert record["stage"] == 1  # declared-only field survives


def test_component_with_no_matching_package_stays_declared_only_no_raise() -> None:
    """A component naming no known derived package id stays declared-only — never raises."""
    facts = {"packages": []}
    cfg = {"components": [{"id": "b", "language": "python"}]}

    result = effective_packages(cfg, facts)

    assert len(result) == 1
    record = result[0]
    assert record["id"] == "b"
    assert record["language"] == "python"
    assert "manifest" not in record  # no fabricated field
    assert "dir" not in record  # no fabricated field


def test_derived_package_with_no_override_passes_through_unchanged() -> None:
    """A derived package with no matching component appears in the output unchanged."""
    facts = {
        "packages": [
            {"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "python"},
        ]
    }
    cfg = {"components": []}

    result = effective_packages(cfg, facts)

    assert result == [{"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "python"}]


def test_output_is_sorted_by_id() -> None:
    """3+ packages/components supplied out of order come back sorted by id."""
    facts = {
        "packages": [
            {"id": "c", "manifest": "c/pyproject.toml", "dir": "c", "language": "python"},
            {"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "python"},
        ]
    }
    cfg = {"components": [{"id": "b", "language": "python"}]}

    ids = [pkg["id"] for pkg in effective_packages(cfg, facts)]

    assert ids == ["a", "b", "c"]
