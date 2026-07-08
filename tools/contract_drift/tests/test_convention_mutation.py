"""P14 demo: flipping a §4-5 convention field trips the drift gate (CONTRACT-04, D-07).

Proves the hash covers cross-cutting conventions, not just the column list: copying the tree to a
tmp dir and flipping ``format-conventions.schema.json``'s ``bom`` const (false→true) bumps the JCS
SHA-256 and trips the gate — exactly like a column reorder would (PITFALLS P14). The committed
baseline is never mutated (all edits happen on a tmp copy).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Make the repo-root `tools` package importable (virtual uv workspace members, not pip-installed).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import load_baseline, run_gate  # noqa: E402
from tools.contract_hash.hash import REPO_ROOT, schema_hash  # noqa: E402

_FC_KEY = "contracts/normalization/format-conventions.schema.json"


def _copy_contracts(tmp_path: Path) -> Path:
    dst = tmp_path / "contracts"
    shutil.copytree(REPO_ROOT / "contracts", dst)
    return dst


def test_unchanged_copy_matches_baseline(tmp_path):
    """Sanity: a pristine copy of the tree passes the gate (exit-0 equivalent)."""
    contracts = _copy_contracts(tmp_path)
    result = run_gate(contracts_dir=contracts)
    assert result["ok"] is True
    assert result["drifted"] == []


def test_convention_flip_bumps_hash_and_trips_gate(tmp_path):
    """Flipping the §4-5 ``bom`` convention bumps the schema hash AND trips the gate (P14)."""
    contracts = _copy_contracts(tmp_path)
    fc = contracts / "normalization" / "format-conventions.schema.json"
    baseline = load_baseline()

    before = schema_hash(fc)
    assert before == baseline[_FC_KEY], "copied convention schema must match committed baseline"

    # §4-5 convention mutation: bom false -> true (NOT a column reorder).
    doc = json.loads(fc.read_text(encoding="utf-8"))
    assert doc["properties"]["bom"]["const"] is False
    doc["properties"]["bom"]["const"] = True
    fc.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    after = schema_hash(fc)
    assert after != before, "P14: a §4-5 convention flip MUST bump the JCS SHA-256"

    result = run_gate(contracts_dir=contracts)
    assert result["ok"] is False, "gate must trip on the convention change"
    drifted_files = {rel for rel, _kind, _cls in result["drifted"]}
    assert _FC_KEY in drifted_files, "the drifted file must be the §4-5 conventions schema"


def test_convention_flip_is_classified(tmp_path):
    """A changed const (expected value) classifies breaking."""
    contracts = _copy_contracts(tmp_path)
    fc = contracts / "normalization" / "format-conventions.schema.json"
    doc = json.loads(fc.read_text(encoding="utf-8"))
    doc["properties"]["bom"]["const"] = True
    fc.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    result = run_gate(contracts_dir=contracts)
    classifications = {rel: cls for rel, _kind, cls in result["drifted"]}
    assert classifications[_FC_KEY] == "breaking"
