"""One assert per exclusion class (D-06) — exact reason string, no content echoed (D-10)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.adoption_scan import scan


@pytest.mark.parametrize(
    ("rel_path", "expected_reason"),
    [
        (".env", "secret-path"),
        ("sink/secret_config.py", "secret-content"),
        ("binary.dat", "binary"),
        ("node_modules/pkg/index.js", "vendored"),
        ("generated.py", "generated"),
        ("assets/oversized.dat", "size-capped"),
        ("backups/repo-dump.txt", "source-dump"),
        ("notes/full-context.txt", "source-dump"),
        ("escape", "symlink-escape"),
    ],
)
def test_exclusion_reason(tmp_minirepo: Path, rel_path: str, expected_reason: str) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    excluded = {entry["path"]: entry for entry in inventory["excluded"]}
    assert rel_path in excluded, f"expected {rel_path!r} to be excluded, got {sorted(excluded)}"
    assert excluded[rel_path]["excluded"] == expected_reason


def test_secret_content_excluded_and_not_echoed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    excluded = {entry["path"]: entry for entry in inventory["excluded"]}
    entry = excluded["sink/secret_config.py"]
    assert set(entry.keys()) == {"path", "size", "excluded"}
    assert entry["excluded"] == "secret-content"
    serialized = json.dumps(inventory)
    assert "AKIA" not in serialized, "matched secret bytes must never appear in the inventory"


def test_no_spurious_exclusions(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    included_paths = {entry["path"] for entry in inventory["included"]}
    expected_included = {
        "widget_a.py",
        "widget_b.py",
        "widget_a_modified.py",
        "README",
        "pyproject.toml",
        ".github/workflows/ci.yml",
        "tests/test_widget.py",
        "docs/adr/0001-decision.md",
        "AGENTS.md",
    }
    assert expected_included <= included_paths

    excluded_paths = {entry["path"] for entry in inventory["excluded"]}
    assert included_paths.isdisjoint(excluded_paths)
