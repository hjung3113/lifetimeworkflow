"""HOOK-03 commit-gate composition tests (RED-first).

Drives the three composed branches of :mod:`tools.hooks.commit_gate` by monkeypatching the REUSED
built-once assets (D-02) so no live .NET / contract tree is needed:

  * ``run_gate``      (tools.contract_drift.drift)   — contract-drift component
  * ``lint_file``     (tools.polyglot_lint.lint)     — §4.3-4.6 polyglot component (staged files)
  * ``resolve_dotnet``(tools.golden_runner.runner)   — golden-parity gating probe

Invariants proved:
  * drift present -> gate blocks (non-zero); clean tree -> 0.
  * a §4.3-4.6 violation in a staged file -> block, regardless of drift.
  * dotnet absent -> golden-parity SKIP (logged), NOT a failure; drift + polyglot still evaluate,
    so the SKIP can never silently suppress a real block (T-04-13 / D-06).
  * the `--from-hook` Bash matcher engages ONLY on a `git commit` (token-walk classifier), never
    shell-interpolating the untrusted command (T-04-14).
"""

from __future__ import annotations

import json

import pytest

from tools.hooks import commit_gate


@pytest.fixture(autouse=True)
def _no_ambient_approval(monkeypatch) -> None:
    """Strip any ambient ``GOLDEN_APPROVE_HUMAN`` so the drift-block tests are deterministic
    regardless of the session env. A live ratification token (e.g. during an intentional
    constitution change) would otherwise route a drift FAIL through the 05-01 warn+pass path
    and give a false green. The approval-path tests set the token explicitly in their own body,
    which runs after this autouse fixture, so they are unaffected. HARNESS_DEV_BYPASS is stripped
    for the same reason — a dev session's opt-out would otherwise false-green the base block tests.
    """
    monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)
    monkeypatch.delenv("HARNESS_DEV_BYPASS", raising=False)


# --- helpers ------------------------------------------------------------------------------------


def _no_staged(monkeypatch) -> None:
    monkeypatch.setattr(commit_gate, "staged_files", lambda: [])


def _dotnet_absent(monkeypatch) -> None:
    monkeypatch.setattr(commit_gate, "resolve_dotnet", lambda: "/nonexistent/dotnet")


def _clean_drift(monkeypatch) -> None:
    monkeypatch.setattr(commit_gate, "run_gate", lambda *a, **k: {"ok": True, "drifted": []})


def _drift_present(monkeypatch) -> None:
    monkeypatch.setattr(
        commit_gate,
        "run_gate",
        lambda *a, **k: {
            "ok": False,
            "drifted": [("contracts/x.schema.json", "changed", "breaking")],
        },
    )


# --- drift component ----------------------------------------------------------------------------


def test_drift_present_blocks(monkeypatch) -> None:
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)
    assert commit_gate.main([]) != 0


def test_clean_tree_exits_zero(monkeypatch) -> None:
    _clean_drift(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)
    assert commit_gate.main([]) == 0


# --- polyglot component (over a REAL staged file through the real lint_file) ---------------------


def test_polyglot_violation_blocks(monkeypatch, tmp_path, capsys) -> None:
    # A staged TSV with a UTF-8 BOM + CRLF is a §4.3 (R1/R2) violation.
    bad = tmp_path / "wire.tsv"
    bad.write_bytes(b"\xef\xbb\xbfid\tval\r\n1\t2\r\n")

    _clean_drift(monkeypatch)  # drift is clean; the polyglot violation alone must block
    _dotnet_absent(monkeypatch)
    monkeypatch.setattr(commit_gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(commit_gate, "staged_files", lambda: ["wire.tsv"])

    assert commit_gate.main([]) != 0
    err = capsys.readouterr().err
    assert "polyglot" in err


def test_clean_tsv_does_not_block(monkeypatch, tmp_path) -> None:
    good = tmp_path / "wire.tsv"
    good.write_bytes(b"id\tval\n1\t2\n")

    _clean_drift(monkeypatch)
    _dotnet_absent(monkeypatch)
    monkeypatch.setattr(commit_gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(commit_gate, "staged_files", lambda: ["wire.tsv"])

    assert commit_gate.main([]) == 0


# --- golden-parity component: dotnet-absent SKIP (D-06) -----------------------------------------


def test_dotnet_absent_skips_golden_not_fail(monkeypatch, capsys) -> None:
    _clean_drift(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)

    rc = commit_gate.main([])
    combined = capsys.readouterr()
    log = combined.out + combined.err
    assert rc == 0
    assert "SKIP" in log
    assert "golden" in log


def test_golden_skip_does_not_suppress_drift(monkeypatch) -> None:
    # The dotnet-absent SKIP must NOT swallow a real drift block (T-04-13).
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)
    assert commit_gate.main([]) != 0


# --- git-subcommand token-walk classifier (T-04-14) ---------------------------------------------


def test_is_git_subcommand_plain_commit() -> None:
    assert commit_gate.is_git_subcommand("git commit -m 'x'", "commit") is True


def test_is_git_subcommand_ignores_status() -> None:
    assert commit_gate.is_git_subcommand("git status", "commit") is False


def test_is_git_subcommand_skips_env_and_global_flags() -> None:
    cmd = "GIT_AUTHOR_NAME=x git -C /repo commit -m y"
    assert commit_gate.is_git_subcommand(cmd, "commit") is True


def test_is_git_subcommand_fullpath_git() -> None:
    assert commit_gate.is_git_subcommand("/usr/bin/git commit --amend", "commit") is True


def test_is_git_subcommand_not_git() -> None:
    assert commit_gate.is_git_subcommand("echo commit", "commit") is False


# --- --from-hook wrapper ------------------------------------------------------------------------


def test_from_hook_ignores_non_commit(monkeypatch) -> None:
    monkeypatch.setattr(
        commit_gate, "read_stdin", lambda: json.dumps({"tool_input": {"command": "git status"}})
    )
    # Even with drift present, a non-commit command is not gated by the --from-hook matcher.
    _drift_present(monkeypatch)
    assert commit_gate.main(["--from-hook"]) == 0


def test_from_hook_blocks_commit_on_drift(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        commit_gate,
        "read_stdin",
        lambda: json.dumps({"tool_input": {"command": "git commit -m 'x'"}}),
    )
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)

    rc = commit_gate.main(["--from-hook"])
    out = capsys.readouterr().out
    assert rc == 2  # Claude PreToolUse block exit code
    # The block decision is the last stdout line (composition PASS/SKIP lines precede it).
    block_line = [ln for ln in out.splitlines() if ln.strip()][-1]
    assert json.loads(block_line)["decision"] == "block"


