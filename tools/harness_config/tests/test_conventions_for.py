"""MONO-05/MONO-06 unit tests — conventions_for() nearest-wins convention-profile lookup.

Synthetic-case fixtures are hermetic (no monkey-patching, no temp-file config — cfg/facts are
passed straight into conventions_for(), mirroring test_effective_packages.py's idiom exactly) and
use domain-neutral ids ("root"/"inner"/"a" — never instance-directory literals, GEN-04). The one
real-tree test is the deliberate exception (libs/python vs root), asserted in-memory only.
"""

from __future__ import annotations

from tools.harness_config import conventions_for


def test_editing_language_command_changes_every_affected_profile_with_no_profile_edit() -> None:
    """MONO-06 strong falsifiable form: a live config read, not a copied literal (RESEARCH.md Q3)."""
    facts = {
        "packages": [
            {"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"},
            {
                "id": "inner",
                "manifest": "libs/x/pyproject.toml",
                "dir": "libs/x",
                "language": "python",
            },
        ]
    }
    cfg_v1 = {"languages": [{"id": "python", "test": "OLD", "format": "f", "bash_scope": "uv *"}]}
    cfg_v2 = {"languages": [{"id": "python", "test": "NEW", "format": "f", "bash_scope": "uv *"}]}

    before_root = conventions_for("pyproject.toml", cfg=cfg_v1, facts=facts)
    before_inner = conventions_for("libs/x/whatever.py", cfg=cfg_v1, facts=facts)
    after_root = conventions_for("pyproject.toml", cfg=cfg_v2, facts=facts)
    after_inner = conventions_for("libs/x/whatever.py", cfg=cfg_v2, facts=facts)

    assert before_root["test"] == "OLD" and before_inner["test"] == "OLD"
    assert after_root["test"] == "NEW" and after_inner["test"] == "NEW"


def test_real_nested_pair_libs_python_vs_root_differ_on_package_and_agents_md() -> None:
    """MONO-05 nearest-wins on the real tree — libs/python resolves to its own package/AGENTS.md."""
    inner = conventions_for("libs/python/normalize/x.py")
    outer = conventions_for("tools/some_module/y.py")

    assert inner["package"] != outer["package"]
    assert inner["dir"] == "libs/python"
    assert inner["agents_md"] == "libs/python/AGENTS.md"
    assert outer["is_default"] is True
    assert outer["agents_md"] == "AGENTS.md"
    # Pitfall 2: both packages are "python", so commands are IDENTICAL by design — this asserts
    # equality deliberately; it is NOT the nested-commands-differ proof (see the synthetic test
    # below for that).
    assert inner["test"] == outer["test"]


def test_path_outside_any_package_returns_explicit_default() -> None:
    """A single-package fixture: any path resolves to the root package, is_default explicitly True."""
    facts = {
        "packages": [{"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"}]
    }
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}

    profile = conventions_for("some/unowned/path.py", cfg=cfg, facts=facts)

    assert profile["is_default"] is True
    assert profile["package"] == "root"


def test_package_whose_language_is_absent_from_languages_reports_no_commands() -> None:
    """A package whose language has no [[languages]] row degrades to None commands, never raises."""
    facts = {
        "packages": [{"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "rust"}]
    }
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}

    profile = conventions_for("a/whatever.rs", cfg=cfg, facts=facts)

    assert profile["language"] == "rust"
    assert profile["test"] is None
    assert profile["format"] is None


def test_synthetic_two_language_nested_pair_commands_differ() -> None:
    """Supplementary fixture (RESEARCH.md Q4): proves the commands-DO-differ case the real tree can't."""
    facts = {
        "packages": [
            {"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"},
            {"id": "inner", "manifest": "inner/inner.csproj", "dir": "inner", "language": "csharp"},
        ]
    }
    cfg = {
        "languages": [
            {"id": "python", "test": "pytest", "format": "ruff", "bash_scope": "uv *"},
            {
                "id": "csharp",
                "test": "dotnet test",
                "format": "dotnet format",
                "bash_scope": "dotnet *",
            },
        ]
    }

    outer = conventions_for("top.py", cfg=cfg, facts=facts)
    inner = conventions_for("inner/x.cs", cfg=cfg, facts=facts)

    assert outer["test"] != inner["test"]
