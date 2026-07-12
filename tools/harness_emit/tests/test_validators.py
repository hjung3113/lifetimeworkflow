"""EMIT-02 loud-fail validators — a cap/shape violation aborts writing NOTHING (never truncate).

Each case points the emitter at a tmp SOURCE holding one mutated agent + a tmp target tree, and
asserts ``emit`` raises :class:`HarnessEmitError` and leaves the target tree EMPTY — no partial or
truncated file. This is the T-07-05 (no silent truncation) / T-07-03 (no model leak) guard: the
gate runs on the source AND both projections BEFORE any write.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.harness_emit import generate as harness_emit
from tools.harness_emit.generate import HarnessEmitError


def _run_with_agent(tmp_path: Path, stem: str, agent_md: str) -> list[Path]:
    """Emit a tmp harness holding exactly one agent (``stem``.md) into an isolated tmp target."""
    agents = tmp_path / "harness" / "agents"
    agents.mkdir(parents=True)
    (agents / f"{stem}.md").write_text(agent_md, encoding="utf-8")
    return harness_emit.emit(
        harness_dir=tmp_path / "harness",
        opencode_dir=tmp_path / ".opencode",
        claude_dir=tmp_path / ".claude",
        manifest_path=tmp_path / "emit-manifest.json",
        root=tmp_path,
    )


def _target_is_empty(tmp_path: Path) -> bool:
    """True iff no agent artifact was written to EITHER target tree (nothing truncated/partial)."""
    for tree in (tmp_path / ".opencode", tmp_path / ".claude"):
        if tree.exists() and any(tree.rglob("*.md")):
            return False
    return True


def test_over_cap_description_aborts_writing_nothing(tmp_path: Path) -> None:
    """A >1024-char description FAILS loudly (never sliced to 1024) — target stays empty."""
    huge = "Use when " + ("x" * 1100)  # well over the 1024 hard cap
    agent = (
        "---\n"
        "name: python-engineer\n"
        f"description: {huge}\n"
        "mode: subagent\n"
        "permission:\n"
        "  read: allow\n"
        "tools: Read\n"
        "---\n\nbody\n"
    )
    with pytest.raises(HarnessEmitError):
        _run_with_agent(tmp_path, "python-engineer", agent)
    assert _target_is_empty(tmp_path), "an over-cap description wrote a (truncated?) artifact"


def test_invalid_permission_key_aborts_writing_nothing(tmp_path: Path) -> None:
    """A permission key outside the 15 valid keys FAILS loudly — target stays empty."""
    agent = (
        "---\n"
        "name: python-engineer\n"
        "description: Use when doing python work in the scheduler now\n"
        "mode: subagent\n"
        "permission:\n"
        "  read: allow\n"
        "  bogus_key: allow\n"
        "tools: Read\n"
        "---\n\nbody\n"
    )
    with pytest.raises(HarnessEmitError):
        _run_with_agent(tmp_path, "python-engineer", agent)
    assert _target_is_empty(tmp_path)


def test_read_only_persona_gaining_write_aborts_writing_nothing(tmp_path: Path) -> None:
    """A read-only persona (code-reviewer) mutated to ``edit: allow`` FAILS — target stays empty."""
    agent = (
        "---\n"
        "name: code-reviewer\n"
        "description: Use when reviewing code adversarially in a read-only pass\n"
        "mode: subagent\n"
        "permission:\n"
        "  read: allow\n"
        "  edit: allow\n"
        "tools: Read, Grep, Glob\n"
        "---\n\nbody\n"
    )
    with pytest.raises(HarnessEmitError):
        _run_with_agent(tmp_path, "code-reviewer", agent)
    assert _target_is_empty(tmp_path)
