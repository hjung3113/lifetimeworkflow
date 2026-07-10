# Stack Research

**Domain:** opencode agent harness (single-source → opencode + Claude Code) for a polyglot .NET 10 + Python contract-first log-parser monorepo
**Researched:** 2026-07-07
**Confidence:** HIGH for versions/toolchain; MEDIUM for opencode plugin internals (opencode.ai serves 403 to fetchers — verified via WebSearch + GitHub raw `sst/opencode` + open-code.ai mirror, not direct docs)

> Scope reminder: the deliverable is the **harness**, not the pipeline. "Stack" here = the tools the harness is authored in and the tools it orchestrates/validates. .NET/Python entries are the toolchains the harness must *drive and gate*, not implement.

---

## Recommended Stack

### Core Technologies (the harness itself)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **opencode** | latest (rolling; `sst/opencode`) | Primary runtime. Hosts agents/commands/skills/plugins, `opencode.json` config, permission matrix | Named primary target. Native TS/JS plugin API + custom `tool()` helper + hook surface (`tool.execute.before/after`, `permission.ask`, `event`, `config`, `command.execute.before`) is exactly the guardrail seam this project needs. Config-as-code (JSON + Markdown agents) suits single-source generation. |
| **@opencode-ai/plugin** + **@opencode-ai/sdk** + **zod** | plugin/sdk track opencode; zod 3.x | Plugin authoring: export function → `{ hooks }`; `tool({description, args:zod, execute})`; `PluginInput` gives `client`, `project`, `directory`, `worktree`, `$` (shell), `serverUrl` | Official API. `zod` schemas for tool args are the idiomatic contract for custom tools. Guardrail plugins (contract-guard, polyglot-boundary linter, format-on-write, session-start injector) all hang off these hooks. |
| **Node.js** | 20 LTS or 22 LTS | Runtime for opencode plugins + the single-source generator (`tools/adapters/`) | opencode plugins are ESM TS/JS; keeping the generator in the same runtime avoids a second toolchain. Use a local `package.json` in the config dir so external plugin deps resolve. |
| **Claude Code** | current | Secondary emitted runtime (`.claude/`) + the dev environment (GSD) | Constraint: dev = Claude Code, deploy = opencode. Harness emits `.claude/{agents,commands,skills}` from the same Markdown source. |
| **.NET SDK** | **10.0.100** (LTS, GA 2025-11-11, supported to 2028-11) | Toolchain the harness bootstraps/gates for parser + converter | LTS — 3-year support window matches a long-lived harness. Installed via `dotnet-install.sh --channel 10.0` in a SessionStart/setup hook (env has **no** .NET yet). |
| **uv** | **0.11.x** (0.11.27, 2026-07-06) | Python env/dep/workspace manager for scheduler + collector + config-parser | Cargo-style **workspaces**: one root `pyproject.toml` + single lockfile across `components/*` + `libs/python`. Already present in env (0.8.17 → bump). Replaces pip/poetry/pyenv/venv. |

### Single-Source → Multi-Runtime Emit (the generation layer)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **wshobson/agents pattern** | reference (2026 multi-harness) | Blueprint for one Markdown source → harness-native artifacts | Proven: `plugins/` = source-of-truth Markdown (Claude-flavored), `tools/adapters/` transpile per harness, `make generate HARNESS=opencode`. OpenCode agents emit to `.opencode/agent/<name>.md` with `mode: subagent`; Claude to `.claude/agents/`. **Adopt the pattern, not the 194-agent payload** (PROJECT decision: custom/minimal over generic port). |
| **Emit-time validators** | custom (Node) | Enforce each runtime's limits at generation | Claude skill limits: `SKILL.md` name ≤ 64 chars, description ≤ 1024 chars, body < ~500 lines (target ~150). opencode permission = 15-key matrix. Generator must fail loud when a source doc would violate a target's limit. |

### .NET golden/approval + test toolchain

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **xunit.v3** | **3.2.2** (2026-01-14) | .NET test framework | v3 has **Microsoft.Testing.Platform** built in — cleaner CI exit-code semantics, matches .NET 10. (Avoid v2 2.9.x for greenfield; v3 is the current line. v4.0.0 still pre-release — not yet.) |
| **Verify.XunitV3** | **31.20.0** (2026-06-18) | Golden/approval (snapshot) testing for .NET | Best-in-class .NET snapshot lib. Built-in scrubbers → canonicalize newlines, culture, GUIDs, dates. Its `.received/.verified` workflow maps directly onto `/golden-approve` + CODEOWNERS human gate. |
| **Microsoft.Testing.Platform** | bundled w/ xunit.v3 | Test runner/exec | Native to xunit.v3; use `dotnet test` or the MTP runner in CI. |

