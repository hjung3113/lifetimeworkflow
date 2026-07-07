# Architecture Research

**Domain:** opencode agent harness for a polyglot (.NET 10 + Python) semiconductor log-parser monorepo
**Researched:** 2026-07-07
**Confidence:** MEDIUM-HIGH (opencode plugin/config mechanics verified against official docs + community references; two-plane memory and dual-emit patterns synthesized from PROJECT.md research + verified runtime capabilities. Domain contracts HIGH — sourced directly from parserimprove skeleton.)

## Executive Framing

This harness is **not an application** — it is a *config compiler plus a runtime overlay* that sits on top of a monorepo. Three architectural ideas dominate, and everything else hangs off them:

1. **Harness source-of-truth → dual-runtime emit.** One authored surface (`harness/`) is *compiled* into two runtime-native artifact sets: opencode (`.opencode/` + `opencode.json` + `AGENTS.md`) as the primary target, and Claude Code (`.claude/`) as a secondary emit. Neither runtime dir is hand-edited.
2. **Two-plane context memory.** A **constitution plane** (contracts, ADRs, glossary, golden sets — human-owned, gated, mostly hand-written) and a **derived/volatile plane** (`.memory/` — auto-regenerated repo-map, contracts-index, active-context, progress — never hand-edited, injected at session start).
3. **Contract-first safety gates.** `contracts/` outranks code. Any contract change flows through a deterministic pipeline: schema-hash → drift check → golden run → human `/golden-approve`. Polyglot correctness is enforced by *golden equivalence*, not by shared types (there are none across the .NET/Python boundary).

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  AUTHORING PLANE (source of truth — humans + agents edit here)         │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────────────────┐ │
│  │  harness/  │  │ contracts/ │  │ docs/ (Diátaxis + adr/ + glossary)│ │
│  │ agents     │  │ log-specs  │  │ reference/ (GENERATED from        │ │
│  │ commands   │  │ reference  │  │            contracts)             │ │
│  │ skills     │  │ normalize  │  └──────────────────────────────────┘ │
│  │ plugins    │  │ state      │            CONSTITUTION PLANE          │
│  │ rules      │  │ golden     │            (gated, CODEOWNERS)         │
│  │ emitter/   │  └────────────┘                                        │
│  └─────┬──────┘                                                        │
└────────┼───────────────────────────────────────────────────────────────┘
         │ tools/harness-emit  (single-source → dual emit)
         ▼
┌──────────────────────┐   ┌──────────────────────┐
│  opencode (PRIMARY)   │   │  Claude Code (2nd)    │   ← GENERATED, never hand-edited
│  .opencode/{agent,    │   │  .claude/{agents,     │
│   command,skill,      │   │   commands,skills}    │
│   plugin,tool}        │   │  .claude/settings.json│
│  opencode.json        │   │  (hooks)              │
│  AGENTS.md (root +    │   │  CLAUDE.md (root +    │
│   per-package)        │   │   per-package)        │
└──────────┬───────────┘   └──────────┬───────────┘
           │ session.created +         │ SessionStart hook
           │ chat.system.transform     │ (additionalContext)
           ▼                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  DERIVED / VOLATILE PLANE — .memory/  (auto-regenerated, injected)     │
