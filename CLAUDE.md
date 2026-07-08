<!-- GSD:project-start source:PROJECT.md -->
## Project

**설비 로그파서 파이프라인 opencode 하네스 (LogParser Pipeline Harness)**

반도체 설비 이벤트 로그파서를 책임 분리된 폴리글랏 모노레포(.NET 10 파서·컨버터 / Python 스케줄러·수집기)로 재설계하는 프로젝트를, **에이전트가 만들고·유지보수·개발·리팩토링**할 수 있게 해주는 **opencode 에이전트 하네스**다. 산출물은 컴포넌트 구현 코드가 아니라 하네스 그 자체 — opencode agents·commands·skills·plugins, Diátaxis+ADR+contracts 문서구조, 그리고 세션을 넘어 유지되는 두 평면(헌법/파생) 컨텍스트 메모리 층이다. 대상 사용자는 이 모노레포에서 일하는 개발자와 그들을 돕는 코딩 에이전트다.

**Core Value:** **계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다** — 에이전트가 이 레포에서 "어떻게 개발·유지보수·리팩토링하는가"가 부족(tribal knowledge)이 아니라 실행 가능한 스킬·커맨드·훅으로 박혀 있어야 한다.

### Constraints

- **Runtime**: opencode 1차 타깃, 단일 소스에서 Claude Code 아티팩트도 생성(개발=Claude, 배포=opencode). 각 런타임 제약(예: 스킬 크기 상한) 존중.
- **Polyglot**: 파서·컨버터=.NET 10(CPU 바운드), 스케줄러·수집기=Python(uv). 언어 경계는 프로세스/파일/DB로만 — 객체 직접 전달 금지.
- **Contract-first**: contracts/가 코드보다 우선. 코드가 계약과 다르면 코드가 틀린 것. 계약 변경은 골든/contract-drift 게이트를 동반.
- **Memory**: two-plane. 파생물(repo-map·contracts-index·docs/reference)은 손으로 관리 금지(자동 생성). 결정은 append-only ADR.
- **Env**: 원격 ephemeral — 하네스는 SessionStart 훅으로 툴체인/상태를 자기부트스트랩. 브랜치 `claude/data-pipeline-harness-8aypct`.
- **모델 아이덴티티**: 커밋·PR·코드 코멘트 등 레포 산출물에 모델 식별자 미포함.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
## Golden-Equivalence Comparator Building Blocks
| Concern | Canonicalization rule | Rationale (from integration_contracts §4) |
|---------|----------------------|-------------------------------------------|
| Encoding | UTF-8, **BOM stripped** | .NET may emit BOM; Python misreads first column (§4.3) |
| Newlines | Force **LF** | .NET defaults to CRLF (§4.3) |
| Decimal | `.` separator, **InvariantCulture** | .NET `ToString` is locale-dependent (§4.6) |
| Numeric compare | **tolerance-aware** float compare | avoid spurious diffs on last-digit float repr |
| Key/row ordering | deterministic sort before diff | unordered sets must not cause false diffs |
| Timezone | UTC, ISO-8601 fixed string | .NET `DateTime.Kind` vs Python naive/aware (§4.4) |
| TSV escape / null | agreed escape + explicit null token | tab/newline-in-value + ""≠null (§4.3) |
## Installation
# --- .NET 10 (env has none) — run from SessionStart/setup hook ---
# csproj: <PackageReference Include="Verify.XunitV3" Version="31.20.0" />
#         <PackageReference Include="JsonSchema.Net" Version="9.2.2" />
# --- Python (uv workspace) ---
# --- Harness / generator (Node, in config dir) ---
# --- Repo-map (derived memory plane) ---
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
## Stack Patterns by Variant
- Contracts = JSON Schema files + TSV spec docs; drift = schema-hash gate; equivalence = golden files.
- No proto, no broker. `/contract-check` = `check-jsonschema` + hash compare.
- Add `.proto` as the single source for job/progress messages; `buf lint` + `buf breaking` become the drift gate for that boundary.
- Keep the *logical job payload identical* to A-model (§④) so the harness commands don't fork.
- Cache tree-sitter tags on disk (diskcache-style) and regenerate repo-map incrementally; cap map token budget (~1k default) in the SessionStart injector.
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| .NET SDK 10.0.100 | xunit.v3 3.2.2, Verify.XunitV3 31.20.0, JsonSchema.Net 9.2.2 | All target current .NET; Verify.XunitV3 requires the v3 line specifically. |
| xunit.v3 3.2.2 | Microsoft.Testing.Platform v1 (default in 3.x) | MTP v2 only from xunit v4 — don't mix. |
| pytest 8.4.x | syrupy 5.2.0 | **Verify** syrupy 5.2.0 against pytest **9.1.x** before bumping — pytest 9 (2026-06) is new. |
| uv 0.11.x | ruff 0.15.x, pyright 1.1.409, pytest 8.4.x | All install cleanly via `uv add --dev`; single workspace lockfile. |
| @opencode-ai/plugin | @opencode-ai/sdk + zod 3.x | Custom `tool()` args expect zod schemas; keep zod major aligned with SDK. |
| Claude Code skills | SKILL.md: name ≤64, desc ≤1024, body <~500 lines | Generator must enforce at emit time or Claude rejects/truncates. |
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

## Agent Rules — see AGENTS.md

The canonical, nearest-wins rules for working in this repo live in **`AGENTS.md`** (root)
and the per-package files it points to (`libs/python/AGENTS.md`, `libs/dotnet/AGENTS.md`).
Read the root `AGENTS.md` first; read a per-package `AGENTS.md` only when you touch that
package (lazy-load). Non-negotiables (contract-first, §4.3–4.6 boundary invariants,
constitution-plane-is-gated, derived-not-hand-edited) are restated per-package — never
inherited-only. This is a pointer, not a duplicate: `AGENTS.md` is the source.

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
