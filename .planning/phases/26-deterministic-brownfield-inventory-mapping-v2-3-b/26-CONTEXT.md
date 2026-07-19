# Phase 26: Deterministic Brownfield Inventory + Mapping *(v2.3 B)* - Context

**Gathered:** 2026-07-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce a complete, evidence-grounded **adoption plan** for an existing (brownfield) repository **without mutating the target and without invoking any agent workflow**. Pure deterministic tooling — agent-free, fully CI-testable. Owns ADOPT-01, ADOPT-02, ADOPT-03. Delivers exactly three outputs:

1. **ADOPT-01 — Bounded deterministic inventory.** A read-only, local-root, confined, ignore-respecting, size-capped inventory reporting languages, package/component boundaries, existing schema/spec/doc/ADR/AGENTS/CODEOWNERS/CI surfaces, and candidate process boundaries via evidence pointers + hashes. Excludes secrets, binaries, vendored trees, generated output, and source dumps.
2. **ADOPT-02 — Evidence-separated mapping plan.** Every proposed member, component, relationship, contract candidate, test command, documentation destination, and AGENTS boundary classified `observed` / `inferred` / `unknown` with source evidence. Unresolved ownership stays a **question**, never invented authority. Uses the Phase-24 TOPO record vocabulary.
3. **ADOPT-03 — Complete destination/disposition manifest.** Exactly one of `create` / `marker-merge` / `preserve` / `conflict` / `derived-regenerate` / `human-ratification-required` assigned to every harness destination: contracts, goldens, ADRs, all four Diátaxis quadrants, both memory planes, task/config/workspace topology, root + nested AGENTS, CODEOWNERS guidance, runtime-neutral sources, emitted runtimes.

**Depends on Phase 24 only** (the ratified `relationship.schema.json` record vocabulary). It does **NOT** need Phase 25's compiler, queries, or conductor — deliberately, so Theme B proceeds in parallel with Theme A.

**Hard invariants:** target tree unchanged; repeated inventory/plan output byte-identical regardless of file enumeration order; no agent invocation; no arbitrary command execution.

**NOT this phase:** the `/adopt` command, the `brownfield-adoption` skill, task-local batches under `.workflow/tasks/`, apply/marker-merge execution, human ratification checkpoint, the three application fixtures — all Phase 27 (ADOPT-04..07).

</domain>

<decisions>
## Implementation Decisions

Interactive discussion (`--chain`). Six decisions locked; several deliberately delegated to researcher/planner (recorded below so they are not re-asked).

### Output contract posture
- **D-01: Contract-first — all three outputs are schema-governed.** Author new JSON-Schema contracts under `contracts/harness/adoption/` for the inventory, the mapping plan, and the disposition manifest. Rationale: mirrors the shipped `contracts/harness/task-control/` precedent exactly (adoption is "an ordinary task" per v2.3 FINAL §146, and task-control already contract-governs state/evidence/handoff/attestation); all three outputs cross the phase boundary into Phase 27 (ADOPT-04 binds inventory·plan·manifest hashes into CAS), so each earns drift-gate protection. The constitution-plane authoring + CODEOWNERS human ratification rides the **established** path — an agent Write into `contracts/` is correctly denied; the schemas land human-ratified (same as ADR-0004/0005/0009 precedent). Phase logic itself stays fully CI-testable.

### Evidence classification calibration (ADOPT-02)
- **D-02: Conservative-unknown bias.** `observed` only on **direct** evidence (file exists, extension present, declared in a manifest file). `inferred` only on **strong structural** signals. **Everything else ambiguous → `unknown` → question.** Rationale: safest posture, fewest silent assumptions, matches the phase's refusal to invent authority. Accepted cost: on large repos the question list is noisy — mitigated by D-05's evidence-bearing question records. Ownership/authority claims (contract authority, component ownership, CODEOWNERS entries) are `unknown` by construction under this rule, satisfying ADOPT-02's "unresolved ownership remains a question rather than invented authority".

