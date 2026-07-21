from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import pytest

import tools.evidence.capture as capture_module
from tools.evidence.capture import (
    EvidenceError,
    EvidenceRefusal,
    add_finding,
    capture,
    validate_evidence,
)


def packet(tmp_path: Path) -> Path:
    root = tmp_path / "T-20260719000000-fixture"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "evidence.json").write_text(
        json.dumps(
            {
                "task_id": "T-20260719000000-fixture",
                "gate_runs": [],
                "findings": [],
                "redaction_report": {"status": "CLEAR", "refused_fields": []},
            }
        ),
        encoding="utf-8",
    )
    (root / "task.json").write_text(
        json.dumps(
            {"task_id": "T-20260719000000-fixture", "acceptance_criteria": [], "constraints": []}
        ),
        encoding="utf-8",
    )
    (root / "state.json").write_text(
        json.dumps(
            {
                "task_id": "T-20260719000000-fixture",
                "phase": "INTAKE",
                "revision": 0,
                "baseline": {"repo_root": ".", "commit": "0" * 40},
                "current_ref": "0" * 40,
                "completed_items": [],
                "next_action": "test",
                "blockers": [],
                "transition": None,
            }
        ),
        encoding="utf-8",
    )
    return root


def fake_tests_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        capture_module,
        "subprocess",
        types.SimpleNamespace(
            run=lambda *args, **kwargs: __import__("subprocess").CompletedProcess(
                args[0], 0, "PASS\n", ""
            ),
        ),
    )


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("print('PASS')", "PASSED"),
        ("print('SKIP: absent')", "SKIPPED"),
        ("print('BLOCKED: waiting')", "BLOCKED"),
        ("raise SystemExit(7)", "FAILED"),
    ],
)
def test_capture_round_trips_observed_statuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str, expected: str
) -> None:
    root = packet(tmp_path)
    script = tmp_path / "gate.py"
    script.write_text(textwrap.dedent(body), encoding="utf-8")
    registry = tmp_path / "registry.json"
    command = [sys.executable, str(script)]
    registry.write_text(
        json.dumps(
            {
                "version": "v1",
                "gates": {"fixture": {"argv": command, "criterion_pattern": "^AC-[0-9]{2,}$"}},
                "secret_patterns": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(capture_module, "GATE_REGISTRY", registry)
    assert capture(root, "fixture", command)["status"] == expected


def test_sensitive_pattern_case_diversity_survives_ignorecase() -> None:
    """CR-01, evidence-capture path: [A-Z]/[a-z] lookaheads immune to re.IGNORECASE.

    Mirrors scan.py's sibling test with a byte-identical fixture literal so a future divergence
    between the two consumers' behavior on the same input is itself a new defect this suite
    would catch.
    """
    assign = "pass" + "word"
    value_all_upper = "".join(["ABCDEFGHIJKLMNOPQRST"])
    assert capture_module._sensitive_pattern().search(assign + ": " + value_all_upper) is None


@pytest.mark.parametrize(
    "fixture_value",
    [
        pytest.param(
            "".join(["AbCdEfGhIjKlMnOpQrSt"]),
            id="mixed_case_digit_less-red_before_task2-WR01_relaxation_proof",
        ),
        pytest.param(
            "".join(["ABCDEFGHIJKLMNO", "12345"]),
            id="uppercase_plus_digit-continuity_guard",
        ),
        pytest.param(
            "".join(["abcdefghijklmno", "12345"]),
            id="lowercase_plus_digit-continuity_guard",
        ),
    ],
)
def test_sensitive_pattern_two_of_three_classes_matches(fixture_value: str) -> None:
    """SC-2 mirror: 2-of-3 charset-class disposition against the redaction-path consumer.

    Mirrors scan.py's sibling test byte-for-byte; the mixed-case-digit-less row is expected to
    FAIL (red) until Task 2 lands the fix.
    """
    sec = "se" + "cret"
    assert capture_module._sensitive_pattern().search(sec + ": " + fixture_value), fixture_value


@pytest.mark.parametrize(
    "fixture_value",
    [
        "".join(["correcthorsebattery", "staple"]),
        "9" * 22,
        "".join(["ABCDEFGHIJKLMNOPQRST"]),
    ],
)
def test_sensitive_pattern_single_class_digit_less_remains_excluded(fixture_value: str) -> None:
    """SC-2 mirror: single-case-only and all-numeric digit-less values remain an accepted,
    documented residual gap on the redaction-path consumer too."""
    assign = "pass" + "word"
    assert capture_module._sensitive_pattern().search(assign + ": " + fixture_value) is None


def test_hash_tamper_and_missing_artifact_fail_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = packet(tmp_path)
    fake_tests_command(monkeypatch)
    record = capture(root, "tests", ["uv", "run", "pytest"])
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
    evidence["gate_runs"] = [
        {
            "id": "E-01",
            "gate": "tests",
            "status": "PASSED",
            "criterion_ids": [],
            "finding_ids": [],
            "argv": ["uv", "run", "pytest"],
            "cwd": root.as_posix(),
            "exit_code": 0,
            "gate_version": "v1",
            "started_at": "2026-07-19T00:00:00Z",
            "ended_at": "2026-07-19T00:00:00Z",
            "source": "local",
            "artifact": {
                "path": "artifacts/tests/E-01/output.log",
                "summary": "forged",
                "sha256": "0" * 64,
            },
        }
    ]
    (root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(EvidenceError, match="integrity anchor mismatch"):
        validate_evidence(root)


def test_sensitive_output_is_refused_without_plaintext_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Fixture value is 20+ chars with upper/lower/digit charset diversity — must satisfy the
    # tightened generic secret_patterns[1] gate (26.1: min-20 + 3-way charset diversity), not
    # just be a plausible-looking password string.
    root = packet(tmp_path)
    registry = tmp_path / "registry.json"
    command = ["uv", "run", "pytest", "-c", "password=Sup3rSecretValue1234567890"]
    registry.write_text(
        json.dumps(
            {
                "version": "v1",
                "gates": {"fixture": {"argv": command, "criterion_pattern": "^AC-[0-9]{2,}$"}},
                "secret_patterns": json.loads(capture_module.GATE_REGISTRY.read_text())[
                    "secret_patterns"
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(capture_module, "GATE_REGISTRY", registry)
    with pytest.raises(EvidenceRefusal):
        capture(root, "fixture", command)
    contents = "\n".join(
        path.read_text(errors="ignore") for path in root.rglob("*") if path.is_file()
    )
    assert "Sup3rSecretValue1234567890" not in contents
    report = json.loads((root / "evidence.json").read_text())["redaction_report"]
    assert report == {"status": "REFUSED", "refused_fields": ["argv"]}


def test_forged_consistent_pass_is_rejected_by_record_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = packet(tmp_path)
    fake_tests_command(monkeypatch)
    record = capture(root, "tests", ["uv", "run", "pytest"])
    artifact = root / record["artifact"]["path"]
    evidence = json.loads((root / "evidence.json").read_text())
    evidence["gate_runs"][0]["status"] = "PASSED"
    evidence["gate_runs"][0]["exit_code"] = 0
    evidence["gate_runs"][0]["artifact"]["sha256"] = (
        __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
    )
    evidence["gate_runs"][0]["artifact"]["summary"] = "forged, but internally consistent"
    (root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(EvidenceError, match="integrity anchor mismatch"):
        validate_evidence(root)


def test_direct_anchor_edit_without_cas_revision_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = packet(tmp_path)
    fake_tests_command(monkeypatch)
    capture(root, "tests", ["uv", "run", "pytest"])
    state = json.loads((root / "state.json").read_text())
    state["evidence_integrity"]["state_revision"] = state["revision"] + 1
    # An out-of-band state write leaves the lifecycle revision unchanged.
    (root / "state.json").write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(EvidenceError, match="integrity anchor mismatch"):
        validate_evidence(root)


def test_same_revision_anchor_rewrite_is_rejected_at_head_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A same-revision rewrite is advisory in-session, but cannot cross COMPLETE's HEAD boundary."""
    root = packet(tmp_path)
    fake_tests_command(monkeypatch)
    capture(root, "tests", ["uv", "run", "pytest"])
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True
    )
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "evidence.json"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "trusted-evidence"], check=True)
    evidence = json.loads((root / "evidence.json").read_text())
    evidence["gate_runs"][0]["artifact"]["summary"] = "same-revision forged rewrite"
    state = json.loads((root / "state.json").read_text())
    state["evidence_integrity"]["evidence_sha256"] = capture_module._digest(evidence)
    state["evidence_integrity"]["run_hashes"] = {
        "E-01": capture_module._digest(evidence["gate_runs"][0])
    }
    (root / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    (root / "state.json").write_text(json.dumps(state), encoding="utf-8")
    validate_evidence(root)
    from tools.task_control.manager import _evidence_matches_head

    assert not _evidence_matches_head(root)


def test_capture_forces_task_repository_cwd_and_strips_gate_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = packet(tmp_path)
    planted = tmp_path / "planted"
    planted.mkdir()
    script = tmp_path / "context.py"
    script.write_text(
        "import os\nfrom pathlib import Path\nprint(Path.cwd())\nprint(os.getenv('PYTEST_ADDOPTS', ''))\nprint(os.getenv('RUFF_OUTPUT_FORMAT', ''))\n",
        encoding="utf-8",
    )
    command = [sys.executable, str(script)]
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "version": "v1",
                "gates": {"fixture": {"argv": command, "criterion_pattern": "^AC-[0-9]{2,}$"}},
                "secret_patterns": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(capture_module, "GATE_REGISTRY", registry)
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("RUFF_OUTPUT_FORMAT", "concise")
    monkeypatch.chdir(planted)
    record = capture(root, "fixture", command)
    assert record["cwd"] == root.as_posix()
    assert (root / record["artifact"]["path"]).read_text(encoding="utf-8").splitlines()[:3] == [
        root.as_posix(),
        "",
        "",
    ]


def test_unregistered_argv_and_sensitive_finding_are_refused(tmp_path: Path) -> None:
    root = packet(tmp_path)
    with pytest.raises(EvidenceError, match="argv is not allowed"):
        capture(root, "tests", ["true"])
    for gate, no_op in (
        ("tests", ["uv", "run", "pytest", "--version"]),
        ("tests", ["uv", "run", "pytest", "--collect-only"]),
        ("lint", ["ruff", "check", ".", "--exit-zero"]),
    ):
        with pytest.raises(EvidenceError, match="argv is not allowed"):
            capture(root, gate, no_op)
    with pytest.raises(EvidenceRefusal):
        add_finding(
            root,
            {
                "id": "F-01",
                "summary": "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
                "constraint_ids": [],
                "severity": "minor",
                "disposition": "open",
            },
        )


@pytest.mark.parametrize(
    "secret",
    [
        "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        "sk-abcdefghijklmnopqrstuvwxyz012345",
        "xoxb-123456-token",
        "-----BEGIN PRIVATE KEY-----",
        "eyJabcde12345.payload.signature",
        "Authorization: Bearer abcdef",
        "aB3dE5fG7hI9jK1mN2pQ4rS6tU8vW0xY/z+=AbCd",
    ],
)
def test_sensitive_stdout_patterns_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, secret: str
) -> None:
    root = packet(tmp_path)
    source = tmp_path / "secret.txt"
    source.write_text(secret, encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "version": "v1",
                "gates": {
                    "fixture": {"argv": ["cat", str(source)], "criterion_pattern": "^AC-[0-9]{2,}$"}
                },
                "secret_patterns": json.loads(capture_module.GATE_REGISTRY.read_text())[
                    "secret_patterns"
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(capture_module, "GATE_REGISTRY", registry)
    with pytest.raises(EvidenceRefusal):
        capture(root, "fixture", ["cat", str(source)])
    assert (
        not list((root / "artifacts").rglob("output.log"))
        if (root / "artifacts").exists()
        else True
    )


def test_git_sha_in_output_is_not_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = packet(tmp_path)
    source = tmp_path / "sha.txt"
    source.write_text("a" * 40, encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "version": "v1",
                "gates": {
                    "fixture": {"argv": ["cat", str(source)], "criterion_pattern": "^AC-[0-9]{2,}$"}
                },
                "secret_patterns": json.loads(capture_module.GATE_REGISTRY.read_text())[
                    "secret_patterns"
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(capture_module, "GATE_REGISTRY", registry)
    assert capture(root, "fixture", ["cat", str(source)])["status"] == "PASSED"
