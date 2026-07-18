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
from tools.handoff.handoff import (
    HandoffError,
    activate,
    fresh_session,
    generate,
    require_resume_attestation,
    resume,
    validate,
)
from tools.memory_regen.inject import TASK_HEADER, assemble
from tools.risk_router.router import decide, load_policy
from tools.task_control.manager import attest, create, transition


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=True
    ).stdout.strip()


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stop_condition: str | None = "stop after the phase gate before writing",
) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True
    )
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    (root / "constraints.md").write_text("no secret output\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "constraints.md"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    head = _git(root, "rev-parse", "HEAD")
    packet = root / ".workflow/tasks/T-20260719000000-handoff"
    policy = load_policy()
    decision = decide(
        policy,
        {
            "scores": {
                key: 0
                for key in (
                    "ambiguity",
                    "change_scope",
                    "data_security",
                    "reversibility",
                    "impact",
                    "coordination",
                    "context_pressure",
                )
            },
            "human_override": {"lane": "STANDARD", "reason": "fixture"},
        },
    )
    decision.pop("scores")
    task = {
        "task_id": "T-20260719000000-handoff",
        "goal": "resume exactly",
        "non_goals": ["do not summarize a transcript"],
        "risk_inputs": {
            key: 0
            for key in (
                "ambiguity",
                "change_scope",
                "data_security",
                "reversibility",
                "impact",
                "coordination",
                "context_pressure",
            )
        },
        "lane": "STANDARD",
        "risk_decision": decision,
        "acceptance_criteria": [{"id": "AC-01", "description": "resume"}],
        "constraints": [
            {
                "id": "C-01",
                "description": "keep boundary",
                "source_path": "constraints.md",
                "source_sha256": hashlib.sha256((root / "constraints.md").read_bytes()).hexdigest(),
            }
        ],
        "decision_refs": [],
    }
    if stop_condition is not None:
        task["stop_condition"] = stop_condition
    evidence = {
        "task_id": task["task_id"],
        "gate_runs": [],
        "findings": [],
        "redaction_report": {"status": "CLEAR", "refused_fields": []},
    }
    state = {
        "task_id": task["task_id"],
        "phase": "INTAKE",
        "revision": 0,
        "baseline": {"repo_root": ".", "commit": head},
        "current_ref": head,
        "completed_items": [],
        "next_action": "run the phase gate",
        "blockers": [],
        "transition": None,
    }
    _write(packet / "task.json", task)
    _write(packet / "evidence.json", evidence)
    create(packet, state)
    attest(
        packet,
        {
            "constraints": [
                {
                    "constraint_id": "C-01",
                    "source_path": "wrong",
                    "source_sha256": "0" * 64,
                    "applies_to_phases": ["INTAKE"],
                    "prohibited_action_ids": [],
                    "required_evidence_ids": [],
                    "planned_action_mapping": ["A-01"],
                }
            ]
        },
    )
    monkeypatch.setattr(
        capture_module,
        "subprocess",
        types.SimpleNamespace(
            run=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "PASS\n", "")
        ),
    )
    capture(packet, "tests", ["uv", "run", "pytest"], criterion_ids=["AC-01"])
    return root, packet


def _publish(root: Path, packet: Path) -> None:
    """Create the checkpoint publication commit trusted by fresh-session validation."""
    subprocess.run(["git", "-C", str(root), "add", ".workflow"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "checkpoint publication"], check=True)


def test_schema_hashes_and_fresh_session_reconstruction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    handoff = generate(packet)
    _publish(root, packet)
    assert validate(packet) == handoff
    handoff_path = packet / "handoffs/revision-0000000001.json"
    assert fresh_session(handoff_path) == {
        "task_id": handoff["task_id"],
        "goal": handoff["goal"],
        "non_goals": handoff["non_goals"],
        "critical_constraint_ids": handoff["critical_constraint_ids"],
        "phase": handoff["phase"],
        "current_ref": handoff["current_ref"],
        "next_action": handoff["next_action"],
        "stop_condition": handoff["stop_condition"],
    }
    assert handoff["state_ref"]["path"].startswith(".workflow/tasks/")
    assert handoff["artifact_refs"][0]["path"].endswith("output.log")


def test_stop_condition_is_exact_when_present_and_honestly_absent_when_omitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root_a, packet_a = _packet(tmp_path / "a", monkeypatch, "stop at the first failed gate")
    root_b, packet_b = _packet(tmp_path / "b", monkeypatch, "stop only after human approval")
    root_c, packet_c = _packet(tmp_path / "c", monkeypatch, None)
    handoff_a, handoff_b, handoff_c = generate(packet_a), generate(packet_b), generate(packet_c)
    _publish(root_a, packet_a)
    _publish(root_b, packet_b)
    _publish(root_c, packet_c)
    assert handoff_a["stop_condition"] != handoff_b["stop_condition"]
    assert handoff_c["stop_condition"] is None
    assert fresh_session(packet_c / "handoffs/revision-0000000001.json")["stop_condition"] is None


