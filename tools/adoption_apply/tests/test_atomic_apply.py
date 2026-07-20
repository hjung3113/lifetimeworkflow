"""test_atomic_apply.py — apply_manifest totality, drift refusal, idempotence, SC-2 integration.

Covers: idempotent re-apply, concurrent-drift refusal, marker-merge idempotence, no-arbitrary-
command-execution, draft-mode artifact-root confinement (ADOPT-05 clause 1), and the SC-2 full
apply-cycle integration proof (one of each of the 6 dispositions in a single manifest).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.adoption_apply import apply


def test_idempotent_reapply(tmp_path):
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "src/widget.py", "disposition": "create"}],
        "excluded": [],
    }
    payloads = {"src/widget.py": b"print('hi')\n"}

    summary = apply.apply_manifest(manifest, tmp_path, payloads=payloads)
    assert summary["applied"] == ["src/widget.py"]

    target = tmp_path / "src" / "widget.py"
    original_bytes = target.read_bytes()

    # A re-drafted manifest against the now-existing target correctly reports preserve — the
    # disposition chain never re-emits `create` for a target it already knows about.
    manifest_redraft = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "src/widget.py", "disposition": "preserve"}],
        "excluded": [],
    }
    summary_2 = apply.apply_manifest(manifest_redraft, tmp_path, payloads=payloads)

    assert summary_2["skipped"] == ["src/widget.py"]
    assert target.read_bytes() == original_bytes


def test_concurrent_drift_refused(tmp_path):
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "src/widget.py", "disposition": "create"}],
        "excluded": [],
    }
    target = tmp_path / "src" / "widget.py"
    target.parent.mkdir(parents=True)
    out_of_band_bytes = b"human edited this after draft time\n"
    target.write_bytes(out_of_band_bytes)

    with pytest.raises(apply.ConcurrentDriftError):
        apply.apply_manifest(manifest, tmp_path, payloads={"src/widget.py": b"new content\n"})

    assert target.read_bytes() == out_of_band_bytes


def test_marker_merge_idempotent(tmp_path):
    target = tmp_path / "AGENTS.md"
    target.write_text("# Repo agents\n\nSome human prose.\n", encoding="utf-8")
    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "AGENTS.md", "disposition": "marker-merge"}],
        "excluded": [],
    }
    block_bodies = {"AGENTS.md": "## Project\n\nManaged content.\n"}

    apply.apply_manifest(manifest, tmp_path, block_bodies=block_bodies)
    first_pass = target.read_text(encoding="utf-8")

    apply.apply_manifest(manifest, tmp_path, block_bodies=block_bodies)
    second_pass = target.read_text(encoding="utf-8")

    assert first_pass == second_pass
    assert "## Project" in first_pass
    assert "Some human prose." in first_pass


def test_no_arbitrary_command_execution(tmp_path, monkeypatch):
    run_spy = MagicMock()
    monkeypatch.setattr("subprocess.run", run_spy)

    settings_target = tmp_path / ".claude" / "settings.json"
    settings_target.parent.mkdir(parents=True)
    settings_target.write_text("{}\n", encoding="utf-8")

    manifest = {
        "target_ref": "unknown",
        "dispositions": [
            {"destination": "src/widget.py", "disposition": "create"},
            {"destination": ".claude/settings.json", "disposition": "marker-merge"},
            {"destination": "src/existing.py", "disposition": "preserve"},
            {"destination": "src/other.py", "disposition": "conflict"},
        ],
        "excluded": [],
    }
    apply.apply_manifest(manifest, tmp_path, payloads={"src/widget.py": b"x = 1\n"})

    assert run_spy.call_count == 0


def test_no_arbitrary_command_execution_structural():
    """Structural proof: apply.py's own source never calls subprocess.run at all."""
    source = Path(apply.__file__).read_text(encoding="utf-8")
    assert "subprocess.run(" not in source


def test_draft_confined_to_artifact_root(tmp_path):
    root = tmp_path / "artifacts" / "adoption" / "batch123"
    root.mkdir(parents=True)

    # A legitimate in-root draft write must not raise.
    apply.refuse_if_outside_root(root / "inventory.json", root)

    # A direct out-of-root write (one artifact-kind level up) is refused.
    with pytest.raises(apply.PathEscapeError):
        apply.refuse_if_outside_root(root.parent.parent / "escape.json", root)

    # A `..`-traversal escape attempt is refused — proves resolved-path, not string-prefix, logic.
    with pytest.raises(apply.PathEscapeError):
        apply.refuse_if_outside_root(root / ".." / ".." / ".." / "etc" / "passwd", root)


def test_sc2_full_apply_cycle(tmp_path):
    settings_target = tmp_path / ".claude" / "settings.json"
    settings_target.parent.mkdir(parents=True)
    settings_target.write_text("{}\n", encoding="utf-8")

    constitution_target = "contracts/new-widget.schema.json"

    manifest = {
        "target_ref": "unknown",
        "dispositions": [
            {"destination": "src/widget.py", "disposition": "create"},
            {"destination": ".claude/settings.json", "disposition": "marker-merge"},
            {"destination": "src/existing.py", "disposition": "preserve"},
            {"destination": "src/other.py", "disposition": "conflict"},
            {"destination": "docs/reference/index.md", "disposition": "derived-regenerate"},
            {"destination": constitution_target, "disposition": "human-ratification-required"},
        ],
        "excluded": [],
    }

    create_spy = MagicMock(wraps=apply.atomic_create)
    original_atomic_create = apply.atomic_create
    try:
        apply.atomic_create = create_spy
        summary = apply.apply_manifest(
            manifest, tmp_path, payloads={"src/widget.py": b"print(1)\n"}
        )
    finally:
        apply.atomic_create = original_atomic_create

    # Constitution-plane row refused before mutation — zero calls involving it.
    assert constitution_target in summary["refused"]
    assert constitution_target not in summary["applied"]
    assert not (tmp_path / constitution_target).exists()
    for call in create_spy.call_args_list:
        assert constitution_target not in str(call.args[0])

    # create row lands atomically.
    assert "src/widget.py" in summary["applied"]
    assert (tmp_path / "src" / "widget.py").read_bytes() == b"print(1)\n"

    # marker-merge row applied on the first pass.
    assert ".claude/settings.json" in summary["applied"]

    # preserve/conflict/derived-regenerate are all no-ops.
    for skipped_destination in ("src/existing.py", "src/other.py", "docs/reference/index.md"):
        assert skipped_destination in summary["skipped"]
        assert not (tmp_path / skipped_destination).exists()

    # marker-merge row is idempotent on a second pass — everything else re-drafted to preserve.
    first_settings_bytes = settings_target.read_bytes()
    manifest_pass_2 = {
        "target_ref": "unknown",
        "dispositions": [
            {"destination": "src/widget.py", "disposition": "preserve"},
            {"destination": ".claude/settings.json", "disposition": "marker-merge"},
            {"destination": "src/existing.py", "disposition": "preserve"},
            {"destination": "src/other.py", "disposition": "conflict"},
            {"destination": "docs/reference/index.md", "disposition": "derived-regenerate"},
            {"destination": constitution_target, "disposition": "human-ratification-required"},
        ],
        "excluded": [],
    }
    summary_2 = apply.apply_manifest(manifest_pass_2, tmp_path)
    assert settings_target.read_bytes() == first_settings_bytes
    assert constitution_target in summary_2["refused"]

    # summary dict correctly buckets all 6 rows in the first pass.
    assert sorted(summary["applied"] + summary["skipped"] + summary["refused"]) == sorted(
        record["destination"] for record in manifest["dispositions"]
    )
