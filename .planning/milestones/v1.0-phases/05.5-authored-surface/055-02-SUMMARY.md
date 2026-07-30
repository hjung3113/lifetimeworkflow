---
phase: 05.5-authored-surface
plan: 02
subsystem: harness
tags: [genericization, de-specialization, contract-first, guard-tokens, template]

# Dependency graph
requires:
  - phase: 05.5-authored-surface (055-01)
    provides: authored assets (domain skills + dotnet-engineer persona) moved to examples/log-parser/; project.toml persona pointer
provides:
  - Domain-neutral surviving core authored surface (data-contracts, new-normalization-rule, orchestrator, explorer, normalize-spec)
  - Core tools/ comment+fixture guard-token sweep — only the sanctioned project.toml persona= line remains
  - Instance docs (examples/log-parser AGENTS.md + README) record the newly-owned skills + .NET persona
affects: [055-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "genericize-body-keep-asset: reword domain examples to the generic contracts/sample instance / abstract placeholders while keeping methodology, order, and gate prose byte-identical"
    - "arbitrary-fixture-rename: JSON-schema property names in drift-classification fixtures are neutral (record_id/rec_id); classification asserts add/remove/rename, not the name"

key-files:
  created: []
  modified:
    - harness/skills/data-contracts/SKILL.md
    - harness/commands/new-normalization-rule.md
    - harness/agents/orchestrator.md
    - harness/agents/explorer.md
    - libs/normalize-spec.md
    - tools/contract_drift/tests/test_classify.py
    - tools/contract_drift/drift.py
    - tools/memory_regen/tests/test_agents_md.py
    - tools/docs_sync/tests/test_docs_sync_determinism.py
    - tools/harness_lint/tests/test_agents.py
    - tools/harness_lint/tests/test_skills.py
    - examples/log-parser/AGENTS.md
    - examples/log-parser/README.md

key-decisions:
  - "Layout block in data-contracts SKILL uses abstract <domain-spec>/<rules>/<reference>/<state> dirs + the generic contracts/sample instance — no examples/ reference introduced, so no new examples/ core token."
  - "new-normalization-rule anchors the generic default contracts/sample/<rule-catalog>; the three mandated steps + failing-stub forcing function + agent: python-engineer kept verbatim."
  - "Swept two extra harness_lint test comments (test_agents.py, test_skills.py) beyond the plan's file list — the Task 2 verify grep excludes only the 055-03 guard file, so those comments had to be neutralized for the plan's own verification to pass."

patterns-established:
  - "Guard-token sweep excludes the 055-03 guard file itself but must clear every other tools/ occurrence including explanatory test comments"

requirements-completed: [GEN-05]

# Metrics
duration: ~14min
completed: 2026-07-09
---

# Phase 5.5 Plan 02: Genericize surviving core prose + sweep tools/ tokens + instance docs Summary

**Purged semiconductor/moved-asset vocabulary from the surviving core authored surface and tools/ comments+fixtures so the only remaining core `examples/` token is the sanctioned project.toml persona= line — the precondition for the 055-03 guard to read 0.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-07-09T05:16Z
- **Completed:** 2026-07-09T05:30Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments
- Genericized the five surviving core authored files (data-contracts SKILL Layout, new-normalization-rule, orchestrator, explorer, normalize-spec) — methodology, mandated order, and drift-gate prose kept byte-identical; only domain examples/moved-asset names reworded.
- Swept every core `tools/` comment + fixture guard-token occurrence (test_classify fixture fields, drift.py docstring, memory_regen/docs_sync/harness_lint comments) with zero assertion/EXPECTED_PAGES/classification-logic changes.
- Updated the instance's own AGENTS.md + README to record the moved `skills/` (normalization-catalog, pipeline-patterns, dotnet-conventions) and `agents/dotnet-engineer` persona, preserving the one-directional dependency invariant.

## Task Commits

1. **Task 1: Genericize surviving core authored surface** - `6407a2f` (refactor)
2. **Task 2: Sweep core comment/fixture guard tokens in tools/** - `0cd3c52` (test)
3. **Task 3: Update instance docs to record moved skills + persona** - `dca815a` (docs)

## Files Created/Modified
- `harness/skills/data-contracts/SKILL.md` - Layout block uses abstract/generic-sample dirs; contract-first + RFC-8785 drift-gate prose verbatim
- `harness/commands/new-normalization-rule.md` - Rule example anchored to the generic contracts/sample catalog; three-step order + failing-stub verbatim; agent: python-engineer unchanged
- `harness/agents/orchestrator.md` - Dropped dotnet-engineer specialist; keeps python-engineer + instance-declared engineers; "polyglot monorepo"
- `harness/agents/explorer.md` - Specialist parenthetical reworded to (python-engineer, or an instance-declared engineer)
- `libs/normalize-spec.md` - References a language-side twin instead of libs/dotnet; §4.3–4.6 rule content intact
- `tools/contract_drift/tests/test_classify.py` - Fixture field equipment_id→record_id, equip_id→rec_id (rename case coherent); comment reworded; assertions unchanged
- `tools/contract_drift/drift.py` - Line-10 docstring reworded off correction-rules.catalog.yaml
- `tools/memory_regen/tests/test_agents_md.py` - libs/dotnet comments → "the instance's language-side package"
- `tools/docs_sync/tests/test_docs_sync_determinism.py` - standard-log/equipment/correction-rules comment mentions neutralized; EXPECTED_PAGES + assertions untouched
- `tools/harness_lint/tests/test_agents.py` - Comment naming dotnet-engineer neutralized (deviation, see below)
- `tools/harness_lint/tests/test_skills.py` - Comment naming normalization-catalog/pipeline-patterns/dotnet-conventions neutralized (deviation, see below)
- `examples/log-parser/AGENTS.md` - Instance layout adds skills/ + agents/ trees, noted as GEN-05-moved instance-owned assets
- `examples/log-parser/README.md` - Layout + prose note the instance now owns its domain skills + .NET persona

## Decisions Made
- Kept the data-contracts Layout block free of any `examples/` reference so no new `examples/` core token is introduced (the only sanctioned one is project.toml persona=).
- Anchored new-normalization-rule to the generic default `contracts/sample/<rule-catalog>` placeholder rather than the moved semiconductor catalog.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Swept two extra harness_lint test comments not in the plan's file list**
- **Found during:** Task 2 (core token sweep)
- **Issue:** Task 2's verify grep (`git grep … -- tools ':!tools/harness_lint/tests/test_core_no_example_dep.py'`) excludes only the 055-03 guard file. Two other tools/ files carried guard tokens in explanatory comments — `tools/harness_lint/tests/test_agents.py:51` (naming `dotnet-engineer`) and `tools/harness_lint/tests/test_skills.py:47` (naming `normalization-catalog`, `pipeline-patterns`, `dotnet-conventions`). Left as-is, the plan's own verification grep (and the 055-03 guard) would still flag them.
- **Fix:** Reworded both comments to the instance-language / domain-skill wording, naming no moved asset. Comments only — no assertion, EXPECTED value, or logic touched.
- **Files modified:** tools/harness_lint/tests/test_agents.py, tools/harness_lint/tests/test_skills.py
- **Verification:** Post-sweep `git grep` over tools/harness/libs (excl guard file) returns only the sanctioned project.toml persona= line; harness_lint suite green apart from the expected transient.
- **Committed in:** 0cd3c52 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for the plan's stated verification (guard reads 0) to hold. Comment-only reword, no logic change, no scope creep.

## Issues Encountered
None — no methodology, order, assertion, or classification logic was changed. The `test_classify` rename case still classifies as breaking; docs_sync EXPECTED_PAGES and determinism snapshots pass unchanged.

## Verification Results

- **tools/contract_drift + tools/memory_regen + tools/docs_sync:** `72 passed` (rename fixture still classifies as rename/breaking; 3 syrupy snapshots pass).
- **Core guard-token git grep** over `tools/ harness/ libs/` (excluding `test_core_no_example_dep.py`): only `harness/project.toml:27: persona = "examples/log-parser/agents/dotnet-engineer.md"` remains — the sanctioned 055-03 transient. All other flagged tokens (`libs/dotnet`, `equipment`, `standard-log`, `correction-rules`, `normalization-catalog`, `pipeline-patterns`, `dotnet-engineer`, `dotnet-conventions`) are gone.
- **Sole remaining core `examples/` reference:** the `harness/project.toml` persona= pointer (confirmed via `git grep 'examples/' -- tools harness libs`).
- **Full non-example suite** (`uv run pytest --ignore=examples`): **349 passed / 1 failed** — the single failure is the SAME expected phase-owned transient `test_core_no_example_dep::test_core_has_no_example_dependency` (project.toml persona pointer; guard exemption lands in 055-03). No new failures introduced.

## Next Phase Readiness
- 055-03 can now extend the GEN-04 guard: every core plane is token-clean except the sanctioned project.toml persona= line, which 055-03 exempts.
- No blockers.

## Self-Check: PASSED

- Files verified present: 055-02-SUMMARY.md, all 13 modified files (spot-checked SKILL.md, README.md).
- Commits verified in git log: 6407a2f, 0cd3c52, dca815a.

---
*Phase: 05.5-authored-surface*
*Completed: 2026-07-09*
