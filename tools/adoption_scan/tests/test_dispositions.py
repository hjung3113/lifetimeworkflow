"""Task 1: destinations.py — totality over the rule-derived, real-file catalog +
each-of-7-dispositions-reachable + marker-capable-set-is-exactly-3 + constitution-always-wins +
hash-equal/hash-differ collision rule + GSD-owned exclusion."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.adoption_scan import cli, destinations
from tools.harness_emit.manifest import is_gsd_owned

# WR-11: a loose sanity floor on the real, git-tracked-filtered catalog size — not an exact count
# (the catalog legitimately grows/shrinks as the harness's file tree does).
_MIN_CATALOG_ROWS = 300

_PLACEHOLDER_DESTINATIONS = (
    "harness/agents/widget-engineer.md",
    "harness/commands/widget-check.md",
    "harness/skills/widget-conventions/SKILL.md",
    ".opencode/agent/widget-engineer.md",
    ".claude/agents/widget-engineer.md",
    "golden/widget/verified/case.txt",
    "docs/adr/0001-decision.md",
    ".memory/agreements/0001-widget.md",
    ".workflow/tasks/T-0001/task.json",
    "tools/widget_tool/pyproject.toml",
)


def test_total(tmp_path: Path) -> None:
    """WR-11: destination_catalog() partitions explicitly into dispositioned vs excluded results,
    and the two counts sum to the catalog's total — a regression that made every row resolve to
    None (e.g. a broken is_gsd_owned) turns this test RED, not vacuously green."""
    catalog = destinations.destination_catalog()
    assert len(catalog) >= _MIN_CATALOG_ROWS

    results = [
        destinations.disposition(row["destination"], tmp_path, proposed_sha=None) for row in catalog
    ]
    dispositioned = [r for r in results if r is not None]
    excluded = [r for r in results if r is None]

    assert dispositioned  # non-vacuous: at least one row actually gets a disposition
    assert len(dispositioned) + len(excluded) == len(catalog)
    assert set(dispositioned) <= set(destinations.DISPOSITION_ENUM)
    schema_path = (
        Path(__file__).resolve().parents[3]
        / "contracts/harness/adoption/manifest.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert set(destinations.DISPOSITION_ENUM) == set(schema["$defs"]["dispositionEnum"]["enum"])


def test_catalog_invariant_to_untracked_local_state(repo_root: Path, tmp_path: Path) -> None:
    """CR-01 mandatory clean-checkout reproduction: a fresh `git worktree` checked out at HEAD
    produces the SAME catalog destination set as the current tree — proving the catalog is
    invariant to any local untracked/gitignored state, independent of this working tree's
    particular contents."""
    worktree_dir = tmp_path / "clean-worktree"
    added = subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_dir), "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if added.returncode != 0:
        pytest.skip(f"git worktree add unavailable in this environment: {added.stderr.strip()}")

    try:
        one_liner = (
            "from tools.adoption_scan import destinations; import json; "
            "print(json.dumps(sorted("
            "r['destination'] for r in destinations.destination_catalog()"
            ")))"
        )
        completed = subprocess.run(
            [sys.executable, "-c", one_liner],
            cwd=str(worktree_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        worktree_catalog = json.loads(completed.stdout)
        current_catalog = sorted(row["destination"] for row in destinations.destination_catalog())
        assert worktree_catalog == current_catalog
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_dir)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )


def test_catalog_excludes_untracked_file_in_matched_category(repo_root: Path) -> None:
    """CR-01 fast companion: a live-created untracked ``.memory/derived/*`` file (real path,
    genuinely gitignored, matching a _CATEGORY_GLOBS pattern) is excluded from the catalog while it
    exists."""
    proof_path = repo_root / ".memory" / "derived" / "__cr01_untracked_proof__.md"
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("untracked proof\n", encoding="utf-8")
    try:
        catalog_destinations = {row["destination"] for row in destinations.destination_catalog()}
        assert ".memory/derived/__cr01_untracked_proof__.md" not in catalog_destinations
    finally:
        proof_path.unlink(missing_ok=True)


def test_catalog_excludes_vendor_and_generated_segments() -> None:
    """WR-02: no catalog row's destination intersects _SKIP_SEGMENTS (structural predicate — real
    vendor/generated dirs like .venv/node_modules may or may not exist in this checkout)."""
    for row in destinations.destination_catalog():
        parts = row["destination"].split("/")
        assert not any(seg in destinations._SKIP_SEGMENTS for seg in parts)


def test_symlink_identity_uses_enumerated_path_not_resolved_target(
    monkeypatch, tmp_path: Path
) -> None:
    """WR-04: destination identity is the ENUMERATED path, not the resolved symlink target — two
    distinct symlinks to the same file produce two distinct catalog rows."""
    monkeypatch.setattr(destinations, "_REPO_ROOT", tmp_path)

    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    real_file = adr_dir / "0001-real.md"
    real_file.write_text("real content\n", encoding="utf-8")
    link_file = adr_dir / "0002-link.md"
    try:
        link_file.symlink_to(real_file)
    except OSError:
        pytest.skip("unprivileged symlink creation is not permitted on this filesystem")

    catalog_destinations = {row["destination"] for row in destinations.destination_catalog()}
    assert "docs/adr/0001-real.md" in catalog_destinations
    assert "docs/adr/0002-link.md" in catalog_destinations


def test_each_disposition_reachable(tmp_path: Path) -> None:
    # create — no existing file.
    assert destinations.disposition("docs/how-to/new.md", tmp_path, proposed_sha=None) == "create"

    # preserve — existing file whose hash matches the proposed hash.
    existing = tmp_path / "docs" / "how-to"
    existing.mkdir(parents=True)
    target_file = existing / "preserve-me.md"
    target_file.write_text("stable content\n", encoding="utf-8")
    proposed_sha = destinations._existing_hash(target_file)
    assert (
        destinations.disposition("docs/how-to/preserve-me.md", tmp_path, proposed_sha) == "preserve"
    )

    # conflict — existing file whose hash differs from the proposed hash.
    assert destinations.disposition("docs/how-to/preserve-me.md", tmp_path, "0" * 64) == "conflict"

    # marker-merge — one of the exactly-3 marker-capable paths.
    assert destinations.disposition("AGENTS.md", tmp_path, proposed_sha=None) == "marker-merge"

    # derived-regenerate — a DERIVED_GLOBS path, regardless of existing-file state.
    assert (
        destinations.disposition("docs/reference/inventory.md", tmp_path, proposed_sha=None)
        == "derived-regenerate"
    )

    # human-ratification-required — a constitution-plane path.
    assert (
        destinations.disposition(
            "contracts/harness/adoption/inventory.schema.json", tmp_path, proposed_sha=None
        )
        == "human-ratification-required"
    )


def test_build_manifest_unrecorded_divergence_conflicts_not_updates(tmp_path: Path) -> None:
    rel = "docs/how-to/managed.md"
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    target.write_text("adopted bytes\n", encoding="utf-8")
    existing_sha = destinations._existing_hash(target)
    moved_payload = tmp_path / "moved-payload"
    moved_payload.write_text("moved harness bytes\n", encoding="utf-8")
    moved_sha = destinations._existing_hash(moved_payload)

    inventory = {"target_ref": "target", "included": [{"path": rel, "sha256": existing_sha}]}
    catalog = [{"destination": rel}]

    without_record = destinations.build_manifest(
        inventory, tmp_path, {rel: moved_sha}, catalog=catalog
    )
    with_matching_record = destinations.build_manifest(
        inventory,
        tmp_path,
        {rel: moved_sha},
        catalog=catalog,
        installed=[{"destination": rel, "installed_sha256": existing_sha, "batch_id": "batch-1"}],
    )

    assert without_record["dispositions"] == [{"destination": rel, "disposition": "conflict"}]
    assert with_matching_record["dispositions"] == [{"destination": rel, "disposition": "update"}]


def test_update_is_reachable_when_the_recorded_hash_matches(tmp_path: Path) -> None:
    rel = "docs/how-to/managed.md"
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    target.write_text("adopted bytes\n", encoding="utf-8")
    existing_sha = destinations._existing_hash(target)
    moved_payload = tmp_path / "moved-payload"
    moved_payload.write_text("moved harness bytes\n", encoding="utf-8")

    assert (
        destinations.disposition(
            rel,
            tmp_path,
            destinations._existing_hash(moved_payload),
            existing_sha=existing_sha,
            installed_sha=existing_sha,
        )
        == "update"
    )


def test_preserve_still_wins_over_update(tmp_path: Path) -> None:
    rel = "docs/how-to/managed.md"
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    target.write_text("unchanged bytes\n", encoding="utf-8")
    existing_sha = destinations._existing_hash(target)

    assert (
        destinations.disposition(
            rel,
            tmp_path,
            existing_sha,
            existing_sha=existing_sha,
            installed_sha=existing_sha,
        )
        == "preserve"
    )


def test_target_side_edit_is_conflict_not_update(tmp_path: Path) -> None:
    rel = "docs/how-to/managed.md"
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    target.write_text("human edit\n", encoding="utf-8")
    existing_sha = destinations._existing_hash(target)
    installed_payload = tmp_path / "installed-payload"
    installed_payload.write_text("adopted bytes\n", encoding="utf-8")
    proposed_payload = tmp_path / "proposed-payload"
    proposed_payload.write_text("moved harness bytes\n", encoding="utf-8")

    assert (
        destinations.disposition(
            rel,
            tmp_path,
            destinations._existing_hash(proposed_payload),
            existing_sha=existing_sha,
            installed_sha=destinations._existing_hash(installed_payload),
        )
        == "conflict"
    )


def test_build_manifest_threads_installed_records(tmp_path: Path) -> None:
    rel = "docs/how-to/managed.md"
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    target.write_text("adopted bytes\n", encoding="utf-8")
    existing_sha = destinations._existing_hash(target)
    installed = [{"destination": rel, "installed_sha256": existing_sha, "batch_id": "batch-1"}]
    moved_payload = tmp_path / "moved-payload"
    moved_payload.write_text("moved harness bytes\n", encoding="utf-8")
    inventory = {"target_ref": "target", "included": [{"path": rel, "sha256": existing_sha}]}

    manifest = destinations.build_manifest(
        inventory,
        tmp_path,
        {rel: destinations._existing_hash(moved_payload)},
        catalog=[{"destination": rel}],
        installed=installed,
    )
    assert manifest["dispositions"] == [{"destination": rel, "disposition": "update"}]
    assert manifest["installed"] == installed
    empty_manifest = destinations.build_manifest(
        inventory, tmp_path, {}, catalog=[], installed=[]
    )
    assert "installed" not in empty_manifest


def test_constitution_always_ratification(tmp_path: Path) -> None:
    """Constitution ALWAYS wins over hash-equal/preserve — even when a same-hash file already
    exists at that path in a synthetic target."""
    rel = "contracts/harness/adoption/inventory.schema.json"
    existing = tmp_path / rel
    existing.parent.mkdir(parents=True)
    existing.write_text("some schema content\n", encoding="utf-8")
    proposed_sha = destinations._existing_hash(existing)

    result = destinations.disposition(rel, tmp_path, proposed_sha)
    assert result == "human-ratification-required"


def test_normalize_spec_always_ratification(tmp_path: Path) -> None:
    """libs/normalize-spec.md is constitution-adjacent (D-04 special case) even though it does
    not match CONSTITUTION_GLOBS."""
    result = destinations.disposition("libs/normalize-spec.md", tmp_path, proposed_sha=None)
    assert result == "human-ratification-required"


def test_collision_rule(tmp_minirepo: Path, tmp_path: Path) -> None:
    """Hash-equal existing file -> preserve; hash-different existing file -> conflict, using the
    Plan-02 fixture's widget_a.py/widget_b.py hash-equal pair and widget_a_modified.py's
    hash-different counterpart."""
    widget_a = tmp_minirepo / "widget_a.py"
    widget_b = tmp_minirepo / "widget_b.py"
    widget_a_modified = tmp_minirepo / "widget_a_modified.py"

    proposed_sha_equal = destinations._existing_hash(widget_b)
    assert destinations._existing_hash(widget_a) == proposed_sha_equal

    target_root = tmp_path / "target"
    target_root.mkdir()
    dest = target_root / "widget_a.py"
    dest.write_bytes(widget_a.read_bytes())

    assert destinations.disposition("widget_a.py", target_root, proposed_sha_equal) == "preserve"

    proposed_sha_differ = destinations._existing_hash(widget_a_modified)
    assert destinations.disposition("widget_a.py", target_root, proposed_sha_differ) == "conflict"


def test_marker_capable_set(tmp_path: Path) -> None:
    """MARKER_CAPABLE resolves marker-merge for EXACTLY AGENTS.md, CLAUDE.md,
    .claude/settings.json and nothing else — a nested AGENTS.md is NOT marker-capable."""
    assert destinations.MARKER_CAPABLE == frozenset(
        {"AGENTS.md", "CLAUDE.md", ".claude/settings.json"}
    )

    for rel in ("AGENTS.md", "CLAUDE.md", ".claude/settings.json"):
        assert destinations.disposition(rel, tmp_path, proposed_sha=None) == "marker-merge"

    nested = destinations.disposition("libs/python/AGENTS.md", tmp_path, proposed_sha=None)
    assert nested != "marker-merge"
    assert nested == "create"


def test_gsd_lanes_excluded() -> None:
    """A GSD-owned row is present in excluded[], never in dispositions[]."""
    catalog = destinations.destination_catalog()
    gsd_row = next(row for row in catalog if is_gsd_owned(row["destination"]))
    assert destinations.disposition(gsd_row["destination"], Path("/nonexistent"), None) is None

    inventory = {"target_ref": "unknown"}
    manifest = destinations.build_manifest(inventory, Path("/nonexistent"), {})
    excluded_destinations = {entry["destination"] for entry in manifest["excluded"]}
    dispositioned_destinations = {entry["destination"] for entry in manifest["dispositions"]}

    assert gsd_row["destination"] in excluded_destinations
    assert gsd_row["destination"] not in dispositioned_destinations
    assert all(entry["reason"] == "gsd-owned" for entry in manifest["excluded"])
    assert len(manifest["dispositions"]) + len(manifest["excluded"]) == len(catalog)


def test_harness_proposed_hash_independent_of_target() -> None:
    """CR-01: the proposed content for a destination is THIS harness checkout's own file at that
    path, never anything derived from a scanned target. A destination that has real content in
    this checkout (e.g. root ``pyproject.toml``) yields a stable, non-None hash; a definitely-absent
    path yields ``None`` (the None-when-absent behavior no longer depends on a removed placeholder
    catalog row)."""
    real_hash = destinations.harness_proposed_hash("pyproject.toml")
    assert real_hash is not None
    assert len(real_hash) == 64

    assert (
        destinations.harness_proposed_hash("harness/agents/definitely-not-a-real-agent.md") is None
    )

    hashes = destinations.harness_proposed_hashes()
    assert hashes["pyproject.toml"] == real_hash
    assert "harness/agents/definitely-not-a-real-agent.md" not in hashes


def test_catalog_covers_real_contract_schemas(repo_root: Path) -> None:
    """Live structural check: the catalog's contract-schema rows equal the real, current count of
    ``contracts/**/*.schema.json`` files — never a hardcoded literal, so it never goes stale."""
    live_count = len([p for p in sorted((repo_root / "contracts").rglob("*.schema.json"))])
    catalog = destinations.destination_catalog()
    catalog_count = sum(
        1
        for row in catalog
        if row["destination"].startswith("contracts/")
        and row["destination"].endswith(".schema.json")
    )
    assert catalog_count == live_count
    assert live_count > 0


def test_catalog_covers_real_nested_agents_md(repo_root: Path) -> None:
    """Live structural check: every nested (non-root), non-instance, non-test-fixture AGENTS.md in
    the checkout has a catalog row, and the root AGENTS.md appears exactly once (not double-counted
    by the nested glob). The domain-instance directory is out of scope (GEN-04 core->instance
    independence) — ``instance_prefix`` is built via concatenation so this file never carries the
    forbidden contiguous core->instance path-token substring itself. Test-fixture AGENTS.md files
    (a "tests" path segment, e.g. ``tools/adoption_apply/tests/fixtures/**/AGENTS.md``) are also out
    of scope: 42-REVIEW.md Fix 1 deliberately excludes them from the catalog so an adopted target
    never receives dev-only fixture content."""
    instance_prefix = "examples" + "/"
    live_nested = {
        p.resolve().relative_to(repo_root.resolve()).as_posix()
        for p in sorted(repo_root.rglob("AGENTS.md"))
        if p.is_file() and p.resolve() != (repo_root / "AGENTS.md").resolve()
    }
    live_nested = {d for d in live_nested if not d.startswith(instance_prefix)}
    live_nested = {d for d in live_nested if "tests" not in d.split("/")}
    catalog_destinations = {row["destination"] for row in destinations.destination_catalog()}

    assert live_nested.issubset(catalog_destinations)
    assert live_nested  # sanity: this repo has at least one nested AGENTS.md
    assert sum(1 for d in catalog_destinations if d == "AGENTS.md") == 1


def test_no_fictional_placeholder_destinations() -> None:
    """None of the 10 confirmed-nonexistent placeholder paths from 26-VERIFICATION.md gap 2 appear
    in the rule-derived catalog."""
    catalog_destinations = {row["destination"] for row in destinations.destination_catalog()}
    for placeholder in _PLACEHOLDER_DESTINATIONS:
        assert placeholder not in catalog_destinations


def test_workflow_tasks_excluded() -> None:
    """No catalog row's destination starts with '.workflow/tasks/' (26-CONTEXT.md-cited scoping
    exclusion — Phase 27's concern, not this plan's)."""
    for row in destinations.destination_catalog():
        assert not row["destination"].startswith(".workflow/tasks/")


def test_catalog_excludes_instance_directory() -> None:
    """GEN-04: the catalog never crosses into the top-level domain-instance directory (built via
    concatenation so this guard-compliant test file never carries the forbidden contiguous
    core->instance path-token substring itself)."""
    instance_prefix = "examples" + "/"
    for row in destinations.destination_catalog():
        assert not row["destination"].startswith(instance_prefix)


def test_catalog_deterministic_across_calls() -> None:
    """destination_catalog() called twice in the same process returns identical output — sorted,
    no nondeterministic glob ordering."""
    first = destinations.destination_catalog()
    second = destinations.destination_catalog()
    assert first == second


def test_cr01_conflict_reachable_through_real_cli(tmp_minirepo: Path, tmp_path: Path) -> None:
    """CR-01 non-negotiable: drive the REAL ``cli.main()`` pipeline end-to-end (not a hand-fed
    ``disposition()`` call) against a target whose ``pyproject.toml`` and
    ``.github/workflows/ci.yml`` content genuinely differs from this harness's own template
    content at those same destinations, and assert ``conflict`` actually fires."""
    out_dir = tmp_path / "out"
    rc = cli.main(["--target", str(tmp_minirepo), "--out", str(out_dir)])
    assert rc == 0

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    by_destination = {
        entry["destination"]: entry["disposition"] for entry in manifest["dispositions"]
    }

    # The fixture's pyproject.toml/ci.yml are deliberately unrelated to this harness's own —
    # both must resolve to conflict now that proposed content is harness-sourced, not
    # self-compared against the target's own scanned bytes.
    assert by_destination["pyproject.toml"] == "conflict"
    assert by_destination[".github/workflows/ci.yml"] == "conflict"

    # A sanity control: `conflict` must be reachable at all (the CR-01 bug made it unreachable
    # through the real CLI for every already-present, non-excluded destination).
    assert "conflict" in by_destination.values()


def test_cr01_repro_throwaway_junk_target(tmp_path: Path) -> None:
    """CR-01 exact repro (26-REVIEW.md): a throwaway target whose ``pyproject.toml``/``.gitignore``
    bear no resemblance to the harness template must NOT be silently reported ``preserve`` through
    the real CLI."""
    target = tmp_path / "junk-target"
    target.mkdir()
    (target / "pyproject.toml").write_text(
        '[project]\nname = "totally-unrelated-junk"\nversion = "0.0.0"\n', encoding="utf-8"
    )
    (target / ".gitignore").write_text("*.junk\n", encoding="utf-8")

    out_dir = tmp_path / "out"
    rc = cli.main(["--target", str(target), "--out", str(out_dir)])
    assert rc == 0

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    by_destination = {
        entry["destination"]: entry["disposition"] for entry in manifest["dispositions"]
    }

    assert by_destination["pyproject.toml"] == "conflict"
    assert by_destination[".gitignore"] == "conflict"
