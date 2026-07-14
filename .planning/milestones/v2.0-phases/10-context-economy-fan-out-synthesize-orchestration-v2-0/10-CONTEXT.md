# Phase 10: Context-Economy Fan-out/Synthesize Orchestration (v2.0 β) - Context

**Gathered:** 2026-07-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a **first-class fan-out → synthesize workflow** that keeps long-lived, multi-session work
context-cheap. A conductor (or a human) decomposes a task, dispatches N analysis subagents, recovers
**schema-bounded, citation-bearing summaries** (paths + claims, not raw file dumps), and synthesizes
a result — WITHOUT any single context ballooning. This is the reusable substrate Phase 11 (γ,
multi-repo) applies across repos. Satisfies **ECON-01, ECON-02, ECON-03**.

**Reuse, do NOT rebuild:** the existing primary `orchestrator`/conductor (already has `task: allow`
and a routing table), the read-only `explorer` persona as the fan-out worker, `/orient`, the Phase-7
emitter single-source→dual-runtime pipeline, and the `references/` byte-copy convention already used
by `golden-debug` and `polyglot-boundary`. This phase adds a thin **workflow skill + command +
return-contract + budget-heuristic skill** over existing machinery — no new dispatch engine, no new
generation logic.

**In scope:** a `fan-out-synthesize` skill, a thin `/fan-out-synthesize` command entry point, a
schema-bounded citation-bearing **return contract** (harness-authored, domain-neutral), a
`context-budget` (delegate-vs-inline) skill wired into the `orchestrator` persona + `/orient`, and
the emitter round-trip of all new surface to both runtimes.
**Out of scope:** the multi-repo workspace / cross-repo fan-out (Phase 11 / MREPO), any new subagent
persona beyond the existing five, a bespoke runtime dispatch tool/engine, and any change to the
constitution/golden planes or the domain `contracts/` data plane.
</domain>

<decisions>
## Implementation Decisions

### ECON-01 — fan-out-synthesize deliverable form
- **D-01:** Ship **BOTH** a reusable **`fan-out-synthesize` skill** (the progressive-disclosure,
  runtime-neutral procedure: decompose → dispatch N → recover schema-bounded summaries → synthesize)
  **and** a thin **`/fan-out-synthesize` command** entry point. One shared workflow usable by BOTH a
  human and the primary orchestrator/conductor (ECON-01 "사람과 지휘자 모두 재사용"), mirroring the
  Phase-9 both-command-and-agent pattern and the existing skill+command pairing.
- **D-02:** The skill/command is the **first-class** artifact — decompose/dispatch/recover/synthesize
  is a named, executable workflow, not scattered orchestrator prose.

### ECON-01 — dispatch mechanism & runtime-neutrality
- **D-03:** Dispatch is a **runtime-neutral procedural skill** executed via the orchestrator's
  **existing Task/subtask affordance** (opencode `task`, Claude `Task`). NO bespoke dispatch
  tool/engine is built — reuse existing machinery (v2.0 non-negotiable: 재사용, 재구축 금지).
- **D-04:** The session-side `deep-research` skill and the `Workflow` tool are **shape inspiration
  only** (fan-out → schema-bounded return → synthesize), NOT a runtime dependency of the deployed
  harness — the emitted opencode/Claude surface must not assume either exists.

### ECON-01 — fan-out worker persona (anti-sprawl)
- **D-05:** The N analysis subagents **reuse the existing read-only `explorer` persona** as the
  worker; the return contract is enforced by the **skill/command prompt**, not by a new persona.
  `EXPECTED_PERSONAS` stays **5** (anti-sprawl). A dedicated analyst persona is a deferred idea only
  if the planner/researcher proves explorer's scope is insufficient.

### ECON-01 — synthesize step owner
- **D-06:** The primary **orchestrator/conductor synthesizes** the recovered summaries (it already has
  `task: allow` and is the sole planner in the deployed harness). No new synthesizer persona — one
  shared workflow, not two (ECON-01).