│  repo-map.md · contracts-index.json · activeContext.md · progress.md   │
└──────────────────────────────────────────────────────────────────────┘
                              │ operates on
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  TARGET MONOREPO   components/{parser,converter(.NET) scheduler,       │
│  (placeholders now)  collector(Py)}  ·  libs/{dotnet,python}  ·  tools/│
│  boundary = process / file / DB only (no in-proc object passing)       │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility (owns) | Boundary / how it talks |
|-----------|----------------------|-------------------------|
| `harness/` (source) | Canonical, runtime-neutral definitions of agents, commands, skills, plugins, rules | Consumed only by the emitter. Never referenced directly by a runtime. |
| `harness/emitter/` (`tools/harness-emit`) | Compiles source → opencode + Claude artifacts, respecting each runtime's limits (skill size caps, hook shape, frontmatter dialect) | Reads `harness/`, writes `.opencode/`, `.claude/`, `opencode.json`, `AGENTS.md`, `CLAUDE.md`. Pure function of source; idempotent. |
| `.opencode/` + `opencode.json` + `AGENTS.md` | Primary runtime surface: agents, commands, skills, plugins, permission matrix, instructions globs, MCP, formatter | Generated artifact. Loaded by opencode at runtime. |
| `.claude/` + `settings.json` + `CLAUDE.md` | Secondary runtime surface for Claude Code (dev-time) | Generated artifact. GSD's existing `.claude/` (get-shit-done) is *separate* and untouched by emit. |
| `contracts/` (constitution) | Single source of every cross-language format: log-specs (TSV), reference-data, normalization rules, state/carryover, golden sets | Read by everything; written only via gated PR. Seeded from parserimprove skeleton as **examples/placeholders**. |
| `docs/` (constitution) | Diátaxis (tutorials/how-to/reference/explanation) + `adr/` (immutable MADR) + `glossary`. `reference/` is *generated from contracts*, agent-maintained | Human reads; agents generate `reference/`. ADRs append-only. |
| `.memory/` (derived plane) | Volatile session state + derived indices: `repo-map`, `contracts-index`, `activeContext`, `progress` | Auto-regenerated by plugin/hook; injected at session start. Never hand-edited (git-ignored or clearly marked derived). |
| `components/`, `libs/` | Placeholders for the *implementation* the harness will help build (out of scope to implement now) | Boundary is process/file/DB only. `libs/{dotnet,python}` for shared code, not cross-language. |
| `tools/` | Emitter, contract-hasher, drift-checker, golden-runner, memory-regenerator, toolchain bootstrap | Invoked by CI, plugins, and commands. |
| `.github/` | Polyglot matrix CI, CODEOWNERS (gates constitution plane), PR template (breaking-change checklist) | Enforces gates that cannot be trusted to the agent. |

## Recommended Project Structure

```
lifetimeworkflow/                      # THIS repo = the target monorepo
├── AGENTS.md                          # GENERATED root instructions (opencode primary)
├── CLAUDE.md                          # GENERATED root instructions (Claude emit)
├── opencode.json                      # GENERATED: models, 15-key permission matrix,
│                                      #   instructions globs, MCP, formatter
│
├── harness/                           # ◄── SOURCE OF TRUTH (authored; runtime-neutral)
│   ├── agents/                        #   orchestrator, dotnet, python, reviewer,
│   │   └── *.md                       #   golden-runner, polyglot-auditor, explorer
│   ├── commands/                      #   /golden /golden-approve /contract-check
│   │   └── *.md                       #   /new-normalization-rule /adr /strangler-step
│   │                                  #   /docs-sync /component /checkpoint
│   ├── skills/                        #   dotnet, python, pipeline-patterns,
│   │   └── <skill>/SKILL.md           #   data-contracts, golden-testing,
│   │                                  #   normalization-catalog, skill-creator
│   ├── plugins/                       #   contract-guard, session-start injector,
│   │   └── *.ts                       #   format-on-write, polyglot-boundary linter
│   ├── rules/                         #   shared rule fragments composed into AGENTS.md
│   │   └── *.md                       #   (constitution pointers, polyglot invariants)
│   ├── partials/                      #   per-package AGENTS.md templates (nearest-wins)
│   └── emitter/                       #   dialect adapters: opencode.ts, claude.ts,
│       └── limits.ts                  #   per-runtime constraints (skill size, hooks)
│
├── contracts/                         # ◄── CONSTITUTION PLANE (gated, CODEOWNERS)
│   ├── log-specs/standard-log.spec.yaml        # seeded example (placeholder columns)
│   ├── reference-data/equipment-master.yaml    # seeded example
│   ├── normalization/correction-rules.catalog.yaml
│   ├── state/equipment-progress.yaml           # carryover model
│   ├── golden/                                  # golden set metadata + fixtures
│   │   └── README.md
│   └── .hashes/                        # GENERATED schema hashes (drift baseline)
│
├── docs/                              # ◄── CONSTITUTION PLANE (Diátaxis)
│   ├── tutorials/                     #   learning-oriented (hand-written)
│   ├── how-to/                        #   task-oriented (hand-written)
│   ├── reference/                     #   GENERATED from contracts (agent-maintained)
│   ├── explanation/                   #   00-system-and-structure etc. (hand-written)
│   ├── adr/                           #   immutable MADR, append-only
│   │   └── NNNN-*.md
│   └── glossary.md                    #   single term definitions
│
├── components/                        # placeholders (implementation OUT OF SCOPE)
│   ├── parser/        (.NET csproj)
│   ├── converter/     (.NET csproj)
│   ├── scheduler/     (Python pyproject / uv)
│   └── collector/     (Python)
├── libs/
│   ├── dotnet/        (shared NuGet)
│   └── python/        (shared pip pkg)
│
├── tools/
│   ├── harness-emit/          # runs harness/emitter → .opencode + .claude
│   ├── contract-hash/         # canonicalize + hash each contract schema
│   ├── contract-drift/        # compare hashes vs baseline, classify breaking
│   ├── golden-runner/         # normalized equivalence comparator (lang-agnostic)
│   ├── memory-regen/          # rebuild repo-map + contracts-index
│   └── bootstrap/             # .NET 10 SDK install + uv workspace setup
│
├── .memory/                   # ◄── DERIVED / VOLATILE PLANE (auto-regen, git-ignored)
│   ├── repo-map.md            #   derived structure map
│   ├── contracts-index.json   #   queryable index of all contracts + hashes
│   ├── activeContext.md       #   current task focus (volatile)
│   └── progress.md            #   what's done / next (volatile)
│
├── .opencode/                 # GENERATED runtime surface (primary)
│   ├── agent/ command/ skill/ plugin/ tool/
├── .claude/
│   ├── (GENERATED) agents/ commands/ skills/ settings.json   ◄─ harness emit
│   └── get-shit-done/          # EXISTING GSD install — SEPARATE, untouched
│
└── .github/
    ├── workflows/ci.yml       # polyglot matrix (.NET 10 + Python/uv) + gates
    ├── CODEOWNERS             # constitution plane requires human approval
    └── pull_request_template.md   # breaking-change + golden checklist
```

