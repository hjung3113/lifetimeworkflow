# Phase 28: Human-Docs Registry, Guard, Derived Queue — Research

**Researched:** 2026-07-21
**Domain:** In-repo deterministic gates over human-authored documentation (registry + digest ledger + classification gate + derived queue). Entirely internal machinery — no external ecosystem.
**Confidence:** HIGH on repo machinery (everything below is read from source at cited line numbers); MEDIUM on two design choices flagged in Open Questions.

## Summary

This phase adds **one new gate** and **one new derived generator** to a repo that already has canonical shapes for both. Nothing here needs invention: the RFC 8785 + SHA-256 manifest/baseline gate (`tools/contract_hash` + `tools/contract_drift`), the `rows → render → write → main` DERIVED generator (`tools/memory_regen/contracts_index.py`), the DATA-slot + thin-loader + consistency-test triad (`harness/project.toml` + `tools/harness_config/loader.py` + `tools/harness_lint/tests/test_language_config.py`), the committed-ledger-bound-to-exact-digests pattern (`tools/adoption_apply/approval.py`), the path-confinement choke point (`tools/adoption_apply/apply.py:94`), and the affected-set query API (`tools/contract_graph/query.py`) all exist and are load-bearing. The phase's engineering risk is almost entirely **integration risk**, not novel-algorithm risk.

Three findings dominate the design space and should be treated as near-locked:

1. **The registry must NOT live on the constitution plane.** `tools/hooks/contract_guard.py:44` denies every agent write under `contracts/**`, `docs/adr/**`, `golden/**`. DOCSUP-07 (Phase 29) requires `/adopt` to *propose* registry/ledger entries. An agent cannot propose an edit to a file it is structurally forbidden from writing. Put the registry at `docs/doc-dependencies.toml` (the requirement names this path literally, REQUIREMENTS.md:33) as ordinary reviewed config; put only its **schema** on the constitution plane at `contracts/harness/docs/doc-dependencies.schema.json`. This is exactly the Phase 26/27 split — `contracts/harness/adoption/manifest.schema.json` is hash-gated, its instances are not.

2. **The anti-rubber-stamp control (DOCSUP-03) requires git history.** A ledger entry claiming `updated` is only meaningful relative to the previous committed ledger state. Reuse `tools/contract_drift/drift.py:129-147` (`_git_show_at`, fixed argv, `shell=False`, `HEAD:./<path>`, degrade-to-None) — the same primitive DOCSUP-05's "old-to-new diff only when retrievable from git" needs. One helper, two consumers.

3. **The derived queue must stay gitignored.** `.gitignore:23-24` uses the contents-form `.memory/derived/*` + `!.memory/derived/contracts-index.md`; the queue is already ignored with **zero .gitignore change**. Committing it would put it into the `stale-derived` CI job (`.github/workflows/ci.yml:227-256`), which regenerates and `git diff --cached --exit-code`s — meaning every ordinary source commit would fail CI unless the queue were regenerated and committed in the same commit. That is pure churn on an artifact whose entire content is a function of files being edited.