@pytest.mark.parametrize("target", ("revision", "artifact"))
def test_stale_snapshot_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    generate(packet)
    _publish(root, packet)
    if target == "revision":
        state = json.loads((packet / "state.json").read_text())
        state["revision"] += 1
        state["evidence_integrity"]["state_revision"] += 1
        _write(packet / "state.json", state)
    else:
        (next((packet / "artifacts").rglob("output.log"))).write_text(
            "tampered\n", encoding="utf-8"
        )
    with pytest.raises(HandoffError, match="stale|invalid packet"):
        validate(packet)


def test_separate_process_resume_validates_then_phase_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    generate(packet)
    state_dir = root / ".memory/state"
    state_dir.mkdir(parents=True)
    pointer = activate(packet, state_dir)
    subprocess.run(
        ["git", "-C", str(root), "add", ".workflow", ".memory/state/active-task.json"], check=True
    )
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "checkpoint publication"], check=True)
    assert set(json.loads((state_dir / "active-task.json").read_text())) == {
        "task_id",
        "handoff_path",
        "state_revision",
    }
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3])}
    child = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.handoff",
            "resume",
            "--state-dir",
            str(state_dir),
            "--repo-root",
            str(root),
        ],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["resume"]["task_id"] == pointer["task_id"]
    assert resume(state_dir, root)["resume"]["next_action"] == "run the phase gate"


