# Phase 24: Contract-Relationship Vocabulary + Compatibility (v2.3 A) - Research

**Researched:** 2026-07-19
**Domain:** Contract-first JSON-Schema authoring + stdlib-TOML config seam + deterministic lowering/union in a polyglot agent-harness template
**Confidence:** HIGH (every claim below is grounded in files read from this repo this session; no external package research was needed — the phase reuses machinery already installed)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (schema granularity):** ONE **record-level** schema `contracts/harness/topology/relationship.schema.json` validating a *single* relationship object — NOT a graph-document schema wrapping the whole array. Array-level consistency (unique ids, resolution) is Phase 25's compiler job. Positive/negative fixtures are instance files validated against this schema through the existing hash/drift path. [CITED: 24-CONTEXT.md D-01]
- **D-02 (endpoint shape):** Endpoints are **bare stable-id strings**. `authority` = a single string; `dependents` = a non-empty array of strings. Schema enforces *shape and cardinality only* (exactly-one authority, ≥1 dependent). Existence/resolution deferred to Phase 25. [CITED: 24-CONTEXT.md D-02]
- **D-03 (additive TOML slot + accessor):** `[[contract_graph.relationships]]` TOML record mirrors the schema fields **1:1** (`id`, `contract`, `authority`, `dependents`, optional `kind`/`labels`). New accessor `contract_graph_relationships(cfg)` in `tools/harness_config/loader.py` returns **raw `list[dict]` passthrough** — zero validation/traversal/discovery/policy — mirroring `pipeline()`/`components()`. Existing loader signatures untouched. [CITED: 24-CONTEXT.md D-03]
- **D-04 (legacy lowering):** Each legacy edge `{from,to,contract}` lowers to `authority=from`, `dependents=[to]`. Synthesized id is **namespaced** (e.g. `pipeline/<contract>/<from>-><to>`) so lowered ids never collide with human-authored ids. `effective_relationships()` unions lowered + explicit in one path. [CITED: 24-CONTEXT.md D-04]
- **D-05 (failure taxonomy):** Union fails deterministically on (a) **duplicate id**, (b) **duplicate semantic edge** = same `(authority, contract, dependent)` triple, (c) **contradiction** = same `contract` claimed by two *different* authorities. Current linear fixtures have no explicit records → lowering-only → **byte-unchanged**. [CITED: 24-CONTEXT.md D-05]

### Claude's Discretion
- Exact synthesized-id delimiter/format (D-04) and diagnostic message wording (D-05) — provided deterministic and stable-sortable.
- Whether the schema gains a sibling `topology/README` — executor discretion; the record schema itself is fixed.

### Deferred Ideas (OUT OF SCOPE — Phase 25/26/27, do NOT build here)
- Domain-neutral compiler, `harness_lint` consistency gate, endpoint/authority-resolution validation — Phase 25 (TOPO-04).
- Affected-set queries (direct/reverse/transitive, cycle-safe) — Phase 25 (TOPO-05).
- `/pipeline`·`pipeline-map`·orchestrator generalization + byte-identical re-emit — Phase 25 (TOPO-06).
- Non-linear generic + cross-repo proof fixtures + topology **ADR-0009 ratification** — Phase 25 (TOPO-07). ADR-0009 does NOT exist yet (highest committed is `docs/adr/0008-*`); leave the reservation intact — do not create it. [VERIFIED: `ls docs/adr/`]
- version/semver compatibility engine, topology runtime/broker, second orchestrator — OUT for v2.3.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TOPO-01 | Human-ratified Draft 2020-12 schema under `contracts/harness/topology/` defining each relationship: stable id, tracked contract ref, exactly-one authority, ≥1 dependents, optional kind/labels; positive/negative fixtures pass the existing contract hash/drift path. | §Schema Authoring (exact shape mirroring `task-control/*.schema.json`); §Ratification Path (auto-glob into manifest + `--write` rebaseline); §Test Surface (task_packet fixture-validation pattern). |
| TOPO-02 | Project AND workspace TOML accept additive `[[contract_graph.relationships]]`; existing loader APIs + legacy config unchanged; new accessors return raw data (no validation/traversal/discovery/policy). | §TOML Loader Extension (near-copy of `pipeline()`; TOML array-of-tables nesting; both `harness/project.toml` and `workspace.toml` slots). |
| TOPO-03 | One deterministic `effective_relationships()` lowers every `[pipeline].edges` entry to authority/dependent and unions with explicit records, failing on dup-id / dup-semantic-edge / contradiction while leaving linear fixtures byte-unchanged. | §Lowering + Union Algorithm (deterministic namespaced id, stable-sort, three fail modes); §Byte-Unchanged proof. |
</phase_requirements>

## Summary

