"""detect.py tests: language/manifest/CI observed, candidate boundary inferred, and full
inventory.schema.json conformance (Task 3 — where the four detection arrays first get populated
end-to-end)."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import pytest
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


def test_csproj_project_reference_legacy_msbuild_namespace_fallback() -> None:
    """IN-01 (47-REVIEW.md): legacy (pre-SDK-style) .csproj files commonly declare
    ``xmlns="http://schemas.microsoft.com/developer/msbuild/2003"`` on the ``<Project>`` root,
    which puts every child element (including ``ProjectReference``) into that namespace. An
    unqualified ``findall`` then silently matches nothing; the parser must fall back to the
    legacy MSBuild namespace when the unqualified search returns no results."""
    text = (
        '<Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003"'
        ' DefaultTargets="Build" ToolsVersion="4.0">\n'
        "  <ItemGroup>\n"
        '    <ProjectReference Include="../widget-core/widget-core.csproj" />\n'
        "  </ItemGroup>\n"
        "</Project>\n"
    )
    entries = detect.detect_dependencies("widget-app/widget-app.csproj", "*.csproj", text)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["path"] == "../widget-core/widget-core.csproj"
    assert entry["kind"] == "runtime"


def test_csproj_project_reference_backslash_separators_normalized() -> None:
    """WR-01 (47-REVIEW.md): a Windows-style backslash ``Include`` path (MSBuild accepts it on
    any OS, and Visual-Studio-authored .csproj files commonly emit it) must normalize to
    forward slashes so the referenced path resolves against git-tracked (always forward-slash)
    manifest paths."""
    text = (
        "<Project>\n"
        "  <ItemGroup>\n"
        '    <ProjectReference Include="..\\widget-core\\widget-core.csproj" />\n'
        "  </ItemGroup>\n"
        "</Project>\n"
    )
    entries = detect.detect_dependencies("widget-app/widget-app.csproj", "*.csproj", text)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["path"] == "../widget-core/widget-core.csproj"
    assert entry["name"] == "../widget-core/widget-core.csproj"
    assert entry["kind"] == "runtime"


def test_package_json_null_dependencies_does_not_raise() -> None:
    """IN-02 (47-REVIEW.md): ``"dependencies": null`` is valid JSON (occasionally emitted by
    hand-edited or programmatic package.json files); ``.get()``'s default only applies when the
    key is absent, not when it is present-but-null, so a naive ``for name in data.get(...,
    {})`` raises ``TypeError`` on iteration. Must degrade to no entries instead."""
    text = json.dumps({"dependencies": None, "devDependencies": None})
    entries = detect.detect_dependencies("package.json", "package.json", text)
    assert entries == []


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


def test_pnpm_workspace_globs_parsed_quotes_stripped_order_preserved() -> None:
    text = 'packages:\n  - "apps/*"\n  - "packages/*"\n'
    assert detect.parse_pnpm_workspace_globs(text) == ["apps/*", "packages/*"]


def test_pnpm_workspace_globs_bare_and_single_quoted_parse_identically() -> None:
    bare = "packages:\n  - apps/*\n  - packages/*\n"
    single_quoted = "packages:\n  - 'apps/*'\n  - 'packages/*'\n"
    double_quoted = 'packages:\n  - "apps/*"\n  - "packages/*"\n'
    expected = ["apps/*", "packages/*"]
    assert detect.parse_pnpm_workspace_globs(bare) == expected
    assert detect.parse_pnpm_workspace_globs(single_quoted) == expected
    assert detect.parse_pnpm_workspace_globs(double_quoted) == expected


def test_pnpm_workspace_globs_comments_and_blanks_ignored_key_ends_block() -> None:
    text = (
        "packages:\n"
        "  # a comment inside the block\n"
        "\n"
        '  - "apps/*"\n'
        "  # another comment\n"
        '  - "packages/*"\n'
        "other_key: value\n"
        "  - not-a-member-of-packages\n"
    )
    assert detect.parse_pnpm_workspace_globs(text) == ["apps/*", "packages/*"]


def test_pnpm_workspace_globs_malformed_or_empty_returns_empty_list_never_raises() -> None:
    assert detect.parse_pnpm_workspace_globs("") == []
    assert detect.parse_pnpm_workspace_globs("not: yaml: at: all: {{{[[[") == []
    assert detect.parse_pnpm_workspace_globs("packages:\n") == []
    assert detect.parse_pnpm_workspace_globs("no packages key here\njust prose\n") == []
    # Genuine negative control: a non-str input reaches `.splitlines()` and raises
    # AttributeError with no `try`/`except` around the body. Deleting the wrapping try/except
    # must red this assertion (it would raise instead of degrading to `[]`).
    assert detect.parse_pnpm_workspace_globs(None) == []  # type: ignore[arg-type]


def test_workspace_member_matches_declared_globs() -> None:
    globs = ["apps/*", "packages/*"]
    assert detect.is_workspace_member("apps/widget-app", globs) is True
    assert detect.is_workspace_member("docs/design-prototype", globs) is False


def test_workspace_member_root_always_true_regardless_of_globs() -> None:
    assert detect.is_workspace_member(".", []) is True
    assert detect.is_workspace_member(".", ["apps/*"]) is True


def test_workspace_member_single_segment_star_does_not_match_nested_dir() -> None:
    assert detect.is_workspace_member("apps/widget-app/nested", ["apps/*"]) is False


def test_workspace_member_traversal_glob_contributes_no_members() -> None:
    # Segment-count mismatch alone would already reject these (glob has one more segment than
    # the directory), so they exercise the traversal guard only incidentally.
    assert detect.is_workspace_member("outside", ["../outside/*"]) is False
    assert detect.is_workspace_member("outside/nested", ["../outside/*"]) is False
    # A genuine negative control: segment COUNTS match (4 vs 4) and every non-".." segment
    # matches too, so only the explicit ".."-segment rejection stops this from matching.
    # Deleting that rejection must red this assertion.
    assert detect.is_workspace_member("sub/../sibling/foo", ["sub/../sibling/*"]) is False


def test_workspace_member_absolute_glob_contributes_no_members() -> None:
    assert detect.is_workspace_member("etc", ["/etc/*"]) is False


def test_pnpm_workspace_manifest_not_registered_in_manifest_kind_table() -> None:
    assert "pnpm-workspace.yaml" not in detect._MANIFEST_KIND_BY_NAME


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


# ── 52-REVIEW.md repairs — parser + matcher (CR-02, WR-01, WR-02, WR-03, WR-09) ──────────────


def test_pnpm_workspace_globs_flow_style_sequence_parsed() -> None:
    """CR-02: `packages: ["apps/*", "packages/*"]` is valid YAML and a common pnpm manifest shape.

    Before the repair the parser only entered its block on a BARE `packages:` line, so flow style
    yielded `[]` — which scan.py then read as "this workspace has exactly one member", collapsing
    the whole inventory to root-only. Reverting the `_parse_flow_sequence` branch reds this.
    """
    assert detect.parse_pnpm_workspace_globs('packages: ["apps/*", "packages/*"]\n') == [
        "apps/*",
        "packages/*",
    ]
    assert detect.parse_pnpm_workspace_globs("packages: [apps/*, 'packages/*']\n") == [
        "apps/*",
        "packages/*",
    ]
    # A literally empty flow sequence really does declare no globs.
    assert detect.parse_pnpm_workspace_globs("packages: []\n") == []


def test_pnpm_workspace_globs_settings_only_manifest_yields_no_globs() -> None:
    """A pnpm-10 settings-only manifest declares no `packages:` key at all (CR-02 row 2)."""
    text = "onlyBuiltDependencies:\n  - esbuild\n"
    assert detect.parse_pnpm_workspace_globs(text) == []


def test_pnpm_workspace_globs_narrow_except_does_not_swallow_programming_errors() -> None:
    """WR-09: the handler is narrowed to input-SHAPE faults only.

    A non-str input still degrades to `[]` (AttributeError on `.splitlines()`), but an unexpected
    exception raised from inside the loop must PROPAGATE rather than being silently converted into
    "this workspace declares zero members". Widening the handler back to `except Exception` reds
    the second half of this test.
    """
    assert detect.parse_pnpm_workspace_globs(None) == []  # type: ignore[arg-type]

    class Exploding(str):
        def splitlines(self):  # type: ignore[override]
            raise ZeroDivisionError("a genuine programming error, not an input-shape fault")

    with pytest.raises(ZeroDivisionError):
        detect.parse_pnpm_workspace_globs(Exploding("packages:\n"))


def test_workspace_member_globstar_matches_any_depth() -> None:
    """WR-01: `**` means any depth (pnpm's own documented example), not exactly one segment.

    The pre-repair `len(glob_parts) != len(directory_parts): continue` rule made `packages/**` a
    single-segment match, so `packages/b/deep` was silently excluded as `non-workspace-member`.
    """
    globs = ["packages/**"]
    assert detect.is_workspace_member("packages/b", globs) is True
    assert detect.is_workspace_member("packages/b/deep", globs) is True
    assert detect.is_workspace_member("packages/b/deep/deeper", globs) is True
    # `**` must not escape its own prefix.
    assert detect.is_workspace_member("apps/a", globs) is False
    # A single `*` still matches exactly one segment (unchanged semantics).
    assert detect.is_workspace_member("apps/a/nested", ["apps/*"]) is False


def test_workspace_member_matching_is_case_sensitive_on_every_platform(monkeypatch) -> None:
    """WR-02: `fnmatch.fnmatch` normcases both operands, making membership — and therefore
    `inventory.json` — platform-dependent; `fnmatchcase` does not.

    The monkeypatch is what gives this test teeth. `posixpath.normcase` is the IDENTITY function,
    so on this repo's CI/dev platforms a plain `assert is_workspace_member("apps/Widget",
    ["apps/widget"]) is False` passes with `fnmatch` too — a check that cannot fail. Substituting
    a lowercasing normcase reproduces `ntpath.normcase`, which is exactly the Windows behaviour
    the finding is about; with `fnmatchcase` the substitution is inert, with `fnmatch` it makes
    the two directories compare equal and reds the assertion.
    """
    monkeypatch.setattr(fnmatch.os.path, "normcase", str.lower)
    assert detect.is_workspace_member("apps/Widget", ["apps/widget"]) is False
    assert detect.is_workspace_member("Apps/widget", ["apps/*"]) is False
    assert detect.is_workspace_member("apps/widget", ["apps/widget"]) is True


def test_workspace_member_honours_negation_globs() -> None:
    """WR-03: a `!`-prefixed glob is a pnpm EXCLUSION, not a positive membership pattern.

    Pre-repair, `!packages/legacy` was stored verbatim and never interpreted, so
    `is_workspace_member("packages/legacy", ["packages/*", "!packages/legacy"])` returned True and
    the inventory over-included.
    """
    globs = ["packages/*", "!packages/legacy"]
    assert detect.is_workspace_member("packages/legacy", globs) is False
    assert detect.is_workspace_member("packages/widget", globs) is True
    # A negation alone grants membership to nothing (no positive match).
    assert detect.is_workspace_member("packages/widget", ["!packages/legacy"]) is False
