"""Task 3: a committed syrupy snapshot of all three artifacts rendered over the D-06 fixture —
the anti-`git diff`-trap determinism proof (26-RESEARCH.md Pitfall 5)."""

from __future__ import annotations

from pathlib import Path

from tools.adoption_scan import destinations, plan, scan

# CR-02 (26-VERIFICATION.md gap 1): a small, hand-listed FIXED catalog, decoupled from the live
# repo's file count, spanning every DISPOSITION_ENUM case reachable against the tmp_minirepo
# fixture (preserve omitted — constructing a hash-equal pair here would require this fixture to
# track the real repo's file content, defeating the point; preserve stays proven by
# test_dispositions.py::test_each_disposition_reachable/test_collision_rule). Rendering the
# manifest section over this fixed list, not the live destination_catalog(), means an unrelated
# future harness file add/remove (a new how-to page, a new ADR) never reds this snapshot test.
_FIXED_CATALOG: tuple[dict, ...] = (
    {
        "destination": "contracts/harness/adoption/inventory.schema.json"
    },  # human-ratification-required
    {"destination": "docs/reference/inventory.md"},  # derived-regenerate
    {"destination": "AGENTS.md"},  # marker-merge
    {"destination": "pyproject.toml"},  # conflict (tmp_minirepo's differs from the harness's own)
    {"destination": ".github/workflows/ci.yml"},  # conflict (same reasoning)
    {"destination": "docs/how-to/brand-new-page.md"},  # create (absent from tmp_minirepo)
)


def test_artifacts_match_committed_snapshot(tmp_minirepo: Path, snapshot) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    plan_doc = plan.build_plan(inventory)
    # CR-01: proposed content comes from the harness's OWN checkout, never the scanned target.
    proposed_hashes = destinations.harness_proposed_hashes()
    manifest_doc = destinations.build_manifest(
        inventory, tmp_minirepo, proposed_hashes, catalog=list(_FIXED_CATALOG)
    )

    combined = (
        "===== inventory =====\n"
        + scan._dump(inventory).decode("utf-8")
        + "===== plan =====\n"
        + scan._dump(plan_doc).decode("utf-8")
        + "===== manifest =====\n"
        + scan._dump(manifest_doc).decode("utf-8")
    )
    assert combined == snapshot
