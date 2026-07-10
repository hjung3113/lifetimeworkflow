"""Generic default instance end-to-end (GEN-02, 05-02 Task 2).

Exercises the FULL contract→hash→drift→golden loop over the committed domain-neutral sample —
WITHOUT .NET — proving the machinery runs on a blank domain (Phase 5 success criterion 2):

  (a) the committed ``golden/sample`` case PASSES via the built-in identity converter (row-order
      diff neutralized by §4.3-4.6 ``normalize_tsv``), writing no ``.received``;
  (b) the sample contract is present in the rebaselined root contract-hash manifest;
  (c) the live contract-drift gate reads clean after the rebaseline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from tools.contract_drift.drift import run_gate
from tools.contract_hash.hash import CONTRACTS_DIR, build_manifest
from tools.golden_runner.runner import run_golden_case


def test_sample_case_passes_via_identity_no_dotnet() -> None:
    """golden/sample runs the generic loop (identity converter, no .NET) → PASS, no .received."""
    out = Path(tempfile.mkstemp(suffix=".tsv")[1])
    try:
        result = run_golden_case("sample", out, converter="identity")
        assert result.passed, f"sample case should PASS; diff:\n{result.diff}"
        assert result.received_path is None  # PASS never proposes a .received baseline
    finally:
        out.unlink(missing_ok=True)


def test_sample_contract_in_manifest() -> None:
    """The domain-neutral sample contract is hashed into the root manifest (rebaselined)."""
    manifest = build_manifest(CONTRACTS_DIR)
    assert "contracts/sample/greeting.schema.json" in manifest


def test_drift_clean_after_rebaseline() -> None:
    """The live contract-drift gate is clean — live manifest matches the committed baseline."""
    result = run_gate()
    assert result["ok"], f"expected clean drift after rebaseline; drifted: {result['drifted']}"
