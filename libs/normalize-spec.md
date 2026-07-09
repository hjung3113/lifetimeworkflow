# Normalization Comparator — Language-Neutral Canonicalization Spec (§4.3–4.6)

**Requirement:** CONTRACT-02 · **Decision:** D-04 / D-05 · **Plane:** constitution (human-owned)

> **The rule is canonical, not any one language.** This document is the single source of
> truth for the §4.3–4.6 TSV canonicalization. The Python core (`libs/python/normalize`) and an
> instance's language-side twin are each a *thin* implementation of these rules.
> A shared `(raw, canonical)` fixture corpus (`libs/normalize-fixtures/*.json`) is loaded by
> **both** test suites; any per-language drift fails the parity test. This core is reused by the
> Phase-4 polyglot linter (POLY-01) — it is a clean, shared library, not a private helper.

> **Scope guard:** This is the **TSV data** comparator for golden equivalence. It has **nothing**
> to do with RFC 8785 / JCS, which canonicalizes JSON *contract text* for the drift hash
> (Plan 05, Python-only). Do not conflate the two canonicalizers — they share only the word
> "canonical".

## Why (P4)

Polyglot representation differences (UTF-8 BOM, CRLF, decimal locale, timezone offset) must be
**neutralized before diff** so golden equivalence is a *normalized* comparison, never a byte diff.
A byte diff produces false reds on encoding/locale noise (Pitfall P4); a value regression must
still fail. Normalize both sides through this core, then diff.

## Canonical Rules

The materialized, hashable form of these conventions lives in
`contracts/normalization/format-conventions.schema.json` (P14 drift target). The corpus and this
spec MUST agree with those `const` values — in particular the `null_token`.

### R1 — Encoding & BOM (§4.3)
- Input is decoded as **UTF-8**. A leading **UTF-8 BOM (`EF BB BF`) is stripped**.
- Output is written **without a BOM** (`new UTF8Encoding(false)` on .NET; `utf-8-sig` decode on
  Python strips a present BOM and re-encoding never re-adds one).
- Rationale: .NET may emit a BOM; Python then misreads the first column (§4.3).

### R2 — Newlines (§4.3)
- All newlines are normalized to **LF** (`\n`). `CRLF` (`\r\n`) and lone `CR` (`\r`) → `LF`.
- Rationale: .NET defaults may be CRLF; force LF so line splitting agrees.

### R3 — Decimal & culture (§4.6)
- Numbers use **`.`** as the decimal separator under **InvariantCulture**. A locale **`,`**
  decimal separator is treated as a decimal point (`","` → `"."`) before parsing.
- **No thousands separators** are permitted in input (§4.6 forbids them), so the comma remap is
  unambiguous.
- Canonical form: parse with the invariant culture, emit fixed-point with **trailing zeros and a
  trailing decimal point removed** (`.NET` `ToString("0.############")`; Python `format(d,"f")`
  then `rstrip("0").rstrip(".")`). Examples: `1,5 → 1.5`, `1.50 → 1.5`, `100 → 100`.
- Never `float()` round-trip — use decimal types (Python `decimal.Decimal`, .NET `decimal`) to
  avoid last-digit representation diffs (§4.6).

### R4 — Float compare tolerance (§4)
- Numeric *comparison* is tolerance-aware (`tolerance = 1e-9`, per `format-conventions.schema.json`)
  so last-digit float representation never flips a golden. Canonical *string* emission (R3) is
  exact; the tolerance applies at compare time in the golden runner.

### R5 — Timezone / datetime (§4.4)
- All datetimes are converted to **UTC** and emitted as a **fixed ISO-8601 string**:
  `yyyy-MM-ddTHH:mm:ssZ`.
- A value carrying an explicit offset (e.g. `+09:00`) is adjusted to UTC. A value with no offset
  is **assumed UTC** (`.NET` `DateTimeStyles.AssumeUniversal | AdjustToUniversal`; Python: attach
  `timezone.utc` when naive, then `astimezone(utc)`).
- Rationale: .NET `DateTime.Kind` vs Python naive/aware serialization diverge — pin the string.

### R6 — Null vs empty (§4.3)
- The agreed **null token** (`format-conventions.schema.json` `null_token`, currently `\N`) is a
  **distinct** value from the empty string. A cell equal to the null token canonicalizes to the
  sentinel **`<NULL>`**; an empty string canonicalizes to the empty string `""`. `"" ≠ null`.

### R7 — TSV escape (§4.3)
- Field separator is the tab (`\t`). The agreed escape rule for tab/newline-in-value is
  **backslash-escape** (`format-conventions.schema.json` `tsv_escape: "backslash"`) — a value
  containing a literal tab or newline is backslash-escaped, never allowed to break the column
  count. (Phase-1 corpus values contain no in-field tabs; the rule is documented for the core to
  honor as fixtures grow.)

### R8 — Deterministic row/key ordering (§4)
- Before diff, rows are sorted with a **deterministic ordinal** (Unicode code-point) sort so an
  unordered set never causes a false diff. Python `sorted()` and .NET `StringComparer.Ordinal`
  agree on ASCII/BMP content.

## Canonical Sentinels (fixed strings both languages emit)

| Concept | Canonical output |
|---------|------------------|
| null token (`\N`) | `<NULL>` |
| empty string | `` (empty) |
| decimal | invariant fixed-point, trailing zeros stripped (`1.5`, `100`) |
| datetime | `yyyy-MM-ddTHH:mm:ssZ` (UTC) |

## Shared Fixture Corpus

`libs/normalize-fixtures/*.json` — one corpus, loaded by BOTH the Python (`pytest`) and .NET
(`xunit.v3`) suites. Each file is a JSON **array** of entries:

```json
{ "name": "…", "kind": "decimal|datetime|string|tsv", "raw": "…", "canonical": "…" }
```

- `kind` in {`decimal`, `datetime`, `string`} → the entry carries a `raw` string; the core's
  cell normalizer must reproduce `canonical`.
- `kind == "tsv"` → the entry carries **`raw_b64`** (base64 of the raw UTF-8 bytes, possibly with
  BOM/CRLF); the core's TSV normalizer must reproduce `canonical`.

Identical `canonical` output across both languages for every entry proves cross-language parity
(D-04) — this corpus is the drift catcher.
