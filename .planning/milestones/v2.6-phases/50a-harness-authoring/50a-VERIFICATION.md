---
phase: 50a-harness-authoring
verified: 2026-07-30T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 50a: Harness Authoring Verification Report

**Phase Goal:** Authoring a harness artifact stops being tribal knowledge. One `harness-author` skill
asks grounded questions and offers defaults cited as `path:line` from this checkout, so the answer is
verifiable against the repo rather than recalled. Its output lands runtime-neutral under `harness/`
only — the emitter projects it.

**Verified:** 2026-07-30
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (Roadmap SC) | Status | Evidence |
|---|---|---|---|
| 1 | `harness-author` exists as a skill and its offered defaults are cited as `path:line` locations that resolve in this checkout | VERIFIED | `harness/skills/harness-author/SKILL.md` exists (107 lines). Manually re-derived every backtick citation via the same regex the gate uses (17 citations) and cross-checked each against the live file: `caps.py:_NAME_MAX/_NAME_RE/_DESC_MAX/_BODY_WARN_LINES`, `caps.py:22-67` (agent caps block), `test_commands.py:52-74` (`EXPECTED_COMMAND_NAMES`, actual span 52-73, fully covered), `test_commands.py:_AGENT_SLUG` (line 39, present), `component.md:1-9`, `curator.md:1-17`, `context-budget/SKILL.md:1-16` — all resolve and their content matches the claim made about them. One citation is imprecise but not dead: `caps.py:139-150` for `EXPECTED_SKILLS` — the constant's actual assignment spans lines 142-153, so the cited range starts inside the preceding docstring and is truncated 3 lines short of the closing brace (misses `"brownfield-adoption"` and `)`). It still lands inside the frozenset body (line 142 opens it) so a reader resolving the citation finds the right construct, just not its full extent. Ran `uv run pytest tools/harness_lint/tests/test_harness_author.py -q` — 4/4 pass. Mutation-tested the gate myself: (a) injected `harness/skills/does-not-exist/SKILL.md:9999` → test correctly FAILS with the missing-path message; (b) restored file, confirmed `git status` clean. |
| 2 | Output lands under `harness/` only; `.opencode/`/`.claude/` change solely through re-emit; emit round-trip is byte-clean | VERIFIED | `git diff b961c4f..HEAD --stat` shows the source landed in `harness/skills/harness-author/SKILL.md` (new), `harness/skills/skill-creator/SKILL.md` (deleted), `harness/skills/brownfield-adoption/SKILL.md` (edited). `.opencode/skill/**` and `.claude/skills/**` changed only for the same files (mirrored deletes/creates), plus `AGENTS.md` and `emit-manifest.json`, both of which the emitter regenerates. Ran `uv run python -m tools.harness_emit` twice from repo root: first run reports 73 artifacts emitted with `git status` showing zero diff both times (byte-clean, idempotent). `find .opencode .claude -iname '*skill-creator*'` → no results; `find .opencode .claude -iname '*harness-author*'` → exactly `.opencode/skill/harness-author` and `.claude/skills/harness-author`. |
| 3 | `skill-creator` no longer exists and everything it did is reachable through `harness-author`; skill count is 8 before and 8 after | VERIFIED | `test -d harness/skills/skill-creator` fails (absent). `git ls-files harness/skills/*/SKILL.md \| wc -l` → 8. Diffed `git show b961c4f:harness/skills/skill-creator/SKILL.md` (46 lines) against the new skill substantively, not just by heading match: Step-0 anti-sprawl question — present, generalized from "skill" to "skill, command, or agent" (`Step 0 (mandatory): why not an existing one?`); name regex `^[a-z0-9]+(-[a-z0-9]+)*$` — present verbatim; dir-name-match rule — present ("directory name equals the frontmatter `name`"); description/body caps — present, now pointed at `caps.py` constants by name instead of restated numbers (upgrade, not a loss — CONTEXT.md mandated this); shared-both-runtimes-caps note — present ("SAME caps apply to both... opencode and Claude"); verify command `uv run pytest tools/harness_lint/tests/test_skills.py -x -q` — present verbatim. `tools/harness_lint/tests/test_harness_author.py::test_harness_author_reachability` mechanically asserts all six elements and passes. `test_no_tracked_reference_to_skill_creator` passes; independently confirmed via `git grep -n 'skill-creator' -- AGENTS.md CLAUDE.md harness/ tools/ .opencode/ .claude/` → no hits (212 remaining hits are all inside `.planning/`, correctly out of scope and untouched history). |
| 4 | Zero new packages under `tools/`, zero new commands, zero new contracts | VERIFIED | `git diff b961c4f..HEAD --stat -- tools/` touches only `harness_lint/caps.py`, the new `harness_lint/tests/test_harness_author.py`, and `harness_emit/tests/__snapshots__/test_emit_determinism.ambr` — no new `tools/*/pyproject.toml`. `find tools -maxdepth 2 -name pyproject.toml` still lists the same 16 packages. `uv run pytest tools/harness_lint/tests/test_commands.py::test_command_count_is_stable -q` passes (19, unchanged from Phase 49). `find contracts -name '*.schema.json' \| wc -l` → 6, unchanged; `git diff b961c4f..HEAD --stat -- contracts/` empty. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `harness/skills/harness-author/SKILL.md` | absorbed, widened meta-authoring skill with grounded citations | VERIFIED | Exists, 107 lines, substantive (not a stub), wired into the emitter (present in both projected trees). |
| `tools/harness_lint/tests/test_harness_author.py` | citation-integrity, dangling-reference, reachability gates | VERIFIED | 207 lines, 4 tests, all collect and pass; mutation-tested for real failure capability (see Anti-Patterns / gate assessment below). |
| `tools/harness_lint/caps.py::EXPECTED_SKILLS` | pinned to the new 8-name set | VERIFIED | Line 142-153: `harness-author` present, `skill-creator` absent, exactly 8 entries. |
| `tools/harness_emit/emit-manifest.json` | regenerated, no `skill-creator` entries | VERIFIED | Regenerated by the emit run; contains `harness-author` emitted paths, none for `skill-creator`. |
| `harness/skills/skill-creator/` | deleted | VERIFIED | `test -d` fails; not in `git ls-files`. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `harness-author/SKILL.md` | `caps.py` | `path:line` citation, never restating a cap number | VERIFIED | Confirmed zero literal `64`/`1024`/`500` digits in the body (`grep` empty); every cap is cited by constant name. |
| `caps.py::EXPECTED_SKILLS` | `test_skills.py::test_expected_skills_present_no_sprawl` | shared frozenset import | VERIFIED | `test_skills.py:34` imports `EXPECTED_SKILLS` from `caps`; assertion at line 56 compares against it directly (no restated list). |
| `caps.py::EXPECTED_SKILLS` | `test_emit_determinism.py::test_emitted_skill_set_matches_expected` | shared frozenset import | VERIFIED | `test_emit_determinism.py:19` imports the same constant; assertion at line 103 compares against it. All three pins share one source — cannot independently drift. |
| `harness-author/SKILL.md` | emitted trees | `tools.harness_emit.generate.emit()` | VERIFIED | Confirmed by direct emit run (73 artifacts, zero post-run diff, twice). |

