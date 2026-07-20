"""DOCSUP-06 adversarial-input table for the five human-doc drafting exclusions.

The phase's anti-pattern fence: the table is authored FIRST and shown RED against pre-fix code FOR
THE STATED REASON — here, ``tools/docs_guard/exclusions.py`` does not exist yet, so collection fails
with ``ModuleNotFoundError``. The verbatim first failure line is recorded in ``29-01-SUMMARY.md``.

Three load-bearing groups, and none of them substitutes for another:

``EXCLUSION_CASES``
    One row per (class, spelling). Every spelling variant that 27.1's CR-01 used to bypass
    ``refuse_if_constitution`` — ``./contracts/x``, ``CONTRACTS/x``, ``docs/../contracts/x`` — is a
    row here, because the classifier is a NEW path-decision surface and CR-01 replays on new
    surfaces unless each one pins the variants itself. Includes the two negative controls (a guard
    that refuses everything passes every refusal row) and the escape rows, whose expectation is a
    RAISED ``PathEscapeError`` and explicitly NOT ``None``: answering "no exclusion applies" to a
    path leaving the repo is CR-01 in its most literal form.

The IDENTITY assertions
    ``exclusions.CONSTITUTION_GLOBS is contract_guard.CONSTITUTION_GLOBS`` and its two siblings.
    ``is``, not ``==``: a monkeypatch proof shows only that the function READS a module attribute,
    and a locally RETYPED list keeps every monkeypatch green while "delete a glob at its home and
    this file fails" silently becomes false. That is Phase 28's CR-02 verbatim; identity is what
    makes the claim true.

The THREE per-class DELETION PROOFS
    Each patches the attribute ITS OWN class actually reads. The ADR proof MUST patch ``ADR_GLOBS``
    and not ``CONSTITUTION_GLOBS``: ``registry.py:55`` binds ``ADR_GLOBS`` at IMPORT time by slicing
    ``CONSTITUTION_GLOBS``, so emptying the latter at runtime leaves the ADR list fully populated
    and a single combined proof could not pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.adoption_apply.apply import PathEscapeError
from tools.adoption_scan import destinations
from tools.docs_guard import exclusions, registry
from tools.hooks import contract_guard

# Rows whose expectation is this sentinel must RAISE PathEscapeError. It is deliberately not
# ``None``: an escape is malformed input, never "no exclusion applies".
RAISES = PathEscapeError

# (case_id, target, expected_reason) — expected is a reason string, ``None``, or ``RAISES``.
EXCLUSION_CASES: list[tuple[str, str, object]] = [
    # --- class 1: contracts (constitution plane), with all four CR-01 spellings ---
    (
        "contracts-plain",
        "contracts/harness/docs/doc-dependencies.schema.json",
        exclusions.REASON_CONSTITUTION,
    ),
    (
        "contracts-dot-slash",
        "./contracts/harness/docs/doc-dependencies.schema.json",
        exclusions.REASON_CONSTITUTION,
    ),
    (
        "contracts-upper",
        "CONTRACTS/harness/docs/doc-dependencies.schema.json",
        exclusions.REASON_CONSTITUTION,
    ),
    # Load-bearing: a `..` that RESOLVES back inside the root is a legal spelling of a constitution
    # path, so `..` must not be pre-rejected the way `refuse_unsafe_destination` (a WRITE guard)
    # rejects it. A classifier returns `str | None`; it cannot both raise and classify.
    (
        "contracts-dotdot-reentrant",
        "docs/../contracts/harness/docs/doc-dependencies.schema.json",
        exclusions.REASON_CONSTITUTION,
    ),
    # --- class 2: golden (constitution plane) ---
    ("golden-plain", "golden/harness/baseline.verified.tsv", exclusions.REASON_CONSTITUTION),
    # --- class 3: accepted ADR — a DISTINCT reason, asserted below to differ from class 1/2 ---
    (
        "adr-plain",
        "docs/adr/0009-contract-relationship-graph-model.md",
        exclusions.REASON_ACCEPTED_ADR,
    ),
    (
        "adr-dot-segment",
        "docs/adr/./0009-contract-relationship-graph-model.md",
        exclusions.REASON_ACCEPTED_ADR,
    ),
    # --- class 4: derived plane, including THIS phase's own emitted twins ---
    ("derived-docs-reference", "docs/reference/manifest.md", exclusions.REASON_DERIVED),
    ("derived-memory", ".memory/derived/contracts-index.md", exclusions.REASON_DERIVED),
    ("derived-opencode-twin", ".opencode/skill/docs-upkeep/SKILL.md", exclusions.REASON_DERIVED),
    ("derived-claude-twin", ".claude/commands/docs-update.md", exclusions.REASON_DERIVED),
    # --- class 5: escapes — NOT None ---
    ("escape-dotdot", "../../etc/passwd", RAISES),
    ("escape-absolute", "/etc/passwd", RAISES),
    # --- class 6: negative controls — the function is not a blanket refusal ---
    ("allowed-how-to", "docs/how-to/task-lifecycle.md", None),
    ("allowed-harness-source", "harness/skills/brownfield-adoption/SKILL.md", None),
]

_CONSTITUTION_ROWS = ("contracts-", "golden-")
_DERIVED_ROWS = ("derived-",)
_ADR_ROWS = ("adr-",)


def _rows(prefixes: tuple[str, ...]) -> list[tuple[str, str, object]]:
    return [row for row in EXCLUSION_CASES if row[0].startswith(prefixes)]


@pytest.mark.parametrize(
    ("target", "expected"),
    [pytest.param(target, expected, id=case_id) for case_id, target, expected in EXCLUSION_CASES],
)
def test_exclusion_reason_table(target: str, expected: object) -> None:
    if expected is RAISES:
        # Explicit: the escape classes' expectation is NOT None.
        assert expected is not None
        with pytest.raises(PathEscapeError):
            exclusions.exclusion_reason(target)
        return
    assert exclusions.exclusion_reason(target) == expected


def test_accepted_adr_reason_is_distinct_from_constitution() -> None:
    """Different remediation (supersede via /adr, never an in-place edit) => different reason."""
    assert exclusions.REASON_ACCEPTED_ADR != exclusions.REASON_CONSTITUTION
    assert exclusions.REASON_ACCEPTED_ADR != exclusions.REASON_DERIVED
    assert (
        exclusions.exclusion_reason("docs/adr/0009-contract-relationship-graph-model.md")
        == exclusions.REASON_ACCEPTED_ADR
    )


def test_symlink_resolving_onto_constitution_plane(tmp_path: Path) -> None:
    """27.1 SC-1's symlink class: the LINK's spelling is innocent; its resolution is not."""
    root = tmp_path / "repo"
    (root / "contracts").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "contracts" / "widget.schema.json").write_text("{}\n", encoding="utf-8")
    link = root / "docs" / "innocent.md"
    link.symlink_to(root / "contracts" / "widget.schema.json")

    assert exclusions.exclusion_reason("docs/innocent.md", root=root) == (
        exclusions.REASON_CONSTITUTION
    )


# --------------------------------------------------------------------------------------------
# The primary control: the glob lists are the very objects their homes export, not equal copies.
# --------------------------------------------------------------------------------------------


def test_constitution_globs_is_the_exported_object() -> None:
    assert exclusions.CONSTITUTION_GLOBS is contract_guard.CONSTITUTION_GLOBS


def test_derived_globs_is_the_exported_object() -> None:
    assert exclusions.DERIVED_GLOBS is destinations.DERIVED_GLOBS


def test_adr_globs_is_the_exported_object() -> None:
    assert exclusions.ADR_GLOBS is registry.ADR_GLOBS


# --------------------------------------------------------------------------------------------
# Deletion proofs — one per class, each patching the attribute its own class actually reads.
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        pytest.param(target, expected, id=case_id)
        for case_id, target, expected in _rows(_CONSTITUTION_ROWS)
    ],
)
def test_deleting_constitution_globs_unrefuses_those_rows(
    monkeypatch: pytest.MonkeyPatch, target: str, expected: object
) -> None:
    assert expected is exclusions.REASON_CONSTITUTION
    monkeypatch.setattr(exclusions, "CONSTITUTION_GLOBS", [])
    assert exclusions.exclusion_reason(target) is None


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        pytest.param(target, expected, id=case_id)
        for case_id, target, expected in _rows(_DERIVED_ROWS)
    ],
)
def test_deleting_derived_globs_unrefuses_those_rows(
    monkeypatch: pytest.MonkeyPatch, target: str, expected: object
) -> None:
    assert expected is exclusions.REASON_DERIVED
    monkeypatch.setattr(exclusions, "DERIVED_GLOBS", [])
    assert exclusions.exclusion_reason(target) is None


@pytest.mark.parametrize(
    ("target", "expected"),
    [pytest.param(target, expected, id=case_id) for case_id, target, expected in _rows(_ADR_ROWS)],
)
def test_deleting_adr_globs_stops_the_accepted_adr_reason(
    monkeypatch: pytest.MonkeyPatch, target: str, expected: object
) -> None:
    """Patches ADR_GLOBS, NOT CONSTITUTION_GLOBS — registry.py:55 binds ADR_GLOBS at import time."""
    assert expected is exclusions.REASON_ACCEPTED_ADR
    monkeypatch.setattr(exclusions, "ADR_GLOBS", [])
    assert exclusions.exclusion_reason(target) != exclusions.REASON_ACCEPTED_ADR