### Structure Rationale

- **`harness/` is the only place humans/agents author runtime config.** Everything under `.opencode/` and `.claude/{agents,commands,skills}` is a build artifact. This prevents the classic "two runtimes drift apart" failure — there is exactly one source.
- **`contracts/` and `docs/adr/` are physically separated from `.memory/`** because they have opposite lifecycles: constitution is durable + gated + versioned; derived plane is disposable + regenerated. Co-locating them invites hand-editing of derived files (rot).
- **`docs/reference/` lives under the human docs tree but is generated** — this is the one place the two planes touch. It is agent-owned, contract-sourced, and regenerated, so it is marked as such at the top of each file.
- **The pre-existing `.claude/get-shit-done/` is quarantined** from emit output. GSD drives *development* of the harness; the harness's own emitted `.claude/` artifacts are the *product*. The emitter must never write into `get-shit-done/`.

## Architectural Patterns

### Pattern 1: Single-Source → Dual-Runtime Emit

**What:** `harness/` holds runtime-neutral definitions (frontmatter + markdown for agents/commands/skills; TS for plugins). `tools/harness-emit` transforms each into runtime-native form.

**When to use:** Always. Never edit `.opencode/` or emitted `.claude/` by hand.

**Runtime-limit reconciliation the emitter must encode (verified constraints):**

| Concern | opencode (primary) | Claude Code (emit) |
|---------|--------------------|--------------------|
| Root instructions file | `AGENTS.md` (preferred; CLAUDE.md ignored if both present) | `CLAUDE.md` |
| Context-file globs | `opencode.json` `instructions` array | `@import` / settings |
| Session-start injection | `session.created` event + `experimental.chat.system.transform` (no literal SessionStart hook) | `SessionStart` hook → `additionalContext` |
| Plugins | JS/TS module exporting hooks (`.opencode/plugin/`) | shell hooks in `settings.json` |
| Permission model | `opencode.json` permission keys, bash **glob last-wins** | `settings.json` allow/deny/ask lists |
| Skills | `skill/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` (size-capped) |

**Trade-off:** The emitter is extra machinery, but it is the only way to keep two runtimes coherent. Because opencode and Claude differ *most* on hooks/injection, plugin logic should live as small, testable functions that each adapter wraps — not as runtime-specific spaghetti.

