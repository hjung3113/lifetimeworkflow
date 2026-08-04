"""End-to-end managed-adopt update, no-op, and conflict behavior."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.adoption_apply import cli as cli_module
from tools.adoption_apply import installed
from tools.adoption_apply.cli import main
from tools.adoption_scan import destinations


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _prepare_cycle(
    monkeypatch: pytest.MonkeyPatch, catalog: list[str], source: dict[str, bytes]
) -> None:
    """Keep a real draft/apply cycle small without mutating this harness checkout."""
    monkeypatch.setattr(
        destinations,
        "destination_catalog",
        lambda: [{"destination": destination} for destination in catalog],
    )
    monkeypatch.setattr(
        destinations,
        "harness_proposed_hashes",
        lambda: {destination: _sha256(payload) for destination, payload in source.items()},
    )
    monkeypatch.setattr(
        cli_module, "_harness_payload", lambda destination: source.get(destination, b"")
    )
    monkeypatch.setattr(
        cli_module,
        "_harness_block_body",
        lambda destination: source.get(destination, b"").decode("utf-8"),
    )


def _draft_apply(task_dir: Path, target: Path) -> tuple[Path, dict, str]:
    assert main(["draft", "--task-dir", str(task_dir), "--target", str(target)]) == 0
    batch_root = next((task_dir / "artifacts" / "adoption").iterdir())
    assert (
        main(
            [
                "apply",
                "--task-dir",
                str(task_dir),
                "--batch-id",
                batch_root.name,
                "--target",
                str(target),
            ]
        )
        == 0
    )
    return batch_root, json.loads((batch_root / "manifest.json").read_bytes()), batch_root.name


def _disposition(manifest: dict, destination: str) -> str:
    return next(
        row["disposition"] for row in manifest["dispositions"] if row["destination"] == destination
    )


def test_installed_record_covers_every_written_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "AGENTS.md").write_text("# Target\n", encoding="utf-8")
    task_dir = tmp_path / "task"
    source = {"AGENTS.md": b"## Managed\n", "managed.txt": b"managed\n"}
    _prepare_cycle(monkeypatch, ["AGENTS.md", "managed.txt", "preserved.txt"], source)
    (target / "preserved.txt").write_bytes(b"preserved\n")
    source["preserved.txt"] = b"preserved\n"

    _, manifest, _ = _draft_apply(task_dir, target)
    output = capsys.readouterr().err
    records = installed.read_installed_record(target)
    written = {"AGENTS.md", "managed.txt"}

    assert {record["destination"] for record in records} == written
    assert written == {
        row["destination"]
        for row in manifest["dispositions"]
        if row["disposition"] in ("create", "marker-merge", "update")
    }
    assert "applied=2 updated=0" in output
    assert "preserved.txt" not in {record["destination"] for record in records}


def test_true_no_op_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    task_dir = tmp_path / "task"
    source = {"managed.txt": b"managed\n"}
    _prepare_cycle(monkeypatch, ["managed.txt"], source)

    _draft_apply(task_dir, target)
    before = _tree_hashes(target)
    installed_before = installed.installed_path(target).read_bytes()
    capsys.readouterr()
    write_spy = MagicMock(wraps=installed.write_installed_record)
    monkeypatch.setattr(installed, "write_installed_record", write_spy)

    _, manifest, _ = _draft_apply(task_dir, target)
    output = capsys.readouterr().err
    after = _tree_hashes(target)

    assert installed.INSTALLED_REL in before
    assert before == after
    assert installed.installed_path(target).read_bytes() == installed_before
    assert write_spy.call_count == 0
    assert _disposition(manifest, "managed.txt") == "preserve"
    assert "applied=0 updated=0 unchanged=" in output


def test_update_fires_when_the_harness_source_moves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    task_dir = tmp_path / "task"
    source = {"managed.txt": b"version one\n"}
    _prepare_cycle(monkeypatch, ["managed.txt"], source)

    _draft_apply(task_dir, target)
    first_sha = installed.read_installed_record(target)[0]["installed_sha256"]
    source["managed.txt"] = b"version two\n"

    _, manifest, _ = _draft_apply(task_dir, target)
    second_sha = installed.read_installed_record(target)[0]["installed_sha256"]

    assert _disposition(manifest, "managed.txt") == "update"
    assert (target / "managed.txt").read_bytes() == b"version two\n"
    assert second_sha == _sha256(b"version two\n")
    assert second_sha != first_sha


def test_target_divergence_conflicts_and_leaves_the_file_byte_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    task_dir = tmp_path / "task"
    catalog = ["a-managed.txt"]
    source = {"a-managed.txt": b"managed\n", "z-create.txt": b"later\n"}
    _prepare_cycle(monkeypatch, catalog, source)

    _draft_apply(task_dir, target)
    recorded_sha = installed.read_installed_record(target)[0]["installed_sha256"]
    edited = b"human edit\n"
    (target / "a-managed.txt").write_bytes(edited)
    catalog.append("z-create.txt")
    capsys.readouterr()

    _, manifest, _ = _draft_apply(task_dir, target)
    output = capsys.readouterr().err

    assert _disposition(manifest, "a-managed.txt") == "conflict"
    assert (target / "a-managed.txt").read_bytes() == edited
    assert (target / "z-create.txt").read_bytes() == b"later\n"
    assert "conflict destination=a-managed.txt" in output
    assert recorded_sha in output
    assert _sha256(edited) in output
    assert "applied=1 updated=0" in output


def test_project_toml_survives_reapply_as_preserve(
    tmp_pnpm_target: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_dir = tmp_path / "task"
    source = {"harness/project.toml": b"[instance]\nname = 'managed'\n"}
    _prepare_cycle(monkeypatch, ["harness/project.toml"], source)

    _draft_apply(task_dir, tmp_pnpm_target)
    project = tmp_pnpm_target / "harness" / "project.toml"
    first = project.read_bytes()
    assert b"[[languages]]" in first

    _, manifest, _ = _draft_apply(task_dir, tmp_pnpm_target)

    assert _disposition(manifest, "harness/project.toml") == "preserve"
    assert _disposition(manifest, "harness/project.toml") not in ("conflict", "update")
    assert project.read_bytes() == first


def test_sidecar_is_spliced_on_the_update_path(
    tmp_pnpm_target: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_dir = tmp_path / "task"
    source = {"harness/project.toml": b"[instance]\nname = 'first'\n"}
    _prepare_cycle(monkeypatch, ["harness/project.toml"], source)

    _draft_apply(task_dir, tmp_pnpm_target)
    source["harness/project.toml"] = b"[instance]\nname = 'second'\n"
    capsys.readouterr()

    _, manifest, _ = _draft_apply(task_dir, tmp_pnpm_target)
    output = capsys.readouterr().err
    project = (tmp_pnpm_target / "harness" / "project.toml").read_bytes()

    assert _disposition(manifest, "harness/project.toml") == "update"
    assert b"name = 'second'" in project
    assert b"[[languages]]" in project
    assert "NOT spliced" not in output


def test_conflict_does_not_abort_the_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    task_dir = tmp_path / "task"
    catalog = ["a-conflict.txt"]
    source = {"a-conflict.txt": b"managed\n", "z-create.txt": b"later\n"}
    _prepare_cycle(monkeypatch, catalog, source)

    _draft_apply(task_dir, target)
    (target / "a-conflict.txt").write_bytes(b"human\n")
    catalog.append("z-create.txt")

    _draft_apply(task_dir, target)

    assert (target / "a-conflict.txt").read_bytes() == b"human\n"
    assert (target / "z-create.txt").read_bytes() == b"later\n"
