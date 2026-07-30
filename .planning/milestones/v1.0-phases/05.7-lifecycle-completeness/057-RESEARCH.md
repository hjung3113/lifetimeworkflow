---
phase: 5.7
slug: lifecycle-completeness
status: ready
created: 2026-07-09
---

# Phase 5.7 — Research (Lifecycle Completeness)

> Source of truth: `057-CONTEXT.md` (`<audit_findings>` + `<decisions>` are ground truth — the
> audit is NOT re-run here). This doc verifies, per gap, the **reused tool**, the **authoring
> shape**, and — CRITICAL (Phase 5.5 lesson) — the **exact `harness_lint` expected-set / guard
> token each new asset must be added to in the SAME wave**. No new external packages.

---

## Reused tools & specs (verified, no re-implementation)

| New asset | Reuses (verified) | Call site |
|---|---|---|
| **LIFE-01 `/contract-check`** | `check-jsonschema==0.37.4` (pinned `pyproject.toml:21`); `tools/contract_drift.drift.run_gate` (`main` prints OK/DRIFT, exit 0/1); `tools/contract_hash.hash` (`--write` rebaselines) | `check-jsonschema --schemafile <schema> <instance>` over `contracts/**` + `uv run python -m tools.contract_drift.drift` |
| **LIFE-02 `golden-debug`** | `tools/golden_runner/runner.py` (`case_dir`/`verified_path`/`received_path`; `.received`/`.verified` under `golden/<case>/expected/`); `libs/normalize-spec.md` R1–R7; `libs/python/normalize`; CLAUDE.md canonicalization table | skill body = decision tree; `references/canonicalization-axes.md` = the 7-axis table |
| **LIFE-03 `polyglot-boundary`** | `libs/normalize-spec.md` R1–R7; CLAUDE.md §"Golden-Equivalence Comparator" table; AGENTS.md non-negotiable #2 | skill body = the single-source invariant map; `references/` folds the CLAUDE.md table |
| **LIFE-04 engineer template + `/add-language`** | `harness/project.toml` `[[languages]].persona` slot; `harness/agents/python-engineer.md` as the reference instantiation; `tools/harness_config/loader.py` | template lives OUTSIDE the `harness/agents/*.md` glob; scaffold derives a persona into the **instance** dir + appends a `[[languages]]` table |
| **LIFE-05 `/new-contract-rule`** | existing `harness/commands/new-normalization-rule.md` body (already contract-first, order-enforced) | `git mv` → rename + neutralize the "normalization/correction rule" naming; its dead `/contract-check` ref is resolved by LIFE-01 |
| **LIFE-06 `/orient`** | `tools/memory_regen` (`repo_map`/`contracts_index`/`inject.assemble`); AGENTS.md golden-path table | `!` macro over `python -m tools.memory_regen.*` — replaces the deferred opencode injector as an explicit entry point |
| **LIFE-07 `/review`** | `harness/agents/code-reviewer.md` (read-only); `tools/hooks/secret_scan.py` | `!git diff` → route to `code-reviewer` → severity-classified findings |
| **LIFE-08 `gate-model`** | `harness/permission-matrix.json` (`path_deny_globs`: `contracts/**`, `docs/adr/**`, `golden/**`); `tools/hooks/{contract_guard,secret_scan,commit_gate}`; `tools/golden_runner/approve.py` (exit 3); `tools/strangler_guard` | skill body = the gate map |
| **LIFE-09 `two-plane-memory`** | AGENTS.md non-negotiables #3/#4/#5; `.memory/state` (committed) vs `.memory/derived` (gitignored) | skill body = the two-plane rule map |
| **LIFE-10 `/verify-work`** | composes `/lint` + `/test` + `/contract-check` + `/golden` (all existing macros) | `!` macro chaining the four in-session gates; distinct from Phase-6 CI + `/checkpoint` |
| **LIFE-11 orchestrator routing** | augment `harness/agents/orchestrator.md` (no new persona) | add a compact routing decision table + intake→decompose procedure |

### The 7 canonicalization axes (LIFE-02 decision tree — from `libs/normalize-spec.md` R1–R7)

1. **Encoding / BOM (R1, §4.3)** — leading `EF BB BF`? → first column misreads. Fix: strip BOM (`utf-8-sig` / `new UTF8Encoding(false)`).
2. **Newlines (R2, §4.3)** — CRLF/lone-CR vs LF → line-split mismatch. Fix: force LF.
3. **Decimal & culture (R3, §4.6)** — `1,5` vs `1.5`, trailing-zero repr → false diff. Fix: InvariantCulture `.`, decimal types (never float round-trip).
4. **Float compare tolerance (R4, §4)** — last-digit float repr flips a golden. Fix: tolerance-aware compare (`1e-9`), not string-exact.
5. **Key/row ordering (§4)** — unordered rows/keys → false diff. Fix: deterministic sort before diff.
6. **Timezone / datetime (R5, §4.4)** — `DateTime.Kind` vs naive/aware → offset drift. Fix: UTC ISO-8601 `yyyy-MM-ddTHH:mm:ssZ`.
7. **TSV escape / null-vs-empty (R6/R7, §4.3)** — tab/newline-in-value + `"" ≠ null` token. Fix: agreed escape + explicit `null_token` (`\N` → `<NULL>` sentinel).

