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
- [ ] **Phase 7: Single-Source Dual-Runtime Emitter** - One authored source compiles into both opencode (primary) + Claude Code (secondary) artifacts, with per-runtime limit validators that fail loud.

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

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Constitution + Golden Core | 6/6 | Complete   | 2026-07-08 |
| 2. Two-Plane Memory + Rules | 5/5 | Complete   | 2026-07-08 |
| 3. Agents + Commands + Skills | 7/7 | Complete   | 2026-07-08 |
| 4. Plugins + Hooks | 6/6 | Complete   | 2026-07-08 |
| 5. De-specialization & Template Extraction | 5/5 | Complete   | 2026-07-09 |
| 5.5. Authored-Surface Genericization (INSERTED) | 3/3 | Complete|  |
| 6. CI + Gates (generic) | 3/3 | Complete   | 2026-07-09 |
| 7. Single-Source Dual-Runtime Emitter | 0/TBD | Not started | - |
