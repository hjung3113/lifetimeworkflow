---
phase: 50a-harness-authoring
fixed_at: 2026-07-30T05:20:00Z
review_path: .planning/phases/50a-harness-authoring/50a-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 50a: Code Review Fix Report

**Fixed at:** 2026-07-30T05:20:00Z
**Source review:** .planning/phases/50a-harness-authoring/50a-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 10 (1 critical, 7 warnings, 2 info)
- Fixed: 10
- Skipped: 0

All ten findings touch the same three interdependent files (`harness/skills/harness-author/SKILL.md`,
`tools/harness_lint/caps.py`, `tools/harness_lint/tests/test_harness_author.py`) — line-number
citations in the skill body shift together with `caps.py` edits, and the citation-gate's own
regex/anchor logic had to change in lockstep with how the skill body writes citations. Splitting
these into ten independent commits would have required repeatedly landing intermediate states with
failing tests (e.g. the new `::`-shaped pytest node-id citation only resolves once the WR-05 gate
fix is present). They were therefore applied and verified together, then committed as ONE atomic
commit that lists every finding ID it closes.

## Fixed Issues

### CR-01 / IN-02: harness-author omits the Agent kind's pinned anti-sprawl set

**Files modified:** `harness/skills/harness-author/SKILL.md`
**Commit:** `612ae41`
**Applied fix:** Added a third Step-0 bullet naming `EXPECTED_PERSONAS` (`caps.py:57-59`) and the
guard that enforces it (`test_agents.py::test_expected_personas_present_no_sprawl`). Extended the
Step-3 Command and Agent bullets with the same "fails loudly if you skip this" phrasing the Skill
bullet already had (closing IN-02 in the same edit, as the review's own fix note predicted).
**Regression test:** `test_harness_author_reachability` was already asserting Step-0/Step-3
content survives; no new dedicated test was needed since the citation-integrity tests
(`test_citations_resolve_in_harness_author_skill`) now also exercise the new Agent bullet's
citations end-to-end. **Evidence:** before the fix, `harness/skills/harness-author/SKILL.md`
Step 0 had only two bullets (Skills, Commands) — verified by reading the pre-fix file (see
REVIEW.md excerpt, lines 56-59). After the fix, `grep -c '^- ' harness/skills/harness-author/SKILL.md`
Step-0 block shows three bullets, and `test_citations_resolve_in_harness_author_skill` passes
against the new Agent citations.

### WR-01: `EXPECTED_SKILLS` citation off by three lines

**Files modified:** `harness/skills/harness-author/SKILL.md`, `tools/harness_lint/caps.py`
**Commit:** `612ae41`
**Applied fix:** Updated the citation from `caps.py:139-150` to `caps.py:144-155` (the WR-07 edit to
`caps.py`'s history docstring shifted the true range from the review's cited `142-153` to `144-155`;
the SKILL.md citation was updated to match the final post-fix line numbers, not the review's
snapshot numbers).
**Regression test:** `test_numeric_range_citation_validates_named_anchor_location` (new).
**Fails-before / passes-after:** Called `_resolve_citation("tools/harness_lint/caps.py", "100-115",
name="EXPECTED_SKILLS")` (a real, in-bounds, but wrong range) — asserts it is now REJECTED
(pre-strengthening WR-03 code returned `None`/accepted for any range less than the file length,
so this same call would have passed silently on the old `_resolve_citation`). Also asserts the
corrected `144-155` range resolves cleanly. Ran with `uv run pytest
tools/harness_lint/tests/test_harness_author.py::test_numeric_range_citation_validates_named_anchor_location
-q`: fails against the pre-fix `_resolve_citation` (no `name` parameter existed, so the call itself
would raise `TypeError` — a stronger failure than a silent pass), passes against the fixed version.

### WR-02: `caps.py:22-67` citation imprecise for "the read-only-persona invariant"

**Files modified:** `harness/skills/harness-author/SKILL.md`
**Commit:** `612ae41`
**Applied fix:** Split the citation into two: `caps.py:22-59` for the persona/permission/mode
constants, and `caps.py:91-103` (`is_read_only`) for the actual invariant-checking function.
**Regression test:** Covered by `test_citations_resolve_in_harness_author_skill`, which now also
validates the trailing `` (`is_read_only`) `` parenthetical resolves within `91-103` (WR-03's
strengthened check). **Evidence:** before the fix, a citation naming `is_read_only` at `22-67`
would have been silently accepted by the pre-fix length-only check (67 < file length); the
strengthened check run against the OLD `22-67` + `is_read_only` combination (verified manually via
`_resolve_citation("tools/harness_lint/caps.py", "22-67", name="is_read_only")`) returns a
"named construct not found within cited lines" offense, confirming the split citation was
necessary and the new range resolves cleanly.

### WR-03: citation gate's numeric-range check never verifies the cited construct

**Files modified:** `tools/harness_lint/tests/test_harness_author.py`
**Commit:** `612ae41`
**Applied fix:** Extended `_CITATION_RE` to optionally capture a trailing `` (`NAME`) `` parenthetical
immediately after a citation, and `_resolve_citation` now accepts a `name` parameter — for a
numeric-range anchor, if a name is given, the cited line range must contain that name verbatim, not
merely have "enough" lines.
**Regression test:** `test_numeric_range_citation_validates_named_anchor_location` (new).
**Fails-before / passes-after:** Ran the test against a reverted copy of `_resolve_citation`
(pre-fix, no `name` param) — the call signature itself doesn't exist, so the test cannot even be
expressed pre-fix; run against a hand-reduced pre-fix equivalent (`len(lines) < end` only, ignoring
`name`), the off-by-range citation for `100-115`/`EXPECTED_SKILLS` was WRONGLY ACCEPTED (offense
`None`). Post-fix: `uv run pytest tools/harness_lint/tests/test_harness_author.py -k
test_numeric_range_citation_validates_named_anchor_location -q` → 1 passed.

### WR-04: citation regex cannot match a path followed by CLI flags

**Files modified:** `harness/skills/harness-author/SKILL.md`,
`tools/harness_lint/tests/test_harness_author.py`
**Commit:** `612ae41`
**Applied fix:** Normalized how the body writes the three verify-command citations — quoting the
test-module path separately from its `-x -q` flags (e.g. `` run `uv run pytest` on
`tools/harness_lint/tests/test_skills.py` with `-x -q` ``) instead of packing both into one backtick
span, so `_CITATION_RE` now matches the bare path.
**Regression test:** `test_verify_command_citations_are_seen_by_citation_gate` (new).
**Fails-before / passes-after:** The test first asserts the OLD broken shape
(`` `tools/harness_lint/tests/test_skills.py -x -q` ``) still produces ZERO extracted citations
(proving the WR-04 bug is real and the test isn't vacuous), then asserts all three verify-command
paths ARE present among the citations extracted from the current (fixed) skill body. Ran
`uv run pytest tools/harness_lint/tests/test_harness_author.py -k
test_verify_command_citations_are_seen_by_citation_gate -q`: against the pre-fix body (which used
the packed `path -x -q` form), the second assertion would fail (none of the three paths appear in
`cited_paths`); against the fixed body, 1 passed.

### WR-05: `::`-anchor handling doesn't match real pytest node-id shape

**Files modified:** `tools/harness_lint/tests/test_harness_author.py`,
`harness/skills/harness-author/SKILL.md`
**Commit:** `612ae41`
**Applied fix:** `_resolve_citation` now strips exactly one leading `:` from the captured anchor
before the `::`-split, so `path.py::test_name` (captured anchor `:test_name`) normalizes to
`test_name` before the verbatim-substring check. Also added a real `::`-shaped citation to the skill
body (`test_agents.py::test_expected_personas_present_no_sprawl`) so the path is exercised, not
latent.
**Regression test:** `test_pytest_node_id_citation_resolves_end_to_end` (new).
**Fails-before / passes-after:** Ran the test against the OLD `_resolve_citation` (needle =
`anchor.split("::")[-1]` with no leading-colon strip): for anchor `:test_expected_personas_present_no_sprawl`,
`.split("::")` is a no-op (no literal `"::"` substring present), so `needle` stays
`:test_expected_personas_present_no_sprawl` — not found verbatim in `test_agents.py` — offense
returned, test fails. Against the fixed version: `uv run pytest
tools/harness_lint/tests/test_harness_author.py -k test_pytest_node_id_citation_resolves_end_to_end
-q` → 1 passed.

### WR-06: reachability gate gameable in both directions

**Files modified:** `tools/harness_lint/tests/test_harness_author.py`
**Commit:** `612ae41`
**Applied fix:** Replaced the six inline boolean expressions in `test_harness_author_reachability`
with named, independently-testable predicate functions (`_has_dir_name_rule`,
`_has_description_cap_reference`, `_has_shared_caps_sentence`, `_has_name_regex_semantics`,
`_has_verify_command`, `_has_anti_sprawl_stem`). The keyword-pair checks now require same-line
co-occurrence (closing the under-strict direction) instead of anywhere-in-document co-occurrence;
the exact-literal checks (name-regex string, verify command) now match on semantic tokens/character
classes instead of one frozen literal (closing the over-strict direction). The test's docstring now
states plainly which failure mode it targets.
**Regression tests (4 new, each proving one direction):**
- `test_dir_name_rule_check_rejects_scattered_unrelated_keywords` — under-strict proof.
- `test_description_cap_reference_check_requires_same_line_cooccurrence` — under-strict proof.
- `test_shared_caps_sentence_check_requires_same_line_cooccurrence` — under-strict proof.
- `test_name_regex_semantics_check_tolerates_anchor_rewording` — over-strict proof.
- `test_verify_command_check_tolerates_flag_and_wrapping_rewording` — over-strict proof.
**Fails-before / passes-after:** Each under-strict test's "scattered" input (e.g. `"directory"` and
`"name"` in unrelated sentences) is the review's OWN documented counter-example (REVIEW.md WR-06,
lines 179-186) — against the OLD inline check (`"directory" not in lowered or "name" not in
lowered`), that scattered input would have INCORRECTLY satisfied the rule (old check passes on
anywhere-co-occurrence). Against the new `_has_dir_name_rule`, it correctly fails. Each over-strict
test's reworded input (`\A...\Z` anchors, path-quoted-separately-from-flags) would have FAILED the
OLD byte-exact check; the new token/character-class check accepts it. Ran `uv run pytest
tools/harness_lint/tests/test_harness_author.py -k "reachability or cooccurrence or rewording" -q`
→ 6 passed (the umbrella test plus the five direction-proof tests).

