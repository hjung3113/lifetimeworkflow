---
quick_id: 260722-1iq
slug: glossary-constitution-plane-drift
date: 2026-07-22
status: complete
commits:
  - 732a0d5  # RED
  - 6d74a50  # A — enforcement
  - 378f8ba  # B — GEN-04 prose
  - f98d63a  # C — registry repoint
---

# Summary — constitution-plane enforcement drift for `docs/glossary.md`

## What was wrong

`docs/adr/0001-walking-skeleton-golden-core.md:48` — accepted 2026-07-08, never superseded —
declares a four-member constitution plane. The Phase-4 enforcement stack implemented three. For two
weeks `docs/glossary.md` was agent-writable while `.memory/README.md`, `AGENTS.md`,
`gate-model/SKILL.md` and the ADR itself all said it was protected.

Not stale prose. **Enforcement drift from an existing accepted decision** — the documents were right
and the code was wrong, which is the opposite of the usual direction and the reason it was nearly
repaired backwards.

## How the decision was reached, and the mistake worth recording

Two Claude audits (one of them mine) recommended the **opposite** repair: delete `docs/glossary.md`
from `.memory/README.md`'s plane table and treat the hook as authoritative. The reasoning cited
ADR-0010:18, which classifies the glossary as human-doc corpus.

**ADR-0010 is `Status: proposed`.** ADR-0001 is `accepted`. In an append-only ADR system an
unratified record cannot override a ratified one, and I used one as if it could. A second error
compounded it: I argued "a constitution-plane file would not need a review binding", while
`contract-graph-adr-0009` — a binding with a `docs/adr/**` target — sat in the same registry as a
standing counterexample I had already read.

An external audit (codex sol, medium) caught both and supplied the principle now written into three
surfaces:

> Constitution ownership controls **who may edit**. A review binding controls **when a human owes a
> review**. They are orthogonal.

The human ratification gate did its job here, and what it caught was the agent's reasoning, not a
typo. That is the case for the gate existing.

## What changed

**RED first** (`732a0d5`) — 14 failed / 126 passed against unfixed code, across all five surfaces.
The passes are the evidence collection succeeded rather than the run erroring.

**(A) `6d74a50`** — `contract_guard.CONSTITUTION_GLOBS` and its deny message (which named three
members and so could not explain a glossary refusal), `harness/permission-matrix.json` +
`_note`, `.github/CODEOWNERS`, `AGENTS.md` non-negotiable 3, `harness/skills/gate-model/SKILL.md`
re-emitted to both runtime trees, and `.memory/README.md`.

The glossary is a **literal path** everywhere, never `docs/**`. Its plane table in
`.memory/README.md` was already correct and was left untouched; only the stale enforcement sentence
changed. Two documents carried the identical fossil — *"runtime enforcement lands in Phase-4 hooks;
this rule is advisory until then"* — true when written, never revisited.

Every surface now records that ADR-0001 declares the membership and the config implements it, so
the next person to add a member is told where the decision has to happen first.

**(B) `378f8ba`** — `docs/explanation/template-and-instances.md` said the GEN-04 guard has one
sanctioned exception, `root`; the guard exempts `root|persona|test_paths`. Kept the "one sanctioned
exception" framing because it is accurate — the exception is a **place** (the `[instance]` +
`[[languages]]` slot per ADR-0002 (c)), not a line. Documentation only: all three classes already
had independent positive tests, so adding one would have asserted a defect that does not exist.

**(C) `f98d63a`** — `lifecycle-eval-shadow-metrics` was bound only to `lifecycle_eval/runner.py`,
which has zero occurrence of `lane_override`; `risk_router/router.py:203-211,235` is what validates
`human_override` as `{lane, reason}` and preserves the override audit with the policy hash. Added
that source. The metric row stays — a real observable whose collector is not built yet.

## Verification

| Gate | Before | After |
|---|---|---|
| `uv run pytest -q` | 1480 passed, 8 snapshots | **1500 passed, 8 snapshots** |
| `contract_drift.drift` | OK | OK |
| `harness_emit` + `git status --porcelain` | clean | clean on a second run |
| `tools/harness_lint` | green | 323 passed |
| `tools.docs_guard` | exit 1, 6 × broken-binding | **exit 1, same 6, no new reason** |
| `decide("docs/glossary.md")` | **ALLOW** | **DENY** |
| `decide("docs/how-to/task-lifecycle.md")` | ALLOW | ALLOW |

### Mutation proofs — all four red the named test

| Mutation | Test that reds |
|---|---|
| delete only `docs/glossary.md` from `CONSTITUTION_GLOBS` | the 7 glossary rows + `test_every_declared_plane_member_is_independently_enforced` |
| delete only the matrix entry | `test_glossary_denied`, `test_constitution_and_secret_paths_denied[docs/glossary.md]`, `test_constitution_paths_denied_globally` |
| `exclusions` **copies** the glob list instead of importing it (CR-02 shape) | `test_constitution_globs_is_the_exported_object` |
| broad `docs/**` instead of the literal file | `test_neighbouring_docs_paths_are_not_constitution` + the set-pinning assertion |

The last one matters most: a well-meaning `docs/**` "fix" would deny the entire human-doc tree and
still satisfy every glossary row. It cannot pass.

`test_every_declared_plane_member_is_independently_enforced` deletes each member in turn and requires
its own probe to stop being denied, so no member can be dropped while the suite stays green on
another member's row. It also pins the set to ADR-0001's four — a fifth cannot appear without a
superseding ADR.

### Correction to the plan, recorded not silently fixed

`TERRA-PLAN.md` §3 predicted `docs_guard` exit **0** at baseline. It is exit **1** (6 required
bindings, no ledger). The plan hedged that exact cell — *"must be checked against the actual CLI
behavior before claiming an exit code"* — and the hedge earned its place.

The plan's highest-risk prediction held: adding the glossary to `CONSTITUTION_GLOBS` moves
`exclusion_reason` from `None` to `constitution-plane` and leaves the corpus untouched — uncovered
**7 → 7**, findings **6 → 6**. Corpus membership and drafting exclusion are distinct. Measured in
process before any edit, and re-confirmed after.

## Deliberately not done

- `docs/adr/0001-*.md` — accepted authority, untouched.
- `docs/adr/0010-*.md` — still `proposed`. Ratifying it is the human's next step.
- `docs/.docs-review-ledger.toml` — **still absent**, as required. Human-authored only.
- `HUMAN_CORPUS`, `uncovered_max`, `binding_min` — not the defect; never touched to force green.

## Next, in order

1. Human ratifies ADR-0010 (`proposed` → `accepted`, fill Date + Deciders).
2. Fresh ledger proposal regenerated against final digests — four of the eight bindings' digests
   moved in this task (`gate-model-permission-surface`, `memory-plane-declaration`,
   `gen04-core-instance-split` targets; `lifecycle-eval-shadow-metrics` sources + identity).
3. Human authors and commits the first ledger.

`lifecycle-eval-shadow-metrics` is now a **repointed** binding. Once a ledger exists it is amber for
exactly one cycle by design — the human commit that lands the new-shape row IS the ratification.
That amber is not a regression, and `uncovered_max` / `binding_min` must not be moved to clear it.
