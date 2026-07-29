# 12. CI and the Merge as Decision Authority

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-26
- **Deciders:** kimhyojung (CODEOWNERS)
- **Supersedes:** 0001, 0010
- **Superseded by:** —
- **Complements:** [ADR-0011](0011-gate-right-sizing-dev-light-ci-strong.md)

## Context and Problem Statement

The v2.5 "De-ceremony" milestone deletes roughly 16,000 lines of self-verification machinery
(Phases 40-44) and takes the number of gates a human must personally *author* from five to zero.
Every one of those deletion phases needs a written decision to cite instead of re-litigating scope
each time — otherwise "should we keep this gate?" gets re-argued five separate times, which is
itself ceremony. This ADR is that written decision, landed once, for the whole milestone.

Three things must be settled together, because they interlock: (1) where does enforcement live once
in-session human-authored gates are gone — the answer has to be a specific, nameable authority, not
"nothing enforces this anymore"; (2) what, precisely, is v2.5 committing to delete, so a later phase
narrowing or widening its own scope has a fixed point to compare against; (3) a boundary the round-1/
round-2 scoping panel got wrong and the round-3 correction fixed — the panel initially deleted the
*product's* whole lifecycle on the reasoning "GSD already covers this," which is true of this
checkout and false of every checkout this harness is installed into. That boundary needs a name and
an operative rule so Phase 42 (and beyond) does not re-make the same mistake.

Two decision records already exist that this ADR must reconcile rather than ignore: ADR-0001's
four-member constitution-plane declaration (`golden/**` included) will become false once Phase 44
relocates golden out of the core, and ADR-0010's docs-review obligation model is the exact kind of
in-session, human-authored review gate that v2.5's "gates a human must author: five to zero" goal
retires. Per the supersede-don't-edit convention, both are addressed here rather than hand-edited.

## Decision Drivers

- Every later v2.5 deletion phase (40-46) needs a single, citable, already-ratified authority instead
  of a fresh human-ratification gate per phase — re-litigating scope five times is itself ceremony.
- The v2.5 binding constraint (owner): never expand scope beyond the harness's stated purpose by
  adding verification gates, security layers, or ceremony; default answer to "should we also gate X?"
  is NO; the surface may not grow without retiring at least as much.
- "Machines gate, humans ratify" (ADR-0001) still holds; what changes is WHERE ratification lives —
  moving from a growing set of in-session human-authored gates to the existing CI fan-in and the
  merge to `main`, which were already the authoritative acceptance point for code changes even before
  this ADR.
- The round-3 correction to the v2.5 scoping panel: GSD (this checkout, Claude Code, never installed)
  is not a substitute for a product capability, because GSD is never shipped to a target monorepo —
  only what `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` installs is. Conflating the two
  would delete real product surface under a false "already covered" premise.
- Between this ADR's ratification and Phase 44's actual code move, `docs/adr/0001`'s four-member
  constitution-plane list and the code that enforces it (`tools/hooks/contract_guard.py`'s
  `CONSTITUTION_GLOBS`, pinned by `tools/hooks/tests/test_contract_guard.py:352-375`) will KNOWINGLY
  disagree with this ADR's stated intent. That gap must be named here, not discovered later as a bug.
- This phase's own human-ratification checkpoint must not become the seed of a new standing gate —
  that would contradict the milestone's own five-to-zero goal in the act of pursuing it.

## Considered Options

1. **No ADR — cite the ROADMAP directly from each deletion phase's PR description.** *Rejected:* the
   ROADMAP is a mutable planning document, not an append-only, human-ratified record; a later PR
   could silently reinterpret scope with no tamper-evident trail, and there is no single ratified
   place to record the DEV/PRODUCT boundary correction so every subsequent phase inherits it.
2. **Five separate ADRs, one per topic (CI+merge authority; deletion enumeration; DEV/PRODUCT
   boundary; ADR-0011 acceptance; bash-residual declaration).** *Rejected:* these topics were reached
   together, in the same scoping round, for the same reason (closing the human-ratification-gate
   pattern before the deletion phases start); splitting them multiplies the ratification cost the
   milestone is trying to eliminate, and ADR-0010 already establishes the in-repo precedent of
   adopting several tightly-reached clauses "as ONE ratified unit."
3. **One ADR, adopted as ONE ratified unit, covering exactly the clauses reached together in this
   phase (chosen).** Mirrors ADR-0010's "adopted as ONE ratified unit" structure. A future phase that
   needs to reverse only part of this decision writes a new, narrower superseding ADR against the
   specific clause — the append-only convention already supports partial reversal via a fresh record;
   it does not require this record to be pre-split.

## Decision Outcome

**Chosen: Option 3 — one ADR, adopted as ONE ratified unit, six clauses:**

### (a) CI and the merge are the authority

