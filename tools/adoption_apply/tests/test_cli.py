"""Tests for tools.adoption_apply.cli — the draft/apply/promote dispatcher composing
batch.py/apply.py/approval.py end to end (added plan-checker revision iteration 1).

Covers: the promote refusal->exit-3 contract at BOTH the direct main() call boundary and an
OS-level subprocess boundary (proving __main__.py's ``from tools.adoption_apply.cli import main``
now resolves), and the draft/apply sub-verbs exercising real filesystem effects (never merely an
import check).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tools.adoption_apply.cli import main

HUMAN_TOKEN_ENV = "GOLDEN_APPROVE_HUMAN"
_HUMAN_VALUE = "ratified-by-a-human"
_TASK_ID = "T-20260721040000-cli-test"
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


@pytest.fixture()
def task_dir(git_repo: Path) -> Path:
    task = git_repo / "task"
    head = _git(git_repo, "rev-parse", "HEAD")
    _write_state(task, revision=0, commit=head)
    return task


def _write_draft(batch_dir: Path) -> None:
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "inventory.json").write_bytes(b'{"inventory": true}\n')
    (batch_dir / "plan.json").write_bytes(b'{"plan": "p1"}\n')
    (batch_dir / "manifest.json").write_bytes(b'{"manifest": true}\n')


def _seed_batch_dir(task_dir: Path) -> tuple[str, Path]:
    from tools.adoption_apply import batch

    moment = datetime(2026, 7, 21, 4, 0, 0, tzinfo=UTC)
    status = batch.create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    batch_id = status["batch_id"]
    batch_dir = batch._batch_dir(task_dir, batch_id)
    _write_draft(batch_dir)
    return batch_id, batch_dir


@pytest.fixture()
def decisions_path(tmp_path: Path) -> Path:
    path = tmp_path / "decisions.json"
    path.write_text(json.dumps(_DECISIONS), encoding="utf-8")
    return path


def test_cli_promote_refused_exit_code_3(
    task_dir: Path, git_repo: Path, decisions_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main(["promote", ...]) with no --approve/--confirm returns exactly int 3."""
    monkeypatch.delenv(HUMAN_TOKEN_ENV, raising=False)
    batch_id, _ = _seed_batch_dir(task_dir)

    exit_code = main(
        [
            "promote",
            "--task-dir",
            str(task_dir),
            "--batch-id",
            batch_id,
            "--repo-root",
            str(git_repo),
            "--decisions",
            str(decisions_path),
        ]
    )

    assert exit_code == 3


def test_cli_promote_refused_exit_code_3_subprocess(
    task_dir: Path, git_repo: Path, decisions_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The identical refusal scenario at OS-level: subprocess.run(...).returncode == 3."""
    monkeypatch.delenv(HUMAN_TOKEN_ENV, raising=False)
    batch_id, _ = _seed_batch_dir(task_dir)

    env = {k: v for k, v in __import__("os").environ.items() if k != HUMAN_TOKEN_ENV}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.adoption_apply",
            "promote",
            "--task-dir",
            str(task_dir),
            "--batch-id",
            batch_id,
            "--repo-root",
            str(git_repo),
            "--decisions",
            str(decisions_path),
        ],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 3, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_cli_promote_succeeds_with_full_human_signals(
    task_dir: Path, git_repo: Path, decisions_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Positive control: all three human signals present -> exit 0, PROMOTED printed."""
    monkeypatch.setenv(HUMAN_TOKEN_ENV, _HUMAN_VALUE)
    batch_id, _ = _seed_batch_dir(task_dir)

    exit_code = main(
        [
            "promote",
            "--task-dir",
            str(task_dir),
            "--batch-id",
            batch_id,
            "--repo-root",
            str(git_repo),
            "--decisions",
            str(decisions_path),
            "--approve",
            "--confirm",
            _HUMAN_VALUE,
        ]
    )

    assert exit_code == 0


@pytest.fixture()
def synthetic_target(tmp_path: Path) -> Path:
    """A small synthetic target tree — this test's OWN fixture (not Plan 27-05's fixtures)."""
    target = tmp_path / "synthetic-target"
    target.mkdir()
    (target / "README").write_text("a plain readme\n", encoding="utf-8")
    (target / "src").mkdir()
    (target / "src" / "widget.py").write_text("print('hi')\n", encoding="utf-8")
    return target


def test_cli_draft_writes_into_batch_root(
    task_dir: Path, synthetic_target: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main(["draft", ...]) writes 3 artifacts under the batch root; target is byte-unchanged."""
    monkeypatch.chdir(Path(__file__).resolve().parents[3])
    readme_before = (synthetic_target / "README").read_bytes()
    widget_before = (synthetic_target / "src" / "widget.py").read_bytes()

    exit_code = main(
        [
            "draft",
            "--task-dir",
            str(task_dir),
            "--target",
            str(synthetic_target),
        ]
    )

    assert exit_code == 0
    batch_dirs = list((task_dir / "artifacts" / "adoption").iterdir())
    assert len(batch_dirs) == 1
    batch_root = batch_dirs[0]
    for name in ("inventory.json", "plan.json", "manifest.json"):
        assert (batch_root / name).is_file(), f"missing {name}"

    assert (synthetic_target / "README").read_bytes() == readme_before
    assert (synthetic_target / "src" / "widget.py").read_bytes() == widget_before


def test_cli_apply_end_to_end(
    task_dir: Path, synthetic_target: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """draft then apply against a separate scratch apply-target — at least one create lands."""
    monkeypatch.chdir(Path(__file__).resolve().parents[3])

    draft_exit = main(
        [
            "draft",
            "--task-dir",
            str(task_dir),
            "--target",
            str(synthetic_target),
        ]
    )
    assert draft_exit == 0

    batch_dirs = list((task_dir / "artifacts" / "adoption").iterdir())
    assert len(batch_dirs) == 1
    batch_id = batch_dirs[0].name

    apply_target = tmp_path / "apply-target"
    apply_target.mkdir()

    apply_exit = main(
        [
            "apply",
            "--task-dir",
            str(task_dir),
            "--batch-id",
            batch_id,
            "--target",
            str(apply_target),
        ]
    )

    assert apply_exit == 0
    manifest = json.loads((batch_dirs[0] / "manifest.json").read_bytes())
    create_destinations = [
        record["destination"]
        for record in manifest["dispositions"]
        if record["disposition"] == "create"
    ]
    assert create_destinations, "expected at least one create-disposition destination"

    applied_at_least_one = False
    for destination in create_destinations:
        applied_path = apply_target / destination
        if applied_path.is_file():
            applied_at_least_one = True
            break
    assert applied_at_least_one, "no create-disposition destination landed on disk"
