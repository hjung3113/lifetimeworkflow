# §4.3–4.6 canonicalization — full rule table

The materialized, hashable form is `contracts/normalization/format-conventions.schema.json`; the
prose spec is `libs/normalize-spec.md` (R1–R7). This table mirrors the `CLAUDE.md`
§"Golden-Equivalence Comparator Building Blocks" table with the rationale per axis.

| Concern | Canonicalization rule | Rationale |
|---|---|---|
| Encoding | UTF-8, **BOM stripped** on read, none on write | One side may emit a BOM; the other then misreads the first column (§4.3) |
| Newlines | Force **LF** | One side may default to CRLF; force LF so line-splitting agrees (§4.3) |
| Decimal | `.` separator, **InvariantCulture**, trailing zeros + trailing `.` trimmed | `ToString`/locale is culture-dependent (§4.6) |
| Numeric compare | **tolerance-aware** float compare (`1e-9`) | avoid spurious reds on last-digit float representation (§4) |
| Key/row ordering | deterministic sort before diff | unordered sets must not cause false diffs (§4) |
| Timezone | UTC, ISO-8601 fixed string `yyyy-MM-ddTHH:mm:ssZ` | one side's `Kind` vs the other's naive/aware serialization diverge (§4.4) |
| TSV escape / null | agreed escape + explicit `null_token` distinct from `""` | tab/newline-in-value + `"" ≠ null` (§4.3) |

## Boundary rule (A-model)

The language boundary is **process / file / DB only** — no in-process object passing. Every value
that crosses is serialized, so every invariant above is about the serialized wire form. A producer
writes; a consumer reads; equivalence is proven by normalizing both and comparing (golden).

## Enforcement seams (one engine)

- On-write: format/contract-guard hook canonicalizes/blocks.
- `/lint` (POLY-01): the tracked-`*.tsv` boundary check.
- Golden runner: the compare path normalizes both sides before diff.

All three call the one shared core (`libs/python/normalize` + the instance twin against the shared
fixture corpus). A second, divergent canonicalizer is forbidden — it silently defeats the gate.

## Contract coupling

Because the conventions are materialized as `const` values in
`contracts/normalization/format-conventions.schema.json`, flipping a convention moves the RFC 8785
schema hash and trips the contract-drift gate — a convention change is therefore a gated,
golden-paired, CODEOWNERS-reviewed act, exactly like any other contract change.
