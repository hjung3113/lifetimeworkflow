# Phase 28: Human-Docs Registry, Guard, Derived Queue - Context

**Gathered:** 2026-07-21
**Status:** Ready for planning
**Mode:** Autonomous smart-discuss — grey areas decided at Claude's discretion per explicit user instruction ("질문 하지말고 니 권장대로 처리해"). Every decision below adopts `28-RESEARCH.md`'s stated recommendation; none is a novel invention at planning time.

<domain>
## Phase Boundary

Detect and surface human-doc review obligations **precisely**, without claiming semantic accuracy and without competing with the derived generators.

Requirements: DOCSUP-01 .. DOCSUP-05 (`.planning/REQUIREMENTS.md:33-37`).
Success criteria: `.planning/ROADMAP.md` `### Phase 28`, four observable criteria.

**IN scope:** the registry (`docs/doc-dependencies.toml`) + its schema, the committed review ledger, the deterministic digest, the five-state guard with its severity/exit mapping and uncovered ratchet, the stable report, and the gitignored derived staleness queue + conditional one-line SessionStart pointer.

**OUT of scope:** the `/docs-update` drive loop and `docs-upkeep` skill (DOCSUP-06, Phase 29); adoption seeding and binding proposals from `/adopt` (DOCSUP-07, Phase 29); any instance-local (`examples/**`) registry overlay.

</domain>

<decisions>
## Implementation Decisions

**All of `28-RESEARCH.md`'s assumptions A1-A7 are ADOPTED as written.** The four open questions are resolved below, each taking the research's own recommendation.

