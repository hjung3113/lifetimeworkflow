"""Installed-record persistence is schema-validated and isolated from the destination catalog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.adoption_apply import installed
from tools.adoption_apply.apply import PathEscapeError
from tools.adoption_scan import destinations


def _records() -> list[dict]:
    return [
        {"destination": "b.py", "installed_sha256": "1" * 64, "batch_id": "batch-1"},
        {"destination": "a.py", "installed_sha256": "0" * 64, "batch_id": "batch-1"},
    ]


def test_public_surface_is_exactly_four_names() -> None:
    assert set(installed.__all__) == {
        "INSTALLED_REL",
        "installed_path",
        "read_installed_record",
        "write_installed_record",
    }


def test_round_trip_sorts_and_has_only_content_derived_keys(tmp_path: Path) -> None:
    path = installed.write_installed_record(tmp_path, _records())
    document = json.loads(path.read_text(encoding="utf-8"))

    assert set(document) == {"installed"}
    assert all(
        set(record) == {"destination", "installed_sha256", "batch_id"}
        for record in document["installed"]
    )
    assert installed.read_installed_record(tmp_path) == [
        {"destination": "a.py", "installed_sha256": "0" * 64, "batch_id": "batch-1"},
        {"destination": "b.py", "installed_sha256": "1" * 64, "batch_id": "batch-1"},
    ]


def test_absent_record_is_empty(tmp_path: Path) -> None:
    assert installed.read_installed_record(tmp_path) == []


def test_tampered_hash_is_refused_on_read(tmp_path: Path) -> None:
    path = installed.write_installed_record(tmp_path, _records())
    path.write_text(
        json.dumps(
            {
                "installed": [
                    {"destination": "a.py", "installed_sha256": "not-a-hash", "batch_id": "x"}
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(installed.InstalledRecordError, match="invalid installed record"):
        installed.read_installed_record(tmp_path)


@pytest.mark.parametrize(
    "document",
    [
        {"installed": [], "unexpected": True},
        {
            "installed": [
                {
                    "destination": "a.py",
                    "installed_sha256": "0" * 64,
                    "batch_id": "x",
                    "unexpected": True,
                }
            ]
        },
    ],
)
def test_extra_keys_are_refused_on_read(tmp_path: Path, document: dict) -> None:
    path = installed.installed_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(installed.InstalledRecordError, match="Additional properties"):
        installed.read_installed_record(tmp_path)


def test_invalid_write_fails_before_creating_a_file(tmp_path: Path) -> None:
    with pytest.raises(installed.InstalledRecordError, match="installed record"):
        installed.write_installed_record(
            tmp_path,
            [{"destination": "a.py", "installed_sha256": "bad", "batch_id": "batch-1"}],
        )
    assert not installed.installed_path(tmp_path).exists()


def test_write_refuses_an_escaping_installed_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(installed, "installed_path", lambda _: tmp_path.parent / "outside.json")

    with pytest.raises(PathEscapeError):
        installed.write_installed_record(tmp_path, _records())


def test_installed_record_is_catalog_isolated(monkeypatch, tmp_path: Path) -> None:
    live_destinations = {row["destination"] for row in destinations.destination_catalog()}
    assert installed.INSTALLED_REL not in live_destinations

    record = tmp_path / installed.INSTALLED_REL
    record.parent.mkdir(parents=True)
    record.write_text("{}\n", encoding="utf-8")
    control = tmp_path / "docs/how-to/real.md"
    control.parent.mkdir(parents=True)
    control.write_text("control\n", encoding="utf-8")
    monkeypatch.setattr(destinations, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(destinations, "_CATEGORY_GLOBS", (".harness/**/*", "docs/how-to/**/*"))
    monkeypatch.setattr(destinations, "_tracked_repo_files", lambda: None)

    catalog = {row["destination"] for row in destinations.destination_catalog()}
    assert installed.INSTALLED_REL not in catalog
    assert "docs/how-to/real.md" in catalog
