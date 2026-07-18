"""Validate task packet files against schemas and cross-document invariants."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.task_packet.transitions import is_transition_allowed

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "contracts" / "harness" / "task-control"
REQUIRED_DOCUMENTS = ("task", "state", "evidence")
OPTIONAL_DOCUMENTS = ("handoff",)


class PacketValidationError(ValueError):
    """A deterministic task packet contract violation."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except FileNotFoundError as exc:
        raise PacketValidationError(f"missing document: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise PacketValidationError(f"invalid JSON in {path.name}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise PacketValidationError(f"{path.name} must contain a JSON object")
    return value


def _schema(name: str) -> dict[str, Any]:
    return _load_json(SCHEMA_DIR / f"{name}.schema.json")


def _validate_schema(name: str, document: dict[str, Any]) -> None:
    validator = Draft202012Validator(_schema(name))
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise PacketValidationError(f"{name}.json:{location}: {error.message}")


def _ids(items: list[dict[str, Any]], label: str) -> set[str]:
    values = [item["id"] for item in items]
    if len(values) != len(set(values)):
        raise PacketValidationError(f"duplicate {label} ID")
    return set(values)


def _require_known(values: list[str], known: set[str], label: str) -> None:
    dangling = sorted(set(values) - known)
    if dangling:
        raise PacketValidationError(f"dangling {label} ID(s): {', '.join(dangling)}")


def _validate_task_id(task_id: str) -> None:
    timestamp = task_id.split("-", 2)[1]
    try:
        datetime.strptime(timestamp, "%Y%m%d%H%M%S")
    except ValueError as exc:
        raise PacketValidationError("task_id contains an invalid UTC timestamp") from exc


def _validate_references(documents: dict[str, dict[str, Any]]) -> None:
    task = documents["task"]
    state = documents["state"]
    evidence = documents["evidence"]
    handoff = documents.get("handoff")

    task_id = task["task_id"]
    _validate_task_id(task_id)
    for name, document in documents.items():
        if document["task_id"] != task_id:
            raise PacketValidationError(f"{name}.json task_id does not match task.json")

    criterion_ids = _ids(task["acceptance_criteria"], "criterion")
    constraint_ids = _ids(task["constraints"], "constraint")
    evidence_ids = _ids(evidence["gate_runs"], "evidence")
    finding_ids = _ids(evidence["findings"], "finding")

    _require_known(state["completed_items"], criterion_ids, "criterion")
    for blocker in state["blockers"]:
        _require_known(blocker["constraint_ids"], constraint_ids, "constraint")
    for run in evidence["gate_runs"]:
        _require_known(run["criterion_ids"], criterion_ids, "criterion")
        _require_known(run["finding_ids"], finding_ids, "finding")
    for finding in evidence["findings"]:
        _require_known(finding["constraint_ids"], constraint_ids, "constraint")

    transition = state["transition"]
    if transition is not None:
        if transition["to"] != state["phase"]:
            raise PacketValidationError("state phase does not match transition target")
        if not is_transition_allowed(task["lane"], transition["from"], transition["to"]):
            raise PacketValidationError(
                f"transition is not allowed for {task['lane']}: "
                f"{transition['from']} -> {transition['to']}"
            )

    if handoff is None:
        return
    _require_known(handoff["critical_constraint_ids"], constraint_ids, "constraint")
    _require_known(handoff["evidence_ids"], evidence_ids, "evidence")
    _require_known(handoff["finding_ids"], finding_ids, "finding")
    snapshot_pairs = (
        ("state_revision", state["revision"]),
        ("goal", task["goal"]),
        ("non_goals", task["non_goals"]),
        ("phase", state["phase"]),
        ("lane", task["lane"]),
        ("baseline", state["baseline"]),
        ("current_ref", state["current_ref"]),
        ("next_action", state["next_action"]),
    )
    for field, expected in snapshot_pairs:
        if handoff[field] != expected:
            raise PacketValidationError(f"handoff {field} does not match packet snapshot")


def validate_packet(packet_dir: str | Path) -> dict[str, dict[str, Any]]:
    """Validate a packet directory and return its decoded documents."""
    root = Path(packet_dir)
    documents = {name: _load_json(root / f"{name}.json") for name in REQUIRED_DOCUMENTS}
    for name in OPTIONAL_DOCUMENTS:
        path = root / f"{name}.json"
        if path.exists():
            documents[name] = _load_json(path)
    for name, document in documents.items():
        _validate_schema(name, document)
    _validate_references(documents)
    return documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one .workflow task packet")
    parser.add_argument("packet_dir")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        validate_packet(args.packet_dir)
    except PacketValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {args.packet_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
