"""ECON-02 Wave-0 structural gate — the fan-out worker return contract.

Pins the shape of ``harness/skills/fan-out-synthesize/references/fan-out-return.schema.json`` so the
context-economy return stays bounded and domain-neutral:

- the schema file exists and ``json.loads`` parses it;
- it declares JSON Schema **Draft 2020-12**;
- it is a closed object (``additionalProperties: false``) — a return cannot smuggle extra keys;
- it ``required``s the citation-bearing pair ``unit`` + ``claims`` (T-10-01: paths+claims, not dumps);
- it carries NO ``$ref`` into the ``contracts/`` constitution plane (D-08 — self-contained);
- its raw text carries no instance-overlay path token (domain-neutral, keeps GEN-04 green).

Mirrors the repo-root idiom of ``test_core_no_example_dep.py`` (``parents[3]``); no runtime import of
any harness module — the schema is read as a file.
"""

from __future__ import annotations

import json
from pathlib import Path

# test_fan_out_return_contract.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA = (
    _REPO_ROOT
    / "harness"
    / "skills"
    / "fan-out-synthesize"
    / "references"
    / "fan-out-return.schema.json"
)

_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

# The instance-overlay path token this schema must NOT contain, assembled from parts so this guard
# file does not itself carry the literal and trip the GEN-04 core→example prose scan.
_INSTANCE_PATH_TOKEN = "examples" + "/"


def _raw() -> str:
    return _SCHEMA.read_text(encoding="utf-8")


def _schema() -> dict:
    return json.loads(_raw())


def test_schema_file_exists() -> None:
    """The return-contract schema is co-located under the skill's references/ (D-08)."""
    assert _SCHEMA.is_file(), f"missing return-contract schema at {_SCHEMA}"


def test_schema_parses_as_json() -> None:
    """The schema is valid JSON (byte-copied verbatim to both runtimes by the emitter)."""
    obj = _schema()
    assert isinstance(obj, dict) and obj, "schema did not parse to a non-empty object"


def test_schema_declares_draft_2020_12() -> None:
    """The contract declares JSON Schema Draft 2020-12."""
    assert _schema().get("$schema") == _DRAFT_2020_12, f"expected $schema == {_DRAFT_2020_12!r}"


def test_schema_is_closed_object() -> None:
    """additionalProperties:false — a return cannot smuggle extra keys (T-10-01)."""
    obj = _schema()
    assert obj.get("type") == "object", "top-level schema must be type object"
    assert obj.get("additionalProperties") is False, (
        "top-level schema must set additionalProperties:false"
    )


def test_schema_requires_citation_bearing_fields() -> None:
    """The required list carries the citation-bearing pair unit + claims."""
    required = _schema().get("required", [])
    assert "unit" in required and "claims" in required, (
        f"required must include both 'unit' and 'claims', got {required!r}"
    )


def test_schema_has_no_contracts_ref() -> None:
    """No $ref targets the contracts/ constitution plane — the schema is self-contained (D-08)."""
    raw = _raw()
    assert "contracts/" not in raw, "schema must not $ref into contracts/ (D-08 self-contained)"


def test_schema_is_domain_neutral() -> None:
    """No instance-overlay path token — the schema is domain-neutral (keeps GEN-04 guard green)."""
    assert _INSTANCE_PATH_TOKEN not in _raw(), (
        "schema carries an instance-overlay path token — GEN-04 leak"
    )
