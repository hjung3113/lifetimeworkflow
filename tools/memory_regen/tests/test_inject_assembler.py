"""Unit tests for the shared session-start injection assembler (HOOK-05, D-02/D-07, Crit-4).

`inject.assemble()` is the ONE payload source both runtimes (Claude now, opencode deferred)
honor. These tests pin the injection *contract*: a capped, banner-first, drift-aware,
pointer-only payload that priority-truncates whole low-priority sections (repo-map dropped
before banner/drift) rather than blind mid-line cutting, and that never leaks full contract
schema bodies (T-02-06 / P13).
"""

from __future__ import annotations

from pathlib import Path

from tools.memory_regen import inject

# ---- banner / cap (D-02, D-07 Crit-4) --------------------------------------------------------


def test_first_line_is_provisional_banner() -> None:
    """Payload leads with the provisional banner (D-02 — non-ignorable, banner-first)."""
    payload = inject.assemble()
    first = payload.splitlines()[0]
    assert first == inject.BANNER
    assert "provisional" in first.lower()


def test_banner_asserts_adr_contract_override() -> None:
    """Banner declares ADR/contracts override .memory/ on conflict (D-02 / P13)."""
    banner = inject.BANNER.lower()
    assert "provisional" in banner
    assert "contract" in banner
    assert "adr" in banner
    assert "override" in banner or "overrides" in banner


def test_default_payload_within_budget() -> None:
    """assemble(budget_chars=4000) is at most 4000 chars (~1k tokens soft cap, D-07)."""
    payload = inject.assemble()
    assert len(payload) <= 4000


def test_generous_budgets_are_respected() -> None:
    """For any budget comfortably above the mandatory banner+drift, len(payload) <= budget."""
    for budget in (1500, 2000, 3000, 4000):
        payload = inject.assemble(budget_chars=budget)
        assert len(payload) <= budget, f"payload exceeded budget {budget}"


# ---- priority-truncation (D-07 — whole sections, reverse priority) ---------------------------


def test_repo_map_present_under_generous_budget(tmp_path: Path) -> None:
    """When a repo-map derived file exists and budget allows, its section is included."""
    derived = tmp_path / "derived"
    derived.mkdir()
    (derived / "repo-map.md").write_text(
        "DERIVED — do not hand-edit\n1. tools/foo.py\n2. libs/bar.py\n", encoding="utf-8"
    )
    payload = inject.assemble(budget_chars=4000, derived_dir=derived)
    assert inject.REPO_MAP_HEADER in payload


def test_tiny_budget_drops_repo_map_but_keeps_banner_and_drift(tmp_path: Path) -> None:
    """Over budget → repo-map (priority 3) dropped; banner (0) + drift (1) survive (D-07)."""
    derived = tmp_path / "derived"
    derived.mkdir()
    (derived / "repo-map.md").write_text(
        "DERIVED — do not hand-edit\n1. tools/foo.py\n2. libs/bar.py\n", encoding="utf-8"
    )
    # Budget = just enough for banner + drift, nothing more.
    mandatory = len(inject.BANNER) + len(inject._drift_summary()) + 1
    payload = inject.assemble(budget_chars=mandatory + 4, derived_dir=derived)
    assert inject.BANNER in payload
    assert inject.DRIFT_HEADER in payload
    assert inject.REPO_MAP_HEADER not in payload, "repo-map must be priority-truncated first"


def test_banner_and_drift_never_dropped_even_over_budget() -> None:
    """Even at an absurdly tiny budget, banner + drift are never dropped (priority 0/1)."""
    payload = inject.assemble(budget_chars=1)
    assert inject.BANNER in payload
    assert inject.DRIFT_HEADER in payload


# ---- pointer-only / no full contract bodies (T-02-06 / P13) ----------------------------------


def test_no_full_contract_schema_body_leaks() -> None:
    """The payload injects index summaries/pointers only — never a JSON schema body (T-02-06)."""
    payload = inject.assemble()
    assert "$schema" not in payload


def test_active_context_is_pointer_not_body(repo_root: Path) -> None:
    """activeContext appears as a pointer PATH, never its file contents (P13)."""
    payload = inject.assemble()
    assert ".memory/state/activeContext.md" in payload
    body = (repo_root / ".memory" / "state" / "activeContext.md").read_text(encoding="utf-8")
    # A distinctive line from the committed body must NOT appear in the injected payload.
    distinctive = "## In flight"
    assert distinctive in body, "fixture guard: expected marker missing from activeContext.md"
    assert distinctive not in payload, "activeContext BODY leaked — inject a pointer only"


def test_contracts_summary_degrades_when_index_absent(tmp_path: Path) -> None:
    """When the contracts-index derived file is absent, a short 'pending' line is emitted."""
    empty_derived = tmp_path / "derived"
    empty_derived.mkdir()
    payload = inject.assemble(derived_dir=empty_derived)
    assert "pending" in payload.lower()


# ---- CLI ------------------------------------------------------------------------------------


def test_main_prints_banner_first(capsys) -> None:
    """`python -m tools.memory_regen.inject` prints a banner-first, capped payload."""
    rc = inject.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.splitlines()[0] == inject.BANNER
    assert len(out.rstrip("\n")) <= 4000
