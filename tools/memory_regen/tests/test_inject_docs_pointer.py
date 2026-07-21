"""The conditional one-line docs-staleness pointer in the SessionStart payload (DOCSUP-04, D-11).

Five invariants, each of which the research named as a way this change can break the injector:

1. ZERO ITEMS IS BYTE-IDENTICAL to today's payload — an empty section string is skipped at
   ``inject.py:181``, so a queue that is absent or empty must contribute nothing at all.
2. AT MOST TWO LINES by construction, regardless of how large the queue grows — the reason the
   ~4000-char budget tests stay safe.
3. DROPPABLE — the never-drop tuple is asserted equal to its exact literal, and the docs section is
   shown dropped under a squeezed budget while the four protected sections survive.
4. READS THE ``derived_dir`` PARAMETER, never a module constant — otherwise the committed snapshot
   absorbs live repo state (research Pitfall 3).
5. NEVER RECOMPUTES THE GUARD — proven by monkeypatching ``classify`` to raise; a guard call would
   put a ``git`` subprocess and a full corpus walk on the session-start hot path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.docs_guard import guard
from tools.memory_regen import docs_staleness, inject

# The exact literal the never-drop tuple must remain. Spelled once, here, so the assertion cannot
# drift from what it is guarding.
NEVER_DROP_LITERAL = '("agreements", "banner", "drift", "task")'


def _dirs(tmp_path: Path) -> tuple[Path, Path]:
    derived, state = tmp_path / "derived", tmp_path / "state"
    derived.mkdir(parents=True)
    state.mkdir(parents=True)
    (derived / "contracts-index.md").write_text("contracts\n", encoding="utf-8")
    (derived / "repo-map.md").write_text("repo\n", encoding="utf-8")
    (state / "activeContext.md").write_text(
        '---\nupdated: "2026-01-02"\n---\n# state\n', encoding="utf-8"
    )
    return derived, state


def _queue(derived: Path, count: int) -> None:
    """Write a rendered queue of ``count`` synthetic rows into ``derived``."""
    rows = [
        (
            f"binding-{index:03d}",
            f"docs/how-to/{index:03d}.md",
            "STALE_REQUIRED",
            "required",
            "updated",
            "(none)",
        )
        for index in range(count)
    ]
    (derived / "docs-staleness.md").write_text(docs_staleness.render(rows), encoding="utf-8")


# ---- 1. zero items is byte-identical ---------------------------------------------------------


def test_docs_pointer_is_empty_without_a_queue_file(tmp_path: Path) -> None:
    """An absent queue file yields "", which inject.py:181 skips outright."""
    derived, _state = _dirs(tmp_path)
    assert inject._docs_staleness_pointer(derived) == ""


def test_docs_pointer_is_empty_for_a_zero_row_queue(tmp_path: Path) -> None:
    """A rendered-but-empty queue also yields "" — the injector keys off the ROW COUNT."""
    derived, _state = _dirs(tmp_path)
    _queue(derived, 0)
    assert inject._docs_staleness_pointer(derived) == ""


def test_zero_item_payload_is_byte_identical(tmp_path: Path) -> None:
    """Absent queue and empty queue produce the SAME payload, and neither carries the header."""
    derived_a, state_a = _dirs(tmp_path / "a")
    derived_b, state_b = _dirs(tmp_path / "b")
    _queue(derived_b, 0)
    payload_a = inject.assemble(derived_dir=derived_a, state_dir=state_a)
    payload_b = inject.assemble(derived_dir=derived_b, state_dir=state_b)
    assert payload_a == payload_b
    assert inject.DOCS_HEADER not in payload_a


# ---- 2. at most two lines, however large the queue grows -------------------------------------


def test_docs_pointer_is_at_most_two_lines(tmp_path: Path) -> None:
    """Fifty queue rows still render a header plus ONE summary line — never a row per binding."""
    derived, _state = _dirs(tmp_path)
    _queue(derived, 50)
    text = inject._docs_staleness_pointer(derived)
    assert text.count("\n") <= 1
    assert text.startswith(inject.DOCS_HEADER)
    assert "50 human doc(s) need review" in text
    assert ".memory/derived/docs-staleness.md" in text
    assert "binding-000" not in text  # pointer only — never the queue's own rows


def test_docs_pointer_counts_only_data_rows(tmp_path: Path) -> None:
    """The table's header and separator lines are never counted as obligations."""
    derived, _state = _dirs(tmp_path)
    _queue(derived, 1)
    assert "1 human doc(s) need review" in inject._docs_staleness_pointer(derived)


