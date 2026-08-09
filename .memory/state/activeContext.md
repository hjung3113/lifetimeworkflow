---
updated: "2026-08-10"
---

# activeContext — volatile session hint (COMMITTED)

> DATA AUTHORITY — on a data conflict, `contracts/` and `docs/adr/` win over
> `.memory/state/`. This is a session progress log, not a reason to re-verify grounded work.
> No secrets, tokens, credentials, or PII here.
> The SessionStart injector injects only a *pointer* to this file, never its body.

## In flight

- Route: none — between phases
- Step: —
- Next command: `/gsd:plan-phase 54` (finish v2.7) or `/gsd:new-milestone`

**v2.7 Real-Target Adoption is 3 of 4 phases shipped.** Nothing is mid-edit; working tree clean and
`origin/main` carries everything through `99befe1`. Phases 51, 52 and 53 are merged (PR #9); Phase
54's SC-1 landed separately (PR #10) along with two silent-gate fixes, and PR #11 cleaned the docs
for internal distribution.

The three lines above are the route state `/flow` §2 prescribes, written by `/checkpoint` and
surfaced by `/orient`'s pointer payload — no new state file, no new writer, no new reader.

Final gate state: core **1078 passed / 8 snapshots**; ruff ratchet **67/67 at baseline**;
`contract-drift`, `emit-drift` and `stale-derived` all exit 0. Surface: **6 contracts, 19 commands,
8 skills**.

## Next

- **Phase 54 Surface Budget Closeout** — SC-1 (the shared `"dir"`-filter helper, DEBT-01) is done.
  SC-2 (closeout counts no greater than the milestone baseline), SC-3 (runtime-surface changes
  originate under `harness/`) and SC-4 (no model identifiers in v2.7 artifacts) are unverified.
- **Template distribution is decided but not built.** Internal use only, no license file. The
  structural problem stands: `.planning/` is roughly half the tracked files, and GSD reads a
  populated `.planning/` as an already-initialized project — worse for a consumer than an absent
  one. Both READMEs now warn about this in prose; a filtered distribution snapshot is the fix and
  has not been made.

## Carry into the next milestone

- **A check that cannot fail** — still this repo's defect class, and it recurred twice during v2.7.
  `/contract-check` stage 1 looped over six schemas with zero sibling instances, so it exited 0
  having validated nothing, for the whole life of the command. And a re-run no-op was being proven
  with a git path-set delta, which cannot see a file whose content was rewritten in place. Both are
  fixed and both now have a guard that was observed failing. Mutation-test every new or edited
  assertion; a gate never seen to fail is decoration.
- **Fixtures do not substitute for the real target.** 1071 fixtures were green while `/adopt` was
  appending a duplicate `END HARNESS-MANAGED` marker to a third party's `AGENTS.md` on every run.
  Only repeated runs against a real repository exposed it.
- **`docs/adr/**` is on `CONSTITUTION_GLOBS`** alongside `contracts/**` and `docs/glossary.md`, so
  authoring an ADR is human-gated exactly like the glossary. When an agent must not write: prepare
  the edit as an off-plane script asserting an exact single match per replacement, and have the human
  run it — `.planning/quick/260729-wdi-*/apply.sh` is the worked example. Never forge
  `GOLDEN_APPROVE_HUMAN`; never use `HARNESS_DEV_BYPASS` on a plane a gate protects.
