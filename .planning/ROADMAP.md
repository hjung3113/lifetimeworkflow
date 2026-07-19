# Roadmap: Contract-First 폴리글랏 에이전트 하네스 템플릿

> **Re-scope (2026-07-08, ADR-0002):** 원래 반도체 로그파서 전용 하네스로 Phase 1–4를 완주했으나, 재사용 가능한 **범용 템플릿**으로 재정의. 완료된 Phase 1–4(도메인 시드 포함)는 유지하고, **새 Phase 5 "De-specialization & Template Extraction"**을 삽입해 도메인·언어 특화 콘텐츠를 `examples/log-parser/`로 격리 + 코어 중립화한다. 기존 Phase 5(CI)·6(Emitter)은 6·7로 밀리며 **generic 관점으로 재범위**된다(하드코딩 `dotnet test`/`pytest` 대신 설정형 매트릭스).

## Overview

This harness is a config compiler plus runtime overlay — not an application — so it is built bottom-up in the order the risk profile dictates. Phases 1–4 proved the durable core on a concrete domain instance (semiconductor log-parser): one real contract→golden→drift→human-approval loop, the two-plane memory + rules, the full authored agent/command/skill surface, and the runtime hooks that enforce what prose only advises. **Phase 5 now extracts that durable core from its domain instance** — demoting the log-parser contracts/normalization/toy-converter to `examples/log-parser/` behind an ADR + hash re-baseline, and turning the hardwired .NET+Python assumption into a project-config slot — so the harness becomes a reusable template any project can fill in. Then a generic non-bypassable CI mirror (config-driven language matrix, not hardcoded jobs) plus human ratification, and finally the single-source emitter that produces both opencode and Claude Code runtime artifacts. The operative principle throughout: machines gate, humans ratify; agents may propose but never self-bless a golden or auto-mutate the constitution plane. **New principle (ADR-0002): the core is domain- and language-neutral; specialization lives only under `examples/<instance>/`, and the core never depends on an example.**

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Constitution + Golden Core** - Walking skeleton: seed contracts, build the shared normalization comparator + golden runner + contract-drift gate, and close one real legacy↔new equivalence loop end-to-end. (completed 2026-07-08)
- [x] **Phase 2: Two-Plane Memory + Rules** - Constitution-vs-derived memory split, auto-regenerated derived artifacts, nearest-wins AGENTS.md, and non-ignorable session-start context injection. (completed 2026-07-08)
- [x] **Phase 3: Agents + Commands + Skills** - The full authored harness surface — personas, commands, skills — in canonical source, with migration commands gated behind the trusted golden net. (completed 2026-07-08)
- [x] **Phase 4: Plugins + Hooks** - Runtime enforcement of everything authored in Phases 1-3: contract-guard, polyglot linter, format-on-write, secret protection, commit gate. (completed 2026-07-08)
- [x] **Phase 5: De-specialization & Template Extraction** *(INSERTED — ADR-0002 re-scope)* - Demote the log-parser domain seed to `examples/log-parser/` (ADR + hash re-baseline), turn hardwired .NET+Python into a project-config slot, add a minimal generic default instance, and prove the core is example-free (core→example CODE no-dependency, SCOPE A: data plane). (completed 2026-07-09)
- [x] **Phase 5.5: Authored-Surface Genericization** *(INSERTED — GEN-05, data-plane follow-up)* - Demote domain skills (`normalization-catalog`, `new-normalization-rule`, `pipeline-patterns`) to the example, derive per-language personas from the `harness/project.toml` slot, sweep residual `libs/dotnet`-style domain prose in core, and extend the GEN-04 guard to prose. (completed 2026-07-09)
- [x] **Phase 5.7: Lifecycle Completeness** *(INSERTED — LIFE-01..11, adversarial-review reinforcement)* - The authored surface is too thin for an agent to carry a unit of work through the full dev lifecycle. An adversarial audit (2026-07-09) found load-bearing gaps: a dangling `/contract-check`, ZERO golden-mismatch/§4.3-4.6 debug surface, the polyglot Core Value scattered as tribal prose, no neutral language-engineer template, and MISSING plan/onboard/review/integrate assets. Add domain-neutral skills/commands (contract-check, golden-debug, polyglot-boundary, gate-model, two-plane-memory, /orient, /review, /verify-work, language-engineer scaffold) + de-domain `/new-normalization-rule`, so the contract→implement→test→debug inner loop and the full lifecycle are actually executable end-to-end. **DONE 2026-07-09** — 057-RESEARCH/VALIDATION/01-PLAN/02-PLAN; two waves; `EXPECTED_SKILLS` 4→8; non-example suite green (402); GEN-04/05 prose guard clean.
- [x] **Phase 6: CI + Gates (generic)** - Non-bypassable CI mirror of the in-session gates plus the human ratification path (CODEOWNERS, PR template), driven by a **config-derived** language matrix rather than hardcoded `dotnet test`/`pytest` jobs; the example instance supplies its own .NET+Python matrix. (completed 2026-07-09)
- [x] **Phase 7: Single-Source Dual-Runtime Emitter** - One authored source compiles into both opencode (primary) + Claude Code (secondary) artifacts, with per-runtime limit validators that fail loud. (completed 2026-07-12)
- [x] **Phase 8: Pipeline-Topology Conductor + Per-Component Agents** *(ADDED — post-Phase-6 user request; independent of Phase 7)* - Evolve the agent model from per-language to pipeline-aware: a generic pipeline-topology slot in the neutral core, an `orchestrator` upgraded into a dataflow-aware conductor that routes by pipeline stage/component, a neutral `component-engineer` template, and a concrete 4-component demonstration in `examples/log-parser/` (parser→converter→scheduler→collector). (completed 2026-07-11)

**Milestone v2.0 — Long-Horizon** *(phases 9/10/11 — numbering continues after v1.0 = phases 1–8; reuses existing machinery, no rebuild)*

- [x] **Phase 9: Self-Maintaining Derived Artifacts + Curator** *(v2.0 α)* - A read-mostly `curator` agent + a CI “stale-derived” gate keep derived artifacts (repo-map, contracts-index, docs `reference/`, memory) fresh automatically — machines regenerate, CI verifies on PR, humans never hand-edit; heavy regen deferred to PR/CI (not per-commit). (completed 2026-07-13)
- [x] **Phase 10: Context-Economy Fan-out/Synthesize Orchestration** *(v2.0 β)* - A first-class fan-out → schema-bounded citation-bearing summary → synthesize workflow keeps long-lived sessions small; the reusable substrate γ builds on. (completed 2026-07-13)
- [x] **Phase 11: Multi-Repo Workspace** *(v2.0 γ)* - Declare and operate several repos as one workspace: a workspace manifest, repo-scoped subagents running the β fan-out, cross-repo contract-drift/golden gates, and repo-crossing pipeline edges. (completed 2026-07-14)

**Milestone v2.1 — MEM2 — Process Memory & Provenance Reframe** *(phases 12–16 — numbering continues after v2.0 = phases 9–11; reuses existing machinery — `tools/memory_regen`, `/checkpoint`, `tools/harness_lint`, Phase-7 emitter, `adr`+CODEOWNERS — no rebuild)*

