"""RED tests for surface-and-confirm referential integrity (Phase 16, MEM2-07 SC3, D-16-03).

Pins the orphan flow of ``routes.retire_agreement`` BEFORE it exists (Wave-2/16-03 + 16-05
implement it). Until then every test ERRORs/FAILs at call time — the intended RED state. The
``routes`` import is deferred so the module still COLLECTS.

The pointer-index is injected via ``derived_dir`` (a seeded ``pointer-index.json`` under ``tmp_path``)
so the orphan check reads the SYNTHETIC index, never the real ``.memory/derived/``. The referrer
files live under ``tmp_path`` too — a confirmed retire must leave them byte-for-byte untouched
(D-16-03: surface + confirm, NEVER auto-rewrite external docs).

Behaviour pinned:
    - retire with referrers + confirm=False → 409 ``{"orphans":[{file,line,kind}]}``, writer NOT called
    - retire with confirm=True → proceeds via ``tools.agree.write.retire``; referrer files unchanged
    - the orphan ``file:line`` entries match the known references in the tmp fixture
"""

from __future__ import annotations

import json
from pathlib import Path

_ITEM = ".memory/agreements/zeta-proceed.md"


def _seed_referrer(tmp_path: Path) -> tuple[Path, Path]:
    """Create a tmp ``docs/guide.md`` referrer + a seeded ``derived/pointer-index.json`` for it.

    ``guide.md`` line 2 references the agreement PATH; the seeded index records exactly that
    ``file:line`` so the orphan surface is falsifiable against a known reference.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text(
        "# Guide\nSee .memory/agreements/zeta-proceed.md before acting.\n",
        encoding="utf-8",
    )
    derived = tmp_path / "derived"
    derived.mkdir()
    (derived / "pointer-index.json").write_text(
        json.dumps(
            {_ITEM: [{"file": "docs/guide.md", "line": 2, "kind": "path"}]},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return derived, docs


def test_orphan_blocks_without_confirm(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """Retire with referrers + no confirm → 409 with orphans; the writer is NOT called."""
    from tools.harness_lint import parse_frontmatter
    from tools.memory_ui import routes

    derived, _docs = _seed_referrer(tmp_path)
    target = tmp_agreements_tree / "zeta-proceed.md"
    before = target.read_text(encoding="utf-8")

    status, _headers, body = routes.retire_agreement(
        "zeta-proceed",
        agreements_dir=tmp_agreements_tree,
        derived_dir=derived,
        confirm=False,
    )
    assert status == 409
    payload = json.loads(body)
    assert payload.get("orphans"), "orphans must be surfaced when referrers exist"
    for orphan in payload["orphans"]:
        assert {"file", "line", "kind"} <= set(orphan)

    # Writer NOT called: the agreement is byte-unchanged and still active.
    assert target.read_text(encoding="utf-8") == before
    frontmatter, _ = parse_frontmatter(before)
    assert frontmatter["status"] == "active"


def test_confirmed_retire_proceeds_and_leaves_docs_untouched(
    tmp_path: Path, tmp_agreements_tree: Path
) -> None:
    """confirm=True retires via the writer; the referrer file is byte-for-byte unchanged."""
    from tools.harness_lint import parse_frontmatter
    from tools.memory_ui import routes

    derived, docs = _seed_referrer(tmp_path)
    referrer = docs / "guide.md"
    referrer_before = referrer.read_bytes()
    target = tmp_agreements_tree / "zeta-proceed.md"

    status, _headers, _body = routes.retire_agreement(
        "zeta-proceed",
        agreements_dir=tmp_agreements_tree,
        derived_dir=derived,
        confirm=True,
    )
    assert status == 200
    assert target.exists()  # flip in place, never delete
    frontmatter, _ = parse_frontmatter(target.read_text(encoding="utf-8"))
    assert frontmatter["status"] == "retired"

    # D-16-03: surface-and-confirm NEVER auto-rewrites the referrer.
    assert referrer.read_bytes() == referrer_before


def test_referrer_file_line_accuracy(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """The orphan list ``file:line`` entries match the known reference in the tmp docs fixture."""
    from tools.memory_ui import routes

    derived, _docs = _seed_referrer(tmp_path)
    status, _headers, body = routes.retire_agreement(
        "zeta-proceed",
        agreements_dir=tmp_agreements_tree,
        derived_dir=derived,
        confirm=False,
    )
    assert status == 409
    orphans = json.loads(body)["orphans"]
    entries = {(orphan["file"], orphan["line"]) for orphan in orphans}
    assert ("docs/guide.md", 2) in entries  # the known reference seeded in the fixture
