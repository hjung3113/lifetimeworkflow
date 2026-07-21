# Retrospective

A living record, appended at each milestone close. Newest milestone first; cross-milestone trends
at the bottom.

> **Note on the template's "Cost Observations → model mix" line.** This repo's constraints forbid
> model identifiers in repo artifacts (`PROJECT.md → Constraints → 모델 아이덴티티`). Cost is
> therefore recorded here in session and commit counts only, never by model name.

---

## Milestone: v2.3 — Contract Graph, Brownfield Adoption, Living Docs

**Shipped:** 2026-07-22
**Phases:** 10 (24, 25, 26, 26.1, 26.2, 27, 27.1, 27.2, 28, 29) | **Plans:** 43 | **Tasks:** 58
**Timeline:** 2026-07-19 → 2026-07-22 (3 days, 310 commits)

### What Was Built

Three orthogonal themes over the v2.2 task-control plane:

- **A — contract graph (24–25).** A ratified relationship record, an additive
  `[[contract_graph.relationships]]` slot in both loaders, deterministic lowering of the legacy
  `[pipeline]` edges into the graph, a domain-neutral `compile_graph()` with three stable diagnostic
  slugs, and cycle-safe `direct`/`reverse`/`transitive` queries returning ids *and* paths. The three
  existing conductor surfaces were generalized to consume it. ADR-0009.
- **B — brownfield adoption (26–27.2).** Read-only inventory → evidence-classified plan →
  destination manifest → refuse-by-default apply, carried as an ordinary `.workflow/tasks/` task.
  Promotion is bound to a `(draft_hash, task_revision, git_ref)` triple. `/adopt` plus three
  domain-neutral fixture trees, one deliberately CRLF/BOM-dirty.
- **C — living docs (28–29).** A registry binding source selectors to human-authored targets, a
  committed review ledger holding only id + digest + disposition, a five-state guard with
  uncovered-count non-regression, a derived staleness queue, and the `/docs-update` drive loop.
  ADR-0010.

### What Worked

- **Additive lowering instead of migration.** Choosing "union the legacy slot into the graph" over
  "migrate configs identically-or-fail" meant three live configs stayed byte-unchanged and the whole
  of Theme A landed without touching a single existing caller's signature. The byte-identical linear
  render was pinned by a hardcoded literal-text regression, so "we didn't change today's output" was
  a test, not a claim.
- **Reusing the v2.2 plane rather than building an adoption plane.** `.workflow/adoption/` was
  explicitly rejected in scoping. Adoption got CAS, evidence and HANDOFF for free, and there is no
  second state machine to keep honest.
- **The inserted phases were allowed to be inserted.** 26.1, 26.2, 27.1 and 27.2 exist because
  adversarial review found real defects and the response was a numbered phase rather than a quiet
  patch. 26.2 is the strongest case: it found that 26.1's *own fix* was inert under `re.IGNORECASE`
  and had opened a false-negative seam into the redaction path. A repo that lets a follow-up phase
  contradict the phase before it is a repo that can correct itself.
- **The gate caught an agent's reasoning, not just a typo.** The constitution-plane drift repair
  landed because ADR-0001's four-member plane was enforced as three. Two internal audits recommended
  the *opposite* repair by citing a then-`proposed` ADR over an `accepted` one. That is the failure
  mode the gate model exists for, and it fired.
- **Verification that drives the loop instead of reading it.** Phase 29's re-verification did not
  accept `docs-guard: exit 0`; it drove the loop green → red → green in a throwaway worktree, and
  re-checked that `ledger_guard` still DENYs *after* the ledger existed. It also caught that the
  carry-forward red-list handed to it was stale in three places.

### What Was Inefficient

- **Ordering put the human-only write last, so the `0 → 1` leg was never observed as a ledger
  state.** 29-04 planned a two-round Option B specifically to watch the gate go red; execution ran
  task 3 before the human-only task 2, so the binding was BROKEN both before and after the bounded
  edit — for a strictly prior reason. The transition had to be recovered later, in a worktree.
  A phase that depends on a human write should schedule that write first, not last.
