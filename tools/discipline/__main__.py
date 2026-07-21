"""``python -m tools.discipline`` — what a task owes, and what it has not done.

The exit mapping is the one ``tools.docs_guard`` already established, deliberately reused rather
than replaced by a fourth convention:

===== ==================================================================================
 0     every discipline owed at the phase is validly discharged (or none is owed).
 1     at least one owed discipline is missing or its record is defective. The same
       condition ``tools.task_control`` refuses the transition on.
 3     the declaration, the risk policy, or the packet is INVALID. Distinct from 1
       because the operator action differs: fix the declaration, not the task.
 2     argparse's stdlib usage error. Never produced deliberately.
===== ==================================================================================

Read-only: this reports, it never writes a record.  Writing one is the agent's job after actually
following the skill, which is the whole point of the discipline being a method and not a checkbox.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.discipline.check import (
    load_declarations,
    missing_disciplines,
    record_path,
    required_disciplines,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.discipline",
        description="Report which lane disciplines a task packet owes and which are outstanding.",
    )
    parser.add_argument("task_dir", help="path to the task packet directory")
    parser.add_argument(
        "--phase",
        default=None,
        help="phase to check against; defaults to the packet's current state phase",
    )
    args = parser.parse_args(argv)

    packet = Path(args.task_dir)
    try:
        task = json.loads((packet / "task.json").read_bytes().removeprefix(b"\xef\xbb\xbf"))
        lane = task["lane"]
        phase = args.phase
        if phase is None:
            state = json.loads((packet / "state.json").read_bytes().removeprefix(b"\xef\xbb\xbf"))
            phase = state["phase"]
        declarations = load_declarations()
        owed = required_disciplines(lane, phase, declarations=declarations)
        missing = missing_disciplines(packet, phase, declarations=declarations)
    except (OSError, KeyError, TypeError, ValueError) as error:
        # DisciplineError is a ValueError and a malformed packet lands here too; both carry the
        # same operator action — fix the declaration or the packet, do not "do the discipline".
        print(f"discipline: cannot evaluate {packet} — {error}", file=sys.stderr)
        return 3

    print(f"lane {lane} at {phase}: {len(owed)} discipline(s) owed")
    outstanding = {item.split(" ", 1)[0] for item in missing}
    for identifier in owed:
        declaration = declarations[identifier]
        status = "MISSING" if identifier in outstanding else "OK"
        detail = next((item for item in missing if item.startswith(identifier)), identifier)
        suffix = "" if status == "OK" else f" — {detail}"
        print(
            f"  {status:8} {identifier} (skill {declaration.skill}, "
            f"record {record_path(packet, identifier).name}){suffix}"
        )
    if missing:
        print(
            "discipline: run the declared skill and record it before the next transition",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
