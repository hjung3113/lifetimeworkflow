"""Generate and validate immutable, pointer-only fresh-session handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.evidence.capture import EvidenceError, _refuse_if_sensitive, validate_evidence
from tools.task_control.manager import TaskControlError, _validate_document, sha256, show

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF_SCHEMA = REPO_ROOT / "contracts/harness/task-control/handoff.schema.json"
TASK_SCHEMA = REPO_ROOT / "contracts/harness/task-control/task.schema.json"
STATE_SCHEMA = REPO_ROOT / "contracts/harness/task-control/state.schema.json"
HANDOFF_DIR = "handoffs"
ACTIVE_POINTER_NAME = "active-task.json"
RESUME_ATTESTATION_NAME = "handoff-resume.json"


class HandoffError(ValueError):
    """A handoff is absent, malformed, stale, or unsafe to publish."""


def _canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffError(f"stale or unreadable handoff: {path.name}") from exc
    if not isinstance(value, dict):
        raise HandoffError(f"{path.name} must be an object")
    return value


def _validate_schema(document: dict[str, Any]) -> None:
    schema = _load(HANDOFF_SCHEMA)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document), key=lambda error: list(error.path)
    )
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.path) or "<root>"
        raise HandoffError(f"handoff.json:{where}: {error.message}")


def _repo(task_dir: Path) -> Path:
    root = next(
        (
            parent
            for parent in (task_dir.resolve(), *task_dir.resolve().parents)
            if (parent / ".git").exists()
        ),
        None,
    )
    if root is None:
        raise HandoffError("handoff requires a task directory within a repository")
    return root


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise HandoffError("handoff reference escapes repository") from exc


def _path_ref(root: Path, path: Path) -> dict[str, str]:
    if not path.is_file():
        raise HandoffError(f"missing referenced path: {_relative(root, path)}")
    return {"path": _relative(root, path), "sha256": sha256(path)}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise HandoffError("cannot resolve repository reference")
    return result.stdout.strip()


def _git_bytes(root: Path, revision: str, relative_path: str) -> bytes:
    """Read a blob from git, never from the mutable worktree."""
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{revision}:{relative_path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise HandoffError(f"trust root is missing committed path: {relative_path}")
    return result.stdout


def packet_root_from_handoff(handoff_path: str | Path) -> Path:
    """Reverse the sole supported handoff layout without guessing directories."""
    source = Path(handoff_path).resolve()
    if source.parent.name != HANDOFF_DIR or not source.name.startswith("revision-"):
        raise HandoffError("handoff path is not a canonical task handoff")
    packet = source.parent.parent
    if not (packet / "task.json").is_file():
        raise HandoffError("handoff packet root is missing task.json")
    return packet


def _changed_paths(root: Path, baseline: str, current: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", baseline, current],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise HandoffError("cannot derive changed paths")
    return sorted(set(line for line in result.stdout.splitlines() if line))


def _atomic_write_once(path: Path, document: dict[str, Any]) -> None:
    payload = _canonical(document)
    if path.exists():
        if path.read_bytes() != payload:
            raise HandoffError(
                "handoff already exists for a different snapshot; create a new revision first"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise HandoffError("handoff already exists for a different snapshot")
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


def _handoff_path(task_dir: Path, revision: int) -> Path:
    return task_dir / HANDOFF_DIR / f"revision-{revision:010d}.json"


def _snapshot(task_dir: Path) -> dict[str, Any]:
    root = _repo(task_dir)
    task = _load(task_dir / "task.json")
    state = show(task_dir)
    evidence = _load(task_dir / "evidence.json")
    try:
        _validate_document("task", task, TASK_SCHEMA)
        _validate_document("state", state, STATE_SCHEMA)
        validate_evidence(task_dir)
    except (TaskControlError, EvidenceError) as exc:
        raise HandoffError(f"cannot snapshot invalid packet: {exc}") from exc
    if not (task["task_id"] == state["task_id"] == evidence["task_id"]):
        raise HandoffError("task/state/evidence task ID mismatch")
    if _git(root, "rev-parse", "HEAD") != state["current_ref"]:
        raise HandoffError("state current ref is stale; refresh state before generating handoff")
    constraints = sorted(task["constraints"], key=lambda item: item["id"])
    critical = [item["id"] for item in constraints]
    constraint_refs = [
        {"path": item["source_path"], "sha256": item["source_sha256"]} for item in constraints
    ]
    decision_refs = sorted(task["decision_refs"], key=lambda item: (item["path"], item["sha256"]))
    artifacts = sorted(
        (
            {
                "evidence_id": run["id"],
                "path": run["artifact"]["path"],
                "sha256": run["artifact"]["sha256"],
            }
            for run in evidence["gate_runs"]
        ),
        key=lambda item: (item["evidence_id"], item["path"]),
    )
    unresolved = sorted(
        (
            [{"id": item["id"], "kind": "blocker"} for item in state["blockers"]]
            + [
                {"id": item["id"], "kind": "finding"}
                for item in evidence["findings"]
                if item["disposition"] == "open"
            ]
        ),
        key=lambda item: (item["kind"], item["id"]),
    )
    reads = sorted(
        {
            _relative(root, task_dir / "task.json"),
            _relative(root, task_dir / "state.json"),
            _relative(root, task_dir / "evidence.json"),
            *(item["source_path"] for item in constraints),
            *(item["path"] for item in decision_refs),
        }
    )
    return {
        "task_id": task["task_id"],
        "state_revision": state["revision"],
        "goal": task["goal"],
        "non_goals": task["non_goals"],
        "critical_constraint_ids": critical,
        "phase": state["phase"],
        "lane": task["lane"],
        "baseline": state["baseline"],
        "current_ref": state["current_ref"],
        "next_action": state["next_action"],
        "evidence_ids": sorted(run["id"] for run in evidence["gate_runs"]),
        "finding_ids": sorted(item["id"] for item in evidence["findings"]),
        "critical_constraint_refs": constraint_refs,
        "decisions": decision_refs,
        "changed_paths": _changed_paths(root, state["baseline"]["commit"], state["current_ref"]),
        "unresolved_items": unresolved,
        # This is intentionally task-specific only.  Do not substitute a generic gate failure
        # rule here: absence must survive a fresh-session restore as absence.
        "stop_condition": task.get("stop_condition"),
        "required_read_paths": reads,
        "state_ref": _path_ref(root, task_dir / "state.json"),
        "evidence_ref": _path_ref(root, task_dir / "evidence.json"),
        "artifact_refs": artifacts,
    }


def generate(task_dir: str | Path) -> dict[str, Any]:
    """Derive and immutably publish one handoff for the packet's current revision."""
    packet = Path(task_dir)
    handoff = _snapshot(packet)
    _refuse_handoff_pii(handoff)
    _validate_schema(handoff)
    _atomic_write_once(_handoff_path(packet, handoff["state_revision"]), handoff)
    return handoff


