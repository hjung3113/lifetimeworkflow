"""Capability declarations and the per-capability agent allowlist (LANE-03).

Routing in this harness has always been by NAME: a skill, a persona file, or a routing table names
``code-reviewer`` and that name is the routing decision. A name is not a declaration — nothing
checks it, and nothing can refuse it. This module supplies the missing half:

* ``harness/capabilities.toml`` declares WHAT KIND of agent a piece of work needs (a capability id)
  and, per capability, the closed ALLOWLIST of personas that may serve it.
* ``harness/disciplines.toml`` names a *capability*, never a persona.
* ``route_defects`` decides whether a concrete agent may serve a capability, and
  ``tools/discipline/check.py`` turns a defect into an unsatisfied discipline — which
  ``tools/task_control`` already refuses at a phase transition.

Nothing here touches a repository. Loading validates SHAPE only: whether a named provider is a real
``harness/agents/<name>.md`` — and whether a ``read_only`` capability's providers actually hold no
write affordance — is a ``tools/harness_lint`` gate, exactly as ``load_declarations`` leaves the
"does this SKILL.md exist" question to ``test_discipline_wiring.py``.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "harness" / "capabilities.toml"

_CAPABILITY_KEYS = frozenset({"description", "providers", "read_only"})
_REQUIRED_CAPABILITY_KEYS = frozenset({"description", "providers"})


class CapabilityError(ValueError):
    """A malformed registry or an unknown capability id — never an ordinary refused route.

    A refused route is an ordinary result (a non-empty ``route_defects`` list), not an exception:
    it is the expected answer whenever work is routed somewhere it does not belong.
    """


@dataclass(frozen=True)
class Capability:
    """One declared capability: what it is for, and who is allowed to serve it."""

    id: str
    description: str
    providers: tuple[str, ...]
    read_only: bool = False


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            value = tomllib.load(handle)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        raise CapabilityError(f"invalid capability registry: {exc}") from exc
    if not isinstance(value, dict):
        raise CapabilityError("capability registry must be a TOML table")
    return value


def load_capabilities(path: str | Path = DEFAULT_REGISTRY) -> dict[str, Capability]:
    """Load and fail-closed-validate every declared capability.

    Fail-closed matters more here than in most loaders: a registry that silently tolerates an
    unknown key is a registry in which a typo'd ``provider`` (singular) declares an empty allowlist
    that permits nobody, or — worse, depending on the reading — is ignored entirely.
    """
    raw = _read_toml(Path(path))
    if raw.get("version") != 1:
        raise CapabilityError("capability registry version must be 1")
    table = raw.get("capability")
    if not isinstance(table, dict) or not table:
        raise CapabilityError("capability registry requires a non-empty [capability] table")
    capabilities: dict[str, Capability] = {}
    for identifier, body in table.items():
        if not isinstance(body, dict):
            raise CapabilityError(f"capability {identifier} must be a table")
        unknown = set(body) - _CAPABILITY_KEYS
        if unknown:
            raise CapabilityError(
                f"capability {identifier} has unknown key(s): {', '.join(sorted(unknown))}"
            )
        missing = _REQUIRED_CAPABILITY_KEYS - set(body)
        if missing:
            raise CapabilityError(
                f"capability {identifier} is missing: {', '.join(sorted(missing))}"
            )
        description = body["description"]
        if not isinstance(description, str) or not description.strip():
            raise CapabilityError(f"capability {identifier} has an invalid description")
        providers = body["providers"]
        if (
            not isinstance(providers, list)
            or not providers
            or not all(isinstance(item, str) and item for item in providers)
        ):
            raise CapabilityError(
                f"capability {identifier} has an invalid providers allowlist"
                " (a capability nobody can serve is unroutable)"
            )
        if len(set(providers)) != len(providers):
            raise CapabilityError(f"capability {identifier} lists a duplicate provider")
        read_only = body.get("read_only", False)
        if type(read_only) is not bool:
            raise CapabilityError(f"capability {identifier} has a non-boolean read_only")
        capabilities[identifier] = Capability(
            id=identifier,
            description=description,
            providers=tuple(providers),
            read_only=read_only,
        )
    return capabilities


def providers_for(
    capability_id: str, *, registry: dict[str, Capability] | None = None
) -> tuple[str, ...]:
    """The allowlist for *capability_id*; raises when the capability is not declared."""
    resolved = registry if registry is not None else load_capabilities()
    capability = resolved.get(capability_id)
    if capability is None:
        raise CapabilityError(f"unknown capability: {capability_id}")
    return capability.providers


def route_defects(
    capability_id: str, agent: str | None, *, registry: dict[str, Capability] | None = None
) -> list[str]:
    """Every reason *agent* may not serve *capability_id*; an empty list means the route is allowed.

    An absent agent and an out-of-allowlist agent are DISTINCT messages: the first says the routing
    claim was never made, the second says it was made and is not permitted. Collapsing them would
    make an unrecorded route indistinguishable from a refused one.
    """
    resolved = registry if registry is not None else load_capabilities()
    capability = resolved.get(capability_id)
    if capability is None:
        return [f"unknown capability: {capability_id}"]
    if not agent:
        return [f"capability {capability_id} requires a named agent, none given"]
    if agent not in capability.providers:
        return [
            f"agent {agent} is not allowed to serve capability {capability_id} "
            f"(allowlist: {', '.join(capability.providers)})"
        ]
    return []
