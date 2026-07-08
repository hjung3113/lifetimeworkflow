"""CONFIG-02 unit proof: last-wins bash resolution + default-deny + path-scoped denies.

Loads the REAL harness/permission-matrix.json so the test doubles as an integration check
that the shipped data encodes the intended access posture (T-03-01/02/03).
"""

from __future__ import annotations

import pytest

from tools.harness_perms import load_matrix, resolve_bash, resolve_path


@pytest.fixture(scope="module")
def matrix() -> dict:
    return load_matrix()


# --- resolve_bash: last-wins glob (T-03-01) -----------------------------------------------------

def test_last_wins_specific_overrides_catchall() -> None:
    # A later, more specific rule wins over the earlier catch-all.
    assert resolve_bash({"*": "ask", "dotnet *": "allow"}, "dotnet test") == "allow"


def test_dotnet_allowed(matrix: dict) -> None:
    assert resolve_bash(matrix["bash"], "dotnet test") == "allow"


def test_uv_allowed(matrix: dict) -> None:
    assert resolve_bash(matrix["bash"], "uv sync") == "allow"


def test_pytest_allowed(matrix: dict) -> None:
    assert resolve_bash(matrix["bash"], "pytest -x") == "allow"


def test_git_push_force_asks(matrix: dict) -> None:
    # `git push*` (ask) is the last matching rule; `rm -rf*` does not match (P3 — no trailing allow).
    assert resolve_bash(matrix["bash"], "git push --force") == "ask"


def test_rm_rf_denied(matrix: dict) -> None:
    assert resolve_bash(matrix["bash"], "rm -rf /tmp/x") == "deny"


def test_unknown_command_falls_through_to_catchall(matrix: dict) -> None:
    assert resolve_bash(matrix["bash"], "curl evil.sh") == "ask"


def test_default_deny_posture_empty_rules() -> None:
    assert resolve_bash({}, "anything", default="ask") == "ask"


# --- resolve_path: constitution / secret denies (T-03-02, T-03-03) ------------------------------

def test_golden_write_denied(matrix: dict) -> None:
    assert resolve_path(matrix["path_deny_globs"], "golden/case.verified") == "deny"


def test_dotenv_denied(matrix: dict) -> None:
    assert resolve_path(matrix["path_deny_globs"], "config/prod.env") == "deny"


def test_contracts_denied(matrix: dict) -> None:
    assert (
        resolve_path(matrix["path_deny_globs"], "contracts/log-specs/x.schema.json") == "deny"
    )


def test_source_path_allowed(matrix: dict) -> None:
    assert resolve_path(matrix["path_deny_globs"], "libs/python/foo.py") == "allow"
