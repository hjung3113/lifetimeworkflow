---
phase: 17-constitution-gate-dev-enforce-decoupling-secure-default-harn
verified: 2026-07-16T01:01:02Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
---

# Phase 17: Constitution-Gate Dev/Enforce Decoupling Verification Report

**Phase Goal:** The product's constitution gates (`contract_guard`, `commit_gate`) stop governing the
Claude dev session while staying enforce-by-default everywhere else, via a secure-default
`HARNESS_DEV_BYPASS` env opt-out honored by a shared `dev_bypassed()` helper, with byte-hygiene never
waived, distinct audit semantics from `GOLDEN_APPROVE_HUMAN`, the flag confined to gitignored
`.claude/settings.local.json`, and ADR-0007 recording the posture.

**Verified:** 2026-07-16T01:01:02Z
**Status:** passed
**Re-verification:** No — initial verification (this is the missing close-out for a phase executed
in an earlier session; plans committed `a6ab9f5`, `911e8d8`, `b1ddee9`, ADR landed `ad6f644`).

## Goal Achievement

### Observable Truths

All truths below were checked by **live execution** of the shipped hooks (not by trusting
SUMMARY.md prose) — direct stdin invocation of `tools.hooks.contract_guard`, direct call of
`tools.hooks.commit_gate.check_drift()` with a mocked drift result, and direct git/grep inspection.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Secure default: `HARNESS_DEV_BYPASS` unset + no token + constitution Write ⇒ still DENIED (SC3, the fail-open regression guard) | VERIFIED | Live invocation: unset env, `Write` to `docs/adr/9999-test.md` → `permissionDecision: deny` printed. |
| 2 | Blank/whitespace `HARNESS_DEV_BYPASS` ⇒ does NOT bypass (SC4, mirrors token blank-rule) | VERIFIED | Live invocation with `HARNESS_DEV_BYPASS="   "` → still `deny`. |
| 3 | `HARNESS_DEV_BYPASS=1` + constitution Write ⇒ allowed, with a distinct dev-only stderr note (SC1) | VERIFIED | Live invocation: no deny JSON printed; stderr note `contract-guard: constitution write to '...' allowed via HARNESS_DEV_BYPASS (dev-only) — CODEOWNERS still gates merge` — no "ratified" wording (`grep -in ratified tools/hooks/contract_guard.py` → empty). |
| 4 | Byte-hygiene never waived: `HARNESS_DEV_BYPASS=1` + constitution path + BOM/CRLF payload ⇒ STILL DENIED (SC2) | VERIFIED | Live invocation with dev flag set: BOM payload → deny `[R1-BOM] UTF-8 BOM present`; CRLF payload → deny `[R2-CRLF] CR byte present`. Byte-hygiene branch in `decide()` runs regardless of `approved`. |
| 5 | `commit_gate`: `HARNESS_DEV_BYPASS=1` downgrades a drift FAIL → WARN(dev) PASS; unset/blank keeps FAIL; distinct from `WARN (ratified)` (SC5) | VERIFIED | Live call of `check_drift()` with a mocked `run_gate()` drift result: unset→FAIL, dev=1→`PASS \| WARN (dev) — HARNESS_DEV_BYPASS set...`, dev=blank→FAIL, token=1→`PASS \| WARN (ratified) — GOLDEN_APPROVE_HUMAN set...`. |
| 6 | DRIFT-ONLY scope: the bypass never touches `check_polyglot`/`check_golden` | VERIFIED | `dev_bypassed` referenced 0 times in `check_polyglot`/`check_golden` bodies; `git show ad6f644` (ADR landing) touched only two docs/adr files, not the hook. |
| 7 | Shared helper, no drift: one `dev_bypassed()` in `_stdin.py` used by both gates | VERIFIED | `tools/hooks/contract_guard.py:37` and `tools/hooks/commit_gate.py:43` both import `dev_bypassed` from `tools.hooks._stdin`; single definition at `_stdin.py:42-44`. |
| 8 | Distinct from `GOLDEN_APPROVE_HUMAN`: separate env var, never labeled "human ratified" | VERIFIED | `DEV_BYPASS_ENV = "HARNESS_DEV_BYPASS"` vs `APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"` in both gate modules; token check runs FIRST in `check_drift()` so a real token still reads "WARN (ratified)"; dev path reads "WARN (dev)". |
| 9 | SC6: no committed config carries the flag; flag lives only in gitignored `.claude/settings.local.json` | VERIFIED | `grep -rn HARNESS_DEV_BYPASS .claude/settings.json .github/ opencode.json` → empty (exit 1). `.claude/settings.local.json` exists locally with `{"env":{"HARNESS_DEV_BYPASS":"1"}}` but `git status --porcelain=v1 --ignored` shows `!!` (ignored/untracked), `git check-ignore -v` confirms `.gitignore:27`, not staged. |
| 10 | ADR-0007 landed, Status accepted, MADR shape, records the posture + accepted self-enabling risk; append-only (0001–0006 intact); NOT self-landed via the new flag (T-17-04) | VERIFIED | `docs/adr/0007-constitution-gate-dev-enforce-decoupling.md` exists, `Status: accepted`, has Context/Decision Drivers/Considered Options/Decision Outcome/Consequences/Links sections mirroring ADR-0006 shape; records (a)-(f) decisions + the agent-self-enabling accepted risk. `docs/adr/README.md` has all 0001–0007 rows. `git show ad6f644 --stat` shows only the two ADR files changed — `tools/hooks/contract_guard.py` untouched at that commit, confirming the raw-shell/human landing did not go through the agent Write/Edit path the hook matches. |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/hooks/_stdin.py` | `DEV_BYPASS_ENV` + shared `dev_bypassed()` | VERIFIED | Lines 39, 42-44; docstring explicitly notes distinctness from `GOLDEN_APPROVE_HUMAN`. |
| `tools/hooks/contract_guard.py` | `main()` honors `token_present or dev_bypassed()`; dev-note; `decide()` byte-hygiene unchanged | VERIFIED | Lines 37 (import), 103-104 (approval seam), 108-117 (dev-note, on-plane only via `_on_constitution_plane`), `decide()` (60-92) unchanged logic — byte-hygiene branch runs independent of `approved`. |
| `tools/hooks/commit_gate.py` | `check_drift()` honors `dev_bypassed()` with distinct WARN(dev), DRIFT-ONLY | VERIFIED | Lines 43 (import), 169-179 (dev branch after token branch); `check_polyglot`/`check_golden` untouched. |
| `tools/hooks/tests/test_stdin.py` | unit cases for set/unset/empty/whitespace | VERIFIED | `test_dev_bypassed_for_nonblank_value`, `test_dev_bypassed_false_for_unset_or_blank`. |
| `tools/hooks/tests/test_contract_guard.py` | SC1-SC4 cases via `main()` | VERIFIED | 7 references to `HARNESS_DEV_BYPASS`; all pass. |
| `tools/hooks/tests/test_commit_gate.py` | SC5 + no-polyglot-weakening cases | VERIFIED | 8 references to `HARNESS_DEV_BYPASS`; all pass. |
| `docs/adr/0007-constitution-gate-dev-enforce-decoupling.md` | MADR record, Status accepted | VERIFIED | Landed via commit `ad6f644`, full MADR shape present. |
| `docs/adr/README.md` | append-only 0007 row | VERIFIED | All 0001-0007 rows present. |
| `.planning/phases/17-.../17-02-ADR-0007.draft.md` | durable scratch draft | VERIFIED | Present with `## Links`, `Status`, all locked-decision terms. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tools/hooks/contract_guard.py` | `tools/hooks/_stdin.dev_bypassed` | import + `main()` approval | WIRED | Live-tested: flag flips the allow/deny outcome exactly as designed. |
| `tools/hooks/commit_gate.py` | `tools/hooks/_stdin.dev_bypassed` | import + `check_drift()` DRIFT-ONLY downgrade | WIRED | Live-tested via mocked `run_gate()`; confined to `check_drift`. |
| `.claude/settings.json` | `tools/hooks/contract_guard.py` / `commit_gate.py --from-hook` | PreToolUse hook wiring | WIRED | `.claude/settings.json:125,145` reference both hook commands. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| SC3 secure default (unset ⇒ deny) | direct stdin invocation of `contract_guard` with unset env | `permissionDecision: deny` | PASS |
| SC1 dev bypass allow + note | direct stdin invocation with `HARNESS_DEV_BYPASS=1` | no deny; stderr dev-note printed | PASS |
| SC4 blank ⇒ deny | direct stdin invocation with `HARNESS_DEV_BYPASS="   "` | `permissionDecision: deny` | PASS |
| SC2 BOM/CRLF still denied under bypass | direct stdin invocation, dev flag set, BOM/CRLF payload | denied both times (`R1-BOM`, `R2-CRLF`) | PASS |
| SC5 drift downgrade | direct `check_drift()` call with mocked drift, four env states | FAIL / WARN(dev) PASS / FAIL / WARN(ratified) PASS as expected | PASS |
| SC6 no config leak | `grep -rn HARNESS_DEV_BYPASS .claude/settings.json .github/ opencode.json` | empty | PASS |
| Flag confined to gitignored file | `git status --porcelain=v1 --ignored` + `git check-ignore -v .claude/settings.local.json` | `!!` ignored, matched `.gitignore:27`, not staged | PASS |
| ADR landing didn't touch the hook | `git show ad6f644 --stat` | only two `docs/adr/*` files changed | PASS |

