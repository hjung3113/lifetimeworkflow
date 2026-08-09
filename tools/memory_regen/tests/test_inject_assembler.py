"""Contract tests for the reframed SessionStart injection assembler."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.memory_regen import inject


def _dirs(tmp_path: Path) -> tuple[Path, Path]:
    derived, state = tmp_path / "derived", tmp_path / "state"
    derived.mkdir()
    state.mkdir()
    (derived / "contracts-index.md").write_text("contracts\n", encoding="utf-8")
    (derived / "repo-map.md").write_text("repo\n", encoding="utf-8")
    (state / "activeContext.md").write_text(
        '---\nupdated: "2026-01-02"\n---\n# state\n', encoding="utf-8"
    )
    return derived, state


def test_banner_is_data_scoped() -> None:
    banner = inject.BANNER.lower()
    assert all(token in banner for token in ("data", "contract", "adr"))
    assert not any(
        token in banner for token in ("provisional", "hint, not truth", "confirm before trusting")
    )


def test_default_payload_within_budget() -> None:
    assert len(inject.assemble()) <= 4000


def test_only_active_non_template_agreements_compose(tmp_agreements_tree: Path) -> None:
    (tmp_agreements_tree / "missing.md").write_text("# Missing\nNo status.\n", encoding="utf-8")
    block = inject._agreements_block(tmp_agreements_tree)
    assert "Ground claims" in block and "Proceed deliberately" in block
    assert (
        "Retired" not in block and "One-line working-style" not in block and "Missing" not in block
    )


def test_agreements_order_is_sorted_not_filesystem(tmp_agreements_tree: Path) -> None:
    block = inject._agreements_block(tmp_agreements_tree)
    assert block.index("Ground claims") < block.index("Proceed deliberately")


def test_overflow_degrades_to_pointer(tmp_agreements_tree: Path) -> None:
    for number in range(7):
        (tmp_agreements_tree / f"extra-{number}.md").write_text(
            f"---\nstatus: active\n---\n# Extra {number}\nA short rule.\n", encoding="utf-8"
        )
    assert inject._agreements_block(tmp_agreements_tree) == inject.AGREEMENTS_POINTER
    assert not any(char.isdigit() for char in inject.AGREEMENTS_POINTER)
    large = tmp_agreements_tree / "large.md"
    large.write_text("---\nstatus: active\n---\n# Large\n" + "x" * 800 + "\n", encoding="utf-8")
    assert inject._agreements_block(tmp_agreements_tree) == inject.AGREEMENTS_POINTER


def test_render_excludes_provenance(tmp_agreements_tree: Path) -> None:
    block = inject._agreements_block(tmp_agreements_tree)
    assert not any(value in block for value in ("provenance", "added:", "status:", "Related:"))


def test_agreements_header_states_scope_limit() -> None:
    assert "contracts/" in inject.AGREEMENTS_HEADER and "docs/adr/" in inject.AGREEMENTS_HEADER
    assert "never override" in inject.AGREEMENTS_HEADER.lower()


def test_agreements_reads_are_confined(tmp_agreements_tree: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("---\nstatus: active\n---\n# Outside\nDo not read.\n", encoding="utf-8")
    (tmp_agreements_tree / "escape.md").symlink_to(outside)
    assert "Outside" not in inject._agreements_block(tmp_agreements_tree)


def test_two_distinct_blocks_emitted(tmp_agreements_tree: Path, tmp_path: Path) -> None:
    derived, state = _dirs(tmp_path)
    payload = inject.assemble(
        derived_dir=derived, state_dir=state, agreements_dir=tmp_agreements_tree
    )
    assert inject.AGREEMENTS_HEADER in payload and inject.BANNER in payload
    assert payload.index(inject.AGREEMENTS_HEADER) < payload.index(inject.BANNER)


def test_agreements_banner_drift_never_dropped(tmp_agreements_tree: Path, tmp_path: Path) -> None:
    derived, state = _dirs(tmp_path)
    payload = inject.assemble(1, derived, state, tmp_agreements_tree)
    assert (
        inject.AGREEMENTS_HEADER in payload
        and inject.BANNER in payload
        and inject.DRIFT_HEADER in payload
    )


def test_pointer_is_progress_log_not_imperative() -> None:
    payload = inject.assemble()
    assert "progress log" in inject.ACTIVE_HEADER.lower()
    assert "confirm against contracts/ADR before trusting" not in payload


def test_updated_stamp_surfaced_verbatim(tmp_path: Path) -> None:
    derived, state = _dirs(tmp_path)
    assert "[updated: 2026-01-02]" in inject.assemble(derived_dir=derived, state_dir=state)


@pytest.mark.parametrize(
    "content", ["# no frontmatter\n", "---\nname: x\n---\n# missing\n", "---\n- list\n---\n# bad\n"]
)
def test_absent_stamp_degrades_gracefully(tmp_path: Path, content: str) -> None:
    derived, state = _dirs(tmp_path)
    (state / "activeContext.md").write_text(content, encoding="utf-8")
    assert "updated: unknown" in inject.assemble(derived_dir=derived, state_dir=state)
    (state / "activeContext.md").unlink()
    assert "updated: unknown" in inject.assemble(derived_dir=derived, state_dir=state)


def test_no_full_contract_schema_body_leaks() -> None:
    assert "$schema" not in inject.assemble()


def test_active_context_pointer_is_ordered_ahead_of_the_elastic_repo_map() -> None:
    """The fixed-size pointer must never be the section a growing repo map squeezes out.

    ``test_active_context_is_pointer_not_body`` only catches this when the LIVE repo map happens to
    sit exactly at the budget edge — it did, once, after an unrelated public symbol was added
    elsewhere in the tree, which is precisely how accidental that guard is. Ordering is the actual
    fix, so assert the ordering: whichever section comes last is the one the budget drops.
    """
    payload = inject.assemble()
    assert inject.ACTIVE_HEADER in payload
    assert payload.index(inject.ACTIVE_HEADER) < payload.index(inject.REPO_MAP_HEADER)
    # ...and putting the pointer first must not cost the whole map: the map is trimmed to fit,
    # not skipped. Dropping it entirely to save a 179-char pointer would be the worse trade.
    assert inject.REPO_MAP_HEADER in payload
    assert len(payload) <= 4000


def test_active_context_is_pointer_not_body(repo_root: Path) -> None:
    payload = inject.assemble()
    body = (repo_root / ".memory/state/activeContext.md").read_text(encoding="utf-8")
    assert (
        ".memory/state/activeContext.md" in payload
        and "## In flight" in body
        and "## In flight" not in payload
    )


def test_main_prints_capped_payload(capsys) -> None:
    assert inject.main([]) == 0
    out = capsys.readouterr().out.rstrip("\n")
    assert out.splitlines()[0] == inject.BANNER
    assert len(out) <= 4000


def _full_cap_agreements(tmp_path: Path) -> Path:
    agreements = tmp_path / "agreements"
    agreements.mkdir()
    for number in range(6):
        (agreements / f"entry-{number}.md").write_text(
            f"---\nstatus: active\n---\n# Entry {number}\n" + "x" * 70 + "\n",
            encoding="utf-8",
        )
    return agreements


def test_budget_holds_with_full_agreements_block(tmp_path: Path) -> None:
    derived, state = _dirs(tmp_path)
    agreements = _full_cap_agreements(tmp_path)
    payload = inject.assemble(derived_dir=derived, state_dir=state, agreements_dir=agreements)
    assert len(inject._agreements_block(agreements)) <= inject._AGREEMENTS_MAX_CHARS
    assert len(payload) <= 4000


def test_repo_map_survives_full_cap_agreements(tmp_path: Path) -> None:
    derived, state = _dirs(tmp_path)
    agreements = _full_cap_agreements(tmp_path)
    payload = inject.assemble(derived_dir=derived, state_dir=state, agreements_dir=agreements)
    assert inject.REPO_MAP_HEADER in payload