- [x] **Phase 12: Model + ADR + Doc Reframe** *(v2.1 A)* - Scaffold the new PROCESS memory tier (`.memory/agreements/<slug>.md` per-guideline, committed human-authored — NOT derived), reword the distrust framing to data-authority everywhere it echoes, and ratify the memory-model change as ADR-0006 via the human-gated constitution path. (completed 2026-07-14)
- [x] **Phase 13: Injector Reframe + Channel Wiring** *(v2.1 B)* - Split the SessionStart banner into a full-body priority-0 working-agreements directive + a data-scoped provenance banner, and surface a verbatim progress `updated:` stamp — preserving `inject.py` determinism and the ~4000-char budget. (completed 2026-07-16)
- [x] **Phase 14: Write Path + Anti-Churn Guard** *(v2.1 C)* - A dedicated `/agree` command adds/retires a working-agreement only on explicit user feedback, backed by a `tools/harness_lint` provenance/anti-invent guard. (completed 2026-07-16)
- [x] **Phase 15: Emit Round-Trip + Gates** *(v2.1 D)* - Round-trip every new/changed surface (`/agree`, updated skills, AGENTS.md managed block) through the Phase-7 emitter to both runtimes with no model id; emit-drift clean, GEN-04 green. (completed 2026-07-15)
- [x] **Phase 16: Local Memory Web UI** *(v2.1 E)* - A local, no-network, no-auth tool to view/edit/retire memory items with pointer-aware referential integrity over a machine-built derived pointer-index. (completed 2026-07-18)
- [x] **Phase 17: Constitution-Gate Dev/Enforce Decoupling** *(infra — independent of v2.1 MEM2)* - A secure-default `HARNESS_DEV_BYPASS` env opt-out so the product's constitution gates stop governing the Claude dev session (default enforce; blank = no bypass; distinct from `GOLDEN_APPROVE_HUMAN`; byte-hygiene never waived), honored by `contract_guard`/`commit_gate`; ADR-0007 records it; CODEOWNERS stays the real gate. (completed 2026-07-15)

**Milestone v2.2 — Adaptive Task Control Plane** *(phases 18–23 — numbering continues after v2.1 = phases 12–17; reuses existing machinery — orchestrator, GSD, two-plane memory, `/review`·`/verify-work`·`/checkpoint`, contract-drift/golden/CI, Phase-7 emitter — no rebuild. Design: `docs/explanation/next-milestone-task-control-plane.md`, codex sol via sol-vs-fable debate. Locked: A=`.workflow/tasks/`, B=6 phases. Contract-first vertical slice — each phase depends on the prior.)*

- [x] **Phase 18: Task Packet Contract Ratification** *(v2.2 A)* - Fix the shape and ownership of task state before any code: human-ratified JSON Schema for TASK/STATE/EVIDENCE/HANDOFF, a `.workflow/tasks/<id>/` instance slot independent of `.memory/state/`, phase/lane enums + allowed-transition table, contract-drift baseline + paired golden. (TCP-01, TCP-02)
- [x] **Phase 19: Deterministic Risk Router** *(v2.2 B)* - A pure-function 7-axis scorer → FAST/STANDARD/STRICT/CONTROLLED lane with byte-identical output, auto-promotion reason codes, per-lane required-artifact matrix, escalate-only instance overlay slot, and the `/intake` entry point that keeps FAST ceremony-free. (TCP-03, TCP-04, TCP-05, TCP-06)
- [x] **Phase 20: Atomic State Manager + Context/Transition Gate** *(v2.2 C)* - Concurrency-safe atomic state transitions (temp-write+rename, revision CAS, interrupted-write recovery) plus a fail-closed phase-start gate (git ref / baseline / worktree / constraint attestation) surfaced as `/phase-gate`. (TCP-07, TCP-08, TCP-09, TCP-10)
- [x] **Phase 21: Evidence Bundle Adapters** *(v2.2 D)* - Collect (never reimplement) existing gate results into tamper-evident, criterion-traced evidence with command·exit·SHA-256, strict skip≠pass, secret refusal, wired to `/review` and `/verify-work`. (TCP-11, TCP-12, TCP-13)
- [x] **Phase 22: Handoff + Fresh-Session Resume** *(v2.2 E)* - An immutable HANDOFF snapshot a fresh session reconstructs 100% from, with `/checkpoint`·`/orient`·`/handoff` revisions and a pointer-only SessionStart injection preserving the ~1k cap. (TCP-14, TCP-15)
- [x] **Phase 23: Lifecycle Evaluation + Docs + CI** *(v2.2 F)* - 20 ratified domain-neutral lifecycle fixtures (5/lane) + stress/negative cases, a ceremony cap on FAST, a how-to doc, a human-ratified structural ADR, and CI fan-in keeping every existing gate green. (TCP-16, TCP-17, TCP-18)

**Milestone v2.3 — Contract Graph, Brownfield Adoption, Living Docs** *(phases 24–29 — numbering continues after v2.2 = phases 18–23; reuses existing machinery — contract-hash/drift, golden comparator, §4.3–4.6 normalize core, config/workspace loaders, task-control CAS/evidence/HANDOFF, fan-out substrate, `/docs-sync`·`/refresh-memory`, Phase-7 emitter — no rebuild. Design: `.planning/research/v2.3-scoping-FINAL.md`, sol-vs-fable debate → codex sol merged FINAL, human-approved. DAG `24→25→28→29` and `24→26→27→29`.)*

- [x] **Phase 24: Contract-Relationship Vocabulary + Compatibility** *(v2.3 A)* - The ratified graph record (`contracts/harness/topology/`), additive `[[contract_graph.relationships]]` TOML slot with thin-loader passthrough, and deterministic legacy `[pipeline]`→graph lowering that unions additively and leaves current linear fixtures byte-unchanged. (TOPO-01, TOPO-02, TOPO-03) (completed 2026-07-19)
- [ ] **Phase 25: Graph Compiler, Queries, Conductor, Proof** *(v2.3 A)* - One domain-neutral compiler + `harness_lint` consistency gate, cycle-safe affected-set queries, `/pipeline`·`pipeline-map`·orchestrator generalized (no new command/persona), non-linear generic + cross-repo fixtures, and a human-ratified topology ADR. (TOPO-04, TOPO-05, TOPO-06, TOPO-07)
- [ ] **Phase 26: Deterministic Brownfield Inventory + Mapping** *(v2.3 B)* - A read-only deterministic repo inventory, an evidence-classified (observed/inferred/unknown) mapping plan in the TOPO vocabulary, and a complete destination/disposition manifest — agent-free, fully CI-testable. (ADOPT-01, ADOPT-02, ADOPT-03)
- [ ] **Phase 27: Task-Local Adoption Workflow + Safe Application** *(v2.3 B)* - Adoption as a `.workflow/tasks/` task (reusing v2.2 CAS/evidence/HANDOFF), structural constitution-write refusal + idempotent collision-safe apply, hash-bound human ratification, and the `/adopt` skill+command with three fixtures (one §4.3–4.6-dirty). (ADOPT-04, ADOPT-05, ADOPT-06, ADOPT-07)
- [ ] **Phase 28: Human-Docs Registry, Guard, Derived Queue** *(v2.3 C)* - Central `docs/doc-dependencies.toml` + review ledger, deterministic fingerprints, the FRESH/BROKEN/STALE_REQUIRED/STALE_ADVISORY/UNCOVERED gate, ADR-safe dispositions, and a derived staleness queue + conditional SessionStart pointer. (DOCSUP-01, DOCSUP-02, DOCSUP-03, DOCSUP-04, DOCSUP-05)
- [ ] **Phase 29: Docs Drive Loop + Adoption Integration + Closeout** *(v2.3 C)* - The `/docs-update` drive loop (ADR/reference/derived excluded), reviewed seeding of the high-risk corpus + adoption-runbook bindings, and the milestone closeout against the full existing gate fan-in. (DOCSUP-06, DOCSUP-07)

