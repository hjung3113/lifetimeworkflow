"""Tests for the package-facts generator (MONO-01/MONO-02).

Pins the guarantees the derived plane depends on:
  (1) determinism — render twice AND generate->hash->delete->regenerate are byte-identical.
  (2) structure — the DERIVED marker, every real-tree package dict carries all 4 keys, and a
      real-tree structural check (header/no-timestamp/non-empty/sorted) that stays entirely
      in-memory so it never commits an instance path into a snapshot file.
  (3) discovery + exclusion — a fixture manifest under `tests/fixtures/**` never becomes a
      package (git-plumbing tmp_path repo, mirrors test_ci_stale_derived.py's tmp_path idiom).
  (4) per-manifest-kind add/remove-a-dependency correctness — the load-bearing MONO-02
      criterion-2 proof, built on synthetic fixture manifests (the live tree only exercises
      2 of 5 edge kinds) plus the unresolvable-dependency-is-dropped guarantee.
  (5) a committed syrupy snapshot of render(build_facts()) over a SYNTHETIC, domain-neutral
      fixture repo (not the real tree — see GEN-04, tools/harness_lint/tests/
      test_core_no_example_dep.py).
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

from tools.memory_regen import package_facts

# ---- (1) determinism ---------------------------------------------------------------------------


def test_render_is_deterministic_over_real_tree() -> None:
    """render(build_facts()) twice over the real repo tree is byte-identical."""
    first = package_facts.render(package_facts.build_facts())
    second = package_facts.render(package_facts.build_facts())
    assert first == second


def test_generate_delete_regenerate_is_byte_identical(tmp_path: Path) -> None:
    """generate -> sha256 -> delete -> regenerate -> assert identical hash."""
    out = tmp_path / "derived" / "package-facts.md"
    package_facts.write(index_path=out)
    digest_1 = hashlib.sha256(out.read_bytes()).hexdigest()
    out.unlink()
    assert not out.exists()
    package_facts.write(index_path=out)
    digest_2 = hashlib.sha256(out.read_bytes()).hexdigest()
    assert digest_1 == digest_2


# ---- (2) structure ------------------------------------------------------------------------------


def test_output_carries_derived_marker() -> None:
    text = package_facts.render(package_facts.build_facts())
    assert text.splitlines()[0].startswith("# DERIVED — do not hand-edit")


def test_real_tree_packages_have_all_keys() -> None:
    facts = package_facts.build_facts()
    assert facts["packages"], "no packages discovered in the real tree"
    for pkg in facts["packages"]:
        assert set(pkg) == {"id", "manifest", "dir", "language"}


def test_real_tree_render_structure() -> None:
    """Structural assertions on the LIVE tree's rendered output, asserted in-memory only (never
    committed) so real-tree coverage does not require embedding instance paths in a committed
    file — that is exactly what GEN-04 (`test_core_no_example_dep.py`) forbids. Checks the
    DERIVED header, the no-timestamp determinism contract, non-empty discovery, and
    manifest-sorted row order.
    """
    facts = package_facts.build_facts()
    text = package_facts.render(facts)
    lines = text.splitlines()
    assert lines[0] == f"# {package_facts.DERIVED_HEADER}"
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text), (
        "derived artifact must carry no timestamp"
    )
    assert facts["packages"], "no packages discovered in the real tree"
    manifests = [pkg["manifest"] for pkg in facts["packages"]]
    assert manifests == sorted(manifests), "packages must be rendered in manifest-sorted order"

    # Convention Profiles section (MONO-05/MONO-06) — asserted IN-MEMORY ONLY, never committed
    # to a snapshot (GEN-04: a live-tree snapshot under tools/ would embed instance paths).
    assert "## Convention Profiles" in text
    root_row = next(line for line in lines if line.startswith("| logparser-harness | . |"))
    inner_row = next(
        line for line in lines if line.startswith("| logparser-normalize | libs/python |")
    )
    # nested-wins: libs/python's nearest AGENTS.md differs from the root's, even though both
    # packages share the same `python` language row (real-tree proof, RESEARCH.md Pitfall 2).
    assert "libs/python/AGENTS.md" in inner_row
    assert "libs/python/AGENTS.md" not in root_row
    assert " AGENTS.md " in root_row or root_row.endswith(" AGENTS.md |")


# ---- (3) discovery + exclusion -------------------------------------------------------------------


def test_discover_manifests_excludes_tests_fixtures_segment(tmp_path: Path) -> None:
    """A manifest at a `tests/fixtures/**` path is excluded; a root manifest is not."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "widget-root"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    fixture_dir = repo / "pkg" / "tests" / "fixtures" / "sample"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "pyproject.toml").write_text(
        '[project]\nname = "widget-fixture"\nversion = "0.1.0"\n', encoding="utf-8"
    )

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=a@a.test", "-c", "user.name=a", "commit", "-m", "seed"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    records = package_facts.discover_manifests(repo_root=repo)
    paths = {record["path"] for record in records}
    assert paths == {"pyproject.toml"}


