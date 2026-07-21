"""LANE-03 wiring gate: a capability nobody can serve, or a route to a persona that is not there.

Four declarations have to agree, and nothing but a test makes them:

* ``harness/capabilities.toml`` — the capability vocabulary and, per capability, the ALLOWLIST
* ``harness/agents/<name>.md`` — the personas the allowlist names
* ``tools/harness_lint/caps.py`` — the enumerated core persona set and the read-only predicate
* ``harness/disciplines.toml`` — the capability each lane discipline routes to

Both directions fail. A route to a persona that does not exist is a route nobody can take; a persona
no capability names is a specialist nothing can reach. The ``read_only`` obligation gets its own
gate, because the single most valuable thing this allowlist asserts is that the seat judging a
change cannot edit it. Every gate carries a MUTATION PROOF operating on a COPY — the real files are
never written by a test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.capability.registry import (
    DEFAULT_REGISTRY,
    CapabilityError,
    load_capabilities,
)
from tools.discipline.check import DEFAULT_DECLARATIONS, DisciplineError, load_declarations
from tools.harness_lint import parse_frontmatter
from tools.harness_lint.caps import EXPECTED_PERSONAS, is_read_only

_REPO_ROOT = Path(__file__).resolve().parents[3]
_AGENTS_DIR = _REPO_ROOT / "harness" / "agents"


def _registry() -> dict:
    return load_capabilities(DEFAULT_REGISTRY)


def _frontmatter(persona: str) -> dict:
    fm, _ = parse_frontmatter((_AGENTS_DIR / f"{persona}.md").read_text(encoding="utf-8"))
    return fm


def test_every_provider_is_a_real_core_persona() -> None:
    for capability in _registry().values():
        for provider in capability.providers:
            assert (_AGENTS_DIR / f"{provider}.md").is_file(), (
                f"{capability.id} routes to a persona with no agent file: {provider}"
            )
            assert provider in EXPECTED_PERSONAS, (
                f"{capability.id} routes to a persona outside the enumerated core set: {provider}"
            )


def test_every_core_persona_provides_at_least_one_capability() -> None:
    """The reverse direction: a persona nothing can route to is unreachable, not optional."""
    served = {provider for cap in _registry().values() for provider in cap.providers}
    unreachable = EXPECTED_PERSONAS - served
    assert not unreachable, f"core persona(s) no capability can route to: {sorted(unreachable)}"


def test_a_read_only_capability_is_served_only_by_read_only_personas() -> None:
    """The point of the allowlist: the seat judging a change must not be able to edit it."""
    for capability in _registry().values():
        if not capability.read_only:
            continue
        for provider in capability.providers:
            assert is_read_only(_frontmatter(provider)), (
                f"{capability.id} is declared read_only but {provider} holds a write affordance"
            )


def test_every_discipline_routes_to_a_declared_capability() -> None:
    registry = _registry()
    for identifier, declaration in load_declarations(DEFAULT_DECLARATIONS).items():
        assert declaration.capability is not None, (
            f"{identifier} names no capability — it would route by persona name"
        )
        assert declaration.capability in registry, (
            f"{identifier} routes to an undeclared capability: {declaration.capability}"
        )


# ── mutation proofs ───────────────────────────────────────────────────────────────────────────

_MUTABLE = """version = 1

[capability.adversarial-review]
description = "read-only review"
providers = [{providers}]
read_only = true
"""


def _copy_registry(tmp_path: Path, providers: list[str]) -> Path:
    rendered = ", ".join(f'"{item}"' for item in providers)
    path = tmp_path / "capabilities.toml"
    path.write_text(_MUTABLE.format(providers=rendered), encoding="utf-8")
    return path


def test_a_route_to_a_nonexistent_persona_is_caught(tmp_path: Path) -> None:
    """MUTATION: point a provider at an agent that does not exist and the forward gate fails."""
    registry = load_capabilities(_copy_registry(tmp_path, ["no-such-persona"]))
    provider = registry["adversarial-review"].providers[0]
    assert not (_AGENTS_DIR / f"{provider}.md").is_file()
    assert provider not in EXPECTED_PERSONAS


def test_a_write_capable_provider_on_a_read_only_capability_is_caught(tmp_path: Path) -> None:
    """MUTATION: put a write-capable persona on a read_only capability and the gate fails."""
    registry = load_capabilities(_copy_registry(tmp_path, ["python-engineer"]))
    capability = registry["adversarial-review"]
    assert capability.read_only
    assert not is_read_only(_frontmatter(capability.providers[0])), (
        "python-engineer must hold a write affordance for this mutation to prove anything"
    )


def test_a_discipline_naming_an_undeclared_capability_is_caught(tmp_path: Path) -> None:
    """MUTATION: route a discipline at a capability nobody declared and the load fails closed."""
    path = tmp_path / "disciplines.toml"
    path.write_text(
        'version = 1\n[discipline.x]\nskill = "clarify"\ncapability = "ghost"\n'
        'owed_by_phase = "EXECUTE"\noutputs_required = 0\n',
        encoding="utf-8",
    )
    with pytest.raises(DisciplineError, match="undeclared capability"):
        load_declarations(path)


def test_an_empty_allowlist_is_refused(tmp_path: Path) -> None:
    """MUTATION: a capability nobody may serve is unroutable, and must not load."""
    with pytest.raises(CapabilityError):
        load_capabilities(_copy_registry(tmp_path, []))
