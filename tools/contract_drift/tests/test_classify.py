"""Breaking-vs-non-breaking classification (CONTRACT-04, D-07, seed change_policy).

Per correction-rules.catalog.yaml change_policy: a purely additive edit (a new optional column, a
new rule case, a new enum value) is NON-BREAKING; removing/renaming a required field or changing a
fixed expected value (const/enum narrowing) is BREAKING.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import classify  # noqa: E402

# A representative TSV-spec-shaped schema: required columns + a fixed convention const + an enum.
_BASE = {
    "type": "object",
    "required": ["timestamp", "equipment_id"],
    "properties": {
        "timestamp": {"type": "string"},
        "equipment_id": {"type": "string"},
        "newline": {"const": "lf"},
        "tsv_escape": {"enum": ["backslash", "forbid"]},
    },
}


# --- non-breaking (purely additive) ---------------------------------------------------------


def test_added_optional_column_is_non_breaking():
    new = copy.deepcopy(_BASE)
    new["properties"]["param_value"] = {"type": "string"}  # added, NOT added to `required`
    assert classify(_BASE, new) == "non-breaking"


def test_added_enum_case_is_non_breaking():
    new = copy.deepcopy(_BASE)
    new["properties"]["tsv_escape"]["enum"] = ["backslash", "forbid", "quote"]  # additive case
    assert classify(_BASE, new) == "non-breaking"


def test_identical_schema_is_non_breaking():
    assert classify(_BASE, copy.deepcopy(_BASE)) == "non-breaking"


# --- breaking (destructive / changed expected) ----------------------------------------------


def test_removed_required_column_is_breaking():
    new = copy.deepcopy(_BASE)
    new["required"] = ["timestamp"]
    del new["properties"]["equipment_id"]
    assert classify(_BASE, new) == "breaking"


def test_renamed_required_column_is_breaking():
    new = copy.deepcopy(_BASE)
    new["required"] = ["timestamp", "equip_id"]
    new["properties"]["equip_id"] = new["properties"].pop("equipment_id")
    assert classify(_BASE, new) == "breaking"


def test_changed_const_expected_value_is_breaking():
    new = copy.deepcopy(_BASE)
    new["properties"]["newline"]["const"] = "crlf"  # changed fixed expected value
    assert classify(_BASE, new) == "breaking"


def test_removed_enum_case_is_breaking():
    new = copy.deepcopy(_BASE)
    new["properties"]["tsv_escape"]["enum"] = ["backslash"]  # dropped a previously-allowed value
    assert classify(_BASE, new) == "breaking"
