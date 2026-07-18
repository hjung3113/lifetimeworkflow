"""Pure, deterministic risk-policy loading, validation, and routing."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

LANES = ("FAST", "STANDARD", "STRICT", "CONTROLLED")
SCORE_FIELDS = (
    "ambiguity",
    "change_scope",
    "data_security",
    "reversibility",
    "impact",
    "coordination",
    "context_pressure",
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "harness" / "risk-policy.toml"
OVERLAY_SCHEMA = Path(__file__).with_name("overlay.schema.json")
ROUTER_VERSION = 1


class RiskRouterError(ValueError):
    """A deterministic invalid-input or invalid-policy error."""


def _read_toml(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).open("rb") as handle:
            value = tomllib.load(handle)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        raise RiskRouterError(f"invalid TOML policy: {exc}") from exc
    if not isinstance(value, dict):
        raise RiskRouterError("policy must be a TOML table")
    return value


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _lane_index(lane: object) -> int:
    if not isinstance(lane, str) or lane not in LANES:
        raise RiskRouterError(f"unknown lane: {lane!r}")
    return LANES.index(lane)


def _validate_core_policy(policy: dict[str, Any]) -> None:
    if policy.get("version") != 1:
        raise RiskRouterError("core policy version must be 1")
    cuts = policy.get("cuts")
    promotions = policy.get("promotions")
    lanes = policy.get("lanes")
    if not isinstance(cuts, dict) or not isinstance(promotions, dict) or not isinstance(lanes, dict):
        raise RiskRouterError("core policy requires cuts, promotions, and lanes tables")
    expected_start = 0
    for lane in LANES:
        interval = cuts.get(lane)
        if not (isinstance(interval, list) and len(interval) == 2 and all(isinstance(n, int) for n in interval)):
            raise RiskRouterError(f"invalid cut for {lane}")
        if interval[0] != expected_start or interval[1] < interval[0]:
            raise RiskRouterError("cuts must be contiguous and ordered")
        expected_start = interval[1] + 1
        lane_data = lanes.get(lane)
        if not isinstance(lane_data, dict):
            raise RiskRouterError(f"missing lane matrix for {lane}")
        for key in ("required_artifacts", "required_gates"):
            values = lane_data.get(key)
            if not (isinstance(values, list) and all(isinstance(item, str) and item for item in values)):
                raise RiskRouterError(f"invalid {key} for {lane}")
            if len(values) != len(set(values)):
                raise RiskRouterError(f"duplicate {key} for {lane}")
    if expected_start != 22:
        raise RiskRouterError("cuts must cover totals 0 through 21")
    for reason, lane in promotions.items():
        if not isinstance(reason, str) or not reason:
            raise RiskRouterError("promotion reason must be a non-empty string")
        _lane_index(lane)


def load_policy(path: str | Path = DEFAULT_POLICY) -> dict[str, Any]:
    """Load and validate core policy data without observing repository state."""
    policy = _read_toml(path)
    _validate_core_policy(policy)
    return policy


def _schema_validate_overlay(overlay: dict[str, Any]) -> None:
    schema = json.loads(OVERLAY_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(overlay), key=lambda e: list(e.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "<root>"
        raise RiskRouterError(f"invalid overlay schema at {location}: {error.message}")


def validate_overlay(core: dict[str, Any], overlay: dict[str, Any]) -> None:
    """Reject every overlay relaxation; only monotonic additions are representable."""
    _validate_core_policy(core)
    _schema_validate_overlay(overlay)
    core_promotions = core["promotions"]
    for reason, lane in overlay.get("minimum_lanes", {}).items():
        if reason in core_promotions and _lane_index(lane) < _lane_index(core_promotions[reason]):
            raise RiskRouterError(f"overlay lowers promotion lane for {reason}")
    for reason in overlay.get("additional_promotions", {}):
        if reason in core_promotions:
            raise RiskRouterError(f"overlay must not replace core promotion predicate: {reason}")
    for lane, additions in overlay.get("lanes", {}).items():
        for key in ("required_artifacts_add", "required_gates_add"):
            if key not in additions:
                continue
            if not all(isinstance(value, str) and value for value in additions[key]):
                raise RiskRouterError(f"overlay contains invalid {key} for {lane}")


def load_overlay(path: str | Path, core: dict[str, Any]) -> dict[str, Any]:
    """Load a declarative instance-owned overlay after fail-closed validation."""
    overlay = _read_toml(path)
    validate_overlay(core, overlay)
    return overlay


def load_project_overlay(project_path: str | Path, core: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve the optional project slot; callers explicitly supply the project data source."""
    project = _read_toml(project_path)
    raw = project.get("instance", {}).get("risk_overlay", "")
    if not isinstance(raw, str):
        raise RiskRouterError("instance.risk_overlay must be a string")
    if not raw:
        return None
    return load_overlay(Path(project_path).parent / raw, core)


