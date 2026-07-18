"""Capture an existing gate command without reimplementing that gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_SCHEMA = REPO_ROOT / "contracts/harness/task-control/evidence.schema.json"
_SENSITIVE = re.compile(
    r"(?:AKIA[0-9A-Z]{16}|(?:api[_-]?key|secret|password|token)\s*[:=]\s*[^\s]+|"
    r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|\b\d{3}-\d{2}-\d{4}\b)",
    re.IGNORECASE,
)


class EvidenceError(ValueError):
    """Evidence is malformed or cannot be safely captured."""


class EvidenceRefusal(EvidenceError):
    """Sensitive data was detected before it reached an artifact."""


def _canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read {path.name}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"{path.name} must be an object")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_bytes(_canonical(value))


def _schema_validate(document: dict[str, Any]) -> None:
    schema = _load(EVIDENCE_SCHEMA)
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda item: list(item.path))
    if errors:
        raise EvidenceError(f"evidence schema: {errors[0].message}")


def normalize_argv(argv: list[str]) -> list[str]:
    normalized = [str(item).removeprefix("\ufeff") for item in argv]
    if not normalized or any(not item or "\x00" in item for item in normalized):
        raise EvidenceError("argv must contain non-empty, NUL-free arguments")
    return normalized


def _refuse_if_sensitive(values: dict[str, str], task_dir: Path) -> None:
    refused = sorted(name for name, value in values.items() if _SENSITIVE.search(value))
    if not refused:
        return
    evidence_path = task_dir / "evidence.json"
    evidence = _load(evidence_path)
    report = evidence.setdefault("redaction_report", {"status": "CLEAR", "refused_fields": []})
    report["status"] = "REFUSED"
    report["refused_fields"] = sorted(set(report.get("refused_fields", [])) | set(refused))
    _write(evidence_path, evidence)
    raise EvidenceRefusal("sensitive evidence refused before artifact write")


def _status(exit_code: int, stdout: str, stderr: str) -> str:
    markers = f"{stdout}\n{stderr}".lstrip().upper()
    if markers.startswith("SKIP:"):
        return "SKIPPED"
    if markers.startswith("BLOCKED:"):
        return "BLOCKED"
    return "PASSED" if exit_code == 0 else "FAILED"


def _next_id(runs: list[dict[str, Any]]) -> str:
    numbers = [int(item["id"].split("-", 1)[1]) for item in runs if re.fullmatch(r"E-\d{2,}", item.get("id", ""))]
    return f"E-{max(numbers, default=0) + 1:02d}"


def capture(
    task_dir: str | Path,
    gate: str,
    argv: list[str],
    *,
    criterion_ids: list[str] | None = None,
    finding_ids: list[str] | None = None,
    gate_version: str = "v1",
    source: str = "local",
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    """Run *argv* once and append only its observed result to evidence.json."""
    root = Path(task_dir)
    command = normalize_argv(argv)
    if not gate or not gate_version or source not in {"local", "ci"}:
        raise EvidenceError("invalid gate capture metadata")
    _refuse_if_sensitive({"argv": "\n".join(command)}, root)
    started = datetime.now(UTC)
    child = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    ended = datetime.now(UTC)
    _refuse_if_sensitive({"stdout": child.stdout, "stderr": child.stderr}, root)
    evidence = _load(root / "evidence.json")
    runs = evidence.setdefault("gate_runs", [])
    run_id = _next_id(runs)
    run_root = root / "artifacts" / gate / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    (run_root / "stdout.log").write_text(child.stdout, encoding="utf-8", newline="\n")
    (run_root / "stderr.log").write_text(child.stderr, encoding="utf-8", newline="\n")
    combined = child.stdout.encode() + b"\n--- STDERR ---\n" + child.stderr.encode()
    artifact = run_root / "output.log"
    artifact.write_bytes(combined)
    record = {
        "id": run_id,
        "gate": gate,
        "status": _status(child.returncode, child.stdout, child.stderr),
        "criterion_ids": sorted(set(criterion_ids or [])),
        "finding_ids": sorted(set(finding_ids or [])),
        "argv": command,
        "exit_code": child.returncode,
        "gate_version": gate_version,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "ended_at": ended.isoformat().replace("+00:00", "Z"),
        "source": source,
        "artifact": {
            "path": artifact.relative_to(root).as_posix(),
            "summary": f"captured {len(child.stdout)} stdout and {len(child.stderr)} stderr bytes",
            "sha256": hashlib.sha256(combined).hexdigest(),
        },
    }
    runs.append(record)
    evidence.setdefault("findings", [])
    evidence.setdefault("redaction_report", {"status": "CLEAR", "refused_fields": []})
    _schema_validate(evidence)
    _write(root / "evidence.json", evidence)
    return record


def validate_evidence(task_dir: str | Path) -> dict[str, Any]:
    root = Path(task_dir)
    evidence = _load(root / "evidence.json")
    _schema_validate(evidence)
    identifiers: set[str] = set()
    for run in evidence["gate_runs"]:
        if run["id"] in identifiers:
            raise EvidenceError("stale evidence index: duplicate evidence ID")
        identifiers.add(run["id"])
        artifact = root / run["artifact"]["path"]
        if not artifact.is_file():
            raise EvidenceError(f"missing artifact: {run['artifact']['path']}")
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != run["artifact"]["sha256"]:
            raise EvidenceError(f"artifact hash mismatch: {run['id']}")
        if run["status"] == "PASSED" and ("exit_code" not in run or run["exit_code"] != 0):
            raise EvidenceError("PASSED evidence must have an observed zero exit code")
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture an existing gate command as task evidence")
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--criterion", action="append", default=[])
    parser.add_argument("--finding", action="append", default=[])
    parser.add_argument("--gate-version", default="v1")
    parser.add_argument("--source", choices=("local", "ci"), default="local")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        record = capture(args.task_dir, args.gate, command, criterion_ids=args.criterion, finding_ids=args.finding, gate_version=args.gate_version, source=args.source)
    except EvidenceError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"id": record["id"], "status": record["status"]}, sort_keys=True))
    return record["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
