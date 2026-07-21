"""Determinism proofs (D-06 / roadmap success criterion 1): byte-identical double-run, and
byte-identical output regardless of a seeded-shuffled enumeration order (seed 1337)."""

from __future__ import annotations

import json
import random
from pathlib import Path

from tools.adoption_scan import scan


def _dumps(inventory: dict) -> bytes:
    return (json.dumps(inventory, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode(
        "utf-8"
    )


def test_double_run_byte_identical(tmp_minirepo: Path) -> None:
    first = scan.build_inventory(tmp_minirepo)
    second = scan.build_inventory(tmp_minirepo)
    assert _dumps(first) == _dumps(second)


def test_shuffled_enumeration_byte_identical(tmp_minirepo: Path) -> None:
    normal_paths, _mode = scan.enumerate_target(tmp_minirepo)
    normal = scan.build_inventory(tmp_minirepo, _paths=normal_paths)

    shuffled_paths = random.Random(1337).sample(normal_paths, len(normal_paths))
    assert shuffled_paths != normal_paths, "seeded shuffle must actually reorder the candidates"
    shuffled = scan.build_inventory(tmp_minirepo, _paths=shuffled_paths)

    assert _dumps(normal) == _dumps(shuffled)