def _effective_policy(core: dict[str, Any], overlay: dict[str, Any] | None) -> dict[str, Any]:
    effective = {
        "cuts": core["cuts"],
        "promotions": dict(core["promotions"]),
        "lanes": {
            lane: {
                "required_artifacts": list(core["lanes"][lane]["required_artifacts"]),
                "required_gates": list(core["lanes"][lane]["required_gates"]),
            }
            for lane in LANES
        },
    }
    if overlay is None:
        return effective
    for reason, lane in overlay.get("minimum_lanes", {}).items():
        effective["promotions"][reason] = lane
    effective["promotions"].update(overlay.get("additional_promotions", {}))
    for lane, additions in overlay.get("lanes", {}).items():
        for source, target in (("required_artifacts_add", "required_artifacts"), ("required_gates_add", "required_gates")):
            for item in additions.get(source, []):
                if item not in effective["lanes"][lane][target]:
                    effective["lanes"][lane][target].append(item)
    return effective


def _validate_input(payload: object, known_reasons: set[str]) -> tuple[dict[str, int], list[str], str | None, str | None]:
    if not isinstance(payload, dict) or set(payload) - {"scores", "fact_flags", "human_override"}:
        raise RiskRouterError("input must contain only scores, fact_flags, and human_override")
    scores = payload.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(SCORE_FIELDS):
        raise RiskRouterError("scores must contain exactly the seven risk axes")
    if any(type(value) is not int or not 0 <= value <= 3 for value in scores.values()):
        raise RiskRouterError("each score must be an integer from 0 through 3")
    flags = payload.get("fact_flags", {})
    if not isinstance(flags, dict) or any(reason not in known_reasons for reason in flags):
        raise RiskRouterError("unknown promotion reason")
    if any(type(enabled) is not bool for enabled in flags.values()):
        raise RiskRouterError("fact flags must be boolean")
    override = payload.get("human_override")
    if override is None:
        return scores, sorted(reason for reason, enabled in flags.items() if enabled), None, None
    if not isinstance(override, dict) or set(override) != {"lane", "reason"}:
        raise RiskRouterError("human_override must contain lane and reason")
    lane, reason = override["lane"], override["reason"]
    _lane_index(lane)
    if not isinstance(reason, str) or not reason:
        raise RiskRouterError("human_override reason must be a non-empty string")
    return scores, sorted(reason for reason, enabled in flags.items() if enabled), lane, reason


def _score_lane(total: int, cuts: dict[str, list[int]]) -> str:
    for lane in LANES:
        lower, upper = cuts[lane]
        if lower <= total <= upper:
            return lane
    raise RiskRouterError("total is outside core cuts")


def decide(core: dict[str, Any], payload: object, overlay: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a JSON-safe deterministic routing decision from policy data and structured input."""
    _validate_core_policy(core)
    if overlay is not None:
        validate_overlay(core, overlay)
    effective = _effective_policy(core, overlay)
    scores, triggered, override_lane, override_reason = _validate_input(payload, set(effective["promotions"]))
    total = sum(scores[axis] for axis in SCORE_FIELDS)
    score_lane = _score_lane(total, effective["cuts"])
    promotions = [{"reason": reason, "minimum_lane": effective["promotions"][reason]} for reason in triggered]
    lane = score_lane
    for promotion in promotions:
        if _lane_index(promotion["minimum_lane"]) > _lane_index(lane):
            lane = promotion["minimum_lane"]
    if override_lane is not None:
        if _lane_index(override_lane) < _lane_index(lane):
            raise RiskRouterError("human override cannot lower the computed lane")
        if _lane_index(override_lane) > _lane_index(lane):
            lane = override_lane
            promotions.append({"reason": override_reason, "minimum_lane": override_lane, "source": "human_override"})
    core_hash = _canonical_hash(core)
    overlay_hash = _canonical_hash(overlay or {})
    return {
        "router_version": ROUTER_VERSION,
        "scores": {axis: scores[axis] for axis in SCORE_FIELDS},
        "total": total,
        "score_lane": score_lane,
        "lane": lane,
        "promotion_reasons": promotions,
        "required_artifacts": sorted(effective["lanes"][lane]["required_artifacts"]),
        "required_gates": sorted(effective["lanes"][lane]["required_gates"]),
        "policy_hashes": {
            "core": core_hash,
            "overlay": overlay_hash,
            "effective": _canonical_hash(effective),
        },
    }


def canonical_decision_json(decision: dict[str, Any]) -> str:
    """Serialize one decision as LF-terminated, byte-stable JSON."""
    return json.dumps(decision, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
