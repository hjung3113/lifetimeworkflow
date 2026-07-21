# Phase 35: Carried-Debt Dispositions — Context

**Gathered:** 2026-07-22
**Status:** Ready for planning
**Mode:** Autonomous. Three independent carried-debt items, each of which must reach a **recorded**
disposition. Silence is not an available outcome for any of them.

<domain>
## Phase Boundary

Three debts carried out of v2.3 are dispositioned. They share a shape and nothing else: each is a
thing the milestone close **noticed and declined to resolve**, and each has been carried far enough
that carrying it again would be the wrong answer.

Requirements: DEBT-02, DEBT-03, DEBT-04 (`.planning/REQUIREMENTS.md:57-68`).
Roadmap: `.planning/ROADMAP.md` Phase 35.

**IN scope:**
- **DEBT-04** — `DEF-05-02-1` verified and closed with whichever answer is true.
- **DEBT-03** — the contract graph compiled once per report, not once per binding (28 IN-03), with
  the `impact.py` signature/cache question decided explicitly rather than carried a fourth time.
- **DEBT-02** — Phase 27's missing `VERIFICATION.md` reaches a recorded disposition.

**OUT of scope:** DEBT-01 (ruff as a CI gate) is Phase 34 and is being executed concurrently by
another agent. This phase does not touch `.github/workflows/ci.yml`, the root ruff config, or
`docs/references/**`. It also does not touch `.planning/STATE.md`, which the orchestrator owns —
what STATE.md should say is *reported*, not written.

**The three items are independent.** They are ordered below by evidence dependency, not by
requirement number: DEBT-04 is empirical and may already be closed, so it runs first and the answer
to it is not assumed.
</domain>

<decisions>
## Implementation Decisions

| # | Grey area | Decision | Rationale |
|---|-----------|----------|-----------|
| D-01 | DEBT-04: is `DEF-05-02-1` still real? | **Determine by running, never by reading.** Run the three named tests with `GOLDEN_APPROVE_HUMAN` unset AND exported. If it does not reproduce, find the commit that repaired it and close the record as already-resolved with that citation — do **not** invent a fix. | The record's own suggested fix is easy enough to apply blind, which is exactly the hazard: applying it to already-repaired code would manufacture work and hide who actually fixed it. |
| D-02 | DEBT-04: is a green run sufficient evidence? | **No.** A green run cannot distinguish "repaired" from "the symptom moved". Neuter the suspected repair and confirm the recorded symptom returns **exactly** — the three named tests and no others. | This is the phase-27.2 / phase-28 house rule (a control that cannot be shown to fail is not a control) applied to a *closure claim* rather than to a test. |
| D-03 | DEBT-04: where does the closure get written, given STATE.md is off-limits? | `.planning/phases/05-despecialization/deferred-items.md` — the file `STATE.md:295` already points at as the record of record. STATE.md's own row is reported to the orchestrator. | Closing the pointed-at record keeps the two consistent without writing the file this phase may not write. |
| D-04 | DEBT-03: signature change, or cached state? | **Neither. A third option: a new PURE batch entry point `impact_map(bindings, cfg)`.** `impact_ids` keeps its exact signature and behaviour; the shared traversal is extracted to a private helper so the two cannot drift. | The residual framed this as a forced binary and both horns are bad. A cache puts mutable state in a module whose opening line advertises purity — and would need a `cfg`-keyed invalidation story for a `cfg` that is an unhashable dict. A signature change ripples into `cli`, `docs_staleness.rows` and three test modules to buy nothing a second name does not. Adding a name is the cheapest honest answer, and it is the one the call sites actually want: **both already build a `{binding id: ids}` mapping**. |
| D-05 | DEBT-03: how is "unchanged" proven? | **Byte-identity of the live report before and after**, captured as a sha256 of `python -m tools.docs_guard` stdout and stderr — plus a test that fails if it regresses. | "Determinism is unchanged" asserted in prose is worth nothing. The hash is checkable by anyone. |
| D-06 | DEBT-03: what test actually guards this? | A test that **counts the live reads** (`compile_graph` / `effective_relationships` calls per report), not one that inspects output. | A per-binding loop renders the **identical** report, so the report text cannot witness the defect. Only the call count can. An output-only test would pass under the regression it exists to catch. |
| D-07 | DEBT-02: author, or write off? | **Author `27-VERIFICATION.md` with an `authored: at-closeout` stamp** — the 27.2 / 28 `VALIDATION.md` precedent. | The write-off option exists for the case where the artifact base cannot substantiate anything. Phase 27's cannot be described that way: it has six SUMMARYs, a `27-REVIEW.md`, an approved contemporaneous `27-VALIDATION.md` with a per-task verification map, `deferred-items.md`, and two follow-on phases (27.1, 27.2) that re-verified its output adversarially. Writing that off would discard real evidence. |
| D-08 | DEBT-02: what may go in it? | **Only what an already-existing artifact substantiates.** Every row cites the artifact it is transcribed from. A criterion with no supporting artifact is recorded as a **gap**, not as a verified row and not as a softened one. | The requirement's own words: manufacturing historical verification authority is not an available option. The gaps are the honest part of the document, so they are not an appendix — they are load-bearing. |
| D-09 | DEBT-02: may the verifier run the suite today and count it as evidence? | **Only as clearly-labelled present-tense evidence, never as phase-time evidence.** A green suite today says the code survived nine subsequent phases; it does not say the phase was verified when it closed. | Conflating the two is precisely the manufactured authority the requirement forbids. |
| D-10 | Constitution plane | **No write to `contracts/**`, `docs/adr/**`, `golden/**`, or `docs/glossary.md` is expected or attempted.** If one turns out to be needed, the intended content goes to `drafts/` and is reported. | The deny is correct; routing around it is the failure mode, not the obstacle. |

</decisions>

<constraints>
## Standing Constraints

- `uv run ...` for everything Python; `uv.lock` unchanged (this phase adds no package).
- No model identifier in any repo artifact.
- Never set or rely on `HARNESS_DEV_BYPASS` or `GOLDEN_APPROVE_HUMAN` to land a write.
- Phase 34 runs concurrently: `.github/workflows/ci.yml`, the root ruff config, and
  `docs/references/**` are untouched here. Pre-existing ruff findings in files this phase does not
  modify are left alone — they are DEBT-01's, and fixing them here would collide.
- Fan-in gate: `uv run pytest -q` green, `uv run python -m tools.contract_drift.drift` clean,
  `uv run python -m tools.docs_guard` still exit 0.
</constraints>
