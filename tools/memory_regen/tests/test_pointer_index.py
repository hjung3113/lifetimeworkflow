"""RED tests for the pointer-index generator (Phase 16, MEM2-07 SC2, D-16-02).

These pin the generator API BEFORE it exists (Wave-1 / 16-02 implements
``tools/memory_regen/pointer_index.py``). Until then every test here ERRORs/FAILs at call time —
that is the intended RED state. The ``pointer_index`` import is deferred into each test body so the
module can still be COLLECTED (an unimplemented module must not hide the test names from the
interface-first contract the Wave-1 executor builds against).

Guarantees pinned (cloned from ``test_repo_map_determinism.py``, header + output paths swapped):
  (a) determinism — render twice AND write→hash→delete→regenerate are byte-identical (Pitfall 1),
      proven WITHOUT git diff because ``.memory/derived/`` is gitignored (Pitfall 2).
  (b) DERIVED marker + no timestamp + no raw float in the json+md body (D-16-02 / Pitfall 1).
  (c) no self-reference under ``.memory/derived/`` + word-boundaried slug (``plan`` ≠ ``planner``).
  (d) a committed syrupy snapshot over the tmp fixture = the determinism reference (NOT under
      ``.memory/``; the ``.ambr`` is generated when 16-02 first runs green, never pre-seeded here).
  (e) referrer shape — lists of ``{"file","line","kind"}``, ``kind in {"path","slug"}``, sorted.

Every generator call passes ``base_dir=``/``scan_roots=`` (and ``json_path=``/``md_path=`` for
writes) pointing under ``tmp_path`` so nothing ever leaks to the real ``.memory/derived/``.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_AGREEMENT_ITEM = ".memory/agreements/plan.md"


def _scan_roots(tree: Path) -> list[Path]:
    """The scan roots for the fixture: a recursive ``docs/`` tree + the single-file ``AGENTS.md``.

    ``.memory/derived/`` is deliberately excluded (self-reference churn guard, D-16-02).
    """
    return [tree / "docs", tree / "AGENTS.md"]


def _build(tree: Path) -> dict:
    from tools.memory_regen import pointer_index

    return pointer_index.build_index(base_dir=tree, scan_roots=_scan_roots(tree))


def _render(tree: Path) -> str:
    from tools.memory_regen import pointer_index

    return pointer_index.render_md(_build(tree))


def test_render_twice_is_byte_identical(tmp_pointer_scan_tree: Path) -> None:
    """render_md(build_index()) twice over the same tree yields identical text (Pitfall 1)."""
    assert _render(tmp_pointer_scan_tree) == _render(tmp_pointer_scan_tree)


def test_write_delete_regenerate_is_byte_identical(
    tmp_path: Path, tmp_pointer_scan_tree: Path
) -> None:
    """write → sha256 → delete → regenerate → identical hash (NOT git diff, Pitfall 2)."""
    from tools.memory_regen import pointer_index

    out_json = tmp_path / "derived" / "pointer-index.json"
    out_md = tmp_path / "derived" / "pointer-index.md"
    pointer_index.write(
        json_path=out_json,
        md_path=out_md,
        base_dir=tmp_pointer_scan_tree,
        scan_roots=_scan_roots(tmp_pointer_scan_tree),
    )
    digest_1 = hashlib.sha256(out_json.read_bytes()).hexdigest()
    out_json.unlink()
    assert not out_json.exists()
    pointer_index.write(
        json_path=out_json,
        md_path=out_md,
        base_dir=tmp_pointer_scan_tree,
        scan_roots=_scan_roots(tmp_pointer_scan_tree),
    )
    assert digest_1 == hashlib.sha256(out_json.read_bytes()).hexdigest()


def test_derived_header_and_no_timestamp(tmp_path: Path, tmp_pointer_scan_tree: Path) -> None:
    """The ``.md`` twin carries the DERIVED header; json+md carry no timestamp / raw float."""
    from tools.memory_regen import pointer_index

    assert (
        pointer_index.DERIVED_HEADER
        == "DERIVED — do not hand-edit (tools/memory_regen/pointer_index.py)"
    )
    out_json = tmp_path / "derived" / "pointer-index.json"
    out_md = tmp_path / "derived" / "pointer-index.md"
    pointer_index.write(
        json_path=out_json,
        md_path=out_md,
        base_dir=tmp_pointer_scan_tree,
        scan_roots=_scan_roots(tmp_pointer_scan_tree),
    )
    md = out_md.read_text(encoding="utf-8")
    assert md.splitlines()[0].startswith("# DERIVED — do not hand-edit")
    assert "pointer_index.py" in md.splitlines()[0]
    combined = md + out_json.read_text(encoding="utf-8")
    # No ISO-ish timestamp anywhere in a derived artifact.
    assert not re.search(r"\d{4}-\d{2}-\d{2}", combined), "no date/timestamp in a derived artifact"
    # No raw float (e.g. a score 0.1735...) — the index is rank/count only.
    assert not re.search(r"0\.\d{3,}", combined), "raw floats must not be printed"


def test_no_self_reference_and_no_false_positive(tmp_pointer_scan_tree: Path) -> None:
    """No referrer under ``.memory/derived/``; slug ``plan`` does NOT match token ``planner``."""
    index = _build(tmp_pointer_scan_tree)

    # (a) self-reference guard: nothing under .memory/derived/ is ever a referrer.
    for referrers in index.values():
        for ref in referrers:
            assert ".memory/derived/" not in ref["file"], "derived plane must be excluded from scan"

    # (b) word-boundary guard against the docs/guide.md fixture:
    #   line 3 "Follow the plan agreement ..."  -> slug hit (expected)
    #   line 4 "The planner subsystem ..."       -> decoy, must NOT hit
    refs = index.get(_AGREEMENT_ITEM, [])
    slug_lines = {
        ref["line"]
        for ref in refs
        if ref["kind"] == "slug" and ref["file"].endswith("docs/guide.md")
    }
    assert 3 in slug_lines, "the real 'plan' slug reference on line 3 must be recorded"
    assert 4 not in slug_lines, "'planner' on line 4 must NOT match the slug 'plan'"


def test_render_matches_committed_snapshot(tmp_pointer_scan_tree: Path, snapshot) -> None:
    """Committed .ambr snapshot pins render_md() over the tmp fixture = the determinism reference.

    The ``.ambr`` is intentionally NOT created in this Wave-0 plan; 16-02 generates it on first
    green run (avoids a stale/empty snapshot), so this fails until then — the intended RED state.
    """
    assert _render(tmp_pointer_scan_tree) == snapshot


def test_referrer_shape(tmp_pointer_scan_tree: Path) -> None:
    """Index values are sorted lists of ``{"file","line","kind"}`` with ``kind`` in the allow-set."""
    index = _build(tmp_pointer_scan_tree)
    assert isinstance(index, dict)
    for referrers in index.values():
        assert isinstance(referrers, list)
        for ref in referrers:
            assert set(ref) == {"file", "line", "kind"}
            assert isinstance(ref["file"], str)
            assert isinstance(ref["line"], int)
            assert ref["kind"] in {"path", "slug"}
        keys = [(ref["file"], ref["line"], ref["kind"]) for ref in referrers]
        assert keys == sorted(keys), "referrer lists must be deterministically sorted"
