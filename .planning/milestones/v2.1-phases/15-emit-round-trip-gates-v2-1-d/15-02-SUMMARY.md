---
phase: 15-emit-round-trip-gates-v2-1-d
plan: 02
subsystem: harness-emit
tags: [gates, verification, mem2-06, model-id, gen-04]
requires:
  - Plan 15-01 committed trees (0f39e6d emit, 2da29e9 .ambr regen)
provides:
  - Executed proof that zero model identifiers exist across all 84 manifest-owned emitted artifacts
  - GEN-04 verdict against the regenerated .ambr (18 passed)
  - test_coexist module docstring consistent with the live 20-command source
  - Recorded SC1 mis-wording (EXPECTED_COMMANDS provably not created)
affects:
  - PR #3 ratification of ADR-0004/0005/0006/0007 (unblocked)
tech-stack:
  added: []
  patterns:
    - "Verify criterion SUBSTANCE via an authoritative source (emit-manifest) when the criterion's own scope is under-specified"
    - "Record mis-worded criteria rather than fabricating source to satisfy prose"
key-files:
  created: []
  modified:
    - tools/harness_emit/tests/test_coexist.py
decisions:
  - "Scanned all 84 manifest-owned artifacts instead of the plan's 4-path grep set — the criterion omitted .claude/agents, where the emitter owns 5 files"
  - "Did NOT create EXPECTED_COMMANDS (0 source hits; D-11 precedent held for the fourth time)"
  - "Did NOT fix test_coexist.py:50, newly staled by 15-01 — T-15-09 bounds this file to one changed line; carried as follow-up"
metrics:
  duration: 6min
  tasks: 2
  files: 1
  completed: 2026-07-16
---

# Phase 15 Plan 02: Gate Proof Summary

Proved SC2/SC3 by execution rather than assumption — zero model identifiers across every
emitted artifact including the bodies no gate covers — then corrected the one genuinely
stale docstring Phase 14 left behind. One comment-level line changed; no behavior.

## What Happened

| # | SHA | What |
|---|-----|------|
| 1 | (none) | Task 1 — verification-only, nothing to commit |
| 2 | `0b82f83` | `docs(15-02)` — module docstring 19 → 20 (1 line) |

## SC2 — Model Identifiers: Zero, Bodies Included

The automated gates (`check_agent`, `check_opencode_config`) read only the `model` frontmatter
key and `opencode.json` values. **No gate greps emitted command/skill bodies** — coverage is
transitive only. Closed manually as agreed (verification, not a new gate):

| Check | Result |
|-------|--------|
| `pytest test_opencode_json.py test_agents.py -k model` | **6 passed** |
| Body grep over `.opencode`, `.claude/commands`, `.claude/skills`, `opencode.json` | **0 hits (exit 1)** |
| `provider/` values in `.opencode/agent` that are not `*-tier` | **none** |
| Distinct model values present | `provider/explorer-tier`, `provider/implementer-tier` — placeholders only |

### The plan's own grep set was under-scoped — widened to prove the claim

SC2 says "anywhere in the emitted trees," but the criterion's path set
(`.opencode .claude/commands .claude/skills opencode.json`) **omits `.claude/agents/`, where the
emitter owns 5 artifacts** (`code-reviewer`, `curator`, `explorer`, `orchestrator`,
`python-engineer`). Passing the literal criterion would not have proven the literal claim.

Widening the scan surfaced two apparent hits — both **false positives, and correctly out of scope**:

- `.claude/agents/gsd-framework-selector.md:50` — `GPT-4o, o3` inside a UI label
- `.claude/agents/gsd-ai-researcher.md:92` — `claude-sonnet-4-6`, `gpt-4o` in prose

Both are **GSD-owned** files (`grep -c` against `emit-manifest.json` = **0**), not emitter output.
They pre-date this phase and sit in a shared directory — the exact reason T-15-06 treats `gsd-*.md`
as untouchable. The emitter never writes them.

**Authoritative resolution:** scanned every path enumerated by `emit-manifest.json` —
**84 artifacts, ZERO model-id hits.** This is a strictly stronger proof than the plan's criterion:
it is ownership-derived rather than path-guessed, so it cannot under-scope as the criterion did.

## SC3 — GEN-04 and Suite

| Check | Result |
|-------|--------|
| GEN-04 `test_core_no_example_dep.py`, run **after** the `.ambr` regen | **18 passed** |
| Full non-example suite | **659 passed / 0 failed** — baseline held |
| Emit-drift replica over the 8-path set | **exit 0 — clean** |
| `git status --porcelain` after Task 1 | clean (`.mcp.json` untracked pre-session) |
| `uv.lock` diff | empty — no installs |

