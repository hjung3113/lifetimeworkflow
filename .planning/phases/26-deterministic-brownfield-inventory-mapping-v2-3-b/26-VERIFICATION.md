---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
verified: 2026-07-20T00:00:00Z
status: gaps_found
score: 3/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/6
  gaps_closed:
    - "ADOPT-01 schema half: inventory.schema.json now has schema_surfaces + codeowners_surfaces (required), detect.py implements both detectors, scan.py wires them"
    - "ADOPT-01/02 plan half: plan.py::classify() walks codeowners_surfaces and emits a real codeowners-ownership question (previously permanently dead code)"
    - "ADOPT-03 catalog totality (data level): destination_catalog() is now rule-derived glob enumeration over the real checkout, not the old static 40-row sample with 10 nonexistent placeholder paths"
  gaps_remaining:
    - "ADOPT-01 schema_surfaces detected but never consumed by plan.py — the contract-candidate proposal/question kind stays permanently unreachable (same defect class as the codeowners gap this round fixed, left open for the schema half)"
  regressions:
    - "CR-01 (new, introduced by 26-06): destination_catalog() globs the live filesystem with no git-tracking filter. The rewrite that closed ADOPT-03's totality gap bakes 3 gitignored, untracked derived files (.memory/derived/pointer-index.json, .memory/derived/pointer-index.md, .memory/derived/repo-map.md) into the committed test_snapshots.ambr. On a clean checkout (exactly CI's core-suite shape: checkout -> uv sync -> uv run pytest, no memory_regen step) the catalog yields 341 rows vs the snapshot's 344 and test_artifacts_match_committed_snapshot FAILS. Independently reproduced: the three destinations are gitignored (git check-ignore confirms) and absent from git ls-files, yet present in the .ambr at lines 677-685."
    - "CR-03 (new, introduced by 26-04/26-05): inventory.schema.json's surfaceRecord.evidence permits minItems:0 ('may be empty for an unknown/absent surface') while plan.schema.json's proposalRecord.evidence and questionRecord.evidence both require minItems:1. Independently reproduced: constructing a schema-valid inventory with a codeowners_surfaces entry carrying evidence:[] and running it through plan.build_plan() produces a plan object that Draft202012Validator flags with two '[] should be non-empty' errors — which is exactly the shape cli.main() schema-validates before writing any artifact, so a schema-valid inventory can hard-fail the CLI with no output at all. Latent only because today's two detectors happen to always attach non-empty evidence; the contract itself sanctions the failing shape."
gaps:
  - truth: "Pipeline is agent-free and fully CI-testable (phase goal text; roadmap SC-1 determinism)"
    status: failed
    reason: >
      The exact commits that closed the previous ADOPT-03 gap (26-06, rewriting destination_catalog()
      to glob the live filesystem) introduced a checkout-state dependency: the committed
      tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr encodes 3 gitignored/untracked
      derived files that exist only on this working tree. CI's core-suite job
      (.github/workflows/ci.yml:170-178, checkout -> uv sync --all-packages -> uv run pytest, no
      memory_regen step) runs on a clean checkout where those 3 files do not exist, so
      test_artifacts_match_committed_snapshot will fail there (341 catalog rows vs 344 baked into
      the snapshot). The suite is green in this session only because of accumulated local
      derived-artifact state, not because the pipeline is deterministic/CI-safe.
    artifacts:
      - path: "tools/adoption_scan/destinations.py"
        issue: "destination_catalog() enumerates Path.glob() over the live filesystem with no git-tracked filter; .memory/derived/**/*.md,*.json glob picks up gitignored generated files whenever they happen to exist locally"
      - path: "tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr"
        issue: "Committed baseline (lines 677-685) bakes in .memory/derived/pointer-index.json, .memory/derived/pointer-index.md, .memory/derived/repo-map.md — all confirmed gitignored via git check-ignore and absent from git ls-files"
    missing:
      - "Filter destination_catalog() to git-tracked paths only (e.g. via `git ls-files`), or explicitly exclude .memory/derived/* except the one re-included contracts-index.md, so the catalog and its snapshot are reproducible on a clean checkout"
      - "Regenerate the snapshot from a clean checkout (or with the filter applied) and confirm the row count is invariant to local derived-artifact state"
  - truth: "Inventory reports schema/CODEOWNERS surfaces and the plan/manifest pipeline is internally consistent (ADOPT-01, ADOPT-02)"
    status: failed
    reason: >
      inventory.schema.json's surfaceRecord.evidence (minItems:0) contradicts plan.schema.json's
      proposalRecord/questionRecord.evidence (both minItems:1). Reproduced directly: a schema-valid
      inventory with a codeowners_surfaces entry carrying evidence:[] produces a plan object that
      fails Draft202012Validator with two '[] should be non-empty' errors. Through cli.main() this
      exits 1 with no artifacts written at all (inventory and manifest discarded too, since
      validation runs before any write) — a schema-valid input crashes the "agent-free,
      fully CI-testable" pipeline this phase's goal text promises. Only latent (not yet hit by the
      two live detectors) because detect_schema_surfaces()/detect_codeowners_surfaces() happen to
      always attach at least one evidence pointer today; the contract itself sanctions the failing
      shape for any other/future producer or hand-authored inventory.
    artifacts:
      - path: "contracts/harness/adoption/inventory.schema.json"
        issue: "surfaceRecord.evidence: minItems 0, described as 'May be empty for an unknown/absent surface' — directly contradicts the plan schema's cardinality requirement for the same evidence shape"
      - path: "contracts/harness/adoption/plan.schema.json"
        issue: "proposalRecord.evidence and questionRecord.evidence both require minItems: 1 with no accommodation for an empty-evidence surface record"
    missing:
      - "Rebaseline surfaceRecord.evidence to minItems:1 (matching actual producer behavior — no detector ever emits an empty-evidence surface) in the same commit as a contract-hash rebaseline + docs_sync + memory_regen + snapshot refresh, or otherwise reconcile the two schemas so no schema-valid inventory can crash the CLI"
      - "A regression test asserting build_plan(inventory) validates for every surface array shape permitted by inventory.schema.json"
