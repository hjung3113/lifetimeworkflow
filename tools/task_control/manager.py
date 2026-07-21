"""File-backed state mutations with atomic replace and revision CAS.

The task directory is the transaction boundary.  State is the only mutable
canonical document here; artifacts are immutable, run-id-addressed files that
must exist before a state transition can rely on them.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.evidence.capture import EvidenceError, validate_evidence
from tools.risk_router.router import REPO_ROOT as RISK_ROUTER_ROOT
from tools.risk_router.router import decide, load_overlay, load_policy
from tools.task_packet.transitions import is_transition_allowed, required_artifacts_for_phase

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SCHEMA = REPO_ROOT / "contracts/harness/task-control/state.schema.json"
TASK_SCHEMA = REPO_ROOT / "contracts/harness/task-control/task.schema.json"
EVIDENCE_SCHEMA = REPO_ROOT / "contracts/harness/task-control/evidence.schema.json"
ATTESTATION_SCHEMA = REPO_ROOT / "contracts/harness/task-control/attestation.schema.json"


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
    _validate_document("state", state, STATE_SCHEMA)


def _validate_document(name: str, document: dict[str, Any], schema_path: Path) -> None:
    schema = _json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: list(e.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "<root>"
        raise TaskControlError(f"{name}.json:{location}: {error.message}")


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
        # Test-only fault injection proves that a process death after durable temp
        # creation leaves the old canonical state intact and releases flock locks.
        if os.environ.get("TASK_CONTROL_FAULT_AFTER_FSYNC"):
            os._exit(86)
        os.replace(temporary, path)
        # Directory fsync is best-effort POSIX durability (not F_FULLFSYNC on macOS).
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


def _cas_write(task_dir: str | Path, expected_revision: int, next_state: dict[str, Any], *, lock_held: bool = False, allow_head_change: bool = False) -> dict[str, Any]:
    """Compare current on-disk revision immediately before one atomic replace."""
    if type(expected_revision) is not int or expected_revision < 0:
        raise TaskControlError("expected revision must be a non-negative integer")
    path = _state_path(task_dir)
    # Every legitimate state mutation advances an existing evidence anchor with
    # the same CAS revision. A hand-edited anchor that leaves revision unchanged
    # therefore fails validation.
    if isinstance(next_state.get("evidence_integrity"), dict):
        next_state = dict(next_state)
        integrity = dict(next_state["evidence_integrity"])
        integrity["state_revision"] = expected_revision + 1
        next_state["evidence_integrity"] = integrity
    # This is a local advisory lock, not a daemon or distributed transaction.  The
    # kernel releases it on process death, including SIGKILL, so no stale reservation wedges a task.
    lock_path = path.with_name(f".{path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_context = nullcontext() if lock_held else lock_path.open("a+b")
    with lock_context as lock:
        if not lock_held:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        current = _read_state(task_dir)
        if current["revision"] != expected_revision:
            raise TaskControlError(f"stale writer: expected revision {expected_revision}, found {current['revision']}")
        if next_state["revision"] != expected_revision + 1:
            raise TaskControlError("mutation must increment revision by exactly one")
        _validate_state(next_state)
        previous_state_sha256 = sha256(path)
        _atomic_replace(path, next_state)
        # Handoff imports this module, so keep the sanctioned lifecycle bridge lazy.
        # It runs while the state CAS lock is held and only advances an already-valid
        # resume proof; absent, malformed, or stale proofs remain fail-closed at the hook.
        from tools.handoff.handoff import refresh_resume_attestation

        refresh_resume_attestation(
            task_dir,
            current,
            next_state,
            previous_state_sha256=previous_state_sha256,
            allow_head_change=allow_head_change,
        )
        return next_state


def _atomic_create(path: Path, value: dict[str, Any]) -> None:
    """Create *path* exactly once using a durable temp plus hard-link publication."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise TaskControlError("state already exists") from exc
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def create(task_dir: str | Path, state: dict[str, Any]) -> dict[str, Any]:
    """Create initial state exactly once; state must be revision-zero INTAKE."""
    path = _state_path(task_dir)
    _validate_state(state)
    if state["revision"] != 0:
        raise TaskControlError("initial state revision must be zero")
    _atomic_create(path, state)
    return state


