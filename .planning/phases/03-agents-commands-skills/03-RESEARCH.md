# Phase 3: Agents + Commands + Skills - Research

**Researched:** 2026-07-08
**Domain:** opencode/Claude-Code agent-harness authoring (single-source `harness/` tree) — config + permission matrix, agent personas, slash commands, progressive-disclosure skills, a contract→docs generator
**Confidence:** HIGH for the harness assets to author, the Python resolver/generator, and Claude skill caps; MEDIUM for opencode runtime frontmatter field names (opencode.ai 403s to fetchers — verified via WebSearch snippets + community mirrors, not primary docs). Runtime *behavior* is DEFERRED (D-02) so MEDIUM here is acceptable: structural validation does not require a live runtime.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Author the whole harness surface in a **neutral `harness/` single source**: `harness/agents/*.md`, `harness/commands/*.md`, `harness/skills/*/SKILL.md`, `harness/plugins/*.ts`, `harness/opencode.json` (+ permission matrix). **Phase 6 emitter** produces `.opencode/` and `.claude/` from here. Phase 3 authors source only — no runtime install, no emit.
- **D-02:** opencode/Claude runtime execution is NOT verifiable in this container (opencode absent) → **structural validation** instead: opencode.json JSON-Schema valid, frontmatter valid, skill size-cap checks, permission matrix well-formed. Live runtime loading is DEFERRED. **BUT pure-logic/generators ARE executed and tested** (the permission resolver D-03, the `/docs-sync` generator D-06).
- **D-03:** `harness/opencode.json`: model tiering (explorer cheap / implementer expensive), instructions glob (AGENTS.md + `contracts/**`), formatter (ruff / dotnet format), MCP wiring (config-only). The 15-key permission matrix is separate data, and a **last-wins glob resolver is a Python pure function, unit-tested** (`*:ask` → `dotnet *:allow` · `uv *:allow` · `git push*:ask`; reviewer read-only; secret/constitution writes deny; `*.env` deny). The resolver is reused by Phase-4 hooks.
- **D-04:** 5 personas = markdown + frontmatter (description = routing signal, 3rd-person concrete; model tier; permission scope; tools allowlist): orchestrator(primary), dotnet-engineer(`dotnet *`), python-engineer(`uv *`·`pytest *`), code-reviewer(read-only Read/Grep/Glob — no bash/edit), explorer(cheap model). Frontmatter is **structurally validated** (description non-empty, permission valid, reviewer has no write/bash).
- **D-05:** 9 commands = markdown prompt macros wrapping Phase-1 tools. Sequence: golden-adjacent (`/build`·`/test`·`/lint`·`/golden`·`/golden-approve`·`/adr`·`/checkpoint`·`/component`) FIRST, migration (`/new-normalization-rule`·`/strangler-step`·`/docs-sync`) LATER. `/strangler-step` **refuses without a captured legacy golden baseline** + extracts one path only + requires `/golden` parity (success criterion 4). `/build`'s dotnet part is .NET-gated (script skips/instructs clearly when dotnet absent).
- **D-06:** `/docs-sync` (DOCS-03) is a **runnable Python generator** (memory_regen pattern): `contracts/` → `docs/reference/*.md`, no hand-authoring, delete+regenerate is deterministic — actually executed and tested. `/new-normalization-rule` scaffolds the order-enforcement (contract → (input,expected) data case → code).
- **D-07:** skills = progressive disclosure (frontmatter always-on + body lazy) + size caps (Claude SKILL.md name≤64 / desc≤1024 / body<~500 lines). Structural cap check at author time; the emit-time validator *body* is Phase 6.

### Claude's Discretion
Command/skill/agent prose, `harness/` detailed tree, the exact permission-matrix glob list, `docs/reference` generation format, MCP server choice — all planner/researcher discretion. Fixed: single-source=`harness/` · golden-adjacent-first · reviewer-read-only · docs-sync-derived · runtime-execution-deferred.

### Deferred Ideas (OUT OF SCOPE)
- Single-source → `.opencode/`+`.claude/` actual emit + per-runtime validator body → **Phase 6**.
- Live opencode loading of agents/commands/permissions → after opencode install.
- Command dotnet-path execution → after .NET policy opens.
- No scope creep.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONFIG-01 | `opencode.json` — model tiering / instructions glob / formatter / MCP | §opencode.json Schema (top-level keys, model+small_model tiering, `instructions` array, `formatter`, `mcp`) |
| CONFIG-02 | 15-key permission matrix — bash glob last-wins, reviewer read-only, secret/constitution deny | §Permission Matrix (15 keys pinned), §Pattern 2 (Python last-wins resolver), §Code Examples (resolver) |
| AGENT-01 | orchestrator (primary) — decompose/delegate | §Agent Format (opencode `mode: primary`; Claude no-mode), §Persona Table |
| AGENT-02 | dotnet-engineer — `dotnet *` scope | §Persona Table (permission `bash: {dotnet *: allow}`) |
| AGENT-03 | python-engineer — `uv *`·`pytest *` scope | §Persona Table |
| AGENT-04 | code-reviewer — read-only (Read/Grep/Glob), no write/bash | §Persona Table (opencode `permission {edit:deny,bash:deny}`; Claude `tools: Read, Grep, Glob`), §Pitfall P-perm |
| AGENT-05 | explorer — cheap model code exploration, returns paths | §Persona Table (`model` = small tier) |
| CMD-01 | `/build`·`/test`·`/lint` — wrap .NET/Python canonical calls | §Command Format, §Command→Tool Map |
| CMD-02 | `/golden` — run + normalized diff | §Command→Tool Map (`python -m tools.golden_runner.runner`) |
| CMD-03 | `/golden-approve` — CODEOWNERS human sign-off only | §Command→Tool Map (`tools.golden_runner.approve`, refusal already coded) |
| CMD-04 | `/checkpoint` — volatile-plane update + commit | §Command→Tool Map (`.memory/state/`, `memory_regen`) |
| CMD-05 | `/new-normalization-rule` — contract→data-case→code order | §Pattern 4 (scaffold order enforcement) |
| CMD-06 | `/strangler-step` — one path, `/golden` parity gate, refuse w/o baseline | §Pattern 5, §Pitfall P10 mapping |
| CMD-07 | `/adr` — append-only MADR scaffold | §Command→Tool Map (docs/adr/ MADR template) |
| CMD-08 | `/docs-sync` — regenerate `reference/` from contracts | §Pattern 3 (generator), §/docs-sync Generator |
| CMD-09 | `/component` — scaffold component w/ structure + AGENTS.md + tests | §Command→Tool Map, §Pattern 4 |
| SKILL-01 | core skills (dotnet-conventions·python-conventions·golden-testing·data-contracts) — progressive disclosure, caps | §Skill Format + Caps |
| SKILL-02 | skill-creator (meta) + domain skills (normalization-catalog·pipeline-patterns) | §Skill Format + Caps |
| DOCS-03 | `reference/` derived from contracts (humans write only tutorials/how-to/explanation) | §/docs-sync Generator |
</phase_requirements>

