"""PIPE-01 component CONSISTENCY gate — the generic [[components]] slot in
harness/project.toml is well-formed and internally agrees (config = SSOT, no codegen).

Mirrors test_language_config.py's structural-scan idiom (repo root via parents[3], real config
loaded through the shared loader, iterate-config / assert-agreement / fail-loud). These checks run
against the GENERIC core default ONLY (source/sink carrying the `greeting` contract) — they must NOT reference any
instance overlay (an instance's own topology lives under its own tree, never the core default).
A malformed component set (a component naming an undeclared language, or duplicate component ids)
fails the suite loud so a broken config never resolves silently (T-8-01).

CER-08 (Phase 44) removed the core edge DATA together with the two edge gates that read it: with no
edges declared, their loop bodies never executed and they passed while asserting nothing. An
instance overlay declares its own edges and gates them in its own tree.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import components, languages, load_project

# test_pipeline_config.py -> tests -> harness_lint -> tools -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTRACTS_DIR = _REPO_ROOT / "contracts"


def _component_ids(cfg: dict) -> set[str]:
    return {c["id"] for c in components(cfg)}


def test_component_languages_are_declared() -> None:
    """Every component's `language` names a declared [[languages]].id (cross-slot agreement).

    A component pointing at an undeclared toolchain is a topology the conductor cannot route —
    fail loud naming the offending component id.
    """
    cfg = load_project()
    declared = {lang["id"] for lang in languages(cfg)}
    for comp in components(cfg):
        assert comp["language"] in declared, (
            f"component {comp['id']!r}: language {comp['language']!r} is not a declared "
            f"[[languages]].id (declared: {sorted(declared)})"
        )


def test_component_ids_unique() -> None:
    """No two components share an `id` (a duplicate makes edge endpoints ambiguous)."""
    ids = [c["id"] for c in components(load_project())]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate component id(s): {dupes}"