| # | Grey area | Decision | Rationale |
|---|-----------|----------|-----------|
| D-01 | Registry plane — constitution or plain config? | **Split, per research:** data at `docs/doc-dependencies.toml` (plain reviewed config, `harness/project.toml` precedent); shape at `contracts/harness/docs/doc-dependencies.schema.json` (constitution plane, hash-gated, ONE human ratification). | Forced, not preferential: `tools/hooks/contract_guard.py:44` denies agent writes under `contracts/**`, and DOCSUP-07 requires `/adopt` to *propose* registry entries. A registry under `contracts/` makes the downstream requirement unimplementable without handing agents `GOLDEN_APPROVE_HUMAN`. Mirrors the Phase 26/27 `manifest.schema.json` split. |
| D-02 | Ledger path + shape | `docs/.docs-review-ledger.toml` (A1). Stores ONLY: binding id, the exact reviewed digest, and the disposition (`updated` \| `reviewed-no-change`), plus `[coverage] uncovered_max`. **No timestamps, no human names, no prose copy, no model identifiers.** | DOCSUP-02 verbatim. Path rename is mechanical; the shape is the load-bearing part. |
| D-03 | Digest algorithm | **Interleave path + per-file hex digest** over the sorted source+target set — deliberately NOT the raw-byte concatenation at `approval.py:57-63`. No §4.3-4.6 normalization before hashing. | `approval.py`'s concatenation is safe only for its fixed 3-file tuple; a registry selector expands to a *variable* set, where raw concatenation makes "move a byte between files" and "add an empty file" invisible. Flagged in the research precisely so a reviewer does not "fix" it back toward the precedent — the plan must carry that note into the code as a comment. |
| D-04 | Anti-rubber-stamp control (DOCSUP-03) | **Disposition/digest coherence against the PREVIOUS COMMITTED ledger.** `reviewed-no-change` is content-bound — valid only against the exact live digest, no history needed. `updated` additionally requires a target-digest delta versus the previous committed ledger, retrieved via the `_git_show_at` shape at `tools/contract_drift/drift.py:129-147`. | Both halves are required. Digests alone cannot detect the paste-the-live-digest attack: after the paste they are consistent by construction. This is the named mechanism DOCSUP-03 demands. |
| D-05 | Five states + severity/exit mapping | `BROKEN` / `STALE_REQUIRED` / `STALE_ADVISORY` / `FRESH` / `UNCOVERED`, **first-match-wins** with `BROKEN` ordered before any staleness check. Exit codes **0 / 1 / 3**, where 3 = registry-invalid (A3). | A missing file must not be reported as merely stale. Exit 3 is a different operator action than exit 1, matching the `approve.py` / `StranglerRefused` exit-3 precedent. Phase 29's `/docs-update` binds to these codes, so they are pinned now. |
| D-06 | Uncovered non-regression ratchet | Stored as `[coverage] uncovered_max` in the ledger. **The guard NEVER writes it** — raising the ratchet is a human edit. | A gate that can lower its own threshold is self-blessing; that is the "machines gate, humans ratify" non-negotiable. |
| D-07 | Human-authored corpus for `UNCOVERED` (research Q1 / A4) | **Adopt the recommendation:** `docs/{tutorials,how-to,explanation}/**` + `docs/glossary.md` + root `AGENTS.md` + root `CLAUDE.md` + `.memory/README.md`. **Exclude** `.planning/**` (GSD-owned lane, `destinations.py:32` `is_gsd_owned`), `examples/**` (GEN-04), and everything in `DERIVED_GLOBS` (authoritative exclusion set — `docs/reference/**`, `.memory/derived/**`). | This sets the ratchet's meaning, so it is stated explicitly rather than inferred inside the guard. Derived and GSD-owned trees have their own generators/owners; counting them would either double-report or make the ratchet meaningless. |
| D-08 | Unverifiable git history (research Q2 / A2) | **Fail-closed for `required` bindings, warn for `advisory`**, with a distinct `unverified-disposition` reason string so an operator can tell it apart from real staleness. | Matches the repo's fail-closed posture. Research confirmed `HEAD:./<path>` works at `actions/checkout` depth 1 (`ci.yml:230`), so the practical exposure is a fresh repo with no `HEAD` — acceptable to fail there. The distinct reason string is mandatory: an indistinguishable failure teaches the wrong fix. |
| D-09 | Accepted-ADR special case | Registry validation **forces** `dispositions = ["REVIEWED_STILL_CURRENT", "SUPERSEDING_ADR_REQUIRED"]` for any `docs/adr/**` target. `SUPERSEDING_ADR_REQUIRED` is an open obligation that can never make a binding green. The report must **never** suggest an in-place ADR edit. | Append-only / supersede-don't-edit is a standing rule; `contract_guard` would deny the write anyway, but a report that teaches the wrong action is itself the defect. |
| D-10 | Derived queue placement (DOCSUP-04) | Generator lives at `tools/memory_regen/docs_staleness.py`, **not** in the new guard package. Queue file stays **gitignored** (`.gitignore:23` already covers it — zero change) and does **NOT** join the `stale-derived` CI job. | `tools/harness_lint/tests/test_derived_freshness.py:32` pins `_ALLOWED_TOOL_MODULES = {memory_regen, docs_sync}` for the curator / `/refresh-memory` surface. Committing the queue would red every ordinary source commit. |
| D-11 | SessionStart pointer (DOCSUP-04) | **One line, conditional** — empty string when the queue is empty, so the payload stays byte-identical to today via `inject.py:181`. Must be **droppable**: never widen the never-drop tuple at `inject.py:184`. Reads the *rendered derived file*, does not recompute the guard. Takes `derived_dir` as a **parameter** — otherwise it leaks real repo state into the committed snapshot. | Preserves the byte-identity determinism test and the ~4000-char budget. The research tabled the six exact tests this can break with path:line; the plan must run them. |
| D-12 | Graph impact ids (DOCSUP-05, A5) | Use `compile_graph` + `direct`/`reverse`/`transitive` from the Phase 25 query API (`query.py:5` names DOCSUP as its intended consumer). Report **ids only**. Map a changed contract source path → schema stem (`compile.py:39-47` `_tracked_schemas`) → authority endpoint via `loader.effective_relationships()` (`loader.py:90-197`), as a small pure helper in `tools/docs_guard/`. **Emit an empty impact list, never a fabricated one**, when a source is not a tracked contract. | Graph nodes are endpoints, not file paths, so the mapping is real work. `OWNER_TBD` (`contracts_index.py:43-45`, "never fabricate") is the house rule for the unmapped case; under-delivering is the safe direction. |
| D-13 | Anti-double-report with contract-drift / golden | The guard reads `run_gate()` for **suppression only**: a binding whose source is a currently-drifted contract reports `SUPPRESSED (contract-drift leading)` rather than `STALE_REQUIRED`. | DOCSUP-05 requires contract/golden failures to stay leading and authoritative. Without this, every contract change fails twice with two different remedies. |
| D-14 | Instance-local registries (research Q3) | Build the loader to accept an **explicit path** (`load_project(path=...)` pattern, STATE.md `[08-04]`) so an overlay is possible later, but **ship only the core registry** in Phase 28. | Keeps GEN-04 green (`test_core_no_example_dep.py`) while leaving the seam open. |
| D-15 | Does Phase 28 need an ADR? (research Q4) | **Yes — one ADR**, authored `Status: proposed`, with a blocking human-ratification checkpoint, following the 25-05 pattern exactly. | The disposition-coherence rule (D-04) and the uncovered ratchet (D-06) are architecturally load-bearing, same weight as ADR-0009's graph model. |
| D-16 | Registry validation is the registry's ONLY validator (A7) | Accepted and must be **stated in the plan and the ADR**: the registry is TOML, so `/contract-check` step 1 (`check-jsonschema` over YAML/JSON) does not cover it. The guard validates it. | So nobody assumes CI validates it twice. |
| D-17 | Module set (anti-sprawl) | **One** new uv member `tools/docs_guard/` + **one** new file `tools/memory_regen/docs_staleness.py`. Everything else is an extension: `inject.py` (+1 section), `refresh-memory.md` (+1 invocation, then re-emit), `ci.yml` (+1 job, +1 `gate.needs`). Root `pyproject.toml` needs no edit (`members` already globs `tools/*`). | Documented anti-sprawl bias — prefer extending. |
| D-18 | Constitution-plane commit budget | **One atomic commit** for the new schema: schema + `hash --write` + `docs_sync` + `contracts_index` + both syrupy snapshots + human ratification token, following the 27.1-03 template. | Half-landing it reds `drift` or `stale-derived`. This is a known-shape task, not a discovery. |

