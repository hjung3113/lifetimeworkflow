# Requirements — v2.4 Enforcement Integrity, Carried Debt, Lane Discipline

Scoped to milestone v2.4 (phases 30–37). Ratified design:
`.planning/research/v2.4-scoping-FINAL.md`. Previous milestone's requirements:
`.planning/milestones/v2.3-REQUIREMENTS.md`.

**Milestone goal:** close the gap between what this harness *declares* and what it *enforces*,
discharge the debt carried across three milestones, and finish the task-lifecycle discipline left
unbuilt by v2.2 — so that every control the documentation claims exists actually fires, and every
carried item reaches a recorded disposition instead of a fourth carry.

The thesis is a sentence this repo already wrote, in ADR-0010: *"a layer that is only a data row is
a claimed control that does not exist — worse than a missing layer, because it reads as covered."*
v2.4 applies it to the harness itself.

## Theme A — Gate Integrity (Phases 30–33)

- [ ] **SEAL-01** *(NEW, Phase 30)*: A **deny-domain registry** declares every path-deny domain in
  the harness — at minimum `contract_guard.CONSTITUTION_GLOBS`, `secret_scan.SECRET_PATH_GLOBS`
  and `ledger_guard.REVIEW_LEDGER_GLOBS` — each with its owner, its bypass semantics
  (`GOLDEN_APPROVE_HUMAN` / `HARNESS_DEV_BYPASS` / none), the tool surfaces it currently covers, and
  its runtime adapters. The domains remain **distinct**: ADR-0010 explains why the review ledger
  must not be folded into the constitution plane, and `commit_gate` is not a path-enumeration site
  at all. A `harness_lint` drift test fails when a hook's live constant disagrees with its
  declaration, proven by a mutation that makes it fail.
- [ ] **SEAL-02** *(NEW, Phase 31)*: A **threat model plus an explicitly chosen enforcement posture**
  for the uncovered bash surface, ratified as an ADR **before** any enforcement is written. The ADR
  picks among filesystem-level enforcement, a constrained command allowlist, protected command
  wrappers, or a documented residual boundary — and states in the ADR itself what remains uncovered.
  A recorded honest residual satisfies this requirement; an unbounded "spelling-independent" claim
  does not.
- [ ] **SEAL-03** *(NEW, Phase 32)*: The posture ratified by SEAL-02 is **implemented in both
  runtimes**, with per-class deletion proofs and live negative controls, and a superseding ADR entry
  records the newly covered surface and the residual. Acceptance is stated against the declared
  posture, never against "all spellings". The known live gap this closes:
  `resolve_bash(..., "uv run python -c \"open('docs/.docs-review-ledger.toml','w')...\"")` resolves
  to `allow` today, because the deny is registered only for `Write|Edit`
  (`.claude/settings.json:121,160`; `.opencode/plugin/ledger-guard.ts:65,70`) while
  `harness/permission-matrix.json:6` grants `"uv *": "allow"`.
- [ ] **SEAL-04** *(NEW, Phase 33)*: `tools/hooks/secret_scan.py` **reads its patterns from the
  contract** instead of declaring them as module constants (`secret_scan.py:42`, carried since 26.2).
  The gate registry is already the single source of truth for `adoption_scan` and `evidence/capture`;
  this hook is the last consumer that forked it. Proven by a contract-side change that moves the
  hook's behaviour.
