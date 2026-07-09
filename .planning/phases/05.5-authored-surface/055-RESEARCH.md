# Phase 5.5: Authored-Surface Genericization (GEN-05) — Research

**Researched:** 2026-07-09
**Domain:** Template de-specialization of the *authored* harness surface (skills / agents / commands) — markdown moves + a prose-purity guard extension. No runtime logic, no external packages.
**Confidence:** HIGH (all claims verified against source with file:line; single self-contained repo, no version/ecosystem uncertainty)

<user_constraints>
## User Constraints (from 055-CONTEXT.md)

### Locked Decisions
- **D-01 — 3-way classification (FIXED):**
  - **Core (stays):** skills `golden-testing`, `skill-creator`, `data-contracts` (body genericized), **`python-conventions`**; personas `orchestrator`, `code-reviewer`, `explorer`, **`python-engineer`**; commands `build`, `test`, `lint`, `golden`, `golden-approve`, `adr`, `checkpoint`, `component`, `strangler-step`, `docs-sync`, `new-normalization-rule` (body genericized).
  - **Move → `examples/log-parser/` (domain):** skills `normalization-catalog`, `pipeline-patterns`.
  - **Move → `examples/log-parser/` (instance language):** skill `dotnet-conventions`, persona `dotnet-engineer`.
- **D-02 —** `new-normalization-rule` stays core; strip semiconductor examples → domain-neutral; name kept (general word); contract-first ORDER logic unchanged.
- **D-03 —** language personas/skills MOVE (source cleanup); `project.toml` is SSOT; per-language *emit* is Phase 7. Permission-matrix `dotnet *` allow-scope is instance-slot data — stays.
- **D-04 —** extend GEN-04 guard to **prose** domain tokens, **carefully** (allowlist, negative-control per token; do NOT retreat to SCOPE-A if over-flagging — refine the token list). Post-move core grep of these tokens = 0.
- **D-05 —** update docs for new locations; update `harness_lint` anti-sprawl expected lists (Phase-3 tests PIN the exact set).

### Claude's Discretion
- Exact `examples/` sub-location for moved skills/agents; genericized example wording; guard token list + allowlist; how the `harness_lint` expected lists are updated.
- **FIXED:** the 3-way split, python-is-core / dotnet-is-instance, `new-normalization-rule` stays+genericized, guard prose extension (careful), logic unchanged, non-example suite green after move.

### Deferred Ideas (OUT OF SCOPE)
- Per-language authored-surface **emit** (`project.toml` → dotnet persona generation) → Phase 7.
- New domain examples; Phase 6 CI / Phase 7 emitter; any normalization/gate logic change.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GEN-05 | Strip domain/language specialization from the authored harness surface: demote domain skills to the example, move instance-language persona/skill to the example, genericize surviving core assets' bodies, extend the GEN-04 guard to prose. | This document: exact move set + destinations (§Architecture Patterns), every `harness_lint` test that goes RED + the precise edit (§Common Pitfalls P1), the extended-guard token list + allowlist + negative-controls (§Architecture Patterns "Guard Shape"), the complete core prose-token inventory to sweep (§Code Examples "Core token inventory"), and doc updates (§Runtime State Inventory). |
</phase_requirements>

## Summary

Phase 5 moved the **data plane** (contracts/golden/`libs/dotnet`) to `examples/log-parser/`. Phase 5.5 moves the **authored surface** and purges domain vocabulary from what stays. Concretely: `git mv` three skills (`normalization-catalog`, `pipeline-patterns`, `dotnet-conventions`) and one persona (`dotnet-engineer`) into `examples/log-parser/`, genericize the bodies of `data-contracts`, `new-normalization-rule` (and, forced by the constraints below, `strangler-step` + the core personas `orchestrator`/`explorer` + `libs/normalize-spec.md`), and extend the GEN-04 guard from CODE-dependency tokens to a small, precise set of DOMAIN/LANGUAGE *prose* tokens.

The single largest risk is not the moves themselves but the **web of hardcoded expectations** the moves invalidate. Four `harness_lint` tests go RED the instant an asset leaves `harness/`, and three of them are *not* obvious from the file being moved: an anti-sprawl skill-set pin, an anti-sprawl persona-set pin, a **command→persona referential-integrity** test (because `strangler-step.md` declares `agent: dotnet-engineer`, `[VERIFIED: harness/commands/strangler-step.md:6]`), and a **`project.toml` persona-path existence** test (because `project.toml` points `dotnet.persona = "harness/agents/dotnet-engineer.md"`, `[VERIFIED: harness/project.toml:27]`). These four edits MUST land in the same wave as the `git mv`, or the suite is RED between steps.