deferred: []
human_verification: []
---

# Phase 26: Deterministic Brownfield Inventory + Mapping (v2.3 B) Verification Report

**Phase Goal:** A read-only deterministic repo inventory, an evidence-classified (observed/inferred/unknown) mapping plan in the TOPO vocabulary, and a complete destination/disposition manifest — agent-free, fully CI-testable.
**Verified:** 2026-07-20
**Status:** gaps_found
**Re-verification:** Yes — after gap-closure plans 26-04, 26-05, 26-06

## Goal Achievement

This is a re-verification following execution of three gap-closure plans that targeted the previous
`26-VERIFICATION.md`'s two FAILED truths (ADOPT-01 surface coverage; ADOPT-03 catalog totality). Both
targeted gaps show real progress at the data/content level, but the fixes themselves introduced two
**new, independently-reproduced CRITICAL regressions** (CR-01, CR-03, both confirmed directly below,
not merely accepted from the orchestrator's report) that break the phase goal's own "agent-free,
fully CI-testable" and "complete...manifest" claims. Net result: the phase goal is **not** achieved.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Repeated inventory/plan/manifest output is byte-identical across repeated invocations in a given tree (roadmap SC-1, narrow reading) | ✓ VERIFIED | `test_determinism.py` double-run + shuffled-enumeration tests still pass; unrelated to the checkout-state issue below (that is a cross-checkout reproducibility failure, not a same-tree repeat-invocation failure) |
| 2 | Pipeline is agent-free and **fully CI-testable** (phase goal text) | ✗ FAILED | See gap: `test_artifacts_match_committed_snapshot` bakes in 3 gitignored/untracked derived files that only exist on this working tree; independently confirmed via `git check-ignore` + `git ls-files` that these 3 paths are absent from git tracking, and CI's `core-suite` job (`.github/workflows/ci.yml:170-178`) runs a clean checkout with no `memory_regen` step before pytest |
| 3 | Every proposed item classified observed/inferred/unknown; unresolved ownership stays a question (roadmap SC-2, ADOPT-02) | ✓ VERIFIED (with new caveat) | `codeowners-ownership` question kind now reachable — `plan.py:182` walks `codeowners_surfaces` and emits it (previously permanently dead code, confirmed fixed by direct grep). Caveat: `schema_surfaces` is populated in the inventory by `scan.py:339` but `plan.py` has no corresponding walk (grep confirms only `codeowners_surfaces` is referenced in `plan.py`) — the `contract-candidate` proposal/question kind remains permanently unreachable, an identically-shaped gap to the one just closed, left open |
| 4 | Every harness destination resolves to exactly one disposition (roadmap SC-3, ADOPT-03) | ✗ FAILED | `destination_catalog()` is now rule-derived (confirmed: no more static 40-row `_CATALOG`, real glob enumeration over `contracts/`, ADRs, `harness/commands`, `harness/skills`, `.claude/agents`, `.opencode/agent`), which is genuine progress on the *content* gap. But the catalog is not reproducible: it depends on gitignored, untracked `.memory/derived/*` files existing at scan time, so "every harness destination" is a moving target across checkouts — the very test meant to prove totality (`test_artifacts_match_committed_snapshot`) fails on a clean checkout, independently reproduced |
| 5 | Inventory/plan pipeline is internally consistent — a schema-valid inventory never crashes the CLI (implicit in "complete...manifest", "fully CI-testable") | ✗ FAILED | Independently reproduced: constructed a schema-valid inventory with `codeowners_surfaces` evidence `[]` (permitted by `inventory.schema.json`'s `minItems:0`), ran it through `plan.build_plan()`, and validated the result against `plan.schema.json` — 2 `'[] should be non-empty'` errors. Through `cli.main()` this is exit 1, zero artifacts written. Latent only because current detectors always attach evidence; the contract itself permits the failing shape for any other producer |
| 6 | Confinement, secret exclusion, size cap, ambiguity, collision detection pass; target tree unchanged (roadmap SC-4) | ⚠️ PARTIAL (carried forward, unaddressed this round) | Not in scope of the 3 gap-closure plans; the previously-identified secret-pattern false positive against real prose (e.g. this repo's own `.github/workflows/ci.yml`) was not revisited and remains an open, disclosed caveat from the prior verification round |

**Score:** 3/6 truths verified (2 net-new failures introduced by the gap-closure fixes themselves, 1 carried-forward partial)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `contracts/harness/adoption/inventory.schema.json` | `schema_surfaces` + `codeowners_surfaces` required properties | ✓ VERIFIED (content) / ✗ contract-inconsistent (cardinality) | Both properties present and required (confirmed via direct JSON load); `evidence` sub-schema (`minItems:0`) contradicts `plan.schema.json`'s `minItems:1` on the same conceptual field — see gap 2 |
| `tools/adoption_scan/detect.py::detect_schema_surfaces/detect_codeowners_surfaces` | Populate the two new inventory fields | ✓ VERIFIED (exists, wired into `scan.py:339-340`) | `detect_schema_surfaces` correctly scoped to `contracts/**/*.schema.json` only (confirmed by reading source); `detect_codeowners_surfaces` only matches the literal `.github/CODEOWNERS` path (misses `CODEOWNERS` at root and `docs/CODEOWNERS`, per code review WR-06, not independently re-verified by me but plausible from source inspection — not re-tested this round) |
| `tools/adoption_scan/destinations.py::destination_catalog()` | Rule-derived, real-file enumeration (not static sample) | ✓ VERIFIED (content) / ✗ FAILED (reproducibility) | Confirmed no static `_CATALOG` remains; confirmed the catalog is checkout-state-dependent via gitignore/ls-files check on the 3 CR-01 paths |
| `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr` | Committed determinism baseline | ✗ NOT reproducible on clean checkout | Confirmed to bake in 3 untracked/gitignored destinations; local suite run (`uv run pytest tools/adoption_scan -q`) passes (58 passed) only because those files exist in this session's working tree |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `scan.py::build_inventory` | `detect.detect_schema_surfaces` / `detect.detect_codeowners_surfaces` | direct call, `schema_surfaces`/`codeowners_surfaces` keys | ✓ WIRED | Confirmed by grep: `scan.py:339-340` |
| `plan.py::classify` | `inventory["codeowners_surfaces"]` | direct dict walk | ✓ WIRED | Confirmed: `plan.py:182` |
| `plan.py::classify` | `inventory["schema_surfaces"]` | — | ✗ NOT WIRED | No reference to `schema_surfaces` anywhere in `plan.py` (confirmed by grep) — `contract-candidate` proposal/question kind stays dead |
| `cli.main()` | `plan.schema.json` validation before write | schema-validate-then-write | ⚠️ WIRED but fragile | Confirmed wiring is correct as designed, but the upstream contract (`inventory.schema.json`) can produce input that trips this exact gate — see gap 2 |
| CI `core-suite` job | `tools/adoption_scan` test snapshot | `uv run pytest` on a clean `actions/checkout` | ✗ NOT reproducible | Confirmed via `git check-ignore`/`git ls-files` that the snapshot's dependency on `.memory/derived/{pointer-index.json,pointer-index.md,repo-map.md}` cannot be satisfied on the clean-checkout shape CI actually runs |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ADOPT-01 | 26-01, 26-02, 26-04, 26-05 | Bounded deterministic inventory incl. schema/CODEOWNERS surfaces | ✗ BLOCKED | Surface detection content gap closed (schema/CODEOWNERS categories now detected and required in the schema), but the schema's own evidence-cardinality contradiction (CR-03) means a schema-valid inventory instance can crash the pipeline — "bounded, deterministic reporting" is not safely guaranteed by the contract itself |
| ADOPT-02 | 26-01, 26-03, 26-05 | Evidence-classified mapping plan, unresolved ownership → question | ✗ BLOCKED | `codeowners-ownership` reachability fixed and confirmed; but `schema_surfaces` remains entirely unconsumed by `classify()`, so an ADOPT-01-reported surface category never becomes a classified proposal/question at all — an identical defect class to the one this round's plans set out to close, left open for schema surfaces |
| ADOPT-03 | 26-01, 26-03, 26-06 | Complete destination/disposition manifest, every harness destination exactly one disposition | ✗ BLOCKED | Catalog totality at the content level is now real (rule-derived glob enumeration, no placeholder rows) — the previously-reported gap-2 defect is fixed. But the fix's own mechanism (unfiltered live-filesystem glob) makes "every harness destination" a function of untracked local state rather than a stable, git-defined set — reproduced failing on a clean checkout, which is exactly the CI shape this requirement and the phase's own "fully CI-testable" language demand |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tools/adoption_scan/destinations.py` | glob enumeration in `destination_catalog()` | Live-filesystem glob with no git-tracking filter | 🛑 Blocker | CR-01 — confirmed clean-checkout test failure |
| `contracts/harness/adoption/{inventory,plan}.schema.json` | `evidence` field cardinality | Two sibling contracts disagree on `minItems` for the same conceptual shape | 🛑 Blocker | CR-03 — confirmed schema-valid input crashes CLI |
| `tools/adoption_scan/plan.py` | `classify()` | `schema_surfaces` inventory field never read | ⚠️ Warning | `contract-candidate` proposal/question kind permanently unreachable — same defect class as the just-fixed codeowners gap |
| `tools/adoption_scan/detect.py` | `detect_codeowners_surfaces` (not independently re-verified beyond source read) | Only matches `.github/CODEOWNERS`, not `CODEOWNERS` or `docs/CODEOWNERS` | ⚠️ Warning | Per code review WR-06; plausible from source but not independently executed this round |

### Human Verification Required

None — CR-01 and CR-03 are both independently, programmatically reproduced above (direct `git check-ignore`/`git ls-files` checks against the snapshot's baked-in paths; a direct `plan.build_plan()` + `Draft202012Validator` repro against a constructed schema-valid inventory). No judgment call is needed to confirm either defect exists.

### Gaps Summary

The two gap-closure plans that targeted the previous round's FAILED truths made real progress at the
data/content level:

- ADOPT-01: `schema_surfaces`/`codeowners_surfaces` now exist, are required, are detected, and
  (for CODEOWNERS) flow into a real classified proposal/question.
- ADOPT-03: the destination catalog is now genuinely rule-derived from the real file tree instead of
  a hand-picked, partially-fictional 40-row sample.

But both fixes introduced their own new, confirmed critical defects that directly undercut the phase
goal's "agent-free, fully CI-testable" language:

1. **CR-01** — `destination_catalog()`'s unfiltered live-filesystem glob bakes gitignored, untracked
   derived files into the committed determinism snapshot. This is a hard CI red on any clean
   checkout (independently confirmed the 3 paths are gitignored and absent from `git ls-files`,
   and that CI's `core-suite` job has no step that would regenerate them before pytest runs).
2. **CR-03** — `inventory.schema.json` and `plan.schema.json` disagree on `evidence` cardinality
   (`minItems:0` vs `minItems:1`), so a schema-valid inventory can crash `cli.main()` with no
   artifacts written. Independently reproduced by direct construction and validation.

Additionally, one gap of the *same shape* as the one just closed (a detected surface never reaching
the classification/question stage) remains open for `schema_surfaces` — `plan.py::classify()` reads
`codeowners_surfaces` but not `schema_surfaces`, so the `contract-candidate` question/proposal kind
stays permanently dead code exactly as `codeowners-ownership` was before this round.

Given the explicit instruction that a suite green only on a developer's working tree does not satisfy
a determinism/reproducibility requirement, and that both new defects are independently reproduced (not
merely accepted from the code-review report), phase 26's goal — "agent-free, fully CI-testable" and
"a complete destination/disposition manifest" — is **not** achieved as of this commit. This is not
eligible for an override suggestion: both defects are unintentional regressions (confirmed by their
own PLAN.md must-haves, which claimed exactly the opposite behavior — e.g. 26-06's must-have explicitly
claims totality "over the larger, real catalog," not one that varies by untracked local state), not an
alternative design choice a human could ratify as acceptable.

---

_Verified: 2026-07-20_
_Verifier: Claude (gsd-verifier)_
