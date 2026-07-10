"""Structural test for the SessionStart hook wiring (HOOK-05, T-02-05, Crit-4).

The injector is the 4th SessionStart slot in .claude/settings.json — it must COEXIST with the 3
existing hooks (gsd-check-update.js, gsd-session-state.sh, tools/bootstrap/install.sh), never
overwrite them (T-02-05 hook-coexistence). These assertions parse the JSON structurally rather
than substring-grepping the whole file, so a reordering or nesting change can't silently pass.
"""

from __future__ import annotations

import json
from pathlib import Path

# The 3 hooks that must survive the 4th-slot append (byte-for-byte coexistence, T-02-05).
EXISTING_COMMANDS = [
    "gsd-check-update.js",
    "gsd-session-state.sh",
    "tools/bootstrap/install.sh",
]
INJECTOR_COMMAND = "memory-inject.sh"


def _session_start_commands(repo_root: Path) -> list[str]:
    """Flatten every command string under hooks.SessionStart[*].hooks[*]."""
    settings = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    groups = settings["hooks"]["SessionStart"]
    commands: list[str] = []
    for group in groups:
        for hook in group["hooks"]:
            commands.append(hook["command"])
    return commands


def test_session_start_has_exactly_four_groups(repo_root: Path) -> None:
    """The injector is added as a 4th group — not merged into an existing one."""
    settings = json.loads((repo_root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    groups = settings["hooks"]["SessionStart"]
    assert len(groups) == 4, (
        f"expected 4 SessionStart groups (3 existing + injector), got {len(groups)}"
    )


def test_three_existing_hooks_survive(repo_root: Path) -> None:
    """All 3 pre-existing SessionStart commands must still be present (coexist, T-02-05)."""
    commands = _session_start_commands(repo_root)
    for needle in EXISTING_COMMANDS:
        assert any(needle in c for c in commands), f"existing SessionStart hook lost: {needle}"


def test_injector_slot_references_memory_inject(repo_root: Path) -> None:
    """The 4th slot wires the memory-inject.sh injector."""
    commands = _session_start_commands(repo_root)
    assert any(INJECTOR_COMMAND in c for c in commands), (
        "injector hook (memory-inject.sh) not wired"
    )


def test_injector_hook_script_exists(repo_root: Path) -> None:
    """The wired script actually exists on disk."""
    assert (repo_root / ".claude" / "hooks" / "memory-inject.sh").is_file()


def test_opencode_stub_authored_and_deferred(repo_root: Path) -> None:
    """The opencode adapter stub is authored, references the SAME contract, and is marked
    deferred."""
    stub = (repo_root / "harness" / "plugins" / "session-inject.ts").read_text(encoding="utf-8")
    assert "tools.memory_regen.inject" in stub, (
        "opencode stub must consume the SAME assembler (D-01)"
    )
    lowered = stub.lower()
    assert "deferred" in lowered and "resume" in lowered, "stub must carry a deferred RESUME note"
