# Milestone v2.0 — Context (for `/gsd:new-milestone`)

**Drafted:** 2026-07-11 (discussion with user)
**Status:** DEFINED, not yet opened. Open v2 only AFTER Phase 7 (emitter) completes v1.0.
**Working title:** Long-Horizon — Self-Maintaining Memory + Context-Economy Orchestration + Multi-Repo Workspace

> This file is the discuss-milestone output that `/gsd:new-milestone` consumes: it fixes the v2
> vision, the three phases (α/β/γ), draft requirement IDs, the reuse map, and the open decisions to
> resolve at plan time. Do NOT run `/gsd:new-milestone` until Phase 7 has shipped — running it early
> orphans the still-pending Phase 7 in v1.

## Sequencing (locked)

**7 → α → β → γ.** Phase 7 (Single-Source Dual-Runtime Emitter) finishes v1.0 first, because α/β/γ
all introduce new agents/skills/hooks that must flow through the P7 emit path (`harness/` →
`.opencode/` + `.claude/`). Then v2 opens with α, β, γ (continuing phase numbering → 9, 10, 11).

## Vision / Problem

The harness is strong at "single repo, single session." Three gaps block long-horizon,
multi-project work:
1. **Derived artifacts go stale** — repo-map / contracts-index / docs `reference/` regenerate at
   SessionStart and via manual `/docs-sync`, but nothing forces freshness at merge. Over a long
   project they drift from reality.
2. **Long sessions burn context** — the orchestrator delegates ad hoc, but there is no first-class
   "fan-out analysis → return summaries only → synthesize" workflow to keep the main session's
   context small while it stays live for a long time.
3. **No multi-repo model** — work that spans repos (coordinated edits, cross-repo contracts) has no
   harness representation; `add_repo` is a session primitive, not a declared workspace.

**North star:** an agent (and a human) can carry a *multi-project* body of work across *many
sessions and a long calendar time* while the project's own context (code graph, memory, docs,
decisions) stays automatically fresh — machines maintain, humans ratify.

## What already exists (REUSE — do not rebuild)

- **Two-plane memory** (`.memory/state` committed · `.memory/derived` gitignored), `tools/memory_regen`
  (repo-map: tree-sitter + networkx PageRank; contracts-index), SessionStart injector.
- **`/docs-sync`** (contracts → Diátaxis `reference/`), **`/orient`**, **ADR** (immutable, append-only).
- **pause-work / resume-work** + `.continue-here.md` / `HANDOFF.json`, **session-report**.
- **GSD `.planning/`** (STATE / ROADMAP / PROJECT) — project-level memory scaffolding.
- **orchestrator persona** + `Task`/`Explore`/`Workflow` delegation; **Phase 8 pipeline-topology**
  slot + conductor (a within-instance dataflow model to generalize across repos).
- **Phase 6 CI gates** + **Phase 7 re-emit-diff gate** (the pattern α extends: CI regenerates a
  derived artifact and fails on diff = "stale derived").
- **`harness/project.toml` slot pattern** (languages, components, pipeline) — the pattern γ lifts one
  level to a workspace slot.

---

## Phase α — Self-Maintaining Derived Artifacts + Curator  (draft REQ: MAINT-01..)

**Goal:** derived artifacts (repo-map, contracts-index, docs `reference/`, memory) are kept fresh
**automatically at merge**, enforced by CI the same way Phase 7 enforces emit-diff — no human
babysitting. A `curator` agent owns this maintenance.

**Scope (draft):**
- **MAINT-01** A `curator` agent (read-mostly; regenerates derived artifacts, never hand-edits them)
  — the single owner of "keep derived fresh."
