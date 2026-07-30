---
phase: 47-package-facts
verified: 2026-07-29T18:31:16Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 47: Package Facts Verification Report

**Phase Goal:** An agent asking "what packages exist here, what do they depend on, and which
package owns this contract?" gets one derived, committed, machine-built answer instead of reading
24 manifests or trusting a hand-written `[[components]]` table.

**Verified:** 2026-07-29T18:31:16Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 (SC1) | One committed derived artifact lists every package with manifest path, language, package id; delete+regenerate is byte-identical | ✓ VERIFIED | `.memory/derived/package-facts.md` is `git ls-files`-tracked, carries `# DERIVED — do not hand-edit (tools/memory_regen/package_facts.py)` header, no timestamp. Ran `uv run python -m tools.memory_regen.package_facts` live in this checkout: `git status --porcelain` showed **zero diff** after regeneration (23 packages, 2 edges — matches committed content). |
| 2 (SC2) | Every dependency edge is parsed from manifests; no hand-maintained dependency list exists; removing a fixture dependency removes exactly that edge | ✓ VERIFIED | `tools/adoption_scan/detect.py` adds `detect_dependencies()` + 5 pure per-kind parsers (`pyproject.toml`, `package.json`, `*.csproj`, `go.mod`, `Cargo.toml`). `tools/adoption_scan/tests/test_detect.py` has concrete, non-tautological assertions per kind (e.g. exact name/kind/path sets on synthetic manifest text). `tools/memory_regen/tests/test_package_facts.py` has 5 **add/remove round-trip** tests, one per manifest kind, each asserting an edge exists before removal and `edges == []` after — a real behavioural proof that would fail if parsing broke. `test_unresolvable_dependency_is_dropped_not_fabricated` proves external deps never become edges. No hand-maintained dependency list found anywhere in `tools/`, `harness/`, `libs/`, or config. |
| 3 (SC3) | `[[components]]` overrides the derived record field-by-field; both live configs (core + instance) still load with zero edits | ✓ VERIFIED | `tools/harness_config/loader.py:effective_packages()` does field-level layering (declared wins, unmatched fields survive, unmatched components stay declared-only without raising). `tools/harness_lint/tests/test_package_facts_override.py` loads `harness/project.toml` unedited through `effective_packages()` and asserts no raise + no vanished ids. `examples/log-parser/tests/test_package_facts_override_instance.py` does the identical proof against the instance overlay, unedited. Confirmed this instance-leg file is wired into CI: `.github/workflows/ci.yml:170` runs `uv run pytest examples/log-parser/tests`; ran it locally — 16 passed, not orphaned. |
| 4 (SC4) | Given a contract path, `contract_graph` reports the owning package, using package facts | ✓ VERIFIED | `tools/contract_graph/ownership.py:owning_package()` is a pure nearest-enclosing-dir lookup; read the module and confirmed it imports neither `compile.py` nor `query.py` (no traversal coupling — only `pathlib`). Re-exported lazily via `tools/contract_graph/__init__.py`. `tools/contract_graph/tests/test_ownership.py` has 6 tests including `test_synthetic_instance_style_fallback_documented` (root fallback proven on a synthetic instance-shaped path per the CONTEXT.md-mandated proof) and a deterministic tie-break test — genuine behavioural coverage, not tautological. |
| 5 (SC5) | No new gate, no new CI job: `ci.yml` job set and `gate.needs` unchanged from base commit `0531987`; only the existing `stale-derived` job widened | ✓ VERIFIED | `git diff 0531987..HEAD -- .github/workflows/ci.yml` shows a 6-line diff entirely inside the `stale-derived` job's two `run:` steps (regen command + diff-check command gain `package_facts`/`package-facts.md`). Diffed the full job-name list at `0531987` vs `HEAD`: identical 11 jobs including `gate`. `gate.needs` line (`ci.yml:329`) is byte-identical between the two revisions. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.memory/derived/package-facts.md` | Committed derived package+edge graph | ✓ VERIFIED | Tracked, correct header, byte-identical regen confirmed live |
| `tools/memory_regen/package_facts.py` | Generator, reuses `detect.py` | ✓ VERIFIED | 246 lines, substantive; imports `tools.adoption_scan.detect`, no re-implementation of manifest recognition |
| `tools/adoption_scan/detect.py` (`detect_dependencies` + 5 parsers) | Dependency extraction per manifest kind | ✓ VERIFIED | Pure functions, unit-tested per kind |
| `tools/harness_config/loader.py` (`effective_packages`) | Override-layering function | ✓ VERIFIED | Field-level merge, tested core + instance legs |
| `tools/contract_graph/ownership.py` (`owning_package`) | Contract→package attribution | ✓ VERIFIED | Pure lookup, no `query.py`/`compile.py` coupling, re-exported |
| `.github/workflows/ci.yml` (`stale-derived` job) | Widened, not a new job | ✓ VERIFIED | Diff confined to 2 `run:` step lines |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `package_facts.py` | `detect.py` | `from tools.adoption_scan import detect` | ✓ WIRED | Live import, used for both `detect_manifests` and `detect_dependencies` |
| `effective_packages()` | `package_facts.build_facts()` | lazy in-function import | ✓ WIRED | Mirrors `compile_graph`'s deferred-import pattern; exercised by tests |
| `ci.yml` stale-derived job | `tools.memory_regen.package_facts` | shell `run:` step | ✓ WIRED | Regenerates and diff-checks `.memory/derived/package-facts.md` |
| `/refresh-memory` + `curator` persona | `tools.memory_regen.package_facts` | doc + shell reference | ✓ WIRED | Present in `.claude`, `.opencode`, and `harness/` (single-source emit) versions |
| Instance overlay test | `effective_packages()` | direct call | ✓ WIRED | Not orphaned — executed via `uv run pytest examples/log-parser/tests` in CI (`ci.yml:170`) and locally (16 passed) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Regeneration is byte-identical | `uv run python -m tools.memory_regen.package_facts` then `git status --porcelain .memory/derived/package-facts.md` | empty diff, "23 package(s), 2 edge(s)" | ✓ PASS |
| GEN-04 core-no-example-dependency guard | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | 18 passed | ✓ PASS |
| Full test suite | `uv run pytest -q` | 912 passed | ✓ PASS |
| Instance leg (not orphaned) | `uv run pytest examples/log-parser/tests -q` | 16 passed | ✓ PASS |
| No literal `examples/` path under `tools/`/`harness/`/`libs/` code (phase-introduced files) | `grep -rn '"examples/'` scoped to `tools`,`harness`,`libs` | only pre-existing, untouched `harness/project.toml` DATA lines (unrelated to this phase, unchanged by it) | ✓ PASS |
| No SessionStart injection of package facts | `grep -n "package_facts\|package-facts" tools/memory_regen/inject.py` and `.claude/hooks/memory-inject.sh` | no matches in either | ✓ PASS |
| No debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER) in phase-touched files | grep across `git diff 0531987..HEAD --name-only` file set | none found | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MONO-01 | 47-01/47-02 | Committed derived package graph | ✓ SATISFIED | `.memory/derived/package-facts.md` + generator |
| MONO-02 | 47-01/47-02 | Dependency edges derived from manifests, no hand-maintained list | ✓ SATISFIED | `detect_dependencies` + fixture round-trip tests |
| MONO-03 | 47-03 | `[[components]]` becomes override slot, zero-edit for both live configs | ✓ SATISFIED | `effective_packages()` + core/instance consistency gates |
| MONO-04 | 47-04 | Package graph feeds `contract_graph` for contract→package attribution | ✓ SATISFIED | `owning_package()` pure lookup |

