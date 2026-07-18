from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import tools.evidence.capture as capture_module
from tools.evidence.capture import EvidenceError, EvidenceRefusal, _status, add_finding, capture, validate_evidence


def packet(tmp_path: Path) -> Path:
    root = tmp_path / "T-20260719000000-fixture"
    root.mkdir()
    (root / "evidence.json").write_text(json.dumps({
        "task_id": "T-20260719000000-fixture",
        "gate_runs": [],
        "findings": [],
        "redaction_report": {"status": "CLEAR", "refused_fields": []},
    }), encoding="utf-8")
    (root / "task.json").write_text(json.dumps({"task_id": "T-20260719000000-fixture", "acceptance_criteria": [], "constraints": []}), encoding="utf-8")
    (root / "state.json").write_text(json.dumps({"task_id": "T-20260719000000-fixture", "phase": "INTAKE", "revision": 0, "baseline": {"repo_root": ".", "commit": "0" * 40}, "current_ref": "0" * 40, "completed_items": [], "next_action": "test", "blockers": [], "transition": None}), encoding="utf-8")
    return root


@pytest.mark.parametrize(("marker", "exit_code", "expected"), [
    ("PASS", 0, "PASSED"), ("FAIL", 7, "FAILED"), ("SKIP: absent", 0, "SKIPPED"), ("BLOCKED: waiting", 0, "BLOCKED"),
])
def test_capture_round_trips_observed_statuses(tmp_path: Path, marker: str, exit_code: int, expected: str) -> None:
    assert _status(exit_code, marker, "") == expected
    assert _status(7, "SKIP: absent", "") == "FAILED"


def test_hash_tamper_and_missing_artifact_fail_validation(tmp_path: Path) -> None:
    root = packet(tmp_path)
    record = capture(root, "tests", ["uv", "run", "pytest", "--version"])
    artifact = root / record["artifact"]["path"]
    artifact.write_bytes(artifact.read_bytes() + b"x")
    with pytest.raises(EvidenceError, match="hash mismatch"):
        validate_evidence(root)
    artifact.unlink()
    with pytest.raises(EvidenceError, match="missing artifact"):
        validate_evidence(root)


def test_unexecuted_pass_and_stale_index_are_rejected(tmp_path: Path) -> None:
    root = packet(tmp_path)
    evidence = json.loads((root / "evidence.json").read_text())
    evidence["gate_runs"] = [{"id": "E-01", "gate": "tests", "status": "PASSED", "criterion_ids": [], "finding_ids": [], "argv": ["uv", "run", "pytest"], "exit_code": 0, "gate_version": "v1", "started_at": "2026-07-19T00:00:00Z", "ended_at": "2026-07-19T00:00:00Z", "source": "local", "artifact": {"path": "artifacts/tests/E-01/output.log", "summary": "forged", "sha256": "0" * 64}}]
    (root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(EvidenceError, match="integrity anchor mismatch"):
        validate_evidence(root)


def test_sensitive_output_is_refused_without_plaintext_artifact(tmp_path: Path) -> None:
    root = packet(tmp_path)
    with pytest.raises(EvidenceRefusal):
        capture(root, "tests", ["uv", "run", "pytest", "-c", "password=super-secret-value"])
    contents = "\n".join(path.read_text(errors="ignore") for path in root.rglob("*") if path.is_file())
    assert "super-secret-value" not in contents
    report = json.loads((root / "evidence.json").read_text())["redaction_report"]
    assert report == {"status": "REFUSED", "refused_fields": ["argv"]}


def test_forged_consistent_pass_is_rejected_by_record_anchor(tmp_path: Path) -> None:
    root = packet(tmp_path)
    record = capture(root, "tests", ["uv", "run", "pytest", "--version"])
    artifact = root / record["artifact"]["path"]
    evidence = json.loads((root / "evidence.json").read_text())
    evidence["gate_runs"][0]["status"] = "PASSED"
    evidence["gate_runs"][0]["exit_code"] = 0
    evidence["gate_runs"][0]["artifact"]["sha256"] = __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
    evidence["gate_runs"][0]["artifact"]["summary"] = "forged, but internally consistent"
    (root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(EvidenceError, match="integrity anchor mismatch"):
        validate_evidence(root)


def test_unregistered_argv_and_sensitive_finding_are_refused(tmp_path: Path) -> None:
    root = packet(tmp_path)
    with pytest.raises(EvidenceError, match="argv is not allowed"):
        capture(root, "tests", ["true"])
    with pytest.raises(EvidenceRefusal):
        add_finding(root, {"id": "F-01", "summary": "ghp_abcdefghijklmnopqrstuvwxyz0123456789", "constraint_ids": [], "severity": "minor", "disposition": "open"})


@pytest.mark.parametrize("secret", ["ghp_abcdefghijklmnopqrstuvwxyz0123456789", "sk-abcdefghijklmnopqrstuvwxyz012345", "xoxb-123456-token", "-----BEGIN PRIVATE KEY-----", "eyJabcde12345.payload.signature", "Authorization: Bearer abcdef", "A" * 40])
def test_sensitive_stdout_patterns_are_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, secret: str) -> None:
    root = packet(tmp_path); source = tmp_path / "secret.txt"; source.write_text(secret, encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"version": "v1", "gates": {"fixture": {"argv_prefix": ["cat"], "criterion_pattern": "^AC-[0-9]{2,}$"}}, "secret_patterns": json.loads(capture_module.GATE_REGISTRY.read_text())["secret_patterns"]}), encoding="utf-8")
    monkeypatch.setattr(capture_module, "GATE_REGISTRY", registry)
    with pytest.raises(EvidenceRefusal):
        capture(root, "fixture", ["cat", str(source)])
    assert not list((root / "artifacts").rglob("output.log")) if (root / "artifacts").exists() else True
