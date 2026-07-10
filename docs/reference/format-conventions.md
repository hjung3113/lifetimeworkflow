<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Cross-cutting format conventions (§4.3-4.6) — materialized, hashable (P14)

> DERIVED reference — regenerated from `contracts/normalization/format-conventions.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

SEED PLACEHOLDER. Materializes the integration_contracts_design §4.3-4.6 cross-cutting canonicalization conventions as explicit const/enum fields so the contract-drift hash (Plan 05, RFC 8785 -> SHA-256) covers convention changes — not only column reorders (PITFALLS P14). Flipping any const here (e.g. bom false->true) MUST bump the drift hash. All values are EXAMPLE placeholders (A4); domain-confirmed values are Out of Scope (CONTRACT-01).

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| bom | const | yes | false | §4.3 byte-order-mark presence — stripped/absent (recommended). .NET may emit a BOM; Python then misreads the first column. |
| culture | const | yes | invariant | §4.6 number formatting culture — InvariantCulture forced (.NET ToString is locale-dependent). |
| decimal_sep | const | yes | . | §4.6 decimal separator — '.' fixed (locale ',' accident guard). |
| encoding | const | yes | utf-8 | §4.3 character encoding — unified UTF-8. |
| float_compare | object | yes |  | §4 numeric comparison — tolerance-aware float compare (avoid last-digit repr diffs). |
| interval | const | yes | [start,end) | §4 interval half-open convention [start,end) for time/file ranges. |
| newline | const | yes | lf | §4.3 line ending — force LF (no CRLF). .NET default may be CRLF. |
| null_token | const | yes | \N | §4.3 explicit null-vs-empty token — EXAMPLE placeholder ('' empty string is distinct from this null token). Domain value TBD. |
| row_ordering | const | yes | deterministic-sort | §4 key/row ordering — deterministic sort before diff (unordered sets must not cause false diffs). |
| timezone | const | yes | utc-iso8601 | §4.4 timezone/time format — UTC, fixed ISO-8601 string. Guards .NET DateTime.Kind vs Python naive/aware serialization divergence. |
| tsv_escape | const | yes | backslash | §4.3 TSV escaping of tab/newline-in-value — EXAMPLE agreed rule (backslash-escape). Domain rule TBD. |

## Canonicalization conventions (§4.3–4.6)

- **bom** = `false` — §4.3 byte-order-mark presence — stripped/absent (recommended). .NET may emit a BOM; Python then misreads the first column.
- **culture** = `invariant` — §4.6 number formatting culture — InvariantCulture forced (.NET ToString is locale-dependent).
- **decimal_sep** = `.` — §4.6 decimal separator — '.' fixed (locale ',' accident guard).
- **encoding** = `utf-8` — §4.3 character encoding — unified UTF-8.
- **interval** = `[start,end)` — §4 interval half-open convention [start,end) for time/file ranges.
- **newline** = `lf` — §4.3 line ending — force LF (no CRLF). .NET default may be CRLF.
- **null_token** = `\N` — §4.3 explicit null-vs-empty token — EXAMPLE placeholder ('' empty string is distinct from this null token). Domain value TBD.
- **row_ordering** = `deterministic-sort` — §4 key/row ordering — deterministic sort before diff (unordered sets must not cause false diffs).
- **timezone** = `utc-iso8601` — §4.4 timezone/time format — UTC, fixed ISO-8601 string. Guards .NET DateTime.Kind vs Python naive/aware serialization divergence.
- **tsv_escape** = `backslash` — §4.3 TSV escaping of tab/newline-in-value — EXAMPLE agreed rule (backslash-escape). Domain rule TBD.