### Python golden/approval + test/quality toolchain

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest** | **8.4.x** (pin `>=8.4,<9` initially; 9.1.1 exists) | Python test framework | Pin to 8.4 for a beat: pytest 9.x (2026-06) is fresh and syrupy 5.2.0 compat should be verified before adopting. Bump to 9.x once green. |
| **syrupy** | **5.2.0** | Golden/approval (snapshot) testing for Python — the pytest analogue of Verify | Single-file `.ambr` snapshots, `--snapshot-update` = `/golden-approve` on the Python side. Custom extensions handle TSV/normalized serialization. |
| **ruff** | **0.15.x** (pin `~=0.15`; 0.14.14 = prior stable) | Lint + format (replaces black/isort/flake8) | Astral, Rust-fast, single config in `pyproject.toml`. Wire into the `format-on-write` plugin + pre-commit. |
| **pyright** | **1.1.409** | Static type checker | Recommend over mypy: faster, and it's the LSP opencode/editors already speak (aligns with the `lsp` permission key). Astral's `ty` is still preview — do **not** standardize on it yet. |

### Contract validation (works from BOTH .NET and Python)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **JSON Schema (Draft 2020-12)** | spec | Neutral contract IR for TSV column specs, reference-data, state/carryover shapes | Language-neutral, both ecosystems have mature validators. The `contracts/` dir holds `.schema.json` as the single source; code in both languages validates against it. |
| **JsonSchema.Net** (json-everything) | **9.2.2** (2026-06-14) | .NET-side schema validation | System.Text.Json-based (no Newtonsoft baggage), current Draft 2020-12. Preferred over **NJsonSchema 11.6.1** (Newtonsoft-based, heavier) and Newtonsoft.Json.Schema (commercial license limits). |
| **jsonschema** (Python) | **4.26.0** | Python-side schema validation | Reference Python implementation, full Draft 2020-12. |
| **check-jsonschema** | **0.37.x** | CLI + pre-commit hook for schema validation | The `/contract-check` command + CI gate wrap this. Validates YAML/JSON contract instances against the schemas in one invocation. |
| **buf CLI** | latest (extension point only) | `.proto` lint + **breaking-change detection** | Only for the deferred **B model** (gRPC). `buf breaking` is the proto-native drift gate. Keep as a documented extension seam, not MVP. |

### Context-memory tooling (two-plane, derived layer)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **tree-sitter** grammars (C#, Python) + **py-tree-sitter** | current | Parse source → symbol defs/refs for the repo map | Aider's proven recipe. Per-language `tags.scm` distinguishes definition vs reference. |
| **networkx** | 3.x | PageRank over the symbol graph | Personalized PageRank ranks files by importance; render top-N elided defs into a token-bounded `.memory/repo-map.md` (derived plane). |
| **grep-ast / aider repomap** (reference) | current | Optional: reuse Aider's `--show-repo-map` instead of rebuilding | If you don't want to hand-roll: shell out to aider's repo-map or port `RepoMapper`. Recommend a **minimal purpose-built generator** (PROJECT: custom/minimal), caching parsed tags on disk. |
| **memory-bank file convention** | pattern | Derived/volatile plane files: `.memory/activeContext.md`, `.memory/progress.md`, `.memory/repo-map.md`, `.memory/contracts-index.md` | Cline "memory-bank" pattern. Constitution plane (`contracts/`, `adr/`, `glossary/`, `golden/`) is human-owned + gated; derived plane is auto-regenerated, never hand-edited. |
| **SessionStart injection** | opencode `event` hook / Claude Code `SessionStart` hook | Non-ignorable injection of derived state each session | opencode: plugin subscribes to session-start `event`, injects repo-map + activeContext. Claude Code: native `SessionStart` hook. Same source doc → both emitted. |

### Development / CI tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **GitHub Actions** | Polyglot matrix CI | Jobs: `dotnet` (`actions/setup-dotnet@v4` or `dotnet-install.sh --channel 10.0` → `dotnet test`), `python` (`astral-sh/setup-uv@v6` → `uv run pytest`), `contract-check` (`check-jsonschema` + schema-hash drift gate), `golden` (both snapshot suites). Fan-in gate requires all green. |
| **pre-commit** | Local guardrails | `ruff` (lint+format), `check-jsonschema`, schema-hash check. Mirrors CI so drift is caught pre-push. |
| **JCS / RFC 8785 canonicalization** | Schema-hash drift detection | Canonicalize each contract schema (sorted keys, normalized whitespace) → SHA-256 → commit the hash. CI recomputes; mismatch without a paired golden update = **fail**. This is the contract-first gate. |
| **CODEOWNERS** | Human approval on constitution plane | `contracts/`, `adr/`, `golden/` require owner review → enforces `/golden-approve` + ADR immutability. |

