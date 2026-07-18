from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tools.evidence.capture import EvidenceError, EvidenceRefusal, capture, validate_evidence


def packet(tmp_path: Path) -> Path:
    root = tmp_path / "T-20260719000000-fixture"
    root.mkdir()
    (root / "evidence.json").write_text(json.dumps({
        "task_id": "T-20260719000000-fixture",
        "gate_runs": [],
        "findings": [],
        "redaction_report": {"status": "CLEAR", "refused_fields": []},
    }), encoding="utf-8")
    return root


@pytest.mark.parametrize(("marker", "exit_code", "expected"), [
    ("PASS", 0, "PASSED"), ("FAIL", 7, "FAILED"), ("SKIP: absent", 0, "SKIPPED"), ("BLOCKED: waiting", 0, "BLOCKED"),
])
def test_capture_round_trips_observed_statuses(tmp_path: Path, marker: str, exit_code: int, expected: str) -> None:
    root = packet(tmp_path)
    record = capture(root, "fixture", [sys.executable, "-c", f"print({marker!r}); raise SystemExit({exit_code})"])
    assert record["status"] == expected
    assert record["status"] != "PASSED" or exit_code == 0
    assert validate_evidence(root)["gate_runs"][0]["status"] == expected


def test_hash_tamper_and_missing_artifact_fail_validation(tmp_path: Path) -> None:
    root = packet(tmp_path)
    record = capture(root, "fixture", [sys.executable, "-c", "print('PASS')"])
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
    evidence["gate_runs"] = [{"id": "E-01", "gate": "fixture", "status": "PASSED", "criterion_ids": [], "finding_ids": [], "artifact": {"path": "artifacts/fixture/E-01/output.log", "summary": "forged", "sha256": "0" * 64}}]
    (root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(EvidenceError, match="missing artifact"):
        validate_evidence(root)


def test_sensitive_output_is_refused_without_plaintext_artifact(tmp_path: Path) -> None:
    root = packet(tmp_path)
    with pytest.raises(EvidenceRefusal):
        capture(root, "fixture", [sys.executable, "-c", "print('password=super-secret-value')"])
    contents = "\n".join(path.read_text(errors="ignore") for path in root.rglob("*") if path.is_file())
    assert "super-secret-value" not in contents
    report = json.loads((root / "evidence.json").read_text())["redaction_report"]
    assert report == {"status": "REFUSED", "refused_fields": ["argv"]}
