"""POLY-01 §4.3-4.6 polyglot-boundary linter — per-rule violation proofs.

Each §4.3-4.6 rule (R1 BOM · R2 CRLF/LF · R3 decimal-locale · R5 timezone/datetime ·
R6 null-vs-empty · R7 TSV column-shift) gets a positive (violation caught) and a negative
(clean input → no violation) assertion, plus a fail-loud CLI exit-code proof. The linter must
NOT re-implement normalization — the decimal/datetime/null checks compare each cell to the
shared ``normalize.core`` output (proven drift-free in test_corpus_parity.py).
"""

from __future__ import annotations

from tools.polyglot_lint.lint import lint_bytes, lint_file, lint_tsv, main


def _codes(vios) -> set[str]:
    return {v.rule for v in vios}


# --- R1 BOM (§4.3) ---------------------------------------------------------------------------


def test_bom_bytes_flagged() -> None:
    assert "R1-BOM" in _codes(lint_bytes(b"\xef\xbb\xbfa\tb\n"))


def test_clean_utf8_lf_no_violation() -> None:
    assert lint_bytes(b"a\tb\nc\td\n") == []


# --- R2 CRLF -> LF (§4.3) --------------------------------------------------------------------


def test_crlf_bytes_flagged() -> None:
    assert "R2-CRLF" in _codes(lint_bytes(b"a\tb\r\nc\td\n"))


# --- R3 decimal-locale + R5 timezone/datetime (§4.6 / §4.4) ----------------------------------


def test_non_canonical_decimal_and_datetime_flagged() -> None:
    # comma-decimal + space-separated naive datetime are both non-canonical.
    codes = _codes(lint_tsv("1,5\t2024-01-01 00:00", kinds=["decimal", "datetime"]))
    assert "R3-decimal" in codes
    assert "R5-datetime" in codes


def test_canonical_decimal_and_datetime_no_violation() -> None:
    # already-canonical dot-decimal + fixed ISO-8601 UTC → nothing to fix.
    assert lint_tsv("1.5\t2024-01-01T00:00:00Z", kinds=["decimal", "datetime"]) == []


def test_wire_null_token_in_typed_column_not_flagged() -> None:
    # the agreed wire null token (\N) is a legitimate value in any typed column (R6).
    assert lint_tsv("\\N\t\\N", kinds=["decimal", "datetime"]) == []


# --- R6 null vs empty (§4.3) -----------------------------------------------------------------


def test_leaked_null_sentinel_flagged() -> None:
    # the internal comparison sentinel <NULL> must never appear in wire TSV data.
    assert "R6-null" in _codes(lint_tsv("a\t<NULL>"))


def test_wire_null_token_not_flagged() -> None:
    # \N (the agreed wire null token) is canonical; only the leaked sentinel is a violation.
    assert lint_tsv("a\t\\N") == []


# --- R7 TSV column-shift (§4.3) --------------------------------------------------------------


def test_uneven_tab_counts_flagged() -> None:
    # row 0 = 2 cols (1 tab), row 1 = 3 cols (2 tabs) → column shift.
    assert "R7-tsv" in _codes(lint_tsv("a\tb\nc\td\te"))


def test_even_tab_counts_no_violation() -> None:
    assert lint_tsv("a\tb\nc\td") == []


# --- lint_file (bytes + text checks combined) ------------------------------------------------


def test_lint_file_detects_bom(tmp_path) -> None:
    p = tmp_path / "x.tsv"
    p.write_bytes(b"\xef\xbb\xbfa\tb\n")
    assert "R1-BOM" in _codes(lint_file(str(p)))


# --- main() fail-loud exit codes (reasons to stderr) -----------------------------------------


def test_main_exits_1_on_violation_and_reasons_to_stderr(tmp_path, capsys) -> None:
    p = tmp_path / "bom.tsv"
    p.write_bytes(b"\xef\xbb\xbfa\tb\n")
    rc = main([str(p)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "R1-BOM" in err


def test_main_exits_0_on_clean_file(tmp_path, capsys) -> None:
    p = tmp_path / "clean.tsv"
    p.write_bytes(b"a\tb\nc\td\n")
    rc = main([str(p)])
    assert rc == 0
    # nothing failed → no violation reason on stderr.
    assert "FAIL" not in capsys.readouterr().err
