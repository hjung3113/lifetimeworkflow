# Phase 36 Research — Discipline Skills + Adversarial Review Panel

**Date:** 2026-07-22
**Confidence:** HIGH on repo machinery (every citation read from source this session). No external
research was needed: LANE-01/LANE-02 are entirely about wiring surfaces this repo already owns.

## 1. What already exists (the reuse inventory)

The lead's brief said REUSE, DO NOT REBUILD. Here is the inventory, and what each piece does or does
not give this phase.

| Existing | What it gives | Gap for LANE-01/02 |
|----------|---------------|--------------------|
| `tools/risk_router/router.py` | 7-axis scoring, the four lanes, promotions, per-lane `required_artifacts` / `required_gates`, effective-policy hashing, overlay merge with a monotone-superset rule (`:78-84`) | The per-lane matrix has **no discipline slot**. Nothing in the router knows the word. |
| `harness/risk-policy.toml` | The policy DATA, runtime-neutral, NOT a contract | Same gap; this is the file to extend. |
| `tools/task_packet/transitions.py` | Legal edges + `required_artifacts_for_phase` read from `contracts/.../transitions.json` | **Contract-backed.** Adding a discipline column here means writing a contract — refused. So the discipline requirement must not live here. |
| `tools/task_control/manager.py` | `transition()` — the single mutation choke point; `_required_artifacts()` — the live-policy read + hash pin; `missing_artifacts()`; evidence coverage; `_has_unresolved_major_finding` | No discipline check. `transition()` is the correct insertion point: every legitimate phase change goes through it. |
| `tools/task_control/phase_gate.py` | Fail-closed resume gate accumulating a `refresh` list | Same — no discipline check. |
| `harness/skills/fan-out-synthesize/` | The decompose → dispatch-read-only-worker → schema-bounded return → synthesize substrate, with an explicit "no bespoke dispatch engine" rule | The substrate is generic. It has no adversarial framing, no expert seats, and no notion of a lane owing a panel. |
| `harness/commands/review.md` + `code-reviewer` persona | One adversarial reviewer, read-only, severity-classified | **One seat is not a panel**, and a command is invoked at will — nothing declares it required. |
| `tools/harness_lint/` | Structural gates incl. skill caps, emit-drift, wiring lints | No gate ties a declared requirement to an authored skill. |
| `tools/harness_emit/` | Single-source projection to `.opencode/` + `.claude/` with counted anti-drift assertions | Counts must move with the authored files. |

**Nothing here is rebuilt.** The phase adds one slot to the policy, one declaration file, one small
checker, two call sites, five skills, one command and one drift test.

## 2. The contract wall, verified

Two things that would be the "obvious" home for a lane's discipline are constitution plane:

1. `contracts/harness/task-control/transitions.json` → `required_artifacts_by_target_phase`.
2. `contracts/harness/task-control/task.schema.json` → `risk_decision`, which is
   `"additionalProperties": false` over exactly ten keys.

(2) is the sharper constraint and it settles the design: `tools/risk_router/intake.py` writes the
`decide()` return into `task.json` as `risk_decision`. **If `decide()` returned one extra key, every
new task packet would fail `_validate_document("task", ...)`.** So `decide()` must not change.

The escape is already in the code: `manager._required_artifacts()` (`:186-190`) reads the requirement
from **live policy**, not from the packet, and separately pins the packet with
`policy_hashes.effective`. The discipline requirement follows the same route. No contract byte moves.

The effective hash DOES move once `required_disciplines` enters `_effective_policy`. Checked: no test
under `tools/*/tests/` pins a literal 60+-hex-char string (`grep -rn "[0-9a-f]\{60,\}"` → zero hits),
and `.workflow/` does not exist in the tree, so there is no live packet to invalidate. The churn is
contained to whatever fixtures recompute the hash themselves — which is the correct behaviour, since
they recompute it by calling `decide()`.

## 3. The mechanism that makes a discipline fail-able

```
harness/risk-policy.toml       [lanes.STRICT] required_disciplines = [...]   ← WHICH lane owes it
harness/disciplines.toml       [discipline.<id>] skill / owed_by_phase / …   ← WHAT discharges it
tools/discipline/check.py      missing_disciplines(task_dir, target_phase)   ← DID it happen
tools/task_control/manager.py  transition() raises TaskControlError          ← the refusal
tools/task_control/phase_gate.py  adds "discipline: <id>" to refresh          ← the resume refusal
```

A discipline is *owed* at target phase `T` when `order(owed_by_phase) <= order(T)` in the canonical
phase order (`contracts/.../transitions.json` `phases` array — an ordered array; note
`transitions.PHASES` is a `frozenset` and must not be used for ordering). `BLOCKED` never owes.