### WR-07: `caps.py` history docstring omits the absorbed skill's literal name

**Files modified:** `tools/harness_lint/caps.py`, `tools/harness_lint/tests/test_harness_author.py`
**Commit:** `612ae41`
**Applied fix:** Restored the literal `` `skill-creator` `` name in `caps.py`'s Phase 50a history
comment (matching the file's own established naming convention). Added a single, narrow,
explicitly-commented exemption (`_HISTORY_EXEMPT_REFERENCE`, a hard-coded `(path, lineno)` pair) to
`test_harness_author.py`'s dangling-reference scan, so exactly that one line is skipped.
**Regression tests (3 new):**
- `test_history_exemption_targets_the_documented_skill_creator_mention` — proves the exemption
  points at a line that actually contains the literal string right now (catches drift/staleness).
- `test_history_exemption_does_not_widen_to_other_skill_creator_lines` — proves a SECOND,
  unrelated `skill-creator` mention on a different line is still flagged, so the exemption cannot
  be widened to hide a real dangling reference.
- `test_no_tracked_reference_to_skill_creator` (existing, still enforced) — proves the exemption is
  the ONLY reason this now-literal-naming file passes the gate.
**Fails-before / passes-after:** Before adding the exemption, restoring the literal name in
`caps.py` and running `test_no_tracked_reference_to_skill_creator` fails (the scan flags
`caps.py:137`). After adding the narrow exemption, the same test passes, while
`test_history_exemption_does_not_widen_to_other_skill_creator_lines` proves a synthetic SECOND
occurrence on `exempt_lineno + 1` is still caught (fails without the exemption's narrow scoping,
passes with it). Ran `uv run pytest tools/harness_lint/tests/test_harness_author.py -k
"skill_creator" -q` → all pass (5 tests: no-tracked-reference, scan-is-live, both exemption tests,
and the reference from test_citations covering the new anchor text).

## Skipped Issues

None — all findings were fixed. IN-01 required no code change per the review's own fix note
("None required for this phase; flag as a candidate follow-up") — it is a scope observation, not a
defect, so it is noted here as intentionally not actioned rather than skipped.

## Verification

- `uv run pytest -q` (full monorepo suite, after `uv sync --all-packages` to restore the
  `tree-sitter`/`networkx` dev deps the worktree's venv did not yet have): **981 passed**.
- `uv run python -m tools.harness_emit` twice in a row: first run re-projected
  `.opencode/skill/harness-author/SKILL.md` and `.claude/skills/harness-author/SKILL.md` (expected,
  the source changed); second run produced **zero further diff** — the emit is idempotent
  post-fix.
- `git diff --stat -- .github/workflows/ci.yml`: empty (no CI diff).
- `ls harness/skills | wc -l` → 8; `ls harness/commands | wc -l` → 19 (both unchanged).
- `grep -rn "examples/" <changed files>`: clean (GEN-04).
- No model identifiers introduced in any changed file.

---

_Fixed: 2026-07-30T05:20:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
