---
phase: 50a-harness-authoring
reviewed: 2026-07-30T04:59:52Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - harness/skills/harness-author/SKILL.md
  - .claude/skills/harness-author/SKILL.md
  - .opencode/skill/harness-author/SKILL.md
  - harness/skills/brownfield-adoption/SKILL.md
  - .claude/skills/brownfield-adoption/SKILL.md
  - .opencode/skill/brownfield-adoption/SKILL.md
  - tools/harness_lint/tests/test_harness_author.py
  - tools/harness_lint/caps.py
  - tools/harness_emit/emit-manifest.json
  - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
  - AGENTS.md
findings:
  critical: 1
  warning: 7
  info: 2
  total: 10
status: issues_found
---

# Phase 50a: Code Review Report

**Reviewed:** 2026-07-30T04:59:52Z
**Depth:** deep
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the new `harness-author` skill, its structural gate (`test_harness_author.py`), the
`caps.py` docstring addendum, the `brownfield-adoption` reference-name updates, and the emitted
projections/manifest/snapshot. The emit round-trip is correct (manifest and `.ambr` snapshot show
only the expected rename), and the dangling-reference gate is sound. However the skill's own core
promise — "defaults cited as `path:line` from this checkout" — is broken in three places (one
already known: `EXPECTED_SKILLS` at `caps.py:139-150` vs. actual `142-153`; two newly found here),
and the citation-integrity gate that is supposed to catch this class of drift has structural blind
spots that let all three slip through. Separately, and more importantly: the skill's guidance for
authoring a new **agent** is asymmetric with its guidance for skills/commands — it never tells the
reader that `EXPECTED_PERSONAS` must be updated, so a reader who follows the skill to add an agent
will hit a guard failure the skill never warned them about. That is a functional defect in the
product artifact itself, not just a citation nit.

## Critical Issues

### CR-01: harness-author omits the Agent kind's pinned anti-sprawl set, guiding a reader into a guaranteed guard failure

**File:** `harness/skills/harness-author/SKILL.md:25-30` and `:58-64`
**Issue:** Step 0 says "The current sets are enumerated at their single source of truth" and lists
exactly two entries:

```
- Skills: `tools/harness_lint/caps.py:139-150` (`EXPECTED_SKILLS`).
- Commands: `tools/harness_lint/tests/test_commands.py:52-74` (`EXPECTED_COMMAND_NAMES`).
```

There is no third bullet for Agents. `tools/harness_lint/caps.py:57-59` defines an exactly
analogous pinned set, `EXPECTED_PERSONAS`, and `tools/harness_lint/tests/test_agents.py`
(`test_expected_personas_present_no_sprawl`, line 67) enforces it with the same "no more, no
fewer" anti-sprawl semantics as `EXPECTED_SKILLS`/`EXPECTED_COMMAND_NAMES`. The Agent section of
Step 1 (`:58-64`) only says "the persona set... live[s] at `tools/harness_lint/caps.py:22-67`" as
descriptive trivia, not as an actionable "you must add your new persona name here or the gate will
fail" instruction — unlike the Skill bullet in Step 3, which explicitly says "...and the pinned
set of skill names (so adding an un-enumerated skill fails loudly)" (`:82`). The Command and Agent
bullets in Step 3 (`:83-86`) carry no equivalent warning at all.

A developer who follows this skill start-to-finish to author a new agent will write
`harness/agents/<persona>.md`, run `test_agents.py -x -q` as instructed, and hit
`test_expected_personas_present_no_sprawl` with no prior guidance connecting that failure back to
anything the skill told them to do. This is exactly the "skill that guides you into a guaranteed
guard failure" failure mode: the artifact's stated job is to make authoring "well-formed and,
where the shape allows, machine-checked" (line 14), and for one of its three documented kinds it
fails to do so.
**Fix:** Add a third Step-0 bullet naming `EXPECTED_PERSONAS` and its location, and add the same
"fails loudly if you skip this" phrasing used for skills to both the Command and Agent bullets in
Step 3, e.g.:
```
- Agents: `tools/harness_lint/caps.py:57-59` (`EXPECTED_PERSONAS`).
```
and in Step 3:
```
- Agent: `tools/harness_lint/tests/test_agents.py -x -q` — enforces the frontmatter shape, the
  read-only-persona invariant, and the pinned `EXPECTED_PERSONAS` set (so adding an un-enumerated
  persona fails loudly).
```

## Warnings

### WR-01: `EXPECTED_SKILLS` citation is off by three lines (confirmed drift)

