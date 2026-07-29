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


def test_schema_surface_observed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    assert inventory["schema_surfaces"], "expected at least one schema surface"
    for record in inventory["schema_surfaces"]:
        assert record["classification"] == "observed"
    all_paths = {
        ref["path"] for record in inventory["schema_surfaces"] for ref in record["evidence"]
    }
    assert "contracts/widget.schema.json" in all_paths


def test_schema_surface_excludes_files_outside_contracts(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    all_paths = {
        ref["path"] for record in inventory["schema_surfaces"] for ref in record["evidence"]
    }
    assert "tools/widget_tool.schema.json" not in all_paths


def test_codeowners_surface_observed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    assert inventory["codeowners_surfaces"], "expected a codeowners surface"
    for record in inventory["codeowners_surfaces"]:
        assert record["classification"] == "observed"
    all_paths = {
        ref["path"] for record in inventory["codeowners_surfaces"] for ref in record["evidence"]
    }
    assert ".github/CODEOWNERS" in all_paths


def test_codeowners_surface_root_location() -> None:
    """WR-06 (26-REVIEW.md): a root CODEOWNERS file (no .github/ prefix) is recognized as its own
    surfaceRecord — one of the two GitHub-honored locations the previous single-path matcher
    missed."""
    included = [{"path": "CODEOWNERS", "sha256": "d" * 64, "size": 6}]
    surfaces = detect.detect_codeowners_surfaces(included)
    assert len(surfaces) == 1
    assert surfaces[0]["target"] == "CODEOWNERS"
    assert surfaces[0]["classification"] == "observed"


def test_codeowners_surface_docs_location() -> None:
    """WR-06: a docs/CODEOWNERS file is recognized as its own surfaceRecord — the second
    previously-missed GitHub-honored location."""
    included = [{"path": "docs/CODEOWNERS", "sha256": "e" * 64, "size": 6}]
    surfaces = detect.detect_codeowners_surfaces(included)
    assert len(surfaces) == 1
    assert surfaces[0]["target"] == "docs/CODEOWNERS"
    assert surfaces[0]["classification"] == "observed"


def test_inventory_validates_against_schema(tmp_minirepo: Path, repo_root: Path) -> None:
    schema_path = repo_root / "contracts" / "harness" / "adoption" / "inventory.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    inventory = scan.build_inventory(tmp_minirepo)
    errors = list(Draft202012Validator(schema).iter_errors(inventory))
    assert not errors, [error.message for error in errors]


def test_pyproject_runtime_and_dev_dependencies_parsed() -> None:
    text = (
        "[project]\n"
        'dependencies = ["widget-core>=1.0", "widget-lib"]\n\n'
        "[dependency-groups]\n"
        'dev = ["widget-test-tools"]\n'
    )
    entries = detect.detect_dependencies("pyproject.toml", "pyproject.toml", text)
    assert len(entries) == 3
    by_name = {entry["name"]: entry for entry in entries}
    assert by_name.keys() == {"widget-core", "widget-lib", "widget-test-tools"}
    assert by_name["widget-core"]["kind"] == "runtime"
    assert by_name["widget-lib"]["kind"] == "runtime"
    assert by_name["widget-test-tools"]["kind"] == "dev"
    for entry in entries:
        assert "path" not in entry


def test_package_json_dependencies_and_dev_dependencies_have_distinct_kind() -> None:
    text = json.dumps(
        {
            "dependencies": {"widget-core": "^1.0.0"},
            "devDependencies": {"widget-test-tools": "^2.0.0"},
        }
    )
    entries = detect.detect_dependencies("package.json", "package.json", text)
    by_name = {entry["name"]: entry for entry in entries}
    assert by_name["widget-core"]["kind"] == "runtime"
    assert by_name["widget-test-tools"]["kind"] == "dev"


def test_csproj_project_reference_is_path_based() -> None:
    text = (
        "<Project>\n"
        "  <ItemGroup>\n"
        '    <ProjectReference Include="../widget-core/widget-core.csproj" />\n'
        "  </ItemGroup>\n"
        "</Project>\n"
    )
    entries = detect.detect_dependencies("widget-app/widget-app.csproj", "*.csproj", text)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["path"] == "../widget-core/widget-core.csproj"
    assert entry["name"] == "../widget-core/widget-core.csproj"
    assert entry["kind"] == "runtime"


def test_go_mod_require_block_and_single_line_both_parsed() -> None:
    text = (
        "module widget-app\n\n"
        "go 1.22\n\n"
        "require (\n"
        "\twidget.example/core v1.0.0\n"
        "\twidget.example/lib v2.0.0\n"
        ")\n\n"
        "require widget.example/extra v3.0.0\n"
    )
    entries = detect.detect_dependencies("go.mod", "go.mod", text)
    names = {entry["name"] for entry in entries}
    assert names == {
        "widget.example/core",
        "widget.example/lib",
        "widget.example/extra",
    }
    for entry in entries:
        assert entry["kind"] == "runtime"
        assert "path" not in entry


def test_cargo_toml_path_dependency_kept_registry_dependency_dropped() -> None:
    text = (
        "[dependencies]\n"
        'widget-core = { path = "../widget-core" }\n'
        'widget-registry = "1.0"\n\n'
        "[dev-dependencies]\n"
        'widget-test-tools = { path = "../widget-test-tools" }\n'
    )
    entries = detect.detect_dependencies("Cargo.toml", "Cargo.toml", text)
    assert len(entries) == 2
    by_name = {entry["name"]: entry for entry in entries}
    assert by_name.keys() == {"widget-core", "widget-test-tools"}
    assert by_name["widget-core"]["kind"] == "runtime"
    assert by_name["widget-core"]["path"] == "../widget-core"
    assert by_name["widget-test-tools"]["kind"] == "dev"
    assert by_name["widget-test-tools"]["path"] == "../widget-test-tools"


def test_unrecognized_kind_returns_empty_list() -> None:
    assert detect.detect_dependencies("x", "unknown-kind", "") == []


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