# ---- (4) per-manifest-kind add/remove-a-dependency correctness ----------------------------------


def _widget_manifest(path: str, kind: str) -> dict:
    return {"path": path, "kind": kind, "classification": "observed", "evidence": []}


def test_pyproject_dependency_add_remove_round_trip(tmp_path: Path) -> None:
    (tmp_path / "widget-core").mkdir()
    (tmp_path / "widget-core" / "pyproject.toml").write_text(
        '[project]\nname = "widget-core"\nversion = "0.1.0"\ndependencies = []\n',
        encoding="utf-8",
    )
    (tmp_path / "widget-app").mkdir()
    app_manifest = tmp_path / "widget-app" / "pyproject.toml"
    app_manifest.write_text(
        '[project]\nname = "widget-app"\nversion = "0.1.0"\ndependencies = ["widget-core"]\n',
        encoding="utf-8",
    )
    manifests = [
        _widget_manifest("widget-core/pyproject.toml", "pyproject.toml"),
        _widget_manifest("widget-app/pyproject.toml", "pyproject.toml"),
    ]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert {"from": "widget-app", "to": "widget-core", "kind": "runtime"} in facts["edges"]

    app_manifest.write_text(
        '[project]\nname = "widget-app"\nversion = "0.1.0"\ndependencies = []\n',
        encoding="utf-8",
    )
    facts_after = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert facts_after["edges"] == []


def test_pyproject_dependency_matches_declared_name_across_pep503_variants(tmp_path: Path) -> None:
    """WR-02 (47-REVIEW.md): a Python package's declared ``[project].name`` and a dependant's
    bare-name reference to it are the SAME distribution per PEP 503/508 even when they differ
    only by hyphen/underscore casing (``widget_core`` vs ``widget-core``) — matching must
    normalize both sides for comparison, while the rendered id stays the manifest's own
    DECLARED name (unchanged visible artifact ids)."""
    (tmp_path / "widget-core").mkdir()
    (tmp_path / "widget-core" / "pyproject.toml").write_text(
        '[project]\nname = "widget_core"\nversion = "0.1.0"\ndependencies = []\n',
        encoding="utf-8",
    )
    (tmp_path / "widget-app").mkdir()
    (tmp_path / "widget-app" / "pyproject.toml").write_text(
        '[project]\nname = "widget-app"\nversion = "0.1.0"\ndependencies = ["widget-core"]\n',
        encoding="utf-8",
    )
    manifests = [
        _widget_manifest("widget-core/pyproject.toml", "pyproject.toml"),
        _widget_manifest("widget-app/pyproject.toml", "pyproject.toml"),
    ]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert {"from": "widget-app", "to": "widget_core", "kind": "runtime"} in facts["edges"]
    # rendered id stays the manifest's own declared name — normalization is comparison-only.
    ids = {pkg["id"] for pkg in facts["packages"]}
    assert "widget_core" in ids
    assert "widget-core" not in ids


