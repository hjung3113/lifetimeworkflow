"""One assert per exclusion class (D-06) — exact reason string, no content echoed (D-10)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.adoption_scan import scan


@pytest.mark.parametrize(
    ("rel_path", "expected_reason"),
    [
        (".env", "secret-path"),
        ("sink/secret_config.py", "secret-content"),
        ("binary.dat", "binary"),
        ("node_modules/pkg/index.js", "vendored"),
        ("generated.py", "generated"),
        ("assets/oversized.dat", "size-capped"),
        ("backups/repo-dump.txt", "source-dump"),
        ("notes/full-context.txt", "source-dump"),
        ("escape", "symlink-escape"),
    ],
)
def test_exclusion_reason(tmp_minirepo: Path, rel_path: str, expected_reason: str) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    excluded = {entry["path"]: entry for entry in inventory["excluded"]}
    assert rel_path in excluded, f"expected {rel_path!r} to be excluded, got {sorted(excluded)}"
    assert excluded[rel_path]["excluded"] == expected_reason


def test_secret_content_excluded_and_not_echoed(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    excluded = {entry["path"]: entry for entry in inventory["excluded"]}
    entry = excluded["sink/secret_config.py"]
    assert set(entry.keys()) == {"path", "size", "excluded"}
    assert entry["excluded"] == "secret-content"
    serialized = json.dumps(inventory)
    assert "AKIA" not in serialized, "matched secret bytes must never appear in the inventory"


def test_derived_marker_does_not_false_positive_on_ordinary_prose(tmp_path: Path) -> None:
    """WR-02 (26-REVIEW.md): "derived —" alone over-matched ordinary human-authored prose using
    that exact phrasing (e.g. this repo's own two-plane-memory SKILL.md). The marker must now be
    anchored to this repo's actual generator convention ("DERIVED — do not hand-edit ...") so
    ordinary prose is NOT misclassified as generated."""
    base = tmp_path
    prose = base / "prose.md"
    prose.write_text(
        "**Gitignored-derived — `.memory/derived/pointer-index.json`** is regenerated on demand.\n",
        encoding="utf-8",
    )
    exclusion = scan.classify_exclusions(prose, base=base, max_bytes=scan.DEFAULT_MAX_FILE_BYTES)
    assert exclusion is None, f"ordinary prose must not be excluded as generated, got {exclusion}"


def test_derived_marker_still_catches_real_generated_headers(tmp_path: Path) -> None:
    """The narrowed marker still catches every real generator convention in this repo (D-06: must
    not regress detection of actually-generated content)."""
    base = tmp_path
    for name, header in (
        (
            "pointer_index.json",
            "DERIVED — do not hand-edit (tools/memory_regen/pointer_index.py)\n",
        ),
        ("repo_map.md", "DERIVED — do not hand-edit (tools/memory_regen/repo_map.py)\n"),
        (
            "relationship.md",
            "DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync\n",
        ),
    ):
        path = base / name
        path.write_text(header, encoding="utf-8")
        exclusion = scan.classify_exclusions(path, base=base, max_bytes=scan.DEFAULT_MAX_FILE_BYTES)
        assert exclusion is not None and exclusion["excluded"] == "generated", (
            f"{name!r} carrying a real DERIVED_HEADER must still be excluded as generated, "
            f"got {exclusion}"
        )


def test_no_spurious_exclusions(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    included_paths = {entry["path"] for entry in inventory["included"]}
    expected_included = {
        "widget_a.py",
        "widget_b.py",
        "widget_a_modified.py",
        "README",
        "pyproject.toml",
        ".github/workflows/ci.yml",
        "tests/test_widget.py",
        "docs/adr/0001-decision.md",
        "AGENTS.md",
    }
    assert expected_included <= included_paths

    excluded_paths = {entry["path"] for entry in inventory["excluded"]}
    assert included_paths.isdisjoint(excluded_paths)


def test_ci_yml_false_positive_closed(repo_root: Path) -> None:
    """SC-1: this repo's own .github/workflows/ci.yml no longer classifies as secret-content.

    Red-green proof: the OLD generic pattern DOES match the real false-positive line (proving the
    bug is real, not a fixture artifact), while the LIVE (currently-committed) ``_secret_pattern()``
    must not classify the file as ``excluded: "secret-content"`` in the inventory. The tightened
    pattern landed in 26.1 (commit d6e9054), so both halves are green and stay green; this test is
    the regression guard, not a pending red.
    """
    ci_yml = repo_root / ".github" / "workflows" / "ci.yml"
    text = ci_yml.read_text(encoding="utf-8")

    # IN-02 (26.1-REVIEW.md): this is a hand-duplicated copy of the pre-26.1 pattern with no
    # git-history link of its own; provenance is commit d6e9054 (26.1's tightening fix).
    old_pattern = re.compile(
        r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*[^\s]+", re.IGNORECASE
    )
    assert old_pattern.search(text), "red check: old pattern must match (proves this is the bug)"

    inventory = scan.build_inventory(repo_root)
    secret_excluded_paths = {
        entry["path"] for entry in inventory["excluded"] if entry["excluded"] == "secret-content"
    }
    assert ".github/workflows/ci.yml" not in secret_excluded_paths, (
        "SC-1: ci.yml must not be excluded as secret-content"
    )


@pytest.mark.parametrize(
    "fixture_value",
    [
        "AKIA" + "ABCDEFGHIJKLMNOP",
        "ghp_" + "A" * 20,
        "sk-" + "B" * 20,
        "xoxb-" + "1" * 10 + "-" + "a" * 10,
        "-----BEGIN " + "RSA PRIVATE KEY-----",
        "eyJ" + "C" * 12 + "." + "D" * 8 + "." + "E" * 8,
        "Authorization: Bearer " + "F" * 20,
    ],
)
def test_secret_shape_still_matches(fixture_value: str) -> None:
    """SC-2: every one of the 7 unchanged named secret shapes is still matched."""
    assert scan._secret_pattern().search(fixture_value), fixture_value


def test_secret_patterns_1_case_diversity_survives_ignorecase() -> None:
    """CR-01: [A-Z]/[a-z] lookaheads must not degrade to 'any letter' under re.IGNORECASE.

    A single-case (all-uppercase), digit-less, 20-char value must NOT match secret_patterns[1]
    in either live consumer function, both before and after Task 2's fix. This is a regression
    guard: an unscoped 2-of-3 relaxation would incorrectly let a single letter alone satisfy the
    disjunction under IGNORECASE if the (?-i:...) scoping is forgotten.
    """
    assign = "pass" + "word"
    value_all_upper = "".join(["ABCDEFGHIJKLMNOPQRST"])  # single-case, digit-less, 20 chars
    assert scan._secret_pattern().search(assign + ": " + value_all_upper) is None


@pytest.mark.parametrize(
    "fixture_value",
    [
        pytest.param(
            "".join(["AbCdEfGhIjKlMnOpQrSt"]),
            id="mixed_case_digit_less-red_before_task2-WR01_relaxation_proof",
        ),
        pytest.param(
            "".join(["ABCDEFGHIJKLMNO", "12345"]),
            id="uppercase_plus_digit-continuity_guard",
        ),
        pytest.param(
            "".join(["abcdefghijklmno", "12345"]),
            id="lowercase_plus_digit-continuity_guard",
        ),
    ],
)
def test_secret_patterns_1_two_of_three_classes_matches(fixture_value: str) -> None:
    """SC-2: 2-of-3 charset-class disposition, proven against the live consumer function.

    The mixed-case-digit-less row is the genuine red-before/green-after case: it does NOT match
    the CURRENT (unedited) pattern (which requires a digit unconditionally), proving WR-01's
    relaxation is not already accidentally true — this row is expected to FAIL until Task 2
    lands the fix. The two digit-bearing rows already match under the current letter+digit
    collapse and must continue to match after Task 2 (continuity guard).
    """
    sec = "se" + "cret"
    assert scan._secret_pattern().search(sec + ": " + fixture_value), fixture_value


@pytest.mark.parametrize(
    "fixture_value",
    [
        "".join(["correcthorsebattery", "staple"]),  # all-lowercase digit-less, 25 chars
        "9" * 22,  # all-numeric, no letters
        "".join(["ABCDEFGHIJKLMNOPQRST"]),  # all-uppercase digit-less, 20 chars
    ],
)
def test_secret_patterns_1_single_class_digit_less_remains_excluded(fixture_value: str) -> None:
    """SC-2: single-case-only and all-numeric digit-less values remain an accepted, documented
    residual gap — never matched, both before and after Task 2 (no transition expected)."""
    assign = "pass" + "word"
    assert scan._secret_pattern().search(assign + ": " + fixture_value) is None


def test_secret_patterns_1_branch_attribution() -> None:
    """SC-3/D-04: pin that the mixed-case-digit-less match comes from registry index 1, not one
    of the other 7 dedicated-shape branches — a structural attribution check, not a substitute
    for the live-consumer behavior assertions above."""
    branch_only = re.compile(scan.SECRET_CONTENT_PATTERNS[1], re.IGNORECASE)
    sec = "se" + "cret"
    fixture_value = sec + ": " + "".join(["ABCDEFGHIJKLMNO", "12345"])
    assert scan._secret_pattern().search(fixture_value)
    assert branch_only.search(fixture_value)


# ---------------------------------------------------------------------------------------------
# OBS-D-01 (51-BASELINE-EVIDENCE.md) — purpose 2; contract value ratified by 52-01 (D-20):
# pnpm workspace member scoping wired into build_inventory.
# ---------------------------------------------------------------------------------------------


def test_pnpm_workspace_exactly_five_members(tmp_pnpm_workspace: Path) -> None:
    """Against tmp_pnpm_workspace, manifests and candidate_process_boundaries contain exactly
    the five declared members (root + 4) — a set-equality assertion against the LITERAL five
    expected directory strings, not merely a count, since a count-only check would pass even if
    scoping picked the wrong five directories."""
    inventory = scan.build_inventory(tmp_pnpm_workspace)

    manifest_paths = {entry["path"] for entry in inventory["manifests"]}
    assert manifest_paths == {
        "package.json",
        "apps/widget-app/package.json",
        "apps/widget-service/package.json",
        "packages/widget-shared/package.json",
        "packages/widget-ui/package.json",
    }

    boundary_targets = {entry["target"] for entry in inventory["candidate_process_boundaries"]}
    assert boundary_targets == {
        ".",
        "apps/widget-app",
        "apps/widget-service",
        "packages/widget-shared",
        "packages/widget-ui",
    }


def test_pnpm_non_member_manifest_excluded_and_absent_from_included_and_manifests(
    tmp_pnpm_workspace: Path,
) -> None:
    """The one non-member manifest (docs/design-prototype/package.json) is excluded with reason
    non-workspace-member, and is absent from BOTH included AND manifests. Reverting the scan.py
    branch (this test's own mutation check, observed RED then reverted — see SUMMARY) must red
    this test."""
    inventory = scan.build_inventory(tmp_pnpm_workspace)

    non_member_path = "docs/design-prototype/package.json"
    excluded_by_path = {entry["path"]: entry for entry in inventory["excluded"]}
    assert non_member_path in excluded_by_path
    assert excluded_by_path[non_member_path]["excluded"] == "non-workspace-member"

    included_paths = {entry["path"] for entry in inventory["included"]}
    manifest_paths = {entry["path"] for entry in inventory["manifests"]}
    assert non_member_path not in included_paths
    assert non_member_path not in manifest_paths


def test_pnpm_no_workspace_manifest_byte_identical_to_precomputed_digest(
    tmp_minirepo: Path,
) -> None:
    """D-10: tmp_minirepo (no pnpm-workspace.yaml) produces byte-identical output to the
    pre-Task-3 baseline. The digest below was captured from the SAME build_inventory() against
    the SAME tmp_minirepo fixture immediately after Task 3's wiring landed (with the D-10
    additive branch confirmed inert for this fixture) — a regression in this test would mean a
    FUTURE change silently altered the no-workspace-manifest path, not that Task 3 itself moved
    it. No `non-workspace-member` entry appears anywhere in the inventory."""
    inventory = scan.build_inventory(tmp_minirepo)
    dumped = scan._dump(inventory)
    assert hashlib.sha256(dumped).hexdigest() == (
        "00d6d50a317d26817863df7075a0217a5080d415504d16eaff8e345f8b340e04"
    )
    assert "non-workspace-member" not in dumped.decode("utf-8")


def test_pnpm_security_precedence_preserved_over_non_workspace_member(tmp_path: Path) -> None:
    """T-52-06: classify_exclusions runs FIRST and unchanged. A manifest that is BOTH outside the
    declared globs AND secret-path (a `.env`-adjacent glob match is not applicable to
    package.json, so this uses the vendored-segment case instead, which is easy to construct and
    exercises the same ordering) keeps its ORIGINAL exclusion reason, never
    non-workspace-member. Swapping the branch order in scan.py must red this test."""
    root = tmp_path / "precedence-workspace"
    root.mkdir()
    (root / "pnpm-workspace.yaml").write_text('packages:\n  - "apps/*"\n', encoding="utf-8")
    (root / "package.json").write_text('{"name": "root"}\n', encoding="utf-8")

    # A manifest that is BOTH a non-member (outside apps/*, packages/*) AND vendored.
    vendored_dir = root / "node_modules" / "design-prototype"
    vendored_dir.mkdir(parents=True)
    (vendored_dir / "package.json").write_text('{"name": "design-prototype"}\n', encoding="utf-8")

    inventory = scan.build_inventory(root)
    excluded_by_path = {entry["path"]: entry for entry in inventory["excluded"]}
    entry = excluded_by_path["node_modules/design-prototype/package.json"]
    assert entry["excluded"] == "vendored", (
        "a manifest that is both vendored AND a non-member must keep its ORIGINAL "
        f"exclusion reason, got {entry['excluded']!r}"
    )


def test_pnpm_escaping_glob_contributes_no_members_and_records_nothing_outside_target(
    tmp_path: Path,
) -> None:
    """A pnpm-workspace.yaml whose globs escape the target root (e.g. "../outside/*") produces
    no members from that glob and never reads or records a path outside the target root — the
    escaping glob simply never matches any in-target manifest directory, so scoping degrades to
    treating every manifest as a non-member of that one glob (any OTHER valid glob in the same
    file still works normally)."""
    root = tmp_path / "escaping-workspace"
    root.mkdir()
    (root / "pnpm-workspace.yaml").write_text(
        'packages:\n  - "../outside/*"\n  - "packages/*"\n', encoding="utf-8"
    )
    (root / "package.json").write_text('{"name": "root"}\n', encoding="utf-8")
    member_dir = root / "packages" / "widget-shared"
    member_dir.mkdir(parents=True)
    (member_dir / "package.json").write_text('{"name": "widget-shared"}\n', encoding="utf-8")

    # A sibling directory OUTSIDE the target root that an escaping glob COULD (if mishandled)
    # try to reach — never created inside `root`, so if scan.py ever recorded a path under it,
    # that would prove the confinement guard failed.
    outside_dir = tmp_path / "outside" / "widget-leaked"
    outside_dir.mkdir(parents=True)
    (outside_dir / "package.json").write_text('{"name": "widget-leaked"}\n', encoding="utf-8")

    inventory = scan.build_inventory(root)
    all_paths = {entry["path"] for entry in inventory["included"]} | {
        entry["path"] for entry in inventory["excluded"]
    }
    assert not any("outside" in path for path in all_paths), (
        f"no path outside the target root may ever be recorded, got {sorted(all_paths)}"
    )
    manifest_paths = {entry["path"] for entry in inventory["manifests"]}
    assert manifest_paths == {"package.json", "packages/widget-shared/package.json"}


def test_pnpm_non_manifest_files_under_non_member_dir_stay_included(
    tmp_pnpm_workspace: Path,
) -> None:
    """Only the manifest itself is scoped out of a non-member directory — an ordinary
    non-manifest file under that same directory (docs/design-prototype/README.md) stays
    INCLUDED and hashed."""
    inventory = scan.build_inventory(tmp_pnpm_workspace)
    included_paths = {entry["path"] for entry in inventory["included"]}
    assert "docs/design-prototype/README.md" in included_paths


def test_pnpm_non_workspace_member_reason_validates_against_ratified_schema(
    tmp_pnpm_workspace: Path, repo_root: Path
) -> None:
    """D-20: the `non-workspace-member` reason this plan emits is a REAL instance validated
    against Plan 01's ratified `inventory.schema.json` enum — not merely asserted as a Python
    string. This is the phase's real instance-conformance evidence for the D-20 enum value."""
    schema_path = repo_root / "contracts" / "harness" / "adoption" / "inventory.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    inventory = scan.build_inventory(tmp_pnpm_workspace)

    reasons = {entry["excluded"] for entry in inventory["excluded"]}
    assert "non-workspace-member" in reasons, "fixture must actually exercise the new reason"

    errors = list(Draft202012Validator(schema).iter_errors(inventory))
    assert not errors, [error.message for error in errors]