## Deviations from Plan

### 1. SC1 is MIS-WORDED — `EXPECTED_COMMANDS` does not exist (recorded, not satisfied)

Success Criterion 1 requires that "`EXPECTED_COMMANDS` are updated to match." **The constant has
never existed.** `grep -rn "EXPECTED_COMMANDS" tools/ harness/ libs/` returns **0 hits** (exit 1),
before and after this plan. `caps.py` defines `EXPECTED_PERSONAS`/`EXPECTED_SKILLS`/
`EXPECTED_TEMPLATES` with **no commands equivalent, by design** — `test_commands.py` is
glob-driven, which is precisely why `/agree` was auto-covered in Phase 14 with zero test edits.

SC1's **substance is fully met** by 15-01's emit + `.ambr` regen. The criterion is mis-worded, not
unmet. Inventing the frozenset (T-15-08) would be source tampering driven by a documentation
defect, and would add the drift surface the glob design exists to avoid. **D-11 precedent held —
the fourth consecutive time this milestone.**

### 2. `test_coexist.py:50` is now stale — flagged, deliberately NOT fixed

Line 50 reads *"the committed trees still hold 19 and Phase 15 (MEM2-06) owns re-emitting them."*
**15-01 re-emitted them; they now hold 20.** So 15-01's work newly staled a line this plan was
scoped to leave alone.

Not fixed: T-15-09 threat-models scope creep on this exact file, and the acceptance criterion
mandates exactly one changed line. Fixing it would breach the plan's own gate to correct a comment
no gate reads. Carried as a follow-up. (Line 44's `18 → 19; 19 → 20` is correct *history*, not stale.)

### 3. Mis-worded-criteria tally now stands at 4 this milestone

15-01 flagged two criteria incapable of detecting their claims (the `[^+-]` list-item grep; the
`tools/**/__snapshots__` pathspec that never matches). SC1 is the third. **This plan's SC2 grep set
is the fourth** — it under-scopes the trees it claims to cover. Notably, this plan's *own*
one-changed-line criterion `grep -c '^[+-][^+-]'` **did work here** (returned exactly **2**) — the
changed line starts with `The`, not a `-` list marker, so it dodged 15-01's failure mode by luck of
content, not by design. The pattern remains latent.

## Verification

| Criterion | Result |
|-----------|--------|
| `sed -n '3p'` contains `20`, not `19` | PASS |
| `ls harness/commands/*.md \| wc -l` | **20** — matches docstring |
| Changed lines in commit | **2** (exactly one line) |
| `git diff HEAD~1 HEAD --name-only` | only `test_coexist.py` |
| `test_all_20_commands_emit_to_both_trees` | passed (5 passed in file) |
| `tools/harness_emit` suite | 47 passed |
| Full suite | 659 passed / 0 failed |

## Downstream Impact

PR #3's two red jobs (`core-suite`, `emit-drift`) were both the single inherited re-emit debt,
settled in 15-01 and **proven safe to ship here**. `gate.needs` lists both, so this unblocks
ratification of **ADR-0004 / 0005 / 0006 / 0007** — the milestone's actual payoff.

## Follow-Up Candidates (deliberately out of scope)

1. **No gate reads the committed trees** — every emit gate renders from `harness/` source into
   tmp. The structural gate-theft hole 15-01 navigated by ordering discipline remains open; only
   the CI `git diff` replica catches it. A local test guarding the committed trees would close it.
2. **`test_coexist.py:50`** — staled by 15-01 (see Deviation 2).
3. **No gate greps emitted bodies for model ids** — closed by hand twice now (15-02 Task 1). If it
   must hold, it belongs in `validate.py`, scanning manifest-owned paths.
4. **`ruff check` as a CI gate** — ~57 pre-existing E-codes + 2 format failures in `tools/`. This
   phase added no new lint debt.
5. **`/agree` lacks `subtask: true`** in its opencode projection — an authored Phase-14 source
   decision; the emitter faithfully projects it. Flag only if a reviewer raises it.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern, or schema change. The sole edit is
a comment. T-15-08 (fabricating `EXPECTED_COMMANDS`) and T-15-09 (scope creep) both held.
T-15-SC: no installs, `uv.lock` byte-identical.

## Known Stubs

None.

## Self-Check: PASSED

- `tools/harness_emit/tests/test_coexist.py` — FOUND, line 3 says 20
- Commit `0b82f83` — FOUND, single file, 2 changed lines
- `EXPECTED_COMMANDS` — 0 hits across `tools/`, `harness/`, `libs/` (provably not created)
- Full suite — 659 passed / 0 failed (baseline held)
