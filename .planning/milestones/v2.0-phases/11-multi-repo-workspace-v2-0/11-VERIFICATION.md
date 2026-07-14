---
phase: 11-multi-repo-workspace-v2-0
verified: 2026-07-14T01:28:44Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 11: Multi-Repo Workspace (v2.0 / γ) Verification Report

**Phase Goal:** Several repos declared and operated as ONE workspace — the harness/project.toml
slot pattern raised one level into a workspace manifest, repo-scoped β fan-out per-repo with
workspace-level synthesis, contract-drift/golden gates extended across repo boundaries, the
Phase-8 pipeline topology generalized so an edge can cross a repo boundary, all while the core
depends on no workspace member (GEN-04 generalized to core→workspace-member).
**Verified:** 2026-07-14T01:28:44Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `workspace.toml` declares member repos + cross-repo edges as pure DATA, raising GEN-03 one level; `tools/workspace_config` is a passthrough loader + consistency gate (MREPO-01) | VERIFIED | `workspace.toml` has `[workspace]`, 2x `[[members]]`, one `[pipeline].edges` inline table, header names its 2 consumers, no logic. `tools/workspace_config/loader.py` — stdlib `tomllib`, `load_workspace/members/edges/split_endpoint`. `tools/harness_lint/tests/test_workspace_config.py` (10 tests, all pass) asserts member uniqueness+existence, edge-endpoint→member resolution, producer-contract tracking, zero-edge SKIP discipline. |
| 2 | Repo-scoped subagents apply the Phase-10 β fan-out/synthesize across the workspace so no single context holds every repo (MREPO-02) | VERIFIED | `harness/agents/orchestrator.md` routing table row + intake clause: "workspace member repo... natural fan-out unit... fan out one read-only worker per member repo". `harness/skills/fan-out-synthesize/SKILL.md` §1/§2/§3: member repo is a valid decompose unit; "never reads a sibling member repo" guarantee stated explicitly. Prose-only (no new skill/command); `EXPECTED_SKILLS`/`EXPECTED_PERSONAS` unchanged. |
| 3 | Cross-repo contract-drift/golden gates extend Phase-6 CI + `contract_drift` across the workspace, failing on drift/golden break spanning a repo boundary (MREPO-03) | VERIFIED | `tools/contract_drift/drift.py::workspace_drift()` iterates each member's OWN baseline via verbatim `run_gate` reuse (no merge) + resolves each edge's contract in its producer; `--workspace` CLI flag. `tools/golden_runner/runner.py::_confine` widened via additive `allowed_roots` (never removes the escape guard) + `workspace_golden_case()`. Separate `workspace` CI job in `.github/workflows/ci.yml` registered in `gate.needs`. |
| 4 | Phase-8 pipeline topology generalizes so a declared edge can cross a repo boundary; a guard proves core→workspace-member single-direction dependency (GEN-04 generalized, MREPO-04); new agents/commands round-trip the emitter to both runtimes | VERIFIED | `split_endpoint("repo:stage")` parses to `(member, stage)`; fixture edge proven cross-member (`from_member != to_member`) in `test_endpoints.py`; core `harness/project.toml` edges proven UNCHANGED (no `:`). `test_core_no_workspace_member_dep.py` (7 tests) scans `git ls-files` under `tools/harness/libs`, resolves forbidden tokens from the live manifest (no hardcoding), key-scoped `workspace.toml` pointer exemption verified against the REAL inline-table edge syntax. Emitter round-trip: `uv run python -m tools.harness_emit` then `git diff --exit-code` over the emit-drift path set exits 0. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `workspace.toml` | Workspace manifest DATA slot, `[[members]]` + `[pipeline].edges` | VERIFIED | Pure data, 2 members, 1 cross-repo edge, header comment names consumers |
| `tools/workspace_config/loader.py` | tomllib passthrough: `load_workspace/members/edges/split_endpoint` | VERIFIED | All 4 exports present, no hardcoded member path (`grep -c 'tests/fixtures/workspace'` = 0) |
| `tools/harness_lint/tests/test_workspace_config.py` | MREPO-01 consistency gate | VERIFIED | 10 tests pass; producer-contract resolution via `rglob`; `KeyError`→assertion fix (WR-02) confirmed present |
| `tests/fixtures/workspace/member-{a,b}/contracts/.hashes/manifest.json` | Pre-baselined producer/consumer manifests | VERIFIED | Both exist, valid JSON, `greeting.schema.json`-keyed |
| `tools/harness_lint/tests/test_core_no_workspace_member_dep.py` | Generalized GEN-04 guard | VERIFIED | 7 tests pass, including real-inline-table-edge-line regression test (WR-01 fix) |
| `tools/workspace_config/tests/test_endpoints.py` | repo:stage parse + cross-boundary proof | VERIFIED | 4 tests pass; cross-member assertion + core-unchanged anti-regression assertion present |
| `tools/contract_drift/drift.py` | `workspace_drift()` + `--workspace` CLI | VERIFIED | Per-member `run_gate` reuse (no merge), edge-contract resolution, `--workspace` flag; CR-01 `_git_show` cwd-mismatch fix present (`_git_show_at` + fallback) |
| `tools/golden_runner/runner.py` | Widened `_confine` (threaded, not removed) + workspace-aware resolution | VERIFIED | `allowed_roots` additive param; negative-control test proves escape guard intact; WR-04 fix (`compare()` routes baseline reads through `_confine`) present |
| `.github/workflows/ci.yml` | Separate `workspace` job in `gate.needs` | VERIFIED | `workspace:` job present, drift+pytest steps, `needs` includes `workspace`; `check-jsonschema --builtin-schema vendor.github-workflows` exits 0 |
| `harness/agents/orchestrator.md` + `.opencode`/`.claude` twins | Member-repo fan-out routing row + intake note | VERIFIED | "member repo" present in all 6 source+emitted files (harness, .opencode, .claude) |
| `harness/skills/fan-out-synthesize/SKILL.md` + twins | Member-repo-as-unit + no-sibling-read guarantee | VERIFIED | Present in all 6 source+emitted files |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `test_workspace_config.py` | `tools.workspace_config` | import load_workspace/members/edges/split_endpoint | WIRED | Confirmed via test run |
| `tools/workspace_config/loader.py` | `workspace.toml` | `tomllib.load` (binary) | WIRED | `uv run pytest tools/workspace_config -q` green |
| `test_core_no_workspace_member_dep.py` | `workspace.toml` member roots | `load_workspace()`/`members()` at runtime | WIRED | No hardcoded fixture path in guard; live negative controls pass |
| `tools/contract_drift/drift.py` | `tools.workspace_config` | `members()`/`edges()` resolve roots at runtime | WIRED | `grep -c 'tests/fixtures/workspace' tools/contract_drift/drift.py` = 0 |
| `.github/workflows/ci.yml` workspace job | `tools.contract_drift.drift --workspace` | CI step | WIRED | Step present, `gate.needs` includes `workspace` |
| `harness/agents/orchestrator.md` | `.opencode/agent/orchestrator.md` + `.claude/agents/orchestrator.md` | `tools.harness_emit` projection | WIRED | Re-emit + `git diff --exit-code` clean (exit 0) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full core suite green | `uv run pytest -q` | 568 passed | PASS |
| Workspace-specific test set green | `uv run pytest tools/workspace_config tools/harness_lint/tests/test_workspace_config.py tools/harness_lint/tests/test_core_no_workspace_member_dep.py tools/golden_runner/tests/test_workspace_golden.py tools/contract_drift/tests/test_workspace_drift.py -q` | 31 passed | PASS |
| CR-01 classification regression (member breaking/non-breaking, not "unknown") | `uv run pytest tools/contract_drift/tests/test_workspace_drift.py -v` | `test_member_breaking_change_is_classified_not_unknown` PASSED, `test_member_non_breaking_change_is_classified_not_unknown` PASSED | PASS |
| WR-01 regression (real inline-table edge line recognized as pointer) | same test module | `test_inline_table_edge_pointer_is_exempt`, `test_real_workspace_edge_line_is_recognized_as_pointer` PASSED | PASS |
| CI workflow structurally valid | `uv run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/ci.yml` | `ok -- validation done` | PASS |
| Emit-drift clean after re-emit | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json` | exit 0 | PASS |
| EXPECTED_SKILLS/PERSONAS unchanged + no model id | `uv run pytest tools/harness_emit tools/harness_lint -q` | 291 passed; no model-id grep hits | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|-------------|-------------|--------|----------|
| MREPO-01 | 11-01-PLAN.md | Workspace model + manifest raising GEN-03 slot pattern one level | SATISFIED | `workspace.toml` + `tools/workspace_config` + consistency gate, all green |
| MREPO-02 | 11-04-PLAN.md | repo-scoped subagents + β fan-out/synthesize across workspace | SATISFIED | Prose wiring in orchestrator + fan-out-synthesize skill, round-tripped to both runtimes |
| MREPO-03 | 11-03-PLAN.md | Cross-repo contract-drift/golden gates extending Phase-6 CI | SATISFIED | `workspace_drift()`, widened `_confine`, separate CI job in `gate.needs` |
| MREPO-04 | 11-02-PLAN.md | Pipeline topology generalized for cross-repo edges + generalized GEN-04 guard | SATISFIED | `split_endpoint`, cross-member fixture edge proof, `test_core_no_workspace_member_dep.py` |

No orphaned requirements — all 4 MREPO IDs from REQUIREMENTS.md are claimed by exactly one plan each and independently verified in the codebase.

### Anti-Patterns Found

None. Scanned all phase-modified files (`tools/workspace_config/**`, `tools/harness_lint/tests/test_workspace_config.py`, `tools/harness_lint/tests/test_core_no_workspace_member_dep.py`, `tools/contract_drift/drift.py`, `tools/golden_runner/runner.py`, `tools/contract_drift/tests/test_workspace_drift.py`, `tools/golden_runner/tests/test_workspace_golden.py`, `tools/workspace_config/tests/test_endpoints.py`, `tools/workspace_config/tests/test_loader.py`, `workspace.toml`, `harness/agents/orchestrator.md`, `harness/skills/fan-out-synthesize/SKILL.md`) for TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER/placeholder/coming-soon/not-yet-implemented markers — zero hits.

### Code Review Fixes Confirmed Holding

The 11-REVIEW.md flagged 1 blocker + 4 warnings + 1 info. All 5 blocker/warning findings were fixed in dedicated commits, and each fix was independently re-verified against the current codebase (not just trusted from commit messages):

| Finding | Commit | Fix Verified |
|---------|--------|--------------|
| CR-01 (blocker): `_git_show` cwd mismatch silently classified all member drift `"unknown"` | `9bbc60c`, `e44601e` | `drift.py::_git_show` now resolves `HEAD:./<rel>` against the member/base root first, falls back to `REPO_ROOT` only when that tree has no such blob. Regression tests `test_member_breaking_change_is_classified_not_unknown` / `test_member_non_breaking_change_is_classified_not_unknown` pass, proving real (not "unknown") classification. |
| WR-01: GEN-04 pointer exemption regex never matched real inline-table edge syntax | `ede905a` | `_WORKSPACE_POINTER_LINE` regex changed to `(?:^\s*|[{,]\s*)(root|from|to|contract)\s*=` with `.search`; new tests `test_inline_table_edge_pointer_is_exempt` + `test_real_workspace_edge_line_is_recognized_as_pointer` (reads the VERBATIM committed `workspace.toml` line) both pass. |
| WR-02: raw `KeyError` instead of clear assertion in consistency-gate test | `bf5f4d3` | `test_workspace_config.py` now asserts `producer_id in by_id` with a descriptive message before indexing. |
| WR-03: unhandled `FileNotFoundError` for a member with no baseline yet | `2a18570` | `workspace_drift()` checks `baseline.exists()` before calling `run_gate`, reports a clean `"missing-baseline"` result instead of crashing; `test_member_missing_baseline_is_reported_not_crash` passes. |
| WR-04: `golden_runner.compare()` bypassed `_confine` for baseline reads | `2986fa1` | `compare()` now routes both `verified_path` reads and `received_path` writes through `_confine(..., allowed_roots)`. |

IN-01 (info: no validation against a degenerate empty-string member root) was not fixed — it remains a low-severity latent gap (no committed member has an empty root; not exploitable in the current fixture). Not a blocker for phase-goal achievement; noted here for visibility.

### Human Verification Required

None. All must-haves are verifiable programmatically via test execution, grep-based structural checks, and CI schema validation.

### Gaps Summary

No gaps. All four success criteria (workspace manifest, repo-scoped fan-out, cross-repo drift/golden gates, generalized pipeline topology + GEN-04 guard) are verified against the actual codebase, not just SUMMARY.md claims. The one code-review blocker and four warnings are all fixed with passing regression tests that specifically target the original failure modes (classification correctness, regex real-syntax matching, crash-safety, confinement trust-boundary consistency). Full suite (568 tests), workspace-specific test set (31 tests), CI workflow schema validation, and emit-drift round-trip all pass clean.

---

_Verified: 2026-07-14T01:28:44Z_
_Verifier: Claude (gsd-verifier)_