### Probe Execution

No dedicated `scripts/*/tests/probe-*.sh` files declared for this phase or found under `scripts/`; phase verification is via the hook test suites + live behavioral spot-checks above.

### Test Suite Results

| Suite | Command | Result |
|-------|---------|--------|
| hooks + harness_lint | `uv run pytest tools/hooks tools/harness_lint -q` | **372 passed** |
| full repo suite | `uv run pytest -q` | **659 passed**, 5 snapshots passed — matches the documented Phase-15 baseline (0 regressions) |

Note: 17-01-SUMMARY.md claimed "348 passed" for `tools/hooks tools/harness_lint` at landing time; the
current count is 372 passed (repo has grown since — this is expected drift from later phases, not a
discrepancy in this phase's own tests, which are present and green).

### Requirements Coverage

Per the task instructions, requirement IDs `DEVBYPASS-SC1..SC6` and `DEVBYPASS-ADR` are phase-local
IDs declared in PLAN frontmatter only; ROADMAP.md records "Requirements: none new (references the
approved brainstorm spec)". These are NOT expected in `.planning/REQUIREMENTS.md` and are not
orphaned — they map 1:1 to the observable truths verified above (SC1-SC6 → truths #1-#9; DEVBYPASS-ADR
→ truth #10), all SATISFIED.

### Anti-Patterns Found

None. `grep -n -E "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER"` returned nothing across all six modified
`tools/hooks/*` files. No debt markers, no stub returns, no empty handlers.

### Human Verification Required

None. All must-haves were verifiable programmatically via direct hook invocation, pytest, and git/grep
inspection. Plan 17-02's Task 2 (`checkpoint:human-verify`) was already completed in the earlier
session — the human landed ADR-0007 via commit `ad6f644`, which this verification independently
confirmed did not touch `tools/hooks/contract_guard.py`.

### Gaps Summary

No gaps. All 10 derived observable truths (roadmap goal + PLAN frontmatter must_haves, merged) were
independently verified by direct execution against the current codebase state, not by trusting
SUMMARY.md claims. The highest-stakes truth — secure default (unset ⇒ still deny) — was proven live,
as was the never-waived byte-hygiene invariant under an active bypass, and the config-leak check (SC6).
ADR-0007 is landed and append-only; the commit that landed it touched only ADR files, corroborating the
17-02-SUMMARY claim that the raw-shell landing did not route through the agent Write/Edit path the
contract-guard hook matches.

---

_Verified: 2026-07-16T01:01:02Z_
_Verifier: Claude (gsd-verifier)_
