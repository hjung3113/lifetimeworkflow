"""Create and validate an initial Phase-18 task packet from deterministic intake input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.risk_router.router import (
    DEFAULT_POLICY,
    RiskRouterError,
    decide,
    load_overlay,
    load_policy,
)
from tools.task_packet.validate import PacketValidationError, validate_packet


class IntakeError(ValueError):
    """A deterministic malformed intake request."""


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def create_packet(
    request: object,
    output: str | Path,
    *,
    policy_path: str | Path = DEFAULT_POLICY,
    overlay_path: str | Path | None = None,
) -> dict[str, Any]:
    """Materialize the documented intake shape and return the validated router decision."""
    if not isinstance(request, dict) or set(request) != {"task", "routing", "baseline"}:
        raise IntakeError("intake must contain only task, routing, and baseline")
    task_input, routing, baseline = request["task"], request["routing"], request["baseline"]
    required_task_fields = {
        "task_id",
        "goal",
        "non_goals",
        "acceptance_criteria",
        "constraints",
        "decision_refs",
    }
    optional_task_fields = {"stop_condition"}
    if (
        not isinstance(task_input, dict)
        or not required_task_fields <= set(task_input)
        or not set(task_input) <= required_task_fields | optional_task_fields
    ):
        raise IntakeError("task must contain immutable task intent fields")
    if not isinstance(baseline, dict) or set(baseline) != {"commit"}:
        raise IntakeError("baseline must contain only commit")
    core = load_policy(policy_path)
    overlay = load_overlay(overlay_path, core) if overlay_path else None
    decision = decide(core, routing, overlay)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    task = dict(task_input)
    task.update({"risk_inputs": decision["scores"], "lane": decision["lane"]})
    task["risk_decision"] = {key: value for key, value in decision.items() if key != "scores"}
    task_id = task["task_id"]
    _write_json(root / "task.json", task)
    _write_json(
        root / "state.json",
        {
            "task_id": task_id,
            "phase": "INTAKE",
            "revision": 0,
            "baseline": {"repo_root": ".", "commit": baseline["commit"]},
            "current_ref": baseline["commit"],
            "completed_items": [],
            "next_action": "Clarify the task using the recorded risk decision.",
            "blockers": [],
            "transition": None,
        },
    )
    _write_json(root / "evidence.json", {"task_id": task_id, "gate_runs": [], "findings": []})
    if overlay_path:
        # Preserve the exact reviewed overlay bytes so later task-control checks can
        # rederive the same effective policy even when intake used an external path.
        (root / "risk-overlay.toml").write_bytes(Path(overlay_path).read_bytes())
    validate_packet(root)
    return decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a validated Phase-18 task packet from intake JSON"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input", type=Path, help="JSON input file; stdin when omitted")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--overlay", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        decision = create_packet(
            json.loads(raw.removeprefix("\ufeff")),
            args.output,
            policy_path=args.policy,
            overlay_path=args.overlay,
        )
        sys.stdout.write(
            json.dumps(decision, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        )
    except (
        OSError,
        json.JSONDecodeError,
        RiskRouterError,
        IntakeError,
        PacketValidationError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
