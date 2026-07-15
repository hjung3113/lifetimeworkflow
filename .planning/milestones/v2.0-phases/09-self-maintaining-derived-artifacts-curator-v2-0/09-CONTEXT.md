# Phase 9: Self-Maintaining Derived Artifacts + Curator (v2.0 α) - Context

**Gathered:** 2026-07-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a **self-maintaining derived plane**: a read-mostly `curator` agent that regenerates the
derived artifacts (repo-map, contracts-index, docs `reference/`, `.memory/`) purely by invoking the
existing `tools/memory_regen` + `/docs-sync` machinery — never hand-editing a derived file — plus a
CI **stale-derived** diff gate, a cost-split hook posture, and a `/refresh-memory` + `/verify-work`
freshness check. Satisfies MAINT-01..04.

**Reuse, do NOT rebuild:** `tools/memory_regen/{repo_map,contracts_index,inject}.py`,
`tools/docs_sync/generate.py` + `/docs-sync`, the two-plane-memory machinery, the Phase-7
emit-drift CI gate (mirror pattern), and the read-only agent persona template. This phase adds a
thin owner + gate + command layer over existing generators — no new generation engine.

**In scope:** curator agent, `/refresh-memory` command, `stale-derived` CI job, hook-posture split,
`/verify-work` freshness integration, and flipping the committed-derived set.
**Out of scope:** the fan-out/synthesize orchestration (Phase 10 / ECON), multi-repo workspace
(Phase 11 / MREPO), any new derivation algorithm, and any change to the constitution/golden planes.
</domain>

<decisions>
## Implementation Decisions

### Committed-derived set (the α KEY DECISION — now resolved)
- **D-01:** The committed + PR-gated derived set is **`docs/reference/**` + `contracts-index`**.
  `docs/reference/**` is already committed; **`contracts-index` flips from gitignored-derived →
  committed-derived** so the stale-derived gate can guard it. Rationale: contracts-index is cheap and
  deterministic — a genuine contract-drift signal worth gating.
- **D-02:** **`repo-map` stays gitignored / session-ephemeral** (regenerated per session via the
  SessionStart inject path), NOT committed and NOT gated. Rationale: PageRank ranking is churny and
  would trip the gate on unrelated edits (noise, not signal). Revisiting this is a deferred idea.
- **D-03:** Planner resolves the exact tracked path for the now-committed `contracts-index` (today it
  is generated under the gitignored `.memory/derived/`) and the paired `.gitignore` amendment
  (lines 17-19 currently ignore `.memory/derived/`). The two-plane invariant holds: the committed set
  is machine-written + CI-verified (derived-never-hand-edited is satisfied by machine-write + gate,
  not by human edits).

### Curator authority & invocation
- **D-04:** Ship **both** a `/refresh-memory` command (entry point for humans, CI, and `/verify-work`)
  **and** a read-mostly `curator` agent persona (delegatable by the `orchestrator`/conductor).
- **D-05:** Curator write boundary is **derived paths only** — it may write the committed-derived set
  (`docs/reference/**`, `contracts-index`) and the session-derived set (`.memory/derived/**`), and
  must **hard-deny** writes to the constitution plane (`contracts/`, `docs/adr/`, `golden/`), source,
  and any non-derived path. Machines-gate / humans-ratify. Derive it from the existing read-only
  persona template (`harness/agents/templates/`, cf. `code-reviewer`/`explorer`); no
  constitution/golden write affordance.
- **D-06:** Curator regenerates ONLY by invoking existing tools (`tools/memory_regen` + `/docs-sync`)
  — it never contains its own derivation logic and never hand-edits a derived artifact.

### Stale-derived CI gate + failure UX
- **D-07:** A **separate `stale-derived` CI job**, mirroring the Phase-7 `emit-drift` job: on a PR it
  regenerates the committed-derived set (`docs/reference/**` + `contracts-index`) and runs
  `git diff --exit-code`, **failing on any diff**. Kept distinct from `emit-drift` (separate concern).
- **D-08:** On failure the job prints an **actionable fix message** — the exact command to run
  locally (e.g. `/refresh-memory` / the curator invocation, then commit) — so a contributor can
  self-serve without reading job internals.

### Hook posture (MAINT-03)
- **D-09:** **No on-write memory hook.** Freshness is enforced by the local `/refresh-memory` command
  + the PR/CI `stale-derived` gate. Commits stay fast and quiet; the existing `format-on-write` hook
  already covers the cheap on-write class, and the existing SessionStart inject already refreshes the
  session-derived plane on session open. No heavy per-commit local regeneration.

