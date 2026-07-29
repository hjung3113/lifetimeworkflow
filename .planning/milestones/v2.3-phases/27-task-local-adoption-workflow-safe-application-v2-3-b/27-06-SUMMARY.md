---
phase: 27-task-local-adoption-workflow-safe-application-v2-3-b
plan: 06
subsystem: harness-emitter
tags: [cli, argparse, jsonschema, harness-command, harness-skill, brownfield-adoption, exit-code-contract]

requires:
  - phase: 27-01
    provides: "tools/adoption_apply package scaffold, __main__.py deferring to cli.py, batch.py CAS-bound batch layout"
  - phase: 27-03
    provides: "apply.py atomic/collision-safe/idempotent writer + refuse_if_outside_root/refuse_if_constitution structural refusals"
  - phase: 27-04
    provides: "approval.py refuse-by-default AdoptionApprovalRefused promotion gate bound to (draft_hash, task_revision, git_ref)"
provides:
  - "tools/adoption_apply/cli.py — the draft/apply/promote argparse dispatcher composing batch.py/apply.py/approval.py; python -m tools.adoption_apply now resolves"
  - "harness/commands/adopt.md — the single thin /adopt command (agent: orchestrator, subtask: true) wrapping discover/draft/apply/promote"
  - "harness/skills/brownfield-adoption/SKILL.md — the discover to draft to human-review to promote to apply runbook skill"
  - "EXPECTED_SKILLS widened to 12 entries; emitted command count bumped 23 -> 24"
  - "Both .opencode/ and .claude/ runtime trees carrying /adopt + brownfield-adoption byte-identically (SC-4)"
affects: [phase-27-closeout, future-adoption-workflow-plans]

tech-stack:
  added: []
  patterns:
    - "CLI subcommand composition: argparse subparsers with set_defaults(func=...), each handler importing and calling only the already-audited batch/apply/approval functions, never re-implementing their logic"
    - "Refuse-by-default exit-code contract: catch the domain refusal exception at the CLI boundary, print, return 3 — proven at both a direct main() call and an OS-level subprocess.run boundary"
    - "CR-01 apply-time content sourcing: create/marker-merge payload bytes for adoption apply come from THIS harness checkout's own file content at the destination, never read back from the scanned target"

key-files:
  created:
    - tools/adoption_apply/cli.py
    - tools/adoption_apply/tests/test_cli.py
    - harness/commands/adopt.md
    - harness/skills/brownfield-adoption/SKILL.md
  modified:
    - tools/harness_lint/caps.py
    - tools/harness_emit/tests/test_coexist.py
    - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
    - .opencode/command/adopt.md (new, emitted)
    - .claude/commands/adopt.md (new, emitted)
    - .opencode/skill/brownfield-adoption/SKILL.md (new, emitted)
    - .claude/skills/brownfield-adoption/SKILL.md (new, emitted)
    - AGENTS.md (HARNESS-MANAGED block regenerated)
    - tools/harness_emit/emit-manifest.json (rebaselined)

key-decisions:
  - "cli.py's apply subcommand sources create/marker-merge payload bytes from THIS harness checkout's own content at each destination (never from the scanned target) — the CR-01 'proposed content is what the harness template would install' contract destinations.py already encodes for hash comparison, extended here to actual file content for the write path."
  - "draft subcommand validates inventory/plan/manifest against their schemas before writing (Rule 2: matches the Shared Pattern 'JSON Schema validation before use' already established by adoption_scan.cli.main and approval.py, even though the plan's <behavior> block did not explicitly require it)."
  - "--decisions is an optional CLI flag (default None) rather than argparse-required — a promote call with no decisions still refuses via approval.promote's own empty-decisions check, so CLI-level enforcement would be redundant."
  - "New skill's anti-sprawl disposition answered in writing per skill-creator Step 0: none of the 11 existing skills own the discover-to-apply brownfield lifecycle; data-contracts/gate-model are about contracts already known to exist, not discovering an unknown target's contracts."

patterns-established:
  - "TDD gate sequence for a composition-only CLI module: RED (test_cli.py importing a nonexistent cli.py, confirmed ImportError) -> GREEN (cli.py implemented, all 5 tests pass) as two separate commits."

requirements-completed: [ADOPT-07]

