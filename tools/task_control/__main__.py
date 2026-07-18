"""CLI for atomic task state management and phase gating."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.task_control.manager import TaskControlError, block, create, resume, show, transition, validate
from tools.task_control.phase_gate import phase_gate


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    if not isinstance(value, dict):
        raise TaskControlError("input JSON must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atomic task-control state manager")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("create", "init"):
        command = commands.add_parser(name); command.add_argument("task_dir", type=Path); command.add_argument("--state", required=True, type=Path)
    command = commands.add_parser("show"); command.add_argument("task_dir", type=Path)
    command = commands.add_parser("validate"); command.add_argument("task_dir", type=Path)
    command = commands.add_parser("transition"); command.add_argument("task_dir", type=Path); command.add_argument("target"); command.add_argument("--expected-revision", type=int, required=True); command.add_argument("--next-action")
    command = commands.add_parser("block"); command.add_argument("task_dir", type=Path); command.add_argument("--expected-revision", type=int, required=True); command.add_argument("--blocker", type=Path, required=True)
    command = commands.add_parser("resume"); command.add_argument("task_dir", type=Path); command.add_argument("target"); command.add_argument("--expected-revision", type=int, required=True); command.add_argument("--resolve-blocker", action="append", default=[])
    command = commands.add_parser("phase-gate"); command.add_argument("task_dir", type=Path); command.add_argument("--expected-revision", type=int, required=True); command.add_argument("--repo-root", type=Path); command.add_argument("--baseline"); command.add_argument("--prohibited-action", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.command in {"create", "init"}: output = create(args.task_dir, _object(args.state))
        elif args.command == "show": output = show(args.task_dir)
        elif args.command == "validate": output = validate(args.task_dir)
        elif args.command == "transition": output = transition(args.task_dir, args.target, args.expected_revision, next_action=args.next_action)
        elif args.command == "block": output = block(args.task_dir, args.expected_revision, _object(args.blocker))
        elif args.command == "resume": output = resume(args.task_dir, args.target, args.expected_revision, resolve_blocker_ids=args.resolve_blocker)
        else: output = {"refresh": phase_gate(args.task_dir, args.expected_revision, repo_root=args.repo_root, baseline=args.baseline, prohibited_actions=args.prohibited_action)}
        print(json.dumps(output, sort_keys=True, indent=2))
    except (OSError, json.JSONDecodeError, TaskControlError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
