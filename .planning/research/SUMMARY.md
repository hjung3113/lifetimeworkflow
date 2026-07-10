# Project Research Summary

**Project:** LogParser Pipeline Harness (설비 로그파서 파이프라인 opencode 하네스)
**Domain:** opencode agent harness (agents/commands/skills/plugins + Diátaxis/ADR/contracts docs + two-plane context memory) for a polyglot .NET 10 + Python, contract-first, legacy-migration monorepo (semiconductor equipment log-parser pipeline)
**Researched:** 2026-07-07
**Confidence:** MEDIUM-HIGH (domain contracts and toolchain versions HIGH; opencode runtime internals MEDIUM — opencode.ai is proxy-403'd, verified via search/mirrors/community references, not live docs)

## Executive Summary

The deliverable is not the log-parser pipeline — it is the **harness that lets agents build, maintain, and refactor it**: opencode agents/commands/skills/plugins, Diátaxis+ADR+contracts documentation, and a two-plane context-memory layer, single-sourced to also emit Claude Code artifacts. All four research dimensions (stack, features, architecture, pitfalls) converge independently on the same structural insight: **this harness is a config compiler plus a runtime overlay, not an application**, and it must be built bottom-up in the order the domain's own risk profile dictates — constitution (contracts/docs/golden) first, memory and rules second, agent/command/skill surface third, plugins/hooks fourth, CI gates fifth, and the single-source dual-runtime emitter **last**, because the emitter has nothing to compile until the source layers exist.

The single most load-bearing technical decision is the **normalized golden-equivalence comparator + shared canonicalization core** (UTF-8 no-BOM, LF-only, InvariantCulture decimals, UTC/ISO-8601 timestamps, defined null-vs-empty, deterministic ordering). This one piece of tooling is reused by both the golden-runner (legacy↔new parity) and the polyglot-boundary linter (on-write conformance), and it must be built before any migration command (`/strangler-step`, `/golden-approve`) depends on it — a naive byte-diff comparator is the single most-cited failure mode across the domain's own design docs and the pitfalls research (false reds on BOM/CRLF/locale/TZ differences erode trust in the only language-agnostic safety net the project has). Equally load-bearing on the governance side: **machines gate, humans ratify**. Contract-drift (schema-hash, must cover §4 cross-cutting conventions not just column lists) and golden-run checks fire automatically in a plugin (fast, in-session) and in CI (hard, non-bypassable); only a human via CODEOWNERS + `/golden-approve` can bless a baseline change. Agents must never self-approve goldens or auto-mutate the constitution plane (contracts/adr/golden) — this is the highest-consequence anti-pattern in the whole harness, because it defeats the one safety net the legacy migration depends on.

The chief risk to manage during planning is **scope, not technology**: PROJECT.md enumerates a full harness surface (7 agents, ~10 commands, 7 skills, 4 plugins, dual-runtime emit) that reads like a checklist but is explicitly "hypothesis until validated." The pitfalls research names this the meta-pitfall — building the entire enumerated surface before one real workflow (one contract → one golden run → one contract-drift failure → one human approval) has gone end-to-end on real seed data. The roadmap should therefore front-load a thin walking skeleton and treat breadth (more agents, more skills, `/strangler-step`, `/docs-sync`, and especially the dual-runtime emitter) as sequenced *after* the core loop is proven, not as parallel work. A second cross-cutting risk is **runtime asymmetry**: opencode has no literal `SessionStart` hook (it uses `session.created` + `experimental.chat.system.transform`) versus Claude Code's native `SessionStart`/`additionalContext`; permission globs are last-wins; skill size caps and nested-AGENTS.md merge semantics (concatenate vs. replace-at-cwd) differ per runtime. These must be encoded as non-negotiable invariants enforced by hooks/emitter validation — never left to inherited prose or "the model will remember."

## Key Findings

### Recommended Stack

The harness itself is authored in Node/TypeScript against the opencode plugin SDK (`@opencode-ai/plugin`, `@opencode-ai/sdk`, `zod` for tool-arg schemas), with Claude Code as a secondary emit target consumed during dev (GSD already drives development). The toolchains the harness *bootstraps and gates* — not implements — are .NET 10 SDK (10.0.100 LTS, installed via `dotnet-install.sh` from a SessionStart/setup hook since the env has none) and Python via `uv` workspaces (0.11.x, already present, replacing pip/poetry/pyenv). Golden/approval testing uses `Verify.XunitV3` (.NET) and `syrupy` (Python) as language-local snapshot tools, but the **cross-language comparator is bespoke** (built once, hosted in Python since collector/scheduler are Python and CI already runs it) — this is the linchpin piece, not a library pick. Contract validation is JSON Schema (Draft 2020-12) via `JsonSchema.Net` (.NET) and `jsonschema`/`check-jsonschema` (Python) as the neutral IR; explicitly **not** Pact/consumer-driven-contract tooling, because the domain's boundaries are file/DB/CLI-spawn, not HTTP/gRPC (Pact only becomes relevant if the deferred B-model/gRPC ever ships). Context-memory tooling (repo-map generation) borrows Aider's proven recipe: tree-sitter grammars + `networkx` PageRank, hand-rolled minimal rather than a 750-file generic port — consistent with the project's explicit "custom/minimal over generic" decision.

**Core technologies:**
- **opencode** (`sst/opencode`, rolling) + `@opencode-ai/plugin`/`sdk` + `zod` — primary runtime; hook surface (`tool.execute.before/after`, `permission.ask`, `event`, `command.execute.before`) is the exact guardrail seam the project needs.
- **.NET 10 SDK 10.0.100 (LTS)** + `uv 0.11.x` — the two toolchains the harness must self-bootstrap in an ephemeral, .NET-less container.
- **Verify.XunitV3 + syrupy** — language-local golden/approval snapshotting; their `.received/.verified` and `--snapshot-update` workflows map directly onto `/golden-approve`.
- **Custom normalization/canonicalization core** (bespoke, Python-hosted) — the cross-language golden comparator; not a library, the single most important piece of custom code in the harness.
- **JSON Schema (Draft 2020-12)** + `check-jsonschema` + JCS/RFC 8785 canonicalization → SHA-256 — the contract-drift schema-hash gate.
- **tree-sitter + networkx** — minimal repo-map generator for the derived memory plane.

### Expected Features

The feature landscape splits cleanly: table stakes are what any credible opencode/Claude Code harness provides (config, permission matrix, personas, commands, skills, hooks, memory files); differentiators are what make this harness worth building bespoke rather than porting generic (contract-drift gate, golden/approval equivalence commands, `/strangler-step`, two-plane memory, the polyglot-boundary linter); anti-features are things a naive harness would add that actively harm this project (big-bang rewrite commands, agents auto-blessing goldens, hand-maintained reference docs, component implementation logic, object-level cross-language interop, auto-mutating the constitution plane, full B-model implementation, porting a 750-file generic pack).

**Must have (table stakes):**
- `opencode.json` core config (model tiering, 15-key permission matrix with last-wins bash globs, instructions glob, MCP, formatter) — nothing else loads without it.
- Agent personas scoped by permission + language (orchestrator, dotnet, python, read-only reviewer, explorer).
- AGENTS.md rules (root + per-package, lazy/nearest-wins loaded).
- Hooks: format-on-write, secret protection, commit gate.

**Should have (differentiators — the actual value proposition):**
- Normalization comparator + `/golden` + `/golden-approve` (CODEOWNERS human sign-off) — the single most important control.
- Contract-drift CI gate (schema hash covering §4 cross-cutting conventions, not just columns).
- Polyglot-boundary linter (encoding/BOM/LF/TSV-escape/timezone/decimal/null enforcement) — shares the comparator's normalization core.
- Two-plane context memory + non-ignorable SessionStart injection + `/checkpoint`.
- Domain contract + docs seed from the parserimprove monorepo_skeleton (concrete, not generic placeholders).

**Defer (v1.x / v2+):**
- `/strangler-step`, `/new-normalization-rule`, `/docs-sync`, `/component` scaffold — real but sequenced after the safety net is proven (each has an explicit trigger condition, e.g. `/strangler-step` waits until golden equivalence is trusted enough to gate real extractions).
- Dedicated golden-runner / polyglot-auditor agent personas — add once those workflows are heavy enough to warrant a dedicated persona (P1 walking-skeleton discipline).
- **Single-source multi-runtime emit (opencode → Claude Code)** — HIGH complexity, explicitly deferred: emitting against a still-moving opencode surface before one workflow is validated is premature (interim: hand-maintain `.claude/` or develop opencode-only).
- B-model (gRPC/MQ) extension points, shadow-run tooling, configuration-parser harness surface.

### Architecture Approach

The harness is a **config compiler plus runtime overlay**: one authored surface (`harness/`) is compiled by an emitter into two runtime-native artifact sets (opencode primary, Claude Code secondary) that are never hand-edited. Memory is split by *authorship and lifecycle*, not topic — a human-owned, gated **constitution plane** (contracts/, docs/adr/, glossary, golden/) versus a machine-owned **derived/volatile plane** (`.memory/`: repo-map, contracts-index, activeContext, progress) that is regenerated every session and never hand-edited. Contract-first safety is a deterministic pipeline: schema-hash → drift check → golden run → human `/golden-approve`; the same underlying tooling (contract-hash/drift/golden-runner) is invoked from both an in-session plugin (fast warning) and CI (hard, non-bypassable gate) — "machines gate, humans ratify" is the operative principle, never "trust the agent to self-police."

**Major components:**
1. **`harness/`** (source of truth, runtime-neutral: agents/commands/skills/plugins/rules/partials/emitter) — the only place humans/agents author runtime config.
2. **`contracts/` + `docs/adr/` + `glossary`** (constitution plane, CODEOWNERS-gated) — every rule, agent, and gate points here; `docs/reference/` is the one place the two planes touch (generated from contracts, agent-maintained).
3. **`.memory/`** (derived/volatile plane) — repo-map, contracts-index, activeContext, progress; auto-regenerated, injected non-ignorably at session start, never hand-edited.
4. **`tools/`** (contract-hash, contract-drift, golden-runner, memory-regen, bootstrap, harness-emit) — the shared implementation invoked by both plugins and CI.
5. **`.opencode/` + `.claude/`** (generated runtime surfaces) — build artifacts only, produced by `tools/harness-emit`; the pre-existing `.claude/get-shit-done/` is quarantined and untouched by emit.

### Critical Pitfalls

1. **Over-engineering the harness before one workflow validates it (meta-pitfall, P1)** — build one thin vertical slice (seed one contract → one `/golden` run → one `/contract-check` failure → one human approval) before widening the surface. This is an ordering mandate for the roadmap, not a feature.
2. **Naive byte-diff golden comparator producing false reds (P4)** — representation differences (BOM, CRLF, decimal locale, TZ, null-vs-empty) are the domain's #1 bug class; a byte comparator can't distinguish them from real regressions, and the team learns to ignore red. Build the normalized canonical comparator first, before any migration command depends on it.
3. **Agents "fixing" golden files to make CI green (P9)** — the highest-consequence failure: it defeats the one language-agnostic safety net the project has. Golden edits must always require the human gate (CODEOWNERS + `/golden-approve`); agents may propose, never merge; every change must cite an ADR/rationale.
4. **Big-bang rewrite temptation without characterizing undocumented legacy behavior first (P10)** — the legacy parser has no tests/handover; "equivalence" has no reference until legacy behavior is captured as golden fixtures. Characterization must precede any `/strangler-step`.
5. **Contract/code divergence undetected because the hash covers the wrong surface (P14)** — hashing just the column list misses the §4-5 cross-cutting conventions (encoding, LF, decimal, null policy). Need hash gate + behavioral linter + golden equivalence together — hash alone is contract-in-name-only.
6. **Runtime asymmetry silently violated** — no literal opencode SessionStart hook (uses `session.created`/`chat.system.transform`), last-wins permission globs, differing skill size caps, and differing nested-AGENTS.md merge semantics (concatenate vs. replace-at-cwd) mean non-negotiable invariants must live in hooks/emitter validation, never in prose that a runtime might not merge the way you assumed.

## Implications for Roadmap

Based on research, suggested phase structure (6 phases, bottom-up dependency order all four research dimensions converged on independently):

### Phase 1: Constitution + Golden Core (the walking skeleton)
**Rationale:** Every rule, agent, gate, and skill downstream references contracts; nothing is meaningful without the source of truth. The normalization core is the single shared linchpin dependency of the golden-runner AND the polyglot-boundary linter — build it once, first, before anything depends on it (Pitfalls P4, P9, P14).
**Delivers:** `contracts/` seeded from the parserimprove monorepo_skeleton (TSV spec, normalization catalog, reference-data, state/carryover — as examples/placeholders); `docs/` Diátaxis skeleton + `adr/0001` + glossary; `contract-hash`/`contract-drift` tooling + `.hashes` baseline (hashing the full §4-5 cross-cutting surface, not just columns); the shared canonicalization/normalization library; `tools/golden-runner`; `/golden` and `/golden-approve` commands with a CODEOWNERS stub. Must close one real loop end-to-end: seed contract → golden run → normalized diff → simulated human approval.
**Addresses:** Contract + docs seed, normalization comparator, `/golden`/`/golden-approve`, contract-drift gate (all P1 must-haves from FEATURES.md).
**Avoids:** P1 (over-engineering before validation), P4 (byte-diff false reds), P9 (agents rubber-stamping goldens), P14 (hash covering the wrong surface).

### Phase 2: Two-Plane Memory + Rules
**Rationale:** Depends on Phase 1 (contracts-index is derived from contracts). Establishes the constitution-vs-derived split before any agent consumes context, and must be scoped correctly from the start — retrofitting lazy loading after context bloat has already shipped is expensive.
**Delivers:** `tools/memory-regen` (repo-map via tree-sitter+networkx, contracts-index); root `AGENTS.md` + per-package partials with nearest-wins layout; design (not yet wired to runtime) for non-ignorable SessionStart injection that injects pointers/indexes, not full contract payloads.
**Uses:** tree-sitter grammars, networkx PageRank, memory-bank file convention.
**Implements:** the derived/volatile plane architecture component.
**Avoids:** P2 (context bloat — cap injection size, inject pointers not payloads), P12 (derived-doc rot — generated, never hand-edited), P13 (volatile memory silently trusted as fact — mark provisional, ADR always overrides memory).

### Phase 3: Agents + Commands + Skills
**Rationale:** Depends on Phase 2 (agents inject rules/memory) and Phase 1 (skills read contracts). This is where the enumerated harness surface gets built — but sequence within the phase matters: `/contract-check`, `/adr`, `/checkpoint`, `/component` first; `/new-normalization-rule` next; `/strangler-step` and `/docs-sync` last within this phase (or pushed to a follow-on milestone) since they depend on the golden safety net being *trusted*, not merely present.
**Delivers:** orchestrator/dotnet/python/reviewer/explorer agent personas (permission- and model-tier-scoped); command set; skills (dotnet, python, pipeline-patterns, data-contracts, golden-testing, normalization-catalog, skill-creator) authored with progressive disclosure.
**Addresses:** Agent personas, slash commands, skills with progressive disclosure (FEATURES.md table stakes + differentiators).
**Avoids:** P7 (description-as-label — write descriptions as routing triggers, test with fixtures), P8 (skill sprawl and agents ignoring prose rules — curate skill count, push enforcement to hooks not prose), P10 (big-bang — `/strangler-step` must refuse to run without a captured legacy baseline).

### Phase 4: Plugins + Hooks
**Rationale:** Depends on memory-regen (session-start calls it), contracts (contract-guard watches them), and agents (guard warns them). This is the runtime *enforcement* of everything authored in Phases 1-3 — prose rules are advisory, hooks are not.
**Delivers:** contract-guard (blocks/asks on writes to contracts/adr/golden), session-start injector (wires Phase 2's memory-regen into both opencode `session.created`/`chat.system.transform` and Claude `SessionStart`/`additionalContext`), format-on-write (LF/no-BOM/InvariantCulture enforcement), polyglot-boundary linter (§4-5 checklist as executable enforcement, sharing Phase 1's normalization core), secret protection, commit gate, and a permission-matrix order-resolution test suite.
**Addresses:** Hooks table stakes; polyglot-boundary linter differentiator.
**Avoids:** P3 (over-broad permissions — default-deny, explicit-allow, order-test the resolver, constitution-plane edits are `ask`/`deny`), P11 (nested AGENTS.md silently dropping root invariants — enforce non-negotiables via hooks, which have no merge semantics, rather than relying on inheritance).

### Phase 5: CI + Gates
**Rationale:** Depends on the drift/golden tooling (Phase 1) and plugins (Phase 4); CI is the non-bypassable mirror of the in-session plugin gates plus the human ratification path. Builds trust in the safety net before it is relied upon for real migration work.
**Delivers:** `.github/workflows/ci.yml` polyglot matrix (.NET 10 + Python/uv jobs, contract-check job, golden job); CODEOWNERS covering `contracts/`, `adr/`, `golden/`; PR template with breaking-change/golden checklist; toolchain bootstrap (.NET 10 SDK install script + uv workspace setup) fully wired to SessionStart/setup (can be stubbed earlier, but must be real and idempotent by this phase since the container is ephemeral).
**Addresses:** Contract-drift CI gate, toolchain bootstrap (FEATURES.md P1 must-haves).
**Avoids:** P9/P10 enforcement gap (CI is the hard gate agents cannot skip), completes the "machines gate, humans ratify" loop end-to-end.

### Phase 6: Single-Source Dual-Runtime Emitter
**Rationale:** Depends on everything — it has no input to compile until the source in Phases 2-4 exists. Building the emitter first (tempting, since it produces the visible artifacts) produces empty scaffolding; this is an explicit anti-pattern called out by both architecture and pitfalls research.
**Delivers:** `harness/emitter` + `tools/harness-emit` generating `.opencode/{agent,command,skill,plugin,tool}` + `opencode.json` + `AGENTS.md` (primary) and `.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md` (secondary), with per-runtime limit validators (Claude skill body/description caps, opencode permission-matrix shape) that **fail the build**, never silently truncate; a CI check that re-emits and diffs to catch generated-artifact drift.
**Uses:** wshobson/agents single-source pattern (adopt the pattern, not the 194-agent payload — per PROJECT.md's explicit "custom/minimal" decision).
**Avoids:** P5 (hand-edited generated artifacts silently drifting from source), P6 (runtime-specific limits violated on emit).

### Phase Ordering Rationale

- **Contracts and the drift/golden tooling are deliberately one phase, not two** — splitting them leaves the safety net half-built and unable to protect any subsequent phase (this is explicit in ARCHITECTURE.md's build-order DAG).
- **Plugins (Phase 4) and CI (Phase 5) encode the same gate logic in two enforcement surfaces** (in-session warning vs. merge-time hard gate) — the shared tooling is built once in Phase 1 and called from both, avoiding duplicated/divergent gate logic.
- **The emitter is built last on purpose** — it is a pure function of the source produced in Phases 2-4; building it early just produces scaffolding with nothing real to compile, and prematurely committing to dual-runtime emit against a still-moving opencode surface is the deferred-complexity call FEATURES.md makes explicitly (P3 priority).
- **Within Phase 3, command sequencing matters even though they're one phase**: `/golden`-adjacent commands (`/contract-check`, `/adr`, `/checkpoint`) come before migration commands (`/strangler-step`, `/docs-sync`), because the latter depend on the safety net being *trusted*, not merely present — this mirrors the FEATURES.md MVP-vs-v1.x split even though ARCHITECTURE.md groups them in one build phase.
- **This ordering is also the pitfall-prevention path**: P1 (walking skeleton) is satisfied by treating Phase 1 as "prove one loop," not "build the constitution exhaustively"; P4/P9/P14 are structurally prevented by sequencing the normalization core and human-gate before any command that could rely on a weak comparator or a self-service golden edit; P10 is prevented by requiring golden capture (Phase 1) before strangler tooling (late Phase 3) can run.

### Research Flags

Phases likely needing deeper research during planning (opencode.ai is proxy-403'd; MEDIUM-confidence claims below need re-verification against live docs):
- **Phase 4 (Plugins + Hooks):** exact opencode hook event names/payloads (`session.created`, `experimental.chat.system.transform`, `tool.execute.before/after`, `permission.ask`), the precise 15-key permission matrix semantics and last-wins glob resolution order, and per-runtime nested-AGENTS.md merge behavior (concatenate vs. replace-at-cwd) all need verification against current opencode/Claude docs, not training-data recall.
- **Phase 6 (Single-Source Emitter):** current Claude Code SKILL.md hard limits (name/description/body caps — sources here range from "≤200 chars description" to "≤1024 chars description" across the four research files, an internal inconsistency to resolve), and opencode's exact per-artifact shape (agent `mode: subagent`, plugin export shape) should be re-verified at implementation time since both runtimes move fast.
- **Phase 3 (Agents/Commands/Skills):** description-as-routing-trigger mechanics and routing-fixture testing are a documented pattern (MEDIUM confidence) but should be validated empirically once real agents/skills exist — this is inherently something no amount of doc research substitutes for.

Phases with standard, well-documented patterns (skip `--research-phase`):
- **Phase 1 (Constitution + Golden Core):** domain contracts (integration_contracts_design.md §4-6, parser_project_revised.md §5/§8) and the golden/canonicalization approach are HIGH confidence, sourced directly from primary domain documents, not inference.
- **Phase 2 (Two-Plane Memory):** the constitution-vs-derived split and Aider-style repo-map generation (tree-sitter + PageRank) are HIGH-confidence, well-established patterns.
- **Phase 5 (CI + Gates):** GitHub Actions polyglot matrix + CODEOWNERS is a standard, well-documented pattern (HIGH confidence).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH for toolchain versions (.NET 10, uv, xunit.v3, Verify.XunitV3, syrupy, ruff, pyright, JsonSchema.Net — all verified against nuget.org/pypi.org/official release notes); MEDIUM for opencode plugin API internals (opencode.ai serves 403 to fetchers; verified via WebSearch + GitHub raw `sst/opencode` mirror, not live docs) |
| Features | MEDIUM — domain feature requirements (contract-first, polyglot safety, strangler migration) are HIGH, read directly from `integration_contracts_design.md`/`parser_project_revised.md`; harness-primitive facts (skill caps, exact hook names) are MEDIUM, grounded in training data since Context7/WebFetch/Brave/Exa/Firecrawl were all unavailable during this research pass |
| Architecture | MEDIUM-HIGH — opencode plugin/config mechanics verified against official docs + a community hook-reference gist (HIGH for the hook list); two-plane memory and dual-emit patterns are synthesized (MEDIUM) from PROJECT.md's prior 3-agent research plus verified runtime capabilities; domain contract structure is HIGH (sourced directly from the parserimprove skeleton) |
| Pitfalls | MEDIUM-HIGH — polyglot-boundary and legacy-migration pitfalls are HIGH (grounded directly in `integration_contracts_design.md` §4-5 and `parser_project_revised.md` §8/§10); harness/opencode-runtime-specific pitfalls (permission matrix, AGENTS.md merge semantics) are MEDIUM since runtime versions move fast; context-memory-rot pitfalls are MEDIUM, pattern-level rather than tool-benchmarked |

**Overall confidence:** MEDIUM-HIGH. Domain/business logic (the polyglot contracts, the migration risk profile, the golden-equivalence rationale) is HIGH across all four files because it is sourced directly from primary project documents. The opencode-runtime-specific mechanics (hook names, permission semantics, skill caps, AGENTS.md merge behavior) are consistently MEDIUM across all four files for the same reason: opencode.ai is blocked by the proxy in this environment, so every researcher corroborated via search/mirrors/community references rather than live docs.

### Gaps to Address

- **opencode.ai proxy-403 blocks direct doc verification.** Before implementing Phase 4 (hooks) and Phase 6 (emitter), re-verify against live docs (or a working fetch path): exact hook event names/payloads, the 15-key permission matrix and last-wins glob resolution, skill size/description caps for both opencode and current Claude Code, and nested-AGENTS.md merge semantics (concatenate vs. replace-at-cwd) per runtime.
- **Internal inconsistency on Claude skill description cap.** STACK.md and ARCHITECTURE.md cite "description ≤1024 chars"/"body <~500 lines" while PITFALLS.md cites "description ≤200 chars (hard limit)." Resolve this precisely at Phase 6 implementation time — the emitter's per-runtime validator must use the correct current number, not either research file's recollection.
- **Domain contract values remain genuinely undecided** (§7/§10 of `parser_project_revised.md`: exact TSV columns, DB schema, carryover/rework policy) — this is explicitly Out of Scope per PROJECT.md, not a research gap to close; the harness must ship these as clearly-flagged placeholders/examples, and the volatile memory plane must never be allowed to "silently resolve" them (Pitfall 13).
- **wshobson/agents single-source pattern is HIGH confidence as a pattern reference but was not verified against the current opencode emit target's exact frontmatter dialect** — confirm the `mode: subagent` / `.opencode/agent/<name>.md` shape at Phase 6 implementation time.

## Sources

### Primary (HIGH confidence)
- `/home/user/lifetimeworkflow/.planning/PROJECT.md` — harness scope, Out of Scope, Key Decisions, constraints
- `/workspace/presentationformat/archive/parserimprove/uploads/integration_contracts_design.md` §0, §4.1-4.7 (polyglot boundary checklist), §5, §6 (contract change management)
- `/workspace/presentationformat/archive/parserimprove/uploads/parser_project_revised.md` §2.2, §5 (golden/equivalence test strategy), §7-8 (risks, undecided items), §9-10 (staged transition)
- nuget.org / pypi.org / devblogs.microsoft.com / learn.microsoft.com — .NET 10 LTS, xunit.v3, Verify.XunitV3, JsonSchema.Net, uv, ruff, pyright, pytest, syrupy, jsonschema, check-jsonschema versions

### Secondary (MEDIUM confidence)
- WebSearch + GitHub raw `sst/opencode/packages/plugin` — plugin hooks, `PluginInput` shape, custom `tool()` helper
- github.com/wshobson/agents — single-source → per-harness adapter pattern (HIGH as a pattern reference)
- aider.chat repo-map writeup + DeepWiki Aider — tree-sitter + personalized PageRank recipe (HIGH)
- docs.claude.com / platform.claude.com agent-skills best-practices — SKILL.md size/description caps (internally inconsistent across research files — see Gaps)
- developers.openai.com/codex/guides/agents-md — nested AGENTS.md replace-vs-merge semantics (confirms per-runtime divergence exists, exact opencode/Claude behavior needs re-verification)
- pactflow.io / docs.pact.io — rationale for why Pact-style contract testing does NOT fit this domain's file/DB/CLI boundaries

### Tertiary (LOW confidence / needs validation)
- Exact opencode 15-key permission matrix key names and glob-resolution edge cases — recommend a resolver order-test suite at Phase 1-2 implementation regardless of doc verification, since this is cheap insurance either way

---
*Research completed: 2026-07-07*
*Ready for roadmap: yes*