duration: 55min
completed: 2026-07-21
---

# Phase 27 Plan 06: /adopt Command + brownfield-adoption Skill + cli.py Composition Seam Summary

**Authored `tools/adoption_apply/cli.py` — the missing draft/apply/promote dispatcher that closes the composition gap plan-checker flagged (`python -m tools.adoption_apply` previously raised `ImportError`) — then the single `/adopt` command and `brownfield-adoption` skill, round-tripped byte-identically to both `.opencode/` and `.claude/`, closing Phase 27's gate (1096 tests green, contract-drift clean, GEN-04 clean, `uv.lock` unchanged).**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-07-21
- **Tasks:** 3 (Task 2 is `tdd="true"`: RED + GREEN as two commits)
- **Files modified:** 12 source files + 4 emitted runtime files + 2 test-infra files

## Accomplishments

- `tools/adoption_apply/cli.py`'s `main()` resolves `python -m tools.adoption_apply {draft,apply,promote}` — real, end-to-end filesystem effects (`draft` writes `inventory.json`/`plan.json`/`manifest.json` under a task-local batch root; `apply` composes `batch` -> `apply` and lands at least one `create`-disposition destination on disk), not merely an import check.
- `promote`'s `AdoptionApprovalRefused` converts to CLI exit code 3 at the process boundary, proven by BOTH a direct `main()` call and an OS-level `subprocess.run([sys.executable, "-m", "tools.adoption_apply", "promote", ...])` assertion (mirrors `golden_runner/approve.py`'s refuse-by-default idiom exactly, D-05).
- `/adopt` (one command, `agent: orchestrator`) and `brownfield-adoption` (one skill) authored — no new persona, no model identifier, structurally verified by `test_commands.py`/`test_skills.py` (147 passed) and a `grep` for model-name tokens.
- Both runtime trees (`.opencode/`, `.claude/`) re-emitted from the widened `harness/` source and confirmed byte-identical on a SECOND re-emit (`git diff --exit-code -- .opencode .claude` clean) — SC-4.
- Full phase gate green: `uv run pytest -q` 1096 passed (up from 1082 pre-plan baseline), `contract_drift.drift` clean, GEN-04 (`test_core_no_example_dep.py`) 18 passed, `uv sync --all-packages && git diff --exit-code uv.lock` clean, derived-plane freshness (`docs_sync` + `memory_regen.contracts_index`) clean.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author /adopt + brownfield-adoption skill** - `aacae02` (feat)
2. **Task 2 RED: add failing test_cli.py** - `da8e427` (test)
2. **Task 2 GREEN: implement cli.py** - `754ea69` (feat)
3. **Task 3: Emit round-trip + coexist count bump + GEN-04 + full phase gate** - `bf0c4c3` (feat)

_TDD task (Task 2) produced two commits (test -> feat); no refactor commit was needed._

## Files Created/Modified

