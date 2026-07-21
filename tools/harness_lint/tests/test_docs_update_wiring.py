"""DOCSUP-06 structural gate — pins the `/docs-update` + `docs-upkeep` wiring.

Plan 29-03 authored a THIN command over the already-coded `tools.docs_guard` plus one skill
carrying the runbook. Most of that surface's correctness is about what it does NOT contain, so this
lint asserts absences as hard as presences:

- the command names `tools.docs_guard` (D-04 — the data source is the guard, re-run with fixed
  argv, and never the derived queue);
- the command names NO `.memory/` path (D-04 / fresh-clone case: `.gitignore` drops the derived
  queue, so a command that read it would report "no work" on a clean checkout — a false green);
- the command carries NO hand-typed exclusion glob (D-06 — the enforcing control is 29-01's
  `tools.docs_guard.exclusion_reason`; a second copy of the glob set in prose is a fork that
  silently diverges from its home);
- all three routed exit codes 0, 1 and 3 are spelled (D-05 — exit 3 is a DIFFERENT operator action
  from exit 1, and collapsing them has an agent editing docs to fix a malformed registry);
- the skill names `exclusion_reason`, so the runbook points at the tested control rather than
  restating the rule as prose.

`docs-upkeep`'s membership in `caps.EXPECTED_SKILLS` is asserted HERE too: a half-widening (skill
authored, cap not moved, or the reverse) then fails with a legible message instead of only deep
inside the emitter's skill-set check.

Parsing is delegated to the shared `parse_frontmatter` — no hand-sliced `---` fences. Kept
domain-neutral so the GEN-04 core-plane guard stays green.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint import parse_frontmatter
from tools.harness_lint.caps import EXPECTED_SKILLS

# test_docs_update_wiring.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_COMMAND = _REPO_ROOT / "harness" / "commands" / "docs-update.md"
_SKILL = _REPO_ROOT / "harness" / "skills" / "docs-upkeep" / "SKILL.md"

# Same routing-trigger vocabulary the command/skill description gates use (test_commands.py:34).
_ROUTING_TRIGGERS = ("use", "when")

# The exclusion globs the command must NOT retype. Each is spelled at its own home
# (CONSTITUTION_GLOBS / DERIVED_GLOBS / ADR_GLOBS) and reached only through `exclusion_reason`.
_FORBIDDEN_GLOB_LITERALS = (
    "contracts/**",
    "docs/reference/**",
    ".memory/derived/**",
    "golden/**",
    "docs/adr/**",
)


def _read(path: Path) -> tuple[dict, str]:
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def test_command_exists_and_is_routed_to_python_engineer() -> None:
    """`/docs-update` exists and runs as a python-engineer subtask (D-01).

    `curator` would be WRONG: it is the derived-plane owner and
    `test_derived_freshness.py` pins its tool modules to memory_regen/docs_sync.
    """
    assert _COMMAND.is_file(), "harness/commands/docs-update.md is missing"
    fm, _ = _read(_COMMAND)
    assert fm.get("agent") == "python-engineer", (
        f"/docs-update must run as python-engineer, got {fm.get('agent')!r}"
    )
    assert fm.get("subtask") is True, "/docs-update must declare subtask: true"
    desc = str(fm.get("description", "")).strip().lower()
    assert desc, "/docs-update has no description"
    assert any(tok in desc for tok in _ROUTING_TRIGGERS), (
        f"/docs-update description lacks a routing trigger ({_ROUTING_TRIGGERS})"
    )


def test_command_names_the_guard_module() -> None:
    """The body invokes the already-coded gate rather than re-deriving staleness (D-04)."""
    _, body = _read(_COMMAND)
    assert "tools.docs_guard" in body, (
        "docs-update.md does not name tools.docs_guard — the command must re-run the guard"
    )


def test_command_names_no_memory_path() -> None:
    """The derived queue is gitignored; reading it is a fresh-clone false green (D-04)."""
    _, body = _read(_COMMAND)
    assert ".memory/" not in body, (
        "docs-update.md names a .memory/ path — the gitignored derived queue is a SessionStart "
        "pointer, never this command's source of truth"
    )


def test_command_carries_no_exclusion_glob_literal() -> None:
    """No second copy of the exclusion set (D-06 — 29-01's exclusion_reason is the control)."""
    _, body = _read(_COMMAND)
    for glob in _FORBIDDEN_GLOB_LITERALS:
        assert glob not in body, (
            f"docs-update.md hand-types the exclusion glob {glob!r} — the exclusion set has one "
            "home and is reached through tools.docs_guard.exclusion_reason"
        )


def test_command_routes_all_three_exit_codes() -> None:
    """0 stops, 1 is the working state, 3 refuses to draft and sends you to the registry (D-05)."""
    _, body = _read(_COMMAND)
    for code in ("0", "1", "3"):
        assert f"exit {code}" in body.lower(), (
            f"docs-update.md does not route exit {code} — all three codes must be spelled"
        )


def test_skill_exists_and_names_the_enforcing_control() -> None:
    """The runbook points at the tested classifier, not at prose restating the rule (D-06)."""
    assert _SKILL.is_file(), "harness/skills/docs-upkeep/SKILL.md is missing"
    fm, body = _read(_SKILL)
    assert fm.get("name") == "docs-upkeep", (
        f"docs-upkeep skill must be named 'docs-upkeep', got {fm.get('name')!r}"
    )
    assert "exclusion_reason" in body, (
        "docs-upkeep/SKILL.md does not name exclusion_reason — a SKILL body that merely SAYS "
        "'do not edit an accepted ADR' is not the control"
    )


def test_docs_upkeep_is_an_expected_skill() -> None:
    """The cap moved with the skill — a half-widening fails here, legibly (D-02)."""
    assert "docs-upkeep" in EXPECTED_SKILLS, (
        "docs-upkeep is not in caps.EXPECTED_SKILLS — the skill and the cap must move together"
    )
