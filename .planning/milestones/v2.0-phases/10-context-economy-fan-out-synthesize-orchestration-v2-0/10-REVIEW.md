---
phase: 10-context-economy-fan-out-synthesize-orchestration-v2-0
reviewed: 2026-07-13T17:21:32Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - harness/skills/fan-out-synthesize/SKILL.md
  - harness/skills/fan-out-synthesize/references/fan-out-return.schema.json
  - harness/skills/context-budget/SKILL.md
  - harness/commands/fan-out-synthesize.md
  - harness/agents/orchestrator.md
  - harness/commands/orient.md
  - tools/harness_lint/caps.py
  - tools/harness_lint/tests/test_fan_out_return_contract.py
  - tools/harness_lint/tests/test_context_budget_wiring.py
  - tools/harness_emit/tests/test_coexist.py
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-07-13T17:21:32Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Reviewed the Phase 10 (Context-Economy Fan-out/Synthesize) authored source surface: the
`fan-out-synthesize` skill + its return-contract JSON Schema, the `context-budget` skill, the
`/fan-out-synthesize` command, the two wiring edits to `orchestrator.md`/`orient.md`, the
`caps.py` enumeration bump, and the three associated structural test files.

Verification performed beyond static reading:
- Loaded `fan-out-return.schema.json` with a real Draft-2020-12 validator (`jsonschema`) and
  round-tripped valid/invalid payloads (empty `citations`, missing `claims`, extra top-level key)
  — the schema behaves exactly as documented (`additionalProperties: false`, `citations` non-empty,
  `unit`+`claims` required).
- Ran the full `tools/harness_lint` + `tools/harness_emit` suites (280 passed; the one error is a
  pre-existing, out-of-scope missing `snapshot` fixture in `test_emit_determinism.py`, unrelated to
  this phase's files).
- Diffed the `orchestrator.md`/`orient.md` wiring commits directly against git history to confirm
  the edits are additive (renumbered intake steps 3→4-7 with no stale numeric cross-references
  elsewhere in `harness/`, table rows appended, no rows removed).
- Grepped the whole reviewed set for model identifiers, `examples/` path leaks, and domain
  (semiconductor/log-parser) vocabulary — none found; `EXPECTED_SKILLS` (11) and
  `EXPECTED_PERSONAS` (5, untouched) both verified against the actual `harness/skills/` and
  `harness/agents/` directory listings.
- Confirmed the return schema carries no `$ref` into `contracts/` and is self-contained (D-08).

No BLOCKER-level defects found. One WARNING (an inconsistent `$id` convention vs. the two existing
schemas in this repo) and two INFO-level documentation-completeness notes.

## Warnings

### WR-01: `fan-out-return.schema.json` `$id` breaks the repo's established absolute-URI convention

**File:** `harness/skills/fan-out-synthesize/references/fan-out-return.schema.json:3`
**Issue:** Every other `$id` in this repo (`contracts/sample/greeting.schema.json`,
`contracts/normalization/format-conventions.schema.json`, `harness/opencode.config.schema.json`)
uses an absolute (if fictitious) URI scheme — `https://harness.local/...` or
`https://logparser-harness/...`. This new schema instead sets:
```json
"$id": "harness/skills/fan-out-synthesize/references/fan-out-return.schema.json"
```
a bare repo-relative path with no scheme. This is a valid URI-reference under Draft 2020-12 (so it
does not fail the structural gate, which only checks `$schema`/`additionalProperties`/`required`),
but it is inconsistent with the sibling schemas' convention and — because `$id` establishes the
base URI a schema resolves relative `$ref`s against — would resolve differently than the
`https://...` siblings if this schema ever grows a `$ref` (e.g. to a shared `$defs` fragment).
Low risk today (no `$ref` present), but a latent inconsistency worth fixing before another schema
copies this pattern.
**Fix:** Align with the existing convention, e.g.:
```json
"$id": "https://harness.local/skills/fan-out-synthesize/references/fan-out-return.schema.json"
```

## Info

### IN-01: SKILL.md's schema summary omits two documented optional fields

**File:** `harness/skills/fan-out-synthesize/SKILL.md:56-60`
**Issue:** The "Deeper reference" section describes the return shape as "`unit` + `claims[]` of
`{claim, confidence?, citations[]}`" but the actual schema (`fan-out-return.schema.json`) also
declares two more optional top-level fields not mentioned anywhere in the skill prose: `status`
(enum `complete`/`partial`/`not-found`) and `open_questions` (array of strings). A worker dispatcher
reading only the skill body (not the schema file) would not know these fields exist to populate
them, even though they're clearly useful (partial-coverage signaling, unresolved gaps).
**Fix:** Extend the "Deeper reference" bullet to mention the optional `status` and `open_questions`
fields, e.g.: "`unit` + optional `status` + `claims[]` of `{claim, confidence?, citations[]}` +
optional `open_questions[]`".

### IN-02: No runtime/hook enforcement of the return-contract schema — compliance is prompt-only

**File:** `harness/skills/fan-out-synthesize/SKILL.md:33-36`, `harness/commands/fan-out-synthesize.md:25-30`
**Issue:** Both the skill and the command state the return contract is "enforced by this prompt,
not by frontmatter," and no hook, plugin, or validator in `tools/hooks/` or `tools/harness_lint/`
actually validates a worker's returned JSON against `fan-out-return.schema.json` at dispatch/recover
time — the structural test (`test_fan_out_return_contract.py`) only pins the schema file's own
shape, not that any real worker return is checked against it. This appears to be a deliberate
design choice (explicitly documented, consistent with "no bespoke dispatch engine"), so it is not
flagged as a defect, but it means a worker persona (`explorer`) that ignores the prompt's
instruction and pastes raw file content back has nothing at runtime to catch that — the "never raw
file dumps" invariant is unenforced outside prompt discipline.
**Fix:** No action required for this phase (by design); consider tracking as a follow-up item if a
runtime hook surface for subtask returns is ever added (e.g. a `task.execute.after` style
validator), since the schema is already in place to validate against.

---

_Reviewed: 2026-07-13T17:21:32Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
