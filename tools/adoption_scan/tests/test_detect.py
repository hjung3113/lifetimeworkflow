"""detect.py tests: language/manifest/CI observed, candidate boundary inferred, and full
inventory.schema.json conformance (Task 3 — where the four detection arrays first get populated
end-to-end)."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.adoption_scan import detect, scan


def _record_by(records: list[dict], key: str, value: object) -> dict | None:
    return next((record for record in records if record[key] == value), None)


def test_python_language_observed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    python = _record_by(inventory["languages"], "name", "python")
    assert python is not None
    assert python["classification"] == "observed"
    assert python["evidence"]


def test_pyproject_manifest_observed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    manifest = _record_by(inventory["manifests"], "path", "pyproject.toml")
    assert manifest is not None
    assert manifest["kind"] == "pyproject.toml"
    assert manifest["classification"] == "observed"


def test_ci_surface_observed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    ci = _record_by(inventory["ci_surfaces"], "target", ".github/workflows")
    assert ci is not None
    assert ci["classification"] == "observed"


def test_candidate_process_boundary_inferred_never_observed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    assert inventory["candidate_process_boundaries"], "expected at least one candidate boundary"
    for record in inventory["candidate_process_boundaries"]:
        assert record["classification"] == "inferred"
        assert record.get("rationale")


def test_inventory_validates_against_schema(tmp_minirepo: Path, repo_root: Path) -> None:
    schema_path = repo_root / "contracts" / "harness" / "adoption" / "inventory.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    inventory = scan.build_inventory(tmp_minirepo)
    errors = list(Draft202012Validator(schema).iter_errors(inventory))
    assert not errors, [error.message for error in errors]


def test_root_and_nested_agents_md_get_per_file_surface_records() -> None:
    """WR-01 (26-REVIEW.md): a root AGENTS.md and every nested AGENTS.md each get their OWN
    surfaceRecord keyed by their actual path — never collapsed into a single fixed-literal-target
    record, since nearest-wins AGENTS.md semantics are inherently per-directory."""
    included = [
        {"path": "AGENTS.md", "sha256": "a" * 64, "size": 1},
        {"path": "libs/python/AGENTS.md", "sha256": "b" * 64, "size": 2},
        {"path": "packages/widget/AGENTS.md", "sha256": "c" * 64, "size": 3},
    ]
    surfaces = detect.detect_documentation_surfaces(included)
    agents_surfaces = [s for s in surfaces if s["target"].endswith("AGENTS.md")]

    targets = {s["target"] for s in agents_surfaces}
    assert targets == {
        "AGENTS.md",
        "libs/python/AGENTS.md",
        "packages/widget/AGENTS.md",
    }, "every distinct AGENTS.md path must get its own surfaceRecord, not one lumped record"

    for surface in agents_surfaces:
        # Each record's evidence must point ONLY at its own file, never at a sibling's.
        assert len(surface["evidence"]) == 1
        assert surface["evidence"][0]["path"] == surface["target"]