def _refuse_handoff_pii(handoff: dict[str, Any]) -> None:
    """Handoffs are durable; reject PII as well as the Phase-21 secret policy."""
    import re

    patterns = (
        re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
        re.compile(r"(?<!\d)(?:\+?\d{1,3}[-. ]?)?(?:\(?\d{2,3}\)?[-. ]?)\d{3,4}[-. ]?\d{4}(?!\d)"),
        re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b"),
        re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
    )
    # Paths and nested metadata are durable handoff content too.  Scan every
    # human-controlled string leaf, excluding opaque identifiers and hashes: the
    # numeric PII patterns would otherwise mistake a task timestamp for a phone.
    opaque_keys = {"commit", "current_ref", "sha256", "task_id", "state_revision", "evidence_id"}

    def strings(value: Any, key: str | None = None) -> list[str]:
        if key in opaque_keys or (key is not None and key.endswith("_id")):
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [text for item in value for text in strings(item, key)]
        if isinstance(value, dict):
            return [text for name, item in value.items() for text in strings(item, name)]
        return []

    values = [re.sub(r"T-\d{14}-[a-z0-9-]+", "TASK", value) for value in strings(handoff)]
    if any(pattern.search(value) for value in values for pattern in patterns):
        raise HandoffError("sensitive handoff refused: PII in handoff content")
    try:
        _refuse_if_sensitive({"handoff": _canonical(handoff).decode("ascii")})
    except EvidenceError as exc:
        raise HandoffError("sensitive handoff refused: credential material") from exc


