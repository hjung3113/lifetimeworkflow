# Phase 36: Discipline Skills + Adversarial Review Panel - Context

**Gathered:** 2026-07-22
**Status:** Ready for planning
**Mode:** Autonomous — grey areas decided at the executing agent's discretion per the lead's brief
("plan it, then implement it"). Every decision below is recorded with its rationale so the SUMMARY
can be judged against a stated intent rather than against a reconstruction.

<domain>
## Phase Boundary

Finish the v2.2 TCP-F carry: make a lane's **required discipline** a thing the lifecycle machinery
can refuse, and make the STRICT+ **adversarial review panel** a declared lane requirement rather
than a paragraph of advice.

Requirements: LANE-01, LANE-02 (`.planning/REQUIREMENTS.md` Theme C).
Roadmap entry: `.planning/ROADMAP.md:131-134`.

**IN scope:**
- A per-lane `required_disciplines` slot in the runtime-neutral risk policy, with the same
  monotone-superset validation the existing `required_artifacts` / `required_gates` slots get.
- A declaration of what each discipline IS (`harness/disciplines.toml`): its skill, the phase it is
  owed by, and its record requirements.
- A checker (`tools/discipline/`) that decides satisfied-vs-missing from a task packet.
- Enforcement at the two existing lifecycle choke points — `manager.transition()` and
  `phase_gate.phase_gate()` — so an unsatisfied discipline **fails a transition**.
- Five authored skills (`clarify`, `test-driven-change`, `diagnose`, `domain-modeling`,
  `adversarial-review-panel`) emitted byte-identically to both runtimes, and one thin command
  (`/discipline`).
- A `harness_lint` drift gate: a discipline named by the policy that has no declaration, or a
  declaration whose skill directory does not exist, fails the suite.

**OUT of scope:**
- LANE-03 capability-neutral routing and LANE-04 `registry.lock` — Phase 37 owns both.
- Any change to `contracts/**`. See the Hard boundary note.
- Building a second fan-out engine. The panel reuses `harness/skills/fan-out-synthesize` and the
  read-only `explorer` persona; it dispatches through the runtime's native subtask affordance.
- Changing what `decide()` returns. See D-03.

## Hard boundary note (contract plane)

`contracts/harness/task-control/transitions.json` holds `required_artifacts_by_target_phase` and
`task.schema.json` holds `risk_decision` with `additionalProperties: false`. Both are constitution
plane; `contract-guard` denies the write and the denial is correct. The design below is deliberately
shaped so that **no contract byte needs to move**: the discipline requirement is read from live
policy at transition time, exactly as `manager._required_artifacts` already reads
`policy["lanes"][lane]["required_artifacts"]` (`tools/task_control/manager.py:186-190`). Nothing is
added to the router's decision record, so `task.json` stays schema-valid unchanged.

`HARNESS_DEV_BYPASS` is not used anywhere in this phase. That bypass is what produced RAT-4.
</domain>

<decisions>
## Implementation Decisions

