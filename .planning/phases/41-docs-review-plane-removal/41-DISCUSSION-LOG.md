# Phase 41: Docs-Review Plane Removal - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-27
**Phase:** 41-docs-review-plane-removal
**Mode:** `--auto --chain` — every question auto-resolved to the recommended option, no user prompts.
**Areas discussed:** Deletion scope, Replacement policy, Ordering & commit discipline, Surviving
references & re-emit, Verification / done-condition

`[--auto] Selected all gray areas: Deletion scope, Replacement policy, Ordering & commit discipline,
Surviving references & re-emit, Verification / done-condition.`

---

## Deletion scope — what leaves with the plane

| Option | Description | Selected |
|--------|-------------|----------|
| CER-05 list + its orphans (registry, derived staleness queue, adoption proposal path) | Delete everything whose only consumer is `tools.docs_guard`; leaves no stranded import | ✓ |
| CER-05 list literally | Delete only what the roadmap bullet names; `docs_staleness.py` keeps importing a deleted package | |
| CER-05 list minus the registry | Keep `doc-dependencies.toml` as documentation of doc↔source links | |

**Auto-selection:** `[auto] Deletion scope — Q: "Does anything beyond the CER-05 list leave with the
plane?" → Selected: "CER-05 list + its orphans" (recommended default)`
**Notes:** Option 2 breaks at import time — `docs_staleness.py:158` names `tools.docs_guard`, and CI
`:351` runs its test in the very job being deleted. Option 3 keeps a file whose only validator is
gone, which is the ceremony v2.5 exists to remove. Recorded in CONTEXT.md as a scope *clarification*
(same plane), not an expansion — the owner's binding constraint forbids growth, not completeness.

---

## Replacement policy

| Option | Description | Selected |
|--------|-------------|----------|
| No replacement | Plane deleted outright; authority is ADR-0012 (CI + the merge) | ✓ |
| Severity flip / advisory-only job | Keep the guard, downgrade findings to warnings | |
| Successor lightweight doc-link checker | Smaller tool, same idea | |

**Auto-selection:** `[auto] Replacement policy — Q: "What replaces the review obligation?" →
Selected: "No replacement" (recommended default)`
**Notes:** Option 2 is provably dead, not merely undesired: `guard.py:383-399` classifies `BROKEN`
before any staleness check and `cli.py:6-13` exits 1 on `BROKEN` regardless of severity — and every
v2.5 deletion produces `BROKEN`. Option 3 is a new gate; the owner's binding constraint answers it
with NO by default. No new ADR: ADR-0012 is already `accepted` and supersedes ADR-0010.

---

## Ordering & commit discipline

| Option | Description | Selected |
|--------|-------------|----------|
| Unbind first, then delete → stage → commit → verify → amend-if-red | Phase 40's measured ordering | ✓ |
| Verify before commit | Conventional, but reds by construction here | |
| One atomic mega-commit | Simple history, unreviewable diff | |

**Auto-selection:** `[auto] Ordering — Q: "What order and commit shape?" → Selected: "Unbind first,
delete → stage → commit → verify → amend-if-red" (recommended default)`
**Notes:** `tools/adoption_scan/destinations.py:217` reads `git ls-files`, so a tracked deletion reds
~3 tests until staged and committed; Phase 40 measured 3→1→0. `git commit -- <pathspec>` every time
(28-01 swept a sibling's files into a shared-index commit).

---

## Surviving references & re-emit

| Option | Description | Selected |
|--------|-------------|----------|
| Source-first + full prose/test sweep in-phase | Edit `harness/**`, re-emit, fix every asserting test and index | ✓ |
| Source-first, defer prose to Phase 45 (Projection Repair) | Smaller phase, stale docs in between | |
| Hand-edit emitted trees | Fastest, reds `emit-drift` | |

**Auto-selection:** `[auto] Surviving references — Q: "How far does the sweep go?" → Selected:
"Source-first + full prose/test sweep in-phase" (recommended default)`
**Notes:** Option 2 leaves `AGENTS.md` advertising a deleted command and skill — a doc that lies is
the failure mode the deleted plane was built to prevent, so it must not be *created* by the deletion.
Option 3 is excluded structurally by the `emit-drift` gate.

---

## Verification / done-condition

| Option | Description | Selected |
|--------|-------------|----------|
| Green fan-in + zero-residue sweep + rebaselined drift/ratchet | Mechanical, checkable | ✓ |
| Green suite only | Misses dangling `needs` and orphan prose | |
| Add a regression test asserting the plane stays deleted | A new gate — forbidden by the binding constraint | |

**Auto-selection:** `[auto] Verification — Q: "What proves the phase done?" → Selected: "Green fan-in
+ zero-residue sweep + rebaselined drift/ratchet" (recommended default)`
**Notes:** Explicitly recorded that **no mutation-proof table is owed** — the anti-pattern rule
governs changes that add or claim a control, and this phase adds none. Option 3 would grow the
surface the milestone is shrinking.

## Claude's Discretion

- Task decomposition and plan count.
- Whether the prose/test sweep is one task or folded into each deletion task.
- Whether the derived reference page removal rides with the contract-removal commit.

## Deferred Ideas

- Full `gate-model` skill deletion → Phase 44 (CER-08).
- Adoption ↔ task-control decoupling + `_CATEGORY_GLOBS` install-set repair → Phase 42 (CER-06, PROD-01).
- `memory_regen` active-task block strip → Phase 43 (CER-07).
- `ruff check` scope / vendored-tree excludes → settled in Phase 34, not reopened.
