from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.task_control.manager import TaskControlError, block, create, missing_artifacts, orphan_artifacts, resume, show, transition
from tools.task_control.phase_gate import phase_gate
from tools.task_packet.transitions import ALLOWED_TRANSITIONS, PHASES


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


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


def make_task(tmp_path: Path, lane: str = "STANDARD") -> tuple[Path, Path]:
    root, commit = make_repo(tmp_path)
    task_dir = root / ".workflow/tasks/T-20260718000000-fixture"
    source = root / "constraints.md"
    required = {"FAST": ["task_packet"], "STANDARD": ["task_packet", "brief_spec"], "STRICT": ["task_packet", "brief_spec", "spec", "plan", "review_record"], "CONTROLLED": ["task_packet", "brief_spec", "spec", "plan", "review_record", "rollback_plan", "audit_evidence"]}[lane]
    task = {"task_id": "T-20260718000000-fixture", "goal": "fixture", "non_goals": [], "risk_inputs": {key: 0 for key in ("ambiguity", "change_scope", "data_security", "reversibility", "impact", "coordination", "context_pressure")}, "lane": lane, "risk_decision": {"router_version": 1, "total": 0, "score_lane": lane, "lane": lane, "promotion_reasons": [], "human_override_audit": None, "required_artifacts": required, "required_gates": [], "policy_hashes": {"core": "a" * 64, "overlay": "b" * 64, "effective": "c" * 64}, "overlay_provenance": None}, "acceptance_criteria": [{"id": "AC-01", "description": "works"}], "constraints": [{"id": "C-01", "description": "keep gate", "source_path": "constraints.md", "source_sha256": digest(source)}], "decision_refs": []}
    evidence = {"task_id": task["task_id"], "gate_runs": [], "findings": []}
    state = {"task_id": task["task_id"], "phase": "INTAKE", "revision": 0, "baseline": {"repo_root": ".", "commit": commit}, "current_ref": commit, "completed_items": [], "next_action": "start", "blockers": [], "transition": None}
    dump(task_dir / "task.json", task); dump(task_dir / "evidence.json", evidence); create(task_dir, state)
    for artifact in required:
        if artifact != "task_packet":
            (task_dir / "artifacts" / artifact / "run-001").mkdir(parents=True)
            (task_dir / "artifacts" / artifact / "run-001" / "result.txt").write_text("complete\n", encoding="utf-8")
    attestation = {"constraints": [{"constraint_id": "C-01", "source_path": "constraints.md", "source_sha256": digest(source), "applies_to_phases": list(PHASES), "prohibited_action_ids": ["write-contract"], "required_evidence_ids": ["E-01"], "planned_action_mapping": ["A-01"]}]}
    dump(task_dir / "context-attestation.json", attestation)
    return root, task_dir


@pytest.mark.parametrize("lane", sorted(ALLOWED_TRANSITIONS))
def test_every_transition_edge_succeeds_and_non_edge_fails(tmp_path: Path, lane: str) -> None:
    for index, (source, target) in enumerate(sorted(ALLOWED_TRANSITIONS[lane])):
        root, task_dir = make_task(tmp_path / f"{lane}-{index}", lane)
        state = show(task_dir)
        state.update({"phase": source, "revision": 1, "transition": {"from": "INTAKE", "to": source}})
        dump(task_dir / "state.json", state)
        if target in {"VERIFY", "COMPLETE"}:
            evidence = json.loads((task_dir / "evidence.json").read_text())
            evidence.update({"findings": [{"id": "F-01", "summary": "covered", "constraint_ids": ["C-01"]}], "gate_runs": [{"id": "E-01", "gate": "test", "status": "PASSED", "criterion_ids": ["AC-01"], "finding_ids": ["F-01"], "artifact": {"path": "artifacts/brief_spec/run-001/result.txt", "summary": "ok", "sha256": "d" * 64}}]})
            dump(task_dir / "evidence.json", evidence)
        assert transition(task_dir, target, 1)["phase"] == target
    root, task_dir = make_task(tmp_path / f"{lane}-nonedge", lane)
    before = (task_dir / "state.json").read_bytes()
    candidates = [(source, target) for source in PHASES for target in PHASES if (source, target) not in ALLOWED_TRANSITIONS[lane]]
    source, target = sorted(candidates)[0]
    state = show(task_dir); state.update({"phase": source, "revision": 1, "transition": {"from": "INTAKE", "to": source}}); dump(task_dir / "state.json", state)
    before = (task_dir / "state.json").read_bytes()
    with pytest.raises(TaskControlError): transition(task_dir, target, 1)
    assert (task_dir / "state.json").read_bytes() == before


