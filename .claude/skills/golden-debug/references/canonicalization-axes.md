# Golden red — the 7 canonicalization axes (discriminator → fix side)

Cross-references: `libs/normalize-spec.md` R1–R7 (the canonical spec), the `CLAUDE.md`
§"Golden-Equivalence Comparator Building Blocks" table, and the const values materialized in
`contracts/normalization/format-conventions.schema.json`. Equivalence is compared **only after**
both sides run through the shared canonicalization core — a red is almost always one missed axis.

| # | Axis (spec rule) | Canonical rule | Discriminator — "is it this one?" | Fix side |
|---|---|---|---|---|
| 1 | Encoding / BOM (R1, §4.3) | UTF-8; leading BOM `EF BB BF` stripped; emit no BOM | Only the first cell of the first row is corrupted (invisible `﻿` prefix); rest of file fine | Producer re-added a BOM → strip on read (`utf-8-sig`) / emit `new UTF8Encoding(false)` |
| 2 | Newlines (R2, §4.3) | Force LF; `\r\n` and lone `\r` → `\n` | Every line mismatches / trailing-cell diff; `\r` bytes present; row count looks right | Producer emitted CRLF/CR → normalize to LF before compare |
| 3 | Decimal & culture (R3, §4.6) | InvariantCulture `.`; comma→dot; trim trailing zeros + trailing `.`; decimal types (never float round-trip) | Diff is purely `1,5`/`1.5`, `1.50`/`1.5`, `100.0`/`100` | Emit InvariantCulture fixed-point, trimmed; parse with decimal, not float |
| 4 | Float compare tolerance (R4, §4) | Compare with tolerance `1e-9`; string emission (R3) is exact | Numbers agree to many digits, differ only in the last | Compare-time concern: the tolerance path was bypassed — route the compare through the runner, don't string-equal floats |
| 5 | Key / row ordering (§4) | Deterministic sort before diff | Same *set* of rows, different order | Sort both sides deterministically before diff — unordered producer must not false-red |
| 6 | Timezone / datetime (R5, §4.4) | Convert to UTC; emit `yyyy-MM-ddTHH:mm:ssZ`; naive assumed UTC | Timestamps off by a fixed offset, or one side `Z`/offset vs the other naive | Normalize to UTC ISO-8601; assume UTC when naive (`Kind` vs naive/aware divergence) |
| 7 | TSV escape / null-vs-empty (R6/R7, §4.3) | Tab field-sep + agreed escape for tab/newline-in-value; `null_token` (`\N`) distinct from `""` | A raw tab/newline shifts columns, or empty-cell vs null-token mismatch | Apply the escape; keep `"" ≠ null` — null token → `<NULL>` sentinel, empty string stays `""` |

## Using the table

1. Diff `golden/<case>/expected/baseline.received.tsv` against `baseline.verified.tsv` — never edit
   `.verified`.
2. Classify the moved cell: **representation** (axes 1–7 above → fix normalization on the offending
   side) vs **value** (real regression → fix producing code; or intended → data case + human
   `/golden-approve` + ADR, exit-3 gated).
3. Re-run `uv run python -m tools.golden_runner.runner <case>` until green *for the right reason*.

## Why byte-diff is banned

A raw `diff` false-reds on every one of axes 1–2, 3, 6, 7 (encoding/locale/timezone/escape noise)
while *hiding* real value regressions behind that noise. The canonicalizing comparator neutralizes
representation, then compares — so a red is either a missed axis or a true value change, nothing else.
