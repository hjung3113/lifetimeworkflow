---
phase: 07-single-source-dual-runtime-emitter
verified: 2026-07-12T09:57:55Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 0
gaps: []
deferred: []
human_verification: []
re_verification:
  previous_status: gaps_found
  previous_score: 9/11
  gaps_closed:
    - "Loud-fail validators robustly enforce the read-only invariant for code-reviewer/explorer (no bypass)"
    - "The ownership manifest's prune (delete) path stays confined to the harness lane — no path traversal outside the emit root"
  gaps_remaining: []
  regressions: []
---

# Phase 7: Single-Source Dual-Runtime Emitter Verification Report

**Phase Goal:** One authored harness source (`harness/`) compiles into both runtime-native artifact sets — opencode (`.opencode/{agent,command,skill,plugin,tool}` + `opencode.json` + `AGENTS.md`) primary and Claude (`.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md`) secondary — with per-runtime loud-fail validators and a CI re-emit-diff drift gate.
**Verified:** 2026-07-12T09:57:55Z
**Status:** passed
**Re-verification:** Yes — after gap closure (commits c741804, 7f43aaa)

## Re-Verification Summary

The prior verification (2026-07-12T08:38:21Z, `gaps_found`, 9/11) failed exactly two must-haves,
both guard-hardening defects independently flagged CR-01/CR-02 in `07-REVIEW.md`. Both are now
fixed on this branch and independently re-verified by this verifier (code read + suite run), and
nothing among the other 9 truths regressed.

### Gap #1 closed — `is_read_only()` dict-bypass (CR-01, commit c741804)

- **Code guard confirmed:** `tools/harness_lint/caps.py` now defines `_grants_allow(value)`
  (lines 71-81), which for a dict-valued permission returns `any(str(v) == "allow" for v in
  value.values())` and for a scalar returns `str(value) == "allow"`. `is_read_only()` (lines
  84-96) now calls `_grants_allow(perm.get(key, "deny"))` for each of `edit`/`bash`/`write`,
  so a per-glob object such as `bash: {"*": "allow"}` — which `str({...}) == "allow"` never
  caught — now correctly resolves to a write/shell affordance and fails the read-only check.
- **Regression test passing:** `tools/harness_lint/tests/test_agents.py::test_read_only_sees_through_per_glob_permission_dict`
  asserts `not is_read_only({"permission": {"bash": {"git *": "allow", "*": "deny"}}})`
  (the exact previously-passing bypass) AND that an all-deny mapping still reads read-only.
  Ran green in isolation.

### Gap #2 closed — prune delete not `_confine`-guarded (CR-02, commit 7f43aaa)

- **Code guard confirmed:** `tools/harness_emit/manifest.py` now defines `_confined(path, root)`
  (lines 48-62) which resolves the path and returns `None` (skip, does not raise) when
  `root_resolved != resolved and root_resolved not in resolved.parents` — mirroring
  `generate._confine` but SKIP-rather-than-crash so one bad entry can't abort the emit; `.resolve()`
  also collapses symlink escapes. `prune_then_write()` (lines 81-88) now computes
  `stale = _confined(root / rel, root)` and `continue`s the loop when `stale is None`, gating the
  `stale.unlink()` behind confinement. The delete target — taken verbatim from the on-disk prior
  manifest (external data) — can no longer reach outside the emit root.
- **Regression test passing:** `tools/harness_emit/tests/test_manifest.py::test_prune_never_deletes_outside_emit_root`
  seeds an outside file, writes a prior manifest whose `paths` contains `"../outside-secret.txt"`,
  runs `harness_emit.emit(...)`, and asserts the outside file survives unchanged. Ran green in
  isolation.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `tools/harness_emit` generates `.opencode/{agent,command,skill,plugin}` + `opencode.json` + `AGENTS.md` from a single `harness/` source | ✓ VERIFIED (with documented `tool` deviation) | Live re-emit this session: "70 artifact(s) emitted to .opencode/ + .claude/ + opencode.json (agents + commands + skills + plugins + config)". `.opencode/tool/` intentionally omitted — no `harness/tool*` source exists (RESOLVED Open Question 3 in 07-RESEARCH.md; reiterated in 07-03-PLAN.md). Reasoned scope narrowing, not an oversight. |