def test_missing_artifact_and_stale_writer_leave_canonical_state_unchanged(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    for path in (task_dir / "artifacts/brief_spec").rglob("*"):
        if path.is_file(): path.unlink()
    before = (task_dir / "state.json").read_bytes()
    with pytest.raises(TaskControlError, match="missing required artifacts"):
        transition(task_dir, "EXECUTE", 0)
    assert (task_dir / "state.json").read_bytes() == before
    (task_dir / "artifacts/brief_spec/run-001/result.txt").write_text("complete\n")
    assert transition(task_dir, "EXECUTE", 0)["revision"] == 1
    with pytest.raises(TaskControlError, match="stale writer"):
        transition(task_dir, "REVIEW", 0)


def test_two_process_writers_with_one_revision_have_exactly_one_winner(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    command = [sys.executable, "-m", "tools.task_control", "transition", str(task_dir), "EXECUTE", "--expected-revision", "0"]
    first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    second = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    outcomes = [first.wait(), second.wait()]
    assert outcomes.count(0) == 1
    assert show(task_dir)["revision"] == 1


def test_blocker_requires_explicit_resolution_before_resume(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    blocked = block(task_dir, 0, {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})
    with pytest.raises(TaskControlError, match="all blockers"):
        resume(task_dir, "EXECUTE", blocked["revision"])
    resumed = resume(task_dir, "EXECUTE", blocked["revision"], resolve_blocker_ids=["B-01"])
    assert resumed["phase"] == "EXECUTE"
    assert resumed["blockers"] == []


def test_interrupted_temporary_write_leaves_one_valid_canonical_state(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    (task_dir / ".state.json.crash.tmp").write_text("{not-json", encoding="utf-8")
    assert show(task_dir)["revision"] == 0
    assert transition(task_dir, "EXECUTE", 0)["revision"] == 1
    assert show(task_dir)["revision"] == 1


def test_phase_gate_fails_closed_for_identity_attestation_blockers_and_actions(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    phase_gate(task_dir, 0, repo_root=root)
    with pytest.raises(TaskControlError, match="prohibited action"):
        phase_gate(task_dir, 0, repo_root=root, prohibited_actions=["write-contract"])
    with pytest.raises(TaskControlError, match="state revision"):
        phase_gate(task_dir, 9, repo_root=root)
    with pytest.raises(TaskControlError, match="baseline commit"):
        phase_gate(task_dir, 0, repo_root=root, baseline="0" * 40)
    outside, _ = make_repo(tmp_path / "wrong-worktree")
    with pytest.raises(TaskControlError, match="worktree task path"):
        phase_gate(task_dir, 0, repo_root=outside)
    dump(task_dir / "context-attestation.json", {"constraints": []})
    with pytest.raises(TaskControlError, match="constraint: C-01"):
        phase_gate(task_dir, 0, repo_root=root)
    root, task_dir = make_task(tmp_path / "block")
    state = show(task_dir); state["blockers"] = [{"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]}]; dump(task_dir / "state.json", state)
    with pytest.raises(TaskControlError, match="unresolved blockers"):
        phase_gate(task_dir, 0, repo_root=root)


def test_orphans_are_diagnostic_not_evidence(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    assert "artifacts/brief_spec/run-001/result.txt" in orphan_artifacts(task_dir)
    assert missing_artifacts(task_dir) == []