## Summary

Phase 3 is a **content-authoring phase with two runnable pure-Python deliverables** bolted on: it produces the full harness surface (1 config + 1 permission-matrix dataset, 5 agent personas, 9 commands, 7 skills) as markdown/JSON in `harness/`, plus (a) a **last-wins permission resolver** and (b) a **`/docs-sync` contract→reference generator** that are genuinely executed and pytest-covered. Everything else is validated *structurally* (JSON-Schema-valid config, valid frontmatter, skill caps) because no opencode runtime exists in the container (D-02). This split — "author-only for the markdown, execute-and-test for the logic" — is the phase's defining shape and it already has a precedent: `harness/plugins/session-inject.ts` (Phase 2) is authored-but-deferred while its underlying `tools/memory_regen/inject.py` is fully tested.

The single most important current-fact correction from this session: **the Claude SKILL.md `description` cap is 1024 characters, not 200.** The PITFALLS.md "≤200 chars" claim is wrong; the official platform.claude.com spec is name ≤64, description ≤1024 (both hard limits, non-empty required), body <~500 lines (a recommendation, not a hard cap). opencode uses the *identical* caps (name 1–64, description 1–1024). Because both runtimes share the same numbers, the author-time cap check is a single rule set — no per-runtime divergence on skill size. The second correction: opencode's agent `tools:` field is **deprecated in favor of `permission:`** — for opencode express least-privilege via the permission block; Claude Code still uses a `tools:` allowlist. That is a real per-runtime mapping the Phase-6 emitter must carry, and Phase 3 must author *both* representations (or author neutrally and let the emitter derive them).

**Primary recommendation:** Author `harness/` as the neutral source with `harness/opencode.json` + a separate `harness/permission-matrix.json` dataset; implement the resolver as `tools/harness_perms/resolver.py` (pure, unit-tested, reused by Phase 4) and `/docs-sync` as `tools/docs_sync/` (stdlib-`json` over `contracts/**/*.schema.json`, zero new deps, syrupy-snapshot determinism mirroring `contracts_index.py`). Validate all markdown structurally with a `tools/harness_lint/` pytest suite. Sequence golden-adjacent commands before migration commands, and make `/strangler-step`'s baseline-refusal and `/docs-sync`'s determinism the two hardest success gates.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| opencode.json config (model/instructions/formatter/mcp) | Harness config (data) | — | Declarative runtime config; consumed by opencode at load, validated structurally here |
| 15-key permission matrix | Harness config (data) | Python resolver (logic) | Matrix is data in `harness/`; the *resolution* is pure Python logic tested now and reused by Phase-4 hooks |
| Permission last-wins resolution | Python pure function (`tools/`) | Phase-4 hooks (consumer) | Deterministic, unit-testable without a runtime; hooks call it later |
| Agent personas | Harness source markdown | Phase-6 emitter (transpile) | Frontmatter+prose; behavior deferred, structure validated |
| Slash commands | Harness source markdown | Phase-1 tools (wrapped) | Commands are thin prompt macros invoking existing `tools/*` CLIs |
| Skills | Harness source markdown+dirs | Phase-6 emitter | Progressive disclosure; caps enforced at author-time structurally |
| `/docs-sync` reference generation | Python generator (`tools/`) | contracts/ (input), docs/reference/ (output) | Pure derivation from contract schemas; executed + determinism-tested |
| Structural validation of the surface | Python pytest (`tools/`) | — | The only "runtime" available in-container; asserts JSON-Schema/frontmatter/caps |
| Session injection plugin | Harness source TS (authored-deferred) | tools/memory_regen (tested logic) | Already exists from Phase 2; Phase 3 only wires it into opencode.json |

## Standard Stack

No new external packages are required. Phase 3 authors markdown/JSON and writes pure-Python tools using **already-pinned** deps.

### Core (already present — reuse, do not add)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `json` | 3.11 | Read `contracts/**/*.schema.json` for `/docs-sync`; parse `harness/opencode.json` + `permission-matrix.json` for validation | `contract_hash/hash.py` already reads schemas via `json.loads` — same path, zero new dep |
| Python stdlib `fnmatch` | 3.11 | Glob matching for the last-wins permission resolver | Matches opencode's `*`/`?` wildcard semantics for bash patterns; stdlib, deterministic |
| `jsonschema` | 4.26.0 | Validate `harness/opencode.json` against a fetched/vendored `opencode.json` schema (structural, D-02) | Already a direct dependency (`pyproject.toml`); Draft 2020-12 |
| `pytest` | >=8.4,<9 | The in-container "runtime": structural + logic tests | Established test framework (RULES) |
| `syrupy` | 5.2.0 | Determinism snapshot for `/docs-sync` output (gitignore-safe proof, exactly as `contracts_index` does) | Already used for derived-plane determinism proofs |
| `ruff` | ~=0.15 | Lint/format the new Python tools | Established |
| `check-jsonschema` | 0.37.4 | Optional CLI structural check of `opencode.json` in addition to the pytest assert | Already present; wraps jsonschema |

### Supporting (harness-native formats — not libraries, but the "stack" being authored)
| Format | Location | Purpose | Notes |
|--------|----------|---------|-------|
| opencode.json | `harness/opencode.json` | Runtime config | `$schema: https://opencode.ai/config.json` |
| Agent markdown | `harness/agents/<name>.md` | Persona frontmatter+prompt | Neutral source; emitter maps to `.opencode/agent/` + `.claude/agents/` |
| Command markdown | `harness/commands/<name>.md` | Slash-command prompt macro | Maps to `.opencode/command/` + `.claude/commands/` |
| SKILL.md | `harness/skills/<name>/SKILL.md` | Progressive-disclosure skill | Maps to `.opencode/skill/` + `.claude/skills/` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `json` over `.schema.json` for `/docs-sync` | Read companion `.yaml` specs (spec.yaml/catalog.yaml) for human descriptions | YAML adds a dep decision (`ruamel.yaml` is transitively present via check-jsonschema; `pyyaml` would be a new direct dep). **Recommend schema-JSON-only** to keep zero-new-deps; if prose descriptions from YAML are wanted, reuse the already-locked `ruamel.yaml` rather than adding pyyaml. `[ASSUMED]` that schemas carry enough (title/description/enum) to generate useful reference — verify against actual `contracts/**/*.schema.json` at plan time. |
| stdlib `fnmatch` for glob | Port opencode's exact matcher | opencode's bash matching is `*`/`?` wildcard over the full command line — `fnmatch.fnmatchcase` matches that. `[ASSUMED]` opencode does not use extended-glob/regex for bash patterns — MEDIUM, verify if resolver parity with the live runtime is ever required (deferred). |
| Vendoring the opencode JSON schema | Fetch `https://opencode.ai/config.json` at test time | Fetching couples the structural test to network + a moving schema. **Recommend vendoring** a pinned copy under `harness/` (or asserting a hand-authored subset schema) so the structural gate is hermetic and deterministic. |