| # | Grey area | Decision | Rationale |
|---|-----------|----------|-----------|
| D-01 | Where does "this lane requires this discipline" live? | `harness/risk-policy.toml`, a new `required_disciplines` key beside `required_artifacts` / `required_gates` in each `[lanes.*]` table. | It is the existing per-lane requirement matrix and it is **not** a contract — `tools/risk_router/router.py:25` points `DEFAULT_POLICY` at `harness/risk-policy.toml`. Putting the requirement anywhere else would be the "second control plane" LANE-01 explicitly forbids. |
| D-02 | Should the requirement be enforced from the packet's frozen `risk_decision`, or from live policy? | **Live policy**, read at transition time. | `_required_artifacts` already reads live policy and separately pins the packet with `policy_hashes.effective`. Reading live is strictly stricter (a tightened policy binds an in-flight task) and needs no contract change. |
| D-03 | Does `decide()` return `required_disciplines`? | **No.** The key participates in the effective-policy hash but never enters the decision record. | `task.schema.json` `risk_decision` is `additionalProperties: false` and is a contract. Adding the key to `decide()`'s return would make every intake write a schema-invalid `task.json` and would require a contract edit this phase may not make. The hash still moves, so a policy change is still detectable. |
| D-04 | Does the discipline requirement participate in the effective-policy hash? | **Yes** — `_effective_policy` gains the key, so `policy_hashes.effective` changes when disciplines change, and an overlay may add disciplines via `required_disciplines_add`. | Without it, an instance overlay could not raise discipline requirements, and a silent discipline change would leave a packet's hash pin unmoved. No test pins a literal hash (verified: zero 60+-hex-char literals under `tools/*/tests/`), so the churn is contained. |
| D-05 | What declares what a discipline *is*? | `harness/disciplines.toml` — id → `skill`, `owed_by_phase`, `outputs_required`, and for the panel `min_experts` / `verdicts`. | Runtime-neutral harness data, same plane as `risk-policy.toml`. Keeping the *policy* (which lane owes it) separate from the *definition* (what discharges it) is what lets Phase 37 route by capability without touching the lane matrix. |
| D-06 | What discharges a discipline? | An immutable per-task record `<<task_dir>>/discipline/<id>.json`, validated against `tools/discipline/record.schema.json`. | Precedent: `tools/risk_router/overlay.schema.json` is a tool-local schema, not a contract — a new validation shape does not have to become constitution plane. |
| D-07 | How is the record kept from being a rubber stamp? | Every record must name the declared skill, the phase it was satisfied at, and repo-relative `outputs` that **must exist**; the panel record must additionally carry ≥`min_experts` reviews with **distinct** expert ids, and every finding it cites must already exist in the packet's `evidence.json` findings. | A record that can be satisfied by writing one JSON literal is a claimed control. Cross-linking panel findings into `evidence.json` reuses the shipped evidence coverage machinery instead of inventing a parallel one, and makes a `block` verdict with an open finding a hard stop at COMPLETE via the existing `_has_unresolved_major_finding`. |
| D-08 | Which lane owes which discipline? | FAST `[]`; STANDARD `clarify`; STRICT `+ test-driven-change, adversarial-review-panel`; CONTROLLED `+ diagnose, domain-modeling`. | Monotone by construction, which the existing `_validate_core_policy` superset rule requires. LANE-02 says the panel is a **STRICT+** requirement — STRICT and CONTROLLED, not STANDARD. |
| D-09 | When is a discipline owed? | `owed_by_phase` in the declaration, compared against the target phase in canonical `PHASES` order: owed when `order(owed_by) <= order(target)`. `BLOCKED` never requires a discipline. | Monotone in the same direction as the artifact matrix, so a discipline cannot be discharged by skipping forward. Blocking a BLOCKED transition on a discipline would trap a task that is blocked *because* the discipline cannot be done. |
| D-10 | Five new skills, or extend existing ones? | Five new (`clarify`, `test-driven-change`, `diagnose`, `domain-modeling`, `adversarial-review-panel`). | `skill-creator`'s anti-sprawl question is answered in RESEARCH §4: no existing skill routes on "the task is ambiguous" / "write the failing test first" / "the defect's cause is unknown" / "the domain vocabulary is unsettled" / "review this adversarially from N expert seats". `review` is a *command* that routes to one `code-reviewer` persona — a single seat is not a panel. Folding five routing triggers into one skill would make the description non-disjoint, which `test_descriptions_are_disjoint` already rejects. |
| D-11 | Does the panel need a new dispatch engine or persona? | **No.** The skill instructs dispatch through the runtime's native subtask affordance to the read-only `explorer` persona with per-seat prompts, exactly as `fan-out-synthesize` §2 does. | LANE-02 says "reusing the Phase-10 fan-out substrate". A second dispatcher would be the thing this milestone exists to stop shipping. |
| D-12 | Emit obligations | `EXPECTED_SKILLS` 13 → 18 (`tools/harness_lint/caps.py:131`) and the command count 25 → 26 (`tools/harness_emit/tests/test_coexist.py:39,65,66`) move in the SAME change as the authored files. | These are live gates; missing either reds the suite at emit time (the 29 D-02 lesson). |
| D-13 | Docs bindings my change moves | `tools/task_control/phase_gate.py` is a source of the **already-stale** `task-control-cli-howto` binding, and `tools/risk_router/router.py` is a source of the advisory `lifecycle-eval-shadow-metrics` binding. I update both target documents with a bounded edit and **draft** the ledger rows; a human lands them. | ADR-0010 §3b: an agent may not author a ledger disposition. The `[STALE_REQUIRED] task-control-cli-howto` red is pre-existing (phase 34) and is not repaired here — but this phase genuinely changes what that how-to documents, so leaving the target unedited would make the human's eventual review wrong. |
| D-14 | Do I add a CI job? | **No.** The new tests run inside the existing `core-suite`, and the drift gate is a `harness_lint` test. | Zero net new jobs; the fan-in already gates the suite. |
| D-15 | Does this phase need an ADR? | **No.** No ratified decision is contradicted or extended: the lane vocabulary, the requirement-matrix shape and the fan-out substrate are all already ratified. If a reviewer disagrees, the escalation is a new ADR in a later phase, never an edit to an accepted one. | ADRs are append-only and this phase adds a *slot* to an existing declared matrix, not a new authority. |
</decisions>

