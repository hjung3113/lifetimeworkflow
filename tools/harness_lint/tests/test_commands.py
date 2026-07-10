"""CMD-01..09 STRUCTURAL gate (D-05) — frontmatter validation of harness/commands/*.md.

Proves the golden-adjacent half of success criterion 3 structurally, without an opencode runtime:
every authored command carries valid frontmatter, a routing-trigger description (P7 — not a bare
label), a well-formed non-empty ``agent`` field, and a boolean ``subtask`` when present.

This validator is **glob-driven**: it discovers every ``harness/commands/*.md`` so the migration
commands added later (e.g. /new-contract-rule, /strangler-step, /docs-sync, and the Phase 5.7
lifecycle commands) are covered by the SAME test with no edits here — avoiding a cross-wave overlap.

STRUCTURAL ONLY: this test does NOT check whether the referenced agent FILE exists under
``harness/agents/``. The personas are authored by Plan 03 in the SAME wave 2, so a file-existence
assertion here would be a false cross-wave gate. That cross-file resolution is deferred to the
phase-level integration test ``test_agent_referential_integrity.py`` (Task 3), which runs green
under the full ``uv run pytest`` suite once all of wave 2 exists.

Parsing is delegated to the shared ``parse_frontmatter`` (Plan 02) — no per-test fence slicing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tools.harness_lint import parse_frontmatter

# test_commands.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_COMMANDS_DIR = _REPO_ROOT / "harness" / "commands"

# A routing-signal description must carry an invocation trigger token (P7 guard — mirrors agents).
_ROUTING_TRIGGERS = ("use", "when")

# A well-formed agent reference is a bare slug (lowercase alnum + single hyphens) — the same shape
# as an agent filename stem. This is a STRUCTURAL check (no path separators, no whitespace); it does
# NOT assert the target file exists (that is Task 3's phase-level integration test).
_AGENT_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# The eight golden-adjacent commands this plan authors (D-05 sequencing) MUST all be present.
EXPECTED_GOLDEN_ADJACENT = frozenset(
    {"build", "test", "lint", "golden", "golden-approve", "adr", "checkpoint", "component"}
)


def _command_files() -> list[Path]:
    return sorted(_COMMANDS_DIR.glob("*.md"))


def _load(path: Path) -> dict:
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm


def test_golden_adjacent_commands_present() -> None:
    """All eight golden-adjacent commands exist under harness/commands/ (D-05)."""
    names = {p.stem for p in _command_files()}
    missing = EXPECTED_GOLDEN_ADJACENT - names
    assert not missing, f"missing golden-adjacent commands: {sorted(missing)}"


@pytest.mark.parametrize("path", _command_files(), ids=lambda p: p.stem)
def test_frontmatter_parses(path: Path) -> None:
    """Frontmatter is present and parses to a non-empty mapping (valid frontmatter)."""
    fm = _load(path)
    assert isinstance(fm, dict) and fm, f"{path.stem}: missing or empty frontmatter"


@pytest.mark.parametrize("path", _command_files(), ids=lambda p: p.stem)
def test_description_is_routing_signal(path: Path) -> None:
    """description present, non-empty, carries a routing trigger token.

    P7 — not a bare label.
    """
    fm = _load(path)
    desc = str(fm.get("description", "")).strip()
    assert desc, f"{path.stem}: description missing or empty"
    lowered = desc.lower()
    assert any(tok in lowered for tok in _ROUTING_TRIGGERS), (
        f"{path.stem}: description lacks a routing trigger ({_ROUTING_TRIGGERS}) — reads as a label"
    )


@pytest.mark.parametrize("path", _command_files(), ids=lambda p: p.stem)
def test_agent_field_well_formed(path: Path) -> None:
    """An ``agent`` field is present, a non-empty string, and a well-formed slug (STRUCTURAL only).

    Does NOT check whether harness/agents/<agent>.md exists — that cross-file resolution is the
    phase-level integration test (test_agent_referential_integrity.py), because agents are authored
    by Plan 03 in the SAME wave 2.
    """
    fm = _load(path)
    agent = fm.get("agent")
    assert isinstance(agent, str) and agent.strip(), (
        f"{path.stem}: 'agent' field missing or not a non-empty string"
    )
    assert _AGENT_SLUG.match(agent), (
        f"{path.stem}: agent {agent!r} is not a well-formed slug (lowercase alnum + hyphens)"
    )


@pytest.mark.parametrize("path", _command_files(), ids=lambda p: p.stem)
def test_subtask_is_boolean_when_present(path: Path) -> None:
    """Any ``subtask`` value, if present, is a boolean."""
    fm = _load(path)
    if "subtask" in fm:
        assert isinstance(fm["subtask"], bool), (
            f"{path.stem}: subtask must be a boolean, got {type(fm['subtask']).__name__}"
        )
