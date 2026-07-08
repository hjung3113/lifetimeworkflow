---
description: >-
  Use when a decision needs to be recorded — scaffolds the next-numbered append-only MADR file
  under docs/adr/ from the standard template. Invoke to capture an architecture decision;
  it never edits an existing ADR (supersede-don't-edit).
agent: orchestrator
---

# /adr — scaffold the next append-only MADR record

Scaffolds a new Architecture Decision Record. The ADR log is **append-only and immutable**
(constitution plane, DOCS-02): this command writes the **next-numbered** `docs/adr/NNNN-*.md` and
**NEVER edits an existing ADR**.

## Append-only convention (do NOT violate)

- Files are `NNNN-kebab-title.md` starting at `0001`; the number is permanent and never reused.
- **Add** the next-numbered ADR — never renumber, reorder, or overwrite an existing record.
- Once a record is `Status: accepted`, its decision content is **not edited**. To change a past
  decision, write a **new** ADR that references the old one (`Supersedes: NNNN`) and set the old
  record's `Status: superseded by NNNN`. The original stays as the historical record.

## Steps

1. Determine the next number = highest existing `docs/adr/NNNN-*.md` + 1 (zero-padded to 4):

   !`ls docs/adr/ | grep -E '^[0-9]{4}-' | sort | tail -1`

2. Create `docs/adr/NNNN-<kebab-title>.md` from the MADR sections: Title, Status
   (`proposed` → `accepted`), Context and Problem Statement, Decision Drivers, Considered Options,
   Decision Outcome, Consequences, Links. Title/topic come from `$ARGUMENTS`.

3. Add a row to the `docs/adr/README.md` index — never remove a row.

## Guard

- This command only **adds** a new file; it must not open an existing `docs/adr/NNNN-*.md` for edit.
- `docs/adr/**` is a constitution-plane path (CODEOWNERS-gated) — the new record lands via human review.
