---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
verified: 2026-07-19T00:00:00Z
status: gaps_found
score: 4/6 must-haves verified
overrides_applied: 0
gaps:
  - truth: "ADOPT-01: inventory reports existing schema/spec/doc/ADR/AGENTS/CODEOWNERS/CI surfaces"
    status: failed
    reason: >
      REQUIREMENTS.md ADOPT-01 and 26-CONTEXT.md both name six surface categories the inventory
      must report: schema, spec, doc, ADR, AGENTS, CODEOWNERS, CI. The shipped
      `inventory.schema.json` has properties for only `documentation_surfaces` (ADR/README/AGENTS)
      and `ci_surfaces` — it has no property, and `detect.py` has no function, for "schema"
      surfaces (e.g. `contracts/**/*.schema.json`) or CODEOWNERS. Confirmed empirically: scanning
      this repo itself (which has 11 real `*.schema.json` files and a real
      `.github/CODEOWNERS`) produces zero schema-surface records and zero CODEOWNERS records in
      inventory.json, because no such record kind is ever emitted. `plan.py` even defines a
      `codeowners-ownership` question kind and text template, but `classify()`/`generate_questions()`
      never populate it because there is no inventory field to walk — it is permanently dead code
      for CODEOWNERS on every real scan.
    artifacts:
      - path: "tools/adoption_scan/detect.py"
        issue: "No detect_codeowners_surfaces() or detect_schema_surfaces() function exists"
      - path: "contracts/harness/adoption/inventory.schema.json"
        issue: "properties are only [target_ref, enumeration_mode, max_file_bytes, included, excluded, languages, manifests, documentation_surfaces, ci_surfaces, test_surfaces, candidate_process_boundaries] — no schema-surface or codeowners-surface slot"
      - path: "tools/adoption_scan/plan.py:54,66,89"
        issue: "codeowners-ownership question kind is wired into the templates/grouping/blocking tables but is structurally unreachable — classify() never walks a codeowners inventory field"
    missing:
      - "detect_schema_surfaces() (contracts/**/*.schema.json, *.spec.md, or similar) feeding a new inventory.schema.json property"
      - "detect_codeowners_surfaces() (.github/CODEOWNERS existence + parsed path entries) feeding a new inventory.schema.json property, wired into plan.classify() so codeowners-ownership questions actually fire"
  - truth: "ADOPT-03 / roadmap SC-3: every harness destination resolves to exactly one disposition"
    status: failed
    reason: >
      `destinations._CATALOG` is a hardcoded, fixed-size, 40-row list that never varies with the
      scanned target OR with the harness's own real file tree — `build_manifest()` always emits
      exactly 39 dispositions + 1 excluded row, verified by directly running
      `python -m tools.adoption_scan --target . --out <dir>` against this repo itself. Several
      catalog rows are literal placeholder paths borrowed from 26-RESEARCH.md's illustrative
      "widget" example and do not exist anywhere in this checkout (e.g.
      `harness/agents/widget-engineer.md`, `harness/commands/widget-check.md`,
      `harness/skills/widget-conventions/SKILL.md`, `.opencode/agent/widget-engineer.md`,
      `.claude/agents/widget-engineer.md`, `golden/widget/verified/case.txt`,
      `docs/adr/0001-decision.md`, `.memory/agreements/0001-widget.md`,
      `.workflow/tasks/T-0001/task.json`, `tools/widget_tool/pyproject.toml` — 10 of 40 rows
      confirmed non-existent by direct filesystem check). Meanwhile this repo actually has 11 real
      `*.schema.json` contract files (catalog covers exactly 1), 10 real ADRs (catalog's ADR row
      points at a nonexistent file), 23 real `harness/commands/*.md` (catalog covers exactly 1),
      11 real `harness/skills/*/SKILL.md` (catalog covers exactly 1), 38 real `.claude/agents/*.md`
      (catalog covers exactly 1), 5 real `.opencode/agent/*.md` (catalog covers exactly 1), and 4
      real nested `AGENTS.md` files (catalog covers exactly 1, `libs/python/AGENTS.md`; the other 3
      — root aside — get no manifest row at all). Roadmap SC-3 reads "every harness destination has
      exactly one disposition" and ADOPT-03's own text lists "contracts·golden·ADR·Diátaxis 4
      quadrants·... root/nested AGENTS·..." as the destinations to be covered — the shipped catalog
      is a one-example-per-category sample, not an enumeration of the actual destination set, so
      the manifest under-covers by roughly an order of magnitude on every glob-shaped category. This
      is disclosed as a deliberate implementation choice in 26-03-SUMMARY.md's key-decisions ("Catalog
      row destinations use concrete representative paths... rather than the research table's literal
      glob-pattern/prose strings"), but the disclosure frames it as a testability convenience, not as
      a scope reduction from "every harness destination" to "one representative example per plane."
      Totality is only proven over the tool's own fixed 40-string catalog (`test_dispositions.py::test_total`),
      never against a target's, or the harness's own, actual file tree.
    artifacts:
      - path: "tools/adoption_scan/destinations.py:98-274"
        issue: "_CATALOG is a static 40-tuple of literal paths, several nonexistent placeholders, never expanded from the glob patterns 26-RESEARCH.md's own catalog specified (contracts/**/*.schema.json, golden/**, docs/adr/**, harness/agents/*.md, harness/commands/*.md, harness/skills/<name>/SKILL.md, .opencode/{agent,...}/**, .claude/{agents,...}/**)"
      - path: "tools/adoption_scan/destinations.py:370-415"
        issue: "build_manifest() iterates destination_catalog() only — never the scanned inventory's included[] set or a real glob expansion, so dispositions[] length is target-independent (always 39) regardless of what a real target or the harness itself actually contains"
    missing:
      - "Either expand each glob-shaped catalog row into one disposition row per real matching file (harness-side, at minimum) at build_manifest() time, or explicitly re-scope ADOPT-03/roadmap SC-3's wording to 'one disposition per destination category' and get that re-scoping ratified — the current code silently does the latter without updating the requirement/roadmap text it claims to satisfy"
