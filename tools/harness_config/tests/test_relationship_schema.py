"""Fixture-driven validation of the contract-relationship record schema (TOPO-01).

Mirrors the ``tools/task_packet/tests/test_task_packet.py`` idiom: one
``Draft202012Validator`` built over ``contracts/harness/topology/relationship.schema.json``,
parametrized across positive/negative fixture ``cases.json`` files. Positive records validate
with zero ``iter_errors``; each negative record (one violated constraint apiece) yields >=1 error.
The schema validates ONE relationship record's shape/cardinality only — endpoint resolution and
cross-record consistency are deferred to Phase 25 (D-01/D-02).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

# tests -> harness_config -> tools -> repo root (parents[3]; mirrors conftest.py).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_PATH = _REPO_ROOT / "contracts" / "harness" / "topology" / "relationship.schema.json"
_FIXTURES = Path(__file__).parent / "fixtures" / "relationships"


def _read(path: Path):
    return json.loads(path.read_bytes())


_SCHEMA = _read(_SCHEMA_PATH)
_VALIDATOR = Draft202012Validator(_SCHEMA)


def test_relationship_schema_is_a_valid_draft_2020_12_schema() -> None:
    Draft202012Validator.check_schema(_SCHEMA)


@pytest.mark.parametrize("case", _read(_FIXTURES / "valid" / "cases.json"), ids=lambda c: c["name"])
def test_positive_relationship_records_validate(case: dict) -> None:
    errors = list(_VALIDATOR.iter_errors(case["record"]))
    assert errors == [], [error.message for error in errors]


@pytest.mark.parametrize(
    "case", _read(_FIXTURES / "negative" / "cases.json"), ids=lambda c: c["name"]
)
def test_negative_relationship_records_are_rejected(case: dict) -> None:
    errors = list(_VALIDATOR.iter_errors(case["record"]))
    assert len(errors) >= 1, f"{case['name']} unexpectedly validated clean"
