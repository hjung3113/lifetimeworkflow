from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.risk_router.__main__ import main
from tools.risk_router.intake import create_packet
from tools.risk_router.router import (
    DEFAULT_POLICY,
    RiskRouterError,
    canonical_decision_json,
    decide,
    load_overlay,
    load_policy,
    load_project_overlay,
)


def _payload(total: int, **flags: bool) -> dict:
    values = [min(3, total - offset * 3) if total > offset * 3 else 0 for offset in range(7)]
    return {
        "scores": {
            "ambiguity": values[0],
            "change_scope": values[1],
            "data_security": values[2],
            "reversibility": values[3],
            "impact": values[4],
            "coordination": values[5],
            "context_pressure": values[6],
        },
        "fact_flags": flags,
    }


@pytest.fixture
def core() -> dict:
    return load_policy(DEFAULT_POLICY)


@pytest.mark.parametrize(
    ("total", "lane"),
    [
        (0, "FAST"),
        (4, "FAST"),
        (5, "STANDARD"),
        (9, "STANDARD"),
        (10, "STRICT"),
        (14, "STRICT"),
        (15, "CONTROLLED"),
        (21, "CONTROLLED"),
    ],
)
def test_cut_boundaries(core: dict, total: int, lane: str):
    decision = decide(core, _payload(total))
    assert decision["total"] == total
    assert decision["lane"] == lane


def test_same_input_and_policy_is_byte_identical(core: dict):
    payload = _payload(7, auth_authorization=True)
    assert canonical_decision_json(decide(core, payload)) == canonical_decision_json(
        decide(core, payload)
    )


def test_decision_contains_required_audit_fields_and_is_capability_neutral(core: dict):
    decision = decide(core, _payload(5))
    assert {
        "scores",
        "total",
        "lane",
        "promotion_reasons",
        "human_override_audit",
        "required_artifacts",
        "policy_hashes",
    } <= set(decision)
    rendered = canonical_decision_json(decision)
    assert "model" not in rendered.lower()
    assert "provider" not in rendered.lower()


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("auth_authorization", "STRICT"),
        ("payment", "CONTROLLED"),
        ("secret_pii", "STRICT"),
        ("destructive_data_change", "CONTROLLED"),
        ("unclear_rollback", "STRICT"),
        ("external_contract_break", "STRICT"),
        ("constitution_plane_touch", "STRICT"),
        ("golden_or_contract_mutation", "CONTROLLED"),
        ("repeated_constraint_violation", "STRICT"),
    ],
)
def test_auto_promotions_beat_score_lane(core: dict, reason: str, expected: str):
    decision = decide(core, _payload(0, **{reason: True}))
    assert decision["score_lane"] == "FAST"
    assert decision["lane"] == expected
    assert decision["promotion_reasons"] == [{"reason": reason, "minimum_lane": expected}]


def test_human_override_can_raise_but_not_lower(core: dict):
    payload = _payload(0)
    payload["human_override"] = {"lane": "STRICT", "reason": "human review requested"}
    assert decide(core, payload)["lane"] == "STRICT"
    payload = _payload(10)
    payload["human_override"] = {"lane": "FAST", "reason": "unsafe downgrade"}
    with pytest.raises(RiskRouterError, match="cannot lower"):
        decide(core, payload)


@pytest.mark.parametrize("lane", ("FAST", "STANDARD", "STRICT", "CONTROLLED"))
def test_human_override_is_always_preserved_as_audit_record(core: dict, lane: str):
    payload = _payload(10)
    payload["human_override"] = {"lane": lane, "reason": "record this human decision"}
    if lane in ("FAST", "STANDARD"):
        with pytest.raises(RiskRouterError, match="cannot lower"):
            decide(core, payload)
    else:
        decision = decide(core, payload)
        assert decision["human_override_audit"] == {
            "lane": lane,
            "reason": "record this human decision",
        }


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"scores": _payload(0)["scores"] | {"ambiguity": 4}},
        _payload(0, unknown_reason=True),
    ],
)
def test_missing_out_of_range_and_unknown_reason_fail(core: dict, payload: dict):
    with pytest.raises(RiskRouterError):
        decide(core, payload)


def test_cli_invalid_input_exits_nonzero(tmp_path: Path, capsys):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(_payload(0, unknown_reason=True)), encoding="utf-8")
    assert main(["--input", str(path)]) == 1
    assert "FAIL:" in capsys.readouterr().err