## Phase Details

### Phase 1: Constitution + Golden Core

**Goal**: The contract-first safety net proves one real legacy↔new equivalence loop end-to-end on seeded domain contracts — the walking skeleton, not exhaustive scaffolding.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: CONTRACT-01, CONTRACT-02, CONTRACT-03, CONTRACT-04, BOOT-01, BOOT-02, BOOT-03, DOCS-01, DOCS-02
**Success Criteria** (what must be TRUE):

  1. Seeded contracts (TSV log spec, normalization catalog, reference-data, state/carryover) exist in `contracts/` as clearly-flagged placeholders, and `docs/` carries a Diátaxis skeleton (tutorials/how-to/reference/explanation) + `adr/0001` + glossary.
  2. A real contract (schema) change, canonicalized via RFC 8785 and hashed to SHA-256, trips the contract-drift gate and is classified breaking vs. non-breaking — and the hash covers the §4-5 cross-cutting conventions, not just the column list.
  3. A legacy↔new fixture differing only in BOM/CRLF/decimal-locale/timezone PASSES the golden runner via normalized equivalence, while a genuine value regression FAILS it — no byte-diff false reds.
  4. `/golden` runs a fixture and surfaces a normalized diff; `/golden-approve` refuses to update the baseline without a CODEOWNERS human sign-off (no agent self-bless).
  5. The .NET 10 SDK installs via `dotnet-install.sh --channel 10.0` and the `uv` workspace resolves, so both toolchains execute a golden run inside the ephemeral container.

**Plans**: 6 plans (3 waves)
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Bootstrap toolchain: .NET 10 SDK + uv workspace + idempotent SessionStart wiring (BOOT-01/02/03)
- [x] 01-03-PLAN.md — Diátaxis docs skeleton + glossary + MADR adr/0001 (DOCS-01/02)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Seed contracts + companion Draft 2020-12 schemas + materialized §4-5 conventions schema (CONTRACT-01)
- [x] 01-04-PLAN.md — Shared §4-5 normalization comparator: neutral spec + dual .NET/Python impl cross-validated by shared corpus (CONTRACT-02)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-05-PLAN.md — Contract-drift gate: RFC 8785 JCS hash manifest + breaking/non-breaking classification, covers §4-5 (CONTRACT-04)
- [x] 01-06-PLAN.md — Golden loop: .NET toy converter + Python golden-runner + two fixtures + /golden-approve refusal gate (CONTRACT-03)

### Phase 2: Two-Plane Memory + Rules

**Goal**: The constitution-vs-derived memory split is established before any agent consumes context, with derived artifacts regenerated (never hand-maintained) and volatile state injectable at session start.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: MEM-01, MEM-02, MEM-03, RULES-01, RULES-02, HOOK-05
**Success Criteria** (what must be TRUE):

  1. The constitution plane (`contracts/`, `docs/adr/`, `glossary`, `golden/`) is laid out as human-owned and marked immutable to agents; the derived/volatile plane (`.memory/`: activeContext, progress, repo-map, contracts-index) is gitignored.
  2. `repo-map` (tree-sitter + PageRank) and `contracts-index` regenerate from code/contracts on demand — deleting them and rerunning the generator reproduces them, proving nothing is hand-edited.
  3. Root `AGENTS.md` (monorepo map, golden-path, contract-first, lazy-load rules) plus per-package .NET and Python `AGENTS.md` resolve nearest-wins, and a `CLAUDE.md` pointer exists.
  4. Session-start injection injects pointers/indexes (not full contract payloads, capped size) and marks volatile state provisional, so an ADR always overrides memory.

**Plans**: 5 plans (2 waves)
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Two-plane `.memory/` layout + gitignore boundary + `tools/memory_regen` uv member with pinned tree-sitter/networkx (MEM-01, MEM-02)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Claude SessionStart injector: shared `inject.assemble` contract (capped/banner/priority-truncate) + 4th-slot hook + authored-deferred opencode stub (HOOK-05)
- [x] 02-03-PLAN.md — contracts-index generator: scan contracts/ + reuse Phase-1 hash/drift modules → deterministic `.memory/derived/contracts-index.md` (MEM-03)
- [x] 02-04-PLAN.md — repo-map generator: tree-sitter 0.25 parse + networkx PageRank → deterministic token-bounded `.memory/derived/repo-map.md` (MEM-03)
- [x] 02-05-PLAN.md — Nearest-wins `AGENTS.md`: root + per-package .NET/Python (restated non-negotiables, P11) + `CLAUDE.md` pointer (RULES-01, RULES-02)

### Phase 3: Agents + Commands + Skills

**Goal**: The full enumerated harness surface exists in canonical source, sequenced so golden-adjacent commands land before migration commands, which stay gated behind a *trusted* (not merely present) golden net.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: CONFIG-01, CONFIG-02, AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, CMD-01, CMD-02, CMD-03, CMD-04, CMD-05, CMD-06, CMD-07, CMD-08, CMD-09, SKILL-01, SKILL-02, DOCS-03
**Success Criteria** (what must be TRUE):

  1. `opencode.json` defines model tiering (cheap explorer / expensive implementer), instructions glob, formatter, and MCP wiring; the 15-key permission matrix resolves bash globs last-wins, scopes the reviewer read-only, and denies secret/constitution writes.
  2. Five agent personas (orchestrator, dotnet-engineer, python-engineer, read-only code-reviewer, explorer) load scoped by permission and model tier.
  3. Golden-adjacent commands (`/build`·`/test`·`/lint`, `/golden` contract-check, `/adr`, `/checkpoint`, `/component`) work; `/new-normalization-rule` enforces the contract → data-based (input,expected) case → code order.
  4. `/strangler-step` refuses to run without a captured legacy golden baseline — it extracts one path only and requires `/golden` parity to pass — and `/docs-sync` regenerates `docs/reference/` purely from contracts (no hand-written reference).
  5. Core and domain skills (dotnet-conventions, python-conventions, golden-testing, data-contracts, normalization-catalog, pipeline-patterns, skill-creator) load with progressive disclosure under each runtime's size cap.

**Plans**: 7 plans (3 waves)
Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Permission matrix data + last-wins glob resolver (runnable, unit-tested; reused by Phase-4 hooks) (CONFIG-02)
- [x] 03-02-PLAN.md — opencode.json config + vendored subset schema + harness_lint foundation (shared frontmatter parser + opencode.json structural test) (CONFIG-01)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-03-PLAN.md — 5 agent personas (dual-representation, routing-signal descriptions) + read-only-reviewer structural validator (AGENT-01..05)
- [x] 03-04-PLAN.md — 8 golden-adjacent command macros (/build /test /lint /golden /golden-approve /adr /checkpoint /component) + glob command validator (CMD-01/02/03/04/07/09)
- [x] 03-05-PLAN.md — 7 skills (4 core + skill-creator + 2 domain) progressive disclosure + structural cap validator (SKILL-01/02)

**Wave 3** *(blocked on Wave 2 completion — migration commands gated behind the golden-adjacent surface, D-05)*

- [x] 03-06-PLAN.md — Runnable /docs-sync generator (contracts→reference, deterministic) + command + generated reference pages (CMD-08, DOCS-03)
- [x] 03-07-PLAN.md — Migration commands: runnable /strangler-step baseline-refusal gate + /new-normalization-rule order scaffold (CMD-05, CMD-06)

### Phase 4: Plugins + Hooks

