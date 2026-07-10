---
name: normalization-catalog
description: >-
  Use when adding or looking up a value normalization or correction rule in
  contracts/normalization. Covers the data-driven catalog of maker/model rule kinds
  (normalization vs correction, enrichment vs fix), the (input, expected) test-case shape golden
  and parameterized tests consume, and the breaking-vs-non-breaking change policy.
---

# normalization-catalog

The map of the value-normalization and correction rules. Rules are managed as **data, not code**
(`contracts/normalization/correction-rules.catalog.yaml` + its schema), so a 50+ rule catalog is
parameterized into tests rather than branched into logic.

## Two distinct stages

- **Normalization** = make the inconsistent consistent (per-maker/per-model raw value → canonical
  value). Keyed by `scope` (`maker_id`, `model_id`) and a `target_field` with a `mapping`.
- **Correction** = fill defects. Its `kind` is either **enrichment** (보강 — add missing signal) or
  **fix** (교정 — repair a wrong value).

Keep these separate: a normalization is a lookup remap; a correction changes semantics.

## Rule shape

Each rule carries `test_cases` of `(input, expected)` pairs. Those pairs are the SAME data the
golden runner and the parameterized unit tests consume — the case is the spec. Add the case first,
then the rule mapping; a rule with no case is unverifiable.

## Change policy (drift-gated)

- Adding a **new** case = **non-breaking**.
- Changing an **existing** case's `expected` = **breaking** — it needs a golden/approval update and
  trips the contract-drift gate (see the data-contracts skill).

## Seeds are placeholders

The catalog is seeded from the parserimprove skeleton; every `TBD`/example value is a placeholder,
not domain truth (CONTRACT-01). The domain rule values are Out of Scope — the point is the
enforcement plumbing.

## Deeper reference

Keep a worked "add one normalization rule" example under `references/` (contract entry →
(input,expected) case → code). See `contracts/normalization/` and the `/new-contract-rule`
command, which scaffolds exactly that order.
