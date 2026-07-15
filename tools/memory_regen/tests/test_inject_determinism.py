"""Determinism regression net for the SessionStart assembler (SC2/SC3).

This backfills the byte-identity guarantee claimed by ``inject.py`` before the
Phase 13 reframe, so it protects that change instead of post-hoc ratifying it.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from tools.memory_regen import inject

from tools.memory_regen.tests.conftest import _AGREEMENTS_CREATION_ORDER


def _fixture_dirs(tmp_path: Path) -> tuple[Path, Path]:
    derived = tmp_path / "derived"
    state = tmp_path / "state"
    derived.mkdir()
    state.mkdir()
    (derived / "contracts-index.md").write_text("contracts fixture\n", encoding="utf-8")
    (derived / "repo-map.md").write_text("repo fixture\n", encoding="utf-8")
    (state / "activeContext.md").write_text("# fixture\n", encoding="utf-8")
    return derived, state


def test_assemble_is_byte_identical(tmp_path: Path, tmp_agreements_tree: Path) -> None:
    """Two assembles over the same fixture tree have identical SHA-256 digests."""
    derived, state = _fixture_dirs(tmp_path)
    first = inject.assemble(
        derived_dir=derived, state_dir=state, agreements_dir=tmp_agreements_tree
    )
    second = inject.assemble(
        derived_dir=derived, state_dir=state, agreements_dir=tmp_agreements_tree
    )
    assert (
        hashlib.sha256(first.encode("utf-8")).hexdigest()
        == hashlib.sha256(second.encode("utf-8")).hexdigest()
    )


def test_assemble_delete_regenerate_is_byte_identical(tmp_path: Path) -> None:
    """assemble → hash → delete → assemble → hash is byte-identical."""
    derived, state = _fixture_dirs(tmp_path)
    output = tmp_path / "payload.txt"
    output.write_text(inject.assemble(derived_dir=derived, state_dir=state), encoding="utf-8")
    digest_1 = hashlib.sha256(output.read_bytes()).hexdigest()
    output.unlink()
    assert not output.exists()
    output.write_text(inject.assemble(derived_dir=derived, state_dir=state), encoding="utf-8")
    digest_2 = hashlib.sha256(output.read_bytes()).hexdigest()
    assert digest_1 == digest_2


def test_payload_matches_snapshot(snapshot, monkeypatch, tmp_path: Path) -> None:
    """A hermetic committed snapshot pins the fixed-fixture payload."""
    derived, state = _fixture_dirs(tmp_path)
    monkeypatch.setattr(
        inject,
        "_drift_summary",
        lambda: f"{inject.DRIFT_HEADER}\ncontract-drift: fixed fixture",
    )
    payload = inject.assemble(derived_dir=derived, state_dir=state)
    assert str(tmp_path) not in payload
    assert payload == snapshot


def test_inject_module_has_no_wallclock(repo_root: Path) -> None:
    """The assembler reads authored freshness data; it never computes wall-clock time."""
    text = (repo_root / "tools/memory_regen/inject.py").read_text(encoding="utf-8")
    for token in ("datetime", "date.today", ".now()", "time.time", "time.monotonic"):
        assert token not in text


def test_hook_wrappers_have_no_wallclock(repo_root: Path) -> None:
    """Runtime envelopes must not add a clock to an otherwise deterministic payload."""
    shell = (repo_root / ".claude/hooks/memory-inject.sh").read_text(encoding="utf-8")
    assert "$(date" not in shell
    assert "`date" not in shell
    assert not re.search(r"^\s*date\b", shell, flags=re.MULTILINE)
    assert "gsd-check-update" in shell  # proves the gate avoids a bare-date false positive
    ts = (repo_root / "harness/plugins/session-inject.ts").read_text(encoding="utf-8")
    assert "Date.now" not in ts
    assert "new Date" not in ts


def test_tmp_agreements_tree_fixture_shape(tmp_agreements_tree: Path) -> None:
    """The synthetic tree remains a meaningful, non-alphabetical test double."""
    assert {p.name for p in tmp_agreements_tree.glob("*.md")} == {
        "README.md",
        "_TEMPLATE.md",
        "alpha-ground.md",
        "middle-retired.md",
        "zeta-proceed.md",
    }
    template = (tmp_agreements_tree / "_TEMPLATE.md").read_text(encoding="utf-8")
    assert "status: active" in template
    assert "<One-line working-style or methodology rule.>" in template
    assert "status: retired" in (tmp_agreements_tree / "middle-retired.md").read_text(
        encoding="utf-8"
    )
    assert not (tmp_agreements_tree / "README.md").read_text(encoding="utf-8").startswith("---")
    assert _AGREEMENTS_CREATION_ORDER != tuple(sorted(_AGREEMENTS_CREATION_ORDER))
