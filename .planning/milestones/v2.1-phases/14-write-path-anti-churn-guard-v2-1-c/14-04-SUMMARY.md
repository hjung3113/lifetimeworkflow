# Plan 14-04 — Summary

**Status:** complete · **Executed by:** Claude (NOT delegated — constitution plane)
**Commit:** `ff832ac` docs(adr): append errata to ADR-0006 — the "committed seed" never existed

## What shipped

A dated `## Errata` section appended to `docs/adr/0006-*.md`, after `## Links`. No decision word
altered.

## Why an errata, not a seed and not ADR-0008

- **Not a seed (D-12):** fabricating an agreement to retroactively make the ADR's claim true would
  require inventing user feedback to fill `provenance:` — the exact T-13-01 / anti-invent violation
  this phase exists to prevent. The phase must not open by committing the sin it closes.
- **Not ADR-0008:** supersede is the instrument for *changing a decision* (`docs/adr/README.md:16`).
  No decision changed — a factual claim in `### Consequences` was wrong.
- **Errata is append-only-legal:** `README.md:14` forbids editing *decision content* and explicitly
  permits fixing typos/links. The false claim sits in `### Consequences`, not `## Decision Outcome`.

## D-13 is the load-bearing half

The errata states plainly that the **empty active set is CORRECT**, so a future agent reading the
phantom-seed claim does not "repair" the directory by inventing an entry.

## Landing path — first real use of ADR-0007

Landed via `HARNESS_DEV_BYPASS` set in gitignored `.claude/settings.local.json` (verified ignored at
`.gitignore:27`; the flag is never committed, per ADR-0007(e)). **`GOLDEN_APPROVE_HUMAN` was not
forged** — the whole point of a distinct variable is that a dev-bypassed write is never mislabeled
human-ratified.

Byte-hygiene held, as ADR-0007(c) promised and as execution confirmed: `decide(approved=True)` with
CRLF content still returns DENY. The committed errata is LF-only with no BOM.

**CODEOWNERS at PR merge remains the real gate.** ADR-0006 (with this errata) is part of the
unratified set on PR #3.
