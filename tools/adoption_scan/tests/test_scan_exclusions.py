"""One assert per exclusion class (D-06) — exact reason string, no content echoed (D-10)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

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
    must not classify the file as ``excluded: "secret-content"`` in the inventory. Until the
    gate-registry.json fix lands, this second half of the assertion is expected to FAIL — that is
    the intended red state for this task.
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
