"""LANE-04 gate: the committed registry.lock still describes the real skill surface.

The `registry-lock` CI job runs the same comparison, but a gate that only exists in CI is a gate you
discover at push time. Running it inside `uv run pytest` too mirrors the belt-and-braces the
discipline wiring lint already has: caught locally, and caught again at the fan-in.

It is a DISTINCT concern from `emit-drift`, which re-derives its expectation from the same source it
checks and is therefore blind to a change in what that source declares. See
tools/skill_registry/registry.py for the three escapes.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.skill_registry.registry import LOCK_PATH, build_registry, diff_lock, dumps, load_lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SKILLS_DIR = _REPO_ROOT / "harness" / "skills"


def test_the_committed_lock_matches_the_tree() -> None:
    differences = diff_lock(load_lock(), build_registry())
    assert not differences, (
        "the skill surface has drifted from harness/skills/registry.lock:\n  "
        + "\n  ".join(differences)
        + "\n\nre-declare it with: uv run python -m tools.skill_registry --write"
    )


def test_the_lock_is_byte_identical_to_a_fresh_serialization() -> None:
    """Determinism: a rewrite on an unchanged tree must produce the committed bytes exactly."""
    assert LOCK_PATH.read_text(encoding="utf-8") == dumps(build_registry())


def test_every_skill_directory_is_locked() -> None:
    on_disk = {path.name for path in _SKILLS_DIR.iterdir() if path.is_dir()}
    assert set(load_lock()["skills"]) == on_disk


def test_a_doctored_lock_fails_the_comparison(tmp_path: Path) -> None:
    """MUTATION on a COPY: neutralize one digest and the comparison flips red."""
    doctored = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    doctored["skills"]["gate-model"]["description_sha256"] = "0" * 64
    path = tmp_path / "registry.lock"
    path.write_text(json.dumps(doctored), encoding="utf-8")
    assert diff_lock(load_lock(path), build_registry()) == [
        "gate-model: description changed (it is the skill's routing trigger)"
    ]
