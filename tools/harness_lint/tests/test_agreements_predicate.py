"""Tests for the shared L1-L4 agreement-file predicate."""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint.agreements import iter_agreement_files, load_agreement
from tools.harness_lint.tests.conftest import _AGREEMENTS_CREATION_ORDER
from tools.memory_regen import inject


def test_files_are_sorted_not_creation_order(tmp_agreements_tree: Path) -> None:
    """Discovery is deterministic rather than filesystem-order dependent."""
    assert _AGREEMENTS_CREATION_ORDER != tuple(sorted(_AGREEMENTS_CREATION_ORDER))
    assert [path.name for path in iter_agreement_files(tmp_agreements_tree)] == [
        "alpha-ground.md",
        "middle-retired.md",
        "zeta-proceed.md",
    ]


def test_template_and_readme_are_excluded(tmp_agreements_tree: Path) -> None:
    names = {path.name for path in iter_agreement_files(tmp_agreements_tree)}
    assert "_TEMPLATE.md" not in names
    assert "README.md" not in names


def test_symlink_escape_is_excluded(tmp_agreements_tree: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    (tmp_agreements_tree / "escape.md").symlink_to(outside)
    assert "escape.md" not in {path.name for path in iter_agreement_files(tmp_agreements_tree)}


def test_empty_and_missing_dirs_are_presence_safe(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert iter_agreement_files(empty) == []
    assert iter_agreement_files(tmp_path / "missing") == []


def test_retired_entry_is_selected(tmp_agreements_tree: Path) -> None:
    assert "middle-retired.md" in {path.name for path in iter_agreement_files(tmp_agreements_tree)}


def test_predicate_parity_with_injector_render_policy(tmp_agreements_tree: Path) -> None:
    """L1-L4 select all entries; inject alone applies its L5 active render policy."""
    paths = iter_agreement_files(tmp_agreements_tree)
    assert {path.name for path in paths} == {
        "alpha-ground.md",
        "middle-retired.md",
        "zeta-proceed.md",
    }
    active = {
        path.name
        for path in paths
        if (load_agreement(path) or ({}, ""))[0].get("status") == "active"
    }
    assert active == {"alpha-ground.md", "zeta-proceed.md"}
    rendered = inject._agreements_block(tmp_agreements_tree)
    assert "Ground claims" in rendered
    assert "Proceed deliberately" in rendered
    assert "Retired rule" not in rendered


def test_malformed_agreement_fails_closed(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.md"
    malformed.write_text("---\nstatus: [\n---\n", encoding="utf-8")
    assert load_agreement(malformed) is None
