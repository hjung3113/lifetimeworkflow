---
phase: 07-single-source-dual-runtime-emitter
plan: 04
subsystem: infra
tags: [emitter, managed-block, merge, idempotent, agents-md, claude-md, drift-gate, regime-b]

# Dependency graph
requires:
  - phase: 07-single-source-dual-runtime-emitter
    provides: "emit spine (generate.emit/_confine/HarnessEmitError), ownership manifest, emit-drift CI diff set (07-01)"
  - phase: 07-single-source-dual-runtime-emitter
    provides: "serialization discipline + opencode.json config emit (07-03)"
provides:
  - "tools/harness_emit/merge.py — idempotent HTML-comment managed-block splice for shared Markdown (Regime B-md)"
  - "AGENTS.md + CLAUDE.md carry a single HARNESS-MANAGED pointer block; all GSD/human content outside preserved verbatim"
  - "generate.emit() Regime-B merge step (read→splice→write, never full-write; not manifest-owned)"
affects: [settings.json signature merge (07-05), emit-drift CI gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regime B managed-block merge: two-marker string splice, no external lib; replace-inside / preserve-outside / append-once-idempotent"
    - "Shared human/GSD files are MERGE targets (Regime B), never whole-file manifest-owned (Regime A)"
    - "Deterministic pointer-only block body (sorted surface index, no timestamps) keeps the drift gate clean on co-owned files"

key-files:
  created:
    - tools/harness_emit/merge.py
    - tools/harness_emit/tests/test_merge_idempotent.py
  modified:
    - tools/harness_emit/generate.py
    - AGENTS.md
    - CLAUDE.md

key-decisions:
  - "splice_managed_block fails loud (ValueError) on a single/malformed marker rather than guessing — never corrupt a shared file"
  - "Managed block appended at file tail (after the GSD profile-end / nearest-wins rules) so all GSD-managed + human prose sits OUTSIDE the fence"
  - "AGENTS.md/CLAUDE.md deliberately kept OUT of emit-manifest.json (Regime B merge, not Regime A own)"

patterns-established:
  - "_merge_shared_markdown(root, agent/command/skill names) runs after all Regime-A writes; .exists() guard keeps tmp-root emit tests (no AGENTS.md/CLAUDE.md) green"

requirements-completed: [EMIT-02]

# Metrics
duration: 9min
completed: 2026-07-12
---

# Phase 7 Plan 04: Shared-File Managed-Block Merge Summary

**Root `AGENTS.md` and `CLAUDE.md` now carry a single idempotent `HARNESS-MANAGED` pointer block spliced in by `tools.harness_emit` — the GSD `## Project`/Developer-Profile blocks, nearest-wins rules, and human prose OUTSIDE the fence are preserved byte-for-byte, and re-emit is byte-identical (the drift gate stays green on these co-owned files).**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-12T08:12:57Z
- **Completed:** 2026-07-12T08:22:00Z
- **Tasks:** 2
- **Files modified:** 5 (2 created + 3 modified)

## Accomplishments
- Built `tools/harness_emit/merge.py` `splice_managed_block(existing_text, block_body)`: a hand-rolled two-marker string splice — replaces ONLY between `<!-- BEGIN HARNESS-MANAGED … -->` / `<!-- END HARNESS-MANAGED -->`, preserves before/after verbatim; appends the fenced block exactly once when markers are absent; normalizes to LF / no-BOM / single trailing newline; fails loud (`ValueError`) on a single (malformed) marker.
- Wrote `test_merge_idempotent.py` (6 assertions): preserve-outside, replace-inside, second-run byte-identical, append-once-when-absent, inside-edit-overwritten-while-outside-survives, and LF/no-BOM/single-trailing-newline + malformed-single-marker fail-loud.
- Wired `generate.emit()` to build deterministic pointer-only block bodies (sorted agent/command/skill index) and `read→splice→write` each shared file — never a template overwrite (Pitfall 2). AGENTS.md/CLAUDE.md are excluded from the ownership manifest (Regime B, not Regime A).
- Verified idempotence: a committed then re-emitted `AGENTS.md`/`CLAUDE.md` reproduces byte-for-byte; the full CI `emit-drift` path set (`.opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json`) is clean.

## Task Commits

TDD RED → GREEN → wire:

1. **Task 1 (RED): failing managed-block idempotency test** — `f7ec3bd` (test)
2. **Task 1 (GREEN): splice_managed_block splice** — `038bb9f` (feat)
3. **Task 2: wire generate.emit() merge + merged AGENTS.md/CLAUDE.md** — `0ffe54b` (feat)

**Plan metadata:** see the final `docs(07-04)` commit.

## Files Created/Modified
- `tools/harness_emit/merge.py` — `BEGIN_MARKER`/`END_MARKER`, `_normalize` (BOM-strip + LF), `_finalize` (single trailing newline), `splice_managed_block`.
- `tools/harness_emit/tests/test_merge_idempotent.py` — 6 idempotency/preservation assertions.
- `tools/harness_emit/generate.py` — `merge` import, `build_agents_block`/`build_claude_block` deterministic pointer bodies, `_merge_shared_markdown`, and the Regime-B merge step inside `emit()`.
- `AGENTS.md` — HARNESS-MANAGED surface-index block appended at tail (all rules preserved).
- `CLAUDE.md` — HARNESS-MANAGED emitter-pointer block appended after the GSD profile fence (Project/Developer-Profile blocks preserved).

## Decisions Made
- **Fail loud on a malformed fence:** exactly-one-marker (or END-before-BEGIN) raises `ValueError` instead of guessing where to splice — a half-marker file is corrupt input and silently patching it risks eating human content.
- **Block placement at file tail:** appended after the last GSD/human section so every GSD-managed and human-authored line sits OUTSIDE the fence and is provably preserved by the preserve-outside path.
- **Not manifest-owned:** AGENTS.md/CLAUDE.md are Regime-B merge targets; adding them to `emit-manifest.json` would (wrongly) mark them prunable whole-file artifacts. They are excluded by design (verified: 0 matches in the manifest).

## Deviations from Plan

None — plan executed exactly as written.

## Threat Coverage
- **T-07-02 (Tampering / DoS-of-workflow):** mitigated — merge is read→splice→write, never full-write; `test_merge_idempotent` asserts outside-marker preservation; done-gate greps confirm `## Project` + Developer Profile survive.
- **T-07-08 (non-idempotent block flaps the drift gate):** mitigated — block body is deterministic (sorted surface index, no timestamps/floats); second-run byte-identical asserted; committed-then-re-emit diff is clean over the full emit-drift path set.
- **T-07-SC (package installs):** honored — zero new dependencies; `uv.lock` untouched.

## Issues Encountered
None. The formatter (PostToolUse ruff) reflowed authored files with no semantic change; all newly-authored code is ruff-clean and the 38-test `tools/harness_emit` suite is green (1 syrupy snapshot passed).

## User Setup Required
None.

## Next Phase Readiness
- The Markdown Regime-B splice is proven safe; Plan 05 tackles the second risky surface — `.claude/settings.json` **signature merge** (JSON, no comment markers), which must stay idempotent against the Phase-2/4 hand-wired SessionStart hooks (`test_hook_wiring.py`: 4 groups, 3 GSD survive) — do NOT double-wire.

## Self-Check: PASSED
(see appended verification below)

---
*Phase: 07-single-source-dual-runtime-emitter*
*Completed: 2026-07-12*
