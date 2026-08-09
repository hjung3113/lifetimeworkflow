---
updated: "2026-08-10"
---

# progress — terse running log (COMMITTED)

> DATA AUTHORITY — on a data conflict, `contracts/` and `docs/adr/` win over
> `.memory/state/`. This is a session progress log, not a reason to re-verify grounded work.
> No secrets/PII. Durable decisions go in append-only `docs/adr/`, not here.

## Recently done (last 5)

- v1.0 (1–8), v2.0 (9–11), v2.1–v2.3, v2.5 (39–46) and v2.6 (47–50a): complete + archived.
  v2.6 carried 50b to v2.7 for want of a real multi-package target.
- **v2.7 phases 51–53 shipped** (PR #9) — a real-target observation baseline, adoption capabilities
  bounded to failures that baseline actually established, and managed install → update → no-op
  semantics for `/adopt` backed by a per-destination `installed.json`.
- **Three defects the fixtures could not reach** surfaced only by running the real target four
  times: scanner-excluded destinations could never leave `conflict`; `marker-merge` rewrote
  unconditionally and advanced the record on a no-op; and the marker splice used `find()` where the
  body legitimately contains an inner fence, appending an extra `END HARNESS-MANAGED` to a third
  party's `AGENTS.md` on every run. The last was unbounded corruption of someone else's file.
- **Phase 54 SC-1 + two silent gates** (PR #10) — `conventions_for()` and `report()` now share one
  `"dir"`-filter helper (DEBT-01); `/contract-check` stage 1 got its first instance to validate,
  having exited 0 while checking nothing; and the SessionStart repo map stopped silently evicting
  the activeContext pointer, which adding one public symbol was enough to trigger.
- **Docs cleaned for internal distribution** (PR #11) — README.ko.md brought to roadmap parity with
  the English file, both license statements set to internal-use-only, and `docs/references/`
  (79 vendored third-party files, one character from the generated `docs/reference/`) removed.

## Remaining

- **Phase 54 SC-2/3/4** — closeout counts, harness-sourced runtime changes, and the no-model-
  identifiers sweep are unverified. SC-1 is done.
- **A filtered distribution snapshot.** `.planning/` is ~half the tracked files and GSD reads a
  populated one as an already-initialized project. Documented in both READMEs; not structurally
  solved.
- Carried debt (detail in `.planning/milestones/v2.5-ROADMAP.md`): the core suite's six-test
  coupling to the reference instance; GEN-04's `_CORE_ROOTS` seeing neither `pyproject.toml` nor
  `.github/`; VERIFICATION.md absent for phases 40/44/45/46, recorded not backfilled.
