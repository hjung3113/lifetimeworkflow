---
phase: 07-single-source-dual-runtime-emitter
plan: 05
subsystem: infra
tags: [emitter, settings-json, signature-merge, regime-b-json, hook-wiring, double-wiring, idempotent, pitfall-4]

# Dependency graph
requires:
  - phase: 07-single-source-dual-runtime-emitter
    provides: "emit spine + ownership manifest + emit-drift CI diff set (07-01)"
  - phase: 07-single-source-dual-runtime-emitter
    provides: "merge.py Regime B-md managed-block splice for shared Markdown (07-04)"
provides:
  - "tools/harness_emit/merge.py::merge_settings — settings.json signature-matched, order-preserving hook-group merge (Regime B-json)"
  - "generate.emit() reads → merge_settings → writes .claude/settings.json order-preservingly (no sort_keys, never manifest-owned)"
  - "test_settings_merge.py + extended test_coexist.py — byte-for-byte reproduction, exactly-4-groups, GSD survival, de-dup, idempotency"
affects: [emit-drift CI gate, .claude/settings.json GSD/harness hook coexistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regime B-json structural merge: append-or-replace harness-signature hook groups IN PLACE by command substring, de-dup duplicates, keep GSD groups verbatim/un-reordered"
    - "Two serialization regimes kept separate: settings.json is order-PRESERVING (no sort_keys); opencode.json + frontmatter are globally sorted"
    - "settings.json is a Regime-B merge target (read→merge→write), never a whole-file manifest-owned Regime-A artifact"

key-files:
  created:
    - tools/harness_emit/tests/test_settings_merge.py
  modified:
    - tools/harness_emit/merge.py
    - tools/harness_emit/generate.py
    - tools/harness_emit/tests/test_coexist.py

key-decisions:
  - "Canonical HARNESS_HOOK_GROUPS defined in merge.py with AUTHORED key order (matcher→hooks, type→command→timeout) matching the live committed bytes, so an in-place replace reproduces settings.json exactly on the FIRST emit"
  - "No harness group is wired into SessionStart — all 4 slots are GSD/injector-owned; the merge only touches PostToolUse/PreToolUse, leaving the 4-group SessionStart contract structurally untouched"
  - "No sentinel key (A3) — signature-match by command substring needs none; avoids the MEDIUM-confidence unknown-key tolerance of the Claude settings validator"
  - "settings.json deliberately kept OUT of emit-manifest.json (Regime B-json merge, not Regime A own)"

patterns-established:
  - "_merge_settings_json(claude_dir) runs after the Markdown merge; .exists() guard keeps tmp-root emit tests (no seeded settings.json) green"

requirements-completed: [EMIT-02]

# Metrics
duration: 4min
completed: 2026-07-12
---

# Phase 7 Plan 05: settings.json Signature Merge Summary

**The emitter now merges its Phase-2/4 hook groups into the LIVE `.claude/settings.json` by command-signature match — IN PLACE, order-preserving, de-duplicated — reproducing the file byte-for-byte from the first emit with SessionStart pinned at exactly 4 groups, so the phase's riskiest surface (Pitfall-4 double-wiring / T-07-11 sort-flap) is proven safe and the whole emit-drift gate diffs clean end-to-end.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-07-12T08:20:30Z
- **Completed:** 2026-07-12T08:24:00Z
- **Tasks:** 2
- **Files modified:** 4 (1 created + 3 modified)

## Accomplishments
- Built `merge.merge_settings(existing, harness_signatures, harness_groups)`: for each event it APPENDS-OR-REPLACES the harness-signature hook groups in place (matched by command substring `tools.hooks.{format_on_write,contract_guard,secret_scan,commit_gate}`), DE-DUPLICATES a duplicated harness group (no double-wire), keeps every GSD/human group verbatim in its live position, and returns a deep copy (input never mutated). Serialized with `json.dumps(merged, indent=2, ensure_ascii=False) + "\n"` — NO `sort_keys` (Regime B-json).
- Defined canonical `HARNESS_HOOK_GROUPS` (PostToolUse: format_on_write; PreToolUse: contract_guard, secret_scan, commit_gate) with AUTHORED key order matching the live committed bytes — the in-place replace reproduces `.claude/settings.json` exactly on the FIRST emit. Verified `json.dumps(parse(live), indent=2, ensure_ascii=False) + "\n"` round-trips the real 3664-byte file identically.
- Wrote `test_settings_merge.py` (6 assertions): byte-for-byte reproduction vs the ACTUAL live file, exactly-4-SessionStart-groups, GSD-hooks-survive-in-order, synthetic-duplicate-de-dup (lands back on live bytes), idempotency, and GSD-group-never-removed-when-sharing-event.
- Wired `generate.emit()` with `_merge_settings_json(claude_dir)` (read→merge→write, `.exists()` guarded, never template-overwrite, never manifest-listed). Extended `test_coexist.py` to seed GSD-owned `.claude/` files (`get-shit-done/`, `hooks/`, `gsd-*.json`, `package.json`, `settings.local.json`, a `gsd-*` agent) + a real-shaped settings.json and assert all byte-unchanged + absent from the manifest, and settings.json reproduced byte-for-byte.
- Confirmed a full `python -m tools.harness_emit` leaves `.claude/settings.json` byte-unchanged (`git diff --exit-code` clean) and the entire emit-drift path set (`.opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json`) diffs clean. `test_hook_wiring.py` (4 groups) still green; full core suite 487 passed.

## Task Commits

TDD RED → GREEN → wire:

1. **Task 1 (RED): failing settings.json signature-merge idempotency test** — `1e20a4b` (test)
2. **Task 1 (GREEN): merge_settings order-preserving signature merge** — `ed56120` (feat)
3. **Task 2: wire settings.json merge into emit + extend coexist** — `afc35f1` (feat)

**Plan metadata:** see the final `docs(07-05)` commit.

## Files Created/Modified
- `tools/harness_emit/merge.py` — `HARNESS_SIGNATURES`, `GSD_SIGNATURES`, canonical `HARNESS_HOOK_GROUPS`, `_group_signature`, and `merge_settings` (Regime B-json append-or-replace-in-place + de-dup) alongside the Plan-04 `splice_managed_block`.
- `tools/harness_emit/tests/test_settings_merge.py` — 6 assertions incl. reproduction against the real `.claude/settings.json` bytes.
- `tools/harness_emit/generate.py` — `_merge_settings_json` helper + the Regime-B-json merge step inside `emit()` (after the Markdown merge, before the manifest write).
- `tools/harness_emit/tests/test_coexist.py` — `_GSD_SEEDS` + `_SEED_SETTINGS` fixtures, GSD-untouched-and-unlisted assertion, byte-for-byte settings reproduction assertion.

## Decisions Made
- **Byte-fidelity via authored-order canonical groups:** the harness groups are declared in `merge.py` with exactly the live key order (`matcher`→`hooks`, `type`→`command`→`timeout`), so replacing the already-committed groups in place is a no-op reproduction. This is the MVP "idempotent coexistence" (Open Q2 / A5) — the harness does NOT migrate ownership of these groups this phase.
- **SessionStart never touched by the merge:** all 4 SessionStart slots are GSD/injector-owned, so `HARNESS_HOOK_GROUPS` has no SessionStart key — the 4-group contract (`test_hook_wiring.py`) is preserved structurally, not just accidentally.
- **Two serialization regimes stay separate:** settings.json is order-preserving (no `sort_keys`) because it is a shared GSD/human doc whose insertion order (SessionStart-first) is NOT alphabetical; a global sort would flap ~274 lines (T-07-11). opencode.json + frontmatter remain globally sorted (Plans 01–04). Unifying them was explicitly avoided.
- **Not manifest-owned:** settings.json is a Regime-B merge target; adding it to `emit-manifest.json` would (wrongly) mark it a prunable whole-file artifact. Excluded by design (test asserts 0 `settings.json` matches in the manifest).

## Deviations from Plan

None — plan executed exactly as written.

## Threat Coverage
- **T-07-09 (double-wiring → 5th SessionStart group):** mitigated — signature-matched in-place append-or-replace with de-dup; `test_settings_merge` + `test_hook_wiring` assert exactly 4 groups; done-gate `git diff --exit-code` on settings.json clean.
- **T-07-11 (global key-sort → ~274-line false drift):** mitigated — order-PRESERVING serialization (no `sort_keys`); test asserts the merge equals the ACTUAL live bytes; two-regime distinction documented in `merge.py`.
- **T-07-02 (overwriting/removing a GSD hook group):** mitigated — GSD signatures never removed/reordered; `test_coexist` asserts every seeded GSD file byte-unchanged; `test_settings_merge` asserts `gsd-validate-commit.sh` survives while harness groups share the event.
- **T-07-10 (emitter escapes into .claude/get-shit-done or .claude/hooks):** mitigated — target globs unchanged; the merge only touches `.claude/settings.json`; seeded `get-shit-done/`/`hooks/`/`gsd-*`/`package.json`/`settings.local.json` are byte-unchanged and absent from the manifest.
- **T-07-SC (package installs):** honored — zero new dependencies; only stdlib `copy`/`json` added; `uv.lock` untouched.

## Issues Encountered
None. The formatter (PostToolUse ruff) is clean on all newly-authored code; the 51-test `tools/harness_emit` + `test_hook_wiring` set is green, and the full 487-test core suite passes.

## User Setup Required
None.

## Next Phase Readiness
- Both risky merge surfaces (Regime B-md Markdown splice in 07-04, Regime B-json settings signature merge here) are proven safe and idempotent. The full single-source → dual-runtime emit pipeline (agents + commands + skills + plugins + opencode.json + AGENTS.md/CLAUDE.md + settings.json) now diffs clean end-to-end from the first re-emit — the emit-drift CI gate covers every generated surface.
- Any future task that MIGRATES the harness hooks under emit ownership (vs. today's coexistence) MUST update `test_hook_wiring.py` in the SAME plan — explicitly out of scope here (Open Q2 MVP decision).

## Self-Check: PASSED

Created file `tools/harness_emit/tests/test_settings_merge.py` verified present on disk; all three task commits (`1e20a4b`, `ed56120`, `afc35f1`) verified in git history. A full re-emit produces a clean `git diff` over the entire emit-drift path set (settings.json included); the manifest lists zero `settings.json` entries.

---
*Phase: 07-single-source-dual-runtime-emitter*
*Completed: 2026-07-12*
