"""Shared fixtures for the docs_guard suite.

The ``docs_repo`` fixture is a REAL ``git init`` tmp tree, not a mock: the guard's
disposition-coherence check reads the previous committed ledger via ``git show HEAD:./<path>``,
and a mocked git proves nothing about that plumbing. Same posture as
``tools/harness_lint/tests/test_ci_stale_derived.py``'s negative controls.

Hermetic by construction: fixed argv + ``shell=False``, and identity is supplied per-invocation
via ``-c user.email=... -c user.name=...`` so no global/user git config is read or written.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_IDENTITY = (
    "-c",
    "user.email=docs-guard@example.invalid",
    "-c",
    "user.name=docs-guard",
    "-c",
    "commit.gpgsign=false",
)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git in ``repo`` with a per-invocation identity — never a global config write."""
    return subprocess.run(
        ["git", *_IDENTITY, *args],
        cwd=repo,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )


@pytest.fixture
def docs_repo(tmp_path: Path) -> Path:
    """A tmp git repo with one commit and a small seed tree; returns the repo root.

    Seed tree (enough for the ledger/git-history tests to commit, mutate, and diff for real)::

        docs/a.md
        docs/nested/b.md
        src/one.py

    Skips — never silently passes — when the ``git`` binary is unavailable.
    """
    if shutil.which("git") is None:
        pytest.skip("git binary unavailable — the docs_repo fixture requires real git plumbing")

    repo = tmp_path / "repo"
    (repo / "docs" / "nested").mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "docs" / "a.md").write_text("alpha\n", encoding="utf-8")
    (repo / "docs" / "nested" / "b.md").write_text("bravo\n", encoding="utf-8")
    (repo / "src" / "one.py").write_text("ONE = 1\n", encoding="utf-8")

    assert git(repo, "init", "--initial-branch=main").returncode == 0
    assert git(repo, "add", "-A").returncode == 0
    seed = git(repo, "commit", "-m", "seed")
    assert seed.returncode == 0, seed.stderr

    return repo