### Pattern 2: Two-Plane Context Memory

**What:** Split memory by *authorship and lifecycle*, not by topic.

| | Constitution plane | Derived / volatile plane |
|---|---|---|
| Location | `contracts/`, `docs/adr/`, `docs/glossary.md`, `contracts/golden/` | `.memory/` |
| Authorship | Human (agent-assisted), gated via CODEOWNERS | Machine (`tools/memory-regen`, plugins) |
| Lifecycle | Durable, versioned, append-only for ADRs | Disposable, regenerated every session |
| Hand-editing | Required (this is intent/decisions) | **Forbidden** (rot source) |
| Examples | TSV spec, normalization catalog, ADRs, glossary | repo-map, contracts-index, activeContext, progress |

**Injection mechanism (the "un-ignorable" part):**
- **opencode:** a `session-start` plugin subscribes to `session.created`, calls `tools/memory-regen` to rebuild `.memory/`, and uses `experimental.chat.system.transform` to prepend the derived plane + constitution pointers into the system prompt.
- **Claude Code:** the emitted `settings.json` `SessionStart` hook runs the same regen and returns `additionalContext`.
- **Lazy / nearest-wins detail:** full contracts are *not* injected. The system prompt injects the **contracts-index** (queryable) + repo-map + active state; per-package `AGENTS.md` (emitted into each `components/*` dir) provides nearest-wins local rules loaded only when the agent works in that package. Deep contract bodies are pulled **on demand** via skills/references.

**Trade-off:** Regenerating on every session costs a few seconds but guarantees the agent never reasons from stale derived state. Volatile files must be git-ignored (or a `.memory/README` marks them derived) so humans never edit them.

### Pattern 3: Contract-First with Schema-Hash Drift Gate

**What:** Each contract file is canonicalized (stable key order, normalized whitespace) and hashed; the hash baseline lives in `contracts/.hashes/`. Any change to a schema changes its hash; `tools/contract-drift` classifies the change as breaking (log-spec columns, DB/state schema, reference-data structure) vs non-breaking.

**When:** Every PR touching `contracts/`. Enforced in CI, not left to the agent.

**Trade-off:** Hashing is cheap and language-agnostic — exactly right for a polyglot repo where you cannot share compile-time types across .NET/Python.

### Pattern 4: Golden Equivalence Gate

