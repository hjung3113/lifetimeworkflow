---
phase: 11-multi-repo-workspace-v2-0
plan: 04
subsystem: workspace-fanout-wiring
tags: [MREPO-02, workspace, fan-out-synthesize, prose-wiring, emit-round-trip, phase-closeout]

# Dependency graph
requires:
  - phase: 11-01
    provides: "workspace.toml manifest + tools.workspace_config loader (members/edges/split_endpoint)"
  - phase: 11-02
    provides: "generalized GEN-04 guard (core → workspace-member) — prose carries no member-root path token"
  - phase: 11-03
    provides: "cross-repo drift + workspace-aware golden + separate workspace CI job"
  - phase: 10-01
    provides: "fan-out-synthesize skill substrate (decompose → dispatch read-only explorer → synthesize)"
provides:
  - "MREPO-02 prose wiring: orchestrator routes workspace-wide analysis by fanning out one read-only worker per member repo"
  - "fan-out-synthesize skill documents member-repo-as-unit + no-sibling-read guarantee (T-11-10)"
  - "emitter round-trip of both edited surfaces to .opencode/ + .claude/ (byte-identical, no new surface)"
affects:
  - "Phase 11 CLOSED OUT — full core suite + emit-drift + GEN-04 twins green"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PROSE wiring reuses the Phase-10 fan-out substrate (a member repo = the skill's existing 'one per unit' fan-out unit) — NO new skill/command/persona"
    - "Content edit to an existing emitted surface round-trips the Phase-7 emitter byte-identical; the AGENTS.md sorted index is UNCHANGED because no surface was added"
    - "Projected-tree emit snapshot (.ambr) regenerated for the content edit — count discipline holds (EXPECTED_SKILLS=11, EXPECTED_PERSONAS=5)"

key-files:
  created:
    - .planning/phases/11-multi-repo-workspace-v2-0/11-04-SUMMARY.md
  modified:
    - harness/agents/orchestrator.md
    - harness/skills/fan-out-synthesize/SKILL.md
    - .opencode/agent/orchestrator.md
    - .opencode/skill/fan-out-synthesize/SKILL.md
    - .claude/agents/orchestrator.md
    - .claude/skills/fan-out-synthesize/SKILL.md
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr

key-decisions:
  - "MREPO-02 satisfied by PROSE wiring only (Pitfall 4) — a new skill would force an EXPECTED_SKILLS bump + full re-emit fixture churn; a member repo is already exactly the skill's 'one per directory/subsystem/contract/question' fan-out unit"
  - "No member-root path literal in either source (generic 'workspace member repo', workspace.toml by name only) so the 11-02 GEN-04 twin stays green"
  - "The no-sibling-read guarantee (each per-repo worker read-only, never reads a sibling member) is the MREPO-02 core context-economy invariant — placed in fan-out §2 DISPATCH (mitigates T-11-10)"
  - "AGENTS.md managed block NOT regenerated: the emitter's index is agent/command/skill NAMES (sorted) — a content edit does not move it; this is expected, not a skipped step"

requirements-completed: [MREPO-02]

# Metrics
metrics:
  duration: 8min
  tasks: 2
  files: 7
  completed: 2026-07-14
---

# Phase 11 Plan 04: Workspace Fan-out Prose Wiring + Emitter Round-Trip (Phase Closeout) Summary

**Workspace-wide analysis is prose-wired to fan out one read-only worker per member repo with
workspace-level synthesis (no single context holds every repo), reusing the Phase-10 fan-out
substrate with NO new surface, and round-tripped byte-identical to both runtimes — closing out
Phase 11.**

## What Was Built

- **Orchestrator wiring** (`harness/agents/orchestrator.md`): one new routing-table row —
  "Analyze a multi-repo workspace / cover several member repos" → "(self) fan out, one read-only
  worker per member repo" → `fan-out-synthesize` skill / `/fan-out-synthesize`; plus an extended
  "Budget the context" intake step naming a **workspace member repo** (declared in `workspace.toml`)
  as a natural fan-out unit so per-repo workers absorb the reading and the conductor synthesizes at
  the workspace level.
- **fan-out-synthesize skill** (`harness/skills/fan-out-synthesize/SKILL.md`): §1 DECOMPOSE now states
  a member repo is a valid disjoint unit; §2 DISPATCH states the guarantee that each per-repo worker
  is read-only and **never reads a sibling member repo** — the invariant that keeps any single context
  from holding every repo at once (MREPO-02's core guarantee, mitigating T-11-10).
- **Emitter round-trip**: `python -m tools.harness_emit` projected both edited surfaces to
  `.opencode/agent/orchestrator.md`, `.opencode/skill/fan-out-synthesize/SKILL.md`,
  `.claude/agents/orchestrator.md`, `.claude/skills/fan-out-synthesize/SKILL.md` (byte-identical),
  and the projected-tree emit snapshot was regenerated for the content edit. No emitter code change,
  no `caps.py` count change, no model id.

## Verification

- **Task 1 grep gates:** `grep -c 'member repo'` → 3 (orchestrator) / 4 (skill), both ≥ 1;
  `grep -c 'tests/fixtures/workspace'` → 0 in both source files (GEN-04-clean prose).
- `uv run pytest tools/harness_lint -q` → **242 passed** (structural + anti-sprawl + GEN-04 twins, no count change).
- `uv run python -m tools.harness_emit` then `git diff --exit-code` over the emit-drift path set → **clean** post-commit (re-emit byte-identical).
- Both runtime orchestrator twins + both fan-out SKILL twins contain "member repo"; no real model id in any regenerated artifact.
- `uv run pytest tools/harness_emit -q` → **47 passed / 1 snapshot** (EXPECTED_SKILLS still 11, EXPECTED_PERSONAS still 5).
- **Phase closeout gate:** `uv run pytest -q` full core suite → **563 passed / 4 snapshots** (all four MREPO gates + existing suite, no regression).
- GEN-04 twins (`test_core_no_workspace_member_dep.py` + `test_core_no_example_dep.py`) → **22 passed**.

## Deviations from Plan

### Documented Adjustments

**1. [Rule 3 - Blocking] Regenerated the projected-tree emit snapshot**
- **Found during:** Task 2 (`test_projected_tree_matches_committed_snapshot` failed after the round-trip).
- **Issue:** The committed syrupy `.ambr` pins the rendered agent/skill bodies; editing the orchestrator + fan-out bodies is a legitimate content change the snapshot must absorb.
- **Fix:** `pytest ... --snapshot-update`; verified the diff is scoped ONLY to the orchestrator + fan-out-synthesize regions (both runtime renderings), with no count/surface change. Anticipated by the plan ("verify fixture twins/.ambr snapshots are unchanged except for the two projected surfaces").
- **Files modified:** `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
- **Commit:** 07c91c8

**2. AGENTS.md managed block NOT regenerated (plan frontmatter listed it as modified)**
- The emitter's `AGENTS.md` managed block is a sorted agent/command/skill NAME index. This plan is a prose content edit to two existing surfaces — no surface added — so the index does not move and the emitter left `AGENTS.md` byte-identical. Listing it in the plan's `files_modified` was a conservative over-estimate; the emit-drift gate confirms `AGENTS.md` is clean.

## Known Stubs

None — the wiring is live prose routed through the existing fan-out substrate; both runtime twins are byte-identical projections verified by the emit-drift gate.

## Threat Flags

None — no new security surface. T-11-10 (worker reading a sibling member) is mitigated by the skill's no-sibling-read prose; T-11-11 (hand-edited generated drift) is enforced by the byte-identical re-emit; T-11-12 (model id leak) verified absent post-emit; T-11-SC (package installs) N/A — prose edit + deterministic re-emit only.

## Self-Check: PASSED

- SUMMARY.md present on disk.
- Both task commits present in git history (05688fb, 07c91c8).
- Emit-drift clean, full core suite 563 passed, GEN-04 twins green.

---
*Phase: 11-multi-repo-workspace-v2-0 — CLOSED OUT (4/4 plans)*
*Completed: 2026-07-14*
