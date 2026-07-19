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


def test_derived_marker_does_not_false_positive_on_ordinary_prose(tmp_path: Path) -> None:
    """WR-02 (26-REVIEW.md): "derived —" alone over-matched ordinary human-authored prose using
    that exact phrasing (e.g. this repo's own two-plane-memory SKILL.md). The marker must now be
    anchored to this repo's actual generator convention ("DERIVED — do not hand-edit ...") so
    ordinary prose is NOT misclassified as generated."""
    base = tmp_path
    prose = base / "prose.md"
    prose.write_text(
        "**Gitignored-derived — `.memory/derived/pointer-index.json`** is regenerated on demand.\n",
        encoding="utf-8",
    )
    exclusion = scan.classify_exclusions(prose, base=base, max_bytes=scan.DEFAULT_MAX_FILE_BYTES)
    assert exclusion is None, f"ordinary prose must not be excluded as generated, got {exclusion}"


def test_derived_marker_still_catches_real_generated_headers(tmp_path: Path) -> None:
    """The narrowed marker still catches every real generator convention in this repo (D-06: must
    not regress detection of actually-generated content)."""
    base = tmp_path
    for name, header in (
        (
            "pointer_index.json",
            "DERIVED — do not hand-edit (tools/memory_regen/pointer_index.py)\n",
        ),
        ("repo_map.md", "DERIVED — do not hand-edit (tools/memory_regen/repo_map.py)\n"),
        (
            "relationship.md",
            "DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync\n",
        ),
    ):
        path = base / name
        path.write_text(header, encoding="utf-8")
        exclusion = scan.classify_exclusions(path, base=base, max_bytes=scan.DEFAULT_MAX_FILE_BYTES)
        assert exclusion is not None and exclusion["excluded"] == "generated", (
            f"{name!r} carrying a real DERIVED_HEADER must still be excluded as generated, "
            f"got {exclusion}"
        )


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