### ECON-02 — summary/return contract
- **D-07:** Enforce a **schema-bounded, citation-bearing return contract**: each subagent returns
  compact **paths + claims** (cited to file/line), NEVER raw file dumps, so the conductor synthesizes
  **without re-reading** the raw files each worker touched (ECON-02).
- **D-08:** The return contract is a **harness-authored, domain-neutral JSON Schema reference
  co-located with the `fan-out-synthesize` skill** (e.g. `references/`-style, byte-copied to both
  runtimes like `golden-debug`/`polyglot-boundary` already do). It is **NOT** placed under the domain
  `contracts/` constitution plane (that plane is the instance data plane, CODEOWNERS-gated and
  domain-specific) — this honors "schema-bounded" + contract-first ethos while keeping the core
  example-independent (GEN-04) and not tripping the domain contract-drift gate.
- **D-09:** The return is an **ephemeral runtime value**, not a committed artifact — so it is a schema
  the subagent conforms to (enforced by prompt + documented shape), NOT a CI-diff-gated file. A
  lightweight conformance validator is optional planner discretion, not a gate requirement.

### ECON-03 — delegate-vs-inline context-budget guide
- **D-10:** Ship a **dedicated `context-budget` skill** (the delegate-vs-inline heuristic: when to fan
  out vs work inline) — progressive disclosure, domain-neutral — rather than burying the heuristic in
  orchestrator prose. Add it to `EXPECTED_SKILLS`.
- **D-11:** Wire the heuristic into **BOTH** named integration points (ECON-03): the `orchestrator`
  persona (routing table / intake procedure) **and** `/orient` (read-order), so the delegate-vs-inline
  routing decision is **observable and repeatable**, matching how `gate-model`/`two-plane-memory` are
  already surfaced.

### Cross-cutting (non-negotiable — mirrors Phase-9 D-11)
- **D-12:** Every new agent/skill/command **round-trips the Phase-7 emitter** to BOTH runtimes
  (opencode primary, Claude secondary) from `harness/` source, carries **no model identifier**, and
  keeps the core example-independent (**GEN-04 guard green**). New skills are enumerated in
  `EXPECTED_SKILLS` (anti-sprawl); no new persona (`EXPECTED_PERSONAS` stays 5).

### Claude's Discretion
- Exact skill/command file names (`fan-out-synthesize`, `/fan-out-synthesize`, `context-budget` are
  the recommended names), the precise JSON-Schema field set of the return contract, the reference-file
  layout, and whether a lightweight conformance validator is added are planner/researcher
  implementation details. The decisions above fix the WHAT and the boundaries, not the file-level HOW.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` — Phase 10 detail: goal + 4 success criteria (fan-out-synthesize usable by
  human AND conductor; enforced summary/return contract; delegate-vs-inline guide wired into
  orchestrator + `/orient`; emitter round-trip + GEN-04).
- `.planning/REQUIREMENTS.md` §ECON — **ECON-01/02/03** (Korean) + the v2.0 cross-cutting
  non-negotiables block (two-plane, machines-gate/humans-ratify, GEN-04, emitter round-trip).
- `.planning/PROJECT.md` — `## Current Milestone: v2.0 Long-Horizon`; β is the reusable substrate γ
  (Phase 11) builds on.

### Reuse targets (the machinery this phase extends, not rebuilds)
- `harness/agents/orchestrator.md` — the primary conductor (`task: allow`, routing table + intake
  procedure) that runs the fan-out and synthesizes; ECON-03 wires the budget heuristic here.
- `harness/agents/explorer.md` — the read-only worker the N fan-out subagents reuse (D-05).
- `harness/commands/orient.md` — `/orient`; ECON-03 wires the delegate-vs-inline read-order here.
- `harness/skills/golden-debug/references/`, `harness/skills/polyglot-boundary/references/` — the
  `references/` byte-copy convention the return-contract schema follows (D-08).
