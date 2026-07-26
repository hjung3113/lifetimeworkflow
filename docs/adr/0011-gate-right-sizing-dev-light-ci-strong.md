# 11. Gate right-sizing — dev-light, CI-strong

- **Status:** proposed
- **Date:** —
- **Deciders:** —

## Context

The harness ships in-session PreToolUse guard hooks (`contract_guard`, `secret_scan`,
`ledger_guard`, `commit_gate`, `resume_gate`) that run `uv run python -m tools.hooks.<x>` before
every Write/Edit/Bash. Over four milestones the enforcement surface grew — each milestone's subject
matter *is* gate machinery, so "maintain consistency" drifted into "add more gates". Two concrete
harms surfaced in v2.4:

1. **The guard wall slows the dev inner loop and can deadlock it.** Because each guard shells out to
   `uv run`, a `tools/*` directory created without its `pyproject.toml` makes uv fail to resolve the
   workspace; the guard's Python never starts; a failing PreToolUse guard denies its tool; and
   Read/Write/Bash go down repo-wide with the repair locked behind the outage. This happened twice
   in one milestone and each time required the human's shell to recover.

2. **In-session denies are largely redundant with CI.** This is a contract-first repo: `contracts/`
   drift, golden parity, and lint are already enforced by the CI fan-in, and constitution changes
   are ratified by CODEOWNERS at the PR to `main`. The in-session guards are belt-and-suspenders on
   top of that — valuable for a consumer editing live, but pure friction for the harness's own dev
   sessions, where the human owner reviews every PR anyway.

The project's stated goal is **consistency across projects + long-horizon maintainability**, not
maximal in-session restriction. ADR-0007 already established that the dev session should be
decoupled from the product's constitution gate (`HARNESS_DEV_BYPASS`), but that flag only changes
`contract_guard`/`commit_gate`'s *decision* — it does not stop the other guards from running, and it
does not address the deadlock, because the failure is at the `uv` layer, before any Python opt-out
can run.

## Decision

**Right-size the guards: dev-light, CI-strong.** Enforcement's authoritative home is CI + CODEOWNERS,
not the in-editor hot path. Two mechanisms, both in the emitted guard command string:

1. **`HARNESS_DEV_LIGHT` opt-out.** A dev session may set `HARNESS_DEV_LIGHT` (in the gitignored
   `.claude/settings.local.json`); every guard then short-circuits to allow before invoking uv. The
   deployed product and CI leave the flag unset and keep full enforcement. This generalises
   ADR-0007's dev/deploy decoupling from "the constitution decision" to "the whole guard wall".

2. **Infrastructure degrade.** Ahead of the guard, a bare-`python3` workspace check
   (`tools/harness_lint/workspace_check.py`, no uv, no deps) runs; if the uv workspace cannot
   resolve, the command exits 0 (allow) with a warning instead of the guard dying and blocking the
   tool. **A guard fails closed on a real deny; it must not fail closed on tooling infrastructure
   that is not its concern.** This benefits the deployed product too — a harness that deadlocks a
   consumer on a broken workspace is a defect.

The non-negotiable invariant: **the degrade must never weaken a real deny.** A healthy workspace with
no bypass and no dev-light still runs the guard and still denies. This is proven adversarially by
`tools/harness_emit/tests/test_guard_prefix.py`, not asserted.

### What stays strong (unchanged)

- CI fan-in: contract-drift, golden parity, ruff ratchet, docs-guard, emit-drift, workspace check.
- CODEOWNERS at the PR to `main` — the human ratification gate for the constitution plane.
- Byte hygiene on the constitution plane is still enforced whenever a guard *does* run (ADR-0007).

### What this deliberately accepts

With `HARNESS_DEV_LIGHT` set, a dev session's writes are not screened in-editor — including
`secret_scan` (a secret could reach a commit, caught by CI's scan / PR review rather than at write
time) and `ledger_guard` (the human-only docs-review-ledger invariant of ADR-0010 is not enforced
in-editor; a self-authored ledger row would be caught only at PR review). This is an eyes-open
trade of in-session safety for dev speed, recorded here rather than left implicit. It is sound only
while the PR to `main` is genuinely reviewed — which is the same assumption ADR-0007 and the whole
"machines gate, humans ratify" model already rest on.

## Consequences

- v2.4's remaining "add more in-session enforcement" work (SEAL-02/03 spelling-independent bash
  denies) is **cut** — it is the opposite of this decision. The deny-domain *registry* landed in
  phase 30 stays as an inventory/reference; it no longer feeds new in-session enforcement.
- The deadlock class that cost two session outages is closed for both dev and deployed use.
- This ADR narrows the scope of, but does not supersede, ADR-0007: `HARNESS_DEV_BYPASS` remains the
  constitution-decision opt-out; `HARNESS_DEV_LIGHT` is the broader guard-wall opt-out. A session
  may set either or both.
