"""Task 3: full-pipeline determinism proofs — double-run byte-identical, and a seeded-shuffled
enumeration order byte-identical to the unshuffled run, for all three artifacts (Pitfall 5: never
proven via `git diff` — always independent byte comparison into separate tmp_path dirs)."""

from __future__ import annotations

import random
from pathlib import Path

from tools.adoption_scan import cli, destinations, plan, scan


def test_double_run_byte_identical(tmp_minirepo: Path, tmp_path: Path) -> None:
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"

    rc1 = cli.main(["--target", str(tmp_minirepo), "--out", str(out1)])
    rc2 = cli.main(["--target", str(tmp_minirepo), "--out", str(out2)])
    assert rc1 == 0
    assert rc2 == 0

    for name in ("inventory", "plan", "manifest"):
        bytes1 = (out1 / f"{name}.json").read_bytes()
        bytes2 = (out2 / f"{name}.json").read_bytes()
        assert bytes1 == bytes2, f"{name}.json differs across independent runs"


def _pipeline_bytes(target: Path, *, _paths: list[Path] | None = None) -> dict[str, bytes]:
    inventory = scan.build_inventory(target, _paths=_paths)
    plan_doc = plan.build_plan(inventory)
    proposed_hashes = {entry["path"]: entry["sha256"] for entry in inventory["included"]}
    manifest_doc = destinations.build_manifest(inventory, target, proposed_hashes)
    return {
        "inventory": scan._dump(inventory),
        "plan": scan._dump(plan_doc),
        "manifest": scan._dump(manifest_doc),
    }


def test_shuffled_enumeration_byte_identical(tmp_minirepo: Path) -> None:
    normal_paths, _mode = scan.enumerate_target(tmp_minirepo)
    normal = _pipeline_bytes(tmp_minirepo, _paths=normal_paths)

    shuffled_paths = random.Random(1337).sample(normal_paths, len(normal_paths))
    assert shuffled_paths != normal_paths, "seeded shuffle must actually reorder the candidates"
    shuffled = _pipeline_bytes(tmp_minirepo, _paths=shuffled_paths)

    assert normal == shuffled
