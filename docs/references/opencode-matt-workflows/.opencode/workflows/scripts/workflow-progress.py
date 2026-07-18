#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

START = "<!-- workflow-progress-data\n"
END = "\nworkflow-progress-data -->"


def repo_root() -> Path:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            return Path(out)
    except Exception:
        pass
    return Path.cwd()


def progress_path() -> Path:
    return repo_root() / ".workflow" / "PROGRESS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def initial_state() -> dict:
    return {
        "version": 1,
        "title": "Engineering workflow",
        "objective": "Not set",
        "definition_of_done": "Not set",
        "status": "idle",
        "phase": "intake",
        "active_flow": None,
        "last_outcome": None,
        "next_action": "Describe the next objective to the orchestrator.",
        "context_summary": "",
        "constraints": [],
        "non_goals": [],
        "artifacts": [],
        "decisions": [],
        "blockers": [],
        "verification": [],
        "active_handoff": {},
        "events": [],
        "updated_at": utc_now(),
    }


def load_state() -> dict:
    p = progress_path()
    if not p.exists():
        return initial_state()
    text = p.read_text(encoding="utf-8")
    a, b = text.find(START), text.find(END)
    if a < 0 or b < 0 or b <= a:
        raise SystemExit(f"Malformed progress file: {p}")
    return json.loads(text[a + len(START):b])


def bullets(values: list[str]) -> str:
    return "\n".join(f"- {v}" for v in values) if values else "- None"


def render(s: dict) -> str:
    h = s.get("active_handoff") or {}
    recent = s.get("events", [])[-20:]
    event_lines = [f"{e['at']} — {e['type']}: {e['summary']}" for e in recent]
    visible = f"""# Workflow Progress

> Managed by `.opencode/workflows/scripts/workflow-progress.py`. Do not edit manually.

## Objective

**Title:** {s['title']}  
**Goal:** {s['objective']}  
**Definition of done:** {s['definition_of_done']}

## Current State

- **Status:** {s['status']}
- **Phase:** {s['phase']}
- **Active flow:** {s.get('active_flow') or 'None'}
- **Last outcome:** {s.get('last_outcome') or 'None'}
- **Updated:** {s['updated_at']}

## Context Summary

{s.get('context_summary') or 'Not recorded.'}

## Constraints

{bullets(s.get('constraints', []))}

## Non-goals

{bullets(s.get('non_goals', []))}

## Active Handoff

- **Goal:** {h.get('goal', 'None')}
- **Reason:** {h.get('reason', 'None')}
- **Stop condition:** {h.get('stop_condition', 'None')}
- **Expected output:** {h.get('expected_output', 'None')}

## Artifacts

{bullets(s.get('artifacts', []))}

## Decisions

{bullets(s.get('decisions', []))}

## Blockers

{bullets(s.get('blockers', []))}

## Verification

{bullets(s.get('verification', []))}

## Next Action

{s.get('next_action') or 'None'}

## Recent Events

{bullets(event_lines)}

"""
    return visible + START + json.dumps(s, ensure_ascii=False, indent=2) + END + "\n"


def save_state(s: dict) -> None:
    s["updated_at"] = utc_now()
    p = progress_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="PROGRESS.", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(render(s))
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def add_event(s: dict, kind: str, summary: str) -> None:
    s.setdefault("events", []).append({"at": utc_now(), "type": kind, "summary": summary})
    s["events"] = s["events"][-100:]


