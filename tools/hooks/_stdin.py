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
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# _stdin.py -> hooks -> tools -> repo root (parents[2]); mirrors tools/harness_perms/resolver.py.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# DEV-only opt-out; distinct from GOLDEN_APPROVE_HUMAN, so a dev-bypassed write is never
# represented as human ratified.
DEV_BYPASS_ENV = "HARNESS_DEV_BYPASS"


def dev_bypassed() -> bool:
    """Return whether the explicit local-dev bypass flag is non-empty and non-blank."""
    return bool((os.environ.get(DEV_BYPASS_ENV) or "").strip())


def repo_relative(file_path: str, root: Path = _REPO_ROOT) -> str:
    """Best-effort normalize a hook ``file_path`` to a repo-root-relative POSIX path.

    Claude's Write/Edit ``tool_input.file_path`` is ABSOLUTE (``/…/contracts/x``), but the
    constitution/secret deny globs (``contracts/**``, ``golden/**``, ``*.env``) are repo-relative
    and matched with ``fnmatchcase``, which anchors at the string start — so an absolute path never
    matches and the path-scoped deny silently no-ops. Normalizing here, at the one Claude-stdin
    seam, lets the shared pure resolver keep seeing relative paths (its signature stays stable).

    * Absolute path under ``root`` -> repo-relative POSIX string (``contracts/x``).
    * Absolute path OUTSIDE the repo -> returned unchanged (still absolute; simply won't match).
    * Already-relative path (as fed by tests) -> unchanged apart from a stripped leading ``./``.
    * Empty string -> unchanged.
    """
    if not file_path:
        return file_path
    candidate = Path(file_path)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(root).as_posix()
        except ValueError:
            return file_path  # outside the repo -> leave as-is (won't match repo-relative globs)
    return file_path[2:] if file_path.startswith("./") else file_path


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