# --- D-05 drift approval-path (GOLDEN_APPROVE_HUMAN) ---------------------------------------------
# "Machines gate, humans ratify" — the drift component honors a human-set GOLDEN_APPROVE_HUMAN
# token exactly as contract_guard does (warn+pass), while polyglot/golden stay HARD.


def test_drift_present_with_approval_warns_not_blocks(monkeypatch, capsys) -> None:
    # A non-empty GOLDEN_APPROVE_HUMAN turns a drift FAIL into a logged WARN+PASS (exit 0).
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)
    monkeypatch.setenv("GOLDEN_APPROVE_HUMAN", "yes")

    assert commit_gate.main([]) == 0
    combined = capsys.readouterr()
    log = combined.out + combined.err
    # The drift line reads as a human-ratified WARN, not a FAIL.
    assert "GOLDEN_APPROVE_HUMAN" in log
    assert "ratified" in log
    assert "FAIL [contract-drift]" not in log


def test_drift_present_without_approval_still_blocks(monkeypatch) -> None:
    # No token -> the pre-existing block behavior is unchanged.
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)
    monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)

    assert commit_gate.main([]) != 0


def test_empty_token_does_not_bypass_drift(monkeypatch) -> None:
    # An empty / whitespace-only value never authorizes (mirrors contract_guard Q1).
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)

    for blank in ("", "   "):
        monkeypatch.setenv("GOLDEN_APPROVE_HUMAN", blank)
        assert commit_gate.main([]) != 0


def test_approval_does_not_bypass_polyglot(monkeypatch, tmp_path) -> None:
    # The token weakens drift ONLY: a staged BOM/CRLF TSV still blocks even when approved (T-05-01).
    bad = tmp_path / "wire.tsv"
    bad.write_bytes(b"\xef\xbb\xbfid\tval\r\n1\t2\r\n")

    _clean_drift(monkeypatch)  # drift clean; the polyglot violation alone must block
    _dotnet_absent(monkeypatch)
    monkeypatch.setattr(commit_gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(commit_gate, "staged_files", lambda: ["wire.tsv"])
    monkeypatch.setenv("GOLDEN_APPROVE_HUMAN", "yes")

    assert commit_gate.main([]) != 0


# --- SC5: HARNESS_DEV_BYPASS local-dev opt-out (DRIFT-ONLY, distinct from the token) -------------


def test_drift_present_with_dev_bypass_warns_not_blocks(monkeypatch, capsys) -> None:
    # SC5: the dev flag downgrades a drift FAIL to a distinct WARN (dev) PASS (exit 0).
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)
    monkeypatch.setenv("HARNESS_DEV_BYPASS", "1")

    assert commit_gate.main([]) == 0
    combined = capsys.readouterr()
    log = combined.out + combined.err
    assert "WARN (dev)" in log
    assert "HARNESS_DEV_BYPASS" in log
    assert "ratified" not in log  # distinct from the human-token WARN (ratified) branch
    assert "FAIL [contract-drift]" not in log


def test_drift_present_dev_bypass_unset_still_blocks(monkeypatch) -> None:
    # Secure default: no token AND no dev flag ⇒ drift still blocks.
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)
    monkeypatch.delenv("HARNESS_DEV_BYPASS", raising=False)

    assert commit_gate.main([]) != 0


def test_blank_dev_bypass_does_not_bypass_drift(monkeypatch) -> None:
    # Empty / whitespace-only flag never bypasses (mirrors the token blank-rule).
    _drift_present(monkeypatch)
    _no_staged(monkeypatch)
    _dotnet_absent(monkeypatch)

    for blank in ("", "   "):
        monkeypatch.setenv("HARNESS_DEV_BYPASS", blank)
        assert commit_gate.main([]) != 0


def test_dev_bypass_does_not_bypass_polyglot(monkeypatch, tmp_path) -> None:
    # DRIFT-ONLY: a staged BOM/CRLF TSV still blocks even with the dev flag set (polyglot untouched).
    bad = tmp_path / "wire.tsv"
    bad.write_bytes(b"\xef\xbb\xbfid\tval\r\n1\t2\r\n")

    _clean_drift(monkeypatch)
    _dotnet_absent(monkeypatch)
    monkeypatch.setattr(commit_gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(commit_gate, "staged_files", lambda: ["wire.tsv"])
    monkeypatch.setenv("HARNESS_DEV_BYPASS", "1")

    assert commit_gate.main([]) != 0
