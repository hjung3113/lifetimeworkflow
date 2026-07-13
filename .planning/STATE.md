---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Long-Horizon
status: planning
stopped_at: Phase 9 context gathered
last_updated: "2026-07-13T14:48:18.919Z"
last_activity: 2026-07-12 — Milestone v2.0 roadmap created (phases 9/10/11, numbering continued)
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-07)

**Core value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·레거시 전환 리스크를 하네스가 자동으로 강제·검증한다 — "어떻게 개발·유지보수·리팩토링하는가"가 실행 가능한 스킬·커맨드·훅으로 박혀 있다.
**Current focus:** Phase 09 — self-maintaining-derived-artifacts-curator (v2.0 α)

## Current Position

Phase: 9 — Self-Maintaining Derived Artifacts + Curator (not started)
Plan: —
Status: Roadmap created — ready to plan Phase 9
Last activity: 2026-07-12 — Milestone v2.0 roadmap created (phases 9/10/11, numbering continued)

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 1 P03 | 2 | 2 tasks | 7 files |
| Phase 1 P02 | 5 | 2 tasks | 11 files |
| Phase 1 P04 | 8 | 3 tasks | 13 files |
| Phase 1 P05 | 18min | 2 tasks | 10 files |
| Phase 1 P06 | 8min | 3 tasks | 21 files |
| Phase 2 P01 | 20min | 2 tasks | 12 files |
| Phase 2 P02-02 | 5min | 2 tasks | 6 files |
| Phase 2 P02-03 | 8min | 1 tasks | 3 files |
| Phase 2 P02-04 | 15min | 2 tasks | 5 files |
| Phase 2 P02-05 | 9min | 2 tasks | 5 files |
| Phase 3 P03-01 | 12min | 2 tasks | 8 files |
| Phase 3 P03-02 | 9min | 2 tasks | 8 files |
| Phase 3 P03-03 | 10min | 2 tasks | 7 files |
| Phase 3 P03-04 | 11min | 3 tasks | 10 files |
| Phase 3 P05 | 12min | 3 tasks | 8 files |
| Phase 3 P06 | 14min | 3 tasks | 14 files |
| Phase 3 P03-07 | 9min | 2 tasks | 10 files |
| Phase 4 P01 | 14min | 2 tasks | 8 files |
| Phase 04 P02 | 7min | 2 tasks | 9 files |
| Phase 04 P03 | 12min | 2 tasks | 2 files |
| Phase 04 P04 | 3min | 2 tasks | 3 files |
| Phase 04 P05 | 5min | 2 tasks | 4 files |
| Phase 04 P06 | 5min | 3 tasks | 8 files |
| Phase 05 P01 | 2min | 2 tasks | 2 files |
| Phase 05 P04 | 12min | 2 tasks | 8 files |
| Phase 05 P02 | 18min | 2 tasks | 11 files |
| Phase 05 P03 | 20min | 2 tasks | 36 files |
| Phase 05 P05 | 15min | 2 tasks | 13 files |
| Phase 06-ci-gates P01 | 6min | 3 tasks | 5 files |
| Phase 06-ci-gates P03 | 7min | 4 tasks | 3 files |
| Phase 08 P01 | 6min | 2 tasks | 5 files |
| Phase 08 P02 | 9min | 2 tasks | 3 files |
| Phase 08 P03 | 7min | 3 tasks | 3 files |
| Phase 08 P05 | 10min | 2 tasks | 3 files |
| Phase 08 P04 | 10min | 3 tasks | 6 files |
| Phase 08 P06 | 12min | 2 tasks | 3 files |
| Phase 07 P01 | 24min | 3 tasks | 20 files |
| Phase 07 P02 | 9min | 2 tasks | 10 files |
| Phase 07 P03 | 10min | 2 tasks | 8 files |
| Phase 07 P04 | 9min | 2 tasks | 5 files |
| Phase 07 P05 | 4min | 2 tasks | 4 files |

## Accumulated Context

### Roadmap Evolution

