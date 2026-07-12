---
phase: 07-single-source-dual-runtime-emitter
verified: 2026-07-12T08:38:21Z
status: gaps_found
score: 9/11 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Loud-fail validators robustly enforce the read-only invariant for code-reviewer/explorer (no bypass)"
    status: failed
    reason: >
      tools.harness_lint.caps.is_read_only() — the sole gate check_agent()/check_projections() call
      to certify a READ_ONLY_PERSONAS agent stays read-only — compares perm.get(key, "deny") to the
      literal string "allow" via str(...) == "allow". If permission.bash is authored as a per-pattern
      object (the exact shape used elsewhere in this same codebase, e.g. harness/opencode.json's own
      permission.bash: {"*": "allow", ...}), str({...}) never equals "allow", so the check silently
      passes even when bash is fully allowed. Independently reproduced: is_read_only({'permission':
      {'bash': {'*': 'allow'}}, 'tools': 'Read, Grep, Glob'}) returns True. Today's authored
      harness/agents/code-reviewer.md and explorer.md happen to use scalar bash: deny, so the CURRENT
      emitted output is correct — but the enforcement mechanism itself is bypassable and gives no
      protection against a future/careless edit that uses the object form. This directly undermines
      the phase's core "loud-fail, never silently wrong" guarantee and was independently flagged as
      CRITICAL (CR-01) in the phase's own 07-REVIEW.md, produced 2026-07-12, with no follow-up fix
      commit since.
    artifacts:
      - path: "tools/harness_lint/caps.py"
        issue: "is_read_only() (lines ~71-83) does str(perm.get(key, 'deny')) == 'allow' — false for a dict-valued bash object that resolves to allow"
      - path: "tools/harness_emit/validate.py"
        issue: "check_agent() and check_projections() both delegate entirely to the buggy is_read_only(), so the source check AND the both-projections check share the same bypass"
    missing:
      - "Fix is_read_only() to resolve a dict-valued bash (or edit/write) permission value to its effective allow/deny (e.g. any pattern in the dict resolving to 'allow' should fail the read-only check), matching the reviewer's proposed _bash_effectively_allows() fix"
      - "Add a regression test asserting a READ_ONLY_PERSONAS agent with permission.bash as a dict containing an 'allow' entry is rejected by check_agent/check_projections"
  - truth: "The ownership manifest's prune (delete) path stays confined to the harness lane — no path traversal outside .opencode/.claude/opencode.json/AGENTS.md/CLAUDE.md"
    status: failed
    reason: >
      Every WRITE in tools/harness_emit/generate.py is routed through the verbatim _confine() guard
      before touching disk (T-07-01 mitigation, confirmed: 10+ call sites). manifest.py's
      prune_then_write() — the one function that DELETES files from disk based on a previously
      committed emit-manifest.json — never calls _confine (confirmed: zero references to _confine in
      tools/harness_emit/manifest.py). It does `stale = root / rel; stale.unlink()` where `rel` comes
      directly from the prior manifest's "paths" array with no resolve()/parents containment check.
      is_gsd_owned() protects gsd-*/get-shit-done/hooks/gsd-command paths specifically, but does NOT
      protect against an arbitrary out-of-lane relative path (e.g. a corrupted manifest entry or a bad
      merge-conflict resolution containing "../../something") — such an entry would be deleted with no
      guard. Independently confirmed via code read (no _confine import/usage in manifest.py). Flagged
      as CRITICAL (CR-02) in 07-REVIEW.md with no follow-up fix commit since.
    artifacts:
      - path: "tools/harness_emit/manifest.py"
        issue: "prune_then_write() (lines ~48-75) computes `stale = root / rel` and calls stale.unlink() with no _confine/resolve+parents check, unlike every write path in generate.py"
    missing:
      - "Route the prune target through _confine (or an equivalent resolve()+parents-of-root check) before unlink(), refusing (not crashing) on an out-of-lane path"
      - "Add a regression test seeding a manifest with a traversal-shaped path (e.g. '../../escape.txt') and asserting prune_then_write refuses to delete it"
deferred: []
human_verification: []
---

# Phase 7: Single-Source Dual-Runtime Emitter Verification Report