</decisions>

<code_context>
## Existing Code Insights

Authoritative detail with file:line citations is in `28-RESEARCH.md` (575 lines, HIGH confidence on repo machinery — every citation read from source). Load-bearing pointers:

- `tools/hooks/contract_guard.py:44` — agent writes under `contracts/**` are denied. Forces D-01.
- `tools/contract_drift/drift.py:129-147` — the `_git_show_at` shape D-04 reuses.
- `tools/adoption_apply/approval.py:57-63` — the raw-concatenation digest D-03 deliberately diverges from.
- `tools/harness_lint/tests/test_derived_freshness.py:32` — `_ALLOWED_TOOL_MODULES` pins D-10.
- `tools/memory_regen/inject.py:181,184` — the conditional-section and never-drop-tuple seams D-11 must respect.
- `tools/memory_regen/contracts_index.py:43-45` — the never-fabricate house rule behind D-12.
- `tools/harness_config/loader.py:90-197`, `compile.py:39-47`, `query.py:5` — the Phase 25 graph API D-12 consumes.
- `.gitignore:23` — already covers the derived queue; zero change (D-10).
- `ci.yml:227-256` — the `stale-derived` job the queue must NOT join.

</code_context>

<specifics>
## Specific Ideas

- **The phase's own anti-pattern fence** (inherited from 26.1/27/27.1 and re-proven in 27.2): every control-shaped change gets its adversarial-input table authored FIRST, and the new test must be shown failing against pre-fix code for the stated reason. Applies here to registry validation (path escape, duplicate id, empty required selector, derived/reference target, ADR-edit policy), to the disposition-coherence check (D-04 — the paste-the-live-digest attack is the adversarial row), and to the ratchet (D-06 — a guard-authored bump must be impossible, not merely unwritten).
- **The six injector tests D-11 can break are named in the research with path:line** — the plan must run them explicitly, not rely on the full suite.
- Report grouping per DOCSUP-05: changed path/hash, graph impact ids, target doc, severity, required disposition.

</specifics>

<deferred>
## Deferred Ideas

- `/docs-update` command + `docs-upkeep` skill → Phase 29 (DOCSUP-06).
- `/adopt` proposing registry/ledger entries → Phase 29 (DOCSUP-07).
- Instance-local (`examples/**`) registry overlay → seam left open by D-14, not built.
- `tools/hooks/secret_scan.py:44-47` reading the contract instead of hardcoding its pattern list → still carried forward from 26.2 / 27.1 / 27.2.

</deferred>
