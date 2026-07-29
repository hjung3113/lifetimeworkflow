---
phase: 39-decision-boundary-v2-5-a
reviewed: 2026-07-26T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - docs/adr/0012-ci-and-merge-as-decision-authority.md
  - docs/adr/0001-walking-skeleton-golden-core.md
  - docs/adr/0010-human-docs-review-obligation-model.md
  - docs/adr/0011-gate-right-sizing-dev-light-ci-strong.md
  - docs/adr/README.md
  - .planning/STATE.md
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 39: Code Review Report

**Reviewed:** 2026-07-26
**Depth:** standard (decision-record accuracy review, no executable code in scope)
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This phase is a decision-record-only change: ADR-0012 (new), two supersede-marker-only edits to
ADR-0001/0010, ADR-0011's frontmatter completion + ratification note, an index update, and four
append-only STATE.md rows. All six code/artifact citations in ADR-0012 were verified to resolve and
accurately describe what they point at:

- `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` — resolves, module docstring/comments
  confirm the "product install set" characterization.
- `tools/harness_emit/generate.py:41-43` — resolves to `OPENCODE_DIR`, `CLAUDE_DIR`,
  `MANIFEST_PATH` definitions; accurately supports the "projects this checkout into `.claude/` and
  `.opencode/`" claim.
- `tools/hooks/contract_guard.py`'s `CONSTITUTION_GLOBS` — resolves, value is the exact four-member
  list ADR-0012 describes (`contracts/**`, `docs/adr/**`, `golden/**`, `docs/glossary.md`).
- `tools/hooks/tests/test_contract_guard.py:352-375` — resolves to
  `test_every_declared_plane_member_is_independently_enforced`, the mutation-proof test ADR-0012
  describes.
- `harness/permission-matrix.json`'s `"uv *": "allow"` — resolves at line 9, matches ADR-0012 clause
  (e) and the STATE.md deny-spelling row verbatim.
- Commit `bc9a6d9` — a real commit ("feat(hooks): guard commands degrade instead of deadlock, and
  dev can opt out"), cited from ADR-0011's Ratification note and STATE.md; description matches the
  commit's actual content.

Supersede-don't-edit integrity holds: `git diff 587e18a..HEAD` on `docs/adr/0001-*.md` and
`docs/adr/0010-*.md` shows only the `Status:`/`Superseded by:` frontmatter lines changed; decision
bodies are byte-identical. `docs/adr/README.md`'s index Status column agrees with each ADR's own
frontmatter (0001 → superseded by 0012, 0010 → superseded by 0012, 0011 → accepted, 0012 →
accepted). STATE.md's Deferred Items table gained exactly 4 new rows (no rows removed), and the
marker `v2.5 P39, ADR-0012` appears exactly 4 times as expected. No internal contradiction was found
in clause (a) (it explicitly disclaims asserting branch-protection as an enforced operational fact,
consistent with the unconfirmed-branch-protection finding in `39-REVIEWS.md`) or in clause (b) (it
carries the "intent recorded at ratification time" scoping sentence).

The one material issue found is that clause (b)'s per-phase enumeration, presented as "reproduced
from `.planning/ROADMAP.md`," silently drops named deletion-target components for two of the five
phases it enumerates. This doesn't invalidate the ADR (clause (b) explicitly disclaims being a
standing constraint on Phase 40-44 execution), but it does mean a reader relying on ADR-0012 alone —
rather than re-reading the ROADMAP — gets an incomplete picture of what those two phases were
scoped to touch as of ratification.

## Warnings

### WR-01: Clause (b)'s Phase 41 enumeration omits the "unbind 8 `[[binding]]` rows" step

**File:** `docs/adr/0012-ci-and-merge-as-decision-authority.md:99-101`
**Issue:** Clause (b) states the Phase 41 enumeration is "reproduced from `.planning/ROADMAP.md`
... at the date of this ADR's ratification." The ROADMAP's Phase 41 entry
(`.planning/ROADMAP.md:207-212`) begins "unbind the 8 `[[binding]]` rows, then delete
`tools/docs_guard` ..." — the unbind step is a named, distinct action, not a sub-detail of the
deletion list. ADR-0012's reproduction starts directly at "`tools/docs_guard` (6110 LOC), the review
ledger, hook `ledger_guard` ..." and never mentions the binding-row unbind step at all.
**Fix:** Either amend the ADR text to include the omitted step (not possible post-ratification per
the append-only/immutable convention — accepted ADRs are not edited), or, since this ADR is already
`accepted`, note the gap in a subsequent phase's SUMMARY/STATE.md entry so Phase 41's actual scope
is not silently narrower than the ADR's "reproduced from ROADMAP" framing implies. At minimum, do
not treat ADR-0012 alone as an exhaustive citation for Phase 41's scope — the ROADMAP entry remains
the fuller source.

### WR-02: Clause (b)'s Phase 43 enumeration omits the `memory_regen` active-task-block strip

**File:** `docs/adr/0012-ci-and-merge-as-decision-authority.md:108-111`
**Issue:** The ROADMAP's Phase 43 entry (`.planning/ROADMAP.md:220-226`) ends with "strip
`memory_regen`'s active-task block (`inject.py:165-195`) keeping the pointer (`:148-162`)." This is
a named, specific deletion-adjacent action (not merely one more package in the "8 `tools/` packages"
count) and is absent from ADR-0012's clause (b) Phase 43 paragraph, which stops at "CI job
`lifecycle-eval` and its `gate.needs` entry."
**Fix:** Same as WR-01 — the accepted ADR cannot be hand-edited to add it back; flag the gap for
downstream readers (e.g., in Phase 43's own plan/summary) rather than relying on ADR-0012's
enumeration as complete for that phase.

## Info

### IN-01: Clause (b)'s Phase 42 enumeration drops the `gate-registry.json` redaction-regex detail

**File:** `docs/adr/0012-ci-and-merge-as-decision-authority.md:103-106`
**Issue:** The ROADMAP's Phase 42 entry additionally specifies "inline `gate-registry.json`'s 7
redaction regexes into `adoption_scan`, live consumer `scan.py:110-112`" — ADR-0012's paraphrase
captures the higher-level intent (drop task-control coupling from `adoption_apply`; repair
`_CATEGORY_GLOBS`) but omits this specific sub-action. Lower severity than WR-01/WR-02 because it is
a sub-detail of an action already named ("drops task-control coupling from `adoption_apply`"),
whereas the WR-01/WR-02 omissions are entire named actions with no partial mention in the ADR text.
**Fix:** No action required for the ADR itself (immutable once accepted); worth keeping in mind
when Phase 42's plan is authored so the redaction-regex inlining isn't assumed out-of-scope just
because ADR-0012 doesn't mention it.

---

_Reviewed: 2026-07-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