def test_package_json_dependency_add_remove_round_trip(tmp_path: Path) -> None:
    (tmp_path / "widget-core").mkdir()
    (tmp_path / "widget-core" / "package.json").write_text(
        '{"name": "widget-core"}\n', encoding="utf-8"
    )
    (tmp_path / "widget-app").mkdir()
    app_manifest = tmp_path / "widget-app" / "package.json"
    app_manifest.write_text(
        '{"name": "widget-app", "dependencies": {"widget-core": "*"},'
        ' "devDependencies": {"widget-core": "*"}}\n',
        encoding="utf-8",
    )
    manifests = [
        _widget_manifest("widget-core/package.json", "package.json"),
        _widget_manifest("widget-app/package.json", "package.json"),
    ]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert {"from": "widget-app", "to": "widget-core", "kind": "runtime"} in facts["edges"]
    assert {"from": "widget-app", "to": "widget-core", "kind": "dev"} in facts["edges"]

    app_manifest.write_text('{"name": "widget-app"}\n', encoding="utf-8")
    facts_after = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert facts_after["edges"] == []


def test_csproj_project_reference_add_remove_round_trip(tmp_path: Path) -> None:
    (tmp_path / "WidgetCore").mkdir()
    (tmp_path / "WidgetCore" / "WidgetCore.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"></Project>\n', encoding="utf-8"
    )
    (tmp_path / "WidgetApp").mkdir()
    app_manifest = tmp_path / "WidgetApp" / "WidgetApp.csproj"
    app_manifest.write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <ItemGroup>\n"
        '    <ProjectReference Include="../WidgetCore/WidgetCore.csproj" />\n'
        "  </ItemGroup>\n"
        "</Project>\n",
        encoding="utf-8",
    )
    manifests = [
        _widget_manifest("WidgetCore/WidgetCore.csproj", "*.csproj"),
        _widget_manifest("WidgetApp/WidgetApp.csproj", "*.csproj"),
    ]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert {"from": "WidgetApp", "to": "WidgetCore", "kind": "runtime"} in facts["edges"]

    app_manifest.write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n  <ItemGroup>\n  </ItemGroup>\n</Project>\n',
        encoding="utf-8",
    )
    facts_after = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert facts_after["edges"] == []


def test_go_mod_require_add_remove_round_trip(tmp_path: Path) -> None:
    (tmp_path / "widget-core").mkdir()
    (tmp_path / "widget-core" / "go.mod").write_text(
        "module widget.example/core\n\ngo 1.22\n", encoding="utf-8"
    )
    (tmp_path / "widget-app").mkdir()
    app_manifest = tmp_path / "widget-app" / "go.mod"
    app_manifest.write_text(
        "module widget.example/app\n\ngo 1.22\n\nrequire (\n\twidget.example/core v0.0.0\n)\n",
        encoding="utf-8",
    )
    manifests = [
        _widget_manifest("widget-core/go.mod", "go.mod"),
        _widget_manifest("widget-app/go.mod", "go.mod"),
    ]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert {
        "from": "widget.example/app",
        "to": "widget.example/core",
        "kind": "runtime",
    } in facts["edges"]

    app_manifest.write_text("module widget.example/app\n\ngo 1.22\n", encoding="utf-8")
    facts_after = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert facts_after["edges"] == []


