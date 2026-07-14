"""Unit tests for :func:`normalize.core.normalize_cell` — R3/R5/R6 cell canonicalization.

Complements ``test_corpus_parity.py`` (which cross-validates the shared fixture corpus) with
direct edge-case coverage the corpus does not carry — notably the empty typed cell that used to
raise before the R6 empty-string guard.
"""

from __future__ import annotations

import sys
from pathlib import Path

_LIBS_PYTHON = Path(__file__).resolve().parents[2]  # tests -> normalize -> python
if str(_LIBS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_LIBS_PYTHON))

from normalize.core import NULL_SENTINEL, normalize_cell  # noqa: E402


# --- R6: null vs empty vs value ------------------------------------------------------------------


def test_null_token_maps_to_sentinel():
    assert normalize_cell("\\N", "decimal") == NULL_SENTINEL
    assert normalize_cell("\\N", "datetime") == NULL_SENTINEL
    assert normalize_cell("\\N", "string") == NULL_SENTINEL


def test_empty_decimal_cell_stays_empty_not_crash():
    # Regression: an empty decimal cell used to raise decimal.InvalidOperation.
    assert normalize_cell("", "decimal") == ""


def test_empty_datetime_cell_stays_empty_not_crash():
    # Regression: an empty datetime cell used to raise ValueError (fromisoformat("")).
    assert normalize_cell("", "datetime") == ""


def test_empty_string_cell_stays_empty():
    assert normalize_cell("", "string") == ""


# --- R3 decimal / R5 datetime still canonicalize non-empty values --------------------------------


def test_decimal_locale_comma_and_trailing_zeros():
    assert normalize_cell("1,50", "decimal") == "1.5"


def test_datetime_offset_converted_to_utc():
    assert normalize_cell("2026-07-14T09:00:00+09:00", "datetime") == "2026-07-14T00:00:00Z"
