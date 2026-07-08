"""Corpus parity test — Python core vs the shared (raw, canonical) fixture corpus (D-04).

Loads EVERY entry in ``libs/normalize-fixtures/*.json`` (the same corpus the .NET xunit suite
loads) and asserts the Python core reproduces each ``canonical`` value. Any per-language drift
fails here. The .NET half asserts the identical corpus — identical output across both proves
cross-language parity.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

# Make the `normalize` package importable (libs/python is a virtual uv workspace member,
# not pip-installed, so add it to sys.path explicitly).
_LIBS_PYTHON = Path(__file__).resolve().parents[2]  # tests -> normalize -> python
if str(_LIBS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_LIBS_PYTHON))

from normalize.core import normalize_cell, normalize_tsv  # noqa: E402

# libs/normalize-fixtures (shared corpus). parents[3] == libs/.
_FIXTURES_DIR = Path(__file__).resolve().parents[3] / "normalize-fixtures"


def _load_corpus() -> list[tuple[str, dict]]:
    files = sorted(_FIXTURES_DIR.glob("*.json"))
    assert files, f"no fixture corpus found under {_FIXTURES_DIR}"
    cases: list[tuple[str, dict]] = []
    for f in files:
        entries = json.loads(f.read_text(encoding="utf-8"))
        for entry in entries:
            cases.append((f"{f.stem}::{entry['name']}", entry))
    return cases


_CORPUS = _load_corpus()


def test_corpus_is_nonempty():
    # Guard against a silently-empty corpus making the parametrized test vacuously pass.
    assert len(_CORPUS) >= 4


@pytest.mark.parametrize("case_id,entry", _CORPUS, ids=[c[0] for c in _CORPUS])
def test_python_core_reproduces_canonical(case_id: str, entry: dict):
    kind = entry["kind"]
    expected = entry["canonical"]
    if kind == "tsv":
        raw = base64.b64decode(entry["raw_b64"])
        actual = normalize_tsv(raw)
    else:
        actual = normalize_cell(entry["raw"], kind)
    assert actual == expected, f"{case_id}: got {actual!r}, expected {expected!r}"