**Primary recommendation:** Build `tools/docs_guard/` as one new uv workspace member (registry loader/validator + digest + classifier + CLI, mirroring `tools/adoption_scan/`'s module split), add `tools/memory_regen/docs_staleness.py` as a thin renderer that *reads the guard's result and writes the queue*, and add exactly one droppable, conditional section to `inject.py::assemble`. Everything else is an extension of an existing file.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Registry shape (schema) | Constitution plane (`contracts/harness/docs/`) | — | A registry a gate fails on is contract-shaped; the *shape* is the contract, hash-gated by `tools.contract_hash` |
| Registry rows (data) | Repo config (`docs/doc-dependencies.toml`) | — | Must be agent-proposable (DOCSUP-07); `contract_guard.py:44` forbids that under `contracts/**` |
| Registry parse + validate | `tools/docs_guard/registry.py` | `jsonschema.Draft202012Validator` (already pinned, `pyproject.toml:10`) | Thin-loader precedent: `tools/harness_config/loader.py:32-39` |
| Digest computation | `tools/docs_guard/digest.py` | — | Markdown/bytes, not JSON — `contract_hash.schema_hash` (JCS) is structurally inapplicable |
| Classification + exit codes | `tools/docs_guard/guard.py` + `cli.py` | — | Result-dict pattern of `contract_drift.run_gate` (drift.py:177-216) |
| Graph impact ids | `tools/contract_graph/query.py` (REUSE verbatim) | `compile.py:49` | query.py:5 already names DOCSUP as its intended consumer |
| Queue render | `tools/memory_regen/docs_staleness.py` | — | Hard constraint: `test_derived_freshness.py:32` restricts the curator/`/refresh-memory` surface to `memory_regen` + `docs_sync` only |
| SessionStart pointer | `tools/memory_regen/inject.py` (+1 section) | — | Single injection contract (D-01, STATE.md `[02-02]`) |
| CI enforcement | `.github/workflows/ci.yml` (+1 job, +1 `gate.needs` entry) | — | Separate-job idiom (`emit-drift` / `stale-derived` / `workspace`) |

## Standard Stack

**Zero new dependencies.** Every capability is covered by what is already pinned.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tomllib` | stdlib (py>=3.11) | Parse `docs/doc-dependencies.toml` | `tools/harness_config/loader.py:18,38` already uses it as the only TOML reader; `pyproject.toml:5` pins `requires-python >=3.11` |
| `jsonschema` | 4.26.0 (pinned, `pyproject.toml:10`) | Validate the parsed registry dict against the constitution-plane schema | `tools/adoption_apply/approval.py:38,~185` uses `Draft202012Validator` in-process for the identical reason |
| `hashlib` | stdlib | SHA-256 over path+byte sets | `contract_hash/hash.py:44`, `approval.py:57-63` |
| `subprocess` (fixed argv, `shell=False`) | stdlib | `git show HEAD:./<path>` retrieval | `drift.py:129-147` — copy the shape, do not re-derive |

### Deliberately NOT used
| Not used | Why |
|----------|-----|
| `rfc8785` / `contract_hash.schema_hash` | JCS canonicalizes **JSON**. Human docs are markdown/TOML/prose. Calling `schema_hash` on a `.md` raises `json.JSONDecodeError`. Reuse the *pattern* (canonical serialize → SHA-256), not the function. |
| `check-jsonschema` CLI | `/contract-check`'s step 1 (`harness/commands/contract-check.md:27`) pairs `<name>.schema.json` with sibling `.yaml/.yml/.json` — a `.toml` instance is silently skipped (presence-safe). The registry is validated in-process by the guard, not by `/contract-check`. **This is a real gap worth stating in the plan.** |
| `refuse_unsafe_destination` (`apply.py:109`) | It also refuses constitution-plane paths. Registry **sources** legitimately include `contracts/**`. Use the narrower `refuse_if_outside_root` (`apply.py:94`) or the `_confine` idiom (`docs_sync/generate.py:189`) for path-escape rejection only. |

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** Every module named above is either Python stdlib or already present in `pyproject.toml:8-11` / `pyproject.toml:15-21`. No slopcheck run was needed; no `npm view`/`pip index` verification applies. If the planner introduces a dependency the audit must be run before that plan lands.

## Concrete Answers to the Phase's Open Design Questions

### Q1 — Where does `docs/doc-dependencies.toml` live, and is it a contract?

**Answer: split it.** Registry data at `docs/doc-dependencies.toml`; registry *shape* at `contracts/harness/docs/doc-dependencies.schema.json`.

Argument from repo precedent, in order of force:

- **Blocking:** `tools/hooks/contract_guard.py:44` sets `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]`, and `decide()` denies any agent Write/Edit landing there without a non-empty `GOLDEN_APPROVE_HUMAN` (contract_guard.py:47-49, STATE.md `[04]` "empty string does not bypass"). DOCSUP-07 requires `/adopt` to *propose* registry entries. A registry under `contracts/` makes DOCSUP-07 unimplementable without handing agents the human token.
- **Precedent:** `harness/project.toml` is the repo's other "data slot a gate fails on" — `[[languages]]`/`[[components]]`/`[[contract_graph.relationships]]` — and it is **not** on the constitution plane and **not** hash-gated. Its correctness is enforced by a *consistency test* (`tools/harness_lint/tests/test_language_config.py`, `test_pipeline_config.py`, `test_contract_graph_config.py`), which STATE.md `[05-04]` records as the deliberate choice over codegen ("D-03 'codegen is overkill'"). Phase 28's guard is the same kind of enforcer.
- **Precedent:** `contracts/harness/adoption/manifest.schema.json` is on the constitution plane; the manifest *instances* live in the task artifact plane. Phase 27.1 SC-4 tightened the schema and paid the full human-ratification cost **once** (`.planning/ROADMAP.md:642` — "paired with hash rebaseline, derived regeneration, and human ratification in one atomic commit"). Paying that once for the registry schema is right; paying it per binding row is not.

**Human-ratification cost of putting the registry itself on the constitution plane (the rejected option):** every `[[binding]]` addition becomes a `GOLDEN_APPROVE_HUMAN`-gated write + `python -m tools.contract_hash.hash --write` rebaseline + `docs_sync` + `contracts_index` regeneration in one atomic commit + CODEOWNERS review (`.github/CODEOWNERS:26`). DOCSUP-07 wants a *seeding* pass over "the highest-risk existing docs" — that is many rows. This option is not merely expensive; it is incompatible with the downstream requirement.

**Cost the recommended split still pays (must be in the plan):** adding `contracts/harness/docs/doc-dependencies.schema.json` is a constitution-plane act. It requires, in ONE commit: the new schema file (human-token write), `uv run python -m tools.contract_hash.hash --write` (baseline at `contracts/.hashes/manifest.json`, hash.py:26), `uv run python -m tools.docs_sync` (a new `docs/reference/doc-dependencies.md` page appears — `docs_sync/generate.py` generates one page per schema), `uv run python -m tools.memory_regen.contracts_index` (a new row in the committed `.memory/derived/contracts-index.md`), and regeneration of the two committed syrupy snapshots. Skipping any of these fails the `drift` job or the `stale-derived` job (ci.yml:227-256). The Phase 27.1-03 plan is the working template for this commit shape.

**Proposed registry schema shape** (constrain hard; DOCSUP-01 lists the required rejections):

```toml
# docs/doc-dependencies.toml
[[binding]]
id = "normalize-core-to-how-to"          # unique, [a-z0-9-]+, minLength 1
sources = ["libs/python/normalize/**"]   # >=1 for severity="required" (empty required selector rejected)
target  = "docs/how-to/task-lifecycle.md"# exactly one human-authored target
severity = "required"                    # enum: required | advisory
dispositions = ["updated", "reviewed-no-change"]  # policy; ADR targets get the restricted set
```

Validation rules (all must be per-rule data cases, not one smoke test):

| Rejection (DOCSUP-01) | Mechanism | Reuse |
|---|---|---|
| Path escape | absolute path or `..` segment in `sources[i]` / `target` → reject **before** any filesystem call | `apply.py:109-125` structural pre-check shape; confinement via `refuse_if_outside_root` (`apply.py:94`) |
| Duplicate id | sorted-diagnostic duplicate scan | `loader.py:149-160` (`effective_relationships` duplicate-id block) — copy the deterministic-sorted-diagnostic idiom verbatim |
| Empty required selector | `severity == "required" and not sources` → reject | new, trivial |
| Derived/reference target | `target` matching `DERIVED_GLOBS` | **import** `tools.adoption_scan.destinations.DERIVED_GLOBS` (destinations.py:105-114) — it already lists `docs/reference/**`, `.memory/derived/**`, `.memory/state/**`, `.opencode/**`, `.claude/{agents,commands,skills}/**`, `opencode.json`. Do not retype it. |
| Accepted-ADR edit policy | `target` under `docs/adr/**` and `dispositions` containing anything outside `{REVIEWED_STILL_CURRENT, SUPERSEDING_ADR_REQUIRED}` → reject | see Q6 |

### Q2 — The ledger's exact committed shape and location

**Location:** `docs/.docs-review-ledger.toml` — sibling of the registry, same directory, same review lens, one TOML parser for both. Rejected alternatives: `contracts/.hashes/`-style hidden dir under the constitution plane (agent-unwritable, same blocker as Q1); `.workflow/tasks/**` (session-local per-run data, deliberately excluded from the destination catalog, destinations.py:132-141 — a ledger must survive across tasks); `.memory/state/` (that plane is *session* state, `.gitignore:18`).

**Closest existing precedent:** `contracts/.hashes/manifest.json` (`contract_hash/hash.py:26,69-82`) — a committed, machine-written baseline of exact content digests that a gate diffs the live tree against. The docs ledger is that same object with a disposition column. The second precedent is `tools/adoption_apply/approval.py` for "a committed record bound to exact digests that any input change invalidates" (approval.py:12-17).

**Exact shape — nothing else is permitted:**

```toml
[coverage]
uncovered_max = 12                       # the non-regression ratchet (see Q4)

[[reviewed]]
id = "normalize-core-to-how-to"          # binding id, must exist in the registry
source_digest = "<64 hex>"               # exact digest reviewed against
target_digest = "<64 hex>"               # exact digest reviewed against
disposition = "updated"                  # enum: updated | reviewed-no-change
```

**Forbidden fields, and the existing lint that would catch each if added:**

| Forbidden | Why | Detector |
|---|---|---|
| Any timestamp / `date` / `updated_at` | Wall-clock in a committed artifact destroys byte-reproducibility; the injector determinism scan already treats clock tokens as a defect class (`test_inject_determinism.py:70-85` scans for `datetime`, `.now()`, `time.time`). Note `approval.schema.json` **does** carry `approved_at` — that is a per-task artifact, not a repo-wide committed baseline; do not cite it as license. |
| Human names / reviewer identity | DOCSUP-02 explicit; CODEOWNERS + git authorship already carry identity, and duplicating it into a machine-diffed file creates churn and a PII surface |
| Prose copy of the doc | DOCSUP-04's "pointer-only" rule generalized; also unbounded growth |
| Model identifiers | CLAUDE.md non-negotiable ("커밋·PR·코드 코멘트 등 레포 산출물에 모델 식별자 미포함"); the emitter already has a real-model-id lint (STATE.md `[07-03]` `check_opencode_config`) — the plan should extend that lint's path set to the ledger, or add an equivalent |

Row ordering: sort `[[reviewed]]` by `id`, always. Write via a deterministic serializer (hand-rolled sorted TOML emit is fine and avoids a `tomli-w` dependency; `hash.py:81` sets the precedent of `sort_keys=True` + trailing newline).

### Q3 — How the digest is computed

**Do not reuse `contract_hash.schema_hash`** (it is JCS-over-JSON; see Standard Stack). **Do** reuse the *pattern* from `approval.py:57-63` (`_recompute_draft_hash`: sha256 over a fixed-order file list, recomputed fresh at every check, never cached) — with one correction.

Recommended algorithm, per binding, computed twice (once over `sources`, once over `target`):

```
resolved = sorted(unique(expand(selector) for selector in selectors), key=posix_path)
h = sha256()
for path in resolved:
    h.update(path.as_posix().encode("utf-8")); h.update(b"\n")
    h.update(sha256(path.read_bytes()).hexdigest().encode("ascii")); h.update(b"\n")
digest = h.hexdigest()
```

Why this and not `_recompute_draft_hash` verbatim: `approval.py:59-62` concatenates raw file bytes with **no separator and no path**. That is safe only because its file list is a fixed 3-element tuple (`_DRAFT_FILES`, approval.py:47). A registry selector expands to a *variable* set, so raw concatenation is ambiguous — moving a byte from the end of file A to the start of file B yields an identical digest, and adding/removing an empty file is invisible. Interleaving the path and the per-file hex digest closes both. **Flag this to the planner as a deliberate divergence from the precedent, with the reason recorded**, so a reviewer does not "fix" it back toward the precedent.

**Byte normalization: none.** Do not run the §4.3–4.6 normalize core over the bytes before hashing. Rationale: (a) the digest must agree with what a human sees in `git diff`; (b) `format-on-write` (HOOK-01, STATE.md `[04-04]`) and `polyglot_lint` already keep the tree LF/no-BOM, so a CRLF-only re-save should not be silently absorbed — it should not happen at all; (c) normalizing would make the digest disagree with the raw-byte model the ledger's reviewer used. Tradeoff accepted and worth one line in the plan.

**Missing file:** a resolved path that does not exist is not a digest input — it is a `BROKEN` binding (see Q4). Never hash "" for a missing file.

### Q4 — The five states: exact rules, severity, exit codes

Per-binding classification, evaluated in this order (first match wins — order matters, `BROKEN` must precede staleness):

| State | Rule | Effect |
|---|---|---|
| `BROKEN` | `target` does not exist, **or** a `sources` selector expands to zero paths, **or** the binding id has no `[[reviewed]]` row and `severity == "required"` | **fail** |
| `FRESH` | `ledger.source_digest == live source digest` **and** `ledger.target_digest == live target digest` | pass |
| `STALE_REQUIRED` | either digest differs and `severity == "required"` | **fail** |
| `STALE_ADVISORY` | either digest differs and `severity == "advisory"` | **warn** (stderr, counted, exit unchanged) |

`UNCOVERED` is **not** a binding state — it is a per-document state. Compute the human-authored doc corpus, subtract every registry `target`, and count the remainder.

**Human-authored corpus definition** (must be explicit or the count is not reproducible): every git-tracked file under `docs/tutorials/**`, `docs/how-to/**`, `docs/explanation/**`, plus `docs/glossary.md`, root `AGENTS.md`, `CLAUDE.md`, every nested `AGENTS.md`, `.memory/README.md`, and `README.md` files — **minus** everything matching `DERIVED_GLOBS` (destinations.py:105-114) and minus `docs/adr/**` if ADRs are handled as a separate class. Use git-tracked-only enumeration: `destinations.py:39-49` already documents why (an untracked working-tree file makes the count non-reproducible on a clean CI checkout — that exact bug was CR-01 in Phase 26).

**Uncovered non-regression storage:** `[coverage] uncovered_max = N` in the ledger (Q2). Guard computes `live_uncovered`; `live_uncovered > uncovered_max` → **fail**; `live_uncovered < uncovered_max` → **pass**, and print `ratchet can tighten: set uncovered_max = <live>`. **The guard must never write the ledger.** A gate that lowers its own threshold is self-blessing, and a read-only gate is also what makes the CI job idempotent. The operator tightens it by hand; that edit is reviewed like any other.

**Exit codes** — following the repo's existing conventions (`drift.py:370-390` uses 0/1; `approve.py` refusal uses 3; `adoption_apply/cli.py` stale-approval uses 4):

| Code | Meaning |
|------|---------|
| 0 | No `BROKEN`, no `STALE_REQUIRED`, uncovered within ratchet. `STALE_ADVISORY` may be present and is printed to stderr. |
| 1 | One or more `BROKEN` / `STALE_REQUIRED`, or uncovered-count regression |
| 2 | argparse usage error (stdlib default — do not reuse) |
| 3 | Registry invalid (DOCSUP-01 rejection). Distinct from 1 because the operator action is different: fix the registry, not the docs. |

### Q5 — Rejecting a ledger-only digest bump (DOCSUP-03's anti-rubber-stamp control)

**Name the mechanism: disposition/digest coherence against the previous committed ledger.**

The attack: an agent (or a hurried human) sees `STALE_REQUIRED`, copies the live `source_digest` into the ledger, writes `disposition = "updated"`, and the gate turns green — with the target document untouched. The digests alone cannot detect this, because after the paste they are consistent by construction.

The control has two halves, and both are needed:

1. **`reviewed-no-change` is content-bound.** It passes only when `ledger.source_digest == live source digest` **and** `ledger.target_digest == live target digest`. A stale or approximate value fails as `STALE_REQUIRED`. This is DOCSUP-03's "`reviewed-no-change` passes only against the exact current digest" and needs no history.

2. **`updated` requires a target delta in the same change.** Retrieve the previous committed ledger via `git show HEAD:./docs/.docs-review-ledger.toml` (reuse the `_git_show_at` shape, `drift.py:129-147`: fixed argv, `shell=False`, `cwd`-relative `HEAD:./<path>`, `CalledProcessError`/decode-error → `None`). For each row whose `disposition == "updated"`: if `source_digest` changed versus the previous committed row **and** `target_digest` is **unchanged** versus that row → **fail** with `disposition-incoherent: binding <id> claims 'updated' but its target digest is unchanged`. That is the ledger-only bump, caught structurally.

**Degradation when history is unretrievable** (shallow clone, first commit, detached tree): `_git_show_at` returns `None`. Recommendation: for `severity == "required"` bindings, treat an unverifiable `updated` claim as **fail** with an explicit `unverified-disposition` reason; for `advisory`, warn. Fail-closed on the required tier matches the repo's posture; DOCSUP-05's "old-to-new diff only when retrievable from git" already establishes honest degradation as the house style. **This is a design decision the planner should confirm with the user** — see Open Questions.

Corollary control worth adding cheaply: a `[[reviewed]]` row whose `id` is not in the registry → registry/ledger incoherence → exit 3. It closes "bless a binding that does not exist."

### Q6 — The accepted-ADR special case

Three repo facts constrain this:

- `docs/adr/**` is in `CONSTITUTION_GLOBS` (`contract_guard.py:44`) — agents cannot write ADRs at all without the human token.
- `docs/adr/README.md` establishes append-only / supersede-not-edit (STATE.md `[01-03]`: "adr/0001 immutably records… append-only/supersede-not-edit convention (DOCS-02)").
- ADR-0009 (`docs/adr/0009-*.md`) demonstrates the live shape: a `- **Status:** accepted` line plus `Supersedes:` / `Superseded by:` fields, and the phase-25 checkpoint pattern where an agent authors `Status: proposed` and a **human** flips it to `accepted` (`25-05-SUMMARY.md` key-decisions).

Design:

- **Registry validation (DOCSUP-01):** a binding whose `target` matches `docs/adr/**` MUST declare `dispositions = ["REVIEWED_STILL_CURRENT", "SUPERSEDING_ADR_REQUIRED"]` and MUST NOT include `updated`. Anything else → exit 3. This is the "accepted-ADR 편집 정책 거부" clause: the registry may not encode a policy that would ever ask anyone to edit an accepted ADR.
- **Status gate:** parse the ADR's `- **Status:**` line. Only `accepted` ADRs get the restricted vocabulary. A `proposed` ADR is still mid-ratification and should be `BROKEN`-adjacent or excluded — recommend: exclude `proposed` ADRs from binding targets entirely (reject at registry validation), because their content is expected to change.
- **`REVIEWED_STILL_CURRENT`** is semantically `reviewed-no-change` on the ADR track and follows the same exact-digest rule as Q5 half 1. It can make a binding `FRESH`.
- **`SUPERSEDING_ADR_REQUIRED`** is an **open obligation, never a green state.** It says: author a NEW ADR via the existing `/adr` command + the human constitution path; do not touch the old one. The binding remains reported until a new ADR lands and the operator retargets or closes the binding. If it could set `FRESH`, it would be a rubber stamp with extra syllables.
- **The guard must never propose or attempt an ADR edit** in its report text. `contract_guard` would deny the write anyway (that is the backstop), but the report telling a human to edit an accepted ADR is itself the defect — it teaches the wrong action. Phase 29's DOCSUP-06 exclusion list (`accepted ADR`, `docs/reference/**`, `.memory/derived/**`, contracts, goldens) is the downstream consumer of this rule; keep the vocabulary identical so `/docs-update` can filter structurally.

### Q7 — DOCSUP-04 without breaking `inject.py`

**Queue generator:** `tools/memory_regen/docs_staleness.py`, a faithful clone of `contracts_index.py`'s quartet — `rows()` / `render()` / `write()` / `main()` (contracts_index.py:51,83,105,117) with `DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/docs_staleness.py)"` (mirroring contracts_index.py:33), sorted rows, **no `datetime`, no raw float** (contracts_index.py:11-14). Output `.memory/derived/docs-staleness.md`. Pointer-only rows: `binding id | target path | state | severity | required disposition | graph impact ids`. Never a prose excerpt, never a diff body.

**Why it must live under `tools/memory_regen/`, not `tools/docs_guard/`:** `tools/harness_lint/tests/test_derived_freshness.py:32` sets `_ALLOWED_TOOL_MODULES = frozenset({"memory_regen", "docs_sync"})` and asserts that `harness/agents/curator.md` and `harness/commands/refresh-memory.md` reference **no other** `tools.<module>` path. A generator invoked from `/refresh-memory` must therefore be spelled `tools.memory_regen.*`. Note the gate scans those two markdown files' **text**, not the import graph — so `docs_staleness.py` importing `tools.docs_guard` is fine; naming `tools.docs_guard` inside `curator.md` / `refresh-memory.md` is not.

**Gitignore:** no change. `.gitignore:23` (`.memory/derived/*`) already covers it, and `.gitignore:24` un-ignores only `contracts-index.md`. Keep the queue ephemeral like `repo-map.md` (STATE.md `[09-02]`: "repo-map.md stays session-ephemeral"). **Do NOT add it to the `stale-derived` job's path list** (ci.yml:236-237).

**Determinism proof:** because the target is gitignored, `git diff` cannot prove it (contracts_index.py:13-14 / Pitfall 2). Use the established pair: a generate-twice SHA-256 equality test **and** a committed syrupy `.ambr` snapshot over a hermetic fixture (precedent: `tools/memory_regen/tests/__snapshots__/`, `test_repo_map_determinism.py`, `test_contracts_index.py`).

**SessionStart pointer — the exact, safe edit.** `inject.py::assemble` (inject.py:157-188) builds a `sections` list of `(name, text)` pairs (inject.py:168-177), skips empty text (inject.py:181-182), and exempts only `("agreements", "banner", "drift", "task")` from the budget drop (inject.py:184). The pointer must be:

- **Conditional:** return `""` when the queue reports zero `BROKEN`/`STALE_REQUIRED` items. An empty string is skipped at inject.py:181, so the zero-item case is **byte-identical to today's payload** — which is what keeps the existing committed snapshot meaningful.
- **Droppable:** insert with a new name (e.g. `"docs"`) that is **not** added to the inject.py:184 tuple. Recommended position: after `("contracts", …)` and before `("repomap", …)`. Never widen the never-drop tuple — that tuple is the reason `test_budget_holds_with_full_agreements_block` (test_inject_assembler.py:152-157) can still hold.
- **Exactly one line, by construction:** build the string as a header + a single `f"{n} human doc(s) need review — see .memory/derived/docs-staleness.md"`. Do not use `_read_head` (inject.py:56-60) — it returns 20 lines (`_HEAD_LINES = 20`, inject.py:24) and would blow the one-line rule.
- **Read the rendered derived file, do not recompute the guard.** `_contracts_summary` (inject.py:63-72) reads `.memory/derived/contracts-index.md`; do the same. Recomputing the guard inside `assemble()` would put a `git` subprocess and a full doc-corpus walk on the session-start hot path and makes the payload depend on live filesystem state the tests cannot fixture.
- **Parameterize `derived_dir`.** The new reader must take `derived_dir` like `_contracts_summary` does, or `test_payload_matches_snapshot` (test_inject_determinism.py:57-67) — which passes fixture dirs and asserts `str(tmp_path) not in payload` — will start leaking real-repo state into the snapshot.

**Tests that will fail if this is done wrong — cite these in the plan:**

| Test | Path:line | What breaks it |
|---|---|---|
| `test_default_payload_within_budget` | `tools/memory_regen/tests/test_inject_assembler.py:32-33` | Runs `assemble()` against the **real** tree with the 4000 default; a multi-line queue block blows it |
| `test_budget_holds_with_full_agreements_block` | `test_inject_assembler.py:152-157` | Widening the never-drop tuple |
| `test_assemble_is_byte_identical` | `test_inject_determinism.py:29-41` | Any live/nondeterministic read |
| `test_assemble_delete_regenerate_is_byte_identical` | `test_inject_determinism.py:44-54` | Same |
| `test_payload_matches_snapshot` | `test_inject_determinism.py:57-67` | Snapshot must be regenerated; also fails if the payload embeds `tmp_path` |
| `test_inject_module_has_no_wallclock` | `test_inject_determinism.py:77-85` | Importing `datetime`/`time` into `inject.py` — a **static token scan** on the file text, so even an unused import fails it |
| default budget constant | `inject.py:158` (`budget_chars: int = 4000`) | Do not change it |

**`/refresh-memory` + emitter round-trip:** `harness/commands/refresh-memory.md:23` must gain `tools.memory_regen.docs_staleness`. That file is runtime-neutral **source** — editing it requires re-running `tools.harness_emit` to `.opencode/` + `.claude/`, or the `emit-drift` CI job (ci.yml:203) fails. Same for `harness/agents/curator.md` if touched.

### Q8 — Graph impact ids (DOCSUP-05)

**Use the existing API; do not invent one.** `tools/contract_graph/query.py:5` literally names this consumer: *"future documentation-impact reports (DOCSUP)"*. Entry points:

- `tools.contract_graph.compile.compile_graph(cfg=None)` (compile.py:49) → `{"adjacency": {...}, ...}`
- `tools.contract_graph.query.direct/reverse/transitive(graph, node)` (query.py:29,39,55) → `{"ids": [...sorted...], "paths": [[...]]}`, cycle-safe, deterministic

**Report `ids` only** (bounded, sorted); `paths` are for the conductor tree render, not a docs report.

**The mapping gap (MEDIUM confidence — the planner must pin this):** graph nodes are **endpoints** (component / member stable ids), not file paths. A changed source path like `contracts/sample/greeting.schema.json` must first be mapped to a contract id (`greeting` — the schema stem, per `compile.py:39-47` `_tracked_schemas`), then to that contract's `authority` endpoint via `tools.harness_config.loader.effective_relationships()` (loader.py:90-197), before `direct`/`transitive` can be called. Recommendation: implement that mapping as a small pure helper in `tools/docs_guard/`, and — critically — **emit an empty impact list, never a fabricated one, when a changed source path is not a tracked contract** (most human docs' sources will not be). The `OWNER_TBD` precedent (contracts_index.py:43-45, "never fabricate (A3)") is the house rule here.

### Q9 — Anti-double-reporting (DOCSUP-05: contract/golden stay leading)

Two concrete controls:

1. **The docs guard must not re-run or re-print `run_gate()`.** `contracts_index.py:71` legitimately embeds drift status because it is an *index*. The docs guard is a *gate*, and a second gate printing another gate's failures produces the double-red that makes CI output unreadable. Its report should open with one line stating that contract-drift and golden are leading and authoritative.
2. **Suppress, don't stack.** A binding whose `sources` include a contract schema that is **currently drifted** (per `run_gate()["drifted"]`, drift.py:216) should report as `SUPPRESSED (contract-drift leading)` rather than `STALE_REQUIRED`. Without this, every legitimate contract change fails twice — once at `drift`, once at `docs-guard` — and the operator gets no signal about which to fix first. The guard may *read* `run_gate()` for this suppression decision; it must not re-render its findings.

## Architecture Patterns

### System Architecture Diagram

```
docs/doc-dependencies.toml ─┐
                            ├─> registry.load+validate ──(invalid)──> exit 3
contracts/harness/docs/     │        (tomllib + Draft202012Validator
  doc-dependencies.schema  ─┘         + DERIVED_GLOBS + ADR policy)
                                             │ bindings[]
                                             v
  working tree bytes ────────────> digest.compute(sources) / digest.compute(target)
                                             │ live digests
docs/.docs-review-ledger.toml ──────────────>│
   (committed)                               │
git show HEAD:./ledger  ────────────────────>│  coherence check (updated vs reviewed-no-change)
   (drift.py::_git_show_at shape)            │
                                             v
contract_drift.run_gate() ──(drifted?)──> guard.classify()
   (suppression only, never re-printed)      │
                                             ├──> report (stdout/stderr) ──> exit 0 | 1 | 3   [CI: docs-guard job]
                                             │
contract_graph.compile + query ─────────────>│  impact ids (bounded, sorted, never fabricated)
                                             │
                                             v
                     memory_regen.docs_staleness.render/write
                                             │
                                  .memory/derived/docs-staleness.md   (gitignored, DERIVED header)
                                             │
                                             v
                        inject.assemble()  +1 droppable, conditional, one-line section
                                             │
                                             v
                              SessionStart payload (<= 4000 chars)
```

### Recommended module layout

```
tools/docs_guard/                 # NEW uv member — mirrors tools/adoption_scan/'s split
├── __init__.py                   # PEP 562 lazy re-export (loader.py / harness_perms precedent)
├── __main__.py                   # `python -m tools.docs_guard`
├── registry.py                   # load + validate docs/doc-dependencies.toml
├── ledger.py                     # load + previous-committed retrieval + coherence check
├── digest.py                     # sorted path+byte-set SHA-256
├── guard.py                      # classify() -> result dict (run_gate result-dict shape)
├── cli.py                        # report render + exit codes
├── pyproject.toml                # package = false (tools/* member convention)
└── tests/

tools/memory_regen/docs_staleness.py   # NEW — queue renderer only (constrained by test_derived_freshness.py:32)
contracts/harness/docs/doc-dependencies.schema.json   # NEW — constitution plane (one ratification)
docs/doc-dependencies.toml             # NEW — registry data
docs/.docs-review-ledger.toml          # NEW — committed ledger
```

**Extensions to existing files (prefer these over new modules — documented anti-sprawl bias):** `tools/memory_regen/inject.py` (+1 section), `harness/commands/refresh-memory.md` (+1 invocation, then emit round-trip), `.github/workflows/ci.yml` (+1 `docs-guard` job, +1 entry in `gate.needs` at ci.yml:285), `root pyproject.toml` `[tool.uv.workspace] members` already globs `tools/*` (pyproject.toml:33) so no edit is needed there.

### Pattern: the DERIVED generator quartet (clone verbatim)

```python
# Source: tools/memory_regen/contracts_index.py:51-123
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/<module>.py)"

def rows(...) -> list[tuple[...]]: ...        # sorted, content-derived only
def render(rows) -> str: ...                  # header + stable table + trailing "\n"; no datetime/float
def write(path=...) -> Path: ...              # mkdir parents, write_text(encoding="utf-8")
def main(argv=None) -> int: ...               # `python -m ...`
```

### Pattern: git retrieval that degrades honestly

```python
# Source: tools/contract_drift/drift.py:129-147
proc = subprocess.run(["git", "show", f"HEAD:./{rel_path}"], cwd=str(cwd),
                      capture_output=True, check=True, shell=False)
# CalledProcessError / decode error / OSError -> return None (never raise into the gate)
```

### Anti-patterns to avoid

- **A second digest implementation.** One `digest.py`, imported by both the guard and the queue renderer. The repo's standing rule (contracts_index.py:4-8): "a second implementation could silently disagree with the gate."
- **A guard that writes.** Not the ledger, not the ratchet, not the registry. Read-only gates are idempotent; writing gates self-bless.
- **Widening `inject.py`'s never-drop tuple** (inject.py:184) to protect the docs pointer. It is the least important section in the payload.
- **Reusing `refuse_unsafe_destination`** for registry path validation — it refuses `contracts/**`, which are legitimate *sources*.
- **Retyping `DERIVED_GLOBS` or `CONSTITUTION_GLOBS`.** Both have single authoritative homes (destinations.py:105-114; contract_guard.py:44) and Phase 26 explicitly imports rather than retypes (destinations.py:28-32).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| TOML parsing | a parser / `tomli` dep | `tomllib` via a thin loader | loader.py:18,38; stdlib on py>=3.11 |
| Schema validation | ad-hoc `if` chains | `jsonschema.Draft202012Validator` over the parsed dict | approval.py:38 precedent; already pinned |
| Derived-vs-human path classification | a new glob list | `tools.adoption_scan.destinations.DERIVED_GLOBS` | destinations.py:105-114 |
| Constitution-plane detection | a new glob list | `tools.hooks.contract_guard.CONSTITUTION_GLOBS` | contract_guard.py:44; destinations.py:31 already imports it |
| Path-escape refusal | new resolve/compare logic | `tools.adoption_apply.apply.refuse_if_outside_root` (apply.py:94) or the `_confine` idiom (docs_sync/generate.py:189) | 5 independent `_confine` variants already exist; do not add a 6th spelling |
| Duplicate-id diagnostics | ad-hoc set math with unstable output | the sorted-diagnostic block at loader.py:149-160 | deterministic diagnostics are a repo invariant |
| Affected-set traversal | BFS/DFS in the guard | `tools.contract_graph.query.{direct,reverse,transitive}` | query.py:29-81; cycle-safe, sorted, path-bearing, explicitly built for DOCSUP |
| Old-content retrieval | `git log`/`git diff` parsing | the `_git_show_at` shape (drift.py:129-147) | fixed argv, `shell=False`, degrades to None |
| Derived-file determinism proof | `git diff` | generate-twice SHA-256 + committed syrupy snapshot | the target is gitignored — contracts_index.py:13-14 |

**Key insight:** every "new" capability in this phase already has exactly one authoritative implementation in this repo. The phase's real work is composition plus three genuinely new decisions: the digest's canonical serialization (Q3), the disposition-coherence rule (Q5), and the uncovered ratchet (Q4).

## Common Pitfalls

### P1 — The constitution-plane commit that half-lands
**What goes wrong:** the new `contracts/harness/docs/doc-dependencies.schema.json` is committed without rebaselining `contracts/.hashes/manifest.json`, or without regenerating `docs/reference/` and `.memory/derived/contracts-index.md`.
**Why:** three separate gates observe a new schema — `drift` (ci.yml:133), `stale-derived` (ci.yml:227), and the two committed syrupy snapshots.
**Avoid:** one atomic commit, following the 27.1-03 template: schema + `hash --write` + `docs_sync` + `contracts_index` + both snapshots + human token.
**Warning sign:** `contract-drift: DRIFT DETECTED` naming a file you just added.

### P2 — The queue makes every commit fail CI
**What goes wrong:** the queue is committed and added to the `stale-derived` path list.
**Why:** its content is a function of the files being edited, so it goes stale on literally every source commit (ci.yml:236-237 stages and diffs).
**Avoid:** leave it gitignored (`.gitignore:23` already covers it). Zero .gitignore change.

### P3 — The injector snapshot silently absorbs real repo state
**What goes wrong:** the new pointer reads `DERIVED_DIR` (module constant, inject.py:21) instead of the `derived_dir` parameter.
**Why:** `test_payload_matches_snapshot` passes fixture dirs; a module-constant read bypasses them and pins live repo state into a committed snapshot.
**Avoid:** parameterize, mirroring `_contracts_summary(derived_dir=...)` (inject.py:63).
**Warning sign:** the snapshot changes when unrelated docs change.

### P4 — A static token scan fails on an unused import
**What goes wrong:** `import datetime` added to `inject.py` "just in case."
**Why:** `test_inject_determinism.py:70-85` is a **text** scan for `datetime`, `date.today`, `.now()`, `time.time`, `time.monotonic` in the file source.
**Avoid:** no clock in `inject.py`, period. It has a live negative control (`test_negative_control_wallclock_scan_flags_planted_token`, test_inject_determinism.py:87-89), so the scan is known-live.

### P5 — A control tested only by the spelling it already handles
**What goes wrong:** the ledger-only-bump test asserts the guard prints a message, not that the guard *fails when the control is removed*.
**Why:** this exact defect class produced Phase 27's three Criticals and 27.2 SC-3/SC-4 (ROADMAP.md:670-673: "a test that cannot fail when the control regresses is not coverage").
**Avoid:** for every control-shaped fix, author the adversarial input table **before** the implementation, record the RED run and its failure message, and prove the test fails with the control deleted.

### P6 — Non-reproducible uncovered count
**What goes wrong:** the corpus enumeration walks the filesystem and picks up untracked local files; CI's clean checkout counts differently.
**Why:** exactly Phase 26 CR-01 (destinations.py:39-49).
**Avoid:** git-tracked-only enumeration, with the same failure-tolerant degradation destinations.py documents.

### P7 — Digest ambiguity from raw concatenation
**What goes wrong:** copying `_recompute_draft_hash` (approval.py:57-63) verbatim onto a variable-size file set.
**Why:** no separators, no path in the hash input — see Q3.
**Avoid:** interleave path + per-file hex digest.

### P8 — Double-red on every contract change
**What goes wrong:** a contract edit fails `drift` and `docs-guard` simultaneously with unrelated-looking messages.
**Avoid:** the suppression rule in Q9.

## Runtime State Inventory

Not applicable — this is an additive greenfield phase, not a rename/refactor/migration. No existing string is being renamed; no stored data, live service config, OS-registered state, secret name, or build artifact carries a value this phase changes. **Verified by:** the phase's requirements (REQUIREMENTS.md:33-37) are all `NEW+REUSE` additions, and the ROADMAP Phase 28 success criteria (ROADMAP.md:60 and the `### Phase 28` block) contain no rename clause.

## Project Constraints (from CLAUDE.md / AGENTS.md)

| Directive | Applies here as |
|---|---|
| Contract-first: contracts/ outrank code | The registry schema lands on the constitution plane and gets hash-gated; the guard obeys it, never the reverse |
| Two-plane memory; derived never hand-edited | `.memory/derived/docs-staleness.md` carries the `DERIVED — do not hand-edit` header and is generated only by `tools.memory_regen.docs_staleness` |
| Decisions are append-only ADRs | If Phase 28 makes an architecturally load-bearing call (e.g. the fail-closed-on-unverifiable-history rule), it belongs in a new ADR authored `Status: proposed` + a human ratification checkpoint (the 25-05 pattern) — never self-ratified |
| No model identifiers in repo artifacts | The ledger, registry, schema, report text, queue, and commits must all pass the existing real-model-id lint; extend that lint's path set to the new files |
| Machines gate, humans ratify | The guard classifies and refuses; only a human writes a ledger disposition. `/adopt` may propose (Phase 29) but cannot make a binding green |
| GEN-04 core↔example independence | The registry's seeded bindings must not make the core depend on `examples/log-parser/**`. `tools/harness_lint/tests/test_core_no_example_dep.py` scans for `examples/` tokens — an `examples/`-targeting binding in a **core** registry would trip it. Recommend: core registry stays core-only; instance bindings go in an instance-local registry, mirroring `examples/log-parser/project.toml`'s overlay pattern (STATE.md `[08-04]`) |
| Emitter round-trip, byte-identical | Any `harness/commands/*` or `harness/agents/*` edit must be re-emitted to `.opencode/` + `.claude/` or `emit-drift` (ci.yml:203) fails |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `>=8.4,<9` + syrupy 5.2.0 (`pyproject.toml:17-18`) |
| Config file | `pyproject.toml:36-40` (`[tool.pytest.ini_options]`, `testpaths = ["libs/python", "tools"]`) |
| Quick run command | `uv run pytest tools/docs_guard tools/memory_regen -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req | Behavior | Type | Command | Exists? |
|---|---|---|---|---|
| DOCSUP-01 | Registry rejects each of: path escape, duplicate id, empty required selector, derived/reference target, accepted-ADR edit policy | unit (table-driven, one row per rejection) | `uv run pytest tools/docs_guard/tests/test_registry.py -x` | ❌ Wave 0 |
| DOCSUP-02 | Digest is deterministic, order-insensitive to selector spelling, order-**sensitive** to content moves between files; ledger shape rejects timestamp/name/prose/model-id keys | unit | `uv run pytest tools/docs_guard/tests/test_digest.py tools/docs_guard/tests/test_ledger.py -x` | ❌ Wave 0 |
| DOCSUP-03 | source-only change → fail; doc+ledger change → pass; unexplained ledger-only bump → fail; `reviewed-no-change` passes only on exact live digest; uncovered regression → fail | unit + CLI exit-code | `uv run pytest tools/docs_guard/tests/test_guard.py -x` | ❌ Wave 0 |
| DOCSUP-04 | Queue byte-identical on regenerate (sha256 + syrupy); `assemble()` byte-identical; budget ≤ 4000; zero-item case byte-identical to today | unit + snapshot | `uv run pytest tools/memory_regen -x` | ⚠️ partially — inject tests exist (`test_inject_assembler.py`, `test_inject_determinism.py`), queue tests are Wave 0 |
| DOCSUP-05 | Report grouping stable; ADR bindings emit only the two dispositions; drifted-contract bindings suppressed; diff omitted when git cannot retrieve | unit | `uv run pytest tools/docs_guard/tests/test_report.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/docs_guard tools/memory_regen -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** full suite + `contract-drift` + `stale-derived` + `emit-drift` + the new `docs-guard` job green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tools/docs_guard/pyproject.toml` + `tools/docs_guard/tests/__init__.py` — new uv member scaffolding (`package = false`, `tools/*` convention)
- [ ] `tools/docs_guard/tests/conftest.py` — hermetic tmp-repo fixture with a real `git init` (the `test_ci_stale_derived.py` negative-control idiom) so the git-retrieval path is exercised, not mocked
- [ ] `tools/memory_regen/tests/test_docs_staleness.py` + a committed `.ambr` snapshot
- [ ] Regenerated `tools/memory_regen/tests/__snapshots__/test_inject_determinism.ambr`
- [ ] **RED-run discipline (27.2 SC-4):** for each control (path escape, ledger-only bump, ratchet regression, ADR policy), the adversarial input table is authored first and the failing run is recorded in the plan summary

## Security Domain

The threat model here is **integrity of a gate**, not network/auth.

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | No user-facing auth surface |
| V3 Session Management | no | — |
| V4 Access Control | yes | `contract_guard` CONSTITUTION_GLOBS (contract_guard.py:44) remains the only writer-side gate for `docs/adr/**`; the docs guard never bypasses or duplicates it |
| V5 Input Validation | yes | Registry validated with `Draft202012Validator` against a hash-gated schema; path escape refused **before** any filesystem call (apply.py:109-125 shape) |
| V6 Cryptography | yes | `hashlib.sha256` only; never a truncated/aggregate hash presented as reconstructable content (v2.3-scoping-FINAL.md:166 decision row) |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Ledger-only digest bump ("rubber stamp") | Repudiation / Tampering | Disposition-coherence check against the previous committed ledger (Q5) |
| Guard lowers its own ratchet | Elevation of Privilege | Guard is strictly read-only; ratchet is operator-edited |
| Registry selector escapes the repo (`../../etc/...`) | Tampering / Information Disclosure | Structural absolute/`..` pre-check + `refuse_if_outside_root` |
| Symlinked source pointing outside the tree | Information Disclosure | Resolve-then-confine, mirroring `build_manifest`'s symlink defense (hash.py:60-63) |
| Fabricated graph impact ids | Spoofing (false assurance) | Empty list when unmapped; the `OWNER_TBD` never-fabricate rule (contracts_index.py:43-45) |
| Report instructs a human to edit an accepted ADR | Tampering | ADR bindings restricted to the two non-editing dispositions (Q6) |
| Subprocess injection via a registry-controlled path | Tampering | `git` invoked with fixed argv, `shell=False` (drift.py:137-143); no registry value ever reaches a shell |

## Landmines (explicit, as requested)

**Non-determinism sources — any one of these voids the phase's core claim:**
- Any `datetime`/`time` import in `inject.py` (static scan, test_inject_determinism.py:70-85).
- `set` iteration leaking into report or queue ordering — sort everything, always (loader.py:149-197 and query.py:73 both do).
- Filesystem walk order — always `sorted()`; `Path.glob` order is not guaranteed.
- Untracked working-tree files entering the corpus/uncovered count (P6).
- A `float` in the queue (repr drift) — contracts_index.py:12 bans it explicitly.
- Recomputing the guard inside `assemble()` (git subprocess + live walk on the hot path).

**Wall-clock / human identity in a committed artifact:**
- No `updated_at`, no `reviewed_at`, no reviewer name, anywhere in `docs/.docs-review-ledger.toml`. `approval.schema.json`'s `approved_at` is a **task-local** artifact and is not a precedent for a repo-wide baseline.
- No model identifier in any new file, commit message, or report string (CLAUDE.md non-negotiable).

**Hand-editability of the derived queue:**
- The queue must carry the `DERIVED — do not hand-edit` first line (contracts_index.py:33 / docs_sync/generate.py:40 both establish it) and must have exactly one writer.
- It must **not** be committed (P2), so a hand-edit is invisible to git — the mitigation is that `/refresh-memory` regenerates it every session and `inject.py` reads only the regenerated file.

**Double-reporting surfaces:**
- `drift` job (ci.yml:133) and `golden` job (ci.yml:150) already fail on contract/golden regressions. The `docs-guard` job must suppress rather than restate (Q9).
- `contracts_index.py:71` already surfaces drift into the derived plane; the queue must not surface it a third time.
- The SessionStart payload already carries a never-dropped `drift` section (inject.py:170). The docs pointer must not mention contract drift at all.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | `docs/.docs-review-ledger.toml` is the right ledger path (requirement names only the registry path) | Q2 | Low — a path rename is mechanical; the shape is the load-bearing part |
| A2 | Fail-closed on unverifiable git history for `required` bindings | Q5 | Medium — on a shallow CI clone this could red the build; needs user confirmation |
| A3 | Exit codes 0/1/3 (3 = registry invalid) | Q4 | Low — internal convention, no external consumer yet; Phase 29's `/docs-update` will bind to it, so pin it now |
| A4 | Human-authored corpus definition (which paths count for `UNCOVERED`) | Q4 | **High** — this directly sets the ratchet's meaning; must be user-confirmed, not inferred |
| A5 | Graph node id for a contract source is the schema stem, resolved to an authority endpoint via `effective_relationships()` | Q8 | Medium — if wrong, impact ids are empty rather than incorrect (safe-direction), but the feature under-delivers |
| A6 | Queue stays gitignored | Q7 | Low — strongly supported by ci.yml:227-256 and STATE.md `[09-02]` |
| A7 | The registry is exempt from `/contract-check` step 1 because it is TOML, not YAML/JSON | Standard Stack | Medium — means the guard is the registry's only validator; acceptable, but must be stated so no one assumes CI validates it twice |

## Open Questions

1. **Corpus definition for `UNCOVERED` (A4).**
   - Known: `DERIVED_GLOBS` gives the exclusion set authoritatively.
   - Unclear: whether `README.md` files, nested `AGENTS.md`, `.planning/**`, and `examples/log-parser/**` docs are in scope.
   - Recommendation: core registry covers `docs/{tutorials,how-to,explanation}/**` + `docs/glossary.md` + root `AGENTS.md`/`CLAUDE.md` + `.memory/README.md`; exclude `.planning/**` (GSD-owned lane — `is_gsd_owned`, destinations.py:32) and `examples/**` (GEN-04). **Confirm with the user before planning.**

2. **Fail-closed vs. warn when git history is unretrievable (A2).**
   - Known: `_git_show_at` degrades to `None` cleanly.
   - Unclear: CI checkout depth. `actions/checkout@v7.0.0` (ci.yml:230) defaults to depth 1 — `HEAD:./<path>` still works at depth 1, so this is likely a non-issue in practice, but a fresh-repo first commit has no `HEAD`.
   - Recommendation: fail-closed for `required`, warn for `advisory`, with a distinct `unverified-disposition` reason string so the operator can tell it apart from a real staleness failure.

3. **Instance-local registries (GEN-04).**
   - Known: `test_core_no_example_dep.py` scans core files for `examples/` tokens.
   - Unclear: whether Phase 28 needs an instance overlay at all, or whether Phase 29's seeding is core-only.
   - Recommendation: build the loader to accept an explicit path (the `load_project(path=...)` pattern, STATE.md `[08-04]`) so an overlay is possible later, but ship only the core registry in Phase 28.

4. **Does Phase 28 need an ADR?**
   - The disposition-coherence rule and the uncovered ratchet are architecturally load-bearing decisions of the same weight as ADR-0009's graph model. Recommendation: yes, one ADR authored `Status: proposed` with a blocking human-ratification checkpoint, following 25-05's pattern exactly.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Python | everything | ✓ | >=3.11 (`pyproject.toml:5`) | — |
| `uv` | workspace/test runner | ✓ | 0.11.x (CLAUDE.md stack) | — |
| `git` binary | ledger history + tracked-file enumeration | ✓ | repo is a git tree | Degrade to `None`/unfiltered, per drift.py:145 and destinations.py:44-47 |
| `jsonschema` | registry validation | ✓ | 4.26.0 pinned | — |
| `syrupy` | determinism snapshots | ✓ | 5.2.0 pinned | — |
| .NET SDK | not needed by this phase | ✗ (egress-deferred, STATE.md `[01-06]`) | — | Irrelevant — Phase 28 is Python-only |

**Missing dependencies with no fallback:** none.

## Sources

### Primary (HIGH — read from source in this session)
- `tools/memory_regen/inject.py:20-24,56-72,157-188` — budget, section list, never-drop tuple, empty-skip
- `tools/memory_regen/contracts_index.py:11-14,33,43-45,51-123` — DERIVED generator quartet, no-datetime/float rule, never-fabricate rule
- `tools/memory_regen/tests/test_inject_determinism.py:29-121`, `test_inject_assembler.py:32-33,152-174` — determinism + budget gates
- `tools/contract_hash/hash.py:26,36-66,69-82` — JCS+SHA-256, manifest baseline, symlink defense
- `tools/contract_drift/drift.py:34-44,129-147,177-216,370-390` — baseline diff, git retrieval, result dict, exit codes
- `tools/harness_config/loader.py:18,32-39,77-197` — thin loader, DATA-slot passthrough, deterministic duplicate diagnostics
- `tools/contract_graph/query.py:1-81`, `compile.py:1-49` — affected-set API (query.py:5 names DOCSUP)
- `tools/adoption_apply/approval.py:12-17,38,47,57-63` — committed record bound to exact digests
- `tools/adoption_apply/apply.py:94,109-160` — confinement + refusal choke point
- `tools/adoption_scan/destinations.py:28-49,101-124` — DERIVED_GLOBS, CONSTITUTION_GLOBS import, git-tracked reproducibility rule
- `tools/hooks/contract_guard.py:1-70` — constitution-plane deny + `GOLDEN_APPROVE_HUMAN`
- `tools/docs_sync/generate.py:1-48,189` — DERIVED reference generator + `_confine`
- `tools/harness_lint/tests/test_derived_freshness.py:1-60` — `_ALLOWED_TOOL_MODULES` constraint
- `.github/workflows/ci.yml:133,150,203,227-256,285` — drift/golden/emit-drift/stale-derived jobs + fan-in
- `.gitignore:17-24`, `.github/CODEOWNERS:26-32`, `pyproject.toml:5-40`, `harness/project.toml`
- `.planning/REQUIREMENTS.md:33-37`, `.planning/ROADMAP.md:60-61` + `### Phase 28`/`### Phase 29`, `.planning/STATE.md` Accumulated Context, `.planning/research/v2.3-scoping-FINAL.md:33-37,155-180`
- `.planning/phases/25-*/25-05-SUMMARY.md` — proposed-then-human-ratified ADR pattern

### Secondary (MEDIUM)
- Graph node-id ↔ contract-path mapping (Q8/A5) — inferred from `compile.py:39-47` + `loader.py:90-197`; not exercised by an existing DOCSUP-shaped test

### Tertiary (LOW)
- None. No web sources were used; this phase's domain is entirely in-repo.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies; every module verified present at a cited line
- Architecture: HIGH — every recommended shape is a clone of a shipped, tested shape in this repo
- Pitfalls: HIGH — each pitfall names the specific existing test or CI job that detects it
- Graph impact mapping (Q8): MEDIUM — the API is certain, the path→node mapping is inferred
- Corpus definition (Q4/A4): LOW until user-confirmed — it sets the ratchet's meaning

**Research date:** 2026-07-21
**Valid until:** indefinite for the external-ecosystem parts (there are none); re-verify the cited line numbers if Phases 26.x/27.x land further changes to `tools/adoption_*`.