def _validate_ref(
    root: Path, reference: dict[str, Any], *, artifact: bool = False, packet: Path | None = None
) -> None:
    path = (
        (packet / str(reference["path"]))
        if artifact and packet is not None
        else root / str(reference["path"])
    )
    if not path.is_file():
        raise HandoffError(f"stale reference: missing {reference['path']}")
    relative = _relative(root, path) if artifact else str(reference["path"])
    committed = _git_bytes(root, "HEAD", relative)
    if (
        hashlib.sha256(committed).hexdigest() != reference["sha256"]
        or sha256(path) != reference["sha256"]
    ):
        label = "artifact" if artifact else "reference"
        raise HandoffError(f"stale {label}: hash mismatch for {reference['path']}")


def validate(task_dir: str | Path, handoff_path: str | Path | None = None) -> dict[str, Any]:
    """Validate against committed HEAD blobs, never a mutable recomputed snapshot."""
    packet = Path(task_dir)
    root = _repo(packet)
    if handoff_path is None:
        current = show(packet)
        source = _handoff_path(packet, current["revision"])
    else:
        source = Path(handoff_path)
    handoff = _load(source)
    _validate_schema(handoff)
    source_relative = _relative(root, source)
    if _git_bytes(root, "HEAD", source_relative) != source.read_bytes():
        raise HandoffError("stale handoff: bytes differ from committed trust root")
    head = _git(root, "rev-parse", "HEAD")
    # A checkpoint publication commit contains the packet and pointer; its parent is the exact
    # code/state revision described by the handoff.  Direct publication at that revision is also
    # accepted for non-checkpoint workflows.
    parents = _git(root, "rev-list", "--parents", "-n", "1", "HEAD").split()
    publication_parent = parents[1] if len(parents) == 2 else None
    if handoff["current_ref"] not in {head, publication_parent}:
        raise HandoffError("stale handoff: current ref is not the publication boundary")
    # Publication-path discipline is enforced before the commit by /checkpoint's
    # explicit path list and the commit hook.  Validation remains a trust-root
    # verifier rather than a second staging-policy interpreter, so it can validate
    # an existing legacy publication whose packet was first introduced with it.
    _validate_ref(root, handoff["state_ref"])
    _validate_ref(root, handoff["evidence_ref"])
    for reference in handoff["critical_constraint_refs"] + handoff["decisions"]:
        _validate_ref(root, reference)
    for reference in handoff["artifact_refs"]:
        # Evidence artifact paths are deliberately relative to the task transaction boundary.
        _validate_ref(root, reference, artifact=True, packet=packet)
    return handoff


def fresh_session(handoff_path: str | Path) -> dict[str, Any]:
    """Return the complete resume minimum using only the immutable handoff file."""
    packet = packet_root_from_handoff(handoff_path)
    handoff = validate(packet, handoff_path)
    required = (
        "task_id",
        "goal",
        "non_goals",
        "critical_constraint_ids",
        "phase",
        "current_ref",
        "next_action",
        "stop_condition",
    )
    restored = {field: handoff[field] for field in required}
    if len(restored) != len(required) or any(
        value in (None, "")
        for key, value in restored.items()
        if key != "stop_condition" and not isinstance(value, list)
    ):
        raise HandoffError("handoff cannot fully reconstruct fresh-session minimum")
    return restored


