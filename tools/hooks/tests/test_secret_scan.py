"""RED->GREEN proof for the HOOK-02 secret_scan PreToolUse gate.

Denies a write/read that carries secret material — either by PATH (``*.env``, via the reused
CONFIG-02 resolver over a SECRET-SPECIFIC glob subset) or by CONTENT (shape-anchored regex:
AWS access key, PEM private-key header, conservative assignment shape). A tests/golden/
normalize-fixtures allow-list prevents the repo's own high-entropy fixtures from tripping the
gate (Pitfall 5 / T-04-04).

Composition invariant (04-06, Blocker-1 fix): secret_scan must NOT deny the constitution plane
(``contracts/**``, ``docs/adr/**``, ``golden/**``). That plane is contract-guard's gate (04-03),
which honors the GOLDEN_APPROVE_HUMAN bypass. If secret_scan denied the full ``path_deny_globs``,
any-deny-wins aggregation would shadow that bypass. So it feeds the resolver only
``SECRET_PATH_GLOBS = ["*.env", "**/*.env"]`` — a constitution path with NO secret content is
allowed here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.hooks.secret_scan import decide

_REPO_ROOT = Path(__file__).resolve().parents[3]

# Realistic-shape but non-live sample values (AWS's documented example key; a fake PEM header).
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
PEM_HEADER = "-----BEGIN RSA PRIVATE KEY-----"


# --- decide(): content patterns (deny) ----------------------------------------------------------


def test_aws_access_key_in_write_denied() -> None:
    out = decide("src/config.py", f"aws_key = {AWS_KEY}")
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pem_private_key_header_denied() -> None:
    out = decide("src/id_rsa", f"{PEM_HEADER}\nMIIEpAIBAAKCAQEA...\n")
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_assignment_shape_secret_denied() -> None:
    out = decide("src/settings.py", 'api_key = "s3cr3tVALUE0123456789abcdef"')
    assert out is not None


# --- decide(): *.env path deny via reused resolver over SECRET subset ----------------------------


def test_dotenv_path_denied_even_without_secret_content() -> None:
    # Path-based deny: a *.env target is denied on path alone (resolver over SECRET_PATH_GLOBS).
    out = decide("config/prod.env", "PLAIN=notasecret")
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_nested_dotenv_path_denied() -> None:
    out = decide("components/collector/.env", "X=1")
    assert out is not None


# --- decide(): allow-list prevents fixture false positives (Pitfall 5 / T-04-04) -----------------


def test_benign_fixture_under_tests_allowed() -> None:
    # Same AWS-key shape, but under tests/ -> allow-listed -> no decision.
    assert decide("tests/fixtures/blob.json", AWS_KEY) is None


def test_benign_fixture_under_golden_allowed() -> None:
    assert decide("golden/case/expected/x.tsv", AWS_KEY) is None


def test_benign_fixture_under_normalize_fixtures_allowed() -> None:
    assert decide("libs/normalize-fixtures/sample.txt", PEM_HEADER) is None


def test_golden_approve_human_token_not_flagged() -> None:
    # The bypass token appearing in a test file must not be treated as a secret.
    assert decide("tools/hooks/tests/test_x.py", "GOLDEN_APPROVE_HUMAN") is None


# --- composition invariant: constitution plane is NOT secret_scan's gate (04-06) ----------------


def test_constitution_schema_no_secret_not_denied() -> None:
    # contracts/** is contract-guard's plane (+ its bypass). secret_scan must not shadow it.
    assert decide("contracts/log-specs/x.schema.json", "{}") is None


def test_constitution_adr_no_secret_not_denied() -> None:
    assert decide("docs/adr/0002-something.md", "# ADR\nplain prose") is None


def test_constitution_golden_no_secret_not_denied() -> None:
    assert decide("golden/case/expected/x.tsv", "col1\tcol2\n") is None


def test_benign_source_file_allowed() -> None:
    assert decide("libs/python/foo.py", "def f():\n    return 1\n") is None


# --- main(): stdin -> deny JSON on hit, silent allow otherwise -----------------------------------


def _run_main(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "tools.hooks.secret_scan"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


def test_main_denies_real_secret_exit0_json() -> None:
    proc = _run_main(
        {"tool_name": "Write", "tool_input": {"file_path": "src/x.py", "content": f"k={AWS_KEY}"}}
    )
    assert proc.returncode == 0
    assert '"permissionDecision": "deny"' in proc.stdout or '"permissionDecision":"deny"' in proc.stdout


def test_main_allowlisted_fixture_silent() -> None:
    proc = _run_main(
        {"tool_name": "Write", "tool_input": {"file_path": "tests/fixtures/blob.json", "content": AWS_KEY}}
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_main_constitution_plane_silent() -> None:
    proc = _run_main(
        {"tool_name": "Write", "tool_input": {"file_path": "contracts/x.schema.json", "content": "{}"}}
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
