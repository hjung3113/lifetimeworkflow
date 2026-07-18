"""CLI for deterministic risk routing; input is one JSON object from stdin or a file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.risk_router.router import (
    DEFAULT_POLICY,
    RiskRouterError,
    canonical_decision_json,
    decide,
    load_overlay,
    load_policy,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route structured task risk deterministically")
    parser.add_argument("--input", type=Path, help="JSON input file; stdin when omitted")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--overlay", type=Path, help="optional declarative escalation-only TOML overlay")
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        core = load_policy(args.policy)
        overlay = load_overlay(args.overlay, core) if args.overlay else None
        sys.stdout.write(canonical_decision_json(decide(core, payload, overlay)))
    except (OSError, json.JSONDecodeError, RiskRouterError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