### `/verify-work` integration
- **D-10:** `/verify-work` incorporates the freshness check — it runs the full regen set locally and
  diffs, so derived drift is caught **pre-handoff**, not only in CI (mirrors how `/verify-work`
  already composes lint + tests + contract-drift + golden).

### Emitter round-trip (cross-cutting, non-negotiable)
- **D-11:** The new `curator` agent and any new command/hook MUST round-trip the Phase-7 emitter to
  **both** runtimes (opencode primary, Claude secondary) from `harness/` source, carry **no model
  identifier**, and keep the core example-independent (GEN-04 guard green).

### Claude's Discretion
- Exact CI job wiring, command file layout, and the precise tracked path for the flipped
  `contracts-index` are implementation details for the planner/researcher — the decisions above fix
  the WHAT and the boundaries, not the file-level HOW.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` — Phase 9 detail: goal, 5 success criteria, and the α KEY DECISION.
- `.planning/REQUIREMENTS.md` — MAINT-01..04 (Korean) + cross-cutting v2.0 constraints.
- `.planning/PROJECT.md` — `## Current Milestone: v2.0 Long-Horizon`, open decision α
  (committed-derived vs session-derived split) — now resolved by D-01/D-02.

### Reuse targets (the machinery this phase owns, not rebuilds)
- `tools/memory_regen/contracts_index.py` — contracts-index generator (the artifact flipping to committed).
- `tools/memory_regen/repo_map.py` — repo-map generator (stays session-ephemeral).
- `tools/memory_regen/inject.py` — SessionStart derived-plane injection payload.
- `tools/docs_sync/generate.py` + the `/docs-sync` command — `docs/reference/**` generator (already committed-derived).

### Gate mirror pattern
- `.github/workflows/ci.yml` — the Phase-7 `emit-drift` job (regenerate → `git diff --exit-code`);
  the `stale-derived` job mirrors it.
- `tools/harness_emit/` — the re-emit-diff precedent (separate-job, fail-on-diff, actionable message).

### Persona template & invariants
- `harness/agents/templates/` + `harness/agents/code-reviewer.md`, `harness/agents/explorer.md` —
  read-only persona template the `curator` derives from.
- `AGENTS.md` + the `two-plane-memory` skill — constitution-vs-derived plane rules; committed-state
  vs gitignored-derived split (the invariant D-03 amends).
- `.gitignore` §17-19 — the `.memory/derived/` ignore rule to amend when flipping contracts-index.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/memory_regen/{contracts_index,repo_map,inject}.py`: the curator/`/refresh-memory` command
  wraps these — no new generation logic.
- `tools/docs_sync/generate.py`: regenerates `docs/reference/**` (already committed-derived).
- `.github/workflows/ci.yml` emit-drift job: copy-and-adapt into a `stale-derived` job.
- `format-on-write` hook: the existing cheap on-write class; MAINT-03 keeps memory regen OFF this path.
- Read-only agent template + `code-reviewer`/`explorer`: the curator's read-mostly persona shape.

### Established Patterns
- Two-plane memory: constitution (human-owned, gated) vs derived (machine-regenerated). Committed set
  = machine-write + CI-verify; gitignored set = session-regenerated. D-01/D-02 move contracts-index
  across that line.
- Phase-7 re-emit-diff gate: regenerate-then-diff, separate CI job, fail-on-diff, actionable message.
- Emitter single-source: every runtime surface (agents/commands/hooks) is authored in `harness/` and
  emitted to both runtimes — curator + `/refresh-memory` follow this (D-11).

### Integration Points
- `/verify-work` composite gate gains the freshness check (D-10).
- SessionStart inject already refreshes session-derived on open — no on-write hook needed (D-09).
- CI fan-in gate gains the new `stale-derived` job alongside emit-drift.
</code_context>

<specifics>
## Specific Ideas

- The committed-derived set is the exact scope of the stale-derived diff gate — keep the two in
  lockstep (anything committed-derived is gated; anything gitignored-derived is not).
- Failure message should be copy-pasteable (the literal refresh command), matching the Phase-7 gate's
  contributor ergonomics.
</specifics>

<deferred>
## Deferred Ideas

- **Committing/gating `repo-map`** — deliberately NOT gated now (PageRank churn). Revisit if a
  low-churn ranking or a churn-tolerant diff (e.g. set-based, order-insensitive) makes it a reliable
  signal. Future consideration, not this phase.
- Fan-out/synthesize orchestration and multi-repo workspace concerns belong to Phase 10 (ECON) and
  Phase 11 (MREPO) respectively — out of scope here.

### Reviewed Todos (not folded)
None — no pending todos matched Phase 9.
</deferred>

---

*Phase: 9-Self-Maintaining Derived Artifacts + Curator*
*Context gathered: 2026-07-13*
