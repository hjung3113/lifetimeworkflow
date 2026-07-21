"""CLI for the capability registry: list the vocabulary, or ask whether a route is permitted.

Exit codes follow the repo's established convention — 0 allowed, 1 unusable input, 2 a malformed
registry, 3 REFUSED. 3 is the refusal code the human-gated tools already use
(``tools.golden_runner.approve``), so a refused route reads the same way to a caller as any other
gate this harness enforces.
"""

from __future__ import annotations

import argparse
import sys

from tools.capability.registry import CapabilityError, load_capabilities, route_defects

EXIT_OK = 0
EXIT_MALFORMED = 2
EXIT_REFUSED = 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.capability",
        description="Declared capabilities and the per-capability agent allowlist.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="print every declared capability and its allowlist")
    route = sub.add_parser("route", help="ask whether an agent may serve a capability")
    route.add_argument("capability")
    route.add_argument("agent")
    args = parser.parse_args(argv)

    try:
        registry = load_capabilities()
    except CapabilityError as exc:
        print(f"capability registry is malformed: {exc}", file=sys.stderr)
        return EXIT_MALFORMED

    if args.command == "list":
        for identifier in sorted(registry):
            capability = registry[identifier]
            flag = " [read-only]" if capability.read_only else ""
            print(f"{identifier}\t{', '.join(capability.providers)}{flag}")
        return EXIT_OK

    defects = route_defects(args.capability, args.agent, registry=registry)
    if defects:
        for defect in defects:
            print(f"REFUSED: {defect}", file=sys.stderr)
        return EXIT_REFUSED
    print(f"allowed: {args.agent} may serve {args.capability}")
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
