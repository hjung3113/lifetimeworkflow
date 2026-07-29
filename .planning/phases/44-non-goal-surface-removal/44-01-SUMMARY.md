---
phase: 44-non-goal-surface-removal
plan: 01
subsystem: harness-surface
tags: [cer-08, deletion, contracts, emitter]
requires: []
provides:
  - "20 commands / 11 skills as the live harness surface"
  - "contracts/.hashes/manifest.json rebaselined to 6 entries"
  - "DATA_CONTRACT_PATHS as an empty retained seam"
affects:
  - tools/harness_lint/caps.py
  - tools/harness_emit/emit-manifest.json
  - contracts/.hashes/manifest.json
tech-stack:
  added: []
  patterns: [source-first-emit, git-rm-then-rm-rf-bytecode-residue]
key-files:
  created: []
  modified:
    - tools/harness_lint/caps.py
    - tools/harness_emit/tests/test_coexist.py
    - tools/contract_hash/hash.py
    - tools/docs_sync/tests/test_docs_sync_determinism.py
  deleted:
    - tools/memory_ui/
    - tools/strangler_guard/
    - harness/commands/strangler-step.md
    - harness/skills/gate-model/
    - contracts/harness/security/
    - contracts/harness/task-control/
    - docs/reference/deny-domains.md
decisions: []
metrics:
  commits: 2
  files-changed: 65
  insertions: 55
  deletions: 3135
  completed: 2026-07-29
---

# Phase 44 Plan 01: Non-Goal Surface Removal (Wave 1) Summary

Two CER-08 deletion commits landed exactly as planned — the orphan tool packages plus their command
and skill surface, then the two non-goal contracts plus every derived artifact that rendered them —
each ending green with an empty `git status --porcelain`.

## Commits

| Hash | Message | `--shortstat` |
|------|---------|---------------|
| `374f991` | `chore(44): delete memory_ui, strangler_guard, /strangler-step, gate-model` | 50 files changed, 37 insertions(+), 2732 deletions(-) |
| `1e79bf6` | `chore(44): delete deny-domains + gate-registry contracts` | 15 files changed, 18 insertions(+), 403 deletions(-) |

Phase-to-date total for D-21: **65 files changed, 55 insertions(+), 3135 deletions(-)**.

### `emit-manifest.json` row-delta

| Commit | Rows added | Rows removed |
|--------|-----------|--------------|
| `374f991` | 0 | **4** — `.claude/commands/strangler-step.md`, `.claude/skills/gate-model/SKILL.md`, `.opencode/command/strangler-step.md`, `.opencode/skill/gate-model/SKILL.md` |
| `1e79bf6` | 0 | 0 — file unchanged, not in the pathspec (as the plan predicted) |

### Commit 1 — `git diff --stat`

50 files. Deletions: `tools/memory_ui/` (13 files, ~1855 LOC), `tools/strangler_guard/` (7 files,
~255 LOC), `harness/commands/strangler-step.md` + its two emitted twins,
`harness/skills/gate-model/SKILL.md` + its two emitted twins. Modifications: the six surviving
`harness/**` pointers (`agents/orchestrator.md`, `commands/{orient,review,verify-work}.md`,
`skills/{brownfield-adoption,two-plane-memory}/SKILL.md`) and their emitted twins,
`AGENTS.md` (HARNESS-MANAGED block, 4 lines), `tools/harness_lint/caps.py`,
`tools/harness_emit/tests/test_coexist.py`, `test_emit_determinism.ambr` (−200),
`tools/harness_emit/emit-manifest.json` (−4), `uv.lock` (−12).

### Commit 2 — `git diff --stat`

15 files. Deletions: `contracts/harness/security/deny-domains.{json,schema.json}` (−305),
`contracts/harness/task-control/gate-registry.json` (−20), `docs/reference/deny-domains.md` (−14,
pruned by `docs_sync`, never hand-deleted). Modifications: `contracts/.hashes/manifest.json` (−3
entries, 9 → 6), `.memory/derived/contracts-index.md`, `tools/contract_hash/hash.py`,
`tools/contract_hash/tests/test_hash.py` (−21, the vacuous test deleted),
`tools/docs_sync/tests/test_docs_sync_determinism.py` (−1), both regenerated `.ambr` snapshots, and
the four `tools/adoption_scan/**` provenance-docstring sites.

