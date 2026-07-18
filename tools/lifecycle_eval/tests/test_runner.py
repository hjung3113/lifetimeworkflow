from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.lifecycle_eval.runner import FIXTURES, LifecycleEvalError, evaluate, load_fixtures

NEGATIVE_FIXTURES = FIXTURES.with_name("negative-fixtures.json")


def test_twenty_human_ratification_pending_fixtures_match_router_with_zero_false_downgrade() -> None:
    fixtures = load_fixtures()
    results = evaluate(fixtures)
    assert len(results) == 20
    assert {item["lane"] for item in results} == {"FAST", "STANDARD", "STRICT", "CONTROLLED"}
    assert all(sum(item["lane"] == lane for item in results) == 5 for lane in {"FAST", "STANDARD", "STRICT", "CONTROLLED"})


def test_fast_ceremony_cap_and_high_risk_review_rollback_are_fixed() -> None:
    for fixture in load_fixtures():
        expected = fixture["expected"]
        if expected["lane"] == "FAST":
            assert expected["ceremony_max"] == 2
        if expected["lane"] in {"STRICT", "CONTROLLED"}:
            assert set(expected["requires"]) == {"independent_review", "rollback_evidence"}


def test_lane_mismatch_is_a_false_downgrade(tmp_path: Path) -> None:
    value = json.loads(FIXTURES.read_text(encoding="utf-8"))
    value["fixtures"][0]["expected"]["lane"] = "STANDARD"
    path = tmp_path / "fixtures.json"; path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(LifecycleEvalError, match="false downgrade"):
        evaluate(load_fixtures(path))


def test_negative_fixture_inventory_freezes_every_fail_closed_boundary() -> None:
    fixtures = json.loads(NEGATIVE_FIXTURES.read_text(encoding="utf-8"))["fixtures"]
    assert {item["scenario"] for item in fixtures} == {
        "buried_constraint_prohibited_action", "stale_handoff", "wrong_worktree_or_ref",
        "missing_evidence", "tampered_evidence", "concurrent_stale_writer", "secret_artifact",
        "constitution_change_without_approval", "illegal_downgrade_overlay",
        "unresumed_transition_write_deny", "resume_gate_env_git_commit_prefix",
        "resume_gate_git_c_commit_prefix",
    }
    assert all(item["expected"] == "BLOCKED" for item in fixtures)
