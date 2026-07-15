"""RED->GREEN unit proof for the shared Claude hook-stdin adapter (Phase-4).

The adapter is the single seam every Phase-4 gate uses to (a) parse Claude's untrusted
PreToolUse JSON into a typed record and (b) emit a well-formed decision back. Defensive parse
(T-04-05 DoS): malformed/empty stdin must NOT raise — it yields a safe sentinel that maps to
"no decision" so a broken payload never crashes the gate (which would let the tool proceed
unguarded).
"""

from __future__ import annotations

import dataclasses

import pytest

from tools.hooks._stdin import DEV_BYPASS_ENV, Event, dev_bypassed, emit_block, emit_deny, parse_event


def test_dev_bypassed_for_nonblank_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DEV_BYPASS_ENV, "1")
    assert dev_bypassed() is True


@pytest.mark.parametrize("value", [None, "", "   ", "\t\n"])
def test_dev_bypassed_false_for_unset_or_blank(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(DEV_BYPASS_ENV, raising=False)
    else:
        monkeypatch.setenv(DEV_BYPASS_ENV, value)
    assert dev_bypassed() is False

# --- parse_event: crafted PreToolUse event -> typed record --------------------------------------


def test_parse_event_extracts_fields() -> None:
    text = (
        '{"session_id":"s1","hook_event_name":"PreToolUse","cwd":"/repo",'
        '"tool_name":"Write","tool_input":{"file_path":"src/x.py","content":"body"}}'
    )
    ev = parse_event(text)
    assert ev.tool_name == "Write"
    assert ev.file_path == "src/x.py"
    assert ev.content == "body"
    assert ev.session_id == "s1"
    assert ev.cwd == "/repo"


def test_parse_event_bash_command_field() -> None:
    text = '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}'
    ev = parse_event(text)
    assert ev.tool_name == "Bash"
    assert ev.command == "rm -rf /"
    # Absent optional fields default to "" (never None, never raise).
    assert ev.file_path == ""
    assert ev.content == ""


def test_parse_event_missing_keys_default_to_empty_string() -> None:
    ev = parse_event("{}")
    assert ev.tool_name == ""
    assert ev.file_path == ""
    assert ev.content == ""
    assert ev.command == ""
    assert ev.cwd == ""
    assert ev.session_id == ""


def test_event_is_frozen() -> None:
    ev = parse_event('{"tool_name":"Read"}')
    assert isinstance(ev, Event)
    with_raises = False
    try:
        ev.tool_name = "Write"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        with_raises = True
    assert with_raises


# --- defensive parse: malformed / empty stdin -> safe sentinel (T-04-05) ------------------------


def test_parse_event_malformed_json_is_safe_sentinel() -> None:
    ev = parse_event("{not json at all")
    # Sentinel: every field empty -> maps to "no decision" downstream. Must not raise.
    assert ev.tool_name == ""
    assert ev.file_path == ""
    assert ev.content == ""


def test_parse_event_empty_string_is_safe_sentinel() -> None:
    ev = parse_event("")
    assert ev.tool_name == ""
    assert ev.file_path == ""


def test_parse_event_non_object_json_is_safe_sentinel() -> None:
    # Valid JSON but not an object (e.g. a bare list/number) must not crash on .get().
    ev = parse_event("[1, 2, 3]")
    assert ev.tool_name == ""
    ev2 = parse_event("42")
    assert ev2.tool_name == ""


# --- emit_deny / emit_block: exact decision shapes ----------------------------------------------


def test_emit_deny_is_pretooluse_permission_decision_shape() -> None:
    out = emit_deny("secret detected")
    assert out == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "secret detected",
        }
    }


def test_emit_block_is_top_level_decision_shape() -> None:
    out = emit_block("blocked reason")
    assert out == {"decision": "block", "reason": "blocked reason"}
