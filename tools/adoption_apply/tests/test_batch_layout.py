"""Tests for tools.adoption_apply.batch — content-derived batch id, CAS-guarded status (ADOPT-04).

Covers the two Nyquist rows named by 27-01-PLAN.md's must_haves.artifacts:
``test_resume_safely`` and ``test_batch_uses_existing_cas``, plus the two supporting cases the
plan's Test matrix names (`<behavior>` block).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tools.adoption_apply.batch import (
    BatchError,
    batch_id_for,
    create_or_resume_batch,
    read_status,
    update_status,
)


@pytest.fixture()
def task_dir(tmp_path: Path) -> Path:
    root = tmp_path / "task"
    root.mkdir()
    return root


def test_resume_safely(task_dir: Path) -> None:
    moment = datetime(2026, 7, 21, 3, 0, 0, tzinfo=UTC)
    first = create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    status_path = task_dir / "artifacts" / "adoption" / first["batch_id"] / "status.json"
    assert status_path.is_file()
    before = status_path.read_bytes()

    later_same_day = datetime(2026, 7, 21, 21, 0, 0, tzinfo=UTC)
    second = create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=later_same_day)

    assert second["batch_id"] == first["batch_id"]
    after = status_path.read_bytes()
    assert after == before, "a same-day resume must be a true no-op — status.json bytes unchanged"


def test_different_ref_or_date_mints_new_batch(task_dir: Path) -> None:
    moment = datetime(2026, 7, 21, 3, 0, 0, tzinfo=UTC)
    baseline = batch_id_for("refs/heads/main", moment)

    different_ref = batch_id_for("refs/heads/feature", moment)
    assert different_ref != baseline

    next_day = datetime(2026, 7, 22, 3, 0, 0, tzinfo=UTC)
    different_date = batch_id_for("refs/heads/main", next_day)
    assert different_date != baseline

    first = create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    second = create_or_resume_batch(task_dir, "refs/heads/feature", discovered_at=moment)
    assert first["batch_id"] != second["batch_id"]


def test_batch_uses_existing_cas(task_dir: Path) -> None:
    moment = datetime(2026, 7, 21, 3, 0, 0, tzinfo=UTC)
    batch = create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    status_path = task_dir / "artifacts" / "adoption" / batch["batch_id"] / "status.json"
    before = status_path.read_bytes()

    with pytest.raises(BatchError):
        update_status(
            task_dir, batch["batch_id"], expected_revision=5, patch={"revision": 6, "note": "stale"}
        )

    after = status_path.read_bytes()
    assert after == before, "a rejected stale write must touch nothing"


def test_update_status_requires_exact_increment(task_dir: Path) -> None:
    moment = datetime(2026, 7, 21, 3, 0, 0, tzinfo=UTC)
    batch = create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)

    with pytest.raises(BatchError):
        update_status(
            task_dir, batch["batch_id"], expected_revision=0, patch={"revision": 2, "note": "skip"}
        )

    updated = update_status(
        task_dir, batch["batch_id"], expected_revision=0, patch={"revision": 1, "note": "ok"}
    )
    assert updated["revision"] == 1
    assert updated["note"] == "ok"

    stored = read_status(task_dir, batch["batch_id"])
    assert stored is not None
    assert json.dumps(stored, sort_keys=True) == json.dumps(updated, sort_keys=True)