### Disposition decision table (ADOPT-03)
- **D-03: Collision rule — content-equal → `preserve`, content-different → `conflict`.** Target file exists at a non-constitution destination and its hash matches the proposed content → `preserve` (idempotent no-op). Hash differs → `conflict` (human decides). `marker-merge` is reserved for **marker-capable** files only (e.g. `AGENTS.md`, harness-managed marker blocks). No automatic overwrite, ever.
- **D-04: Remaining rows are requirement-locked (do not re-derive):**
  - Constitution destination (`contracts/`, `docs/adr/`, `golden/`) → **always `human-ratification-required`**, regardless of whether the target file exists — any write there is refused before mutation (ADOPT-05/06).
  - Derived-plane destination (`.memory/derived/**`, `docs/reference/**`) → `derived-regenerate`.
  - Non-constitution destination with no existing target file → `create`.
  - Together with D-03 this table is **total**: every harness destination resolves to exactly one disposition (roadmap success criterion 3).

### Phase-26 proof strategy
- **D-06: One synthetic mini-repo fixture, with a separate assert per detection.** A single small synthetic target tree that embeds every case — secret, binary, vendored, generated, over-size-cap, collision, and ambiguous-evidence — covered by individual assertions so a failure still names its cause. Determinism proven by running the tool twice over the same fixture and diffing byte-for-byte (plus a shuffled-enumeration-order variant). Rationale: v2.3 FINAL §152 forbids a broad fixture/framework stack; Phase 27 owns the three *application* fixtures, so Phase 26 must not proliferate fixtures. Bonus: this tree seeds Phase 27's fixtures.

### Deliberately delegated (do NOT re-ask the user)
- **D-05: Question-record shape → researcher/planner.** The `question` entries in the plan schema MUST carry at minimum a **stable id**, the **target** (harness destination / topic), and an **evidence pointer** (path + hash). Whether they additionally carry a proposed candidate, and how they are grouped/ordered, is designed by the researcher after inspecting how Phase 27's human-ratification step will consume them. Ordering must be deterministic whatever shape is chosen.
- **D-07: Exclusion + size-cap mechanism → researcher.** Whether the secret/binary/vendor/generated exclusion, confinement, and size-cap ride the existing `tools/evidence` machinery (v2.2) or a purpose-built adoption scanner is the researcher's call — **reuse-first; if not reused, the plan must state why**. Secret-detection posture should follow D-02's safest-bias (exclude on suspicion) unless research shows a concretely better rule.

### Research-round resolutions (locked after 26-RESEARCH.md)

These close the open questions and the A1 assumption raised by the researcher. They are locked the
same as D-01..D-07 — do not re-litigate.

- **D-08: "source dump" (ADOPT-01) means BOTH readings.** (a) whole-repo single-file concatenations
  (repomix / gitingest / LLM-input dumps), detected by their banner/structure marker within the
  first 2 KiB; and (b) over-cap text blobs plus paths carrying a `dump` / `snapshot` / `backup`
  segment. Rationale: the size cap already catches the large concatenations, so the marginal cost of
  (a) is one cheap marker check for under-cap concat artifacts — and an inventory that ingests a
  repo-concat file double-counts every file in it, the exact pollution ADOPT-01 exists to prevent.
  Exclusion reason recorded as `source-dump`. (Resolves assumption A1, which was undefined in
  REQUIREMENTS.md and v2.3 FINAL.)
- **D-09: `git ls-files` is allowed — fixed argv, `shell=False`, failure-tolerant — with a complete
  builtin fallback.** The phase invariant "no arbitrary command execution" forbids executing
  *discovered* scripts (v2.3 FINAL §147), not a fixed, non-shell `git` argv; the repo already does
  this in `contract_drift.drift._git_show` and `evidence.capture._committed_approval`. The design
  MUST NOT depend on git: when git is absent or fails, the builtin denylist walk produces a complete
  result, and the enumeration mode is recorded in the artifact so a run is self-describing. The
  plan's threat model must call this distinction out explicitly.
- **D-10: exclusions are recorded, not omitted.** Every excluded file appears in a separate
  `excluded[]` array as `{path, size, reason}` — **no content hash, no content excerpt**. Rationale:
  roadmap success criterion 4 requires secret/size-cap/vendor/generated detection to *pass*, which is
  only testable if exclusions are observable; and withholding hash+content keeps secret material out
  of the artifact entirely.
- **D-11: three self-contained schemas; `--out` is required.** Each of the three schemas under
  `contracts/harness/adoption/` duplicates its small shared `$defs` (evidence pointer, classification
  enum, disposition enum) rather than introducing cross-file `$ref` — all 8 existing contracts in
  this repo are self-contained, and neither `check-jsonschema` nor `tools.contract_hash` has ever been
  exercised against cross-file `$ref`. The tool has **no default output location**: `--out` is
  mandatory and the tool refuses when `--out` resolves inside `--target`. This keeps Phase 27's
  task-plane integration a pure argument change with zero behavior change, and honors §146 (Phase 26
  creates no task plane).