<code_context>
## Existing Code Insights

All citations read from source this session.

- `harness/risk-policy.toml:22-36` — the four `[lanes.*]` tables. The insertion point for D-01.
- `tools/risk_router/router.py:25` `DEFAULT_POLICY`; `:53-88` `_validate_core_policy` (the
  contiguous-cuts + per-key monotone-superset validation to extend); `:157-186` `_effective_policy`
  (explicit key list, so a new key is invisible until added — D-04); `:222-260` `decide()` (must NOT
  gain the key — D-03).
- `tools/task_control/manager.py:186-220` `_required_artifacts` — the live-policy read + effective
  hash pin this design copies. `:223-236` `missing_artifacts`. `:336-372` `transition()` — the
  enforcement choke point.
- `tools/task_control/phase_gate.py:41-108` — the fail-closed resume gate; `refresh` list idiom.
- `tools/task_packet/transitions.py:46` `PHASES` — the canonical phase set for the D-09 ordering.
  It is a `frozenset`, so the ordering must come from the contract's `phases` **array** order, not
  from the set.
- `contracts/harness/task-control/task.schema.json` `risk_decision.additionalProperties: false` —
  the wall behind D-03.
- `tools/risk_router/overlay.schema.json` — precedent for a tool-local JSON Schema (D-06).
- `harness/skills/fan-out-synthesize/SKILL.md` §2 — "no bespoke dispatch engine", the substrate
  LANE-02 reuses.
- `tools/harness_lint/caps.py:120-145` — `EXPECTED_SKILLS` and the anti-sprawl comment block.
- `tools/harness_emit/tests/test_coexist.py:39,65,66` — the 25-command counters.
- `tools/harness_lint/tests/test_docs_update_wiring.py`, `test_context_budget_wiring.py` — the
  precedent shape for a "the authored surface is actually wired" lint.
- `docs/doc-dependencies.toml` — the two bindings D-13 names.
</code_context>

<specifics>
## Specific Ideas

- **The anti-pattern fence is active.** Every control-shaped claim gets a mutation proof: neutralize
  the control and show the outcome flips. A gate that cannot be shown failing is not evidence.
- **The demonstration command matters more than the code.** The phase's headline deliverable is a
  single reproducible invocation that FAILS because a lane's declared discipline is unsatisfied, and
  passes once the record exists. It goes in the SUMMARY verbatim.
- `uv run` for everything; a new `tools/<name>/` package gets its `pyproject.toml` in the same
  commit as its first module, or every `uv` call in the repo breaks.
- `uv run python -m tools.ruff_baseline` must exit 0. The baseline only ratchets down.

</specifics>

<deferred>
## Deferred Ideas

- Capability-neutral routing for the panel seats (a seat is currently a prompt role, not a declared
  capability) — Phase 37, LANE-03.
- A `registry.lock` covering the discipline↔skill mapping — Phase 37, LANE-04. This phase ships the
  drift **test**; the lock file is 37's.
- Letting the v2.3 impact/affected-set change which disciplines a task owes — EVOL-01, needs its own
  ADR.
- A signed/external attestation for a panel seat (a human or a foreign model signing a review) —
  TCP-F05, needs a breaking ADR.
</deferred>