# ---- 3. droppable, and the never-drop tuple is untouched -------------------------------------


def test_never_drop_tuple_is_unchanged(repo_root: Path) -> None:
    """The four-element never-drop tuple at inject.py:184 is verbatim what it was (T-28-32)."""
    text = (repo_root / "tools/memory_regen/inject.py").read_text(encoding="utf-8")
    assert f"if name not in {NEVER_DROP_LITERAL}" in text
    assert "budget_chars: int = 4000" in text


def test_docs_pointer_is_droppable(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """Under a squeezed budget the docs section is dropped; the four protected ones survive."""
    derived, state = _dirs(tmp_path)
    _queue(derived, 3)
    payload = inject.assemble(
        budget_chars=1, derived_dir=derived, state_dir=state, agreements_dir=tmp_agreements_tree
    )
    assert inject.DOCS_HEADER not in payload
    assert inject.BANNER in payload
    assert inject.DRIFT_HEADER in payload
    assert inject.AGREEMENTS_HEADER.splitlines()[0] in payload


def test_docs_pointer_present_under_the_default_budget(tmp_path: Path) -> None:
    """With room to spare the section IS surfaced, so the droppability test is not vacuous."""
    derived, state = _dirs(tmp_path)
    _queue(derived, 3)
    payload = inject.assemble(derived_dir=derived, state_dir=state)
    assert inject.DOCS_HEADER in payload
    assert payload.index(inject.CONTRACTS_HEADER) < payload.index(inject.DOCS_HEADER)
    assert payload.index(inject.DOCS_HEADER) < payload.index(inject.REPO_MAP_HEADER)


# ---- 4. the derived_dir parameter, not a module constant -------------------------------------


def test_docs_pointer_uses_derived_dir_parameter(tmp_path: Path) -> None:
    """The pointer reflects the FIXTURE queue, and no tmp_path leaks into the payload."""
    derived, state = _dirs(tmp_path)
    _queue(derived, 7)
    payload = inject.assemble(derived_dir=derived, state_dir=state)
    assert "7 human doc(s) need review" in payload
    assert str(tmp_path) not in payload


# ---- 5. never recomputes the guard -----------------------------------------------------------


def test_docs_pointer_does_not_recompute_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A guard call on the session-start hot path would surface here as an exception."""

    def _explode(*args: object, **kwargs: object) -> dict:
        raise AssertionError("assemble() must never recompute the docs guard")

    monkeypatch.setattr(guard, "classify", _explode)
    derived, state = _dirs(tmp_path)
    _queue(derived, 2)
    payload = inject.assemble(derived_dir=derived, state_dir=state)
    assert "2 human doc(s) need review" in payload


def test_inject_never_imports_docs_guard(repo_root: Path) -> None:
    """Static proof of the same boundary: inject.py names no guard module at all."""
    text = (repo_root / "tools/memory_regen/inject.py").read_text(encoding="utf-8")
    assert "docs_guard" not in text


# ---- no double-reporting of contract drift ---------------------------------------------------


def test_docs_pointer_mentions_no_drift(tmp_path: Path) -> None:
    """The payload already carries a never-dropped drift section; a third surfacing would double."""
    derived, _state = _dirs(tmp_path)
    _queue(derived, 4)
    text = inject._docs_staleness_pointer(derived).lower()
    assert "drift" not in text
    assert "contract" not in text
