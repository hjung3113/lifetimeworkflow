"""Tests for the /docs-sync generator (DOCS-03, D-06, ROADMAP success criterion 4).

Pins the guarantees the derived reference quadrant depends on:
  (a) determinism — render() twice AND generate→hash→delete→regenerate are byte-identical
      (Pitfall P12); proven WITHOUT git diff via sha256 over a tmp_path out dir + a committed
      syrupy snapshot (the canonical determinism reference).
  (b) confinement — every write() target stays under docs/reference/; a traversal-shaped path is
      refused (T-03-21, mirrors golden_runner._confine).
  (c) structure — every page starts with the DERIVED "do not hand-edit" marker; the five seed
      schemas map 1:1 to five reference pages; format-conventions carries the §4.3–4.6 block.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools.docs_sync import generate as docs_sync

# The seed schemas map 1:1 to reference pages (DOCS-03). After the 05-03 domain move (GEN-01) the
# relocated domain schemas moved to the log-parser example, so the CORE contracts tree now holds only
# the generic §4.3–4.6 convention page (format-conventions) and the domain-neutral generic default
# instance (greeting, GEN-02, 05-02).
EXPECTED_PAGES = frozenset(
    {
        "format-conventions",
        "greeting",
    }
)


# ---- (a) determinism: byte-identical, proven without git diff --------------------------------


def test_render_is_deterministic_over_real_tree() -> None:
    """render() twice over each real schema is byte-identical (no timestamp/float, Pitfall P12)."""
    for name, schema in docs_sync.iter_schemas():
        assert docs_sync.render(name, schema) == docs_sync.render(name, schema)


def test_generate_delete_regenerate_is_byte_identical(tmp_path: Path) -> None:
    """generate → sha256 → delete → regenerate → identical hashes.

    (NOT git diff), against tmp_path.
    """
    out = tmp_path / "reference"

    first = docs_sync.write(out=out)
    digest_1 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first}

    for p in first:
        p.unlink()
        assert not p.exists()

    second = docs_sync.write(out=out)
    digest_2 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in second}

    assert digest_1 == digest_2


def test_render_matches_committed_snapshot(snapshot) -> None:
    """A committed syrupy snapshot pins render() over the real contracts tree (determinism ref)."""
    combined = "\n".join(
        f"===== {name} =====\n{docs_sync.render(name, schema)}"
        for name, schema in docs_sync.iter_schemas()
    )
    assert combined == snapshot


# ---- (b) confinement: writes stay under docs/reference/, traversal refused --------------------


def test_write_targets_stay_under_out_dir(tmp_path: Path) -> None:
    """Every write() target resolves under the out dir — no page escapes the reference quadrant."""
    out = tmp_path / "reference"
    written = docs_sync.write(out=out)
    out_resolved = out.resolve()
    assert written, "generator wrote nothing"
    for path in written:
        # Raises ValueError if the path is not under out_resolved.
        path.resolve().relative_to(out_resolved)


def test_confine_refuses_traversal(tmp_path: Path) -> None:
    """A traversal-shaped target is refused rather than escaping docs/reference/ (T-03-21)."""
    base = tmp_path / "reference"
    base.mkdir()
    with pytest.raises(docs_sync.DocsSyncError):
        docs_sync._confine(base / ".." / "escape.md", base)


# ---- (c) structure: DERIVED marker, 5 pages, conventions block -------------------------------


def test_every_page_starts_with_derived_marker(tmp_path: Path) -> None:
    """Each generated page's first line is the DERIVED 'do not hand-edit' marker (D-06/T-03-22)."""
    written = docs_sync.write(out=tmp_path / "reference")
    for path in written:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert docs_sync.DERIVED_HEADER in first_line
        assert "do not hand-edit" in first_line.lower()


def test_seed_schemas_map_one_to_one_to_pages(tmp_path: Path) -> None:
    """Every seed schema (incl. the generic greeting sample) maps 1:1 to a reference page."""
    written = docs_sync.write(out=tmp_path / "reference")
    names = {p.stem for p in written}
    assert names == EXPECTED_PAGES


def test_format_conventions_page_has_conventions_block(tmp_path: Path) -> None:
    """The format-conventions page carries the §4.3–4.6 canonicalization block (BOM/LF/decimal…)."""
    out = tmp_path / "reference"
    docs_sync.write(out=out)
    text = (out / "format-conventions.md").read_text(encoding="utf-8")
    assert "Canonicalization conventions (§4.3" in text
    # A couple of the const invariants must be materialized from the schema.
    assert "**bom**" in text
    assert "**newline**" in text


def test_rows_are_sorted_and_typed() -> None:
    """rows() returns (name, type, required, enum/const, description).

    Names sorted, required bool.
    """
    # Repointed off a relocated domain schema (05-03 domain move) to a schema that STAYS in the
    # core tree — format-conventions carries top-level const props, so rows() coverage is preserved.
    _, schema = next((n, s) for n, s in docs_sync.iter_schemas() if n == "format-conventions")
    table = docs_sync.rows(schema)
    assert table, "format-conventions yielded no rows"
    names = [r[0] for r in table]
    assert names == sorted(names)
    for name, typ, required, _enum_const, _desc in table:
        assert isinstance(name, str) and name
        assert isinstance(typ, str) and typ
        assert isinstance(required, bool)
