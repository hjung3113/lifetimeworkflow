"""test_manifest_schema_conformance.py — WR-03: manifest.schema.json's `destination`/`path` fields
constrain shape (no absolute paths, no `..` path segments) at the schema layer, independent of
`apply.py`'s runtime `refuse_unsafe_destination` choke point (defense in depth).

Mirrors `tools/adoption_scan/tests/test_schema_conformance.py`'s loader/`Draft202012Validator`
house convention, scoped to `manifest.schema.json`'s `destination`/`path` shape specifically.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_DIR = _REPO_ROOT / "contracts" / "harness" / "adoption"


def _schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def _base_document() -> dict:
    return {"target_ref": "unknown", "dispositions": [], "excluded": []}


def _errors_for_destination(destination: str) -> list:
    document = _base_document()
    document["dispositions"] = [{"destination": destination, "disposition": "create"}]
    validator = Draft202012Validator(_schema("manifest"))
    return list(validator.iter_errors(document))


UNSAFE_DESTINATIONS = [
    "/etc/passwd",  # absolute
    "../etc/passwd",  # leading traversal
    "a/../contracts/x.json",  # mid-path traversal
]

SAFE_DESTINATIONS = [
    "contracts/widget.schema.json",
    "src/widget.py",
    "foo/bar..json",  # literal ".." substring inside a filename, not a path segment
]


@pytest.mark.parametrize("destination", UNSAFE_DESTINATIONS)
def test_manifest_schema_rejects_unsafe_destination(destination: str) -> None:
    errors = _errors_for_destination(destination)
    assert errors, f"expected {destination!r} to fail schema validation, but it passed"


@pytest.mark.parametrize("destination", SAFE_DESTINATIONS)
def test_manifest_schema_accepts_safe_destination(destination: str) -> None:
    errors = _errors_for_destination(destination)
    assert errors == [], f"expected {destination!r} to pass schema validation: {errors}"


@pytest.mark.parametrize("destination", UNSAFE_DESTINATIONS)
def test_manifest_schema_excluded_destination_and_evidence_path_also_constrained(
    destination: str,
) -> None:
    schema = _schema("manifest")
    validator = Draft202012Validator(schema)

    excluded_document = _base_document()
    excluded_document["excluded"] = [{"destination": destination, "reason": "gsd-owned"}]
    excluded_errors = list(validator.iter_errors(excluded_document))
    assert excluded_errors, (
        f"expected excludedDestinationRecord.destination={destination!r} to fail validation"
    )

    evidence_document = _base_document()
    evidence_document["dispositions"] = [
        {
            "destination": "contracts/widget.schema.json",
            "disposition": "create",
            "evidence": [
                {
                    "path": destination,
                    "sha256": "0" * 64,
                }
            ],
        }
    ]
    evidence_errors = list(validator.iter_errors(evidence_document))
    assert evidence_errors, f"expected evidenceRef.path={destination!r} to fail validation"


def test_schema_copy_not_mutated_by_document_construction() -> None:
    """Sanity guard: building test documents never mutates the loaded schema dict in place."""
    schema = _schema("manifest")
    before = copy.deepcopy(schema)
    _errors_for_destination("/etc/passwd")
    assert schema == before