def add_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage .workflow/PROGRESS.md")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show")
    show.add_argument("--compact", action="store_true")
    show.add_argument("--json", action="store_true")

    init = sub.add_parser("init")
    init.add_argument("--title", required=True)
    init.add_argument("--goal", required=True)
    init.add_argument("--done", required=True)

    context = sub.add_parser("context")
    context.add_argument("--summary")
    context.add_argument("--constraint", action="append", default=[])
    context.add_argument("--non-goal", action="append", default=[])

    route = sub.add_parser("route")
    route.add_argument("--flow", required=True)
    route.add_argument("--goal", required=True)
    route.add_argument("--reason", required=True)
    route.add_argument("--stop", required=True)
    route.add_argument("--expected", required=True)

    start = sub.add_parser("start")
    start.add_argument("--flow", required=True)
    start.add_argument("--goal", required=True)

    result = sub.add_parser("result")
    result.add_argument("--status", choices=["completed", "partial", "blocked", "failed"], required=True)
    result.add_argument("--summary", required=True)
    result.add_argument("--artifact", action="append", default=[])
    result.add_argument("--verification", action="append", default=[])
    result.add_argument("--next", required=True)

    decision = sub.add_parser("decision")
    decision.add_argument("--text", required=True)

    blocker = sub.add_parser("blocker")
    blocker.add_argument("--add")
    blocker.add_argument("--clear")

    status = sub.add_parser("status")
    status.add_argument("--set", choices=["idle", "active", "paused", "completed"], required=True)
    status.add_argument("--next")

    args = parser.parse_args()
    state = load_state()

    if args.command == "show":
        if not progress_path().exists():
            print("STATUS=ABSENT\nnext=initialise progress when substantive work begins" if args.compact else "No progress document exists.")
        elif args.json:
            print(json.dumps(state, ensure_ascii=False, indent=2))
        elif args.compact:
            print(f"status={state['status']}\nphase={state['phase']}\nactive_flow={state.get('active_flow') or 'none'}\nobjective={state['objective']}\nnext_action={state['next_action']}\nblockers={len(state.get('blockers', []))}\nartifacts={len(state.get('artifacts', []))}")
        else:
            print(render(state), end="")
        return

    if args.command == "init":
        state = initial_state()
        state.update(title=args.title, objective=args.goal, definition_of_done=args.done, status="active", phase="intake", next_action="Clarify context or select a workflow.")
        add_event(state, "init", args.goal)
    elif args.command == "context":
        if args.summary is not None:
            state["context_summary"] = args.summary
        add_unique(state["constraints"], args.constraint)
        add_unique(state["non_goals"], args.non_goal)
        add_event(state, "context", "Updated durable context")
    elif args.command == "route":
        state.update(status="active", phase="routed", active_flow=args.flow, active_handoff={"goal": args.goal, "reason": args.reason, "stop_condition": args.stop, "expected_output": args.expected}, next_action=f"Run {args.flow}.")
        add_event(state, "route", f"Selected {args.flow}: {args.reason}")
    elif args.command == "start":
        state.update(status="active", phase="executing", active_flow=args.flow, next_action=f"Await result from {args.flow}.")
        add_event(state, "start", f"{args.flow}: {args.goal}")
    elif args.command == "result":
        state.update(last_outcome=args.status, phase="reviewed", next_action=args.next)
        state["status"] = "paused" if args.status == "blocked" else "active"
        if args.status == "completed" and args.next.lower() in {"none", "done", "complete"}:
            state["status"] = "completed"
        add_unique(state["artifacts"], args.artifact)
        add_unique(state["verification"], args.verification)
        add_event(state, "result", f"{args.status}: {args.summary}")
    elif args.command == "decision":
        add_unique(state["decisions"], [args.text])
        add_event(state, "decision", args.text)
    elif args.command == "blocker":
        if bool(args.add) == bool(args.clear):
            raise SystemExit("Provide exactly one of --add or --clear")
        if args.add:
            add_unique(state["blockers"], [args.add])
            state["status"] = "paused"
            add_event(state, "blocker", args.add)
        else:
            state["blockers"] = [x for x in state["blockers"] if args.clear not in x]
            add_event(state, "unblock", args.clear)
    elif args.command == "status":
        state["status"] = args.set
        if args.next:
            state["next_action"] = args.next
        add_event(state, "status", args.set)

    save_state(state)
    print(progress_path())


if __name__ == "__main__":
    main()
