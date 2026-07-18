from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.contract_drift.drift import run_gate
from tools.contract_hash.hash import build_manifest, write_manifest
from tools.memory_regen import pointer_index, repo_map
from tools.memory_regen.contracts_index import write as write_contracts_index
from tools.task_packet.transitions import ALLOWED_TRANSITIONS, PHASES, is_transition_allowed
from tools.task_packet.validate import (
    REPO_ROOT,
    SCHEMA_DIR,
    PacketValidationError,
    main,
    validate_packet,
)

FIXTURES = Path(__file__).parent / "fixtures"
EXAMPLE = REPO_ROOT / ".workflow" / "tasks" / "T-20260718090000-contract-ratification"
COMMIT = "71456f772b26430a1fdeb02819f9f1822a01f2b7"
SHA256 = "a" * 64


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _base_packet(lane: str = "STRICT", phase: str = "REVIEW", revision: int = 6, transition=None):
    if transition is None and revision != 0:
        transition = {"from": "EXECUTE", "to": phase}
    task_id = "T-20260718090100-schema-fixture"
    task = {
        "task_id": task_id,
        "goal": "Validate the task packet contract.",
        "non_goals": ["Mutate runtime state."],
        "risk_inputs": {
            "ambiguity": 1,
            "change_scope": 1,
            "data_security": 0,
            "reversibility": 1,
            "impact": 1,
            "coordination": 1,
            "context_pressure": 1,
        },
        "lane": lane,
        "risk_decision": {
            "router_version": 1,
            "total": 6,
            "score_lane": "STANDARD",
            "lane": lane,
            "promotion_reasons": [],
            "human_override_audit": None,
            "required_artifacts": ["task_packet"],
            "required_gates": ["lint", "test"],
            "policy_hashes": {"core": SHA256, "overlay": SHA256, "effective": SHA256},
            "overlay_provenance": None,
        },
        "acceptance_criteria": [{"id": "AC-01", "description": "Validation passes."}],
        "constraints": [
            {
                "id": "C-01",
                "description": "Use the contract as authority.",
                "source_path": "contracts/harness/task-control/task.schema.json",
                "source_sha256": SHA256,
            }
        ],
        "decision_refs": [{"path": "docs/adr/ADR-0001-task-control.md", "sha256": SHA256}],
    }
    state = {
        "task_id": task_id,
        "phase": phase,
        "revision": revision,
        "baseline": {"repo_root": ".", "commit": COMMIT},
        "current_ref": COMMIT,
        "completed_items": [],
        "next_action": "Run validation.",
        "blockers": [
            {"id": "B-01", "summary": "Await contract ratification.", "constraint_ids": ["C-01"]}
        ],
        "transition": transition,
    }
    evidence = {
        "task_id": task_id,
        "gate_runs": [
            {
                "id": "E-01",
                "gate": "schema-validation",
                "status": "PASSED",
                "criterion_ids": ["AC-01"],
                "finding_ids": ["F-01"],
                "cwd": "/repository",
                "artifact": {
                    "path": "artifacts/schema-validation.txt",
                    "summary": "Schema validation result.",
                    "sha256": SHA256,
                },
            }
        ],
        "findings": [
            {
                "id": "F-01",
                "summary": "Contract is internally consistent.",
                "constraint_ids": ["C-01"],
                "severity": "minor",
                "disposition": "open",
            }
        ],
    }
    handoff = {
        "task_id": task_id,
        "state_revision": revision,
        "goal": task["goal"],
        "non_goals": task["non_goals"],
        "critical_constraint_ids": ["C-01"],
        "phase": phase,
        "lane": lane,
        "baseline": state["baseline"],
        "current_ref": state["current_ref"],
        "next_action": state["next_action"],
        "evidence_ids": ["E-01"],
        "finding_ids": ["F-01"],
        "critical_constraint_refs": [{"path": "constraints.md", "sha256": SHA256}],
        "decisions": [],
        "changed_paths": [],
        "unresolved_items": [{"id": "F-01", "kind": "finding"}],
        "stop_condition": "Stop if validation fails.",
        "required_read_paths": ["task.json", "state.json", "evidence.json", "constraints.md"],
        "state_ref": {"path": "state.json", "sha256": SHA256},
        "evidence_ref": {"path": "evidence.json", "sha256": SHA256},
        "artifact_refs": [{"evidence_id": "E-01", "path": "artifacts/schema-validation.txt", "sha256": SHA256}],
    }
    return {"task": task, "state": state, "evidence": evidence, "handoff": handoff}