---

## Golden-Equivalence Comparator Building Blocks

The cross-language safety net. Golden files are the neutral artifact; both languages must produce byte-identical (post-canonicalization) output. Build a **small shared canonicalizer** (domain-specific — Verify/syrupy scrubbers cover the language-local half, but the *cross-language* comparator lives in `tools/`):

| Concern | Canonicalization rule | Rationale (from integration_contracts §4) |
|---------|----------------------|-------------------------------------------|
| Encoding | UTF-8, **BOM stripped** | .NET may emit BOM; Python misreads first column (§4.3) |
| Newlines | Force **LF** | .NET defaults to CRLF (§4.3) |
| Decimal | `.` separator, **InvariantCulture** | .NET `ToString` is locale-dependent (§4.6) |
| Numeric compare | **tolerance-aware** float compare | avoid spurious diffs on last-digit float repr |
| Key/row ordering | deterministic sort before diff | unordered sets must not cause false diffs |
| Timezone | UTC, ISO-8601 fixed string | .NET `DateTime.Kind` vs Python naive/aware (§4.4) |
| TSV escape / null | agreed escape + explicit null token | tab/newline-in-value + ""≠null (§4.3) |

Recommendation: implement once (Python is a good host — collector/scheduler are Python and CI already runs it), invoked by both `/golden` and the CI `golden` job. Do **not** rely on naive `diff`.

---

## Installation