**Installation:** none. `uv sync` already resolves everything.

## Package Legitimacy Audit

Phase 3 installs **no external packages**. All tools are stdlib + already-locked deps (jsonschema 4.26.0, pytest, syrupy, ruff — audited in Phase 1). slopcheck N/A (no new registry installs).

| Package | Registry | Disposition |
|---------|----------|-------------|
| (none — zero new installs) | — | N/A |

**Packages removed due to slopcheck [SLOP]:** none
**Packages flagged [SUS]:** none

## opencode.json Schema (CONFIG-01)

**`$schema`:** `https://opencode.ai/config.json` `[CITED: opencode.ai/docs/config]` (schema URL confirmed via WebSearch snippet of official docs).

**Top-level keys** (the ones relevant to CONFIG-01; opencode ignores unknown keys but the schema validates known ones):

| Key | Shape | Phase-3 use | Confidence |
|-----|-------|-------------|-----------|
| `$schema` | string (URL) | pin to `https://opencode.ai/config.json` | HIGH |
| `model` | string `"provider/model-id"` | the expensive **implementer** default tier | MEDIUM |
| `small_model` | string `"provider/model-id"` | the cheap **explorer/summarization** tier (model tiering, D-03) | MEDIUM `[ASSUMED]` exact key name `small_model` — verify at Phase 6 wiring |
| `provider` | object (provider→config, models, apiKey/env) | provider wiring (config-only) | MEDIUM |
| `agent` | object (name→{mode,model,prompt,tools,permission,temperature}) | per-agent overrides; personas may also live as separate markdown files | MEDIUM |
| `command` | object (name→{template,description,agent,model,subtask}) | commands may live here or as markdown files | MEDIUM |
| `permission` | object — the 15-key matrix (see below) | project-wide default permission block | HIGH (15 keys pinned) |
| `instructions` | array of glob strings | `["AGENTS.md", "**/AGENTS.md", "contracts/**"]` — but **inject pointers, not payloads** (P2: a broad `contracts/**` glob pulls everything; scope narrowly) | HIGH |
| `formatter` | object (name→{command, extensions/globs, environment}) | `ruff format` for `*.py`, `dotnet format` for `*.cs` | MEDIUM |
| `mcp` | object (name→{type:"local"/"remote", command/url, enabled}) | MCP wiring, config-only (D-03) | MEDIUM |

**Structural validation approach (D-02):** vendor a pinned `opencode.config.schema.json` (or a hand-authored subset asserting the keys above + the permission shape) under `harness/`, then a pytest asserts `jsonschema.validate(load("harness/opencode.json"), schema)`. Do **not** fetch the live schema at test time (network + drift). This satisfies success criterion 1's "opencode.json defines model tiering, instructions glob, formatter, MCP wiring" without a runtime.

## Permission Matrix — 15 Keys + Last-Wins (CONFIG-02)

**The 15 keys** `[VERIFIED: WebSearch of official opencode docs + wesammustafa mirror, cross-confirmed]`:

```
read, edit, bash, glob, grep, list, task,
external_directory, todowrite, question,
webfetch, websearch, lsp, skill, doom_loop
```

Each key takes `"allow" | "ask" | "deny"`. `bash` additionally accepts an **object** of glob→decision sub-rules.

**Last-wins glob ordering** `[CITED: opencode.ai/docs/permissions]`: for `bash`, rules match against the full command line with `*` (multi-char) and `?` (single-char) wildcards; **the last matching rule wins.** Idiom: put the catch-all `*` FIRST, then increasingly specific overrides. Ending the matrix with a broad `allow` overrides every prior `deny` (Pitfall P3).

```json
"bash": {
  "*": "ask",
  "dotnet *": "allow",
  "uv *": "allow",
  "pytest *": "allow",
  "git push*": "ask",
  "rm -rf*": "deny"
}
```

**Defaults confirmed:** `external_directory` defaults to `"ask"` (file access outside project root). `[CITED: wesammustafa mirror]`

**Constitution / secret denies (D-03, P3):** the matrix must deny agent writes to the constitution plane and secrets. opencode's `edit`/`bash` don't natively glob file *paths* the way bash globs commands — so path-scoped denies (`contracts/**`, `docs/adr/**`, `golden/**`, `*.env`) are enforced in Phase 4 by the **contract-guard hook calling the resolver**, not solely by opencode's native `edit` key. In `harness/`, encode these path rules as data in `permission-matrix.json`; the Python resolver evaluates them; opencode.json carries the coarse `edit: "deny"`/`"ask"` default. `[ASSUMED]` opencode's native `edit` key is not path-globbable — MEDIUM; the resolver is the portable enforcement regardless, which is why D-03 mandates it.

**The Python resolver (D-03, executed + tested):** a pure function `resolve(matrix, kind, subject) -> "allow"|"ask"|"deny"` where `kind ∈ {bash, edit, ...}` and `subject` is a command line or a file path. Last-wins semantics: iterate rules in author order, keep the decision of the **last** pattern that matches (`fnmatch.fnmatchcase`). Reused verbatim by Phase-4 hooks. Unit tests assert: `dotnet test`→allow, `git push --force`→ask/deny, edit `golden/x`→deny, edit `x.env`→deny, unknown command→ask (default-deny posture). This directly satisfies success criterion 1.

## Agent Format (AGENT-01..05)

**opencode** `.opencode/agent/<name>.md` (or inline under `opencode.json.agent`) `[CITED: opencode.ai/docs/agents]`:

