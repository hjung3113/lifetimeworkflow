"""Execute ratification-pending lifecycle fixtures through the existing primitives."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from tools.discipline.check import (
    load_declarations,
    missing_disciplines,
    record_path,
    required_disciplines,
)
from tools.evidence.capture import add_finding, capture
from tools.handoff.handoff import activate, generate
from tools.risk_router.intake import create_packet
from tools.risk_router.router import LANES, decide, load_policy
from tools.task_control.manager import (
    TaskControlError,
    attest,
    missing_artifacts,
    refresh_ref,
    show,
    transition,
)
from tools.task_control.phase_gate import phase_gate
from tools.task_packet.transitions import required_artifacts_for_phase

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures") / "lane-fixtures.json"
NEGATIVE_FIXTURES = FIXTURES.with_name("negative-fixtures.json")


class LifecycleEvalError(ValueError):
    """A fixture is malformed or contradicts the deterministic lifecycle policy."""


def load_fixtures(path: Path = FIXTURES) -> list[dict[str, Any]]:
    value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    fixtures = value.get("fixtures") if isinstance(value, dict) else None
    if not isinstance(fixtures, list) or len(fixtures) != 20:
        raise LifecycleEvalError("exactly 20 lifecycle fixtures are required")
    return fixtures


def verify_negative_fixtures(path: Path = NEGATIVE_FIXTURES) -> None:
    """Bind every negative scenario to a collected executable regression node."""
    value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    fixtures = value.get("fixtures") if isinstance(value, dict) else None
    if not isinstance(fixtures, list) or len(fixtures) != 12:
        raise LifecycleEvalError("exactly 12 negative lifecycle fixtures are required")
    collected = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if collected.returncode:
        raise LifecycleEvalError(f"pytest collection failed: {collected.stderr.strip()}")
    nodes = set(collected.stdout.splitlines())
    for fixture in fixtures:
        if not isinstance(fixture, dict) or fixture.get("expected") != "BLOCKED":
            raise LifecycleEvalError("negative fixture must be a BLOCKED object")
        verified_by = fixture.get("verified_by")
        if not isinstance(verified_by, str) or "::" not in verified_by:
            raise LifecycleEvalError(f"negative fixture lacks verified_by: {fixture.get('id')}")
        module, test = verified_by.split("::", 1)
        node = module.replace(".", "/") + ".py::" + test
        if not any(item == node or item.startswith(node + "[") for item in nodes):
            raise LifecycleEvalError(f"negative fixture verification node is not collected: {verified_by}")


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise LifecycleEvalError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _commit(root: Path, message: str, *paths: str) -> str:
    _git(root, "add", *paths)
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def _artifact(packet: Path, name: str) -> None:
    artifact = packet / "artifacts" / name / "run-001" / "result.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("complete\n", encoding="utf-8")


def _materialize_required_artifacts(packet: Path, lane: str, target: str) -> None:
    for name in required_artifacts_for_phase(lane, target):
        if name != "task_packet":
            _artifact(packet, name)


def _materialize_required_disciplines(packet: Path, lane: str, target: str) -> None:
    """Write a well-formed discipline record for every discipline the lane owes at *target*.

    The fixture exercises the lifecycle end to end, so it must satisfy the lane's METHOD obligations
    the same way it satisfies its artifact obligations — otherwise every STRICT+ fixture stops at
    the first discipline refusal.
    """
    declarations = load_declarations()
    for identifier in required_disciplines(lane, target, declarations=declarations):
        declaration = declarations[identifier]
        record: dict[str, Any] = {
            "discipline": identifier,
            "skill": declaration.skill,
            "task_id": packet.name,
            "satisfied_at_phase": declaration.owed_by_phase,
            "outputs": ["constraints.md"],
        }
        if declaration.min_experts is not None:
            record["panel"] = {
                "reviews": [
                    {"expert": f"seat-{index}", "verdict": "pass", "finding_ids": []}
                    for index in range(declaration.min_experts)
                ]
            }
        path = record_path(packet, identifier)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


def _assert_missing_disciplines_reject(packet: Path, target: str) -> None:
    """A declared discipline must REFUSE the transition before it is recorded."""
    try:
        transition(packet, target, show(packet)["revision"])
    except TaskControlError as exc:
        if "missing required disciplines" not in str(exc):
            raise LifecycleEvalError(f"{target} rejected for the wrong reason: {exc}") from exc
        return
    raise LifecycleEvalError(f"{target} accepted an unsatisfied lane discipline")


def _assert_missing_artifacts_reject(packet: Path, target: str) -> None:
    try:
        transition(packet, target, show(packet)["revision"])
    except TaskControlError as exc:
        if "missing required artifacts" not in str(exc):
            raise LifecycleEvalError(f"{target} rejected for the wrong reason: {exc}") from exc
        return
    raise LifecycleEvalError(f"{target} accepted without its required artifacts")


def _capture_evidence(packet: Path) -> None:
    record = capture(packet, "lint", ["ruff", "check", "."], criterion_ids=["AC-01"], finding_ids=["F-01"])
    add_finding(packet, {"id": "F-01", "summary": "fixture constraint covered", "constraint_ids": ["C-01"], "severity": "minor", "disposition": "resolved", "evidence_ref": record["id"]})


def _resume_in_fresh_process(root: Path, state_dir: Path) -> None:
    environment = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    child = subprocess.run(
        [sys.executable, "-m", "tools.handoff", "resume", "--state-dir", str(state_dir), "--repo-root", str(root)],
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    if child.returncode:
        raise LifecycleEvalError(f"fresh-process orient/phase-gate failed: {child.stderr.strip() or child.stdout.strip()}")
    payload = json.loads(child.stdout)
    if not isinstance(payload.get("resume"), dict):
        raise LifecycleEvalError("fresh-process orient did not reconstruct the handoff")


def _assert_policy_and_transition_contract(lane: str, decision: dict[str, Any]) -> None:
    """Reject policy/transition drift before exercising the packet it would create."""
    artifacts = set(decision["required_artifacts"])
    gates = set(decision["required_gates"])
    transition_artifacts = set(required_artifacts_for_phase(lane, "COMPLETE"))
    if artifacts != transition_artifacts:
        raise LifecycleEvalError(f"policy and COMPLETE artifact contract differ for {lane}")
    if lane == "FAST":
        forbidden = {"review", "human_review", "spec", "plan"}
        if artifacts != {"task_packet"} or gates != {"lint", "test"} or forbidden & (artifacts | gates):
            raise LifecycleEvalError("FAST policy ceremony regressed")
    if lane == "STRICT" and ("review_record" not in artifacts or not {"review", "human_review"} <= gates or "rollback_plan" in artifacts):
        raise LifecycleEvalError("STRICT policy obligations differ from the ratified contract")
    if lane == "CONTROLLED" and (not {"review_record", "rollback_plan"} <= artifacts or not {"review", "human_review", "rollback_verified"} <= gates):
        raise LifecycleEvalError("CONTROLLED policy obligations differ from the ratified contract")


def _exercise_fixture(fixture: dict[str, Any], decision: dict[str, Any], root_parent: Path) -> dict[str, Any]:
    identifier = fixture["id"]
    root = root_parent / identifier
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "Lifecycle Fixture")
    constraint = root / "constraints.md"
    constraint.write_text("do not bypass lifecycle gates\n", encoding="utf-8")
    baseline = _commit(root, "fixture baseline", "constraints.md")
    packet = root / ".workflow" / "tasks" / f"T-20260719000000-{identifier.lower()}"
    request = {
        "task": {"task_id": packet.name, "goal": "exercise lifecycle", "non_goals": [], "acceptance_criteria": [{"id": "AC-01", "description": "lifecycle completes"}], "constraints": [{"id": "C-01", "description": "preserve lifecycle gates", "source_path": "constraints.md", "source_sha256": hashlib.sha256(constraint.read_bytes()).hexdigest()}], "decision_refs": [], "stop_condition": "fixture completed"},
        "routing": fixture["risk"],
        "baseline": {"commit": baseline},
    }
    intake_decision = create_packet(request, packet)
    if intake_decision != decision:
        raise LifecycleEvalError(f"intake decision drifted from router: {identifier}")
    attest(packet, {"constraints": [{"constraint_id": "C-01", "source_path": "wrong", "source_sha256": "0" * 64, "applies_to_phases": ["INTAKE", "CLARIFY", "SPEC", "PLAN", "EXECUTE", "REVIEW", "VERIFY", "COMPLETE"], "prohibited_action_ids": ["bypass-gate"], "required_evidence_ids": ["E-01"], "planned_action_mapping": ["A-01"]}]})
    lane = decision["lane"]
    _assert_policy_and_transition_contract(lane, decision)
    events: list[dict[str, Any]] = [{"event": "intake", "user_visible": True}]
    targets = {"FAST": ("EXECUTE", "VERIFY", "COMPLETE"), "STANDARD": ("EXECUTE", "VERIFY", "COMPLETE"), "STRICT": ("CLARIFY", "SPEC", "PLAN", "EXECUTE", "REVIEW", "VERIFY", "COMPLETE"), "CONTROLLED": ("CLARIFY", "SPEC", "PLAN", "EXECUTE", "REVIEW", "VERIFY", "COMPLETE")}[lane]
    for target in targets:
        required = required_artifacts_for_phase(lane, target)
        if missing_artifacts(packet, list(required)):
            _assert_missing_artifacts_reject(packet, target)
            _materialize_required_artifacts(packet, lane, target)
        if missing_disciplines(packet, target):
            _assert_missing_disciplines_reject(packet, target)
            _materialize_required_disciplines(packet, lane, target)
        state = transition(packet, target, show(packet)["revision"])
        events.append({"event": f"transition:{state['phase']}", "user_visible": target == "VERIFY"})
        phase_gate(packet, state["revision"], repo_root=root)
        if target == "EXECUTE":
            _capture_evidence(packet)
            generate(packet)
            state_dir = root / ".memory" / "state"
            state_dir.mkdir(parents=True)
            activate(packet, state_dir)
            checkpoint = _commit(root, "handoff checkpoint", ".workflow", ".memory/state/active-task.json")
            _resume_in_fresh_process(root, state_dir)
            refreshed = refresh_ref(packet, show(packet)["revision"], checkpoint)
            phase_gate(packet, refreshed["revision"], repo_root=root)
        if target == "VERIFY":
            checkpoint = _commit(root, "evidence checkpoint", ".workflow")
            refresh_ref(packet, show(packet)["revision"], checkpoint)
    if show(packet)["phase"] != "COMPLETE":
        raise LifecycleEvalError(f"fixture did not complete: {identifier}")
    if lane == "FAST":
        if sum(event["user_visible"] for event in events) > 2:
            raise LifecycleEvalError(f"FAST user-visible ceremony exceeded two steps: {identifier}")
    return {"events": events, "phase": show(packet)["phase"]}


def evaluate(fixtures: list[dict[str, Any]]) -> list[dict[str, str]]:
    policy = load_policy()
    results: list[dict[str, str]] = []
    ids: set[str] = set()
    with tempfile.TemporaryDirectory(prefix="lifecycle-eval-") as temporary:
        workspace = Path(temporary)
        for fixture in fixtures:
            if not isinstance(fixture, dict) or not isinstance(fixture.get("id"), str):
                raise LifecycleEvalError("fixture id is required")
            identifier = fixture["id"]
            if identifier in ids:
                raise LifecycleEvalError(f"duplicate fixture: {identifier}")
            ids.add(identifier)
            expected = fixture.get("expected")
            if not isinstance(expected, dict) or expected.get("lane") not in LANES or expected.get("result") != "PASS":
                raise LifecycleEvalError(f"invalid expected result: {identifier}")
            decision = decide(policy, fixture.get("risk"))
            actual = decision["lane"]
            if actual != expected["lane"]:
                raise LifecycleEvalError(f"false downgrade or lane mismatch: {identifier}: expected {expected['lane']}, got {actual}")
            lifecycle = _exercise_fixture(fixture, decision, workspace)
            if lifecycle["phase"] != "COMPLETE":
                raise LifecycleEvalError(f"lifecycle did not reach COMPLETE: {identifier}")
            results.append({"id": identifier, "lane": actual, "result": "PASS"})
    if {item["lane"] for item in results} != set(LANES):
        raise LifecycleEvalError("every lane must be represented")
    if any(sum(1 for item in results if item["lane"] == lane) != 5 for lane in LANES):
        raise LifecycleEvalError("five fixtures per lane are required")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate lifecycle lane fixtures")
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    args = parser.parse_args(argv)
    try:
        results = evaluate(load_fixtures(args.fixtures))
        verify_negative_fixtures()
        print(json.dumps({"fixtures": results, "false_downgrades_enforced_zero": True}, sort_keys=True))
    except (OSError, json.JSONDecodeError, LifecycleEvalError, TaskControlError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
