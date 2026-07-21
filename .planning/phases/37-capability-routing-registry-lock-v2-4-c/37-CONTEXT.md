# Phase 37: Capability Routing + Registry Lock + Closeout — Context

**Gathered:** 2026-07-22
**Status:** Ready for planning
**Mode:** Autonomous — grey areas decided at the executing agent's discretion per the lead's brief
("plan it, then implement it"). Every decision is recorded with its rationale so the SUMMARY can be
judged against a stated intent.

<domain>
## Phase Boundary

Close Theme C. Make **which kind of agent** a lane's method needs a *declared capability* rather
than a hardcoded persona name, put a **hard allowlist** behind that declaration, and lock the
emitted **skill surface** to a committed registry so it cannot drift from what the harness declares.

Requirements: LANE-03, LANE-04 (`.planning/REQUIREMENTS.md` Theme C).
Roadmap entry: `.planning/ROADMAP.md:135-137`.

**IN scope:**
- A runtime-neutral capability registry (`harness/capabilities.toml`): capability id → the
  **allowlist** of personas that may serve it, plus a read-only obligation flag.
- A pure resolver/refusal library + CLI (`tools/capability/`).
- Capability-neutral routing wired into the *existing* discipline choke point: a declaration names a
  **capability**, a record names the **agent** that carried it out, and an agent outside the
  capability's allowlist FAILS `manager.transition()` / `phase_gate()`.
- The orchestrator persona routing table gains a capability-first step (routing stops being a list
  of hardcoded persona names).
- `harness/skills/registry.lock` + `tools/skill_registry/` (`--check` / `--write`) + one CI job,
  mirroring the shipped `emit-drift` posture.
- Bidirectional drift lints for both new registries, each with a mutation proof.
- `37-VERIFICATION.md` covering **phase 37 only**.

**OUT of scope:**
- Any change to `contracts/**`, `docs/adr/**`, `golden/**`, `docs/glossary.md`. See the hard
  boundary note. `HARNESS_DEV_BYPASS` is not used anywhere in this phase — that bypass produced
  RAT-4, the debt this milestone discharges.
- Authoring a `docs/.docs-review-ledger.toml` row (ADR-0010 §3b, human-only). Rows are DRAFTED.
- The milestone-level audit and `.planning/{STATE,ROADMAP,MILESTONES}.md` — the orchestrator owns
  milestone closeout.
- A second emitter, a second fan-out engine, or a parallel drift mechanism. Everything hangs off
  `tools/harness_emit`'s manifest and the shipped `emit-drift` job shape.
- Repairing the two KNOWN-RED docs-guard bindings (`task-control-cli-howto`,
  `lifecycle-eval-shadow-metrics`). Their human rows are already drafted by phases 34 and 36.

## Hard boundary note (contract plane)

Nothing in this design moves a contract byte. `contracts/harness/task-control/task.schema.json`
keeps `risk_decision.additionalProperties: false`; the capability requirement is read from LIVE
harness data at transition time, exactly as the phase-36 discipline requirement is
(`tools/task_control/manager.py:440`). The discipline record schema
(`tools/discipline/record.schema.json`) is **tool-local**, not constitution plane — precedent
`tools/risk_router/overlay.schema.json` — so the new `agent` field is an ordinary tool change.
</domain>

<decisions>
## Implementation Decisions

