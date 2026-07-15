# Phase 7: Single-Source Dual-Runtime Emitter - Research

**Researched:** 2026-07-12
**Domain:** Deterministic codegen (single authored source → two runtime-native artifact trees), idempotent managed-block merge, re-emit-diff drift gating
**Confidence:** HIGH (the emitter is a pure function of an in-repo source whose format, validators, and analog tooling all already exist and were read directly this session)

## Summary

Phase 7 builds `tools/harness_emit/` — a Python tool that reads the runtime-neutral authored source under `harness/` and writes two runtime-native artifact trees: `.opencode/` (primary) and the harness slice of `.claude/` (secondary), plus the shared config/marker files (`opencode.json`, `AGENTS.md`, `.claude/settings.json`, `CLAUDE.md`). Critically, this is **not** a research-heavy phase: the source format, the per-runtime caps, the determinism discipline, and the drift-gate archetype **all already exist in the repo** and were inspected directly. The emitter's real work is (1) projecting each source artifact's frontmatter into each runtime's shape, (2) owning only what it writes via an explicit manifest, and (3) merging managed blocks into human/GSD-shared files without clobbering.

The single most load-bearing discovery: **the `harness/` source is already dual-representation.** An agent like `harness/agents/python-engineer.md` carries BOTH the opencode keys (`mode: subagent`, a `permission:` block) AND the Claude key (`tools: Read, Edit, Bash, Grep, Glob`) in one frontmatter block. The existing validator `tools/harness_lint/tests/test_agents.py` explicitly checks "the read-only invariant holds in BOTH runtime representations." So the emitter is mostly a **projection/selection** of frontmatter keys per target plus file placement — not a transpiler. The one genuine transform is `harness/permission-matrix.json` → `opencode.json`'s 15-key `permission` block.

The determinism + drift-gate pattern is fully precedented by `tools/docs_sync/` (a codegen-from-source tool: `rows → render → write → main`, DERIVED header, sorted keys, no timestamps/floats, byte-identical delete+regenerate, proven by a committed syrupy snapshot) and by `tools/contract_drift/` (recompute → compare-to-committed-baseline → non-zero exit on drift). Phase 7 extends exactly these: emit deterministically, commit the output, and add one CI job that re-emits and runs `git diff --exit-code` on the generated paths.

**Primary recommendation:** Build `tools/harness_emit/` as a virtual uv-workspace member cloning the `tools/docs_sync/` structure and determinism discipline; reuse `tools/harness_lint.parse_frontmatter` (the shared reader) and the existing agent/command/skill/opencode validators as the emit-time gate; own emitted whole-files via a committed JSON manifest; merge managed blocks into `AGENTS.md`/`CLAUDE.md` via HTML-comment marker fences and into `.claude/settings.json` via signature-matched hook-group replacement; deliver the agents-only walking slice first (D-05), then expand commands → skills → plugins(verbatim) → config/marker merges.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 Emitter language = Python** (`tools/harness_emit/`). Consistent with every existing `tools/*` (harness_config / contract_drift / golden_runner), and folds naturally into CI. **`.ts` plugins are VERBATIM COPIED** to `.opencode/plugin/`, NOT generated — no Node toolchain. (The CLAUDE.md stack-table Node/adapters suggestion is deliberately NOT adopted: the source is already Markdown+TS, so there is nothing to transpile.)
- **D-02 Emit outputs are COMMITTED + re-emit-diff drift gate (most important).** `.opencode/` and the emitted `.claude/{agents,commands,skills}` (plus the `opencode.json`/`AGENTS.md`/`settings.json`/`CLAUDE.md` managed blocks) are committed, so success criterion 4 (CI re-emits and fails on diff) holds. Extend the Phase-6 `tools/contract_drift` / CI gate pattern verbatim. Outputs are "do-not-hand-edit derivatives" but **machine-written, CI-verified** — not a two-plane violation. (v2-α later reuses this pattern for the whole derived plane.)
- **D-03 `.claude/` GSD coexistence = manifest-owned + merge.** The emitter owns ONLY an explicit manifest of files it wrote; it **never touches** `gsd-*` files, `.claude/get-shit-done/`, or `.claude/hooks/` (GSD-owned). Namespace harness artifacts to avoid `gsd-` collision. `settings.json` / `CLAUDE.md` / `AGENTS.md` = managed-marker-block MERGE, not overwrite (preserve GSD/human content).
- **D-04 Source is runtime-neutral; the emitter is the sole specialization point.** `harness/` frontmatter stays runtime-neutral; the emitter specializes via one mapping table — opencode (`mode: subagent`, `permission-matrix.json` → `opencode.json` 15-key), Claude (`.claude/*` + `settings.json`). Do not bake runtime shape into the source.
- **D-05 MVP slice = agents first.** Walking skeleton: the 4 agents pass source → both runtimes → validators → CI diff end-to-end (exercising frontmatter mapping + validators + drift gate), THEN expand commands → skills → plugins → settings.

### Claude's Discretion
- Emitter internal module split, mapping-table detail, manifest format, merge-marker syntax, validator placement (emit-time AND CI both), CI job name — all researcher/planner discretion.
- **FIXED (not negotiable):** Python emitter · committed outputs + drift gate · GSD untouched/merge · runtime-neutral source · agents-first MVP · no model identifiers in any emitted artifact.

### Already Confirmed (✔)
- Target path/file sets (In-scope list), validators loud-fail, `.claude/get-shit-done/` untouched, wshobson single-source→adapter pattern.

