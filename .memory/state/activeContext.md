---
updated: "2026-07-30"
---

# activeContext — volatile session hint (COMMITTED)

> DATA AUTHORITY — on a data conflict, `contracts/` and `docs/adr/` win over
> `.memory/state/`. This is a session progress log, not a reason to re-verify grounded work.
> No secrets, tokens, credentials, or PII here.
> The SessionStart injector injects only a *pointer* to this file, never its body.

## In flight

- Route: none — between milestones
- Step: —
- Next command: /gsd:new-milestone (v2.6)

**Milestone v2.5 De-ceremony is SHIPPED, ARCHIVED and TAGGED `v2.5`.** Nothing is mid-edit. Working
tree clean; branch `claude/data-pipeline-harness-8aypct` and `origin/main` both carry the work
(PR #5 the milestone close, PR #6 the leftovers — both CI-green on all 11 jobs plus `gate`).

The three lines above are the route state `/flow` §2 prescribes, written by `/checkpoint` and
surfaced by `/orient`'s pointer payload — no new state file, no new writer, no new reader.

Final gate state: core **881 passed / 7 snapshots**, instance **14**; `contract-drift` (core +
workspace), `emit-drift`, `stale-derived` and the ruff ratchet all exit 0. Commands **18**.

## Next

- **v2.6 Minimal Monorepo Core (phases 47–50)** — scoped in ROADMAP, not started. Smallest
  goal-complete subset is v2.5 + 47 + 49. Start with `/gsd:new-milestone`, which writes the fresh
  `.planning/REQUIREMENTS.md` — deliberately absent right now, archived rather than lost
  (`.planning/milestones/v2.5-REQUIREMENTS.md`).
- D-24 is re-openable there as a machine-side check on golden baseline diffs; v2.5's no-growth
  constraint forbade exactly that and is now closed.

## Carry into the next milestone

- **A check that cannot fail** — this milestone's own defect class, eight instances: six across
  phases 40–46, plus two caught during the close itself (phases 43–46 sat unchecked in ROADMAP while
  the Progress table read Complete; CER-01/02/03 read `Not started` against a VERIFICATION recording
  all three SATISFIED). The gates verify that declared things *exist*, never that declarations still
  *mean* something. Mutation-test every new or edited assertion; scope predicates to their section.
- **`docs/adr/**` is on `CONSTITUTION_GLOBS`** alongside `contracts/**` and `docs/glossary.md`, so
  authoring an ADR is human-gated exactly like the glossary. When an agent must not write: prepare
  the edit as an off-plane script asserting an exact single match per replacement, and have the human
  run it — `.planning/quick/260729-wdi-*/apply.sh` is the worked example. Never forge
  `GOLDEN_APPROVE_HUMAN`; never use `HARNESS_DEV_BYPASS` on a plane a gate protects.
