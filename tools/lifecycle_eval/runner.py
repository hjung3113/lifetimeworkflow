"""Evaluate ratification-pending lifecycle fixtures using existing policy primitives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.risk_router.router import LANES, decide, load_policy

FIXTURES = Path(__file__).with_name("fixtures") / "lane-fixtures.json"


class LifecycleEvalError(ValueError):
    """A fixture is malformed or contradicts the deterministic lifecycle policy."""


def load_fixtures(path: Path = FIXTURES) -> list[dict[str, Any]]:
    value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    fixtures = value.get("fixtures") if isinstance(value, dict) else None
    if not isinstance(fixtures, list) or len(fixtures) != 20:
        raise LifecycleEvalError("exactly 20 lifecycle fixtures are required")
    return fixtures


def evaluate(fixtures: list[dict[str, Any]]) -> list[dict[str, str]]:
    policy = load_policy()
    results: list[dict[str, str]] = []
    ids: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict) or not isinstance(fixture.get("id"), str):
            raise LifecycleEvalError("fixture id is required")
        identifier = fixture["id"]
        if identifier in ids:
            raise LifecycleEvalError(f"duplicate fixture: {identifier}")
        ids.add(identifier)
        expected = fixture.get("expected")
        if not isinstance(expected, dict) or expected.get("lane") not in LANES or expected.get("result") != "PASS":
            raise LifecycleEvalError(f"invalid expected result: {identifier}")
        decision = decide(policy, fixture.get("risk"))
        actual = decision["lane"]
        if actual != expected["lane"]:
            raise LifecycleEvalError(f"false downgrade or lane mismatch: {identifier}: expected {expected['lane']}, got {actual}")
        if actual == "FAST" and expected.get("ceremony_max") != 2:
            raise LifecycleEvalError(f"FAST fixture must freeze the two-step user ceremony: {identifier}")
        if actual in {"STRICT", "CONTROLLED"} and set(expected.get("requires", [])) != {"independent_review", "rollback_evidence"}:
            raise LifecycleEvalError(f"high-risk fixture lacks review/rollback requirement: {identifier}")
        results.append({"id": identifier, "lane": actual, "result": "PASS"})
    if {item["lane"] for item in results} != set(LANES) or {item["lane"] for item in results}.difference(LANES):
        raise LifecycleEvalError("every lane must be represented")
    if any(sum(1 for item in results if item["lane"] == lane) != 5 for lane in LANES):
        raise LifecycleEvalError("five fixtures per lane are required")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate lifecycle lane fixtures")
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    args = parser.parse_args(argv)
    try:
        results = evaluate(load_fixtures(args.fixtures))
        print(json.dumps({"fixtures": results, "false_downgrades": 0}, sort_keys=True))
    except (OSError, json.JSONDecodeError, LifecycleEvalError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