Phase 24 is a **pure additive vocabulary + coexistence-semantics phase** on top of machinery that is already fully installed and green in this repo. There is **no new dependency, no new gate, no new external package** — the phase composes four existing, well-understood primitives: (1) the Draft 2020-12 per-record schema pattern under `contracts/harness/task-control/`, (2) the RFC-8785/JCS schema-hash + drift ratification path (`tools/contract_hash` + `tools/contract_drift`), (3) the stdlib-`tomllib` passthrough loader (`tools/harness_config/loader.py`), and (4) the jsonschema-`Draft202012Validator` positive/negative fixture-test pattern proven in `tools/task_packet/`.

The three requirements decompose cleanly: TOPO-01 authors one record schema + fixtures and rebaselines the hash manifest (a constitution-plane change; machines gate, humans ratify via CODEOWNERS on `contracts/`); TOPO-02 adds a `[contract_graph]` parent table with `[[contract_graph.relationships]]` array-of-tables to `harness/project.toml` and `workspace.toml`, plus a raw-passthrough accessor that is a near-verbatim copy of the existing `pipeline()`/`components()` helpers; TOPO-03 adds exactly one new function `effective_relationships()` carrying deterministic lowering + union + a three-mode failure taxonomy.

The dominant risk is **not** technical difficulty — it is **scope discipline and byte-invariance**. The schema must validate *structure and cardinality only* (no endpoint resolution — that is Phase 25). The accessor must not change any existing signature. The lowering must leave the current linear `source→sink/greeting` topology byte-identical (it has no explicit records, so `effective_relationships()` on it is lowering-only). And the new schema, once added, will trip the drift gate as an `added` entry until the manifest is rebaselined — that rebaseline is the human-ratification checkpoint, and it must be paired (CODEOWNERS-gated on `contracts/`).

**Primary recommendation:** Author `contracts/harness/topology/relationship.schema.json` in the exact style of `contracts/harness/task-control/attestation.schema.json` (compact, `$schema`+`$id`+`title`+`type:object`+`additionalProperties:false`+`required`, `$defs` for the id/string patterns); add the `[contract_graph]` TOML slot to both configs behind `BEGIN/END` markers with the "Pure DATA / Consumers:" comment convention; add `contract_graph_relationships(cfg)` as a copy of `components()`; add `effective_relationships(cfg)` as the single logic-bearing function; wire fixture-validation + lowering/union tests in the `tools/task_packet` style; then rebaseline via `python -m tools.contract_hash.hash --write` as the ratification step.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Relationship record wire shape (schema) | Constitution plane (`contracts/`) | — | Contract-first: the ratified schema is the single source of truth; code validates against it, never the reverse. |
| Additive config data (`[[contract_graph.relationships]]`) | Config-data slot (`harness/project.toml`, `workspace.toml`) | — | Pure DATA slot; enforcement never lives in config (mirrors `[[languages]]`/`[pipeline]`). |
| Raw passthrough accessor | Loader (`tools/harness_config/loader.py`) | — | Thin I/O + shape, zero policy — same tier as `pipeline()`/`components()`. |
| Lowering + union + failure taxonomy | Loader function `effective_relationships()` | — | The one logic-bearing function; deterministic, pure (dict-in → list-out/raise), no I/O beyond reading cfg. |
| Fixture validation, lowering-determinism, union-failure tests | Test plane (pytest) | — | Positive/negative fixtures + property tests, `tools/task_packet` idiom. |
| Endpoint/authority resolution, compiler, gate, queries | **Phase 25 (NOT here)** | — | Explicitly deferred; schema validates cardinality only, not resolution. |

## Standard Stack

### Core (all already installed — verify, do not add)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `tomllib` | 3.11+ | Parse `harness/project.toml` + `workspace.toml` | Already the sole reader in both loaders; `requires-python >=3.11` guarantees it — no external TOML dep. [VERIFIED: `tools/harness_config/loader.py:18`, `tools/workspace_config/loader.py`] |
| `jsonschema` (`Draft202012Validator`) | 4.x (installed) | Validate fixture instances against the record schema in tests | The repo-wide standard validator — used in `task_packet/validate.py:12`, `risk_router`, `evidence/capture.py`, `task_control/manager.py`, `handoff/handoff.py`. [VERIFIED: `grep jsonschema tools/`] |
| `rfc8785` | installed | JCS canonicalization feeding the SHA-256 schema hash | The single canonicalizer behind `contract_hash.schema_hash`; the new schema is hashed by it automatically. [VERIFIED: `tools/contract_hash/hash.py:21`] |
| `pytest` | 8.4.x | Test runner for all new Phase-24 tests | Repo standard (`uv run pytest`); existing `*.cpython-311-pytest-8.4.2.pyc` artifacts confirm 8.4.2 in use. [VERIFIED: pyc artifacts under `tools/*/tests/__pycache__`] |

**Installation:** NONE. This phase adds zero packages. All four primitives are already present and exercised by green suites. If a plan proposes `npm install` / `pip install` / `uv add`, that is a scope error.

