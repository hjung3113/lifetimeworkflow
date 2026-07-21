"""POLY-01 corpus-parity — the linter's canonical target IS ``normalize.core`` (D-02/D-03).

Phase-4 success criterion 2 requires the polyglot linter to *reuse* the Phase-1 normalization
core "built once, not re-implemented". This proves it two ways:

1. **Identity** — the ``normalize_cell`` / ``normalize_tsv`` the linter module holds are the
   very same function objects as ``normalize.core``'s (never a second, drifting copy).
2. **Corpus** — for every entry in the shared ``libs/normalize-fixtures/*.json`` corpus, the
   canonical target the linter compares against reproduces the corpus ``canonical`` exactly —
   the same corpus that cross-validates the Python and .NET cores (D-04).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from normalize.core import normalize_cell, normalize_tsv

from tools.polyglot_lint import lint

_FIXTURES = Path(__file__).resolve().parents[3] / "libs" / "normalize-fixtures"


def _load(name: str) -> list[dict]:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_linter_reuses_shared_core_not_a_reimplementation() -> None:
    # The linter must import + call normalize.core — never ship a second normalizer (D-03).
    assert lint.normalize_cell is normalize_cell
    assert lint.normalize_tsv is normalize_tsv


@pytest.mark.parametrize(
    "fixture", ["decimal_locale.json", "null_vs_empty.json", "tz_iso8601.json"]
)
def test_cell_corpus_parity(fixture: str) -> None:
    for entry in _load(fixture):
        got = lint.normalize_cell(entry["raw"], entry["kind"])
        assert got == entry["canonical"], f"{fixture}:{entry['name']}"


def test_tsv_corpus_parity() -> None:
    for entry in _load("bom_crlf.json"):
        raw = base64.b64decode(entry["raw_b64"])
        got = lint.normalize_tsv(raw)
        assert got == entry["canonical"], entry["name"]