- **MAINT-02** A CI "stale-derived" gate: on PR, regenerate repo-map / contracts-index / docs
  `reference/` and **fail on diff** (mirror Phase 7's re-emit-diff). This decides which derived
  artifacts become *committed-and-PR-refreshed* vs *session-regenerated-and-gitignored* (KEY
  DECISION below).
- **MAINT-03** A hook posture: cheap refresh on write (format-on-write class); heavy regen deferred
  to PR/CI (never per-commit — too slow/noisy).
- **MAINT-04** A `/refresh-memory` (or curator-invoked) command that runs the full regen set locally
  before handoff, so `/verify-work` can include a freshness check.

**Reuse:** `tools/memory_regen`, `/docs-sync`, Phase-7 re-emit-diff gate, two-plane-memory skill.
**Strong tie to Phase 7:** the curator agent + its hooks must be emitted to both runtimes.
**Key open decision (α):** which derived artifacts flip from gitignored-derived to committed-derived
so a PR can refresh them without violating "derived is not hand-edited" (they'd be machine-written,
CI-verified — still never hand-edited).

## Phase β — Context-Economy Fan-out/Synthesize Orchestration  (draft REQ: ECON-01..)

**Goal:** a first-class workflow where the main/orchestrator session spawns subagents to analyze
(per file / per subsystem / per repo), returns **only distilled summaries**, and the orchestrator
**synthesizes** — keeping the long-lived session's context small. This is the mechanism behind both
"long session" and (with γ) "multi-repo analysis."

**Scope (draft):**
- **ECON-01** A `fan-out-synthesize` skill/command (deep-research / `Workflow` shape): decompose a
  task → dispatch N analyst subagents → collect schema-bounded summaries → synthesize. Reusable by
  humans and by the conductor.
- **ECON-02** A summary/return contract: subagents return compact, citation-bearing results (paths +
  claims, not file dumps) so the orchestrator never re-reads raw files.
- **ECON-03** Guidance/skill on when to delegate vs inline (context-budget heuristics), wired into
  the orchestrator persona and `/orient`.

**Reuse:** orchestrator persona, `Task`/`Explore`/`Workflow`, deep-research skill shape.
**Note:** likely SMALL — authored skills/commands, not new runtime machinery.

## Phase γ — Multi-Repo Workspace  (draft REQ: MREPO-01..)

**Goal:** declare and operate on **multiple repos** as one workspace: an orchestrator delegates
per-repo analysis to repo-scoped subagents (β) and synthesizes; cross-repo contracts are declared
and drift-gated like single-repo contracts.

**Scope (draft):**
- **MREPO-01** A workspace model + manifest — lift the `harness/project.toml` slot pattern one level:
  declare member repos + cross-repo edges (which repo produces/consumes which contract). (KEY
  DECISION: which of the three models below.)
- **MREPO-02** Repo-scoped subagents + the β fan-out/synthesize applied across repos (per-repo
  analysis → workspace-level synthesis), so no single context holds all repos.
- **MREPO-03** Cross-repo contract drift/golden gates (extend Phase-6 CI + `contract_drift` across
  the workspace).
- **MREPO-04** The pipeline-topology (Phase 8) generalized so edges can cross repo boundaries.

**Reuse:** session `add_repo`, `harness/project.toml` slot pattern, Phase-8 topology, Phase-6 CI,
`contract_drift`/`contract_hash`.
**Key open decision (γ) — workspace model:**
- (a) **Session `add_repo` federation** — lightest; repos added per session, no persisted manifest.
- (b) **Workspace manifest** (RECOMMENDED) — a `workspace.toml`-style slot declaring member repos +
  cross-repo contracts; the harness reads it (mirrors the project.toml slot posture).
- (c) **Meta-repo** (submodules / worktrees) — heaviest; one repo of repos.

---

## Cross-cutting constraints (all phases — non-negotiable)

- **Two-plane memory** respected; **derived never hand-edited** (machine-written + CI-verified is OK).
- **Machines gate, humans ratify** — curator/CI may regenerate + block, but constitution-plane
  (contracts / adr / golden) writes stay human-ratified (GOLDEN_APPROVE_HUMAN).
- **GEN-04** core→example (and, for γ, core→workspace-member) no-dependency stays green.
- **Runtime limits** honored via Phase 7 emit validators (skill/desc/body caps, opencode permission
  matrix); every new agent/skill/hook must round-trip through the emitter.
- **opencode primary**, Claude Code secondary; **no model identifiers** in repo artifacts.
- Prefer **PR/CI enforcement** over per-commit local hooks for anything heavy.

## Open decisions to resolve at plan time
1. (α) committed-derived vs session-derived split for PR refresh.
2. (γ) workspace model a / b / c (lean b).
3. Milestone numbering: continue (9/10/11) vs `--reset-phase-numbers` (v2-P1..). Lean continue.
4. Whether β is one phase or folds into α/γ as a shared skill (lean: keep β as its own small phase —
   it's the reusable substrate for γ).

## How to open v2 (after Phase 7 ships)
`/gsd:new-milestone "Long-Horizon: self-maintaining memory + multi-repo"` — it will read THIS file,
confirm scope, define MAINT-/ECON-/MREPO- requirements, and spawn the roadmapper for phases α/β/γ.