The guard extension is the delicate part. A naive prose scan for "dotnet", ".NET", "parser", "converter", or "normalize" would flag dozens of *legitimately general* core lines (argparse `parser`, `golden_runner` spawning "the converter", `logparser-*` package names). The correct design is a **narrow token set of proper nouns + rare vocab** (moved-asset slugs, `libs/dotnet` path, `equipment`/`standard-log`/`correction-rules`/`wafer`/`설비`) that — after the move + a bounded prose sweep — is provably 0 in the scanned core, with one sanctioned exemption for the `harness/project.toml` instance-pointer lines (which must legitimately name the moved `dotnet-engineer` persona under `examples/`).

**Primary recommendation:** One wave, ordered: (1) `git mv` the 4 assets to `examples/log-parser/{skills,agents}/`; (2) in the SAME change, update `EXPECTED_SKILLS`→4, `EXPECTED_PERSONAS`→4, repoint `strangler-step` agent to `orchestrator`, repoint `project.toml` `dotnet.persona` to the new `examples/` path; (3) sweep the enumerated core prose tokens (§Code Examples); (4) extend the guard with the narrow token set + a `project.toml` pointer-line exemption + one negative-control per token; (5) update `examples/log-parser/{AGENTS.md,README.md}` layout. Then `uv run pytest` (non-example suite) is green. Zero new packages.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Domain skill content (correction catalog, pipeline scenarios) | Instance (`examples/log-parser/skills/`) | — | Semiconductor-specific knowledge; not reusable by another domain (ADR-0002 "core is domain-neutral"). |
| Instance-language persona/skill (`dotnet-engineer`, `dotnet-conventions`) | Instance (`examples/log-parser/{agents,skills}/`) | — | .NET is a language the *log-parser instance* declares in `project.toml [[languages]]`; "core is language-neutral" (ADR-0002 (b)). |
| Python persona/skill (`python-engineer`, `python-conventions`) | Core (`harness/`) | Instance reuse (allowed: example→core) | The harness itself is authored in Python (`tools/*`) — Python is "the language the core is built in", the ADR-0002 (b) stated exception. |
| Contract-first methodology (`data-contracts`, `new-normalization-rule`) | Core (`harness/`) | — | Contract-first ordering is domain-neutral machinery; only the *examples* in the body are domain-specific → genericize body, keep asset. |
| Legacy-extraction discipline (`strangler-step`) | Core (`harness/`) | — | Strangler-fig is a general migration pattern; `tools/strangler_guard` is language-neutral (structural path slugify, `[VERIFIED: tools/strangler_guard/guard.py:40]`) → genericize prose, repoint agent off the moved persona. |
| Core→instance dependency invariant (now incl. prose) | Core guard (`tools/harness_lint`) | — | Tamper-evident prose-purity extension of the Phase-5 GEN-04 guard. |
| Language/toolchain declaration (incl. persona pointers) | Instance-data slot (`harness/project.toml`) | — | Pure data; the one sanctioned place a core file names an instance-owned asset (ADR-0002 (c)). |

## Standard Stack

No new libraries. This phase is markdown file moves + Python test edits inside the existing `tools/harness_lint` package.

| Existing tool | Version (per CLAUDE.md) | Role in this phase |
|---------------|-------------------------|--------------------|
| `git mv` | — | History-preserving move of 4 authored files (matches Phase-5 precedent). |
| `pytest` (via `uv run pytest`) | `>=8.4,<9` | Runs the `harness_lint` structural suite that gates the move. |
| `tools.harness_lint.parse_frontmatter` | in-repo | Shared frontmatter parser reused by all structural tests (no re-implementation). |

**Package Legitimacy Audit:** N/A — zero external packages installed or added this phase.

## Architecture Patterns

### Pattern 1: Move destinations (confirmed by existing consumers)

- **Skills →** `examples/log-parser/skills/<name>/SKILL.md` (`normalization-catalog`, `pipeline-patterns`, `dotnet-conventions`).
- **Persona →** `examples/log-parser/agents/dotnet-engineer.md`.

