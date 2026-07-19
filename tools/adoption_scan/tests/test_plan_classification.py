"""Task 2: plan.py — evidence ladder, D-05 question records, relationship candidates."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.adoption_scan import plan, scan

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RELATIONSHIP_SCHEMA = json.loads(
    (_REPO_ROOT / "contracts" / "harness" / "topology" / "relationship.schema.json").read_text(
        encoding="utf-8"
    )
)


def _evidence_ref(path: str = "widget_a.py") -> dict:
    return {"path": path, "sha256": "a" * 64, "size": 10}


def test_every_entry_classified(tmp_minirepo: Path) -> None:
    inventory = scan.build_inventory(tmp_minirepo)
    proposals = plan.classify(inventory)
    assert proposals, "the fixture must produce at least one proposal"
    for proposal in proposals:
        assert proposal["classification"] in ("observed", "inferred", "unknown")

    built = plan.build_plan(inventory)
    for question in built["questions"]:
        assert question["classification"] == "unknown"


def test_unresolved_ownership_becomes_question() -> None:
    """A relationship proposal with an unresolved authority (D-05 '?' sentinel) yields a
    relationship-authority question carrying a schema-incomplete candidate, and NEVER appears in
    generate_relationship_candidates()'s output with an invented authority."""
    proposals = [
        {
            "id": "relationship/orders",
            "kind": "relationship",
            "classification": "unknown",
            "target": "orders::?->worker",
            "evidence": [_evidence_ref("services/worker/orders_consumer.py")],
        }
    ]
    inventory = {"target_ref": "unknown"}

    candidates = plan.generate_relationship_candidates(inventory, proposals)
    assert candidates == []

    questions = plan.generate_questions(inventory, proposals)
    assert len(questions) == 1
    question = questions[0]
    assert question["kind"] == "relationship-authority"
    assert question["classification"] == "unknown"
    candidate = question["candidate"]
    assert candidate["record_kind"] == "relationshipCandidate"
    assert "authority" not in candidate["record"]
    assert candidate["record"]["dependents"] == ["worker"]

    # Never satisfies the ratified relationship shape (structurally incomplete — D-05).
    validator = Draft202012Validator(_RELATIONSHIP_SCHEMA)
    errors = list(validator.iter_errors(candidate["record"]))
    assert errors, "a candidate record must NEVER validate against the ratified relationship schema"


def test_question_shape_and_ordering() -> None:
    proposals = [
        {
            "id": "docs-destination/README",
            "kind": "docs-destination",
            "classification": "unknown",
            "target": "README",
            "evidence": [_evidence_ref("README")],
        },
        {
            "id": "test-command/tests",
            "kind": "test-command",
            "classification": "unknown",
            "target": "tests",
            "evidence": [_evidence_ref("tests/test_widget.py")],
        },
        {
            "id": "agents-boundary/AGENTS.md",
            "kind": "agents-boundary",
            "classification": "unknown",
            "target": "AGENTS.md",
            "evidence": [_evidence_ref("AGENTS.md")],
        },
    ]
    inventory = {"target_ref": "unknown"}

    first = plan.generate_questions(inventory, proposals)
    second = plan.generate_questions(inventory, proposals)

    ids_first = [q["id"] for q in first]
    ids_second = [q["id"] for q in second]
    assert ids_first == ids_second, "question ids must be stable across independent calls"

    for question in first:
        assert question["id"]
        assert question["target"]
        assert question["evidence"]

    keys = [(q.get("group", ""), q["kind"], q["target"], q["id"]) for q in first]
    assert keys == sorted(keys)


def test_relationship_candidates_validate() -> None:
    proposals = [
        {
            "id": "relationship/orders-observed",
            "kind": "relationship",
            "classification": "observed",
            "target": "orders::serviceA->serviceB",
            "evidence": [_evidence_ref("services/serviceA/orders.py")],
        },
        {
            "id": "relationship/orders-inferred",
            "kind": "relationship",
            "classification": "inferred",
            "target": "billing::serviceC->serviceD",
            "evidence": [_evidence_ref("services/serviceC/billing.py")],
        },
        {
            "id": "relationship/orders-unknown",
            "kind": "relationship",
            "classification": "unknown",
            "target": "shipping::?->serviceE",
            "evidence": [_evidence_ref("services/serviceE/shipping.py")],
        },
    ]
    inventory = {"target_ref": "unknown"}

    candidates = plan.generate_relationship_candidates(inventory, proposals)
    assert len(candidates) == 2

    validator = Draft202012Validator(_RELATIONSHIP_SCHEMA)
    for candidate in candidates:
        errors = list(validator.iter_errors(candidate))
        assert errors == [], f"{candidate!r} must validate: {errors}"
        assert candidate["id"].startswith("adoption/")


def test_classify_over_fixture_validates_shape(tmp_minirepo: Path) -> None:
    """build_plan() over the real D-06 fixture never invents a relationship (no relationship
    signal exists in the inventory), and every proposal carries a valid classification."""
    inventory = scan.build_inventory(tmp_minirepo)
    built = plan.build_plan(inventory)
    assert built["relationships"] == []
    assert built["target_ref"] == inventory["target_ref"]
    ids = [p["id"] for p in built["proposals"]]
    assert ids == sorted(ids)
