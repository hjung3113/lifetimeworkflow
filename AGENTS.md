# AGENTS.md — Root Rules (nearest-wins)

> Canonical rules source for agents working in this repo. Per-package `AGENTS.md`
> (e.g. `libs/python/AGENTS.md`, `libs/dotnet/AGENTS.md`) refine these for a subtree
> and **resolve nearest-wins**. Non-negotiables are **restated** in each per-package
> file — never inherited-only — because runtime merge semantics differ (Codex replaces
> nested `AGENTS.md`; others concat). Prose here is advisory; the true backstop is the
> non-ignorable SessionStart injector (Phase 2) plus Phase-4 hooks (contract-guard,
> polyglot-boundary linter).

## Monorepo map

This repo is a **reusable, contract-first polyglot agent-harness TEMPLATE**: a domain-neutral
**harness core** plus one-or-more **instances** under `examples/<name>/`. The core depends on
**NO** instance — a one-directional invariant enforced by the GEN-04 guard
(`tools/harness_lint/tests/test_core_no_example_dep.py`); an instance depends on the core, never
the reverse. **Language boundary = process / file / DB only — never in-process object passing**
(A-model: CLI-spawn + exit codes).

```txt
CORE — domain-neutral, stays on clone ───────────────────────────────────────────────
contracts/    Constitution plane — the ACTIVE instance's contracts / generic default at root
              (JSON Schema Draft 2020-12 + YAML specs). THE single source of truth.
golden/       Constitution plane — approved equivalence baselines (.verified). Human-promoted only.
docs/         Diátaxis docs + docs/adr/ (append-only MADR) + docs/glossary.md (ubiquitous language).
libs/python/  The harness's language-neutral §4.3–4.6 normalization core — STAYS in core.  → see libs/python/AGENTS.md
libs/         + normalize-spec.md (canonical rule spec) + normalize-fixtures/ (shared (raw,canonical) corpus).
tools/        The reusable engine (Python): contract_hash, contract_drift, golden_runner,
              harness_config, harness_lint, memory_regen, bootstrap.
harness/      The reusable harness config: project.toml (language/instance slot), agents/, commands/,
              skills/, permission-matrix.json.
.memory/      Derived/volatile plane. state/ committed; derived/ gitignored + auto-regenerated (never hand-edit).

INSTANCES — domain seeds, the demoted specifics ─────────────────────────────────────
examples/<instance>/   A domain seed: its own contracts/, golden/, components/, language-side
                       normalize twin, tests + manifest. Depends on the core; the core never
                       depends on it. Reference instance = examples/log-parser/ (semiconductor
                       equipment-log domain).  → see examples/log-parser/AGENTS.md
```

The active language/toolchain set is a **DATA slot** in `harness/project.toml` (`[instance]` root +
`[[languages]]`). The log-parser instance supplies **.NET 10** (parser/converter, CPU-bound) +
**Python/uv** (scheduler/collector); those two talk only across process/file/DB boundaries. Cloning
this repo as a fresh template = swap the instance under `examples/` + that config. **Domain
specifics live with the instance** — see `examples/log-parser/{AGENTS.md,README.md}` and the
`docs/explanation/template-and-instances.md` narrative.

## Golden-path commands (Phase-1 tooling)

| Task | Command |
|------|---------|
| Run all tests | `uv run pytest` |
| Contract-drift gate (JCS SHA-256 over `contracts/**/*.schema.json`) | `bash tools/contract_drift/check.sh` (or `python -m tools.contract_drift.drift`) |
| Contract hash baseline/manifest | `python -m tools.contract_hash.hash` |
| Golden equivalence runner (normalize both sides, diff vs `.verified`) | `python -m tools.golden_runner.runner` |
| Promote a golden baseline (human-gated) | `python -m tools.golden_runner.approve --approve --adr <id>` |
| Regenerate derived memory (repo-map / contracts-index) | `python -m tools.memory_regen.repo_map` · `python -m tools.memory_regen.contracts_index` |
| Assemble the SessionStart injection payload | `python -m tools.memory_regen.inject` |

## Non-negotiable rules

1. **Contract-first.** `contracts/` is the single source of truth. **Code that disagrees
   with the contract is wrong — fix the code, not the contract.** A contract change is a
   deliberate act that carries a golden / contract-drift gate (schema-hash moves without a
   paired golden update = CI fail).

2. **Polyglot §4.3–4.6 boundary invariants.** Cross-language equivalence is only ever
   checked **after** the shared canonicalization core runs — never a raw byte-diff. The
   invariants: UTF-8 with **BOM stripped**, forced **LF**, InvariantCulture `.` decimals,
   tolerance-aware float compare, deterministic key/row ordering, **UTC** ISO-8601
   timestamps, explicit TSV escape + null-vs-empty token. Language boundary =
   process/file/DB only (A-model); no in-process object passing.

3. **Constitution plane is gated — machines gate, humans ratify.** Agents do **not** write
   to `contracts/`, `docs/adr/`, or `golden/`. These are human-owned / CODEOWNERS-gated;
   no agent self-blesses a golden baseline or edits an ADR (ADRs are append-only /
   supersede-not-edit). Runtime enforcement lands in Phase-4 hooks; this rule is advisory
   until then.

4. **Derived plane is not hand-edited.** `.memory/derived/` (repo-map, contracts-index) is
   regenerated by `tools/memory_regen`. Delete + rerun reproduces it byte-identically. Never
   hand-edit derived artifacts; decisions belong in append-only ADRs, not `.memory/state/`.

5. **Lazy-load rule.** Do **not** preload full contract bodies into context. Use the injected
   contracts-index / repo-map **pointers** and read a specific contract only when the task
   needs it. This is the mechanism the SessionStart injector implements (~1k-token cap,
   pointer-only, data-authority-banner-first). On a **data** conflict, `contracts/` and
   `docs/adr/` are authoritative over volatile `.memory/state/` — this determines which
   artifact wins a contradiction, not whether grounded work should be distrusted.

## Working in a package

Read the per-package `AGENTS.md` **only when you touch that package** (lazy-load). Each
per-package file is self-sufficient: it carries its language-local commands **and** restates
the non-negotiables above — contract-first, the §4.3–4.6 boundary invariants, and
constitution-plane-is-gated (P11 backstop).

<!-- BEGIN HARNESS-MANAGED (generated by tools.harness_emit — do not hand-edit) -->
## Harness-Emitted Runtime Surface

This block is generated by `tools.harness_emit` from the runtime-neutral `harness/` source and projected into both runtime trees (`.opencode/` + `.claude/`). Do not hand-edit — a re-emit overwrites it. Everything OUTSIDE the HARNESS-MANAGED markers is preserved verbatim.

- **Agents** (`.opencode/agent/` · `.claude/agents/`): code-reviewer, curator, explorer, orchestrator, python-engineer
- **Commands** (`.opencode/command/` · `.claude/commands/`): add-language, adr, agree, build, checkpoint, component, contract-check, docs-sync, fan-out-synthesize, golden, golden-approve, intake, lint, new-contract-rule, orient, phase-gate, pipeline, refresh-memory, review, strangler-step, test, verify-work
- **Skills** (`.opencode/skill/` · `.claude/skills/`): context-budget, data-contracts, fan-out-synthesize, gate-model, golden-debug, golden-testing, pipeline-map, polyglot-boundary, python-conventions, skill-creator, two-plane-memory
- **Plugins** (`.opencode/plugin/`) + root `opencode.json` — see `tools/harness_emit/emit-manifest.json` for the full owned-path set.
<!-- END HARNESS-MANAGED -->