It is *discharged* by `<task_dir>/discipline/<id>.json` that:
- validates against `tools/discipline/record.schema.json`,
- names the declared `skill` for that discipline (a record claiming the wrong skill is invalid),
- was satisfied at a phase that is at or before the owing phase,
- lists `outputs` — repo-relative paths that must **exist**,
- and, for a discipline declaring `min_experts`, carries that many reviews with **distinct** expert
  ids, each with a declared verdict, where every cited finding id exists in the packet's
  `evidence.json` `findings`.

The last clause is what stops the record from being a rubber stamp: panel findings must be real
evidence findings, which are already schema-validated and already drive `_evidence_covers_*` and
`_has_unresolved_major_finding` at VERIFY/COMPLETE.

## 4. Anti-sprawl: why five new skills and not an extension

`skill-creator` requires this question be answered before a skill directory exists. Answered against
the 13 shipped skills, by routing trigger:

| Candidate host | Its trigger | Why it cannot absorb the new one |
|----------------|-------------|----------------------------------|
| `context-budget` | "should I delegate or work inline" | Budget arithmetic; says nothing about ambiguity resolution. |
| `fan-out-synthesize` | "the surface is too wide for one context" | The **substrate**. The panel *uses* it. Folding adversarial seat design into it would make the generic substrate carry a lane-specific procedure. |
| `gate-model` | "a write was blocked, what is gated" | About refusals, not about method. |
| `golden-debug` | "a snapshot went red, which axis" | Domain-specific decision tree for the 7 canonicalization axes; `diagnose` is the general cause-before-fix discipline. |
| `python-conventions` | "writing Python here" | Mentions pytest; does not route on "write the failing test first". |
| `data-contracts` | "reading/changing contracts" | Contract mechanics, not domain vocabulary modelling. |
| `docs-upkeep` | "the docs gate reports an obligation" | A different obligation entirely. |

So: five new skills, each with a disjoint routing trigger (required — `test_descriptions_are_disjoint`
rejects duplicates and `test_skills.py` requires a routing token in each description).

`harness/commands/review.md` deserves a note: it exists, it is adversarial, and it is read-only —
but it routes to **one** `code-reviewer` persona and is invoked at will. LANE-02 asks for a *declared
lane requirement* with *multiple experts*. The panel skill therefore composes: N seats dispatched via
the fan-out substrate, each seat a distinct adversarial frame, findings landed in `evidence.json`.
`/review` remains the single-seat entry point and is not replaced.

## 5. Emit + gate obligations (verified live)

- `tools/harness_lint/caps.py:131` `EXPECTED_SKILLS` — frozenset of 13; `tools/harness_emit/validate.py:182`
  asserts the discovered set **equals** it. 13 → 18.
- `tools/harness_emit/tests/test_coexist.py:39,65,66` — literal `25` command count in the test name,
  the docstring and two assertions. 25 → 26.
- `tools/harness_lint/tests/test_skills.py` — name regex, ≤64 name, ≤1024 description, no reserved
  vendor word, no `<`/`>`, a routing token in the description, disjoint descriptions.
- `tools/harness_emit/generate.py:361` carries a stale inline comment ("real tree = 9"); it is a
  comment, not a gate. Left alone rather than opportunistically edited.
- Emit round-trip: `uv run python -m tools.harness_emit` then `git status --porcelain` must be empty
  **including untracked files** (the 29 D-03 blind spot: bare `git diff` does not see new files).

## 6. Docs bindings this phase moves

`docs/doc-dependencies.toml`:

- `task-control-cli-howto` — sources include `tools/task_control/phase_gate.py`. Already
  `STALE_REQUIRED` from phase 34 (known red, not mine). This phase genuinely changes the documented
  behaviour, so `docs/how-to/task-lifecycle.md` gets a bounded edit and a **drafted** ledger row.
- `lifecycle-eval-shadow-metrics` (advisory) — sources include `tools/risk_router/router.py`.
  Advisory never flips the exit code; the target is reviewed and a row drafted.

ADR-0010 §3b: an agent may not author a `docs/.docs-review-ledger.toml` disposition. Drafts go to
`drafts/` with landing instructions; the human lands them.

## 7. Open questions carried into planning

- **Q1 — should FAST owe anything?** No. FAST exists to be cheap; the monotone rule makes `[]` the
  only honest floor. Recorded rather than debated at execution time.
- **Q2 — should the record be an `artifacts/<name>/<run-id>/` immutable run instead of a single
  JSON?** No: the artifact tree is evidence-run addressed and `orphan_artifacts` only recognises
  `output.log`. A discipline record is a *declaration about method*, not a gate run. Kept separate
  and out of the orphan scan.
- **Q3 — min_experts value for the panel?** 3. Below 3 a "panel" is a pair, and the empirical case
  in LANE-02 (v2.3's four review-driven phases) came from multi-frame review. Declared as data so it
  can move without code.
