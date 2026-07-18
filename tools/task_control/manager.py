"""File-backed state mutations with atomic replace and revision CAS.

The task directory is the transaction boundary.  State is the only mutable
canonical document here; artifacts are immutable, run-id-addressed files that
must exist before a state transition can rely on them.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.risk_router.router import load_policy
from tools.task_packet.transitions import is_transition_allowed

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SCHEMA = REPO_ROOT / "contracts/harness/task-control/state.schema.json"


class TaskControlError(ValueError):
    """A deterministic state-control failure."""


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    except FileNotFoundError as exc:
        raise TaskControlError(f"missing file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise TaskControlError(f"invalid JSON in {path.name}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise TaskControlError(f"{path.name} must be a JSON object")
    return value


def _state_path(task_dir: str | Path) -> Path:
    return Path(task_dir) / "state.json"


def _validate_state(state: dict[str, Any]) -> None:
    schema = _json(STATE_SCHEMA)
    errors = sorted(Draft202012Validator(schema).iter_errors(state), key=lambda e: list(e.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "<root>"
        raise TaskControlError(f"state.json:{location}: {error.message}")


def _read_state(task_dir: str | Path) -> dict[str, Any]:
    state = _json(_state_path(task_dir))
    _validate_state(state)
    return state


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def _atomic_replace(path: Path, value: dict[str, Any]) -> None:
    """Durably replace *path* with a same-directory temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _cas_write(task_dir: str | Path, expected_revision: int, next_state: dict[str, Any]) -> dict[str, Any]:
    """Compare current on-disk revision immediately before one atomic replace."""
    if type(expected_revision) is not int or expected_revision < 0:
        raise TaskControlError("expected revision must be a non-negative integer")
    path = _state_path(task_dir)
    # O_EXCL reservation is deliberately short-lived.  It is not a daemon or a
    # cross-worktree lock; it closes the check/replace window for competing CAS writers.
    reservation = path.with_name(f".{path.name}.cas")
    try:
        fd = os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise TaskControlError("stale writer: another mutation is in progress") from exc
    try:
        os.close(fd)
        current = _read_state(task_dir)
        if current["revision"] != expected_revision:
            raise TaskControlError(f"stale writer: expected revision {expected_revision}, found {current['revision']}")
        if next_state["revision"] != expected_revision + 1:
            raise TaskControlError("mutation must increment revision by exactly one")
        _validate_state(next_state)
        _atomic_replace(path, next_state)
        return next_state
    finally:
        try:
            reservation.unlink()
        except FileNotFoundError:
            pass


def create(task_dir: str | Path, state: dict[str, Any]) -> dict[str, Any]:
    """Create initial state exactly once; state must be revision-zero INTAKE."""
    path = _state_path(task_dir)
    if path.exists():
        raise TaskControlError("state already exists")
    _validate_state(state)
    if state["revision"] != 0:
        raise TaskControlError("initial state revision must be zero")
    _atomic_replace(path, state)
    return state


def show(task_dir: str | Path) -> dict[str, Any]:
    return _read_state(task_dir)


def _required_artifacts(task_dir: str | Path) -> list[str]:
    task = _json(Path(task_dir) / "task.json")
    decision = task.get("risk_decision", {})
    required = decision.get("required_artifacts")
    if not isinstance(required, list) or not all(isinstance(item, str) and item for item in required):
        lane = task.get("lane")
        required = load_policy()["lanes"].get(lane, {}).get("required_artifacts")
    if not isinstance(required, list):
        raise TaskControlError("task has no valid required artifact matrix")
    return list(required)


def missing_artifacts(task_dir: str | Path) -> list[str]:
    root = Path(task_dir)
    missing: list[str] = []
    for artifact in _required_artifacts(root):
        if artifact == "task_packet":
            present = all((root / name).is_file() for name in ("task.json", "state.json", "evidence.json"))
        else:
            # Every non-packet artifact must be completed in an immutable run-ID directory.
            artifact_root = root / "artifacts" / artifact
            present = artifact_root.is_dir() and any(child.is_dir() and any(child.iterdir()) for child in artifact_root.iterdir())
        if not present:
            missing.append(artifact)
    return missing


