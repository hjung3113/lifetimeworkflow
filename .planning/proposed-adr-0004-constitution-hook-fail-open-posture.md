# PROPOSED ADR-0004 — pending human promotion into docs/adr/

> This is a DRAFT staged in the derived/planning plane. The contract-guard hook (correctly)
> refuses an agent write to `docs/adr/**`. To promote: a human copies this body to
> `docs/adr/0004-constitution-hook-fail-open-posture.md` (drop this banner) and commits it under
> CODEOWNERS review — or sets `GOLDEN_APPROVE_HUMAN` for a session and writes it there via the
> `adr` skill. The block below is the intended final ADR content verbatim.

---

# 4. Constitution-Plane Hook Fail-Open Posture on Malformed Stdin

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-14
- **Deciders:** full-harness audit (finding M4), operator-delegated decision
- **Supersedes:** —
- **Superseded by:** —
- **Complements:** the HOOK-04 contract-guard / HOOK-02 secret-scan gates (`tools/hooks/`).

## Context and Problem Statement

The full-harness audit (`.planning/AUDIT-FINDINGS.md`, finding M4) surfaced that the constitution-
plane PreToolUse gate `tools/hooks/contract_guard.py` is **fail-open** on malformed hook stdin: the
shared adapter `tools/hooks/_stdin.py` maps unparseable / non-object / field-omitted payloads to a
safe sentinel `Event()` (every field `""`), and `decide()` reads an empty `file_path` as "not on the
constitution plane" → no deny → the write proceeds. A payload that a malicious or buggy caller
malforms therefore never reaches the deny branch.

This decision was previously implicit (documented in `_stdin.py` as "individual gates choose fail-open
vs fail-closed on top of [the sentinel]") but never ratified. The audit also fixed finding H1 (commit
`7d71c7e`): before H1, the gate was a no-op for *all* real writes because Claude's absolute `file_path`
never matched the repo-relative deny globs. With H1 fixed, a **well-formed** event is now correctly
gated, which sharpens the question the sentinel path answers: when the event itself is unreadable,
should the constitution guard deny (fail-closed) or allow (fail-open)?

## Decision Drivers

- **Blast radius of fail-closed.** The guard fires on every `Write|Edit` PreToolUse. A malformed
  payload carries no usable `file_path`, so fail-closed cannot deny *selectively* — it would deny the
  tool call outright, blocking **every** edit (the overwhelming majority of which are legitimate
  non-constitution source edits) whenever stdin is malformed. That wedges normal editing to defend a
  plane that has independent, stronger backstops.
- **The constitution plane is defended in depth, not by this hook alone.** CODEOWNERS review on
  `contracts/`·`docs/adr/`·`golden/` and the CI schema-hash **contract-drift gate**
  (`tools/contract_drift`, `.github/workflows/ci.yml`) are the *authoritative* ratification barriers.
  A change that slips a runtime hook still cannot merge without human review + a paired golden/ADR.
  The PreToolUse hook is a fast **first-line** convenience deny, not the last line.
- **H1 already closes the realistic exposure.** The genuine gap was well-formed absolute-path writes
  silently passing (H1) — now fixed and regression-tested. A *malformed* event is a narrow,
  bug/attack-shaped edge, not the common path.
- **Secret-scan asymmetry is intentional.** `secret_scan` is an advisory content gate and stays
  fail-open by its own module contract; making only `contract_guard` fail-closed would still not be
  selective (same no-`file_path` problem) and would break editing.

## Considered Options

1. **Flip `contract_guard` to fail-closed on the sentinel (deny when `file_path` is empty).**
   *Rejected:* not selective — denies all `Write|Edit` on any malformed payload, wedging legitimate
   source editing to guard a plane CODEOWNERS + the drift gate already ratify.
2. **Add path-independent heuristics (e.g., deny if `content` looks schema-shaped).** *Rejected:*
   guesswork with false positives; the plane's real gate is identity/CODEOWNERS, not content shape.
3. **Keep fail-open; ratify it explicitly and rely on the layered backstops (chosen).** Document that
   the runtime hook is a best-effort first-line deny; correctness of the plane is guaranteed by
   CODEOWNERS + the CI contract-drift gate, which a malformed-stdin bypass cannot defeat.

## Decision Outcome

**Chosen: Option 3 — the constitution-plane hooks remain fail-open on malformed/unparseable stdin, by
ratified decision.** The safe-sentinel path in `tools/hooks/_stdin.py` and the empty-`file_path`
allow in `contract_guard.decide()` / `secret_scan.decide()` are intentional: on an unreadable event
the gate declines to decide rather than blocking every edit. This is acceptable because:

- H1 (commit `7d71c7e`) ensures every **well-formed** constitution-plane write IS denied (absolute
  paths normalized to repo-relative before glob matching), with absolute-path regression tests.
- The **authoritative** ratification of the constitution plane is CODEOWNERS + the CI schema-hash
  contract-drift gate; neither is reachable by a malformed-stdin bypass, so the plane cannot be
  silently changed on `main`.
- Fail-closed offers no *selective* protection here (no `file_path` to match) and its cost —
  wedging all editing on any malformed payload — is disproportionate.

### Consequences

- **Good:** normal editing is never blocked by a malformed hook payload; the plane stays defended by
  the layered, merge-blocking backstops.
- **Neutral:** the runtime hook is explicitly a *first-line convenience*, not the security boundary of
  record — the boundary is CODEOWNERS + CI drift.
- **Bad / accepted:** a hypothetical caller that both (a) targets the constitution plane and (b)
  malforms its own PreToolUse stdin is not denied at the hook; it is still caught at PR review / CI
  drift. If this edge ever needs closing, revisit with a *selective* mechanism (e.g., a fail-closed
  deny scoped to events that parse far enough to expose a constitution `file_path` but fail later),
  not a blanket flip.

## Links

- Audit finding M4 and the layered-backstop context: `.planning/AUDIT-FINDINGS.md`.
- Gates: `tools/hooks/contract_guard.py`, `tools/hooks/secret_scan.py`, `tools/hooks/_stdin.py`
  (`repo_relative` + safe-sentinel `parse_event`).
- Authoritative backstops: CODEOWNERS on `contracts/`·`docs/adr/`·`golden/`; the CI contract-drift
  gate `tools/contract_drift` (`.github/workflows/ci.yml`).
- Related fix: H1 absolute-path normalization (commit `7d71c7e`).
