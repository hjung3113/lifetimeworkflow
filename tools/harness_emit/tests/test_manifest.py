"""EMIT-02 ownership manifest — covers only harness paths, prunes stale, never touches gsd-* (D-03).

Emits the real harness agents into an isolated tmp tree and asserts:
  * the manifest lists EXACTLY the emitted agent paths;
  * a stale path from a PRIOR manifest is pruned (deleted) on re-emit;
  * a seeded ``gsd-*`` sibling is NEVER pruned and NEVER enumerated (GSD lane is untouchable).
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


def _listed(manifest_path: Path) -> set[str]:
    return set(json.loads(manifest_path.read_text(encoding="utf-8"))["paths"])


def test_manifest_lists_every_emitted_agent(tmp_path: Path) -> None:
    """The manifest's path set equals exactly the emitted agent files (nothing missing/extra)."""
    written, manifest_path = _emit(tmp_path)
    assert written, "emit produced no agents"
    emitted_rel = {p.relative_to(tmp_path).as_posix() for p in written}
    assert _listed(manifest_path) == emitted_rel


def test_stale_prior_path_is_pruned_on_re_emit(tmp_path: Path) -> None:
    """A harness path listed by the PRIOR manifest but no longer emitted is deleted on re-emit."""
    stale = tmp_path / ".opencode" / "agent" / "removed.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale prior artifact", encoding="utf-8")
    prior = {"tool": "tools.harness_emit", "paths": [".opencode/agent/removed.md"]}

    _, manifest_path = _emit(tmp_path, prior_manifest=prior)

    assert not stale.exists(), "a stale prior-owned path was not pruned"
    assert ".opencode/agent/removed.md" not in _listed(manifest_path)


def test_prune_never_deletes_outside_emit_root(tmp_path: Path) -> None:
    """A prior-manifest entry that traverses outside ``root`` is NOT deleted (confinement guard).

    The prune loop's paths come from the on-disk prior manifest (external data). A tampered
    ``../`` entry must never let ``unlink`` reach beyond the emit root.
    """
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("must survive — outside the emit root", encoding="utf-8")
    emit_root = tmp_path / "repo"
    emit_root.mkdir()
    # A malicious/corrupt prior entry that escapes ``root`` via traversal.
    prior = {"tool": "tools.harness_emit", "paths": ["../outside-secret.txt"]}
    manifest_path = emit_root / "emit-manifest.json"
    manifest_path.write_text(json.dumps(prior), encoding="utf-8")
    harness_emit.emit(
        opencode_dir=emit_root / ".opencode",
        claude_dir=emit_root / ".claude",
        manifest_path=manifest_path,
        root=emit_root,
    )

    assert outside.exists(), "prune deleted a file OUTSIDE the emit root — confinement guard failed"
    assert outside.read_text(encoding="utf-8") == "must survive — outside the emit root"


def test_gsd_sibling_is_never_pruned_or_enumerated(tmp_path: Path) -> None:
    """A seeded gsd-* sibling survives re-emit and never appears in the manifest (GSD lane safe)."""
    gsd = tmp_path / ".claude" / "agents" / "gsd-researcher.md"
    gsd.parent.mkdir(parents=True)
    gsd.write_text("GSD-owned — must never be touched", encoding="utf-8")
    # Even a (wrongly) gsd-listing prior manifest must NOT cause the gsd file to be pruned.
    prior = {"tool": "tools.harness_emit", "paths": [".claude/agents/gsd-researcher.md"]}

    _, manifest_path = _emit(tmp_path, prior_manifest=prior)

    assert gsd.exists(), "a gsd-* sibling was pruned — the GSD lane must be untouchable"
    assert gsd.read_text(encoding="utf-8") == "GSD-owned — must never be touched"
    assert not any("gsd-" in path for path in _listed(manifest_path)), (
        "the manifest enumerated a gsd-* path — it must own only harness artifacts"
    )
