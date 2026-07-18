---
phase: 15-emit-round-trip-gates-v2-1-d
reviewed: 2026-07-16T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - .claude/commands/agree.md
  - .claude/commands/checkpoint.md
  - .claude/commands/lint.md
  - .claude/commands/orient.md
  - .claude/skills/two-plane-memory/SKILL.md
  - .opencode/command/agree.md
  - .opencode/command/checkpoint.md
  - .opencode/command/lint.md
  - .opencode/command/orient.md
  - .opencode/plugin/session-inject.ts
  - .opencode/skill/two-plane-memory/SKILL.md
  - tools/harness_emit/emit-manifest.json
  - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
  - tools/harness_emit/tests/test_coexist.py
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-07-16
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Phase 15 is a mechanical re-emit. **The phase's stated deliverable is verified: it holds.** I
independently re-ran the emitter into an isolated tmp tree and diffed against the committed trees:

- `.opencode/**` — byte-identical (rc=0)
- `.claude/commands/**` — byte-identical (only `gsd/` differs, correctly not emitter-owned)
- `.claude/skills/**` — byte-identical (rc=0)
- `tools/harness_emit/emit-manifest.json` — byte-identical to a fresh emit (84 paths, matches 84 written)
- Full `tools/harness_emit` suite: 47 passed, 1 snapshot passed

