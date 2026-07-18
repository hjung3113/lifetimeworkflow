"""Fail-closed PreToolUse gate for mutating work after an active HANDOFF.

The hook deliberately decides only what its envelope makes mechanically knowable: Write/Edit are
mutating, and a small anchored set of Bash forms is mutating.  It does not infer intent from prose
or treat read-only commands as execution.  When an active task is in EXECUTE, REVIEW, or VERIFY,
every such action requires a current revision-bound resume attestation.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from tools.handoff.handoff import HandoffError, require_resume_attestation
from tools.hooks._stdin import emit_deny, parse_event, read_stdin
from tools.task_control.manager import TaskControlError, show

PROTECTED_PHASES = frozenset({"EXECUTE", "REVIEW", "VERIFY"})
_MUTATING_BASH = re.compile(
    # `env NAME=value git commit` and `git -C worktree commit` are still writes.
    # Keep this lexical and anchored: the hook is not a shell parser, but prefix
    # wrappers must not turn a protected mutation into an allow.
    r"(?:^|[;&|]\s*)(?:(?:command|builtin)\s+|env(?:\s+[A-Za-z_][A-Za-z0-9_]*=[^\s]+)*\s+)*(?:"
    r"git(?:\s+-C\s+[^\s]+)*\s+(?:add|apply|checkout|cherry-pick|commit|merge|mv|rebase|reset|restore|rm|switch)|"
    r"(?:rm|mv|cp|touch|mkdir|rmdir)\b|(?:sed|perl)\s+-i\b|tee\b|apply_patch\b)|(?:^|[^<])>>?",
)


def _repo_root(cwd: str) -> Path | None:
    """Resolve only a real Git worktree; an unknown cwd must not create a false allow."""
    if not cwd:
        return None
    result = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    return (
        Path(result.stdout.strip()).resolve()
        if result.returncode == 0 and result.stdout.strip()
        else None
    )


def _is_mutating(tool_name: str, command: str) -> bool:
    if tool_name in {"Write", "Edit"}:
        return True
    return tool_name == "Bash" and bool(_MUTATING_BASH.search(command))


def _active_protected_task(root: Path) -> bool:
    pointer_path = root / ".memory/state/active-task.json"
    if not pointer_path.is_file():
        return False
    try:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        if not isinstance(pointer, dict) or set(pointer) != {
            "task_id",
            "handoff_path",
            "state_revision",
        }:
            return True  # active but malformed is fail-closed.
        packet = root / str(pointer["handoff_path"])
        state = show(packet.parent.parent)
        return state.get("phase") in PROTECTED_PHASES
    except (OSError, ValueError, TaskControlError):
        return True  # active but unreadable is fail-closed.


def decide(tool_name: str, command: str, cwd: str) -> dict | None:
    """Deny only a mechanically identified protected mutation lacking a valid attestation."""
    if not _is_mutating(tool_name, command):
        return None
    root = _repo_root(cwd)
    if root is None or not _active_protected_task(root):
        return None
    try:
        require_resume_attestation(root / ".memory/state", root)
    except (HandoffError, OSError, ValueError) as exc:
        return emit_deny(f"resume_gate: {exc}")
    return None


def main() -> int:
    """Claude PreToolUse entrypoint; denial is data on stdout, never a crash."""
    event = parse_event(read_stdin())
    result = decide(event.tool_name, event.command, event.cwd)
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