**Confirmation the destination is correct / orphan-free:**
- `harness_lint` discovers skills/agents purely **by directory glob**, not a hardcoded path list: `_SKILLS_DIR / "*/SKILL.md"` `[VERIFIED: tools/harness_lint/tests/test_skills.py:27,61]` and `_AGENTS_DIR / "*.md"` `[VERIFIED: tools/harness_lint/tests/test_agents.py:21,67]`. So moved-out assets simply **vanish** from the scanned set — the only edit needed is the anti-sprawl *expected* frozenset (see P1).
- `harness/opencode.json` declares **no skill/agent glob** — only `instructions: ["AGENTS.md","**/AGENTS.md"]` and `plugin: ["harness/plugins/session-inject.ts"]` `[VERIFIED: harness/opencode.json:8,31]`. Moving skill/agent source does **not** touch `opencode.json`. Runtime emit is Phase 7 (out of scope).
- The persona destination is **dictated** by `project.toml` + `test_each_configured_persona_exists`, which resolves `_REPO_ROOT / lang["persona"]` and asserts the file exists `[VERIFIED: tools/harness_lint/tests/test_language_config.py:48-52]`. Point `project.toml` `dotnet.persona` at the new location and the test resolves.
- No other repo file references the moved slugs (grep of `AGENTS.md CLAUDE.md README.md docs/ examples/ .memory/` for all four slugs returned **empty** — verified this session). No orphaned reference outside the `harness_lint` expected-lists.

### Pattern 2: Genericize-body-keep-asset (D-02)

For `data-contracts`, `new-normalization-rule`, `strangler-step`: reword only the domain *examples/prose*; the **methodology/order logic is unchanged**. E.g. `new-normalization-rule.md`'s mandated order (contract → (input,expected) data case → failing stub) `[VERIFIED: harness/commands/new-normalization-rule.md:21-40]` stays verbatim; only the `contracts/normalization/correction-rules.catalog.yaml` / `equipment` example references are swapped for the generic instance (`contracts/sample`, a neutral `greeting`/`record` example).

### Pattern 3: Guard Shape (D-04 prose extension) — narrow tokens + one exemption

Extend `tools/harness_lint/tests/test_core_no_example_dep.py`. Keep the SCOPE-A `_PATH_TOKENS = ("examples/", "components/toy-converter")` and `import examples` `[VERIFIED: test_core_no_example_dep.py:41,44]`. **Add a second tier** of prose tokens:

```python
# Prose domain/language tokens (GEN-05): moved-asset proper nouns + rare domain vocab.
# Chosen narrow enough that NO legitimately-general core line matches (no bare "dotnet"/".NET"/
# "parser"/"converter"/"normalize"/"log-parser" — those are general and stay).
_PROSE_TOKENS = (
    "dotnet-engineer", "dotnet-conventions", "normalization-catalog", "pipeline-patterns",
    "libs/dotnet", "equipment", "standard-log", "correction-rules", "wafer", "설비",
)
```

**Scan roots:** unchanged — `git ls-files tools harness libs` `[VERIFIED: test_core_no_example_dep.py:32,55]` (root `AGENTS.md`/`CLAUDE.md`/`README.md`/`docs/` are NOT scanned, which correctly bounds the sweep to core planes).

**Exemptions (the allowlist):**
1. **Self-exclusion** — the guard file holds the tokens as negative-control literals and is excluded from its own scan (existing mechanism, `[VERIFIED: test_core_no_example_dep.py:36,68-69]`).
2. **`harness/project.toml` instance-pointer lines** — generalize the existing `_is_instance_root_line` (currently only the `root =` line, `[VERIFIED: test_core_no_example_dep.py:74-76`]) to also skip `persona =` lines. Rationale: `project.toml` is the ONE sanctioned instance-data file (ADR-0002 (c)); its `dotnet.persona` legitimately points at `examples/log-parser/agents/dotnet-engineer.md` — a line that contains BOTH the SCOPE-A `examples/` token AND the new `dotnet-engineer` token. Exempting the whole pointer line covers both. (`project.toml` comment line 5 says "log-parser example instance" — `log-parser` is deliberately NOT a token, so no exemption needed there.)

**No broad allowlist is required** beyond these two: every *other* current core occurrence of a token is either (a) removed by the move, or (b) reworked by the bounded prose sweep (§Code Examples). Verified there is no legitimately-general core line that matches a chosen token and cannot be reworded.

