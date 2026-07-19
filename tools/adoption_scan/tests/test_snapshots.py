"""Task 3: a committed syrupy snapshot of all three artifacts rendered over the D-06 fixture —
the anti-`git diff`-trap determinism proof (26-RESEARCH.md Pitfall 5)."""

from __future__ import annotations

from pathlib import Path

from tools.adoption_scan import destinations, plan, scan


def test_artifacts_match_committed_snapshot(tmp_minirepo: Path, snapshot) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    plan_doc = plan.build_plan(inventory)
    # CR-01: proposed content comes from the harness's OWN checkout, never the scanned target.
    proposed_hashes = destinations.harness_proposed_hashes()
    manifest_doc = destinations.build_manifest(inventory, tmp_minirepo, proposed_hashes)

    combined = (
        "===== inventory =====\n"
        + scan._dump(inventory).decode("utf-8")
        + "===== plan =====\n"
        + scan._dump(plan_doc).decode("utf-8")
        + "===== manifest =====\n"
        + scan._dump(manifest_doc).decode("utf-8")
    )
    assert combined == snapshot