### Supporting (existing tools composed, not modified)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `python -m tools.contract_hash.hash --write` | Rebaseline `contracts/.hashes/manifest.json` after adding the new schema | The ratification step for TOPO-01 (see §Ratification Path). [VERIFIED: `tools/contract_hash/hash.py:108`] |
| `python -m tools.contract_drift.drift` (`tools/contract_drift/check.sh`) | The drift gate that goes red on unbaselined schema change | Must stay green post-rebaseline. [VERIFIED: `tools/contract_drift/drift.py:340`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| One record-level schema (D-01) | A graph-document schema wrapping the whole array with `uniqueItems`/cross-record checks | REJECTED by D-01: array-level consistency is Phase-25 compiler work; a document schema would pull resolution semantics into Phase 24 (scope leak). |
| Bare-string endpoints (D-02) | Object endpoints `{component, member?}` | REJECTED by D-02: existence/resolution deferred to Phase 25; strings keep the vocabulary pure. |
| `check-jsonschema` CLI for fixture tests | `Draft202012Validator` in-process | Repo convention is in-process `Draft202012Validator` (task_packet/validate.py); `check-jsonschema` exists as a documented CLI but tests use the Python validator. Use the Python validator for determinism + error-path sorting parity. [VERIFIED: `tools/task_packet/validate.py:42-48`] |

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** All libraries used (`tomllib`, `jsonschema`, `rfc8785`, `pytest`) are already present in the repo and exercised by green suites. No registry lookup, no slopcheck run required. [VERIFIED: no install step in phase scope; deps confirmed imported across `tools/`]

## Architecture Patterns

### System Architecture Diagram (data flow, Phase 24 scope only)

```text
                        ┌─────────────────────────────────────────────┐
   harness/project.toml │  [[components]] + [pipeline].edges (legacy)  │
   workspace.toml       │  [contract_graph.relationships] (NEW, add'l) │
                        └───────────────┬─────────────────────────────┘
                                        │ tomllib.load  (binary mode)
                                        ▼
                    tools/harness_config/loader.py
                    ┌───────────────────────────────────────────────┐
                    │ pipeline(cfg)        → dict  (UNCHANGED)       │
                    │ components(cfg)      → list  (UNCHANGED)       │
                    │ contract_graph_relationships(cfg) → list[dict] │  raw passthrough (NEW)
                    │                                                │
                    │ effective_relationships(cfg):        (NEW)    │
                    │   1. lower each [pipeline].edges edge          │
                    │        {from,to,contract}                      │
                    │      → {id: "pipeline/<contract>/<from>-><to>",│
                    │         contract, authority:from,              │
                    │         dependents:[to]}                       │
                    │   2. union with explicit records (passthrough) │
                    │   3. FAIL on: dup id | dup (auth,contract,dep) │
                    │        | contradiction (contract→2 authorities)│
                    │   4. stable-sort → deterministic list          │
                    └───────────────────┬───────────────────────────┘
                                        │ list[relationship] (or raise)
                                        ▼
                    ┌───────────────────────────────────────────────┐
                    │ Consumers (LATER phases — not built here):     │
                    │  · Phase 25 compiler / queries / conductor     │
                    │  · Phase 26 brownfield mapper vocabulary       │
                    │  · lowered view feeds existing /pipeline trace │
                    └───────────────────────────────────────────────┘

   contracts/harness/topology/relationship.schema.json (NEW record schema)
        │  auto-discovered by build_manifest glob **/*.schema.json
        ▼
   tools/contract_hash → JCS SHA-256 → contracts/.hashes/manifest.json (rebaselined = ratified)
        │
        ▼
   tools/contract_drift.run_gate  →  green iff live manifest == committed baseline
```

The diagram traces the primary use case: a config is loaded, `effective_relationships()` produces a deterministic unioned relationship list (or fails loud), and the new schema plugs into the existing hash/drift ratification loop. File→responsibility mapping is in the Responsibility Map above.

### Recommended Project Structure (files this phase touches/creates)

```text
contracts/harness/topology/
  relationship.schema.json          # NEW — the record schema (D-01)
  README.md                         # OPTIONAL (executor discretion, D-01/02 note)
contracts/.hashes/manifest.json     # EDIT — rebaselined to include the new schema (ratification)
harness/project.toml                # EDIT — add [contract_graph] slot behind BEGIN/END markers
workspace.toml                      # EDIT — add [contract_graph] slot (TOPO-02 = project AND workspace)
tools/harness_config/loader.py      # EDIT — add contract_graph_relationships() + effective_relationships()
tools/harness_config/__init__.py    # EDIT — add both names to __all__ (lazy re-export)
tools/harness_config/tests/         # NEW/EDIT — accessor + lowering + union-failure tests
  (fixtures for positive/negative relationship instances)
```

### Pattern 1: Per-Record Draft 2020-12 Schema (mirror `attestation.schema.json`)

**What:** A compact single-object schema; `$schema`+`$id` (both use the `https://harness.local/contracts/...` synthetic base), `title`, `type:object`, `additionalProperties:false`, an explicit `required` array, `properties`, and a `$defs` block for reused patterns.
**When to use:** The relationship record schema.
**Example (structure to follow — observed from repo):**
```json
// Source: contracts/harness/task-control/attestation.schema.json (read this session)
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://harness.local/contracts/harness/topology/relationship.schema.json",
  "title": "Contract relationship record",
  "description": "Human-ratified shape for a single authority→dependents contract relationship.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "contract", "authority", "dependents"],
  "properties": {
    "id":         { "type": "string", "minLength": 1 },
    "contract":   { "type": "string", "minLength": 1 },
    "authority":  { "type": "string", "minLength": 1 },
    "dependents": { "type": "array", "minItems": 1,
                    "items": { "type": "string", "minLength": 1 }, "uniqueItems": true },
    "kind":       { "type": "string", "minLength": 1 },
    "labels":     { "type": "array", "items": { "type": "string", "minLength": 1 }, "uniqueItems": true }
  }
}
```
Key conventions observed and to replicate: `$id` path exactly mirrors the repo-relative file path (task/attestation both do this); `additionalProperties:false` at the object root; `minLength:1` on all id/name strings; `uniqueItems:true` on string arrays (see `task.schema.json` `non_goals`, `decision_refs`). Cardinality: `authority` is a single string (exactly one), `dependents` is `minItems:1` (≥1). `kind`/`labels` are optional (absent from `required`). [CITED: attestation.schema.json, task.schema.json — read this session]

### Pattern 2: Raw Passthrough Accessor (copy `components()`)

**What:** A one-line-body helper: default-load cfg if omitted, `return list(cfg.get("<key>", []))`. Zero validation.
**Example (the template to near-copy — observed):**
```python
# Source: tools/harness_config/loader.py:53-62 (components) — read this session
def contract_graph_relationships(cfg: dict | None = None) -> list[dict]:
    """Return the [[contract_graph.relationships]] tables (loads default config if omitted).

    Raw passthrough (mirrors components()/pipeline()): the topology-relationship DATA slot flows
    through UNCHANGED — NO enforcement here. Validation/resolution is Phase-25 compiler work.
    """
    if cfg is None:
        cfg = load_project()
    return list(cfg.get("contract_graph", {}).get("relationships", []))
```
Note the nesting: `[[contract_graph.relationships]]` in TOML parses to `cfg["contract_graph"]["relationships"]` (a list of dicts under a parent table). Mirror the `edges()` accessor's `cfg.get("pipeline", {}).get("edges", [])` two-level `.get` idiom. [VERIFIED: `tools/workspace_config/loader.py` `edges()`]

### Anti-Patterns to Avoid

- **Graph-document schema:** wrapping the array + adding cross-record `uniqueItems`/resolution into the schema. VIOLATES D-01 (that is Phase-25 compiler). The schema validates ONE record.
- **Endpoint resolution in the schema or accessor:** checking `authority`/`dependents` against declared components/members. VIOLATES D-02 (Phase 25). Cardinality/shape only.
- **Changing an existing loader signature** (`pipeline`, `components`, `languages`, `language_bash_scopes`, `load_project`): the module docstring explicitly says "Keep the signatures stable." VIOLATES TOPO-02. Only ADD functions. [CITED: `loader.py:5-6`]
- **Editing legacy config values** to "migrate" them: the byte-unchanged invariant (TOPO-03) forbids touching existing `[[components]]`/`[pipeline]` data. Add a NEW `[contract_graph]` block only.
- **Hand-rolling canonicalization or hashing:** the schema is hashed by `rfc8785` + `hashlib.sha256` automatically via `build_manifest`. Never compute a hash by hand.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema-instance validation in tests | A custom shape-checker | `jsonschema.Draft202012Validator(schema).iter_errors(doc)` sorted by `absolute_path` | Repo standard; identical error-path ergonomics to `task_packet/validate.py:42-48`. [VERIFIED] |
| Canonical schema hashing | Manual key-sort + sha256 | `tools.contract_hash.schema_hash` (rfc8785 JCS) | Already the single canonicalizer; auto-picks up new `**/*.schema.json`. [VERIFIED: hash.py:36-44] |
| Manifest rebaseline | Hand-editing `manifest.json` | `python -m tools.contract_hash.hash --write` | Writes `sort_keys=True, indent=2` deterministically; hand-editing risks a non-canonical byte diff. [VERIFIED: hash.py:69-82] |
| TOML parsing | A regex/hand parser | stdlib `tomllib` via `load_project()`/`load_workspace()` | Both loaders already do this; binary-mode `tomllib.load`. [VERIFIED: loader.py:38-39] |
| Drift-path test scaffolding | A bespoke tmp-tree harness | Copy the `tools/task_packet/tests` idiom: `shutil.copytree(REPO_ROOT/"contracts", tmp)`, `write_manifest(baseline, contracts)`, `run_gate(...)` | Proven pattern for exercising hash/drift over a tmp copy. [VERIFIED: test_task_packet.py:280-304] |

**Key insight:** Everything Phase 24 needs is a composition of green primitives. The only genuinely new *logic* is `effective_relationships()`; everything else is copy-a-pattern.

## Common Pitfalls

### Pitfall 1: The drift gate goes red the moment the schema is added — and that's expected
**What goes wrong:** After creating `relationship.schema.json`, `contract_drift` reports it as an `added` entry and `run_gate` returns `ok:False` (any non-empty `drifted` list fails). CI red.
**Why it happens:** `build_manifest` auto-globs `**/*.schema.json`; the new file is in the live manifest but not the committed baseline. `diff_manifests` classifies it `added` → drifted. [VERIFIED: drift.py:211-212, hash.py:57]
**How to avoid:** Run `python -m tools.contract_hash.hash --write` to rebaseline `contracts/.hashes/manifest.json` in the SAME change that adds the schema + fixtures. This IS the ratification step (machines gate, humans ratify): the baseline change lands under `contracts/`, which is CODEOWNERS-gated, so a human must approve. Commit schema + fixtures + rebaselined manifest together.
**Warning signs:** `contract-drift: DRIFT DETECTED — [added] contracts/harness/topology/relationship.schema.json` in CI.

### Pitfall 2: `$id` / path mismatch
**What goes wrong:** `$id` doesn't match the file's repo-relative path.
**Why it happens:** Copy-paste from `task.schema.json` without updating the path segment.
**How to avoid:** `$id` = `https://harness.local/contracts/harness/topology/relationship.schema.json` — mirror the on-disk path exactly (both task-control schemas do). [VERIFIED: task.schema.json:3]

### Pitfall 3: Accidental Phase-25 scope creep into the schema
**What goes wrong:** Adding `uniqueItems` across records, endpoint-existence checks, or authority-resolution to the schema.
**Why it happens:** It "feels incomplete" to validate only one record.
**How to avoid:** D-01/D-02 are explicit — schema validates ONE record's shape + cardinality; resolution and array-consistency are Phase 25. The record schema has no knowledge of other records or of declared components/members.
**Warning signs:** The schema references components, members, or `contract` existence.

### Pitfall 4: Byte-drift in the linear fixtures
**What goes wrong:** Editing `harness/project.toml`'s existing `[[components]]`/`[pipeline]` block, or reformatting it, when adding the `[contract_graph]` slot.
**Why it happens:** Auto-formatters, or "tidying" the file.
**How to avoid:** APPEND a new `BEGIN/END` marker block; leave the `PIPE-01 topology` block byte-identical. Verify with `git diff --check` and a targeted diff showing only added lines. TOPO-03 success criterion 3 requires "NO edits" to existing config. Prove `effective_relationships()` on the unedited config yields the lowered `source→sink/greeting` relationship with zero config change. [CITED: project.toml:47-81]

### Pitfall 5: GEN-04 core→example leak
**What goes wrong:** New loader code or schema text mentions `examples/`, an instance path, or a domain prose token.
**Why it happens:** Writing an example relationship that references the log-parser instance.
**How to avoid:** Keep all new core files domain-neutral. The generic default (`source→sink` carrying `greeting`) is the ONLY topology core may reference. `test_core_no_example_dep.py` scans `tools/`, `harness/`, `libs/` for `examples/`, `import examples`, and prose tokens (`equipment`, `wafer`, etc.). New tests/fixtures under `tools/` must not carry those tokens. [VERIFIED: test_core_no_example_dep.py:43-68]

### Pitfall 6: Non-deterministic union output
**What goes wrong:** `effective_relationships()` returns records in dict/insertion order that varies, or diagnostics differ run-to-run.
**Why it happens:** Relying on set iteration order or unsorted dict keys.
**How to avoid:** Stable-sort the final list (e.g. by `id`); build detection maps deterministically; make diagnostic strings a pure function of the offending records (sorted). No wall-clock, no `set` in the output path. This mirrors the repo-wide determinism constraint (v2.3 §6). [CITED: v2.3-scoping-FINAL.md §6 Determinism]

### Pitfall 7: `workspace.toml` endpoints carry a `repo:` half — lowering must not choke
**What goes wrong:** `workspace.toml`'s `[pipeline].edges` use `repo:stage` endpoints (e.g. `member-a:emit`). If `effective_relationships()` is run against a workspace config, lowered `authority`/`dependents` will contain the raw `repo:stage` string.
**Why it happens:** The project vs workspace edge endpoint shapes differ (`split_endpoint` exists for the workspace half). [VERIFIED: workspace.toml edges; workspace_config `split_endpoint`]
**How to avoid:** Phase 24's lowering is a **pure string passthrough** of `from`/`to` into `authority`/`dependents` — it does NOT interpret `repo:stage` (that resolution is Phase 25). Keep the lowered id/endpoints as the raw edge strings; do not call `split_endpoint`. Confirm with a workspace-config lowering test that the raw endpoints survive verbatim. Decide (planner) whether `effective_relationships()` reads project-config only or is parameterized to accept either cfg — recommend a `cfg`-in signature so it works for both `load_project()` and `load_workspace()` outputs (both are plain dicts with a `pipeline.edges` list).

## Code Examples

### Deterministic lowering + union skeleton (new function — the one logic-bearing piece)
```python
# Source: pattern synthesized from loader.py accessors + D-04/D-05 (24-CONTEXT.md). [ASSUMED shape — planner refines]
def effective_relationships(cfg: dict | None = None) -> list[dict]:
    """Lower legacy [pipeline].edges → authority/dependent records and union with explicit
    [[contract_graph.relationships]] records. Deterministic, stable-sorted. Raises on
    duplicate id / duplicate semantic edge / contradiction (D-05).
    """
    if cfg is None:
        cfg = load_project()
    lowered = [
        {
            "id": f"pipeline/{e['contract']}/{e['from']}->{e['to']}",   # namespaced (D-04)
            "contract": e["contract"],
            "authority": e["from"],
            "dependents": [e["to"]],
        }
        for e in cfg.get("pipeline", {}).get("edges", [])
    ]
    explicit = contract_graph_relationships(cfg)
    merged = lowered + explicit
    # (a) duplicate id
    # (b) duplicate semantic edge = same (authority, contract, dependent)
    # (c) contradiction = one contract claimed by two different authorities
    # ... deterministic detection, raise a stable-diagnostic ValueError on any ...
    return sorted(merged, key=lambda r: r["id"])
```
Diagnostic wording + exact delimiter are executor discretion (D-05 / Claude's Discretion) — the constraint is *deterministic + stable-sortable*. Note a single record with multiple `dependents` expands to multiple `(authority, contract, dependent)` triples for the duplicate-semantic-edge check.

### Positive/negative fixture test (mirror task_packet)
```python
# Source: tools/task_packet/tests/test_task_packet.py:166-229 idiom. [VERIFIED pattern]
from jsonschema import Draft202012Validator
# positive: valid records pass iter_errors == []
# negative (parametrized cases.json): missing required id/contract/authority; empty dependents;
#   dependents not unique; additional property → each must produce >=1 error.
```

## Runtime State Inventory

> N/A — Phase 24 is greenfield-additive (new schema + new config slot + new functions). It is NOT a rename/refactor/migration. No stored data, live-service config, OS-registered state, secrets, or build artifacts embed a string being changed. Explicitly: **None — verified by the phase being pure-add (no existing identifier is renamed; existing config is byte-unchanged per TOPO-03).**

## State of the Art

Not applicable — this phase uses in-repo primitives only, no evolving external ecosystem. The relevant "state of the art" is internal: the `task-control` schemas (added 2026-07-18/19) are the current per-record schema exemplar and the JCS/rfc8785 hash path is the current ratification mechanism. No deprecated approach in play.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `effective_relationships()` should accept a generic `cfg` dict so it serves both `load_project()` and `load_workspace()` (satisfying TOPO-02/03 for both files). | Pitfall 7 / Code Examples | If planner instead wants two separate functions or project-only, the workspace lowering requirement (TOPO-02 = project AND workspace) may be under-served. LOW risk — parameterizing on `cfg` is the least-assuming design. |
| A2 | Exact lowered-id format `pipeline/<contract>/<from>-><to>`. | D-04 / Code Examples | Format is explicitly executor discretion (D-04 / Claude's Discretion); any deterministic stable-sortable namespaced scheme is acceptable. Near-zero risk. |
| A3 | The ratification checkpoint is "rebaseline manifest + CODEOWNERS review on `contracts/`" — no separate ADR is authored in Phase 24. | Ratification Path / Pitfall 1 | ADR-0009 is Phase 25 (confirmed: no `0009-*` file exists). If a human wants an ADR now, that would be scope creep into Phase 25. Low risk — CONTEXT.md D and canonical_refs are explicit. |

## Open Questions

1. **Does `effective_relationships()` live in `harness_config` even though it also serves workspace configs?**
   - What we know: `contract_graph_relationships` clearly belongs in `harness_config/loader.py` (project config). Workspace has its own loader (`tools/workspace_config/loader.py`).
   - What's unclear: whether the workspace slot gets its own accessor in `workspace_config` and whether `effective_relationships` is duplicated/shared.
   - Recommendation: Put `effective_relationships(cfg)` in `harness_config/loader.py` taking a plain `cfg` dict (works for both since both expose `pipeline.edges` + `contract_graph.relationships` as plain dict/list). Add a thin `contract_graph_relationships` accessor to BOTH loaders (project + workspace) for symmetry with `pipeline()`/`edges()`. Planner to confirm placement; keep signatures additive either way.

2. **Fixture location: `tools/harness_config/tests/` vs `contracts/harness/topology/fixtures/`?**
   - What we know: `task_packet` keeps fixtures under `tools/task_packet/tests/fixtures/`. There is no existing `tools/harness_config/tests/` dir yet (loader tests live in `tools/harness_lint/tests/test_pipeline_config.py`).
   - What's unclear: exact home for the new positive/negative relationship instances.
   - Recommendation: Co-locate fixtures with the new tests under `tools/harness_config/tests/fixtures/` (mirrors task_packet). Keep them domain-neutral (GEN-04). The contract-hash/drift path only cares about the schema file itself under `contracts/`; fixtures are test-plane artifacts validated in-process by `Draft202012Validator` — they do NOT need to live under `contracts/` and should NOT (that would add them to the hash manifest glob... note: the glob is `**/*.schema.json`, so non-`.schema.json` fixtures under `contracts/` are ignored, but keeping fixtures in the test plane is cleaner).

## Environment Availability

> All dependencies are in-repo Python tooling already exercised by green suites; no external service/tool is required.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python `tomllib` | loader | ✓ | 3.11+ stdlib | — |
| `jsonschema` | fixture tests | ✓ | 4.x | — |
| `rfc8785` | contract_hash | ✓ | installed | — |
| `pytest` (via `uv run pytest`) | test suite | ✓ | 8.4.2 | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

## Validation Architecture

> `nyquist_validation: true` in `.planning/config.json` — section included. This is a deterministic-analyzer phase, so validation is squarely in scope. [VERIFIED: `.planning/config.json`]

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (via `uv run pytest`) |
| Config file | root `pyproject.toml` `testpaths` (repo convention; example tests off-root per `test_paths` in project.toml) |
| Quick run command | `uv run pytest tools/harness_config tools/contract_drift/tests/test_convention_mutation.py -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TOPO-01 | Valid relationship instances pass the schema | unit | `uv run pytest tools/harness_config/tests -k schema_validates` | ❌ Wave 0 |
| TOPO-01 | Negative instances (missing id/contract/authority, empty dependents, extra prop) are rejected | unit | `uv run pytest tools/harness_config/tests -k negative` | ❌ Wave 0 |
| TOPO-01 | New schema is in the rebaselined manifest and drift stays green | integration | `uv run python -m tools.contract_drift.drift` | ✅ (drift tool exists) |
| TOPO-02 | `contract_graph_relationships(cfg)` returns raw list unchanged; existing signatures untouched | unit | `uv run pytest tools/harness_config/tests -k accessor` | ❌ Wave 0 |
| TOPO-02 | Slot accepted in BOTH `project.toml` and `workspace.toml` | unit | `uv run pytest tools/harness_config/tests -k workspace_slot` | ❌ Wave 0 |
| TOPO-03 | Lowering of `source→sink/greeting` is deterministic + byte-unchanged config | unit | `uv run pytest tools/harness_config/tests -k lowering_determinism` | ❌ Wave 0 |
| TOPO-03 | Union fails on dup-id / dup-semantic-edge / contradiction | unit | `uv run pytest tools/harness_config/tests -k union_failure` | ❌ Wave 0 |
| TOPO-03 | Linear project/workspace/log-parser files require no edits | regression | `git diff --check` + targeted diff assertion | ✅ (git) |
| ALL | GEN-04 core→example guard stays green | regression | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py` | ✅ |
| ALL | Existing topology/loader gates stay green | regression | `uv run pytest tools/harness_lint/tests/test_pipeline_config.py` | ✅ |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/harness_config tools/harness_lint/tests/test_core_no_example_dep.py tools/harness_lint/tests/test_pipeline_config.py -q`
- **Per wave merge:** `uv run pytest -q && uv run python -m tools.contract_drift.drift`
- **Phase gate:** Full suite green + `contract-drift: OK` + `git diff --check` clean before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/harness_config/tests/test_topology_relationships.py` — accessor passthrough, lowering determinism, union failure modes (TOPO-02/03)
- [ ] `tools/harness_config/tests/test_relationship_schema.py` — positive fixtures validate, negative fixtures rejected (TOPO-01)
- [ ] `tools/harness_config/tests/fixtures/` — positive + negative relationship instances (domain-neutral, GEN-04-safe)
- [ ] `tools/harness_config/tests/conftest.py` — if a shared fixture-loading helper is warranted (there is currently no `tools/harness_config/tests/` dir; loader is tested via `harness_lint`)
- [ ] Drift-path regression test in the `test_task_packet` style (copytree contracts → `write_manifest` → `run_gate` OK with the new schema)

## Security Domain

> `security_enforcement` not explicitly `false` — but this phase has a minimal attack surface (no auth, no network, no untrusted input beyond in-repo config the human owns). ASVS applicability is narrow.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | yes (constitution-plane) | CODEOWNERS gate on `contracts/` + `contracts/.hashes/` — humans ratify schema/baseline changes; agents cannot self-promote. [CITED: v2.3-FINAL §6] |
| V5 Input Validation | yes | `Draft202012Validator` on fixtures; `additionalProperties:false` rejects unknown keys; stdlib `tomllib` parse. |
| V6 Cryptography | yes (integrity, not secrecy) | RFC-8785 JCS canonicalization + SHA-256 via `rfc8785`/`hashlib` — never hand-rolled; the drift gate is the integrity check. [VERIFIED: hash.py] |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Silent schema change without ratification | Tampering | Schema-hash drift gate (`contract_drift.run_gate`) fails on any unbaselined change; rebaseline is CODEOWNERS-gated. |
| Agent self-promotes a constitution artifact | Elevation of Privilege | Human ratification checkpoint; `contracts/` under CODEOWNERS; machines gate / humans ratify. |
| Non-deterministic output enabling a hidden diff | Repudiation | Stable-sort + JCS canonical serialization; `git diff --check`; byte-unchanged regression. |
| Path traversal via config strings | Tampering | Phase 24 stores endpoints as opaque strings (no filesystem resolution here); existing `repoPath` pattern precedent exists for when Phase 25 resolves them. |

## Sources

### Primary (HIGH confidence — read this session)
- `tools/harness_config/loader.py` — accessor signatures (`load_project`, `languages`, `components`, `pipeline`, `language_bash_scopes`), "keep signatures stable" mandate, `list(cfg.get(...))` passthrough idiom.
- `tools/harness_config/__init__.py` — lazy PEP-562 re-export; `__all__` extension point.
- `tools/workspace_config/loader.py` — `load_workspace`, `members`, `edges` (two-level `.get`), `split_endpoint` (`repo:stage`).
- `tools/contract_hash/hash.py` — `schema_hash` (rfc8785+sha256), `build_manifest` (`**/*.schema.json` auto-glob + explicit DATA contracts), `write_manifest --write` (sort_keys/indent).
- `tools/contract_drift/drift.py` — `diff_manifests` (changed/added/removed), `run_gate` (`ok` iff no drift), `classify`, rebaseline hint, workspace gate.
- `contracts/harness/task-control/task.schema.json`, `attestation.schema.json` — per-record Draft 2020-12 exemplar ($schema/$id/required/additionalProperties/$defs/uniqueItems/minLength).
- `contracts/sample/greeting.schema.json` — simplest schema exemplar.
- `contracts/.hashes/manifest.json` — the committed baseline (9 entries) the new schema must be added to.
- `harness/project.toml` — `BEGIN/END PIPE-01 topology` marker + "Pure DATA / Consumers:" convention; `source→sink/greeting` linear default.
- `workspace.toml` — additive-slot target #2; `repo:stage` edge endpoints.
- `tools/harness_lint/tests/test_pipeline_config.py` — topology consistency-gate posture; `_CONTRACTS_DIR.rglob("*.schema.json")` contract-existence check.
- `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 guard scan surface + prose tokens.
- `tools/task_packet/validate.py` + `tools/task_packet/tests/test_task_packet.py` — `Draft202012Validator` fixture-validation idiom; positive/negative `cases.json` layout; tmp-copytree drift-path exercise.
- `.claude/skills/data-contracts/SKILL.md` — contract-first rule, layout, `check-jsonschema` validation, drift gate.
- `.planning/research/v2.3-scoping-FINAL.md` §Theme A + §Phase 24 — ratified vocabulary + lowering semantics + determinism constraint.
- `.planning/phases/24-.../24-CONTEXT.md` — D-01..D-05 locked decisions.
- `.planning/config.json` — `nyquist_validation: true`.
- `docs/adr/` listing — confirms ADR-0009 not created (highest `0008`).

### Secondary / Tertiary
- None — no external sources needed; all findings are repo-grounded.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every library is already imported and green in the repo; no external verification needed.
- Architecture / patterns: HIGH — directly copied from read exemplars (task-control schemas, loader accessors, task_packet tests).
- Pitfalls: HIGH — each derived from an observed mechanism (drift auto-glob, GEN-04 scan, byte-invariance, `repo:stage` endpoints).
- Assumptions (A1–A3): LOW-MEDIUM — flagged; all are executor-discretion or trivially-safe design choices, not factual risks.

**Research date:** 2026-07-19
**Valid until:** 2026-08-18 (stable — in-repo primitives; only invalidated if the contract_hash/drift or loader modules are refactored)