### Deferred Ideas (OUT OF SCOPE)
- Multi-repo / workspace emit → v2-γ
- Curator auto-refresh of derived artifacts (hook) → v2-α
- opencode runtime live-execution validation → after opencode is installed (this phase validates STRUCTURE/loadability only; opencode is not installed in this container)
- Example-domain content emit (`examples/` is separate; the harness itself is what gets emitted)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EMIT-01 | The canonical harness source format (`harness/`) — single source for agents/commands/skills/plugins | §"Input Contract" documents the exact authored format of every artifact type as it exists today; the source is already dual-representation and runtime-neutral (D-04 holds by construction). No source format change needed — Phase 7 consumes it as-is. |
| EMIT-02 | The emitter — generate opencode (primary) + Claude Code (`.claude/`) artifacts from source; per-runtime constraint validators loud-fail (skill size caps etc.) instead of truncating | §"Mapping Table", §"Validator Architecture", §"Manifest + Managed-Block Merge", §"Re-Emit-Diff Drift Gate", §"Test Strategy". Validators reuse the existing `tools/harness_lint` cap gates; loud-fail = raise/abort-before-write (never truncate). |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Read authored source (`harness/**`) | Build tool (`tools/harness_emit`) | — | Pure file I/O; reuses `tools.harness_lint.parse_frontmatter` (the one shared reader) |
| Project frontmatter per runtime | Build tool | — | The sole specialization point (D-04); a mapping table, not runtime logic |
| Write `.opencode/**` + `opencode.json` + root `AGENTS.md` | Build tool → opencode runtime consumes | opencode runtime (deferred) | opencode is the primary deploy target; not installed here, so structural validation only |
| Write `.claude/{agents,commands,skills}` + merge `settings.json`/`CLAUDE.md` | Build tool → Claude Code runtime consumes | Claude Code runtime | Secondary target; must coexist with GSD assets already living in `.claude/` |
| Verbatim-copy `.ts` plugins → `.opencode/plugin/` | Build tool | opencode runtime (deferred) | D-01: no Node toolchain; the `.ts` is authored source, not codegen output |
| Per-runtime cap/shape validation | Build tool (emit-time) + CI | — | Loud-fail gate; reuses existing `tools/harness_lint` validators |
| Re-emit-diff drift gate | CI (GitHub Actions) | pre-commit (optional) | Extends the `tools/contract_drift` / Phase-6 CI archetype (D-02) |
| Ownership boundary vs GSD | Build tool (manifest) | — | Manifest lists only emitted files; GSD/human files never touched (D-03) |

## Input Contract (EMIT-01 — the authored `harness/` source, as it exists today)

> Verified by direct read of every file this session. `[VERIFIED: codebase]`

### Source tree

```
harness/
├── agents/                     # 4 core personas → .opencode/agent + .claude/agents
│   ├── orchestrator.md         # mode: primary  (the conductor)
│   ├── python-engineer.md      # mode: subagent
│   ├── code-reviewer.md        # read-only (both representations)
│   ├── explorer.md             # read-only
│   └── templates/              # NOT emitted — persona-template scaffolds (engineer.md, component-engineer.md)
├── commands/                   # 18 command macros → .opencode/command + .claude/commands
│   └── *.md                    # frontmatter: description, agent, subtask
├── skills/                     # 9 core skills → .opencode/skill + .claude/skills
│   └── <name>/SKILL.md         # + optional references/ subtree (golden-debug, polyglot-boundary have one)
├── plugins/                    # 5 .ts plugins → VERBATIM COPY to .opencode/plugin (D-01)
│   └── *.ts
├── git-hooks/pre-commit        # source of the git commit-gate (installed manually, not emitted per se)
├── permission-matrix.json      # 15-key permission data → opencode.json permission block
├── opencode.json               # authored opencode config (model tiering, formatter, instructions, mcp, plugin)
├── opencode.config.schema.json # vendored subset schema for validating opencode.json (48 lines)
└── project.toml                # GEN-03 language/toolchain + PIPE-01 topology DATA slot
```

### Frontmatter schema per artifact type

**Agent** (`harness/agents/*.md`) — dual-representation, runtime-neutral:
```yaml
name: python-engineer                 # slug: ^[a-z0-9]+(-[a-z0-9]+)*$
description: >-                        # routing signal — must contain "use"/"when" trigger token
  Use when the scheduler ...
mode: subagent                         # opencode key: primary | subagent | all
permission:                            # opencode key: 15-key block (bash is insertion-ordered last-wins)
  read: allow
  edit: allow
  bash: { "*": ask, "uv *": allow, "pytest *": allow }
tools: Read, Edit, Bash, Grep, Glob    # Claude key: comma-joined tool allowlist
# model: provider/explorer-tier        # OPTIONAL — placeholder tier token ONLY (never a real model ID)
```
Body = the persona system prompt (Markdown).

**Command** (`harness/commands/*.md`):
```yaml
description: >-                         # routing signal (use/when trigger)
  Use when you need to compile ...
agent: orchestrator                     # slug of the persona that owns the command
subtask: true                           # boolean when present
```
Body = Markdown with opencode-style `` !`shell command` `` bash-execution lines and `$ARGUMENTS`/`$FILE` interpolation.

**Skill** (`harness/skills/<name>/SKILL.md`):
```yaml
name: data-contracts                    # slug; MUST equal parent dir name; ≤64 chars
description: >-                          # routing signal; ≤1024 chars; no reserved word (anthropic/claude); no <> chars
  Use when reading, changing ...
```
Body = progressive-disclosure Markdown; optional `references/*.md` subtree for depth.

**Plugin** (`harness/plugins/*.ts`): TypeScript ESM. Each carries a "RESUME NOTE — AUTHORED-ONLY, EXECUTION DEFERRED" banner and consumes a `tools.*` Python module via `execFileSync`. **Not parsed — copied byte-for-byte.**

**Config** (`permission-matrix.json`, `opencode.json`, `project.toml`): JSON/TOML DATA. `permission-matrix.json` has the 15 opencode keys + a `bash` insertion-ordered object (catch-all `*` FIRST, specifics after — last-wins glob, Pitfall P3) + a non-opencode `path_deny_globs` array + a leading `_note`.

