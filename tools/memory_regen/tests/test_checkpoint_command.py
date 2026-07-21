"""Structural regression tests for /checkpoint's write-half mandates (MEM2-05, Phase 13-01).

`13-VALIDATION.md` documents these as bare ``grep -q`` "Automated Command" cells rather than
pytest — which means nothing in the ``uv run pytest tools/memory_regen -q`` sampling loop protects
them from silent regression (e.g. an edit to `checkpoint.md` that drops the stamp mandate would
never fail CI). This file wraps those same assertions into the pytest suite so they run on every
sampled commit, matching the structural-pytest convention already used in `test_hook_wiring.py`
and `test_layout.py` (real repo files, no fixtures — these are prose/state-plane contracts, not
pure functions).
"""

from __future__ import annotations

import re
from pathlib import Path


def _checkpoint_text(repo_root: Path) -> str:
    return (repo_root / "harness" / "commands" / "checkpoint.md").read_text(encoding="utf-8")


def test_checkpoint_mandates_the_updated_stamp(repo_root: Path) -> None:
    """/checkpoint must instruct writing the `updated:` frontmatter stamp, quoted, every time."""
    text = _checkpoint_text(repo_root)
    assert "updated:" in text
    assert re.search(r"quote|quoted", text, flags=re.IGNORECASE)
    assert "activeContext.md" in text and "progress.md" in text


def test_checkpoint_mandates_tight_bounded_progress(repo_root: Path) -> None:
    """/checkpoint must mandate the last-N-done + remaining shape and forbid an accumulating log."""
    text = _checkpoint_text(repo_root)
    assert re.search(r"last .*done|no.*done-log|git holds", text, flags=re.IGNORECASE)
    assert "git holds the full completed history" in text


def test_checkpoint_adds_no_wallclock(repo_root: Path) -> None:
    """/checkpoint stays prose-only — the orchestrator supplies the date, no `$(date)` shell line
    (D-11/Q6): keeps 13-02's static no-wall-clock gate meaningful."""
    text = _checkpoint_text(repo_root)
    assert "$(date" not in text
    assert "`date" not in text


def test_state_files_carry_the_updated_stamp(repo_root: Path) -> None:
    """Both committed state files must carry the `updated:` frontmatter key that /checkpoint
    mandates and that `_active_context_pointer` reads verbatim (SC3 write half, plan 13-01)."""
    state_dir = repo_root / ".memory" / "state"
    for name in ("activeContext.md", "progress.md"):
        text = (state_dir / name).read_text(encoding="utf-8")
        assert re.search(r"^updated:", text, flags=re.MULTILINE), (
            f"{name} is missing an `updated:` frontmatter stamp"
        )
