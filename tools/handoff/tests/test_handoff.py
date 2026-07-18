from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

import tools.evidence.capture as capture_module
from tools.evidence.capture import capture
from tools.handoff.handoff import HandoffError, activate, fresh_session, generate, resume, validate
from tools.risk_router.router import decide, load_policy
from tools.task_control.manager import attest, create


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True).stdout.strip()


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    root = tmp_path / "repo"; root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    (root / "constraints.md").write_text("no secret output\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "constraints.md"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    head = _git(root, "rev-parse", "HEAD")
    packet = root / ".workflow/tasks/T-20260719000000-handoff"
    policy = load_policy()
    decision = decide(policy, {"scores": {key: 0 for key in ("ambiguity", "change_scope", "data_security", "reversibility", "impact", "coordination", "context_pressure")}, "human_override": {"lane": "STANDARD", "reason": "fixture"}})
    decision.pop("scores")
    task = {"task_id": "T-20260719000000-handoff", "goal": "resume exactly", "non_goals": ["do not summarize a transcript"], "risk_inputs": {key: 0 for key in ("ambiguity", "change_scope", "data_security", "reversibility", "impact", "coordination", "context_pressure")}, "lane": "STANDARD", "risk_decision": decision, "acceptance_criteria": [{"id": "AC-01", "description": "resume"}], "constraints": [{"id": "C-01", "description": "keep boundary", "source_path": "constraints.md", "source_sha256": hashlib.sha256((root / "constraints.md").read_bytes()).hexdigest()}], "decision_refs": []}
    evidence = {"task_id": task["task_id"], "gate_runs": [], "findings": [], "redaction_report": {"status": "CLEAR", "refused_fields": []}}
    state = {"task_id": task["task_id"], "phase": "INTAKE", "revision": 0, "baseline": {"repo_root": ".", "commit": head}, "current_ref": head, "completed_items": [], "next_action": "run the phase gate", "blockers": [], "transition": None}
    _write(packet / "task.json", task); _write(packet / "evidence.json", evidence); create(packet, state)
    attest(packet, {"constraints": [{"constraint_id": "C-01", "source_path": "wrong", "source_sha256": "0" * 64, "applies_to_phases": ["INTAKE"], "prohibited_action_ids": [], "required_evidence_ids": [], "planned_action_mapping": ["A-01"]}]})
    monkeypatch.setattr(capture_module, "subprocess", types.SimpleNamespace(run=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "PASS\n", "")))
    capture(packet, "tests", ["uv", "run", "pytest"], criterion_ids=["AC-01"])
    return root, packet


def test_schema_hashes_and_fresh_session_reconstruction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    handoff = generate(packet)
    assert validate(packet) == handoff
    handoff_path = packet / "handoffs/revision-0000000001.json"
    assert fresh_session(handoff_path) == {
        "task_id": handoff["task_id"], "goal": handoff["goal"], "non_goals": handoff["non_goals"],
        "critical_constraint_ids": handoff["critical_constraint_ids"], "phase": handoff["phase"],
        "current_ref": handoff["current_ref"], "next_action": handoff["next_action"],
    }
    assert handoff["state_ref"]["path"].startswith(".workflow/tasks/")
    assert handoff["artifact_refs"][0]["path"].endswith("output.log")


@pytest.mark.parametrize("target", ("revision", "artifact"))
def test_stale_snapshot_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str) -> None:
    _, packet = _packet(tmp_path, monkeypatch); generate(packet)
    if target == "revision":
        state = json.loads((packet / "state.json").read_text()); state["revision"] += 1; state["evidence_integrity"]["state_revision"] += 1
        _write(packet / "state.json", state)
    else:
        (next((packet / "artifacts").rglob("output.log"))).write_text("tampered\n", encoding="utf-8")
    with pytest.raises(HandoffError, match="stale|invalid packet"):
        validate(packet)


def test_separate_process_resume_validates_then_phase_gates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, packet = _packet(tmp_path, monkeypatch); generate(packet)
    state_dir = root / ".memory/state"; state_dir.mkdir(parents=True)
    pointer = activate(packet, state_dir)
    assert set(json.loads((state_dir / "active-task.json").read_text())) == {"task_id", "handoff_path", "state_revision"}
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3])}
    child = subprocess.run([sys.executable, "-m", "tools.handoff", "resume", "--state-dir", str(state_dir), "--repo-root", str(root)], text=True, capture_output=True, env=env, check=False)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["resume"]["task_id"] == pointer["task_id"]
    assert resume(state_dir, root)["resume"]["next_action"] == "run the phase gate"
