---
phase: 26-deterministic-brownfield-inventory-mapping-v2-3-b
verified: 2026-07-19T17:59:36Z
status: passed
score: 5/6 must-haves verified (1 disclosed, non-blocking, out-of-scope limitation carried forward)
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/6
  gaps_closed:
    - "CR-01 (destination_catalog() checkout-state dependency): destination_catalog() now filters every glob match through git ls-files (failure-tolerant); independently reproduced via a real `git worktree add --detach HEAD` clean checkout — the worktree's catalog is byte-identical (341 rows, zero diff) to the current tree's catalog, and a live-created untracked `.memory/derived/*` file is proven excluded from the catalog while it exists."
    - "CR-02 (snapshot coupled to live repo size): build_manifest() now accepts an injectable catalog=; the committed test_snapshots.ambr's manifest section is rendered over a 6-row fixed catalog instead of the live ~340-row repo enumeration. Independently reproduced: added a throwaway tracked file under docs/adr/ (a catalog-covered directory) and confirmed test_artifacts_match_committed_snapshot still passes."
    - "CR-03 (inventory.schema.json vs plan.schema.json evidence-cardinality contradiction): inventory.schema.json's surfaceRecord.evidence is now minItems:1, matching plan.schema.json's proposalRecord/questionRecord.evidence. Independently reproduced: the exact prior repro (codeowners_surfaces entry with evidence:[]) now fails at the inventory-schema gate itself (12 validation errors including the evidence-shape violation) instead of reaching build_plan() and crashing the CLI. Contract-hash manifest recomputes byte-identical; docs_sync/memory_regen produce zero diff (derived plane in sync)."
    - "WR-05 (schema_surfaces detected but never consumed by plan.py): plan.py::classify() now walks inventory['schema_surfaces'] per evidence pointer, emitting one contract-candidate proposal per schema file. Independently reproduced: a real self-scan of this repo's own contracts/ tree produces exactly 11 contract-candidate proposals, matching the live count of 11 real *.schema.json files under contracts/."
    - "WR-06 (detect_codeowners_surfaces only recognized .github/CODEOWNERS): now recognizes all three GitHub-honored locations (CODEOWNERS, .github/CODEOWNERS, docs/CODEOWNERS) via a _CODEOWNERS_PATHS frozenset; confirmed present in source and covered by two new unit tests, both passing."
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "SC-4 secret-exclusion precision: the secret-content regex should not false-positive on real, non-secret prose"
    addressed_in: "Not scheduled in a later phase's stated goal/success criteria — this is a disclosed, pre-existing, out-of-scope limitation, not a deferred-by-roadmap item"
    evidence: "Reproduced: tools.adoption_scan.scan._secret_pattern() matches 'TOKEN: gate' inside this repo's own .github/workflows/ci.yml (the (?:api[_-]?key|secret|password|token)\\s*[:=]\\s*[^\\s]+ pattern is over-broad). This was carried forward, unaddressed, from the prior verification round; none of plans 26-07/26-08/26-09 touched scan.py's secret-pattern logic (confirmed via `git diff --stat` across the gap-closure commit range: zero changes to scan.py). The failure direction is conservative (over-exclusion of non-secret content), not a security regression (no secret leak), so it does not block the phase goal, but it is a real precision gap that should get its own follow-up plan before Phase 27 relies on scan.py's secret classification for broader targets."
human_verification: []
---

# Phase 26: Deterministic Brownfield Inventory + Mapping (v2.3 B) Verification Report

**Phase Goal:** A read-only deterministic repo inventory, an evidence-classified (observed/inferred/unknown) mapping plan in the TOPO vocabulary, and a complete destination/disposition manifest — agent-free, fully CI-testable.
**Verified:** 2026-07-19T17:59:36Z
**Status:** passed
**Re-verification:** Yes — after gap-closure plans 26-07, 26-08, 26-09

## Goal Achievement

