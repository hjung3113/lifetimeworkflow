"""Keep /contract-check stage 1 from silently becoming a no-op."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTRACTS_DIR = _REPO_ROOT / "contracts"
_INSTANCE_SUFFIXES = (".yaml", ".yml", ".json")


def _stage_one_pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for schema in sorted(_CONTRACTS_DIR.glob("**/*.schema.json")):
        base = schema.name.removesuffix(".schema.json")
        for suffix in _INSTANCE_SUFFIXES:
            instance = schema.with_name(f"{base}{suffix}")
            if instance.is_file():
                pairs.append((schema, instance))
    return pairs


def test_contract_check_stage_one_has_instance_pair() -> None:
    """The command's schema/companion convention must discover at least one pair."""
    assert _stage_one_pairs(), (
        "contract-check stage 1 is vacuous: no contracts/**/*.schema.json has a sibling "
        "instance with .yaml/.yml/.json"
    )