| 2 | Same source emits `.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md`, respecting each runtime's shape, `.claude/get-shit-done/` untouched | ✓ VERIFIED | (carried, unchanged) `.claude/{agents,commands,skills}` populated + shape-correct; `.claude/settings.json` reproduced byte-for-byte; `CLAUDE.md` HARNESS-MANAGED block with GSD sections intact; `emit-manifest.json` holds zero gsd-*/get-shit-done paths. |
| 3 | Per-runtime limit validators (Claude skill desc/body caps, opencode permission-matrix shape) FAIL the build rather than silently truncating | ✓ VERIFIED | `validate.py` never slices/truncates, only raises `HarnessEmitError`; AND the read-only-invariant validator it delegates to (`is_read_only`) is now robust (gap #1 closed) — the "never silently wrong" guarantee holds. |
| 4 | A CI check re-emits and diffs the generated surfaces to catch hand-edited drift | ✓ VERIFIED | (carried) `.github/workflows/ci.yml` `emit-drift` job present and listed in `gate.needs`. |
| 5 | Re-emit is idempotent / byte-identical (`git diff --exit-code` clean) | ✓ VERIFIED | Ran `uv run python -m tools.harness_emit` (70 artifacts) then `git diff --quiet -- .opencode .claude/agents .claude/commands .claude/skills opencode.json AGENTS.md` → **exit 0**; `git status --short` over the full surface (incl. `.claude/settings.json`, `CLAUDE.md`) empty. |
| 6 | Full test suite green | ✓ VERIFIED | `uv run pytest -q` → **489 passed** (was 487; +2 new regression tests), 4 syrupy snapshots passed. |
| 7 | opencode agent projection carries `mode`+`permission`; Claude projection carries `tools`, no `permission` block | ✓ VERIFIED | (carried) `.opencode/agent/python-engineer.md` has `mode`+`permission`; `.claude/agents/python-engineer.md` has `tools`, no `permission`/`mode`. |
| 8 | Read-only personas (code-reviewer, explorer) stay read-only in BOTH projections, and the enforcing validator is robust | ✓ VERIFIED | Emitted data correct today (code-reviewer: `edit/bash/write: deny` → Claude `tools: Read, Grep, Glob`); AND the enforcement mechanism is now bypass-proof for per-glob dict permissions (gap #1 closed, regression test passing). |
| 9 | Ownership manifest lists only harness-owned paths; prune (delete) path is confined and never touches out-of-lane paths | ✓ VERIFIED | `emit-manifest.json` holds zero gsd paths; `is_gsd_owned()` still skips gsd lanes; AND the delete now routes through `_confined()` so a traversal-shaped manifest entry (`../…`) is skipped, not deleted (gap #2 closed, regression test passing). |
| 10 | AGENTS.md/CLAUDE.md managed-block merge preserves outside-marker content; settings.json signature merge preserves GSD hook wiring (4 SessionStart groups) | ✓ VERIFIED | (carried) `## Project` + Developer-Profile intact in CLAUDE.md; `.claude/settings.json` has exactly 4 SessionStart groups; `test_hook_wiring.py` (10 tests) green. |
| 11 | No real model identifier leaks into any emitted harness artifact | ✓ VERIFIED | (carried) Only non-harness `gsd-ai-researcher.md` matches a model-ID regex; zero matches in any harness-emitted path. |

**Score:** 11/11 truths verified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/harness_emit/generate.py` | Emit spine: REPO_ROOT, HarnessEmitError, `_confine`, deterministic write, `main()` | ✓ VERIFIED | `_confine` at every write site; live `main()` re-emit succeeds + idempotent. |
| `tools/harness_emit/project_agent.py` | Agent frontmatter projection (opencode/Claude) | ✓ VERIFIED | `to_opencode`/`to_claude`; output shape spot-checked. |
| `tools/harness_emit/project_command.py` | Command projection | ✓ VERIFIED | Claude drops `agent`/`subtask`, keeps `description`. |
| `tools/harness_emit/project_skill.py` | Skill projection + `references/` byte-copy | ✓ VERIFIED | 9 skills to both trees; references byte-identical. |
| `tools/harness_emit/permissions.py` | permission-matrix.json → 15-key opencode.json block | ✓ VERIFIED | `opencode.json` permission has exactly the 15 keys; `bash` `*`-first order preserved. |
| `tools/harness_emit/merge.py` | Managed-block splice + settings.json signature merge | ✓ VERIFIED | Both markers present; settings.json reproduces live bytes. |
| `tools/harness_emit/validate.py` | Loud-fail cap/shape gate | ✓ VERIFIED | Never slices/truncates; delegates read-only check to now-robust `is_read_only` (gap #1 closed). |
| `tools/harness_lint/caps.py` | Shared caps + robust `is_read_only` | ✓ VERIFIED | `_grants_allow()` enumerates dict permission values; `is_read_only` sees through per-glob dicts (commit c741804). |
| `tools/harness_emit/manifest.py` | Ownership manifest, confined prune-then-write, gsd-* exclusion | ✓ VERIFIED | `_confined()` gates `unlink`; gsd-* exclusion intact (commit 7f43aaa). |
| `.github/workflows/ci.yml` | `emit-drift` job + `gate.needs` entry | ✓ VERIFIED | Present; in `gate.needs`. |
| `.opencode/{agent,command,skill,plugin}` + `opencode.json` + `AGENTS.md` | Primary target surface | ✓ VERIFIED (tool omitted, documented) | Populated; idempotent re-emit clean. |
| `.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md` | Secondary target surface | ✓ VERIFIED | Populated; settings.json byte-reproduced; CLAUDE.md merged. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `project_agent.py` | `tools.harness_lint.parse_frontmatter` | shared frontmatter reader | ✓ WIRED | Import present. |
| `validate.py` | `tools.harness_lint.caps` | cap constant + `is_read_only` imports | ✓ WIRED | Delegation now sound (gap #1 closed). |
| `.github/workflows/ci.yml gate` | `emit-drift` | `needs` fan-in | ✓ WIRED | In `gate.needs`. |
| `project_skill.py` | `harness/skills/<name>/references/` | byte-for-byte copy to both trees | ✓ WIRED, DATA FLOWS | references byte-identical. |
| `generate.py` | `merge.py` | splice managed block into AGENTS.md/CLAUDE.md | ✓ WIRED | Markers present; idempotent. |
| `manifest.prune_then_write` | filesystem delete | `_confined` traversal guard | ✓ WIRED | `stale = _confined(root / rel, root)`; `unlink` gated on non-None (gap #2 closed). |
| `validate.check_agent` / `check_projections` | `is_read_only` | read-only invariant enforcement | ✓ WIRED, SOUND | Delegate no longer bypassable (gap #1 closed). |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite | `uv run pytest -q` | 489 passed | ✓ PASS |
| Read-only dict-bypass regression | `pytest ...::test_read_only_sees_through_per_glob_permission_dict` | passed | ✓ PASS |
| Prune traversal-confinement regression | `pytest ...::test_prune_never_deletes_outside_emit_root` | passed | ✓ PASS |
| Idempotent re-emit | `uv run python -m tools.harness_emit && git diff --quiet -- .opencode .claude/agents .claude/commands .claude/skills opencode.json AGENTS.md` | exit 0, empty diff | ✓ PASS |
| Both fixes committed | `git log --oneline` shows c741804 + 7f43aaa | present | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| EMIT-01 | 07-01, 07-02, 07-03 | 정본 하네스 소스 포맷(`harness/`) — single source for agents/commands/skills/plugins | ✓ SATISFIED | `harness/{agents,commands,skills,plugins}` are the sole source consumed by every projector. |
| EMIT-02 | 07-01 through 07-05 | Emitter generates opencode + Claude artifacts; per-runtime validators loud-fail instead of truncating | ✓ SATISFIED | Emission + primary loud-fail caps confirmed; the read-only-invariant validator is now robust (gap #1) and the manifest prune path is now traversal-confined (gap #2). Both CRITICAL 07-REVIEW.md findings remediated by commits c741804 / 7f43aaa. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tools/harness_lint/caps.py` | 71-96 | (RESOLVED) former `is_read_only` string-equality dict-bypass | ℹ️ Resolved | Fixed by `_grants_allow` (commit c741804); regression test guards it. |
| `tools/harness_emit/manifest.py` | 48-88 | (RESOLVED) former unconfined delete path | ℹ️ Resolved | Fixed by `_confined` gate (commit 7f43aaa); regression test guards it. |
| `tools/harness_emit/validate.py` | ~63-70 | `check_agent` measures description length against un-folded text | ⚠️ Warning | Overly-conservative, not a bypass (folding only shrinks length). Carried WR-01, non-blocking, not remediated. |
| `tools/harness_emit/generate.py` | ~356-362 | `check_skill_set` gated behind `if skills:` — no-ops on empty set | ⚠️ Warning | Carried WR-02, non-blocking. |
| `tools/harness_emit/validate.py` | ~215-222 | model-identifier scan only inspects top-level keys | ⚠️ Warning | Carried WR-03, non-blocking. |
| `tools/harness_emit/permissions.py` | ~26-33 | `build_permission_block` doesn't validate merged block against `VALID_PERMISSION_KEYS` | ⚠️ Warning | Carried WR-04, non-blocking. |

No `TBD`/`FIXME`/`XXX` debt markers in any file modified by this phase. The two former 🛑 Blocker
anti-patterns are now resolved; the remaining ⚠️ Warnings are pre-existing hardening items from
07-REVIEW.md that do not block the phase goal.

### Human Verification Required

None. All findings are programmatically verifiable and were confirmed by direct code inspection +
suite execution.

### Gaps Summary

No gaps. Both previously-failing must-haves are closed:

1. **`is_read_only()` dict-bypass (gap #1 / CR-01)** — fixed in commit **c741804**. `caps.py` now
   has `_grants_allow()` which enumerates per-glob dict permission values; `is_read_only()` uses it
   for `edit`/`bash`/`write`. Independently confirmed: the regression test
   `test_read_only_sees_through_per_glob_permission_dict` — which asserts a `bash: {"git *":
   "allow", "*": "deny"}` persona is NOT read-only (the exact former bypass) — passes.

2. **prune delete traversal gap (gap #2 / CR-02)** — fixed in commit **7f43aaa**. `manifest.py` now
   has `_confined()` (resolve + parents check, SKIP not raise), and `prune_then_write()` gates
   `stale.unlink()` behind it. Independently confirmed: the regression test
   `test_prune_never_deletes_outside_emit_root` — which seeds `../outside-secret.txt` in the prior
   manifest and asserts the outside file survives emit — passes.

Full suite is 489 passed (up from 487 by exactly the two new regression tests), re-emit is
byte-identical (`git diff --quiet` exit 0) across the entire documented surface, and none of the
other 9 truths regressed. Phase goal achieved.

The two remaining pre-existing items — ROADMAP SC1 literally listing `.opencode/tool/` (deliberately
omitted, no source exists; documented RESOLVED Open Question) and the non-blocking WR-01..WR-04
hardening warnings from 07-REVIEW.md — are informational and do not block the phase goal.

---

_Verified: 2026-07-12T09:57:55Z_
_Verifier: Claude (gsd-verifier)_