def test_resume_attestation_blocks_absent_and_stale_then_allows_a_real_process_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    # STANDARD->EXECUTE needs exactly these predecessor artifacts.  The fixture's existing
    # captured test evidence remains the handoff evidence; these are structural prerequisites.
    (packet / "artifacts/brief_spec/run-1").mkdir(parents=True)
    (packet / "artifacts/brief_spec/run-1/brief.md").write_text("brief\n", encoding="utf-8")
    attestation_draft = {
        "constraints": [
            {
                "constraint_id": "C-01",
                "source_path": "wrong",
                "source_sha256": "0" * 64,
                "applies_to_phases": ["EXECUTE"],
                "prohibited_action_ids": [],
                "required_evidence_ids": [],
                "planned_action_mapping": ["A-01"],
            }
        ]
    }
    attest(packet, attestation_draft)
    subprocess.run(["git", "-C", str(root), "add", ".workflow"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "execution prerequisites"], check=True)
    transition(packet, "EXECUTE", 1, current_ref=_git(root, "rev-parse", "HEAD"))
    generate(packet)
    state_dir = root / ".memory/state"
    state_dir.mkdir(parents=True)
    activate(packet, state_dir)
    subprocess.run(
        ["git", "-C", str(root), "add", ".workflow", ".memory/state/active-task.json"], check=True
    )
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "checkpoint publication"], check=True)

    with pytest.raises(HandoffError, match="unreadable"):
        require_resume_attestation(state_dir, root)

    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3])}
    hook_event = json.dumps(
        {"tool_name": "Write", "cwd": str(root), "tool_input": {"file_path": str(root / "work.py")}}
    )
    absent = subprocess.run(
        [sys.executable, "-m", "tools.hooks.resume_gate"],
        input=hook_event,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert json.loads(absent.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    prefixed = subprocess.run(
        [sys.executable, "-m", "tools.hooks.resume_gate"],
        input=json.dumps(
            {"tool_name": "Bash", "cwd": str(root), "tool_input": {"command": "command git commit -m x"}}
        ),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert json.loads(prefixed.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    resumed = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.handoff",
            "resume",
            "--state-dir",
            str(state_dir),
            "--repo-root",
            str(root),
        ],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert resumed.returncode == 0, resumed.stderr
    require_resume_attestation(state_dir, root)
    allowed = subprocess.run(
        [sys.executable, "-m", "tools.hooks.resume_gate"],
        input=hook_event,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert allowed.returncode == 0 and not allowed.stdout

    state = json.loads((packet / "state.json").read_text(encoding="utf-8"))
    state["revision"] += 1
    state["evidence_integrity"]["state_revision"] += 1
    _write(packet / "state.json", state)
    denied = subprocess.run(
        [sys.executable, "-m", "tools.hooks.resume_gate"],
        input=hook_event,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert denied.returncode == 0
    assert json.loads(denied.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_resume_transition_then_gated_checkpoint_commit_keeps_lifecycle_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The actual PreToolUse gate must permit a resumed sanctioned transition through commit."""
    root, packet = _packet(tmp_path, monkeypatch)
    (packet / "artifacts/brief_spec/run-1").mkdir(parents=True)
    (packet / "artifacts/brief_spec/run-1/brief.md").write_text("brief\n", encoding="utf-8")
    attestation = json.loads((packet / "context-attestation.json").read_text(encoding="utf-8"))
    attestation["constraints"][0]["applies_to_phases"] = ["EXECUTE"]
    attest(packet, attestation)
    subprocess.run(["git", "-C", str(root), "add", ".workflow"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "execution prerequisites"], check=True)
    transition(packet, "EXECUTE", 1, current_ref=_git(root, "rev-parse", "HEAD"))
    generate(packet)
    state_dir = root / ".memory/state"
    state_dir.mkdir(parents=True)
    activate(packet, state_dir)
    subprocess.run(
        ["git", "-C", str(root), "add", ".workflow", ".memory/state/active-task.json"], check=True
    )
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "checkpoint publication"], check=True)
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3])}

    def gated(command: str, tool_name: str = "Bash") -> None:
        event = json.dumps({"tool_name": tool_name, "cwd": str(root), "tool_input": {"command": command}})
        result = subprocess.run(
            [sys.executable, "-m", "tools.hooks.resume_gate"], input=event, text=True,
            capture_output=True, env=env, check=False,
        )
        assert result.returncode == 0 and not result.stdout, result.stdout

    denied = subprocess.run(
        [sys.executable, "-m", "tools.hooks.resume_gate"],
        input=json.dumps({"tool_name": "Write", "cwd": str(root), "tool_input": {}}),
        text=True, capture_output=True, env=env, check=False,
    )
    assert json.loads(denied.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert resume(state_dir, root)["resume"]["task_id"] == "T-20260719000000-handoff"

    # This CAS bump used to stale the sole attestation and deadlock the next mutation.
    transition(packet, "REVIEW", 2)
    gated("git add work.py")
    (root / "work.py").write_text("after transition\n", encoding="utf-8")
    gated("git add work.py .workflow/tasks/T-20260719000000-handoff/state.json")
    subprocess.run(
        ["git", "-C", str(root), "add", "work.py", ".workflow/tasks/T-20260719000000-handoff/state.json"],
        check=True,
    )
    gated('git commit -m "checkpoint after transition"')
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "checkpoint after transition"], check=True)


def test_pii_refusal_covers_required_read_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, packet = _packet(tmp_path, monkeypatch)
    task = json.loads((packet / "task.json").read_text(encoding="utf-8"))
    task["constraints"][0]["source_path"] = "alice@example.com.txt"
    _write(packet / "task.json", task)
    with pytest.raises(HandoffError, match="PII in handoff content"):
        generate(packet)
    assert not (packet / "handoffs").exists()


@pytest.mark.parametrize(
    "field",
    (
        "next_action",
        "state_ref",
        "evidence_ref",
        "critical_constraint_refs",
        "decisions",
        "artifact_refs",
    ),
)
def test_fresh_session_rejects_each_committed_handoff_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    generate(packet)
    _publish(root, packet)
    source = packet / "handoffs/revision-0000000001.json"
    forged = json.loads(source.read_text(encoding="utf-8"))
    if field == "next_action":
        forged[field] = "ATTACKER ACTION"
    elif field in {"state_ref", "evidence_ref"}:
        forged[field]["sha256"] = "0" * 64
    elif field == "critical_constraint_refs":
        forged[field][0]["sha256"] = "0" * 64
    elif field == "decisions":
        forged[field] = [{"path": "constraints.md", "sha256": "0" * 64}]
    else:
        forged[field][0]["sha256"] = "0" * 64
    _write(source, forged)
    with pytest.raises(HandoffError, match="trust root|stale"):
        fresh_session(source)


def test_same_revision_state_and_handoff_forgery_is_rejected_by_head_trust_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    generate(packet)
    _publish(root, packet)
    state = json.loads((packet / "state.json").read_text(encoding="utf-8"))
    state["next_action"] = "ATTACKER ACTION"
    _write(packet / "state.json", state)
    handoff_path = packet / "handoffs/revision-0000000001.json"
    forged = json.loads(handoff_path.read_text(encoding="utf-8"))
    forged["next_action"] = "ATTACKER ACTION"
    forged["state_ref"]["sha256"] = hashlib.sha256((packet / "state.json").read_bytes()).hexdigest()
    _write(handoff_path, forged)
    with pytest.raises(HandoffError, match="trust root|stale"):
        validate(packet)


def test_pii_refusal_leaves_no_handoff_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, packet = _packet(tmp_path, monkeypatch)
    task = json.loads((packet / "task.json").read_text(encoding="utf-8"))
    task["goal"] = "contact alice@example.com"
    _write(packet / "task.json", task)
    with pytest.raises(HandoffError, match="PII in handoff content"):
        generate(packet)
    assert not (packet / "handoffs").exists()


def test_real_generate_activate_assemble_injects_reserved_task_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, packet = _packet(tmp_path, monkeypatch)
    generate(packet)
    state_dir = root / ".memory/state"
    state_dir.mkdir(parents=True)
    activate(packet, state_dir)
    subprocess.run(
        ["git", "-C", str(root), "add", ".workflow", ".memory/state/active-task.json"], check=True
    )
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "checkpoint publication"], check=True)
    derived = root / ".memory/derived"
    derived.mkdir(parents=True)
    (derived / "contracts-index.md").write_text("contract\n" * 20, encoding="utf-8")
    (derived / "repo-map.md").write_text("repo\n" * 20, encoding="utf-8")
    payload = assemble(
        derived_dir=derived, state_dir=state_dir, agreements_dir=root / ".memory/agreements"
    )
    assert "ACTIVE HANDOFF INVALID" not in payload, payload
    assert TASK_HEADER in payload and "run the phase gate" in payload