### The 15 opencode permission keys `[VERIFIED: codebase tools/harness_lint/tests/test_agents.py]`
`read, edit, bash, glob, grep, list, task, external_directory, todowrite, question, webfetch, websearch, lsp, skill, doom_loop`. (`write` is NOT native — file writes fall under `edit`; `write` is tolerated only as an explicit defensive deny.)

## Mapping Table (EMIT-02 — the sole specialization point, D-04)

> The emitter selects/projects frontmatter keys per target and places files. Divergence is confined to this table.

| Source | opencode target | opencode frontmatter | Claude target | Claude frontmatter | Divergence |
|--------|-----------------|----------------------|---------------|--------------------|-----------|
| `agents/<n>.md` | `.opencode/agent/<n>.md` | keep `name, description, mode, permission` (opencode-native); `tools` optional | `.claude/agents/<n>.md` | keep `name, description, tools`; **drop** `mode` + `permission` block; keep `model` if present | opencode = `mode`+`permission` block; Claude = `tools` allowlist. Read-only invariant must survive BOTH projections. |
| `commands/<n>.md` | `.opencode/command/<n>.md` | keep `description, agent, subtask` | `.claude/commands/<n>.md` | keep `description`; map/drop `agent`+`subtask` (no Claude equivalent); body `` !`…` `` bash lines are shared | Claude commands have no `agent`/`subtask` concept. `!`-bash + `$ARGUMENTS` are supported by both. |
| `skills/<n>/SKILL.md` (+`references/`) | `.opencode/skill/<n>/SKILL.md` (+copy `references/`) | keep `name, description` | `.claude/skills/<n>/SKILL.md` (+copy `references/`) | keep `name, description` | **None** — same shape, same caps (name≤64, desc≤1024) both runtimes. |
| `plugins/*.ts` | `.opencode/plugin/*.ts` (verbatim copy) | n/a | **no Claude target** | n/a | Claude uses `settings.json` hooks, not `.ts` plugins. Plugins are opencode-only. |
| `permission-matrix.json` | merged into `opencode.json` `permission` (15-key) | n/a | (informs `.claude` tool allowlists only, not a file) | n/a | opencode has a native permission matrix; Claude expresses affordance via per-agent `tools`. |
| `opencode.json` + matrix | root `opencode.json` (emitter owns wholesale) | n/a | — | n/a | opencode-only config file. |
| (whole surface) | root `AGENTS.md` (opencode reads it) — **managed-block merge** | n/a | `CLAUDE.md` (pointer) — **managed-block merge** + `.claude/settings.json` (hook wiring) — **signature merge** | n/a | Shared/human files — merge, never overwrite (D-03). |
| — | `.opencode/tool/` | — | — | — | **No `tool` source authored today.** Emit an empty dir or skip; opencode custom tools (`.ts`) can be added later. Flag as open. |

### opencode dir naming (singular vs plural)
ROADMAP success criterion 1 and CLAUDE.md both specify **singular** paths: `.opencode/{agent,command,skill,plugin,tool}` and `.opencode/agent/<name>.md`. One WebSearch source referenced `.opencode/agents/` (plural). **Follow the ROADMAP/CLAUDE.md singular convention** (the phase's declared target and opencode's documented convention); re-confirm against the installed opencode version before the first live run. `[CITED: ROADMAP §Phase 7 + CLAUDE.md]` / `[ASSUMED: singular is current opencode convention]`

## Manifest + Managed-Block Merge (D-03)

Two ownership regimes. The emitter must distinguish them.

### Regime A — whole-file ownership (manifest-pruned)
Applies to: `.opencode/{agent,command,skill,plugin}/**`, `.opencode/opencode.json`, `.claude/{agents,commands,skills}/**` (the harness slice only).