def show(task_dir: str | Path) -> dict[str, Any]:
    return _read_state(task_dir)


def _required_artifacts(task_dir: str | Path) -> list[str]:
    task = _json(Path(task_dir) / "task.json")
    _validate_document("task", task, TASK_SCHEMA)
    policy = load_policy()
    lane = task["lane"]
    required = policy["lanes"].get(lane, {}).get("required_artifacts")
    if not isinstance(required, list):
        raise TaskControlError("task has no valid required artifact matrix")
    decision = task["risk_decision"]
    declared = decision["required_artifacts"]
    if not set(declared) >= set(required):
        raise TaskControlError("task required artifacts weaken current policy")
    provenance = decision["overlay_provenance"]
    overlay = None
    if provenance is not None:
        source = provenance["source"]
        snapshot = Path(task_dir) / "risk-overlay.toml"
        overlay_path = snapshot if snapshot.is_file() else RISK_ROUTER_ROOT / source
        try:
            overlay = load_overlay(overlay_path, policy)
        except Exception as exc:
            raise TaskControlError(f"task overlay cannot be replayed: {exc}") from exc
        if overlay.get("_provenance", {}).get("content_sha256") != provenance["content_sha256"]:
            raise TaskControlError("task overlay provenance does not match current overlay")
    current_hashes = decide(
        policy,
        {"scores": {key: 0 for key in ("ambiguity", "change_scope", "data_security", "reversibility", "impact", "coordination", "context_pressure")}},
        overlay,
    )["policy_hashes"]
    if decision["policy_hashes"]["effective"] != current_hashes["effective"]:
        raise TaskControlError("task policy hash does not match current policy")
    return list(required)


def missing_artifacts(task_dir: str | Path, required: list[str] | None = None) -> list[str]:
    root = Path(task_dir)
    missing: list[str] = []
    for artifact in (required if required is not None else _required_artifacts(root)):
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
    # Only adapter-owned output.log files can become canonical run artifacts.
    # Auxiliary files are not evidence and must not make a valid capture orphaned.
    found = sorted(path.relative_to(root).as_posix() for path in artifacts.rglob("output.log") if path.is_file())
    return [path for path in found if path not in referenced]


def _evidence_covers_constraints(task_dir: str | Path) -> bool:
    task = _json(Path(task_dir) / "task.json")
    evidence = _json(Path(task_dir) / "evidence.json")
    _validate_document("evidence", evidence, EVIDENCE_SCHEMA)
    required = {item["id"] for item in task.get("constraints", [])}
    covered: set[str] = set()
    findings = {item["id"]: set(item.get("constraint_ids", [])) for item in evidence.get("findings", [])}
    for run in evidence.get("gate_runs", []):
        if run.get("status") == "PASSED":
            for finding_id in run.get("finding_ids", []):
                covered.update(findings.get(finding_id, set()))
    return required <= covered


def _evidence_covers_criteria(task_dir: str | Path) -> bool:
    task = _json(Path(task_dir) / "task.json")
    evidence = _json(Path(task_dir) / "evidence.json")
    _validate_document("evidence", evidence, EVIDENCE_SCHEMA)
    required = {item["id"] for item in task.get("acceptance_criteria", [])}
    covered = {
        criterion_id
        for run in evidence.get("gate_runs", [])
        if run.get("status") == "PASSED"
        for criterion_id in run.get("criterion_ids", [])
    }
    return required <= covered


