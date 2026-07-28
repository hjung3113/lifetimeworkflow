---
name: dotnet-conventions
description: >-
  Use when writing or reviewing .NET code in libs/dotnet or components (the parser/converter
  side). Covers the .NET 10 SDK toolchain, xunit.v3 + Verify.XunitV3 testing, JsonSchema.Net
  validation, and the emit-side boundary rules (UTF-8 no-BOM, forced LF, InvariantCulture
  decimals, UTC ISO-8601) that keep polyglot equivalence green.
---

# dotnet-conventions

How .NET code is written in this monorepo. The .NET side owns the CPU-bound parser and
converter; it talks to the Python side only across process/file/DB (A-model), never in-process.

## Toolchain

- **.NET 10 SDK** (`dotnet *` scope). Build with `dotnet build`, test with `dotnet test`.
- The SDK is egress-blocked in this ephemeral container (BOOT-01) — author code and tests, but
  `dotnet` execution is deferred until the SDK is installed. Do not route around the egress deny.
- **Tests:** xunit.v3 (Microsoft.Testing.Platform built in). Do not use xunit v2 or the v4
  pre-release.
- **Golden / approval:** Verify.XunitV3 — the `.received`/`.verified` snapshot workflow. Promotion
  is human review at the PR (the `/examples/*/golden/` CODEOWNERS entry), never an agent
  self-bless.
- **Schema validation:** JsonSchema.Net (System.Text.Json, Draft 2020-12). No Newtonsoft.

## Boundary invariants (§4.3–4.6) — the .NET-specific traps

.NET defaults fight polyglot equivalence; every emit path MUST normalize:

- **Encoding:** UTF-8 with **BOM stripped** (.NET loves to emit a BOM; Python then misreads the
  first column).
- **Newlines:** force **LF** (.NET defaults to CRLF).
- **Decimals:** `.` separator via **InvariantCulture** always (`.ToString()` is locale-dependent).
- **Timestamps:** **UTC** ISO-8601 fixed strings; mind `DateTime.Kind` (naive vs aware drift).
- **TSV / null:** agreed escape for tab/newline-in-value; explicit null token (`"" ≠ null`).

The canonicalization core lives in `libs/dotnet/Normalize`, cross-validated against
`libs/python/normalize` via the shared `libs/normalize-fixtures` corpus. Equivalence is checked
**after** this core — never a raw byte-diff.

## Non-negotiables

Contract-first (`contracts/` wins; fix the code, not the contract). Never write the constitution
plane (`contracts/`, `docs/adr/`, `golden/`) from .NET code. See `libs/dotnet/AGENTS.md` for the
self-sufficient per-package rules.

## Deeper reference

Put extended examples (a full Verify test, a normalization emit walkthrough) under `references/`
in this skill directory rather than inlining here — the body stays scannable (progressive
disclosure). See `libs/dotnet/AGENTS.md` and `CLAUDE.md` §"Golden-Equivalence Comparator".
