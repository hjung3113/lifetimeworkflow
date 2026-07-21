"""LANE-04: the skill surface cannot drift from its declaration.

The three mutation proofs at the bottom are the reason this gate exists at all: each is a change
that `emit-drift` re-emits GREEN, because it re-derives its expectation from the same source it is
checking. If any of them stopped failing here, the lock would be decorative.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.skill_registry.__main__ import EXIT_DRIFT, EXIT_MALFORMED, EXIT_OK, main
from tools.skill_registry.registry import (
    LOCK_PATH,
    SKILLS_DIR,
    SkillRegistryError,
    build_registry,
    diff_lock,
    dumps,
    load_lock,
    write_lock,
)

_SKILL = """---
name: {name}
description: {description}
---

# {name}

Body.
"""

_DECLARATIONS = """version = 1

[discipline.demo]
skill = "alpha"
owed_by_phase = "EXECUTE"
outputs_required = 1
"""


@pytest.fixture
def tree(tmp_path: Path) -> dict:
    """A miniature skill tree with its own manifest and declarations — never the real files."""
    skills = tmp_path / "skills"
    for name in ("alpha", "beta"):
        directory = skills / name
        directory.mkdir(parents=True)
        (directory / "SKILL.md").write_text(
            _SKILL.format(name=name, description=f"do {name} things"), encoding="utf-8"
        )
    (skills / "alpha" / "references").mkdir()
    (skills / "alpha" / "references" / "note.md").write_text("detail\n", encoding="utf-8")

    manifest = tmp_path / "emit-manifest.json"
    paths = []
    for name in ("alpha", "beta"):
        for lane in (".claude/skills", ".opencode/skill"):
            paths.append(f"{lane}/{name}/SKILL.md")
    paths += [
        ".claude/skills/alpha/references/note.md",
        ".opencode/skill/alpha/references/note.md",
        ".claude/commands/unrelated.md",
    ]
    manifest.write_text(json.dumps({"paths": sorted(paths)}), encoding="utf-8")

    declarations = tmp_path / "disciplines.toml"
    declarations.write_text(_DECLARATIONS, encoding="utf-8")
    return {"skills": skills, "manifest": manifest, "declarations": declarations, "root": tmp_path}


def _build(tree: dict) -> dict:
    return build_registry(
        tree["skills"], manifest_path=tree["manifest"], declarations_path=tree["declarations"]
    )


# ── shape ─────────────────────────────────────────────────────────────────────────────────────


def test_the_registry_records_every_declared_facet(tree: dict) -> None:
    registry = _build(tree)
    assert set(registry["skills"]) == {"alpha", "beta"}
    alpha = registry["skills"]["alpha"]
    assert set(alpha) == {"description_sha256", "sources", "emitted", "disciplines"}
    assert set(alpha["sources"]) == {"SKILL.md", "references/note.md"}
    assert alpha["disciplines"] == ["demo"]
    assert registry["skills"]["beta"]["disciplines"] == []


def test_emitted_paths_cover_both_runtime_lanes_and_nothing_else(tree: dict) -> None:
    """The declared PAIR catches a half-emitted surface; unrelated paths must not leak in."""
    emitted = _build(tree)["skills"]["alpha"]["emitted"]
    assert emitted == [
        ".claude/skills/alpha/SKILL.md",
        ".claude/skills/alpha/references/note.md",
        ".opencode/skill/alpha/SKILL.md",
        ".opencode/skill/alpha/references/note.md",
    ]
    assert not any("commands" in path for path in emitted)


def test_serialization_is_deterministic(tree: dict) -> None:
    first, second = dumps(_build(tree)), dumps(_build(tree))
    assert first == second
    assert first.endswith("\n")


def test_a_skill_directory_without_a_skill_md_is_refused(tree: dict) -> None:
    (tree["skills"] / "gamma").mkdir()
    with pytest.raises(SkillRegistryError, match="no SKILL.md"):
        _build(tree)


def test_a_skill_without_a_description_is_refused(tree: dict) -> None:
    (tree["skills"] / "beta" / "SKILL.md").write_text(
        "---\nname: beta\n---\n\n# beta\n", encoding="utf-8"
    )
    with pytest.raises(SkillRegistryError, match="no description"):
        _build(tree)


def test_a_malformed_lock_is_refused_not_ignored(tmp_path: Path) -> None:
    path = tmp_path / "registry.lock"
    path.write_text('{"version": 99, "skills": {}}', encoding="utf-8")
    with pytest.raises(SkillRegistryError, match="version"):
        load_lock(path)
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SkillRegistryError, match="invalid registry lock"):
        load_lock(path)
    with pytest.raises(SkillRegistryError, match="no registry lock"):
        load_lock(tmp_path / "absent.lock")


# ── mutation proofs: the three escapes emit-drift cannot see ──────────────────────────────────


def test_a_description_rewrite_is_caught(tree: dict) -> None:
    """ESCAPE 1: the routing trigger changes; a re-emit propagates it and emit-drift stays green."""
    locked = _build(tree)
    (tree["skills"] / "alpha" / "SKILL.md").write_text(
        _SKILL.format(name="alpha", description="something else entirely"), encoding="utf-8"
    )
    differences = diff_lock(locked, _build(tree))
    assert "alpha: description changed (it is the skill's routing trigger)" in differences


def test_a_new_reference_file_is_caught(tree: dict) -> None:
    """ESCAPE 2: the emitter discovers references/ by glob, so a new file needs no declaration."""
    locked = _build(tree)
    (tree["skills"] / "alpha" / "references" / "extra.md").write_text("more\n", encoding="utf-8")
    assert "alpha: source file added: references/extra.md" in diff_lock(locked, _build(tree))


def test_a_half_emitted_surface_is_caught(tree: dict) -> None:
    """ESCAPE 3: a skill that reaches one runtime and not the other is a consistent re-emit."""
    locked = _build(tree)
    manifest = json.loads(tree["manifest"].read_text())
    manifest["paths"] = [p for p in manifest["paths"] if p != ".opencode/skill/beta/SKILL.md"]
    tree["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    differences = diff_lock(locked, _build(tree))
    assert any(item.startswith("beta: emitted path set changed") for item in differences)


def test_a_repointed_discipline_is_caught(tree: dict) -> None:
    """Phase 36's deferred item: a lane requirement silently routed to a different procedure."""
    locked = _build(tree)
    tree["declarations"].write_text(_DECLARATIONS.replace('"alpha"', '"beta"'), encoding="utf-8")
    differences = diff_lock(locked, _build(tree))
    assert any("alpha: the disciplines naming this skill changed" in item for item in differences)
    assert any("beta: the disciplines naming this skill changed" in item for item in differences)


