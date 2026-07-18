"""RED tests for the pure route functions (Phase 16, MEM2-07 SC1, D-16-04).

These pin the ``tools.memory_ui.routes`` API BEFORE it exists (Wave-2 / 16-03 implements EXACTLY
these signatures). Until then every test ERRORs/FAILs at call time — the intended RED state. The
``routes`` import is deferred into each test body so the module can still be COLLECTED.

Every route call threads injected plane dirs (``state_dir=``/``agreements_dir=``/``derived_dir=``)
from the synthetic ``tmp_agreements_tree`` corpus + tmp state — so NO test ever writes a real
agreement, touches the real ``.memory/`` planes, or opens a socket (16-RESEARCH Pitfall 2).

Pinned signatures (all return ``(status:int, headers:dict, body:bytes)``):
    list_items(*, state_dir, agreements_dir, show_retired=False)
    view_item(item_id, *, state_dir, agreements_dir)
    add_agreement(slug, title, rule, *, because, related=None, agreements_dir, derived_dir)
    retire_agreement(slug, *, agreements_dir, derived_dir, confirm=False)
    save_progress(item_id, body_text, *, state_dir)
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def _state_dir(tmp_path: Path) -> Path:
    """A tmp ``.memory/state`` with the two editable progress files (extra key to prove preserve)."""
    state = tmp_path / "state"
    state.mkdir()
    (state / "activeContext.md").write_text(
        '---\nupdated: "2026-07-16"\n---\n\n# Active context\n\nSession log.\n',
        encoding="utf-8",
    )
    (state / "progress.md").write_text(
        '---\nupdated: "2026-07-16"\nowner: "harness"\n---\n\n# Progress\n\ntiny.\n',
        encoding="utf-8",
    )
    return state


def test_list_items(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """Lists exactly the two state files + active agreements; show_retired appends retired ones."""
    from tools.memory_ui import routes

    state = _state_dir(tmp_path)
    status, _headers, body = routes.list_items(state_dir=state, agreements_dir=tmp_agreements_tree)
    assert status == 200
    text = body.decode("utf-8")
    assert "activeContext.md" in text and "progress.md" in text
    assert "alpha-ground" in text and "zeta-proceed" in text  # active agreements
    assert "middle-retired" not in text  # retired hidden by default
    assert "_TEMPLATE" not in text and "README" not in text  # excluded corpus entries

    status2, _headers2, body2 = routes.list_items(
        state_dir=state, agreements_dir=tmp_agreements_tree, show_retired=True
    )
    assert status2 == 200
    assert "middle-retired" in body2.decode("utf-8")  # appended when show_retired=True


def test_view_item(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """Returns 200 with the item body for a state file and for an agreement."""
    from tools.memory_ui import routes

    state = _state_dir(tmp_path)
    status, _headers, body = routes.view_item(
        "progress.md", state_dir=state, agreements_dir=tmp_agreements_tree
    )
    assert status == 200
    assert b"tiny." in body

    status_a, _headers_a, body_a = routes.view_item(
        "zeta-proceed", state_dir=state, agreements_dir=tmp_agreements_tree
    )
    assert status_a == 200
    assert b"Proceed deliberately" in body_a


def test_edit_calls_agree_writer(tmp_path: Path, tmp_agreements_tree: Path, monkeypatch) -> None:
    """An agreement add routes through ``tools.agree.write`` (spy) — no direct file write in routes.

    Wave-2 must call the writer module-qualified (``agree_write.add(...)``, per 16-RESEARCH
    Pattern 3) so this ``tools.agree.write.add`` patch is observed.
    """
    from tools.agree import write as agree_write
    from tools.memory_ui import routes

    derived = tmp_path / "derived"
    derived.mkdir()
    calls: list[tuple] = []
    real_add = agree_write.add

    def _spy_add(*args, **kwargs):
        calls.append((args, kwargs))
        return real_add(*args, **kwargs)

    monkeypatch.setattr(agree_write, "add", _spy_add)

    routes.add_agreement(
        "new-rule",
        "New rule",
        "Do the agreed thing.",
        because="the user said keep this",
        agreements_dir=tmp_agreements_tree,
        derived_dir=derived,
    )
    assert calls, (
        "add_agreement must delegate to tools.agree.write.add (never write files directly)"
    )


def test_add_blank_because_refuses(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """Blank ``because`` surfaces AgreementRefused as a non-200 with the REFUSED message; no write."""
    from tools.memory_ui import routes

    derived = tmp_path / "derived"
    derived.mkdir()
    before = sorted(p.name for p in tmp_agreements_tree.glob("*.md"))
    status, _headers, body = routes.add_agreement(
        "blank-because",
        "Blank because",
        "Should never be written.",
        because="",
        agreements_dir=tmp_agreements_tree,
        derived_dir=derived,
    )
    assert status != 200
    assert b"REFUSED:" in body  # verbatim anti-invent message surfaced to the page
    after = sorted(p.name for p in tmp_agreements_tree.glob("*.md"))
    assert before == after, "a refused add must write NOTHING"


def test_retire_flips_in_place(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """A confirmed retire (no referrers) leaves the file present with ``status: retired``."""
    from tools.harness_lint import parse_frontmatter
    from tools.memory_ui import routes

    derived = tmp_path / "derived"
    derived.mkdir()  # empty index → no orphans → retire proceeds
    target = tmp_agreements_tree / "zeta-proceed.md"
    status, _headers, _body = routes.retire_agreement(
        "zeta-proceed", agreements_dir=tmp_agreements_tree, derived_dir=derived, confirm=True
    )
    assert status == 200
    assert target.exists(), "retire flips status in place — it NEVER deletes"
    frontmatter, _ = parse_frontmatter(target.read_text(encoding="utf-8"))
    assert frontmatter["status"] == "retired"


def test_progress_save_stamps_quoted_date(tmp_path: Path) -> None:
    """save_progress rewrites the body and sets a QUOTED ``updated:`` date; other keys preserved."""
    from tools.memory_ui import routes

    state = _state_dir(tmp_path)
    target = state / "progress.md"
    status, _headers, _body = routes.save_progress(
        "progress.md", "# Progress\n\nnew body line.\n", state_dir=state
    )
    assert status == 200
    text = target.read_text(encoding="utf-8")
    # Quoted-string scalar so it round-trips as a string, not a YAML date object (checkpoint.md).
    assert re.search(r'updated:\s*"\d{4}-\d{2}-\d{2}"', text), "updated: must be a quoted ISO date"
    assert "new body line." in text  # body rewritten
    assert "harness" in text  # the pre-existing 'owner' frontmatter key is preserved
