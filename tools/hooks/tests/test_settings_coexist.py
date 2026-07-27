"""Coexistence proof for the Phase-4 gate wiring in ``.claude/settings.json`` (T-04-17/T-04-18).

The four Phase-4 gates (contract_guard, secret_scan, commit_gate PreToolUse; format_on_write
PostToolUse) are APPENDED to a settings.json that already carries GSD's own guards. The single
critical risk is silently clobbering a GSD guard on the shared config edit (Pitfall 1) — so this
test asserts BOTH directions:

  * every pre-existing GSD command substring still resolves in its original event array, and
  * each of the four new gate commands is registered under the correct event array with the
    expected matcher (written RED-first, so an un-wired or mis-wired gate fails loud).

Parsed with stdlib ``json`` only — no harness imports — so it is a pure structural assertion on
the committed live config.
"""

from __future__ import annotations

import json
from pathlib import Path

# test file -> tests -> hooks -> tools -> repo root (parents[3]); mirrors conftest wiring.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SETTINGS = _REPO_ROOT / ".claude" / "settings.json"


def _load() -> dict:
    return json.loads(_SETTINGS.read_text(encoding="utf-8"))


def _commands(hooks: dict, event: str) -> list[str]:
    """All command strings registered under ``event`` (flattened across matcher slots)."""
    commands: list[str] = []
    for slot in hooks.get(event, []):
        for hook in slot.get("hooks", []):
            if hook.get("type") == "command":
                commands.append(hook.get("command", ""))
    return commands


def _slots_with_command(hooks: dict, event: str, needle: str) -> list[dict]:
    """Every slot under ``event`` whose command contains ``needle`` (matcher preserved)."""
    matches: list[dict] = []
    for slot in hooks.get(event, []):
        for hook in slot.get("hooks", []):
            if needle in hook.get("command", ""):
                matches.append(slot)
                break
    return matches


# --- pre-existing GSD guards must survive the append (Pitfall 1 / T-04-17) ----------------------

# (event, command-substring) for every GSD guard that MUST still be present after the edit.
_GSD_GUARDS = [
    ("SessionStart", "gsd-check-update"),
    ("SessionStart", "gsd-session-state"),
    ("SessionStart", "bootstrap/install.sh"),
    ("SessionStart", "memory-inject"),
    ("PreToolUse", "gsd-prompt-guard"),
    ("PreToolUse", "gsd-read-guard"),
    ("PreToolUse", "gsd-workflow-guard"),
    ("PreToolUse", "gsd-validate-commit"),
    ("PostToolUse", "gsd-context-monitor"),
    ("PostToolUse", "gsd-read-injection-scanner"),
    ("PostToolUse", "gsd-phase-boundary"),
]


def test_all_eleven_gsd_guards_survive() -> None:
    hooks = _load()["hooks"]
    for event, needle in _GSD_GUARDS:
        commands = _commands(hooks, event)
        assert any(needle in cmd for cmd in commands), (
            f"GSD guard '{needle}' missing from {event} — a Phase-4 append clobbered it (Pitfall 1)"
        )


# --- harness gates are wired under the correct event array + matcher ------------------------------

# (event, command-substring, expected-matcher) for each appended Phase-4 gate.
_NEW_GATES = [
    ("PreToolUse", "tools.hooks.contract_guard", "Write|Edit"),
    ("PreToolUse", "tools.hooks.secret_scan", "Read|Write|Edit"),
    ("PreToolUse", "tools.hooks.commit_gate", "Bash"),
    ("PostToolUse", "tools.hooks.format_on_write", "Write|Edit"),
]


def test_harness_gates_registered_with_expected_matcher() -> None:
    hooks = _load()["hooks"]
    for event, needle, matcher in _NEW_GATES:
        slots = _slots_with_command(hooks, event, needle)
        assert slots, f"new gate '{needle}' is not registered under {event} (enforcement gap)"
        matchers = {slot.get("matcher") for slot in slots}
        assert matcher in matchers, (
            f"new gate '{needle}' under {event} has matcher {matchers}, expected '{matcher}'"
        )


def test_commit_gate_runs_from_hook() -> None:
    """The commit_gate PreToolUse slot must invoke the ``--from-hook`` Bash-stdin wrapper."""
    hooks = _load()["hooks"]
    commands = _commands(hooks, "PreToolUse")
    commit_cmds = [c for c in commands if "tools.hooks.commit_gate" in c]
    assert commit_cmds, "commit_gate not wired into PreToolUse"
    assert any("--from-hook" in c for c in commit_cmds), (
        "commit_gate must run with --from-hook so it reads the Bash stdin and gates git commit"
    )


def test_expected_slot_counts() -> None:
    """7 PreToolUse (4 GSD + 3 harness) and 4 PostToolUse (3 GSD + 1 harness)."""
    hooks = _load()["hooks"]
    assert len(hooks["PreToolUse"]) == 7, "expected 7 PreToolUse slots (4 GSD + 3 harness gates)"
    assert len(hooks["PostToolUse"]) == 4, "expected 4 PostToolUse slots (3 GSD + 1 new gate)"