def test_an_added_and_a_removed_skill_are_both_caught(tree: dict) -> None:
    locked = _build(tree)
    (tree["skills"] / "gamma").mkdir()
    (tree["skills"] / "gamma" / "SKILL.md").write_text(
        _SKILL.format(name="gamma", description="new"), encoding="utf-8"
    )
    assert "gamma: present in the tree, absent from the lock" in diff_lock(locked, _build(tree))

    added = _build(tree)
    (tree["skills"] / "gamma" / "SKILL.md").unlink()
    (tree["skills"] / "gamma").rmdir()
    assert "gamma: locked but no longer in the tree" in diff_lock(added, _build(tree))


def test_an_unchanged_tree_reports_no_drift(tree: dict) -> None:
    """The positive control: without it, a diff function that returns everything looks correct."""
    assert diff_lock(_build(tree), _build(tree)) == []


def test_write_lock_round_trips(tree: dict) -> None:
    path = tree["root"] / "registry.lock"
    write_lock(_build(tree), path)
    assert diff_lock(load_lock(path), _build(tree)) == []


# ── the shipped lock + the CLI ────────────────────────────────────────────────────────────────


def test_the_committed_lock_matches_the_real_tree() -> None:
    assert LOCK_PATH.is_file(), "harness/skills/registry.lock is not committed"
    assert diff_lock(load_lock(), build_registry()) == []
    assert set(load_lock()["skills"]) == {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}


def test_cli_check_passes_on_the_committed_lock(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == EXIT_OK
    assert "skill-registry: OK" in capsys.readouterr().out


def test_cli_check_fails_and_names_the_fix(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """THE DEMONSTRATION: a drifted surface exits 1 and says exactly how to re-declare it."""
    import tools.skill_registry.__main__ as cli

    drifted = build_registry()
    drifted["skills"]["clarify"]["description_sha256"] = "0" * 64
    monkeypatch.setattr(cli, "build_registry", lambda: drifted)
    assert main([]) == EXIT_DRIFT
    err = capsys.readouterr().err
    assert "DRIFTED" in err
    assert "clarify: description changed" in err
    assert "uv run python -m tools.skill_registry --write" in err


def test_cli_reports_an_absent_lock_distinctly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import tools.skill_registry.__main__ as cli

    def _absent() -> dict:
        raise SkillRegistryError("no registry lock at nowhere")

    monkeypatch.setattr(cli, "load_lock", _absent)
    assert main([]) == EXIT_MALFORMED
    assert "no registry lock" in capsys.readouterr().err


def test_cli_write_is_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Writing the lock on an unchanged tree must be a no-op — the determinism proof."""
    before = LOCK_PATH.read_bytes()
    assert main(["--write"]) == EXIT_OK
    assert LOCK_PATH.read_bytes() == before
    assert "unchanged" in capsys.readouterr().out


def test_cli_accepts_the_explicit_check_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """The CI step spells the assertion out; --check must mean the same as the bare default."""
    assert main(["--check"]) == EXIT_OK
    assert "skill-registry: OK" in capsys.readouterr().out


def test_cli_refuses_write_and_check_together() -> None:
    with pytest.raises(SystemExit):
        main(["--write", "--check"])