@pytest.mark.parametrize("newline", ("\n", "\r\n"))
def test_cli_strips_bom_and_accepts_lf_or_crlf(tmp_path: Path, capsys, newline: str):
    path = tmp_path / "bom.json"
    path.write_bytes(
        ("\ufeff" + json.dumps(_payload(0), indent=2).replace("\n", newline)).encode("utf-8")
    )
    assert main(["--input", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["lane"] == "FAST"


def test_fast_stays_ceremony_free(core: dict):
    decision = decide(core, _payload(0))
    assert decision["required_artifacts"] == ["task_packet"]
    assert set(decision["required_gates"]) == {"lint", "test"}


def test_controlled_has_human_dry_run_rollback_and_audit(core: dict):
    decision = decide(core, _payload(21))
    assert {"rollback_plan", "audit_evidence"} <= set(decision["required_artifacts"])
    assert {"human_review", "dry_run", "rollback_verified"} <= set(decision["required_gates"])


def test_overlay_only_escalates_and_effective_is_never_weaker(core: dict, tmp_path: Path):
    overlay_path = tmp_path / "overlay.toml"
    overlay_path.write_text(
        """[minimum_lanes]\nauth_authorization = \"CONTROLLED\"\n\n[additional_promotions]\nlocal_audit_required = \"STRICT\"\n\n[lanes.FAST]\nrequired_gates_add = [\"local_audit\"]\n""",
        encoding="utf-8",
    )
    overlay = load_overlay(overlay_path, core)
    for total in range(22):
        payload = _payload(total, auth_authorization=total % 2 == 0)
        core_decision = decide(core, payload)
        effective_decision = decide(core, payload, overlay)
        ordering = {
            lane: index for index, lane in enumerate(("FAST", "STANDARD", "STRICT", "CONTROLLED"))
        }
        assert ordering[effective_decision["lane"]] >= ordering[core_decision["lane"]]
        assert set(effective_decision["required_artifacts"]) >= set(
            core_decision["required_artifacts"]
        )
        assert set(effective_decision["required_gates"]) >= set(core_decision["required_gates"])
    for lower_total in range(22):
        for higher_total in range(lower_total, 22):
            lower = decide(core, _payload(lower_total), overlay)
            higher = decide(core, _payload(higher_total), overlay)
            assert set(higher["required_artifacts"]) >= set(lower["required_artifacts"])
            assert set(higher["required_gates"]) >= set(lower["required_gates"])


def test_every_lane_promotion_keeps_lower_lane_requirements(core: dict):
    for lower_total in range(22):
        lower = decide(core, _payload(lower_total))
        for higher_total in range(lower_total, 22):
            higher = decide(core, _payload(higher_total))
            assert set(higher["required_artifacts"]) >= set(lower["required_artifacts"])
            assert set(higher["required_gates"]) >= set(lower["required_gates"])


def test_decide_does_not_read_overlay_schema_after_loading(core: dict, tmp_path: Path, monkeypatch):
    overlay_path = tmp_path / "overlay.toml"
    overlay_path.write_text(
        '[lanes.FAST]\nrequired_gates_add = ["local_audit"]\n', encoding="utf-8"
    )
    overlay = load_overlay(overlay_path, core)
    import tools.risk_router.router as router

    monkeypatch.setattr(router, "OVERLAY_SCHEMA", tmp_path / "missing.schema.json")
    assert decide(core, _payload(0), overlay)["required_gates"] == ["lint", "local_audit", "test"]


def test_intake_creates_a_valid_phase18_packet(core: dict, tmp_path: Path):
    request = {
        "task": {
            "task_id": "T-20260718210000-risk-intake",
            "goal": "Prove deterministic intake packet generation.",
            "non_goals": ["Mutate contracts."],
            "acceptance_criteria": [{"id": "AC-01", "description": "Packet validates."}],
            "constraints": [],
            "decision_refs": [],
            "stop_condition": "stop after packet intake",
        },
        "routing": _payload(0, golden_or_contract_mutation=True),
        "baseline": {"commit": "a" * 40},
    }
    packet = tmp_path / "packet"
    decision = create_packet(request, packet)
    assert decision["lane"] == "CONTROLLED"
    from tools.task_packet.validate import validate_packet

    documents = validate_packet(packet)
    assert documents["task"]["risk_decision"]["policy_hashes"] == decision["policy_hashes"]
    assert documents["task"]["risk_decision"]["promotion_reasons"] == decision["promotion_reasons"]


def test_intake_accepts_a_task_without_optional_stop_condition(core: dict, tmp_path: Path):
    request = {
        "task": {
            "task_id": "T-20260718210001-optional-stop",
            "goal": "Prove optional task stop condition.",
            "non_goals": [],
            "acceptance_criteria": [{"id": "AC-01", "description": "Packet validates."}],
            "constraints": [],
            "decision_refs": [],
        },
        "routing": _payload(0),
        "baseline": {"commit": "a" * 40},
    }
    packet = tmp_path / "packet"
    create_packet(request, packet)
    from tools.task_packet.validate import validate_packet

    assert "stop_condition" not in validate_packet(packet)["task"]


def test_project_slot_loads_only_an_explicit_overlay(core: dict, tmp_path: Path):
    overlay = tmp_path / "overlay.toml"
    overlay.write_text('[lanes.FAST]\nrequired_gates_add = ["local_audit"]\n', encoding="utf-8")
    project = tmp_path / "project.toml"
    project.write_text('[instance]\nrisk_overlay = "overlay.toml"\n', encoding="utf-8")
    loaded = load_project_overlay(project, core)
    assert loaded is not None
    assert loaded["lanes"] == {"FAST": {"required_gates_add": ["local_audit"]}}
    assert loaded["_provenance"]["source"] == "external/overlay.toml"


@pytest.mark.parametrize(
    "overlay",
    [
        {"cuts": {"FAST": [0, 21]}},
        {"lanes": {"FAST": {"required_gates": []}}},
        {"lanes": {"FAST": {"required_artifacts": []}}},
        {"minimum_lanes": {"payment": "FAST"}},
        {"additional_promotions": {"payment": "CONTROLLED"}},
    ],
)
def test_overlay_relaxations_and_core_replacements_are_rejected(
    core: dict, overlay: dict, tmp_path: Path
):
    path = tmp_path / "overlay.toml"
    lines = []
    for key, value in overlay.items():
        if key == "cuts":
            lines.append("[cuts]\nFAST = [0, 21]")
        elif key == "lanes":
            lines.append("[lanes.FAST]\nrequired_gates = []")
        elif key == "minimum_lanes":
            lines.append('[minimum_lanes]\npayment = "FAST"')
        else:
            lines.append('[additional_promotions]\npayment = "CONTROLLED"')
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(RiskRouterError):
        load_overlay(path, core)