def _has_unresolved_major_finding(task_dir: str | Path) -> bool:
    evidence = _json(Path(task_dir) / "evidence.json")
    return any(
        finding.get("severity") in {"blocker", "major"}
        and finding.get("disposition") == "open"
        for finding in evidence.get("findings", [])
    )


def _constitution_diff_requires_approval(task_dir: str | Path) -> bool:
    state = _read_state(task_dir)
    root = Path(task_dir).resolve()
    repository = next((parent for parent in root.parents if (parent / ".git").exists()), None)
    if repository is None:
        raise TaskControlError("cannot locate repository for constitution-plane diff")
    try:
        changed = subprocess.run(
            ["git", "-C", str(repository), "diff", "--name-only", state["baseline"]["commit"], state["current_ref"]],
            text=True, capture_output=True, check=True,
        ).stdout.splitlines()
    except subprocess.CalledProcessError as exc:
        raise TaskControlError("cannot inspect constitution-plane diff") from exc
    constitution_paths = sorted(path for path in changed if path == "golden" or path.startswith(("contracts/", "golden/", "docs/adr/", "glossary/")))
    constitution = bool(constitution_paths)
    if not constitution:
        return False
    evidence = _json(root / "evidence.json")
    for run in evidence.get("gate_runs", []):
        reference = run.get("human_approval_ref")
        if not isinstance(reference, str) or not re.fullmatch(r"approvals/[A-Za-z0-9_-]+\.json", reference):
            continue
        # The approval is a human trust root only when it is already tracked by
        # HEAD. Read its committed bytes; a working-tree file is agent-writable.
        committed = subprocess.run(["git", "-C", str(repository), "show", f"HEAD:{reference}"], capture_output=True, check=False)
        if committed.returncode != 0:
            continue
        try:
            approval = json.loads(committed.stdout.removeprefix(b"\xef\xbb\xbf"))
        except json.JSONDecodeError:
            continue
        if isinstance(approval, dict) and set(approval) == {"approved_paths"} and isinstance(approval["approved_paths"], list) and all(isinstance(path, str) for path in approval["approved_paths"]) and sorted(set(approval["approved_paths"])) == constitution_paths:
            return False
    return True


def _evidence_matches_head(task_dir: str | Path) -> bool:
    """COMPLETE consumes evidence that is tracked and byte-identical to HEAD."""
    root = Path(task_dir).resolve()
    repository = next((parent for parent in root.parents if (parent / ".git").exists()), None)
    if repository is None:
        return False
    try:
        relative = root.relative_to(repository).as_posix() + "/evidence.json"
        head = subprocess.run(["git", "-C", str(repository), "show", f"HEAD:{relative}"], capture_output=True, check=False)
    except (OSError, ValueError):
        return False
    return head.returncode == 0 and head.stdout == (root / "evidence.json").read_bytes()


def transition(task_dir: str | Path, target: str, expected_revision: int, *, next_action: str | None = None, current_ref: str | None = None) -> dict[str, Any]:
    state = _read_state(task_dir)
    if state["blockers"] and target != "BLOCKED":
        raise TaskControlError("unresolved blockers permit only BLOCKED transition")
    task = _json(Path(task_dir) / "task.json")
    # Always verify the task's policy snapshot, even when this target has no
    # artifact prerequisite; otherwise early-phase transitions could launder a weakened packet.
    _required_artifacts(task_dir)
    if not is_transition_allowed(task.get("lane", ""), state["phase"], target):
        raise TaskControlError(f"illegal transition: {state['phase']} -> {target}")
    if target == "BLOCKED":
        raise TaskControlError("use block with a non-empty blocker to enter BLOCKED")
    required = required_artifacts_for_phase(task["lane"], target)
    if required:
        missing = missing_artifacts(task_dir, required)
        if missing:
            raise TaskControlError(f"missing required artifacts: {', '.join(missing)}")
    if target in {"VERIFY", "COMPLETE"}:
        try:
            validate_evidence(task_dir)
        except EvidenceError as exc:
            raise TaskControlError(f"evidence.json: {exc}") from exc
        if not _evidence_covers_constraints(task_dir) or not _evidence_covers_criteria(task_dir):
            raise TaskControlError("required evidence does not cover every constraint and criterion")
    if target == "COMPLETE" and _has_unresolved_major_finding(task_dir):
        raise TaskControlError("unresolved blocker or major finding prevents COMPLETE")
    if target == "COMPLETE" and not _evidence_matches_head(task_dir):
        raise TaskControlError("COMPLETE requires evidence.json committed at HEAD")
    if target == "COMPLETE" and _constitution_diff_requires_approval(task_dir):
        raise TaskControlError("constitution-plane diff requires human approval reference")
    next_state = dict(state)
    next_state.update({"phase": target, "revision": expected_revision + 1, "transition": {"from": state["phase"], "to": target}})
    if next_action is not None:
        next_state["next_action"] = next_action
    if current_ref is not None:
        next_state["current_ref"] = current_ref
    return _cas_write(task_dir, expected_revision, next_state)


