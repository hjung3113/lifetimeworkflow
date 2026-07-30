---
phase: 01-constitution-golden-core
plan: 04
subsystem: normalization-core
tags: [contract-02, canonicalization, polyglot, golden-equivalence, cross-validation, d-04, d-05]

# Dependency graph
requires:
  - phase: 01-constitution-golden-core (01-01)
    provides: uv workspace (libs/python member) + .NET 10 bootstrap scripts the .NET half will use
  - phase: 01-constitution-golden-core (01-02)
    provides: contracts/normalization/format-conventions.schema.json (null_token/bom/newline consts the corpus conforms to)
provides:
  - libs/normalize-spec.md — language-neutral §4.3-4.6 canonicalization rules (the canonical RULE, D-04)
  - libs/normalize-fixtures/*.json — shared (raw,canonical) corpus loaded by BOTH language suites (drift catcher)
  - libs/python/normalize — Python thin core (normalize_cell + normalize_tsv), green against the corpus
  - libs/dotnet/Normalize — .NET thin core (NormalizeCell + NormalizeTsv), authored in full (dotnet test deferred)
affects:
  - Plan 06 (golden runner reuses the §4-5 core to normalize both sides before diff)
  - Phase 4 POLY-01 (polyglot linter reuses the same shared core)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Rule-is-canonical (D-04): one language-neutral spec, two thin impls, one shared fixture corpus proves parity"
    - "Don't hand-roll the representation layer: stdlib decimal/utf-8-sig/datetime (Py) + InvariantCulture/DateTimeStyles/UTF8Encoding(false) (.NET)"
    - "Shared corpus as the drift anchor: identical canonical output across both languages = parity, any divergence fails the parity test"

key-files:
  created:
    - libs/normalize-spec.md
    - libs/normalize-fixtures/decimal_locale.json
    - libs/normalize-fixtures/bom_crlf.json
    - libs/normalize-fixtures/tz_iso8601.json
    - libs/normalize-fixtures/null_vs_empty.json
    - libs/python/normalize/__init__.py
    - libs/python/normalize/core.py
    - libs/python/normalize/tests/test_corpus_parity.py
    - libs/dotnet/Normalize/Normalizer.cs
    - libs/dotnet/Normalize/Normalize.csproj
    - libs/dotnet/Normalize.Tests/CorpusParityTests.cs
    - libs/dotnet/Normalize.Tests/Normalize.Tests.csproj
  modified:
    - libs/python/pyproject.toml

key-decisions:
  - "Canonical null sentinel = '<NULL>', empty string stays '' — DISTINCT tokens (§4.3 '' != null, R6)"
  - "Decimal canonical = InvariantCulture fixed-point with trailing zeros stripped; locale ',' remapped to '.' before parse (thousands forbidden -> unambiguous)"
  - "Datetime canonical = UTC 'yyyy-MM-ddTHH:mm:ssZ'; naive values assumed UTC (AssumeUniversal / Python attach UTC)"
  - "Rows ordinal-sorted before diff (Python sorted() == .NET StringComparer.Ordinal on ASCII/BMP) for deterministic order (R8)"
  - "Corpus is a JSON array of {name,kind,raw|raw_b64,canonical}; kind=tsv carries base64 raw bytes for BOM/CRLF cases"

requirements-completed: [CONTRACT-02]

# Metrics
duration: 8min
completed: 2026-07-08
---

# Phase 1 Plan 04: Shared Canonicalizing Comparator Summary

**A single §4.3–4.6 TSV canonicalizer expressed as a language-neutral spec (the canonical RULE, D-04) with two thin implementations — Python (green) and .NET (authored in full) — cross-validated by ONE shared `(raw,canonical)` fixture corpus so any per-language drift fails a parity test. This is the linchpin the golden runner (Plan 06) and the Phase-4 polyglot linter (POLY-01) reuse; it is deliberately NOT the RFC 8785/JCS contract-text hasher (Plan 05).**

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-07-08
- **Tasks:** 3
- **Files:** 13 (12 created, 1 modified)

## Accomplishments

- **Language-neutral spec (`libs/normalize-spec.md`):** eight rules R1–R8 covering UTF-8/BOM strip, LF, InvariantCulture decimal with `,`→`.` remap + trailing-zero strip, float tolerance (compare-time), UTC ISO-8601 datetimes, null-vs-empty distinction, TSV backslash-escape, and deterministic ordinal row sort — each cross-linked to `format-conventions.schema.json` so the corpus and the materialized convention agree.
- **Shared corpus (`libs/normalize-fixtures/*.json`):** four files, 15 entries — `decimal_locale` (comma/dot separator, trailing zeros, integer), `tz_iso8601` (offset/naive/Z), `bom_crlf` (base64 raw bytes: BOM + CRLF + out-of-order rows), `null_vs_empty` (null token → `<NULL>`, empty → ``). Corpus `null_token` (`\N`) verified equal to the schema const.
- **Python core:** `normalize_cell(value, kind, null_token)` + `normalize_tsv(raw_bytes)` on stdlib `decimal` / `utf-8-sig` / `datetime` (no float round-trip, no hand-rolled BOM). Parity test loads every corpus entry — **16 passed** (`uv run pytest ... -x` exit 0), ruff clean.
- **.NET core:** `Normalizer.NormalizeCell` + `NormalizeTsv` on `CultureInfo.InvariantCulture`, `DateTimeStyles.AssumeUniversal|AdjustToUniversal`, `new UTF8Encoding(false)` + explicit `\n`, targeting `net10.0`. xunit.v3 3.2.2 `CorpusParityTests` loads the SAME corpus via a walk-up-to-repo-root resolver. Contains no contract-text JSON canonicalizer (TSV comparator only).

## Task Commits

1. **Task 1: language-neutral spec + shared fixture corpus** — `58d2c8d` (feat)
2. **Task 2: Python §4-5 core + corpus parity test** — `fcfbe8a` (feat)
3. **Task 3: .NET §4-5 core + corpus parity test** — `870a6c6` (feat)

## Files Created/Modified

- `libs/normalize-spec.md` — canonical §4.3–4.6 rule spec (R1–R8) + corpus format contract
- `libs/normalize-fixtures/{decimal_locale,bom_crlf,tz_iso8601,null_vs_empty}.json` — shared drift-catcher corpus
- `libs/python/normalize/{__init__.py,core.py}` — Python thin core (public surface for reuse)
- `libs/python/normalize/tests/test_corpus_parity.py` — parametrized parity test over the corpus
- `libs/python/pyproject.toml` — description updated to reflect the landed core (stdlib-only)
- `libs/dotnet/Normalize/{Normalizer.cs,Normalize.csproj}` — .NET thin core, net10.0
- `libs/dotnet/Normalize.Tests/{CorpusParityTests.cs,Normalize.Tests.csproj}` — xunit.v3 parity test over the SAME corpus

## Deviations from Plan

None beyond the pre-authorized .NET-runtime deferral (below). Plan tasks executed as written.

## Deferred Verification (.NET runtime — egress policy, NOT a failure)

Per the execution directive and STATE.md's standing BOOT-01 blocker, this container's egress policy hard-blocks the .NET 10 SDK download (403), so `dotnet` is not installed and cannot be installed here.

- **⏸ DEFERRED:** Task 3 automated verification `dotnet test libs/dotnet/Normalize.Tests` — the .NET half of the parity cross-check. Also the plan's `bash tools/bootstrap/verify.sh` gate (asserts dotnet 10) is unrunnable for the same reason.
- **Why this is safe:** the shared corpus + language-neutral spec are the source of truth. The .NET source is authored in full and mirrors the Python core rule-for-rule (same InvariantCulture decimal + `,`→`.` remap + trailing-zero strip, same UTC ISO-8601 format, same BOM-strip + LF + ordinal row sort). When the .NET 10 SDK is allowlisted (or pre-installed) on a later run, `dotnet test` verifies with **zero code changes**.
- **Human action to close:** allowlist the .NET install hosts (see STATE.md BOOT-01 blocker) or ship a pre-installed .NET 10, then run `"$HOME/.dotnet/dotnet" test libs/dotnet/Normalize.Tests/Normalize.Tests.csproj` — expect all 15 corpus entries green, identical canonical output to the Python suite.

## Threat Model Coverage

- **T-04-01 (per-language drift):** mitigated — ONE shared corpus loaded by BOTH suites; Python half proven green, .NET half asserts the identical corpus (verification deferred, not the mitigation).
- **T-04-02 (float/locale repr bugs):** mitigated — stdlib `decimal` + `CultureInfo.InvariantCulture`, never a float/double round-trip or manual munging.
- **T-04-03 (corpus fixtures):** accept — synthetic representation samples (1.5, dates, BOM bytes), no PII/secrets.

No new threat surface beyond the plan's `<threat_model>`.

## Known Stubs

None. The Python core is a complete working implementation; the .NET core is complete source pending only runtime execution (deferred above). The TSV backslash-escape rule (R7) is documented and honored structurally but not exercised by a Phase-1 corpus entry (no in-field tabs yet) — this is intentional per plan scope, to grow with fixtures.

## Next Phase Readiness

- The shared §4-5 core is available for Plan 06's golden runner (normalize both sides before diff) and Phase-4 POLY-01 (linter reuse) — exposed as clean importable/referenceable libraries.
- Python parity is green now; the .NET parity half is one `dotnet test` away once BOOT-01 egress is resolved.

## Self-Check: PASSED

All 12 created files + 1 modified file verified on disk; all three task commits (58d2c8d, fcfbe8a, 870a6c6) present in git history; Python parity suite green (16 passed, exit 0). The only unverified item is `dotnet test`, explicitly deferred by egress policy (not a failure).

---
*Phase: 01-constitution-golden-core*
*Completed: 2026-07-08*
