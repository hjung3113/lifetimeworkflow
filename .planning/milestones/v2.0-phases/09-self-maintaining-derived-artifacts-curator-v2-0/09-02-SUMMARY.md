---
phase: 09-self-maintaining-derived-artifacts-curator-v2-0
plan: 02
subsystem: two-plane-memory
tags: [gitignore, derived-plane, committed-derived, contracts-index, MAINT-02]
requires:
  - "contracts-index generator (tools.memory_regen.contracts_index) — pre-existing, unchanged"
provides:
  - ".memory/derived/contracts-index.md as committed-derived (tracked) artifact"
  - "gitignore contents-form + negation so the stale-derived gate (Plan 04) can guard it"
affects:
  - ".gitignore"
  - ".memory/derived/contracts-index.md"
tech-stack:
  added: []
  patterns:
    - "git contents-form exclusion (`dir/*`) + single-file negation (`!dir/file`) to re-include one file under an otherwise-ignored derived dir (P3)"
key-files:
  created:
    - .memory/derived/contracts-index.md
  modified:
    - .gitignore
decisions:
  - "Kept generator INDEX_PATH at .memory/derived/contracts-index.md unchanged; the flip is a .gitignore change ONLY (inject.py untouched, minimal blast radius) — D-03/A1"
  - "repo-map.md stays session-ephemeral/ignored via the contents-form `*`; only contracts-index.md is re-included"
metrics:
  duration: 3min
  completed: 2026-07-13
---

# Phase 9 Plan 02: Committed-Derived contracts-index Flip Summary

Flipped `.memory/derived/contracts-index.md` from gitignored-derived to committed-derived using a git contents-form ignore + single-file negation, keeping `repo-map.md` session-ephemeral and the generator/inject path untouched — so the Plan-04 `stale-derived` gate can guard it (MAINT-02).

## What Was Built

- **`.gitignore` (MOD):** Replaced the directory-form rule `.memory/derived/` (line 19) with the contents-form pair `.memory/derived/*` + `!.memory/derived/contracts-index.md`. The directory form (trailing `/`) blocks descent so a `!` negation under it does nothing (P3); the contents form (`/*`) lets the single-file re-include take effect. Comment updated to document the committed-derived exception (machine-write + CI-verify).
- **`.memory/derived/contracts-index.md` (NEW, tracked):** Regenerated via `python -m tools.memory_regen.contracts_index` (2 contracts indexed, drift clean) and `git add`-ed. Now the first tracked file under `.memory/derived/`.

## Verification Evidence

- `git check-ignore .memory/derived/repo-map.md` → prints path, exit 0 (still ignored).
- `git check-ignore .memory/derived/contracts-index.md` → prints nothing, exit 1 (NOT ignored).
- `git ls-files .memory/derived/` → `.memory/derived/contracts-index.md` (tracked).
- Determinism: second regen left no unstaged modification (`git diff --exit-code` exit 0; porcelain shows `A ` staged only) — byte-identical.
- `tools/memory_regen/inject.py` unmodified (git status clean for that path); `INDEX_PATH` unchanged.

## Deviations from Plan

None - plan executed exactly as written.

Note: the plan's Task 2 `<automated>` verify used `git diff --cached --exit-code` for the determinism check; for a brand-new tracked file that command reports the whole file-add (exit 1) rather than a determinism failure. The determinism-correct check is the unstaged comparison against the staged blob (`git diff --exit-code` / porcelain), which passed byte-identical. No behavioral change — the underlying property (byte-stable regen) is satisfied.

## Known Stubs

None.

## Threat Flags

None. The `.gitignore` negation names EXACTLY `!.memory/derived/contracts-index.md`; everything else under `.memory/derived/` (incl. `repo-map.md`) stays ignored via `*`, and the `*.env` / constitution denies are unaffected (T-9-02-01 mitigated as planned).

## Commits

- c777952: chore(09-02): flip contracts-index to committed-derived via gitignore negation
- 8246708: feat(09-02): track committed-derived contracts-index.md

## Self-Check: PASSED
- FOUND: .gitignore (modified, contains `!.memory/derived/contracts-index.md`)
- FOUND: .memory/derived/contracts-index.md (tracked via git ls-files)
- FOUND commit: c777952
- FOUND commit: 8246708