Enforcement's authoritative home for this repository is the CI fan-in (contract-drift, golden
parity, ruff ratchet, docs-guard, emit-drift, workspace check, core-suite) and the merge to `main`
being the acceptance point — under whatever review policy this repository applies at that merge. This
ADR does not assert that CODEOWNERS review is enforced by GitHub branch protection as an operational
fact; branch protection was not confirmed during this phase's research (see 39-REVIEWS.md, Codex
finding). What is asserted is narrower and verifiable: CI + the merge, under this repository's
applicable review policy, is where acceptance happens, replacing the previous pattern of adding a new
in-session, human-authored gate for every new concern.

### (b) The v2.5 deletion enumeration — intent recorded at ratification time

The following surfaces are what Phases 40-44 target for deletion or relocation, reproduced from
`.planning/ROADMAP.md` (the v2.5 De-ceremony section, Phase 40-44 detail) at the date of this ADR's
ratification:

**Phase 40 — Self-Gate Teardown.** `tools/skill_registry` (611 LOC), `harness/skills/registry.lock`,
CI job `registry-lock` and its `gate.needs` entry.

**Phase 41 — Docs-Review Plane Removal.** `tools/docs_guard` (6110 LOC), the review ledger, hook
`ledger_guard` and its `path_deny_globs` entry, the `/docs-update` command, skill `docs-upkeep`,
`contracts/harness/docs/*`, CI job `docs-guard` and its `gate.needs` entry.

**Phase 42 — Adoption Decoupling + Install-Set Repair.** This phase is a decoupling, not a deletion:
it drops task-control coupling from `adoption_apply` and repairs `_CATEGORY_GLOBS` (adding the
surviving `tools/**` that today ships commands and CI a target never receives). It is named here as a
non-deletion so this enumeration is not misread as exhaustive-of-deletions-only.

**Phase 43 — Lifecycle Plane Removal.** 8 `tools/` packages (7021 LOC), the 7 task-control contracts,
commands `intake`, `phase-gate`, `handoff`, `discipline`, hook `resume_gate`, the 5 discipline
skills, `harness/{capabilities,disciplines,risk-policy}.toml`, `.workflow/tasks/`, CI job
`lifecycle-eval` and its `gate.needs` entry.

**Phase 44 — Non-Goal Surface Removal.** `secret_scan` (no replacement job), `deny-domains.*`,
`gate-registry.json` and their `DATA_CONTRACT_PATHS` entries, `tools/memory_ui` (1756 LOC),
`tools/strangler_guard` and `/strangler-step`, `/pipeline`, `pipeline-map`, and `[pipeline].edges`,
skill `gate-model`, `/component`'s topology half, and the golden stack's relocation to
`examples/log-parser/` — all one phase, not two.

This clause records the enumeration as **intent at the ratification date**. A later phase narrowing
or widening its own scope relative to this list does NOT falsify this ADR and does NOT require
superseding it — the enumeration is a point-in-time record of what was agreed when this ADR was
ratified, not a standing constraint on how Phases 40-44 execute.

### (c) The DEV/PRODUCT boundary and its operative rule

**DEV** is this checkout — Claude Code plus GSD, the planning/execution harness a developer works
inside. GSD is never installed into a target monorepo. **PRODUCT** is what
`tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` actually installs into a target monorepo when
`/adopt` runs — a narrower, named, shipped set distinct from DEV. The emitter,
`tools/harness_emit/generate.py:41-43`, projects this checkout into itself (`.claude/` and
`.opencode/`); it is not the install channel and does not determine what a target repository
receives.

**Operative rule:** no product capability may be declined on the ground that GSD covers it; only a
named shipped artifact may cover it. A capability is "covered" only if it appears in
`_CATEGORY_GLOBS` (or an equivalent named, shipped artifact) — never by pointing at this checkout's
own tooling, which the target repository will never see.

### (d) ADR-0001's constitution-member list is superseded; ADR-0010 retires

This ADR supersedes ADR-0001's four-member constitution-plane declaration
(`contracts/**`, `docs/adr/**`, `golden/**`, `docs/glossary.md`) to the extent that `golden/**`
leaves the constitution-plane core: per clause (b), Phase 44 relocates the golden stack to
`examples/log-parser/`. ADR-0010's human-docs-review obligation model retires — it is exactly the
kind of in-session, human-authored review gate that v2.5's "gates a human must author: five to zero"
goal removes; its deletion is executed in Phase 41.

Between this ADR's ratification and Phase 44's actual code move, `tools/hooks/contract_guard.py`'s
`CONSTITUTION_GLOBS` and the pinned test `tools/hooks/tests/test_contract_guard.py:352-375` will
KNOWINGLY still enforce `golden/**` as a fourth member. This is named here as an **expected,
temporary ADR-vs-code inconsistency assigned to Phase 44** — not a defect of this ADR, and not
something Phase 39 or any intervening phase is expected to reconcile early.

