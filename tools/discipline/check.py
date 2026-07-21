"""Deterministic lane-discipline checking: what a lane owes, and whether it was carried out.

Three data sources, none of them constitution plane:

* ``harness/risk-policy.toml`` — which lane owes which discipline (read LIVE, never from the task's
  frozen ``risk_decision``; the packet's ``policy_hashes.effective`` pin is what ties the two).
* ``harness/disciplines.toml`` — what each discipline is and what discharges it.
* ``<task_dir>/discipline/<id>.json`` — the task's own claim that it happened.

Nothing here mutates a repository.  ``missing_disciplines`` is a pure decision function; the refusal
lives in ``tools.task_control``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.risk_router.router import RiskRouterError, load_policy
from tools.task_packet.transitions import TRANSITIONS_PATH

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECLARATIONS = REPO_ROOT / "harness" / "disciplines.toml"
RECORD_SCHEMA = Path(__file__).with_name("record.schema.json")
RECORD_DIRNAME = "discipline"

_DECLARATION_KEYS = frozenset(
    {"skill", "owed_by_phase", "outputs_required", "min_experts", "verdicts"}
)
_REQUIRED_DECLARATION_KEYS = frozenset({"skill", "owed_by_phase", "outputs_required"})


class DisciplineError(ValueError):
    """A malformed declaration, policy, or packet — never an unsatisfied discipline.

    An unsatisfied discipline is an ordinary result (a non-empty ``missing_disciplines`` list), not
    an exception: it is the expected state of a task that has not done the work yet.
    """


def _ordered_phases() -> tuple[str, ...]:
    """Lifecycle order from the transitions contract's ORDERED ``phases`` array.

    ``transitions.PHASES`` is a frozenset — correct for membership, useless for ordering, and using
    it here would make "is this discipline owed yet" depend on set iteration order.
    """
    value = json.loads(TRANSITIONS_PATH.read_bytes())
    phases = value.get("phases")
    if not isinstance(phases, list) or not all(isinstance(item, str) and item for item in phases):
        raise DisciplineError("invalid transition contract: phases must be an array of strings")
    return tuple(phases)


PHASE_ORDER = _ordered_phases()
# A blocked task owes nothing: blocking is frequently what happens BECAUSE the discipline cannot be
# carried out, and refusing the BLOCKED transition would trap the task with no legal move.
NO_DISCIPLINE_PHASES = frozenset({"BLOCKED"})


@dataclass(frozen=True)
class Declaration:
    """One declared discipline: its skill, when it is owed, and what discharges it."""

    id: str
    skill: str
    owed_by_phase: str
    outputs_required: int
    min_experts: int | None = None
    verdicts: tuple[str, ...] | None = None


def _read_toml(path: Path) -> dict[str, Any]:
    import tomllib

    try:
        with path.open("rb") as handle:
            value = tomllib.load(handle)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        raise DisciplineError(f"invalid discipline declarations: {exc}") from exc
    if not isinstance(value, dict):
        raise DisciplineError("discipline declarations must be a TOML table")
    return value


def load_declarations(path: str | Path = DEFAULT_DECLARATIONS) -> dict[str, Declaration]:
    """Load and fail-closed-validate every declared discipline."""
    raw = _read_toml(Path(path))
    if raw.get("version") != 1:
        raise DisciplineError("discipline declarations version must be 1")
    table = raw.get("discipline")
    if not isinstance(table, dict) or not table:
        raise DisciplineError("discipline declarations require a non-empty [discipline] table")
    declarations: dict[str, Declaration] = {}
    for identifier, body in table.items():
        if not isinstance(body, dict):
            raise DisciplineError(f"declaration for {identifier} must be a table")
        unknown = set(body) - _DECLARATION_KEYS
        if unknown:
            raise DisciplineError(
                f"declaration for {identifier} has unknown key(s): {', '.join(sorted(unknown))}"
            )
        missing = _REQUIRED_DECLARATION_KEYS - set(body)
        if missing:
            raise DisciplineError(
                f"declaration for {identifier} is missing: {', '.join(sorted(missing))}"
            )
        skill = body["skill"]
        owed = body["owed_by_phase"]
        outputs = body["outputs_required"]
        if not isinstance(skill, str) or not skill:
            raise DisciplineError(f"declaration for {identifier} has an invalid skill")
        if owed not in PHASE_ORDER or owed in NO_DISCIPLINE_PHASES:
            raise DisciplineError(f"declaration for {identifier} has an unknown owed_by_phase")
        if type(outputs) is not int or outputs < 0:
            raise DisciplineError(f"declaration for {identifier} has an invalid outputs_required")
        experts = body.get("min_experts")
        if experts is not None and (type(experts) is not int or experts < 2):
            raise DisciplineError(
                f"declaration for {identifier} has an invalid min_experts"
                " (a panel needs at least 2 seats)"
            )
        verdicts = body.get("verdicts")
        if verdicts is not None and not (
            isinstance(verdicts, list)
            and verdicts
            and all(isinstance(item, str) and item for item in verdicts)
        ):
            raise DisciplineError(f"declaration for {identifier} has an invalid verdict vocabulary")
        declarations[identifier] = Declaration(
            id=identifier,
            skill=skill,
            owed_by_phase=owed,
            outputs_required=outputs,
            min_experts=experts,
            verdicts=None if verdicts is None else tuple(verdicts),
        )
    return declarations


def lane_disciplines(lane: str, *, policy: dict[str, Any] | None = None) -> list[str]:
    """Every discipline the lane owes, in declared order, read from LIVE policy."""
    try:
        resolved = policy if policy is not None else load_policy()
    except RiskRouterError as exc:
        raise DisciplineError(f"invalid risk policy: {exc}") from exc
    lanes = resolved.get("lanes", {})
    if lane not in lanes:
        raise DisciplineError(f"unknown lane: {lane}")
    values = lanes[lane].get("required_disciplines")
    if not isinstance(values, list):
        raise DisciplineError(f"lane {lane} declares no required_disciplines")
    return list(values)


def required_disciplines(
    lane: str,
    target_phase: str,
    *,
    policy: dict[str, Any] | None = None,
    declarations: dict[str, Declaration] | None = None,
) -> list[str]:
    """The lane's disciplines that are owed at or before *target_phase*."""
    if target_phase not in PHASE_ORDER:
        raise DisciplineError(f"unknown phase: {target_phase}")
    if target_phase in NO_DISCIPLINE_PHASES:
        return []
    declared = declarations if declarations is not None else load_declarations()
    target_index = PHASE_ORDER.index(target_phase)
    owed: list[str] = []
    for identifier in lane_disciplines(lane, policy=policy):
        declaration = declared.get(identifier)
        if declaration is None:
            raise DisciplineError(f"lane {lane} requires an undeclared discipline: {identifier}")
        if PHASE_ORDER.index(declaration.owed_by_phase) <= target_index:
            owed.append(identifier)
    return owed


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    except FileNotFoundError as exc:
        raise DisciplineError(f"missing file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise DisciplineError(f"invalid JSON in {path.name}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise DisciplineError(f"{path.name} must be a JSON object")
    return value


def _repository_root(task_dir: Path) -> Path:
    """The root a record's output paths are resolved against.

    A live packet lives at ``<repo>/.workflow/tasks/<task_id>``; a fixture packet is its own root.
    """
    for ancestor in task_dir.parents:
        if ancestor / ".workflow" / "tasks" / task_dir.name == task_dir:
            return ancestor
    return task_dir


def record_path(task_dir: str | Path, discipline_id: str) -> Path:
    return Path(task_dir) / RECORD_DIRNAME / f"{discipline_id}.json"


def _finding_ids(task_dir: Path) -> set[str]:
    evidence_path = task_dir / "evidence.json"
    if not evidence_path.is_file():
        return set()
    evidence = _json(evidence_path)
    findings = evidence.get("findings", [])
    if not isinstance(findings, list):
        return set()
    return {
        item["id"]
        for item in findings
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def validate_record(
    record: dict[str, Any],
    declaration: Declaration,
    *,
    task_dir: str | Path,
    finding_ids: set[str] | None = None,
) -> list[str]:
    """Return every defect in *record*; an empty list means the discipline is discharged.

    The defects are what stop a record from being a rubber stamp: it must name the declared skill,
    have been satisfied no later than the phase it is owed by, cite outputs that actually EXIST, and
    — for a panel — carry distinct seats whose findings are real evidence findings.
    """
    packet = Path(task_dir)
    schema = json.loads(RECORD_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(record), key=lambda e: list(e.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "<root>"
        return [f"schema {location}: {error.message}"]

    defects: list[str] = []
    if record["discipline"] != declaration.id:
        defects.append(f"record names discipline {record['discipline']}, expected {declaration.id}")
    if record["skill"] != declaration.skill:
        defects.append(
            f"record names skill {record['skill']}, declaration names {declaration.skill}"
        )
    satisfied = record["satisfied_at_phase"]
    if satisfied in NO_DISCIPLINE_PHASES:
        defects.append(f"record was satisfied at {satisfied}, which discharges nothing")
    elif PHASE_ORDER.index(satisfied) > PHASE_ORDER.index(declaration.owed_by_phase):
        defects.append(
            f"record was satisfied at {satisfied}, after the owed phase {declaration.owed_by_phase}"
        )

    outputs = record["outputs"]
    if len(outputs) < declaration.outputs_required:
        defects.append(
            f"record cites {len(outputs)} output(s), declaration requires "
            f"{declaration.outputs_required}"
        )
    root = _repository_root(packet)
    for output in outputs:
        if not (root / output).exists():
            defects.append(f"record cites an output that does not exist: {output}")

    if declaration.min_experts is not None:
        panel = record.get("panel")
        if not isinstance(panel, dict):
            defects.append("record declares no panel, but the discipline requires one")
        else:
            reviews = panel["reviews"]
            experts = {review["expert"] for review in reviews}
            if len(experts) < declaration.min_experts:
                defects.append(
                    f"panel carries {len(experts)} distinct expert seat(s), declaration requires "
                    f"{declaration.min_experts}"
                )
            known = finding_ids if finding_ids is not None else _finding_ids(packet)
            for review in reviews:
                if (
                    declaration.verdicts is not None
                    and review["verdict"] not in declaration.verdicts
                ):
                    defects.append(
                        f"panel seat {review['expert']} reports an undeclared verdict: "
                        f"{review['verdict']}"
                    )
                for finding_id in review["finding_ids"]:
                    if finding_id not in known:
                        defects.append(
                            f"panel seat {review['expert']} cites a finding absent from "
                            f"evidence.json: {finding_id}"
                        )
    return defects


def missing_disciplines(
    task_dir: str | Path,
    target_phase: str,
    *,
    policy: dict[str, Any] | None = None,
    declarations: dict[str, Declaration] | None = None,
) -> list[str]:
    """Every discipline owed at *target_phase* that is not validly discharged by the packet."""
    packet = Path(task_dir)
    task = _json(packet / "task.json")
    lane = task.get("lane")
    if not isinstance(lane, str):
        raise DisciplineError("task.json declares no lane")
    declared = declarations if declarations is not None else load_declarations()
    owed = required_disciplines(lane, target_phase, policy=policy, declarations=declared)
    if not owed:
        return []
    known = _finding_ids(packet)
    missing: list[str] = []
    for identifier in owed:
        path = record_path(packet, identifier)
        if not path.is_file():
            missing.append(identifier)
            continue
        try:
            record = _json(path)
        except DisciplineError as exc:
            missing.append(f"{identifier} ({exc})")
            continue
        if isinstance(record.get("task_id"), str) and record["task_id"] != task.get("task_id"):
            missing.append(f"{identifier} (record belongs to task {record['task_id']})")
            continue
        defects = validate_record(record, declared[identifier], task_dir=packet, finding_ids=known)
        if defects:
            missing.append(f"{identifier} ({defects[0]})")
    return missing
