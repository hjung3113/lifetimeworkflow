"""MONO-05/MONO-06 unit tests — conventions_for() nearest-wins convention-profile lookup.

Synthetic-case fixtures are hermetic (no monkey-patching, no temp-file config — cfg/facts are
passed straight into conventions_for(), mirroring test_effective_packages.py's idiom exactly) and
use domain-neutral ids ("root"/"inner"/"a" — never instance-directory literals, GEN-04). The one
real-tree test is the deliberate exception (libs/python vs root), asserted in-memory only.
"""

from __future__ import annotations

import pytest

from tools.harness_config import conventions_for
from tools.harness_config.loader import _nearest_agents_md

# ---- CR-01 (48-REVIEW.md): _nearest_agents_md must never walk above the repo root -------------


def test_nearest_agents_md_rejects_relative_traversal_escaping_repo_root() -> None:
    """A ``../..``-escaping dir_ must fail closed with a scoped ValueError, never an unhandled
    crash from deep inside the walk and never a silent out-of-root probe."""
    with pytest.raises(ValueError, match="resolves outside the repo root"):
        _nearest_agents_md("../../etc")


def test_nearest_agents_md_rejects_absolute_path_escaping_repo_root() -> None:
    """An absolute dir_ (``_REPO_ROOT / "/etc"`` discards ``_REPO_ROOT`` per pathlib join
    semantics) must also fail closed rather than walking the real filesystem root."""
    with pytest.raises(ValueError, match="resolves outside the repo root"):
        _nearest_agents_md("/etc")


def test_nearest_agents_md_tolerates_nonexistent_in_repo_dir() -> None:
    """A dir_ that does not exist on disk but stays inside the repo root is NOT an error — it
    falls through to the nearest existing ancestor's AGENTS.md (here, the repo root's)."""
    assert _nearest_agents_md("this/path/does/not/exist/anywhere") == "AGENTS.md"


def test_nearest_agents_md_tolerates_empty_string_as_repo_root() -> None:
    """The empty string resolves to ``_REPO_ROOT`` itself — a valid, in-root input."""
    assert _nearest_agents_md("") == "AGENTS.md"


def test_conventions_for_propagates_out_of_root_dir_as_scoped_value_error() -> None:
    """A malformed config ``dir`` (typo'd traversal) must surface as a clear ValueError through
    the public conventions_for() entry point too — never an opaque crash."""
    facts = {
        "packages": [
            {"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"},
            {
                "id": "escaped",
                "manifest": "../escaped/pyproject.toml",
                "dir": "../escaped",
                "language": "python",
            },
        ]
    }
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}

    with pytest.raises(ValueError, match="resolves outside the repo root"):
        conventions_for("../escaped/thing.py", cfg=cfg, facts=facts)


# ---- WR-02 (48-REVIEW.md): the "dir" filter must distinguish declared-only from malformed ------


def test_malformed_component_missing_dir_but_has_manifest_is_reported_on_stderr(capsys) -> None:
    """A record carrying 'manifest' (meaning it is NOT a legitimate declared-only component) but
    missing 'dir' must surface a stderr diagnostic naming it, not vanish silently."""
    facts = {
        "packages": [{"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"}]
    }
    cfg = {
        "languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}],
        "components": [{"id": "malformed", "manifest": "malformed/pyproject.toml"}],
    }

    profile = conventions_for("whatever.py", cfg=cfg, facts=facts)

    assert profile["package"] == "root"  # falls back to root; ownership not fabricated
    captured = capsys.readouterr()
    assert "malformed" in captured.err
    assert "no 'dir'" in captured.err


def test_legitimate_declared_only_component_produces_no_stderr_warning(capsys) -> None:
    """A genuinely declared-only [[components]] entry (no 'dir', no 'manifest' — never came from
    build_facts()) must load with zero edits and zero diagnostic noise."""
    facts = {
        "packages": [{"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"}]
    }
    cfg = {
        "languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}],
        "components": [{"id": "declared-only", "stage": "ingest"}],
    }

    profile = conventions_for("whatever.py", cfg=cfg, facts=facts)

    assert profile["package"] == "root"
    captured = capsys.readouterr()
    assert captured.err == ""