**Negative controls (one per new token):** add a parametrized test crafting a synthetic core line per token and asserting `_scan_lines` flags it — mirrors the existing three negative-control tests `[VERIFIED: test_core_no_example_dep.py:114-129]`. `wafer`/`설비` are pure negative-control tokens (0 real occurrences — safest).

### Anti-Patterns to Avoid
- **Hard-flagging bare `dotnet`/`.NET`/`parser`/`converter`/`normalize`/`log-parser`.** These appear legitimately across core: `argparse` `parser` variables, `golden_runner` spawning "the .NET converter" `[VERIFIED: tools/golden_runner/runner.py:159-224]`, `logparser-*` distribution names in every `tools/*/pyproject.toml`, and test comments that name "the log-parser example" to explain the instance relationship. Flagging them would RED the suite on general text (exactly the D-04 warning). Keep them OUT of the token set.
- **Moving `strangler-step` to `examples/` to dodge the referential-integrity break.** D-01 locks it as core. The correct fix is repoint its `agent:` to a core persona + reword its `.NET parser/converter` prose to language-neutral.
- **Landing the `git mv` and the expected-list edits in separate commits.** The suite is RED in between; keep them atomic.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Move history | `cp` + `rm` | `git mv` | Preserves blame/history (Phase-5 precedent, ADR-0002 "history-preserving `git mv`"). |
| Frontmatter parse in the guard/tests | Per-test fence slicing | existing `tools.harness_lint.parse_frontmatter` `[VERIFIED: test_skills.py:23]` | One shared parser is the established idiom. |
| Prose scan | A new bespoke linter | Extend `test_core_no_example_dep.py` | The Phase-5 guard already has the `git ls-files` scan loop, self-exclusion, and negative-control scaffold `[VERIFIED: test_core_no_example_dep.py:53-135]`; D-04 explicitly makes it the base. |

## Runtime State Inventory

> Rename/refactor phase — all five categories answered.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | None — no datastore keys on the moved slugs. Skills/agents/commands are markdown source; no DB, no `.memory/` derived file names them (grep of `.memory/` empty, verified). | None. |
| **Live service config** | `harness/opencode.json` — declares NO skill/agent path glob; only `instructions`/`plugin` `[VERIFIED: harness/opencode.json:8,31]`. `harness/permission-matrix.json` names only `"dotnet *"` bash scope `[VERIFIED: harness/permission-matrix.json:8]` — instance-slot DATA, stays (D-03), does not name the persona. | None to `opencode.json`/matrix. |
| **OS-registered / config-registered state** | `harness/project.toml` `[[languages]]` dotnet block: `persona = "harness/agents/dotnet-engineer.md"` `[VERIFIED: harness/project.toml:27]` — a **path pointer to the moved persona**. | **Code edit:** repoint to `examples/log-parser/agents/dotnet-engineer.md` (+ guard pointer-line exemption). |
| **Cross-references (command→persona, persona→persona)** | (1) `harness/commands/strangler-step.md:6` `agent: dotnet-engineer` `[VERIFIED]` — dangling after move. (2) `harness/agents/orchestrator.md:6,23` and `harness/agents/explorer.md:20` name `dotnet-engineer` in prose `[VERIFIED]`. (3) `libs/normalize-spec.md:7` references `libs/dotnet/Normalize` `[VERIFIED]`. | **Code edits:** repoint strangler-step agent → `orchestrator`; reword orchestrator/explorer to drop `dotnet-engineer`; reword `libs/normalize-spec.md` `libs/dotnet` → "a language-side twin". |
| **Build artifacts / installed packages** | None — no compiled artifact carries a skill/agent name; `logparser-*` dist names are pre-existing and NOT in the token set (out of scope). | None. |

**The canonical check:** After every `harness/skills`/`harness/agents` move, what still points at the old path? Answer: exactly `project.toml:27` (path), `strangler-step.md:6` (agent ref), and the two `harness_lint` expected frozensets — all enumerated in P1.

## Common Pitfalls

### Pitfall 1: Four `harness_lint` tests go RED on the move — three are non-obvious
**What goes wrong:** The `git mv` alone turns the non-example suite RED in four places.
**Exact failures + edits (sequence these WITH the move):**

