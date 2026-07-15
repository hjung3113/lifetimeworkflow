<!-- refreshed: 2026-07-14 -->
# Architecture

**Analysis Date:** 2026-07-14

## System Overview

This repository is **not** a running application — it is a **contract-first polyglot agent-harness
template**. The "system" it builds is a set of guardrail tooling (Python CLIs, generated agent/
command/skill artifacts, CI gates) that lets AI coding agents safely develop a separate polyglot
monorepo (an "instance," e.g. `examples/log-parser/`). Read this diagram as: authored source →
validated/projected artifacts → two runtime trees, plus a parallel contracts → drift/golden gate
pipeline.

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    AUTHORED SOURCE (human-edited, runtime-neutral)                 │
├───────────────────────────┬───────────────────────────┬─────────────────────────────┤
│  harness/agents/*.md      │  harness/commands/*.md     │  harness/skills/*/SKILL.md  │
│  harness/plugins/*.ts     │  harness/permission-matrix │  harness/project.toml        │
│  harness/opencode.json    │  .json                     │  (language/instance slot)    │
└─────────────┬─────────────┴──────────────┬──────────────┴───────────────┬───────────┘
              │                            │                              │
              ▼                            ▼                              ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│           tools/harness_emit (EMIT-01/02) — validate-then-write emitter            │
│           `tools/harness_emit/generate.py::emit()`                                  │
│  discover (iter_agents/iter_commands/iter_skills) → validate (validate.py) →        │
│  project per-runtime shape (project_agent.py / project_command.py / project_skill.py)│
│  → deterministic render (render_markdown, LF/no-BOM, fixed frontmatter order) →      │
│  confine + write BOTH trees → ownership manifest (manifest.py, prune-then-write)     │
└──────────────┬───────────────────────────────────────────┬──────────────────────────┘
               ▼                                            ▼
┌────────────────────────────────┐          ┌────────────────────────────────────────┐
│  .opencode/ (PRIMARY runtime)   │          │  .claude/ (SECONDARY runtime, dev env)  │
│  agent/ command/ skill/ plugin/ │          │  agents/ commands/ skills/               │
│  + root opencode.json            │          │  settings.json (Regime-B signature merge)│
└────────────────────────────────┘          └────────────────────────────────────────┘
      GENERATED — never hand-edited (re-emit overwrites; CI `emit-drift` gate enforces)

┌───────────────────────────────────────────────────────────────────────────────────┐
│         CONSTITUTION PLANE (human-owned, CODEOWNERS-gated, single source of truth) │
│  `contracts/**` (JSON Schema Draft 2020-12 + YAML)   `docs/adr/**` (append-only)    │
│  `golden/**` (.verified baselines)   `docs/glossary.md`   `libs/normalize-spec.md`  │
└───────────────────────────┬─────────────────────────────────────────┬───────────────┘
                             ▼                                        ▼
┌────────────────────────────────────────┐        ┌───────────────────────────────────┐
│ tools/contract_hash + tools/contract_drift │      │ tools/golden_runner                │
│ RFC 8785 (JCS) canonicalize → SHA-256    │        │ spawn converter (A-model CLI) →    │
│ per-schema hash → manifest baseline;      │        │ normalize both sides via           │
│ drift = live vs baseline + breaking/      │        │ libs/python/normalize.core →       │
│ non-breaking classification               │        │ diff → PASS or .received.tsv       │
└────────────────────────────────────────┘        └───────────────────────────────────┘
                             │                                        │
                             └──────────────┬─────────────────────────┘
                                             ▼
                          ┌──────────────────────────────────────┐
                          │  .github/workflows/ci.yml — `gate`    │
                          │  fan-in of 9 jobs (see CI Gates below)│
                          └──────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────┐
│         DERIVED PLANE (machine-owned, regenerated, two git-treatment sub-tiers)     │
│  gitignored: `.memory/derived/repo-map.md` (tree-sitter + networkx PageRank)         │
│  committed-derived (CI-verified): `.memory/derived/contracts-index.md`,              │
│    `docs/reference/**` (tools/docs_sync)                                             │
│  committed STATE (agent-authored, provisional): `.memory/state/activeContext.md`,     │
│    `.memory/state/progress.md`                                                       │
└───────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
                          SessionStart injection (`tools/memory_regen/inject.py::assemble()`)
                          banner → live drift summary → contracts-index head → repo-map top-N
                          → activeContext pointer — capped ~1k tokens / 4000 chars, pointer-only
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Harness-source authoring | Runtime-neutral agents/commands/skills/plugins/config | `harness/agents/*.md`, `harness/commands/*.md`, `harness/skills/*/SKILL.md`, `harness/plugins/*.ts`, `harness/opencode.json`, `harness/permission-matrix.json` |
| Emit spine | Validate-then-write single-source → dual-runtime projector | `tools/harness_emit/generate.py` |
| Per-runtime projection | Shape frontmatter for opencode vs Claude | `tools/harness_emit/project_agent.py`, `tools/harness_emit/project_command.py`, `tools/harness_emit/project_skill.py` |
| Emit validation (loud-fail) | Cap/shape checks before any write | `tools/harness_emit/validate.py` |
| Ownership manifest | Prune-then-write list of emitter-owned paths | `tools/harness_emit/manifest.py`, `tools/harness_emit/emit-manifest.json` |
| Regime-B merge (shared files) | Splice HARNESS-MANAGED block into `AGENTS.md`/`CLAUDE.md`, signature-merge `.claude/settings.json` | `tools/harness_emit/merge.py` |
| Permission projection | Matrix → 15-key opencode permission block | `tools/harness_emit/permissions.py` |
| Schema canonicalization + hashing | RFC 8785 JCS + SHA-256 baseline manifest | `tools/contract_hash/hash.py` |
| Contract-drift gate | Live vs baseline diff + breaking/non-breaking classification (single-repo + cross-repo workspace) | `tools/contract_drift/drift.py` |
| Golden equivalence runner | Spawn converter (A-model CLI), normalize both sides, diff, propose `.received.tsv` | `tools/golden_runner/runner.py` |
| Golden promotion (human-gated) | `.received.tsv` → `.verified.tsv` only with explicit approval token | `tools/golden_runner/approve.py` |
| §4.3–4.6 normalization core | Language-neutral canonicalization (BOM/CRLF/decimal/timezone/null/TSV) | `libs/python/normalize/core.py`, `libs/normalize-spec.md` |
| Polyglot boundary linter | Detect-by-normalization rule engine (R1–R8) shared by hooks + commit-gate | `tools/polyglot_lint/lint.py` |
| Permission resolver | Pure last-wins glob bash resolver + path-scoped deny resolver | `tools/harness_perms/resolver.py` |
| PreToolUse/PostToolUse hooks | Constitution-plane write gate, byte-hygiene auto-fix, secret scan, commit gate | `tools/hooks/contract_guard.py`, `tools/hooks/format_on_write.py`, `tools/hooks/secret_scan.py`, `tools/hooks/commit_gate.py` |
| Strangler-extraction refusal gate | Refuse legacy extraction with no captured golden baseline | `tools/strangler_guard/guard.py` |
| Derived-memory regeneration | Repo-map (tree-sitter + PageRank), contracts-index, docs/reference, SessionStart payload | `tools/memory_regen/repo_map.py`, `tools/memory_regen/contracts_index.py`, `tools/docs_sync/generate.py`, `tools/memory_regen/inject.py` |
| Harness config loader | `harness/project.toml` GEN-03 SSOT reader (languages/components/pipeline) | `tools/harness_config/loader.py` |
| Workspace config loader | `workspace.toml` MREPO-01 SSOT reader (members/edges) | `tools/workspace_config/loader.py` |
| Lint/consistency guards | GEN-03/GEN-04/GEN-05 consistency + core→example dependency guard | `tools/harness_lint/tests/test_core_no_example_dep.py`, `tools/harness_lint/tests/test_language_config.py`, `tools/harness_lint/tests/test_pipeline_config.py` |
| Toolchain bootstrap | SessionStart self-heal: install .NET 10, `uv sync` | `tools/bootstrap/install.sh`, `tools/bootstrap/verify.sh` |
| CI mirror | Re-runs every tools/* gate at merge time, config-derived language matrix | `.github/workflows/ci.yml` |

## Pattern Overview

**Overall:** Config-as-data harness generator + gated constitution/derived two-plane memory model,
layered on top of a template↔instance split.

**Key Characteristics:**
- **Single-source, dual-runtime emission.** Every agent/command/skill/plugin/permission is
  authored exactly once under `harness/` and mechanically projected to `.opencode/` (primary) and
  `.claude/` (secondary, dev environment). The emitter is deterministic (no timestamps, no floats,
  fixed frontmatter key order, LF/no-BOM) so re-emit is byte-identical — this is what the CI
  `emit-drift` gate checks.
- **Contract-first.** `contracts/**` (JSON Schema Draft 2020-12 + YAML) is the single source of
  truth; code that disagrees with a contract is wrong. Every schema change must be paired with a
  golden baseline update and is caught by the JCS-hash drift gate if not.
- **Two-plane (really three-tier) memory model.** CONSTITUTION (`contracts/`, `docs/adr/`,
  `golden/`, `docs/glossary.md`) is human-owned/CODEOWNERS-gated. DERIVED splits into gitignored
  (`.memory/derived/repo-map.md`) and committed-derived/CI-verified (`.memory/derived/
  contracts-index.md`, `docs/reference/**`). STATE (`.memory/state/*.md`) is committed,
  agent-authored, and explicitly provisional (constitution always wins on conflict).
- **Template↔instance split (ADR-0002).** The core (`tools/`, `harness/`, `libs/`, `contracts/`
  generic default) is domain-neutral and depends on **no** instance. `examples/log-parser/` is a
  reference instance (semiconductor equipment-log domain) that depends on the core. The
  dependency direction is enforced mechanically by the GEN-04/GEN-05 guard test.
- **Polyglot boundary = process/file/DB only.** .NET and Python components never pass objects
  in-process; the golden runner spawns the .NET converter via `subprocess.run([...], shell=False)`
  and reads its `--out` file — never stdout, never an in-process call.
- **Machines gate, humans ratify.** Agents cannot write `contracts/**`, `docs/adr/**`, `golden/**`
  without a human-authorized `GOLDEN_APPROVE_HUMAN` token (`tools/hooks/contract_guard.py`); golden
  promotion (`.received.tsv` → `.verified.tsv`) requires an explicit `--approve --adr <id>` CLI
  call, never an automatic overwrite.
- **Config-as-data SSOT slots, no codegen.** `harness/project.toml` ([instance]/[[languages]]/
  [[components]]/[pipeline]) and `workspace.toml` ([workspace]/[[members]]/[pipeline]) are pure
  TOML data with zero embedded logic; consistency between config and derived artifacts (CI matrix,
  permission-matrix bash scopes, engineer personas) is enforced by dedicated pytest consistency
  gates, not by generating one from the other (D-03: "full codegen is overkill").

## Layers

**Authored harness source (`harness/`):**
- Purpose: Runtime-neutral definitions of agents, commands, skills, plugins, and config that the
  emitter projects into both runtime trees.
- Location: `harness/agents/*.md`, `harness/commands/*.md`, `harness/skills/*/SKILL.md`,
  `harness/plugins/*.ts`, `harness/git-hooks/pre-commit`, `harness/opencode.json`,
  `harness/permission-matrix.json`, `harness/project.toml`.
- Contains: Markdown with YAML frontmatter (agents/commands/skills), TypeScript plugin sources
  (copied byte-for-byte, never parsed/executed by the emitter), JSON config, TOML data slots.
- Depends on: Nothing else in the repo (leaf authoring layer); `harness/plugins/*.ts` conceptually
  depends on opencode's runtime plugin API (`tool.execute.before/after`, `permission.ask`, `event`,
  `command.execute.before` hooks) but that dependency is not resolved at emit time.
- Used by: `tools/harness_emit` (source of truth for generation).

**Emit engine (`tools/harness_emit/`):**
- Purpose: Read `harness/` source, validate cap/shape rules, project per-runtime frontmatter,
  render deterministic Markdown/JSON, write both runtime trees plus an ownership manifest.
- Location: `tools/harness_emit/{generate,manifest,merge,permissions,project_agent,project_command,
  project_skill,validate}.py`.
- Contains: Pure-Python transform + write logic; no runtime execution of the emitted `.ts` plugins.
- Depends on: `tools/harness_lint` (shared frontmatter parser `parse_frontmatter`), `tools/
  harness_perms` (permission matrix loader).
- Used by: `python -m tools.harness_emit` (CLI entry, `tools/harness_emit/__main__.py`); the CI
  `emit-drift` job re-runs it and diffs against committed output.

**Generated runtime trees (`.opencode/`, `.claude/`):**
- Purpose: Runtime-native artifact trees actually loaded by opencode (primary) and Claude Code
  (secondary, the dev environment).
- Location: `.opencode/{agent,command,skill,plugin}/`, root `opencode.json`, `.claude/{agents,
  commands,skills}/`, `.claude/settings.json` (hook groups signature-merged, not template-owned).
- Contains: Machine-rendered Markdown (DERIVED marker as first frontmatter line), byte-copied `.ts`
  plugin sources, the 15-key opencode permission block.
- Depends on: Nothing (leaf, generated-only).
- Used by: The opencode/Claude runtimes directly; never read as source by any tool in this repo. Do
  not treat as source when mapping the codebase.

**Constitution plane (`contracts/`, `docs/adr/`, `golden/`, `docs/glossary.md`,
`libs/normalize-spec.md`):**
- Purpose: The single, human-owned source of truth for data shape (contracts), architectural
  decisions (ADRs, append-only), approved cross-language equivalence baselines (golden), and shared
  vocabulary.
- Location: `contracts/{normalization,sample}/*.schema.json` + `contracts/.hashes/manifest.json`
  (root generic-default instance); `docs/adr/000N-*.md`; `golden/sample/{input,expected}/`;
  `docs/glossary.md`; `libs/normalize-spec.md` (the canonical §4.3–4.6 rule spec text).
- Contains: JSON Schema Draft 2020-12 documents, YAML instance data, Markdown ADRs, TSV golden
  fixtures.
- Depends on: Nothing (constitution is the root of trust).
- Used by: `tools/contract_hash`, `tools/contract_drift`, `tools/golden_runner`,
  `tools/hooks/contract_guard.py` (write-gate), `tools/docs_sync` (renders `docs/reference/**`
  from it).

**Gate engine (`tools/contract_hash/`, `tools/contract_drift/`, `tools/golden_runner/`,
`tools/polyglot_lint/`, `tools/hooks/`, `tools/strangler_guard/`):**
- Purpose: Enforce contract-first + polyglot-boundary invariants, both interactively (hooks) and at
  merge time (CI mirror of the same CLIs).
- Location: `tools/contract_hash/hash.py`, `tools/contract_drift/drift.py`,
  `tools/golden_runner/{runner,approve}.py`, `tools/polyglot_lint/lint.py`, `tools/hooks/
  {contract_guard,format_on_write,secret_scan,commit_gate}.py`, `tools/strangler_guard/guard.py`.
- Contains: Pure-Python canonicalization, hashing, subprocess-spawn (A-model), diff, and
  stdin-driven hook decision logic (no `eval`, no shell string interpolation).
- Depends on: `libs/python/normalize/core.py` (the one §4.3–4.6 engine, reused — never
  reimplemented), `tools/harness_perms` (permission resolution), `tools/workspace_config`
  (cross-repo member/edge resolution).
- Used by: Interactive PreToolUse/PostToolUse hooks (wired via `.claude/settings.json`, authored via
  `harness/plugins/*.ts` for opencode), the `harness/commands/*.md` command macros
  (`/contract-check`, `/golden`, `/golden-approve`, `/strangler-step`), and `.github/workflows/
  ci.yml` (`contract-check`, `drift`, `golden`, `workspace` jobs).

**Derived-memory engine (`tools/memory_regen/`, `tools/docs_sync/`):**
- Purpose: Regenerate the derived plane (repo-map, contracts-index, docs/reference,
  SessionStart payload) from the constitution plane + source tree; never hand-edited.
- Location: `tools/memory_regen/{repo_map,contracts_index,inject,queries}.py`,
  `tools/docs_sync/{generate,__main__}.py`.
- Contains: tree-sitter parsing + `networkx.pagerank` (repo-map), Markdown rendering from
  `contracts/**` (docs/reference), a capped/priority-truncated injection-payload assembler.
- Depends on: `libs/python` + `tools` source trees (repo-map scope), `contracts/**` (docs_sync
  input), `tools/contract_drift.run_gate` (live drift summary in the injection payload).
- Used by: `/refresh-memory` command, CI `stale-derived` job (regenerate + diff), the opencode
  `event` hook / Claude `SessionStart` hook (non-ignorable injection, deferred wiring documented in
  `tools/memory_regen/inject.py`).

**Config-slot layer (`harness/project.toml`, `workspace.toml`, their loaders):**
- Purpose: Pure-data SSOT for the active instance's language/toolchain set, pipeline topology, and
  (one level up) the multi-repo workspace member/edge graph.
- Location: `harness/project.toml` (`[instance]`, `[[languages]]`, `[[components]]`, `[pipeline]`),
  `workspace.toml` (`[workspace]`, `[[members]]`, `[pipeline]`), `tools/harness_config/loader.py`,
  `tools/workspace_config/loader.py`.
- Contains: Stdlib `tomllib`-read TOML; zero enforcement logic.
- Depends on: Nothing (leaf data).
- Used by: `.github/workflows/ci.yml` (`setup` job derives the language test matrix from it), the
  GEN-03/MREPO-01 consistency-gate tests, `tools/golden_runner.workspace_golden_case`, `tools/
  contract_drift.workspace_drift`.

**Instance (`examples/log-parser/`, secondary/reference only):**
- Purpose: A concrete domain seed (semiconductor equipment-log parsing) proving the core harness
  works end-to-end; not itself part of the reusable core.
- Location: `examples/log-parser/{agents,components,contracts,golden,libs,skills,tests}/`,
  `examples/log-parser/project.toml`.
- Contains: `.NET` converter project (`components/toy-converter`, `libs/dotnet`), instance-specific
  contracts/golden/skills/agents.
- Depends on: The core (`tools/`, `libs/python`, `harness/` mechanics).
- Used by: Nothing in the core — the GEN-04 guard test
  (`tools/harness_lint/tests/test_core_no_example_dep.py`) proves this is a one-directional
  dependency by scanning every tracked core file for `examples/` path references, `import examples`,
  and a narrow set of GEN-05 domain-prose tokens.

## Data Flow

### Single-source → dual-runtime emit path

1. Author edits an artifact under `harness/agents/*.md`, `harness/commands/*.md`, or
   `harness/skills/*/SKILL.md` (or the shared `harness/opencode.json` /
   `harness/permission-matrix.json`).
2. `python -m tools.harness_emit` runs (`tools/harness_emit/__main__.py` → `generate.main()`).
3. **Discovery**: `iter_agents`/`iter_commands`/`iter_skills` glob `harness/{agents,commands,
   skills}/` non-recursively (so `agents/templates/*.md` scaffolds are excluded) and parse
   frontmatter via the shared `tools.harness_lint.parse_frontmatter` (`tools/harness_emit/
   generate.py:143-194`).
4. **Validate-then-write**: every artifact and its per-runtime projection is validated by
   `tools/harness_emit/validate.py` BEFORE any file is written — a single cap/shape violation
   aborts the whole emit with nothing written (`tools/harness_emit/generate.py:340-370`).
5. **Projection**: `tools/harness_emit/project_agent.py::to_opencode/to_claude` (and the
   command/skill equivalents) reshape frontmatter per runtime (e.g. opencode's `permission` object
   vs Claude's tool-allowlist convention).
6. **Deterministic render**: `render_markdown()` emits a DERIVED-marker comment as the first
   frontmatter line, a fixed key order (bash sub-object keeps AUTHORED insertion order — last-wins
   glob semantics), LF-normalized body — so re-running produces byte-identical output
   (`tools/harness_emit/generate.py:117-137`).
7. **Path confinement + write**: every target path is `_confine`d under its runtime root before
   writing (`tools/harness_emit/generate.py:58-64`); agents/commands/skills/plugin `.ts` files
   (byte-for-byte copy, never parsed) are written to both `.opencode/` and `.claude/`.
8. **opencode.json**: the ONE genuine transform — `build_opencode_config()` takes authored
   `harness/opencode.json` and replaces its partial `permission` block with the full 15-key block
   projected from `harness/permission-matrix.json` (`tools/harness_emit/generate.py:200-213`).
9. **Regime-B merges**: the HARNESS-MANAGED block in root `AGENTS.md`/`CLAUDE.md` is spliced (not
   template-overwritten) via `merge.splice_managed_block`; `.claude/settings.json` hook groups are
   signature-merged (append-or-replace only the harness-owned groups, never GSD hooks) via
   `merge.merge_settings` (`tools/harness_emit/generate.py:270-318`).
10. **Ownership manifest**: `tools/harness_emit/manifest.py::prune_then_write` writes
    `tools/harness_emit/emit-manifest.json` — the full set of emitter-owned paths, pruned of
    stale entries.
11. **CI `emit-drift` gate**: re-runs the same emit and `git diff --exit-code` over every emitted
    path; any hand-edit to `.opencode/**`, `.claude/{agents,commands,skills}/**`, `opencode.json`,
    `AGENTS.md`, `CLAUDE.md`, or `.claude/settings.json` fails the build
    (`.github/workflows/ci.yml`, `emit-drift` job).

### Contract-drift gate path

1. `contracts/**/*.schema.json` is edited (constitution plane — human-gated write).
2. `tools/contract_hash/hash.py::build_manifest` canonicalizes each schema with RFC 8785 (JCS,
   via the `rfc8785` package) and SHA-256s the canonical bytes.
3. `python -m tools.contract_hash.hash --write` updates the committed baseline
   `contracts/.hashes/manifest.json`.
4. `tools/contract_drift/drift.py::run_gate` recomputes the live manifest and diffs it against the
   baseline (`diff_manifests`), splitting into changed/added/removed.
5. Each `changed` schema is classified `breaking` vs `non-breaking` by `classify()` — indexing both
   old (`git show HEAD:...`) and new schema documents into `(const/enum/required/prop)` constraints
   and comparing (`tools/contract_drift/drift.py:50-110`).
6. `bash tools/contract_drift/check.sh` (or `python -m tools.contract_drift.drift`) exits non-zero
   on any drift, printing the rebaseline command and requiring it be "paired with a golden/ADR
   update (CODEOWNERS-gated)".
7. `--workspace` mode (`workspace_drift`) extends this per-declared-member (via `workspace.toml`)
   plus resolves every cross-repo pipeline edge's contract in its producer member.
8. CI mirrors this in the `drift` job (root + example manifests) and the `workspace` job
   (`--workspace` flag).

### Golden equivalence path

1. `tools/golden_runner/runner.py::run_golden_case(case, out_path)` resolves the seed
   (`golden/<case>/input/seed.tsv`).
2. The converter is spawned over the A-model boundary: `run_converter` calls
   `subprocess.run([dotnet_exe, "run", "--project", ..., "--", "--in", seed, "--out", out_path],
   shell=False)` — never a string+shell call, never an in-process object pass
   (`tools/golden_runner/runner.py:182-227`). A converter-agnostic `run_identity_converter`
   (pure stdlib byte-copy) serves as the template's generic, .NET-free default.
3. The runner reads the converter's `--out` FILE (the boundary is a file, not stdout).
4. `compare()` normalizes BOTH the new output and the approved
   `golden/<case>/expected/baseline.verified.tsv` via the shared `libs/python/normalize.core
   .normalize_tsv` — never a raw byte-diff (`tools/golden_runner/runner.py:116-156`).
5. Equal → PASS. Different → FAIL, and the RAW converter output is written to
   `golden/<case>/expected/baseline.received.tsv` — `.verified.tsv` is NEVER touched by the runner.
6. Promotion is a separate, explicit, human-gated step: `python -m tools.golden_runner.approve
   --approve --adr <id>` (`tools/golden_runner/approve.py`) — the only path that moves
   `.received.tsv` → `.verified.tsv`.
7. CI's `golden` job runs both the root identity case (`.NET-free`) and the example's `.NET` golden
   parity suite with a real .NET 10 SDK installed.

### SessionStart injection path (derived plane → agent context)

1. `tools/memory_regen/inject.py::assemble()` is the ONE payload source for both runtimes.
2. Priority order (capped ~1k tokens / 4000 chars, priority-truncated from the bottom, never
   mid-line cut): (0) provisional banner (never dropped) → (1) live drift summary (via
   `tools.contract_drift.run_gate`, never dropped) → (2) contracts-index head → (3) repo-map top-N
   → (4) `.memory/state/activeContext.md` POINTER (path + one-line note, never the file body).
3. Claude Code: `.claude/hooks/memory-inject.sh` wraps stdout in
   `{hookSpecificOutput:{additionalContext}}` (non-ignorable SessionStart injection).
4. opencode: `harness/plugins/session-inject.ts` shells out to the same
   `python -m tools.memory_regen.inject` module from a `chat.system.transform` hook (authored,
   deferred wiring).

**State Management:** No application runtime state. "State" here means the derived/committed memory
planes described above; `.memory/state/activeContext.md` and `.memory/state/progress.md` are the
only mutable, agent-authored, git-committed state, and both are explicitly documented as
provisional/overridable by the constitution plane.

## Key Abstractions

**Constitution plane vs Derived plane vs State plane:**
- Purpose: Encode which files are human-owned truth (never agent-written), which are
  machine-regenerated (never hand-edited), and which are agent-authored volatile hints
  (provisional, constitution always wins).
- Examples: `contracts/**`, `docs/adr/**`, `golden/**` (constitution); `.memory/derived/*.md`,
  `docs/reference/**` (derived); `.memory/state/*.md` (state).
- Pattern: Declared in `.memory/README.md` (a table) and the `two-plane-memory` skill
  (`harness/skills/two-plane-memory/SKILL.md`); enforced at runtime by
  `tools/hooks/contract_guard.py` (deny-by-default constitution writes) and at CI time by the
  `stale-derived` job (regenerate + diff).

**A-model polyglot boundary (process/file/DB only):**
- Purpose: Guarantee .NET and Python components never share in-process objects; every
  cross-language interaction is a CLI spawn with explicit exit codes and file I/O.
- Examples: `tools/golden_runner/runner.py::run_converter` (subprocess spawn + `--out` file read),
  `tools/bootstrap/install.sh` (installs the .NET 10 SDK the spawn resolves via
  `resolve_dotnet()` — `$DOTNET_ROOT/dotnet` or `$HOME/.dotnet/dotnet`, never a bare PATH lookup).
- Pattern: Documented in the `polyglot-boundary` skill
  (`harness/skills/polyglot-boundary/SKILL.md`) and enforced structurally — the core ships no
  in-process .NET/Python bridge of any kind.

**Config-as-data SSOT slot (GEN-03 / MREPO-01):**
- Purpose: Let a downstream fork swap languages/instances/workspace members by editing pure TOML
  data, with zero enforcement logic embedded in the data file itself — consistency is a separate,
  explicit gate.
- Examples: `harness/project.toml` (`[instance]`, `[[languages]]`, `[[components]]`, `[pipeline]`),
  `workspace.toml` (`[workspace]`, `[[members]]`, `[pipeline]`).
- Pattern: A thin stdlib `tomllib` loader (`tools/harness_config/loader.py`,
  `tools/workspace_config/loader.py`) with zero validation; a SEPARATE pytest consistency-gate file
  (`tools/harness_lint/tests/test_language_config.py`,
  `tools/harness_lint/tests/test_pipeline_config.py`,
  `tools/harness_lint/tests/test_workspace_config.py`) asserts the data agrees with dependent
  artifacts (permission-matrix bash scopes, personas, CI matrix legs).

**Ownership manifest (emit provenance):**
- Purpose: Track exactly which generated paths the emitter owns, so re-emission can prune stale
  artifacts and CI's `emit-drift` job knows the full diffable path set.
- Examples: `tools/harness_emit/emit-manifest.json` (the committed baseline — a flat sorted list of
  85 paths under `.claude/` and `.opencode/` plus root `opencode.json`).
- Pattern: `tools/harness_emit/manifest.py::prune_then_write` — write the CURRENT written-path set,
  removing entries no longer produced (e.g. a deleted skill's files disappear from both the tree
  and the manifest on the next emit).

**Loud-fail validation (validate-then-write):**
- Purpose: Never leave the repo in a half-written state on a cap/shape violation.
- Examples: `tools/harness_emit/validate.py::check_agent/check_command/check_skill` (raises before
  any write occurs); `tools/harness_emit/generate.py::emit()` runs ALL validation for ALL artifact
  types before the first `write_text` call.
- Pattern: A typed exception (`HarnessEmitError`, mirroring `DocsSyncError`) raised eagerly; the
  caller (CLI) surfaces it and exits non-zero, never partially emitting.

## Entry Points

**Harness emitter:**
- Location: `python -m tools.harness_emit` (`tools/harness_emit/__main__.py` → `generate.main`).
- Triggers: Manual run after editing `harness/**`; CI `emit-drift` job.
- Responsibilities: Emit agents/commands/skills/plugins/config to `.opencode/` + `.claude/`, splice
  shared `AGENTS.md`/`CLAUDE.md` managed blocks, merge `.claude/settings.json` hook groups, write
  the ownership manifest.

**Contract-drift gate:**
- Location: `python -m tools.contract_drift.drift` (also `bash tools/contract_drift/check.sh`).
- Triggers: `/contract-check` command, pre-commit hook, CI `drift`/`workspace` jobs.
- Responsibilities: Recompute live JCS-SHA256 manifest, diff vs committed baseline, classify
  breaking/non-breaking, exit non-zero on any drift.

**Golden runner:**
- Location: `python -m tools.golden_runner.runner <case> [--out PATH]`.
- Triggers: `/golden` command, CI `golden` job.
- Responsibilities: Run one golden equivalence case end-to-end (spawn converter → normalize →
  diff → PASS/FAIL + `.received.tsv`).

**Golden approve (human-gated promotion):**
- Location: `python -m tools.golden_runner.approve --approve --adr <id>`.
- Triggers: `/golden-approve` command, only after a human reviews a `.received.tsv` diff.
- Responsibilities: The ONLY code path that promotes `.received.tsv` → `.verified.tsv`.

**Derived-memory regeneration:**
- Location: `python -m tools.memory_regen.repo_map`, `python -m tools.memory_regen.contracts_index`,
  `python -m tools.docs_sync`, `python -m tools.memory_regen.inject`.
- Triggers: `/refresh-memory` command, CI `stale-derived` job, SessionStart hooks.
- Responsibilities: Regenerate `.memory/derived/repo-map.md`, `.memory/derived/contracts-index.md`,
  `docs/reference/**`, and assemble the SessionStart injection payload.

**Toolchain bootstrap:**
- Location: `tools/bootstrap/install.sh`, `tools/bootstrap/verify.sh`.
- Triggers: SessionStart hook in an ephemeral container (env ships no .NET).
- Responsibilities: Idempotently install .NET 10 SDK to `$HOME/.dotnet`, `uv sync --all-packages`
  the Python workspace; `verify.sh` is the strict read-only green-gate assertion.

**PreToolUse/PostToolUse hooks:**
- Location: `tools/hooks/contract_guard.py` (constitution-plane write gate),
  `tools/hooks/format_on_write.py` (byte-hygiene auto-fix), `tools/hooks/secret_scan.py`,
  `tools/hooks/commit_gate.py`.
- Triggers: opencode `tool.execute.before/after` hooks (via `harness/plugins/*.ts`, wiring
  deferred to opencode runtime), Claude Code `.claude/settings.json` hook groups (signature-merged
  by the emitter).
- Responsibilities: Deny agent writes to `contracts/**`/`docs/adr/**`/`golden/**` unless a human
  `GOLDEN_APPROVE_HUMAN` token is present; auto-fix BOM/CRLF on write elsewhere; scan for secrets;
  gate commits.

## Architectural Constraints

- **No shared runtime process.** There is no long-running server; every tool is a standalone CLI
  invoked as `python -m tools.<name>` (or a `.sh` script), designed to be called from an agent
  session, a git hook, or CI. Nothing in `tools/` holds in-process state across invocations.
- **Cross-language boundary is process/file/DB only** — never in-process object passing. This is a
  repo-wide non-negotiable (root `AGENTS.md` rule 2) and is structurally enforced: the golden
  runner's `run_converter` always uses `subprocess.run([...], shell=False)` plus a `--out` file, and
  no code anywhere imports a .NET assembly from Python or vice versa.
- **No shell string interpolation.** Every `subprocess.run` call in `tools/` uses an argv list
  (`shell=False`); CI workflow `run:` steps never interpolate `${{ github.event.* }}` (only
  repo-owned data from `harness/project.toml` / computed `needs.*.result` enums).
- **One-directional core→instance dependency.** `tools/`, `harness/`, `libs/` (core) must never
  import, path-reference, or carry the domain prose of `examples/**` (any instance). This is
  proven, not just documented, by `tools/harness_lint/tests/test_core_no_example_dep.py`, which
  scans every git-tracked core file for `examples/` path tokens, `import examples`, and a narrow
  GEN-05 prose-token list, with negative-control tests proving the scanner is live (not silently
  no-op'd). The single sanctioned exception is the `root =` / `persona =` / `test_paths =`
  instance-pointer lines in `harness/project.toml` (ADR-0002 (c)).
- **Path confinement on every write.** Both the emitter (`_confine` in
  `tools/harness_emit/generate.py`) and the golden runner (`_confine` in
  `tools/golden_runner/runner.py`) resolve and verify every write target stays under an allowed
  root (repo root, system temp, or an additive `allowed_roots` widening for workspace members)
  before writing — a path escaping confinement raises loudly instead of writing outside the repo.
- **Determinism is load-bearing, not cosmetic.** The emitter and `docs_sync` both forbid
  `datetime.now()`/floats/non-deterministic ordering in generated output, because CI's
  `emit-drift` and `stale-derived` jobs assert "regenerate == committed" via `git diff
  --exit-code`; any non-determinism would make those gates permanently red or silently
  ineffective.
- **Global state:** None beyond the two committed `.memory/state/*.md` files, which are explicitly
  documented as provisional agent-authored hints (not source of truth).
- **Golden baseline plane never machine-written.** `golden/**/expected/baseline.verified.tsv` is
  written exactly once, by a human running `/golden-approve`; every automated code path (runner,
  hooks) can only produce `baseline.received.tsv` alongside it.

## Anti-Patterns

### Hand-rolling normalization logic instead of reusing `libs/python/normalize/core.py`

**What happens:** A new hook, linter, or converter twin reimplements BOM stripping, decimal
formatting, or timezone canonicalization locally instead of importing the shared core.
**Why it's wrong:** The whole point of the §4.3–4.6 rule set (documented in
`libs/normalize-spec.md`) is ONE engine reused by every call site (golden runner, polyglot linter,
hooks); a second implementation can silently drift and defeat the golden-equivalence guarantee —
explicitly called out as the "RESEARCH anti-pattern" in `tools/polyglot_lint/lint.py`'s docstring.
**Do this instead:** Add the `_LIBS_PYTHON` sys.path shim (see `tools/golden_runner/runner.py:28-34`
or `tools/polyglot_lint/lint.py:24-27`) and import from `normalize.core` directly.

### Template-overwriting shared human/GSD files instead of splicing the managed block

**What happens:** A change to the emitter fully rewrites `AGENTS.md`, `CLAUDE.md`, or
`.claude/settings.json` instead of only touching the HARNESS-MANAGED fenced region.
**Why it's wrong:** These files also carry human-authored prose (nearest-wins rules, GSD's
`## Project` block, non-harness hook groups) that must survive re-emission untouched — a full
overwrite silently destroys that content (flagged as "Pitfall 2" / threat T-07-02 in
`tools/harness_emit/generate.py`).
**Do this instead:** Use `merge.splice_managed_block` (Markdown fenced block) or
`merge.merge_settings` (order-preserving, signature-scoped JSON merge) — read current on-disk
content, replace ONLY the owned region, write back.

