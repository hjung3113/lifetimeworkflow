"""§4.3–4.6 canonicalization core — Python thin implementation (CONTRACT-02, D-04/D-05).

The RULE is canonical (see ``libs/normalize-spec.md``); this module is one thin implementation
of it. The .NET core (``libs/dotnet/Normalize``) implements the same rules and both are
cross-validated by the shared ``libs/normalize-fixtures/*.json`` corpus.

Do NOT hand-roll number formatting, BOM detection, or timezone math — use stdlib
``decimal`` / ``codecs`` (``utf-8-sig``) / ``datetime`` so the deceptively-complex polyglot
representation layer is handled by well-tested code (RESEARCH §Don't Hand-Roll).

This is the TSV data comparator ONLY. It contains zero RFC 8785 / JCS code (that is the
Python-only contract-text hasher in Plan 05 — a different canonicalizer).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

# R6 — the agreed null token (format-conventions.schema.json `null_token` const) maps to this
# DISTINCT sentinel; an empty string maps to "" ("" != null, §4.3).
DEFAULT_NULL_TOKEN = "\\N"
NULL_SENTINEL = "<NULL>"


def _norm_decimal(value: str) -> str:
    """R3 — InvariantCulture decimal, '.' separator, no thousands, trailing zeros stripped.

    A locale ',' decimal separator is remapped to '.' before parsing (thousands separators are
    forbidden by §4.6, so the remap is unambiguous). Uses ``decimal.Decimal`` — never a
    ``float()`` round-trip — to avoid last-digit representation diffs.
    """
    d = Decimal(value.replace(",", "."))
    s = format(d, "f")  # fixed-point, no exponent
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _norm_datetime(value: str) -> str:
    """R5 — convert to UTC and emit the fixed ISO-8601 string ``yyyy-MM-ddTHH:MM:SSZ``.

    A value with an explicit offset is adjusted to UTC; a naive value is assumed UTC.
    """
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)  # assume UTC when naive
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_cell(value: str, kind: str, null_token: str = DEFAULT_NULL_TOKEN) -> str:
    """Canonicalize a single cell per its ``kind`` (``decimal`` | ``datetime`` | ``string``).

    The null-token check (R6) runs first so a null is never mis-parsed as a decimal/datetime.
    """
    if value == null_token:
        return NULL_SENTINEL
    if kind == "decimal":
        return _norm_decimal(value)
    if kind == "datetime":
        return _norm_datetime(value)
    # string / any other kind: pass through (R6 empty-string stays empty)
    return value


def normalize_tsv(raw: bytes) -> str:
    """Canonicalize a whole TSV blob: R1 (BOM strip) + R2 (LF) + R8 (deterministic row sort).

    ``utf-8-sig`` decoding strips a leading UTF-8 BOM if present. Rows are ordinal-sorted
    (``sorted`` compares by Unicode code point) so an unordered set never causes a false diff.
    """
    text = raw.decode("utf-8-sig")  # R1 strip BOM
    text = text.replace("\r\n", "\n").replace("\r", "\n")  # R2 force LF
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]  # drop trailing empty from final newline
    return "\n".join(sorted(lines))  # R8 deterministic ordinal order