| # | Test (id) | Why RED | Exact edit |
|---|-----------|---------|------------|
| 1 | `test_skills.py::test_expected_skills_present_no_sprawl` `[VERIFIED:tools/harness_lint/tests/test_skills.py:48-58,69-74]` | Glob finds 4 skills; `EXPECTED_SKILLS` pins 7 incl. the 3 moved. | `EXPECTED_SKILLS = {"python-conventions","golden-testing","data-contracts","skill-creator"}` |
| 2 | `test_agents.py::test_expected_personas_present_no_sprawl` `[VERIFIED:tools/harness_lint/tests/test_agents.py:52-54,95-101]` | Glob finds 4 personas; `EXPECTED_PERSONAS` pins 5 incl. `dotnet-engineer`. | `EXPECTED_PERSONAS = {"orchestrator","python-engineer","code-reviewer","explorer"}` |
| 3 | `test_agent_referential_integrity.py::test_command_agent_resolves_to_real_persona[strangler-step]` `[VERIFIED:tools/harness_lint/tests/test_agent_referential_integrity.py:42-56]` | Glob-driven; `strangler-step.md:6 agent: dotnet-engineer` no longer resolves to a `harness/agents/*.md` file. | Repoint `strangler-step.md` `agent: orchestrator` (+ genericize its `.NET parser/converter` prose). |
| 4 | `test_language_config.py::test_each_configured_persona_exists` `[VERIFIED:tools/harness_lint/tests/test_language_config.py:48-52]` | `project.toml dotnet.persona` path file no longer exists. | `project.toml:27 persona = "examples/log-parser/agents/dotnet-engineer.md"` (+ guard pointer-line exemption, else the extended guard flags this line). |

**Not affected (verified):**
- `test_commands.py::test_golden_adjacent_commands_present` — asserts `EXPECTED_GOLDEN_ADJACENT - names == ∅`, i.e. **extras allowed, no exact-set pin** `[VERIFIED:tools/harness_lint/tests/test_commands.py:56-60]`. `new-normalization-rule`/`strangler-step`/`docs-sync` remain valid; no command-set edit needed.
- `test_language_config.py::test_matrix_language_scopes_equal_config` — checks scope equality only `[VERIFIED:test_language_config.py:39-45]`; moving a persona *file* doesn't change scopes. `python.persona` stays `harness/agents/python-engineer.md` (core).
- Per-file structural tests (caps, frontmatter) for the moved skills/agents are **parametrized over the glob** → they simply stop being collected. No failure. (Side effect: the moved assets lose structural validation — see Open Question 1.)

**Warning sign:** any `assert names == set(EXPECTED_*)` failure message printing "got […4…], expected […5/7…]".

### Pitfall 2: The extended guard flags legitimately-general core text (over-reach)
**What goes wrong:** Adding `dotnet`/`.NET`/`parser`/`converter`/`normalize`/`log-parser` to the token set RED-flags argparse `parser`, `golden_runner`'s ".NET converter", `logparser-*` package names, and "the log-parser example" explanatory comments.
**How to avoid:** Use the narrow proper-noun/rare-vocab token set in §Pattern 3. Prove each token is 0 in post-sweep core (the guard IS that proof) and add a negative-control per token so the scan can't silently no-op. `wafer`/`설비` guarantee 0 today (safest anchors).
**Warning sign:** the guard's offender list printing a `tools/*/pyproject.toml` `name = "logparser-..."` line or an `argparse.ArgumentParser` line — means a too-general token leaked into the set.

### Pitfall 3: The `project.toml` persona path becomes a self-inflicted guard leak
**What goes wrong:** After repointing `dotnet.persona` to `examples/log-parser/agents/dotnet-engineer.md`, that line contains `examples/` (SCOPE-A token) **and** `dotnet-engineer` (new token) → the guard flags `project.toml`.
**How to avoid:** Extend the existing `project.toml` exemption from the `root =` line to the `persona =` lines (§Pattern 3 exemption 2). Add a positive test that the exempted `persona = "examples/..."` line is NOT flagged (mirrors `test_instance_root_pointer_is_exempt` `[VERIFIED:test_core_no_example_dep.py:132-135]`).

## Code Examples

### Core prose-token inventory to sweep (the exhaustive list the guard will enforce → 0)

Every current core (`tools/`+`harness/`+`libs/`) occurrence of a chosen token, classified. VANISH = removed by the move/list-update; REWORD = bounded prose edit; EXEMPT = sanctioned pointer.

