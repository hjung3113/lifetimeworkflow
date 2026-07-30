# Phase 50a: Harness Authoring - Context

**Gathered:** 2026-07-30
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous) — 3 areas, all accepted as recommended

<domain>
## Phase Boundary

Deliver one `harness-author` skill that guides authoring a harness artifact through grounded Q&A with
defaults cited as `path:line` from this checkout, writing output **runtime-neutral under `harness/`
only** (the emitter projects it). It **absorbs `skill-creator`**, keeping skills at 8 → 8 and adding
zero packages, commands or contracts.

Out of the boundary: generating the emitted trees directly, any new gate on hand-authored artifacts
(emit-drift already catches divergence), plugin/hook authoring, and Phase 50b's managed adopt.

</domain>

<decisions>
## Implementation Decisions

### Scope of `harness-author`
- Covers the three artifact kinds the emitter projects from single-file sources: **commands, agents,
  skills**. `skill-creator` covered skills only; the same runtime-neutral-source rule and emit
  round-trip govern all three, so the wider scope is what makes it "harness-author" rather than a
  rename.
- `skill-creator`'s **Step 0 anti-sprawl question** is preserved and generalized to **every kind**:
  "why can't this live in an existing one?" That question is why the surface stayed small; losing it
  in the absorption would be the real regression.
- Q&A asks one grounded question per decision that has a genuine repo default; anything the repo
  already determines is not asked.
- Plugins and hooks are **explicitly out of scope**, stated in the body — they have no analogous
  single-file source shape today, and silence would read as an oversight.

### Grounded defaults
- Every offered default carries a `path:line` that **resolves in this checkout**.
- Citations anchor on **stable names** (a named function, a frontmatter key, a test name) rather than
  bare line numbers, because line numbers drift. A test asserts the cited paths exist.
- Caps are **not restated**: the body points at `tools/harness_lint/caps.py` and the verify test as
  the authority. Restated numbers are a second source that silently goes stale.
- The skill ends by naming the runnable checks — `tools/harness_lint/tests/test_skills.py` and the
  emit round-trip — so verification is an executable step, not an aspiration.

### Absorption mechanics
- **One change**: create `harness/skills/harness-author/` and delete `harness/skills/skill-creator/`
  together, so the skill count is never 9.
- Dependent references move in the same commit: `tools/harness_lint/caps.py` (the pinned skill-name
  set), `tools/harness_emit/emit-manifest.json`, root `AGENTS.md`, and
  `harness/skills/brownfield-adoption/SKILL.md` — then re-emit both runtime trees.
- The pinned-name-set guard is **kept and updated**, not relaxed. It is designed to fail until the set
  matches; that failure is the feature.
- A test asserts **no tracked file references `skill-creator`** after the change — a dangling pointer
  to a deleted skill is a broken product surface, and a one-time manual grep does not keep it fixed.

### Claude's Discretion
- The body's section layout and question wording, provided Step 0 comes first.
- Which specific `path:line` anchors are cited per artifact kind, provided each resolves.
- Whether `references/` holds per-kind templates or the body carries them, subject to the concise-body
  cap.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `harness/skills/skill-creator/SKILL.md` (46 lines) — the source being absorbed: Step 0 anti-sprawl,
  Step 1 shape (name regex `^[a-z0-9]+(-[a-z0-9]+)*$`, dir-name match, description caps, progressive
  disclosure), Step 2 verify, and the note that both runtimes share the same caps.
- `tools/harness_lint/caps.py` — pins the skill-name set and the caps; the authority the body should
  point at.
- `tools/harness_lint/tests/test_skills.py` — enforces caps, regex, dir-name match, routing-trigger
  token, reserved-word/tag bans, and the pinned name set.
- `tools/harness_emit/` + `emit-manifest.json` — projects `harness/` sources into `.opencode/` and
  `.claude/`; the manifest enumerates what is emitted.
- Existing authored surface to cite as examples: 19 commands under `harness/commands/`, agents under
  `harness/agents/` (incl. `orchestrator.md`), 8 skills under `harness/skills/`.

### Established Patterns
- Single-source authoring: `harness/` is the only hand-edited tree; `.opencode/` and `.claude/` are
  generated and never hand-edited. Emit is idempotent and proven by an emit-drift check.
- Consistency gates live in `tools/harness_lint/tests/` and are designed to fail loudly on an
  un-enumerated artifact.
- GEN-04: nothing under `tools/`, `harness/`, `libs/` may name or path-reference `examples/`.
- No model identifiers in any repo artifact.

### Integration Points
- Files referencing `skill-creator` today (all must move together): `AGENTS.md`,
  `tools/harness_emit/emit-manifest.json`, `tools/harness_lint/caps.py`,
  `harness/skills/brownfield-adoption/SKILL.md`, plus the two emitted copies under
  `.opencode/skill/` and `.claude/skills/` (regenerated, not hand-edited).
- Phase 49 left commands at 19 and both command-surface guards pinned; this phase must not disturb
  them.

</code_context>

<specifics>
## Specific Ideas

- Criterion 1 needs a real proof: a test that every `path:line` citation in the skill body resolves to
  an existing file (and, where an anchor name is cited, that the name is present). A skill full of
  plausible-but-dead citations is exactly the failure this criterion exists to catch.
- Criterion 3's "everything it did is reachable" should be checked against `skill-creator`'s actual
  content — Step 0, the shape rules, the shared-caps note, the verify command — not asserted.

</specifics>

<deferred>
## Deferred Ideas

- Plugin/hook authoring guidance — revisit if those gain a single-file source shape.
- A gate blocking hand-authored `.opencode/` / `.claude/` edits — emit-drift already detects it, and a
  new gate contradicts the v2.6 no-growth constraint.

</deferred>