- The emitter writes a committed **manifest** (recommend `tools/harness_emit/emit-manifest.json`, or two per-tree manifests `.opencode/.harness-manifest.json` + a `.claude` equivalent) listing every relative path it owns, with the emit tool version.
- **Prune-then-write:** on each run, delete files listed in the PREVIOUS manifest that are no longer emitted, then write the current set. This keeps re-emit idempotent (a renamed/removed source artifact doesn't leave an orphan) while **never** enumerating or touching non-manifest paths.
- **GSD safety:** the emitter's target globs must exclude `gsd-*`, `.claude/get-shit-done/**`, `.claude/hooks/**`, `.claude/commands/gsd/**`. Harness agents (`orchestrator`, `python-engineer`, `code-reviewer`, `explorer`) carry no `gsd-` prefix, and GSD agents are all `gsd-*` → **no name collision** in `.claude/agents/`. Harness commands emit to `.claude/commands/*.md` (top level); GSD commands live under `.claude/commands/gsd/` → **no collision**. Verify this non-collision as a test.

### Regime B — managed-block merge (shared human/GSD files)
Applies to: root `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`.

- **Markdown files (`AGENTS.md`, `CLAUDE.md`)** — HTML-comment marker fences (invisible when rendered):
  ```markdown
  <!-- BEGIN HARNESS-MANAGED (generated by tools.harness_emit — do not hand-edit) -->
  ...emitted block...
  <!-- END HARNESS-MANAGED -->
  ```
  Replace ONLY the content between markers; content outside is preserved verbatim. If markers are absent, append the block once (idempotent thereafter). This is a well-understood idempotent pattern; hand-roll it as a small string splice (no external "managed block" lib needed for two markers).
- **JSON file (`.claude/settings.json`)** — JSON cannot hold comment markers. **Recommended: signature-matched hook-group replacement.** The emitter knows the deterministic set of harness-owned hook commands (`tools.hooks.format_on_write`, `tools.hooks.contract_guard`, `tools.hooks.secret_scan`, `tools.hooks.commit_gate`, `tools/bootstrap/install.sh`, `.claude/hooks/memory-inject.sh`). Merge = parse JSON → remove any hook group whose command matches a harness signature → re-insert the harness groups in deterministic order → write with **order-preserving** serialization `json.dumps(merged, indent=2, ensure_ascii=False) + "\n"` (**NO `sort_keys=True`** — the live `.claude/settings.json` is authored `SessionStart`-first and inner-key order is not alphabetical, so a global key-sort would produce a ~274-line Day-1 false-positive drift; see Regime B-json in 07-05-PLAN.md and the two-serialization-regime distinction). GSD hook groups (matched by `gsd-*` command substrings) are never removed or reordered. This needs **no schema-polluting sentinel key** (safer than injecting `"_source"` fields that a Claude settings validator might reject — MEDIUM confidence on unknown-key tolerance, so avoid it).
  - **Coexistence nuance (IMPORTANT):** the harness hook entries + `memory-inject.sh` are ALREADY hand-wired into `.claude/settings.json`/`.claude/hooks/` by Phases 2 and 4 and are covered by `tools/memory_regen/tests/test_hook_wiring.py` (asserts exactly 4 SessionStart groups, 3 GSD survive). The Phase-7 settings merge must be **idempotent with respect to what Phase 2/4 already committed** — re-emitting must reproduce the existing file byte-for-byte (or the plan must consciously migrate that wiring under emit ownership and update `test_hook_wiring.py`). Decide this explicitly in planning; do not silently double-wire.

### Idempotency requirements (mirror §4.3–4.6 canonicalization)
Every write must be deterministic so re-emit is byte-identical (the drift gate depends on it):
- **LF** line endings, **no BOM**, UTF-8 (§4.3).
- **Sorted keys** in emitted JSON that the emitter OWNS wholesale (`opencode.json` and any emitter-authored JSON): `json.dumps(sort_keys=True)`; preserve authored key order only where semantically required (the `bash` last-wins matrix — emit its keys in the AUTHORED insertion order, NOT sorted, because order is semantic; document this exception). **Exception — Regime B managed-merge JSON (`.claude/settings.json`)**: order-preserving, NO `sort_keys` (see Regime B above), because that file is co-owned with Phase 2/4 wiring and must reproduce its existing bytes.
- **No `datetime.now()`, no timestamps, no raw floats** (Pitfall P12, exactly as `tools/docs_sync/generate.py` avoids them).
- Frontmatter re-serialization must be stable: prefer a fixed key order per artifact type rather than round-tripping ruamel (round-trip can reorder/reflow). Emit frontmatter from an explicit ordered template.

## Validator Architecture (EMIT-02 criterion 3 — loud-fail, never truncate)

**Reuse the existing caps — do NOT invent new ones.** They already live in `tools/harness_lint` and were read this session:

| Artifact | Rule | Severity | Source of truth |
|----------|------|----------|-----------------|
| Skill | `name` ≤64, slug regex, == dir name | HARD fail | `test_skills.py` `_NAME_MAX=64` |
| Skill | `description` ≤1024, no `<>`, no reserved word (anthropic/claude), has routing trigger | HARD fail | `test_skills.py` `_DESC_MAX=1024` |
| Skill | body >500 lines | **WARN only** (never reject) | `test_skills.py` `_BODY_WARN_LINES=500` (D-07) |
| Agent | `permission` keys ⊆ 15 valid keys | HARD fail | `test_agents.py` `VALID_PERMISSION_KEYS` |
| Agent | `mode` ∈ {primary, subagent, all} | HARD fail | `test_agents.py` `VALID_MODES` |
| Agent | read-only personas (code-reviewer, explorer) have no write/shell affordance in EITHER projection | HARD fail | `test_agents.py` `is_read_only` |
| Agent | `model`, if present, == `provider/explorer-tier` (no real model ID) | HARD fail | `test_agents.py` `test_no_real_model_identifier` |
| Command | `agent` well-formed slug; `subtask` boolean when present | HARD fail | `test_commands.py` |
| opencode.json | validates against `harness/opencode.config.schema.json` (vendored subset, hermetic) | HARD fail | `test_opencode_json.py` (uses `jsonschema`) |
| permission-matrix | 15-key shape; `bash` catch-all `*` FIRST (last-wins) | HARD fail | `permission-matrix.json` `_note` (Pitfall P3) |

**The ≤200 vs ≤1024 skill-description ambiguity is RESOLVED** to **1024** in-repo (`test_skills.py` comment: "the 200-vs-1024 correction"). Use 1024. `[VERIFIED: codebase test_skills.py]` (STATE.md line 159 flagged this to resolve at the emitter; it is resolved.)

**Loud-fail semantics:** run validators on the source (and on the projected output) **before any write**; on a HARD failure, raise a typed error (mirror `DocsSyncError`) and abort with a non-zero exit **writing nothing** — no partial/truncated tree. Do NOT truncate an over-cap description; fail and name the offending file. Body-over-500 emits a `warnings.warn`, not a failure (D-07). Placement: validators live in `tools/harness_emit/validate.py`, imported by (a) the emitter as a pre-write gate and (b) the emitter tests. Do NOT re-implement the caps a third time — import the constants or factor them into a shared module so a cap change lands in one place.

## Re-Emit-Diff Drift Gate (D-02, criterion 4 — extend `tools/contract_drift` archetype)

The mechanism is directly precedented:
- `tools/contract_drift/check.sh` = `exec uv run python -m tools.contract_drift.drift "$@"` (recompute → compare to committed baseline → non-zero exit on drift).
- The Phase-6 CI (`.github/workflows/ci.yml`) already runs `drift`, `golden`, `contract-check`, `core-suite`, a config-derived `lang-tests` matrix, and fans them into one `gate` job.

**Add ONE CI job** (recommend name `emit-drift`), structurally identical to the existing jobs:
```yaml
emit-drift:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v7.0.0
    - uses: astral-sh/setup-uv@v8.3.2
    - run: uv sync --all-packages
    - name: Re-emit the harness surface
      run: uv run python -m tools.harness_emit
    - name: Fail on any hand-edited generated-artifact drift
      run: git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json
```
Then add `emit-drift` to the `gate` job's `needs:` list so it is part of the non-bypassable fan-in.

**Why `git diff --exit-code` works on the merged files too:** because the managed-block merge is idempotent, re-emitting an already-correct `AGENTS.md`/`CLAUDE.md`/`settings.json` reproduces it byte-for-byte → clean diff. If a human hand-edited inside a managed block, re-emit overwrites it → dirty diff → fail (exactly the intended catch). If a human edited OUTSIDE the block, re-emit preserves it → clean diff (intended). This is the whole point of markers.

## Test Strategy (clone the `tools/docs_sync/tests/` idiom)

`tools/harness_emit/` = a **virtual uv-workspace member** (`package = false`, `dependencies = []`, `requires-python >=3.11`), invoked as `python -m tools.harness_emit`, mirroring `tools/docs_sync/pyproject.toml`. `conftest.py` puts the repo root on `sys.path` (`parents[3]`), exactly like `docs_sync/tests/conftest.py`.

`tools/harness_emit/tests/`:
- **`test_emit_determinism.py`** — (a) emit into `tmp_path` twice → sha256 per file identical; (b) emit → delete → regenerate → byte-identical (Pitfall P12); (c) a committed **syrupy snapshot** (`.ambr`) of the projected artifacts as the canonical determinism reference (proven WITHOUT git diff, like docs_sync). syrupy is already the workspace snapshot tool (`syrupy 5.2.0`, `pytest 8.4.x`).
- **`test_mapping.py`** — an agent projects correctly to BOTH targets: opencode output has `mode`+`permission` and NO Claude-only leakage; Claude output has `tools` and NO `permission` block; read-only invariant survives both.
- **`test_coexist.py`** — emit into a fixture `.claude/` seeded with `gsd-*` agents/commands + a GSD `settings.json` → every GSD file is byte-unchanged; manifest lists only harness paths; `settings.json` GSD hook groups survive and harness groups are present (extends the `test_hook_wiring.py` assertions).
- **`test_validators.py`** — an over-cap skill description / an invalid permission key / a non-boolean `subtask` → emitter **raises and writes nothing** (assert the tmp target tree is empty). A 600-line skill body → warns, still emits.
- **`test_manifest.py`** — manifest covers every emitted file; a stale harness file from a prior manifest is pruned; a `gsd-*` sibling is never pruned.
- **`test_merge_idempotent.py`** — managed-block splice into a `CLAUDE.md`/`AGENTS.md` fixture with human content before/after the block → human content preserved, block replaced, second run byte-identical.

Register the emit surface's expected file set the same way `test_skills.py`/`test_agents.py` pin `EXPECTED_SKILLS`/`EXPECTED_PERSONAS` (anti-drift on the emitted set).

## Recommended Project Structure

```
tools/harness_emit/
├── __init__.py
├── __main__.py            # python -m tools.harness_emit → main()
├── emit.py                # orchestration: read source → validate → project → write → manifest
├── project_agent.py       # frontmatter projection: agent → opencode / claude
├── project_command.py     # command projection
├── project_skill.py       # skill (+references) copy/projection
├── permissions.py         # permission-matrix.json → opencode.json permission block (15-key)
├── merge.py               # managed-block splice (md) + signature merge (settings.json)
├── manifest.py            # read/write/prune the ownership manifest
├── validate.py            # emit-time cap/shape gate (imports harness_lint caps)
├── pyproject.toml         # virtual member, deps = []
└── tests/
    ├── conftest.py
    ├── test_emit_determinism.py
    ├── test_mapping.py
    ├── test_coexist.py
    ├── test_validators.py
    ├── test_manifest.py
    └── __snapshots__/
```

### System flow

```
harness/ (authored, runtime-neutral, dual-representation)
    │  parse_frontmatter (shared reader, tools.harness_lint)
    ▼
[validate.py]  ── HARD fail → abort, write nothing (loud-fail, no truncate)
    │  (pass)
    ▼
[project_* / permissions / merge]  ── select keys per runtime (the ONLY specialization, D-04)
    ├─► .opencode/{agent,command,skill,plugin}/**  +  opencode.json  +  AGENTS.md (managed block)
    └─► .claude/{agents,commands,skills}/**  +  settings.json (signature merge)  +  CLAUDE.md (managed block)
    │  deterministic write (LF, no BOM, sorted keys, no timestamps)
    ▼
[manifest.py]  prune prior-owned orphans → write emit-manifest.json
    │
    ▼
CI: re-emit → git diff --exit-code (emit-drift job → gate fan-in)   [D-02, criterion 4]
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frontmatter parsing | Per-artifact fence slicing | `tools.harness_lint.parse_frontmatter` | The one shared reader; CRLF-safe, ruamel-safe-loader. Re-implementing risks divergent parsing. |
| Cap constants (64/1024/500, 15 keys, modes) | New literals in the emitter | Import from / share with `tools/harness_lint` | A cap defined twice drifts; the existing validators are the source of truth. |
| Determinism discipline | Ad-hoc serialization | Clone `tools/docs_sync/generate.py` (sorted keys, DERIVED header, no floats/timestamps) | Proven byte-identical; the drift gate depends on it. |
| Drift gate | New comparison harness | Extend `tools/contract_drift` + one CI job pattern | The re-emit→diff→fail archetype already exists and is wired into the `gate` fan-in. |
| Snapshot testing | Custom golden files | `syrupy` (already in the workspace, `.ambr`) | The repo's determinism-proof tool (docs_sync uses it). |
| TOML/JSON reading | New parsers | stdlib `tomllib` (`tools.harness_config.loader`) + stdlib `json` | Zero new deps; `requires-python >=3.11` guarantees `tomllib`. |
| Plugin transpile | A Node/TS build step | **Verbatim byte-copy** of `*.ts` | D-01: `.ts` is authored source, not codegen input. No Node toolchain. |

**Key insight:** Phase 7 adds almost no new machinery — it composes four existing, tested repo patterns (shared frontmatter reader, docs_sync determinism, harness_lint caps, contract_drift gate). The novel surface is small: frontmatter projection tables, the ownership manifest, and the managed-block merge. Keep those three thin and well-tested; reuse everything else.

## Common Pitfalls

### Pitfall 1: Truncating instead of failing on an over-cap skill
**What goes wrong:** emitter silently clips a >1024 description to fit, corrupting the artifact.
**Why:** naive "make it fit" defensiveness.
**Avoid:** HARD-fail before writing (criterion 3 is explicit). Body>500 is the ONLY soft case (warn), per D-07.
**Warning sign:** any `[:1024]` slice or `.truncate(` in the emitter.

### Pitfall 2: Overwriting `.claude/settings.json` / `CLAUDE.md` / `AGENTS.md`
**What goes wrong:** clobbering GSD hook wiring or human prose → breaks the GSD workflow the repo runs on.
**Why:** treating shared files like owned files.
**Avoid:** managed-block merge (markers for md, signature match for settings.json). Never full-write a shared file. `test_coexist.py` must assert GSD survival.
**Warning sign:** `settings.json` written from a template rather than merged into the parsed existing file.

### Pitfall 3: Non-deterministic emit → drift gate flaps
**What goes wrong:** ruamel round-trip reorders keys, or a timestamp leaks, so re-emit differs → CI red on unchanged source.
**Why:** serializing via round-trip instead of an explicit ordered template.
**Avoid:** fixed key order per artifact type; `json.dumps(sort_keys=True)`; no `datetime.now()`; LF/no-BOM. Exception: the `bash` last-wins matrix keeps AUTHORED order (order is semantic — sorting it would break the `*`-first invariant).
**Warning sign:** two consecutive `python -m tools.harness_emit` runs produce a git diff.

### Pitfall 4: Double-wiring the Phase 2/4 hooks
**What goes wrong:** Phase 7 re-emits harness hook groups that Phases 2/4 already committed into `settings.json`, producing 5+ SessionStart groups and breaking `test_hook_wiring.py` (expects exactly 4).
**Why:** the emitter and the earlier hand-wiring both claim the same entries.
**Avoid:** decide ownership explicitly — either the merge reproduces the existing wiring byte-for-byte (idempotent), or the plan migrates that wiring under emit ownership AND updates `test_hook_wiring.py` in the same wave.
**Warning sign:** SessionStart group count changes after emit.

### Pitfall 5: Emitting a real model identifier
**What goes wrong:** a projected agent/opencode.json carries a real provider model ID → violates the model-identity constraint.
**Why:** copying a `model:` value without the placeholder guard.
**Avoid:** the emit-time validator enforces `model == provider/explorer-tier` / `provider/implementer-tier` placeholders only (already checked by `test_agents.py`/`test_opencode_json.py`). Extend to emitted output.

### Pitfall 6: Assuming opencode dir names/hook APIs without verifying
**What goes wrong:** emitting `.opencode/agents/` (plural) or wiring a wrong hook event name; opencode later rejects it.
**Why:** opencode is not installed here; docs are proxy-403'd (STATE lines 158–159).
**Avoid:** follow ROADMAP/CLAUDE.md singular paths; validate STRUCTURE only this phase; carry a RESUME note to re-verify at first opencode install (mirrors the plugin stubs' existing banners).
**Warning sign:** a live opencode-load assertion in this phase (out of scope).

## Runtime State Inventory

> This is a rename/refactor-adjacent phase (it writes generated trees that coexist with GSD state), so the inventory applies.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — the emitter reads `harness/` and writes files; no datastore keys involved. Verified: no DB/collection references in the emit path. | none |
| Live service config | `.claude/settings.json` (GSD hook wiring + Phase 2/4 harness hooks) is live Claude Code config NOT fully in a template — the emitter must MERGE into it, not overwrite. `.claude/get-shit-done/`, `.claude/hooks/gsd-*`, `.claude/commands/gsd/` are GSD-owned live config. | signature-merge settings.json; exclude all `gsd-*`/get-shit-done/hooks from emit targets (D-03) |
| OS-registered state | None — no Task Scheduler / systemd / pm2 registrations embed emitted names. Verified: no such registrations in repo. | none |
| Secrets/env vars | None renamed. `GOLDEN_APPROVE_HUMAN` (commit-gate bypass) is referenced by hooks but not emitted/renamed by this phase. | none |
| Build artifacts | `.opencode/` does NOT exist yet (greenfield) — first emit creates it; must be added to git (committed, D-02) and NOT gitignored. `.claude/` harness slice is likewise first-created. Confirm `.gitignore` does not exclude `.opencode/` (currently it does not). | commit `.opencode/**` + `.claude/{agents,commands,skills}` harness slice; verify not gitignored |

**Existing `.gitignore` relevant lines:** only `.memory/derived/` and `.claude/settings.local.json` are ignored — `.opencode/` and the committed `settings.json` are tracked. `[VERIFIED: codebase .gitignore]`

## Package Legitimacy Audit

**No external packages are installed by this phase.** The emitter uses only stdlib (`json`, `tomllib`, `pathlib`, `warnings`) plus `ruamel.yaml` (already in the workspace lock via `tools.harness_lint`) for reading, and `syrupy`/`pytest` (already dev-deps) for tests. `pyproject.toml` declares `dependencies = []` (mirrors `tools/docs_sync`). `uv sync --all-packages` must NOT mutate `uv.lock`. slopcheck/registry audit is N/A — nothing to install. `[VERIFIED: codebase — zero new deps, matches docs_sync/contract_hash posture]`

## State of the Art

| Old Approach | Current Approach | When | Impact |
|--------------|------------------|------|--------|
| wshobson 194-agent generic port | Custom minimal single-source→adapter (PATTERN only) | PROJECT decision (CLAUDE.md) | Emit ONLY the hand-authored `harness/` surface; no generic payload |
| Node `tools/adapters/` transpile (CLAUDE.md stack table) | Python emitter, `.ts` verbatim-copied (D-01) | This phase | No Node toolchain; source is already Markdown+TS |
| Runtime-specific authored source | Runtime-neutral dual-representation source projected at emit | D-04 | One source of truth; the emitter is the only specialization point |

**Deprecated/outdated:** the CLAUDE.md "Single-Source → Multi-Runtime Emit" row suggesting Node/`make generate HARNESS=opencode` is superseded by D-01 (Python, no Node). Keep the *pattern* (one source → per-runtime adapters), drop the Node mechanism.

## Validation Architecture

> `workflow.nyquist_validation = true` in `.planning/config.json` — this section is REQUIRED.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x + syrupy 5.2.0 (workspace dev-deps; `uv.lock`) |
| Config file | root `pyproject.toml` (`[tool.pytest]` testpaths = tools/ + libs/python) |
| Quick run command | `uv run pytest tools/harness_emit -x` |
| Full suite command | `uv run pytest` (harness core suite — the CI `core-suite` job) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EMIT-01 | Source frontmatter parses + projects for all 4 artifact types | unit | `uv run pytest tools/harness_emit/tests/test_mapping.py -x` | ❌ Wave 0 |
| EMIT-02 | Both runtime trees emitted with correct per-runtime shape | unit + snapshot | `uv run pytest tools/harness_emit/tests/test_emit_determinism.py -x` | ❌ Wave 0 |
| EMIT-02 | Over-cap/invalid artifact FAILS build (no truncate) | unit | `uv run pytest tools/harness_emit/tests/test_validators.py -x` | ❌ Wave 0 |
| EMIT-02 | GSD/human files untouched; managed-block merge idempotent | unit | `uv run pytest tools/harness_emit/tests/test_coexist.py tools/harness_emit/tests/test_merge_idempotent.py -x` | ❌ Wave 0 |
| EMIT-02 | Manifest owns only emitted files; prunes orphans not GSD | unit | `uv run pytest tools/harness_emit/tests/test_manifest.py -x` | ❌ Wave 0 |
| EMIT-02 | Re-emit → clean git diff (drift gate) | CI/integration | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` | ❌ Wave 0 (+ ci.yml job) |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_emit -x`
- **Per wave merge:** `uv run pytest` (full core suite — includes the harness_lint validators the emitter reuses)
- **Phase gate:** full suite green + `emit-drift` diff clean before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tools/harness_emit/pyproject.toml` — virtual member, `dependencies = []`
- [ ] `tools/harness_emit/tests/conftest.py` — repo-root on sys.path (clone docs_sync)
- [ ] `tools/harness_emit/tests/__snapshots__/` — syrupy `.ambr` for the projected tree
- [ ] `.github/workflows/ci.yml` — add `emit-drift` job + add it to `gate.needs`
- [ ] Framework install: none — pytest/syrupy already in the lock

## Security Domain

> `security_enforcement` not disabled in config → include. This phase is a build tool over trusted in-repo files; the surface is small.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no auth in a codegen tool |
| V3 Session Management | no | — |
| V4 Access Control | yes | manifest-scoped writes + GSD-path exclusion = the "don't write outside your lane" control (D-03); mirror `docs_sync._confine` path confinement so no emit escapes its target trees |
| V5 Input Validation | yes | `parse_frontmatter` uses ruamel **safe** loader (no arbitrary object construction from markdown); emit-time validators reject malformed frontmatter |
| V6 Cryptography | no | no crypto (unlike contract_hash's RFC 8785; the drift gate here is a plain git diff, not a hash) |

### Known Threat Patterns for a codegen/emitter
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in an emitted filename (a source `name` like `../escape`) | Tampering | `_confine`-style resolve+base-check before every write (reuse `docs_sync._confine`); slug-validate names |
| Clobbering GSD/human config | Tampering / DoS-of-workflow | manifest ownership + managed-block merge; `test_coexist.py` |
| Leaking a real model identifier into emitted artifacts | Information disclosure (policy) | placeholder-only validator (already enforced on source; extend to output) |
| Executing untrusted plugin `.ts` at emit | Elevation | plugins are COPIED, never executed, during emit (D-01); execution is opencode-runtime, deferred |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | opencode uses SINGULAR dir names (`.opencode/agent`, `command`, `skill`, `plugin`, `tool`) | Mapping Table | Low — ROADMAP+CLAUDE.md specify singular; re-verify at first opencode install. Wrong → rename dirs (mechanical). |
| A2 | opencode command frontmatter honors `agent`/`subtask` and `!`-bash + `$ARGUMENTS` interpolation | Mapping Table | Low-Med — matches authored source intent + opencode docs; unverified live (proxy-403). Wrong → adjust command projection. |
| A3 | Claude ignores an unknown key in a settings.json hook group (why we AVOID a sentinel and use signature-match instead) | Managed-Block Merge | Low — mitigated by choosing signature-match, which needs no sentinel. |
| A4 | No `.opencode/tool/` source exists today, so `tool` emit is empty/deferred | Mapping Table | Low — verified no `harness/tool*` source. Wrong → add a tool projector later. |
| A5 | The Phase 2/4 hand-wired settings.json harness hooks should be reproduced idempotently (not re-owned) by Phase 7 | Managed-Block Merge / Pitfall 4 | Med — a planning decision, not a fact. Wrong choice → `test_hook_wiring.py` breaks; resolve explicitly in the plan. |

**These A-items are planner/discuss inputs, not locked facts.** A1/A2/A6-class items carry existing in-repo RESUME-note precedent (defer live verification to opencode install).

## Open Questions (RESOLVED)

1. **`.opencode/opencode.json` location — repo root or `.opencode/`?**
   - Known: ROADMAP criterion 1 lists "`.opencode/{...}` + `opencode.json`" — reads as a sibling at repo root (opencode reads root `opencode.json`).
   - Unclear: whether a `.opencode/opencode.json` is also honored.
   - Recommendation: emit root `opencode.json` (opencode's documented project config location); own it wholesale via manifest (no GSD conflict).
   - **RESOLVED:** emit root `opencode.json`, owned wholesale via manifest — carried by **07-03 Task 2**.

2. **Does Phase 7 take ownership of the Phase 2/4 settings.json/hooks wiring, or just coexist idempotently?** (A5)
   - Recommendation: coexist idempotently in the MVP (reproduce byte-for-byte); consider migrating to emit-ownership as a later, explicit task that also updates `test_hook_wiring.py`. Decide in planning.
   - **RESOLVED:** coexist idempotently (order-preserving, byte-for-byte reproduction of the live file; NO ownership migration) — locked as the MVP decision (A5) in **07-05** (`<interfaces>` MVP decision + Regime B-json order-preserving merge). Ownership migration is explicitly out of scope for this phase.

3. **`.opencode/tool/` — emit empty dir, or omit until a tool source exists?**
   - Recommendation: omit (don't emit empty dirs; git doesn't track them anyway). Add a tool projector when the first `harness/tool*` source lands.
   - **RESOLVED:** omit `.opencode/tool/` (no empty-dir emit) until the first `harness/tool*` source lands — carried by **07-03 Task 1**.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | the emitter + tests | ✓ | 3.11 (`requires-python >=3.11`, tomllib present) | — |
| uv | run/test the tool | ✓ | workspace (0.11.x per CLAUDE.md) | — |
| pytest + syrupy | determinism/snapshot tests | ✓ | 8.4.x / 5.2.0 (in `uv.lock`) | — |
| ruamel.yaml | frontmatter reader | ✓ | in lock via harness_lint | stdlib fence-parse (not recommended — don't hand-roll) |
| jsonschema | opencode.json validation | ✓ | in lock (used by test_opencode_json) | — |
| opencode runtime | LIVE artifact load | ✗ | not installed | STRUCTURAL validation only (per CONTEXT out-of-scope); RESUME note for live verify |
| Node.js | (NOT needed — D-01) | n/a | — | plugins verbatim-copied, no transpile |

**Missing dependencies with no fallback:** none block this phase.
**Missing dependencies with fallback:** opencode runtime — structural/loadability validation substitutes for live execution (explicitly in scope per CONTEXT).

## Sources

### Primary (HIGH confidence — direct codebase read this session)
- `harness/agents/*.md`, `harness/commands/*.md`, `harness/skills/*/SKILL.md`, `harness/plugins/*.ts`, `harness/permission-matrix.json`, `harness/opencode.json`, `harness/project.toml` — the input contract
- `tools/docs_sync/{generate.py,pyproject.toml,tests/*}` — codegen determinism + virtual-member + syrupy idiom (closest analog)
- `tools/contract_drift/check.sh` + `.github/workflows/ci.yml` — the re-emit-diff drift-gate + CI fan-in archetype
- `tools/harness_lint/frontmatter.py` + `tests/{test_agents,test_commands,test_skills,test_opencode_json}.py` — shared reader + the exact caps/validators (name≤64, desc≤1024, body-warn-500, 15 keys, modes, read-only invariant)
- `tools/harness_config/loader.py` — tomllib config-loader idiom
- `tools/memory_regen/tests/test_hook_wiring.py` + `.claude/settings.json` — the settings.json coexistence contract (4 SessionStart groups, GSD survival)
- `.planning/{ROADMAP.md,REQUIREMENTS.md,STATE.md}` + `07-CONTEXT.md` + `CLAUDE.md` — scope, decisions, prior research flags

### Secondary (MEDIUM confidence)
- code.claude.com/docs/en/sub-agents — Claude subagent `.claude/agents/` + frontmatter (name/description/tools/model) and `.claude/commands/` slash-command format
- WebSearch (opencode agents) — opencode agent markdown frontmatter (mode primary|subagent|all, permission, model, tools), project agents dir

### Tertiary (LOW confidence — flagged)
- opencode.ai/docs/* — proxy-403 (STATE lines 158–159); opencode dir singular/plural + hook event names to re-verify at install

## Metadata

**Confidence breakdown:**
- Input contract (EMIT-01): HIGH — every source file read directly
- Mapping/projection (EMIT-02): HIGH for the mechanics (source is dual-representation; caps/validators exist); MEDIUM on exact opencode dir/frontmatter acceptance (runtime not installed, docs 403)
- Manifest + merge: HIGH on the pattern (precedented by docs_sync determinism + test_hook_wiring coexistence); the settings.json signature-merge is a design recommendation, not an existing artifact
- Drift gate + tests: HIGH — direct clone of contract_drift + docs_sync patterns already in CI
- Pitfalls: HIGH — derived from in-repo constraints (P3/P12/D-07/model-identity/hook-wiring test)

**Research date:** 2026-07-12
**Valid until:** ~2026-08-11 (stable — all inputs are in-repo; only the opencode-runtime specifics are external and already flagged for install-time re-verification)
