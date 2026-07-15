"""EMIT-02 agent frontmatter projection — the sole specialization point (D-04).

An authored agent frontmatter block is DUAL-representation (it carries BOTH runtimes). These tests
pin that the emitter PROJECTS it correctly into each runtime's shape:
  * opencode keeps ``name``/``description``/``mode``/``permission`` and drops Claude-only ``tools``;
  * Claude keeps ``name``/``description``/``tools`` and drops ``mode`` + the ``permission`` block;
  * the read-only invariant (code-reviewer / explorer) survives BOTH projections.

RED at Task 1: ``tools.harness_emit.project_agent`` does not exist yet — collection/import fails.
GREEN at Task 2 once the projector lands.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_emit import project_agent, project_command, project_skill
from tools.harness_lint import parse_frontmatter
from tools.harness_lint.caps import is_read_only

# test_mapping.py -> tests -> harness_emit -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_AGENTS_DIR = _REPO_ROOT / "harness" / "agents"
_COMMANDS_DIR = _REPO_ROOT / "harness" / "commands"
_SKILLS_DIR = _REPO_ROOT / "harness" / "skills"


def _load(name: str) -> tuple[dict, str]:
    return parse_frontmatter((_AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8"))


def _load_command(name: str) -> tuple[dict, str]:
    return parse_frontmatter((_COMMANDS_DIR / f"{name}.md").read_text(encoding="utf-8"))


def _load_skill(name: str) -> tuple[dict, str]:
    return parse_frontmatter((_SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8"))


def test_opencode_agent_shape() -> None:
    """opencode projection keeps name/description/mode/permission; NO Claude-only ``tools``."""
    fm, _ = _load("python-engineer")
    proj = project_agent.to_opencode(fm)
    assert proj["name"] == "python-engineer"
    assert str(proj["description"]).strip()
    assert proj["mode"] == "subagent"
    assert isinstance(proj["permission"], dict) and proj["permission"]
    assert "tools" not in proj, "opencode projection leaked the Claude-only 'tools' key"


def test_claude_agent_shape() -> None:
    """Claude projection keeps name/description/tools; drops ``permission`` block AND ``mode``."""
    fm, _ = _load("python-engineer")
    proj = project_agent.to_claude(fm)
    assert proj["name"] == "python-engineer"
    assert str(proj["description"]).strip()
    assert str(proj["tools"]).strip()
    assert "permission" not in proj, "Claude projection leaked the opencode 'permission' block"
    assert "mode" not in proj, "Claude projection leaked the opencode 'mode' key"


def test_read_only_invariant_both() -> None:
    """code-reviewer projects read-only in BOTH targets (is_read_only true on each projection)."""
    fm, _ = _load("code-reviewer")
    assert is_read_only(project_agent.to_opencode(fm)), "read-only broke in opencode projection"
    assert is_read_only(project_agent.to_claude(fm)), "read-only broke in Claude projection"


def test_opencode_command_shape() -> None:
    """opencode command projection keeps description/agent/subtask verbatim."""
    fm, _ = _load_command("build")
    proj = project_command.to_opencode(fm)
    assert str(proj["description"]).strip()
    assert proj["agent"] == "orchestrator"
    assert proj["subtask"] is True


def test_claude_command_shape() -> None:
    """Claude command projection keeps description only; drops agent + subtask (no equivalent)."""
    fm, _ = _load_command("build")
    proj = project_command.to_claude(fm)
    assert str(proj["description"]).strip()
    assert "agent" not in proj, "Claude command projection leaked the opencode-only 'agent' key"
    assert "subtask" not in proj, "Claude command projection leaked the opencode-only 'subtask' key"


def test_claude_command_shape_when_subtask_absent() -> None:
    """A command without ``subtask`` (e.g. /adr) still projects to a bare description for Claude."""
    fm, _ = _load_command("adr")
    proj = project_command.to_claude(fm)
    assert set(proj) == {"description"}, f"Claude command projection has stray keys: {sorted(proj)}"


def test_skill_projection_is_identical_for_both_runtimes() -> None:
    """A skill keeps name+description identically for BOTH runtimes (divergence = None, D-04)."""
    fm, _ = _load_skill("data-contracts")
    opencode_proj = project_skill.to_opencode(fm)
    claude_proj = project_skill.to_claude(fm)
    assert opencode_proj == claude_proj, "skill projection must be identical across runtimes"
    assert opencode_proj["name"] == "data-contracts"
    assert str(opencode_proj["description"]).strip()
    assert set(opencode_proj) == {"name", "description"}, "skill projection has stray keys"
