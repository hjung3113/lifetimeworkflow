"""SKILL-01/02 STRUCTURAL cap gate (D-07) — validation of harness/skills/*/SKILL.md.

Proves success criterion 5 structurally, without a runtime: every authored skill stays within the
shared runtime caps so no loader silently truncates or rejects it (T-03-17), the set is exactly the
seven enumerated skills with disjoint routing descriptions (anti-sprawl, T-03-18), and no reserved
vendor word or angle-bracket tag leaks into a name/description (T-03-19).

The caps are IDENTICAL for opencode and Claude (RESEARCH §"Skill Format + Caps" — the 200-vs-1024
correction): name ≤64, description ≤1024 as HARD failures; body >~500 lines only WARNS (a
recommendation, never a reject) per D-07.

Parsing is delegated to the shared ``parse_frontmatter`` (Plan 02) — no per-test fence slicing.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pytest

from tools.harness_lint import parse_frontmatter

# test_skills.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SKILLS_DIR = _REPO_ROOT / "harness" / "skills"

# Shared caps (BOTH runtimes — the 200-vs-1024 correction; body cap is a warn threshold).
_NAME_MAX = 64
_DESC_MAX = 1024
_BODY_WARN_LINES = 500

# name regex: lowercase alnum segments joined by single hyphens.
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# A routing-signal description must carry an invocation trigger token (P7 guard — mirrors agents).
_ROUTING_TRIGGERS = ("use", "when")

# Reserved vendor words banned from a skill name/description (Claude skill rules, T-03-19).
_RESERVED_WORDS = ("anthropic", "claude")

# Angle-bracket XML tags are forbidden in name/description (T-03-19).
_XML_CHARS = ("<", ">")

# Exactly the seven enumerated skills (D-07) — core + meta + domain. No more, no fewer (anti-sprawl).
EXPECTED_SKILLS = frozenset(
    {
        "dotnet-conventions",
        "python-conventions",
        "golden-testing",
        "data-contracts",
        "skill-creator",
        "normalization-catalog",
        "pipeline-patterns",
    }
)


def _skill_files() -> list[Path]:
    return sorted(_SKILLS_DIR.glob("*/SKILL.md"))


def _load(path: Path) -> tuple[dict, str]:
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def test_expected_skills_present_no_sprawl() -> None:
    """Exactly the seven enumerated skill directories exist — no missing, no extra (T-03-18)."""
    names = {p.parent.name for p in _skill_files()}
    assert names == set(EXPECTED_SKILLS), (
        f"skill set drift: got {sorted(names)}, expected {sorted(EXPECTED_SKILLS)}"
    )


@pytest.mark.parametrize("path", _skill_files(), ids=lambda p: p.parent.name)
def test_frontmatter_parses(path: Path) -> None:
    """Frontmatter is present and parses to a non-empty mapping (valid SKILL.md)."""
    fm, _ = _load(path)
    assert isinstance(fm, dict) and fm, f"{path.parent.name}: missing or empty frontmatter"


@pytest.mark.parametrize("path", _skill_files(), ids=lambda p: p.parent.name)
def test_name_within_caps_and_matches_dir(path: Path) -> None:
    """name: ≤64, regex-valid, equals parent dir, no reserved word, no XML tag (T-03-17/19)."""
    fm, _ = _load(path)
    name = str(fm.get("name", ""))
    dir_name = path.parent.name
    assert name, f"{dir_name}: name missing or empty"
    assert len(name) <= _NAME_MAX, f"{dir_name}: name length {len(name)} exceeds {_NAME_MAX}"
    assert _NAME_RE.match(name), f"{dir_name}: name {name!r} fails regex {_NAME_RE.pattern}"
    assert name == dir_name, f"{dir_name}: frontmatter name {name!r} != parent dir {dir_name!r}"
    lowered = name.lower()
    assert not any(w in lowered for w in _RESERVED_WORDS), (
        f"{dir_name}: name contains a reserved vendor word {_RESERVED_WORDS}"
    )
    assert not any(c in name for c in _XML_CHARS), f"{dir_name}: name contains an XML tag char"


@pytest.mark.parametrize("path", _skill_files(), ids=lambda p: p.parent.name)
def test_description_within_caps_and_routes(path: Path) -> None:
    """description: non-empty, ≤1024, no XML tag, no reserved word, carries a trigger (T-03-17/19)."""
    fm, _ = _load(path)
    dir_name = path.parent.name
    desc = str(fm.get("description", "")).strip()
    assert desc, f"{dir_name}: description missing or empty"
    assert len(desc) <= _DESC_MAX, f"{dir_name}: description length {len(desc)} exceeds {_DESC_MAX}"
    assert not any(c in desc for c in _XML_CHARS), f"{dir_name}: description contains an XML tag char"
    lowered = desc.lower()
    assert not any(w in lowered for w in _RESERVED_WORDS), (
        f"{dir_name}: description contains a reserved vendor word {_RESERVED_WORDS}"
    )
    assert any(tok in lowered for tok in _ROUTING_TRIGGERS), (
        f"{dir_name}: description lacks a routing trigger ({_ROUTING_TRIGGERS}) — reads as a label"
    )


def test_descriptions_are_disjoint() -> None:
    """No two skills share an identical description (routing must be unambiguous, T-03-18)."""
    descs = [str(_load(p)[0].get("description", "")).strip().lower() for p in _skill_files()]
    assert len(descs) == len(set(descs)), "duplicate skill descriptions — routing is ambiguous"


@pytest.mark.parametrize("path", _skill_files(), ids=lambda p: p.parent.name)
def test_body_line_cap_only_warns(path: Path) -> None:
    """A body over ~500 lines emits a warning — it MUST NOT hard-fail (D-07 recommendation)."""
    _, body = _load(path)
    line_count = len(body.splitlines())
    if line_count > _BODY_WARN_LINES:
        warnings.warn(
            f"{path.parent.name}: SKILL.md body is {line_count} lines "
            f"(> {_BODY_WARN_LINES} recommended) — consider moving depth into references/",
            stacklevel=2,
        )
    # No assertion on line_count: the cap is advisory, not a gate.