**File:** `harness/skills/harness-author/SKILL.md:28`
**Issue:** Cited as `tools/harness_lint/caps.py:139-150`. The actual `EXPECTED_SKILLS = frozenset(
... )` block spans `caps.py:142-153` (verified via `grep -n`). Lines 139-150 instead cover the
tail of the preceding narrative comment ("...at eight before and after. / The eight entries below
are the whole set. / No more, no fewer (anti-sprawl).") through only the first five of the eight
frozenset entries — a reader following the citation lands mostly on prose and misses
`context-budget`, `brownfield-adoption`, and the closing paren.
**Fix:** Update the citation to `caps.py:142-153`.

### WR-02: `caps.py:22-67` citation for "the read-only-persona invariant" is imprecise

**File:** `harness/skills/harness-author/SKILL.md:63-64`
**Issue:** The sentence "the persona set, the valid permission keys, the valid modes, and the
read-only-persona invariant all live at `tools/harness_lint/caps.py:22-67`" is only partly
accurate: lines 22-67 do cover `VALID_PERMISSION_KEYS` (25-43), `VALID_MODES` (50),
`EXPECTED_PERSONAS` (57-59), and the `READ_ONLY_PERSONAS` *constant* (64) — but the actual
invariant-checking logic, `is_read_only()`, lives at `caps.py:91-103`, outside the cited range. A
reader who follows the citation to "see the invariant" finds only a frozenset of persona names,
not the function that enforces it.
**Fix:** Either widen the citation to `caps.py:22-103`, or split it into two citations (one for the
persona/permission/mode constants, one for `is_read_only()` at `91-103`).

### WR-03: The citation gate's numeric-range check never verifies the cited construct is actually within range

**File:** `tools/harness_lint/tests/test_harness_author.py:72-81`
**Issue:** `_resolve_citation` only checks `line_count < end` — i.e., "does the file have at least
`end` lines" — never that the named construct (`EXPECTED_SKILLS`, the read-only invariant, etc.)
actually starts/ends within `[start, end]`. This is exactly why WR-01 and WR-02 pass the gate
today despite being wrong: `caps.py` has well over 150/67 lines, so any numeric range up to the
file's total length is accepted regardless of content. Combined with the fenced-code-block
exemption (`_strip_fences`, `:53-57`) — which is reasonable in isolation but compounds the same
blind spot for illustrative snippets — the gate can only catch "citation points off the end of the
file," not "citation points at the wrong part of the file," which is the more common real-world
drift mode (as demonstrated by WR-01/WR-02 both existing in the same 106-line skill).
**Fix:** At minimum, tighten to require the cited range's start line be within some proximity
(e.g., ±2 lines) of a construct name occurring nearby, or — cheaper — require the anchor name (when
present in the citation as a parenthetical, e.g. `` (`EXPECTED_SKILLS`) ``) also appear verbatim
inside the cited numeric range, not just anywhere in the file. That single check would have caught
both WR-01 and WR-02 without a general source-parser.

### WR-04: Citation regex cannot match a path immediately followed by CLI flags, so three verify-command citations bypass validation entirely

**File:** `tools/harness_lint/tests/test_harness_author.py:46-48`; `harness/skills/harness-author/SKILL.md:80,83,86`
**Issue:** `_CITATION_RE` requires the backtick-quoted content to be exactly
`path[:anchor]` with no other characters. The three verify-command citations in Step 3 —
`` `uv run pytest tools/harness_lint/tests/test_skills.py -x -q` ``,
`` `tools/harness_lint/tests/test_commands.py -x -q` ``, and
`` `tools/harness_lint/tests/test_agents.py -x -q` `` — contain a space before the trailing
`-x -q` flags, so the regex never matches them as citations at all (the path-char class excludes
whitespace, and nothing after the path can close the backtick). These three references to real
test-module paths are therefore never checked by `test_citations_resolve_in_harness_author_skill`;
they happen to be correct today, but the gate provides zero assurance of that and a future typo in
one of these three lines (e.g. a renamed test module) would ship silently.
**Fix:** Either quote just the path portion separately from the flags (e.g. "Run
`` `tools/harness_lint/tests/test_skills.py` `` with `-x -q`"), or extend `_CITATION_RE` to also
match a path token embedded in a larger backtick-quoted command string.

### WR-05: `_resolve_citation`'s `::`-anchor handling doesn't match the real pytest node-id shape it claims to support

**File:** `tools/harness_lint/tests/test_harness_author.py:82-88`
**Issue:** The comment says "Strip a leading `::` pytest-node-id separator before the verbatim
substring check," implemented as `needle = anchor.split("::")[-1]`. But the real pytest node-id
shape is `path.py::test_name` (double colon immediately after the path, no single colon first).
`_CITATION_RE`'s design consumes exactly one literal `:` as the path/anchor separator
(`r"(?::(?P<anchor>...))?"`), so for `` `path.py::test_name` `` the captured `anchor` group is
`":test_name"` (leading colon retained, because only the *first* of the two colons is eaten by the
non-capturing group). `":test_name".split("::")` does not contain the substring `"::"` (it has a
single leading colon), so the split is a no-op and `needle` stays `":test_name"` — the subsequent
verbatim-substring check against the target file would then always fail for a syntactically valid
pytest node-id citation, because the target file contains `test_name`, not `:test_name`. The `::`
splitting logic only actually works for a different, non-standard shape:
`` `path.py:Class::method` `` (single colon separator, `::` embedded later). No citation in the
current skill body exercises this path, so the bug is latent, but the doc-comment's claim and the
code's actual behavior disagree about which shape is supported.
**Fix:** Either fix the regex to treat `::` itself as the separator (matching real pytest node-ids
directly), or correct the doc-comment to describe the shape the code actually handles, and add a
unit test asserting `path.py::test_name` resolves correctly.

### WR-06: The reachability gate (`test_harness_author_reachability`) is gameable in both directions

**File:** `tools/harness_lint/tests/test_harness_author.py:171-207`
**Issue:**
- **Under-strict (misses real deletions):** several checks only require two common words to appear
  *anywhere* in the body, independent of each other and of position. E.g. the
  "directory-name-equals-frontmatter-name rule" check (`:192-193`) merely requires `"directory"`
  and `"name"` to both appear somewhere, case-insensitively. Both already occur in unrelated
  sentences — `"directory"` at line 22 ("adding a directory") and line 38 ("equals the parent
  directory"), `"name"` in five other places — so deleting the actual rule sentence at line 35
  while leaving those other occurrences intact would still pass this check. The
  `"caps.py" in text and "description" in lowered` check (`:195-196`) and the
  `"opencode" in lowered and "claude" in lowered` check (`:198-199`) have the identical weakness:
  both words already occur multiple times in unrelated contexts throughout the file.
- **Over-strict (breaks on harmless rewording):** the opposite two checks require byte-exact
  substrings — the regex literal `^[a-z0-9]+(-[a-z0-9]+)*$` (`:189-190`) and the verify command
  `uv run pytest tools/harness_lint/tests/test_skills.py -x -q` (`:201-202`) — so a
  meaning-preserving edit (different flag order, an equivalent regex written with `\A`/`\Z`, a
  line-wrap) would fail the gate even though nothing was actually lost.
  Net effect: the gate is simultaneously too loose to catch real content loss for most of its six
  checks, and too brittle for the two it gets exactly right.
**Fix:** For the keyword-pair checks, require the words to co-occur within the same sentence/line
(or search for a short anchor phrase actually present in the current text, e.g. `"directory name
equals the frontmatter"`) rather than anywhere-in-document co-occurrence. For the exact-string
checks, consider matching on the semantic token (e.g. `test_skills.py` + `-x -q` as separate
required substrings) instead of one frozen literal.

### WR-07: `caps.py`'s Phase 50a docstring addendum breaks its own file's narration convention, hurting future grep-discoverability

**File:** `tools/harness_lint/caps.py:137-139`
**Issue:** Every other phase entry in the `EXPECTED_SKILLS` history comment literally names the
skill(s) it affects in backticks — `` `gate-model` ``, `` `golden-testing` ``,
`` `golden-debug` `` — so a future reader can `grep -n <skill-name> caps.py` and land directly on
the removal/change rationale. The Phase 50a entry deliberately avoids the literal `skill-creator`
string ("Phase 50a (Harness Authoring) absorbs the prior skills-only meta-authoring skill...")
specifically so it doesn't get caught by the new dangling-reference gate
(`test_no_tracked_reference_to_skill_creator`) — a documented, deliberate tradeoff per
`.planning/phases/50a-harness-authoring/50a-01-SUMMARY.md`. The cost of that tradeoff is real: this
is the one entry in an otherwise consistently-literal history comment that is not
grep-discoverable by the name of the thing it describes.
**Fix:** No code change required if the tradeoff is accepted, but consider scoping the
dangling-reference gate's `_SCAN_TARGETS` (or adding a narrow, explicitly-commented exemption for
this one historical mention) so `caps.py` can name `skill-creator` literally in its own history
comment without tripping the guard — restoring the file's self-consistency.

## Info

### IN-01: Citation-integrity coverage is scoped to `harness-author` only, not repo-wide

**File:** `tools/harness_lint/tests/test_harness_author.py:128-143`
**Issue:** `test_citations_resolve_in_harness_author_skill` reads exactly one file
(`_HARNESS_AUTHOR_SKILL`). This is intentional per the module's stated Success Criterion 1 scope,
but worth naming explicitly: "citations resolve" is not a repo-wide invariant this phase
establishes — it is a one-file spot-check. Other skills this phase also touched (e.g.
`brownfield-adoption`) have no equivalent citation gate, so any future drift there would not be
caught by this test module.
**Fix:** None required for this phase; flag as a candidate follow-up if citation rot elsewhere
becomes a recurring problem.

### IN-02: Step 3's Command and Agent bullets lack the "fails loudly" callout the Skill bullet has

**File:** `harness/skills/harness-author/SKILL.md:80-86`
**Issue:** Restates part of CR-01 at the Step-3 level specifically: only the Skill bullet
(`:80-82`) tells the reader the structural gate also enforces "the pinned set of skill names (so
adding an un-enumerated skill fails loudly)." The Command bullet (`:83-85`) and Agent bullet
(`:86`) describe what the gate checks generically ("enforces the caps...") without calling out that
each also has its own pinned-name gate the reader must satisfy.
**Fix:** See CR-01's fix — extending both bullets closes this gap at the same time.

---

_Reviewed: 2026-07-30T04:59:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