### (e) The bash surface is a permanent residual by design

ADR-0011's "What this deliberately accepts" section already names the residual: with
`HARNESS_DEV_LIGHT` set, a dev session's writes are not screened in-editor, including `secret_scan`
and `ledger_guard`; a secret or a self-authored ledger row is caught only at CI/PR review, not at
write time. `.planning/STATE.md`'s per-tool-deny-spelling finding independently documents the
underlying gap (`"uv *": "allow"` in `harness/permission-matrix.json` bypasses the `Write|Edit`-only
matcher). This ADR declares both as a **permanent residual by design**, not a temporary gap awaiting
a future spelling-independent bash-deny mechanism (the v2.4 SEAL-02/03 direction ADR-0011 already
cut). RAT-4, RAT-5, and the per-tool deny spelling close as obsolete-by-deletion for this reason,
recorded in `.planning/STATE.md`.

### (f) This phase's human checkpoint is a one-time transition, not a standing gate

The human-ratification checkpoint used to land this ADR (Task 1 of the plan that produced it) is a
**one-time transition** step for Phase 39 only. It exists because this is the milestone's single
hinge point — the decision every later deletion phase cites — and a decision of that weight is worth
one deliberate human read. No new recurring human-authored gate is created by this milestone as a
result: this checkpoint does not repeat for Phases 40-46, and its existence here is consistent with,
not contrary to, the v2.5 de-ceremony goal of reducing human-authored gates from five to zero.

## Consequences

- **Good:** every later v2.5 deletion phase (40-46) has one fixed, citable decision instead of
  re-litigating scope; the milestone's binding constraint (surface may not grow without retiring at
  least as much) is honored by this ADR's own shape — one record replacing what would otherwise be up
  to five separate future ratification gates.
- **Good:** the DEV/PRODUCT boundary and its operative rule are now a standing citation available to
  Phase 42 and any phase tempted to decline a product capability because "GSD already does this" —
  closing exactly the round-1/round-2 scoping mistake the round-3 correction fixed.
- **Accepted / temporary inconsistency:** between this ADR and Phase 44's actual code move,
  `tools/hooks/contract_guard.py`'s `CONSTITUTION_GLOBS` and the pinned test
  `tools/hooks/tests/test_contract_guard.py:352-375` will KNOWINGLY still enforce `golden/**` as a
  fourth constitution-plane member, even though this ADR declares golden leaves the core. This is
  expected and assigned to Phase 44 — not a defect of this ADR, and repeated here (per this ADR's own
  Decision Outcome clause (d)) so a future reader of only the Consequences section still finds it
  without re-deriving it.
- **Accepted / permanent:** the bash surface (`HARNESS_DEV_LIGHT` in-editor screening gaps for
  `secret_scan` and `ledger_guard`, and the per-tool deny-spelling gap) is a permanent residual by
  design, not a temporary state — RAT-4, RAT-5, and the per-tool deny spelling close as
  obsolete-by-deletion rather than carrying forward as future work.
- **Neutral:** this ADR's clause (b) enumeration is a point-in-time record; Phases 40-44 executing
  with a narrower or wider scope than listed here does not require a superseding ADR (see clause (b)).
- **Bad / accepted:** bundling six clauses into one ratified unit raises the cost of a future partial
  reversal — reversing any single clause requires a new ADR that supersedes this one narrowly, which
  is more work than reversing a single-topic record would be. This mirrors ADR-0010's precedent and is
  accepted for the same reason: these six clauses were reached together, in one scoping round, for one
  purpose (closing the human-ratification-gate pattern before Phase 40 starts).

## Links

- Supersedes (constitution-member list only, per clause (d)):
  [ADR-0001](0001-walking-skeleton-golden-core.md).
- Supersedes (retirement, per clause (d)): [ADR-0010](0010-human-docs-review-obligation-model.md).
- Complements (ratifies, does not change): [ADR-0011](0011-gate-right-sizing-dev-light-ci-strong.md).
- Design authority: `.planning/research/v2.5-scoping-FINAL.md` (the DEV/PRODUCT boundary round-3
  correction); `.planning/ROADMAP.md` (v2.5 De-ceremony section, Phase 39-46 detail);
  `.planning/REQUIREMENTS.md` (CER-01, CER-02, CER-03).
- Enforcement code referenced: `tools/hooks/contract_guard.py` (`CONSTITUTION_GLOBS`);
  `tools/hooks/tests/test_contract_guard.py:352-375` (the pinned four-member mutation-proof test,
  Phase 44's target); `tools/adoption_scan/destinations.py::_CATEGORY_GLOBS` (the product install
  set); `tools/harness_emit/generate.py:41-43` (the DEV-checkout emitter).
- Disposition record: `.planning/STATE.md` (RAT-4, RAT-5, per-tool deny spelling — obsolete-by-
  deletion; SEAL-05 — withdrawn).
