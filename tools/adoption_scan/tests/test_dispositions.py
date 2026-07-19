"""Task 1: destinations.py — totality over the 40-row catalog + each-of-6-dispositions-reachable
+ marker-capable-set-is-exactly-3 + constitution-always-wins + hash-equal/hash-differ collision
rule + GSD-owned exclusion."""

from __future__ import annotations

import json
from pathlib import Path

from tools.adoption_scan import cli, destinations


def test_total(tmp_path: Path) -> None:
    """Every non-excluded row resolves to a non-None value from the 6-value enum; row 40
    (GSD-owned) resolves to None (excluded) — 39 dispositioned + 1 excluded."""
    catalog = destinations.destination_catalog()
    assert len(catalog) == 40

    dispositioned = 0
    excluded = 0
    for row in catalog:
        result = destinations.disposition(row["destination"], tmp_path, proposed_sha=None)
        if result is None:
            excluded += 1
            continue
        assert result in destinations.DISPOSITION_ENUM
        dispositioned += 1

    assert dispositioned == 39
    assert excluded == 1


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
    """The GSD-owned row is present in excluded[], never in dispositions[]."""
    catalog = destinations.destination_catalog()
    gsd_row = next(row for row in catalog if row["num"] == 40)
    assert destinations.disposition(gsd_row["destination"], Path("/nonexistent"), None) is None

    inventory = {"target_ref": "unknown"}
    manifest = destinations.build_manifest(inventory, Path("/nonexistent"), {})
    excluded_destinations = {entry["destination"] for entry in manifest["excluded"]}
    dispositioned_destinations = {entry["destination"] for entry in manifest["dispositions"]}

    assert gsd_row["destination"] in excluded_destinations
    assert gsd_row["destination"] not in dispositioned_destinations
    assert all(entry["reason"] == "gsd-owned" for entry in manifest["excluded"])
    assert len(manifest["dispositions"]) == 39
    assert len(manifest["excluded"]) == 1


def test_harness_proposed_hash_independent_of_target() -> None:
    """CR-01: the proposed content for a destination is THIS harness checkout's own file at that
    path, never anything derived from a scanned target. A destination that has real content in
    this checkout (e.g. root ``pyproject.toml``) yields a stable, non-None hash; a catalog
    placeholder row with no shippable template content (e.g. ``harness/agents/widget-engineer.md``,
    a fixture stand-in) yields ``None``."""
    real_hash = destinations.harness_proposed_hash("pyproject.toml")
    assert real_hash is not None
    assert len(real_hash) == 64

    assert destinations.harness_proposed_hash("harness/agents/widget-engineer.md") is None
    assert destinations.harness_proposed_hash(".workflow/tasks/T-0001/task.json") is None

    hashes = destinations.harness_proposed_hashes()
    assert hashes["pyproject.toml"] == real_hash
    assert "harness/agents/widget-engineer.md" not in hashes


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
