"""The guard-command PREFIX must lighten dev and survive a broken workspace WITHOUT ever weakening a
real deny. That last clause is the whole risk: a degrade that fires on a genuine refusal would
silently disable every constitution/secret/ledger guard — the exact "claimed control that does not
exist" this repo exists to prevent. So each branch is proven by execution, and the deny-preservation
branch is proven adversarially.

The prefix (``merge._GUARD_PREFIX``) has two clauses, ahead of ``uv run python -m tools.hooks.<x>``:

    [ -n "$HARNESS_DEV_LIGHT" ] && exit 0;                                  # dev opt-out
    python3 tools/harness_lint/workspace_check.py >/dev/null 2>&1 || exit 0; # infra degrade

Three behaviours, three tests, plus the structural check that every guard actually carries it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.harness_emit import merge

REPO_ROOT = Path(__file__).resolve().parents[3]

_CONSTITUTION_WRITE = (
    '{"tool_name":"Write","tool_input":{"file_path":"contracts/x.json","content":"{}"}}'
)


def _run_prefixed(
    command: str, *, env_extra: dict[str, str], stdin: str = ""
) -> subprocess.CompletedProcess:
    """Run a full prefixed guard command through bash from the repo root, with a controlled env.

    The constitution-plane bypasses are stripped unless env_extra re-adds them, so a deny is the
    guard's real decision, not an inherited session token.
    """
    import os

    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("HARNESS_DEV_BYPASS", "HARNESS_DEV_LIGHT", "GOLDEN_APPROVE_HUMAN")
    }
    env.update(env_extra)
    return subprocess.run(
        ["bash", "-c", command],
        cwd=REPO_ROOT,
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )


def _contract_guard_command() -> str:
    """The exact emitted PreToolUse contract_guard command (prefix + guard)."""
    for group in merge.HARNESS_HOOK_GROUPS["PreToolUse"]:
        for hook in group["hooks"]:
            if "tools.hooks.contract_guard" in hook["command"]:
                return hook["command"]
    raise AssertionError("contract_guard command not found in HARNESS_HOOK_GROUPS")


def test_every_guard_command_carries_the_prefix() -> None:
    """Structural: no guard is emitted without the degrade/opt-out prefix.

    Without it a guard can still deadlock the session on a broken workspace.
    """
    naked: list[str] = []
    for event in ("PreToolUse", "PostToolUse"):
        for group in merge.HARNESS_HOOK_GROUPS[event]:
            for hook in group["hooks"]:
                cmd = hook["command"]
                if "tools.hooks." in cmd and not cmd.startswith(merge._GUARD_PREFIX):
                    naked.append(cmd)
    assert naked == [], f"these guard commands lack _GUARD_PREFIX and can still deadlock: {naked}"


def test_real_deny_is_preserved_on_a_healthy_workspace() -> None:
    """ADVERSARIAL — the load-bearing test. Healthy workspace, no bypass, no dev-light: the prefix
    must run the guard and the guard must still DENY a constitution write. If this ever passes to
    'allow', the degrade has eaten a real refusal and every guard is inert."""
    result = _run_prefixed(_contract_guard_command(), env_extra={}, stdin=_CONSTITUTION_WRITE)
    assert '"permissionDecision": "deny"' in result.stdout, (
        "the guard DID NOT deny a constitution write through the prefix — the degrade or opt-out "
        f"clause is firing when it must not. stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_dev_light_skips_the_guard_entirely() -> None:
    """HARNESS_DEV_LIGHT set → clause 1 exits 0 before uv is ever invoked → allow, no guard run."""
    result = _run_prefixed(
        _contract_guard_command(), env_extra={"HARNESS_DEV_LIGHT": "1"}, stdin=_CONSTITUTION_WRITE
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "", (
        f"dev-light must produce a silent allow (no guard output), got: {result.stdout!r}"
    )


def test_broken_workspace_degrades_to_allow(tmp_path: Path) -> None:
    """A tools/* member with no pyproject makes uv unresolvable. Clause 2's bare-python3 check must
    fire and the prefix must exit 0 (allow) instead of the guard dying and blocking the tool.

    Simulated hermetically: a throwaway repo shape with a broken member, running only clause 2's
    logic against it, so the real repo is never broken by the test."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["tools/*"]\n', encoding="utf-8"
    )
    broken = tmp_path / "tools" / "broken"
    broken.mkdir(parents=True)
    (broken / "mod.py").write_text("x = 1\n", encoding="utf-8")

    check = REPO_ROOT / "tools" / "harness_lint" / "workspace_check.py"
    # Clause 2 verbatim: `check || exit 0` — a non-zero check means the guard is skipped (allow).
    command = f'python3 "{check}" "{tmp_path}" >/dev/null 2>&1 || exit 0; echo "GUARD_RAN"'
    result = subprocess.run(["bash", "-c", command], capture_output=True, text=True)
    assert result.returncode == 0
    assert "GUARD_RAN" not in result.stdout, (
        "the guard ran against a broken workspace — clause 2 did not degrade, so the session would "
        "have deadlocked"
    )


def test_workspace_check_is_the_degrade_oracle_and_is_uv_free() -> None:
    """Clause 2 relies on workspace_check running WITHOUT uv (that is the point — uv is what's
    broken). Prove it imports nothing from a uv-only path by running it on bare python3."""
    check = REPO_ROOT / "tools" / "harness_lint" / "workspace_check.py"
    result = subprocess.run(
        [sys.executable, str(check)], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, (
        f"workspace_check must pass on the healthy repo: {result.stderr!r}"
    )