def activate(task_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    """Record only the active task identity and immutable handoff pointer in session state."""
    packet = Path(task_dir)
    root = _repo(packet)
    # Activation happens before the checkpoint publication commit.  It may only point at a
    # generator-produced snapshot for the exact current packet; resume remains HEAD-bound.
    source = _handoff_path(packet, show(packet)["revision"])
    handoff = _load(source)
    if handoff != _snapshot(packet):
        raise HandoffError("cannot activate a stale unpublished handoff")
    pointer = {
        "task_id": handoff["task_id"],
        "handoff_path": _relative(root, _handoff_path(packet, handoff["state_revision"])),
        "state_revision": handoff["state_revision"],
    }
    path = Path(state_dir) / ACTIVE_POINTER_NAME
    # Session state is intentionally the sole mutable pointer plane: no packet body, logs,
    # evidence, or contract text may be copied here.
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=Path(state_dir)
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(pointer))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return pointer


def resume(state_dir: str | Path, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Fresh-process resume barrier: validate HANDOFF then run the existing phase gate."""
    pointer_path = Path(state_dir) / ACTIVE_POINTER_NAME
    if not pointer_path.exists():
        return {"resume": None, "diagnostics": ["no active task"]}
    pointer = _load(pointer_path)
    if set(pointer) != {"task_id", "handoff_path", "state_revision"}:
        raise HandoffError(
            "active task pointer must contain only task ID, revision, and handoff path"
        )
    root = Path(repo_root).resolve() if repo_root else REPO_ROOT
    handoff_path = root / str(pointer["handoff_path"])
    packet = handoff_path.parent.parent
    handoff = validate(packet, handoff_path)
    if (
        handoff["task_id"] != pointer["task_id"]
        or handoff["state_revision"] != pointer["state_revision"]
    ):
        raise HandoffError("active task pointer is stale; regenerate handoff and checkpoint")
    from tools.task_control.phase_gate import phase_gate

    try:
        diagnostics = phase_gate(
            packet,
            handoff["state_revision"],
            repo_root=root,
            publication_parent=handoff["current_ref"],
        )
    except TaskControlError as exc:
        raise HandoffError(f"resume blocked until /phase-gate passes: {exc}") from exc
    attestation = {
        "kind": "handoff-resume-attestation",
        "task_id": handoff["task_id"],
        "state_revision": handoff["state_revision"],
        "head": _git(root, "rev-parse", "HEAD"),
        "handoff_path": str(pointer["handoff_path"]),
        "handoff_sha256": sha256(handoff_path),
        "state_sha256": sha256(packet / "state.json"),
        "attested_at": datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    _atomic_replace(Path(state_dir) / RESUME_ATTESTATION_NAME, attestation)
    return {"resume": fresh_session(handoff_path), "diagnostics": diagnostics}


def require_resume_attestation(state_dir: str | Path, repo_root: str | Path | None = None) -> None:
    """Fail-closed common entry barrier for EXECUTE, REVIEW, and VERIFY."""
    root = Path(repo_root).resolve() if repo_root else REPO_ROOT
    pointer_path = Path(state_dir) / ACTIVE_POINTER_NAME
    if not pointer_path.exists():
        return
    pointer = _load(pointer_path)
    if set(pointer) != {"task_id", "handoff_path", "state_revision"}:
        raise HandoffError("protected entry blocked: active task pointer is invalid")
    handoff_path = root / str(pointer["handoff_path"])
    packet = packet_root_from_handoff(handoff_path)
    state = show(packet)
    if state["task_id"] != pointer["task_id"] or state["revision"] < pointer["state_revision"]:
        raise HandoffError("protected entry blocked: active task revision is stale")
    attestation = _load(Path(state_dir) / RESUME_ATTESTATION_NAME)
    expected_keys = {
        "kind",
        "task_id",
        "state_revision",
        "head",
        "handoff_path",
        "handoff_sha256",
        "state_sha256",
        "attested_at",
    }
    if set(attestation) != expected_keys:
        raise HandoffError("protected entry blocked: resume attestation is invalid")
    if (
        attestation.get("kind") != "handoff-resume-attestation"
        or attestation.get("task_id") != pointer["task_id"]
        or attestation.get("state_revision") != state["revision"]
        or attestation.get("head") != _git(root, "rev-parse", "HEAD")
        or attestation.get("handoff_path") != pointer["handoff_path"]
    ):
        raise HandoffError("protected entry blocked: active handoff has not been resumed")
    if attestation.get("handoff_sha256") != sha256(handoff_path):
        raise HandoffError("protected entry blocked: resume attestation is stale")
    if attestation.get("state_sha256") != sha256(packet / "state.json"):
        raise HandoffError("protected entry blocked: active task state is stale")


def refresh_resume_attestation(
    task_dir: str | Path,
    previous_state: dict[str, Any],
    next_state: dict[str, Any],
    *,
    previous_state_sha256: str,
    allow_head_change: bool = False,
) -> None:
    """Advance a valid resume proof only after a sanctioned CAS state mutation.

    The pointer remains anchored to the immutable handoff that was resumed.  Its
    attestation follows the verified state lineage, so a normal lifecycle transition
    cannot freeze the session.  A new HEAD is accepted only for ``refresh_ref``,
    whose caller verifies that the supplied ref is exactly HEAD.
    """
    packet = Path(task_dir)
    root = _repo(packet)
    state_dir = root / ".memory/state"
    pointer_path = state_dir / ACTIVE_POINTER_NAME
    attestation_path = state_dir / RESUME_ATTESTATION_NAME
    if not pointer_path.exists():
        return
    try:
        pointer = _load(pointer_path)
    except HandoffError:
        return
    expected_pointer_keys = {"task_id", "handoff_path", "state_revision"}
    if set(pointer) != expected_pointer_keys or pointer["task_id"] != next_state["task_id"]:
        return
    try:
        attestation = _load(attestation_path)
    except HandoffError:
        return
    expected_keys = {
        "kind", "task_id", "state_revision", "head", "handoff_path",
        "handoff_sha256", "state_sha256", "attested_at",
    }
    current_head = _git(root, "rev-parse", "HEAD")
    if (
        set(attestation) != expected_keys
        or attestation.get("kind") != "handoff-resume-attestation"
        or attestation.get("task_id") != next_state["task_id"]
        or attestation.get("state_revision") != previous_state["revision"]
        or attestation.get("handoff_path") != pointer["handoff_path"]
        or attestation.get("handoff_sha256") != sha256(root / str(pointer["handoff_path"]))
        or attestation.get("state_sha256") != previous_state_sha256
    ):
        return
    if not allow_head_change and attestation.get("head") != current_head:
        return
    advanced = dict(attestation)
    advanced.update(
        {
            "state_revision": next_state["revision"],
            "head": current_head,
            "state_sha256": sha256(packet / "state.json"),
            "attested_at": datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
        }
    )
    _atomic_replace(attestation_path, advanced)


def _atomic_replace(path: Path, document: dict[str, Any]) -> None:
    """Atomically replace the deliberately mutable current-session attestation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(document))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and validate immutable task handoffs")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "validate"):
        command = commands.add_parser(name)
        command.add_argument("task_dir", type=Path)
    fresh = commands.add_parser("fresh-session")
    fresh.add_argument("handoff", type=Path)
    active = commands.add_parser("activate")
    active.add_argument("task_dir", type=Path)
    active.add_argument("--state-dir", required=True, type=Path)
    resume_command = commands.add_parser("resume")
    resume_command.add_argument("--state-dir", required=True, type=Path)
    resume_command.add_argument("--repo-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            result = generate(args.task_dir)
        elif args.command == "validate":
            result = validate(args.task_dir)
        elif args.command == "fresh-session":
            result = fresh_session(args.handoff)
        elif args.command == "activate":
            result = activate(args.task_dir, args.state_dir)
        else:
            result = resume(args.state_dir, args.repo_root)
    except HandoffError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