**Goal**: Everything authored in Phases 1-3 is enforced at runtime by non-bypassable hooks, because prose rules are advisory and hooks are not.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: HOOK-01, HOOK-02, HOOK-03, HOOK-04, POLY-01
**Success Criteria** (what must be TRUE):

  1. `contract-guard` blocks or asks on any write to `contracts/`/`adr/`/`golden/` without an approval path, and enforces on-write encoding/TSV rules.
  2. The polyglot-boundary linter runs the `integration_contracts` §4-5 checklist (encoding/BOM/LF/TSV-escape/timezone/decimal-locale/null-vs-empty/atomic-write/identifier rules) on-write and in-session, failing loud, and shares Phase 1's normalization core (built once, not re-implemented).
  3. `format-on-write` enforces LF / no-BOM / InvariantCulture on every edit, and secret protection blocks secret read/write via deny-list + pattern scan.
  4. The commit gate blocks commits when contract-drift, golden parity, or the polyglot linter fail; a permission-matrix order-resolution test suite proves last-wins glob behavior and default-deny on constitution-plane edits.

**Plans**: 6 plans

Plans:
- [x] 04-01-PLAN.md — POLY-01 polyglot §4.3-4.6 boundary linter (detection-by-normalization, shares normalize.core)
- [x] 04-02-PLAN.md — tools/hooks shared stdin adapter + HOOK-02 secret protection (resolver path-deny + shape-anchored regex)
- [x] 04-03-PLAN.md — HOOK-04 contract-guard (constitution-plane deny + GOLDEN_APPROVE_HUMAN bypass + on-write TSV)
- [x] 04-04-PLAN.md — HOOK-01 format-on-write (BOM/LF byte-fix + ruff, dotnet-format gated-skip, idempotent)
- [x] 04-05-PLAN.md — HOOK-03 commit-gate (drift + golden[skip] + polyglot) + permission order-resolution suite
- [x] 04-06-PLAN.md — Claude hook wiring (coexist) + coexist test + authored opencode plugin stubs

### Phase 5: De-specialization & Template Extraction *(INSERTED — ADR-0002)*

**Goal**: The durable harness core is cleanly separated from its log-parser domain instance, so the repo is a reusable template: domain contracts/normalization/toy-converter move to `examples/log-parser/`, the .NET+Python assumption becomes a project-config slot, and the core provably depends on no example.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04 (see REQUIREMENTS.md v1 §GEN)
**Success Criteria** (what must be TRUE):

  1. The log-parser domain seed — `contracts/{log-specs,reference-data,normalization,state}`, `libs/{python/normalize,dotnet/Normalize,normalize-fixtures}`, `components/toy-converter`, and its `golden/` cases — is relocated under `examples/log-parser/` behind a new ADR (0002 or successor) and a re-baselined contract-hash manifest, so the live contract-drift gate reads clean AFTER the move (no orphaned/broken drift baseline).
  2. A minimal, domain-neutral **default instance** exists at the repo root (a generic sample contract + its golden fixture) that exercises the full contract→hash→drift→golden loop without any semiconductor-log content — proving the machinery runs on a blank domain.
  3. The participating languages/toolchains are read from a single project-config slot (e.g. `harness/project.toml`); the permission matrix's `dotnet */uv */pytest *` scopes, the engineer personas, and the `/build`·`/test`·`/lint` command bodies derive from that config rather than hardcoding .NET+Python — and the log-parser example supplies the .NET 10 + Python(uv) values.
  4. A guard test proves **core→example single-direction dependency**: nothing under `tools/`, `harness/`, `libs/` (core) imports or path-references `examples/**`; the full non-example test suite stays green after extraction.
  5. Root docs (`CLAUDE.md`, root `AGENTS.md`, `docs/`) describe the template + how to add an instance, with log-parser specifics moved into the example's own `AGENTS.md`/README.

**Plans**: 5 plans (4 waves)

Plans:
**Wave 1**

- [x] 05-01-PLAN.md — D-05 commit-gate drift approval path: `GOLDEN_APPROVE_HUMAN` warn+pass on drift (polyglot/golden stay hard); core-only, lands first
- [x] 05-04-PLAN.md — GEN-03 language config slot: `harness/project.toml` SSOT + thin `tools/harness_config` loader + consistency test (matrix scopes/personas derive from config)

**Wave 2** *(blocked on 05-01)*

- [x] 05-02-PLAN.md — GEN-02 generic default instance: `contracts/sample/greeting.schema.json` + `golden/sample/**` + golden_runner identity converter/golden_dir; full loop runs .NET-free; rebaseline root manifest

**Wave 3** *(blocked on 05-01, 05-02)*

- [x] 05-03-PLAN.md — GEN-01 domain MOVE: `git mv` seed → `examples/log-parser/`; rebaseline root + example manifests (drift clean); move domain golden tests; regen 3 snapshots

**Wave 4** *(blocked on 05-03, 05-04)*

- [x] 05-05-PLAN.md — GEN-04 core→example no-dependency guard + root docs recast (template + instance) + ADR-0002 (via approval path)

### Phase 6: CI + Gates (generic)

