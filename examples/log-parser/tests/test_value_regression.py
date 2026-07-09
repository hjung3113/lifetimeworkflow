"""value-regression golden case → FAIL (CONTRACT-03, ROADMAP 성공기준 3, Pitfall P4).

The input carries the SAME representation noise as repr-only (BOM/CRLF/locale/TZ) PLUS a genuine
value regression (param_value 9.99 vs the baseline's 1.5). Normalization neutralizes the noise but
the real value difference survives → the runner reports FAIL and writes a .received file WITHOUT
ever overwriting the human-approved .verified baseline (P9).

Requires the .NET SDK (spawn). Skipped (not failed) when dotnet is not installed — the comparison
logic itself is proven .NET-free in test_compare_recorded.py.
"""

from __future__ import annotations

from tools.golden_runner.runner import baseline_path, run_golden_case, verified_path


def test_value_regression_fails(
    require_dotnet, golden_out, example_golden_dir, toy_converter_project
):
    verified_before = verified_path("value-regression", example_golden_dir).read_bytes()

    result = run_golden_case(
        "value-regression",
        golden_out,
        dotnet_exe=require_dotnet,
        project=toy_converter_project,
        golden_dir=example_golden_dir,
    )

    assert not result.passed, (
        "value-regression must FAIL — a genuine value change must survive normalization "
        "(normalization must not swallow real regressions, P4)."
    )
    # runner wrote a machine-proposed .received ...
    assert result.received_path is not None and result.received_path.exists()
    # ... and NEVER touched the human-approved .verified baseline (P9).
    assert baseline_path("value-regression", example_golden_dir).read_bytes() == verified_before