- `tools/harness_emit/` + the emit-drift CI gate — the Phase-7 single-source→dual-runtime pipeline
  every new surface must round-trip (D-12).
- `tools/harness_lint/caps.py` — `EXPECTED_SKILLS` (9 today) / `EXPECTED_PERSONAS` (5 today) the
  anti-sprawl gates; new skills are enumerated here, persona count stays 5.

### Invariants & precedent
- `AGENTS.md` + the `two-plane-memory` / `gate-model` skills — constitution-vs-derived planes; the
  precedent for a heuristic skill surfaced through the orchestrator + `/orient` (D-10/D-11).
- `.planning/phases/09-self-maintaining-derived-artifacts-curator-v2-0/09-CONTEXT.md` — Phase-9
  D-11 (emitter round-trip, no model id, GEN-04) restated here as D-12; same both-command-and-agent
  shipping pattern.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `harness/agents/orchestrator.md`: the conductor already has `task: allow`, a routing decision table,
  and an intake procedure — extend it with fan-out routing + the delegate-vs-inline heuristic; it runs
  dispatch and synthesizes (D-03/D-06/D-11).
- `harness/agents/explorer.md`: read-only search persona reused verbatim as the fan-out worker (D-05).
- `references/` byte-copy (golden-debug, polyglot-boundary): the emit path for the return-contract
  schema reference to both runtimes (D-08).
- Phase-7 emitter (`tools/harness_emit/`) + emit-drift gate: the mandatory round-trip for new surface.

### Established Patterns
- Skill + command pairing (progressive-disclosure skill = the reusable workflow; thin command = the
  entry point) — the shape for `fan-out-synthesize` (D-01).
- Heuristic-skill-wired-into-orchestrator + `/orient` (gate-model, two-plane-memory) — the shape for
  `context-budget` (D-10/D-11).
- Anti-sprawl enumerated sets in `caps.py` (`EXPECTED_SKILLS`/`EXPECTED_PERSONAS`) — new skills added,
  persona count held at 5.
- Domain-neutral core + `examples/**` isolation (GEN-04): the return contract is a harness mechanism,
  so it must NOT live in the domain `contracts/` plane (D-08).

### Integration Points
- `orchestrator` routing table + intake procedure ← fan-out workflow + budget heuristic (ECON-03).
- `/orient` read-order ← delegate-vs-inline pointer (ECON-03).
- Phase-7 emitter ← new skill(s) + command projected to `.opencode/**` and `.claude/**` (D-12).
- `EXPECTED_SKILLS` in `tools/harness_lint/caps.py` ← the two new skills enumerated (anti-sprawl).
</code_context>

<specifics>
## Specific Ideas

- Return summaries must be **citation-bearing** (file/line + claim) so synthesis never re-reads raw
  files — this is the whole point of the context economy (ECON-02); keep the schema tight.
- The return-contract schema is domain-neutral and lives WITH the skill (references/ byte-copy), not
  in `contracts/` — schema-bounded without polluting the instance constitution plane.
- One shared workflow for human + conductor (not two divergent paths) — ECON-01.
</specifics>

<deferred>
## Deferred Ideas

- **Dedicated analyst/summarizer persona** — deliberately NOT added now (reuse `explorer`,
  anti-sprawl). Revisit only if the planner/researcher proves the read-only explorer scope cannot
  carry the schema-bounded return contract.
- **CI-gated / persisted fan-out artifacts** — the return is an ephemeral runtime value this phase
  (D-09); persisting + gating recovered summaries is out of scope.
- **Cross-repo fan-out / workspace-level synthesis** — belongs to Phase 11 (MREPO); β is the
  single-repo substrate γ generalizes.

### Reviewed Todos (not folded)
None — no pending todos matched Phase 10.
</deferred>

---

*Phase: 10-Context-Economy Fan-out/Synthesize Orchestration*
*Context gathered: 2026-07-13*