### Claude's Discretion
- Module location and naming (`tools/brownfield_inventory/` vs extending an existing tool package), internal data structures, exact canonical sort keys, schema property spellings, CLI/module entry point (`python -m tools.<x>`), and test file layout — planner decides, provided outputs are deterministic, repo-confined, and read-only with respect to the target.
- Inventory detection breadth (which languages / package managers / "candidate process boundary" heuristics, and whether to reuse the repo-map tree-sitter machinery) — researcher/planner scope; the user explicitly declined to constrain it.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Ratified design + requirements (authoritative)
- `.planning/research/v2.3-scoping-FINAL.md` — §"Theme B — Brownfield adoption" (ADOPT-01..07 statements) and §"Phase 26 — Deterministic Brownfield Inventory and Mapping" (lines ~77–87: Goal, Owns 1:1, dependency edge `24 -> 26`, sequencing rationale, Exit). Also §146 (no `.workflow/adoption/` plane — adoption is an ordinary task), §147 (no autonomous contract extraction / no executing discovered scripts), §152 (no broad fixture stack).
- `.planning/REQUIREMENTS.md` — ADOPT-01, ADOPT-02, ADOPT-03 (owned 1:1 by this phase). ADOPT-04..07 listed there are Phase 27 — read only to avoid building them here.
- `.planning/ROADMAP.md` — "### Phase 26" (Goal, Mode: standard, Depends on Phase 24, 4 observable success criteria).

### Phase 24 output this phase consumes (record vocabulary)
- `contracts/harness/topology/relationship.schema.json` — the ratified relationship record; the mapping plan proposes candidates in THIS vocabulary.
- `.planning/phases/24-contract-relationship-vocabulary-compatibility-v2-3-a/24-CONTEXT.md` — locked vocabulary decisions D-01..D-05 (namespaced lowered ids, endpoints are opaque strings).
- `tools/harness_config/loader.py` — `effective_relationships()` / `contract_graph_relationships()`; the vocabulary's single lowering+union path. Phase 26 emits candidates compatible with it; it does NOT need Phase 25's compiler.

### Contract-first authoring precedent for D-01
- `contracts/harness/task-control/` — `state.schema.json`, `evidence.schema.json`, `handoff.schema.json`, `attestation.schema.json`, `task.schema.json`, `gate-registry.json`, `transitions.json`. The structural precedent the new `contracts/harness/adoption/` schemas mirror.
- `tools/contract_hash/hash.py` + `tools/contract_drift/drift.py` — RFC-8785 canonicalization + schema-hash drift gate that will govern the new schemas. Reuse; do not fork.
- `harness/skills/data-contracts/SKILL.md` and `harness/skills/contract-check/SKILL.md` — the contract-first authoring + validation flow the new schemas must pass.
- `harness/skills/gate-model/SKILL.md` — why an agent Write into `contracts/` is refused and what the human-ratified path is (D-01 depends on this).

### Reuse candidates for the inventory (D-07 decides)
- `tools/evidence/capture.py` — v2.2 evidence capture: confinement, size-cap, hashing, evidence pointers. **First reuse candidate** for ADOPT-01's evidence pointers.
- `tools/memory_regen/repo_map.py` + `tools/memory_regen/pointer_index.py` — existing repo-scanning / pointer machinery (language + symbol awareness); consult before writing a new scanner.
- `tools/harness_config/` + `tools/workspace_config/` — how the harness already models members/components/topology; the manifest's destination list must line up with these.
- `tools/harness_emit/generate.py` + `merge.py` — marker-block merge semantics; authoritative for what "marker-capable" means in D-03.

### Gate + boundary constraints
- `tools/harness_lint/tests/test_core_no_example_dep.py` — GEN-04 one-way core→example guard; any fixture referencing an instance path uses non-contiguous `Path` segments (Phase 24/25 precedent).
- `harness/skills/polyglot-boundary/SKILL.md` — §4.3–4.6 canonicalization invariants; relevant because Phase 27's fixtures include CRLF/BOM input and Phase 26's inventory must not silently normalize what it reports.
- `AGENTS.md` (root) — nearest-wins agent rules; the manifest proposes root/nested AGENTS destinations.

