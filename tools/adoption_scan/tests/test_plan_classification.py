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
_INVENTORY_SCHEMA = json.loads(
    (_REPO_ROOT / "contracts" / "harness" / "adoption" / "inventory.schema.json").read_text(
        encoding="utf-8"
    )
)
_PLAN_SCHEMA = json.loads(
    (_REPO_ROOT / "contracts" / "harness" / "adoption" / "plan.schema.json").read_text(
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


def test_nested_agents_md_gets_its_own_agents_boundary_proposal() -> None:
    """WR-01 (26-REVIEW.md): plan.classify() resolves ``agents-boundary`` by AGENTS.md FILENAME
    (not exact-string-equal-to-the-literal-"AGENTS.md"), so a nested surfaceRecord (target =
    "libs/python/AGENTS.md", as detect.py now emits per-path) still classifies as
    agents-boundary — not docs-destination — and gets its own question, distinct from root."""
    inventory = {
        "target_ref": "unknown",
        "manifests": [],
        "candidate_process_boundaries": [],
        "documentation_surfaces": [
            {
                "target": "AGENTS.md",
                "classification": "observed",
                "evidence": [_evidence_ref("AGENTS.md")],
            },
            {
                "target": "libs/python/AGENTS.md",
                "classification": "observed",
                "evidence": [_evidence_ref("libs/python/AGENTS.md")],
            },
        ],
        "ci_surfaces": [],
        "test_surfaces": [],
        "languages": [],
    }

    built = plan.build_plan(inventory)
    agents_proposals = {
        p["target"]: p for p in built["proposals"] if p["kind"] == "agents-boundary"
    }
    assert set(agents_proposals) == {"AGENTS.md", "libs/python/AGENTS.md"}

    agents_questions = {
        q["target"]: q for q in built["questions"] if q["kind"] == "agents-boundary"
    }
    assert set(agents_questions) == {"AGENTS.md", "libs/python/AGENTS.md"}
    # Distinct, content-derived ids — never collapsed into one question for both files.
    assert agents_questions["AGENTS.md"]["id"] != agents_questions["libs/python/AGENTS.md"]["id"]


def test_codeowners_ownership_question_fires() -> None:
    """The codeowners-ownership question kind — structurally wired since Plan 26-03 but
    permanently unreachable until this plan fed it a real inventory signal — actually fires on a
    codeowners_surfaces entry."""
    inventory = {
        "target_ref": "unknown",
        "codeowners_surfaces": [
            {
                "target": ".github/CODEOWNERS",
                "classification": "observed",
                "evidence": [_evidence_ref(".github/CODEOWNERS")],
            }
        ],
    }

    built = plan.build_plan(inventory)

    codeowners_proposals = [p for p in built["proposals"] if p["kind"] == "codeowners"]
    assert len(codeowners_proposals) == 1
    assert codeowners_proposals[0]["classification"] == "unknown"

    codeowners_questions = [q for q in built["questions"] if q["kind"] == "codeowners-ownership"]
    assert len(codeowners_questions) == 1


def test_contract_candidate_question_fires() -> None:
    """WR-05 (26-REVIEW.md): the contract-candidate proposal/question kind — structurally wired
    since Plan 26-01/03 but permanently unreachable until classify() walked schema_surfaces —
    actually fires on a schema_surfaces entry, and is non-blocking (unlike codeowners-ownership)."""
    inventory = {
        "target_ref": "unknown",
        "schema_surfaces": [
            {
                "target": "contracts/**/*.schema.json",
                "classification": "observed",
                "evidence": [_evidence_ref("contracts/widget.schema.json")],
            }
        ],
    }

    built = plan.build_plan(inventory)

    contract_proposals = [p for p in built["proposals"] if p["kind"] == "contract-candidate"]
    assert len(contract_proposals) == 1
    assert contract_proposals[0]["classification"] == "unknown"
    assert contract_proposals[0]["target"] == "contracts/widget.schema.json"

    contract_questions = [q for q in built["questions"] if q["kind"] == "contract-candidate"]
    assert len(contract_questions) == 1
    assert contract_questions[0]["blocking"] is False


def test_contract_candidate_proposal_per_schema_file() -> None:
    """WR-05: one contract-candidate proposal PER evidence pointer (per schema file), never one
    lumped proposal for the whole schema_surfaces entry."""
    inventory = {
        "target_ref": "unknown",
        "schema_surfaces": [
            {
                "target": "contracts/**/*.schema.json",
                "classification": "observed",
                "evidence": [
                    _evidence_ref("contracts/widget.schema.json"),
                    _evidence_ref("contracts/gadget.schema.json"),
                ],
            }
        ],
    }

    built = plan.build_plan(inventory)
    contract_proposals = [p for p in built["proposals"] if p["kind"] == "contract-candidate"]
    assert len(contract_proposals) == 2
    assert {p["target"] for p in contract_proposals} == {
        "contracts/widget.schema.json",
        "contracts/gadget.schema.json",
    }


def test_contract_candidate_matches_real_repo_schema_count(repo_root: Path) -> None:
    """Live structural check: a real scan of this harness's own contracts/ tree produces exactly
    one contract-candidate proposal per real contracts/**/*.schema.json file — never a hardcoded
    literal, mirroring test_dispositions.py's test_catalog_covers_real_contract_schemas."""
    inventory = scan.build_inventory(repo_root)
    built = plan.build_plan(inventory)
    live_count = len(sorted((repo_root / "contracts").rglob("*.schema.json")))
    contract_proposal_count = len(
        [p for p in built["proposals"] if p["kind"] == "contract-candidate"]
    )
    assert contract_proposal_count == live_count
    assert live_count > 0


def _minimal_surface_record(target: str) -> dict:
    return {
        "target": target,
        "classification": "observed",
        "evidence": [_evidence_ref(target)],
    }


def test_build_plan_validates_for_every_inventory_surface_shape() -> None:
    """CR-03 forward-direction proof: a maximally-populated, schema-valid inventory (every
    surface-array shape inventory.schema.json permits, each carrying non-empty evidence — the
    ONLY schema-valid shape now that surfaceRecord.evidence requires minItems:1) always produces a
    build_plan() output that itself validates against plan.schema.json."""
    inventory = {
        "target_ref": "unknown",
        "enumeration_mode": "builtin",
        "max_file_bytes": 1_000_000,
        "included": [],
        "excluded": [],
        "languages": [],
        "manifests": [],
        "documentation_surfaces": [_minimal_surface_record("README")],
        "ci_surfaces": [_minimal_surface_record(".github/workflows")],
        "test_surfaces": [_minimal_surface_record("tests")],
        "candidate_process_boundaries": [_minimal_surface_record("services/worker")],
        "schema_surfaces": [_minimal_surface_record("contracts/**/*.schema.json")],
        "codeowners_surfaces": [_minimal_surface_record(".github/CODEOWNERS")],
    }

    inventory_validator = Draft202012Validator(_INVENTORY_SCHEMA)
    inventory_errors = list(inventory_validator.iter_errors(inventory))
    assert inventory_errors == [], (
        f"the fixture itself must be schema-conformant under minItems:1: {inventory_errors!r}"
    )

    built = plan.build_plan(inventory)
    plan_validator = Draft202012Validator(_PLAN_SCHEMA)
    plan_errors = list(plan_validator.iter_errors(built))
    assert plan_errors == [], (
        f"build_plan() output must validate against plan.schema.json: {plan_errors!r}"
    )


def test_empty_evidence_surface_record_now_fails_at_inventory_schema_gate() -> None:
    """CR-03 negative control: an inventory carrying evidence:[] on a surfaceRecord-shaped field
    is now schema-INVALID against inventory.schema.json itself — one gate earlier than the
    previous build_plan()-time failure."""
    inventory = {
        "target_ref": "x",
        "codeowners_surfaces": [
            {"target": ".github/CODEOWNERS", "classification": "observed", "evidence": []}
        ],
    }

    validator = Draft202012Validator(_INVENTORY_SCHEMA)
    errors = list(validator.iter_errors(inventory))
    assert any(
        "non-empty" in error.message or "minItems" in str(error.validator) for error in errors
    )


def test_classify_over_fixture_validates_shape(tmp_minirepo: Path) -> None:
    """build_plan() over the real D-06 fixture never invents a relationship (no relationship
    signal exists in the inventory), and every proposal carries a valid classification."""
    inventory = scan.build_inventory(tmp_minirepo)
    built = plan.build_plan(inventory)
    assert built["relationships"] == []
    assert built["target_ref"] == inventory["target_ref"]
    ids = [p["id"] for p in built["proposals"]]
    assert ids == sorted(ids)