- `tools/adoption_apply/cli.py` - `main()` argparse dispatcher; `_cmd_draft`/`_cmd_apply`/`_cmd_promote` compose `batch.create_or_resume_batch`, `apply.apply_manifest`/`refuse_if_outside_root`, and `approval.promote`
- `tools/adoption_apply/tests/test_cli.py` - 5 tests: exit-3 direct + subprocess, positive-control promote, draft artifact-root confinement, draft/apply end-to-end
- `harness/commands/adopt.md` - thin macro, 4 sub-verbs (`discover`/`draft`/`apply`/`promote`), fixed `python -m` argv forms only
- `harness/skills/brownfield-adoption/SKILL.md` - 5-stage lifecycle runbook with the anti-sprawl disposition cited in its opening paragraph
- `tools/harness_lint/caps.py` - `EXPECTED_SKILLS` widened by exactly one entry
- `tools/harness_emit/tests/test_coexist.py` - command-count assertion bumped 23 -> 24, docstring narrative extended
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` - pinned projection snapshot refreshed for the new command + skill
- `.opencode/command/adopt.md`, `.claude/commands/adopt.md`, `.opencode/skill/brownfield-adoption/SKILL.md`, `.claude/skills/brownfield-adoption/SKILL.md` - newly emitted, byte-identical dual-runtime projections
- `AGENTS.md`, `tools/harness_emit/emit-manifest.json` - HARNESS-MANAGED block and owned-path manifest regenerated

## Decisions Made

- `cli.py apply`'s payload/block-body content for `create`/`marker-merge` destinations is sourced from THIS harness checkout's own files at the destination path — not from the scanned target — extending `destinations.py`'s CR-01 hash-comparison contract ("proposed content is what the harness template would install") to the actual write path. This was necessary because `apply.apply_manifest`'s signature takes `payloads`/`block_bodies` dicts, not a `batch_dir` kwarg (the plan's `<behavior>` block's `apply.apply_manifest(manifest, target_root, batch_dir=batch_root)` sketch predates the final `apply.py` signature; the real signature was read and honored instead).
- Added JSON Schema validation of `inventory`/`plan`/`manifest` before writing in `draft` (Rule 2) — not explicitly spelled out in the plan's `<behavior>` block, but matches the Shared Pattern PATTERNS.md names ("JSON Schema validation before use") and `tools.adoption_scan.cli.main`'s own precedent for the identical three documents.
- `--decisions` is optional (not `argparse`-`required=True`) on `promote`: a call with no decisions naturally refuses via `approval.promote`'s own empty-decisions check, so a CLI-level required flag would only duplicate that refusal path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Frontmatter description arrow characters tripped the XML-tag-char guard**
- **Found during:** Task 1 (`brownfield-adoption/SKILL.md` authoring)
- **Issue:** The skill description used `->` arrows (`discover -> draft -> ...`) in its routing description; `test_skills.py::test_description_within_caps_and_routes` rejects any `<`/`>` character in a description, and `->` contains `>`.
- **Fix:** Rewrote the phrase without arrows (`the discover, draft, human review, promote, apply lifecycle`).
- **Files modified:** `harness/skills/brownfield-adoption/SKILL.md`
- **Verification:** `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_skills.py -q` — 147 passed
- **Committed in:** `aacae02` (Task 1 commit)

**2. [Rule 1 - Bug] Snapshot test failure after adding the new command/skill**
- **Found during:** Task 3, running `uv run pytest tools/harness_emit -q` before the emit
- **Issue:** `test_projected_tree_matches_committed_snapshot` (a `syrupy` `.ambr` snapshot) failed because the projected source now includes `/adopt` and `brownfield-adoption`, which the pinned snapshot predates.
- **Fix:** Ran `uv run pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update -q` to refresh the pinned snapshot, then re-ran the full `tools/harness_emit` suite to confirm all 47 tests green before touching the committed `.opencode`/`.claude` trees (gate-theft-avoidance ordering).
- **Files modified:** `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr`
- **Verification:** `uv run pytest tools/harness_emit -q` — 47 passed
- **Committed in:** `bf0c4c3` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — structural gate fixes required to keep the plan's own acceptance criteria green, no scope creep beyond what the plan's tasks already required).
**Impact on plan:** Neither deviation altered scope; both were required corrections surfaced by the plan's own verification commands.

## Issues Encountered

None beyond the two auto-fixed items above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 27 (task-local adoption workflow + safe application, v2.3 B) is fully closed: ADOPT-04 through ADOPT-07 all satisfied, `/adopt` is a real, human-gated, dual-runtime-emitted entry point over the deterministic `tools.adoption_scan`/`tools.adoption_apply` pipeline.
- Full suite (1096 tests), contract-drift, GEN-04, and `uv.lock` stability are all green — no known blockers for phase closeout or the next milestone.
- `harness/skills/brownfield-adoption/SKILL.md` and `harness/commands/adopt.md` are ready references for any future plan that extends the adoption workflow (e.g. a `discover` sub-verb wired directly into `/adopt` rather than delegated to `python -m tools.adoption_scan`, should that consolidation ever be desired — no such plan exists yet).

---
*Phase: 27-task-local-adoption-workflow-safe-application-v2-3-b*
*Completed: 2026-07-21*

## Self-Check: PASSED

All created files verified present on disk (cli.py, test_cli.py, adopt.md command, brownfield-adoption
SKILL.md, all 4 emitted runtime copies, this SUMMARY.md). All 5 task/summary commit hashes
(`aacae02`, `da8e427`, `754ea69`, `bf0c4c3`, `c2b2335`) verified present in `git log --oneline --all`.
