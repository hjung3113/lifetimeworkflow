from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import types
from pathlib import Path

import pytest

from tools.risk_router.intake import create_packet
import tools.evidence.capture as capture_module
from tools.evidence.capture import add_finding, capture
from tools.risk_router.router import decide, load_policy
from tools.task_control.manager import TaskControlError, attest, block, create, missing_artifacts, orphan_artifacts, refresh_ref, resume, show, transition, validate
from tools.task_control.phase_gate import phase_gate
from tools.task_packet.transitions import ALLOWED_TRANSITIONS, PHASES, required_artifacts_for_phase


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture(autouse=True)
def canonical_gate_child(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep lifecycle fixtures fast while still exercising capture publication."""
    monkeypatch.setattr(capture_module, "subprocess", types.SimpleNamespace(
        run=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "PASS\n", ""),
    ))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True, capture_output=True).stdout.strip()


def make_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    (root / "constraints.md").write_text("do not bypass gates\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    return root, git(root, "rev-parse", "HEAD")


def add_artifact(task_dir: Path, name: str) -> Path:
    result = task_dir / "artifacts" / name / "run-001" / "result.txt"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("complete\n", encoding="utf-8")
    return result


def attestation_draft() -> dict:
    return {"constraints": [{"constraint_id": "C-01", "source_path": "wrong", "source_sha256": "0" * 64, "applies_to_phases": sorted(PHASES), "prohibited_action_ids": ["write-contract"], "required_evidence_ids": ["E-01"], "planned_action_mapping": ["A-01"]}]}


def make_task(tmp_path: Path, lane: str = "STANDARD") -> tuple[Path, Path]:
    root, commit = make_repo(tmp_path)
    task_dir = root / ".workflow/tasks/T-20260718000000-fixture"
    source = root / "constraints.md"
    policy = load_policy()
    decision = decide(policy, {"scores": {key: 0 for key in ("ambiguity", "change_scope", "data_security", "reversibility", "impact", "coordination", "context_pressure")}, "human_override": {"lane": lane, "reason": "fixture"}})
    decision.pop("scores")
    task = {"task_id": "T-20260718000000-fixture", "goal": "fixture", "non_goals": [], "risk_inputs": {key: 0 for key in ("ambiguity", "change_scope", "data_security", "reversibility", "impact", "coordination", "context_pressure")}, "lane": lane, "risk_decision": decision, "acceptance_criteria": [{"id": "AC-01", "description": "works"}], "constraints": [{"id": "C-01", "description": "keep gate", "source_path": "constraints.md", "source_sha256": digest(source)}], "decision_refs": [], "stop_condition": "stop after fixture gate"}
    evidence = {"task_id": task["task_id"], "gate_runs": [], "findings": [], "redaction_report": {"status": "CLEAR", "refused_fields": []}}
    state = {"task_id": task["task_id"], "phase": "INTAKE", "revision": 0, "baseline": {"repo_root": ".", "commit": commit}, "current_ref": commit, "completed_items": [], "next_action": "start", "blockers": [], "transition": None}
    dump(task_dir / "task.json", task); dump(task_dir / "evidence.json", evidence); create(task_dir, state)
    attest(task_dir, attestation_draft())
    return root, task_dir


def cover_constraints(task_dir: Path, artifact: Path | None = None, *, artifacts: list[Path] | None = None) -> None:
    # A real child capture replaces the former hand-written PASSED record.
    if json.loads((task_dir / "evidence.json").read_text())["findings"]:
        return
    record = capture(task_dir, "tests", ["uv", "run", "pytest"], criterion_ids=["AC-01"], finding_ids=["F-01"])
    add_finding(task_dir, {"id": "F-01", "summary": "covered", "constraint_ids": ["C-01"], "severity": "minor", "disposition": "resolved", "evidence_ref": record["id"]})


def satisfy_target(task_dir: Path, lane: str, target: str) -> None:
    for name in required_artifacts_for_phase(lane, target):
        if name != "task_packet":
            add_artifact(task_dir, name)
    if target in {"VERIFY", "COMPLETE"}:
        cover_constraints(task_dir)
    if target == "COMPLETE":
        root = next(parent for parent in task_dir.parents if (parent / ".git").exists())
        subprocess.run(["git", "-C", str(root), "add", task_dir.relative_to(root) / "evidence.json"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "evidence"], check=True)
        refresh_ref(task_dir, show(task_dir)["revision"], git(root, "rev-parse", "HEAD"))


@pytest.mark.parametrize("lane", sorted(ALLOWED_TRANSITIONS))
def test_every_transition_edge_succeeds_and_every_non_edge_fails(tmp_path: Path, lane: str) -> None:
    for index, (source, target) in enumerate(sorted(ALLOWED_TRANSITIONS[lane])):
        root, task_dir = make_task(tmp_path / f"{lane}-edge-{index}", lane)
        state = show(task_dir)
        state.update({"phase": source, "revision": 1, "transition": {"from": "INTAKE", "to": source}})
        dump(task_dir / "state.json", state)
        satisfy_target(task_dir, lane, target)
        if target == "BLOCKED":
            assert block(task_dir, show(task_dir)["revision"], {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})["phase"] == target
        else:
            assert transition(task_dir, target, show(task_dir)["revision"])["phase"] == target
    for index, (source, target) in enumerate(sorted((pair for source in PHASES for target in PHASES if (pair := (source, target)) not in ALLOWED_TRANSITIONS[lane]))):
        root, task_dir = make_task(tmp_path / f"{lane}-nonedge-{index}", lane)
        state = show(task_dir); state.update({"phase": source, "revision": 1, "transition": {"from": "INTAKE", "to": source}}); dump(task_dir / "state.json", state)
        before = (task_dir / "state.json").read_bytes()
        with pytest.raises(TaskControlError):
            if target == "BLOCKED": block(task_dir, 1, {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})
            else: transition(task_dir, target, 1)
        assert (task_dir / "state.json").read_bytes() == before


def test_phase_oriented_artifacts_allow_strict_and_controlled_lifecycle(tmp_path: Path) -> None:
    for lane in ("STRICT", "CONTROLLED"):
        root, task_dir = make_task(tmp_path / lane, lane)
        revision = 0
        phase_gate(task_dir, revision, repo_root=root)
        for target in ("CLARIFY", "SPEC", "PLAN", "EXECUTE", "REVIEW", "VERIFY", "COMPLETE"):
            satisfy_target(task_dir, lane, target)
            if target in {"VERIFY", "COMPLETE"}:
                cover_constraints(task_dir, artifacts=sorted((task_dir / "artifacts").rglob("result.txt")))
            revision = show(task_dir)["revision"]
            # The documented gate runs before every transition, not only after lifecycle completion.
            phase_gate(task_dir, revision, repo_root=root)
            state = transition(task_dir, target, revision)
            revision = state["revision"]
            phase_gate(task_dir, revision, repo_root=root)
        assert state["phase"] == "COMPLETE"


def test_policy_tampering_and_invalid_evidence_are_rejected(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "CONTROLLED")
    task = json.loads((task_dir / "task.json").read_text()); task["risk_decision"]["required_artifacts"] = ["task_packet"]; dump(task_dir / "task.json", task)
    with pytest.raises(TaskControlError, match="weaken"):
        transition(task_dir, "CLARIFY", 0)
    root, task_dir = make_task(tmp_path / "hash", "CONTROLLED")
    task = json.loads((task_dir / "task.json").read_text()); task["risk_decision"]["policy_hashes"]["effective"] = "0" * 64; dump(task_dir / "task.json", task)
    with pytest.raises(TaskControlError, match="policy hash"):
        transition(task_dir, "CLARIFY", 0)
    root, task_dir = make_task(tmp_path / "evidence", "FAST")
    state = show(task_dir); state.update({"phase": "EXECUTE", "revision": 1, "transition": {"from": "INTAKE", "to": "EXECUTE"}}); dump(task_dir / "state.json", state)
    dump(task_dir / "evidence.json", {"task_id": show(task_dir)["task_id"], "gate_runs": [{"constraint_ids": ["C-01"]}], "findings": []})
    with pytest.raises(TaskControlError, match="evidence.json"):
        transition(task_dir, "VERIFY", 1)


def test_block_obeys_matrix_and_legal_state_succeeds(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    state = show(task_dir); state.update({"phase": "COMPLETE", "revision": 1, "transition": {"from": "VERIFY", "to": "COMPLETE"}}); dump(task_dir / "state.json", state)
    with pytest.raises(TaskControlError, match="illegal transition"):
        block(task_dir, 1, {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})
    root, task_dir = make_task(tmp_path / "legal")
    assert block(task_dir, 0, {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})["phase"] == "BLOCKED"


def test_crash_after_fsync_leaves_valid_canonical_and_next_mutation_succeeds(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    command = [sys.executable, "-m", "tools.task_control", "transition", str(task_dir), "EXECUTE", "--expected-revision", "0"]
    crashed = subprocess.run(command, env={**os.environ, "TASK_CONTROL_FAULT_AFTER_FSYNC": "1"})
    assert crashed.returncode == 86
    assert show(task_dir)["revision"] == 0
    assert transition(task_dir, "EXECUTE", 0)["revision"] == 1
    assert any(name.endswith((".tmp", ".cas")) for name in validate(task_dir)["write_residues"])


def test_two_process_writers_with_one_revision_have_exactly_one_winner(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    command = [sys.executable, "-m", "tools.task_control", "transition", str(task_dir), "EXECUTE", "--expected-revision", "0"]
    barrier = threading.Barrier(3)
    outcomes: list[int] = []
    def run() -> None:
        barrier.wait(); outcomes.append(subprocess.run(command, capture_output=True).returncode)
    threads = [threading.Thread(target=run) for _ in range(2)]
    [thread.start() for thread in threads]; barrier.wait(); [thread.join() for thread in threads]
    assert outcomes.count(0) == 1
    assert show(task_dir)["revision"] == 1


def test_two_process_creates_have_exactly_one_winner(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    state = show(task_dir)
    (task_dir / "state.json").unlink()
    state_file = tmp_path / "initial-state.json"; dump(state_file, state)
    command = [sys.executable, "-m", "tools.task_control", "create", str(task_dir), "--state", str(state_file)]
    barrier = threading.Barrier(3)
    outcomes: list[int] = []
    def run() -> None:
        barrier.wait(); outcomes.append(subprocess.run(command, capture_output=True).returncode)
    threads = [threading.Thread(target=run) for _ in range(2)]
    [thread.start() for thread in threads]; barrier.wait(); [thread.join() for thread in threads]
    assert outcomes.count(0) == 1
    assert show(task_dir)["revision"] == 0


def test_attest_refresh_ref_and_phase_gate(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "STANDARD")
    artifact = add_artifact(task_dir, "brief_spec"); cover_constraints(task_dir, artifact)
    state = transition(task_dir, "EXECUTE", show(task_dir)["revision"])
    phase_gate(task_dir, state["revision"], repo_root=root)
    (root / "change.txt").write_text("change\n"); subprocess.run(["git", "-C", str(root), "add", "."], check=True); subprocess.run(["git", "-C", str(root), "commit", "-qm", "change"], check=True)
    with pytest.raises(TaskControlError, match="current ref"):
        phase_gate(task_dir, state["revision"], repo_root=root)
    refreshed = refresh_ref(task_dir, state["revision"], git(root, "rev-parse", "HEAD"))
    phase_gate(task_dir, refreshed["revision"], repo_root=root)


def test_orphans_are_diagnostic_before_verify_and_block_verify(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    artifact = add_artifact(task_dir, "brief_spec")
    cover_constraints(task_dir, artifact)
    orphan = task_dir / "artifacts" / "tests" / "unreferenced" / "output.log"
    orphan.parent.mkdir(parents=True, exist_ok=True); orphan.write_text("orphan\n", encoding="utf-8")
    assert orphan_artifacts(task_dir)
    assert phase_gate(task_dir, show(task_dir)["revision"], repo_root=root) == [f"orphan artifact: {orphan.relative_to(task_dir).as_posix()}"]
    state = show(task_dir); state.update({"phase": "VERIFY", "revision": 1, "transition": {"from": "EXECUTE", "to": "VERIFY"}}); dump(task_dir / "state.json", state)
    with pytest.raises(TaskControlError, match="orphan artifact"):
        phase_gate(task_dir, 1, repo_root=root)


def test_phase_gate_accepts_every_strict_and_controlled_phase(tmp_path: Path) -> None:
    for lane in ("STRICT", "CONTROLLED"):
        root, task_dir = make_task(tmp_path / f"gate-{lane}", lane)
        revision = 0
        phase_gate(task_dir, revision, repo_root=root)
        for target in ("CLARIFY", "SPEC", "PLAN", "EXECUTE", "REVIEW", "VERIFY", "COMPLETE"):
            satisfy_target(task_dir, lane, target)
            if target in {"VERIFY", "COMPLETE"}:
                cover_constraints(task_dir, artifacts=sorted((task_dir / "artifacts").rglob("result.txt")))
            revision = show(task_dir)["revision"]
            state = transition(task_dir, target, revision)
            revision = state["revision"]
            phase_gate(task_dir, revision, repo_root=root)


def test_overlay_packet_transitions_and_tampering_is_rejected(tmp_path: Path) -> None:
    root, commit = make_repo(tmp_path)
    task_dir = root / ".workflow/tasks/T-20260718000000-overlay"
    overlay = tmp_path / "overlay.toml"
    overlay.write_text('[lanes.FAST]\nrequired_gates_add = ["local_audit"]\n', encoding="utf-8")
    request = {"task": {"task_id": "T-20260718000000-overlay", "goal": "overlay", "non_goals": [], "acceptance_criteria": [{"id": "AC-01", "description": "works"}], "constraints": [], "decision_refs": [], "stop_condition": "stop after overlay"}, "routing": {"scores": {key: 0 for key in ("ambiguity", "change_scope", "data_security", "reversibility", "impact", "coordination", "context_pressure")}}, "baseline": {"commit": commit}}
    create_packet(request, task_dir, overlay_path=overlay)
    assert (task_dir / "risk-overlay.toml").read_bytes() == overlay.read_bytes()
    assert transition(task_dir, "EXECUTE", 0)["phase"] == "EXECUTE"
    task = json.loads((task_dir / "task.json").read_text()); task["risk_decision"]["policy_hashes"]["effective"] = "0" * 64; dump(task_dir / "task.json", task)
    with pytest.raises(TaskControlError, match="policy hash"):
        transition(task_dir, "VERIFY", 1)


def test_phase_artifact_contract_matches_policy_and_is_monotonic() -> None:
    policy = load_policy()
    ordered = ("EXECUTE", "REVIEW", "VERIFY", "COMPLETE")
    for lane, lane_policy in policy["lanes"].items():
        assert {phase: required_artifacts_for_phase(lane, phase) for phase in PHASES}
        phase_sets = [set(required_artifacts_for_phase(lane, phase)) for phase in ordered]
        assert phase_sets[-1] == set(lane_policy["required_artifacts"])
        assert all(earlier <= later for earlier, later in zip(phase_sets, phase_sets[1:]))
    with pytest.raises(ValueError, match="lane"):
        required_artifacts_for_phase("UNKNOWN", "EXECUTE")
    with pytest.raises(ValueError, match="missing"):
        required_artifacts_for_phase("FAST", "UNKNOWN")


def test_verify_requires_passing_evidence_for_every_required_criterion(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    state = transition(task_dir, "EXECUTE", 0)
    artifact = add_artifact(task_dir, "brief_spec")
    cover_constraints(task_dir, artifact)
    evidence = json.loads((task_dir / "evidence.json").read_text())
    evidence["gate_runs"][0]["criterion_ids"] = []
    dump(task_dir / "evidence.json", evidence)
    with pytest.raises(TaskControlError, match="integrity anchor mismatch"):
        transition(task_dir, "VERIFY", show(task_dir)["revision"])


def test_complete_rejects_unresolved_major_finding(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    state = transition(task_dir, "EXECUTE", 0)
    artifact = add_artifact(task_dir, "brief_spec")
    cover_constraints(task_dir, artifact)
    state = transition(task_dir, "VERIFY", show(task_dir)["revision"])
    evidence = json.loads((task_dir / "evidence.json").read_text())
    evidence["findings"][0].update({"severity": "major", "disposition": "open"})
    dump(task_dir / "evidence.json", evidence)
    with pytest.raises(TaskControlError, match="integrity anchor mismatch"):
        transition(task_dir, "COMPLETE", state["revision"])


def test_complete_requires_approval_reference_for_constitution_diff(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    state = transition(task_dir, "EXECUTE", 0)
    artifact = add_artifact(task_dir, "brief_spec")
    cover_constraints(task_dir, artifact)
    state = transition(task_dir, "VERIFY", show(task_dir)["revision"])
    (root / "contracts").mkdir(); (root / "contracts" / "changed.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True); subprocess.run(["git", "-C", str(root), "commit", "-qm", "constitution"], check=True)
    state = refresh_ref(task_dir, state["revision"], git(root, "rev-parse", "HEAD"))
    with pytest.raises(TaskControlError, match="approval"):
        transition(task_dir, "COMPLETE", state["revision"])
    (root / "approvals").mkdir(); (root / "approvals" / "fixture.json").write_text(json.dumps({"approved_paths": ["contracts/changed.json"]}), encoding="utf-8")
    capture(task_dir, "tests", ["uv", "run", "pytest"], human_approval_ref="approvals/fixture.json")
    with pytest.raises(TaskControlError, match="committed at HEAD"):
        transition(task_dir, "COMPLETE", show(task_dir)["revision"])
    subprocess.run(["git", "-C", str(root), "add", "approvals/fixture.json", task_dir.relative_to(root) / "evidence.json"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "approval-and-evidence"], check=True)
    assert transition(task_dir, "COMPLETE", show(task_dir)["revision"])["phase"] == "COMPLETE"


def test_complete_rejects_working_tree_rewrite_of_committed_approval(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    transition(task_dir, "EXECUTE", 0); add_artifact(task_dir, "brief_spec"); cover_constraints(task_dir)
    state = transition(task_dir, "VERIFY", show(task_dir)["revision"])
    (root / "contracts").mkdir(); (root / "contracts" / "changed.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True); subprocess.run(["git", "-C", str(root), "commit", "-qm", "constitution"], check=True)
    refresh_ref(task_dir, state["revision"], git(root, "rev-parse", "HEAD"))
    (root / "approvals").mkdir(); approval = root / "approvals" / "fixture.json"
    approval.write_text(json.dumps({"approved_paths": ["contracts/previous.json"]}), encoding="utf-8")
    capture(task_dir, "tests", ["uv", "run", "pytest"], human_approval_ref="approvals/fixture.json")
    subprocess.run(["git", "-C", str(root), "add", "approvals/fixture.json", task_dir.relative_to(root) / "evidence.json"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "wrong-approval-and-evidence"], check=True)
    approval.write_text(json.dumps({"approved_paths": ["contracts/changed.json"]}), encoding="utf-8")
    with pytest.raises(TaskControlError, match="approval"):
        transition(task_dir, "COMPLETE", show(task_dir)["revision"])