- [ ] **SEAL-05** *(NEW, Phase 33)*: **RAT-4 reaches a recorded disposition**, and the harness
  defines a **portable ratification record** — a checkable provenance artifact that does not depend
  on a git host assigning a reviewer. Explicitly excluded: repairing GitHub branch protection,
  reviewer eligibility or CODEOWNERS behaviour for a solo owner. RAT-5 is marked
  closed-with-caveats (PR #4 merged it), not reopened.

## Theme B — Carried Debt (Phases 34–35)

- [ ] **DEBT-01** *(NEW, Phase 34)*: `ruff check` becomes a **required CI gate**. The vendored
  `docs/references/opencode-matt-workflows/**` tree joins `extend-exclude` (~180 of the 617 current
  findings), and the genuine remainder is held by a **ratcheting baseline** that can only shrink.
  Carried three milestones; a lint that cannot fail CI is not a gate.
- [ ] **DEBT-02** *(NEW, Phase 35)*: Phase 27's missing `VERIFICATION.md` reaches a **recorded
  disposition** — either authored with an explicit at-closeout honesty stamp (the 27.2 / 28
  precedent, which states plainly that it could not have steered the phase it describes), or
  formally written off with a reason. Manufacturing historical verification authority is not an
  available option.
- [ ] **DEBT-03** *(NEW, Phase 35)*: The contract graph is **compiled once per report, not once per
  binding** (28 IN-03), with an explicit recorded decision about `impact.py`'s public signature and
  cache invalidation rather than a fourth carry.
- [ ] **DEBT-04** *(NEW, Phase 35)*: `DEF-05-02-1` is **verified and closed** — the three
  `commit_gate` drift-block tests that leak an ambient `GOLDEN_APPROVE_HUMAN` token and therefore
  fail only when the session token is exported. It may already be repaired; the record is closed
  with whichever answer is true.

## Theme C — Lane Discipline (Phases 36–37, the v2.2 TCP-F carry)

- [ ] **LANE-01** *(NEW+REUSE, Phase 36)*: Clarify / TDD / diagnose / domain-modeling **discipline
  skills are wired into the task lifecycle**, so a lane's required discipline is executable rather
  than advisory (TCP-F01). Reuses the v2.2 lane vocabulary and required-artifact matrix; adds no
  second control plane.
- [ ] **LANE-02** *(NEW+REUSE, Phase 36)*: A **STRICT+ adversarial multi-expert review panel** is a
  declared lane requirement (TCP-F02), reusing the Phase-10 fan-out substrate. The empirical case is
  v2.3: 4 of its 10 phases exist because adversarial review found real defects, one of them a phase
  whose own fix was inert at runtime.
- [ ] **LANE-03** *(NEW+REUSE, Phase 37)*: **Specialist agent allowlist + capability-neutral
  routing** (TCP-F03) — routing by declared capability, not by hardcoded persona name.
- [ ] **LANE-04** *(NEW, Phase 37)*: **Skill `registry.lock` + adapter CI** (TCP-F04), so the emitted
  skill surface cannot drift from its declaration. Mirrors the existing emit-drift gate's posture.

## Future Requirements

Deferred to a later milestone — cut from v2.4 by human decision, recorded so they are not lost by
being merely "out of scope":

- **EVOL-01** — impact-driven task-evidence policy: let the v2.3 topology affected-set change a
  lane's *required* evidence. Needs its own ratified ADR.
- **EVOL-02** — contract versioning / compatibility engine: semver ranges, migration graph,
  compatibility matrix. The largest single item in the backlog; a standalone engine.
- **EVOL-03** — `examples/**` instance-local docs-registry overlay (the seam left open by
  28-CONTEXT D-14).
- **TCP-F05** — signed external evidence attestation, and the STRICT rollback policy. Both still
  need a breaking ADR.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Repairing GitHub's trust model (branch protection, reviewer eligibility, CODEOWNERS for a solo owner) | Repository administration, not harness behaviour. The harness may define and verify a portable ratification record; it cannot make a solo author independently review themself. |
| A universal "spelling-independent" bash deny with unbounded acceptance | Not soundly implementable from command text: interpreters, build tools, subprocesses, symlinks and generated scripts defeat static inference. SEAL-02 must choose a bounded posture and state the residual. |
| Merging the three deny domains into one plane | ADR-0010 records why the review ledger is deliberately a separate domain with its own constant, its own exception type and no opt-out. SEAL-01 is an inventory, not a merge. |
| Re-litigating the Phase-28/29 `human_needed` verification rows | They are acknowledged human-ratification rows, not implementation debt. |
| Editing accepted ADRs | Append-only. Clarification happens by a superseding ADR. |
| Pact / broker contract testing, a second orchestrator, autonomous contract extraction | Standing exclusions carried from prior milestones. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEAL-01 | Phase 30 | Not started |
| SEAL-02 | Phase 31 | Not started |
| SEAL-03 | Phase 32 | Not started |
| SEAL-04 | Phase 33 | Not started |
| SEAL-05 | Phase 33 | Not started |
| DEBT-01 | Phase 34 | Not started |
| DEBT-02 | Phase 35 | Not started |
| DEBT-03 | Phase 35 | Not started |
| DEBT-04 | Phase 35 | Not started |
| LANE-01 | Phase 36 | Not started |
| LANE-02 | Phase 36 | Not started |
| LANE-03 | Phase 37 | Not started |
| LANE-04 | Phase 37 | Not started |

> **Recorded deviation from the review.** The codex-sol review advised cutting Themes C *and* D and
> shipping **five** phases, on the grounds that this draft was "four milestones disguised as ten
> phases". The human kept Theme C and cut only Theme D, giving eight phases. The reviewer's sizing
> risk is accepted knowingly, and its named failure mode — phase 32 expanding without bound because
> "spelling independence" is not a bounded acceptance criterion — is mitigated by requiring SEAL-02's
> posture ADR to be ratified *before* phase 32 begins. If phase 31 cannot pick a posture, stop.
