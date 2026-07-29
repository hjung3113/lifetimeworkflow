"""Language-agnostic identity converter + golden_dir override (GEN-02, 05-02 Task 1).

Proves the generic (no-.NET) golden loop end-to-end WITHOUT depending on golden/sample:
each case is built in a tmp golden_dir so the test is order-independent from the yet-unwritten
sample fixtures. The identity converter copies seed bytes verbatim (zero canonicalization); a
case PASSES only when the seed→baseline diff is limited to what ``normalize_tsv`` neutralizes
(R1 BOM / R2 CRLF / R8 row-order) — a genuine value diff still FAILs and writes ``.received``
while never touching the human-approved ``.verified`` baseline (P9).
"""

from __future__ import annotations

from pathlib import Path

from golden_runner.runner import (
    run_golden_case,
    run_identity_converter,
    verified_path,
)


def _write_case(
    golden_dir: Path,
    case: str,
    seed_lines: list[str],
    baseline_lines: list[str],
) -> None:
    """Materialize a tmp golden case: byte-clean (LF, no BOM) seed + verified baseline."""
    seed = golden_dir / case / "input" / "seed.tsv"
    seed.parent.mkdir(parents=True, exist_ok=True)
    seed.write_bytes(("\n".join(seed_lines) + "\n").encode("utf-8"))

    baseline = golden_dir / case / "expected" / "baseline.verified.tsv"
    baseline.parent.mkdir(parents=True, exist_ok=True)
    baseline.write_bytes(("\n".join(baseline_lines) + "\n").encode("utf-8"))


def test_identity_converter_copies_bytes_verbatim(tmp_path: Path) -> None:
    """The identity converter writes the seed bytes verbatim — no canonicalization, no .NET."""
    seed = tmp_path / "seed.tsv"
    raw = b"name\tgreeting\r\nbob\thello\n"  # deliberately CRLF + no trailing newline norm
    seed.write_bytes(raw)
    out = tmp_path / "out.tsv"

    run_identity_converter(seed, out)

    assert out.read_bytes() == raw  # byte-for-byte copy, zero transformation


def test_row_order_case_passes_with_identity_and_no_dotnet(tmp_path: Path) -> None:
    """A row-order-only diff run through identity PASSES (normalize_tsv R8 sorts both equal)."""
    golden_dir = tmp_path / "golden"
    # seed rows UNSORTED; baseline = the SAME lines ordinal-sorted.
    _write_case(
        golden_dir,
        "roworder",
        seed_lines=["name\tgreeting", "carol\thello", "alice\thello", "bob\thello"],
        baseline_lines=["alice\thello", "bob\thello", "carol\thello", "name\tgreeting"],
    )
    out = tmp_path / "out.tsv"

    result = run_golden_case("roworder", out, converter="identity", golden_dir=golden_dir)

    assert result.passed, f"row-order case should PASS after normalize; diff:\n{result.diff}"
    assert result.received_path is None  # PASS never writes a .received


def test_golden_dir_override_resolves_under_tmp(tmp_path: Path) -> None:
    """The golden_dir override reroots case/seed/verified/received off REPO_ROOT/golden."""
    golden_dir = tmp_path / "golden"
    _write_case(
        golden_dir,
        "roworder",
        seed_lines=["a\t1", "b\t2"],
        baseline_lines=["a\t1", "b\t2"],
    )
    # verified_path must resolve under the override, not the repo golden dir.
    vp = verified_path("roworder", golden_dir=golden_dir)
    assert vp == golden_dir / "roworder" / "expected" / "baseline.verified.tsv"
    assert vp.is_file()


def test_value_diff_fails_and_never_touches_verified(tmp_path: Path) -> None:
    """A genuine value diff FAILs, writes .received, and leaves .verified untouched (P9)."""
    golden_dir = tmp_path / "golden"
    _write_case(
        golden_dir,
        "valuediff",
        seed_lines=["name\tgreeting", "bob\tgoodbye"],  # 'goodbye' != baseline 'hello'
        baseline_lines=["bob\thello", "name\tgreeting"],
    )
    out = tmp_path / "out.tsv"
    verified = verified_path("valuediff", golden_dir=golden_dir)
    verified_before = verified.read_bytes()

    result = run_golden_case("valuediff", out, converter="identity", golden_dir=golden_dir)

    assert not result.passed, "a genuine value diff must FAIL (identity can't neutralize it)"
    assert result.diff, "a FAIL must surface a normalized diff"
    assert result.received_path is not None and result.received_path.exists()
    assert verified.read_bytes() == verified_before  # .verified NEVER overwritten
