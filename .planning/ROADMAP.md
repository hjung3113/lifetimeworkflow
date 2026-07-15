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
- [ ] **Phase 13: Injector Reframe + Channel Wiring** *(v2.1 B)* - Split the SessionStart banner into a full-body priority-0 working-agreements directive + a data-scoped provenance banner, and surface a verbatim progress `updated:` stamp — preserving `inject.py` determinism and the ~4000-char budget.
- [ ] **Phase 14: Write Path + Anti-Churn Guard** *(v2.1 C)* - A dedicated `/agree` command adds/retires a working-agreement only on explicit user feedback, backed by a `tools/harness_lint` provenance/anti-invent guard.
- [x] **Phase 15: Emit Round-Trip + Gates** *(v2.1 D)* - Round-trip every new/changed surface (`/agree`, updated skills, AGENTS.md managed block) through the Phase-7 emitter to both runtimes with no model id; emit-drift clean, GEN-04 green. (completed 2026-07-15)
- [ ] **Phase 16: Local Memory Web UI** *(v2.1 E)* - A local, no-network, no-auth tool to view/edit/retire memory items with pointer-aware referential integrity over a machine-built derived pointer-index.
- [x] **Phase 17: Constitution-Gate Dev/Enforce Decoupling** *(infra — independent of v2.1 MEM2)* - A secure-default `HARNESS_DEV_BYPASS` env opt-out so the product's constitution gates stop governing the Claude dev session (default enforce; blank = no bypass; distinct from `GOLDEN_APPROVE_HUMAN`; byte-hygiene never waived), honored by `contract_guard`/`commit_gate`; ADR-0007 records it; CODEOWNERS stays the real gate. (completed 2026-07-15)

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
| 15. Emit Round-Trip + Gates (v2.1 D) | 2/2 | Complete   | 2026-07-15 |
| 16. Local Memory Web UI (v2.1 E) | 0/TBD | Not started | - |

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
**Plans:** 2 plans (2 waves)

Plans:
- [ ] 17-01-PLAN.md — HARNESS_DEV_BYPASS: shared dev_bypassed() + thread into contract_guard/commit_gate + tests (SC1–SC6)
- [ ] 17-02-PLAN.md — ADR-0007 recording the posture (draft-to-scratch + human-gated landing)

---

## Milestone v2.1 — MEM2 — Process Memory & Provenance Reframe

> **Numbering continues (do NOT reset).** v2.0 ended at Phase 11; this milestone runs **Phases 12–16**. Design source: `.planning/MEMORY-UPGRADE-PROPOSAL.md` (§7 operator refinements are AUTHORITATIVE, supersede §2/§5 on conflict). Every phase **reuses existing machinery** (`tools/memory_regen`/`inject.py`, `/checkpoint`, `tools/harness_lint`, the Phase-7 emitter `tools/harness_emit`, the `adr` skill + CODEOWNERS path) — no new machinery is invented. Sequencing is dependency-locked 12 → 13 → 14 → 15 → 16: the model+ADR ground the injector; the injector consumes the channel the write-path fills; emit round-trips the surface changes; the UI operates on the finished, committed channel.
>
> **Cross-cutting non-negotiables (all phases):** contract-first / constitution gated (ADR-0006 lands via the human-ratified path — an agent Write to `docs/adr/` is correctly denied by contract-guard); machines gate / humans ratify (agreements are written **only** on explicit user feedback — the user is the ratifier); the new agreements channel is a **committed human-authored tier** (like `state/`), NOT a derived artifact — never regenerated, never colliding with `.memory/derived/`; every surface change round-trips the emitter to both runtimes with **no model id**; GEN-04 core→example independence stays green; project decisions are **linked** (ADR / PROJECT.md Key Decisions), never restated in the PROCESS channel (§7c).

### Phase 12: Model + ADR + Doc Reframe *(v2.1 A)*

**Goal**: The PROCESS memory channel exists as a scaffolded per-guideline tier and the distrust framing reads as *data authority* everywhere it echoes — and the memory-model change is ratified as ADR-0006 through the human-gated constitution path. This is the model + documentation foundation the injector (Phase 13) and write-path (Phase 14) build on.
**Mode:** standard
**Depends on**: Phase 11 (last shipped)
**Requirements**: MEM2-01, MEM2-03 *(also authors the ADR-0006 portion of MEM2-06 — the emit portion of MEM2-06 is owned by Phase 15)*
**Success Criteria** (what must be TRUE):

  1. `.memory/agreements/` exists as a committed, human-authored tier with a defined per-guideline entry shape — one file per guideline (`<slug>.md`: title + one-line rule + `status` active/retired + a provenance stamp "added because &lt;user feedback&gt;" + added-date) — documented (schema/fixture) and scaffolded (empty or seed), and it is explicitly a committed tier like `state/`, NOT a derived artifact (it never regenerates, never collides with `.memory/derived/`).
  2. No session-start surface tells an agent to "confirm before trusting" its own grounded work: the distrust prose is reworded to data-authority ("which artifact wins a DATA conflict") in `.memory/README.md`, `.memory/state/activeContext.md`, `.memory/state/progress.md`, `harness/skills/two-plane-memory/SKILL.md`, and `AGENTS.md`.
  3. The agreements-entry shape links to ADRs / PROJECT.md Key-Decisions and never restates a project decision (§7c) — the PROCESS channel is working-style/methodology only.
  4. ADR-0006 records the memory-model change (append-only, next number after 0005) and lands via the human-ratified path — an agent Write to `docs/adr/` is correctly denied by contract-guard, and CODEOWNERS ratifies at merge (mirrors the ADR-0004/0005 posture).

