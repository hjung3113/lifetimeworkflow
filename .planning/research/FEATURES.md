# Feature Research

**Domain:** Agent harness (opencode-first, single-source→Claude Code) for a polyglot (.NET 10 + Python), contract-first, legacy-migration monorepo — semiconductor equipment log-parser pipeline
**Researched:** 2026-07-07
**Confidence:** MEDIUM
(Domain contracts = HIGH — read directly from `integration_contracts_design.md` §4-5 and `parser_project_revised.md` §5. Harness-primitive facts = MEDIUM — grounded in training data; Context7/WebFetch/Brave/Exa/Firecrawl all unavailable in this environment, see Sources.)

---

## Framing: who the "users" are

The deliverable is the harness, not the pipeline. Two user classes:

1. **Developers** working in the monorepo — want the toolchain wrapped, conventions enforced, tribal knowledge made executable.
2. **Coding agents** operating on the repo — want personas, scoped permissions, progressive-disclosure skills, and durable cross-session memory so they behave consistently.

"Table stakes" = what any mature coding-agent harness provides (missing = the harness feels broken/unsafe). "Differentiators" = capabilities that only make sense for THIS contract-first, polyglot, strangler-migration project — this is where the Core Value ("contracts as single source of truth; harness auto-enforces polyglot representation gaps + legacy-transition risk") lives. "Anti-features" = things a naive harness would add that actively harm this project.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Baseline capabilities of any credible opencode/Claude Code agent harness. Users don't reward these; they penalize their absence.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **`opencode.json` core config** (model tiering, instructions glob, MCP, formatter) | Every opencode harness is bootstrapped from this file; nothing else loads without it | MEDIUM | Foundational — all other features depend on it. Model tiering (cheap explorer / strong implementer) is a cost + quality lever. |
| **15-key permission matrix** (bash glob, last-wins) | Agents must be sandboxed; unrestricted `bash`/`edit` is unacceptable for a repo touching servers/DB | MEDIUM | last-wins glob ordering is subtle — allow broad, deny narrow, order matters. Must be tested. Reviewer agent = read-only via permission scoping. |
| **Agent personas** — orchestrator + per-language implementers (dotnet, python) + read-only reviewer + explorer | Polyglot repo needs language-scoped agents; separation of "decides" vs "implements" vs "reviews" vs "reads" is standard | MEDIUM | Must-cover adds golden-runner + polyglot-auditor (see differentiators). Personas differ by tools, model tier, and permission scope. |
| **Slash commands wrapping the toolchain** | Developers/agents shouldn't memorize `dotnet test` / `uv run` / CI invocations; commands encode the canonical way | LOW–MEDIUM each | Thin wrappers are LOW; contract/golden/strangler commands are their own differentiators (below). |
| **Skills with progressive disclosure** (dotnet, python, pipeline-patterns, data-contracts, golden-testing, normalization-catalog, skill-creator) | Loading all knowledge always blows context; SKILL.md front-matter + lazy body load is the expected pattern | MEDIUM | Respect per-runtime size limits (Claude Code skill body caps differ from opencode). skill-creator = meta-skill for maintaining the set. |
| **Rules / AGENTS.md** (root + per-package, lazy-loaded) | The canonical "how we work here" file both runtimes read; per-package files scope conventions to .NET vs Python subtrees | LOW to write / MEDIUM to get right | Per-package AGENTS.md lazy-loading avoids dumping both languages' rules into every session. |
| **Hooks / plugins: format-on-write** | Auto-format on edit is baseline hygiene; prevents diff noise and enforces the formatter from config | MEDIUM (plugin dev) | Ties to `formatter` in opencode.json. Also the enforcement point for LF/encoding (see polyglot linter). |
| **Hooks: secret protection** | Blocking writes/reads of secrets is a safety baseline for any repo touching AP/DB servers | MEDIUM | Deny-list + pattern scan on tool.execute.before. |
| **Hooks: commit gate** | Prevent agents committing when tests/gates fail; "green before commit" is expected | MEDIUM | Composes with contract-drift + golden gates — the gate is where differentiators plug in. |
| **MCP server wiring** | Standard extension surface; expected to be configurable even if unused at MVP | LOW | Config-only at MVP. |
| **Session/memory files** (activeContext, progress) | Cross-session continuity is now an expected harness feature (memory-bank pattern) | MEDIUM | Becomes a differentiator via the two-plane split + non-ignorable injection (below). |

### Differentiators (Competitive Advantage)

