"""Tests for tools.adoption_apply.approval — the ADOPT-06 refuse-by-default ratification gate.

Covers the Nyquist rows named by 27-VALIDATION.md: the two refusal tests, the three INDEPENDENT
single-axis invalidation tests (each holding the other two dimensions constant, per 27-RESEARCH's
Pitfall 2), a positive control, and the SC-1 full resume+invalidation composition with batch.py.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tools.adoption_apply import batch
from tools.adoption_apply.approval import (
    AdoptionApprovalRefused,
    check_valid,
    promote,
)

HUMAN_TOKEN_ENV = "GOLDEN_APPROVE_HUMAN"
_HUMAN_VALUE = "ratified-by-a-human"

_TASK_ID = "T-20260721030000-approval-test"
_DECISIONS = [{"item_id": "prop-1", "kind": "contract", "disposition": "approve"}]


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    (root / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=root, check=True)
    return root


def _write_state(task_dir: Path, *, revision: int, commit: str) -> None:
    state = {
        "task_id": _TASK_ID,
        "phase": "INTAKE",
        "revision": revision,
        "baseline": {"repo_root": ".", "commit": commit},
        "current_ref": commit,
        "completed_items": [],
        "next_action": "review adoption batch",
        "blockers": [],
        "transition": None if revision == 0 else {"from": "INTAKE", "to": "INTAKE"},
    }
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "state.json").write_bytes(
        (json.dumps(state, sort_keys=True, indent=2) + "\n").encode("utf-8")
    )


def _bump_revision(task_dir: Path) -> None:
    state = json.loads((task_dir / "state.json").read_bytes())
    _write_state(task_dir, revision=state["revision"] + 1, commit=state["current_ref"])


@pytest.fixture()
def task_dir(git_repo: Path) -> Path:
    task = git_repo / "task"
    head = _git(git_repo, "rev-parse", "HEAD")
    _write_state(task, revision=0, commit=head)
    return task


def _write_draft(batch_dir: Path, *, plan_seed: str = "p1") -> None:
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "inventory.json").write_bytes(b'{"inventory": true}\n')
    (batch_dir / "plan.json").write_bytes(f'{{"plan": "{plan_seed}"}}\n'.encode())
    (batch_dir / "manifest.json").write_bytes(b'{"manifest": true}\n')


def _seed_batch(task_dir: Path, git_repo: Path, *, plan_seed: str = "p1") -> str:
    moment = datetime(2026, 7, 21, 3, 0, 0, tzinfo=UTC)
    status = batch.create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    batch_id = status["batch_id"]
    _write_draft(batch._batch_dir(task_dir, batch_id), plan_seed=plan_seed)
    return batch_id


def test_refused_without_human_confirmation(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(HUMAN_TOKEN_ENV, raising=False)
    batch_id = _seed_batch(task_dir, git_repo)
    with pytest.raises(AdoptionApprovalRefused):
        promote(
            task_dir,
            batch_id,
            git_repo,
            approve=True,
            decisions=_DECISIONS,
            confirmation=None,
        )


def test_refused_without_approve_flag(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    batch_id = _seed_batch(task_dir, git_repo)
    with pytest.raises(AdoptionApprovalRefused):
        promote(
            task_dir,
            batch_id,
            git_repo,
            approve=False,
            decisions=_DECISIONS,
            confirmation=_HUMAN_VALUE,
        )


def test_valid_when_nothing_changed(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    batch_id = _seed_batch(task_dir, git_repo)
    promote(
        task_dir,
        batch_id,
        git_repo,
        approve=True,
        decisions=_DECISIONS,
        confirmation=_HUMAN_VALUE,
    )
    assert check_valid(task_dir, batch_id, git_repo) is True


def test_invalidated_on_draft_change(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Draft changes; revision AND ref held constant."""
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    batch_id = _seed_batch(task_dir, git_repo)
    promote(
        task_dir,
        batch_id,
        git_repo,
        approve=True,
        decisions=_DECISIONS,
        confirmation=_HUMAN_VALUE,
    )
    assert check_valid(task_dir, batch_id, git_repo) is True

    # Simulate a re-draft: mutate ONLY plan.json's bytes.
    _write_draft(batch._batch_dir(task_dir, batch_id), plan_seed="p2-redrafted")

    assert check_valid(task_dir, batch_id, git_repo) is False


def test_invalidated_on_revision_change(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Task revision changes; draft AND ref held constant."""
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    batch_id = _seed_batch(task_dir, git_repo)
    promote(
        task_dir,
        batch_id,
        git_repo,
        approve=True,
        decisions=_DECISIONS,
        confirmation=_HUMAN_VALUE,
    )
    assert check_valid(task_dir, batch_id, git_repo) is True

    _bump_revision(task_dir)

    assert check_valid(task_dir, batch_id, git_repo) is False


def test_invalidated_on_ref_change(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git ref changes; draft AND revision held constant."""
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    batch_id = _seed_batch(task_dir, git_repo)
    promote(
        task_dir,
        batch_id,
        git_repo,
        approve=True,
        decisions=_DECISIONS,
        confirmation=_HUMAN_VALUE,
    )
    assert check_valid(task_dir, batch_id, git_repo) is True

    (git_repo / "advance.txt").write_text("advance\n", encoding="utf-8")
    subprocess.run(["git", "add", "advance.txt"], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "advance HEAD"], cwd=git_repo, check=True)

    assert check_valid(task_dir, batch_id, git_repo) is False


def test_valid_false_on_missing_draft_artifact(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WR-02: a batch missing one of its 3 draft artifacts returns False, never raises."""
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    batch_id = _seed_batch(task_dir, git_repo)
    promote(
        task_dir,
        batch_id,
        git_repo,
        approve=True,
        decisions=_DECISIONS,
        confirmation=_HUMAN_VALUE,
    )
    assert check_valid(task_dir, batch_id, git_repo) is True

    (batch._batch_dir(task_dir, batch_id) / "plan.json").unlink()

    assert check_valid(task_dir, batch_id, git_repo) is False


def test_sc1_full_resume_cycle(
    task_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-1: batch resumes safely; changed draft/ref/revision invalidates a valid approval."""
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    moment = datetime(2026, 7, 21, 3, 0, 0, tzinfo=UTC)

    # (1) New batch created.
    first = batch.create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    batch_id = first["batch_id"]

    # (2) Write synthetic draft artifacts into the batch dir.
    _write_draft(batch._batch_dir(task_dir, batch_id))

    # (3) promote() succeeds; check_valid() is True.
    promote(
        task_dir,
        batch_id,
        git_repo,
        approve=True,
        decisions=_DECISIONS,
        confirmation=_HUMAN_VALUE,
    )
    assert check_valid(task_dir, batch_id, git_repo) is True

    # (4) A same-ref, same-UTC-date resume returns the SAME batch and leaves the approval valid.
    second = batch.create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    assert second["batch_id"] == batch_id
    assert check_valid(task_dir, batch_id, git_repo) is True

    # (5) Mutating one axis (draft) invalidates the approval.
    _write_draft(batch._batch_dir(task_dir, batch_id), plan_seed="resumed-then-redrafted")
    assert check_valid(task_dir, batch_id, git_repo) is False
