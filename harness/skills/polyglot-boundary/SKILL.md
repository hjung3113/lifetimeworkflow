---
name: polyglot-boundary
description: >-
  Use whenever code crosses the language boundary or reads/writes a wire file (TSV) — the single
  source of truth for the §4.3-4.6 canonicalization invariants (BOM, LF, decimals, float tolerance,
  ordering, UTC, TSV escape/null) and the process/file/DB-only boundary rule. Consult when a value
  moves between the two language sides.
---

# polyglot-boundary

The Core Value of this repo, as one skill instead of scattered prose. The languages express the
same values differently; those representation differences are exactly the bugs this harness exists
to catch. This skill is the map of the boundary and its invariants — the canonical, hashed rule
lives in the constitution plane; this is the pointer + the reasoning.

## The boundary is process / file / DB only (A-model)

Cross-language calls happen through a **process spawn, a file, or a DB** — never in-process object
passing. A producer on one side writes a wire artifact; the consumer on the other side reads it.
This is why the invariants below are about *serialized representation*, not object shape.

## The §4.3–4.6 invariants (canonicalize before you compare)

Cross-language equivalence is only ever checked **after** the shared canonicalization core runs —
never a raw byte-diff (a byte-diff false-reds on encoding/locale/timezone noise and hides real
regressions). The invariants:

1. **Encoding / BOM (§4.3)** — UTF-8; a leading BOM is stripped; output carries no BOM.
2. **Newlines (§4.3)** — forced LF; CRLF and lone CR normalize to LF.
3. **Decimal & culture (§4.6)** — InvariantCulture `.` separator; no thousands separators; decimal
   types, never a float round-trip; trailing zeros + trailing `.` trimmed.
4. **Float compare tolerance (§4)** — numeric *comparison* is tolerance-aware (`1e-9`) so a
   last-digit representation never flips equivalence.
5. **Key / row ordering (§4)** — deterministic sort before diff; unordered sets must not false-red.
6. **Timezone / datetime (§4.4)** — convert to UTC; emit fixed ISO-8601 `yyyy-MM-ddTHH:mm:ssZ`; a
   naive value is assumed UTC.
7. **TSV escape / null-vs-empty (§4.3)** — tab field separator with the agreed escape for
   tab/newline-in-value; the null token is distinct from the empty string (`"" ≠ null`).

## Where the canonical rule actually lives (don't fork it)

- **`libs/normalize-spec.md`** (R1–R7) is the language-neutral spec — the single source of truth.
- **`libs/python/normalize`** is a *thin* implementation of that spec; an instance's language-side
  twin is another thin implementation. **The rule is canonical, not any one language.**
- **`contracts/normalization/format-conventions.schema.json`** materializes the conventions as
  `const`/`enum` fields — so a convention flip (e.g. `bom: false → true`) bumps the drift hash
  exactly like a schema change. That schema is the hashed, gated form; edit it only through the
  contract-drift + golden path.
- A shared `(raw, canonical)` fixture corpus (`libs/normalize-fixtures/`) is loaded by BOTH test
  suites; any per-language drift fails the parity test.

## One core, three call sites

The same rule engine is reused, never re-implemented: the on-write format/guard hook, the
`/lint` POLY-01 check over tracked `*.tsv` wire files, and the golden runner's compare path all call
the one shared core. Do not add a second canonicalizer (a divergent impl defeats the whole point).

> Scope guard: this is the **TSV data** comparator. It is NOT RFC 8785 / JCS, which canonicalizes
> JSON *contract text* for the drift hash — they share only the word "canonical". Do not conflate.

## Related
- `harness/skills/golden-debug/SKILL.md` — the decision tree when these invariants are violated and
  a golden goes red.
- `references/canonicalization-table.md` — the full rule table with rationale per axis.