Project-specific capabilities that encode contract-first + polyglot-safety + strangler-migration into the harness. These are the reason to build a bespoke harness instead of porting a generic one.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Single-source multi-runtime emit** (opencode primary + Claude Code `.claude/` artifacts) | Author once, run in dev (Claude Code + GSD) and deploy (opencode) without drift; respects each runtime's constraints | HIGH | Needs a canonical source format + emit/build step + per-runtime constraint model (e.g. skill size caps, command syntax). Cross-cutting; wshobson single-source pattern. Drift between emitted artifacts is the main risk. |
| **Contract-drift CI gate (schema hash)** | Contracts are the constitution; a silent schema change is the #1 polyglot failure mode. Hash the TSV spec / DB schema / .proto and fail CI on unblessed change | MEDIUM | Directly implements `integration_contracts_design.md` §6 ("change requires golden update"). Composes into the commit gate + CI. |
| **Golden / approval equivalence commands** — `/golden` (run + normalized diff) and `/golden-approve` (bless via CODEOWNERS human sign-off) | Language-agnostic safety net for legacy→new equivalence (`parser_project_revised.md` §5.1). The single most important migration control | HIGH | Comparator must normalize encoding/BOM/LF/TZ/decimal BEFORE diff, else false diffs. Approval requires a human (CODEOWNERS) — agents must NOT self-bless (see anti-features). |
| **`/new-normalization-rule`** (contract-first ordering: contract → data-driven test → code) | 50+ maker/model normalization+correction cases; enforce that the contract (normalization-catalog) and a data-driven (input,expected) case are added BEFORE code | MEDIUM | Implements §5.4 data-driven parametrized tests. Prevents the legacy failure mode of normalization logic scattered across code. |
| **`/adr`** (append-only MADR) | Decisions are the durable/constitutional layer; immutable ADRs stop re-litigation and capture legacy-spec discoveries | LOW | §8 risk mitigation: "discovered legacy spec → document it." Cheap, high leverage. |
| **`/strangler-step`** (incremental legacy extraction, parity-gated) | Encodes the migration philosophy: extract one path, prove equivalence via golden, never big-bang (§9 staged transition) | HIGH | Each step = scope a slice → run `/golden` → require parity before merge. This is the anti-thesis of the big-bang anti-feature. |
| **`/docs-sync`** (regenerate Diátaxis reference from contracts) | reference/ docs are DERIVED, not hand-written — keeps docs from rotting out of sync with the contract single-source | MEDIUM–HIGH | Only reference/ is generated; tutorials/how-to/explanation stay human-authored. Depends on contracts being machine-readable enough to generate from. |
| **`/component` scaffold** | New components (converter, parser, collector…) must be born with the right structure, AGENTS.md, test harness, boundary conventions | MEDIUM | Encodes §3.1 responsibility separation + testable-by-design (§5.3) so agents can't create untestable god-functions (the legacy problem 2.2). |
| **Two-plane context memory + SessionStart injection** | Split constitutional plane (contracts, adr, glossary, golden — human-owned, gated) from derived/volatile plane (.memory/ activeContext, progress + derived repo-map, contracts-index); inject via non-ignorable SessionStart hook | HIGH | The memory architecture. Derived artifacts auto-regenerate (never hand-maintained); volatile state force-injected so agents can't miss it. Independent of GSD `.planning/`. |
| **`/checkpoint`** (memory-bank update) | Durable progress capture across ephemeral remote containers; agents resume with correct state | LOW–MEDIUM | Writes the volatile plane (activeContext/progress). Container is ephemeral → checkpoints must be committed. |
| **Polyglot-boundary linter/plugin** (encoding / BOM / LF / TSV escape / timezone / decimal / null enforcement) | The bugs are in representation, not logic (§0, §4.3–4.6). Turn the §4–5 checklist into an executable linter at the boundary | MEDIUM–HIGH | UTF-8 no-BOM, LF-only, tab-delimited escape rules, UTC/ISO-8601 strings, InvariantCulture `.` decimals, explicit null-vs-empty. Runs on-write (hook) and in CI. This is the harness's signature polyglot safety net. |
| **Domain contract + docs seed** (parserimprove monorepo_skeleton: TSV spec, normalization, master-data, state placeholders) | Concrete example contracts make the harness verifiable and immediately useful vs an empty generic scaffold | LOW–MEDIUM | Ships as seed/placeholders (domain values are Out of Scope / undecided per §7, §10). |
| **Toolchain bootstrap** (.NET 10 SDK install script + uv workspace + polyglot matrix CI skeleton, wired to SessionStart/setup) | Remote ephemeral container has no .NET 10 SDK; harness must self-bootstrap or agents stall | MEDIUM | SessionStart-triggered. uv already present; .NET 10 SDK install script required. |

