"""Tests for the contracts-index generator (MEM-03, D-04/D-05/D-06, ROADMAP Crit-2).

Pins the three guarantees the derived plane depends on:
  (a) determinism — render twice AND generate→hash→delete→regenerate are byte-identical (Pitfall 1);
      proven WITHOUT git diff, because ``.memory/derived/`` is gitignored (Pitfall 2).
  (b) drift correctness — a mutated schema in a tmp contracts tree surfaces a ``drift:*`` status in
      its row while the untouched sibling stays ``clean`` (reused run_gate() — no second hasher).
  (c) a committed syrupy snapshot of render() over the REAL contracts tree = the determinism
      reference stored under __snapshots__/ (NOT under .memory/).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.contract_hash.hash import build_manifest
from tools.memory_regen import contracts_index

# ---- (b) drift correctness: mutated tmp schema shows drift, sibling clean --------------------


def _write_baseline(tmp_path: Path, contracts_dir: Path) -> Path:
    """Snapshot the pristine tmp contracts tree into a baseline manifest run_gate can diff."""
    baseline = build_manifest(contracts_dir)
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline, indent=2, sort_keys=True), encoding="utf-8")
    return baseline_path


def test_drift_status_reflects_mutated_schema(tmp_path: Path, tmp_contracts_tree: Path) -> None:
    """One mutated schema → its row is drift:*; the untouched sibling stays clean (reused gate)."""
    baseline_path = _write_baseline(tmp_path, tmp_contracts_tree)

    schemas = sorted(tmp_contracts_tree.glob("**/*.schema.json"))
    assert len(schemas) >= 2, "fixture must sample >= 2 schemas to prove drift vs clean"
    mutated = schemas[0]
    obj = json.loads(mutated.read_text(encoding="utf-8"))
    obj["__drift_probe__"] = "mutated-by-test"  # additive change → trips the hash → drift
    mutated.write_text(json.dumps(obj, indent=2), encoding="utf-8")

    rows = contracts_index.index_rows(tmp_contracts_tree, baseline_path)
    status = {rel: drift for rel, _kind, _owner, _hash, drift in rows}

    mutated_rel = mutated.resolve().relative_to(tmp_contracts_tree.resolve().parent).as_posix()
    sibling_rel = schemas[1].resolve().relative_to(tmp_contracts_tree.resolve().parent).as_posix()

    assert status[mutated_rel].startswith("drift:"), status
    assert status[sibling_rel] == "clean", status


def test_clean_tree_has_no_drift(tmp_path: Path, tmp_contracts_tree: Path) -> None:
    """An unmutated tree diffed against its own baseline → every row clean (reused gate)."""
    baseline_path = _write_baseline(tmp_path, tmp_contracts_tree)
    rows = contracts_index.index_rows(tmp_contracts_tree, baseline_path)
    assert rows, "fixture yielded no rows"
    assert all(drift == "clean" for *_rest, drift in rows), rows


# ---- (a) determinism: byte-identical, proven without git diff --------------------------------


def test_render_is_deterministic_over_real_tree() -> None:
    """render(index_rows()) twice over the real contracts tree is byte-identical (Pitfall 1)."""
    first = contracts_index.render(contracts_index.index_rows())
    second = contracts_index.render(contracts_index.index_rows())
    assert first == second


def test_generate_delete_regenerate_is_byte_identical(tmp_path: Path) -> None:
    """generate → sha256 → delete → regenerate → assert identical hash (NOT git diff, Pitfall 2)."""
    out = tmp_path / "derived" / "contracts-index.md"
    contracts_index.write(index_path=out)
    digest_1 = hashlib.sha256(out.read_bytes()).hexdigest()
    out.unlink()
    assert not out.exists()
    contracts_index.write(index_path=out)
    digest_2 = hashlib.sha256(out.read_bytes()).hexdigest()
    assert digest_1 == digest_2


# ---- structure: DERIVED marker, no timestamp, no full schema body ----------------------------


def test_output_carries_derived_marker_and_no_body() -> None:
    """Header marks DERIVED; no timestamp / no raw `$schema` body dump (index rows only)."""
    text = contracts_index.render(contracts_index.index_rows())
    assert text.splitlines()[0].startswith("# DERIVED — do not hand-edit")
    assert "do not hand-edit" in text
    # Index carries pointers/rows only — never a full schema body (T-02-06).
    assert '"$schema"' not in text
    assert '"properties"' not in text


def test_rows_have_kind_owner_hash_and_status() -> None:
    """Every row = (rel, kind, owner=TBD, hash[:12], status); hash is a prefix, owner never
    fabricated."""
    rows = contracts_index.index_rows()
    assert rows, "no contracts indexed"
    for rel, kind, owner, hash_prefix, status in rows:
        assert rel.startswith("contracts/")
        assert kind in {"log-spec", "normalization", "reference-data", "state", "other"}
        assert owner == "TBD"
        assert len(hash_prefix) == 12
        assert status == "clean" or status.startswith("drift:")


# ---- (c) committed syrupy snapshot = determinism reference -----------------------------------


def test_render_matches_committed_snapshot(snapshot) -> None:
    """Committed .ambr snapshot pins render() over the real contracts tree (determinism
    reference)."""
    assert contracts_index.render(contracts_index.index_rows()) == snapshot