Each axis in the skill gets a **"is this the cause?"** discriminator + a **"which side to fix"**
(regressed code vs intentional change → data case + human approval + ADR — never edit `.verified`).

---

## CRITICAL: harness_lint guard-update map (Phase 5.5 lesson — update IN-WAVE)

Verified by reading `tools/harness_lint/tests/*`. Each new asset must be reconciled with these or
the suite goes RED.

| Guard test | Assertion kind | New-asset obligation |
|---|---|---|
| `test_skills.py::test_expected_skills_present_no_sprawl` | **EXACT MATCH** `EXPECTED_SKILLS` | MUST add every new skill dir: `golden-debug`, `polyglot-boundary`, `gate-model`, `two-plane-memory` → set grows 4 → 8. |
| `test_skills.py` (parametrized) | per-skill caps | name ≤64 & `^[a-z0-9]+(-[a-z0-9]+)*$` & == dir; desc ≤1024, carries `use`/`when`, **disjoint**, no `anthropic`/`claude`, no `<`/`>`. |
| `test_agents.py::test_expected_personas_present_no_sprawl` | **EXACT MATCH** `EXPECTED_PERSONAS` | Engineer **template** MUST live outside `harness/agents/*.md` (glob is non-recursive) → put at `harness/agents/templates/engineer.md`. Set stays 4. Derived instance personas land under `examples/<instance>/agents/`, not core. |
| `test_commands.py::test_golden_adjacent_commands_present` | **SUBSET** (only the 8 golden-adjacent must exist) | New commands do NOT need an EXPECTED edit — but parametrized per-command gates below apply. |
| `test_commands.py` (parametrized) | per-command frontmatter | Each new command: valid frontmatter, `description` with `use`/`when`, `agent:` a well-formed slug, `subtask` boolean if present. |
| `test_agent_referential_integrity.py` | cross-file resolve | Each new command's `agent:` MUST be one of the 4 real personas: `orchestrator`, `python-engineer`, `code-reviewer`, `explorer`. |
| `test_core_no_example_dep.py` | **prose + path guard** | Every new CORE asset must avoid `_PROSE_TOKENS` (`dotnet-engineer`, `dotnet-conventions`, `normalization-catalog`, `pipeline-patterns`, `libs/dotnet`, `equipment`, `standard-log`, `correction-rules`, `wafer`, `설비`) + `examples/` path refs. Bare `dotnet`/`.NET`/`parser`/`converter`/`normalize`/`log-parser` are ALLOWED (general). |
| `test_language_config.py` (GEN-03) | config↔matrix↔persona agreement | `/add-language` appends a `[[languages]]` table; the persona pointer + `bash_scope` must agree with `permission-matrix.json`. Log-parser instance's existing dotnet/python rows already pass — a NEW instance language would need its own row + matrix scope. LIFE-04 ships the **template + scaffold**, not a new active language, so the GEN-03 gate stays green untouched. |

### Command `agent:` assignments (referential-integrity safe)
- `/contract-check` → `python-engineer` · `/new-contract-rule` → `python-engineer` (unchanged) ·
  `/add-language` → `python-engineer` · `/orient` → `orchestrator` · `/review` → `code-reviewer` ·
  `/verify-work` → `orchestrator`.

---

## Locked-constraint conformance (per 057-CONTEXT `<decisions>` "고정")
- **Domain-neutral:** golden-debug/polyglot-boundary/gate-model/two-plane-memory phrase §4.3–4.6 with
  general terms only; no `_PROSE_TOKENS`. Engineer template is generic ("engineer", "the language's
  toolchain") — the .NET twin stays an *example* concern.
- **Skill caps:** bodies target <500 lines; depth → `references/` (progressive disclosure).
- **`code-reviewer` read-only:** `/review` routes TO it; it gains no write affordance.
- **Least privilege:** every new command is a thin macro over existing tools; no new broad bash scopes.
- **Reuse `tools/`:** zero re-implementation (table above). **No model identifiers** in any artifact.
- **ADEQUATE untouched:** `golden-testing`, `docs-sync`, `adr`, `strangler-step`, `component`, `/golden*`, `/test` unchanged.
- **git mv** for LIFE-05 rename.

## Constitution plane / approval token
- No `contracts/`, `docs/adr/`, or `golden/` writes are planned (all new assets are `harness/` +
  `.planning/`). → **No `GOLDEN_APPROVE_HUMAN` token needed.** Decision: record NO lifecycle ADR
  (the CONTEXT + REQUIREMENTS §LIFE already carry the rationale; an ADR would need the gated approval
  path for no added enforcement value). If a future reviewer wants the decision immortalized, that is
  a separate gated ADR write.

## Validation invariant
- Phase-wide: the non-example `uv run pytest` suite stays GREEN, and after the phase
  `test_core_no_example_dep.py` reads 0 core-prose domain tokens on the new assets.