This is a re-verification following three gap-closure plans that targeted the previous round's two
CRITICAL regressions (CR-01, CR-03) and the one carried-forward gap (WR-05 / schema_surfaces
unreachability). Every fix was independently reproduced in this session — not accepted from the
executor's report or a code review — using the exact adversarial checks the orchestrator specified
(a real `git worktree` clean-checkout comparison, a live-created gitignored-file exclusion test, an
unrelated tracked-file-add snapshot-stability test, a direct schema-validator repro of the CR-03
shape, and a live self-scan count match for WR-05/WR-06). All five targeted defects are closed. The
phase goal — "agent-free, fully CI-testable" inventory/plan/manifest pipeline — is now achieved. One
pre-existing, disclosed, out-of-scope limitation (SC-4's secret-pattern false-positive precision)
remains open and is reported honestly below; it does not block the phase goal.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Repeated inventory/plan output is byte-identical across invocations, enumeration-order-independent (roadmap SC-1) | ✓ VERIFIED | `test_determinism.py` unaffected by this round's changes; ran as part of the full 1031-test suite, green |
| 2 | Every proposed item classified observed/inferred/unknown; unresolved ownership stays a question (roadmap SC-2, ADOPT-02) | ✓ VERIFIED | Previously verified with a caveat (schema_surfaces detected-but-unconsumed). Caveat closed this round: independently ran `scan.build_inventory` + `plan.build_plan` against this repo's own live `contracts/` tree — produced exactly 11 `contract-candidate` proposals, matching `len(sorted(Path("contracts").rglob("*.schema.json")))` == 11. `test_contract_candidate_question_fires`/`test_contract_candidate_proposal_per_schema_file`/`test_contract_candidate_matches_real_repo_schema_count` all pass |
| 3 | Every harness destination resolves to exactly one disposition (roadmap SC-3, ADOPT-03) | ✓ VERIFIED | Independently reproduced the exact clean-checkout test the orchestrator required: `git worktree add --detach HEAD` into a scratch dir, ran `destination_catalog()` there via the repo's own venv interpreter, and diffed the sorted destination list against the current (untracked-state-laden) working tree's catalog — **byte-identical, 341 rows, zero diff**. Also independently created a live untracked `.memory/derived/__verify_untracked_proof__.md` file (confirmed gitignored via `git check-ignore`) and confirmed it is excluded from `destination_catalog()`'s output while it exists |
| 4 | Pipeline is agent-free and fully CI-testable (phase goal text) | ✓ VERIFIED | Same clean-worktree reproduction above proves the catalog is invariant to local untracked state — the exact property CI's `core-suite` job (checkout → `uv sync` → `uv run pytest`, no `memory_regen` step) depends on. Additionally reproduced CR-02's fix: added a throwaway tracked file under `docs/adr/` (a catalog-covered, non-fixed-catalog-affecting directory) and confirmed `test_artifacts_match_committed_snapshot` still passes (the committed snapshot's manifest section is now a fixed 6-row catalog, confirmed via `grep -c '"destination"'` == 6 against the 535-line `.ambr`, down from 1859 lines/~340 rows) |
| 5 | Inventory/plan pipeline is internally consistent — a schema-valid inventory never crashes the CLI (implicit in "complete...manifest", "fully CI-testable") | ✓ VERIFIED | Confirmed both schemas: `inventory.schema.json`'s `surfaceRecord.evidence` is now `minItems: 1` (was 0), matching `plan.schema.json`'s `proposalRecord.evidence`/`questionRecord.evidence` (both already `minItems: 1`). Independently re-ran the exact prior CR-03 repro (a `codeowners_surfaces` entry with `evidence: []`) against `inventory.schema.json` directly with `Draft202012Validator` — it now fails at the **inventory-schema gate itself** (12 validation errors including the evidence-shape violation), one full validation step earlier than the previous `build_plan()`-time crash. `contracts/.hashes/manifest.json` recomputes byte-identical (`build_manifest()` == committed); `docs_sync`/`memory_regen` re-run produced zero `git status` diff (derived plane in sync). `test_build_plan_validates_for_every_inventory_surface_shape` / `test_empty_evidence_surface_record_now_fails_at_inventory_schema_gate` both pass |
| 6 | Confinement, secret exclusion, size cap, ambiguity, collision detection pass; target tree unchanged (roadmap SC-4) | ⚠️ PARTIAL — disclosed, carried forward, unaddressed this round | Not in scope of plans 26-07/08/09 (confirmed via `git diff --stat` across the full gap-closure commit range: zero changes to `scan.py`). Independently re-confirmed the previously-identified secret-pattern false positive still exists: `scan._secret_pattern().search(open(".github/workflows/ci.yml").read())` matches `"TOKEN: gate"` — the `(?:api[_-]?key\|secret\|password\|token)\s*[:=]\s*[^\s]+` pattern is over-broad against real, non-secret CI prose. The failure direction is conservative (over-exclusion of non-secret content into the "excluded" bucket, not a secret leak), so the mechanism functions safely, but the precision gap is real and unfixed |

**Score:** 5/6 truths fully verified; 1 truth carries a disclosed, non-blocking, out-of-scope precision limitation (unchanged from the prior round, not a new regression, not part of this round's targeted defects)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/adoption_scan/destinations.py::destination_catalog()` | Rule-derived, git-tracked-filtered, checkout-invariant enumeration | ✓ VERIFIED | `_tracked_repo_files()` present, called once per `destination_catalog()` call; independently reproduced checkout-invariance via clean worktree (see truth 3) |
| `tools/adoption_scan/destinations.py::build_manifest()` | Injectable `catalog=` parameter decoupling the committed snapshot from live repo size | ✓ VERIFIED | Signature confirmed: `build_manifest(inventory, target_root, proposed_hashes, *, catalog=None)`; `test_snapshots.py` passes a 6-row `_FIXED_CATALOG`; live-catalog default (`catalog=None`) unchanged for `cli.py` and structural tests |
| `contracts/harness/adoption/inventory.schema.json` | `surfaceRecord.evidence` requires `minItems: 1` | ✓ VERIFIED | Confirmed via direct JSON load: `minItems: 1`, description updated to "A surface with no evidence is never emitted by any detector; evidence is always non-empty." |
| `tools/adoption_scan/plan.py::classify()` | Walks `schema_surfaces` per evidence pointer, emitting `contract-candidate` proposals | ✓ VERIFIED (content + wiring + live data flow) | Confirmed via grep (line 195) and a live self-scan producing 11 proposals matching 11 real schema files |
| `tools/adoption_scan/detect.py::detect_codeowners_surfaces()` | Recognizes `CODEOWNERS`, `.github/CODEOWNERS`, `docs/CODEOWNERS` | ✓ VERIFIED | `_CODEOWNERS_PATHS` frozenset confirmed in source; `test_codeowners_surface_root_location`/`test_codeowners_surface_docs_location` both pass |
| `tools/adoption_scan/tests/__snapshots__/test_snapshots.ambr` | Committed determinism baseline, decoupled from live repo size | ✓ VERIFIED (reproducible) | 535 lines / 6 manifest rows (down from 1859/~340); confirmed stable against an unrelated tracked-file addition |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `destination_catalog()` | `git ls-files` | `_tracked_repo_files()`, failure-tolerant | ✓ WIRED | Confirmed by clean-worktree reproduction (identical catalogs across checkouts) |
| `test_snapshots.py` | `build_manifest()` | `catalog=_FIXED_CATALOG` keyword argument | ✓ WIRED | Confirmed unaffected by unrelated tracked-file additions |
| `plan.py::classify()` | `inventory["schema_surfaces"]` | direct dict/evidence walk | ✓ WIRED | Confirmed by live self-scan producing the expected 11 proposals |
| `plan.py::classify()` | `inventory["codeowners_surfaces"]` | direct dict walk (prior round) | ✓ WIRED | Unchanged, still passing |
| `detect.py::detect_codeowners_surfaces` | `_CODEOWNERS_PATHS` | frozenset membership | ✓ WIRED | Confirmed via source + unit tests for all three locations |
| `inventory.schema.json` | `plan.schema.json` | shared evidence-cardinality invariant (`minItems: 1` both sides) | ✓ WIRED | Confirmed via direct JSON load of both schemas and a fresh `Draft202012Validator` repro |
| CI `core-suite` job | `tools/adoption_scan` test snapshot | `uv run pytest` on a clean `actions/checkout` | ✓ REPRODUCIBLE | Clean-worktree reproduction is the closest available proxy for CI's exact shape (no network `git clone` available in this sandbox); worktree checkout produces a byte-identical catalog with no untracked local state |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ADOPT-01 | 26-01, 26-02, 26-04, 26-05, 26-08 | Bounded deterministic inventory incl. schema/CODEOWNERS surfaces | ✓ SATISFIED | Surface detection content gap closed (prior round); evidence-cardinality contradiction closed this round (CR-03) — a schema-valid inventory can no longer crash the pipeline |
| ADOPT-02 | 26-01, 26-03, 26-05, 26-09 | Evidence-classified mapping plan, unresolved ownership → question | ✓ SATISFIED | `codeowners-ownership` (prior round) and `contract-candidate` (this round, WR-05) question/proposal kinds both now fire on real data; WR-06's multi-location CODEOWNERS detection closes the last silent-miss vector for the blocking ownership question |
| ADOPT-03 | 26-01, 26-03, 26-06, 26-07 | Complete destination/disposition manifest, every harness destination exactly one disposition | ✓ SATISFIED | Catalog totality (content, prior round) + reproducibility (CR-01, this round) + snapshot decoupling (CR-02, this round) — independently reproduced via clean-worktree checkout |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tools/adoption_scan/scan.py` | `_secret_pattern()` / `SECRET_PATH_GLOBS` | Secret-content regex over-broad against real, non-secret prose (e.g. `TOKEN: gate` in `.github/workflows/ci.yml`) | ⚠️ Warning (carried forward, disclosed, non-blocking) | Conservative-safe failure direction (over-exclusion, not a secret leak); precision gap, not a security regression; unaddressed by this round's plans (out of scope) |
| `tools/adoption_scan/destinations.py` | `_INSTANCE_DIR_NAME = "examples"` | Instance-root name hardcoded rather than read from `harness/project.toml`'s `[instance] root` slot (26-REVIEW.md WR-01) | ℹ️ Info (carried forward, disclosed, unaddressed) | Correct for this repo's current instance root; would silently mis-scope for a harness deployment with a differently-named instance root |
| `tools/adoption_scan/destinations.py` | `**/pyproject.toml` in `_CATEGORY_GLOBS` | Catalogs 25 workspace-member manifests with none of their source (26-REVIEW.md WR-03) | ℹ️ Info (carried forward, disclosed, unaddressed) | Out of scope for this round; a target accepting the full catalog would get manifests for packages that don't exist there |
| `tools/adoption_scan/detect.py` | `detect_test_surfaces` (`parts[:1] == ("tests",)`) | Only recognizes a repo-root `tests/` directory, misses this very repo's own `tools/<pkg>/tests/` layout (26-REVIEW.md WR-07) | ℹ️ Info (carried forward, disclosed, unaddressed) | Running the scanner against this harness itself would report no test surface |
| `contracts/harness/adoption/inventory.schema.json` | top-level `description` | Plan-numbered changelog prose ("Plan 26-05's detect.py wiring...") baked into a CODEOWNERS-gated contract, rendered into user-facing docs (26-REVIEW.md WR-08) | ℹ️ Info (explicitly deferred by 26-08-PLAN.md, unaddressed as planned) | Cosmetic; costs a future hash rebaseline to remove, not a functional defect |

### Human Verification Required

None — every truth in this round was independently, programmatically reproduced above (a real
`git worktree` clean-checkout comparison, a live gitignored-file exclusion test, an unrelated
tracked-file-add snapshot-stability test, a direct `Draft202012Validator` repro against both
schemas, a live self-scan count match, and full-suite/contract-drift/GEN-04/docs_sync/memory_regen
re-runs). No judgment call is required to confirm any of the five targeted defects are closed.

### Gaps Summary

All three gap-closure plans (26-07, 26-08, 26-09) achieved what they set out to do, and every fix
was independently reproduced in this verification session rather than accepted from the executor's
or reviewer's report:

- **CR-01** (checkout-state-dependent catalog): closed via a git-tracked-only filter, proven with a
  real `git worktree` clean-checkout comparison (byte-identical, 341 rows) and a live
  gitignored-file exclusion test.
- **CR-02** (snapshot coupled to live repo size): closed via an injectable `catalog=` parameter;
  proven stable against an unrelated tracked-file addition.
- **CR-03** (cross-schema evidence-cardinality contradiction): closed by tightening
  `inventory.schema.json` to `minItems: 1`; the exact prior repro now fails at the earliest
  possible gate (inventory validation) instead of crashing the CLI downstream. Contract-hash,
  docs_sync, and memory_regen all confirmed in sync.
- **WR-05** (schema_surfaces detected but never consumed): closed; a live self-scan of this repo's
  own `contracts/` tree produces the exact expected count (11 proposals for 11 real schema files).
- **WR-06** (single-location CODEOWNERS detection): closed; all three GitHub-honored locations are
  now recognized and independently tested.

One item remains open, exactly as disclosed by the orchestrator's brief: **SC-4's secret-pattern
false positive** against real, non-secret prose (reproduced again this round against
`.github/workflows/ci.yml`) was not in scope of plans 26-07/08/09 and remains unaddressed. It does
not block the phase goal — the failure direction is conservative (over-exclusion, not a secret
leak) and the mechanism itself functions and is tested — but it is a real precision gap that should
get a dedicated follow-up plan, ideally before Phase 27 broadens scan.py's secret classification to
arbitrary brownfield targets where the false-positive rate against real prose matters more.

Several other review findings (WR-01 instance-root hardcode, WR-03 `pyproject.toml` catalog rows,
WR-07 test-surface detection scope, WR-08 plan-numbered contract prose, WR-09 general docstring
hygiene, IN-01..04) were explicitly out of scope for this gap-closure round and remain open,
disclosed, non-blocking limitations — none of them contradicts the phase goal text ("agent-free,
fully CI-testable" read-only inventory + evidence-classified plan + complete manifest"), and none
of them was newly introduced by this round's work.

**Conclusion: the phase goal is achieved.** The pipeline is agent-free, its determinism and
totality properties are independently proven reproducible across a real clean checkout (not merely
green on this working tree), and the two-contract internal-consistency defect that could previously
crash the CLI on a schema-valid input is closed. Phase 26 is ready to proceed; the one disclosed
limitation (SC-4 secret-pattern precision) and the other carried-forward info-level findings are
recommended as a small follow-up plan, not a blocker to Phase 27.

---

_Verified: 2026-07-19T17:59:36Z_
_Verifier: Claude (gsd-verifier)_
