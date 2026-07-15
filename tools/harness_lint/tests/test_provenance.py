"""Validation map coverage for agreement provenance lint."""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint.provenance import check_agreement, lint_dir, lint_file, main


def _write_entry(directory: Path, name: str = "entry.md", **frontmatter: str) -> Path:
    fields = "\n".join(f"{key}: {value}" for key, value in frontmatter.items())
    path = directory / name
    path.write_text(f"---\n{fields}\n---\n\n# Test\n\nRule.\n", encoding="utf-8")
    return path


def _codes(violations: list[object]) -> set[str]:
    return {violation.rule for violation in violations}  # type: ignore[attr-defined]


def test_well_formed_stamp_is_clean() -> None:
    assert (
        check_agreement(
            {
                "status": "active",
                "added": "2026-01-02",
                "provenance": "added because the user asked for it",
            }
        )
        == []
    )


def test_absent_provenance_is_a_violation() -> None:
    assert "PROV-provenance" in _codes(check_agreement({"status": "active", "added": "2026-01-02"}))


def test_provenance_requires_added_because_prefix() -> None:
    assert "PROV-provenance" in _codes(
        check_agreement(
            {"status": "active", "added": "2026-01-02", "provenance": "because requested"}
        )
    )


def test_provenance_rejects_empty_tail() -> None:
    assert "PROV-provenance" in _codes(
        check_agreement({"status": "active", "added": "2026-01-02", "provenance": "added because"})
    )


def test_provenance_rejects_whitespace_only_tail() -> None:
    assert "PROV-provenance" in _codes(
        check_agreement(
            {"status": "active", "added": "2026-01-02", "provenance": "added because   "}
        )
    )


def test_unquoted_date_yields_violation_not_typeerror(tmp_path: Path) -> None:
    entry = _write_entry(
        tmp_path,
        status="active",
        added="2026-07-16",
        provenance='"added because requested"',
    )
    assert "PROV-added-type" in _codes(lint_file(entry))


def test_non_iso_added_stamp_is_a_violation() -> None:
    assert "PROV-added-format" in _codes(
        check_agreement(
            {"status": "active", "added": "16-07-2026", "provenance": "added because requested"}
        )
    )


def test_pending_status_is_a_violation(tmp_path: Path) -> None:
    _write_entry(
        tmp_path,
        status="pending",
        added='"2026-01-02"',
        provenance='"added because requested"',
    )
    assert "PROV-status" in {violation.rule for _, violation in lint_dir(tmp_path)}


def test_retired_entries_are_linted_without_being_rejected(tmp_path: Path) -> None:
    clean = _write_entry(
        tmp_path,
        "retired-clean.md",
        status="retired",
        added='"2026-01-02"',
        provenance='"added because requested"',
    )
    dirty = _write_entry(tmp_path, "retired-dirty.md", status="retired", added='"2026-01-02"')
    assert lint_file(clean) == []
    assert "PROV-provenance" in _codes(lint_file(dirty))


def test_template_and_readme_are_excluded(tmp_path: Path) -> None:
    _write_entry(tmp_path, "_TEMPLATE.md", status="active")
    (tmp_path / "README.md").write_text("documentation\n", encoding="utf-8")
    assert lint_dir(tmp_path) == []


def test_empty_directory_is_clean(tmp_path: Path) -> None:
    assert lint_dir(tmp_path) == []


def test_main_uses_stdout_for_ok_and_stderr_for_all_failures(tmp_path: Path, capsys) -> None:
    assert main([str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert "provenance-lint: OK" in captured.out
    assert captured.err == ""

    _write_entry(tmp_path, status="pending")
    assert main([str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "PROV-status" in captured.err
    assert "PROV-added-type" in captured.err
    assert "PROV-provenance" in captured.err
    assert captured.out == ""