| Frontmatter field | Values | Notes |
|-------------------|--------|-------|
| `description` | string | **Routing signal** (P7): "Use when… + what it does", 3rd-person, concrete triggers |
| `mode` | `primary` \| `subagent` \| `all` | default `all`; orchestrator = `primary`, others = `subagent` |
| `model` | `"provider/model-id"` | omit → primary uses global `model`, subagent inherits caller's model; explorer sets the cheap tier explicitly |
| `temperature` | number | lower = deterministic |
| `permission` | object (subset of the 15 keys) | **preferred** least-privilege mechanism |
| `tools` | object/list | **DEPRECATED in opencode** in favor of `permission` — still parsed but prefer `permission` |

**Claude Code** `.claude/agents/<name>.md` (verified from repo's own GSD agents): frontmatter `name`, `description`, `tools:` (comma-list allowlist e.g. `Read, Grep, Glob`), optional `color`. **No `mode` field** — Claude agents are subagents invoked by description; there is no `primary` concept in the same shape. **`tools:` is the live allowlist in Claude** (opposite of opencode where it's deprecated).

**Per-runtime mapping the Phase-6 emitter carries (author both intents now, D-01/D-04):**

| Persona | opencode | Claude |
|---------|----------|--------|
| orchestrator (AGENT-01) | `mode: primary`, broad permission | agent w/ delegation tools |
| dotnet-engineer (AGENT-02) | `permission.bash: {"*":"ask","dotnet *":"allow"}` | `tools: Read, Edit, Bash, Grep, Glob` (rely on hooks for scope) |
| python-engineer (AGENT-03) | `permission.bash: {"*":"ask","uv *":"allow","pytest *":"allow"}` | same |
| **code-reviewer (AGENT-04)** | `permission: {edit:"deny", bash:"deny", write:"deny"}` | `tools: Read, Grep, Glob` (NO Write/Bash/Edit) |
| explorer (AGENT-05) | `model:` = cheap tier, `permission: {edit:"deny"}` | `tools: Read, Grep, Glob` + cheap model |

**Structural validation (D-04):** pytest parses each agent's YAML frontmatter and asserts: `description` non-empty; `mode` ∈ {primary,subagent,all} when present; permission keys ⊆ the 15; **code-reviewer has no edit/bash/write allow in either representation** (the read-only invariant, P-perm). Recommend a shared frontmatter parser in `tools/harness_lint/`.

## Command Format (CMD-01..09)

**opencode** `.opencode/command/<name>.md` `[CITED: opencode.ai/docs/commands]` (note: singular `command/`; some community docs write `commands/` — pin `command/` for opencode, `commands/` for Claude):