### Anti-Features (Commonly Requested, Often Problematic)

Things a naive or generic harness would add that actively damage THIS project. Documented to prevent scope creep and to give agents explicit refusal grounds.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Big-bang rewrite command** (e.g. `/rewrite-legacy`, "port the whole parser at once") | Feels faster; "just replace the ugly legacy in one shot" | Legacy spec is undocumented (§8) and equivalence is the top risk (§2.2, §8). A big-bang has no parity checkpoints → silent regressions in downstream statistics | `/strangler-step` — extract one path, gate each on golden equivalence, never all at once (§9 staged) |
| **Agents auto-blessing / auto-approving golden files** | "The diff is probably fine, let the agent approve it to unblock CI" | Destroys the safety net — the whole point of golden is a HUMAN confirms only-intended diffs. Auto-bless means regressions get rubber-stamped | `/golden-approve` requires CODEOWNERS human sign-off; agents may propose but never approve. Hard-deny in permission matrix. |
| **Hand-maintained reference docs** | "Just write the API/schema docs in markdown like everyone does" | reference/ drifts from the contract single-source instantly; contract-first means docs must be derived | `/docs-sync` regenerates reference/ from contracts. Humans write only tutorials/how-to/explanation. |
| **Component implementation logic in the harness** (parser/converter/scheduler/collector algorithms, real column values, DB schema) | "While we're here, let's just implement the parser too" | Explicitly Out of Scope (PROJECT.md) — deliverable is the harness. Domain values are undecided (§7, §10); baking guesses in creates false contracts | Harness ships scaffolds, contracts-as-placeholders, and skills that guide humans to fill logic in-house. |
| **Object-level / in-memory language interop** (shared objects, embedded runtime, FFI between .NET and Python) | "Avoid the overhead of files/processes; just pass objects" | Violates the core boundary rule (§0): boundaries must be language-neutral (process/file/DB only). Reintroduces the representation-mismatch bugs the harness exists to prevent | Enforce coarse-grained boundaries; A-model = CLI spawn + exit codes (§4 ①). B-model (gRPC/MQ) as an extension point only. |
| **Auto-mutating the constitutional plane** (agent edits contracts/adr/glossary freely) | "Let the agent keep contracts up to date automatically" | Contracts/ADRs are human-owned and gated; auto-edits bypass the drift gate and immutability of ADRs → the single source of truth becomes untrustworthy | Agents propose contract changes via PR that trip the contract-drift gate + require human review; ADRs are append-only. |
| **Full B-model (gRPC/message-queue) runtime implementation** | "Build the scalable worker/queue now" | Out of Scope; MVP is A-model (CLI spawn) robustness. Premature B-model adds infra without payoff | Encode A-model contracts; keep job payload shape isomorphic so A→B is a later command/skill extension (§4 ④). |
| **Porting a 750-file generic harness** (gsd-opencode port) | "Reuse an existing big harness instead of building" | Generic bulk buries the domain-specific contract/golden/polyglot controls that are the entire value; maintenance burden | Bespoke, minimal, domain-accurate harness (Key Decision in PROJECT.md). |
| **"Real-time everything" progress streaming as SSOT** | "Stream live job progress and treat it as state" | DB is the SSOT (§4.1, §7 ⑦); socket/stream progress is volatile signal only. Dual sources of truth = the exact bug being removed | Volatile progress → derived plane at most; confirmed state → DB only. |

---

## Feature Dependencies

```
opencode.json (config, permission matrix, model tiers, formatter, MCP)
    └──requires──> AGENTS.md rules (root + per-package)
                       └──requires──> Agent personas (orchestrator/dotnet/python/reviewer/explorer/golden-runner/polyglot-auditor)
                                          └──requires──> Slash commands (toolchain wrappers)
                                          └──requires──> Skills (progressive disclosure)

Domain contract + docs seed (constitutional plane)
    └──requires──> Contract-drift CI gate (schema hash)
    └──requires──> /new-normalization-rule (contract-first ordering)
    └──requires──> /docs-sync (derive reference/ from contracts)
    └──requires──> Polyglot-boundary linter (§4-5 checklist encoded)

Golden fixtures + normalization comparator (encoding/LF/TZ/decimal-aware)
    └──requires──> /golden (run + normalized diff)
                       └──requires──> /golden-approve (CODEOWNERS human sign-off)
                                          └──requires──> /strangler-step (parity-gated extraction)

Two-plane memory files (.memory/ + derived repo-map, contracts-index)
    └──requires──> SessionStart injection plugin (non-ignorable)
    └──requires──> /checkpoint (writes volatile plane)

Hooks: format-on-write ──enables──> Polyglot-boundary linter (LF/encoding enforcement on-write)
Commit gate ──composes──> {contract-drift gate, /golden parity, polyglot linter}
Toolchain bootstrap (.NET 10 + uv + CI matrix) ──enables──> golden-runner + implementer agents (nothing runs without SDK)

Single-source multi-runtime emit ──wraps──> {agents, commands, skills, plugins}  (cross-cutting build step)

/strangler-step ──CONFLICTS──> big-bang rewrite (mutually exclusive migration philosophies)
Agent auto-approval ──CONFLICTS──> /golden-approve human gate (safety-net integrity)
Hand-written reference docs ──CONFLICTS──> /docs-sync (derived-docs integrity)
```

