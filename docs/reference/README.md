# Reference

*Diátaxis quadrant: **information-oriented**. **DERIVED — do NOT hand-author.***

> ⚠️ **This quadrant is generated, not written.** Its content is **derived from `contracts/`**
> by the `/docs-sync` command in **Phase 3 (DOCS-03)**. Reference pages describe the exact,
> mechanical truth of the contracts (TSV column specs, schemas, normalization conventions,
> exit codes, file boundaries) and must stay in lock-step with the schemas that are the
> single source of truth. Editing reference pages by hand would fork them from the contracts
> and defeat the contract-first invariant.

## Status this phase

- **Phase 1 (now):** this placeholder README only — marks the quadrant as **derived-later**.
- **Phase 3 (DOCS-03):** `/docs-sync` populates reference pages **from `contracts/`**; drift
  between contracts and reference is caught by the harness, not by human review.

## Will be generated (from contracts/)

- Column-level TSV spec reference (from `contracts/log-specs/*.schema.json`).
- Normalization / §4.3–4.6 format-conventions reference (from `contracts/normalization/format-conventions.schema.json`).
- Reference-data + state/carryover shapes.

> Do not add hand-authored content here. If you need to document a contract, change the
> contract; the reference regenerates from it.
