"""EMIT-02 determinism — two emits produce byte-identical output (the drift gate depends on it).

Mirrors the tools/docs_sync determinism idiom (Pitfall P12): emit into two independent tmp trees
and assert the per-file sha256 is identical. No ``datetime.now()``/timestamps/floats and a fixed
ordered frontmatter template make re-emit reproducible byte-for-byte, which is exactly what the
CI ``emit-drift`` gate (`git diff --exit-code`) relies on.

RED at Task 1: ``tools.harness_emit.generate`` does not exist yet — import fails.
GREEN at Task 2 once the emit spine lands.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from tools.harness_emit import generate as harness_emit
from tools.harness_emit import project_agent, project_command, project_skill
from tools.harness_lint.caps import EXPECTED_SKILLS

# test_emit_determinism.py -> tests -> harness_emit -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_AGENTS_DIR = _REPO_ROOT / "harness" / "agents"
_COMMANDS_DIR = _REPO_ROOT / "harness" / "commands"
_SKILLS_DIR = _REPO_ROOT / "harness" / "skills"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _emit_into(base: Path) -> list[Path]:
    """Emit the real harness/ agents into an isolated tmp tree (own manifest — no real writes)."""
    return harness_emit.emit(
        opencode_dir=base / ".opencode",
        claude_dir=base / ".claude",
        manifest_path=base / "emit-manifest.json",
        root=base,
    )


def test_emit_twice_byte_identical(tmp_path: Path) -> None:
    """Two emits into separate tmp trees produce identical sha256 per relative file path."""
    first = _emit_into(tmp_path / "a")
    second = _emit_into(tmp_path / "b")

    assert first, "emit wrote nothing"
    digest_1 = {p.relative_to(tmp_path / "a").as_posix(): _sha256(p) for p in first}
    digest_2 = {p.relative_to(tmp_path / "b").as_posix(): _sha256(p) for p in second}

    assert digest_1 == digest_2


def test_projected_tree_matches_committed_snapshot(snapshot) -> None:
    """A committed syrupy .ambr pins the projected agent tree — determinism WITHOUT git diff.

    Mirrors the tools/docs_sync committed-snapshot idiom: renders every agent to BOTH runtime shapes
    and compares to the checked-in .ambr, so a projection/serialization regression is caught in the
    unit suite (not only by the CI re-emit-diff gate).
    """
    parts: list[str] = []
    for name, fm, body in harness_emit.iter_agents(_AGENTS_DIR):
        opencode_md = harness_emit.render_markdown(project_agent.to_opencode(fm), body)
        claude_md = harness_emit.render_markdown(project_agent.to_claude(fm), body)
        parts.append(f"===== opencode-agent/{name} =====\n{opencode_md}")
        parts.append(f"===== claude-agent/{name} =====\n{claude_md}")
    for name, fm, body in harness_emit.iter_commands(_COMMANDS_DIR):
        opencode_md = harness_emit.render_markdown(project_command.to_opencode(fm), body)
        claude_md = harness_emit.render_markdown(project_command.to_claude(fm), body)
        parts.append(f"===== opencode-command/{name} =====\n{opencode_md}")
        parts.append(f"===== claude-command/{name} =====\n{claude_md}")
    for name, fm, body, _ in harness_emit.iter_skills(_SKILLS_DIR):
        skill_md = harness_emit.render_markdown(project_skill.project(fm), body)
        parts.append(f"===== skill/{name} =====\n{skill_md}")
    assert "\n".join(parts) == snapshot


def test_references_byte_copied_to_both_trees(tmp_path: Path) -> None:
    """Each skill's references/** is copied byte-for-byte to BOTH .opencode and .claude trees."""
    written = _emit_into(tmp_path)
    for name, _, _, skill_dir in harness_emit.iter_skills(_SKILLS_DIR):
        for rel in project_skill.iter_reference_files(skill_dir / "references"):
            src_bytes = (skill_dir / "references" / rel).read_bytes()
            opencode_ref = tmp_path / ".opencode" / "skill" / name / "references" / rel
            claude_ref = tmp_path / ".claude" / "skills" / name / "references" / rel
            assert opencode_ref.read_bytes() == src_bytes, f"opencode ref drifted: {name}/{rel}"
            assert claude_ref.read_bytes() == src_bytes, f"claude ref drifted: {name}/{rel}"
            assert opencode_ref in written and claude_ref in written, (
                f"reference file not tracked by the manifest: {name}/{rel}"
            )


def test_emitted_skill_set_matches_expected(tmp_path: Path) -> None:
    """The emitted skill set equals EXPECTED_SKILLS exactly (anti-drift, no sprawl)."""
    written = _emit_into(tmp_path)
    emitted = {p.parent.name for p in written if p.name == "SKILL.md"}
    assert emitted == set(EXPECTED_SKILLS), (
        f"emitted skill set drift: got {sorted(emitted)}, expected {sorted(EXPECTED_SKILLS)}"
    )