**`dotnet-engineer`:** `test_agents.py:53` (VANISH via list update) · `test_core_no_example_dep.py:11` (self-excluded) · `harness/agents/dotnet-engineer.md` (MOVE) · `orchestrator.md:6,23` (REWORD → drop specialist naming) · `explorer.md:20` (REWORD) · `project.toml:27` (EXEMPT pointer, repointed) · `strangler-step.md:6` (REWORD → `agent: orchestrator`). `[all VERIFIED this session]`

**`dotnet-conventions` / `normalization-catalog` / `pipeline-patterns`:** only in `test_skills.py:50,55,56` (VANISH via list update) + `test_core_no_example_dep.py:11-12` (self-excluded) + their own skill dirs (MOVE). Post: 0.

**`libs/dotnet`:** `memory_regen/tests/test_agents_md.py:22,43` (REWORD comment → "the instance's language-side package") · `test_core_no_example_dep.py:10,40` (self-excluded) · `dotnet-conventions`/`dotnet-engineer` (MOVE) · `libs/normalize-spec.md:7` (REWORD → "a language-side twin"). `[VERIFIED]`

**`equipment`:** `contract_drift/tests/test_classify.py:23,26,58,65` — the sample schema field `equipment_id` (REWORD → neutral field e.g. `record_id`; it is arbitrary fixture data, not load-bearing) · `docs_sync/tests/test_docs_sync_determinism.py:23` (REWORD comment) · `pipeline-patterns`/`data-contracts` (MOVE / genericize). `[VERIFIED]`

**`standard-log`:** `docs_sync/tests/test_docs_sync_determinism.py:23,129` (REWORD comments) · `data-contracts:20` (genericize). `[VERIFIED]`

**`correction-rules`:** `contract_drift/drift.py:10` + `contract_drift/tests/test_classify.py:3` + `docs_sync/tests/...:23` (REWORD comments) · `normalization-catalog` (MOVE) · `data-contracts:21`, `new-normalization-rule.md:22,23` (genericize). `[VERIFIED]`

**`wafer`, `설비`:** 0 occurrences in core (verified) — pure negative-control anchors.

**Deliberately EXCLUDED (legitimately general, do NOT flag):** bare `dotnet`/`.NET`, `parser`, `converter`, `normalize`/`normalization`, `log-parser`/`logparser`, `log-spec`/`log-specs`. Examples of why: `contracts_index.py:37 "log-specs": "log-spec"` is generic contract-kind plumbing `[VERIFIED:tools/memory_regen/contracts_index.py:37]`; `golden_runner/runner.py` "converter" is the generic A-model boundary `[VERIFIED:tools/golden_runner/runner.py:139-146]`.

### `new-normalization-rule` — what to reword (D-02), what to keep
Reword the domain example anchors: `correction-rules.catalog.yaml` / `correction-rules.schema.json` / `correction_rules` `[VERIFIED:harness/commands/new-normalization-rule.md:22-23]` → the generic instance's contract (`contracts/sample/...` or an abstract `<rule-catalog>.yaml`). **Keep verbatim:** the three-step mandated order and the failing-stub forcing function `[VERIFIED:new-normalization-rule.md:21-45]`; `agent: python-engineer` (core, stays) `[VERIFIED:new-normalization-rule.md:6]`.

### `data-contracts` — semiconductor lines to genericize (D-02)
`[VERIFIED harness/skills/data-contracts/SKILL.md]`: line 20 `log-specs/ standard-log.spec.yaml`; line 21 `normalization/ correction-rules.catalog.yaml`; line 23 `reference-data/ equipment-master.yaml`; line 24 `state/ equipment-progress.yaml`. Reword the `## Layout` block to the generic instance's dirs (or abstract `<domain-spec>/`, `<rules>/`, `<reference>/`, `<state>/`). **Keep:** the contract-first rule, Draft-2020-12 shape, `check-jsonschema`, and the RFC 8785 schema-hash drift-gate prose `[VERIFIED:SKILL.md:9-52]` — methodology unchanged.

### `python-engineer` / `python-conventions` stay-in-core check (Q5)
Verified they carry **no log-parser-domain** specifics — only general Python/uv/ruff/pyright/pytest guidance + the domain-neutral §4.3–4.6 boundary and contract-first rules `[VERIFIED:harness/agents/python-engineer.md:1-35; harness/skills/python-conventions/SKILL.md:1-52]`. They reference "scheduler, collector, `tools/`" (harness roles, not semiconductor vocab) and `libs/python`/`libs/python/AGENTS.md` (core paths). **No genericization needed** — consistent with D-01 (the harness itself is Python; these describe how to work on the core). None of the guard tokens appear in either file.

