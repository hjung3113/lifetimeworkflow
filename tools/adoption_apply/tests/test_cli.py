"""Tests for tools.adoption_apply.cli — the draft/apply dispatcher composing
batch.py/apply.py end to end (added plan-checker revision iteration 1).

Covers: the draft/apply sub-verbs exercising real filesystem effects (never merely an import
check). The former ADOPT-06 promote/approval gate is deleted (D-01); the review moves to the PR.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tools.adoption_apply.cli import main

_TASK_ID = "T-20260721040000-cli-test"


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


def _seed_batch_with_manifest(task_dir: Path, manifest: dict) -> tuple[str, Path]:
    """A batch whose manifest.json is *manifest* verbatim — inventory/plan content is never
    re-validated by ``apply``, so it is deliberately dummy."""
    from tools.adoption_apply import batch

    moment = datetime(2026, 7, 21, 5, 0, 0, tzinfo=UTC)
    status = batch.create_or_resume_batch(task_dir, "refs/heads/main", discovered_at=moment)
    batch_id = status["batch_id"]
    batch_dir = batch._batch_dir(task_dir, batch_id)
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "inventory.json").write_bytes(b'{"inventory": true}\n')
    (batch_dir / "plan.json").write_bytes(b'{"plan": "p1"}\n')
    (batch_dir / "manifest.json").write_bytes(
        (json.dumps(manifest, sort_keys=True) + "\n").encode("utf-8")
    )
    return batch_id, batch_dir


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
    task_dir: Path,
    git_repo: Path,
    synthetic_target: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """draft, then apply against a separate scratch apply-target — at least one create lands.

    D-01 rationale: the former ADOPT-06 promote step is deleted whole; draft -> apply now runs
    with no intervening gate (D-03) and no existing assertion in this test is weakened — only the
    promote step is removed.
    """
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
            "--repo-root",
            str(git_repo),
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


# --- WR-04 (27.1-02): apply re-validates manifest.json against its schema before use ------------


def test_cli_apply_refuses_on_malformed_manifest(
    task_dir: Path,
    git_repo: Path,
    tmp_path: Path,
) -> None:
    """manifest.json is valid JSON but schema-invalid (missing required "excluded") -> exit 1."""
    malformed_manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "src/widget.py", "disposition": "create"}],
        # "excluded" deliberately omitted — required by manifest.schema.json.
    }
    batch_id, _ = _seed_batch_with_manifest(task_dir, malformed_manifest)

    apply_target = tmp_path / "apply-target"
    apply_target.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.adoption_apply",
            "apply",
            "--task-dir",
            str(task_dir),
            "--batch-id",
            batch_id,
            "--target",
            str(apply_target),
            "--repo-root",
            str(git_repo),
        ],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "schema" in result.stderr.lower()
    assert "Traceback" not in result.stderr
    assert list(apply_target.iterdir()) == []


# --- Plan-checker BLOCKER (27.1-02): hostile destinations refuse cleanly, never a traceback -----


def test_cli_apply_refuses_hostile_destination_cleanly(
    task_dir: Path,
    git_repo: Path,
    tmp_path: Path,
) -> None:
    """An absolute destination, a `..`-traversal destination, and a symlinked marker-capable
    destination each refuse with exit 1, a clean stderr message, no `Traceback`, and zero writes —
    the same clean bucket every other apply_manifest-raised fault already gets (SC-2's exact
    trigger case, now also proven at the CLI boundary rather than only the module boundary)."""
    apply_target = tmp_path / "apply-target"
    apply_target.mkdir()

    cases: list[tuple[str, dict, Path | None]] = []

    # Case 1: absolute destination (synthetic, guaranteed nonexistent — never a literal system
    # path like /etc/passwd, per 27.1-01's PATH_ESCAPE_DESTINATIONS convention).
    absolute_destination = str(tmp_path / "outside-marker" / "widget.txt")
    cases.append(
        (
            "absolute",
            {
                "target_ref": "unknown",
                "dispositions": [{"destination": absolute_destination, "disposition": "create"}],
                "excluded": [],
            },
            Path(absolute_destination),
        )
    )

    # Case 2: `..`-traversal destination.
    traversal_destination = "../outside-marker/widget.txt"
    cases.append(
        (
            "traversal",
            {
                "target_ref": "unknown",
                "dispositions": [{"destination": traversal_destination, "disposition": "create"}],
                "excluded": [],
            },
            apply_target.parent / "outside-marker" / "widget.txt",
        )
    )

    for case_name, manifest, escape_path in cases:
        batch_id, _ = _seed_batch_with_manifest(task_dir, manifest)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.adoption_apply",
                "apply",
                "--task-dir",
                str(task_dir),
                "--batch-id",
                batch_id,
                "--target",
                str(apply_target),
                "--repo-root",
                str(git_repo),
            ],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1, (
            f"{case_name}: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "Traceback" not in result.stderr, f"{case_name}: unhandled exception leaked"
        assert result.stderr.strip(), f"{case_name}: expected a clean refusal message"
        if escape_path is not None:
            assert not escape_path.exists(), f"{case_name}: hostile destination must not land"

    # Case 3: a symlinked marker-capable destination — the destination string itself
    # ("AGENTS.md") is legitimate; the hostility is the pre-existing symlink at the resolved
    # apply-target path, matching apply.py's own test_marker_merge_refuses_symlink_read fixture.
    victim = tmp_path / "victim.txt"
    victim.write_text("SECRET-ORIGINAL\n", encoding="utf-8")
    agents_md = apply_target / "AGENTS.md"
    agents_md.symlink_to(victim)

    symlink_manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": "AGENTS.md", "disposition": "marker-merge"}],
        "excluded": [],
    }
    batch_id, _ = _seed_batch_with_manifest(task_dir, symlink_manifest)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.adoption_apply",
            "apply",
            "--task-dir",
            str(task_dir),
            "--batch-id",
            batch_id,
            "--target",
            str(apply_target),
            "--repo-root",
            str(git_repo),
        ],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr
    assert "SECRET-ORIGINAL" not in result.stderr
    assert result.stderr.strip()
    assert agents_md.is_symlink(), "the symlink itself must be untouched"
    assert victim.read_text(encoding="utf-8") == "SECRET-ORIGINAL\n"


# --- WR-05 (27.2-01): a directory-shaped destination refuses cleanly at the CLI boundary --------


@pytest.mark.parametrize(
    ("case_name", "destination", "expected_guard"),
    [
        ("root_dot", ".", "names a directory"),
        ("trailing_slash", "newdir/", "names a directory"),
    ],
    ids=["root_dot", "trailing_slash"],
)
def test_cli_apply_refuses_directory_shaped_destination(
    task_dir: Path,
    git_repo: Path,
    tmp_path: Path,
    case_name: str,
    destination: str,
    expected_guard: str,
) -> None:
    """WR-05: `destination: "."` crashes with an unhandled `IsADirectoryError` pre-fix, and
    `destination: "newdir/"` silently creates a FILE named `newdir` pre-fix. Both must exit 1 with
    a clean stderr and no `Traceback`.

    The assertion is on `expected_guard` — the refusal's own identifying text — NOT on the
    destination substring: for the `"."` row, `assert destination in result.stderr` is satisfied by
    any stderr this CLI can emit (the `tools.adoption_apply apply:` prefix alone contains a dot),
    so with the guard reverted that row passed via `ConcurrentDriftError` -> exit 1 for entirely
    the wrong reason. Parametrized rather than looped so a regression names the spelling that
    broke instead of aborting a shared loop.
    """
    apply_target = tmp_path / "dirshaped-target"
    apply_target.mkdir()

    manifest = {
        "target_ref": "unknown",
        "dispositions": [{"destination": destination, "disposition": "create"}],
        "excluded": [],
    }
    batch_id, _ = _seed_batch_with_manifest(task_dir, manifest)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.adoption_apply",
            "apply",
            "--task-dir",
            str(task_dir),
            "--batch-id",
            batch_id,
            "--target",
            str(apply_target),
            "--repo-root",
            str(git_repo),
        ],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, f"{case_name}: stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr, f"{case_name}: unhandled exception leaked"
    assert expected_guard in result.stderr, (
        f"{case_name}: refused by the wrong guard — stderr={result.stderr!r}"
    )
    # No directory-shaped row may leave anything behind in the target tree.
    assert not (apply_target / "newdir").exists(), case_name
    assert list(apply_target.iterdir()) == [], case_name
