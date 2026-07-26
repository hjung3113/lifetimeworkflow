"""EMIT-02 command coexistence — the harness command surface must never collide with GSD (T-07-02).

The emitter writes its 20 harness commands as TOP-LEVEL ``.claude/commands/*.md`` (Claude) and
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
from tools.harness_emit.merge import _GUARD_PREFIX


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


def test_all_26_commands_emit_to_both_trees(tmp_path: Path) -> None:
    """26 commands land in .opencode/command/*.md AND .claude/commands/*.md (top-level).

    Phase 9 adds /refresh-memory (the curator's local derived-freshness macro), taking the count
    from 17 → 18; Phase 10 adds /fan-out-synthesize (the context-economy fan-out entry point),
    taking it 18 → 19; Phase 14 adds /agree (the agreements write path, MEM2-04), taking it 19 → 20;
    Phase 19 adds /intake (the deterministic task-control entry point), taking it 20 → 21;
    Phase 20 adds /phase-gate, taking it 21 → 22; Phase 22 adds /handoff, taking it 22 → 23.
    Phase 27 adds `/adopt` (the brownfield-adoption composition entry point), taking it 23 → 24.
    Phase 29 adds `/docs-update` (the bounded human-doc review loop, DOCSUP-06), taking it 24 → 25.
    Phase 36 adds `/discipline` (the read-only lane-discipline report, LANE-01), taking it 25 → 26.
    Phase 41 deletes `/docs-update` (the docs-review plane removal, CER-05), taking it back 26 → 25.

    This count tracks the runtime-neutral SOURCE (``harness/commands/*.md``), NOT the committed
    ``.opencode/`` / ``.claude/`` trees: ``_emit`` projects into ``tmp_path``. So authoring a new
    source command bumps this count immediately — whether or not the real trees are re-emitted.
    Phase 14 is deliberately source-only (its 14-CONTEXT D-10 originally assumed the opposite and
    was wrong); the committed trees still hold 19 and Phase 15 (MEM2-06) owns re-emitting them.
    That deferral is tracked by ``test_projected_tree_matches_committed_snapshot``, which is a
    DIFFERENT test and stays red on purpose until Phase 15. Do not "fix" it here.
    """
    written, _ = _emit(tmp_path)
    opencode_cmds = [
        p
        for p in written
        if (tmp_path / ".opencode" / "command") in p.parents and p.suffix == ".md"
    ]
    claude_cmds = _claude_commands(tmp_path, written)
    assert len(opencode_cmds) == 25, f"expected 25 opencode commands, got {len(opencode_cmds)}"
    assert len(claude_cmds) == 25, f"expected 25 Claude commands, got {len(claude_cmds)}"


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


# --- settings.json / GSD-subtree coexistence (Regime B-json, T-07-02 / T-07-10) ------------------

# The GSD-owned .claude/ files the emitter must NEVER read, write, or prune. Seeded into the tmp
# tree and asserted byte-unchanged after a full emit (and absent from the ownership manifest).
_GSD_SEEDS = {
    ".claude/get-shit-done/config.json": '{"gsd": "owned — never touched"}\n',
    ".claude/hooks/gsd-session-state.sh": "#!/usr/bin/env bash\necho gsd-owned\n",
    ".claude/gsd-state.json": '{"phase": "gsd-owned"}\n',
    ".claude/package.json": '{"name": "gsd-package"}\n',
    ".claude/settings.local.json": '{"local": "gsd-owned"}\n',
    ".claude/agents/gsd-planner.md": "GSD-owned agent — never emitted over\n",
}

# A minimal but structurally-real settings.json: 4 SessionStart groups (3 GSD + injector) plus the
# already-wired harness hook groups — exactly the shape merge_settings must reproduce in place.
_SEED_SETTINGS = {
    "hooks": {
        "SessionStart": [
            {"hooks": [{"type": "command", "command": "node .claude/hooks/gsd-check-update.js"}]},
            {"hooks": [{"type": "command", "command": "bash .claude/hooks/gsd-session-state.sh"}]},
            {"hooks": [{"type": "command", "command": "bash tools/bootstrap/install.sh"}]},
            {"hooks": [{"type": "command", "command": "bash .claude/hooks/memory-inject.sh"}]},
        ],
        "PostToolUse": [
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": "bash .claude/hooks/gsd-phase-boundary.sh",
                        "timeout": 5,
                    }
                ],
            },
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": _GUARD_PREFIX + "uv run python -m tools.hooks.format_on_write",
                        "timeout": 30,
                    }
                ],
            },
        ],
        "PreToolUse": [
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": _GUARD_PREFIX + "uv run python -m tools.hooks.contract_guard",
                        "timeout": 10,
                    }
                ],
            },
            {
                "matcher": "Read|Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": _GUARD_PREFIX + "uv run python -m tools.hooks.secret_scan",
                        "timeout": 10,
                    }
                ],
            },
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": _GUARD_PREFIX
                        + "uv run python -m tools.hooks.commit_gate --from-hook",
                        "timeout": 120,
                    }
                ],
            },
            {
                "matcher": "Write|Edit|Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": _GUARD_PREFIX + "uv run python -m tools.hooks.resume_gate",
                        "timeout": 15,
                    }
                ],
            },
        ],
    }
}


def _seed_gsd_tree(tmp_path: Path) -> dict[str, str]:
    """Write the GSD-owned fixtures + a real-shaped settings.json; return their original bytes."""
    originals: dict[str, str] = {}
    for rel, content in _GSD_SEEDS.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        originals[rel] = content
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(_SEED_SETTINGS, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return originals


def test_gsd_owned_claude_files_untouched_and_unlisted(tmp_path: Path) -> None:
    """Every seeded GSD-owned .claude/ file is byte-unchanged after emit and absent from manifest."""
    originals = _seed_gsd_tree(tmp_path)

    _, manifest_path = _emit(tmp_path)

    for rel, original in originals.items():
        path = tmp_path / rel
        assert path.exists(), f"GSD-owned file was deleted: {rel}"
        assert path.read_text(encoding="utf-8") == original, f"GSD-owned file was mutated: {rel}"
    listed = set(json.loads(manifest_path.read_text(encoding="utf-8"))["paths"])
    for rel in originals:
        assert rel not in listed, f"manifest enumerated a GSD-owned file: {rel}"
    # settings.json is Regime B (merge, not own) — must never be manifest-listed either.
    assert not any("settings.json" in p for p in listed), (
        "settings.json is a Regime-B merge target — it must not be in the ownership manifest"
    )


def test_seeded_settings_json_reproduced_byte_for_byte(tmp_path: Path) -> None:
    """A full emit over a seeded settings.json reproduces it byte-for-byte (idempotent coexist)."""
    _seed_gsd_tree(tmp_path)
    settings = tmp_path / ".claude" / "settings.json"
    before = settings.read_text(encoding="utf-8")

    _emit(tmp_path)

    after = settings.read_text(encoding="utf-8")
    assert after == before, "the emit mutated settings.json — merge must reproduce it byte-for-byte"
    parsed = json.loads(after)
    assert len(parsed["hooks"]["SessionStart"]) == 4, "SessionStart group count drifted from 4"
