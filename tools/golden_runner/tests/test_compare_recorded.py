"""Runtime-free proof of the golden-runner comparison path (CONTRACT-03, Pitfall P4/P9).

The end-to-end tests (test_repr_only / test_value_regression) spawn the .NET converter and are
DEFERRED in this container (.NET 10 egress-blocked). This module exercises the SAME
normalize + diff + ``.received`` logic (``runner.compare``) directly, feeding RECORDED converter
outputs — so the comparison core is verified green in pure Python with zero .NET.

The recorded outputs equal a live ``dotnet run`` because both §4-5 cores implement identical rules
(cross-validated by libs/normalize-fixtures, D-04).
"""

from __future__ import annotations

from pathlib import Path

from tools.golden_runner.runner import compare, received_path, verified_path

_RECORDED = Path(__file__).resolve().parent / "recorded"


def test_repr_only_recorded_output_passes():
    """repr-only recorded output normalizes to the baseline → PASS, no .received written (P4)."""
    output = (_RECORDED / "repr-only.converter-output.tsv").read_bytes()
    result = compare(output, "repr-only")
    assert result.passed, f"expected PASS after normalization; diff was:\n{result.diff}"
    assert result.received_path is None


def test_value_regression_recorded_output_fails_and_never_touches_verified():
    """value-regression recorded output has a real value diff → FAIL, .received written, .verified intact."""  # noqa: E501
    case = "value-regression"
    verified_before = verified_path(case).read_bytes()
    output = (_RECORDED / "value-regression.converter-output.tsv").read_bytes()

    rec = received_path(case)
    try:
        result = compare(output, case)
        assert not result.passed, (
            "a genuine value regression must FAIL (not swallowed by normalize)"
        )
        assert result.diff, "a FAIL must surface a normalized diff"
        # machine-proposed .received was written ...
        assert result.received_path == rec and rec.exists()
        # ... and the human-approved .verified baseline was NEVER overwritten (P9).
        assert verified_path(case).read_bytes() == verified_before
    finally:
        # keep the working tree clean (a .received is a transient proposal, gitignored).
        if rec.exists():
            rec.unlink()