- **A fan-in gate `&&`-chained a member that is designed to exit non-zero.** `28-08-PLAN.md:257`
  chained `docs_guard`, which could not exit 0 before the ledger existed. It had to be satisfied by
  running its members individually. A fan-in command must not `&&` a designed-non-zero gate.
- **A blocking human-verification gate shipped without being exercised**, recorded as such in a
  SUMMARY rather than smoothed over — but it still shipped.
- **Auto-extracted milestone accomplishments were unusable.** The generated MILESTONES.md entry
  pulled 43 SUMMARY one-liners including fragments like "The member." and "Task 1", and had to be
  rewritten by hand at close.
- **`ruff check` still is not a CI gate**, and the debt grew to 617 errors — ~180 of them purely
  because a vendored tree is missing from `extend-exclude`. Three milestones of carrying this.

### Patterns Established

- **Machines gate, humans ratify — now with a third disjoint deny domain.** `ledger_guard` honours
  neither `GOLDEN_APPROVE_HUMAN` nor `HARNESS_DEV_BYPASS`. A self-blessed row and an honest seed row
  are byte-identical; only a human's commit separates them, so no env var may bridge that gap.
- **Digests record review debt, not prose correctness.** ADR-0010 deliberately refuses a semantic
  documentation oracle: a hash proves a human looked at a `(sources, target)` pair, nothing more.
- **A closeout does not repair on the way past.** T-29-21 named it and the milestone honoured it
  twice — once for the `lifecycle-eval` conftest, once for the bash-spelled write-deny found at the
  very end. A closeout that fixes things reports a state that never existed.
- **`authored: at-closeout` as an honesty stamp.** VALIDATION.md files written after the phase they
  describe say so in their own frontmatter and claim no prospective authority.
- **Check an ADR's Status before citing it.** A `proposed` ADR does not outrank an `accepted` one.

### Key Lessons

1. **Schedule the human-only write first.** Everything downstream of a ratification either observes
   the real transition or reconstructs it afterwards in a worktree. The second is strictly worse.
2. **A control that ships green without ever being seen to move is not yet evidence.** This
   milestone's recurring defect, named explicitly by the phase-29 verifier.
3. **A fix can be inert.** 26.1's charset-diversity lookaheads were correct as written and did
   nothing at runtime. Test through the live consumer, on the branch that actually changed.
4. **A stale carry-forward list biases in one direction** — everything on it was still believed red.
   Two of three had already been fixed. Verify the premises you hand a verifier.
5. **Enforcement and declaration drift apart silently.** Four documents said `docs/glossary.md` was
   gated; the code gated three of four members. Only an external audit caught which side was wrong.

### Cost Observations

- 310 commits across 3 days; 184 files and +20,789 lines outside `.planning/`.
- 10 phases for 6 planned — 4 were adversarial-review insertions, i.e. ~40% of the phase count went
  to defects found by review rather than to planned scope. That is a cost, and also the reason the
  milestone closed with 16/16 gates green.
- Model mix intentionally not recorded — see the note at the top of this file.

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Days | Notable |
|-----------|--------|-------|------|---------|
| v2.0 Long-Horizon | 3 | 11 | — | curator + fan-out substrate + multi-repo workspace |
| v2.1 MEM2 | 6 | — | — | process-memory tier + provenance reframe |
| v2.2 Task Control Plane | 6 | — | — | task packet, risk router, CAS, evidence, HANDOFF |
| v2.3 Contract Graph / Adoption / Living Docs | 10 (4 inserted) | 43 | 3 | first milestone whose close depended on a human write no agent could perform |

**Recurring, still unresolved across milestones:**

- `ruff check` is not a CI gate (carried since ~Phase 14; now 617 errors).
- `secret_scan.py` hardcodes its patterns instead of reading the contract (carried since 26.2).
- Provenance obligations accumulate faster than they discharge: a solo-authored PR cannot fire a
  CODEOWNERS gate whose sole owner is the author (RAT-5), so ADR merges to `main` keep deferring.

**Improving:**

- Adversarial review is finding real, load-bearing defects earlier and they are being turned into
  numbered phases instead of silent patches.
- Verification is moving from reading gate output to driving gates, and from trusting the
  carry-forward record to falsifying it.