def _write_packet(root: Path, documents: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, document in documents.items():
        (root / f"{name}.json").write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return root


def _set_path(document: dict, path: list, value) -> None:
    target = document
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def _remove_path(document: dict, path: list) -> None:
    target = document
    for part in path[:-1]:
        target = target[part]
    del target[path[-1]]


@pytest.mark.parametrize("case", _read(FIXTURES / "valid" / "cases.json"), ids=lambda c: c["name"])
def test_five_positive_packets_pass_all_four_schemas(tmp_path: Path, case: dict):
    documents = _base_packet(
        lane=case["lane"],
        phase=case["phase"],
        revision=case["revision"],
        transition=case["transition"],
    )
    assert set(validate_packet(_write_packet(tmp_path / case["name"], documents))) == {
        "task",
        "state",
        "evidence",
        "handoff",
    }


@pytest.mark.parametrize(
    ("document", "field"),
    [
        (document, field)
        for document, fields in _read(FIXTURES / "negative" / "missing-required.json")[
            "top_level"
        ].items()
        for field in fields
    ],
)
def test_each_top_level_required_field_is_rejected(tmp_path: Path, document: str, field: str):
    documents = _base_packet()
    del documents[document][field]
    with pytest.raises(PacketValidationError):
        validate_packet(_write_packet(tmp_path / f"{document}-{field}", documents))


@pytest.mark.parametrize(
    ("document", "object_path", "field"),
    [
        (case["document"], case["object_path"], field)
        for case in _read(FIXTURES / "negative" / "missing-required.json")["nested"]
        for field in case["fields"]
    ],
)
def test_each_nested_required_field_is_rejected(
    tmp_path: Path, document: str, object_path: list, field: str
):
    documents = _base_packet()
    _remove_path(documents[document], [*object_path, field])
    with pytest.raises(PacketValidationError):
        validate_packet(_write_packet(tmp_path / f"{document}-{field}", documents))


@pytest.mark.parametrize(
    "case", _read(FIXTURES / "negative" / "cases.json"), ids=lambda c: c["name"]
)
def test_negative_fixtures_are_rejected(tmp_path: Path, case: dict):
    documents = copy.deepcopy(_base_packet())
    if "path" in case:
        _set_path(documents[case["document"]], case["path"], case["value"])
    else:
        _remove_path(documents[case["document"]], case["remove"])
    if case["name"] == "illegal-transition":
        documents["state"]["phase"] = "COMPLETE"
        documents["handoff"]["phase"] = "COMPLETE"
    match = "invalid UTC timestamp" if case["name"] == "invalid-task-timestamp" else None
    with pytest.raises(PacketValidationError, match=match):
        validate_packet(_write_packet(tmp_path / case["name"], documents))


def test_unknown_and_non_edge_transitions_fail_closed():
    assert not is_transition_allowed("UNKNOWN", "INTAKE", "EXECUTE")
    assert not is_transition_allowed("FAST", "UNKNOWN", "EXECUTE")
    assert not is_transition_allowed("FAST", "EXECUTE", "COMPLETE")
    assert is_transition_allowed("FAST", "EXECUTE", "VERIFY")


def test_schema_enums_transition_contract_and_runtime_sets_are_identical():
    task_schema = _read(SCHEMA_DIR / "task.schema.json")
    state_schema = _read(SCHEMA_DIR / "state.schema.json")
    handoff_schema = _read(SCHEMA_DIR / "handoff.schema.json")
    contract = _read(SCHEMA_DIR / "transitions.json")

    phase_sets = (
        set(state_schema["$defs"]["phase"]["enum"]),
        set(handoff_schema["$defs"]["phase"]["enum"]),
        set(contract["phases"]),
        set(PHASES),
    )
    lane_sets = (
        set(task_schema["$defs"]["lane"]["enum"]),
        set(handoff_schema["$defs"]["lane"]["enum"]),
        set(contract["lanes"]),
        set(ALLOWED_TRANSITIONS),
    )
    assert all(value == phase_sets[0] for value in phase_sets[1:])
    assert all(value == lane_sets[0] for value in lane_sets[1:])
    for lane, raw_edges in contract["lanes"].items():
        edges = {tuple(edge) for edge in raw_edges}
        assert edges == ALLOWED_TRANSITIONS[lane]
        assert all(source in PHASES and target in PHASES for source, target in edges)


def test_committed_example_packet_validates():
    validate_packet(EXAMPLE)


def test_memory_state_deletion_does_not_change_packet_validation(tmp_path: Path):
    packet = _write_packet(tmp_path / ".workflow" / "tasks" / "packet", _base_packet())
    memory_state = tmp_path / ".memory" / "state"
    memory_state.mkdir(parents=True)
    (memory_state / "activeContext.md").write_text("active\n", encoding="utf-8")
    before = validate_packet(packet)
    shutil.rmtree(memory_state)
    after = validate_packet(packet)
    assert before == after


def test_task_packet_deletion_does_not_change_derived_regeneration(tmp_path: Path):
    contracts = tmp_path / "contracts"
    shutil.copytree(REPO_ROOT / "contracts", contracts)
    baseline = contracts / ".hashes" / "manifest.json"
    write_manifest(baseline, contracts)
    packet = _write_packet(tmp_path / ".workflow" / "tasks" / "packet", _base_packet())
    source = tmp_path / "tools" / "sample.py"
    source.parent.mkdir(parents=True)
    source.write_text("def sample():\n    return 1\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "note.md").write_text("See .memory/state/progress.md.\n", encoding="utf-8")

    first_index = tmp_path / "first-contracts.md"
    second_index = tmp_path / "second-contracts.md"
    write_contracts_index(first_index, contracts, baseline)
    first_repo_map = repo_map.render(repo_map.build_graph([source.parent], base_dir=tmp_path))
    first_pointers = pointer_index.render_md(
        pointer_index.build_index(base_dir=tmp_path, scan_roots=[docs])
    )
    shutil.rmtree(packet)
    write_contracts_index(second_index, contracts, baseline)
    second_repo_map = repo_map.render(repo_map.build_graph([source.parent], base_dir=tmp_path))
    second_pointers = pointer_index.render_md(
        pointer_index.build_index(base_dir=tmp_path, scan_roots=[docs])
    )
    assert first_index.read_bytes() == second_index.read_bytes()
    assert first_repo_map == second_repo_map
    assert first_pointers == second_pointers


def test_cli_main_returns_zero_for_valid_packet(tmp_path: Path, capsys):
    packet = _write_packet(tmp_path / "valid", _base_packet())
    assert main([str(packet)]) == 0
    assert capsys.readouterr().out.startswith("PASS:")


def test_cli_main_returns_one_for_invalid_packet(tmp_path: Path, capsys):
    documents = _base_packet()
    del documents["task"]["goal"]
    packet = _write_packet(tmp_path / "invalid", documents)
    assert main([str(packet)]) == 1
    assert capsys.readouterr().err.startswith("FAIL:")


def test_schema_manifest_and_paired_fixture_cover_all_contracts():
    manifest = build_manifest()
    expected = _read(FIXTURES / "expected.json")
    for name in ("task", "state", "evidence", "handoff"):
        key = f"contracts/harness/task-control/{name}.schema.json"
        assert key in manifest
        Draft202012Validator.check_schema(_read(SCHEMA_DIR / f"{name}.schema.json"))
    assert "contracts/harness/task-control/transitions.json" in manifest
    assert expected["valid"] == "pass"
    assert all(result == "fail" for name, result in expected.items() if name != "valid")


def test_transition_data_contract_mutation_trips_drift_gate(tmp_path: Path):
    contracts = tmp_path / "contracts"
    shutil.copytree(REPO_ROOT / "contracts", contracts)
    baseline = contracts / ".hashes" / "manifest.json"
    write_manifest(baseline, contracts)
    transition_path = contracts / "harness" / "task-control" / "transitions.json"
    contract = _read(transition_path)
    contract["version"] += 1
    transition_path.write_text(json.dumps(contract) + "\n", encoding="utf-8")
    result = run_gate(contracts, baseline)
    assert not result["ok"]
    assert (
        "contracts/harness/task-control/transitions.json",
        "changed",
        "breaking",
    ) in result["drifted"]


def test_task_control_files_are_lf_utf8_without_bom():
    paths = [
        *SCHEMA_DIR.glob("*.json"),
        *FIXTURES.rglob("*.json"),
        *(REPO_ROOT / "tools" / "task_packet").glob("*.py"),
        *(REPO_ROOT / "tools" / "task_packet").glob("*.toml"),
        *(REPO_ROOT / ".workflow" / "tasks").rglob("*.json"),
        REPO_ROOT / ".workflow" / "tasks" / "README.md",
    ]
    for path in paths:
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert b"\r\n" not in raw, path
        raw.decode("utf-8")