**Goal**: A non-bypassable CI mirror of the in-session plugin gates plus the human ratification path completes the "machines gate, humans ratify" loop — driven by a config-derived language matrix so it stays reusable across instances, not hardwired to one domain's toolchain.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: CI-01, CI-02
**Success Criteria** (what must be TRUE):

  1. A GitHub Actions matrix runs the **config-derived** per-language test jobs + the generic `contract-check`/drift/golden jobs as non-bypassable checks on every PR, installing each configured toolchain and resolving workspaces idempotently as part of the run. The log-parser example contributes the `.NET 10 + pytest` legs (this is where the .NET egress deferral finally runs for real, on GitHub runners).
  2. A golden or contract-drift failure in CI blocks merge and cannot be skipped by an agent.
  3. CODEOWNERS gates `contracts/`, `adr/`, and `golden/` (and the example instances' equivalents) so only a human ratifies constitution-plane and golden-baseline changes.
  4. The PR template carries a lightweight breaking-change / golden checklist that surfaces on every pull request.

**Plans**: 3 plans (2 waves)
- [x] 06-01-PLAN.md — Enabler-1: per-language `test_paths` config slot + loader passthrough + matrix-shape Wave-0 test (Wave 1)
- [x] 06-02-PLAN.md — Enabler-2: `--contracts-dir`/`--baseline`/`--manifest` argparse on drift+hash CLIs for example-manifest gating (Wave 1)
- [x] 06-03-PLAN.md — Workflow: config-derived `.github/workflows/ci.yml` + CODEOWNERS + PR template (Wave 2)

### Phase 7: Single-Source Dual-Runtime Emitter

**Goal**: One authored harness source compiles into both runtime-native artifact sets, built last because it is a pure function of the Phase 2-5 source and has nothing to compile until they exist.
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: EMIT-01, EMIT-02
**Success Criteria** (what must be TRUE):

  1. `tools/harness-emit` generates `.opencode/{agent,command,skill,plugin,tool}` + `opencode.json` + `AGENTS.md` (primary target) from a single `harness/` source of truth.
  2. The same source emits `.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md` (secondary target), respecting each runtime's shape and leaving the quarantined `.claude/get-shit-done/` untouched.
  3. Per-runtime limit validators (Claude skill description/body caps, opencode permission-matrix shape) FAIL the build rather than silently truncating.
  4. A CI check re-emits and diffs the generated surfaces to catch any hand-edited generated-artifact drift.

**Plans**: 5 plans (5 waves)

Plans:
**Wave 1** *(agent-first walking slice — D-05: through EVERY mechanic)*

- [x] 07-01-PLAN.md — Agents walking slice: emit spine + agent projection + loud-fail validators + ownership manifest + committed .opencode/agent + .claude/agents + emit-drift CI gate (EMIT-01/02)

**Wave 2** *(blocked on 07-01)*

- [x] 07-02-PLAN.md — Widen: commands (17) + skills (9, references/ byte-copy); GSD command non-collision (EMIT-01/02)

**Wave 3** *(blocked on 07-02)*

- [x] 07-03-PLAN.md — opencode primary: verbatim .ts plugin copy + permission-matrix→opencode.json 15-key block + schema loud-fail (EMIT-01/02)

**Wave 4** *(blocked on 07-03 — risky merge surface #1)*

- [x] 07-04-PLAN.md — merge.py Markdown managed-block splice into shared AGENTS.md + CLAUDE.md (preserve GSD/human content) (EMIT-02)

**Wave 5** *(blocked on 07-04 — risky merge surface #2, Pitfall-4 double-wiring)*

- [x] 07-05-PLAN.md — merge.py settings.json signature merge: idempotent coexistence, exactly 4 SessionStart groups, GSD hooks survive (EMIT-02)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Constitution + Golden Core | 6/6 | Complete   | 2026-07-08 |
| 2. Two-Plane Memory + Rules | 5/5 | Complete   | 2026-07-08 |
| 3. Agents + Commands + Skills | 7/7 | Complete   | 2026-07-08 |
| 4. Plugins + Hooks | 6/6 | Complete   | 2026-07-08 |
| 5. De-specialization & Template Extraction | 5/5 | Complete   | 2026-07-09 |
| 5.5. Authored-Surface Genericization (INSERTED) | 3/3 | Complete|  |
| 6. CI + Gates (generic) | 3/3 | Complete   | 2026-07-09 |
| 7. Single-Source Dual-Runtime Emitter | 5/5 | Complete   | 2026-07-12 |
| 8. Pipeline-Topology Conductor + Per-Component Agents | 6/6 | Complete   | 2026-07-11 |
| 9. Self-Maintaining Derived Artifacts + Curator | 4/4 | Complete   | 2026-07-13 |
| 10. Context-Economy Fan-out/Synthesize Orchestration | 3/3 | Complete    | 2026-07-13 |
| 11. Multi-Repo Workspace | 4/4 | Complete    | 2026-07-14 |
| 12. Model + ADR + Doc Reframe (v2.1 A) | 3/3 | Complete | 2026-07-14 |
| 13. Injector Reframe + Channel Wiring (v2.1 B) | 0/TBD | Not started | - |
| 14. Write Path + Anti-Churn Guard (v2.1 C) | 0/TBD | Not started | - |
| 15. Emit Round-Trip + Gates (v2.1 D) | 2/2 | Complete    | 2026-07-15 |
| 16. Local Memory Web UI (v2.1 E) | 6/6 | Complete    | 2026-07-18 |

### Phase 8: Pipeline-Topology Conductor + Per-Component Agents

**Goal**: Evolve the harness agent model from per-**language** to pipeline-**aware**. Today the primary `orchestrator` routes by work-shape and delegates to per-language specialists (`python-engineer` + a derived `dotnet-engineer`); it has no model of the pipeline dataflow, and agents don't map to pipeline components (parser/converter both collapse into "dotnet-engineer"). This phase adds a generic pipeline-topology declaration to the neutral core, evolves the `orchestrator` into a topology-aware **conductor** that understands the end-to-end dataflow (stage→stage, edge contracts) and routes to per-**component** specialists, adds a neutral `component-engineer` template, and demonstrates it concretely in `examples/log-parser/`. Locked with the user: build BOTH the neutral core mechanism AND the concrete example; EVOLVE the existing primary `orchestrator` (no second primary/tier).
**Mode:** standard
**Depends on**: Phase 6 (merged). Independent of Phase 7 — the emitter is a pure function of the authored source and can compile this phase's new agents, but does not block it.
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06
**Success Criteria** (what must be TRUE):

  1. `harness/project.toml` declares a generic pipeline-topology slot (component id + stage + language ref + edge contracts consumes/produces); `tools/harness_config/loader.py` exposes it and a GEN-03-style consistency gate fails on divergence — with ZERO example dependency in core (GEN-04 guard green).
  2. The primary `orchestrator` is topology-aware: it reads the declared topology and routes by pipeline stage/component (not only language) with an updated routing table + dataflow-aware intake; a neutral `component-engineer` template exists under `harness/agents/templates/` and is persona-anti-sprawl-exempt.
  3. `examples/log-parser/` demonstrates the mechanism end-to-end — 4 component agents (parser / converter / scheduler / collector) + the log-parser pipeline topology declared in the instance's `project.toml` slot; the conductor can trace a request across the full parser→converter→scheduler→collector flow.
  4. New skill(s)/command(s) make the pipeline model executable (topology-trace / `/pipeline`); full non-example `uv run pytest` green; GEN-04/05 + persona guards clean; the Phase 7 emit surface is unaffected.

**Plans**: TBD

### Phase 9: Self-Maintaining Derived Artifacts + Curator *(v2.0 α)*

**Goal**: The derived plane stays fresh on its own — repo-map, contracts-index, docs `reference/`, and `.memory/` are regenerated by machines and verified by CI, with a single `curator` agent owning “derived freshness” and no human ever hand-editing a derived artifact. Reuses the existing `tools/memory_regen`, `/docs-sync`, and two-plane-memory machinery (no rebuild).
**Mode:** standard
**Depends on**: Phase 8 (last shipped v1.0 phase; first v2.0 phase)
**Requirements**: MAINT-01, MAINT-02, MAINT-03, MAINT-04
**Success Criteria** (what must be TRUE):

  1. A read-mostly `curator` agent exists (no constitution/golden write — machines gate, humans ratify) and is the single owner of derived freshness: it regenerates repo-map, contracts-index, docs `reference/`, and `.memory/` purely by invoking the existing `tools/memory_regen` + `/docs-sync`, and never hand-edits a derived file.
  2. A CI “stale-derived” gate regenerates the committed derived artifacts on a PR and FAILS on any diff — mirroring the Phase-7 re-emit-diff gate — so a stale derived plane cannot merge; machine-write + CI-verify satisfies the derived-never-hand-edited rule.
  3. Hook posture is split by cost: on-write hooks do only cheap refresh (format-on-write class), while heavy regeneration is deferred to PR/CI — there is no heavy per-commit local hook (slow/noisy is avoided).
  4. `/refresh-memory` (or an equivalent `curator` invocation) runs the full regen set locally before handoff, and `/verify-work` incorporates that freshness check so drift is caught pre-handoff, not in CI.
  5. The new `curator` agent (and any new command/hook) round-trips the Phase-7 emitter to BOTH runtimes (opencode primary, Claude secondary) with no model identifier, and the core stays example-independent (GEN-04 guard green).

**Plans**: 4 plans (3 waves)

Plans:
**Wave 1** *(foundation — reconcile pre-existing drift + flip contracts-index; no emitter touch, parallel-safe)*

- [x] 09-01-PLAN.md — Reconcile docs/reference drift + docs_sync prune-then-write + prune/determinism tests (MAINT-02)
- [x] 09-02-PLAN.md — Flip contracts-index to committed-derived: .gitignore contents-form + negation + track the file (MAINT-02)

**Wave 2** *(blocked on 09-01, 09-02 — the sole emitter-round-trip owner)*

- [x] 09-03-PLAN.md — Curator persona + /refresh-memory + /verify-work freshness + two-plane doc + caps bump 4→5; re-emit both runtimes (MAINT-01, MAINT-03, MAINT-04)

**Wave 3** *(blocked on 09-01, 09-02, 09-03 — lands last so CI is green on arrival)*

- [x] 09-04-PLAN.md — stale-derived CI job (regen → git add -A → git diff --cached --exit-code) + gate.needs + structural/negative-control test (MAINT-02)

**KEY DECISION (RESOLVED at plan time, D-01/D-02):** committed-derived set = `docs/reference/**` + `contracts-index` (the gated scope); `repo-map` stays gitignored/session-ephemeral (PageRank churn = noise, not signal).


### Phase 10: Context-Economy Fan-out/Synthesize Orchestration *(v2.0 β)*

**Goal**: Long-lived, multi-session work stays context-cheap. A first-class fan-out → dispatch N analysis subagents → recover schema-bounded summaries → synthesize workflow lets a conductor (and a human) cover large surfaces without a single context ballooning — by returning compact citation-bearing claims instead of raw file dumps. This is the reusable substrate Phase 11 (γ) applies across repos.
**Mode:** standard
**Depends on**: Phase 9
**Requirements**: ECON-01, ECON-02, ECON-03
**Success Criteria** (what must be TRUE):

  1. A `fan-out-synthesize` skill/command decomposes a task, dispatches N analysis subagents, recovers schema-bounded summaries, and synthesizes a result — usable by BOTH a human and the primary orchestrator/conductor (one shared workflow, not two).
  2. A summary/return contract is enforced so subagents return compact, citation-bearing output (paths + claims, not file dumps), letting the conductor synthesize WITHOUT re-reading the raw files each subagent touched.
  3. A delegate-vs-inline context-budget guide/skill (a heuristic for when to fan out vs work inline) is wired into the `orchestrator` persona and `/orient`, so the routing decision is observable and repeatable.
  4. Every new agent/skill/command round-trips the Phase-7 emitter to both runtimes (opencode primary, Claude secondary, no model identifier), and the core stays example-independent (GEN-04 guard green).

**Plans**: 3 plans (3 waves)

Plans:
**Wave 1**

- [x] 10-01-PLAN.md — fan-out-synthesize skill + citation-bearing return-contract schema + /fan-out-synthesize command + return-contract test (ECON-01, ECON-02)

**Wave 2** *(blocked on 10-01 — shared caps.py enumeration)*

- [x] 10-02-PLAN.md — context-budget skill wired into orchestrator + /orient + wiring test (ECON-03)

**Wave 3** *(blocked on 10-01, 10-02 — emitter round-trip lands last)*

- [x] 10-03-PLAN.md — re-emit both runtimes + commit derived trees + full-suite/GEN-04/emit-drift/anti-sprawl gate (ECON-01, ECON-02, ECON-03 / D-12)

### Phase 11: Multi-Repo Workspace *(v2.0 γ)*

**Goal**: Several repos are declared and operated as ONE workspace. The `harness/project.toml` slot pattern is raised one level into a workspace manifest, repo-scoped subagents run the β fan-out per-repo with workspace-level synthesis (no single context holds all repos), contract-drift/golden gates extend across repo boundaries, and the Phase-8 pipeline topology generalizes so an edge can cross a repo boundary — all while the core depends on no workspace member (GEN-04 generalized to core→workspace-member).
**Mode:** standard
**Depends on**: Phase 10 (β fan-out/synthesize is the reusable substrate γ applies across repos)
**Requirements**: MREPO-01, MREPO-02, MREPO-03, MREPO-04
**Success Criteria** (what must be TRUE):

  1. A workspace model + manifest declares member repos and cross-repo edges (which repo produces/consumes which contract), raising the `harness/project.toml` slot pattern one level; the manifest is pure DATA (loader passthrough + consistency gate), consistent with the GEN-03/PIPE-01 slot pattern.
  2. Repo-scoped subagents apply the Phase-10 β fan-out/synthesize across the workspace (per-repo analysis → workspace-level synthesis) so no single context has to hold every repo at once.
  3. Cross-repo contract-drift/golden gates extend the Phase-6 CI + `contract_drift` machinery across the workspace, failing on a drift or golden break whose edge spans a repo boundary — machines gate, humans ratify (constitution plane stays human-owned).
  4. The Phase-8 pipeline topology generalizes so a declared edge can cross a repo boundary, and a guard proves core→workspace-member single-direction dependency (GEN-04 generalized — core never imports/path-references a workspace member); new agents/commands round-trip the Phase-7 emitter to both runtimes.

**Plans**: 4 plans (3 waves)
**KEY DECISION (RESOLVED at plan time):** workspace model **b — workspace manifest as pure DATA** (top-level `workspace.toml`, raising the `harness/project.toml` GEN-03 slot pattern one level; declares `[[members]]` + `[pipeline].edges` with `repo:stage` endpoints so one table serves both cross-repo drift/golden member-resolution and repo-crossing topology). No enforcement in the manifest; a `tools/workspace_config` loader passthrough + a `test_workspace_config.py` consistency gate enforce well-formedness. Fan-out reuse is prose-wired (no new skill/command); the 2-member demo fixture lives INSIDE `REPO_ROOT` (`tests/fixtures/workspace/`) so `golden_runner._confine` passes unchanged.

Plans:
**Wave 1**

- [x] 11-01-PLAN.md — MREPO-01: `workspace.toml` DATA slot + `tools/workspace_config` loader/gate + minimal 2-member fixture (fully baselined, in-repo)

**Wave 2** *(blocked on 11-01; parallel — no file overlap)*

- [x] 11-02-PLAN.md — MREPO-04: `repo:stage` edge generalization + generalized core→workspace-member GEN-04 guard twin
- [x] 11-03-PLAN.md — MREPO-03: cross-repo contract-drift + workspace-aware golden (`_confine` widened) + separate `workspace` CI job in `gate.needs`

**Wave 3** *(blocked on 11-01/02/03 — closeout)*

- [x] 11-04-PLAN.md — MREPO-02: prose-wire member-repo fan-out reuse into orchestrator + fan-out-synthesize skill; emitter round-trip to both runtimes + full phase gate

### Phase 17: Constitution-Gate Dev/Enforce Decoupling *(infra — independent of v2.1 MEM2)*

**Goal:** The product's constitution gates (`contract_guard`, `commit_gate`) stop governing the Claude **dev** session while staying enforce-by-default everywhere else. Add a secure-default `HARNESS_DEV_BYPASS` env opt-out (default = enforce; blank/whitespace = no bypass; distinct from `GOLDEN_APPROVE_HUMAN` so a dev-bypassed write is never mislabeled "human ratified"), honored by both gates via a shared `dev_bypassed()` helper in `tools/hooks/_stdin.py`. Byte-hygiene (§4.3-4.6 BOM/CRLF) is **never** waived. Flag lives only in gitignored `.claude/settings.local.json`. ADR-0007 records the posture change; CODEOWNERS at PR merge remains the real, non-bypassable gate. Design source: `docs/superpowers/specs/2026-07-14-contract-guard-dev-bypass-design.md`.

**Requirements**: none new (references the approved brainstorm spec)
**Depends on:** None (harness-core; independent of the Phase 12–16 memory chain)
**Plans:** 2/2 plans complete

Plans:
- [x] 17-01-PLAN.md — HARNESS_DEV_BYPASS: shared dev_bypassed() + thread into contract_guard/commit_gate + tests (SC1–SC6)
- [x] 17-02-PLAN.md — ADR-0007 recording the posture (draft-to-scratch + human-gated landing)

### Phase 18: Task Packet Contract Ratification *(v2.2 A)*

**Goal:** 작업 상태·증거·인계의 shape와 소유권을 코드보다 먼저 사람 승인 계약으로 고정한다 — 이후 모든 phase가 prose 해석이 아니라 ratified schema를 소비한다.
**Mode:** standard
**Depends on:** Nothing new (reuses `contracts/`, contract-drift, golden machinery)
**Requirements:** TCP-01, TCP-02
**Success criteria** (observable):
1. `task`/`state`/`evidence`/`handoff` JSON Schema(Draft 2020-12) 4종이 `contracts/harness/task-control/`에 존재하고 contract-drift 베이스라인에 등록된다 — schema hash 이동은 paired golden + 사람 승인을 요구한다.
2. positive fixture ≥5개가 4 schema를 통과하고, 필수 필드별 negative fixture와 미정의 phase/lane/transition이 각각 거부된다.
3. `.workflow/tasks/<id>/` 인스턴스가 `.memory/state/`와 상호 독립이다 — 한쪽 삭제가 다른 쪽 검증/재생성을 바꾸지 않는다(deletion-independence 테스트).
4. dangling criterion/constraint/evidence ID와 baseline-commit 부재가 결정론적으로 거부된다.

### Phase 19: Deterministic Risk Router *(v2.2 B)*

**Goal:** 작업 규모가 아니라 위험·맥락 압력에 비례해 절차를 강화하되, 레인 판정과 필수 산출물은 전부 재현 가능한 순수 함수로 계산한다.
**Mode:** standard
**Depends on:** Phase 18 (task packet에 lane·risk input 필드)
**Requirements:** TCP-03, TCP-04, TCP-05, TCP-06
**Success criteria** (observable):
1. 동일 intake 입력 + policy hash가 실행 순서·호스트와 무관하게 byte-identical decision JSON을 낸다.
2. `0..4/5..9/10..14/15..21` 경계 fixture가 각각 FAST/STANDARD/STRICT/CONTROLLED를 낸다.
3. 자동 승격 fixture(auth·payment·secret·destructive·헌법 접촉…)가 점수 레인보다 낮지 않은 결과를 내고, overlay가 레인/게이트를 낮추려 하면 validation이 실패한다.
4. `/intake`가 packet을 생성하고 FAST fixture가 상세 SPEC/PLAN/worktree/이중 review를 자동 요구하지 않는다.
5. policy·output·fixture에 실제 모델 ID/provider 문자열이 없다.

### Phase 20: Atomic State Manager + Context/Transition Gate *(v2.2 C)*

**Goal:** 오케스트레이터의 prose 진행을 원자적·동시성 안전한 상태 전이로 바꾸고, phase 시작 전 ref·제약을 fail-closed 검증한다.
**Mode:** standard
**Depends on:** Phase 18 (state schema), Phase 19 (lane별 필수 산출물)
**Requirements:** TCP-07, TCP-08, TCP-09, TCP-10
**Success criteria** (observable):
1. transition matrix의 모든 허용 edge는 성공하고 모든 non-edge/필수-산출물-부재 advance는 canonical 파일을 바꾸지 않고 실패한다.
2. 강제 종료 후 정확히 하나의 valid state가 canonical하고, 같은 revision을 경쟁하는 두 writer 중 정확히 하나만 성공한다.
3. stale ref·wrong worktree·baseline mismatch·constraint attestation 누락이 EXECUTE 진입 전 차단된다.
4. `/phase-gate`가 두 런타임에 emit되고 generated-tree drift가 0이다.

### Phase 21: Evidence Bundle Adapters *(v2.2 D)*

**Goal:** "실행했다"는 서술 대신 기존 게이트의 실제 결과를 위조 탐지 가능하게 작업 계약에 연결한다 — 검증 로직은 재구현하지 않는다.
**Mode:** standard
**Depends on:** Phase 20 (transition/gate), Phase 18 (evidence schema)
**Requirements:** TCP-11, TCP-12, TCP-13
**Success criteria** (observable):
1. pass/fail/skip/blocked fixture가 서로 다른 status로 round-trip하고 skip이 pass로 승격되지 않는다.
2. artifact 1 byte 변조 시 hash 검증이 실패하고, 실행 안 한 게이트를 PASSED로 등록할 수 없다.
3. 필수 criterion에 passing evidence가 없으면 VERIFY 완료가, unresolved blocker/major finding이 있으면 COMPLETE가 거부된다.
4. secret/PII fixture가 evidence·HANDOFF에 평문 기록되지 않고 명시적으로 거부되며, 기존 `/verify-work` 5-gate regression이 그대로 통과한다.

### Phase 22: Handoff + Fresh-Session Resume *(v2.2 E)*

**Goal:** 대화 transcript 없이 정확한 task snapshot을 새 세션에 전달하고 안전한 재개를 강제한다.
**Mode:** standard
**Depends on:** Phase 20 (state/revision), Phase 21 (evidence refs)
**Requirements:** TCP-14, TCP-15
**Success criteria** (observable):
1. HANDOFF schema + 참조 hash가 검증되고, stale revision/ref/artifact를 가리키는 HANDOFF는 실패한다.
2. HANDOFF만 읽은 fresh-session checker가 task-id·goal·non-goals·critical constraints·현재 phase·ref·next-action을 100% 복원한다.
3. create→transition→evidence→handoff→(새 프로세스) orient→phase-gate end-to-end가 green이다.
4. SessionStart injector가 active task를 pointer-only로 주입하며 기존 ~1k token cap과 lazy-load를 지킨다(task 유무 양쪽 snapshot).

### Phase 23: Lifecycle Evaluation + Docs + CI *(v2.2 F)*

**Goal:** 소작업 ceremony 억제·고위험 fail-closed·fresh-session 재개를 출하 전에 재현 가능하게 증명하고, 구조 결정을 사람이 ratify한다.
**Mode:** standard
**Depends on:** Phases 18–22 (전 계층)
**Requirements:** TCP-16, TCP-17, TCP-18
**Success criteria** (observable):
1. 레인별 5개 = 20 ratified lifecycle fixture가 expected lane·결과와 일치하고 false downgrade가 0건이다.
2. stress/negative 사례(buried constraint·stale handoff·wrong worktree·tampered/missing evidence·concurrent writers·constitution change·illegal downgrade)가 모두 실행/COMPLETE 전에 차단된다.
3. FAST fixture가 상세 SPEC/PLAN/worktree/이중 review 없이 통과하고 FAST 사용자 의식 단계 상한(intake+verify)이 고정된다.
4. 구조 결정 ADR이 사람 승인 append-only로 랜딩되고 `docs/how-to/task-lifecycle.md`가 추가된다.
5. 전체 `uv run pytest` + contract-drift + golden + stale-derived + GEN-04 + harness emit-drift + 모델 식별자 lint가 green이다.

### Phase 24: Contract-Relationship Vocabulary + Compatibility *(v2.3 A)*

**Goal:** 마이그레이션을 강제하지 않고 ratified 그래프 record와 추가형 설정 seam을 출하한다 — 다운스트림이 무엇이든 이 어휘를 소비한다.
**Mode:** standard
**Depends on:** none (v2.2 완료 위에 시작)
**Requirements:** TOPO-01, TOPO-02, TOPO-03
**Success criteria** (observable):
1. `contracts/harness/topology/` 관계 record 스키마가 사람 승인되고 positive/negative fixture가 contract-hash/drift 경로를 통과한다.
2. 레거시 `[pipeline]` lowering이 byte-deterministic하고 explicit record와 추가형 union하며, 중복 id·중복 semantic edge·모순 시 fail한다.
3. 현재 `harness/project.toml`·`workspace.toml`·log-parser instance가 편집 없이 유효하게 유지된다(선형 fixture byte-unchanged).
4. 전체 contract-drift·GEN-04·기존 topology 테스트가 green이다.

**Plans**: 2 plans (1 wave)

Plans:
**Wave 1** *(parallel — no file overlap)*

- [x] 24-01-PLAN.md — TOPO-01: ratified relationship record schema + positive/negative fixtures + contract-hash rebaseline
- [x] 24-02-PLAN.md — TOPO-02/TOPO-03: additive `[contract_graph]` TOML slot + raw-passthrough accessors + deterministic `effective_relationships()` lowering/union

### Phase 25: Graph Compiler, Queries, Conductor, Proof *(v2.3 A)*

**Goal:** 일반 관계 그래프를 하나의 결정론적 구현과 기존 사용자 표면으로 사용 가능하게 만든다.
**Mode:** standard
**Depends on:** Phase 24 (ratified record + 슬롯 + lowering)
**Requirements:** TOPO-04, TOPO-05, TOPO-06, TOPO-07
**Success criteria** (observable):
1. 도메인 중립 컴파일러가 안정 정렬·repo-confined 출력·안정 진단 코드를 내고 fan-in/fan-out/disconnected/cycle을 허용한다.
2. direct/reverse/transitive affected-set 질의가 cycle에서 종료하고 id·path만 결정론적으로 반환하며, 새 task-evidence 요구를 만들지 않는다.
3. cross-repo authority-member contract 해소가 기존 drift 검사를 재사용하고, generic 비선형 + 불변 선형 regression fixture가 통과한다.
4. `/pipeline`·`pipeline-map`·orchestrator가 두 런타임에 byte-identical 왕복(모델 id 없음)하고 사람 승인 topology ADR이 랜딩된다.

**Plans**: 5 plans (4 waves)

Plans:
**Wave 1**

- [ ] 25-01-PLAN.md — TOPO-04: `tools/contract_graph` compiler + `harness_lint` consistency gate (unresolved-authority/dangling-endpoint/unknown-contract slugs) + WR-02 closure

**Wave 2** *(blocked on 25-01)*

- [ ] 25-02-PLAN.md — TOPO-05: cycle-safe direct/reverse/transitive affected-set queries ({ids, paths}, no task-evidence/no contract-preload)

**Wave 3** *(blocked on 25-01, 25-02 — parallel, no file overlap)*

- [ ] 25-03-PLAN.md — TOPO-06: `/pipeline`·`pipeline-map`·`orchestrator.md` indented-tree render (D-01) + linear byte-identity regression + emit round-trip
- [ ] 25-04-PLAN.md — TOPO-07: generic non-linear proof fixtures (fan-out, request/response split, event fan-out, legal cycle, cross-repo authority) + WR-01 disposition + GEN-04 regression

**Wave 4** *(blocked on 25-03, 25-04)*

- [ ] 25-05-PLAN.md — D-04: ADR-0009 (full model — compiler + queries + conductor contract) authored + human-ratified

### Phase 26: Deterministic Brownfield Inventory + Mapping *(v2.3 B)*

**Goal:** target을 변경하거나 에이전트 워크플로를 호출하지 않고 evidence-근거 adoption plan을 만든다.
**Mode:** standard
**Depends on:** Phase 24 (record 어휘만 — 컴파일러/질의 불필요; Phase 25와 병렬)
**Requirements:** ADOPT-01, ADOPT-02, ADOPT-03
**Success criteria** (observable):
1. 반복 inventory/plan 출력이 byte-identical하다(파일 열거 순서 무관).
2. 제안된 모든 항목이 observed/inferred/unknown으로 분류되고 미해결 ownership은 question으로 남는다.
3. 모든 하네스 destination이 정확히 하나의 disposition을 가진다.
4. confinement·secret 제외·size cap·ambiguity·collision 탐지가 통과하고 target tree는 불변이다.

### Phase 27: Task-Local Adoption Workflow + Safe Application *(v2.3 B)*

**Goal:** 결정론적 plan을 출하된 task control plane 위에서 재개 가능·사람 ratified·비파괴 adoption 워크플로로 전환한다.
**Mode:** standard
**Depends on:** Phase 26 (inventory/manifest spine)
**Requirements:** ADOPT-04, ADOPT-05, ADOPT-06, ADOPT-07
**Success criteria** (observable):
1. `.workflow/tasks/<id>/artifacts/adoption/<batch>/` batch가 안전하게 재개되고, 변경된 draft/ref/revision이 승인을 무효화한다.
2. `contracts/`·`docs/adr/`·`golden/` destination이 mutation 전에 거부되고, 비-헌법 apply가 atomic·collision-safe·idempotent하다.
3. 3개 fixture(polyglot 단일·2-레포 client/server·partial/collision, 최소 하나 CRLF/BOM)가 통과한다.
4. `/adopt` + `brownfield-adoption` skill이 두 런타임에 byte-identical 왕복(새 persona 없음, 모델 id 없음)한다.

### Phase 28: Human-Docs Registry, Guard, Derived Queue *(v2.3 C)*

**Goal:** semantic 정확성을 주장하거나 derived 생성기와 경쟁하지 않고 사람-문서 review 의무를 정확히 탐지·surface한다.
**Mode:** standard
**Depends on:** Phase 25 (그래프 impact 질의·최종 표면); Phase 27은 seed 데이터만 공급(슬립해도 machinery 비차단)
**Requirements:** DOCSUP-01, DOCSUP-02, DOCSUP-03, DOCSUP-04, DOCSUP-05
**Success criteria** (observable):
1. registry validation(path escape·중복 id·빈 required·derived/reference target·accepted-ADR 편집 거부)이 통과한다.
2. source-only 변경이 fail·doc+ledger 변경이 pass·설명 없는 ledger-only bump이 fail·`reviewed-no-change`가 정확한 현재 digest에만 pass한다.
3. `BROKEN`·`STALE_REQUIRED` fail·`STALE_ADVISORY` warn·uncovered 비-회귀가 강제된다.
4. 파생 큐가 결정론적으로 재생성되고 injector byte-identity + ~4,000자 예산 테스트가 green이며 `/docs-sync`·`/refresh-memory`·stale-derived 의미가 불변이다.

### Phase 29: Docs Drive Loop + Adoption Integration + Closeout *(v2.3 C)*

**Goal:** bounded 사람 대면 docs 워크플로를 추가하고 adoption seeding을 연결하며 세 테마를 전체 게이트 fan-in으로 닫는다.
**Mode:** standard
**Depends on:** Phase 28 (결정론적 guard); Phase 27 (destination manifest·command)
**Requirements:** DOCSUP-06, DOCSUP-07
**Success criteria** (observable):
1. `/docs-update` + `docs-upkeep`가 두 런타임에 byte-identical emit하고 accepted ADR·`docs/reference/**`·`.memory/derived/**`·contracts·golden 제외가 게이트로 테스트된다.
2. `/adopt`이 binding을 제안하되 스스로 review(green)할 수 없다.
3. required seed 문서가 fresh이거나 정확히 dispositioned된다.
4. 전체 `uv run pytest` + contract-drift + golden + workspace drift + stale-derived + lifecycle + GEN-04 twin + docs guard + emit-drift + 모델 식별자 lint + injector budget + `git diff --check`가 green이다.
