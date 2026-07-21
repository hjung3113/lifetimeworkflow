"""LANE-01/LANE-02 wiring gate: a required discipline that has no procedure is a claimed control.

Three declarations have to agree, and nothing but a test makes them:

* ``harness/risk-policy.toml`` — which lane owes which discipline id
* ``harness/disciplines.toml`` — what that id is, and which skill discharges it
* ``harness/skills/<name>/SKILL.md`` — the procedure itself

Both directions fail. A lane requiring an id nobody declared is a requirement no agent can satisfy;
a declaration nobody requires is a dead procedure accumulating in the tree. Each direction carries a
mutation proof, operating on a COPY — the real files are never written by a test.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from tools.discipline.check import DisciplineError, load_declarations
from tools.risk_router.router import DEFAULT_POLICY, LANES, load_policy

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SKILLS_DIR = _REPO_ROOT / "harness" / "skills"
_DECLARATIONS = _REPO_ROOT / "harness" / "disciplines.toml"


def _required_ids() -> set[str]:
    policy = load_policy(DEFAULT_POLICY)
    return {
        identifier for lane in LANES for identifier in policy["lanes"][lane]["required_disciplines"]
    }


def test_every_required_discipline_is_declared() -> None:
    declared = set(load_declarations(_DECLARATIONS))
    undeclared = _required_ids() - declared
    assert not undeclared, f"lane policy requires undeclared discipline(s): {sorted(undeclared)}"


def test_every_declaration_is_required_by_some_lane() -> None:
    """The reverse direction: a procedure nobody owes is dead weight, not optionality."""
    unused = set(load_declarations(_DECLARATIONS)) - _required_ids()
    assert not unused, f"declared but required by no lane: {sorted(unused)}"


def test_every_declared_skill_exists_and_is_authored() -> None:
    for identifier, declaration in load_declarations(_DECLARATIONS).items():
        skill = _SKILLS_DIR / declaration.skill / "SKILL.md"
        assert skill.is_file(), f"{identifier} names a skill with no SKILL.md: {declaration.skill}"
        assert skill.read_text(encoding="utf-8").strip(), f"{identifier}: empty SKILL.md"


def test_the_panel_skill_reuses_the_fan_out_substrate() -> None:
    """LANE-02 reuses the Phase-10 substrate; a second dispatcher is the thing to prevent."""
    body = (_SKILLS_DIR / "adversarial-review-panel" / "SKILL.md").read_text(encoding="utf-8")
    assert "fan-out-synthesize" in body
    assert "explorer" in body


def test_the_panel_thresholds_are_data_not_prose() -> None:
    """min_experts lives in the declaration, so changing it does not mean editing a skill."""
    declaration = load_declarations(_DECLARATIONS)["adversarial-review-panel"]
    assert declaration.min_experts is not None and declaration.min_experts >= 3
    body = (_SKILLS_DIR / "adversarial-review-panel" / "SKILL.md").read_text(encoding="utf-8")
    assert "harness/disciplines.toml" in body


def _copy_declarations(tmp_path: Path, mutate) -> Path:
    raw = tomllib.loads(_DECLARATIONS.read_text(encoding="utf-8"))
    mutate(raw)
    lines = [f"version = {raw['version']}", ""]
    for identifier, body in raw["discipline"].items():
        lines.append(f"[discipline.{identifier}]")
        for key, value in body.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, list):
                rendered = ", ".join(f'"{item}"' for item in value)
                lines.append(f"{key} = [{rendered}]")
            else:
                lines.append(f"{key} = {value}")
        lines.append("")
    path = tmp_path / "disciplines.toml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_an_undeclared_requirement_is_caught(tmp_path: Path) -> None:
    """MUTATION: delete a declaration the policy requires and the forward check fails."""
    path = _copy_declarations(tmp_path, lambda raw: raw["discipline"].pop("clarify"))
    declared = set(load_declarations(path))
    assert _required_ids() - declared == {"clarify"}


def test_a_declaration_naming_a_missing_skill_is_caught(tmp_path: Path) -> None:
    """MUTATION: repoint a declaration at a skill that does not exist."""

    def repoint(raw: dict) -> None:
        raw["discipline"]["clarify"]["skill"] = "no-such-skill"

    declaration = load_declarations(_copy_declarations(tmp_path, repoint))["clarify"]
    assert not (_SKILLS_DIR / declaration.skill / "SKILL.md").is_file()


def test_a_malformed_declaration_is_refused_not_ignored(tmp_path: Path) -> None:
    path = tmp_path / "disciplines.toml"
    path.write_text('version = 1\n[discipline.x]\nskill = "x"\n', encoding="utf-8")
    with pytest.raises(DisciplineError):
        load_declarations(path)