| # | Grey area | Decision | Rationale |
|---|-----------|----------|-----------|
| D-01 | Where does a capability get declared? | A new runtime-neutral `harness/capabilities.toml`, same plane as `harness/disciplines.toml` and `harness/risk-policy.toml`. | Phase 36 deliberately split *policy* (which lane owes a method) from *declaration* (what the method is) so that "Phase 37 can re-route the method by capability without touching the risk policy" (`harness/disciplines.toml` header). Honouring that split means the capability vocabulary is a third file, not a fourth key in the lane matrix. |
| D-02 | Should the allowlist be per **lane**? | **No — per capability.** `[capability.<id>].providers` is the allowlist. | `_validate_core_policy` enforces a **monotone superset** across lanes: a higher lane may only ADD. An allowlist NARROWS as risk rises, so a per-lane allowlist would be monotone in the wrong direction and would have to special-case the validator. Per-capability keeps the existing invariant untouched, and narrowing is expressed by a stricter *capability*, not a stricter lane. |
| D-03 | Do agents declare their capabilities in their own frontmatter? | **No.** The registry names providers. | `tools/harness_emit/project_agent.py` projects a FIXED key list per runtime (`name, description, mode, permission, model` / `name, description, tools, model`). A `capabilities:` key would be silently DROPPED from both emitted trees — a declaration that does not survive emit is exactly the "claimed control" this milestone exists to remove. Registry-side declaration also keeps the allowlist readable in one place. |
| D-04 | What makes routing *fail*? | `harness/disciplines.toml` gains an optional `capability` key. When present, the discipline record must name an `agent`; an agent outside that capability's `providers` is a record **defect**, so `missing_disciplines()` is non-empty and `manager.transition()` / `phase_gate()` REFUSE. | Reuses the live, already-enforced choke point instead of inventing a routing runtime. Phase 36's own deferred list names this seam: "Capability-neutral routing for the panel seats (a seat is currently a prompt role, not a declared capability) — Phase 37, LANE-03". |
| D-05 | Which disciplines get a capability? | **All five.** `adversarial-review-panel` → `adversarial-review` (checked **per panel seat**); `clarify`, `test-driven-change`, `diagnose`, `domain-modeling` → `implementation` (checked on the record's single `agent`). | A capability applied to one declaration would be a demonstration, not a mechanism. Uniform application means every lane at STANDARD and above routes by capability. |
| D-06 | Is `agent` required in the record schema? | Schema-optional; **required by validation** exactly when the declaration carries a `capability`. | Keeps the schema backward-compatible for a declaration with no capability (the mechanism stays optional by design), while making it non-optional wherever it is actually declared. The refusal message says which. |
| D-07 | Is there a reverse "every capability is required by some discipline" lint? | **No.** The reverse gate is instead: every core persona (`caps.EXPECTED_PERSONAS`) provides **≥1** capability, and every `providers` entry is a real `harness/agents/<name>.md`. | Capabilities also describe personas no discipline owes (`reconnaissance`, `orchestration`, `derived-maintenance`). A "required by some discipline" rule would force deleting those, which would make the registry a discipline annex rather than a routing vocabulary. The persona-coverage rule is the one that catches a real defect: a persona nothing can route to, or a route to a persona that does not exist. |
| D-08 | Does `read_only` do anything? | Yes — a capability declaring `read_only = true` must have every provider satisfy `tools.harness_lint.caps.is_read_only`. | The single most valuable thing an allowlist can assert here is that adversarial review cannot be performed by an agent that can edit the thing it is reviewing. Reuses the shipped predicate rather than restating the rule. |
| D-09 | What does `registry.lock` cover, given `emit-drift` exists? | A **different** question. `emit-drift` asks "does the emitted tree match a re-emit of the source?". The lock asks "does the skill surface match its **declaration**?" — per skill: the description digest, the digest of every authored source file, the emitted target paths in BOTH runtimes, and the disciplines that name it. | A description edit, a new `references/` file, or a skill that fails to emit to one runtime all re-emit cleanly and pass `emit-drift`. The lock makes each of those a deliberate, reviewable `--write`. |
| D-10 | Where do the emitted paths in the lock come from? | `tools.harness_emit.manifest.load_manifest` over the committed `emit-manifest.json`, filtered to the two skill lanes. | The lead's brief: the manifest "is the precedent and probably the seam". Recomputing the emit layout in a second module is exactly the parallel mechanism to avoid. |
| D-11 | Lock format + hashing | Deterministic JSON (`sort_keys=True, indent=2`, trailing LF) at `harness/skills/registry.lock`; SHA-256 over raw file bytes, and over the UTF-8 description string. | Mirrors `manifest.prune_then_write`'s determinism contract. Raw-byte digests (not JCS) because the inputs are Markdown, not JSON documents; `tools/contract_hash` stays the JSON-canonicalization owner. |
| D-12 | New CI jobs | **One** — `registry-lock`, added to the fan-in `needs` list. LANE-03's gates ride inside the existing `core-suite`. | LANE-04's requirement literally names "adapter CI". A lint-only gate would not fail a PR that never runs the suite locally; and the shipped precedent for a lock-vs-recompute gate is a separate job (`drift`, `emit-drift`, `stale-derived`). |
| D-13 | Does this phase need an ADR? | **No.** No ratified decision is contradicted. The capability registry adds a vocabulary; the lock adds a recompute gate in the shape of three shipped ones. | ADRs are append-only and this phase may not write `docs/adr/**` regardless. If a reviewer disagrees, the escalation is a NEW ADR in a later phase. |
| D-14 | Docs bindings my change moves | Whatever `tools.docs_guard` reports for the touched sources is handled per ADR-0010: bounded edit of the bound target where the target is editable, and the ledger row **DRAFTED** into `drafts/`, never authored. | ADR-0010 §3b — an agent may not author a ledger disposition. |
</decisions>

<code_context>
## Existing Code Insights

All citations read from source this session.

- `harness/disciplines.toml` — the declaration table + the header comment that explicitly reserves
  capability re-routing for this phase. The insertion point for D-04/D-05.
- `tools/discipline/check.py` — `Declaration`, `load_declarations` (fail-closed key validation with
  `_DECLARATION_KEYS` / `_REQUIRED_DECLARATION_KEYS`), `validate_record` (the defect list), and
  `missing_disciplines` (the pure decision function). All four are the D-04 extension points.
- `tools/discipline/record.schema.json` — `additionalProperties: false` at the root AND inside
  `panel.reviews.items`, so BOTH need the new `agent` property (D-06).
- `tools/task_control/manager.py:440` — `missing_disciplines(task_dir, target)` → `TaskControlError`.
  The refusal already exists; this phase only widens what counts as missing.
- `tools/task_control/phase_gate.py:93` — the same check applied to a RESUMED phase.
- `tools/harness_lint/caps.py` — `EXPECTED_PERSONAS`, `READ_ONLY_PERSONAS`, `is_read_only(fm)`,
  `EXPECTED_SKILLS`. D-07/D-08 reuse all four rather than restating them.
- `tools/harness_emit/manifest.py` `load_manifest` + `prune_then_write` — the D-10 seam and the
  D-11 determinism contract.
- `tools/harness_emit/emit-manifest.json` — 119 lines, the committed owned-path set including every
  `.claude/skills/**` and `.opencode/skill/**` path.
- `tools/harness_emit/project_agent.py` — the fixed per-runtime key projection behind D-03.
- `.github/workflows/ci.yml:237-274` (`emit-drift`) — the job shape D-12 copies; `:381` is the
  fan-in `needs` list to extend.
- `tools/harness_lint/tests/test_discipline_wiring.py` — the bidirectional-lint-with-mutation-proof
  shape the two new lints follow, including the "operate on a COPY, never write the real files" rule.
- `tools/discipline/pyproject.toml` + `tools/lifecycle_eval/tests/conftest.py` — the mandatory
  scaffolding for a new `tools/<name>/` member (pyproject in the SAME step; tests put the repo root
  on `sys.path` or `uv run pytest tools/<pkg>` alone fails).
- `harness/agents/orchestrator.md` — the routing decision table that currently names personas
  directly; the LANE-03 narrative target.
</code_context>

<specifics>
## Specific Ideas

- **Every control-shaped claim gets a mutation proof.** Neutralize the control, show the outcome
  flips. A gate that cannot be shown failing is not evidence.
- **Two demonstration commands go in the SUMMARY verbatim**: one that REFUSES an out-of-allowlist
  route, one that CATCHES a drifted skill surface.
- A new `tools/<name>/` gets its `pyproject.toml` in the same commit as its first module, or every
  `uv` call in the repo breaks. `python3 tools/harness_lint/workspace_check.py` is the bare-python3
  check that survives that state.
- `uv run python -m tools.ruff_baseline` must exit 0; it only ratchets down.
- Anything under `harness/` must round-trip through `tools.harness_emit` to BOTH runtime trees with
  `git status --porcelain` empty. Run the emitter; do not assume.

</specifics>

<deferred>
## Deferred Ideas

- A capability declared on a **lane** (narrowing allowlists as risk rises) — needs the
  `_validate_core_policy` monotone rule to grow a direction-aware mode. Not this phase (D-02).
- Instance-local capability overlays (an `examples/**` instance adding its own personas to an
  allowlist) — the same seam as EVOL-03's docs-registry overlay.
- Locking the **command** and **agent** surfaces the way LANE-04 locks skills. The mechanism
  generalizes; the requirement named skills only.
- Signed/external attestation of a panel seat's agent identity — TCP-F05, needs a breaking ADR.
</deferred>