deferred: []
human_verification: []
---

# Phase 26: Deterministic Brownfield Inventory + Mapping (v2.3 B) Verification Report

**Phase Goal:** A read-only deterministic repo inventory, an evidence-classified (observed/inferred/unknown) mapping plan in the TOPO vocabulary, and a complete destination/disposition manifest — agent-free, fully CI-testable.
**Verified:** 2026-07-19
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Repeated inventory/plan/manifest output is byte-identical regardless of file enumeration order (roadmap SC-1) | ✓ VERIFIED | `test_determinism.py::test_double_run_byte_identical` + `::test_shuffled_enumeration_byte_identical`, `test_snapshots.py` committed syrupy snapshot; `1010 passed` full suite; independently re-ran `python -m tools.adoption_scan --target . --out <dir>` twice — identical output confirmed by prior review's own re-run (26-REVIEW.md "Determinism" verification block) |
| 2 | Every proposed item classified observed/inferred/unknown; unresolved ownership stays a question (roadmap SC-2, ADOPT-02) | ✓ VERIFIED (with caveat) | `plan.py::classify()` — direct-restatement→observed (manifests), structural-inference→inferred (candidate_process_boundaries, always `rationale`-carrying), everything ownership/placement→unknown by construction (docs-destination, agents-boundary, test-command). Confirmed on a real self-scan: 64 proposals, 7 questions, all AGENTS.md/docs/test-command entries `unknown`. Caveat: `excluded-file` and `collision` question kinds are defined in the schema/templates but never fire on any real scan (honestly disclosed in 26-03-SUMMARY.md, not a requirement violation — ADOPT-02's text does not name these two kinds explicitly) |
| 3 | Every harness destination resolves to exactly one disposition (roadmap SC-3, ADOPT-03) | ✗ FAILED | See gap below — the manifest's "40-row catalog" is a fixed representative sample (10 of 40 rows are nonexistent placeholder paths), never expanded against the harness's or a target's real file tree; self-scan always yields exactly 39/1 regardless of the repo actually having 11 schemas, 10 ADRs, 23 commands, 11 skills, 38 `.claude/agents`, 5 `.opencode/agent`, 4 nested `AGENTS.md` |
| 4 | Confinement, secret exclusion, size cap, ambiguity, collision detection pass; target tree unchanged (roadmap SC-4) | ⚠️ PARTIAL | Confinement/symlink-escape, vendored, generated-segment, size-cap, binary, and read-only guarantees all hold and are unit-tested (`test_scan_exclusions.py`, `test_readonly.py`); collision (preserve/conflict) now correctly reachable post-CR-01-fix (independently verified — self-scan against this repo produced 1 real `conflict` row and 13 `preserve` rows). However the reused v2.2 secret-content pattern is demonstrably too broad for prose: scanning this repo's own real `.github/workflows/ci.yml` excludes it as `secret-content` because the comment text `"...enforcement is a REPO SETTING..."` contains the substring `"...TOKEN: gate..."`, which matches the shared `gate-registry.json` pattern `(?:token)\s*[:=]\s*[^\s]+` case-insensitively — a genuine false positive on ordinary prose, reproduced directly, not hypothetical |
| 5 | Inventory reports existing schema/spec/doc/ADR/AGENTS/CODEOWNERS/CI surfaces (ADOPT-01 literal text) | ✗ FAILED | See gap below — `detect.py` has no schema-surface or CODEOWNERS-surface detection at all; `inventory.schema.json` has no property to hold either. CI-surface detection is unreliable per Truth 4's false positive |
| 6 | Pipeline is agent-free and fully CI-testable, and is actually wired into CI (not merely wireable) | ✓ VERIFIED | `tools/adoption_scan` is a `uv` workspace member (`tools/*` glob in root `pyproject.toml`); root `testpaths = ["libs/python", "tools"]` includes it; `.github/workflows/ci.yml`'s `core-suite` job runs `uv run pytest` (full suite, includes `tools/adoption_scan/tests/*`, which drives `cli.main()` end-to-end via `test_cr01_conflict_reachable_through_real_cli`); `drift` job's `uv run python -m tools.contract_drift.drift` covers the three new adoption schemas (confirmed hash entries present, drift green). No agent invocation anywhere in `tools/adoption_scan/` — pure stdlib + repo-internal imports |

**Score:** 4/6 truths verified (2 failed as detailed above)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `contracts/harness/adoption/{inventory,plan,manifest}.schema.json` | 3 self-contained, drift-gated schemas | ✓ VERIFIED | Present, hash-baselined in `contracts/.hashes/manifest.json`, `contract-drift: OK`, no cross-file `$ref` (D-11 confirmed by grep) |
| `tools/adoption_scan/scan.py` + `detect.py` | Confined read-only enumeration + exclusion classification + surface detection | ⚠️ PARTIAL | Enumeration/exclusion/hashing solid and tested; surface detection incomplete (schema/CODEOWNERS missing, CI detection has a reproduced false-positive) — see gaps |
| `tools/adoption_scan/plan.py` | D-02 ladder, D-05 questions, relationship candidates | ✓ VERIFIED (dormant relationship path acknowledged) | Structurally sound; relationship-candidate emission is unit-tested but never exercised on a real scan (no relationship signal source in ADOPT-01 scope — acceptable, honestly disclosed) |
| `tools/adoption_scan/destinations.py` | 40-row catalog + total 7-step disposition chain | ⚠️ PARTIAL | Chain logic itself is correctly total and CR-01/WR-03 fixes hold up under independent re-verification; the catalog it operates over is not a real destination enumeration — see gap |
| `tools/adoption_scan/cli.py` | Wired pipeline, schema-validates before write, `--out` required/confined | ✓ VERIFIED | Confirmed via direct invocation against this repo (`python -m tools.adoption_scan --target . --out <dir>`) — produced schema-conformant artifacts, refused overlapping `--out` per D-11 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `cli.py` | `scan.build_inventory` → `plan.build_plan` → `destinations.build_manifest` | direct function calls | ✓ WIRED | Confirmed by reading `cli.py:73-77` and by direct execution |
| `destinations.harness_proposed_hashes()` | harness's own checkout content (CR-01 fix) | `_REPO_ROOT / destination` read | ✓ WIRED | Independently reproduced the CR-01 repro: a target `pyproject.toml`/`.gitignore` with different content than this checkout's own now resolves `conflict`, not `preserve` |
| `plan.classify()` | `inventory["documentation_surfaces"]` (per-file AGENTS.md) | WR-01 fix | ✓ WIRED | Independently confirmed on a real self-scan: 4 distinct `agents-boundary` proposals/questions, one per real nested `AGENTS.md` file |
| CI (`core-suite`, `drift` jobs) | `tools/adoption_scan` tests + new schemas | `uv run pytest` / `uv run python -m tools.contract_drift.drift` | ✓ WIRED | Confirmed workspace membership + testpaths + job commands in `.github/workflows/ci.yml` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ADOPT-01 | 26-01, 26-02 | Bounded deterministic inventory: languages, manifests, doc/ADR/AGENTS/CODEOWNERS/CI/schema/spec surfaces, candidate process boundaries, secret/binary/vendor/generated/source-dump exclusion | ✗ BLOCKED (partial) | Enumeration/exclusion/language/manifest/AGENTS/ADR detection solid; schema-surface and CODEOWNERS-surface detection entirely absent (no code, no schema property); CI-surface detection demonstrably false-positives on this repo's own real workflow file |
| ADOPT-02 | 26-01, 26-03 | Evidence-classified mapping plan (observed/inferred/unknown), unresolved ownership → question, TOPO vocabulary compatibility | ✓ SATISFIED | `classify()`/`generate_questions()`/`generate_relationship_candidates()` structurally enforce the ladder and never-invented-authority; relationship candidates validate against `relationship.schema.json` (unit-tested); dormant on real scans only because no relationship signal exists yet (acceptable, ADOPT-01-scope limitation, not an ADOPT-02 defect) |
| ADOPT-03 | 26-01, 26-03 | Complete destination/disposition manifest — exactly one disposition per harness destination across contracts/golden/ADR/Diátaxis/memory/config/AGENTS/CODEOWNERS/source/emitted | ✗ BLOCKED | The disposition rule chain itself is correct and total over its own catalog, but the catalog is a fixed 40-entry representative sample (not a real per-file enumeration); the manifest under-covers real contract/ADR/agent/skill/command file counts by roughly an order of magnitude per category |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tools/adoption_scan/scan.py:54` | `SECRET_PATH_GLOBS` | Redundant glob (`**/*.env` subsumed by `*.env` under `fnmatch`) | ℹ️ Info | Cosmetic, already disclosed as IN-01, deliberately deferred by repo owner |
| `tools/adoption_scan/plan.py:150-170` | Overlapping `test-command` questions from CI + test surfaces | ℹ️ Info | UX only, already disclosed as IN-02, deliberately deferred by repo owner |
| `tools/adoption_scan/scan.py:52` (`_secret_pattern`, reused from `gate-registry.json`) | Secret-content regex too broad for prose | ⚠️ Warning | Newly found in this verification — false-excludes this repo's own real `.github/workflows/ci.yml`, defeating CI-surface detection on a realistic, non-synthetic case; not covered by any existing test (`test_scan_exclusions.py` only tests the fixture's deliberately-planted secret files, never a real-world prose false positive) |

### Human Verification Required

None — all findings in this report are independently, programmatically reproducible (direct CLI execution against this repo, direct filesystem checks, direct code reading), so none require a human-only judgment call. The two BLOCKER gaps and the newly found secret-pattern false positive are all objectively demonstrated above.

### Gaps Summary

Two of the phase's three owned requirements are only partially delivered at the end state, despite REQUIREMENTS.md marking ADOPT-01/02/03 "Complete":

1. **ADOPT-01 under-detects surfaces.** The phase's own CONTEXT.md and REQUIREMENTS.md text name six inventory surface categories (schema, spec, doc, ADR, AGENTS, CODEOWNERS, CI); the shipped code detects four (doc, ADR, AGENTS, CI) and the CI detector itself has a reproduced false-positive against this repo's own real file. Schema-surface and CODEOWNERS-surface detection do not exist in `detect.py` or `inventory.schema.json` at all — not a stub, an outright omission the schema itself has no room for.

2. **ADOPT-03's manifest does not cover "every harness destination."** The 40-row catalog in `destinations.py` is a fixed, hand-picked representative sample — several rows are literal fictional placeholder paths inherited from the research doc's illustrative "widget" example and do not exist anywhere in this checkout. Running the tool against this repo's own real tree (which has 11 real contract schemas, 10 real ADRs, 23 real harness commands, 11 real skills, 38 real `.claude/agents`, 5 real `.opencode/agent`, 4 real nested `AGENTS.md`) still always produces exactly 39 dispositioned rows + 1 excluded row — proving the manifest's coverage is target/harness-content-independent, not an enumeration of real destinations. The disposition *rule chain* itself is sound (CR-01/WR-03 fixes hold under independent re-verification), but the catalog it is applied to falls well short of "every harness destination" as both the roadmap success criterion and the requirement text state it.

Both gaps were introduced by design decisions made during 26-01 (schema authoring — no schema/CODEOWNERS property) and 26-03 (catalog authored as representative literal paths rather than glob-derived per-file rows) and were not caught by the code review (which focused on the disposition *chain's* correctness, not the catalog's *coverage*) or by the test suite (which only proves totality/reachability over the tool's own fixed catalog, never against a real file tree's actual destination count).

**This looks like it could be an intentional scope interpretation** (a "one disposition per destination *category*" reading rather than "one disposition per destination *file*"), but that reading was never surfaced to the user for explicit sign-off — the SUMMARY frames the catalog-row change as an implementation convenience ("so `disposition()` can be exercised directly and honestly... without a synthetic-string special case"), not as a load-bearing scope reduction from the roadmap's literal "every harness destination" wording. If this scope reading is in fact intended, it should be recorded as an explicit override rather than left implicit:

```yaml
overrides:
  - must_have: "Every harness destination resolves to exactly one disposition (roadmap SC-3)"
    reason: "Catalog enumerates one representative destination per plane/category rather than every real file; Phase 27 is expected to expand categories to real files at apply time."
    accepted_by: "{name}"
    accepted_at: "{ISO timestamp}"
```

---

_Verified: 2026-07-19_
_Verifier: Claude (gsd-verifier)_
