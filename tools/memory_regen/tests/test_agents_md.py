"""Structural test for the nearest-wins AGENTS.md rules layer (Crit-3, RULES-01/02, P11).

Asserts:
- all three AGENTS.md exist (root + per-package Python + .NET);
- the root carries the monorepo map, a golden-path command, contract-first, and lazy-load;
- each PER-PACKAGE file RESTATES the non-negotiables (contract-first + constitution-gated +
  §4-5 boundary invariants) rather than relying on inheritance — the P11 backstop
  (Codex-style runtimes replace nested AGENTS.md instead of concatenating);
- CLAUDE.md carries the AGENTS.md pointer without our touching the GSD-managed profile block.

These are content-substring checks on *committed* authoring-plane files (not gitignored,
not derived), so no determinism/`git diff` nuance applies.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT_AGENTS = "AGENTS.md"
# After the 05-03 domain move (GEN-01), the .NET package (libs/dotnet, incl. its per-package
# AGENTS.md) relocated under the log-parser example instance. The CORE per-package rules plane is now
# Python-only; the .NET per-package rules live with the example (05-05 recasts the root map).
PER_PACKAGE_AGENTS = ["libs/python/AGENTS.md"]


def _read(repo_root: Path, rel: str) -> str:
    p = repo_root / rel
    assert p.is_file(), f"missing required rules file: {rel}"
    return p.read_text(encoding="utf-8")


def test_all_three_agents_md_exist(repo_root: Path) -> None:
    for rel in [ROOT_AGENTS, *PER_PACKAGE_AGENTS]:
        assert (repo_root / rel).is_file(), f"AGENTS.md missing: {rel}"


def test_root_agents_carries_map_goldenpath_contractfirst_lazyload(repo_root: Path) -> None:
    text = _read(repo_root, ROOT_AGENTS)
    lower = text.lower()
    # Monorepo map: names the plane/layout members. After the 05-03 domain move (GEN-01),
    # libs/dotnet relocated under the log-parser example instance, so it is no longer a required CORE
    # root-map member (05-05 recasts the root map to the template shape).
    for member in ("contracts/", "golden/", "libs/python", "tools/", ".memory/"):
        assert member in text, f"root AGENTS.md monorepo map missing member: {member}"
    # At least one golden-path command reference.
    assert any(
        cmd in text for cmd in ("tools.contract_drift", "tools.golden_runner", "uv run pytest")
    ), "root AGENTS.md missing a golden-path command reference"
    # Contract-first rule + lazy-load rule.
    assert "contract-first" in lower, "root AGENTS.md missing the contract-first rule"
    assert "lazy-load" in lower, "root AGENTS.md missing the lazy-load rule"


@pytest.mark.parametrize("rel", PER_PACKAGE_AGENTS)
def test_per_package_restates_non_negotiables(repo_root: Path, rel: str) -> None:
    """P11 backstop: each per-package file must RESTATE the non-negotiables, not inherit them."""
    text = _read(repo_root, rel)
    lower = text.lower()
    # Contract-first restated.
    assert "contract-first" in lower, (
        f"{rel} does not restate contract-first (P11 inherit-only risk)"
    )
    # Constitution-plane-is-gated restated (names the gated members).
    assert "contracts/" in text and "golden/" in text, f"{rel} does not restate constitution-gated"
    assert "do not write" in lower or "human-promoted" in lower or "gated" in lower, (
        f"{rel} does not restate the constitution-gated rule"
    )
    # §4-5 boundary invariants restated (BOM + LF are the signature markers).
    assert "bom" in lower and "lf" in lower, f"{rel} does not restate the §4-5 boundary invariants"


def test_claude_md_points_to_agents_md(repo_root: Path) -> None:
    """RULES-01: CLAUDE.md carries a pointer to AGENTS.md (not a duplicate)."""
    text = _read(repo_root, "CLAUDE.md")
    assert "AGENTS.md" in text, "CLAUDE.md must point to AGENTS.md"


def test_claude_md_gsd_profile_block_untouched(repo_root: Path) -> None:
    """T-02-13: the GSD-managed profile block must survive intact (we only appended a pointer)."""
    text = _read(repo_root, "CLAUDE.md")
    assert "<!-- GSD:profile-start -->" in text and "<!-- GSD:profile-end -->" in text, (
        "GSD-managed profile block markers must remain intact"
    )
