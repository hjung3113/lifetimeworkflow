"""repr-only golden case → PASS (CONTRACT-03, ROADMAP 성공기준 3, Pitfall P4).

End-to-end walking-skeleton slice: the runner spawns the .NET toy converter over the A-model CLI
boundary, captures its --out file, normalizes BOTH that output and the approved .verified baseline
via the shared §4-5 core, and diffs. The input differs from the baseline ONLY in representation
(BOM/CRLF/decimal-locale/TZ), so the normalized diff is empty → PASS. A byte-diff would false-red.

Requires the .NET SDK (spawn). Skipped (not failed) when dotnet is not installed — the comparison
logic itself is proven .NET-free in test_compare_recorded.py.
"""

from __future__ import annotations

from tools.golden_runner.runner import run_golden_case


def test_repr_only_passes(require_dotnet, golden_out):
    result = run_golden_case("repr-only", golden_out, dotnet_exe=require_dotnet)
    assert result.passed, (
        "repr-only case must PASS after §4-5 normalization neutralizes the BOM/CRLF/locale/TZ "
        f"representation diffs (P4). Diff was:\n{result.diff}"
    )
    assert result.received_path is None, "a PASS must not write a .received file"