def orphan_artifacts(task_dir: str | Path) -> list[str]:
    """List immutable artifact runs not referenced by evidence; they are never canonical evidence."""
    root = Path(task_dir)
    evidence = _json(root / "evidence.json")
    referenced = {entry["artifact"]["path"] for entry in evidence.get("gate_runs", []) if isinstance(entry, dict) and isinstance(entry.get("artifact"), dict) and isinstance(entry["artifact"].get("path"), str)}
    artifacts = root / "artifacts"
    if not artifacts.exists():
        return []
    found = sorted(path.relative_to(root).as_posix() for path in artifacts.rglob("*") if path.is_file())
    return [path for path in found if path not in referenced]


def _evidence_covers_constraints(task_dir: str | Path) -> bool:
    task = _json(Path(task_dir) / "task.json")
    evidence = _json(Path(task_dir) / "evidence.json")
    required = {item["id"] for item in task.get("constraints", [])}
    covered: set[str] = set()
    findings = {item["id"]: set(item.get("constraint_ids", [])) for item in evidence.get("findings", [])}
    for run in evidence.get("gate_runs", []):
        if run.get("status") == "PASSED":
            for finding_id in run.get("finding_ids", []):
                covered.update(findings.get(finding_id, set()))
            covered.update(run.get("constraint_ids", []))  # forwards-compatible local evidence.
    return required <= covered


def transition(task_dir: str | Path, target: str, expected_revision: int, *, next_action: str | None = None) -> dict[str, Any]:
    state = _read_state(task_dir)
    if state["blockers"] and target != "BLOCKED":
        raise TaskControlError("unresolved blockers permit only BLOCKED transition")
    task = _json(Path(task_dir) / "task.json")
    if not is_transition_allowed(task.get("lane", ""), state["phase"], target):
        raise TaskControlError(f"illegal transition: {state['phase']} -> {target}")
    if target not in {"BLOCKED", "INTAKE", "CLARIFY", "SPEC", "PLAN"}:
        missing = missing_artifacts(task_dir)
        if missing:
            raise TaskControlError(f"missing required artifacts: {', '.join(missing)}")
    if target in {"VERIFY", "COMPLETE"} and not _evidence_covers_constraints(task_dir):
        raise TaskControlError("required evidence does not cover every constraint")
    next_state = dict(state)
    next_state.update({"phase": target, "revision": expected_revision + 1, "transition": {"from": state["phase"], "to": target}})
    if next_action is not None:
        next_state["next_action"] = next_action
    return _cas_write(task_dir, expected_revision, next_state)


def block(task_dir: str | Path, expected_revision: int, blocker: dict[str, Any]) -> dict[str, Any]:
    state = _read_state(task_dir)
    next_state = dict(state)
    blockers = list(state["blockers"])
    if any(item["id"] == blocker.get("id") for item in blockers):
        raise TaskControlError("duplicate blocker ID")
    blockers.append(blocker)
    next_state.update({"phase": "BLOCKED", "revision": expected_revision + 1, "blockers": blockers, "transition": {"from": state["phase"], "to": "BLOCKED"}})
    return _cas_write(task_dir, expected_revision, next_state)


def resume(
    task_dir: str | Path,
    target: str,
    expected_revision: int,
    *,
    resolve_blocker_ids: list[str] | None = None,
) -> dict[str, Any]:
    state = _read_state(task_dir)
    if state["phase"] != "BLOCKED":
        raise TaskControlError("resume requires BLOCKED phase")
    resolved = set(resolve_blocker_ids or [])
    unknown = resolved - {item["id"] for item in state["blockers"]}
    if unknown:
        raise TaskControlError(f"unknown blocker ID(s): {', '.join(sorted(unknown))}")
    if resolved:
        remaining = [item for item in state["blockers"] if item["id"] not in resolved]
    else:
        remaining = state["blockers"]
    if remaining:
        raise TaskControlError("resume requires all blockers to be resolved")
    task = _json(Path(task_dir) / "task.json")
    if not is_transition_allowed(task.get("lane", ""), "BLOCKED", target):
        raise TaskControlError(f"illegal transition: BLOCKED -> {target}")
    next_state = dict(state)
    next_state.update({"phase": target, "revision": expected_revision + 1, "blockers": remaining, "transition": {"from": "BLOCKED", "to": target}})
    return _cas_write(task_dir, expected_revision, next_state)


def validate(task_dir: str | Path) -> dict[str, Any]:
    state = _read_state(task_dir)
    missing = missing_artifacts(task_dir)
    return {"state": state, "missing_artifacts": missing, "orphan_artifacts": orphan_artifacts(task_dir)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
