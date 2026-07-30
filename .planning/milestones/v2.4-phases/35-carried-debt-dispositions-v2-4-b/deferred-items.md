# Phase 35 — Deferred Items

Items surfaced during the phase that are **not** in its scope to resolve, recorded so they are not
lost by being merely noticed.

## From plan 35-03 (DEBT-02, the Phase-27 verification sweep)

### P27-IN-01 — `apply.py` docstring's security claim is broader than what the code proves

- **Origin:** `27-REVIEW.md` finding **IN-01** (Info), `tools/adoption_apply/apply.py:1-37`,
  reviewed 2026-07-21.
- **Status: OPEN — no disposition in any artifact, in any phase.** Not Phase 27's, not 27.1's, not
  27.2's, not the v2.3 milestone audit's. It is not recorded as fixed, not recorded as accepted,
  and not recorded as deferred. It was simply never answered.
- **Surfaced by:** the DEBT-02 artifact sweep (Phase 35, 2026-07-22). This is a **newly recorded**
  open item, not a previously tracked one — which is why it gets a record here rather than a
  pointer to an existing one.
- **Do not conflate with 27.1's IN-01.** Phase 27.1's review has its own `IN-01` which is a
  **different finding that reuses the ID**. Reading 27.1's disposition as covering this one is an
  error an earlier draft of `27-VERIFICATION.md` actually made and corrected.
- **Why not resolved here:** Phase 35's scope is the three carried debts (DEBT-02/03/04). Resolving
  a code-documentation accuracy finding in `tools/adoption_apply/` is a different phase's work, and
  the honest act available to DEBT-02 was to record it rather than to silently absorb or drop it.
- **Note on its current relevance:** the docstring's claim was written about pre-27.1 code, and
  27.1 substantially changed the controls it describes (CR-01/CR-02/CR-03 fixes). Whether the claim
  is *still* broader than the code is therefore an open question, not a known defect — checking it
  is part of the work, not a precondition to recording it.

### P27-IN-02 — `_recompute_draft_hash` hashes bytes but never validates their schema shape

- **Origin:** `27-REVIEW.md` finding **IN-02** (Info), `tools/adoption_apply/approval.py:57-63`,
  reviewed 2026-07-21.
- **Status: OPEN — no disposition in any artifact, in any phase.** Same as P27-IN-01 above.
- **Substance:** the draft hash is computed over the raw bytes of the batch's
  `inventory.json`/`plan.json`/`manifest.json` in a fixed order. The bytes are bound, but nothing
  checks that each document is the shape it claims to be. A structurally invalid draft therefore
  produces a perfectly valid, perfectly stable approval binding.
- **Do not conflate with 27.1's IN-02** — again a different finding reusing the ID.
- **Why not resolved here:** out of Phase 35's scope, as above.

---

**How these two should be dispositioned.** Either is acceptable and both are better than the status
quo: (a) a decision recorded against each — including an explicit "accepted, will not fix" with a
reason — or (b) promotion into a requirement for a later milestone. What is *not* acceptable is a
third silent carry: these are Info-severity findings that have now survived four phases and a
milestone close without anyone saying anything about them, which is how the two `IN-` IDs came to be
mistaken for 27.1's in the first place.
