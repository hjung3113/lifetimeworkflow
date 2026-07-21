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

import tools.discipline.check as check_module
import tools.evidence.capture as capture_module
from tools.capability.registry import providers_for
from tools.discipline.__main__ import main as discipline_main
from tools.discipline.check import load_declarations, record_path, required_disciplines
from tools.evidence.capture import add_finding, capture
from tools.risk_router.intake import create_packet
from tools.risk_router.router import decide, load_policy
from tools.task_control.manager import (
    TaskControlError,
    attest,
    block,
    create,
    orphan_artifacts,
    refresh_ref,
    show,
    transition,
    validate,
)
from tools.task_control.phase_gate import phase_gate
from tools.task_packet.transitions import ALLOWED_TRANSITIONS, PHASES, required_artifacts_for_phase


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture(autouse=True)
def canonical_gate_child(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep lifecycle fixtures fast while still exercising capture publication."""
    monkeypatch.setattr(
        capture_module,
        "subprocess",
        types.SimpleNamespace(
            run=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "PASS\n", ""),
        ),
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, text=True, capture_output=True
    ).stdout.strip()


def make_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True
    )
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
    return {
        "constraints": [
            {
                "constraint_id": "C-01",
                "source_path": "wrong",
                "source_sha256": "0" * 64,
                "applies_to_phases": sorted(PHASES),
                "prohibited_action_ids": ["write-contract"],
                "required_evidence_ids": ["E-01"],
                "planned_action_mapping": ["A-01"],
            }
        ]
    }


def make_task(tmp_path: Path, lane: str = "STANDARD") -> tuple[Path, Path]:
    root, commit = make_repo(tmp_path)
    task_dir = root / ".workflow/tasks/T-20260718000000-fixture"
    source = root / "constraints.md"
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
            "human_override": {"lane": lane, "reason": "fixture"},
        },
    )
    decision.pop("scores")
    task = {
        "task_id": "T-20260718000000-fixture",
        "goal": "fixture",
        "non_goals": [],
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
        "lane": lane,
        "risk_decision": decision,
        "acceptance_criteria": [{"id": "AC-01", "description": "works"}],
        "constraints": [
            {
                "id": "C-01",
                "description": "keep gate",
                "source_path": "constraints.md",
                "source_sha256": digest(source),
            }
        ],
        "decision_refs": [],
        "stop_condition": "stop after fixture gate",
    }
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
        "baseline": {"repo_root": ".", "commit": commit},
        "current_ref": commit,
        "completed_items": [],
        "next_action": "start",
        "blockers": [],
        "transition": None,
    }
    dump(task_dir / "task.json", task)
    dump(task_dir / "evidence.json", evidence)
    create(task_dir, state)
    attest(task_dir, attestation_draft())
    return root, task_dir


def cover_constraints(
    task_dir: Path, artifact: Path | None = None, *, artifacts: list[Path] | None = None
) -> None:
    # A real child capture replaces the former hand-written PASSED record.
    if json.loads((task_dir / "evidence.json").read_text())["findings"]:
        return
    record = capture(
        task_dir, "tests", ["uv", "run", "pytest"], criterion_ids=["AC-01"], finding_ids=["F-01"]
    )
    add_finding(
        task_dir,
        {
            "id": "F-01",
            "summary": "covered",
            "constraint_ids": ["C-01"],
            "severity": "minor",
            "disposition": "resolved",
            "evidence_ref": record["id"],
        },
    )


def satisfy_target(task_dir: Path, lane: str, target: str) -> None:
    # Artifacts AND disciplines: both are lane requirements for entering `target`.  Tests that
    # exercise the discipline refusal itself call `satisfy_artifacts` directly instead.
    satisfy_disciplines(task_dir, lane, target)
    satisfy_artifacts(task_dir, lane, target)


def satisfy_artifacts(task_dir: Path, lane: str, target: str) -> None:
    for name in required_artifacts_for_phase(lane, target):
        if name != "task_packet":
            add_artifact(task_dir, name)
    if target in {"VERIFY", "COMPLETE"}:
        cover_constraints(task_dir)
    if target == "COMPLETE":
        root = next(parent for parent in task_dir.parents if (parent / ".git").exists())
        subprocess.run(
            ["git", "-C", str(root), "add", task_dir.relative_to(root) / "evidence.json"],
            check=True,
        )
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "evidence"], check=True)
        refresh_ref(task_dir, show(task_dir)["revision"], git(root, "rev-parse", "HEAD"))


@pytest.mark.parametrize("lane", sorted(ALLOWED_TRANSITIONS))
def test_every_transition_edge_succeeds_and_every_non_edge_fails(tmp_path: Path, lane: str) -> None:
    for index, (source, target) in enumerate(sorted(ALLOWED_TRANSITIONS[lane])):
        root, task_dir = make_task(tmp_path / f"{lane}-edge-{index}", lane)
        state = show(task_dir)
        state.update(
            {"phase": source, "revision": 1, "transition": {"from": "INTAKE", "to": source}}
        )
        dump(task_dir / "state.json", state)
        satisfy_target(task_dir, lane, target)
        if target == "BLOCKED":
            assert (
                block(
                    task_dir,
                    show(task_dir)["revision"],
                    {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]},
                )["phase"]
                == target
            )
        else:
            assert transition(task_dir, target, show(task_dir)["revision"])["phase"] == target
    for index, (source, target) in enumerate(
        sorted(
            pair
            for source in PHASES
            for target in PHASES
            if (pair := (source, target)) not in ALLOWED_TRANSITIONS[lane]
        )
    ):
        root, task_dir = make_task(tmp_path / f"{lane}-nonedge-{index}", lane)
        state = show(task_dir)
        state.update(
            {"phase": source, "revision": 1, "transition": {"from": "INTAKE", "to": source}}
        )
        dump(task_dir / "state.json", state)
        before = (task_dir / "state.json").read_bytes()
        with pytest.raises(TaskControlError):
            if target == "BLOCKED":
                block(task_dir, 1, {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})
            else:
                transition(task_dir, target, 1)
        assert (task_dir / "state.json").read_bytes() == before


def test_phase_oriented_artifacts_allow_strict_and_controlled_lifecycle(tmp_path: Path) -> None:
    for lane in ("STRICT", "CONTROLLED"):
        root, task_dir = make_task(tmp_path / lane, lane)
        revision = 0
        phase_gate(task_dir, revision, repo_root=root)
        for target in ("CLARIFY", "SPEC", "PLAN", "EXECUTE", "REVIEW", "VERIFY", "COMPLETE"):
            satisfy_target(task_dir, lane, target)
            if target in {"VERIFY", "COMPLETE"}:
                cover_constraints(
                    task_dir, artifacts=sorted((task_dir / "artifacts").rglob("result.txt"))
                )
            revision = show(task_dir)["revision"]
            # The documented gate runs before every transition, not only after lifecycle completion.
            phase_gate(task_dir, revision, repo_root=root)
            state = transition(task_dir, target, revision)
            revision = state["revision"]
            phase_gate(task_dir, revision, repo_root=root)
        assert state["phase"] == "COMPLETE"


def test_policy_tampering_and_invalid_evidence_are_rejected(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "CONTROLLED")
    task = json.loads((task_dir / "task.json").read_text())
    task["risk_decision"]["required_artifacts"] = ["task_packet"]
    dump(task_dir / "task.json", task)
    with pytest.raises(TaskControlError, match="weaken"):
        transition(task_dir, "CLARIFY", 0)
    root, task_dir = make_task(tmp_path / "hash", "CONTROLLED")
    task = json.loads((task_dir / "task.json").read_text())
    task["risk_decision"]["policy_hashes"]["effective"] = "0" * 64
    dump(task_dir / "task.json", task)
    with pytest.raises(TaskControlError, match="policy hash"):
        transition(task_dir, "CLARIFY", 0)
    root, task_dir = make_task(tmp_path / "evidence", "FAST")
    state = show(task_dir)
    state.update(
        {"phase": "EXECUTE", "revision": 1, "transition": {"from": "INTAKE", "to": "EXECUTE"}}
    )
    dump(task_dir / "state.json", state)
    dump(
        task_dir / "evidence.json",
        {
            "task_id": show(task_dir)["task_id"],
            "gate_runs": [{"constraint_ids": ["C-01"]}],
            "findings": [],
        },
    )
    with pytest.raises(TaskControlError, match="evidence.json"):
        transition(task_dir, "VERIFY", 1)


def test_block_obeys_matrix_and_legal_state_succeeds(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    state = show(task_dir)
    state.update(
        {"phase": "COMPLETE", "revision": 1, "transition": {"from": "VERIFY", "to": "COMPLETE"}}
    )
    dump(task_dir / "state.json", state)
    with pytest.raises(TaskControlError, match="illegal transition"):
        block(task_dir, 1, {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})
    root, task_dir = make_task(tmp_path / "legal")
    assert (
        block(task_dir, 0, {"id": "B-01", "summary": "wait", "constraint_ids": ["C-01"]})["phase"]
        == "BLOCKED"
    )


def test_crash_after_fsync_leaves_valid_canonical_and_next_mutation_succeeds(
    tmp_path: Path,
) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    command = [
        sys.executable,
        "-m",
        "tools.task_control",
        "transition",
        str(task_dir),
        "EXECUTE",
        "--expected-revision",
        "0",
    ]
    crashed = subprocess.run(command, env={**os.environ, "TASK_CONTROL_FAULT_AFTER_FSYNC": "1"})
    assert crashed.returncode == 86
    assert show(task_dir)["revision"] == 0
    assert transition(task_dir, "EXECUTE", 0)["revision"] == 1
    assert any(name.endswith((".tmp", ".cas")) for name in validate(task_dir)["write_residues"])


def test_two_process_writers_with_one_revision_have_exactly_one_winner(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    command = [
        sys.executable,
        "-m",
        "tools.task_control",
        "transition",
        str(task_dir),
        "EXECUTE",
        "--expected-revision",
        "0",
    ]
    barrier = threading.Barrier(3)
    outcomes: list[int] = []

    def run() -> None:
        barrier.wait()
        outcomes.append(subprocess.run(command, capture_output=True).returncode)

    threads = [threading.Thread(target=run) for _ in range(2)]
    [thread.start() for thread in threads]
    barrier.wait()
    [thread.join() for thread in threads]
    assert outcomes.count(0) == 1
    assert show(task_dir)["revision"] == 1


def test_two_process_creates_have_exactly_one_winner(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    state = show(task_dir)
    (task_dir / "state.json").unlink()
    state_file = tmp_path / "initial-state.json"
    dump(state_file, state)
    command = [
        sys.executable,
        "-m",
        "tools.task_control",
        "create",
        str(task_dir),
        "--state",
        str(state_file),
    ]
    barrier = threading.Barrier(3)
    outcomes: list[int] = []

    def run() -> None:
        barrier.wait()
        outcomes.append(subprocess.run(command, capture_output=True).returncode)

    threads = [threading.Thread(target=run) for _ in range(2)]
    [thread.start() for thread in threads]
    barrier.wait()
    [thread.join() for thread in threads]
    assert outcomes.count(0) == 1
    assert show(task_dir)["revision"] == 0


def test_attest_refresh_ref_and_phase_gate(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "STANDARD")
    artifact = add_artifact(task_dir, "brief_spec")
    cover_constraints(task_dir, artifact)
    satisfy_disciplines(task_dir, "STANDARD", "EXECUTE")
    state = transition(task_dir, "EXECUTE", show(task_dir)["revision"])
    phase_gate(task_dir, state["revision"], repo_root=root)
    (root / "change.txt").write_text("change\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "change"], check=True)
    with pytest.raises(TaskControlError, match="current ref"):
        phase_gate(task_dir, state["revision"], repo_root=root)
    refreshed = refresh_ref(task_dir, state["revision"], git(root, "rev-parse", "HEAD"))
    phase_gate(task_dir, refreshed["revision"], repo_root=root)


def test_orphans_are_diagnostic_before_verify_and_block_verify(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path)
    artifact = add_artifact(task_dir, "brief_spec")
    cover_constraints(task_dir, artifact)
    orphan = task_dir / "artifacts" / "tests" / "unreferenced" / "output.log"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("orphan\n", encoding="utf-8")
    assert orphan_artifacts(task_dir)
    assert phase_gate(task_dir, show(task_dir)["revision"], repo_root=root) == [
        f"orphan artifact: {orphan.relative_to(task_dir).as_posix()}"
    ]
    state = show(task_dir)
    state.update(
        {"phase": "VERIFY", "revision": 1, "transition": {"from": "EXECUTE", "to": "VERIFY"}}
    )
    dump(task_dir / "state.json", state)
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
                cover_constraints(
                    task_dir, artifacts=sorted((task_dir / "artifacts").rglob("result.txt"))
                )
            revision = show(task_dir)["revision"]
            state = transition(task_dir, target, revision)
            revision = state["revision"]
            phase_gate(task_dir, revision, repo_root=root)


def test_overlay_packet_transitions_and_tampering_is_rejected(tmp_path: Path) -> None:
    root, commit = make_repo(tmp_path)
    task_dir = root / ".workflow/tasks/T-20260718000000-overlay"
    overlay = tmp_path / "overlay.toml"
    overlay.write_text('[lanes.FAST]\nrequired_gates_add = ["local_audit"]\n', encoding="utf-8")
    request = {
        "task": {
            "task_id": "T-20260718000000-overlay",
            "goal": "overlay",
            "non_goals": [],
            "acceptance_criteria": [{"id": "AC-01", "description": "works"}],
            "constraints": [],
            "decision_refs": [],
            "stop_condition": "stop after overlay",
        },
        "routing": {
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
            }
        },
        "baseline": {"commit": commit},
    }
    create_packet(request, task_dir, overlay_path=overlay)
    assert (task_dir / "risk-overlay.toml").read_bytes() == overlay.read_bytes()
    assert transition(task_dir, "EXECUTE", 0)["phase"] == "EXECUTE"
    task = json.loads((task_dir / "task.json").read_text())
    task["risk_decision"]["policy_hashes"]["effective"] = "0" * 64
    dump(task_dir / "task.json", task)
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
    (root / "contracts").mkdir()
    (root / "contracts" / "changed.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "constitution"], check=True)
    state = refresh_ref(task_dir, state["revision"], git(root, "rev-parse", "HEAD"))
    with pytest.raises(TaskControlError, match="approval"):
        transition(task_dir, "COMPLETE", state["revision"])
    (root / "approvals").mkdir()
    (root / "approvals" / "fixture.json").write_text(
        json.dumps({"approved_paths": ["contracts/changed.json"]}), encoding="utf-8"
    )
    capture(task_dir, "tests", ["uv", "run", "pytest"], human_approval_ref="approvals/fixture.json")
    with pytest.raises(TaskControlError, match="committed at HEAD"):
        transition(task_dir, "COMPLETE", show(task_dir)["revision"])
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "add",
            "approvals/fixture.json",
            task_dir.relative_to(root) / "evidence.json",
        ],
        check=True,
    )
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "approval-and-evidence"], check=True)
    assert transition(task_dir, "COMPLETE", show(task_dir)["revision"])["phase"] == "COMPLETE"


def test_complete_rejects_working_tree_rewrite_of_committed_approval(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "FAST")
    transition(task_dir, "EXECUTE", 0)
    add_artifact(task_dir, "brief_spec")
    cover_constraints(task_dir)
    state = transition(task_dir, "VERIFY", show(task_dir)["revision"])
    (root / "contracts").mkdir()
    (root / "contracts" / "changed.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "constitution"], check=True)
    refresh_ref(task_dir, state["revision"], git(root, "rev-parse", "HEAD"))
    (root / "approvals").mkdir()
    approval = root / "approvals" / "fixture.json"
    approval.write_text(
        json.dumps({"approved_paths": ["contracts/previous.json"]}), encoding="utf-8"
    )
    capture(task_dir, "tests", ["uv", "run", "pytest"], human_approval_ref="approvals/fixture.json")
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "add",
            "approvals/fixture.json",
            task_dir.relative_to(root) / "evidence.json",
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "wrong-approval-and-evidence"], check=True
    )
    approval.write_text(
        json.dumps({"approved_paths": ["contracts/changed.json"]}), encoding="utf-8"
    )
    with pytest.raises(TaskControlError, match="approval"):
        transition(task_dir, "COMPLETE", show(task_dir)["revision"])


# ── LANE-01 / LANE-02: a lane's declared discipline is refusable ──────────────────────────────


def write_discipline_record(task_dir: Path, identifier: str, **overrides: object) -> Path:
    """Write a well-formed record for *identifier*, then apply the overrides under test."""
    declaration = load_declarations()[identifier]
    body: dict = {
        "discipline": identifier,
        "skill": declaration.skill,
        "task_id": json.loads((task_dir / "task.json").read_text())["task_id"],
        "satisfied_at_phase": declaration.owed_by_phase,
        "outputs": ["constraints.md"],
    }
    # LANE-03: resolve the agent from the DECLARED CAPABILITY's allowlist, so this helper stays
    # capability-neutral — no persona name is hardcoded here either.
    provider = (
        providers_for(declaration.capability)[0] if declaration.capability is not None else None
    )
    if provider is not None:
        body["agent"] = provider
    if declaration.min_experts is not None:
        body["panel"] = {
            "reviews": [
                {
                    "expert": name,
                    "verdict": "pass",
                    "finding_ids": [],
                    **({"agent": provider} if provider is not None else {}),
                }
                for name in ("contract", "security", "rollback")[: declaration.min_experts]
            ]
        }
    body.update(overrides)
    path = record_path(task_dir, identifier)
    dump(path, body)
    return path


def satisfy_disciplines(task_dir: Path, lane: str, target: str) -> None:
    for identifier in required_disciplines(lane, target):
        write_discipline_record(task_dir, identifier)


def test_strict_execute_is_refused_without_the_clarify_record(tmp_path: Path) -> None:
    """LANE-01: the declared discipline is a refusal, not advice."""
    _, task_dir = make_task(tmp_path, "STRICT")
    for target in ("CLARIFY", "SPEC", "PLAN"):
        transition(task_dir, target, show(task_dir)["revision"])
    satisfy_artifacts(task_dir, "STRICT", "EXECUTE")
    before = show(task_dir)
    with pytest.raises(TaskControlError, match="missing required disciplines: clarify"):
        transition(task_dir, "EXECUTE", before["revision"])
    after = show(task_dir)
    assert (after["phase"], after["revision"]) == (before["phase"], before["revision"])
    write_discipline_record(task_dir, "clarify")
    assert transition(task_dir, "EXECUTE", before["revision"])["phase"] == "EXECUTE"


def test_strict_verify_is_refused_without_the_review_panel(tmp_path: Path) -> None:
    """LANE-02: the STRICT+ adversarial panel is a DECLARED lane requirement."""
    _, task_dir = make_task(tmp_path, "STRICT")
    for target in ("CLARIFY", "SPEC", "PLAN"):
        transition(task_dir, target, show(task_dir)["revision"])
    satisfy_target(task_dir, "STRICT", "EXECUTE")
    transition(task_dir, "EXECUTE", show(task_dir)["revision"])
    satisfy_target(task_dir, "STRICT", "REVIEW")
    transition(task_dir, "REVIEW", show(task_dir)["revision"])
    satisfy_artifacts(task_dir, "STRICT", "VERIFY")
    with pytest.raises(TaskControlError, match="adversarial-review-panel"):
        transition(task_dir, "VERIFY", show(task_dir)["revision"])
    write_discipline_record(task_dir, "adversarial-review-panel")
    assert transition(task_dir, "VERIFY", show(task_dir)["revision"])["phase"] == "VERIFY"


def test_three_identical_seats_do_not_satisfy_the_panel(tmp_path: Path) -> None:
    """One opinion typed three times is not multi-expert review."""
    _, task_dir = make_task(tmp_path, "STRICT")
    for target in ("CLARIFY", "SPEC", "PLAN"):
        transition(task_dir, target, show(task_dir)["revision"])
    satisfy_target(task_dir, "STRICT", "EXECUTE")
    transition(task_dir, "EXECUTE", show(task_dir)["revision"])
    satisfy_target(task_dir, "STRICT", "REVIEW")
    transition(task_dir, "REVIEW", show(task_dir)["revision"])
    satisfy_artifacts(task_dir, "STRICT", "VERIFY")
    write_discipline_record(
        task_dir,
        "adversarial-review-panel",
        panel={
            "reviews": [
                {"expert": "security", "verdict": "pass", "finding_ids": []} for _ in range(3)
            ]
        },
    )
    with pytest.raises(TaskControlError, match="distinct expert seat"):
        transition(task_dir, "VERIFY", show(task_dir)["revision"])


def test_verify_is_refused_when_a_panel_seat_routes_outside_the_allowlist(tmp_path: Path) -> None:
    """LANE-03 THE DEMONSTRATION: an out-of-allowlist route REFUSES the transition.

    The seat is otherwise perfect — distinct expert, declared verdict, real outputs. The only defect
    is that the agent filling it is not on the `adversarial-review` allowlist, and that alone stops
    the task leaving REVIEW. Swapping in an allowlisted provider lets the same transition through,
    so the refusal is caused by the route and by nothing else.
    """
    _, task_dir = make_task(tmp_path, "STRICT")
    for target in ("CLARIFY", "SPEC", "PLAN"):
        transition(task_dir, target, show(task_dir)["revision"])
    satisfy_target(task_dir, "STRICT", "EXECUTE")
    transition(task_dir, "EXECUTE", show(task_dir)["revision"])
    satisfy_target(task_dir, "STRICT", "REVIEW")
    transition(task_dir, "REVIEW", show(task_dir)["revision"])
    satisfy_artifacts(task_dir, "STRICT", "VERIFY")
    allowed = providers_for("adversarial-review")[0]
    seats = ("contract", "security", "rollback")

    def _panel(agents: tuple[str, ...]) -> dict:
        return {
            "reviews": [
                {"expert": expert, "verdict": "pass", "finding_ids": [], "agent": agent}
                for expert, agent in zip(seats, agents, strict=True)
            ]
        }

    # `python-engineer` is a real, declared persona — just not one allowed to review adversarially.
    write_discipline_record(
        task_dir,
        "adversarial-review-panel",
        panel=_panel((allowed, "python-engineer", allowed)),
    )
    before = show(task_dir)
    with pytest.raises(
        TaskControlError, match="not allowed to serve capability adversarial-review"
    ):
        transition(task_dir, "VERIFY", before["revision"])
    after = show(task_dir)
    assert (after["phase"], after["revision"]) == (before["phase"], before["revision"])

    # POSITIVE CONTROL: only the route changes, and the same transition now succeeds.
    write_discipline_record(
        task_dir, "adversarial-review-panel", panel=_panel((allowed, allowed, allowed))
    )
    assert transition(task_dir, "VERIFY", before["revision"])["phase"] == "VERIFY"


def test_an_unrouted_record_is_refused_like_an_absent_one(tmp_path: Path) -> None:
    """LANE-03: a record that never says who did the work does not discharge the discipline."""
    _, task_dir = make_task(tmp_path, "STANDARD")
    for target in ("CLARIFY", "SPEC", "PLAN"):
        transition(task_dir, target, show(task_dir)["revision"])
    satisfy_artifacts(task_dir, "STANDARD", "EXECUTE")
    path = write_discipline_record(task_dir, "clarify")
    body = json.loads(path.read_text())
    del body["agent"]
    dump(path, body)
    with pytest.raises(TaskControlError, match="requires a named agent, none given"):
        transition(task_dir, "EXECUTE", show(task_dir)["revision"])


def test_fast_owes_no_discipline_and_is_unaffected(tmp_path: Path) -> None:
    _, task_dir = make_task(tmp_path, "FAST")
    assert transition(task_dir, "EXECUTE", 0)["phase"] == "EXECUTE"


def test_phase_gate_refuses_a_resumed_task_missing_its_discipline(tmp_path: Path) -> None:
    root, task_dir = make_task(tmp_path, "STRICT")
    for target in ("CLARIFY", "SPEC", "PLAN"):
        transition(task_dir, target, show(task_dir)["revision"])
    satisfy_artifacts(task_dir, "STRICT", "EXECUTE")
    write_discipline_record(task_dir, "clarify")
    state = transition(task_dir, "EXECUTE", show(task_dir)["revision"])
    record_path(task_dir, "clarify").unlink()
    with pytest.raises(TaskControlError, match="discipline: clarify"):
        phase_gate(task_dir, state["revision"], repo_root=root)
    write_discipline_record(task_dir, "clarify")
    assert phase_gate(task_dir, state["revision"], repo_root=root) == []


def test_the_refusal_is_load_bearing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MUTATION: empty the lane's declared disciplines and the same transition succeeds."""
    _, task_dir = make_task(tmp_path, "STRICT")
    for target in ("CLARIFY", "SPEC", "PLAN"):
        transition(task_dir, target, show(task_dir)["revision"])
    satisfy_artifacts(task_dir, "STRICT", "EXECUTE")
    revision = show(task_dir)["revision"]
    with pytest.raises(TaskControlError, match="missing required disciplines"):
        transition(task_dir, "EXECUTE", revision)
    neutralized = load_policy()
    neutralized["lanes"]["STRICT"]["required_disciplines"] = []
    monkeypatch.setattr(check_module, "load_policy", lambda *args, **kwargs: neutralized)
    assert transition(task_dir, "EXECUTE", revision)["phase"] == "EXECUTE"


def test_discipline_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """0 clean / 1 outstanding / 3 invalid — the tools.docs_guard convention, reused."""
    _, task_dir = make_task(tmp_path, "STRICT")
    assert discipline_main([str(task_dir), "--phase", "INTAKE"]) == 0
    assert discipline_main([str(task_dir), "--phase", "EXECUTE"]) == 1
    assert "MISSING  clarify" in capsys.readouterr().out
    write_discipline_record(task_dir, "clarify")
    assert discipline_main([str(task_dir), "--phase", "EXECUTE"]) == 0
    assert discipline_main([str(task_dir / "nowhere"), "--phase", "EXECUTE"]) == 3
    assert discipline_main([str(task_dir), "--phase", "NOT-A-PHASE"]) == 3