### Silently auto-blessing a golden diff or contract change

**What happens:** Code path writes directly to `golden/**/baseline.verified.tsv` or edits
`contracts/**`/`docs/adr/**` without going through the human-gated command.
**Why it's wrong:** Violates the "machines gate, humans ratify" invariant (root `AGENTS.md` rule 3,
`tools/hooks/contract_guard.py`); an agent that self-blesses a baseline defeats the entire
contract-first safety model this harness exists to enforce.
**Do this instead:** Golden mismatches always write `.received.tsv` beside the untouched
`.verified.tsv` (`tools/golden_runner/runner.py::compare`); promotion is only
`python -m tools.golden_runner.approve --approve --adr <id>`, and constitution writes require a
human-set `GOLDEN_APPROVE_HUMAN` env token.

## Error Handling

**Strategy:** Typed, loud-fail exceptions raised eagerly (before partial writes), non-zero exit
codes as the primary machine-readable failure signal, human-actionable remediation text printed to
stderr alongside every gate failure.

**Patterns:**
- Custom exception classes per tool (`HarnessEmitError`, `GoldenRunnerError`, `StranglerRefused`,
  `GoldenApprovalRefused`) rather than bare `Exception`/`assert`.
- CLI `main()` functions return an `int` exit code (0 pass / 1 fail / occasionally 3 for an
  explicit refusal like `strangler_guard`), never `sys.exit()` scattered through library code — the
  `if __name__ == "__main__": raise SystemExit(main())` idiom is uniform across `tools/*/[generate|
  runner|drift].py`.
