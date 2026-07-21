"""Read the ratified lane-specific transition data contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRANSITIONS_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "harness"
    / "task-control"
    / "transitions.json"
)


def _load_contract() -> dict[str, Any]:
    value = json.loads(TRANSITIONS_PATH.read_bytes())
    if not isinstance(value, dict) or not isinstance(value.get("phases"), list):
        raise ValueError("invalid transition contract: phases must be an array")
    if not isinstance(value.get("lanes"), dict):
        raise ValueError("invalid transition contract: lanes must be an object")
    return value


def _load_edges(raw: object) -> frozenset[tuple[str, str]]:
    if not isinstance(raw, list):
        raise ValueError("invalid transition contract: lane edges must be an array")
    edges: set[tuple[str, str]] = set()
    for edge in raw:
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or not all(isinstance(phase, str) for phase in edge)
        ):
            raise ValueError("invalid transition contract: each edge must contain two phases")
        pair = (edge[0], edge[1])
        if pair in edges:
            raise ValueError("invalid transition contract: duplicate edge")
        edges.add(pair)
    return frozenset(edges)


_CONTRACT = _load_contract()
PHASES = frozenset(str(phase) for phase in _CONTRACT["phases"])
ALLOWED_TRANSITIONS = {str(lane): _load_edges(edges) for lane, edges in _CONTRACT["lanes"].items()}
_PHASE_ARTIFACTS = _CONTRACT.get("required_artifacts_by_target_phase", {})


def is_transition_allowed(lane: str, source: str, target: str) -> bool:
    """Return False for unknown lanes, phases, and non-edges."""
    if source not in PHASES or target not in PHASES:
        return False
    return (source, target) in ALLOWED_TRANSITIONS.get(lane, frozenset())


def required_artifacts_for_phase(lane: str, target: str) -> list[str]:
    """Return the ratified predecessor artifacts required before entering *target*."""
    if lane not in ALLOWED_TRANSITIONS:
        raise ValueError(f"invalid phase artifact contract lane: {lane}")
    lane_values = _PHASE_ARTIFACTS.get(lane)
    if not isinstance(lane_values, dict) or target not in lane_values:
        raise ValueError(f"missing phase artifact contract for {lane}/{target}")
    values = lane_values[target]
    if not isinstance(values, list) or not all(isinstance(item, str) and item for item in values):
        raise ValueError(f"invalid phase artifact contract for {lane}/{target}")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate phase artifact contract for {lane}/{target}")
    return list(values)
