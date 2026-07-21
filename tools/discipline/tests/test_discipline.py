"""LANE-01/LANE-02/LANE-03: the declaration loader and the satisfied-vs-missing decision function.

Every defect class asserts its SPECIFIC message, not merely that the defect list is non-empty — a
checker that rejects everything for the wrong reason is indistinguishable from one that works, and
the positive controls at the bottom are what keep the rule from degrading into "nothing is ever
satisfied".

The LANE-03 block at the bottom covers capability-neutral routing: a declaration names a capability,
a record names the agent that served it, and an agent outside that capability's allowlist makes the
record undischarged — which is what tools/task_control turns into a refused transition.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.capability.registry import load_capabilities, providers_for
from tools.discipline.check import (
    DEFAULT_DECLARATIONS,
    PHASE_ORDER,
    Declaration,
    DisciplineError,
    load_declarations,
    missing_disciplines,
    record_path,
    required_disciplines,
    validate_record,
)
from tools.risk_router.router import DEFAULT_POLICY, load_policy


@pytest.fixture
def declarations() -> dict:
    return load_declarations(DEFAULT_DECLARATIONS)


@pytest.fixture
def policy() -> dict:
    return load_policy(DEFAULT_POLICY)


def _packet(tmp_path: Path, lane: str, *, findings: list[str] = ()) -> Path:
    packet = tmp_path / "task-0001"
    packet.mkdir(parents=True, exist_ok=True)
    (packet / "task.json").write_text(
        json.dumps({"task_id": "task-0001", "lane": lane}), encoding="utf-8"
    )
    (packet / "evidence.json").write_text(
        json.dumps({"findings": [{"id": item} for item in findings]}), encoding="utf-8"
    )
    (packet / "notes.md").write_text("an output that exists\n", encoding="utf-8")
    return packet


def _write_record(packet: Path, discipline: str, body: dict) -> None:
    path = record_path(packet, discipline)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


def _agent_for(discipline: str) -> str | None:
    """The first allowlisted provider for whatever capability the declaration names (LANE-03).

    Resolved from the registry rather than typed, so this helper never hardcodes a persona name —
    which is the whole point of capability-neutral routing.
    """
    declaration = load_declarations()[discipline]
    if declaration.capability is None:
        return None
    return providers_for(declaration.capability)[0]


def _record(discipline: str, skill: str, phase: str, **extra) -> dict:
    body = {
        "discipline": discipline,
        "skill": skill,
        "task_id": "task-0001",
        "satisfied_at_phase": phase,
        "outputs": ["notes.md"],
    }
    agent = _agent_for(discipline)
    if agent is not None:
        body["agent"] = agent
    body.update(extra)
    return body


def _panel(
    experts: list[str],
    verdict: str = "pass",
    finding_ids: list[str] = (),
    agent: str | None = None,
) -> dict:
    seat_agent = agent if agent is not None else _agent_for("adversarial-review-panel")
    return {
        "reviews": [
            {
                "expert": expert,
                "verdict": verdict,
                "finding_ids": list(finding_ids),
                **({"agent": seat_agent} if seat_agent is not None else {}),
            }
            for expert in experts
        ]
    }


# ── ordering and declaration loading ──────────────────────────────────────────────────────────


def test_phase_order_comes_from_the_contract_array():
    """Ordered, not a frozenset — 'is it owed yet' must not depend on set iteration order."""
    assert PHASE_ORDER == (
        "INTAKE",
        "CLARIFY",
        "SPEC",
        "PLAN",
        "EXECUTE",
        "REVIEW",
        "VERIFY",
        "COMPLETE",
        "BLOCKED",
    )


def test_every_policy_discipline_is_declared(declarations: dict, policy: dict):
    for lane in ("FAST", "STANDARD", "STRICT", "CONTROLLED"):
        for identifier in policy["lanes"][lane]["required_disciplines"]:
            assert identifier in declarations


def _declaration_toml(version: int = 1, **fields: object) -> str:
    lines = [f"version = {version}", "", "[discipline.x]"]
    for key, value in fields.items():
        rendered = f'"{value}"' if isinstance(value, str) else str(value)
        lines.append(f"{key} = {rendered}")
    return "\n".join(lines) + "\n"


_WELL_FORMED = {"skill": "x", "owed_by_phase": "EXECUTE", "outputs_required": 1}


@pytest.mark.parametrize(
    ("text", "match"),
    [
        (_declaration_toml(version=2, **_WELL_FORMED), "version"),
        (_declaration_toml(**{**_WELL_FORMED, "owed_by_phase": "NOWHERE"}), "owed_by_phase"),
        (_declaration_toml(skill="x", owed_by_phase="EXECUTE"), "missing"),
        (_declaration_toml(**_WELL_FORMED, bogus=1), "unknown key"),
        (_declaration_toml(**_WELL_FORMED, min_experts=1), "min_experts"),
        ("version = 1\n", "non-empty"),
    ],
)
def test_malformed_declarations_are_refused(tmp_path: Path, text: str, match: str):
    path = tmp_path / "disciplines.toml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(DisciplineError, match=match):
        load_declarations(path)


# ── what is owed, and when ────────────────────────────────────────────────────────────────────


def test_fast_owes_nothing_anywhere(declarations: dict, policy: dict):
    for phase in PHASE_ORDER:
        assert required_disciplines("FAST", phase, policy=policy, declarations=declarations) == []


def test_blocked_owes_nothing_even_for_controlled(declarations: dict, policy: dict):
    """A task is often BLOCKED precisely BECAUSE the discipline cannot be carried out."""
    owed = required_disciplines("CONTROLLED", "BLOCKED", policy=policy, declarations=declarations)
    assert owed == []


def test_a_discipline_is_owed_from_its_phase_onward(declarations: dict, policy: dict):
    assert required_disciplines("STRICT", "PLAN", policy=policy, declarations=declarations) == []
    assert required_disciplines("STRICT", "EXECUTE", policy=policy, declarations=declarations) == [
        "clarify"
    ]
    assert "adversarial-review-panel" not in required_disciplines(
        "STRICT", "REVIEW", policy=policy, declarations=declarations
    )
    assert "adversarial-review-panel" in required_disciplines(
        "STRICT", "VERIFY", policy=policy, declarations=declarations
    )
    assert "adversarial-review-panel" in required_disciplines(
        "STRICT", "COMPLETE", policy=policy, declarations=declarations
    )


def test_a_lane_requiring_an_undeclared_discipline_is_refused(declarations: dict, policy: dict):
    mutated = json.loads(json.dumps(policy))
    mutated["lanes"]["STRICT"]["required_disciplines"].append("telepathy")
    with pytest.raises(DisciplineError, match="undeclared discipline: telepathy"):
        required_disciplines("STRICT", "VERIFY", policy=mutated, declarations=declarations)


# ── one case per defect class ─────────────────────────────────────────────────────────────────


def test_record_naming_the_wrong_skill_is_invalid(tmp_path: Path, declarations: dict):
    packet = _packet(tmp_path, "STRICT")
    defects = validate_record(
        _record("clarify", "diagnose", "CLARIFY"), declarations["clarify"], task_dir=packet
    )
    assert defects == ["record names skill diagnose, declaration names clarify"]


def test_record_satisfied_after_the_owed_phase_is_invalid(tmp_path: Path, declarations: dict):
    packet = _packet(tmp_path, "STRICT")
    defects = validate_record(
        _record("clarify", "clarify", "VERIFY"), declarations["clarify"], task_dir=packet
    )
    assert defects == ["record was satisfied at VERIFY, after the owed phase EXECUTE"]


def test_record_citing_a_missing_output_is_invalid(tmp_path: Path, declarations: dict):
    packet = _packet(tmp_path, "STRICT")
    record = _record("clarify", "clarify", "CLARIFY", outputs=["not-written.md"])
    defects = validate_record(record, declarations["clarify"], task_dir=packet)
    assert defects == ["record cites an output that does not exist: not-written.md"]


def test_record_citing_no_output_is_invalid(tmp_path: Path, declarations: dict):
    packet = _packet(tmp_path, "STRICT")
    record = _record("clarify", "clarify", "CLARIFY", outputs=[])
    defects = validate_record(record, declarations["clarify"], task_dir=packet)
    assert defects == ["record cites 0 output(s), declaration requires 1"]


def test_panel_with_duplicate_seats_is_not_a_panel(tmp_path: Path, declarations: dict):
    """Three seats, two opinions: one reviewer typed twice is not multi-expert review."""
    packet = _packet(tmp_path, "STRICT")
    record = _record(
        "adversarial-review-panel",
        "adversarial-review-panel",
        "REVIEW",
        panel=_panel(["contract", "security", "security"]),
    )
    defects = validate_record(record, declarations["adversarial-review-panel"], task_dir=packet)
    assert defects == [
        "panel carries 2 distinct expert seat(s), declaration requires 3",
    ]


def test_panel_citing_an_unknown_finding_is_invalid(tmp_path: Path, declarations: dict):
    packet = _packet(tmp_path, "STRICT", findings=["F-01"])
    seat = _agent_for("adversarial-review-panel")
    record = _record(
        "adversarial-review-panel",
        "adversarial-review-panel",
        "REVIEW",
        panel={
            "reviews": [
                {"expert": "contract", "verdict": "pass", "finding_ids": ["F-01"], "agent": seat},
                {
                    "expert": "security",
                    "verdict": "concerns",
                    "finding_ids": ["F-99"],
                    "agent": seat,
                },
                {"expert": "rollback", "verdict": "pass", "finding_ids": [], "agent": seat},
            ]
        },
    )
    defects = validate_record(record, declarations["adversarial-review-panel"], task_dir=packet)
    assert defects == [
        "panel seat security cites a finding absent from evidence.json: F-99",
    ]


def test_panel_verdict_outside_the_declared_vocabulary_is_invalid(
    tmp_path: Path, declarations: dict
):
    packet = _packet(tmp_path, "STRICT")
    record = _record(
        "adversarial-review-panel",
        "adversarial-review-panel",
        "REVIEW",
        panel=_panel(["contract", "security", "rollback"], verdict="looks-fine"),
    )
    defects = validate_record(record, declarations["adversarial-review-panel"], task_dir=packet)
    assert all("undeclared verdict: looks-fine" in defect for defect in defects)
    assert len(defects) == 3


def test_panel_absent_from_a_panel_discipline_is_invalid(tmp_path: Path, declarations: dict):
    packet = _packet(tmp_path, "STRICT")
    record = _record("adversarial-review-panel", "adversarial-review-panel", "REVIEW")
    defects = validate_record(record, declarations["adversarial-review-panel"], task_dir=packet)
    assert defects == ["record declares no panel, but the discipline requires one"]


def test_schema_violation_short_circuits_with_one_message(tmp_path: Path, declarations: dict):
    packet = _packet(tmp_path, "STRICT")
    record = _record("clarify", "clarify", "CLARIFY")
    record["unexpected"] = True
    defects = validate_record(record, declarations["clarify"], task_dir=packet)
    assert len(defects) == 1 and defects[0].startswith("schema ")


# ── positive controls: a rule that rejects everything is not a gate ───────────────────────────


@pytest.mark.parametrize(
    "discipline",
    ["clarify", "test-driven-change", "adversarial-review-panel", "diagnose", "domain-modeling"],
)
def test_a_well_formed_record_discharges_every_discipline(
    tmp_path: Path, declarations: dict, discipline: str
):
    packet = _packet(tmp_path, "CONTROLLED", findings=["F-01"])
    declaration = declarations[discipline]
    extra = {}
    if declaration.min_experts is not None:
        extra["panel"] = _panel(["contract", "security", "rollback"], finding_ids=["F-01"])
    record = _record(discipline, declaration.skill, declaration.owed_by_phase, **extra)
    assert validate_record(record, declaration, task_dir=packet) == []


def test_missing_disciplines_reports_owed_then_clears(
    tmp_path: Path, declarations: dict, policy: dict
):
    packet = _packet(tmp_path, "STRICT")
    assert missing_disciplines(packet, "EXECUTE", policy=policy, declarations=declarations) == [
        "clarify"
    ]
    _write_record(packet, "clarify", _record("clarify", "clarify", "CLARIFY"))
    assert missing_disciplines(packet, "EXECUTE", policy=policy, declarations=declarations) == []


def test_missing_disciplines_carries_the_first_defect(
    tmp_path: Path, declarations: dict, policy: dict
):
    packet = _packet(tmp_path, "STRICT")
    _write_record(packet, "clarify", _record("clarify", "clarify", "VERIFY"))
    assert missing_disciplines(packet, "EXECUTE", policy=policy, declarations=declarations) == [
        "clarify (record was satisfied at VERIFY, after the owed phase EXECUTE)"
    ]


def test_a_record_from_another_task_does_not_discharge(
    tmp_path: Path, declarations: dict, policy: dict
):
    packet = _packet(tmp_path, "STRICT")
    body = _record("clarify", "clarify", "CLARIFY")
    body["task_id"] = "task-9999"
    _write_record(packet, "clarify", body)
    assert missing_disciplines(packet, "EXECUTE", policy=policy, declarations=declarations) == [
        "clarify (record belongs to task task-9999)"
    ]


# ── LANE-03: capability-neutral routing + the agent allowlist ──────────────────────────────────


def test_every_declaration_names_a_declared_capability(declarations: dict):
    """A declaration routes by CAPABILITY, never by a persona name."""
    registry = load_capabilities()
    for identifier, declaration in declarations.items():
        assert declaration.capability is not None, f"{identifier} declares no capability"
        assert declaration.capability in registry


def test_a_declaration_naming_an_undeclared_capability_is_refused(tmp_path: Path):
    """MUTATION: a typo'd capability is a loud load error, not a silently unenforced route."""
    path = tmp_path / "disciplines.toml"
    path.write_text(
        'version = 1\n[discipline.x]\nskill = "x"\ncapability = "no-such-capability"\n'
        'owed_by_phase = "EXECUTE"\noutputs_required = 0\n',
        encoding="utf-8",
    )
    with pytest.raises(DisciplineError, match="undeclared capability"):
        load_declarations(path)


