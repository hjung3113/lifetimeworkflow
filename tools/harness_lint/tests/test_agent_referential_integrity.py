"""Phase-level agent-referential-integrity integration test (T-03-16, cross-file).

Every command's ``agent:`` value must resolve to a real persona file under ``harness/agents/``.
This is the cross-file assertion intentionally moved OUT of the per-plan structural gate
(``test_commands.py``, Task 2): the referenced personas are authored by Plan 03 in the SAME wave 2,
so a file-existence check inside the per-plan command gate would be a false cross-wave gate.

It is therefore a **phase-level / full-suite integration test**: it runs green under the full
``uv run pytest`` suite only AFTER all of wave 2 exists (commands from Plan 04 + personas from
Plan 03). It is NOT wired as a per-plan wave-2 gate — the per-task verify for Task 3 only asserts
this module is syntactically importable (``py_compile``); the resolution assertion itself is what
the phase-level ``uv run pytest`` verifies.

Glob-driven on both sides so migration commands (Plans 06/07) are covered with no edits here.

Parsing is delegated to the shared ``parse_frontmatter`` (Plan 02) — no per-test fence slicing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.harness_lint import parse_frontmatter

# test_agent_referential_integrity.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_COMMANDS_DIR = _REPO_ROOT / "harness" / "commands"
_AGENTS_DIR = _REPO_ROOT / "harness" / "agents"


def _command_files() -> list[Path]:
    return sorted(_COMMANDS_DIR.glob("*.md"))


def _load(path: Path) -> dict:
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm


@pytest.mark.parametrize("path", _command_files(), ids=lambda p: p.stem)
def test_command_agent_resolves_to_real_persona(path: Path) -> None:
    """Each command's ``agent:`` resolves to an existing harness/agents/<agent>.md file.

    Fails loud with the offending command filename and the missing agent path on a dangling
    reference (a command pointing at a persona that was never authored).
    """
    fm = _load(path)
    agent = str(fm.get("agent", "")).strip()
    assert agent, f"{path.name}: command has no 'agent' field to resolve"
    agent_file = _AGENTS_DIR / f"{agent}.md"
    assert agent_file.is_file(), (
        f"{path.name}: dangling agent reference {agent!r} — "
        f"no persona file at {agent_file.relative_to(_REPO_ROOT)}"
    )
