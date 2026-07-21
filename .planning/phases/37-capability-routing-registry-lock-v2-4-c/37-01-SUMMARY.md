# Summary 37-01 — LANE-03: Capability Registry + Allowlist + Capability-Neutral Routing

**Status:** Complete · **Commit:** `932aaf4`

## What the plan said, and what happened

The goal was goal-backward: *a task packet whose discipline record routes to an agent outside the
declared capability's allowlist must be unable to leave its phase.* That is what shipped, at the
already-live choke point, with a positive control that shows the refusal flipping.

## The demonstration — verbatim

**An out-of-allowlist route is REFUSED, end to end through the lifecycle machinery:**

```sh
uv run pytest "tools/task_control/tests/test_task_control.py::test_verify_is_refused_when_a_panel_seat_routes_outside_the_allowlist" -q
```

The test drives a real STRICT packet to `REVIEW`, writes a panel record whose seats are otherwise
perfect — three **distinct** experts, a declared verdict, real `outputs` — and changes exactly one
thing: the middle seat is filled by `python-engineer`, a real declared persona that is simply not on
the `adversarial-review` allowlist. `transition(..., "VERIFY", ...)` raises

```
TaskControlError: missing required disciplines: adversarial-review-panel (panel seat security:
agent python-engineer is not allowed to serve capability adversarial-review
(allowlist: code-reviewer, explorer))
```

and the assertion `(after["phase"], after["revision"]) == (before["phase"], before["revision"])`
proves no state was written. The **positive control** in the same test then rewrites only the seat's
agent to an allowlisted provider and the identical transition succeeds — so the refusal is caused by
the route and by nothing else.

**The same refusal as a one-line CLI:**

```sh
$ uv run python -m tools.capability route adversarial-review python-engineer
REFUSED: agent python-engineer is not allowed to serve capability adversarial-review (allowlist: code-reviewer, explorer)
$ echo $?
3
$ uv run python -m tools.capability route adversarial-review code-reviewer
allowed: code-reviewer may serve adversarial-review
```

## Reused vs built

| Reused unchanged | Built |
|---|---|
| `manager.transition()` / `phase_gate()` refusal (no line changed — the mechanism only widened what counts as missing) | `harness/capabilities.toml` — the vocabulary + per-capability allowlist |
| the phase-36 discipline record shape and defect-list idiom | `tools/capability/` — `load_capabilities`, `providers_for`, `route_defects`, CLI |
| `caps.EXPECTED_PERSONAS` + `caps.is_read_only` (both representations, per-glob-dict aware) | one new defect class in `validate_record` + the `capability` declaration key |
| `fan-out-synthesize` substrate for the panel | `test_capability_wiring.py` — 4 gates, 4 mutation proofs |
| `test_discipline_wiring.py`'s copy-never-the-real-file mutation idiom | |

## Decisions worth restating

- **The allowlist is per capability, not per lane** (CONTEXT D-02). `_validate_core_policy` requires
  each lane's `required_*` to be a monotone **superset** of the lane below. An allowlist *narrows*
  as risk rises, so a per-lane allowlist would be monotone in the wrong direction, or would force a
  direction flag into a shipped invariant. Narrowing is expressed by requiring a stricter capability.
- **Capabilities are not agent frontmatter** (D-03). `project_agent.py` projects a FIXED key list per
  runtime, so a `capabilities:` key would be silently dropped from both emitted trees — a
  declaration that does not survive emit is precisely the claimed control this milestone removes.
- **`read_only` is enforced, not annotated** (D-08). `adversarial-review` is declared read-only and
  `test_capability_wiring.py` fails if any provider holds a write affordance. An agent that can edit
  the change it is judging is the author wearing a second hat.
- **Applied to all five disciplines** (D-05), not one. A capability wired into a single declaration
  would be a demonstration; every lane at STANDARD and above now routes by capability.

## Files

- New: `harness/capabilities.toml`, `tools/capability/{__init__,__main__,registry}.py`,
  `tools/capability/pyproject.toml`, `tools/capability/tests/{conftest,test_registry}.py`,
  `tools/harness_lint/tests/test_capability_wiring.py`
- Changed: `harness/disciplines.toml`, `tools/discipline/{check.py,record.schema.json}`,
  `harness/agents/orchestrator.md`, the five discipline skills + the panel seat schema,
  fixture builders in `tools/{task_control,handoff,lifecycle_eval}`, both emitted runtime trees.

## Verification

`uv run pytest tools/capability` **alone** → 21 passed (isolatability confirmed, not assumed).
`uv run pytest -q` → 1659 passed / 8 snapshots (baseline 1621; +38). Ratchet 0 after recording the
shrink (266 → 245). `tools.contract_drift.drift` clean. `python3 tools/harness_lint/workspace_check.py`
OK. Emit round-trip left `git status --porcelain` empty for the runtime trees.

**Not repaired, correctly:** no contract byte moved, no ADR was written, no ledger row was authored.

## Deviations

One, recorded: the emit-determinism syrupy snapshot was updated (`--snapshot-update`) because the
orchestrator persona genuinely changed. That is the snapshot doing its job, not a bypass — the
change is visible in the committed `.ambr` diff.
