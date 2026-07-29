---
phase: 44-non-goal-surface-removal
plan: 03
subsystem: harness-surface
tags: [CER-08, topology, non-goal-removal, vacuous-gate]
requires:
  - "44-02 (secret_scan whole-surface removal) — HEAD 81f8dea"
provides:
  - "core [pipeline] edge DATA removed; loader.pipeline() retained as a reader mechanism"
  - "/pipeline command and pipeline-map skill removed from both runtime trees"
  - "/component reduced to the ① scaffold mechanism (steps 1–3 + Guard)"
affects:
  - harness/project.toml
  - harness/agents/orchestrator.md
  - tools/harness_lint
  - tools/harness_config
  - tools/workspace_config
  - examples/log-parser/tests
tech-stack:
  added: []
  patterns:
    - "delete the DATA, keep the reader — an instance overlay supplies its own edges"
    - "a gate whose loop body never executes is deleted with its data, not left green"
key-files:
  created: []
  modified:
    - harness/commands/component.md
    - harness/project.toml
    - harness/agents/orchestrator.md
    - harness/skills/brownfield-adoption/SKILL.md
    - tools/harness_lint/caps.py
    - tools/harness_lint/tests/test_pipeline_config.py
    - tools/harness_lint/tests/test_orchestrator_topology.py
    - tools/harness_config/tests/test_loader.py
    - tools/harness_config/tests/test_topology_relationships.py
    - tools/workspace_config/tests/test_endpoints.py
    - examples/log-parser/tests/test_pipeline_topology.py
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/emit-manifest.json
  deleted:
    - harness/commands/pipeline.md
    - harness/skills/pipeline-map/SKILL.md
    - tools/harness_lint/tests/test_conductor_graph_render.py
decisions:
  - "D-11 executed at the measured span :37–EOF, not D-11's stated :37-66 + :68"
  - "loader.pipeline() kept (explicit non-goal) — the instance imports it at collection time"
  - "_CORE_RESOLUTION_DOCS repointed at harness/agents/templates/component-engineer.md, kept non-empty"
metrics:
  duration: ~25m
  completed: 2026-07-29
---

# Phase 44 Plan 03: Non-Goal Topology Surface Removal Summary

Removed `/component`'s topology-registration half, then the core `[pipeline]` edge DATA, the
`/pipeline` command and the `pipeline-map` skill — keeping `loader.pipeline()`, `[[components]]`
and the TOPO-02 relationships slot alive, and deleting the two `harness_lint` edge gates that went
vacuously green rather than red when the data disappeared.

## Commits

| Hash | Message | Shortstat |
|---|---|---|
| `f28a9cd` | `refactor(44-03): remove /component's topology-registration half` | 4 files changed, 215 deletions(-) |
| `18124d3` | `chore(44-03): delete the core [pipeline] data, /pipeline and pipeline-map` | 25 files changed, 112 insertions(+), 1405 deletions(-) |

`18124d3` was amended once (see Deviations) before any downstream work; no red commit was left behind.

## Task 1 — `/component`

`harness/commands/component.md` 78 → **35 lines**: kept `:1-36` (first "Mandated order" + its Guard),
excised `:37`–EOF plus the trailing blank line. Contains no `topology`, `pipeline` or `pipeline-map`
token. Re-emitted both trees + the `.ambr` snapshot. `emit-manifest.json` did **not** move, exactly as
the plan predicted (no artifact added or removed).

Post-commit: `933 passed / 7 snapshots`, examples leg `14 passed`, ruff `PASS — findings went DOWN`,
`git diff --exit-code` clean, `git status --porcelain` empty.

## Task 2 — `[pipeline]` DATA, `/pipeline`, `pipeline-map`

Executed as written. `pipeline()` and the TOPO-02 slot survive; `[[components]]` untouched.

**Post-commit numbers requested by the plan:**

| Measurement | Value |
|---|---|
| `test_pipeline_config.py` pass count | **2 passed** (was 4 — the two edge gates gone, not vacuous) |
| `examples/log-parser/tests` | **14 passed** |
| Core suite | **915 passed / 7 snapshots** (from 933: −4 conductor-render, −2 edge gates, −1 endpoints, −1 relationships, and the emit-count/snapshot rebalance) |
| `emit-manifest.json` row delta | **−4 rows** (`.opencode/command/pipeline.md`, `.claude/commands/pipeline.md`, `.opencode/skill/pipeline-map/SKILL.md`, `.claude/skills/pipeline-map/SKILL.md`); total artifacts 83 → 79 |
| ruff ratchet | `73 findings (baseline 84)` — `E501 84 → 73`, **F401 absent (0)** |
| `effective_relationships(load_project())` | `[]`, no raise |
| `pipeline(load_project()).get("edges", [])` | `[]` |

