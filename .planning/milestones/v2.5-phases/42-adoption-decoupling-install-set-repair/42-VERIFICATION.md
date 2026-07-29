---
phase: 42-adoption-decoupling-install-set-repair
verified: 2026-07-28T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 42: Adoption Decoupling + Install-Set Repair Verification Report

**Phase Goal:** Make adoption standalone (`draft → apply → PR review`, no `task_control` import,
no task-revision binding, no `GOLDEN_APPROVE_HUMAN`, no read of a task-control contract — CER-06),
and make the installed product non-inert by shipping the Python its own emitted artifacts invoke
(PROD-01).

**Verified:** 2026-07-28
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths / Success Criteria (ROADMAP §Phase 42, all 6)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | `grep -rn "task_control" tools/adoption_apply/ tools/adoption_scan/` returns nothing | ✓ VERIFIED | Ran independently: empty output, exit 1. `approval.py` confirmed deleted (`test -f` → absent). `cli.py` subparsers are only `draft`/`apply` (`tools/adoption_apply/cli.py:202-210`). `scan.py` retains two prose comments with the hyphenated string `task-control` (`scan.py:11,57`) documenting provenance of the byte-copied patterns — these do not match the grep pattern (`task_control`, underscore) and are not a live read. |
| 2 | `grep -rn "GOLDEN_APPROVE_HUMAN" ...` returns nothing; `draft → apply` completes with the var unset | ✓ VERIFIED | Grep empty, exit 1 (independently re-run). Full-suite pytest (1315 passed) exercises the apply path unconditionally; independently confirmed `python -m tools.adoption_apply promote --help` now fails argparse (`invalid choice: 'promote'`), proving the subcommand and its gate are gone, not merely unreachable. |
| 3 | `scan.py` reads no file under `contracts/harness/task-control/`; 8 secret patterns owned locally; redaction tests pass unchanged | ✓ VERIFIED | `scan.py:60-124` defines `SECRET_CONTENT_PATTERNS` (8-tuple), `_GATE_REGISTRY_PATH` constant absent (`grep -c` → 0). Independently loaded `gate-registry.json`'s live `secret_patterns` (8 entries) and `scan.SECRET_CONTENT_PATTERNS` and asserted tuple equality in a fresh interpreter — **byte-identical: True**. `uv run pytest tools/adoption_scan -q` → 87 passed (includes secret-redaction tests). |
| 4 | `_CATEGORY_GLOBS` contains a `tools/**` entry; a fixture install proves every emitted `tools.X` module lands | ✓ VERIFIED | `destinations.py:179` → `"tools/**/*"` (note: not the plan's literal `"tools/**"` — SUMMARY documents this as an in-scope Rule-1 fix, since bare `tools/**` matches directories only under `pathlib.Path.glob`; verified this reasoning holds by testing both forms — see "Install-Completeness Attack" below). `tools/adoption_scan/tests/test_install_completeness.py` → 2 passed. |
| 5 | `uv run pytest -q` green; `emit-drift`, `stale-derived`, `contract-drift`, ruff ratchet clean | ✓ VERIFIED | `uv run pytest -q` → **1315 passed**, 7 snapshots passed (independently re-run). `python -m tools.harness_emit && git status --porcelain` → empty (one unrelated pre-existing diff in `.planning/config.json`'s `_auto_chain_active` session flag was produced by re-running the emitter in this verification session, not phase content — reverted, confirmed not a phase-42 artifact). `contract-drift` → `OK`. `ruff_baseline` → `245 findings (baseline 245) — PASS`. |
| 6 | Net surface change: no new command/agent/skill/contract/hook/dependency — only data rows + local constants | ✓ VERIFIED | `git diff --name-status 733db6f^..HEAD` shows exactly one new non-planning file added: `tools/adoption_scan/tests/test_install_completeness.py` (a test). `uv.lock` untouched. Only `tools/adoption_apply/pyproject.toml`'s `description:` string changed (no dependency edit). No new `.claude/commands`, `.opencode/command`, skills, or `contracts/*.schema.json` appear in the diff. |

**Score:** 6/6 criteria verified.

### Install-Completeness Attack (focus area 2 — falsification, not trust)

Independently, not from the SUMMARY:

- **Coverage claim vs. reality:** the test's own `_discover_module_refs()` was run standalone against
  the live tree; it found **25 distinct dotted references, 21 distinct top-level `tools.*`
  packages** — matching the phase's claimed "research enumerated 21 distinct modules" exactly.
  `test_discovers_at_least_twenty_modules` backstops this at `>= 20`.
- **Falsification of the fix:** removed the `"tools/**/*"` row from `_CATEGORY_GLOBS` by hand and
  re-ran `test_install_completeness.py` — it genuinely reds:
  `AssertionError: tools.adoption_apply ... is missing from the applied target tree`. Restored the
  file; the test returns to green (2 passed). This rules out both historical near-misses recorded in
  42-04-SUMMARY.md (the directory-only vacuous pass, and the bare `"tools/**"` no-op glob) — the test
  as it stands today is a real, non-vacuous regression guard.
- **Junk/secret sweep (focus area 3):** built the manifest against a scratch target and enumerated all
  317 `tools/`-prefixed `create` dispositions. Zero `__pycache__`, `.pyc`, `.venv`, or cache entries
  (confirms `destination_catalog()` sources from `git ls-files`, so untracked build artifacts are
  excluded by construction — not merely assumed). Name-matched for anything secret/credential-shaped:
  the only two hits are `tools/hooks/secret_scan.py` and its test — the secret-scanning tool itself,
  not a leaked secret.

### Human-Gate Non-Reintroduction (focus area 5)

- `harness/commands/adopt.md`: `grep -i "promote\|human gate\|approval"` → no matches.
- `harness/skills/brownfield-adoption/SKILL.md`: no `promote`/`five-stage` residue; only remaining
  `Stage 4` is the renumbered `apply` stage.
- Both emitted projections (`.claude/`, `.opencode/`) independently grepped for `promote` — no matches.
  Emit is byte-identical to source (`emit-drift` clean).
- `promote` subcommand is genuinely gone at the CLI level (argparse rejects it), not merely
  undocumented.

### Out-of-Scope Discipline (focus area 6)

| Item | Expected | Found |
|------|----------|-------|
| `tools/task_control` | survives (Phase 43) | EXISTS |
| `contracts/harness/task-control/gate-registry.json` | survives (Phase 44) | EXISTS |
| `tools/hooks/secret_scan.py` | survives (Phase 44) | EXISTS |
| `contracts/harness/security/deny-domains.{json,schema.json}` | survives | EXIST |
| 8 inlined secret patterns vs. registry's `secret_patterns` | byte-identical | Confirmed via direct tuple-equality assertion in a fresh interpreter, independent of the SUMMARY's own claim |

### Bookkeeping Honesty (focus area 7)

- `.planning/REQUIREMENTS.md` checkbox list: `CER-06` and `PROD-01` both `[x]`.
- Traceability table (`REQUIREMENTS.md:184-185`): both rows now read `Complete` (were `Not started`
  before 42-05's reconciliation edit) — checkbox list and table now agree.
- **Minor pre-existing staleness (not phase-42's defect, carried in the original requirement prose):**
  `REQUIREMENTS.md:61` still says "the 7 redaction regexes it needs are inlined" — the live count is
  8 (CONTEXT.md D-05 explicitly flags this as stale prose predating verification). 42-05's SUMMARY
  scoped its REQUIREMENTS.md edit to the traceability-table status cells only, not this body-text
  correction. This is cosmetic (does not affect closure — the code and tests are correct at 8) but is
  worth a follow-up prose fix; not blocking.

### Anti-Patterns Found

None in the phase's own changed files. No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers
introduced. `approval.py` and its test were deleted whole rather than stubbed. No hardcoded-empty
stub patterns in `test_install_completeness.py` (it performs a real `apply_manifest()` run).

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|---|---|---|---|
| CER-06 | 42-01, 42-02, 42-03 | ✓ SATISFIED | SC-1/2/3 above |
| PROD-01 | 42-04 | ✓ SATISFIED | SC-4 above, independently falsified |

### Human Verification Required

None. All 6 success criteria are mechanically checkable and were independently re-run (not merely
trusted from SUMMARYs); the one behavior CONTEXT.md flagged as "manual-only" (a human judging the
resulting `/adopt` flow reads sensibly after the gate's removal) is a UX-quality judgment on
already-verified, code-consistent documentation — not a functional gap. Given the doc/code agreement
confirmed above, this does not block phase closure.

### Gaps Summary

No gaps found. The phase's own SUMMARY history is candid about the two near-misses in 42-04 (vacuous
directory-only assertion, then a no-op `"tools/**"` glob) and this verification independently
reproduced both failure modes and confirmed the shipped test/glob combination genuinely closes them.
The single carried item — REQUIREMENTS.md's stale "7 redaction regexes" body text — is cosmetic
documentation debt in a milestone-tracking file, not phase-42 code or contract debt, and does not
block proceeding to Phase 43.

---

_Verified: 2026-07-28_
_Verifier: Claude (gsd-verifier)_