### Dependency Notes

- **Everything requires `opencode.json`:** it defines model, the 15-key permission matrix, instructions glob, and formatter. No agent, command, or hook resolves without it. Build first.
- **Personas require the permission matrix + AGENTS.md:** the read-only reviewer and language-scoped implementers are *defined by* their permission scope and rules; personas without scoping are theater.
- **All contract-first commands require the contract seed:** `/contract-check`, contract-drift gate, `/new-normalization-rule`, and `/docs-sync` all read the constitutional plane. Seed the placeholders before building these.
- **`/golden-approve` requires `/golden`, `/strangler-step` requires both:** the migration workflow is a chain — you cannot bless a candidate that wasn't produced, and you cannot strangler-extract without a parity gate. Order golden → approve → strangler.
- **The comparator is the load-bearing dependency of the whole safety net:** if the normalized-diff comparator doesn't neutralize encoding/BOM/LF/TZ/InvariantCulture-decimal differences first (§4.3–4.6), every golden run produces false diffs and the net is worthless. The polyglot-boundary linter and the golden comparator share this normalization core — build it once, reuse.
- **SessionStart injection requires the derived artifacts to exist and be regenerable:** repo-map and contracts-index must have a generator before the hook can inject them; otherwise it injects stale hand-written junk (which is itself an anti-feature).
- **Single-source emit wraps all four surfaces:** it's a cross-cutting build concern, not a leaf feature. Design the canonical source format before authoring many agents/commands, or you'll retrofit painfully.
- **Toolchain bootstrap gates all execution:** golden-runner and .NET implementer agents are inert until the .NET 10 SDK install script runs (SDK is absent in the ephemeral container). Wire it to SessionStart/setup early.

---

## MVP Definition

### Launch With (v1) — validate the core value: contracts-as-constitution + polyglot safety enforced by the harness

- [ ] **`opencode.json` + 15-key permission matrix** — nothing loads without it; read-only reviewer + language scoping depend on it.
- [ ] **AGENTS.md (root + per-package) + core personas** (orchestrator, dotnet, python, reviewer, explorer) — the operating surface.
- [ ] **Contract + docs seed (constitutional plane)** — placeholders that make everything else concrete and testable.
- [ ] **Normalization comparator + `/golden` + `/golden-approve` (CODEOWNERS)** — the migration safety net; the single most important control.
- [ ] **Contract-drift CI gate (schema hash)** — enforces contracts-first; cheap once the seed exists.
- [ ] **Polyglot-boundary linter (§4-5 checklist)** — signature safety net; shares the comparator's normalization core.
- [ ] **Hooks: format-on-write + secret protection + commit gate** — baseline safety, and the composition point for gates.
- [ ] **Two-plane memory + SessionStart injection + `/checkpoint`** — durable state across ephemeral containers.
- [ ] **Toolchain bootstrap (.NET 10 install + uv + CI skeleton)** — otherwise agents stall on a machine with no SDK.

### Add After Validation (v1.x) — once the safety net is proven on real seed data