def test_declared_only_component_alongside_derived_package_resolves_to_derived_owner() -> None:
    """IN-02 (48-REVIEW.md): a fixture combining one derived package and one declared-only
    [[components]] entry (no matching facts package, no 'dir') proves the 'dir' filter's
    documented Pitfall-1 handling directly, rather than only being read from the docstring —
    ownership resolves to the derived package without raising."""
    facts = {
        "packages": [{"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"}]
    }
    cfg = {
        "languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}],
        "components": [{"id": "declared-only", "stage": "ingest"}],
    }

    profile = conventions_for("some/file.py", cfg=cfg, facts=facts)

    assert profile["package"] == "root"
    assert profile["is_default"] is True


def test_editing_language_command_changes_every_affected_profile_with_no_profile_edit() -> None:
    """MONO-06 strong falsifiable form: a live config read, not a copied literal (RESEARCH.md
    Q3)."""
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
    """A single-package fixture: any path resolves to the root package, is_default explicitly
    True."""
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


# ---- OBS-D-03/D-11: `lint` is a permanent key, not a null-to-populate --------------------------


def test_conventions_for_always_returns_lint_key_including_no_matching_language_row() -> None:
    """The returned key set is exactly the documented 9 keys — including `lint` — for both a
    package whose language matches a `[[languages]]` row and one whose language matches none."""
    facts = {
        "packages": [
            {"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"},
            {"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "rust"},
        ]
    }
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}
    expected_keys = {
        "package",
        "dir",
        "language",
        "test",
        "format",
        "lint",
        "bash_scope",
        "agents_md",
        "is_default",
    }

    matched = conventions_for("pyproject.toml", cfg=cfg, facts=facts)
    unmatched = conventions_for("a/whatever.rs", cfg=cfg, facts=facts)

    assert set(matched.keys()) == expected_keys
    assert set(unmatched.keys()) == expected_keys


def test_lint_is_none_when_language_row_declares_no_lint_key() -> None:
    """This repo's own `python`/`dotnet` rows declare no `lint` key — `.get`, not a subscript, so
    the call must not raise `KeyError` and `lint` resolves to `None`."""
    facts = {
        "packages": [{"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"}]
    }
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}

    profile = conventions_for("whatever.py", cfg=cfg, facts=facts)

    assert profile["lint"] is None


def test_lint_value_is_read_from_the_matched_language_row_not_hardcoded() -> None:
    """A language row that DOES declare `lint` must have it surface verbatim — proving the value
    is read from config, not a hardcoded `None` shape stub (D-11)."""
    facts = {
        "packages": [{"id": "root", "manifest": "pyproject.toml", "dir": ".", "language": "python"}]
    }
    cfg = {
        "languages": [
            {"id": "python", "test": "t", "format": "f", "lint": "ruff check", "bash_scope": "uv *"}
        ]
    }

    profile = conventions_for("whatever.py", cfg=cfg, facts=facts)

    assert profile["lint"] == "ruff check"


def test_no_matching_language_row_leaves_test_format_bash_scope_and_lint_all_none() -> None:
    """When no `[[languages]]` row matches at all, `test`/`format`/`bash_scope` AND `lint` are all
    `None` (unchanged prior behavior plus the new key)."""
    facts = {
        "packages": [{"id": "a", "manifest": "a/pyproject.toml", "dir": "a", "language": "rust"}]
    }
    cfg = {"languages": [{"id": "python", "test": "t", "format": "f", "bash_scope": "uv *"}]}

    profile = conventions_for("a/whatever.rs", cfg=cfg, facts=facts)

    assert profile["test"] is None
    assert profile["format"] is None
    assert profile["bash_scope"] is None
    assert profile["lint"] is None


def test_synthetic_two_language_nested_pair_commands_differ() -> None:
    """Supplementary fixture (RESEARCH.md Q4): proves the commands-DO-differ case the real tree
    can't."""
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
