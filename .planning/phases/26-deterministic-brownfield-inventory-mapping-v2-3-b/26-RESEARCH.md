# Phase 26: Deterministic Brownfield Inventory + Mapping *(v2.3 B)* — Research

**Researched:** 2026-07-19
**Domain:** Internal Python tooling — deterministic read-only repo scanning, JSON-Schema-governed artifacts, contract-plane ratification
**Confidence:** HIGH (nearly every answer is in-repo and was read directly; no external library research was needed or performed)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01: Contract-first — all three outputs are schema-governed.** Author new JSON-Schema contracts under `contracts/harness/adoption/` for the inventory, the mapping plan, and the disposition manifest. Rationale: mirrors the shipped `contracts/harness/task-control/` precedent exactly (adoption is "an ordinary task" per v2.3 FINAL §146, and task-control already contract-governs state/evidence/handoff/attestation); all three outputs cross the phase boundary into Phase 27 (ADOPT-04 binds inventory·plan·manifest hashes into CAS), so each earns drift-gate protection. The constitution-plane authoring + CODEOWNERS human ratification rides the **established** path — an agent Write into `contracts/` is correctly denied; the schemas land human-ratified (same as ADR-0004/0005/0009 precedent). Phase logic itself stays fully CI-testable.
- **D-02: Conservative-unknown bias.** `observed` only on **direct** evidence (file exists, extension present, declared in a manifest file). `inferred` only on **strong structural** signals. **Everything else ambiguous → `unknown` → question.** Ownership/authority claims (contract authority, component ownership, CODEOWNERS entries) are `unknown` by construction under this rule.
- **D-03: Collision rule — content-equal → `preserve`, content-different → `conflict`.** `marker-merge` is reserved for **marker-capable** files only. No automatic overwrite, ever.
- **D-04: Remaining rows are requirement-locked (do not re-derive):** constitution destination (`contracts/`, `docs/adr/`, `golden/`) → **always `human-ratification-required`**; derived-plane destination (`.memory/derived/**`, `docs/reference/**`) → `derived-regenerate`; non-constitution destination with no existing target file → `create`. Together with D-03 the table is **total**.
- **D-06: One synthetic mini-repo fixture, with a separate assert per detection.** Determinism proven by double-run byte diff plus a shuffled-enumeration-order variant. No fixture proliferation (v2.3 FINAL §152).

### Claude's Discretion

- **D-05: Question-record shape → researcher/planner.** Floor: stable id + target + evidence pointer (path + hash). Ordering must be deterministic.
- **D-07: Exclusion + size-cap mechanism → researcher.** Reuse-first; if not reused, state why. Secret posture follows D-02 safest-bias.
- Module location and naming, internal data structures, exact canonical sort keys, schema property spellings, CLI/module entry point, and test file layout — planner decides, provided outputs are deterministic, repo-confined, and read-only with respect to the target.
- Inventory detection breadth (languages / package managers / candidate-process-boundary heuristics, whether to reuse repo-map tree-sitter machinery) — researcher/planner scope; user explicitly declined to constrain it.

### Deferred Ideas (OUT OF SCOPE)

- `/adopt` command + `brownfield-adoption` skill, task-local batches under `.workflow/tasks/`, apply/marker-merge execution, human-ratification checkpoint, the three application fixtures — **Phase 27 (ADOPT-04..07)**.
- Docs dependency registry / ledger seeding from adoption — Phase 29 (DOCSUP-07).
- Graph-impact reports over the adoption plan — needs Phase 25 queries; not a Phase 26 dependency.
- Autonomous contract extraction, golden inference from behavior, source refactoring, repo moves, CI/package-manager rewriting, **executing discovered scripts**, remote workspace members — permanently out (v2.3 FINAL §147).
- Inventory detection breadth beyond what the researcher selects.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (from REQUIREMENTS.md) | Research Support |
|----|-------------------------------------|------------------|
| **ADOPT-01** | Read-only local-root inventory reports languages · package/component boundaries · existing schema/spec/doc/ADR/AGENTS/CODEOWNERS/CI surfaces · candidate process boundaries, deterministically, as confined · ignore-respecting · size-capped evidence pointers + hashes; excludes secret · binary · vendor · generated · source dumps. | §D-07 Decision (reuse surface), §Determinism Recipe, §Exclusion Rules, §Standard Stack |
| **ADOPT-02** | Every proposed member · component · relationship · contract candidate · test command · documentation destination · AGENTS boundary is classified `observed`/`inferred`/`unknown` with source evidence; unresolved ownership stays a **question**, not invented authority. | §Evidence Classification Ladder, §D-05 Question-Record Shape, §TOPO vocabulary binding |
| **ADOPT-03** | The plan assigns exactly one of `create`/`marker-merge`/`preserve`/`conflict`/`derived-regenerate`/`human-ratification-required` to every harness destination across contracts · golden · ADR · Diátaxis 4 quadrants · both memory planes · task/config/workspace topology · root/nested AGENTS · CODEOWNERS guidance · runtime-neutral source · emitted runtimes. | §Authoritative Harness Destination Catalog, §Marker-Capability, §Disposition Resolution Order |
</phase_requirements>

---

## Summary

Phase 26 is an **internal-tooling phase with zero external dependencies**. Every answer needed to plan it lives in this repo and was read directly during this session; no new package is required, and none should be added. The work decomposes into: (a) three new JSON Schemas landed on the CODEOWNERS-gated constitution plane via the *exact* Phase-24 ratification procedure, (b) one new `tools/` uv-workspace member that walks a target root read-only and emits three deterministic JSON artifacts, and (c) one synthetic fixture tree plus determinism/detection tests.

The **central research finding** is that `tools/evidence/capture.py` is **not** a file scanner (D-07). It is a *gate-command runner* — it executes a registered subprocess, hashes its combined stdout/stderr into a task artifact, and CAS-anchors the record into `state.json`. It has no directory walk, no size cap, no ignore handling, and no file-content hashing. Its confinement helper `_repository_root` resolves the *execution cwd*, not a scan boundary. Reusing it wholesale would mean executing commands — the one thing v2.3 FINAL §147 forbids. **The reusable pieces are elsewhere**: the confinement idiom in `tools/memory_regen/repo_map.py::_iter_source_files` (cloned in `pointer_index.py`, `harness_emit/manifest.py::_confined`, `contract_hash/hash.py`), the secret patterns in `contracts/harness/task-control/gate-registry.json` + `tools/hooks/secret_scan.PATTERNS`, and the RFC-8785 hasher in `tools/contract_hash/hash.py`. So the recommendation is **a purpose-built adoption scanner assembled from four existing repo primitives** — reuse at the function level, not a fork and not a new engine.

The **second load-bearing finding** is a hidden gate coupling: adding schemas under `contracts/harness/adoption/` automatically changes **three** committed derived artifacts (`docs/reference/*.md` via `tools.docs_sync`, `.memory/derived/contracts-index.md` via `tools.memory_regen.contracts_index`) and the drift baseline `contracts/.hashes/manifest.json`. Missing any of them REDs the `stale-derived` or `drift` CI job. The Phase-24 plan handled only the drift baseline because its schema landed with a `docs/reference/relationship.md` regeneration in a sibling step; Phase 26 adds three schemas at once and must regenerate all derived artifacts in the same wave.

**Primary recommendation:** Build `tools/adoption_scan/` as a new virtual uv-workspace member with a `scan → classify → plan → render/write → main` pipeline mirroring `tools/memory_regen/pointer_index.py`; emit all three artifacts through one canonical writer (`json.dumps(obj, sort_keys=True, indent=2) + "\n"`); land the three schemas via the Phase-24 three-step ratification procedure (author → `python -m tools.contract_hash.hash --write` → verify `python -m tools.contract_drift.drift` green) and regenerate `docs/reference` + `contracts-index.md` in the same wave.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Target-tree enumeration (walk, confinement, ignore, size cap) | Python tool (`tools/adoption_scan`) | — | Read-only local filesystem work; no service boundary crossed. |
| Content hashing (evidence pointers) | Python tool, stdlib `hashlib` | — | Raw file bytes are not JSON, so RFC-8785 does not apply to them. |
| Artifact shape governance | Constitution plane (`contracts/harness/adoption/*.schema.json`) | Python tool validates against it | Contract-first: `contracts/` is authority, code conforms (CLAUDE.md). |
| Artifact hash / drift protection | `tools/contract_hash` + `tools/contract_drift` | CI `drift` job | Reuse-don't-fork; one hasher for the whole repo. |
| Relationship candidate vocabulary | `contracts/harness/topology/relationship.schema.json` (Phase 24) | `tools/harness_config.effective_relationships` (consumer, Phase 27+) | Phase 26 emits candidates in this vocabulary; it does NOT resolve them. |
| Human ratification of the new schemas | Human / CODEOWNERS + `.github/CODEOWNERS` | `tools/hooks/contract_guard` in-session | "Machines gate, humans ratify." Agent write to `contracts/**` is denied. |
| Reference docs for the new schemas | `tools/docs_sync` (derived) | CI `stale-derived` job | `docs/reference/**` is committed-derived; never hand-authored. |
| Applying the plan to a target tree | **Phase 27** | — | Explicitly out of Phase 26 (target tree must stay unchanged). |

---

## Standard Stack

### Core — nothing new is added