**Plans**: 3 plans (2 waves)

Plans:
**Wave 1** *(parallel — zero file overlap)*

- [ ] 12-01-PLAN.md — Scaffold `.memory/agreements/` committed tier (`_TEMPLATE.md` + tier README) + four-plane `.memory/README.md` + data-authority reword of the two shared docs (README STATE section + two-plane-memory SKILL source) (MEM2-01, MEM2-03)
- [ ] 12-02-PLAN.md — Data-authority reword of the three non-shared surfaces: `.memory/state/activeContext.md`, `.memory/state/progress.md`, `AGENTS.md` (edit outside the HARNESS-MANAGED block) (MEM2-03)

**Wave 2** *(blocked on 12-01, 12-02)*

- [ ] 12-03-PLAN.md — Author ADR-0006 (memory-model change) via the human-ratified constitution path; agent Write correctly denied, human token/CODEOWNERS ratifies (MEM2-06 ADR portion) [autonomous: false]

### Phase 13: Injector Reframe + Channel Wiring *(v2.1 B)*

**Goal**: SessionStart injects the working-agreements as a full-body priority-0 directive plus a separate data-scoped provenance banner, and surfaces a verbatim progress freshness stamp — all while preserving `inject.py` determinism and the ~4000-char budget. This consumes the channel scaffolded in Phase 12.
**Mode:** standard
**Depends on**: Phase 12 (the `.memory/agreements/` shape + reworded prose it composes/surfaces)
**Requirements**: MEM2-02, MEM2-05
**Success Criteria** (what must be TRUE):

  1. `inject.py` emits two distinct blocks: (a) a full-body **working-agreements directive** composed from the active `.memory/agreements/*` files at a new priority-0 (never-dropped, honored as a directive), **capped** (N entries / M chars; overflow degrades to a pointer per Q4) so it cannot crowd out drift + index; and (b) a **data-scoped** provenance banner that reads as "which artifact wins a data conflict" — NOT "distrust/retract your own grounded work". The activeContext pointer is reworded to a progress-log pointer.
  2. delete+regen of the injector payload is **byte-identical** (determinism at `inject.py:20-22` preserved) and the assembled payload stays within the ~4000-char budget (`inject.py:105`) even with the capped agreements block present.
  3. `/checkpoint` writes an `updated: <ISO-date>` stamp into `.memory/state/activeContext.md` / `progress.md`; `assemble()` surfaces that stamp **verbatim** — NO wall-clock inside `assemble()` (determinism intact) and NO hook-wrapper wall-clock code — freshness is judged **agent-side** against the session date (no fixed threshold, per Q6).
  4. Progress state stays tight by design (in-flight + remaining + a short last-N-done summary); no ever-growing done-log is introduced (full history lives in git, §7a).

**Plans**: 4 plans in 3 waves

Plans:
**Wave 1**
- [ ] 13-01-PLAN.md — Wave 1 · State stamp + /checkpoint mandate + agreements no-secrets line (MEM2-05 write half, SC3/SC4)
- [ ] 13-02-PLAN.md — Wave 1 · Determinism safety net backfill: byte-identity + snapshot + no-wall-clock statics (MEM2-02 SC2 prerequisite)

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 13-03-PLAN.md — Wave 2 · Injector reframe: agreements directive at priority-0, data-scoped banner, verbatim stamp (sole owner of inject.py)

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 13-04-PLAN.md — Wave 3 · Re-enable injection + retire the superseded provisional/banner-first prose (D-20/D-06)

### Phase 14: Write Path + Anti-Churn Guard *(v2.1 C)*

**Goal**: A dedicated `/agree` command is the sanctioned — and only — way a working-agreement is added or retired, and it fires only on explicit user feedback; a `tools/harness_lint` provenance/anti-invent guard enforces that every entry is origin-stamped and that agents cannot self-invent unsolicited entries.
**Mode:** standard
**Depends on**: Phase 13 (the injector consumes the files this command writes)
**Requirements**: MEM2-04
**Success Criteria** (what must be TRUE):

  1. A dedicated **`/agree`** command appends a new per-guideline agreement **only in response to explicit user feedback**, and retires one by flipping that file's `status` to `retired` (per Q5/§7b) — never auto-churned, never silently rotated like the progress log.
  2. A `tools/harness_lint` check **fails when an agreement file lacks a well-formed provenance/origin stamp** ("added because &lt;user feedback&gt;" + added-date), so agents cannot auto-invent entries; the guard follows the existing `stale-derived` gate pattern (regenerate → verify).
  3. `/agree` is added to `EXPECTED_COMMANDS` (source side; its emit round-trip to both runtimes is owned by Phase 15).