### Phase 25 (parallel, NOT a dependency)
- `.planning/phases/25-graph-compiler-queries-conductor-proof-v2-3-a/25-CONTEXT.md` — read only to keep vocabulary aligned. Phase 26 must not take a build dependency on the Phase-25 compiler/queries.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/evidence/capture.py` — confinement + size-cap + hash + evidence-pointer capture already solved for the task plane (v2.2). Prime reuse target for ADOPT-01 (D-07).
- `tools/contract_hash/hash.py` — RFC-8785 canonical hashing; use for both the new adoption schemas' drift hashes and the inventory's content hashes rather than a second hasher.
- `tools/contract_drift/drift.py` — the drift gate the three new schemas automatically fall under once authored.
- `tools/memory_regen/repo_map.py` / `pointer_index.py` — existing repo-walk + pointer indexing; consult before writing a fresh walker.
- `tools/harness_emit/merge.py` — marker-block merge semantics define which destinations are `marker-merge`-capable (D-03).
- `contracts/harness/task-control/*.schema.json` — the shape/style template for the new `contracts/harness/adoption/` schemas.

### Established Patterns
- **Contract-first, reuse-don't-fork** — new outputs get schemas; hashing/drift/confinement ride existing tools (carried from Phases 24–25).
- **Descriptive stable diagnostic slugs** — `harness_lint` convention (GEN-04, POLY-01, GEN-03); any detection diagnostics emitted here follow that style, not numbered codes.
- **Machines gate, humans ratify** — constitution-plane writes are refused for agents; D-01's schemas land via the human-ratified path.
- **Deterministic, repo-confined, stably-sorted output** — every tool in `tools/` already holds this line; byte-identical repeat output is a roadmap success criterion here.
- **GEN-04 one-way core→example** — the new tool is core; it must not depend on `examples/log-parser/`.

### Integration Points
- **Phase 27 (ADOPT-04..07)** consumes all three outputs: batches under `.workflow/tasks/<task-id>/artifacts/adoption/<batch-id>/` bind inventory·plan·manifest hashes into the existing CAS/evidence/HANDOFF lifecycle; the disposition manifest drives safe-apply and the constitution refusal.
- **Phase 29 (DOCSUP-07)** — `/adopt` may later propose docs-registry/ledger entries seeded from this phase's documentation destinations, but must leave inferred ownership unresolved.
- **Phase 24 vocabulary** — proposed relationship candidates are expressed as `relationship.schema.json` records so they drop straight into `[contract_graph]` after human ratification.

</code_context>

<specifics>
## Specific Ideas

- Three schemas under `contracts/harness/adoption/` mirroring the `contracts/harness/task-control/` layout (D-01).
- Disposition table is **total** — the manifest enumerates every harness destination and each resolves through exactly one row: constitution → `human-ratification-required`; derived → `derived-regenerate`; non-constitution absent → `create`; non-constitution present & hash-equal → `preserve`; present & hash-different → `conflict`; marker-capable → `marker-merge` (D-03/D-04).
- Question records carry at minimum `{stable id, target, evidence pointer(path+hash)}` (D-05).
- One synthetic mini-repo fixture with secret / binary / vendored / generated / over-cap / collision / ambiguous cases embedded; determinism proven by double-run diff plus a shuffled-enumeration-order run (D-06).

</specifics>

<deferred>
## Deferred Ideas

- **`/adopt` command + `brownfield-adoption` skill, task-local batches, apply/marker-merge execution, human-ratification checkpoint, the three application fixtures (polyglot single-repo / two-repo client-server / partial-adoption-collision, one with CRLF+BOM)** — Phase 27 (ADOPT-04..07). Explicitly out of Phase 26.
- **Docs dependency registry / ledger seeding from adoption** — Phase 29 (DOCSUP-07).
- **Graph-impact reports over the adoption plan** — needs Phase 25 queries; not a Phase 26 dependency.
- **Autonomous contract extraction, golden inference from behavior, source refactoring, repo moves, CI/package-manager rewriting, executing discovered scripts, remote workspace members** — permanently out of scope (v2.3 FINAL §147).
- **Inventory detection breadth beyond what the researcher selects** (exotic languages/package managers) — deliberately unconstrained; extend later if a real target needs it.

None dropped — each is owned by a later phase or explicitly out-of-scope.

</deferred>

---

*Phase: 26-Deterministic Brownfield Inventory + Mapping (v2.3 B)*
*Context gathered: 2026-07-19*
