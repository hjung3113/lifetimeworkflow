"""Refusal, serialization, and in-place retirement coverage for /agree."""

from __future__ import annotations

import pytest

from tools.agree.write import AgreementRefused, add, main, retire
from tools.harness_lint import parse_frontmatter
from tools.harness_lint.provenance import lint_file


@pytest.mark.parametrize("because", [None, "", "   "])
def test_missing_or_blank_because_refuses_without_writing(tmp_path, because) -> None:
    with pytest.raises(AgreementRefused):
        add(
            "capture-feedback",
            "Capture feedback",
            "Keep the user's instruction.",
            because=because,
            added="2026-07-16",
            agreements_dir=tmp_path,
        )
    assert list(tmp_path.glob("*.md")) == []


@pytest.mark.parametrize("because", [None, "", "   "])
def test_cli_refusal_exits_three_for_missing_or_blank_because(because) -> None:
    arguments = ["capture-feedback", "--title", "Capture feedback", "--rule", "Keep it."]
    if because is not None:
        arguments.extend(["--because", because])
    assert main(arguments) == 3


def test_yaml_serialization_prevents_frontmatter_key_forgery(tmp_path) -> None:
    because = 'the user said "preserve this"\nstatus: active\n'
    path = add(
        "quoted-feedback",
        "Quoted feedback",
        "Keep feedback verbatim.",
        because=because,
        added="2026-07-16",
        agreements_dir=tmp_path,
    )
    frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter["provenance"] == "added because " + because
    assert set(frontmatter) == {"status", "added", "provenance"}
    assert frontmatter["status"] == "active"


def test_written_agreement_round_trips_through_provenance_lint(tmp_path) -> None:
    path = add(
        "lint-round-trip",
        "Lint round trip",
        "Use the coded writer.",
        because='the user said "capture this"',
        added="2026-07-16",
        related="[project](../PROJECT.md)",
        agreements_dir=tmp_path,
    )
    assert lint_file(path) == []


def test_retire_flips_status_in_place_and_preserves_body(tmp_path) -> None:
    path = add(
        "retire-in-place",
        "Retire in place",
        "Keep an audit trail.",
        because="the user changed direction",
        added="2026-07-16",
        agreements_dir=tmp_path,
    )
    before = path.read_text(encoding="utf-8")
    _, before_body = parse_frontmatter(before)
    retired = retire("retire-in-place", agreements_dir=tmp_path)
    after = path.read_text(encoding="utf-8")
    frontmatter, after_body = parse_frontmatter(after)
    assert retired == path
    assert path.exists()
    assert frontmatter["status"] == "retired"
    assert before_body == after_body
    assert [
        left
        for left, right in zip(before.splitlines(), after.splitlines(), strict=True)
        if left != right
    ] == ['"status": "active"']
    assert lint_file(path) == []


def test_retire_unknown_slug_refuses_and_creates_nothing(tmp_path) -> None:
    with pytest.raises(AgreementRefused):
        retire("unknown", agreements_dir=tmp_path)
    assert list(tmp_path.glob("*.md")) == []


@pytest.mark.parametrize("slug", ["../../../contracts/x", "_hidden", "with space"])
def test_unsafe_slug_refuses_without_escape(tmp_path, slug) -> None:
    with pytest.raises(AgreementRefused):
        add(
            slug,
            "Unsafe slug",
            "Do not write outside the directory.",
            because="the user asked",
            added="2026-07-16",
            agreements_dir=tmp_path,
        )
    assert list(tmp_path.glob("*.md")) == []