- Gate CLIs print a remediation hint on failure (e.g. contract_drift's rebaseline command, the
  `stale-derived` job's `/refresh-memory` pointer) so a human/agent knows the exact next command.
- `tools/memory_regen/inject.py::_drift_summary` degrades gracefully (`except Exception: return
  "...unknown (gate unavailable)"`) since the SessionStart payload must never crash a session.

## Cross-Cutting Concerns

**Logging:** No structured logging framework; tools print human-readable status lines to
stdout/stderr (`print(...)`) — this is a CLI-tool codebase, not a service, so stdout/stderr plus
process exit code IS the interface.

**Validation:** JSON Schema Draft 2020-12 (`check-jsonschema`) validates every contract instance
against its schema; `tools/harness_emit/validate.py` validates emitted-artifact shape/caps;
`tools/harness_lint/frontmatter.py` provides one shared frontmatter parser reused by both the
emitter and lint tests (never re-sliced ad hoc).

**Authentication/Authorization:** N/A at the application level (no users/sessions). The nearest
analogue is the permission-matrix access-control model (`harness/permission-matrix.json` →
`tools/harness_perms/resolver.py`): a 15-key allow/ask/deny matrix plus insertion-ordered
last-wins bash globs plus `path_deny_globs` for the constitution/secret planes, enforced by
PreToolUse hooks and gated by an env-var human-approval token for constitution writes.

---

*Architecture analysis: 2026-07-14*