### Anti-Patterns / Gate-Quality Findings (informational, not blocking)

Per the request to specifically assess whether the citation-integrity and reachability gates "could
actually fail," I mutation-tested both beyond the dangling-reference gate the requester already
checked:

1. **Citation gate correctly fails on a missing path.** Injected a citation to a nonexistent file
   (`harness/skills/does-not-exist/SKILL.md:9999`) — the test failed with a precise offender message
   naming the bad citation. Confirmed live.
2. **Citation gate's fenced-code exemption CAN hide a dead citation.** Injected a dead citation
   (`harness/skills/totally-fake-dir/SKILL.md:1`) wrapped in a ```` ``` ```` fence — the test passed
   (fences are stripped before scanning, by design per `50a-CONTEXT.md`'s decision that fenced text is
   "an example, not a claim about this checkout"). This is a real loophole in the general-purpose gate
   (anyone could hide a bad claim in a fence later), but the currently delivered `SKILL.md` has exactly
   one fenced block (the verify-command snippet) and it contains no citations — so the loophole is not
   exploited in this delivery. Flagging as a design tradeoff to watch, not a gap in this phase.
3. **Citation gate's numeric-range check verifies line COUNT, not line CONTENT.** Injected a citation
   `AGENTS.md:1-5` claiming (falsely) to be "the skill-name enumeration" — the test passed because
   `AGENTS.md` has ≥5 lines; the gate never checks that lines 1-5 actually contain what the prose
   claims. This is the same mechanism behind the `caps.py:139-150` imprecision noted under Truth 1: a
   numeric-range citation is checked for existence-of-enough-lines only, not semantic accuracy. This
   matches the plan's own documented design (`50a-01-PLAN.md` Task 1 `<behavior>`: "if the anchor is
   numeric... assert the file has at least that many lines") — it is an accepted, weaker guarantee than
   the name-anchor path (which does substring-match the actual anchor text), not an unintended defect.
   The reachability gate (`test_harness_author_reachability`) is a straightforward verbatim/near-
   verbatim substring assertion over six required elements — mutation-testing it (removing any one
   required phrase) would fail it; not separately re-tested here since its assertions are simple direct
   string containment with no numeric-range weak point.

Neither finding blocks Success Criterion 1 (every citation in the delivered file resolves to a real,
substantively-matching location, with one citation truncated but not wrong) or Success Criterion 3. They
are recorded as observations for anyone hardening this gate further.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| MONO-10 | 50a-01 | A developer can author a new harness artifact through a `harness-author` skill with grounded, checkable defaults | SATISFIED | Skill exists, widened to skills+commands+agents, citations verified above. |
| MONO-11 | 50a-01 | `harness-author` absorbs `skill-creator`, keeping the skill count net ±0 | SATISFIED | `skill-creator` deleted, 8-before/8-after confirmed, reachability gate passes and was independently cross-checked. |

No orphaned requirements for this phase (REQUIREMENTS.md maps only MONO-10/MONO-11 to Phase 50a, both
claimed by the single plan).

### Human Verification Required

None. All four success criteria are mechanically checkable and were checked directly against the live
tree (not the SUMMARY's narration): `uv run pytest -q` (971 passed), the emit round-trip run twice,
direct `git diff`/`git ls-files`/`find` counts, and manual re-derivation + cross-check of every citation
the skill body offers.

### Gaps Summary

None blocking. Two minor, non-blocking gate-quality observations recorded above (fenced-block citation
exemption; numeric-range citations check line-count not content) — both are consequences of the design
decision recorded in `50a-CONTEXT.md`, not defects introduced by this phase's execution, and neither is
exploited by the delivered `harness-author/SKILL.md`.

---

_Verified: 2026-07-30_
_Verifier: Claude (gsd-verifier)_