| Frontmatter | Body placeholders |
|-------------|-------------------|
| `description` (string), `agent` (which agent runs it), `model` (optional), `subtask` (bool — force a subagent so command doesn't pollute primary context) | `$ARGUMENTS` (everything after the command name); `$1`,`$2`… (positional); `` !`shell cmd` `` (shell interpolation — output injected); `@filename` (file inclusion) |

**Claude Code** `.claude/commands/<name>.md` (verified from repo GSD commands): markdown prompt, frontmatter is lighter; Claude uses `$ARGUMENTS` and `!` bash execution / `@` file refs similarly but the exact frontmatter keys differ. Author neutral source; emitter maps.

**Command → Phase-1 tool map** (commands are thin macros over already-tested CLIs):

| Command | Wraps | Entry |
|---------|-------|-------|
| `/build` | .NET build (gated) + Python noop | `dotnet build` guarded by `resolve_dotnet()` presence; skip+instruct when absent (D-05) |
| `/test` | full test suite | `uv run pytest` (+ `dotnet test` gated) |
| `/lint` | lint/format | `ruff check` + `ruff format --check` (+ `dotnet format`) |
| `/golden` | golden equivalence + normalized diff | `python -m tools.golden_runner.runner <case>` |
| `/golden-approve` | human-gated promotion | `python -m tools.golden_runner.approve --approve --adr <id>` (refusal already coded, exit 3) |
| `/adr` | append-only MADR scaffold | write `docs/adr/NNNN-*.md` (next number; never edit existing) |
| `/checkpoint` | volatile-plane update + commit | write `.memory/state/{activeContext,progress}.md`; `git commit` (ephemeral-container persistence) |
| `/component` | scaffold component + AGENTS.md + tests | new `components/<n>/` or `libs/*` tree w/ self-sufficient per-package AGENTS.md (P11) |
| `/new-normalization-rule` | order enforcement | scaffold: contract entry → `(input,expected)` data case → code stub (fails until filled) |
| `/strangler-step` | one-path extraction, parity-gated | **refuse without captured legacy baseline**; require `/golden` parity (D-05, P10) |
| `/docs-sync` | contracts → `docs/reference/` | `python -m tools.docs_sync` (runnable generator, D-06) |

## `/docs-sync` Generator (DOCS-03, D-06)

**Pattern:** clone `tools/memory_regen/contracts_index.py` structure exactly — `rows()` → `render()` → `write()` → `main()`, DERIVED header, no timestamps/floats, delete+regenerate byte-identical, determinism proven by a committed **syrupy snapshot** (NOT git diff — `docs/reference/` may be committed, but the snapshot is the canonical determinism proof and works regardless).

**Input → output:** read `contracts/**/*.schema.json` via stdlib `json` (zero new deps — same read path as `contract_hash`). For each schema, emit `docs/reference/<name>.md` with: title (`title`/`$id`), description, the property/column table (name, type, required, enum/const, description), and the §4-5 format-conventions block from `format-conventions.schema.json`. **Only `reference/` is generated**; `tutorials/`, `how-to/`, `explanation/` stay human-authored (anti-feature: hand-written reference).

**Generatable vs hand-authored:**
- Generatable (from schema): column/field tables, types, required-ness, enum/const values, format conventions (BOM/LF/decimal/TZ/null), hash provenance.
- Hand-authored (stays in tutorials/how-to/explanation): *why*, workflows, narrative, migration guides.

**Determinism guards (P12):** sort keys; no `datetime.now()`; DERIVED "do not hand-edit — generated from contracts/ by tools.docs_sync" header; a pytest that runs the generator twice and asserts identical bytes + matches the syrupy snapshot. `[ASSUMED]` the seed schemas carry enough `description`/`title` to produce useful reference text — verify against `contracts/log-specs/standard-log.schema.json` et al. at plan time; if thin, generate structure-only tables (still valid, just terse).

## Skill Format + Caps (SKILL-01/02, D-07)

**opencode** `.opencode/skill/<name>/SKILL.md` `[CITED: opencode.ai/docs/skills + agensi.io format ref]`: frontmatter required `name` (1–64, lowercase alnum + single hyphens, matches dir name), `description` (1–1024, tells agent *when* to activate); optional `license`, `compatibility`, `metadata` (string→string). Optional subdirs `scripts/`, `references/`, `assets/`. Unknown fields ignored.

**Claude Code** `.claude/skills/<name>/SKILL.md` `[VERIFIED: platform.claude.com/docs/agent-skills]`: `name` ≤64 (lowercase, hyphens, no "anthropic"/"claude", no XML tags), `description` non-empty ≤**1024** (no XML tags, must state what + when), body <~500 lines recommended (progressive disclosure — startup loads only name+description).

**Discrepancy RESOLVED:** the "≤200 chars" in PITFALLS.md P5/P6 is **WRONG**. Authoritative caps are **name ≤64, description ≤1024** for BOTH runtimes (identical numbers). Body <~500 lines is a *recommendation* on the Claude side, not a hard reject. Author-time cap check is therefore a single shared rule.

**The 7 skills (D-07):** core = `dotnet-conventions`, `python-conventions`, `golden-testing`, `data-contracts`; meta = `skill-creator`; domain = `normalization-catalog`, `pipeline-patterns` (carryover + scenarios). Keep the set small and descriptions **disjoint** (P7/P8 anti-sprawl): each description is verb-first "Use when… + does…" with non-overlapping triggers.

**Structural cap validation (D-07):** pytest parses each `SKILL.md`: name ≤64 & regex `^[a-z0-9]+(-[a-z0-9]+)*$` & matches dir name; description non-empty ≤1024; body line count warns >500; no XML tags in name/description; description contains a "when"/"use" trigger token (routing guard, P7).

## Neutral Single-Source Layout (`harness/`)

```
harness/
├── opencode.json                 # CONFIG-01: model/small_model, instructions[], formatter, mcp, permission(default)
├── opencode.config.schema.json   # vendored/pinned subset schema for the structural test (hermetic)
├── permission-matrix.json        # CONFIG-02: the 15-key matrix + path-scoped deny rules (data the resolver reads)
├── agents/                       # AGENT-01..05  (neutral frontmatter → emitter maps to opencode+claude)
│   ├── orchestrator.md
│   ├── dotnet-engineer.md
│   ├── python-engineer.md
│   ├── code-reviewer.md
│   └── explorer.md
├── commands/                     # CMD-01..09  (golden-adjacent first, migration later)
│   ├── build.md test.md lint.md golden.md golden-approve.md adr.md checkpoint.md component.md
│   └── new-normalization-rule.md strangler-step.md docs-sync.md
├── skills/                       # SKILL-01/02  (each dir: SKILL.md + optional references/ scripts/ assets/)
│   ├── dotnet-conventions/SKILL.md
│   ├── python-conventions/SKILL.md
│   ├── golden-testing/SKILL.md
│   ├── data-contracts/SKILL.md
│   ├── skill-creator/SKILL.md
│   ├── normalization-catalog/SKILL.md
│   └── pipeline-patterns/SKILL.md
└── plugins/
    └── session-inject.ts         # EXISTS (Phase 2) — Phase 3 only WIRES it into opencode.json.plugin

tools/
├── harness_perms/                # D-03: last-wins resolver (pure, tested, reused by Phase 4)
│   ├── resolver.py  __init__.py  tests/test_resolver.py
├── docs_sync/                    # D-06: contracts → docs/reference generator (runnable, tested)
│   ├── __init__.py  generate.py  tests/test_docs_sync_determinism.py
└── harness_lint/                 # D-02/D-04/D-07: structural validators
    ├── frontmatter.py  __init__.py
    └── tests/ test_opencode_json.py test_agents.py test_commands.py test_skills.py
```

- `opencode.json` + `permission-matrix.json` live at `harness/` root (config-as-data).
- The Phase-2 `harness/plugins/session-inject.ts` stays put; Phase 3 adds its registration to `opencode.json` (the plugin's own RESUME NOTE flags this as the Phase-3 wiring point — re-verify `chat.system.transform` vs `experimental.chat.system.transform` and `event` session.created hook names then, MEDIUM confidence).
- `tools/*` are uv workspace members (matches `members = ["libs/python", "tools/*"]`) — each new tool dir needs a `pyproject.toml` or uv sync fails (documented in root pyproject).

## Architecture Patterns

### System Architecture Diagram

```
                    ┌──────────────── harness/ (neutral single source) ────────────────┐
 author (human/     │  opencode.json ─┐                                                 │
 agent, this phase) │  permission-    │   agents/*.md    commands/*.md   skills/*/SKILL │
        │           │  matrix.json    │        │              │              │          │
        ▼           │       │         │        │              │              │          │
   ┌─────────┐      └───────┼─────────┼────────┼──────────────┼──────────────┼──────────┘
   │ EXECUTED │             │         │        │              │              │
   │ + TESTED │      ┌──────▼──────┐  │   ┌─────▼──────────────▼──────────────▼─────┐
   │ (D-03,   │      │harness_perms│  │   │      harness_lint (pytest)              │  STRUCTURAL
   │  D-06)   │      │  resolver   │  │   │ jsonschema-valid · frontmatter · caps   │  VALIDATION
   └────┬─────┘      │ (last-wins) │  │   └─────────────────────────────────────────┘  (D-02)
        │            └──────┬──────┘  │              (no opencode runtime here)
        │        reused by  │         │
        │        Phase-4 ───┘         │
        ▼                             ▼
   ┌─────────────┐        ┌────────────────────────────┐
   │ docs_sync   │ reads  │ contracts/**/*.schema.json │  (constitution plane, input only)
   │ generate.py │───────▶│                            │
   └──────┬──────┘        └────────────────────────────┘
          │ writes (DERIVED, deterministic)
          ▼
   docs/reference/*.md ──── syrupy snapshot proves delete+regenerate == byte-identical

   commands/*.md ──invoke──▶ tools/{golden_runner,contract_drift,memory_regen,...}  (Phase-1 CLIs)

   [DEFERRED → Phase 6]  harness/ ──emit──▶ .opencode/{agent,command,skill} + .claude/{agents,commands,skills}
```

### Pattern 1: Author-neutral, emit-later (D-01)
**What:** every surface file is written once in `harness/` in a form the Phase-6 emitter can transpile to both runtimes. **When:** all agents/commands/skills. **How:** where opencode and Claude diverge (agent `tools:` vs `permission:`; command dir name), author the *intent* and document the mapping in a comment/metadata block so the emitter is a pure function. Do NOT hand-author `.opencode/` or `.claude/` in this phase.

### Pattern 2: Pure resolver, data matrix (D-03)
**What:** matrix is JSON data; resolution is a stdlib-only pure function. **When:** CONFIG-02. **Why:** testable now without a runtime, reused unchanged by Phase-4 hooks — one implementation, no drift (mirrors how `contracts_index` reuses `contract_hash`/`contract_drift` rather than re-implementing).

### Pattern 3: Derived generator = memory_regen clone (D-06)
**What:** `/docs-sync` copies the `contracts_index.py` shape (rows→render→write→main, DERIVED header, determinism-by-construction, syrupy proof). **Why:** proven pattern in-repo; guarantees the "delete+regenerate identical" success criterion and the "no hand-written reference" anti-feature.

### Pattern 4: Order-enforcing scaffolds (D-05/D-06)
**What:** `/new-normalization-rule` and `/component` scaffold in the *mandated order* (contract → data-case → code; component structure+AGENTS.md+tests together) and leave failing stubs so the order can't be skipped silently.

### Pattern 5: Refuse-without-baseline gate (D-05)
**What:** `/strangler-step` checks for a captured legacy golden baseline for the target path and **exits non-zero** if absent — the same "machines gate" shape as `approve.py`'s `GoldenApprovalRefused`. Extracts one path only; requires `/golden` parity green.

### Anti-Patterns to Avoid
- **Broad `allow` at the bottom of the bash matrix** — last-wins makes it override every deny (P3). End with specifics, never `*`.
- **Description-as-label** — noun-phrase descriptions break routing (P7). Always "Use when…".
- **Hand-authoring `.opencode/`/`.claude/`** in this phase — that's Phase-6 emit; hand-editing = drift (P5).
- **Inlining full contract bodies into agents/instructions** — context bloat (P2); inject pointers.
- **`/docs-sync` writing outside `reference/`** — only `reference/` is derived (P12 / anti-feature).
- **Skill sprawl** — 7 skills, disjoint descriptions; skill-creator must demand "why not an existing skill?" (P8).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Golden run + normalized diff | A new comparator in the command | `tools.golden_runner.runner` | Already shares the §4-5 core; a second impl drifts (P4) |
| Golden promotion gate | Command-level approval logic | `tools.golden_runner.approve` (refusal coded, exit 3) | Human-gate already tested |
| Contract hash/drift for `/docs-sync` provenance | Re-hash schemas in docs_sync | `tools.contract_hash` / `tools.contract_drift` | Second hash impl can disagree w/ the gate (P14) |
| Deterministic derived-file render | Ad-hoc string building | Clone `contracts_index.py` render/determinism discipline | Proven byte-identical + syrupy pattern |
| opencode.json validity | Regex/manual key checks | `jsonschema.validate` against a vendored schema | Draft 2020-12 validator already a dep |
| YAML frontmatter parsing | String slicing | One shared `harness_lint/frontmatter.py` (stdlib or ruamel already locked) | Consistent across agent/command/skill validators |

**Key insight:** Phase 3 wraps and validates — it should reuse every Phase-1/2 tool and clone their determinism discipline, authoring almost no new *logic* beyond the resolver and the docs generator.

## Common Pitfalls

### Pitfall P3: Over-broad bash permission (last-wins misordered)
**Goes wrong:** a trailing `"*":"allow"` (or an appended unblock rule) overrides earlier denies → destructive commands / constitution edits slip through. **Avoid:** `*` FIRST = `ask`; specifics after; never end with broad allow. **Warning sign:** matrix ends with a catch-all allow, or no resolver test feeds sample commands. **Verify:** resolver unit test asserts `git push --force`→ask/deny, edit `golden/*`/`*.env`→deny.

### Pitfall P7: Description-as-label → bad routing
**Goes wrong:** `description: "Python agent"` gives the orchestrator no invocation signal. **Avoid:** verb-first "Use when… + does…" with concrete triggers (contract change, golden red, migration step). **Verify:** harness_lint asserts each agent/skill/command description contains a trigger token and is non-empty; keep descriptions disjoint.

### Pitfall P5/P6: Runtime caps (skill size) — and the 200-vs-1024 trap
**Goes wrong:** authoring to a wrong cap. **Fixed fact:** name ≤64, description ≤1024 (both runtimes, hard); body <~500 lines (recommendation). The old "≤200" is wrong. **Verify:** harness_lint enforces the real numbers; warn (not fail) on body >500.

### Pitfall P12: Derived-doc rot (`/docs-sync`)
**Goes wrong:** someone hand-edits `docs/reference/`. **Avoid:** DERIVED "do not hand-edit" header + determinism test + (Phase-5) CI re-emit diff. **Verify:** run generator twice → identical bytes; matches syrupy snapshot.

### Pitfall P-perm: Reviewer not actually read-only (AGENT-04)
**Goes wrong:** code-reviewer authored with edit/bash access in one runtime representation. **Avoid:** opencode `permission: {edit:deny,bash:deny,write:deny}` AND Claude `tools: Read, Grep, Glob` (no Write/Bash/Edit). **Verify:** harness_lint asserts the reviewer has zero write/bash affordance in *both* representations.

### Pitfall P10: `/strangler-step` without a captured baseline
**Goes wrong:** migration with no equivalence reference → silent regression. **Avoid:** command refuses (non-zero) when no legacy golden baseline exists for the path. **Verify:** a test invoking the scaffold logic with no baseline asserts refusal.

### Pitfall P1: Over-authoring surface before it's validated
**Goes wrong:** all 21 artifacts written, none proven. **Avoid:** the two *runnable* deliverables (resolver, docs_sync) carry real tests; structural lint covers the rest. Don't add skills/commands beyond the enumerated 7/9.

## Code Examples

### Last-wins bash resolver (D-03)
```python
# tools/harness_perms/resolver.py  — pure, stdlib-only, reused by Phase-4 hooks
from fnmatch import fnmatchcase

Decision = str  # "allow" | "ask" | "deny"

def resolve_bash(rules: dict[str, Decision], command: str, default: Decision = "ask") -> Decision:
    """Last matching glob wins (opencode semantics). `rules` is authored order-preserving
    (Python 3.7+ dict preserves insertion order); put '*' first, specifics after."""
    decision = default
    for pattern, verb in rules.items():
        if fnmatchcase(command, pattern):
            decision = verb          # LAST match wins — do not break
    return decision

def resolve_path(deny_globs: list[str], path: str) -> Decision:
    """Path-scoped deny for constitution/secret writes (contracts/**, golden/**, *.env)."""
    return "deny" if any(fnmatchcase(path, g) for g in deny_globs) else "allow"
```

### opencode.json skeleton (CONFIG-01/02)
```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "PROVIDER/IMPLEMENTER-TIER",       // expensive tier
  "small_model": "PROVIDER/EXPLORER-TIER",    // cheap tier (verify key name at Phase 6)
  "instructions": ["AGENTS.md", "**/AGENTS.md"],   // pointers, NOT contracts/** payloads (P2)
  "formatter": {
    "ruff":   { "command": ["ruff", "format", "$FILE"], "extensions": [".py"] },
    "dotnet": { "command": ["dotnet", "format"],        "extensions": [".cs"] }
  },
  "permission": {
    "edit": "ask",
    "bash": { "*": "ask", "dotnet *": "allow", "uv *": "allow",
              "pytest *": "allow", "git push*": "ask", "rm -rf*": "deny" },
    "webfetch": "ask", "external_directory": "ask"
  },
  "mcp": {}                                     // config-only wiring (D-03)
}
```

### `/docs-sync` generator shape (D-06) — clone of contracts_index.py
```python
# tools/docs_sync/generate.py
import json
from pathlib import Path
DERIVED = "DERIVED — do not hand-edit (tools/docs_sync/generate.py) — regenerate from contracts/"
def rows(schema: dict) -> list[tuple]:            # deterministic: sort props, no timestamps/floats
    props = schema.get("properties", {})
    req = set(schema.get("required", []))
    return [(n, p.get("type","?"), n in req, p.get("description","")) for n, p in sorted(props.items())]
def render(name: str, schema: dict) -> str: ...    # header=DERIVED, stable md table
def write(contracts="contracts", out="docs/reference") -> list[Path]: ...  # one .md per *.schema.json
# main(): regenerate all; a pytest runs write() twice → byte-identical + syrupy snapshot
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| opencode agent `tools:` allowlist | `permission:` block (per-tool allow/ask/deny) | opencode 2025-2026 | Phase 3 authors permission for opencode; `tools:` stays the Claude mechanism — emitter maps both |
| "Claude skill description ≤200 chars" (repo PITFALLS) | **≤1024 chars** (official) | corrected this session | Author to 1024; the 200 claim is retired |
| Broad global agent permissions | Least-privilege per-agent `permission` overrides (3 levels: project→agent-config→frontmatter) | opencode current | Reviewer/explorer scoped by permission, not convention |

**Deprecated/outdated:**
- opencode agent `tools:` field — deprecated in favor of `permission:` (still parsed).
- PITFALLS.md P5/P6 "≤200 char description" — factually wrong; use 1024.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `small_model` is the exact opencode key for the cheap tier | opencode.json Schema | Config key rename needed at Phase 6 wiring; structural test would pin whatever schema says |
| A2 | opencode native `edit` key is not file-path-globbable (path denies enforced via resolver/hook) | Permission Matrix | If it IS path-globbable, some denies can live in opencode.json too — resolver still correct, just belt-and-suspenders |
| A3 | opencode bash glob matching == `fnmatch` (`*`/`?`), not regex/extglob | Alternatives / resolver | Resolver could mis-predict live runtime edge cases (deferred; parity not required in Phase 3) |
| A4 | Seed `*.schema.json` carry enough title/description/enum to generate useful reference text | /docs-sync Generator | If thin, generate structure-only tables (still valid, terser) |
| A5 | opencode command dir is singular `command/` (skill `skill/`, agent `agent/`) | Command/Skill Format | Emitter path wrong; trivially fixed at Phase 6; community docs disagree (singular vs plural) |
| A6 | `chat.system.transform` (not `experimental.` prefixed) is the opencode injection hook | Layout / plugin wiring | Phase-2 stub already flags this MEDIUM; re-verify before wiring plugin into opencode.json |
| A7 | Claude agents have no `mode` field equivalent to opencode `primary` | Agent Format | Orchestrator "primary" maps to a Claude convention, not a field; emitter handles |

## Open Questions

1. **Vendored schema vs subset assertion for opencode.json structural test.**
   - Know: fetching the live schema is non-hermetic. Recommend vendoring a pinned copy or hand-authoring a subset schema asserting the CONFIG-01/02 keys.
   - Unclear: whether the full official schema is small/stable enough to vendor wholesale.
   - Recommendation: hand-author a *subset* Draft-2020-12 schema covering the keys this phase asserts; note it's a validation aid, not the runtime's schema.

2. **Do commands live as markdown files or inline in opencode.json?** Both are supported. Recommend markdown files in `harness/commands/` (uniform with agents/skills, cleaner emit). Confirm at plan time.

3. **YAML descriptions in `/docs-sync`?** Schemas alone (stdlib json, zero dep) vs also reading `*.yaml` specs (needs ruamel.yaml — already locked transitively). Recommend schema-only for MVP; revisit if reference is too terse.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 + uv workspace | resolver, docs_sync, harness_lint tests | ✓ | uv present | — |
| jsonschema | opencode.json structural test | ✓ | 4.26.0 (direct dep) | hand-rolled key asserts |
| syrupy | docs_sync determinism proof | ✓ | 5.2.0 | run-twice byte-compare (no snapshot) |
| opencode runtime | live agent/command/permission loading | ✗ | — | **DEFERRED (D-02)** — structural validation only |
| .NET SDK | `/build`·`/test` dotnet path execution | ✗ (egress-blocked) | — | command skips+instructs when `resolve_dotnet()` absent (D-05) |
| Network to opencode.ai | fetching live config schema | ✗ (403 to fetchers) | — | vendor/subset schema (Open Q1) |

**Missing with no fallback:** none block Phase 3 (all deferred items are explicitly out of scope per D-02).
**Missing with fallback:** opencode runtime → structural validation; .NET → gated skip; opencode.ai schema fetch → vendored subset.

## Validation Architecture

`workflow.nyquist_validation: true` → this section applies.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.4,<9 (+ syrupy 5.2.0 for determinism snapshots) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths = libs/python, tools) |
| Quick run command | `uv run pytest tools/harness_perms tools/docs_sync tools/harness_lint -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Automated Command | File |
|-----|----------|-----------|-------------------|------|
| CONFIG-01 | opencode.json is JSON-Schema valid; has model/small_model/instructions/formatter/mcp | structural | `pytest tools/harness_lint/tests/test_opencode_json.py -x` | ❌ Wave 0 |
| CONFIG-02 | 15-key matrix well-formed; last-wins resolves correctly | unit | `pytest tools/harness_perms/tests/test_resolver.py -x` | ❌ Wave 0 |
| CONFIG-02 | `git push --force`→ask/deny, `dotnet test`→allow, edit `golden/*`+`*.env`→deny | unit | same file | ❌ Wave 0 |
| AGENT-01..05 | each agent frontmatter valid (description non-empty, mode/permission valid) | structural | `pytest tools/harness_lint/tests/test_agents.py -x` | ❌ Wave 0 |
| AGENT-04 | code-reviewer read-only in BOTH representations (no edit/bash/write) | structural | same file | ❌ Wave 0 |
| CMD-01..09 | each command frontmatter valid; description has routing trigger | structural | `pytest tools/harness_lint/tests/test_commands.py -x` | ❌ Wave 0 |
| CMD-03 | `/golden-approve` refuses w/o human token/adr (already coded) | unit | `pytest tools/golden_runner/tests/test_approve_gate.py` | ✅ exists |
| CMD-06 | `/strangler-step` scaffold refuses w/o captured baseline | unit | `pytest tools/harness_lint/tests/test_strangler_refusal.py -x` (or in the command's tool) | ❌ Wave 0 |
| CMD-08 / DOCS-03 | `/docs-sync` delete+regenerate byte-identical; only writes `reference/` | integration+snapshot | `pytest tools/docs_sync/tests/test_docs_sync_determinism.py -x` | ❌ Wave 0 |
| SKILL-01/02 | each SKILL.md: name≤64 & regex & dir-match; desc≤1024 non-empty; body cap warn | structural | `pytest tools/harness_lint/tests/test_skills.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_perms tools/docs_sync tools/harness_lint -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** full suite green before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/harness_perms/resolver.py` + `tests/test_resolver.py` — CONFIG-02 (last-wins, default-deny, path denies)
- [ ] `tools/docs_sync/generate.py` + `tests/test_docs_sync_determinism.py` — CMD-08/DOCS-03 (determinism + reference-only)
- [ ] `tools/harness_lint/frontmatter.py` (shared YAML frontmatter parser) + tests for opencode.json / agents / commands / skills
- [ ] `tools/harness_lint/tests/test_strangler_refusal.py` — CMD-06 refusal (or colocate with the command's scaffold logic)
- [ ] `harness/opencode.config.schema.json` — vendored/subset schema for the structural test
- [ ] `pyproject.toml` for each new `tools/*` member (uv workspace requirement)
- [ ] Framework install: none (pytest/syrupy already locked)

## Security Domain

`security_enforcement` not set in config → treated as enabled. The security-relevant surface of Phase 3 is the **permission matrix + resolver** (this is the harness's sandbox) and input handling in the two runnable tools.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V4 Access Control | yes | 15-key permission matrix; reviewer read-only; constitution/secret path denies; default-deny posture |
| V5 Input Validation | yes | frontmatter/JSON parsed with `jsonschema` + explicit schema; glob patterns matched with stdlib `fnmatch` (no eval) |
| V6 Cryptography | no | no crypto authored here (contract hashing is Phase-1, reused not reimplemented) |
| V2 Authentication | no | human-gate is Phase-1 `approve.py` (env token) — reused |

### Known Threat Patterns for this harness
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Trailing broad `allow` overrides denies (last-wins) | Elevation of Privilege | `*` first, specifics after; resolver test proves resolution (P3) |
| Reviewer/explorer authored with write/bash | Elevation of Privilege | deny in opencode `permission` + omit from Claude `tools:`; lint asserts both (P-perm) |
| Secret exfiltration via `*.env` / secret read | Information Disclosure | path-deny globs in matrix; resolver denies; Phase-4 secret-protection hook (HOOK-02) enforces at runtime |
| Command injection through `!`shell`` / `$ARGUMENTS` in commands | Tampering | commands wrap `tools/*` CLIs which already use `subprocess([list], shell=False)`; never build shell strings from args |
| `/docs-sync` path traversal writing outside `reference/` | Tampering | generator confines output to `docs/reference/` (mirror `golden_runner._confine`); test asserts no writes elsewhere |

## Sources

### Primary (HIGH confidence)
- `platform.claude.com/docs/en/agents-and-tools/agent-skills` — SKILL.md name ≤64, description ≤1024 non-empty, progressive disclosure (resolves the 200-vs-1024 discrepancy)
- Repo `.claude/agents/*.md` + `.claude/commands/gsd/*.md` — Claude agent/command frontmatter (name/description/tools/color; `$ARGUMENTS`) observed directly
- Repo `tools/{golden_runner,contract_hash,contract_drift,memory_regen}/*.py` — command-wrapped CLIs, the memory_regen determinism pattern, `_confine`, approval refusal
- Repo `pyproject.toml` / `uv.lock` — dependency availability (jsonschema 4.26.0, syrupy, ruff; ruamel.yaml transitive)

### Secondary (MEDIUM confidence — opencode specifics, opencode.ai 403s to fetchers)
- WebSearch of `opencode.ai/docs/{config,permissions,agents,commands,skills}` snippets — 15 permission keys, allow/ask/deny, bash last-wins, `mode` primary/subagent/all, `tools:` deprecated → `permission:`, command `$ARGUMENTS`/`!shell`/`@file`/subtask, `.opencode/{agent,command,skill}/` paths
- `github.com/wesammustafa/OpenCode-Everything-You-Need-to-Know` (raw) — 15-key table, external_directory default `ask`, 3-level permission override
- `agensi.io/learn/skill-md-format-reference` + `opencode.ai/docs/skills` snippet — opencode SKILL.md fields (name 1-64, description 1-1024, optional license/compatibility/metadata, scripts/references/assets)
- Phase-2 `harness/plugins/session-inject.ts` RESUME NOTE — opencode hook-name MEDIUM confidence flagged for Phase-3 re-verify

### Tertiary (LOW confidence / flagged)
- `small_model` exact key name (A1); opencode bash glob == fnmatch (A3); command dir singular/plural (A5) — verify at Phase-6 emit/wiring

## Metadata

**Confidence breakdown:**
- Surface to author (agents/commands/skills lists, harness layout, tool-wrapping): HIGH — enumerated in CONTEXT/ROADMAP/REQUIREMENTS + existing tools inspected directly
- Runnable logic (resolver, docs_sync, structural lint): HIGH — pure Python, patterns already proven in-repo (contracts_index, golden_runner)
- Claude skill/agent caps + formats: HIGH — official docs + repo's own artifacts
- opencode frontmatter field names + permission keys: MEDIUM — official-doc snippets via WebSearch + mirrors (opencode.ai un-fetchable); acceptable because D-02 defers runtime behavior and structural validation is hermetic
- opencode config exact key names (small_model, hook names, dir singular/plural): MEDIUM-LOW — flagged in Assumptions Log for Phase-6 verification

**Research date:** 2026-07-08
**Valid until:** 2026-08-07 for stable repo facts; ~2026-07-22 for opencode specifics (rolling `sst/opencode` — re-verify field names before Phase-6 emit)
</content>
</invoke>