The `.ambr` snapshot, manifest, and both runtime trees are faithful projections of `harness/`
source. The one hand-authored change (`test_coexist.py:1`, 19 → 20) is correct and consistent with
the assertions at lines 61–62. No model identifiers appear in the emitted trees (the two `--claude`
/ `--gemini` hits are GSD-owned files under `.claude/commands/gsd/`, outside emitter ownership and
outside this phase's scope). Per the derived-plane rule, no finding below recommends editing a
generated file — each is filed against the `harness/` source or the gate it was projected through.

**The material finding is not in the emitted content — it is in the gate that is supposed to keep
that content honest.** Phase 15 exists because the committed trees went stale in Phase 14 and no
gate caught it. That root cause is still live: I reproduced a stale-tree escape against the current
`emit-drift` gate. Phase 15 re-emitted the trees but did not close the hole that let them drift.

## Critical Issues

### CR-01: `emit-drift` gate is blind to untracked files — stale committed trees still ship undetected

**File:** `.github/workflows/ci.yml:197` (gate for the artifacts in this phase's scope)
**Issue:** The gate is `git diff --exit-code -- .opencode opencode.json .claude/agents
.claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json`. Bare `git diff` reports
only **tracked** modifications — it is structurally blind to **new untracked files**. Any newly
emitted artifact is therefore invisible to the gate.

This is the exact defect that caused Phase 14's stale trees and made Phase 15 necessary. It is
still open. I proved it empirically:

1. Added `harness/skills/golden-debug/references/zz-probe-ref.md` (a new source reference file).
2. Ran `uv run python -m tools.harness_emit` — it emitted two new files into the committed trees.
3. Ran the **exact CI gate command** → **rc=0, gate PASSES**, while `git status` showed
   `?? .claude/skills/golden-debug/references/zz-probe-ref.md` and the `.opencode` twin untracked.

Result: **stale committed trees ship green.** (Probe artifacts removed; tree restored and verified
clean.)

New *commands* happen to be caught today, but only **incidentally**: `AGENTS.md` is tracked and its
HARNESS-MANAGED block enumerates command *names*, so adding a command mutates a tracked file. That
is a coincidence of the index's granularity, not a gate. It does **not** hold for:

- skill `references/**` files (proven above — `AGENTS.md` lists skill names only, not reference files)
- any future emitted artifact not name-enumerated in the `AGENTS.md` index

Compounding it: `tools/harness_emit/emit-manifest.json` **is** tracked and **did** change in the
probe (`+2` lines) — it was the one artifact that recorded the drift — but it is **not in the gate's
path list**, so nothing diffed it.

The `stale-derived` job at `ci.yml:206` already documents the correct idiom and explicitly excludes
`emit-drift` from it: *"THE ONE DEVIATION FROM emit-drift (Pitfall P1): use `git add -A` + `git diff
--cached --exit-code`, NOT bare `git diff`. emit-drift's outputs are all pre-tracked."* That stated
premise — **"emit-drift's outputs are all pre-tracked"** — is **false**, and is precisely the
assumption that failed in Phase 14. Emit outputs are pre-tracked only until someone authors a new
source artifact, which is exactly when the gate is needed.

**Fix:** apply the `stale-derived` idiom to `emit-drift` and add the manifest to the diffed set:

```yaml
      - name: Re-emit the harness surface
        run: uv run python -m tools.harness_emit
      - name: Fail on any hand-edited or stale generated-artifact drift
        run: |
          # `git add -A` first: bare `git diff` cannot see NEW untracked emit outputs, which is
          # how the trees went stale in Phase 14 (a new source artifact emits untracked files).
          git add -A -- .opencode opencode.json .claude/agents .claude/commands .claude/skills \
            AGENTS.md CLAUDE.md .claude/settings.json tools/harness_emit/emit-manifest.json
          git diff --cached --exit-code -- .opencode opencode.json .claude/agents \
            .claude/commands .claude/skills AGENTS.md CLAUDE.md .claude/settings.json \
            tools/harness_emit/emit-manifest.json
```

Also correct the now-false premise in the `stale-derived` comment at `ci.yml:206` so the next
reader does not re-derive the same wrong conclusion.

## Warnings

### WR-01: `test_projected_tree_matches_committed_snapshot` cannot detect stale committed trees, but its name says it can

**File:** `tools/harness_emit/tests/test_emit_determinism.py:55-61`
**Issue:** The name reads as "the projected tree matches the committed tree," but the test does
neither half of that. It renders every agent/command/skill **from `harness/` source in memory**
(`iter_agents`/`iter_commands`/`iter_skills` → `render_markdown`) and compares to the checked-in
`.ambr`. It **never reads `.opencode/` or `.claude/`**. "committed" refers to the committed
*snapshot file*, not the committed *trees*. It is a source→projection regression test, and it is a
good one — but it is structurally incapable of detecting stale committed trees, because both sides
of its comparison derive from source.

This is not cosmetic: the naming materially misled Phase 14's deferral reasoning, which cited this
test as tracking the stale-tree deferral. It cannot. It went red in Phase 14 only because the
`.ambr` lacked `/agree`, and green in Phase 15 via `--snapshot-update` — neither transition says
anything about the committed trees. With CR-01 open, **no gate covers committed-tree freshness for
non-name-enumerated artifacts.**

(Scoped to this file. The known carried `test_coexist.py:50` stale comment is deliberately excluded
per the phase's one-changed-line criterion.)

**Fix:** rename to intent and state the boundary in the docstring:

```python
def test_projected_source_matches_committed_ambr_snapshot(snapshot) -> None:
    """A committed .ambr pins the projection of harness/ SOURCE — a serialization regression gate.

    SCOPE BOUNDARY: both sides derive from harness/ source; this test never reads the committed
    .opencode/ or .claude/ trees and CANNOT detect stale committed trees. Committed-tree freshness
    is owned solely by the CI emit-drift gate (see CR-01).
    """
```

### WR-02: `/agree` interpolates `$ARGUMENTS` into a shell string while instructing the reader not to

**File:** `harness/commands/agree.md:14-17` (projected to `.claude/commands/agree.md:13-15` and
`.opencode/command/agree.md:14-16`)
**Issue:** The command states *"Arguments are passed positionally to the coded writer; do not build
shell strings from feedback"* and the very next line does exactly that:

```
!`uv run python -m tools.agree.write $ARGUMENTS`
```

`$ARGUMENTS` is raw text substitution into a shell command line — not positional argv passing. The
guidance and the implementation contradict each other, and the guidance is the false one.

`/agree` carries elevated risk relative to the seven other `$ARGUMENTS` commands
(`adr`, `golden`, `golden-approve`, `component`, `add-language`, `new-contract-rule`,
`strangler-step`), which take slugs and identifiers. `/agree` is the **only** one whose contract is
to carry **verbatim free-text user prose** through `--because`. Prose contains apostrophes (quote
breakage) and may contain backticks or `$(...)` (command substitution). When an agent relays
feedback quoted from repo content or another document, that text is not fully trusted input.

Rated WARNING, not BLOCKER: the pattern predates this phase, execution is permission-gated, and the
realistic failure mode is mangling rather than a remote attacker. It is a real injection seam and
the self-contradiction should not stand.

**Fix:** in `harness/commands/agree.md`, drop the false claim and make the shell contract explicit,
or have the agent invoke the writer via a structured tool call rather than `!`-shell. Minimum:

```markdown
## Invocation

`$ARGUMENTS` is substituted into a shell command line. Quote every value, and never pass
unescaped backticks or `$(...)` in `--because` — shell metacharacters in feedback are executed,
not stored. Prefer the explicit form below over free-form interpolation.

!`uv run python -m tools.agree.write $ARGUMENTS`
```

Verified accurate in the same file (no finding): the exit-3 refusal on missing/blank `--because`
matches `tools/agree/write.py:58,134`, and `/lint`'s presence-safe provenance claim matches
`tools/harness_lint/provenance.py:85-102`.

## Info

### IN-01: `/checkpoint` stages files then commits by pathspec — the `git add` is a no-op

**File:** `harness/commands/checkpoint.md` (projected to `.claude/commands/checkpoint.md:30-32`)
**Issue:** `git add <paths>` is followed by `git commit -m "..." <paths>`. Committing with an
explicit pathspec bypasses the index entirely, so the preceding `git add` has no effect on the
commit. Harmless, but it teaches a wrong mental model of a two-step stage-then-commit. Secondary:
when neither state file has changed, `git commit` exits non-zero ("nothing to commit"), surfacing
a spurious failure on a no-op checkpoint.

**Fix:** drop the redundant `git add` (the pathspec commit already scopes the write and satisfies
the "never `git add -A`" rule), and tolerate the empty case, e.g. guard on
`git diff --quiet -- <paths> || git commit ...`.

### IN-02: `session-inject.ts` swallows every error into an empty payload with no signal

**File:** `harness/plugins/session-inject.ts` (projected to `.opencode/plugin/session-inject.ts:29-31`)
**Issue:** `assemblePayload` catches all errors and returns `""`, so a broken/missing generator
degrades to *silently no orientation at all* — indistinguishable from an intentionally empty
payload. Graceful degradation is explicitly intended ("never break session start"), so this is
intentional, and the file is authored-but-deferred with no runtime to validate against. Noted only
because a silent total loss of the orientation payload is a failure mode worth one line of
diagnostics when the opencode surface lands.

**Fix:** at Phase 3 wiring, keep the non-throwing behavior but emit a diagnostic on the catch path
(e.g. `console.warn`) so an absent payload is distinguishable from an empty one.

---

_Reviewed: 2026-07-16_
_Reviewer: gsd-code-reviewer_
_Depth: standard_