def block(task_dir: str | Path, expected_revision: int, blocker: dict[str, Any]) -> dict[str, Any]:
    state = _read_state(task_dir)
    task = _json(Path(task_dir) / "task.json")
    if not is_transition_allowed(task.get("lane", ""), state["phase"], "BLOCKED"):
        raise TaskControlError(f"illegal transition: {state['phase']} -> BLOCKED")
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
    root = Path(task_dir)
    residues = sorted(path.name for path in root.iterdir() if path.name.endswith(".tmp") or path.name.endswith(".cas"))
    return {"state": state, "missing_artifacts": missing, "orphan_artifacts": orphan_artifacts(task_dir), "write_residues": residues}


def refresh_ref(task_dir: str | Path, expected_revision: int, current_ref: str) -> dict[str, Any]:
    """Atomically refresh the repository ref without bypassing revision CAS."""
    state = _read_state(task_dir)
    repository = next(
        (parent for parent in (Path(task_dir).resolve(), *Path(task_dir).resolve().parents) if (parent / ".git").exists()),
        None,
    )
    if repository is None:
        raise TaskControlError("cannot locate repository for current ref refresh")
    head = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if head.returncode or current_ref != head.stdout.strip():
        raise TaskControlError("current ref refresh must name repository HEAD")
    next_state = dict(state)
    next_state.update({"current_ref": current_ref, "revision": expected_revision + 1})
    return _cas_write(task_dir, expected_revision, next_state, allow_head_change=True)


def attest(task_dir: str | Path, records: dict[str, Any]) -> dict[str, Any]:
    """Write attestation records with source hashes derived from the immutable task packet."""
    root = Path(task_dir).resolve()
    task = _json(root / "task.json")
    _validate_document("task", task, TASK_SCHEMA)
    by_id = {constraint["id"]: constraint for constraint in task["constraints"]}
    repository = next(
        (ancestor for ancestor in root.parents if ancestor / ".workflow" / "tasks" / root.name == root),
        None,
    )
    if repository is None:
        raise TaskControlError("task directory is not under .workflow/tasks")
    output = dict(records)
    constraints = output.get("constraints")
    if not isinstance(constraints, list):
        raise TaskControlError("attestation constraints must be an array")
    for record in constraints:
        if not isinstance(record, dict) or record.get("constraint_id") not in by_id:
            raise TaskControlError("attestation has unknown constraint ID")
        constraint = by_id[record["constraint_id"]]
        source = repository / constraint["source_path"]
        if not source.is_file():
            raise TaskControlError(f"missing constraint source: {constraint['source_path']}")
        record["source_path"] = constraint["source_path"]
        record["source_sha256"] = sha256(source)
    _validate_document("context-attestation", output, ATTESTATION_SCHEMA)
    _atomic_replace(root / "context-attestation.json", output)
    return output


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
