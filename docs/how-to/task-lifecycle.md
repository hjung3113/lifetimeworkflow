# Run a task through the control-plane lifecycle

*Diátaxis quadrant: **how-to**. This recipe assumes that the task contract and risk policy already exist.*

## 1. Create the packet from an intake request

Put the task intent, seven risk scores, fact flags, and baseline commit in a JSON request. Create the packet under the repository-local task namespace:

```sh
uv run python -m tools.risk_router.intake --input intake.json --output .workflow/tasks/T-YYYYMMDDHHMMSS-example
```

The router is deterministic. Do not select a lower lane manually; an instance overlay may only add obligations or promote a lane.

## 2. Start each phase through its gate

Record the constraint coverage first, then use the task-control gate before an execution phase:

```sh
uv run python -m tools.task_control attest .workflow/tasks/T-YYYYMMDDHHMMSS-example --attestation attestation.json
uv run python -m tools.task_control phase-gate .workflow/tasks/T-YYYYMMDDHHMMSS-example --expected-revision 0
```

Advance only with the current revision. A stale ref, wrong worktree, missing predecessor artifact, unresolved blocker, or incomplete constraint coverage must be refreshed rather than bypassed.

```sh
uv run python -m tools.task_control transition .workflow/tasks/T-YYYYMMDDHHMMSS-example EXECUTE --expected-revision 0
```

FAST remains `INTAKE → EXECUTE → VERIFY → COMPLETE`: packet creation plus verification are its two user-visible ceremony steps. It does not require a detailed spec, plan, separate worktree, or double review. STRICT requires the policy's independent review record; CONTROLLED additionally requires rollback evidence (the `rollback_plan` and `rollback_verified` gate).

### The lane's disciplines are refused, not suggested

A lane owes **artifacts** and it owes **disciplines** — the method behind the artifact. `harness/risk-policy.toml` declares which disciplines each lane owes (`required_disciplines`) and `harness/disciplines.toml` declares what each one is: its skill, the phase it is owed by, and what discharges it. FAST owes none; STANDARD owes `clarify`; STRICT adds `test-driven-change` and `adversarial-review-panel`; CONTROLLED adds `diagnose` and `domain-modeling`.

Ask what is outstanding before attempting the transition:

```sh
uv run python -m tools.discipline .workflow/tasks/T-YYYYMMDDHHMMSS-example --phase EXECUTE
```

Exit `0` means nothing is owed or everything is discharged, `1` means something is outstanding, `3` means the declaration or the packet is malformed (fix that, not the task). A transition attempted with an outstanding discipline is refused before any state is written:

```
FAIL: missing required disciplines: clarify
```

`phase-gate` reports the same condition as a `discipline: <id>` refresh reason, so a resumed session cannot inherit a green a fresh transition would have refused.

Discharge one by following its skill and then writing `<task_dir>/discipline/<id>.json`, naming the declared skill, the phase, and `outputs` paths that exist. A panel discipline additionally needs the declared number of **distinct** expert seats, and every finding it cites must already exist in the packet's `evidence.json`. No tool writes the record for you: the record is the claim that the method was followed.

## 3. Capture existing gates as evidence

Use the evidence adapter to record an already-registered gate. It captures the actual command, exit status, artifact path, and hash; it does not redefine the gate.

```sh
uv run python -m tools.evidence capture .workflow/tasks/T-YYYYMMDDHHMMSS-example tests --criterion AC-01
```

Missing or changed evidence prevents VERIFY/COMPLETE. Do not put secrets, credentials, PII, or long logs in evidence or HANDOFF.

## 4. Generate, activate, and resume a HANDOFF

At a handoff boundary, generate its immutable snapshot, publish its pointer through the existing checkpoint flow, and let a fresh process validate it before work resumes:

```sh
uv run python -m tools.handoff generate .workflow/tasks/T-YYYYMMDDHHMMSS-example
uv run python -m tools.handoff resume --state-dir .memory/state --repo-root .
```

The resume gate denies mutations in protected phases until this revision-bound validation succeeds. A stale HANDOFF must be regenerated; it is never silently repaired.

## Ownership boundaries

| Area | Owner | Rule |
|---|---|---|
| `harness/` commands and runtime projections | generator | Edit the source then run `python -m tools.harness_emit`; never hand-edit `.claude/` or `.opencode/`. |
| `.memory/derived/` | generator | Regenerate; never hand-edit. |
| `.workflow/tasks/` packets and evidence | task-control tools | Use the lifecycle commands and their atomic writes. |
| `contracts/`, `golden/`, `docs/adr/` | human/CODEOWNERS | Machines gate; humans ratify. Agents may prepare drafts only. |

## 5. Complete and verify the repository gates

Before completion, evidence must be current and committed at HEAD, and any constitution-plane change needs a human approval reference. Run the repository gates rather than inventing a replacement:

```sh
uv run pytest
uv run python -m tools.contract_drift.drift
uv run python -m tools.harness_emit
git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json
```
