"""EMIT-02 command coexistence — the harness command surface must never collide with GSD (T-07-02).

The emitter writes its 17 harness commands as TOP-LEVEL ``.claude/commands/*.md`` (Claude) and
``.opencode/command/*.md`` (opencode). GSD owns the ``.claude/commands/gsd/**`` subtree; the two
sets must be provably DISJOINT — a harness command must never land under ``gsd/`` and a seeded
``gsd/`` fixture must survive an emit byte-for-byte and never be enumerated by the ownership
manifest.

Emits the REAL ``harness/commands`` into an isolated tmp tree (mirrors test_manifest.py) so the
assertions run without touching the real repo trees.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.harness_emit import generate as harness_emit


def _emit(tmp_path: Path, prior_manifest: dict | None = None) -> tuple[list[Path], Path]:
    manifest_path = tmp_path / "emit-manifest.json"
    if prior_manifest is not None:
        manifest_path.write_text(json.dumps(prior_manifest), encoding="utf-8")
    written = harness_emit.emit(
        opencode_dir=tmp_path / ".opencode",
        claude_dir=tmp_path / ".claude",
        manifest_path=manifest_path,
        root=tmp_path,
    )
    return written, manifest_path


def _claude_commands(tmp_path: Path, written: list[Path]) -> list[Path]:
    commands_dir = tmp_path / ".claude" / "commands"
    return [p for p in written if commands_dir in p.parents and p.suffix == ".md"]


def test_all_17_commands_emit_to_both_trees(tmp_path: Path) -> None:
    """17 commands land in .opencode/command/*.md AND .claude/commands/*.md (top-level)."""
    written, _ = _emit(tmp_path)
    opencode_cmds = [
        p
        for p in written
        if (tmp_path / ".opencode" / "command") in p.parents and p.suffix == ".md"
    ]
    claude_cmds = _claude_commands(tmp_path, written)
    assert len(opencode_cmds) == 17, f"expected 17 opencode commands, got {len(opencode_cmds)}"
    assert len(claude_cmds) == 17, f"expected 17 Claude commands, got {len(claude_cmds)}"


def test_harness_commands_are_top_level_never_under_gsd(tmp_path: Path) -> None:
    """Every emitted Claude command is a top-level *.md — none nested under a gsd/ subtree."""
    written, _ = _emit(tmp_path)
    claude_cmds = _claude_commands(tmp_path, written)
    assert claude_cmds, "no Claude commands were emitted"
    commands_dir = tmp_path / ".claude" / "commands"
    for path in claude_cmds:
        assert path.parent == commands_dir, f"harness command is not top-level: {path}"
        assert "gsd" not in path.relative_to(tmp_path).parts, f"harness command under gsd/: {path}"


def test_seeded_gsd_command_survives_byte_unchanged_and_unlisted(tmp_path: Path) -> None:
    """A seeded .claude/commands/gsd/ fixture is byte-unchanged and absent from the manifest."""
    gsd_cmd = tmp_path / ".claude" / "commands" / "gsd" / "plan.md"
    gsd_cmd.parent.mkdir(parents=True)
    original = "GSD-owned command — must never be touched by the harness emitter\n"
    gsd_cmd.write_text(original, encoding="utf-8")
    # Even a (wrongly) gsd-listing prior manifest must not cause a prune of the gsd fixture.
    prior = {"tool": "tools.harness_emit", "paths": [".claude/commands/gsd/plan.md"]}

    _, manifest_path = _emit(tmp_path, prior_manifest=prior)

    assert gsd_cmd.exists(), "the seeded gsd/ command was deleted — GSD lane must be untouchable"
    assert gsd_cmd.read_text(encoding="utf-8") == original, "the gsd/ command was mutated"
    listed = set(json.loads(manifest_path.read_text(encoding="utf-8"))["paths"])
    assert not any("commands/gsd/" in p for p in listed), (
        "the manifest enumerated a gsd/ command — the harness owns only top-level commands"
    )