`git grep -n "/pipeline" -- harness` → nothing. `git grep -n "pipeline-map" -- harness tools` →
**exactly one** line (`tools/harness_lint/caps.py:125`, the retained Phase-8 history), as specified.

Gates on the final commit: full suite green, examples leg green, `harness_emit` + `git diff
--exit-code` clean, `contract_drift` OK, ruff ratchet PASS, `workspace_check` OK,
`git status --porcelain` empty.

## Deviations from Plan

**1. [Rule 1 — authored-prose fix] `caps.py` narrative extension reworded, commit amended**
- **Found during:** Task 2 post-commit criteria check.
- **Issue:** The plan's verification requires `git grep "pipeline-map" -- harness tools` to return
  exactly one line (the Phase-8 history at `caps.py:125`). My first wording of the step-6 narrative
  extension repeated the literal token `pipeline-map`, producing **two** matches. The plan left the
  extension's wording to the executor; the criterion was not wrong, my prose was.
- **Fix:** Reworded the extension to refer to "the Phase-8 topology-trace skill named above" instead
  of repeating the token; `git commit --amend`. The history line at `:125` was **not** deleted.
- **Files modified:** `tools/harness_lint/caps.py`
- **Commit:** `18124d3` (amended)

**2. [Rule 2 — stale-claim cleanup] Two module docstrings narrowed alongside their deleted tests**
- `tools/workspace_config/tests/test_endpoints.py` — its module docstring asserted an
  anti-regression invariant over core `[pipeline]` edges whose only test was deleted in step 7.
- `tools/harness_lint/tests/test_orchestrator_topology.py` — its docstring claimed the routing
  section "references `/pipeline`", the assertion step 6 removed.
- Both are prose-only and GEN-04-token-free. Left a claimed-but-unenforced control in place would be
  the exact defect this plan removes.

**3. [Rule 3 — line-length] One reflow in the instance test**
Rewrapped a docstring line in `examples/log-parser/tests/test_pipeline_topology.py` that my edit
pushed over the E501 limit.

## Criteria that did not hold

None, after the amend in Deviation 1. Every measured number in the plan matched:
`component.md` ≤ 40 lines (35), `test_pipeline_config.py` 4 → 2, `F401` stayed at 0 after the two
prescribed import cleanups, ruff total fell below 84 (73), the manifest self-pruned without hand
editing, and the three `adoption_scan` tests were red between `git rm` and `git commit` and cleared
on commit — exactly as briefed, not repaired.

## Things the plan did not anticipate

1. **`tools/harness_emit/tests/test_coexist.py:3`** — the *module* docstring carries a fifth stale
   command count ("writes its 20 harness commands"), outside the four sites the plan enumerates.
   Checked git history: plan 01 (`374f991`) also left it untouched when it took the count 21 → 20, so
   the line has been stale since an earlier phase and is unasserted. **Left as-is** — following the
   plan literally. Worth a one-line fix in a later phase.
2. **`tools/harness_lint/tests/test_pipeline_config.py`** retains `_REPO_ROOT` / `_CONTRACTS_DIR`,
   which only `test_edge_contracts_have_a_tracked_schema` used. They are module-level constants, so
   ruff does not flag them (F401 covers imports only) and the plan's measured `F401 0 → 3` implies the
   replay kept them too. Removing them would have orphaned the `pathlib.Path` import and *created* an
   F401. **Left as-is** deliberately.
3. **`harness/agents/templates/component-engineer.md:14`** still names `[pipeline]` when describing
   `<STAGE>`. That is not a corpse pointer: the slot remains valid for an instance overlay (which is
   why `pipeline()` survives) — only the *core default's* edge data is gone. Untouched.
4. **`harness/project.toml`'s TOPO-02 comment block** retains two `[pipeline]` mentions describing the
   "legacy linear model" it coexists with. These are comments (the verify block's
   `grep -v '^#'` excludes them) and are accurate history. Untouched.

## Self-Check: PASSED

- `harness/commands/pipeline.md`, `harness/skills/pipeline-map/`,
  `tools/harness_lint/tests/test_conductor_graph_render.py` — confirmed absent.
- `def pipeline` present in `tools/harness_config/loader.py` — confirmed.
- No uncommented `[pipeline]` table in `harness/project.toml` — confirmed.
- Commits `f28a9cd` and `18124d3` present in `git log`.
- `git status --porcelain` empty at HEAD.