| Library / module | Version | Purpose | Why standard here |
|------------------|---------|---------|-------------------|
| Python stdlib (`pathlib`, `hashlib`, `json`, `re`, `argparse`, `tomllib`) | 3.11+ (`requires-python >=3.11`) | Walk, hash, serialize, parse TOML manifests | `[VERIFIED: /Users/hyojung/orca/lifetimeworkflow/pyproject.toml:5]` — `tomllib` is stdlib-guaranteed by the pin; both existing loaders rely on this. |
| `jsonschema` | `==4.26.0` (root dep, already pinned) | Validate the three emitted artifacts against their schemas in tests | `[VERIFIED: pyproject.toml:10]`; `Draft202012Validator` idiom already used by `tools/evidence/capture.py:75` and `tools/task_packet/validate.py`. |
| `rfc8785` | `==0.1.4` (root dep) | Only via `tools.contract_hash.hash.schema_hash` — never called directly for file bytes | `[VERIFIED: pyproject.toml:9]` |
| `pytest` | `>=8.4,<9` (dev group) | Test framework | `[VERIFIED: pyproject.toml:17]` |
| `syrupy` | `==5.2.0` (dev group) | Committed snapshot of the three artifacts over the fixture tree (the repo's determinism-proof idiom) | `[VERIFIED: pyproject.toml:18]`; used by `memory_regen`, `docs_sync`, `pointer_index`. |

### Supporting — existing in-repo modules to import, not reimplement

| Module | Public surface to use | Purpose |
|--------|----------------------|---------|
| `tools.contract_hash.hash` | `schema_hash(path)`, `build_manifest()`, `write_manifest()`, `MANIFEST_PATH`, `CONTRACTS_DIR`, `REPO_ROOT` | Schema-hash rebaseline for the three new contracts. |
| `tools.contract_drift.drift` | `run_gate(contracts_dir, baseline_path)`; CLI `python -m tools.contract_drift.drift` | Verify the rebaseline is green. |
| `tools.harness_perms` | `resolve_path(globs, rel_path) -> "allow"|"deny"|None`, `resolve_bash`, `load_matrix` (lazy PEP-562 re-export) | Last-wins glob resolution — the repo's ONLY glob matcher. Use it for constitution/derived/secret path classification instead of writing a matcher. |
| `tools.hooks.contract_guard` | `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]`, `_on_constitution_plane` | The authoritative constitution-plane definition for D-04. Import the constant; do not retype the list. |
| `tools.hooks.secret_scan` | `PATTERNS` (3 shape-anchored regexes), `SECRET_PATH_GLOBS = ["*.env", "**/*.env"]`, `ALLOWLIST_PREFIXES` | Secret exclusion (see §Exclusion Rules). |
| `contracts/harness/task-control/gate-registry.json` → `secret_patterns` | 8 shape-anchored regexes (AWS, GH PAT, `sk-`, Slack, PEM, JWT, Bearer, generic assignment) | The **broader** committed pattern set. Read it as data — same as `tools/evidence/capture.py::_sensitive_pattern`. |
| `tools.harness_config.loader` | `load_project`, `languages`, `components`, `pipeline`, `contract_graph_relationships`, `effective_relationships` | Reference shape for what an adopted `harness/project.toml` must eventually contain — drives which inventory facts the mapping plan needs. |
| `tools.workspace_config.loader` | `load_workspace`, `members`, `edges`, `contract_graph_relationships`, `split_endpoint` | Same, one level up (multi-repo members). |
| `tools.harness_emit.merge` | `BEGIN_MARKER`, `END_MARKER`, `splice_managed_block`, `HARNESS_SIGNATURES` | **Authoritative** definition of marker-capability for D-03. |
| `tools.harness_emit.manifest` | `is_gsd_owned(rel)`, `load_manifest(path)` | The emitted-runtime ownership set + the GSD-owned lanes the manifest must never claim. |
| `tools.memory_regen.repo_map` | `_iter_source_files` idiom (copy the pattern, it's private), `lang_for_path` from `tools.memory_regen.queries` | Confined symlink-guarded walk + language detection by extension. |

### Alternatives Considered

| Instead of | Could use | Tradeoff / verdict |
|------------|-----------|--------------------|
| Purpose-built scanner (recommended) | `tools/evidence/capture.py` wholesale | **Rejected.** It runs subprocesses (`subprocess.run(command, cwd=execution_root)` at `capture.py:236`) and CAS-writes `state.json` — both forbidden/out-of-scope here. See §D-07. |
| stdlib walk + explicit ignore list | `pathspec` (gitignore semantics library) | **Rejected.** Not in `uv.lock` `[VERIFIED: grep of uv.lock found no pathspec entry]`; adding a dependency for one phase violates the repo's zero-new-deps discipline (`tools/docs_sync/pyproject.toml` states this explicitly). |
| stdlib walk + `git ls-files`/`git check-ignore` fallback | pure stdlib only | **Recommended hybrid.** `git ls-files` with `shell=False` is *already* the repo's tracked-set enumerator (`tools/harness_lint/tests/test_core_no_example_dep.py`), so it is precedent-backed. But it fails on a non-git target, so it must be a *fallback-capable* path, and the fallback must be deterministic. |
| tree-sitter symbol extraction (`tools.memory_regen.queries`) | extension-based language detection only | **Recommend extension-only for Phase 26.** D-02's conservative bias makes symbol-level inference `unknown` anyway; tree-sitter adds parse-time nondeterminism risk and grammar dependency for no classification gain. Note it as a Phase-27+ extension seam. |

**Installation:** none. `uv sync --all-packages` must not mutate `uv.lock` — the new `tools/<name>/pyproject.toml` declares `dependencies = []` and `[tool.uv] package = false`, exactly like `tools/docs_sync/pyproject.toml` `[VERIFIED: read directly]`.

---

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** All dependencies are already pinned in the committed root `pyproject.toml` + `uv.lock` and were verified by direct file read this session. No slopcheck run is required because no new package name enters the repo.

If a planner later proposes any new dependency (e.g. `pathspec`), it must be gated behind a `checkpoint:human-verify` task and run through the Package Legitimacy Gate — but the research recommendation is **do not add one**.

---

## D-07 Decision: Reuse Surface Analysis (PRIMARY RESEARCH QUESTION)

### What `tools/evidence/capture.py` actually is

`[VERIFIED: read /Users/hyojung/orca/lifetimeworkflow/tools/evidence/capture.py, 339 lines, this session]`

Public surface:

```python
capture(task_dir, gate, argv, *, criterion_ids=None, finding_ids=None,
        gate_version="v1", source="local", human_approval_ref=None) -> dict
add_finding(task_dir, finding: dict) -> dict
validate_evidence(task_dir) -> dict
normalize_argv(argv: list[str]) -> list[str]
main(argv=None) -> int          # python -m tools.evidence.capture
# Exceptions: EvidenceError(ValueError), EvidenceRefusal(EvidenceError)
```

Behaviour of `capture()`: validate the gate against the committed `gate-registry.json` → refuse if argv is sensitive → resolve the *execution* root → **`subprocess.run(command, cwd=execution_root, ...)`** → refuse if stdout/stderr is sensitive → write `artifacts/<gate>/<E-NN>/output.log` → append a record with `sha256` of the combined output → schema-validate → atomic-write `evidence.json` → CAS-bump `state.json` via `tools.task_control.manager._cas_write`.

### Gap analysis against ADOPT-01

| ADOPT-01 need | Present in `capture.py`? | Evidence |
|---|---|---|
| Directory walk / enumeration | **No** | No `rglob`/`walk`/`iterdir` anywhere in the module. |
| Scan-root confinement | **No** (only `_repository_root`, which finds the nearest `.git` ancestor to use as *cwd*) | `capture.py:162-167` |
| Size cap | **No** | No length/byte limit exists; the whole subprocess output is written. |
| Ignore-respecting (gitignore) | **No** | Nothing reads `.gitignore`. |
| File-content hashing | Partial — `hashlib.sha256(combined)` of subprocess output only; `_digest()` hashes *dicts* via a non-RFC-8785 `json.dumps(sort_keys, indent=2)` | `capture.py:36-40, 250` |
| Secret exclusion | **Yes, reusable in spirit** — `_sensitive_pattern()` compiles `gate-registry.json` `secret_patterns`; `_looks_like_high_entropy_token()` is a base64-shape entropy heuristic that deliberately exempts 40-hex git IDs | `capture.py:94-128` |
| Read-only w.r.t. target | **No** — it writes `artifacts/`, `evidence.json`, and CAS-bumps `state.json`; it also *executes* a command | `capture.py:236-261` |

### Verdict — REUSE AT FUNCTION LEVEL, NOT MODULE LEVEL

**Do not build the adoption scanner on `tools/evidence/capture.py`.** Concrete reasons (state these verbatim in the plan, per D-07's "if not reused, state why"):

1. **It executes commands.** `capture()`'s core act is `subprocess.run`. v2.3 FINAL §147 forbids executing discovered scripts and Phase 26's own invariant is "no arbitrary command execution." A scanner built on it would either bypass its entire body (making the "reuse" cosmetic) or violate the invariant.
2. **It mutates state.** Every successful path writes `evidence.json` + CAS-bumps `state.json` inside a `.workflow/tasks/<id>/` root. Phase 26 must be read-only and must NOT create a task plane — §146 says adoption's task plane is Phase 27's job.
3. **It has no walker, no cap, no ignore handling.** Three of ADOPT-01's five bounding requirements are simply absent; there is nothing to reuse for them.
4. **Its confinement is cwd resolution, not a scan boundary.** `_repository_root` answers "where do I run the gate?"; ADOPT-01 needs "which paths may I read?"

**What to reuse instead (four in-repo primitives, all read directly this session):**

| Need | Reuse | Source of truth |
|---|---|---|
| Scan-root confinement + symlink escape guard | The 3-line idiom `resolved = p.resolve(); if root_resolved != resolved and root_resolved not in resolved.parents: continue` | `tools/memory_regen/repo_map.py:66-69`; identical in `pointer_index.py:96-98`, `harness_emit/manifest.py:48-62`, `contract_hash/hash.py:61-63`. This is the repo's established traversal defense (T-02-10 / T-16-01). |
| Secret pattern set | `contracts/harness/task-control/gate-registry.json` → `secret_patterns` (8 regexes) — read as **data**, exactly as `capture._sensitive_pattern()` does | `[VERIFIED: read this session]` |
| Secret path globs + fixture allow-list | `tools.hooks.secret_scan.SECRET_PATH_GLOBS`, `ALLOWLIST_PREFIXES` fed through `tools.harness_perms.resolve_path` | `tools/hooks/secret_scan.py:38-44` |
| High-entropy token heuristic | Port/import `capture._looks_like_high_entropy_token` semantics (base64-charset 40-char runs, entropy ≥ 4.3, 40-hex git-ID exemption). **Recommend extracting it to a shared helper rather than copying** — but if extraction risks touching the v2.2 evidence path, a documented reimplementation with a cross-test asserting both agree is acceptable. | `tools/evidence/capture.py:103-116` |
| JSON canonical hashing (for the *schemas*, not file bytes) | `tools.contract_hash.hash.schema_hash` | `[VERIFIED]` |

**Size cap:** nothing in the repo implements one. This is genuinely new. Recommend a module-level `MAX_FILE_BYTES` constant (default `256 * 1024`); a file over the cap is **inventoried by path + size + a `size-capped` exclusion reason, with NO content hash and NO content read** — checked via `Path.stat().st_size` *before* opening. This keeps the tool O(dir-entries) on large binaries and satisfies "size-capped."

---

## Determinism Recipe (Success criterion 1)

Repeated output must be byte-identical **regardless of filesystem enumeration order**. The repo has a proven recipe; follow it exactly.

**Does a canonical JSON writer already exist to reuse?** — Partially, and the distinction matters:

- `tools.contract_hash.hash.schema_hash` produces the RFC-8785 (JCS) canonical **bytes for hashing**, via `rfc8785.dumps`. It is a *hasher*, not a file writer, and JCS output is minified (no indent) — unsuitable as the committed artifact form.
- The repo's de-facto canonical **writer** is the one-liner repeated in every generator: `json.dumps(obj, sort_keys=True, indent=2) + "\n"` written with `encoding="utf-8"`. `[VERIFIED: tools/memory_regen/pointer_index.py:221, tools/harness_emit/manifest.py:93, tools/contract_hash/hash.py:81]`
- A **third, divergent** form exists in `tools/evidence/capture.py:36` — `json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"` (note `ensure_ascii=True`). Do not silently pick one; state the choice in the plan. **Recommendation: `sort_keys=True, indent=2, ensure_ascii=True`** for adoption artifacts, because they may carry non-ASCII paths from a brownfield target and ASCII-escaping removes any locale/encoding variance from the committed bytes.

**The seven determinism rules (all drawn from in-repo module docstrings):**

1. **Sort the walk.** `sorted(root.rglob("*"))` — never rely on `os.scandir` order. `[repo_map.py:61]`
2. **Sort every emitted list** by an explicit, total key. Never iterate a `set`. `[pointer_index.py:165-171]`
3. **Repo-relative POSIX paths only** — `resolved.relative_to(base).as_posix()`. Absolute paths and `tmp_path` must never leak into output. `[pointer_index.py:64-70]` This is what lets the fixture test compare bytes across machines.
4. **No timestamps.** Never `datetime.now()` anywhere in the output path. `[repo_map.py:12-15]`
5. **No raw floats** in rendered output (rank-only, not score). Not directly applicable here, but the constraint generalizes: no value whose repr is platform-dependent.
6. **Explicit tie-break on every sort.** Where a sort key can collide (two entries with equal disposition, equal target), append the stable id as the final tuple element so ordering is total.
7. **Sort keys must be data, not enumeration position.** Never emit an index/ordinal derived from walk order; derive ids from content (path, or path+hash), then sort.

**Shuffled-enumeration proof (D-06):** the clean way is to make the walker's file list injectable — e.g. `build_inventory(root, *, _paths: list[Path] | None = None)` or a module-level `_iter_files` the test monkeypatches to return `random.Random(1337).sample(files, len(files))`. Assert the emitted bytes equal the unshuffled run's bytes. Use a **seeded** shuffle so a failure is reproducible.

**Double-run proof:** run `write()` twice into two tmp dirs, assert `read_bytes()` equality (mirrors the repo's write→hash→delete→regenerate idiom). Do **not** use `git diff` — the artifacts are not committed (`pointer_index.py:12-14` warns about exactly this trap).

---

## Schema Authoring & Ratification Procedure (D-01)

**The established path, reconstructed from the Phase-24 commit + plan** `[VERIFIED: git show 7e3630d; read .planning/phases/24-.../24-01-PLAN.md Tasks 1 & 3]`:

**Why an agent write is refused:** `tools/hooks/contract_guard.py` is a PreToolUse(Write|Edit) hook whose `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]` are resolved through `tools.harness_perms.resolve_path`; a `deny` result blocks the write unless a **non-empty** `GOLDEN_APPROVE_HUMAN` env var is present (set by a human in the gitignored `.claude/settings.local.json`). Even an approved write is denied if its bytes carry a BOM or CRLF (`tools.polyglot_lint.lint_bytes`). `[VERIFIED: read contract_guard.py + harness/skills/gate-model/SKILL.md]`

**What "human-ratified" operationally means here:** the *merge-time* CODEOWNERS review, not an in-session token dance. `.github/CODEOWNERS` routes `/contracts/`, `/docs/adr/`, `/golden/`, `/approvals/` to `@hjung3113`. The file itself documents that CODEOWNERS is **advisory** unless branch protection's "Require review from Code Owners" is enabled, and that a solo author cannot self-approve. `[VERIFIED: read .github/CODEOWNERS]` Phase 24 explicitly accepted this residual risk (`T-24-02 … accept (out-of-band)`).

**The three-step procedure to replicate (per schema, or once for all three):**

1. **Author** `contracts/harness/adoption/<name>.schema.json` — LF, no BOM, Draft 2020-12. The write requires the human ratification token in-session, or the human authors it.
2. **Rebaseline:** `uv run python -m tools.contract_hash.hash --write`. `build_manifest`'s `**/*.schema.json` glob picks the new files up automatically — **do not hand-edit `contracts/.hashes/manifest.json`**. `[VERIFIED: hash.py:29, 57]`
3. **Verify green:** `uv run python -m tools.contract_drift.drift` must exit 0. Note `run_gate` classifies an added schema as `("added", "non-breaking")` but **still counts it as drift** (`ok = not drifted`), so the gate is RED between steps 1 and 2 — expected, and the rebaseline is the ratification checkpoint. `[VERIFIED: drift.py:211-215]`

### ⚠️ HIGH-IMPACT GATE COUPLING — three more artifacts move

Adding schemas under `contracts/**` also changes the **committed-derived** plane, which a separate CI job gates:

| Artifact | Generator | Gate |
|---|---|---|
| `docs/reference/<name>.md` (one page per schema) | `uv run python -m tools.docs_sync` | `stale-derived` job: `git add -A -- docs/reference .memory/derived/contracts-index.md && git diff --cached --exit-code` |
| `.memory/derived/contracts-index.md` | `uv run python -m tools.memory_regen.contracts_index` | same job |
| `contracts/.hashes/manifest.json` | `tools.contract_hash.hash --write` | `drift` job |

`[VERIFIED: read .github/workflows/ci.yml lines 100-145, 232-250; docs/reference/ already contains relationship.md, state.md, evidence.md … one per existing schema]`

**Planner action:** include one task that runs `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index` and commits the regenerated derived files. Three new schemas ⇒ three new `docs/reference/*.md` pages. Omitting this REDs `stale-derived`.

**Also note the `contract-check` CI job** validates `<name>.schema.json` against a *sibling instance* `<name>.{json,yaml,yml}` if one exists, and prints a visible `SKIP` if no pairs exist. Adoption schemas will have no siblings under `contracts/` (the instances are emitted into a scratch/task dir), so this job stays a SKIP — that is correct, not a hole. `[VERIFIED: ci.yml:108-127]`

### Schema style template (mirror `relationship.schema.json` / `task-control/*`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://harness.local/contracts/harness/adoption/inventory.schema.json",
  "title": "Brownfield adoption inventory",
  "description": "…what it validates AND what it deliberately does NOT validate…",
  "type": "object",
  "additionalProperties": false,
  "required": ["…"],
  "properties": { "…": {} },
  "$defs": { "…": {} }
}
```

Conventions confirmed across all 8 existing schemas: `$id` mirrors the on-disk repo-relative path exactly; `additionalProperties: false` at every object level; `required` lists are explicit; string fields carry `minLength: 1`; string arrays carry `uniqueItems: true`; shared shapes live in `$defs` and are `$ref`'d (`#/$defs/taskId`). `[VERIFIED: read relationship.schema.json in full, evidence.schema.json head]`

---

## Authoritative Harness Destination Catalog (ADOPT-03, success criterion 3)

Derived from the actual repo layout + `tools/harness_emit` + `tools/workspace_config` + `.gitignore` + the two-plane-memory skill, all read this session. Every row resolves to exactly one disposition.

| # | Destination | Plane | Disposition (D-03/D-04) | Marker-capable? | Source of truth |
|---|---|---|---|---|---|
| 1 | `contracts/**/*.schema.json` | constitution | `human-ratification-required` | no | `contract_guard.CONSTITUTION_GLOBS` |
| 2 | `contracts/.hashes/manifest.json` | constitution (derived-in-form, gated-in-fact) | `human-ratification-required` | no | under `contracts/**`; CODEOWNERS `/contracts/` |
| 3 | `contracts/README.md` | constitution | `human-ratification-required` | no | same glob |
| 4 | `golden/**` (`golden/<case>/…verified…`) | constitution | `human-ratification-required` | no | `CONSTITUTION_GLOBS`; `/golden-approve` exit-3 refusal |
| 5 | `docs/adr/**` (MADR records) | constitution, append-only | `human-ratification-required` | no | `CONSTITUTION_GLOBS`; ADRs supersede, never edit |
| 6 | `docs/tutorials/**` | human-authored docs | absent→`create`, equal→`preserve`, differ→`conflict` | no | Diátaxis Q1 |
| 7 | `docs/how-to/**` | human-authored docs | `create`/`preserve`/`conflict` | no | Diátaxis Q2 |
| 8 | `docs/reference/**` | **committed-derived** | **`derived-regenerate`** | no | `tools/docs_sync` owns it; `stale-derived` gate |
| 9 | `docs/explanation/**` | human-authored docs | `create`/`preserve`/`conflict` | no | Diátaxis Q4 |
| 10 | `docs/glossary.md` | human-authored | `create`/`preserve`/`conflict` | no | present in repo |
| 11 | `.memory/state/{activeContext,progress}.md` | derived plane, committed-state tier | `derived-regenerate` | no | two-plane-memory skill |
| 12 | `.memory/derived/contracts-index.md` | committed-derived | `derived-regenerate` | no | `.gitignore` re-include; `memory_regen.contracts_index` |
| 13 | `.memory/derived/{repo-map,pointer-index}.{md,json}` | gitignored-derived | `derived-regenerate` | no | `.gitignore` `.memory/derived/*` |
| 14 | `.memory/agreements/**` | Plane 3, human-authored/curated | `create`/`preserve`/`conflict` | no | two-plane-memory §Plane 3 |
| 15 | `.memory/README.md` | human-authored | `create`/`preserve`/`conflict` | no | tracked |
| 16 | `harness/project.toml` (`[instance]`, `[[languages]]`, `[[components]]`, `[pipeline]`, `[[contract_graph.relationships]]`) | runtime-neutral config | `create`/`preserve`/`conflict` | no (TOML — see below) | `tools/harness_config/loader.py` |
| 17 | `workspace.toml` (`[workspace]`, `[[members]]`, `[pipeline].edges`, `[[contract_graph.relationships]]`) | runtime-neutral config | `create`/`preserve`/`conflict` | no | `tools/workspace_config/loader.py` |
| 18 | `harness/permission-matrix.json` | runtime-neutral config | `create`/`preserve`/`conflict` | no | `tools/harness_perms` |
| 19 | `harness/risk-policy.toml` | runtime-neutral config | `create`/`preserve`/`conflict` | no | `tools/risk_router` |
| 20 | `harness/opencode.json` + `harness/opencode.config.schema.json` | runtime-neutral source | `create`/`preserve`/`conflict` | no | emitter input |
| 21 | `harness/agents/*.md` (+ `agents/templates/`) | runtime-neutral source | `create`/`preserve`/`conflict` | no | `harness_emit.generate` |
| 22 | `harness/commands/*.md` | runtime-neutral source | `create`/`preserve`/`conflict` | no | same |
| 23 | `harness/skills/<name>/SKILL.md` (+ `references/`) | runtime-neutral source | `create`/`preserve`/`conflict` | no | same |
| 24 | `harness/plugins/*.ts` | runtime-neutral source | `create`/`preserve`/`conflict` | no | copied byte-for-byte; never parsed |
| 25 | `harness/git-hooks/pre-commit` | runtime-neutral source | `create`/`preserve`/`conflict` | no | present |
| 26 | `.opencode/{agent,command,skill,plugin}/**` | **emitted runtime** | `derived-regenerate` | no | `harness_emit` ownership manifest; `emit-drift` CI job |
| 27 | `.claude/{agents,commands,skills}/**` | **emitted runtime** | `derived-regenerate` | no | same |
| 28 | root `opencode.json` | **emitted runtime** | `derived-regenerate` | no | `generate.py:437` writes it; `emit-drift` gates it |
| 29 | `.claude/settings.json` | **shared, structurally merged** | `marker-merge` | **yes (JSON signature merge)** | `merge.merge_settings` + `HARNESS_SIGNATURES` |
| 30 | root `AGENTS.md` | **shared marker file** | **`marker-merge`** | **yes** | `merge.splice_managed_block` |
| 31 | root `CLAUDE.md` | **shared marker file** | **`marker-merge`** | **yes** | same |
| 32 | nested `AGENTS.md` (`libs/python/`, `examples/*/`, `examples/*/libs/*/`) | human-authored, nearest-wins | `create`/`preserve`/`conflict` | **no** (not spliced by the emitter today) | `find` → 4 files; only the root one is emitter-managed |
| 33 | `.github/CODEOWNERS` | human-owned guidance | `create`/`preserve`/`conflict` — and ADOPT-02 keeps ownership **`unknown`/question** | no | `.github/CODEOWNERS` |
| 34 | `.github/workflows/ci.yml` | human-owned CI | `create`/`preserve`/`conflict` | no | present |
| 35 | `.workflow/tasks/**` (task control plane) | task plane | `create`/`preserve`/`conflict` | no | v2.2; Phase 27 writes batches here |
| 36 | root `pyproject.toml` / language build manifests | human-owned | `create`/`preserve`/`conflict` | no | §147 forbids rewriting package managers → in practice these should surface as **questions** |
| 37 | `tools/<pkg>/pyproject.toml` (workspace members) | human-owned | `create`/`preserve`/`conflict` | no | uv workspace members |
| 38 | `libs/normalize-spec.md` + `libs/normalize-fixtures/` | constitution-adjacent (per two-plane-memory: `libs/normalize-spec.md` is *constitution*) | `human-ratification-required` for the spec; `create`/`preserve`/`conflict` for fixtures | no | two-plane-memory §Plane 1 |
| 39 | `.gitignore` | human-owned | `create`/`preserve`/`conflict` | no | present |
| 40 | GSD-owned lanes (`.claude/get-shit-done/**`, `.claude/hooks/**`, `.claude/commands/gsd/**`, any `gsd-*` file) | **excluded — not a harness destination** | *no disposition; explicitly excluded* | n/a | `harness_emit.manifest.is_gsd_owned` |

**Row 40 is important for totality**: the manifest is total over *harness destinations*, and `is_gsd_owned()` defines the set that is by construction not one. Encode this as an explicit exclusion predicate (import `is_gsd_owned`), not as silence — otherwise a reviewer cannot distinguish "excluded" from "missed."

### Disposition resolution order (implement as a single ordered rule chain)

```
1. is_gsd_owned(rel)                              -> NOT A DESTINATION (excluded, recorded)
2. resolve_path(CONSTITUTION_GLOBS, rel)=="deny"  -> human-ratification-required   (D-04, wins over everything)
   OR rel == "libs/normalize-spec.md"
3. rel in DERIVED_GLOBS                           -> derived-regenerate            (D-04)
     docs/reference/**, .memory/derived/**, .memory/state/**,
     .opencode/**, .claude/agents/**, .claude/commands/**, .claude/skills/**, opencode.json
4. rel in MARKER_CAPABLE                          -> marker-merge                  (D-03)
     AGENTS.md (root only), CLAUDE.md, .claude/settings.json
5. not (target_root / rel).exists()               -> create                        (D-04)
6. sha256(existing) == sha256(proposed)           -> preserve                      (D-03)
7. otherwise                                      -> conflict                      (D-03)
```

Rules 1–4 are **path-only** (no content read, no proposal needed); 5–7 require a proposed-content hash. Test totality directly: a property test asserting every destination in the catalog resolves to exactly one non-null disposition, and that the chain has no fall-through.

---

## Marker-Capability (D-03) — the exact answer from `harness_emit/merge.py`

`[VERIFIED: read tools/harness_emit/merge.py in full, 238 lines]`

There are **exactly two marker regimes**, and marker-capability means "one of these two applies":

**Regime B-md — HTML-comment fence splice** (`splice_managed_block`):
```
BEGIN_MARKER = "<!-- BEGIN HARNESS-MANAGED (generated by tools.harness_emit — do not hand-edit) -->"
END_MARKER   = "<!-- END HARNESS-MANAGED -->"
```
Contract: both markers present → replace only the fenced region, text outside preserved byte-for-byte; both absent → append the fenced block once (idempotent on the second call); **exactly one marker (or END before BEGIN) → `raise ValueError`, never guess**. Output is normalized to LF, BOM-stripped, single trailing newline.
Applied by the emitter to exactly two files: **root `AGENTS.md`** and **root `CLAUDE.md`** (`generate.py:297-316`).

**Regime B-json — signature-matched, order-preserving hook merge** (`merge_settings`):
Applied to exactly one file: **`.claude/settings.json`**. Harness-owned hook groups are identified by `HARNESS_SIGNATURES` (`tools.hooks.format_on_write`, `contract_guard`, `secret_scan`, `commit_gate`, `resume_gate`), appended-or-replaced in place, de-duped; GSD-owned groups (`GSD_SIGNATURES`) are never removed or reordered; **no global key sort** (serialized with `json.dumps(..., indent=2, ensure_ascii=False) + "\n"`, deliberately without `sort_keys`).

**Therefore the marker-capable set for D-03 is exactly:**
```python
MARKER_CAPABLE = {"AGENTS.md", "CLAUDE.md", ".claude/settings.json"}
```

Explicitly **NOT** marker-capable, despite intuition:
- **Nested `AGENTS.md`** (`libs/python/AGENTS.md`, `examples/*/AGENTS.md`, `examples/*/libs/dotnet/AGENTS.md`) — the emitter splices only the *root* pair. `[VERIFIED: generate.py:297-316 takes `Path(root)`]` Classify these as ordinary `create`/`preserve`/`conflict`. If a planner wants them marker-merged, that is a scope expansion of the emitter and belongs to a different phase.
- **TOML configs** (`harness/project.toml`, `workspace.toml`) — no marker machinery exists for TOML anywhere in the repo. Additive-key merging into TOML is Phase-27-and-beyond territory at best; today it is `conflict` when it differs.
- Every emitted-runtime file — those are whole-file writes (Regime A) gated by the ownership manifest, i.e. `derived-regenerate`.

---

## Evidence Classification Ladder (ADOPT-02 / D-02)

Encode D-02 as an explicit, testable ladder. Each rule names the *kind* of signal so the emitted record can carry a machine-readable reason.

| Class | Admissible signals (exhaustive; anything else falls through) |
|---|---|
| **`observed`** | (a) file/directory exists at the recorded path (evidence pointer = path + sha256); (b) a declaration read *literally* out of a manifest file the tool parses — `pyproject.toml` `[tool.uv.workspace].members`, `[project].dependencies`, `[tool.pytest.ini_options].testpaths`; `package.json` `workspaces`/`scripts`; `*.csproj`/`*.sln` project references; `go.mod` module; `Cargo.toml` `[workspace].members`; (c) a file extension present in the tree (language presence). |
| **`inferred`** | Strong *structural* signals only: a directory containing a recognized manifest is a component root; a `tests/`+`test_*.py` pair implies a Python test surface; a `.github/workflows/*.yml` file implies CI; a `CODEOWNERS` file implies review routing *exists* (never who owns what). Each inferred record MUST carry the structural rule id that produced it. |
| **`unknown`** → **question** | Everything else. **By construction includes**, per D-02: contract authority for any candidate contract; component/member ownership; who owns a CODEOWNERS path; which of several plausible test commands is canonical; whether two directories are one component or two; the intended Diátaxis quadrant for an existing doc; whether an existing `AGENTS.md` is nearest-wins-correct. |

**Bright-line rule to state in the plan:** the tool may never write an `authority` value into a proposed relationship record from inference. A relationship candidate with an unresolved authority is emitted as a `question` (with the candidate's `contract` and `dependents` attached as context), not as a relationship with a guessed `authority`. This is what "never invented authority" means concretely, and it is exactly why the `relationship.schema.json` `required: ["id","contract","authority","dependents"]` cannot be satisfied by an inference.

**Vocabulary binding:** proposed relationships that *do* have observed authority are emitted as records validating against `contracts/harness/topology/relationship.schema.json` — `{id, contract, authority, dependents[], kind?, labels?}`, `additionalProperties: false`, endpoints are opaque strings. Namespace proposed ids to prevent collision with human-authored ones and with the `pipeline/<contract>/<from>-><to>` ids that `effective_relationships()` synthesizes — recommend the prefix **`adoption/`** (e.g. `adoption/<contract>/<authority>-><dependent>`). `[VERIFIED: harness_config/loader.py:138-146 shows the `pipeline/` namespace precedent and its collision rationale]`

---

## D-05: Question-Record Shape (recommended)

**How Phase 27 will consume questions** `[VERIFIED: REQUIREMENTS.md ADOPT-04/05/06 + ROADMAP Phase 27 success criteria]`:
- ADOPT-04 stores questions in the batch at `.workflow/tasks/<task-id>/artifacts/adoption/<batch-id>/` alongside inventory, plan, draft tree, conflicts, source ref, task revision, artifact hashes, approval.
- ADOPT-06 requires a **human decision** covering "proposed contract·golden·ADR·relationship authority·conflict·unknown", **bound to the exact draft hash, task revision, and git ref**, such that any input change invalidates the approval.

That drives four design consequences:

1. **The id must be content-derived and stable across runs**, otherwise a re-run renumbers questions and silently invalidates approvals for unrelated reasons. Recommend `Q-<sha256(kind + "\x00" + target)[:12]>` — deterministic, collision-resistant, and *insensitive* to the evidence hash so that a question about the same topic keeps its identity while its evidence updates.
2. **The evidence pointer must be a list**, not a single item — most real questions rest on several files. The floor (path + hash) is satisfied per-element.
3. **A question must carry its unresolved candidate when one exists**, so the human ratifies a *proposal* rather than authors from scratch — but the candidate must be structurally quarantined (nested under `candidate`) so no consumer can mistake it for a ratified record.
4. **Grouping should be a field, not a nesting level.** Flat array + a `group` key keeps the JSON diff-friendly and the sort trivially total; Phase 27's UI/prompt can group at render time.

**Recommended shape:**

```json
{
  "id": "Q-3f2a9c1b7e04",
  "kind": "relationship-authority",
  "group": "topology",
  "target": "harness/project.toml#contract_graph.relationships",
  "question": "Which endpoint is the authority for contract 'orders'?",
  "classification": "unknown",
  "evidence": [
    { "path": "services/api/schema/orders.json", "sha256": "…", "size": 1284 },
    { "path": "services/worker/orders_consumer.py", "sha256": "…", "size": 3021 }
  ],
  "candidate": {
    "record_kind": "relationship",
    "record": { "id": "adoption/orders/?->worker", "contract": "orders", "dependents": ["worker"] }
  },
  "blocking": true
}
```

- `required`: `["id", "kind", "target", "question", "classification", "evidence"]` — this exceeds D-05's floor without over-constraining.
- `candidate` is **optional** and, when present, is deliberately schema-incomplete w.r.t. `relationship.schema.json` (missing `authority`) — a structural guarantee it cannot be mistaken for a ratified record.
- `blocking` lets Phase 27 distinguish "must answer before apply" from "advisory."
- **Deterministic ordering:** sort by `(group, kind, target, id)` — total because `id` is unique by construction.

**Enumerated `kind` values (recommended closed enum, keeps Phase 27's prompt switch total):**
`relationship-authority`, `contract-candidate`, `component-boundary`, `member-boundary`, `test-command`, `docs-destination`, `agents-boundary`, `codeowners-ownership`, `collision`, `ambiguous-language`, `excluded-file`.

---

## Exclusion Rules (ADOPT-01) — deterministic, no execution, no network

All five exclusion classes must be decidable from path + `stat()` + at most a bounded byte prefix. Every exclusion is **recorded** in the inventory with a stable reason slug (not silently dropped) — otherwise "excludes secrets" is unfalsifiable and success criterion 4 cannot be asserted.

| Class | Rule | Reason slug | Basis |
|---|---|---|---|
| **secret (path)** | `resolve_path(SECRET_PATH_GLOBS, rel) == "deny"` → `*.env`, `**/*.env`. Extend with the conventional set: `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `.npmrc`, `.pypirc`, `.netrc`, `*.keystore`, `secrets.*`. | `secret-path` | `tools/hooks/secret_scan.py:38` `[VERIFIED]`; the extension list is `[ASSUMED]` conventional. |
| **secret (content)** | The 8 `gate-registry.json` `secret_patterns` regexes + the base64-shape entropy heuristic, applied to a **bounded prefix** (recommend first 64 KiB) of a text-decodable file. D-02 posture: **exclude on suspicion**, record the reason, never echo the matched bytes into the artifact. | `secret-content` | `capture.py:94-116` `[VERIFIED]` |
| **binary** | NUL byte in the first 8192 bytes → binary. (The classic, execution-free heuristic — same test `git` uses.) Fall back to `UnicodeDecodeError` on a UTF-8 decode attempt of the prefix, mirroring `pointer_index.py:153-155`'s `except (OSError, UnicodeDecodeError): continue`. Optionally add a suffix denylist (`.png .jpg .gif .pdf .zip .tar .gz .whl .so .dll .dylib .exe .class .jar .pyc .wasm`) as a fast path. | `binary` | NUL-scan is `[ASSUMED]` (universal convention); the decode-failure fallback is `[VERIFIED: pointer_index.py]`. |
| **vendored** | Path-segment denylist, matched on **whole path segments** (never substrings): `node_modules`, `vendor`, `third_party`, `thirdparty`, `.venv`, `venv`, `site-packages`, `Pods`, `bower_components`, `packages` (only when a sibling lockfile indicates a package cache), `.git`, `.hg`, `.svn`. | `vendored` | `[ASSUMED]` conventional; `.venv`/`__pycache__` are corroborated by this repo's own `.gitignore` `[VERIFIED]`. |
| **generated** | (a) path-segment denylist from this repo's own `.gitignore`: `bin`, `obj`, `dist`, `build`, `target`, `out`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.dotnet`, `coverage`, `.next`, `.nuxt`; (b) suffix denylist `*.pyc`, `*.pyo`, `*.min.js`, `*.map`, `*.lock` (lockfiles are inventoried by *existence* as an observed signal but their content is not hashed line-wise); (c) **content marker**: the first 2048 bytes contain a case-insensitive `do not (hand-)?edit` / `auto-generated` / `@generated` / `DERIVED —` marker. Marker (c) is the repo's own convention — every derived file here starts with `DERIVED — do not hand-edit`. | `generated` | (a) `[VERIFIED: .gitignore]`; (c) `[VERIFIED: repo_map.DERIVED_HEADER, pointer_index.DERIVED_HEADER, docs_sync docstring]`; the rest `[ASSUMED]`. |
| **source dump** | ADOPT-01's "source dumps": a single text file above the size cap whose extension is a source or archive-ish text type, OR a file whose path segment matches `dump`, `snapshot`, `backup`, `archive`. Simplest correct treatment: **the size cap already covers this** — record it as `size-capped` and additionally tag `source-dump` when the segment matches. | `size-capped` / `source-dump` | `[ASSUMED]` — ADOPT-01's phrase is not further defined anywhere in REQUIREMENTS.md or the FINAL doc; flag for planner/user confirmation. |
| **ignore-respecting** | Preferred: `git -C <target> ls-files -z --cached --others --exclude-standard` via `subprocess.run(list_argv, shell=False)` — precedent-backed, honours `.gitignore` + `.git/info/exclude` + global excludes exactly. Must be wrapped: non-zero exit / `FileNotFoundError` / not-a-git-repo ⇒ fall back to the built-in denylist walk and **record which mode was used** in the inventory (`enumeration_mode: "git" | "builtin"`), because the two produce different sets and a silent switch would break reproducibility claims. | — | `git ls-files` precedent `[VERIFIED: tools/harness_lint/tests/test_core_no_example_dep.py]` |

**Two non-negotiables for the walker:**
- **Never read a file to decide to exclude it by path.** Order the checks path-first (segments, suffix, size via `stat`) then content-last, so a 2 GB binary in `node_modules` costs one `stat`.
- **`stat()` before `open()`**, always — this is what makes the size cap a real bound rather than a post-hoc truncation.

---

## Architecture Patterns

### System Architecture Diagram

```
                       target root (read-only, --target <path>)
                                    │
                                    ▼
              ┌──────────────────────────────────────────┐
              │  enumerate()                             │
              │  · git ls-files -z  (mode="git")         │◄── falls back on any failure
              │    else confined rglob (mode="builtin")  │
              │  · resolve() + parents confinement guard │
              │  · sorted()                              │
              └──────────────┬───────────────────────────┘
                             │  candidate paths (sorted, repo-relative POSIX)
                             ▼
              ┌──────────────────────────────────────────┐
              │  classify_exclusions()                   │
              │  path segs → suffix → stat size cap →    │
              │  NUL/decode → secret regex (bounded)     │
              └────┬──────────────────────────┬──────────┘
        excluded   │                          │ included
      (path+reason,│                          │ (path + sha256 + size)
       no content) │                          ▼
                   │        ┌──────────────────────────────────────────┐
                   │        │  detect()                                │
                   │        │  languages (ext) · manifests (toml/json/ │
                   │        │  csproj/mod) · doc & ADR & AGENTS &      │
                   │        │  CODEOWNERS & CI surfaces · candidate    │
                   │        │  process boundaries                      │
                   │        └────────────────┬─────────────────────────┘
                   │                         │
                   ▼                         ▼
        ┌────────────────────────────────────────────────────┐
        │  ARTIFACT 1 — inventory.json                       │──► inventory.schema.json
        └────────────────────────┬───────────────────────────┘
                                 ▼
        ┌────────────────────────────────────────────────────┐
        │  map_plan()  — evidence ladder (D-02)              │
        │  observed / inferred / unknown→question            │
        │  relationship candidates in TOPO vocabulary        │
        └────────────────────────┬───────────────────────────┘
                                 ▼
        ┌────────────────────────────────────────────────────┐
        │  ARTIFACT 2 — plan.json  (+ questions[])           │──► plan.schema.json
        └────────────────────────┬───────────────────────────┘
                                 │
      DESTINATION CATALOG ───────┤  (static, 40 rows + is_gsd_owned exclusion)
                                 ▼
        ┌────────────────────────────────────────────────────┐
        │  dispositions() — ordered rule chain 1..7          │
        │  needs: existing target hash + proposed hash       │
        └────────────────────────┬───────────────────────────┘
                                 ▼
        ┌────────────────────────────────────────────────────┐
        │  ARTIFACT 3 — manifest.json                        │──► manifest.schema.json
        └────────────────────────┬───────────────────────────┘
                                 ▼
                    write() — one canonical writer
              json.dumps(sort_keys=True, indent=2,
                         ensure_ascii=True) + "\n", utf-8
                                 │
                                 ▼
                   --out <dir>   (NEVER inside the target)
```

Note the two boundary invariants the diagram encodes: (1) nothing flows *back* into the target root; (2) `--out` defaults to a path outside the target so a scan of the repo itself cannot pollute its own next run.

### Recommended project structure

```
tools/adoption_scan/                 # name: planner's call; this one is descriptive + snake_case
├── pyproject.toml                   # dependencies = [] ; [tool.uv] package = false
├── __init__.py                      # module docstring + PEP-562 lazy re-export (see harness_perms)
├── __main__.py                      # from tools.adoption_scan.cli import main
├── scan.py                          # enumerate() + classify_exclusions() + hashing
├── detect.py                        # language/manifest/surface detection rules
├── destinations.py                  # the static destination catalog + disposition rule chain
├── plan.py                          # evidence ladder + question records + TOPO candidates
├── cli.py                           # argparse: --target --out --max-file-bytes --json
└── tests/
    ├── __init__.py
    ├── conftest.py                  # sys.path wiring, parents[3]  (copy harness_config/tests/conftest.py)
    ├── fixtures/minirepo/…           # THE single synthetic target tree (D-06)
    ├── test_scan_exclusions.py      # one assert per detection class
    ├── test_determinism.py          # double-run + seeded-shuffle
    ├── test_dispositions.py         # totality + each of the 6 dispositions
    ├── test_plan_classification.py  # observed/inferred/unknown + question shape
    └── test_schema_conformance.py   # all 3 artifacts validate against their schemas
```

**Invocation convention** `[VERIFIED: python-conventions SKILL.md + every existing tool]`: module path only — `uv run python -m tools.adoption_scan --target <path> --out <dir>`. Never a file path. `__main__.py` is a 3-line shim (`tools/docs_sync/__main__.py` is the template). The new dir is auto-included by `[tool.uv.workspace] members = ["libs/python", "tools/*"]`, and **it must carry a `pyproject.toml` or `uv sync` prunes it** `[VERIFIED: pyproject.toml:32-35]`.

### Pattern 1: The generator quartet

Every deterministic tool in this repo uses the same four-function shape. Follow it so the code reviews itself:

```python
# Source: tools/memory_regen/pointer_index.py (verbatim structure)
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/<pkg>/<mod>.py)"

def build_index(*, base_dir=None, scan_roots=None) -> dict: ...   # pure: data in, data out
def render_md(index: dict) -> str: ...                            # pure: data -> text
def write(json_path=JSON_PATH, md_path=MD_PATH, *, base_dir=None) -> tuple[Path, Path]: ...
def main(argv=None) -> int: ...
```

Key property: `build_*` is **pure and injectable** (`base_dir`, `scan_roots` parameters) so the tests can point it at `tmp_path` without the random tmp path leaking into the output. This injectability is what makes the D-06 determinism tests possible at all — design for it from task one.

### Pattern 2: Confined, symlink-guarded walk

```python
# Source: tools/memory_regen/repo_map.py:53-71 (identical in 3 other modules)
root_resolved = root.resolve()
for p in sorted(root.rglob("*")):
    if not p.is_file():
        continue
    resolved = p.resolve()
    # Defense-in-depth: skip anything a symlink points outside the subtree.
    if root_resolved != resolved and root_resolved not in resolved.parents:
        continue
    files.append(p)
```

### Pattern 3: Fail loud on ambiguity, never guess

`splice_managed_block` raises `ValueError` when exactly one marker is present. `effective_relationships` raises on duplicate ids, duplicate semantic edges, and authority contradictions — with **sorted** diagnostic strings so the error text itself is deterministic. Adopt both habits: any adoption ambiguity is either a `question` record (data) or a raised `ValueError` with a sorted message (fatal); never a silent default.

### Anti-Patterns to Avoid

- **A second hasher.** `tools.contract_hash` is the only JSON canonical hasher. For raw file bytes use `hashlib.sha256(path.read_bytes())` — do *not* run file bytes through `rfc8785` (it only accepts JSON) and do *not* invent a third dict-digest.
- **A second glob matcher.** `tools.harness_perms.resolve_path` is the repo's last-wins resolver, reused verbatim by both hooks (`D-02` of Phase 4). Hand-rolling `fnmatch` logic here would create two disagreeing definitions of "constitution plane."
- **Retyping `CONSTITUTION_GLOBS` / marker constants.** Import them. A copy drifts.
- **Writing anything into the target.** Not even a cache, not even a lockfile. `--out` must be validated to not be inside `--target` (raise on violation).
- **Numbering questions by walk position.** Guarantees churn; use content-derived ids.
- **`set` iteration in an output path.** The classic determinism bug this repo calls out repeatedly.
- **A `datetime.now()` "generated_at" field.** Tempting, fatal to byte-identity. If provenance is wanted, emit the *tool module path* and the *target's git ref* (a fact about the input, not the clock).

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Glob-based path classification | `fnmatch` chains | `tools.harness_perms.resolve_path` | Last-wins semantics + `*` ordering rules already settled; two matchers = two truths. |
| Constitution-plane membership | A new list of paths | `tools.hooks.contract_guard.CONSTITUTION_GLOBS` | It is *the* gate's definition; anything else can disagree with the hook. |
| Marker-block semantics | A regex splice | `tools.harness_emit.merge.splice_managed_block` (+ `BEGIN_MARKER`/`END_MARKER`) | Handles the one-marker corruption case, LF/BOM normalization, and idempotence. |
| Canonical JSON hashing | `json.dumps(sort_keys=True)` + sha256 for *contract* hashes | `tools.contract_hash.hash.schema_hash` | RFC-8785 number canonicalization is subtle; the drift gate depends on this exact form. |
| Schema-hash baseline maintenance | Hand-editing `contracts/.hashes/manifest.json` | `python -m tools.contract_hash.hash --write` | The glob auto-discovers; hand edits desync ordering/formatting and RED the drift gate. |
| gitignore semantics | A `.gitignore` parser | `git ls-files --exclude-standard` (shell=False) with a recorded builtin fallback | Negation patterns, `**`, directory-vs-contents forms, `info/exclude`, and global excludes are a swamp — this repo's own `.gitignore` already relies on the subtle `/*`-vs-`/` distinction (documented at `.gitignore` line ~19). |
| Secret detection | New regexes | `gate-registry.json` `secret_patterns` (+ `secret_scan.PATTERNS`) | Committed, reviewed, shape-anchored to avoid firing on the repo's own fixtures. |
| Repo-relative POSIX key derivation | String slicing | `resolved.relative_to(base).as_posix()` with a `ValueError` fallback | `pointer_index._rel` is the settled idiom; slicing breaks on symlinks and Windows separators. |

**Key insight:** every "primitive" this phase needs already exists somewhere in `tools/` because five prior phases needed it. The phase's real work is **composition + the destination catalog + the classification ladder**, not machinery. A plan that reads like "write a scanner" is mis-scoped; a plan that reads like "assemble four known primitives behind three ratified schemas" is right.

---

## Common Pitfalls

### Pitfall 1: The `stale-derived` CI job REDs after adding the schemas
**What goes wrong:** three new schemas ⇒ `tools.docs_sync` wants to emit three new `docs/reference/*.md` pages and `contracts_index.md` changes; CI `git add -A -- docs/reference .memory/derived/contracts-index.md && git diff --cached --exit-code` fails.
**Why:** `docs/reference/**` and `contracts-index.md` are *committed-derived* — machine-write + CI-verify.
**Avoid:** a dedicated task running `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index`, then commit the regenerated files. **Never hand-write a reference page.**
**Warning sign:** a `docs/reference/` diff appearing in a later unrelated commit.

### Pitfall 2: Drift gate is RED between authoring and rebaselining
**What goes wrong:** `python -m tools.contract_drift.drift` exits non-zero right after the schema files land.
**Why:** `run_gate` returns `ok = not drifted`, and an added schema *is* drift (classified `added`/`non-breaking`, but still counted).
**Avoid:** treat "author → rebaseline → verify" as one atomic wave; never commit step 1 alone. `commit_gate` will also block a commit while drift is red.

### Pitfall 3: `uv.lock` mutates and the CI leg fails
**What goes wrong:** adding `tools/<name>/` without a `pyproject.toml` breaks `uv sync --all-packages`; adding one *with* dependencies mutates `uv.lock`.
**Why:** `[tool.uv.workspace] members = ["tools/*"]` — uv requires every matched dir to have a `pyproject.toml`.
**Avoid:** copy `tools/docs_sync/pyproject.toml` verbatim in shape: `dependencies = []`, `[tool.uv] package = false`. Verify `git diff --exit-code uv.lock` is clean after `uv sync --all-packages`.

### Pitfall 4: GEN-04 core→example guard REDs on fixture prose
**What goes wrong:** `tools/harness_lint/tests/test_core_no_example_dep.py` scans every tracked file under `tools/`, `harness/`, `libs/` for `examples/`, `components/toy-converter`, `import examples`, and the prose tokens `dotnet-engineer`, `dotnet-conventions`, `normalization-catalog`, `pipeline-patterns`, `libs/dotnet`, `equipment`, `standard-log`, `correction-rules`, `wafer`, `설비`.
**Why:** the new tool and its fixture tree live under `tools/` — inside the scanned set.
**Avoid:** keep the synthetic mini-repo fixture **domain-neutral** (`source`/`sink`/`widget`/`greeting`, per the Phase-24 precedent). If a fixture must reference an instance path, use non-contiguous `Path` segments (`Path("examples") / "log-parser"`) — the Phase-24/25 precedent.
**Warning sign:** the word `examples/` appearing as a contiguous literal anywhere in the new package.

### Pitfall 5: Test artifacts written into the repo, then "proven deterministic" with `git diff`
**What goes wrong:** the artifacts aren't committed, so `git diff` is vacuously clean and the determinism test proves nothing.
**Why:** the exact trap `pointer_index.py:12-14` documents.
**Avoid:** prove determinism by **byte comparison of two independent runs** into two `tmp_path` dirs, plus a **committed syrupy snapshot** of the artifact rendered over the fixture tree.

### Pitfall 6: `tmp_path` leaking into the artifacts
**What goes wrong:** the syrupy snapshot changes every run because absolute tmp paths are embedded.
**Why:** the walker recorded absolute paths.
**Avoid:** thread a `base_dir`/`target_root` parameter through and emit only `relative_to(base).as_posix()` keys — `repo_map.build_graph(base_dir=…)` exists for precisely this reason.

### Pitfall 7: Secret material leaking into the artifact via the *reason*
**What goes wrong:** a helpful "matched pattern: `api_key=AKIA…`" excerpt lands in the emitted JSON — which Phase 27 then commits into a task batch.
**Why:** natural diagnostic instinct.
**Avoid:** an excluded-secret record carries **path + reason slug + size only** — never the matched bytes, never a content hash (a hash of a low-entropy secret is itself a fingerprint). `capture._refuse_if_sensitive` records only *field names*, never values — mirror that.

### Pitfall 8: Symlink loops and traversal
**What goes wrong:** `rglob("*")` on a target with a self-referential symlink hangs or escapes.
**Why:** no confinement.
**Avoid:** Pattern 2's `resolve()` + `parents` guard on every path, and skip (never follow) directory symlinks that resolve outside the target root. Also record them as `excluded: symlink-escape` rather than silently dropping.

### Pitfall 9: The scanner is pointed at this repo and rewrites its own inputs
**What goes wrong:** `--out` defaults inside the target; run 2 inventories run 1's output.
**Avoid:** validate `--out` is not inside `--target` (compare resolved paths, raise on violation) and, defensively, exclude the out dir from enumeration.

---

## Code Examples

### Canonical artifact writer (use exactly one, in one place)

```python
# Source: composition of tools/memory_regen/pointer_index.py:221 and tools/evidence/capture.py:36
def _dump(document: dict) -> bytes:
    """The ONE canonical serialization for every adoption artifact.

    sort_keys → key order independent of construction order.
    indent=2   → reviewable diffs (matches every other artifact in the repo).
    ensure_ascii=True → a non-ASCII path in a brownfield target cannot vary the bytes.
    trailing "\\n" → POSIX-clean; required for byte-identical re-runs.
    """
    return (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
```

### Content hash for an evidence pointer (bounded)

```python
# stdlib only; stat BEFORE open so the cap is a real bound.
def _evidence_pointer(path: Path, base: Path, max_bytes: int) -> dict:
    size = path.stat().st_size
    rel = path.resolve().relative_to(base).as_posix()
    if size > max_bytes:
        return {"path": rel, "size": size, "excluded": "size-capped"}
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return {"path": rel, "size": size, "sha256": digest.hexdigest()}
```

### Ignore-respecting enumeration with a recorded fallback

```python
# Precedent: tools/harness_lint/tests/test_core_no_example_dep.py uses `git ls-files` (shell=False).
def _enumerate(target: Path) -> tuple[list[Path], str]:
    argv = ["git", "-C", str(target), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    try:
        proc = subprocess.run(argv, capture_output=True, check=False)   # shell=False, fixed argv
        if proc.returncode == 0:
            names = [n for n in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if n]
            return sorted(target / n for n in names), "git"
    except (OSError, UnicodeDecodeError):
        pass
    return _builtin_walk(target), "builtin"   # denylist walk; mode recorded in the artifact
```

*(Note: this is the one `subprocess` call in the tool. It is a **fixed argv to `git`**, not a discovered script — distinct from what §147 forbids. State that distinction explicitly in the plan so a reviewer does not read it as a violation. If the planner prefers zero subprocess, the builtin walk alone is acceptable — but then "ignore-respecting" degrades to the denylist and the plan must say so.)*

### Disposition rule chain (totality-testable)

```python
def disposition(rel: str, target_root: Path, proposed_sha: str | None) -> str | None:
    if is_gsd_owned(rel):                                        # imported from harness_emit.manifest
        return None                                              # excluded, not a destination
    if resolve_path(CONSTITUTION_GLOBS, rel) == "deny" or rel == "libs/normalize-spec.md":
        return "human-ratification-required"
    if resolve_path(DERIVED_GLOBS, rel) == "deny":
        return "derived-regenerate"
    if rel in MARKER_CAPABLE:                                    # AGENTS.md, CLAUDE.md, .claude/settings.json
        return "marker-merge"
    existing = target_root / rel
    if not existing.exists():
        return "create"
    return "preserve" if _sha256(existing) == proposed_sha else "conflict"
```

---

## State of the Art

| Old approach | Current approach in this repo | When changed | Impact on Phase 26 |
|---|---|---|---|
| Ad-hoc `.rglob` walks | Confined + symlink-guarded walk idiom (T-02-10 / T-16-01) | Phases 2 / 16 | Copy the idiom verbatim; do not invent. |
| `json.dumps(sort_keys=True)` for contract hashing | RFC-8785 via `rfc8785.dumps` in `contract_hash` | Phase 1 (CONTRACT-04) | Use `schema_hash` for schemas only; raw bytes use plain sha256. |
| Hand-written `docs/reference/*.md` | Generated by `tools.docs_sync` from `contracts/**` | Phase 3 (DOCS-03) | Three new schemas ⇒ three new generated pages. |
| `.memory/derived/contracts-index.md` gitignored | Flipped to **tracked** so CI can gate it | Phase 9 | Must be regenerated + committed in this phase's wave. |
| Free-form pipeline `edges` | Additive `[[contract_graph.relationships]]` + `effective_relationships()` lowering | Phase 24 (TOPO-02/03) | Proposed relationships use the new record shape; legacy `pipeline/…` id namespace is taken — use `adoption/…`. |

**Deprecated / do not reach for:** none identified in this domain. No external library in this space is being considered.

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 **(RESOLVED: D-08 — BROADENED)** | ~~"Source dumps" means over-cap text blobs and `dump`/`snapshot`/`backup`-segment paths~~ → **both readings**: whole-repo single-file concatenations (repomix/gitingest, detected by banner marker in the first 2 KiB) **plus** over-cap text blobs and `dump`/`snapshot`/`backup`-segment paths. Exclusion reason `source-dump`. | §Exclusion Rules | The phrase is undefined in REQUIREMENTS.md and v2.3 FINAL; a different intent (e.g. "a single-file concatenation of a whole repo, as produced by repomix/gitingest") would change the detection rule. **Recommend confirming with the user or letting discuss-phase resolve.** |
| A2 | Vendored-directory denylist (`node_modules`, `vendor`, `third_party`, `Pods`, `bower_components`, …) | §Exclusion Rules | Under-inclusive on an unusual ecosystem ⇒ noise in the inventory (recoverable; every exclusion is recorded and re-runnable). |
| A3 | Binary detection via NUL byte in the first 8192 bytes | §Exclusion Rules | A UTF-16 text file is misclassified binary. Low impact — it is recorded as excluded with a reason, not silently dropped. |
| A4 | Extended secret-path suffixes (`*.pem`, `*.key`, `id_rsa*`, `.npmrc`, `.netrc`, …) beyond the committed `*.env` globs | §Exclusion Rules | Missing one ⇒ a secret-bearing path is inventoried by path (content is still never emitted, and content patterns still apply). |
| A5 | Content marker regex for "generated" (`@generated`, `do not edit`, `auto-generated`) | §Exclusion Rules | False positive excludes a hand-authored file that says "do not edit" in prose. Mitigate by limiting the scan to the first 2048 bytes and requiring the marker in the first 5 lines. |
| A6 | Question `kind` enum values | §D-05 | Phase 27's prompt switch may need a value not listed; the enum should be extensible-by-ratification (it lives in a schema, so extending it is a contract change — that is intentional). |
| A7 | `MAX_FILE_BYTES` default of 256 KiB | §D-07 / §Exclusion Rules | Too small ⇒ real source files excluded on repos with large generated-but-tracked files; too large ⇒ slow scans. Make it a CLI flag with the default recorded **in the artifact** so a run is self-describing. |
| A8 | Recommended package name `tools/adoption_scan/` | §Recommended structure | Naming only; explicitly the planner's discretion per CONTEXT.md. |

---

## Open Questions (RESOLVED)

> All four were put to the user after this research landed and are now locked as
> **D-08..D-11** in `26-CONTEXT.md` § "Research-round resolutions". Assumption **A1**
> ("source dumps") was resolved in the same round. The recommendations below were
> accepted except where a `RESOLVED:` marker says otherwise. Do not re-litigate.

1. **RESOLVED: D-10.** (Recommendation accepted.) **Does the inventory record excluded files, or omit them?**
   - What we know: ADOPT-01 says the inventory "excludes" secrets/binaries/vendor/generated; roadmap success criterion 4 requires that "secret exclusion … detection **passes**," which is only testable if exclusions are observable.
   - What's unclear: whether "excludes" means "not in the included set" or "absent entirely."
   - **Recommendation:** record every exclusion as `{path, size, reason}` with **no content hash and no content excerpt**, in a separate `excluded[]` array. This satisfies both readings, makes D-06's per-detection asserts trivial, and keeps secret material out of the artifact.

2. **RESOLVED: D-09.** (Recommendation accepted — allowed, fixed argv, `shell=False`, with a complete builtin fallback; the design must not depend on git.) **Is `git ls-files` acceptable given "no arbitrary command execution"?**
   - What we know: §147 forbids *executing discovered scripts*; the repo already shells out to `git` with a fixed argv in a CI-gated test and in `capture._committed_approval` / `drift._git_show`.
   - What's unclear: whether the phase's own stricter invariant ("no arbitrary command execution") was intended to also exclude a fixed `git` argv.
   - **Recommendation:** implement it as a fixed-argv, `shell=False`, failure-tolerant call with a recorded fallback mode, and call the distinction out explicitly in the plan's threat model. If the planner or a reviewer disagrees, the builtin denylist walk is a complete fallback — the design must not *depend* on git.

3. **RESOLVED: D-11 (first half).** (Recommendation accepted — three self-contained schemas, duplicated small `$defs`, no cross-file `$ref`.) **One schema or three under `contracts/harness/adoption/`?**
   - D-01 says three (inventory / plan / manifest), mirroring task-control's five files. That is the recommendation. A shared `$defs` (evidence pointer, classification enum, disposition enum) would ideally live in a fourth `common.schema.json` — but note that cross-file `$ref` has never been used in this repo's contracts (all 8 existing schemas are self-contained). **Recommendation: keep each of the three self-contained and duplicate the small `$defs`**, matching existing style, rather than introducing cross-file `$ref` resolution that `check-jsonschema` and `schema_hash` have never been exercised against.

4. **RESOLVED: D-11 (second half).** (Recommendation accepted — `--out` is required, no default, refused when it resolves inside `--target`.) **Where does the tool write by default?**
   - Not specified anywhere. Phase 27 will place artifacts under `.workflow/tasks/<task-id>/artifacts/adoption/<batch-id>/`, but Phase 26 must not create a task plane (§146).
   - **Recommendation:** `--out` is **required** (no default), and the tool refuses if `--out` resolves inside `--target`. This makes Phase 27's integration a pure argument change with zero behavior change.

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python | the whole phase | ✓ | `>=3.11` enforced by `pyproject.toml`; repo runs on it today | — |
| `uv` | test/run invocation | ✓ | workspace resolves today (`uv.lock` committed) | — |
| `pytest` | tests | ✓ | `>=8.4,<9` | — |
| `syrupy` | determinism snapshots | ✓ | `5.2.0` | plain byte-comparison assertions |
| `jsonschema` | artifact validation in tests | ✓ | `4.26.0` | — |
| `rfc8785` | schema-hash rebaseline | ✓ | `0.1.4` | — |
| `git` | ignore-respecting enumeration | ✓ (repo is a git tree; already shelled out to by existing tests/tools) | any | **builtin denylist walk**, mode recorded in the artifact |
| `.NET SDK` | — | not needed | — | — |
| Network | — | not needed | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** `git` (fallback: builtin denylist enumeration).

---

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Framework | pytest `>=8.4,<9` (uv workspace) + syrupy 5.2.0 |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["libs/python", "tools"]`, `python_files = ["test_*.py", "*_test.py"]`) — **plus a new `tools/<pkg>/tests/conftest.py`** for `sys.path` wiring (Wave 0) |
| Quick run command | `uv run pytest tools/<pkg> -q` |
| Full suite command | `uv run pytest -q` |
| Contract gates | `uv run python -m tools.contract_drift.drift` · `uv run python -m tools.docs_sync` + `uv run python -m tools.memory_regen.contracts_index` (then `git diff --exit-code -- docs/reference .memory/derived/contracts-index.md`) |
| Estimated runtime | quick ~5 s; full suite ~60 s (unchanged from Phase 24/25) |

### Phase Requirements → Test Map

| Req | Behavior | Test type | Automated command | File exists? |
|---|---|---|---|---|
| ADOPT-01 | Target tree is byte-unchanged after a scan (hash every fixture file before/after) | unit | `uv run pytest tools/<pkg>/tests/test_readonly.py -x` | ❌ Wave 0 |
| ADOPT-01 | Scan is confined — a symlink escaping the target root is skipped and recorded | unit | `… tests/test_scan_exclusions.py::test_symlink_escape_excluded` | ❌ Wave 0 |
| ADOPT-01 | Secret file excluded by path (`.env`) | unit | `…::test_secret_path_excluded` | ❌ Wave 0 |
| ADOPT-01 | Secret excluded by content pattern; **matched bytes absent from artifact** | unit | `…::test_secret_content_excluded_and_not_echoed` | ❌ Wave 0 |
| ADOPT-01 | Binary excluded (NUL prefix) | unit | `…::test_binary_excluded` | ❌ Wave 0 |
| ADOPT-01 | Vendored dir excluded (`node_modules/`) | unit | `…::test_vendored_excluded` | ❌ Wave 0 |
| ADOPT-01 | Generated file excluded (`__pycache__` + `@generated` marker) | unit | `…::test_generated_excluded` | ❌ Wave 0 |
| ADOPT-01 | Over-cap file excluded as `size-capped`, **not read** | unit | `…::test_size_cap` | ❌ Wave 0 |
| ADOPT-01 | Evidence pointers carry `{path, sha256, size}` and paths are repo-relative POSIX | unit | `…::test_evidence_pointer_shape` | ❌ Wave 0 |
| ADOPT-01 | Language + manifest + doc/ADR/AGENTS/CODEOWNERS/CI surfaces detected | unit | `… tests/test_detect.py` | ❌ Wave 0 |
| **SC-1** | Double run over the fixture is byte-identical | unit | `… tests/test_determinism.py::test_double_run_byte_identical` | ❌ Wave 0 |
| **SC-1** | Seeded-shuffled enumeration order produces identical bytes | unit | `…::test_shuffled_enumeration_byte_identical` | ❌ Wave 0 |
| **SC-1** | Committed syrupy snapshot of all three artifacts | snapshot | `… tests/test_snapshots.py` | ❌ Wave 0 |
| ADOPT-02 | Every plan entry carries exactly one of observed/inferred/unknown | unit | `… tests/test_plan_classification.py::test_every_entry_classified` | ❌ Wave 0 |
| ADOPT-02 | An ambiguous-ownership case yields a **question**, never an `authority` | unit | `…::test_unresolved_ownership_becomes_question` | ❌ Wave 0 |
| ADOPT-02 | Question records satisfy the D-05 floor + deterministic ordering | unit | `…::test_question_shape_and_ordering` | ❌ Wave 0 |
| ADOPT-02 | Relationship candidates validate against `topology/relationship.schema.json` | unit | `…::test_relationship_candidates_validate` | ❌ Wave 0 |
| **ADOPT-03 / SC-3** | Every catalog destination resolves to exactly one disposition (totality) | unit | `… tests/test_dispositions.py::test_total` | ❌ Wave 0 |
| ADOPT-03 | Each of the 6 dispositions is exercised by ≥1 case | unit | `…::test_each_disposition_reachable` | ❌ Wave 0 |
| ADOPT-03 | Constitution path is `human-ratification-required` even when the file exists | unit | `…::test_constitution_always_ratification` | ❌ Wave 0 |
| ADOPT-03 | Hash-equal → `preserve`; hash-different → `conflict` | unit | `…::test_collision_rule` | ❌ Wave 0 |
| ADOPT-03 | `marker-merge` only for `AGENTS.md`/`CLAUDE.md`/`.claude/settings.json` | unit | `…::test_marker_capable_set` | ❌ Wave 0 |
| ADOPT-03 | GSD-owned lanes are excluded, not dispositioned | unit | `…::test_gsd_lanes_excluded` | ❌ Wave 0 |
| D-01 | All three artifacts validate against their new schemas | unit | `… tests/test_schema_conformance.py` | ❌ Wave 0 |
| D-01 | Drift gate green after rebaseline | gate | `uv run python -m tools.contract_drift.drift` | ✅ exists |
| D-01 | Committed-derived plane fresh | gate | `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index && git diff --exit-code -- docs/reference .memory/derived/contracts-index.md` | ✅ exists |
| repo invariant | GEN-04 core→example guard still green | gate | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | ✅ exists |
| repo invariant | `uv.lock` unchanged | gate | `uv sync --all-packages && git diff --exit-code uv.lock` | ✅ exists |

### Sampling Rate

- **Per task commit:** `uv run pytest tools/<pkg> -q`
- **Per wave merge:** `uv run pytest -q` + `uv run python -m tools.contract_drift.drift`
- **Phase gate:** full suite green + drift green + committed-derived fresh + `git diff --exit-code uv.lock` clean, before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tools/<pkg>/pyproject.toml` — workspace member (else `uv sync --all-packages` fails)
- [ ] `tools/<pkg>/tests/__init__.py` + `conftest.py` — `sys.path` wiring, `parents[3]` (copy `tools/harness_config/tests/conftest.py`)
- [ ] `tools/<pkg>/tests/fixtures/minirepo/**` — the ONE synthetic target tree (D-06), embedding: secret file · secret content · binary · vendored dir · generated file · over-cap file · collision pair (equal + different) · ambiguous-evidence case · escaping symlink. Domain-neutral vocabulary only (Pitfall 4).
- [ ] All `test_*.py` files listed ❌ above
- [ ] Framework install: **none** — pytest/syrupy already present.

---

## Security Domain

### Applicable ASVS Categories

| ASVS category | Applies | Standard control |
|---|---|---|
| V2 Authentication | no | No auth surface; local CLI tool. |
| V3 Session Management | no | Stateless single-shot invocation. |
| V4 Access Control | **yes** | The constitution plane is the access-control boundary: `tools/hooks/contract_guard` + `.github/CODEOWNERS` + `GOLDEN_APPROVE_HUMAN`. The tool must never write it and must always disposition it `human-ratification-required`. |
| V5 Input Validation | **yes** | The *target tree is untrusted input*. Path confinement (`resolve()` + `parents` guard), size caps before read, bounded content scanning, and `Draft202012Validator` on every emitted artifact. |
| V6 Cryptography | **yes (hashing only)** | `hashlib.sha256` for file bytes; `rfc8785` + sha256 via `tools.contract_hash` for schemas. Never hand-roll either. No encryption, no key handling. |
| V12 File & Resources | **yes** | The dominant category: traversal, symlink escape, resource exhaustion, and secret exfiltration via artifact content. |
| V14 Configuration | **yes** | New workspace member must not mutate `uv.lock`; new schemas must not desync `contracts/.hashes/manifest.json`. |

### Known Threat Patterns for this phase

| Pattern | STRIDE | Standard mitigation |
|---|---|---|
| Path traversal / symlink escape out of the target root | Tampering, Info Disclosure | `resolved.relative_to`/`parents` confinement guard on **every** path (repo_map idiom); skip + record escapes. |
| Resource exhaustion on a huge or symlink-looped target | Denial of Service | `stat()`-first size cap; never follow escaping directory symlinks; bounded prefix reads for content heuristics. |
| Secret exfiltration into the emitted artifact (which Phase 27 commits) | Information Disclosure | Exclude on suspicion (D-02); record path + reason slug + size **only** — never matched bytes, never a content hash for a secret-flagged file. Mirrors `capture._refuse_if_sensitive` (field names only). |
| Agent self-ratification of the new contracts | Elevation of Privilege | Unchanged existing controls: `contract_guard` PreToolUse deny + `GOLDEN_APPROVE_HUMAN` + CODEOWNERS `/contracts/`. Phase 26 adds no new bypass. Residual risk (CODEOWNERS advisory unless branch protection is enabled) is pre-accepted, documented in `.github/CODEOWNERS` and Phase 24's `T-24-02`. |
| Executing content discovered in the target (a "test command" the inventory found) | Elevation of Privilege | **Structural**: the tool has no execution path for discovered strings. Detected test commands are recorded as `inferred` **data**, never invoked. §147. |
| Command injection via the one `git` subprocess | Tampering | Fixed argv list, `shell=False`, target path passed as a discrete `-C` argument, never string-interpolated. Precedent: `test_core_no_example_dep.py`, `capture._committed_approval`. |
| Scanner mutates the target it is auditing | Tampering | `--out` refused inside `--target`; a before/after hash of every fixture file asserts byte-invariance (`test_readonly.py`). |
| Non-deterministic output silently invalidating Phase 27 approvals | Repudiation | The full determinism recipe + double-run + shuffled-order + committed snapshot tests. |

---

## Sources

### Primary (HIGH confidence — read directly from the working tree this session)

- `tools/evidence/capture.py` (339 lines, full read) — D-07 gap analysis
- `tools/contract_hash/hash.py` (full read) — RFC-8785 hashing, manifest glob, `--write` rebaseline
- `tools/contract_drift/drift.py` (lines 1-300) — `run_gate` semantics, added/removed classification
- `tools/harness_emit/merge.py` (full read) — marker regimes, `BEGIN_MARKER`/`END_MARKER`, `merge_settings`, `HARNESS_SIGNATURES`
- `tools/harness_emit/manifest.py` (full read) — `is_gsd_owned`, `_confined`, prune-then-write
- `tools/harness_emit/generate.py` (grep of write targets) — emitted destination set
- `tools/memory_regen/repo_map.py`, `tools/memory_regen/pointer_index.py` (full reads) — walk confinement, generator quartet, determinism discipline
- `tools/harness_config/loader.py`, `tools/workspace_config/loader.py` (full reads) — topology/config vocabulary, `effective_relationships` lowering + `pipeline/` id namespace
- `tools/hooks/contract_guard.py`, `tools/hooks/secret_scan.py` (head reads) — `CONSTITUTION_GLOBS`, `SECRET_PATH_GLOBS`, `PATTERNS`, `ALLOWLIST_PREFIXES`
- `tools/harness_perms/__init__.py` — `resolve_path`/`resolve_bash`/`load_matrix` lazy API
- `tools/harness_lint/tests/test_core_no_example_dep.py` (head read) — GEN-04/GEN-05 token tiers, `git ls-files` precedent
- `contracts/harness/topology/relationship.schema.json` (full read), `contracts/harness/task-control/evidence.schema.json` (head), `contracts/harness/task-control/gate-registry.json` (`secret_patterns`, gates)
- `.github/workflows/ci.yml` (jobs: contract-check, drift, golden, harness-core, lifecycle, emit-drift, stale-derived, workspace, fan-in)
- `.github/CODEOWNERS` (full read) — constitution routing + advisory caveat + solo-approval nuance
- `.gitignore`, `pyproject.toml`, `workspace.toml` layout, `tools/docs_sync/pyproject.toml`, `tools/harness_config/tests/conftest.py`
- `harness/skills/{gate-model,two-plane-memory,python-conventions}/SKILL.md`
- `.planning/phases/24-…/24-01-PLAN.md` (Tasks 1 & 3, threat model) — the ratification procedure precedent
- `git show 7e3630d` — the actual Phase-24 schema-landing commit
- `.planning/research/v2.3-scoping-FINAL.md` (Phase 26 block, §146/147/152), `.planning/REQUIREMENTS.md` (ADOPT-01..07), `.planning/ROADMAP.md` (Phase 26 success criteria)

### Secondary (MEDIUM confidence)

- None — no external source was consulted.

### Tertiary (LOW confidence)

- The `[ASSUMED]`-tagged detection denylists in §Exclusion Rules (A1-A5, A7) rest on general ecosystem convention, not on an in-repo or documented source. See the Assumptions Log.

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — every module, version, and pin was read from the committed tree this session; nothing new is introduced.
- Architecture / determinism recipe: **HIGH** — four existing modules implement the identical pattern and document why.
- Destination catalog: **HIGH** for rows derived from code (constitution globs, marker set, emitted set, GSD exclusion); **MEDIUM** for the human-authored doc/config rows, which are enumerated from the live tree and could grow.
- Ratification procedure: **HIGH** — reconstructed from the actual Phase-24 plan *and* the actual commit; the derived-plane coupling was verified against `ci.yml`.
- Exclusion rules: **MEDIUM** — secret patterns and confinement are verified in-repo; binary/vendor/generated/source-dump denylists are conventional assumptions (A1-A5).
- D-05 question shape: **MEDIUM** — grounded in ADOPT-04/06's stated consumption requirements, but Phase 27 is unplanned, so the shape is a recommendation, not an observation.

**Research date:** 2026-07-19
**Valid until:** stable — this is internal repo knowledge with no external dependency. Re-verify only if `tools/harness_emit`, `tools/hooks`, `contracts/`, or `.github/workflows/ci.yml` change materially.
