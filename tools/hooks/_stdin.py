"""Shared Claude hook-stdin adapter for the Phase-4 gates (thin, stdlib-only).

Every Phase-4 gate (secret_scan here; contract-guard / boundary / stop gates in plans 03-05)
uses this one seam to translate Claude's untrusted hook stdin JSON into a typed record and back
into a decision. Keeping it in `_stdin` means the gate modules never re-implement JSON plumbing
and the plans can add sibling modules without touching each other's files.

Verified PreToolUse stdin fields (04-RESEARCH Pattern 2)::

    { "session_id":"…", "hook_event_name":"PreToolUse", "cwd":"…",
      "tool_name":"Write|Edit|Read|Bash",
      "tool_input": { "file_path":"…", "content":"…", "command":"…" } }

Two decision shapes:
  * PreToolUse: ``{"hookSpecificOutput":{"hookEventName":"PreToolUse",
    "permissionDecision":"deny","permissionDecisionReason":…}}``  (``emit_deny``)
  * PostToolUse / Stop: top-level ``{"decision":"block","reason":…}``  (``emit_block``)

Security (T-04-05, §Security Domain V5): stdin is untrusted. ``parse_event`` and ``read_stdin``
wrap all parsing in try/except and default to a SAFE SENTINEL (every field ``""``) rather than
raising — a malformed payload must never crash the gate, because a crashed gate would let the
guarded tool proceed unguarded. The sentinel maps to "no decision" downstream; individual gates
choose fail-open vs fail-closed on top of it.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    """Immutable, typed view of a Claude hook stdin event.

    All fields are plain strings; absent/optional fields are ``""`` (never ``None``) so gate code
    can pattern-match without None-guards. A frozen dataclass makes the parsed event tamper-proof
    as it flows through a gate.
    """

    tool_name: str = ""
    file_path: str = ""
    content: str = ""
    command: str = ""
    cwd: str = ""
    session_id: str = ""


def parse_event(text: str) -> Event:
    """Parse Claude hook stdin JSON ``text`` into an :class:`Event`, defensively (T-04-05).

    Missing keys default to ``""``. Malformed JSON, empty input, or a non-object top-level value
    (bare list/number) all yield the safe sentinel ``Event()`` instead of raising.
    """
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return Event()
    if not isinstance(data, dict):
        return Event()

    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    def _s(mapping: dict, key: str) -> str:
        value = mapping.get(key, "")
        return value if isinstance(value, str) else ""

    return Event(
        tool_name=_s(data, "tool_name"),
        file_path=_s(tool_input, "file_path"),
        content=_s(tool_input, "content"),
        command=_s(tool_input, "command"),
        cwd=_s(data, "cwd"),
        session_id=_s(data, "session_id"),
    )


def read_stdin() -> str:
    """Read all of stdin, swallowing read errors into ``""`` (fail-safe for the adapter itself)."""
    try:
        return sys.stdin.read()
    except (OSError, ValueError):
        return ""


def emit_deny(reason: str) -> dict:
    """PreToolUse deny decision (exit 0 + this dict as stdout JSON = block the tool call)."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def emit_block(reason: str) -> dict:
    """Top-level block decision for PostToolUse / Stop gates (later plans)."""
    return {"decision": "block", "reason": reason}