def test_an_out_of_allowlist_agent_makes_the_record_invalid(tmp_path: Path, declarations: dict):
    """THE LANE-03 defect: a record routed outside the capability's allowlist is not discharged."""
    packet = _packet(tmp_path, "STRICT")
    record = _record("clarify", "clarify", "CLARIFY", agent="code-reviewer")
    defects = validate_record(record, declarations["clarify"], task_dir=packet)
    assert defects == [
        "agent code-reviewer is not allowed to serve capability implementation "
        "(allowlist: python-engineer)"
    ]


def test_a_record_with_no_agent_is_not_discharged(tmp_path: Path, declarations: dict):
    """An unrecorded route is a defect in its own right — silence is not a route."""
    packet = _packet(tmp_path, "STRICT")
    record = _record("clarify", "clarify", "CLARIFY")
    del record["agent"]
    assert validate_record(record, declarations["clarify"], task_dir=packet) == [
        "capability implementation requires a named agent, none given"
    ]


def test_the_panel_allowlist_is_checked_per_seat(tmp_path: Path, declarations: dict):
    """A panel routed three ways is three routing decisions; only the bad seat is named."""
    packet = _packet(tmp_path, "STRICT")
    good = providers_for("adversarial-review")[0]
    record = _record(
        "adversarial-review-panel",
        "adversarial-review-panel",
        "REVIEW",
        panel={
            "reviews": [
                {"expert": "contract", "verdict": "pass", "finding_ids": [], "agent": good},
                {
                    "expert": "security",
                    "verdict": "pass",
                    "finding_ids": [],
                    "agent": "python-engineer",
                },
                {"expert": "rollback", "verdict": "pass", "finding_ids": [], "agent": good},
            ]
        },
    )
    defects = validate_record(record, declarations["adversarial-review-panel"], task_dir=packet)
    assert defects == [
        "panel seat security: agent python-engineer is not allowed to serve capability "
        "adversarial-review (allowlist: code-reviewer, explorer)"
    ]


def test_missing_disciplines_reports_the_routing_refusal(
    tmp_path: Path, declarations: dict, policy: dict
):
    """The routing defect reaches the decision function, which is what task_control refuses on."""
    packet = _packet(tmp_path, "STRICT")
    _write_record(packet, "clarify", _record("clarify", "clarify", "CLARIFY", agent="curator"))
    assert missing_disciplines(packet, "EXECUTE", policy=policy, declarations=declarations) == [
        "clarify (agent curator is not allowed to serve capability implementation "
        "(allowlist: python-engineer))"
    ]


def test_a_declaration_without_a_capability_imposes_no_routing(tmp_path: Path):
    """The mechanism is opt-in BY DECLARATION: no capability, no routing requirement."""
    packet = _packet(tmp_path, "STRICT")
    neutral = Declaration(
        id="clarify", skill="clarify", owed_by_phase="CLARIFY", outputs_required=1
    )
    record = _record("clarify", "clarify", "CLARIFY")
    del record["agent"]
    assert validate_record(record, neutral, task_dir=packet) == []