**What:** Golden sets in `contracts/golden/` hold input → expected-normalized-output fixtures. `tools/golden-runner` compares component output after *normalization* (encoding→UTF-8 no BOM, LF, InvariantCulture decimals, UTC, TSV escaping, null vs empty) so a .NET and a Python producer are judged equal on *meaning*, not bytes. This is the polyglot safety net that catches representation-difference bugs (the domain's #1 risk class).

**When:** On any contract change and on any component change that could alter output.

### Pattern 5: Nearest-Wins Layered Instructions

**What:** Root `AGENTS.md` holds repo-wide invariants (contract-first, polyglot boundary rules, constitution pointers). Each `components/<pkg>/AGENTS.md` holds package-local rules and is loaded only when the agent is working there. opencode resolves the nearest instruction file; deeper files override shallower.

**Trade-off:** Keeps the always-loaded context small while giving precise local guidance — but per-package files must also be *generated* from `harness/partials/` so they don't drift.

## Data Flow

### Flow A: Session Context Injection (every session)

```
session start (opencode session.created  /  Claude SessionStart hook)
   ↓
tools/memory-regen  →  rebuild .memory/{repo-map, contracts-index}
   ↓
plugin reads .memory/ + constitution pointers
   ↓
inject into system prompt
   (opencode: experimental.chat.system.transform ;  Claude: additionalContext)
   ↓
agent starts with: derived state + contracts-index (queryable) + active task
   ↓  (on demand, nearest-wins)
agent enters components/parser/ → parser AGENTS.md loads → pulls full log-spec via skill
```

### Flow B: Contract-Drift + Golden Safety Gate (the core enforcement path)

```
1. author edits contracts/log-specs/standard-log.spec.yaml   (PR)
        ↓
2. contract-guard plugin (tool.execute.before on write to contracts/**)
     → warns agent: "constitution plane — gated"
        ↓
3. tools/contract-hash  → recompute canonical schema hash
        ↓
4. tools/contract-drift → diff hash vs contracts/.hashes baseline
     ├─ no change  → pass
     ├─ non-breaking → note in PR
     └─ BREAKING (columns / DB / reference structure) → require golden update
        ↓
5. tools/golden-runner → run golden set through affected component(s),
     compare NORMALIZED output vs expected
     ├─ equivalent → gate green
     └─ diff → gate red, block merge
        ↓
6. CI (.github/workflows/ci.yml) polyglot matrix runs 3-5 on both languages
        ↓
7. CODEOWNERS forces human review of contracts/**  +  /golden-approve
     → human command updates golden baseline + contracts/.hashes
        ↓
8. merge → new hash baseline committed → next drift check measures against it
```

**Direction of authority:** contracts → hash → drift → golden → human approve. The agent may *propose* every step; only the human `/golden-approve` + CODEOWNERS can *ratify* a baseline change. Machines gate; humans ratify.

## Build Order (dependency DAG — drives roadmap phases)

The harness must be built bottom-up because later layers *reference and enforce* earlier ones. Building agents before contracts, or the emitter before the source it emits, produces empty scaffolding.

```
Phase 1  CONSTITUTION FIRST
  contracts/ (seed from parserimprove skeleton as examples)
  + docs/ (Diátaxis skeleton + adr/0001 + glossary)
  + contract-hash / contract-drift tooling + .hashes baseline
     └─ WHY FIRST: every rule, agent, and gate points at contracts.
        Nothing downstream is meaningful without the source of truth.
        ↓
Phase 2  MEMORY + RULES
  .memory/ derived-plane generators (memory-regen: repo-map, contracts-index)
  + root AGENTS.md rules + per-package partials + nearest-wins layout
     └─ DEPENDS ON: contracts (index is derived from them).
        Establishes the two-plane split before any agent consumes context.
        ↓
Phase 3  AGENTS + COMMANDS + SKILLS (authored in harness/)
  orchestrator/dotnet/python/reviewer/golden-runner/polyglot-auditor/explorer
  + /golden /contract-check /strangler-step /adr /docs-sync ... commands
  + dotnet/python/data-contracts/golden-testing/... skills
     └─ DEPENDS ON: rules + memory (agents inject them) and contracts (skills read them).
        ↓
Phase 4  PLUGINS + HOOKS
  contract-guard, session-start injector, format-on-write, polyglot-boundary linter
     └─ DEPENDS ON: memory-regen (session-start calls it), contracts (guard watches them),
        agents (guard warns them). Hooks are the runtime enforcement of Phases 1-3.
        ↓
Phase 5  CI + GATES
  .github polyglot matrix + CODEOWNERS + PR template + golden-runner in CI
     └─ DEPENDS ON: drift + golden tooling (Phase 1) and plugins (Phase 4);
        CI is the non-bypassable mirror of the plugin gates + human ratification path.
        ↓
Phase 6  SINGLE-SOURCE EMITTER (dual-runtime)
  harness/emitter + tools/harness-emit → generate .opencode + opencode.json
  + AGENTS.md + .claude/ + CLAUDE.md, respecting per-runtime limits
     └─ DEPENDS ON EVERYTHING: it emits the source produced in Phases 2-4.
        Build last because it has nothing to compile until the source exists.
```

**Cross-cutting (Phase 0 / continuous):** `tools/bootstrap` (.NET 10 SDK install + uv workspace) is wired into session-start early but can be stubbed until Phase 4 hooks exist. Because the environment is ephemeral, bootstrap must be idempotent and self-healing.

**Key ordering implications for the roadmap:**
- Do **not** build the emitter first (tempting, since it produces the visible artifacts) — it has no input until the source layers exist.
- Contracts and the drift/golden tooling are a *single* early phase; splitting them leaves the gate half-built and unable to protect subsequent work.
- Plugins (Phase 4) and CI (Phase 5) encode the *same* gate logic in two enforcement surfaces (in-session vs merge-time); build the shared tooling once (Phase 1) and call it from both.

## Anti-Patterns

### Anti-Pattern 1: Hand-editing generated runtime dirs
**What people do:** Tweak `.opencode/agent/*.md` or emitted `.claude/` directly to fix something fast.
**Why wrong:** Next emit overwrites it; the two runtimes silently diverge.
**Instead:** Edit `harness/`, re-run `tools/harness-emit`. Treat `.opencode/` and emitted `.claude/` as build output (consider a CI check that fails if they're dirty vs a fresh emit).

### Anti-Pattern 2: Putting derived state in the constitution plane (or vice-versa)
**What people do:** Commit hand-written notes into `.memory/`, or let an agent "remember" a decision only in `activeContext.md`.
**Why wrong:** `.memory/` is regenerated → the note vanishes. Decisions must be durable.
**Instead:** Decisions → append-only ADR (constitution). Transient focus → `.memory/` (derived). If it must survive a session, it is not derived.

### Anti-Pattern 3: Injecting full contracts into every session
**What people do:** Dump all of `contracts/` into the system prompt "so the agent always knows."
**Why wrong:** Blows the context budget; the domain has many spec/reference files.
**Instead:** Inject the **contracts-index** (queryable) + repo-map; load full bodies on demand via skills and nearest-wins per-package `AGENTS.md`.

### Anti-Pattern 4: Trusting the agent to be the gate
**What people do:** Rely on an agent instruction "always run golden before changing a contract."
**Why wrong:** Instructions are advisory; a gate that can be skipped is not a gate.
**Instead:** Enforce in CI + CODEOWNERS + `/golden-approve`. The plugin is a *fast warning*; CI is the *hard gate*; the human is the *ratifier*.

### Anti-Pattern 5: Byte-equality golden comparison
**What people do:** `diff` .NET vs Python output directly.
**Why wrong:** Representation differences (BOM, CRLF, decimal locale, TZ) create false failures and mask real ones.
**Instead:** Normalize both sides (UTF-8 no BOM, LF, InvariantCulture, UTC, defined null/empty) *then* compare — the golden-runner owns this normalization.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| harness/ ↔ runtime dirs | one-way emit (tools/harness-emit) | never reverse; runtime dirs are artifacts |
| constitution plane ↔ derived plane | one-way derive (memory-regen, docs/reference gen) | derived reads constitution, never writes it |
| plugin gate ↔ CI gate | shared tooling (contract-hash/drift/golden) | two surfaces, one implementation |
| .NET components ↔ Python components | process / file / DB only | no in-proc object passing; enforced by polyglot-boundary linter |
| harness emit ↔ GSD .claude/get-shit-done | none — quarantined | emitter must not write into get-shit-done/ |

### External / Runtime

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| opencode runtime | reads opencode.json + .opencode/ + AGENTS.md; plugins via JS hooks | primary target |
| Claude Code runtime | reads CLAUDE.md + .claude/ + settings.json hooks | secondary emit; also the dev-time driver (GSD) |
| .NET 10 SDK / uv | bootstrapped by tools/bootstrap at session-start | env is ephemeral → must self-install idempotently |
| MCP servers | declared in opencode.json | optional; emit to Claude equivalent |

## Sources

- OpenCode Config docs — opencode.json (instructions, permissions, agents, MCP): https://opencode.ai/docs/config/ (403 on direct fetch; corroborated via search + mirror) — MEDIUM
- OpenCode Plugins docs + hook reference (session.created, tool.execute.before/after, experimental.chat.system.transform, permission events): https://opencode.ai/docs/plugins/ and https://gist.github.com/johnlindquist/0adf1032b4e84942f3e1050aba3c5e4a — HIGH (hook list verified against community reference)
- OpenCode Agents / Commands / Skills / Rules docs: https://opencode.ai/docs/agents/, /commands/, /skills/, /rules/ — MEDIUM
- parserimprove monorepo_skeleton (contracts, docs 00-04, README) — domain source of truth — HIGH
- integration_contracts_design.md (§4 cross-cutting contracts, §5 Py↔.NET checklist, §6 change management) — HIGH
- .planning/PROJECT.md (harness requirements, 3-agent research synthesis, key decisions) — HIGH

---
*Architecture research for: opencode agent harness (polyglot .NET/Python log-parser monorepo)*
*Researched: 2026-07-07*