**Phase Goal:** One authored harness source compiles into both runtime-native artifact sets, built last because it is a pure function of the Phase 2-5 source.
**Verified:** 2026-07-12T08:38:21Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `tools/harness_emit` generates `.opencode/{agent,command,skill,plugin}` + `opencode.json` + `AGENTS.md` from a single `harness/` source | ✓ VERIFIED (with documented deviation on `tool`) | `.opencode/{agent,command,skill,plugin}` all populated (4 agents, 17 commands, 9 skills, 5 plugins); `opencode.json` emitted at repo root; `AGENTS.md` carries a HARNESS-MANAGED block. `.opencode/tool/` is intentionally omitted — no `harness/tool*` source exists; documented as RESOLVED Open Question 3 in 07-RESEARCH.md and reiterated in 07-03-PLAN.md ("Do NOT emit a `.opencode/tool/` dir ... omit"). This is a reasoned scope narrowing of the literal ROADMAP SC1 text, not an oversight — see override suggestion below. |
| 2 | Same source emits `.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md`, respecting each runtime's shape, `.claude/get-shit-done/` untouched | ✓ VERIFIED | `.claude/{agents,commands,skills}` populated and shape-correct (agents: `tools` key, no `permission`/`mode`; commands: `description` only, no `agent`/`subtask`); `.claude/settings.json` reproduces the live 4-SessionStart-group file byte-for-byte (`git diff --exit-code` clean); `CLAUDE.md` carries a HARNESS-MANAGED block with GSD `## Project`/Developer-Profile sections untouched; `git status --short .claude/get-shit-done/` empty (untouched); `emit-manifest.json` contains zero `gsd-*`/`get-shit-done` paths. |
| 3 | Per-runtime limit validators (Claude skill description/body caps, opencode permission-matrix shape) FAIL the build rather than silently truncating | ✓ VERIFIED (caps) / ✗ compromised (read-only invariant, see gap #1) | `tools/harness_emit/tests/test_validators.py` (over-cap description, invalid permission key, read-only-mutation cases) — 46/46 `tools/harness_emit` tests pass; `validate.py` never slices/truncates, only raises `HarnessEmitError`. However, the read-only-invariant validator itself has a confirmed bypass (gap #1) — the "never silently wrong" guarantee is not fully robust. |
| 4 | A CI check re-emits and diffs the generated surfaces to catch hand-edited drift | ✓ VERIFIED | `.github/workflows/ci.yml` has an `emit-drift` job (`uv run python -m tools.harness_emit && git diff --exit-code -- .opencode opencode.json .claude/agents .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json`), present in `gate.needs` (`needs: [setup, lang-tests, contract-check, drift, golden, core-suite, emit-drift]`). |
| 5 | Re-emit is idempotent / byte-identical (`git diff --exit-code` clean) | ✓ VERIFIED | Ran `uv run python -m tools.harness_emit` live in this verification session (70 artifacts + merges), then `git diff --exit-code -- .opencode .claude/agents .claude/commands .claude/skills opencode.json AGENTS.md CLAUDE.md .claude/settings.json` → exit 0, `git status --short` empty. |
| 6 | Full test suite green | ✓ VERIFIED | `uv run pytest -q` → **487 passed** (matches SUMMARY claim exactly), including 4 syrupy snapshots. |
| 7 | opencode agent projection carries `mode`+`permission`; Claude projection carries `tools`, no `permission` block | ✓ VERIFIED | Inspected `.opencode/agent/python-engineer.md` (has `mode`, `permission`) vs `.claude/agents/python-engineer.md` (has `tools: Read, Edit, Bash, Grep, Glob`, no `permission`/`mode`). |
| 8 | Read-only personas (code-reviewer, explorer) stay read-only in BOTH projections (as currently authored) | ✓ VERIFIED (data), ✗ enforcement not robust — see gap #1 | Emitted `.opencode/agent/code-reviewer.md` (`edit: deny, bash: deny, write: deny`) and `.claude/agents/code-reviewer.md` (`tools: Read, Grep, Glob`) are correctly read-only TODAY. But the validator that is supposed to guarantee this invariant going forward has a confirmed bypass (gap #1). |
| 9 | Ownership manifest lists only harness-owned paths; no gsd-* file is ever written or pruned | ✓ VERIFIED (gsd-specific protection) / ✗ traversal-safety gap — see gap #2 | `emit-manifest.json` contains zero gsd-matching paths; `test_coexist.py` (10 tests) passes, seeding GSD fixtures and asserting byte-unchanged. However, the delete path in `manifest.prune_then_write()` has no `_confine`/traversal guard (gap #2) — a corrupted manifest entry outside gsd-* naming would not be protected. |
| 10 | AGENTS.md/CLAUDE.md managed-block merge preserves outside-marker content; settings.json signature merge preserves GSD hook wiring (4 SessionStart groups) | ✓ VERIFIED | `grep` confirms `## Project` + `Developer Profile` intact in CLAUDE.md; `.claude/settings.json` has exactly 4 SessionStart groups (3 GSD hooks + memory-inject, verified by direct JSON parse); `tools/memory_regen/tests/test_hook_wiring.py` (10 tests) passes. |
| 11 | No real model identifier leaks into any emitted harness artifact | ✓ VERIFIED | `grep -rE 'claude-(opus|sonnet|haiku|fable)' .opencode .claude/agents .claude/commands .claude/skills opencode.json` — only match is `.claude/agents/gsd-ai-researcher.md` (a pre-existing GSD-owned file, not part of the harness emit surface, and not modified by this phase). Zero matches in any harness-emitted path. |

**Score:** 9/11 truths fully verified; 2 truths verified for current data but backed by a confirmed-bypassable enforcement mechanism (gaps #1, #2).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/harness_emit/generate.py` | Emit spine: REPO_ROOT, HarnessEmitError, `_confine`, deterministic write, `main()` | ✓ VERIFIED | Present; `_confine` called at every write site (10+ call sites grepped). |
| `tools/harness_emit/project_agent.py` | Agent frontmatter projection (opencode/Claude) | ✓ VERIFIED | `to_opencode`/`to_claude` present; output shape spot-checked (python-engineer, code-reviewer). |
| `tools/harness_emit/project_command.py` | Command projection | ✓ VERIFIED | Claude drops `agent`/`subtask`, keeps `description`; opencode keeps all three — confirmed on `.claude/commands/build.md` vs `.opencode/command/build.md`. |
| `tools/harness_emit/project_skill.py` | Skill projection + `references/` byte-copy | ✓ VERIFIED | 9 skills emitted to both trees; `references/canonicalization-axes.md` `cmp`'d byte-identical in both `.opencode` and `.claude`. |
| `tools/harness_emit/permissions.py` | permission-matrix.json → 15-key opencode.json block | ✓ VERIFIED | `opencode.json`'s `permission` has exactly the 15 valid keys; `bash` sub-object first key is `"*"` (last-wins order preserved). |
| `tools/harness_emit/merge.py` | Managed-block splice (Markdown) + settings.json signature merge | ✓ VERIFIED | `splice_managed_block` + `merge_settings` present; both markers found in AGENTS.md/CLAUDE.md; settings.json reproduces live bytes. |
| `tools/harness_emit/validate.py` | Loud-fail cap/shape gate | ✓ VERIFIED (mostly) | Never slices/truncates (`grep` for `[:1024]`/`.truncate(` — zero hits); `check_agent`/`check_command`/`check_skill`/`check_opencode_config` all raise `HarnessEmitError`. BUT the read-only check it delegates to (`is_read_only`) is bypassable — see gap #1. |
| `tools/harness_emit/manifest.py` | Ownership manifest, prune-then-write, gsd-* exclusion | ⚠️ PARTIAL | gsd-* exclusion works (verified); prune (delete) path is NOT `_confine`d — see gap #2. |
| `.github/workflows/ci.yml` | `emit-drift` job + `gate.needs` entry | ✓ VERIFIED | Job present (lines ~179-192), listed in `gate.needs`. |
| `.opencode/{agent,command,skill,plugin}` + `opencode.json` + `AGENTS.md` | Primary target surface | ✓ VERIFIED (tool omitted, documented) | All populated per counts (4/17/9/5); `opencode.json` at root; `AGENTS.md` merged. |
| `.claude/{agents,commands,skills}` + `settings.json` + `CLAUDE.md` | Secondary target surface | ✓ VERIFIED | All populated; settings.json byte-reproduced; CLAUDE.md merged. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `project_agent.py` | `tools.harness_lint.parse_frontmatter` | shared frontmatter reader | ✓ WIRED | Confirmed import present, used for all artifact discovery. |
| `validate.py` | `tools.harness_lint.caps` | cap constant imports | ✓ WIRED | Confirmed import list (`_BODY_WARN_LINES`, `_DESC_MAX`, ..., `is_read_only`). |
| `.github/workflows/ci.yml gate` | `emit-drift` | `needs` fan-in | ✓ WIRED | Confirmed in `gate.needs` array. |
| `project_skill.py` | `harness/skills/<name>/references/` | byte-for-byte copy to both trees | ✓ WIRED, DATA FLOWS | `cmp` confirms byte-identity end to end. |
| `generate.py` | `merge.py` | splice managed block into AGENTS.md/CLAUDE.md | ✓ WIRED | Both markers present in live files; idempotent re-emit confirmed. |
| `manifest.prune_then_write` | filesystem delete | `_confine` traversal guard | ✗ NOT WIRED | No `_confine` call in the delete path (gap #2). |
| `validate.check_agent` / `check_projections` | `is_read_only` | read-only invariant enforcement | ⚠️ WIRED BUT UNSOUND | Delegation exists but the delegate has a confirmed logic bypass (gap #1). |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite | `uv run pytest -q` | 487 passed | ✓ PASS |
| Idempotent re-emit | `uv run python -m tools.harness_emit && git diff --exit-code -- .opencode .claude/{agents,commands,skills} opencode.json AGENTS.md CLAUDE.md .claude/settings.json` | exit 0, empty diff | ✓ PASS |
| GSD untouched | `git status --short .claude/get-shit-done/` | empty | ✓ PASS |
| 15-key permission block, `*`-first bash | direct JSON parse of `opencode.json` | 15 keys, `bash` first key `"*"` | ✓ PASS |
| SessionStart group count | direct JSON parse of `.claude/settings.json` | 4 groups (3 GSD + memory-inject) | ✓ PASS |
| Plugin byte-fidelity | `cmp` all 5 `harness/plugins/*.ts` vs `.opencode/plugin/*.ts` | all identical | ✓ PASS |
| No model-identifier leak in harness surface | `grep -rE 'claude-(opus\|sonnet\|haiku\|fable)' .opencode .claude/{agents,commands,skills} opencode.json` | only non-harness `gsd-ai-researcher.md` hit | ✓ PASS |
| **`is_read_only()` bypass reproduction** | `python3 -c "... is_read_only({'permission': {'bash': {'*':'allow'}}, ...})"` | returned `True` (should be `False`) | ✗ FAIL — confirms gap #1 |
| **`manifest.py` uses `_confine` on delete** | `grep -n "_confine" tools/harness_emit/manifest.py` | zero matches | ✗ FAIL — confirms gap #2 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| EMIT-01 | 07-01, 07-02, 07-03 | 정본 하네스 소스 포맷(`harness/`) — single source for agents/commands/skills/plugins | ✓ SATISFIED | `harness/{agents,commands,skills,plugins}` exist and are the sole source consumed by every projector. |
| EMIT-02 | 07-01 through 07-05 | Emitter generates opencode(primary) + Claude Code artifacts from source; per-runtime validators loud-fail instead of truncating | ⚠️ MOSTLY SATISFIED | Emission + primary loud-fail caps confirmed; but the read-only-invariant validator (part of the "validators must not silently be wrong" contract) has a confirmed logic bypass (gap #1) and the manifest prune path lacks the traversal guard applied everywhere else (gap #2). Both are pre-existing, documented CRITICAL findings from the phase's own `07-REVIEW.md` with no remediation commit since. |

Both EMIT-01 and EMIT-02 are marked `[x]` complete in `.planning/REQUIREMENTS.md` and ROADMAP.md; EMIT-01 is fully substantiated. EMIT-02 is substantiated for the emission/caps machinery but not for the two CRITICAL code-review findings, which remain open.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tools/harness_lint/caps.py` | ~71-83 | `is_read_only()` string-equality check against a possibly-dict permission value | 🛑 Blocker | Read-only invariant enforcement can be silently bypassed (gap #1) |
| `tools/harness_emit/manifest.py` | ~48-75 (unlink ~69) | Delete path skips `_confine`/traversal check applied to every write path | 🛑 Blocker | Traversal-unsafe delete if manifest is corrupted/maliciously edited (gap #2) |
| `tools/harness_emit/validate.py` | ~63-70 | `check_agent` measures description length against un-folded text (inconsistent with `check_command`/`check_skill`, which fold first) | ⚠️ Warning | Overly-conservative; could loud-fail a valid agent authored with a block scalar containing extra whitespace. Non-blocking (not exploitable as a bypass — folding only shrinks length). Not independently re-verified as failing in current data; carried from 07-REVIEW.md WR-01. |
| `tools/harness_emit/generate.py` | ~356-362 | `check_skill_set` anti-sprawl guard gated behind `if skills:` — no-ops on an empty skill set | ⚠️ Warning | If `harness/skills/` were ever emptied, the "must equal EXPECTED_SKILLS" guard would silently skip rather than loud-fail. Carried from 07-REVIEW.md WR-02, not independently re-verified. |
| `tools/harness_emit/validate.py` | ~215-222 | `check_opencode_config`'s model-identifier scan only inspects top-level keys | ⚠️ Warning | A real model ID nested under e.g. `agent.<name>.model` would not be caught. Carried from 07-REVIEW.md WR-03, not independently re-verified. |
| `tools/harness_emit/permissions.py` | ~26-33 | `build_permission_block` doesn't validate the merged block against `VALID_PERMISSION_KEYS` | ⚠️ Warning | A typo'd key in `harness/permission-matrix.json` would pass through into committed `opencode.json` uncaught. Carried from 07-REVIEW.md WR-04, not independently re-verified. |

No `TBD`/`FIXME`/`XXX` debt markers found in any file modified by this phase.

### Human Verification Required

None. All findings in this report are programmatically verifiable (code inspection + reproduction), and were confirmed by direct execution/grep rather than requiring subjective human judgment.

### Gaps Summary

The emit pipeline itself works and is proven idempotent end-to-end: 487/487 tests pass, a live re-emit in this session produced a byte-for-byte clean `git diff` across the entire documented surface (`.opencode`, `opencode.json`, `.claude/{agents,commands,skills}`, `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`), the CI `emit-drift` gate is wired into `gate.needs`, GSD coexistence holds, and 9/11 must-have truths verify cleanly against the current codebase state.

However, this phase's own code review (`07-REVIEW.md`, produced the same day as the final SUMMARY commit) identified **2 CRITICAL findings that remain unfixed** — no commit after the review addresses them:

1. **`is_read_only()` bypass (CR-01)** — the function that is supposed to guarantee code-reviewer/explorer stay read-only in both runtime projections can be silently defeated by a dict-shaped `permission.bash` value (a shape legitimately used elsewhere in this same codebase, e.g. `harness/opencode.json`). Independently reproduced in this verification session: `is_read_only({'permission': {'bash': {'*': 'allow'}}, ...})` returns `True`. Today's authored source happens to use the scalar form, so the CURRENT emitted output is correct — but the enforcement mechanism itself provides no real protection against a future edit, defeating the phase's stated "loud-fail, never silently wrong" contract for this specific invariant.

2. **`manifest.prune_then_write()` traversal gap (CR-02)** — every write in the emitter is routed through the `_confine` guard (confirmed: 10+ call sites), but the one function that DELETES files from disk based on the prior manifest is not. Independently confirmed: zero references to `_confine` in `tools/harness_emit/manifest.py`. `is_gsd_owned()` protects gsd-*-named/lane paths specifically, but an out-of-lane path (e.g. from a corrupted manifest or bad merge) would be deleted unchecked.

Both findings are pre-existing in the reviewed code, independently reproduced by this verifier (not merely trusted from the review report), and directly relate to must-have truths this phase's own PLAN frontmatter declares ("read-only personas stay read-only in BOTH projections", "the manifest lists only harness-owned paths"). Given the adversarial verification stance and that these are CRITICAL-severity, confirmed-exploitable logic bugs in the exact enforcement code this phase exists to deliver, they are reported as gaps rather than accepted as pre-existing/out-of-scope.

**This may be intentional if the team judges "current data is correct" sufficient for this phase and wants to defer the enforcement hardening.** To accept this deviation, add to VERIFICATION.md frontmatter:

```yaml
overrides:
  - must_have: "Loud-fail validators robustly enforce the read-only invariant for code-reviewer/explorer (no bypass)"
    reason: "Current authored agents use only scalar permission.bash; dict-shaped bypass is a latent hardening item, not an active data error. Accepted for Phase 7 MVP; tracked as follow-up."
    accepted_by: "<name>"
    accepted_at: "<ISO timestamp>"
  - must_have: "The ownership manifest's prune (delete) path stays confined to the harness lane"
    reason: "gsd-* paths are explicitly protected by is_gsd_owned(); the manifest is a committed, code-reviewed artifact, not attacker-controlled input in the current threat model. Accepted for Phase 7 MVP; tracked as follow-up."
    accepted_by: "<name>"
    accepted_at: "<ISO timestamp>"
```

Separately, ROADMAP Success Criterion 1 literally lists `.opencode/{agent,command,skill,plugin,tool}`, but the emitter deliberately omits `tool` (no `harness/tool*` source exists today; documented as a RESOLVED Open Question in 07-RESEARCH.md and explicitly called out in 07-03-PLAN.md). This is a reasoned, documented scope narrowing rather than an oversight, and emitting an empty untracked directory would add no value — it is not counted as a blocking gap here, but is flagged for awareness.

---

_Verified: 2026-07-12T08:38:21Z_
_Verifier: Claude (gsd-verifier)_
