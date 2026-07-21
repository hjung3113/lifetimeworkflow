"""Template anti-sprawl + shape gate — frontmatter validation of harness/agents/templates/*.md.

Closes the gap where the `templates/` subdirectory is validated by NOTHING: the persona gate
(``test_agents.py``) globs ``harness/agents/*.md`` NON-recursively, so the fill-in-the-blanks
persona templates that ``/add-language`` and ``/component`` instantiate escape every structural
check. This gate pins the template set to exactly the enumerated two (no sprawl, P1/P8) and asserts
each carries a valid, least-privilege, subagent-mode frontmatter with a routing-signal description.

Templates are NOT personas — they live in a subdirectory precisely so they are not counted among
the four core personas. This module reuses the persona gate's ``VALID_PERMISSION_KEYS`` /
``VALID_MODES`` / ``parse_frontmatter`` so the two gates cannot drift.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.harness_lint import parse_frontmatter
from tools.harness_lint.tests.test_agents import (
    _AGENTS_DIR,
    ALLOWED_PERMISSION_KEYS,
    VALID_MODES,
)

# The fill-in-the-blanks persona templates live one level below the core personas.
_TEMPLATES_DIR = _AGENTS_DIR / "templates"

# Exactly the two enumerated templates — the per-language engineer and the per-component engineer.
# A template is NOT a persona (it lives in templates/), so EXPECTED_PERSONAS stays 4 while this set
# grows independently. Adding/removing a templates/*.md without updating this set fails the gate.
EXPECTED_TEMPLATES = frozenset({"engineer", "component-engineer"})

# A routing-signal description must carry an invocation trigger token (P7 guard, mirrors test_agents).
_ROUTING_TRIGGERS = ("use", "when")


def _template_files() -> list[Path]:
    return sorted(_TEMPLATES_DIR.glob("*.md"))


def _load(path: Path) -> dict:
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm


def _permission(fm: dict) -> dict:
    perm = fm.get("permission", {})
    return perm if isinstance(perm, dict) else {}


def test_templates_no_sprawl() -> None:
    """Exactly the two enumerated templates exist — no missing, no extra (P1/P8)."""
    stems = {p.stem for p in _template_files()}
    assert stems == set(EXPECTED_TEMPLATES), (
        f"template set drift: got {sorted(stems)}, expected {sorted(EXPECTED_TEMPLATES)}"
    )


@pytest.mark.parametrize("path", _template_files(), ids=lambda p: p.stem)
def test_template_mode_is_subagent(path: Path) -> None:
    """Every template declares ``mode: subagent`` — an instantiated copy must never be primary."""
    fm = _load(path)
    assert fm.get("mode") in VALID_MODES, f"{path.stem}: invalid/absent mode {fm.get('mode')!r}"
    assert fm.get("mode") == "subagent", f"{path.stem}: template mode must be subagent"


@pytest.mark.parametrize("path", _template_files(), ids=lambda p: p.stem)
def test_template_permission_keys_are_valid_subset(path: Path) -> None:
    """Permission keys are a subset of the 15 valid keys (+ the deny-only 'write' alias)."""
    keys = set(_permission(_load(path)).keys())
    extra = keys - ALLOWED_PERMISSION_KEYS
    assert not extra, f"{path.stem}: invalid/over-broad permission keys {sorted(extra)}"


@pytest.mark.parametrize("path", _template_files(), ids=lambda p: p.stem)
def test_template_bash_is_least_privilege(path: Path) -> None:
    """The bash affordance gates everything to ``ask`` except a single scoped allow (least priv)."""
    bash = _permission(_load(path)).get("bash", {})
    assert isinstance(bash, dict), f"{path.stem}: bash permission must be a scoped map"
    assert str(bash.get("*")) == "ask", f"{path.stem}: bash catch-all '*' must be 'ask'"
    allows = [scope for scope, verdict in bash.items() if scope != "*" and str(verdict) == "allow"]
    assert allows, f"{path.stem}: bash must carry a scoped allow (the toolchain placeholder)"


@pytest.mark.parametrize("path", _template_files(), ids=lambda p: p.stem)
def test_template_description_is_routing_signal(path: Path) -> None:
    """description present, non-empty, carries a routing trigger token (P7 — not a bare label)."""
    fm = _load(path)
    desc = str(fm.get("description", "")).strip()
    assert desc, f"{path.stem}: description missing or empty"
    lowered = desc.lower()
    assert any(tok in lowered for tok in _ROUTING_TRIGGERS), (
        f"{path.stem}: description lacks a routing trigger ({_ROUTING_TRIGGERS}) — reads as a label"
    )