```bash
# --- .NET 10 (env has none) — run from SessionStart/setup hook ---
curl -sSL https://dot.net/v1/dotnet-install.sh -o dotnet-install.sh
./dotnet-install.sh --channel 10.0            # installs SDK 10.0.1xx LTS
dotnet new xunit --version 3.2.2              # per test project
# csproj: <PackageReference Include="Verify.XunitV3" Version="31.20.0" />
#         <PackageReference Include="JsonSchema.Net" Version="9.2.2" />

# --- Python (uv workspace) ---
uv self update                                 # -> 0.11.x
uv add --dev pytest syrupy ruff pyright        # 8.4.x / 5.2.0 / 0.15.x / 1.1.409
uv add --dev check-jsonschema                  # 0.37.x
uv add jsonschema                              # 4.26.0 (runtime validator)

# --- Harness / generator (Node, in config dir) ---
npm install @opencode-ai/plugin @opencode-ai/sdk zod
npm install -D typescript

# --- Repo-map (derived memory plane) ---
uv add tree-sitter tree-sitter-c-sharp tree-sitter-python networkx
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Verify.XunitV3 31.20.0 | ApprovalTests.Net | If team already standardized on ApprovalTests' reporters; Verify has better scrubber ergonomics for this canonicalization-heavy domain. |
| JsonSchema.Net 9.2.2 | NJsonSchema 11.6.1 | If you also need **C#/TS class generation from schema**; NJsonSchema does codegen, JsonSchema.Net is validate-only-focused. |
| pyright 1.1.409 | mypy | Legacy/strict-mypy shops; mypy plugin ecosystem. pyright is faster + LSP-native here. |
| syrupy 5.2.0 | pytest-snapshot / pytest-regressions | syrupy is the modern default; alternatives fine for plain-text-only fixtures. |
| Custom minimal repo-map (tree-sitter+networkx) | Aider `--show-repo-map` / RepoMapper MCP | If you want it working in an afternoon, shell out to Aider; custom gives control over token budget + C#/Python-only scope. |
| Schema-hash + golden gate | Pact / PactFlow BDCT + Drift | **Only if boundaries become HTTP.** See "What NOT to Use". |
| xunit.v3 3.2.2 | NUnit / MSTest | Team preference; all three now support Microsoft.Testing.Platform. xUnit is the .NET community default. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Pact / consumer-driven contract testing** | Pact is built for **HTTP/gRPC/message** request-response contracts. This domain's boundaries are **file / DB / CLI-spawn** (integration_contracts §④ A-model). Pact adds a broker + mock-provider machinery that models nothing here. | JSON Schema + **golden equivalence** + schema-hash drift gate. Revisit only if the B-model (gRPC) ships. |
| **Newtonsoft.Json.Schema** | Commercial licensing beyond a free op-count; ties you to Newtonsoft | JsonSchema.Net (System.Text.Json, free) |
| **xunit v2 (2.9.x)** for greenfield | Predates Microsoft.Testing.Platform integration; v3 is the current line | xunit.v3 3.2.2 |
| **xunit v4 pre-release (4.0.0-pre)** | Not GA; MTP v2 default not stabilized | xunit.v3 3.2.2 |
| **Astral `ty`** as the standardized type checker | Still preview/pre-1.0 in 2026 | pyright 1.1.409 now; re-evaluate `ty` at 1.0 |
| **pip / poetry / pyenv** | uv workspaces replace all three; mixing causes lockfile drift | uv 0.11.x |
| **Porting gsd-opencode / 750-file generic packs** | PROJECT decision: custom, minimal, domain-accurate | wshobson *pattern* + hand-authored harness |
| **Object/in-process cross-language calls** | Domain rule: language boundary = process/file/DB only | CLI spawn + exit codes (A model) |
| **Naive `diff` for golden compare** | Fails on BOM/CRLF/locale/float-repr — the exact polyglot bugs (§4.3–4.6) | Canonicalizing comparator (above) |

---

## Stack Patterns by Variant

**If staying on A-model (CLI spawn — MVP, recommended):**
- Contracts = JSON Schema files + TSV spec docs; drift = schema-hash gate; equivalence = golden files.
- No proto, no broker. `/contract-check` = `check-jsonschema` + hash compare.

**If B-model (gRPC) is later adopted:**
- Add `.proto` as the single source for job/progress messages; `buf lint` + `buf breaking` become the drift gate for that boundary.
- Keep the *logical job payload identical* to A-model (§④) so the harness commands don't fork.

**If repo grows past ~a few hundred source files:**
- Cache tree-sitter tags on disk (diskcache-style) and regenerate repo-map incrementally; cap map token budget (~1k default) in the SessionStart injector.

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| .NET SDK 10.0.100 | xunit.v3 3.2.2, Verify.XunitV3 31.20.0, JsonSchema.Net 9.2.2 | All target current .NET; Verify.XunitV3 requires the v3 line specifically. |
| xunit.v3 3.2.2 | Microsoft.Testing.Platform v1 (default in 3.x) | MTP v2 only from xunit v4 — don't mix. |
| pytest 8.4.x | syrupy 5.2.0 | **Verify** syrupy 5.2.0 against pytest **9.1.x** before bumping — pytest 9 (2026-06) is new. |
| uv 0.11.x | ruff 0.15.x, pyright 1.1.409, pytest 8.4.x | All install cleanly via `uv add --dev`; single workspace lockfile. |
| @opencode-ai/plugin | @opencode-ai/sdk + zod 3.x | Custom `tool()` args expect zod schemas; keep zod major aligned with SDK. |
| Claude Code skills | SKILL.md: name ≤64, desc ≤1024, body <~500 lines | Generator must enforce at emit time or Claude rejects/truncates. |

---

## Sources

- WebSearch + GitHub raw `sst/opencode/packages/plugin` — plugin hooks (`tool.execute.before/after`, `permission.ask`, `event`, `config`, `command.execute.before`), `PluginInput` (`client`, `project`, `directory`, `worktree`, `$`), custom `tool()` helper — MEDIUM (opencode.ai 403s direct fetch)
- WebSearch — opencode 15-key permission matrix + last-wins glob (`*` first, specifics after) — MEDIUM
- github.com/wshobson/agents (README, docs/harnesses.md) — single-source → per-harness adapters, opencode `mode: subagent` — HIGH
- devblogs.microsoft.com/dotnet Announcing .NET 10; learn.microsoft.com dotnet-install-script — .NET 10 LTS 10.0.100, GA 2025-11-11 — HIGH
- nuget.org — xunit.v3 3.2.2 (2026-01-14), Verify.XunitV3 31.20.0 (2026-06-18), JsonSchema.Net 9.2.2 (2026-06-14), NJsonSchema 11.6.1 — HIGH
- pypi.org / GitHub releases — uv 0.11.27 (2026-07-06), ruff 0.15.13 (0.14.14 stable), pyright 1.1.409, pytest 9.1.1 (8.4.x stable), syrupy 5.2.0, jsonschema 4.26.0, check-jsonschema 0.37.x — HIGH
- pactflow.io / docs.pact.io — Pact v4 is HTTP/gRPC/message-oriented (why NOT for file/DB/CLI) — HIGH
- aider.chat/2023/10/22/repomap.html + DeepWiki Aider — tree-sitter + personalized PageRank + tags.scm + token budget + disk cache — HIGH
- docs.claude.com agent-skills best-practices — SKILL.md name ≤64 / desc ≤1024 / body <500 lines, progressive disclosure — HIGH

---
*Stack research for: opencode harness / polyglot .NET 10 + Python contract-first monorepo*
*Researched: 2026-07-07*
</content>
</invoke>
