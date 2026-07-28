"""Structural layout test for the two-plane memory skeleton + resolved toolchain (Crit-1,
MEM-01/02).

Assertions only touch *structure*, never the content of a gitignored path, and never
`git diff` on `.memory/derived/` (Pitfall 2: a gitignored path never shows in `git diff`,
so such a test is a silent no-op). The gitignore boundary is probed with `git check-ignore`
instead.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# The three constitution-plane members that .memory/README.md must name (MEM-01).
# ADR-0001's fourth member, root `golden/`, is superseded by ADR-0012 clause (d).
CONSTITUTION_MEMBERS = ["contracts/", "docs/adr/", "glossary"]


def _is_git_ignored(repo_root: Path, rel_path: str) -> bool:
    """True iff `git check-ignore` matches (rc 0) — i.e. the path is gitignored."""
    proc = subprocess.run(
        ["git", "check-ignore", rel_path],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    # rc 0 => ignored (match printed); rc 1 => NOT ignored; rc >1 => error.
    assert proc.returncode in (0, 1), f"git check-ignore errored on {rel_path}: {proc.stderr}"
    return proc.returncode == 0


def test_derived_plane_is_gitignored(repo_root: Path) -> None:
    """`.memory/derived/` is regenerated every session → must be gitignored (D-03/D-04)."""
    assert _is_git_ignored(repo_root, ".memory/derived/repo-map.md"), (
        ".memory/derived/ must be gitignored (add `.memory/derived/` to .gitignore)"
    )


def test_state_plane_is_tracked(repo_root: Path) -> None:
    """`.memory/state/` holds small volatile state that survives the container → must be tracked."""
    assert not _is_git_ignored(repo_root, ".memory/state/activeContext.md"), (
        ".memory/state/ must stay TRACKED (do not gitignore it)"
    )


def test_readme_carries_derived_marker(repo_root: Path) -> None:
    """The committed README must carry the DERIVED marker so the boundary is explicit (D-04)."""
    readme = (repo_root / ".memory" / "README.md").read_text(encoding="utf-8")
    assert "DERIVED" in readme


def test_readme_names_all_constitution_members(repo_root: Path) -> None:
    """README must name all three constitution-plane members (MEM-01 declaration)."""
    readme = (repo_root / ".memory" / "README.md").read_text(encoding="utf-8")
    missing = [m for m in CONSTITUTION_MEMBERS if m not in readme]
    assert not missing, f".memory/README.md does not name constitution members: {missing}"


def test_state_stubs_carry_no_secrets(repo_root: Path) -> None:
    """T-02-01: committed state must not carry secret *values* (banners warning about them
    are OK)."""
    state_dir = repo_root / ".memory" / "state"
    for stub in state_dir.glob("*.md"):
        text = stub.read_text(encoding="utf-8").lower()
        # A crude value-shape check: no `key = <value>` / `key: <value>` secret assignments.
        for marker in ("password:", "password =", "api_key:", "api_key =", "secret=", "token="):
            assert marker not in text, f"possible secret value in {stub}: {marker!r}"


@pytest.mark.parametrize(
    "module",
    ["tree_sitter", "tree_sitter_python", "tree_sitter_c_sharp", "tree_sitter_bash", "networkx"],
)
def test_pinned_toolchain_imports(module: str) -> None:
    """The five pinned deps resolve in the workspace env (so Wave-2 plans never touch uv.lock)."""
    __import__(module)