def test_cargo_toml_path_dependency_add_remove_round_trip(tmp_path: Path) -> None:
    (tmp_path / "widget-core").mkdir()
    (tmp_path / "widget-core" / "Cargo.toml").write_text(
        '[package]\nname = "widget-core"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "widget-app").mkdir()
    app_manifest = tmp_path / "widget-app" / "Cargo.toml"
    app_manifest.write_text(
        '[package]\nname = "widget-app"\nversion = "0.1.0"\n\n'
        '[dependencies]\nwidget-core = { path = "../widget-core" }\n',
        encoding="utf-8",
    )
    manifests = [
        _widget_manifest("widget-core/Cargo.toml", "Cargo.toml"),
        _widget_manifest("widget-app/Cargo.toml", "Cargo.toml"),
    ]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert {"from": "widget-app", "to": "widget-core", "kind": "runtime"} in facts["edges"]

    app_manifest.write_text('[package]\nname = "widget-app"\nversion = "0.1.0"\n', encoding="utf-8")
    facts_after = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert facts_after["edges"] == []


def test_malformed_manifest_does_not_crash_generator(tmp_path: Path, capsys) -> None:
    """WR-03 (47-REVIEW.md): a syntactically malformed manifest degrades for that ONE file
    instead of crashing the whole regeneration — the package is still listed (falling back to
    its directory name, since the declared name could not be parsed) and the parse failure
    surfaces on stderr rather than being silently swallowed."""
    (tmp_path / "widget-broken").mkdir()
    (tmp_path / "widget-broken" / "pyproject.toml").write_text(
        "[project\nname = not valid toml\n", encoding="utf-8"
    )
    (tmp_path / "widget-app").mkdir()
    (tmp_path / "widget-app" / "pyproject.toml").write_text(
        '[project]\nname = "widget-app"\nversion = "0.1.0"\ndependencies = []\n',
        encoding="utf-8",
    )
    manifests = [
        _widget_manifest("widget-broken/pyproject.toml", "pyproject.toml"),
        _widget_manifest("widget-app/pyproject.toml", "pyproject.toml"),
    ]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    ids = {pkg["id"] for pkg in facts["packages"]}
    assert "widget-broken" in ids, "the package must still be listed from what is known"
    assert "widget-app" in ids
    captured = capsys.readouterr()
    assert "widget-broken/pyproject.toml" in captured.err, (
        "the parse failure must surface on stderr, not be silently swallowed"
    )


def test_unresolvable_dependency_is_dropped_not_fabricated(tmp_path: Path) -> None:
    (tmp_path / "widget-app").mkdir()
    (tmp_path / "widget-app" / "pyproject.toml").write_text(
        '[project]\nname = "widget-app"\nversion = "0.1.0"\n'
        'dependencies = ["widget-external-package"]\n',
        encoding="utf-8",
    )
    manifests = [_widget_manifest("widget-app/pyproject.toml", "pyproject.toml")]

    facts = package_facts.build_facts(manifest_paths=manifests, repo_root=tmp_path)
    assert facts["edges"] == []
    assert not any(
        "widget-external-package" in (edge["from"], edge["to"]) for edge in facts["edges"]
    )


# ---- (5) committed snapshot -----------------------------------------------------------------


def test_render_matches_committed_snapshot(snapshot, tmp_path: Path) -> None:
    """Snapshot render(build_facts()) over a SYNTHETIC, domain-neutral fixture repo — not the
    real tree. The real tree also carries the reference instance's own manifests; snapshotting
    it would commit instance-path literals into `tools/`, which GEN-04
    (`test_core_no_example_dep.py`) forbids for core planes. This fixture still exercises the
    renderer meaningfully: 4 packages across 3 manifest kinds (pyproject.toml, package.json,
    `.csproj`) and 2 dependency edges (a pyproject.toml runtime dep, and a package.json runtime
    dep resolving cross-kind to a pyproject.toml package), pinning the DERIVED header, column
    set and row ordering. Built via the same git-plumbing tmp_path idiom as
    `test_discover_manifests_excludes_tests_fixtures_segment`, exercising discovery
    end-to-end (``manifest_paths=None``).
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "widget-lib").mkdir()
    (repo / "widget-lib" / "pyproject.toml").write_text(
        '[project]\nname = "widget-lib"\nversion = "0.1.0"\ndependencies = []\n',
        encoding="utf-8",
    )
    (repo / "widget-core").mkdir()
    (repo / "widget-core" / "pyproject.toml").write_text(
        '[project]\nname = "widget-core"\nversion = "0.1.0"\ndependencies = ["widget-lib"]\n',
        encoding="utf-8",
    )
    (repo / "widget-app").mkdir()
    (repo / "widget-app" / "package.json").write_text(
        '{"name": "widget-app", "dependencies": {"widget-core": "*"}}\n', encoding="utf-8"
    )
    (repo / "widget-cli").mkdir()
    (repo / "widget-cli" / "WidgetCli.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"></Project>\n', encoding="utf-8"
    )

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=a@a.test", "-c", "user.name=a", "commit", "-m", "seed"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    facts = package_facts.build_facts(repo_root=repo)
    assert len(facts["packages"]) == 4, "fixture repo should yield exactly the 4 seeded packages"
    assert len(facts["edges"]) == 2, "fixture repo should yield exactly the 2 seeded edges"
    assert package_facts.render(facts) == snapshot