- Milestone v2.0 roadmap created (2026-07-12): **phases 9/10/11** appended, numbering continued after v1.0 (phases 1–8). Phase 9 (α) Self-Maintaining Derived Artifacts + Curator (MAINT-01..04); Phase 10 (β) Context-Economy Fan-out/Synthesize (ECON-01..03); Phase 11 (γ) Multi-Repo Workspace (MREPO-01..04). Sequencing locked 9→10→11 (β is the reusable fan-out substrate γ builds on). All 11 v2.0 requirements mapped 1:1; coverage 11/11. Two plan-time KEY DECISIONS carried, unresolved: (α) which derived artifacts flip gitignored-derived → committed-derived for PR refresh; (γ) workspace model a/b/c (lean b: workspace manifest). Cross-cutting non-negotiables reasserted: derived-never-hand-edited (machine-write + CI-verify OK), machines-gate/humans-ratify on the constitution plane, GEN-04 core→example/workspace-member no-dependency, every new agent/skill/hook round-trips the Phase-7 emitter to both runtimes, PR/CI enforcement preferred over heavy per-commit hooks.
- Phase 8 added (2026-07-10): **Pipeline-Topology Conductor + Per-Component Agents** (PIPE-01..06). Post-Phase-6 user request — evolve the agent model from per-language to pipeline-aware. Independent of Phase 7 (emitter). Locked with user: build BOTH neutral core mechanism AND concrete `examples/log-parser/` demo; EVOLVE the existing primary `orchestrator` (no second primary/tier); formal GSD phase.

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Bottom-up 6-phase spine — constitution/golden first, emitter last (research converged across all 4 dimensions).
- [Roadmap]: Normalization comparator (CONTRACT-02) is the single shared linchpin — built once in Phase 1, reused by golden runner AND polyglot linter (POLY-01, Phase 4).
- [Roadmap]: "Machines gate, humans ratify" — no agent self-bless of golden; constitution plane is human-owned/CODEOWNERS-gated.
- [Phase ?]: [01-03] Diátaxis docs skeleton laid down; reference/ quadrant flagged derived-from-contracts (populated by /docs-sync in Phase 3, DOCS-03) — never hand-authored.
- [Phase ?]: [01-03] MADR adr/0001 immutably records walking-skeleton architecture; adr/README.md establishes append-only/supersede-not-edit convention (DOCS-02).
- [Phase ?]: [01-02] format-conventions.schema.json materializes §4.3-4.6 conventions as const/enum fields — the P14 drift-hash target so convention changes (not just column reorders) trip the gate (Plan 05).
- [Phase ?]: [01-02] golden/ seeded as a TOP-LEVEL constitution-plane sibling of contracts/ (no contracts/golden/ nesting), per D-06/D-07 locked layout.
- [Phase ?]: [01-04] §4-5 normalization core (CONTRACT-02): language-neutral spec + Python (green) + .NET (authored; dotnet test deferred by BOOT-01 egress), cross-validated by one shared libs/normalize-fixtures corpus (D-04).
- [Phase ?]: [01-05] contract-drift gate (CONTRACT-04): RFC 8785 (JCS, rfc8785 0.1.4) canonicalize + SHA-256 per-schema manifest over all contracts/**/*.schema.json incl. format-conventions.schema.json — a §4-5 convention flip (bom false->true) bumps the hash and trips the gate exactly like a column reorder (P14); changes classified breaking vs non-breaking.
- [Phase 1]: [01-06] Walking-skeleton golden loop closed (CONTRACT-03): Python golden-runner spawns .NET toy converter (subprocess shell=False, dotnet via absolute $HOME/.dotnet path P5), normalizes both sides via shared §4-5 core, diffs vs approved .verified. repr-only PASS / value-regression FAIL (P4). /golden-approve refuses promotion without human --approve+--adr+token (P9). — End-to-end polyglot equivalence slice; .NET live spawn DEFERRED (BOOT-01 egress), comparison path proven green via recorded-output twin.
- [Phase 2]: [02-01] Two-plane .memory/ locked: state/ committed (survives ephemeral container), derived/ gitignored + DERIVED marker; constitution-immutability is a declaration here — runtime enforcement is Phase-4 contract-guard (MEM-01/02, D-03/D-04).
- [Phase 2]: [02-01] tools/memory_regen pins EXACT tree-sitter 0.25.2 + grammar wheels (py 0.25.0 / cs 0.23.5 / bash 0.25.1) + networkx 3.6.1 — individual wheels NOT language-pack (runtime download breaks determinism); resolved once so Wave-2 never touches uv.lock (T-02-SC).
- [Phase 2]: [02-01] Bootstrap runs 'uv sync --all-packages' (install+verify): memory_regen is the first member with deps absent from the virtual root, so a bare 'uv sync' silently prunes the tree-sitter/networkx toolchain every SessionStart.
- [Phase 2]: [02-02] Single injection contract fixed (D-01): python -m tools.memory_regen.inject is the ONE payload source; Claude SessionStart hook (4th slot, coexists) + authored-deferred opencode adapter both wrap the identical assemble() — capped ~1k-token, banner-first (never dropped), drift-aware, priority-truncated, pointer-only (no full contract bodies, P13/T-02-06).
- [Phase 2]: [02-05] Nearest-wins AGENTS.md rules layer: root (map + golden-path + non-negotiables + lazy-load) + per-package Python/.NET files that RESTATE non-negotiables verbatim (P11 — Codex replaces nested AGENTS.md vs concat, so never inherit-only). CLAUDE.md gets a pointer-not-duplicate section in the non-GSD-managed gap (profile block untouched, T-02-13). Prose is advisory by design — true backstop = 02-02 injector + Phase-4 hooks. Phase 2 COMPLETE (all 4 success criteria met).
- [Phase 2]: [02-04] repo-map uses networkx pure-Python PageRank backend (_pagerank_python) — numpy-free; keeps 02-01 pinned toolchain + uv.lock untouched (T-02-SC). Determinism (delete+regen byte-identical) via sorted node/edge insertion + (-score,path) tie-break + rank-only (no floats) + no timestamp; proven by generate-twice sha256 + committed syrupy snapshot (NOT git diff — derived/ gitignored). tree-sitter 0.25 Query+QueryCursor API (NOT removed lang.query().captures()).
- [Phase 3]: [03-01] CONFIG-02 permission = data + pure tested resolver: harness/permission-matrix.json holds the 15-key matrix (bash *-first last-wins, terminal rm -rf*:deny not a broad allow per P3) + path_deny_globs (contracts/**, docs/adr/**, golden/**, *.env); tools/harness_perms/resolver.py (resolve_bash/resolve_path/load_matrix) is pure fnmatch+json, unit-proven, reused verbatim by Phase-4 hooks. __init__ re-exports lazily (PEP 562) to avoid conftest-collection deadlock in the namespace-package uv member.
- [Phase 3]: [03-03] Five personas authored as dual-representation harness/agents/*.md (opencode permission: + Claude tools:); code-reviewer AND explorer read-only in BOTH reps enforced by is_read_only() in test_agents.py (T-03-09/P-perm); placeholder model tiers only (provider/explorer-tier), no real model IDs; engineer bash scope mirrors permission-matrix.json (dotnet */uv */pytest *).
- [Phase ?]: [03-05] Seven skills as harness/skills/<name>/SKILL.md with progressive disclosure; caps identical for opencode AND Claude (name<=64/desc<=1024 HARD, body>500 WARN) per RESEARCH 200-vs-1024 correction; test_skills.py pins exactly 7 disjoint skills (anti-sprawl P8).
- [Phase ?]: [03-06] /docs-sync (DOCS-03/CMD-08): tools/docs_sync stdlib-json generator clones contracts_index.py determinism (rows/render/write/main, DERIVED header, no datetime/float) — contracts/**/*.schema.json to docs/reference/*.md byte-identical delete+regenerate (sha256 + committed syrupy, NOT git diff). write() confined under docs/reference/ (mirror golden_runner._confine, T-03-21); read via stdlib json same path as contract_hash, zero new deps (T-03-SC/T-03-23). reference/ is DERIVED, tutorials/how-to/explanation stay human-authored. Command macro wraps python -m tools.docs_sync (agent python-engineer).
- [Phase ?]: [03-07] CMD-06 /strangler-step is a RUNNABLE gate (tools/strangler_guard): require_baseline refuses (StranglerRefused -> exit 3, mirroring approve.py) when no captured legacy golden .verified baseline exists for a target path; never fabricates one (P10/T-03-24). Macro adds single-path + mandatory /golden parity. CMD-05 /new-normalization-rule enforces contract -> (input,expected) data case -> intentional failing code stub (Pattern 4/D-06). Phase 3 COMPLETE (7/7).
- [Phase ?]: [04-01] POLY-01 polyglot §4.3-4.6 linter (tools/polyglot_lint): detection-by-normalization diffs raw vs libs/python normalize.core (R1-BOM/R2-CRLF/R7-tsv/R3-decimal/R5-datetime/R6-null), fail loud exit 1; reuses the core (no second normalizer, D-02/D-03) proven by identity + corpus-parity on libs/normalize-fixtures. Shared engine HOOK-04/HOOK-03 will call.
- [Phase 04]: secret_scan feeds resolve_path only the *.env SECRET subset, never the full constitution deny key — preserves contract-guard's GOLDEN_APPROVE_HUMAN bypass under any-deny-wins aggregation (04-06 composition invariant / Blocker-1 fix)
- [Phase 04]: shared tools/hooks _stdin adapter is fail-safe on malformed/empty stdin — yields a sentinel Event mapping to 'no decision' so a broken payload never crashes a gate (T-04-05)
- [Phase ?]: HOOK-04 contract-guard uses CONSTITUTION_GLOBS (constitution-only subset, no *.env) so its domain is provably disjoint from secret_scan (W-1)
- [Phase ?]: Approved-but-dirty constitution writes still denied via reused lint_bytes (D-04 byte-pristine); allowed-path BOM/CRLF deferred to format-on-write 04-04
- [Phase ?]: GOLDEN_APPROVE_HUMAN bypass requires non-empty non-blank value; empty string does not bypass (Q1 RESOLVED, T-04-06)
- [Phase ?]: 04-04: HOOK-01 format-on-write reuses normalize.core strip_bom_normalize_newlines (single §4.3-4.6 rule, D-02); mutates via FS/subprocess not Claude Write (no PostToolUse re-entry); dotnet-format gated-skip, gate always exits 0
- [Phase 04]: HOOK-03 commit-gate composes run_gate + lint_file + golden-parity (D-02, no re-impl)
- [Phase 04]: Golden-parity is dotnet-gated: SKIP-with-log when .NET absent so drift+polyglot always run (D-06)
- [Phase ?]: 04-06: appended Phase-4 gate slots to .claude/settings.json (append-only, never rewrote GSD objects); coexist test guards all 11 GSD guards + the four new gates (7 PreToolUse / 4 PostToolUse)
- [Phase ?]: 04-06: opencode plugin stubs authored-only, not registered in opencode.json — execution deferred (D-01); hook names A1 MEDIUM, re-verify at opencode wiring
- [Phase 05]: [05-01] D-05 commit-gate drift approval path — check_drift honors a non-empty GOLDEN_APPROVE_HUMAN token (drift FAIL -> logged WARN+PASS, verbatim contract_guard:91 mirror); DRIFT-ONLY (polyglot §4.3-4.6 + golden stay hard, proven by test_approval_does_not_bypass_polyglot); empty/blank never authorizes. Core-only commit lands clean with no token — opens the sanctioned landing path for the 05-02/03/05 domain-move commits.
- [Phase 05]: [05-02] GEN-02 generic default instance — parametrized the golden runner (built-in language-agnostic `run_identity_converter` verbatim stdlib byte-copy + `converter`/`golden_dir` params; §4.3-4.6 `normalize_tsv` compare path untouched, default stays "dotnet"). Added domain-neutral `contracts/sample/greeting.schema.json` (zero semiconductor vocab) + `golden/sample/*` identity golden case whose seed→baseline diff is ROW-ORDER only (R8) so it PASSes without .NET; seed byte-clean (LF/no-BOM) for the ADDED-file polyglot lint. Rebaselined the 6-schema root manifest (drift reads clean), added `greeting` to docs-sync EXPECTED_PAGES + regenerated docs-sync AND memory_regen contracts-index determinism snapshots. Core now points at a generic instance, not a void — precondition for the 05-03 domain move. NOTE: 3 commit_gate drift-block tests fail ONLY while GOLDEN_APPROVE_HUMAN is live in-shell (pre-existing test-isolation gap; green in CI/token-unset: 364 passed); logged as DEF-05-02-1.
- [Phase 05]: [05-03] GEN-01 domain MOVE — semiconductor seed + the example's .NET language-side impl relocated under `examples/log-parser/` via history-preserving `git mv` (verbatim, renames stay `R` → excluded from commit_gate `--diff-filter=ACM` so the intentionally-dirty BOM/CRLF golden seeds are NOT re-linted, P2). Moved: contracts/{log-specs,reference-data,state} + normalization/correction-rules.*, components/toy-converter, `libs/dotnet` WHOLESALE (not a uv member, no core Python importer; ADR-0002 core-is-language-neutral), golden/{repr-only,value-regression}, + the 3 domain golden_runner tests + tests/recorded/*. STAYED core: libs/python/normalize + libs/normalize-fixtures (uv members / core-imported), format-conventions.schema.json. De-pinned core golden_runner (dropped TOY_CONVERTER_PROJECT default → project required via run_golden_case(project=...); deleted dead toy_converter_project fixture). Rebaselined root manifest to generic only (format-conventions + sample/greeting) → live drift clean; built the example's own manifest. Repointed core tests to surviving material (docs-sync EXPECTED_PAGES→{format-conventions,greeting} + rows() target; test_agents_md drops libs/dotnet as a core plane) + regenerated docs-sync & contracts-index snapshots (repo-map .ambr unchanged, fixture-based). Landed ONE commit (ebe4276) through the LIVE gate with GOLDEN_APPROVE_HUMAN — no --no-verify. Non-example suite green (361 passed).
- [Phase 05]: [05-04] GEN-03 language/toolchain SSOT — harness/project.toml is a data-only slot ([instance] root + [[languages]] dotnet/python: bash_scope/test/format/persona/sdk_bootstrap) carrying the log-parser EXAMPLE INSTANCE's values (not a core hardcode). tools/harness_config is a new tools/* uv member (package=false, PEP 562 lazy re-export) parsing it with stdlib tomllib; language_bash_scopes() folds the implicit `pytest *`. "Derived-not-hardcoded" satisfied by a CONSISTENCY TEST (D-03 "codegen is overkill"), not codegen: test_language_config asserts permission-matrix allow-scopes == config-derived set + each persona file exists — divergence FAILS (config = SSOT). Existing hardcoded values kept & proven consistent, not ripped out. Zero external deps (uv.lock registers in-repo member only). Precondition for Phase-6 config-derived CI matrix.
- [Phase ?]: [05-05] GEN-04 core→example guard + ADR-0002 de-specialization; SCOPE A guard scans tools/harness/libs for examples/ refs + import examples + moved components/toy-converter (self-excluded, [instance] root exempt, live negative controls); bare libs/dotnet prose deferred to GEN-05; ADR-0002 (accepted, complements 0001) records generic re-scope + normalize split (python normalize+fixtures STAY as language-neutral core, libs/dotnet MOVES because core-is-language-neutral) + project.toml language slot + GOLDEN_APPROVE_HUMAN drift-only path; landed via live gate, non-example suite 366 passed; Phase 5 COMPLETE.
- [Phase ?]: [Phase 08]: [08-01] PIPE-01 generic pipeline-topology DATA slot — cloned the [[languages]] -> loader.languages() -> test_language_config.py triad verbatim: harness/project.toml gains a banner-scoped GENERIC-ONLY source/sink/sample-record default ([[components]] + [pipeline]); loader.components()/pipeline() are pure passthrough (no enforcement); consistency lives in the gate test_pipeline_config.py (component.language in declared languages, ids unique, edges well-formed: endpoints declared + contract in from.produces AND to.consumes). Concrete multi-component topology deferred to instance overlay (Plan 04) to keep core GEN-04 green. Non-example suite 418 passed.
- [Phase ?]: [Phase 08]: [08-02] PIPE-02 conductor evolved IN PLACE — the primary orchestrator now reads the declared [[components]]/[pipeline] topology (tools.harness_config) and routes by pipeline stage/component (not only language): new 'Trace the topology' intake step + stage/component routing rows + /pipeline entry; test_orchestrator_topology.py pins single-primary + topology-intake + stage/component routing. EXPECTED_PERSONAS stays 4 (no second primary). Fixed a pre-existing GEN-04 prose leak in 08-01's test_pipeline_config.py (literal examples/ token slipped the guard which scans git ls-files, file committed after guard ran). Full non-example suite 421 passed.
- [Phase ?]: [Phase 08]: [08-03] PIPE-03 neutral component-engineer template (anti-sprawl-EXEMPT under harness/agents/templates/ like engineer.md) — stage-keyed fill-in-the-blanks persona; /component gains a mandated-order+all-three-or-none section deriving the agent into the instance agents/ and registering the [[components]]/[pipeline] slot; new test_agent_templates.py closes the templates/*.md gap (EXPECTED_TEMPLATES={engineer,component-engineer}, imports VALID_MODES/ALLOWED_PERMISSION_KEYS from test_agents). EXPECTED_PERSONAS stays 4; GEN-04 green; full non-example suite 430 passed.
- [Phase 08]: [08-04] PIPE-04 instance overlay demonstration: examples/log-parser/project.toml declares the concrete parser(1,.NET)→converter(2,.NET)→scheduler(3,py)→collector(4,py) topology with real domain-contract edges (standard-log, equipment-progress x2) as an OVERLAY of the neutral core slot (loaded path-locally via load_project(path=); core [instance] root stays ""). 4 per-stage component agents instantiate the component-engineer template (mode:subagent, name==component.id, least-privilege bash). Instance topology gate runs ONLY in the example leg (off root testpaths, no GEN-04 trip). Core 439 passed; example leg 9 passed/2 skipped.
- [Phase ?]: [Phase 08]: [08-06] PIPE-06 closeout — extended persona anti-sprawl to the conductor (test_single_primary_carries_conductor_signal; EXPECTED_PERSONAS stays 4). Full guard surface green: core 440 passed/3 snapshots + instance leg 9 passed/2 skipped (expected .NET egress). ADR-0003 (accepted, complements ADR-0002) records pipeline-topology pure-DATA slot + instance overlay: generic default in core, concrete parser→converter→scheduler→collector topology in examples/log-parser/project.toml, GEN-04 as PRIMARY driver; landed via human GOLDEN_APPROVE_HUMAN gate. Phase 8 COMPLETE (6/6).
- [Phase ?]: [07-01] EMIT-01/02 agent-first emit walking skeleton (D-05): tools/harness_emit projects runtime-neutral harness/agents to .opencode/agent (mode+permission) + .claude/agents (tools); DERIVED marker on line 2 so first line stays --- and frontmatter loads; permission.bash kept in authored last-wins order (P3); byte-identical re-emit proven by sha256 + committed syrupy .ambr.
- [Phase ?]: [07-01] Caps + is_read_only + READ_ONLY_PERSONAS extracted to tools/harness_lint/caps.py as single source shared by lints AND emit validate.py; validate-then-write raises HarnessEmitError writing nothing on over-cap desc / invalid permission key / real model ID / read-only-gains-write (never truncate).
- [Phase ?]: [07-01] emit-manifest.json prune-then-write owns ONLY harness paths with gsd-* exclusion (D-03); emit-drift CI job (re-emit + git diff --exit-code over full documented path set) in non-bypassable gate.needs — later-wave paths pre-covered.
- [Phase ?]: [07-02] EMIT commands+skills widening: project_command (opencode keeps agent/subtask, Claude description-only) + project_skill (identical both runtimes, references/** byte-copied to both trees). Loud-fail check_command/check_skill/check_skill_set from caps.py; test_coexist proves gsd/ non-collision; re-emit byte-identical.
- [Phase ?]: [07-03] EMIT plugins+config: 5 harness .ts plugins byte-verbatim-copied to .opencode/plugin (never parsed/executed, D-01/T-07-04); permission-matrix.json projected to opencode.json full 15-key block via permissions.build_permission_block (strips _note+path_deny_globs), bash *-first last-wins order preserved (P3/T-07-06); emitter owns root opencode.json wholesale; check_opencode_config loud-fails on jsonschema-invalid (T-07-07) + any real model id (placeholder-tier regex, T-07-03); re-emit byte-identical.
- [Phase ?]: [Phase 07]: [07-04] EMIT-02 Regime B-md managed-block merge — merge.splice_managed_block is a hand-rolled two-marker (BEGIN/END HTML-comment) string splice: replaces ONLY inside the fence, preserves outside verbatim (T-07-02), appends once when markers absent (idempotent), LF/no-BOM/single trailing newline, fails loud (ValueError) on a single/malformed marker. generate.emit() reads->splices->writes root AGENTS.md (deterministic sorted agent/command/skill index) + CLAUDE.md (emitter pointer); NEVER full-write; both EXCLUDED from emit-manifest.json (Regime B not A). GSD Project/Developer-Profile + nearest-wins rules preserved byte-for-byte; committed-then-re-emit clean over the full emit-drift path set; 38 harness_emit tests green.
- [Phase ?]: settings.json signature merge is order-preserving (Regime B-json, no sort_keys) — reproduces live bytes byte-for-byte; opencode.json/frontmatter stay globally sorted
- [Phase ?]: Harness hook groups coexist idempotently with GSD wiring (no ownership migration); SessionStart pinned at 4 groups

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- **[BLOCKING — plan 01-01] BOOT-01 .NET 10 install egress-denied:** `tools/bootstrap/install.sh` + `verify.sh` are committed and correct, but the .NET 10 download hosts are blocked by this container's egress policy (`builds.dotnet.microsoft.com`, `dotnetcli.azureedge.net`, `dotnetcli.blob.core.windows.net`, `aka.ms` → 403 CONNECT). The proxy README forbids routing around policy denials. **Human action:** allowlist those hosts in the egress policy (or ship a pre-installed .NET 10), then run `bash tools/bootstrap/install.sh && bash tools/bootstrap/verify.sh` to finish the plan. uv workspace (BOOT-02) and SessionStart wiring (BOOT-03) are DONE and green.
- Toolchain: .NET 10 SDK is NOT installed in this ephemeral env — Phase 1 (BOOT-01) install script gates all .NET-side execution.
- Research flag: opencode.ai is proxy-403'd; re-verify exact hook event names, 15-key permission matrix semantics, and skill size caps against live docs before Phase 4 (hooks) and Phase 6 (emitter).
- Research flag: internal inconsistency on Claude skill description cap (≤200 vs ≤1024 chars) — resolve precisely at Phase 6 emitter-validator implementation.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| testing (isolation) | DEF-05-02-1: 3 commit_gate drift-block tests leak the live GOLDEN_APPROVE_HUMAN token (missing delenv) → fail only when the session token is exported; green in CI. Suggested fix: add `monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)`. See phases/05-despecialization/deferred-items.md | open | 05-02 |

## Session Continuity

Last session: 2026-07-13T14:48:18.894Z
Stopped at: Phase 9 context gathered
Resume file: .planning/phases/09-self-maintaining-derived-artifacts-curator-v2-0/09-CONTEXT.md