**Plans**: 4 plans in 3 waves

Plans:
**Wave 1**
- [ ] 14-01-PLAN.md — Wave 1 · Extract the shared L1-L4 agreements predicate into tools/harness_lint/agreements.py + widen the no-wall-clock gate with a negative control (D-05/D-14/D-17/D-18; sole owner of inject.py)
- [ ] 14-04-PLAN.md — Wave 1 · ADR-0006 `## Errata`: correct the phantom "committed seed" claim, declare the empty active set CORRECT (D-12/D-13; constitution write, human-gated)

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 14-02-PLAN.md — Wave 2 · The provenance lint: tools/harness_lint/provenance.py + tests + `added:` template quoting + presence-safe /lint step (D-01/D-02/D-03/D-04/D-16)

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 14-03-PLAN.md — Wave 3 · The /agree write path: new zero-dep tools/agree/ member, refusal-first writer, YAML-serialized provenance, source-only command (D-07/D-08/D-09/D-10/D-11/D-15/D-19/D-20)

### Phase 15: Emit Round-Trip + Gates *(v2.1 D)*

**Goal**: Every new/changed surface from this milestone (`/agree`, updated skills, the updated `AGENTS.md` managed block) round-trips the Phase-7 emitter to both runtimes with no model id — proving emit-drift clean, GEN-04 green, and counts/fixtures updated. This is the emit portion of MEM2-06 (its ADR portion landed in Phase 12).
**Mode:** standard
**Depends on**: Phase 14 (the full set of surface changes must exist before the round-trip)
**Requirements**: MEM2-06
**Success Criteria** (what must be TRUE):

  1. Re-running `tools/harness_emit` (glob discovery, mirroring the Phase-10/11 emitter round-trip — no emitter code change expected) projects `/agree` + the updated skills + the updated `AGENTS.md` managed block to BOTH runtimes (`.opencode/` + `.claude/`); emit fixtures/counts + `EXPECTED_COMMANDS` are updated to match.
  2. The **emit-drift gate is clean** (re-emit + diff over the full documented path set) and **no model id** appears anywhere in the emitted trees (placeholder tiers only).
  3. **GEN-04 core→example independence stays green** and the full non-example test suite passes.

> **SC1 note (planning, 2026-07-16):** `EXPECTED_COMMANDS` **does not exist** in any source file
> (verified: 0 hits across `tools/`, `harness/`, `libs/`). `test_commands.py` is glob-driven by
> design, which is why `agree.md` was auto-covered in Phase 14 with zero test edits; Phase 14 already
> ruled against inventing the constant (D-11). SC1 is **mis-worded** — the third such instance in this
> milestone's own source. Its substance is satisfied by the re-emit plus the `.ambr` regen. Likewise
> "counts updated" is **already done**: `test_all_20_commands_emit_to_both_trees` was bumped 19→20 by
> Phase 14 (`fa1aea8`) and passes, because `_emit(tmp_path)` counts the runtime-neutral SOURCE, not the
> committed trees.

**Plans**: 2 plans

Plans:
**Wave 1**
- [x] 15-01-PLAN.md — Wave 1 · Run the Phase-7 emitter, commit the measured delta (2 new + 8 changed + AGENTS.md splice + manifest), then regenerate the projected-tree `.ambr` — emit strictly BEFORE snapshot-regen (gate-theft guard)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 15-02-PLAN.md — Wave 2 · Prove the gates (model-id incl. the body coverage gap, GEN-04 post-regen, full suite, emit-drift replica), fix the stale `test_coexist` module docstring 19→20, record the SC1 mis-wording

### Phase 16: Local Memory Web UI *(v2.1 E)*

**Goal**: A lightweight, local, no-network, no-auth tool lets a user view / edit / retire memory items (progress state + per-guideline agreements) with pointer-aware referential integrity — surfacing "what points to this item" over a machine-built derived pointer-index and keeping references consistent on edit/retire, so memory hygiene is systematized rather than manual.
**Mode:** standard
**Depends on**: Phase 15 (operates on the finished, committed memory channel + emitted surface)
**Requirements**: MEM2-07
**Success Criteria** (what must be TRUE):

  1. A **local** web tool (no external network, no auth surface) lists the committed memory items — progress state + per-guideline agreements — and lets a user view, edit, and retire them.
  2. A machine-built **derived pointer-index** surfaces "what points to this item" (docs / skills / `inject.py` pointers that reference memory files); the index is treated like other derived artifacts (generated, not hand-maintained).
  3. Editing or retiring an item keeps references consistent — an edit/retire that would orphan a pointer is surfaced and reconciled — so a hand-edit can no longer silently break references.

**Plans**: TBD
**UI hint**: yes