No orphaned requirements found in REQUIREMENTS.md's Phase 47 mapping.

### Anti-Patterns Found

None. Sampled assertions across all five plans (detect.py parsers, package_facts round-trip tests,
effective_packages layering tests, owning_package tests, ci.yml diff) — each is a genuine
behavioural check that would fail if the underlying implementation regressed (concrete before/after
values, not self-comparisons or `== True`-style tautologies). No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER
markers in any file touched by this phase.

Special-scrutiny item (47-04's "no second traversal engine" claim): confirmed by direct code
inspection, not by the acceptance grep count alone — `tools/contract_graph/ownership.py` imports
only `pathlib`, and neither `compile.py` nor `query.py` is imported or called anywhere in the
module. The no-coupling property holds independently of how the acceptance grep was satisfied.

### Human Verification Required

None. This phase is fully report-only tooling with no UI/visual/real-time surface; every success
criterion and key claim was verifiable by direct code inspection, live regeneration, and test
execution.

### Gaps Summary

No gaps. All five roadmap success criteria are verified against live code behavior (not SUMMARY.md
narrative): the derived artifact regenerates byte-identically, dependency edges are proven by
add/remove round-trip tests on synthetic fixtures for all five manifest kinds, the override layer
is field-level and non-destructive with both live configs loading unedited (instance leg confirmed
wired into CI, not orphaned), contract ownership is a pure lookup with no second traversal engine,
and the CI job set/gate.needs are unchanged from the phase's base commit with only the existing
`stale-derived` job's steps widened. Full test suite (912 tests) and the instance-leg suite (16
tests) both pass locally.

---

_Verified: 2026-07-29T18:31:16Z_
_Verifier: Claude (gsd-verifier)_