- [ ] **`/strangler-step`** — trigger: golden equivalence is trusted enough to gate real extractions.
- [ ] **`/new-normalization-rule`** — trigger: first real normalization cases need contract-first onboarding.
- [ ] **`/docs-sync`** — trigger: reference/ starts drifting from contracts.
- [ ] **`/component` scaffold** — trigger: second/third component needs consistent birth.
- [ ] **`/adr`** — trigger: first architectural decision worth freezing (can also land in v1, it's cheap).
- [ ] **golden-runner + polyglot-auditor specialized agents** — trigger: golden/linter workflows are heavy enough to warrant dedicated personas.
- [ ] **skill-creator + full skill set** (pipeline-patterns, data-contracts, normalization-catalog) — trigger: knowledge stabilizes enough to encode.

### Future Consideration (v2+) — defer until v1 harness is validated in real use

- [ ] **Single-source multi-runtime emit (opencode → Claude Code)** — HIGH complexity; defer until the opencode surface is stable, else you maintain an emitter for a moving target. (Interim: hand-maintain `.claude/` or develop opencode-only.)
- [ ] **B-model extension points (gRPC/MQ scaffolding)** — defer per §4; A-model must be robust first, job payloads kept isomorphic.
- [ ] **Shadow-run / parallel-operation tooling** — defer per §5.5 (optional even in the domain project).
- [ ] **Configuration-parser harness surface** — explicitly a later component (Out of Scope now).

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| opencode.json + permission matrix | HIGH | MEDIUM | P1 |
| AGENTS.md + core personas | HIGH | MEDIUM | P1 |
| Contract + docs seed | HIGH | LOW–MEDIUM | P1 |
| Normalization comparator + /golden + /golden-approve | HIGH | HIGH | P1 |
| Contract-drift CI gate (schema hash) | HIGH | MEDIUM | P1 |
| Polyglot-boundary linter | HIGH | MEDIUM–HIGH | P1 |
| Hooks: format-on-write / secret / commit gate | HIGH | MEDIUM | P1 |
| Two-plane memory + SessionStart injection + /checkpoint | HIGH | HIGH | P1 |
| Toolchain bootstrap (.NET 10 + uv + CI) | HIGH | MEDIUM | P1 |
| Slash commands (toolchain wrappers) | MEDIUM | LOW | P1 |
| /strangler-step | HIGH | HIGH | P2 |
| /new-normalization-rule | HIGH | MEDIUM | P2 |
| /docs-sync | MEDIUM | MEDIUM–HIGH | P2 |
| /component scaffold | MEDIUM | MEDIUM | P2 |
| /adr | MEDIUM | LOW | P2 |
| Skills (progressive disclosure) + skill-creator | MEDIUM | MEDIUM | P2 |
| golden-runner / polyglot-auditor agents | MEDIUM | MEDIUM | P2 |
| Single-source multi-runtime emit | MEDIUM | HIGH | P3 |
| B-model extension points | LOW | HIGH | P3 |
| Shadow-run tooling | LOW | MEDIUM | P3 |

**Priority key:** P1 = must have for launch · P2 = should have, add after validation · P3 = defer.

---

## Competitor / Prior-Art Feature Analysis

Comparison is against harness patterns, not products (this is a bespoke internal harness).

| Feature | Generic coding-agent harness (e.g. gsd-opencode-style, 750-file) | Memory-bank / cline-style pattern | Our Approach |
|---------|-------------------------------|-----------------------------------|--------------|
| Personas | Generic dev/reviewer roles | N/A | Language-scoped (.NET/Python) + golden-runner + polyglot-auditor, permission-scoped |
| Memory | Single flat context / rules file | Memory-bank markdown files, hand-updated | Two-plane: human-owned constitutional (contracts/adr/golden) + auto-derived volatile (repo-map/contracts-index), non-ignorable injection |
| Docs | Hand-written | N/A | Diátaxis; reference/ DERIVED from contracts via /docs-sync |
| Migration | Ad-hoc refactor commands | N/A | Golden-parity-gated /strangler-step; big-bang explicitly forbidden |
| Polyglot safety | None (single-language assumption) | None | §4-5 checklist as executable linter + normalization-aware golden comparator |
| Approvals | Agent may auto-apply | Agent auto-applies | Human CODEOWNERS sign-off for golden; agents propose only |
| Multi-runtime | Single target | Single target | Single-source → opencode + Claude Code emit (deferred to P3) |

---

## Sources

- `/home/user/lifetimeworkflow/.planning/PROJECT.md` — harness scope, Out of Scope, Key Decisions (HIGH)
- `/workspace/presentationformat/archive/parserimprove/uploads/integration_contracts_design.md` §0, §4.1–4.7, §5 (polyglot Py↔.NET checklist), §6 (contract change → golden update) (HIGH)
- `/workspace/presentationformat/archive/parserimprove/uploads/parser_project_revised.md` §5 (test strategy: golden/equivalence, data-driven normalization), §8 (risks), §9 (staged transition, no big-bang) (HIGH)
- opencode / Claude Code harness primitives (agents, commands, skills, plugins/hooks, permission matrix, AGENTS.md, MCP) — training data, Jan 2026 cutoff (MEDIUM; Context7, WebFetch, Brave, Exa, Firecrawl all unavailable in this environment — verify skill size caps and exact plugin hook-event names against current opencode docs before implementation)

---
*Feature research for: opencode agent harness (polyglot, contract-first, legacy-migration monorepo)*
*Researched: 2026-07-07*
