"""Capture registered gate commands and append tamper-evident task evidence."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_SCHEMA = REPO_ROOT / "contracts/harness/task-control/evidence.schema.json"
STATE_SCHEMA = REPO_ROOT / "contracts/harness/task-control/state.schema.json"
GATE_REGISTRY = REPO_ROOT / "contracts/harness/task-control/gate-registry.json"


class EvidenceError(ValueError):
    """Evidence is malformed or cannot be safely captured."""


class EvidenceRefusal(EvidenceError):
    """Sensitive data was detected before it reached an artifact."""


def _canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read {path.name}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"{path.name} must be an object")
    return value


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(value)); handle.flush(); os.fsync(handle.fileno())
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


def _schema_validate(document: dict[str, Any], schema_path: Path = EVIDENCE_SCHEMA) -> None:
    schema = _load(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda item: list(item.path))
    if errors:
        raise EvidenceError(f"evidence schema: {errors[0].message}")


def _registry() -> dict[str, Any]:
    value = _load(GATE_REGISTRY)
    if not isinstance(value.get("gates"), dict) or not isinstance(value.get("version"), str):
        raise EvidenceError("invalid gate registry")
    return value


def normalize_argv(argv: list[str]) -> list[str]:
    normalized = [str(item).removeprefix("\ufeff") for item in argv]
    if not normalized or any(not item or "\x00" in item for item in normalized):
        raise EvidenceError("argv must contain non-empty, NUL-free arguments")
    return normalized


def _sensitive_pattern() -> re.Pattern[str]:
    patterns = _registry().get("secret_patterns")
    if not isinstance(patterns, list) or not all(isinstance(item, str) for item in patterns):
        raise EvidenceError("invalid secret pattern registry")
    # Email and SSN are intentionally not blanket blockers: ordinary test output often
    # contains them. Credentials remain fail-closed, while PII needs an explicit policy.
    return re.compile("(?:" + "|".join(patterns) + ")" if patterns else r"(?!)", re.IGNORECASE)


def _looks_like_high_entropy_token(value: str) -> bool:
    """Reject base64-like 40-byte tokens, but not ordinary 40-hex Git IDs."""
    for candidate in re.findall(r"\b[A-Za-z0-9/+=]{40}\b", value):
        if re.fullmatch(r"[0-9a-fA-F]{40}", candidate):
            continue
        # Plain long identifiers and filesystem segments are not credentials.
        # This heuristic is deliberately scoped to the base64-only characters.
        if not any(char in "/+=" for char in candidate):
            continue
        frequencies = {char: candidate.count(char) / len(candidate) for char in set(candidate)}
        entropy = -sum(probability * __import__("math").log2(probability) for probability in frequencies.values())
        if entropy >= 4.3:
            return True
    return False


def _refuse_if_sensitive(values: dict[str, str], root: Path | None = None) -> None:
    refused = sorted(name for name, value in values.items() if _sensitive_pattern().search(value) or _looks_like_high_entropy_token(value))
    if refused:
        if root is not None and (root / "evidence.json").is_file():
            with _lock(root):
                evidence = _load(root / "evidence.json")
                report = evidence.setdefault("redaction_report", {"status": "CLEAR", "refused_fields": []})
                report["status"] = "REFUSED"; report["refused_fields"] = sorted(set(report["refused_fields"]) | set(refused))
                _schema_validate(evidence); _atomic_write(root / "evidence.json", evidence); _anchor(root, evidence)
        raise EvidenceRefusal("sensitive evidence refused before artifact write")


def _status(exit_code: int, stdout: str, stderr: str) -> str:
    markers = f"{stdout}\n{stderr}".lstrip().upper()
    if markers.startswith("SKIP:") and exit_code == 0:
        return "SKIPPED"
    if markers.startswith("BLOCKED:") and exit_code == 0:
        return "BLOCKED"
    return "PASSED" if exit_code == 0 else "FAILED"


def _next_id(runs: list[dict[str, Any]]) -> str:
    numbers = [int(item["id"].split("-", 1)[1]) for item in runs if re.fullmatch(r"E-\d{2,}", item.get("id", ""))]
    return f"E-{max(numbers, default=0) + 1:02d}"


def _validate_gate(gate: str, argv: list[str], criterion_ids: list[str], gate_version: str) -> None:
    registry = _registry(); definition = registry["gates"].get(gate)
    if not isinstance(definition, dict):
        raise EvidenceError("unregistered gate")
    if gate_version != registry["version"]:
        raise EvidenceError("gate version does not match registry")
    canonical = definition.get("argv")
    if not isinstance(canonical, list) or argv != canonical:
        raise EvidenceError("argv is not allowed for gate")
    pattern = definition.get("criterion_pattern")
    if not isinstance(pattern, str) or any(re.fullmatch(pattern, item) is None for item in criterion_ids):
        raise EvidenceError("criterion is not allowed for gate")


def _lock(root: Path):
    # Evidence publication and lifecycle transitions share one state CAS lock.
    lock_path = root / ".state.json.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def _anchor(root: Path, evidence: dict[str, Any]) -> None:
    """CAS-style state revision anchors every record and the complete evidence index."""
    state_path = root / "state.json"
    if not state_path.is_file():
        raise EvidenceError("capture requires state.json integrity anchor")
    state = _load(state_path)
    anchors = {run["id"]: _digest(run) for run in evidence["gate_runs"]}
    next_state = dict(state)
    next_state["revision"] = state["revision"] + 1
    if next_state.get("transition") is None:
        # A capture is a provenance mutation, not a lifecycle move; its first CAS
        # records an explicit self-transition so revision>0 keeps provenance shape.
        next_state["transition"] = {"from": state["phase"], "to": state["phase"]}
    next_state["evidence_integrity"] = {
        "evidence_sha256": _digest(evidence),
        "run_hashes": anchors,
        "state_revision": next_state["revision"],
    }
    _schema_validate(next_state, STATE_SCHEMA)
    # Local import avoids the module-level capture <-> manager import cycle.
    from tools.task_control.manager import TaskControlError, _cas_write
    try:
        _cas_write(root, state["revision"], next_state, lock_held=True)
    except TaskControlError as exc:
        raise EvidenceError(f"cannot CAS evidence integrity anchor: {exc}") from exc


def _mutate_evidence(root: Path, mutate: Any) -> dict[str, Any]:
    with _lock(root):
        evidence = _load(root / "evidence.json")
        result = mutate(evidence)
        _schema_validate(evidence)
        _atomic_write(root / "evidence.json", evidence)
        _anchor(root, evidence)
        return result


def capture(task_dir: str | Path, gate: str, argv: list[str], *, criterion_ids: list[str] | None = None,
            finding_ids: list[str] | None = None, gate_version: str = "v1", source: str = "local",
            cwd: str | Path | None = None, human_approval_ref: str | None = None) -> dict[str, Any]:
    """Run a registered command once and append only its observed result."""
    root = Path(task_dir); command = normalize_argv(argv)
    criteria = sorted(set(criterion_ids or [])); findings = sorted(set(finding_ids or []))
    if not gate or source not in {"local", "ci"}:
        raise EvidenceError("invalid gate capture metadata")
    _validate_gate(gate, command, criteria, gate_version)
    _refuse_if_sensitive({"argv": "\n".join(command)}, root)
    started = datetime.now(UTC); child = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False); ended = datetime.now(UTC)
    _refuse_if_sensitive({"stdout": child.stdout, "stderr": child.stderr}, root)
    combined = child.stdout.encode() + b"\n--- STDERR ---\n" + child.stderr.encode()
    created_run_roots: list[Path] = []

    def append(evidence: dict[str, Any]) -> dict[str, Any]:
        run_id = _next_id(evidence.setdefault("gate_runs", [])); run_root = root / "artifacts" / gate / run_id
        run_root.mkdir(parents=True, exist_ok=False)
        created_run_roots.append(run_root)
        artifact = run_root / "output.log"; artifact.write_bytes(combined)
        record = {"id": run_id, "gate": gate, "status": _status(child.returncode, child.stdout, child.stderr),
                  "criterion_ids": criteria, "finding_ids": findings, "argv": command, "exit_code": child.returncode,
                  "gate_version": gate_version, "started_at": started.isoformat().replace("+00:00", "Z"),
                  "ended_at": ended.isoformat().replace("+00:00", "Z"), "source": source, **({"human_approval_ref": human_approval_ref} if human_approval_ref else {}),
                  "artifact": {"path": artifact.relative_to(root).as_posix(), "summary": f"captured {len(child.stdout)} stdout and {len(child.stderr)} stderr bytes", "sha256": hashlib.sha256(combined).hexdigest()}}
        evidence["gate_runs"].append(record); evidence.setdefault("findings", []); evidence.setdefault("redaction_report", {"status": "CLEAR", "refused_fields": []})
        return record
    try:
        return _mutate_evidence(root, append)
    except Exception:
        # A failed schema/state publication cannot make an unreferenced artifact canonical.
        # Remove this run's directory so retrying the same E-ID cannot wedge capture.
        if created_run_roots:
            import shutil
            shutil.rmtree(created_run_roots[-1], ignore_errors=True)
        raise


def add_finding(task_dir: str | Path, finding: dict[str, Any]) -> dict[str, Any]:
    """Append a reviewed finding through the same secret-safe, anchored path."""
    root = Path(task_dir)
    _refuse_if_sensitive({"finding": "\n".join(str(v) for v in finding.values() if isinstance(v, str))}, root)
    def append(evidence: dict[str, Any]) -> dict[str, Any]:
        findings = evidence.setdefault("findings", [])
        if any(item.get("id") == finding.get("id") for item in findings):
            raise EvidenceError("duplicate finding ID")
        findings.append(finding)
        evidence.setdefault("gate_runs", []); evidence.setdefault("redaction_report", {"status": "CLEAR", "refused_fields": []})
        return finding
    return _mutate_evidence(root, append)


def validate_evidence(task_dir: str | Path) -> dict[str, Any]:
    root = Path(task_dir); evidence = _load(root / "evidence.json"); _schema_validate(evidence)
    state = _load(root / "state.json")
    integrity = state.get("evidence_integrity")
    if not isinstance(integrity, dict) or integrity.get("evidence_sha256") != _digest(evidence) or integrity.get("state_revision") != state.get("revision"):
        raise EvidenceError("evidence integrity anchor mismatch")
    identifiers: set[str] = set(); finding_ids = {item["id"] for item in evidence["findings"]}
    task = _load(root / "task.json"); criteria = {item["id"] for item in task.get("acceptance_criteria", [])}; constraints = {item["id"] for item in task.get("constraints", [])}
    for run in evidence["gate_runs"]:
        if run["id"] in identifiers: raise EvidenceError("stale evidence index: duplicate evidence ID")
        identifiers.add(run["id"]); _validate_gate(run["gate"], run.get("argv", []), run["criterion_ids"], run.get("gate_version", ""))
        if integrity.get("run_hashes", {}).get(run["id"]) != _digest(run): raise EvidenceError("run integrity anchor mismatch")
        artifact = root / run["artifact"]["path"]
        if not artifact.is_file(): raise EvidenceError(f"missing artifact: {run['artifact']['path']}")
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != run["artifact"]["sha256"]: raise EvidenceError(f"artifact hash mismatch: {run['id']}")
        if run["status"] == "PASSED" and run.get("exit_code") != 0: raise EvidenceError("PASSED evidence must have an observed zero exit code")
        if run["status"] in {"SKIPPED", "BLOCKED"} and run.get("exit_code") != 0: raise EvidenceError("SKIPPED/BLOCKED evidence must have an observed zero exit code")
        if not set(run["criterion_ids"]) <= criteria or not set(run["finding_ids"]) <= finding_ids: raise EvidenceError("dangling evidence reference")
    for finding in evidence["findings"]:
        _refuse_if_sensitive({"finding": finding["summary"]})
        if not set(finding["constraint_ids"]) <= constraints: raise EvidenceError("dangling constraint reference")
        if finding.get("evidence_ref") not in {None, *identifiers}: raise EvidenceError("dangling finding evidence reference")
        if finding["severity"] == "blocker" and finding["disposition"] == "accepted" and not _committed_approval(root, finding.get("human_approval_ref")):
            raise EvidenceError("accepted blocker finding requires human approval reference")
    return evidence


def _committed_approval(root: Path, reference: object) -> bool:
    if not isinstance(reference, str) or not re.fullmatch(r"approvals/[A-Za-z0-9_-]+\.json", reference):
        return False
    repository = next((parent for parent in root.resolve().parents if (parent / ".git").exists()), None)
    if repository is None:
        return False
    try:
        return subprocess.run(["git", "-C", str(repository), "cat-file", "-e", f"HEAD:{reference}"], capture_output=True, check=False).returncode == 0
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture a registered gate command as task evidence")
    sub = parser.add_subparsers(dest="action")
    cap = sub.add_parser("capture"); cap.add_argument("--task-dir", required=True); cap.add_argument("--gate", required=True); cap.add_argument("--criterion", action="append", default=[]); cap.add_argument("--finding", action="append", default=[]); cap.add_argument("--gate-version", default="v1"); cap.add_argument("--source", choices=("local", "ci"), default="local"); cap.add_argument("--human-approval-ref"); cap.add_argument("command", nargs=argparse.REMAINDER)
    finding = sub.add_parser("add-finding"); finding.add_argument("--task-dir", required=True); finding.add_argument("--id", required=True); finding.add_argument("--summary", required=True); finding.add_argument("--constraint", action="append", default=[]); finding.add_argument("--severity", required=True, choices=("blocker", "major", "minor", "nit")); finding.add_argument("--disposition", required=True, choices=("open", "resolved", "accepted")); finding.add_argument("--evidence-ref"); finding.add_argument("--human-approval-ref")
    args = parser.parse_args(argv)
    try:
        if args.action == "add-finding":
            result = add_finding(args.task_dir, {"id": args.id, "summary": args.summary, "constraint_ids": args.constraint, "severity": args.severity, "disposition": args.disposition, **({"evidence_ref": args.evidence_ref} if args.evidence_ref else {}), **({"human_approval_ref": args.human_approval_ref} if args.human_approval_ref else {})})
        else:
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            result = capture(args.task_dir, args.gate, command, criterion_ids=args.criterion, finding_ids=args.finding, gate_version=args.gate_version, source=args.source, human_approval_ref=args.human_approval_ref)
    except EvidenceError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr); return 3
    print(json.dumps({"id": result["id"], "status": result.get("status", "RECORDED")}, sort_keys=True))
    return result.get("exit_code", 0)


if __name__ == "__main__":
    raise SystemExit(main())