## State of the Art
N/A — self-contained repo refactor; no evolving external ecosystem. The relevant "state" is the Phase-5 guard, which this phase extends (not replaces).

## Validation Architecture

**nyquist_validation:** `true` `[VERIFIED:.planning/config.json:19]` → section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (`>=8.4,<9`) via `uv run pytest` |
| Config | uv workspace root `pyproject.toml`; tests under `tools/harness_lint/tests/` |
| Quick run | `uv run pytest tools/harness_lint -q` |
| Full suite | `uv run pytest` (non-example core suite) |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Automated Command | Exists? |
|-----|----------|-----------|-------------------|---------|
| GEN-05 | Exactly the 4 core skills remain (no sprawl) | unit | `uv run pytest tools/harness_lint/tests/test_skills.py::test_expected_skills_present_no_sprawl -x` | ✅ (edit `EXPECTED_SKILLS`) |
| GEN-05 | Exactly the 4 core personas remain | unit | `uv run pytest tools/harness_lint/tests/test_agents.py::test_expected_personas_present_no_sprawl -x` | ✅ (edit `EXPECTED_PERSONAS`) |
| GEN-05 | No command dangles to a moved persona | integration | `uv run pytest tools/harness_lint/tests/test_agent_referential_integrity.py -x` | ✅ (repoint strangler-step) |
| GEN-05 | `project.toml` personas resolve on disk | unit | `uv run pytest tools/harness_lint/tests/test_language_config.py::test_each_configured_persona_exists -x` | ✅ (repoint path) |
| GEN-05 | Core planes carry 0 domain prose tokens | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -x` | ⚠️ EXTEND (add `_PROSE_TOKENS` + per-token negative-control + project.toml pointer exemption) |
| GEN-05 | `project.toml` instance pointer to `examples/` persona is exempt | unit | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py::test_instance_pointer_persona_is_exempt -x` | ❌ Wave 0 (new positive test) |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_lint -q`
- **Per wave merge:** `uv run pytest` (full non-example suite)
- **Phase gate:** full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Extend `test_core_no_example_dep.py`: `_PROSE_TOKENS`, `_scan_lines` to include them, generalize `_is_instance_root_line`→pointer-line (root+persona), one negative-control test per new token, one positive exemption test for the `persona = "examples/..."` line.
- [ ] Update `EXPECTED_SKILLS` (→4) and `EXPECTED_PERSONAS` (→4).
- [ ] No new test *file* needed — all edits extend existing modules.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `git` | history-preserving move | ✓ (repo is git) | — | — |
| `uv` + `pytest` | run structural suite | ✓ per CLAUDE.md (uv workspace) | uv 0.11.x / pytest 8.4.x | — |
| `.NET` runtime | — | ✗ (egress-deferred, BOOT-01) | — | Not needed — this phase touches no `dotnet` execution; only markdown + Python tests. |

**Missing with no fallback:** none. **Missing with fallback:** none material (no external tool the phase requires is absent).

## Security Domain

`security_enforcement` absent in `.planning/config.json` → treat as enabled. This phase adds **no** auth/session/access-control/crypto/input-parsing surface — it moves markdown and edits a structural test. The only security-relevant control is the **tamper-evident guard** (V-integrity): the extended prose scan must be *live* (negative-control per token proves it cannot silently no-op) — this is already the Phase-5 idiom `[VERIFIED:test_core_no_example_dep.py:114-129]`. No ASVS category (V2–V6) applies to a documentation/refactor change with no runtime attack surface.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `strangler-step` repoints to `agent: orchestrator` (a delegating core persona) rather than `python-engineer`. | Pitfall P1 #3 | Low — any core persona satisfies referential integrity; `orchestrator` best matches "decompose + delegate to a language engineer". Planner may prefer another core persona; either passes the tests. |
| A2 | Genericized examples use the existing generic `contracts/sample` instance (or abstract placeholders). | Code Examples | Low — must confirm `contracts/sample` exists as the generic default (Phase-5 `run_identity_converter`/`golden/sample` imply it `[VERIFIED:tools/golden_runner/tests/test_sample_loop.py:23-26]`); if not, use abstract `<...>` placeholders. |
| A3 | `equipment_id` fixtures in `test_classify.py` are freely renamable to a neutral field without breaking drift-classification logic. | Code Examples | Low — they are arbitrary JSON-schema property names in classification fixtures `[VERIFIED:tools/contract_drift/tests/test_classify.py:23-65]`; the test asserts add/remove/rename *classification*, not the specific name. |
| A4 | `examples/log-parser/{skills,agents}/` are the right sub-locations (vs a `harness-overlay/`). | Pattern 1 | Low — mirrors the instance's existing `contracts/`,`libs/`,`components/`,`tests/` layout `[VERIFIED:examples/log-parser/ listing]`; no consumer constrains it. |

## Open Questions

1. **Moved skills/agents lose structural validation.** After the move, `harness_lint`'s caps/frontmatter tests (glob over `harness/skills`,`harness/agents`) no longer cover the 4 moved assets, and the example has no equivalent validator.
   - What we know: `harness_lint` globs core dirs only; the example's `tests/` are golden-runner cases, not frontmatter lints.
   - What's unclear: whether the template should validate *instance* authored surface now or defer to Phase 7's emitter.
   - Recommendation: **defer to Phase 7** (emit-time validators per CLAUDE.md "Emit-time validators"). Note it so it isn't silently lost.

2. **`orchestrator`/`explorer` genericization wording.** They must stop naming `dotnet-engineer` but may still name `python-engineer` (core). 
   - Recommendation: reword to "the instance's language specialists (e.g. `python-engineer` for the Python core; instance-declared engineers per `project.toml`)" — keeps a concrete core example without naming a moved instance asset. Also reword `orchestrator.md:18` "polyglot log-parser monorepo" → "polyglot monorepo" (cleanliness; `log-parser` is not a guard token so this is a judgment edit, not test-forced).

3. **`docs-sync` / derived-doc regeneration.** `docs_sync` tests carry comments naming `standard-log`/`equipment`/`correction-rules` (already reworded in the sweep). Confirm no *generated* `docs/reference/**` output enumerates the moved skills (grep of `.memory/` and `docs/` for slugs was empty this session) — if a derived doc is later regenerated, it draws from source and will self-correct.

## Sources

### Primary (HIGH confidence — in-repo, file:line verified this session)
- `tools/harness_lint/tests/{test_skills.py,test_agents.py,test_commands.py,test_agent_referential_integrity.py,test_language_config.py,test_core_no_example_dep.py}` — the anti-sprawl pins, glob discovery, referential-integrity, persona-existence, and the Phase-5 guard base.
- `harness/{project.toml,opencode.json,permission-matrix.json}` — SSOT persona pointer, no skill glob, dotnet scope-slot.
- `harness/skills/{data-contracts,normalization-catalog,pipeline-patterns,dotnet-conventions,python-conventions}/SKILL.md`; `harness/agents/{dotnet-engineer,python-engineer,orchestrator,explorer}.md`; `harness/commands/{new-normalization-rule,strangler-step}.md` — content classification.
- `tools/{contract_drift,docs_sync,golden_runner,memory_regen,strangler_guard}/**` and `libs/normalize-spec.md` — the exhaustive core prose-token inventory.
- `docs/adr/0002-general-template-de-specialization.md`; `.planning/phases/05.5-authored-surface/055-CONTEXT.md`; `.planning/config.json` — locked decisions + de-specialization rationale.

### Secondary / Tertiary
- None — no external sources needed (self-contained refactor, no new packages, no ecosystem/version questions).

## Metadata
**Confidence breakdown:**
- Move set + destinations: HIGH — consumers (glob discovery, `project.toml` pointer test) verified.
- RED-test enumeration: HIGH — each failure traced to a specific pinned frozenset / glob / path assertion with line numbers.
- Guard token set + allowlist: HIGH — every current core occurrence of every candidate token enumerated and classified; over-reach tokens explicitly excluded with counter-examples.
- Genericization targets: HIGH — exact lines cited; strangler-step + orchestrator/explorer + normalize-spec surfaced as forced-additions beyond the CONTEXT's named two.

**Research date:** 2026-07-09
**Valid until:** stable (~30 days; only invalidated by concurrent edits to `harness/` or `tools/harness_lint/`).
