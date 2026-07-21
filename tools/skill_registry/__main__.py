"""CLI for the skill registry lock: check the declared surface, or rewrite the declaration.

Default is ``--check``, deliberately: the gate is the point, and a tool whose bare invocation
REWRITES the thing it is supposed to be guarding would make the guard a formality.
"""

from __future__ import annotations

import argparse
import sys

from tools.skill_registry.registry import (
    LOCK_PATH,
    SkillRegistryError,
    build_registry,
    diff_lock,
    dumps,
    load_lock,
    write_lock,
)

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_MALFORMED = 2

_FIX = "uv run python -m tools.skill_registry --write"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.skill_registry",
        description="Lock the declared skill surface and fail on any drift from it.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite harness/skills/registry.lock from the current tree",
    )
    # --check is the default; accepted explicitly so the CI step reads as what it asserts rather
    # than as a bare invocation whose behaviour a reader has to look up.
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the tree against the committed lock (the default)",
    )
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")

    try:
        recomputed = build_registry()
    except SkillRegistryError as exc:
        print(f"skill surface is unreadable: {exc}", file=sys.stderr)
        return EXIT_MALFORMED

    if args.write:
        try:
            before = dumps(load_lock())
        except SkillRegistryError:
            before = ""
        after = dumps(recomputed)
        write_lock(recomputed)
        if before == after:
            print(f"registry lock unchanged: {LOCK_PATH.name}")
        else:
            print(f"registry lock rewritten: {LOCK_PATH.name}")
            for line in diff_lock(load_lock_or_empty(before), recomputed):
                print(f"  {line}")
        return EXIT_OK

    try:
        locked = load_lock()
    except SkillRegistryError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        print(f"Generate it with:\n\n    {_FIX}\n", file=sys.stderr)
        return EXIT_MALFORMED

    differences = diff_lock(locked, recomputed)
    if not differences:
        print(
            f"skill-registry: OK — {len(recomputed['skills'])} skill(s) match the committed lock."
        )
        return EXIT_OK
    print("", file=sys.stderr)
    print(
        "FAIL: the skill surface has DRIFTED from its declaration in harness/skills/registry.lock.",
        file=sys.stderr,
    )
    for line in differences:
        print(f"  {line}", file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "If the change is intended, re-declare it so the move is deliberate and reviewable:",
        file=sys.stderr,
    )
    print(f"\n    {_FIX}\n\nthen commit the regenerated lock.", file=sys.stderr)
    return EXIT_DRIFT


def load_lock_or_empty(serialized: str) -> dict:
    """Parse a previously-serialized lock, or an empty surface when there was none."""
    import json

    if not serialized:
        return {"skills": {}}
    return json.loads(serialized)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