## Acceptance criteria — all held

| Criterion | Observed |
|-----------|----------|
| `uv run pytest -q` | C1: **951 passed, 7 snapshots**. C2: **950 passed, 7 snapshots**. (983 → 951 is the 32 tests deleted with `memory_ui`/`strangler_guard`; 951 → 950 is the vacuous `test_hash.py` test.) |
| `uv run pytest examples/log-parser/tests -q` | 14 passed, both commits |
| `python -m tools.harness_emit && git diff --exit-code` | exit 0, both commits |
| `python -m tools.contract_drift.drift` | `OK — live manifest matches the committed baseline`, exit 0 |
| `python -m tools.ruff_baseline` | `80 findings (baseline 84)` — `improved E501: baseline 84 -> found 80`, exit 0. Exactly the measured shrink. **`--update` not run.** |
| `tools/harness_lint/workspace_check.py` | `OK — every globbed Python member has a pyproject.toml` |
| `git status --porcelain` | empty after each commit |
| Task 1 absence gate (tracked-emptiness + `test ! -e` + `! git grep strangler`) | PASS |
| Task 2 absence gates (`test ! -e` ×3, manifest == 6, `! git grep gate-registry -- tools harness contracts`) | PASS — `manifest entries: 6` |
| `adoption_scan` 20 redaction/exclusion tests unchanged | 49 passed across `test_dispositions.py` + `test_scan_exclusions.py` |

## Deviations from Plan

**None of substance.** Three notes, all within the plan's own instructions:

1. **`uv.lock` self-refreshed before the explicit `uv lock`.** Immediately after `git rm -r`,
   `git status` already showed ` M uv.lock` with exactly the two workspace members removed. The
   plan's mandated `uv lock && uv sync --all-packages` was still run; it was a no-op
   (`Resolved 50 packages`, `Checked 30 packages`). No behavioural difference.
2. **`CLAUDE.md` was in Task 1's pathspec but the emitter did not modify it.** Step 6 lists it; a
   pathspec entry for an unmodified file is inert. Not a defect, but worth recording so a future
   replay does not go looking for a missing `CLAUDE.md` hunk.
3. **`scan.py` / `__init__.py` provenance wording was tightened once after the first rewrite.** The
   first rewrite used "task-control **gate registry** contract", which still matched the plan's
   loose sweep regex `gate.registry` (the `.` matching the space). Reworded to "task-control
   registry contract" so the `<verification>` sweep now returns **only** `README.ko.md:79` and
   `docs/adr/0012-…:114`. Both are legitimate history; the ADR is append-only by rule.

## Things the plan did not anticipate

- **`README.ko.md:79`** carries `harness/task-control/  # gate-registry` inside a directory-tree
  listing that is now stale (`contracts/harness/task-control/` no longer exists). It is not in this
  plan's `files_modified`, is outside the Task 2 gate scope (`tools harness contracts`), and root
  prose reconciliation is Phase 45's CER-11 — so it was **left untouched** and is flagged here for
  Phase 45 rather than fixed ad hoc.
- **The three documented intra-commit `adoption_scan` reds were never observed**, because the full
  suite was only run *after* each commit (as the plan's own step-7 wording directs). Nothing was
  "repaired". Recording this so a later replay does not read their absence as a discrepancy.
- **`harness/agents/templates/*.md`** were grep-confirmed clean of both artifacts, as the plan
  predicted — no work there.

## Known Stubs

None.

## Threat Flags

None — this plan removes surface only. T-44-01 mitigated (`uv lock` + `uv sync --all-packages` ran
before the commit; `workspace_check.py` green). T-44-02 mitigated (every baseline regenerated by its
owning tool; no hand-edit). T-44-21 mitigated (`emit-manifest.json` in Commit 1's pathspec;
`git status --porcelain` empty).

## Self-Check: PASSED

- `374f991` and `1e79bf6` both present in `git log`.
- `contracts/.hashes/manifest.json` exists with 6 entries.
- `tools/memory_ui`, `tools/strangler_guard`, `harness/commands/strangler-step.md`,
  `harness/skills/gate-model`, `contracts/harness/security`, `contracts/harness/task-control`,
  `docs/reference/deny-domains.md` all confirmed absent from both the index and the filesystem.
